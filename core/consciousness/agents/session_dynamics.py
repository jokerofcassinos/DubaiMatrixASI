"""
╔══════════════════════════════════════════════════════════════════════════════╗
║               DUBAI MATRIX ASI — SESSION DYNAMICS AGENT                     ║
║       Adaptação de comportamento baseada em sessões globais                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from core.consciousness.agents.base import BaseAgent, AgentSignal
from utils.time_tools import TimeEngine
from utils.decorators import catch_and_log

class SessionDynamicsAgent(BaseAgent):
    """
    Agente de Dinâmica de Sessão.
    Ajusta o bias direcional e a agressividade baseando-se na sessão UTC atual.
    BTCUSD tem comportamentos distintos (ex: Fakeouts em Ásia, Tendências em NY).
    """

    def __init__(self, weight: float = 1.0):
        super().__init__("SessionDynamics", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        info = TimeEngine.session_info()
        sessions = info["active_sessions"]
        trading_favorability = info["trading_favorability"]
        
        signal = 0.0
        # Heurísticas de Bias por Sessão (BTCUSD histórico)
        if "NY_OPEN" in sessions or "OVERLAP_EU_US" in sessions:
            # NY/London Overlap costuma ser volátil e tendencioso
            signal = 0.1 # Leve bias bullish histórico (ou momentum follow)
        elif "ASIA" in sessions and "EUROPE" not in sessions:
            # Ásia costuma ser lateral ou mean-reverting para BTC
            signal = 0.0 # Neutralidade absoluta
            
        confidence = trading_favorability
        
        return AgentSignal(
            agent_name=self.name,
            signal=float(signal),
            confidence=float(confidence),
            reasoning=f"Sessions={sessions}, Favorability={trading_favorability:.2f}",
            weight=self.weight
        )

class TemporalTrendAgent(BaseAgent):
    """
    Agente de Tendência Temporal.
    Analisa a influência do horário (H) na formação de tendências.
    Ex: Tendências que começam às 10:00 UTC tendem a consolidar até as 14:00 UTC.
    """

    def __init__(self, weight: float = 1.0):
        super().__init__("TemporalTrend", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        now = TimeEngine.now_utc()
        hour = now.hour
        
        signal = 0.0
        reasoning = ""
        
        # Horários de Reversão / Continuação estatística do BTC
        if 12 <= hour <= 14:
            # Pré-NY Open: Reversões de tendências de Londres são comuns
            signal = 0.0 
            reasoning = "NY_PRE_OPEN_INCERTAINTY"
        elif 14 <= hour <= 18:
            # NY Afternoon: Geralmente onde as tendências do dia se confirmam
            signal = 0.1
            reasoning = "NY_TREND_CONTINUATION"
        elif 0 <= hour <= 2:
            # Asia Open: Frequentemente caça liquidez do fechamento de NY
            signal = -0.1
            reasoning = "ASIA_LIQUIDITY_HUNT"
            
        return AgentSignal(
            agent_name=self.name,
            signal=float(signal),
            confidence=0.6,
            reasoning=reasoning,
            weight=self.weight
        )
