import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal
from config.omega_params import OMEGA

class TopologicalManifoldAgent(BaseAgent):
    """
    Ω-EPISTEMIC AGENT: TOPOLOGICAL MANIFOLD AGENT
    
    Detecta a formação de "Buracos Topológicos" em uma variedade 3D (Preço x Tempo x Inércia).
    Zonas de baixa densidade informacional (vácuos) atraem o preço violentamente.
    """
    
    def __init__(self, **kwargs):
        weight = kwargs.get("weight", 3.2)
        super().__init__("TopologicalManifoldAgent", weight=weight)
        
    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles = snapshot.candles.get("M1")
        if not candles or len(candles["close"]) < 60:
            return AgentSignal(agent_name=self.name, signal=0.0, confidence=0.0, reasoning="NO_DATA", weight=self.weight)

        closes = np.array(candles["close"], dtype=np.float64)
        volumes = np.array(candles["tick_volume"], dtype=np.float64)
        
        # 1. Calcular Inércia (Volume/Range)
        ranges = np.array(candles["high"]) - np.array(candles["low"])
        inertia = volumes / np.where(ranges == 0, 1.0, ranges)
        
        # 2. Mapear Manifold 3D
        # Simplificamos detectando "Vácuos de Inércia" em níveis de preço
        current_price = snapshot.price
        price_std = np.std(closes)
        
        # Zonas de "Buraco": Pouco volume e alta velocidade histórica no nível atual
        historical_density = np.sum(np.exp(-0.5 * ((closes - current_price) / price_std)**2) * inertia)
        
        signal = 0.0
        confidence = 0.0
        reasoning = ""
        
        # Se a densidade histórica for muito baixa (< threshold) e temos momentum
        density_thresh = np.mean(inertia) * 0.5
        
        if historical_density < density_thresh:
            v_pulse = snapshot.metadata.get("v_pulse", 0.0)
            if v_pulse > 0.5:
                 # Direção do vácuo via momentum
                 momentum = closes[-1] - closes[-5]
                 signal = 0.9 if momentum > 0 else -0.9
                 confidence = 0.85
                 reasoning = f"TOPOLOGICAL_GAP: Density={historical_density:.2f} < {density_thresh:.2f}. Vacuum hole detected."
        
        return AgentSignal(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            weight=self.weight,
            reasoning=reasoning
        )
