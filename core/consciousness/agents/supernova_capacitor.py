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
    def __init__(self, weight=3.0):
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

        # PHASE 47: Refined Supernova Ignition
        # Se a velocidade de agressão é alta (>30 ticks/sec) 
        # MAS o spread está comprimido, a explosão é iminente.
        if tick_velocity > 30.0 and micro_spread <= (snapshot.symbol_info.get('point', 0.01) * 3):
            
            delta = orderflow_analysis.get('delta', 0.0)
            
            # Detecção de desequilíbrio cumulativo (Order Flow Imbalance)
            if delta > 75.0:
                signal = 1.0
                confidence = 0.95
                reasoning = f"SUPERNOVA IGNITION: Bullish (v={tick_velocity:.1f} d={delta:.1f})"
            elif delta < -75.0:
                signal = -1.0
                confidence = 0.95
                reasoning = f"SUPERNOVA IGNITION: Bearish (v={tick_velocity:.1f} d={delta:.1f})"
            elif tick_velocity > 60.0:
                # [V-REVERSAL DETECT] Se o preço está parado mas os ticks explodiram, 
                # seguimos a direção da última vela HFT
                hft_dir = 1.0 if delta > 0 else -1.0
                signal = hft_dir * 0.8
                confidence = 0.90
                reasoning = f"SUPERNOVA V-PULSE: High Velocity Pulse ({tick_velocity:.1f} t/s)"
                
        return AgentSignal(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning
        )
