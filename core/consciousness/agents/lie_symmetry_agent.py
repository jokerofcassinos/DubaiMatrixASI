import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal
from config.omega_params import OMEGA

class LieSymmetryAgent(BaseAgent):
    """
    Ω-PhD-7 AGENT: LIE SYMMETRY AGENT
    
    Detecta "Simetrias Translacionais" no fluxo de ordens (Order Book Refreshes).
    Identifica o comportamento de "Hidden Refreshing" (Icebergs) via 
    invariância algébrica da pressão do book.
    """
    
    def __init__(self, weight=4.6):
        super().__init__("LieSymmetry", weight=weight)
        
    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        tick_buffer = snapshot.recent_ticks[-30:] if hasattr(snapshot, 'recent_ticks') else []
        if not tick_buffer:
             tick_buffer = snapshot.metadata.get("tick_buffer", [])[-30:]
             
        if len(tick_buffer) < 20:
            return AgentSignal(self.name, 0.0, 0.0, "INSUFFICIENT_SYMMETRY_DATA", self.weight)

        # 1. Extrair Vetores de Pressão (Buy Volume / Sell Volume)
        buy_vols = np.array([t.get("buy_volume", 1.0) for t in tick_buffer], dtype=np.float64)
        sell_vols = np.array([t.get("sell_volume", 1.0) for t in tick_buffer], dtype=np.float64)
        
        # 2. Calcular Invariantes de Lie (Transformação Translacional)
        # Se ΔVolume / ΔPreço é constante para múltiplos degraus, temos uma 
        # simetria de "Refreshing" (Iceberg Algorithmic Injection).
        
        prices = np.array([t.get("last", 0) for t in tick_buffer], dtype=np.float64)
        dp = np.diff(prices)
        dv_buy = np.diff(buy_vols)
        dv_sell = np.diff(sell_vols)
        
        # Filtros de divisão por zero
        dp_nonzero = np.where(dp == 0, 1e-9, dp)
        
        # Razão de Injeção: r = dv / dp
        r_buy = dv_buy / dp_nonzero
        r_sell = dv_sell / dp_nonzero
        
        # 3. Detectar Estabilidade (Symmetry)
        # Se a variância de 'r' é muito baixa, a injeção é matemática (simétrica).
        # Lie Algebra: [X, Y] = 0 (Comutação / Invariância)
        var_r_buy = np.var(r_buy[-10:])
        var_r_sell = np.var(r_sell[-10:])
        
        # Threshold de Estabilidade (Simetria)
        lie_thresh = OMEGA.get("lie_symmetry_threshold", 0.1)
        
        signal = 0.0
        conf = 0.0
        reason = "ASYMMETRIC_CHAOS_STREAK"
        
        if var_r_buy < lie_thresh and np.mean(buy_vols[-5:]) > np.mean(sell_vols[-5:]):
            signal = 1.0
            conf = 0.94
            reason = f"LIE_TRANSLATIONAL_SYMMETRY (Buy_Var={var_r_buy:.4f} < {lie_thresh})"
        elif var_r_sell < lie_thresh and np.mean(sell_vols[-5:]) > np.mean(buy_vols[-5:]):
            signal = -1.0
            conf = 0.94
            reason = f"LIE_TRANSLATIONAL_SYMMETRY (Sell_Var={var_r_sell:.4f} < {lie_thresh})"
            
        return AgentSignal(self.name, signal, conf, reason, self.weight)
