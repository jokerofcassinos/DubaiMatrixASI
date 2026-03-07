"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — STRUCTURAL PREMIUM AGENTS                   ║
║       CRT (Candle Range Theory) & TBS (Trend Bias/Breakdown System)         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal
from utils.time_tools import TimeEngine
from utils.decorators import catch_and_log

class CRTAgent(BaseAgent):
    """
    Agente CRT (Candle Range Theory).
    Foca na anatomia do range inicial vs expansões.
    Analisa Asian Range (Consolidação), London (Expansão) e NY (Continuação/Reversão).
    Busca por 'Judas Swings' (rompimento falso do range inicial).
    """

    def __init__(self, weight: float = 1.5):
        super().__init__("CRTAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        # Lógica de Range de Sessão (Simplificada para o Agente)
        info = TimeEngine.session_info()
        sessions = info["active_sessions"]
        
        signal = 0.0
        reasoning = ""
        
        if "LONDON_OPEN" in sessions:
            # Detectar se estamos manipulando o range asiático (Judas Swing)
            # (Requereria dados históricos do dia, simulamos bias por volatilidade)
            signal = 0.2 # Bias de expansão comum em Londres
            reasoning = "London Expansion Bias"
        
        return AgentSignal(self.name, signal, 0.4, reasoning, self.weight)

class TBSAgent(BaseAgent):
    """
    Agente TBS (Trend Bias System).
    Combina multi-timeframe structural breakdown (M15 vs M5 vs M1).
    Foca no alinhamento de intenção direcional e quebras de padrão.
    """

    def __init__(self, weight: float = 1.7):
        super().__init__("TBSAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        m15_candles = snapshot.candles.get("M15")
        m5_candles = snapshot.candles.get("M5")
        
        if not m15_candles or not m5_candles:
            return None
            
        m15_closes = m15_candles["close"]
        m5_closes = m5_candles["close"]
        
        # Alinhamento de Tendência
        m15_dir = 1 if m15_closes[-1] > m15_closes[-5] else -1
        m5_dir = 1 if m5_closes[-1] > m5_closes[-3] else -1
        
        signal = 0.0
        confidence = 0.0
        
        if m15_dir == m5_dir:
            signal = 0.85 * m15_dir
            confidence = 0.8
            reasoning = "MTF Trend Alignment (M15/M5)"
        else:
            signal = 0.0
            confidence = 0.2
            reasoning = "MTF Structural Conflict"
            
        return AgentSignal(self.name, signal, confidence, reasoning, self.weight)
