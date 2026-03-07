"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — BLACK SWAN AGENT (TDA)                     ║
║     Agente que utiliza Topologia de Dados para prever crashes.             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import Optional, Dict
from core.consciousness.agents.base import BaseAgent, AgentSignal
from cpp.asi_bridge import CPP_CORE

class BlackSwanAgent(BaseAgent):
    """
    Agente de Detecção de Cisnes Negros via TDA.
    Monitora 'buracos' na liquidez e instabilidade geométrica.
    """

    def __init__(self, weight=2.5):
        super().__init__("BlackSwan", weight=weight) # Peso crítico
        self.needs_orderflow = True

    def analyze(self, snapshot, orderflow_analysis=None, **kwargs) -> Optional[AgentSignal]:
        if not snapshot.book:
            return None

        # 1. Extrair Point Cloud do Book (Bids e Asks combinados)
        bids = np.array([p[0] for p in snapshot.book.get('bids', [])], dtype=np.float64)
        bid_vols = np.array([p[1] for p in snapshot.book.get('bids', [])], dtype=np.float64)
        asks = np.array([p[0] for p in snapshot.book.get('asks', [])], dtype=np.float64)
        ask_vols = np.array([p[1] for p in snapshot.book.get('asks', [])], dtype=np.float64)

        if len(bids) < 5 or len(asks) < 5:
            return None

        prices = np.concatenate([bids, asks])
        volumes = np.concatenate([bid_vols, ask_vols])

        # 2. Calcular Topologia via C++
        topo = CPP_CORE.calculate_topology(prices, volumes)
        if not topo:
            return None

        # 3. Gerar Sinal
        signal = 0.0
        confidence = 0.0
        
        # Se houver buracos topológicos massivos, o mercado está instável
        if topo['unstable']:
            signal = -1.0 # Veto/Alerta de venda ou saída
            confidence = min(1.0, topo['betti_1'] * 0.2)
            reasoning = f"GEOMETRIC_COLLAPSE | Betti1: {topo['betti_1']} | MaxHole: {topo['max_hole']:.2f}"
        else:
            # Estabilidade geométrica favorece a permanência em regime atual
            signal = 0.0
            confidence = 0.5
            reasoning = f"GeometricStability: {1.0 - topo['entropy']:.2f} | Cohesion: {topo['betti_0']}"

        return AgentSignal(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning
        )
