"""
╔══════════════════════════════════════════════════════════════════════════════╗
║               DUBAI MATRIX ASI — MARKET TRANSITION AGENT                    ║
║       Monitoramento e predição de transições de regime                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal
from core.consciousness.regime_detector import MarketRegime
from utils.decorators import catch_and_log

class MarketTransitionAgent(BaseAgent):
    """
    Agente de Transição de Mercado.
    Foca especificamente em antecipar a mudança de um regime para outro.
    Ex: RANGING -> BREAKOUT, CHOPPY -> TREND.
    """

    def __init__(self, weight: float = 1.0):
        super().__init__("MarketTransition", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, regime_state=None, **kwargs) -> AgentSignal:
        # Se regime_state não for passado via kwargs, tentamos inferir do snapshot (ou aguardamos o Brain injetar)
        # Nota: O Brain deve injetar regime_state no analyze se disponível.
        
        # Fallback se o Brain ainda não foi atualizado para passar regime_state
        if not regime_state:
            return None

        prob = regime_state.transition_prob
        current = regime_state.current
        predicted = regime_state.predicted_next
        
        if prob < 0.4:
            return AgentSignal(self.name, 0.0, 0.3, "Stability high, transition unlikely", self.weight)

        # Mapeamento de direção da transição
        signal = 0.0
        if predicted in [MarketRegime.TRENDING_BULL, MarketRegime.BREAKOUT_UP, MarketRegime.CREEPING_BULL]:
            signal = 0.8 * prob
        elif predicted in [MarketRegime.TRENDING_BEAR, MarketRegime.BREAKOUT_DOWN, MarketRegime.DRIFTING_BEAR]:
            signal = -0.8 * prob
        elif predicted == MarketRegime.MEAN_REVERTING:
            # Se estamos em tendência e vamos para Mean Reversion, sinal contrário à tendência
            if current == MarketRegime.TRENDING_BULL: signal = -0.5
            elif current == MarketRegime.TRENDING_BEAR: signal = 0.5
            
        confidence = prob # A confiança é a própria probabilidade de transição
        
        return AgentSignal(
            agent_name=self.name,
            signal=float(signal),
            confidence=float(confidence),
            reasoning=f"TransitionProb={prob:.2f}, From={current.value}, To={predicted.value}",
            weight=self.weight
        )
