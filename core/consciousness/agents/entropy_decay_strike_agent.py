import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal
from core.consciousness.regime_detector import MarketRegime
from config.omega_params import OMEGA

class EntropyDecayStrikeAgent(BaseAgent):
    """
    Ω-EPISTEMIC AGENT: ENTROPY DECAY STRIKE
    
    Detecta o colapso da entropia informacional (Decay). 
    Quando a incerteza estatística morre e o enxame entra em ressonância, 
    é o momento do "Strike" de alta precisão.
    """
    
    def __init__(self, **kwargs):
        weight = kwargs.get("weight", 3.5)
        super().__init__("EntropyDecayStrikeAgent", weight=weight)
        
    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        entropy = snapshot.metadata.get("shannon_entropy", 0.9)
        entropy_history = snapshot.metadata.get("entropy_history", [entropy])
        
        if len(entropy_history) < 5:
            return AgentSignal(agent_name=self.name, signal=0.0, confidence=0.0, reasoning="Waiting for entropy stabilization.", weight=self.weight)
        
        regime = kwargs.get("regime_state")
        if regime and hasattr(regime, 'current') and regime.current == MarketRegime.HIGH_VOL_CHAOS:
            return AgentSignal(agent_name=self.name, signal=0.0, confidence=0.0, reasoning="Waiting for entropy stabilization.", weight=self.weight)
            
        # 1. Calcular o Decay (Derivada da Entropia)
        decay = entropy - np.mean(entropy_history[-5:])
        
        signal = 0.0
        confidence = 0.0
        reasoning = ""
        
        # 2. Strike Trigger: Entropia colapsando (decay negativo forte) + Momentum
        if decay < -0.15 and entropy < 0.6:
            v_pulse = snapshot.metadata.get("v_pulse", 0.0)
            if v_pulse > 0.4:
                # Direção confirmada pelo V-Pulse/Inércia
                signal = 1.0 if v_pulse > 0 else -1.0 # V-Pulse is always positive in current dataengine, check direction
                # Direção real via Close[0] vs Close[-1]
                candles = snapshot.candles.get("M1")
                if candles:
                    direction = np.sign(candles["close"][-1] - candles["close"][-2])
                    signal = 1.0 * direction
                    confidence = 0.95
                    reasoning = f"ENTROPY_COLLAPSE_STRIKE: Entropy={entropy:.2f} Decay={decay:.2f}. Deterministic certainty incoming."
        
        return AgentSignal(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            weight=self.weight,
            reasoning=reasoning
        )
