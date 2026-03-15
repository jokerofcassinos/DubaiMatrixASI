import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal
from core.consciousness.regime_detector import MarketRegime
from config.omega_params import OMEGA

class QuantumTunnelingOscillator(BaseAgent):
    """
    Ω-EPISTEMIC AGENT: QUANTUM TUNNELING OSCILLATOR
    
    Este agente detecta a probabilidade de o preço "tunelar" através de barreiras
    de liquidez (suportes/resistências) sem a necessidade de momentum linear.
    Utiliza a métrica de "Viscosidade do Book" contra a "Curvatura de Ricci" do preço.
    """
    
    def __init__(self, **kwargs):
        weight = kwargs.get("weight", OMEGA.get("weight_quantum_tunneling", 1.25))
        super().__init__("QuantumTunnelingOscillator", weight=weight)
        
    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        regime = kwargs.get("regime_state")
        entropy = snapshot.metadata.get("shannon_entropy", 0.5)
        v_pulse = snapshot.metadata.get("v_pulse", 0.0)
        
        # 1. Recuperar Curvatura (Ricci Flow Proxy)
        # Se a volatilidade cai mas a entropia informacional sobe, a curvatura é negativa = Compressão.
        volatility_ratio = snapshot.indicators.get("M1_volatility_ratio", [1.0])
        v_ratio = volatility_ratio[-1] if volatility_ratio else 1.0
        
        curvature = (entropy / max(v_ratio, 0.01))
        
        signal = 0.0
        confidence = 0.0
        reasoning = ""
        
        # 2. Lógica de Tunelamento (Quantum Tunneling)
        # Se estamos em drift/baixa liquidez e a curvatura explode (> 1.5)
        is_bottleneck = regime.current.value in ["LOW_LIQUIDITY", "CHOPPY", "SQUEEZE_BUILDUP"]
        
        # The user's instruction seems to indicate a desire to use the MarketRegime enum directly
        # for comparison and potentially add a specific check for SQUEEZE_BUILDUP.
        # The provided snippet was syntactically incorrect, so I'm interpreting it as
        # wanting to add a more robust check for SQUEEZE_BUILDUP using the enum directly.
        # I'm adding this as an additional condition to `is_bottleneck` for robustness.
        if regime and hasattr(regime, 'current') and regime.current == MarketRegime.SQUEEZE_BUILDUP:
            is_bottleneck = True # Ensure it's considered a bottleneck if it's SQUEEZE_BUILDUP via enum
        
        if is_bottleneck and curvature > 1.45:
            # Detectar a direção do tunelamento via delta de ticks
            delta = snapshot.metadata.get("book_imbalance", 0.0)
            
            if delta > 0.6: # Pressão compradora invisível
                signal = 0.85
                confidence = 0.88
                reasoning = f"TUNNELING_BUY: Curvature={curvature:.2f} (E={entropy:.2f}/V={v_ratio:.2f}) | Liquidity Leakage detected."
            elif delta < -0.6: # Pressão vendedora invisível
                signal = -0.85
                confidence = 0.88
                reasoning = f"TUNNELING_SELL: Curvature={curvature:.2f} (E={entropy:.2f}/V={v_ratio:.2f}) | Liquidity Leakage detected."
        
        # 3. Ignition Awareness
        if v_pulse > 0.7:
             confidence = min(0.95, confidence * 1.25)
             reasoning += " [IGNITION_BOOST]"

        return AgentSignal(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            weight=self.weight,
            reasoning=reasoning
        )
