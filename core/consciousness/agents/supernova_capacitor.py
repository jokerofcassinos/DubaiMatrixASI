"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — SUPERNOVA CAPACITOR AGENT                    ║
║     Volatilidade Preditiva: Antecipa o rompimento através da micro-compressão║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import numpy as np
from typing import Optional
from core.consciousness.agents.base import BaseAgent, AgentSignal

class SupernovaCapacitorAgent(BaseAgent):
    """
    O Capacitor Supernova.
    Identifica "Fissuras de Volatilidade". Quando o preço congela num spread microscópico
    sob alta densidade de ticks, a panela de pressão vai explodir.
    Diferente do ATR (que sobe depois da explosão), o Capacitor atinge 1.0 ANTES da explosão.
    """
    def __init__(self, weight=2.5):
        super().__init__("SupernovaCapacitor", weight=weight)
        self.needs_orderflow = True

    def analyze(self, snapshot, orderflow_analysis=None, **kwargs) -> Optional[AgentSignal]:
        if not orderflow_analysis:
            return None

        # Velocidade do mercado (Ticks por segundo)
        tick_velocity = orderflow_analysis.get('tick_velocity', 0)
        
        # O OrderBook depth
        book = snapshot.book
        if not book or not book.get('bids') or not book.get('asks'):
            return None
            
        bids = book['bids']
        asks = book['asks']
        
        best_bid = bids[0]['price'] if isinstance(bids[0], dict) else bids[0][0]
        best_ask = asks[0]['price'] if isinstance(asks[0], dict) else asks[0][0]
        
        micro_spread = best_ask - best_bid
        
        signal = 0.0
        confidence = 0.0
        reasoning = "Normal Pressure"

        # Se a velocidade de agressão é insanamente alta (>50 ticks/sec)
        # MAS o spread não sai do lugar (micro_spread mínimo histórico),
        # estamos no olho da Fissura de Volatilidade.
        if tick_velocity > 40.0 and micro_spread <= (snapshot.symbol_info.get('point', 0.01) * 2):
            
            # Qual o lado que está "empurrando" a porta fechada?
            delta = orderflow_analysis.get('delta', 0.0)
            
            if delta > 100.0:
                # Compradores empurrando, mas a parede (limit sell) não cede. 
                # Quando a parede quebrar, o preço entra em Supernova pra cima.
                signal = 1.0
                confidence = 0.95
                reasoning = "SUPERNOVA CAPACITOR: Bullish Micro-Compression"
            elif delta < -100.0:
                signal = -1.0
                confidence = 0.95
                reasoning = "SUPERNOVA CAPACITOR: Bearish Micro-Compression"
                
        return AgentSignal(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning
        )
