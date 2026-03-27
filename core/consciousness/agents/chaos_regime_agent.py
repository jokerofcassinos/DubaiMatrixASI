"""
╔══════════════════════════════════════════════════════════════════════════════╗
║             DUBAI MATRIX ASI — CHAOS REGIME AGENT (PHASE Ω-ONE)              ║
║     Agente que detecta o Horizonte de Lyapunov e previsibilidade.            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import Optional
from core.consciousness.agents.base import BaseAgent, AgentSignal
from cpp.asi_bridge import CPP_CORE

class ChaosRegimeAgent(BaseAgent):
    """
    Agente focado na detecção de Caos Determinístico.
    Quantifica quando o mercado entra em 'Turbulência' (Horizonte de Lyapunov curto).
    Veta trades ou reduz confiança quando a previsibilidade é nula.
    """

    def __init__(self, weight=1.5):
        super().__init__("ChaosRegime", weight=weight)
        self.needs_orderflow = False

    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        if not hasattr(snapshot, 'close') or snapshot.close is None or len(snapshot.close) < 100:
            return None

        # Usamos os últimos 100 closes para análise de caos
        data = snapshot.close[-100:]
        
        # Estima sample rate
        sample_rate = 1.0 
        
        chaos = CPP_CORE.calculate_chaos(data, sample_rate)
        if not chaos:
            return None

        # 1. Avaliação de Previsibilidade
        horizon = float(chaos['horizon'])
        is_chaotic = chaos['chaotic']
        
        signal = 0.0
        confidence = 0.0
        
        if is_chaotic or horizon < 60.0:
            # Alta entropia e baixo horizonte -> Neutralizar sinais
            signal = 0.0
            confidence = 0.1 
            reasoning = f"CHAOS DETECTED | Hor: {horizon:.1f}s | Pred: NULL"
        else:
            # Mercado organizado — Não gera sinal direcional por si só
            signal = 0.0 
            confidence = 0.5
            reasoning = f"STABLE FLOW | Hor: {horizon:.1f}s | Pred: HIGH"

        return AgentSignal(
            agent_name=self.name,
            signal=float(signal),
            confidence=float(confidence),
            reasoning=reasoning
        )
