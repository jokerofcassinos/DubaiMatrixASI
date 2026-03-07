"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                DUBAI MATRIX ASI — PRESSURE MATRIX AGENT                     ║
║       Sintetização multi-dimensional de pressão de mercado                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal
from utils.decorators import catch_and_log

class PressureMatrixAgent(BaseAgent):
    """
    Agente de Pressão Matriz.
    Analisa a convergência entre fluxo de ticks, book de ofertas e spread.
    Identifica divergências de pressão (Preço vs Volume).
    """

    def __init__(self, weight: float = 1.0):
        super().__init__("PressureMatrix", weight)
        self.needs_orderflow = True

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, orderflow_analysis: dict = None, **kwargs) -> AgentSignal:
        if not orderflow_analysis:
            return None

        # 1. Pressão de Ticks (Delta + Imbalance)
        delta_signal = orderflow_analysis.get("signal", 0.0)
        imbalance = orderflow_analysis.get("imbalance", 0.0)
        
        # 2. Pressão de Book
        book_imbalance = orderflow_analysis.get("book_imbalance", 0.0)
        
        # 3. Pressão de Velocidade/Cinemática
        velocity = orderflow_analysis.get("tick_velocity", 0.0)
        velocity_norm = np.tanh(velocity / 10.0) if velocity > 0 else 0.0
        
        # 4. Detecção de Divergência de Pressão
        # Se o preço está subindo mas a pressão (delta/imbalance) é negativa (ou vice-versa)
        price_change = 0.0
        candles = snapshot.candles.get("M1")
        if candles and len(candles["close"]) > 1:
            price_change = (candles["close"][-1] - candles["close"][-2]) / candles["close"][-2]
        
        pressure_sum = (delta_signal * 0.4) + (imbalance * 0.3) + (book_imbalance * 0.3)
        
        divergence_bonus = 0.0
        if price_change > 0 and pressure_sum < -0.3:
            # Preço sobe mas pressão é vendedora forte (Divergência Bearish)
            divergence_bonus = -0.2
        elif price_change < 0 and pressure_sum > 0.3:
            # Preço cai mas pressão é compradora forte (Divergência Bullish)
            divergence_bonus = 0.2

        final_signal = np.clip(pressure_sum + divergence_bonus, -1.0, 1.0)
        
        # Confiança baseada na intensidade da velocidade e volume climax
        climax = orderflow_analysis.get("volume_climax", False)
        confidence = 0.5 + (0.2 if climax else 0.0) + (abs(velocity_norm) * 0.3)
        confidence = min(0.95, confidence)

        return AgentSignal(
            agent_name=self.name,
            signal=float(final_signal),
            confidence=float(confidence),
            reasoning=f"FlowSignal={delta_signal:.2f}, BookImb={book_imbalance:.2f}, Divergence={divergence_bonus:.2f}",
            weight=self.weight
        )
