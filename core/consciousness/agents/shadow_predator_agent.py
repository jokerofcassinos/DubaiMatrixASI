"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — SHADOW PREDATOR AGENT                      ║
║     Agente que detecta inimigos e ativa o MODO PREDADOR.                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from typing import Optional
from core.consciousness.agents.base import BaseAgent, AgentSignal
from execution.shadow_predator import ShadowPredatorEngine

class ShadowPredatorAgent(BaseAgent):
    """
    Agente sentinela que monitora assinaturas hostis.
    """

    def __init__(self, predator_engine: ShadowPredatorEngine):
        super().__init__("ShadowPredator", weight=2.0)
        self.engine = predator_engine
        self.needs_orderflow = True

    def analyze(self, snapshot, orderflow_analysis=None, **kwargs) -> Optional[AgentSignal]:
        analysis = self.engine.analyze_signature(snapshot, orderflow_analysis)
        
        pressure = analysis.get("adversarial_pressure", 0.0)
        is_spoofing = analysis.get("spoofing_detected", False)
        
        signal = 0.0
        confidence = 0.0
        
        if is_spoofing:
            # Operar CONTRA a manipulação
            # Se estão fazendo spoofing de compra (induzindo compra), nós VENDEMOS.
            # No nosso engine, pressure > 0 significa spoofing de venda removido (induzindo compra)
            signal = -1.0 if pressure > 0 else 1.0
            confidence = 0.9 # Alta confiança em detectar manipulação
            
        reasoning = f"Spoofing: {is_spoofing} | AdvPressure: {pressure:.2f}"
        if analysis.get("layering_detected"):
            reasoning += " | Layering Detected"
            
        return AgentSignal(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning
        )
