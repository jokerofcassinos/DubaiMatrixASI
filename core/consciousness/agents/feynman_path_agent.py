"""
╔══════════════════════════════════════════════════════════════════════════════╗
║             DUBAI MATRIX ASI — FEYNMAN PATH AGENT (PHASE Ω-ONE)              ║
║     Agente que modela a evolução de preço como Propagador Quântico.          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import Optional
from core.consciousness.agents.base import BaseAgent, AgentSignal
from cpp.asi_bridge import CPP_CORE

class FeynmanPathAgent(BaseAgent):
    """
    Agente baseado em Integrais de Trajetória de Feynman.
    Calcula a probabilidade de transição para alvos de preço baseados em volatilidade.
    Identifica muros de liquidez via interferência quântica.
    """

    def __init__(self, weight=2.8):
        super().__init__("FeynmanPath", weight=weight)
        self.needs_orderflow = False # Focado em trajetórias de preço

    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        if not hasattr(snapshot, 'close') or snapshot.close is None or len(snapshot.close) < 50:
            return None

        closes = snapshot.close[-50:]
        current_price = float(closes[-1])
        
        # ATR para definir alvos de probabilidade
        atr = snapshot.atr if hasattr(snapshot, 'atr') and snapshot.atr > 0 else (np.max(closes) - np.min(closes)) * 0.1
        if atr <= 0: atr = current_price * 0.001
        
        # 1. Definir alvos em potencial (Bullish e Bearish)
        target_bull = current_price + (atr * 1.5)
        target_bear = current_price - (atr * 1.5)
        
        # 2. Calcular Propagadores via C++
        # time_horizon em segundos (ex: 60s para scalping M1)
        # liquidity_friction mapeado da agressividade ou volume
        friction = 1.0 
        
        prop_bull = CPP_CORE.calculate_feynman_path(closes, target_bull, 60.0, friction)
        prop_bear = CPP_CORE.calculate_feynman_path(closes, target_bear, 60.0, friction)
        
        if not prop_bull or not prop_bear:
            return None

        # 3. Análise de Interferência
        bull_score = prop_bull['interference']
        bear_score = prop_bear['interference']
        
        total_score = bull_score + bear_score
        if total_score <= 1e-9: return None
        
        # Calculamos o sinal pela assimetria das amplitudes
        signal = (bull_score - bear_score) / total_score
        
        # A confiança é a magnitude da maior interferência detectada
        confidence = np.clip(max(bull_score, bear_score), 0.1, 0.95)
        
        reasoning = f"Quantum Bias: {signal:+.4f} | Peak Inter: {max(bull_score, bear_score):.3f}"
        
        return AgentSignal(
            agent_name=self.name,
            signal=float(signal),
            confidence=float(confidence),
            reasoning=reasoning
        )
