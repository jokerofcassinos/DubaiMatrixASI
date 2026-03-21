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
        # [Phase Ω-Sensory] Pre-allocar p/ evitar O(N) copy do vstack
        self.database = np.zeros((max_episodes, vector_dim), dtype=np.float64)
        self.metadata = [None] * max_episodes
        self.cursor = 0
        self.is_full = False

    def add_episode(self, vector: np.ndarray, outcome_data: dict):
        """Adiciona um 'episódio' (snapshot + o que aconteceu depois)."""
        if len(vector) != self.vector_dim:
            log.warning(f"⚠️ Vetor de memória com dimensão incorreta: {len(vector)} vs {self.vector_dim}")
            return

        # Inserção O(1) no slot circular
        self.database[self.cursor] = vector
        self.metadata[self.cursor] = outcome_data
        
        self.cursor += 1
        if self.cursor >= self.max_episodes:
            self.cursor = 0
            self.is_full = True

    def _get_active_db(self) -> np.ndarray:
        """Retorna apenas a parte preenchida da database."""
        if not self.is_full:
            return self.database[:self.cursor]
        return self.database

    def recall(self, query_vector: np.ndarray, top_k: int = 5) -> List[dict]:
        """Busca momentos similares no passado."""
        active_db = self._get_active_db()
        if len(active_db) == 0:
            return []

        # Usar busca C++ acelerada
        db_flat = active_db.flatten()
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
