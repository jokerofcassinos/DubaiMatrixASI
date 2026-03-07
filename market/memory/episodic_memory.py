"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — EPISODIC MEMORY                            ║
║     Banco de dados vetorial em memória para "Intuição" de mercado.          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
import time
import os
import json
from typing import List, Tuple, Optional
from cpp.asi_bridge import CPP_CORE
from utils.logger import log

class EpisodicMemory:
    """
    Sistema de Memória Episódica (Time-Series RAG).
    Armazena snapshots passados como vetores e permite busca por similaridade.
    """

    def __init__(self, vector_dim: int = 64, max_episodes: int = 10000):
        self.vector_dim = vector_dim
        self.max_episodes = max_episodes
        self.database = np.zeros((0, vector_dim), dtype=np.float64)
        self.metadata = [] # Lista de dicts com o outcome real do episódio

    def add_episode(self, vector: np.ndarray, outcome_data: dict):
        """Adiciona um 'episódio' (snapshot + o que aconteceu depois)."""
        if len(vector) != self.vector_dim:
            log.warning(f"⚠️ Vetor de memória com dimensão incorreta: {len(vector)} vs {self.vector_dim}")
            return

        # Concatenar novo vetor
        self.database = np.vstack([self.database, vector])
        self.metadata.append(outcome_data)

        # Manter limite
        if len(self.database) > self.max_episodes:
            self.database = self.database[-self.max_episodes:]
            self.metadata = self.metadata[-self.max_episodes:]

    def recall(self, query_vector: np.ndarray, top_k: int = 5) -> List[dict]:
        """Busca momentos similares no passado."""
        if len(self.database) == 0:
            return []

        # Usar busca C++ acelerada
        db_flat = self.database.flatten()
        similarities, indices = CPP_CORE.vector_search(query_vector, db_flat, top_k)

        results = []
        if similarities is not None:
            for sim, idx in zip(similarities, indices):
                meta = self.metadata[idx].copy()
                meta['similarity'] = sim
                results.append(meta)
        
        return results

    def get_market_intuition(self, current_vector: np.ndarray) -> dict:
        """
        Gera uma "intuição" baseada na média dos outcomes dos top k episódios similares.
        """
        matches = self.recall(current_vector, top_k=10)
        if not matches:
            return {"bias": 0.0, "confidence": 0.0}

        total_bias = 0.0
        weights_sum = 0.0

        for m in matches:
            # Pesar pela similaridade
            weight = m['similarity']
            price_change = m.get('next_excursion', 0.0)
            total_bias += price_change * weight
            weights_sum += weight

        return {
            "bias": total_bias / (weights_sum + 0.0001),
            "confidence": np.mean([m['similarity'] for m in matches]),
            "match_count": len(matches)
        }
