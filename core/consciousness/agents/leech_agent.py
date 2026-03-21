"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — LIQUIDITY LEECH AGENT                        ║
║     Parasitismo Simbiótico: Usa Baleias Institucionais como Escudo           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import Optional
from core.consciousness.agents.base import BaseAgent, AgentSignal
from utils.logger import log

class LiquidityLeechAgent(BaseAgent):
    """
    Agente Sanguessuga (Parasitismo Institucional).
    Lê os avisos do ShadowPredator. Se uma baleia está spoofando pesadamente
    ou ancorada num iceberg (criando um muro no book), o LeechAgent vira a favor
    do muro, operando com risco nulo usando o lote institucional como escudo.
    """

    def __init__(self, predator_engine, weight=2.0):
        super().__init__("LiquidityLeech", weight=weight)
        self.predator_engine = predator_engine
        self.needs_orderflow = True

    def analyze(self, snapshot, orderflow_analysis=None, **kwargs) -> Optional[AgentSignal]:
        if not self.predator_engine or not orderflow_analysis:
            return None

        # Puxamos o último diagnóstico da Engine Predatória
        predator_sig = self.predator_engine.analyze_signature(snapshot, orderflow_analysis)
        
        signal = 0.0
        confidence = 0.0
        reasoning = "Sem hospedeiro detectado"
        
        if predator_sig and predator_sig.get("is_manipulated", False):
            # Há uma baleia ativa. Qual o tipo de manipulação?
            if "Spoofing" in predator_sig.get("type", ""):
                # Spoofing cria uma "parede fantasma". O preço FOGE da parede.
                # Se a parede está no BID (Buy wall falsa), o preço vai SUBIR (front-running retail)
                # Nós sugamos a subida rápida antes da parede sumir.
                if not snapshot.book:
                    return AgentSignal(self.name, 0.0, 0.0, "NO_BOOK_DATA", self.weight)

                bids_vol = sum([b['volume'] if isinstance(b, dict) else b[1] for b in snapshot.book.get('bids', [])])
                asks_vol = sum([a['volume'] if isinstance(a, dict) else a[1] for a in snapshot.book.get('asks', [])])
                
                if bids_vol > asks_vol * 3.0: # Muro colossal no Bid
                    signal = 1.0
                    confidence = 0.95
                    reasoning = "Leeching on Bullish Spoof Wall"
                elif asks_vol > bids_vol * 3.0:
                    signal = -1.0
                    confidence = 0.95
                    reasoning = "Leeching on Bearish Spoof Wall"

        return AgentSignal(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning
        )
