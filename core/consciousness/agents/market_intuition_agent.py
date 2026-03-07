"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — MARKET INTUITION AGENT                     ║
║     Agente que utiliza a Memória Episódica para prever o futuro.            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import Optional
from core.consciousness.agents.base import BaseAgent, AgentSignal
from market.memory.episodic_memory import EpisodicMemory

class MarketIntuitionAgent(BaseAgent):
    """
    Agente de Intuição de Mercado (Time-Series RAG).
    Codifica o snapshot atual em um embedding e busca no passado.
    """

    def __init__(self, memory: EpisodicMemory):
        super().__init__("MarketIntuition", weight=1.8)
        self.memory = memory
        self.needs_orderflow = True

    def analyze(self, snapshot, orderflow_analysis=None, **kwargs) -> Optional[AgentSignal]:
        # 1. Gerar Embedding do Contexto Atual (Dimen=64 conforme planejado)
        # Usamos uma combinação de indicadores e métricas de orderflow normalizadas
        embedding = self._generate_embedding(snapshot, orderflow_analysis)
        
        # 2. Consultar Memória
        intuition = self.memory.get_market_intuition(embedding)
        
        bias = intuition.get("bias", 0.0)
        confidence = intuition.get("confidence", 0.0)
        
        # 3. Gerar Sinal
        signal = 0.0
        if bias > 0.0005: # Threshold de excursão positiva
            signal = 1.0
        elif bias < -0.0005:
            signal = -1.0
            
        return AgentSignal(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=f"IntuitionBias: {bias:.6f} | Confidence: {confidence:.2f} | Matches: {intuition.get('match_count')}"
        )

    def _generate_embedding(self, snapshot, flow) -> np.ndarray:
        """Codifica o snapshot em um vetor de 64 dimensões."""
        # TODO: Implementar codificação real. Por enquanto, um placeholder determinístico.
        vec = np.zeros(64, dtype=np.float64)
        
        # Inserir métricas chave nas primeiras posições
        if snapshot.indicators:
            vec[0] = snapshot.indicators.get('rsi', 50) / 100.0
            vec[1] = snapshot.indicators.get('hurst', 0.5)
            
        if flow:
            vec[2] = flow.get('order_imbalance', 0.0)
            vec[3] = flow.get('volume_climax_score', 0.0)
            
        # Adicionar ruído determinístico baseado no preço para evitar vetores zerados
        price_seed = int(snapshot.price * 10000) % 1000 / 1000.0
        vec[4:] = price_seed
        
        return vec
