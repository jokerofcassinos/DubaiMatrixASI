"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — THERMODYNAMIC AGENT                        ║
║     Analisa o mercado como um sistema físico de entropia e pressão          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from typing import Optional
import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal
from cpp.asi_bridge import CPP_CORE

class ThermodynamicAgent(BaseAgent):
    """
    Agente que consome métricas de Entropia de Shannon e Termodinâmica via C++.
    Identifica estados críticos de compressão de volume e pressão direcional.
    """

    def __init__(self, weight=1.3):
        super().__init__("Thermodynamic", weight=weight)
        self.needs_orderflow = False

    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        book = snapshot.book
        if not book or not book.get('bids') or not book.get('asks'):
            return None

        bids = np.array([[b['price'], b['volume']] for b in book['bids']]) if book['bids'] else np.empty((0, 2))
        asks = np.array([[a['price'], a['volume']] for a in book['asks']]) if book['asks'] else np.empty((0, 2))

        if len(bids) == 0 or len(asks) == 0:
            return None
        
        # 1. Chamar motor C++
        thermo = CPP_CORE.calculate_thermodynamics(
            bids[:, 0], bids[:, 1], 
            asks[:, 0], asks[:, 1]
        )
        
        if not thermo:
            return None
            
        entropy = thermo.get('entropy', 0.0)
        pressure = thermo.get('pressure', 0.0)
        is_critical = thermo.get('is_critical', False)
        
        # 2. Lógica de sinal:
        # Pressão positiva (Bids > Asks) + Baixa Entropia (Concentração) = BUY
        # Pressão negativa (Asks > Bids) + Baixa Entropia (Concentração) = SELL
        
        signal = 0.0
        # Confiança é inversamente proporcional à entropia (menos desordem = mais certeza)
        confidence = max(0.0, 1.0 - (entropy / 10.0)) 
        
        # Se estamos em estado crítico, a confiança explode
        if is_critical:
            confidence = min(1.0, confidence * 1.5)
            
        # Determinar direção pela pressão
        # Nota: O motor C++ calcula pressão como abs(diff), 
        # aqui precisamos saber a direção real.
        bid_vol = np.sum(bids[:, 1])
        ask_vol = np.sum(asks[:, 1])
        
        if bid_vol > ask_vol:
            signal = 1.0
        else:
            signal = -1.0
            
        return AgentSignal(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=f"Entropy: {entropy:.2f} | Pressure: {pressure:.2f} | Critical: {is_critical}"
        )
