import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal
from config.omega_params import OMEGA

class RiemannianRicciAgent(BaseAgent):
    """
    Ω-PhD-7 AGENT: RIEMANNIAN RICCI MANIFOLD AGENT
    
    Modela o mercado como uma variedade 3D (Preço, Tempo, Volume).
    Calcula o Tensor de Curvatura de Ricci (R) para identificar "Poços Gravitacionais" 
    onde a liquidez atrai o preço deterministicamente.
    """
    
    def __init__(self, weight=4.5):
        super().__init__("RiemannianRicci", weight=weight)
        self._curvature_history = []
        
    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles = snapshot.candles.get("M1")
        if not candles or len(candles["close"]) < 50:
            return AgentSignal(self.name, 0.0, 0.0, "INSUFFICIENT_GEOMETRY_DATA", self.weight)

        # 1. Definir Coordenadas da Variedade (x1=Price, x2=Time, x3=Volume)
        # Usamos normalização local para garantir métricas comparáveis
        prices = np.array(candles["close"][-30:], dtype=np.float64)
        vols = np.array(candles["tick_volume"][-30:], dtype=np.float64)
        times = np.arange(len(prices), dtype=np.float64)
        
        # 2. Calcular o Tensor Métrico (g_ij)
        # g = diag(1/var_price, 1/var_time, 1/var_vol)
        # Simplificamos para Curvatura Escalar de Ricci em 1D Projetado
        
        # Calcular derivadas de primeira e segunda ordem (Christoffel Symbols proxy)
        dp = np.gradient(prices)
        d2p = np.gradient(dp)
        
        # Curvatura K = |d2p| / (1 + dp^2)^(3/2)
        curvature = np.abs(d2p) / (1 + dp**2)**1.5
        
        # Média da curvatura recente vs histórica
        current_k = np.mean(curvature[-5:])
        avg_k = np.mean(curvature)
        
        # 3. Detectar Singularidade (Ricci Flow Concentration)
        # Se a curvatura está "explodindo" (> threshold), o preço está entrando em um atrator.
        k_threshold = OMEGA.get("ricci_k_threshold", 2.5)
        
        signal = 0.0
        conf = 0.0
        reason = "EUCLIDEAN_SPACE_FLAT"
        
        k_ratio = current_k / (avg_k + 1e-9)
        momentum = prices[-1] - prices[-10]
        
        # 3. Detectar Singularidade ou Geodésica
        if k_ratio > k_threshold:
            # Singularidade: Curvatura explodindo (Atrator)
            signal = np.sign(momentum)
            conf = min(0.98, k_ratio / 10.0)
            reason = f"RICCI_SINGULARITY (K_Ratio={k_ratio:.2f} > {k_threshold:.1f})"
        elif k_ratio < 0.2 and abs(momentum) > (snapshot.atr * 0.5):
            # GEODÉSICA: Curvatura baixíssima (<20% da média) + Momentum consistente.
            # Isso é o "Institutional Glide" que queremos capturar.
            signal = np.sign(momentum)
            conf = 0.88 # Alta confiança em fluxo laminar
            reason = f"GEODESIC_FLOW (K_Ratio={k_ratio:.2f} < 0.20) - Institutional Glide"
            
        return AgentSignal(self.name, signal, conf, reason, self.weight)
