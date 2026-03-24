"""
Agente Ph.D. focado em Cross-Asset Arbitrage (Nexus).
Observa movimentos microestruturais do Ouro e NASDAQ para antecipar BTC.
"""

from core.consciousness.agents.base import BaseAgent, AgentSignal

class NexusAgent(BaseAgent):
    def __init__(self, weight: float = 3.5):
        super().__init__("NexusAgent", weight)
        # Agent has high volatility tolerance
        
    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        import time
        resonance = snapshot.metadata.get("nexus_resonance", 0.0)
        breakouts = snapshot.metadata.get("nexus_breakouts", [])
        
        current = time.time()
        if abs(resonance) > 0.3 and current - getattr(self, '_last_log', 0) > 30.0:
            from utils.logger import log
            log.signal(f"🌐 [NEXUS AGENT] Forte Colinearidade Macro detectada: Φ={resonance:+.2f}")
            self._last_log = current
        
        if abs(resonance) < 0.2:
            return AgentSignal(self.name, 0.0, 0.0, "Nexus Silencioso. Sem liderança macro.", self.weight)

        # Sinal fortíssimo se ativos macroeconômicos explodiram juntos (Risk-ON / Risk-OFF)
        confidence = min(0.4 + (abs(resonance) * 0.6), 1.0)
        
        # Filtro de Confirmação (Se ETH estiver alinhado com o S&P500)
        if len(breakouts) >= 2:
            confidence = min(confidence + 0.2, 1.0) # Confluência Extrema
            
        reason = f"Cross-Asset Resonance Φ={resonance:+.2f} | Drivers: {', '.join(breakouts) if breakouts else 'Continuous Flow'}"
        
        if resonance > 0.2:
            return AgentSignal(self.name, 1.0, confidence, reason, self.weight)
        elif resonance < -0.2:
            return AgentSignal(self.name, -1.0, confidence, reason, self.weight)
            
        return AgentSignal(self.name, 0.0, 0.0, "Baixa ressonância macro", self.weight)
