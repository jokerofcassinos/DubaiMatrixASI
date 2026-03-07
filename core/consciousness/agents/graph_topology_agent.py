"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — GRAPH TOPOLOGY AGENT                       ║
║     Analisa o livro de ofertas como um grafo de liquidez (LGNN)             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from typing import Optional
import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal
from cpp.asi_bridge import CPP_CORE

class GraphTopologyAgent(BaseAgent):
    """
    Agente que consome métricas de Grafo de Liquidez via C++.
    Identifica "Avalanche Risk" através de centralidade de autovetor e desequilíbrio.
    """

    def __init__(self, weight=1.4):
        super().__init__("GraphTopology", weight=weight)
        self.needs_orderflow = True

    def analyze(self, snapshot, orderflow_analysis=None, **kwargs) -> Optional[AgentSignal]:
        # 1. Obter dados do book
        book = snapshot.book
        if not book or not book.get('bids') or not book.get('asks'):
            return None

        # Concatenar bids e asks para o grafo (extrair price e volume)
        bids = np.array([[b['price'], b['volume']] for b in book['bids']]) if book['bids'] else np.empty((0, 2))
        asks = np.array([[a['price'], a['volume']] for a in book['asks']]) if book['asks'] else np.empty((0, 2))
        
        if len(bids) == 0 or len(asks) == 0:
            return None
        
        # O C++ espera ticks brutos para calcular arestas de velocidade
        # Para fins de snapshot, usamos os últimos 50 ticks se disponíveis
        ticks = kwargs.get('ticks', [])
        
        # 2. Chamar motor C++
        lgnn = CPP_CORE.calculate_lgnn(ticks, bids[:, 0], bids[:, 1]) # Simplificado para teste
        
        if not lgnn:
            return None
            
        risk = lgnn.get('avalanche_risk', 0.0)
        centrality = lgnn.get('global_centrality', 0.0)
        
        # 3. Gerar sinal baseado em Risco de Avalanche e Centralidade
        # Avalanche positiva (centralidade vendedora sendo rompida) = BUY
        # Avalanche negativa (centralidade compradora sendo rompida) = SELL
        
        signal = 0.0
        confidence = abs(risk)
        
        if centrality > 0.05: # Pressão compradora no grafo
            signal = 1.0
        elif centrality < -0.05: # Pressão vendedora no grafo
            signal = -1.0
            
        # Se o risco de avalanche for extremo (>0.8), aumentamos a confiança
        if risk > 0.8:
            confidence = min(1.0, confidence * 1.2)

        return AgentSignal(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=f"AvalancheRisk: {risk:.2f} | GlobalCentrality: {centrality:.3f} | Clusters: {len(lgnn.get('clusters', []))}"
        )
