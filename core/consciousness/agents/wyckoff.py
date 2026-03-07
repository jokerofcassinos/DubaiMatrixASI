"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                DUBAI MATRIX ASI — WYCKOFF STRUCTURAL AGENT                  ║
║       Classificação de fases: Acumulação, Distribuição, Reacumulação        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal
from utils.decorators import catch_and_log

class WyckoffStructuralAgent(BaseAgent):
    """
    Agente Wyckoff Matrix.
    Identifica ciclos de mercado baseados em Supply/Demand e esforço vs resultado.
    Eventos-chave: SC (Selling Climax), AR (Automatic Rally), ST (Secondary Test), 
    Spring (Armadilha de fundo), LPS (Last Point of Support).
    """

    def __init__(self, weight: float = 1.8):
        super().__init__("WyckoffMatrix", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles = snapshot.candles.get("M15")
        if not candles or len(candles["close"]) < 50:
            return None

        # 1. Decomposição de Ciclo
        # (Lógica simplificada para detecção de Spring e Upthrust)
        closes = candles["close"]
        lows = candles["low"]
        highs = candles["high"]
        volumes = candles["tick_volume"]

        # Detectar Spring (Fase C)
        # Preço quebra o suporte recente mas fecha dentro da lateralização com volume alto
        last_closes = closes[-20:]
        support = np.min(last_closes[:-1])
        resistance = np.max(last_closes[:-1])
        
        signal = 0.0
        reasoning = ""
        
        # SPRING DETECTOR
        if lows[-1] < support and closes[-1] > support:
            # Rejeição de fundo violenta (Mola de Wyckoff)
            vol_spike = volumes[-1] > np.mean(volumes[-20:]) * 1.5
            if vol_spike:
                signal = 0.9
                reasoning = "⚡ WYCKOFF_SPRING (Phase C) Detected"
        
        # UPTHRUST DETECTOR (UTAD)
        elif highs[-1] > resistance and closes[-1] < resistance:
            vol_spike = volumes[-1] > np.mean(volumes[-20:]) * 1.5
            if vol_spike:
                signal = -0.9
                reasoning = "⚠️ WYCKOFF_UPTHRUST (UTAD) Detected"

        # 2. Esforço vs Resultado
        # Volume alto sem movimento proporcional
        price_spread = abs(closes[-1] - closes[-2])
        vol_norm = volumes[-1] / (np.mean(volumes[-20:]) + 1e-10)
        
        if vol_norm > 2.0 and price_spread < np.mean(np.abs(np.diff(closes[-20:]))):
             # Esforço (volume) alto, Resultado (preço) baixo -> Absorção / Reversão Iminente
             if signal == 0: 
                 signal = -0.5 if closes[-1] > closes[-2] else 0.5
                 reasoning += " | Divergence: Effort/Result"

        confidence = 0.7 if abs(signal) > 0.5 else 0.2
        
        return AgentSignal(
            agent_name=self.name,
            signal=float(signal),
            confidence=float(confidence),
            reasoning=reasoning,
            weight=self.weight
        )
