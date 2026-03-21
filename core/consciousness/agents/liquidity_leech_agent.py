"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                DUBAI MATRIX ASI — LIQUIDITY LEECH AGENT                      ║
║         Phase Ω-Transcendence: Parasitismo Simbiótico de Whale Walls       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import Dict, Optional
from core.consciousness.agents.base import BaseAgent, AgentSignal
from market.data_engine import MarketSnapshot
from utils.logger import log

class LiquidityLeechAgent(BaseAgent):
    """
    Agente Predator-Symbiotic.
    Detecta 'Institutional Spoofing' e 'Icebergs' no L2.
    Sinaliza para entrar 'na carona' (leeching) de ordens institucionais massivas.
    """

    def __init__(self):
        super().__init__(name="LiquidityLeechAgent")
        self.priority = 1.0 # Alta prioridade na convergência

    def analyze(self, snapshot: MarketSnapshot, flow_analysis: Dict, **kwargs) -> AgentSignal:
        """
        Analisa a boundary entre o bulk do book e o deslocamento de preço.
        """
        book = snapshot.book
        if not book or not book.get("bids") or not book.get("asks"):
            return self._idle()

        # 1. Identificar Walls (Spoofing detection logic)
        bids = book.get('bids', [])
        asks = book.get('asks', [])
        
        if not bids or not asks:
            return self._idle()

        avg_bid_vol = np.mean([b[1] for b in bids[:10]])
        avg_ask_vol = np.mean([a[1] for a in asks[:10]])
        
        # Detectar anomalia de volume (Wall) nos primeiros níveis
        bid_wall = any(b[1] > avg_bid_vol * 15 for b in bids[:5])
        ask_wall = any(a[1] > avg_ask_vol * 15 for a in asks[:5])
        
        # 2. Verificar Inércia de Preço (Iceberg detection)
        # Se tem muita agressão (delta) mas o preço não rompe a wall
        flow_delta = flow_analysis.get("delta", 0.0)
        
        signal_val = 0.0
        confidence = 0.0
        reasoning = ""

        if bid_wall and flow_delta < -500: # Muita venda batendo mas a wall segura
            signal_val = 0.85 # BUY (Leech behind the buyer wall)
            confidence = 0.90
            reasoning = "Symbiotic Leech: Institutional BID WALL protecting price despite delta pressure."
        elif ask_wall and flow_delta > 500: # Muita compra batendo mas a wall segura
            signal_val = -0.85 # SELL (Leech behind the seller wall)
            confidence = 0.90
            reasoning = "Symbiotic Leech: Institutional ASK WALL absorbing aggressive buys."
        else:
            return self._idle()

        return AgentSignal(
            agent_name=self.name,
            signal=signal_val,
            confidence=confidence,
            weight=1.5,
            reasoning=reasoning,
            metadata={"bid_wall": bid_wall, "ask_wall": ask_wall}
        )

    def _idle(self):
        return AgentSignal(self.name, 0.0, 0.5, "No institutional walls detected.", 1.0)
