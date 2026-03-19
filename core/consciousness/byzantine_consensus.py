"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — BYZANTINE CONSENSUS                        ║
║     Consenso de Tolerância a Falhas Bizantinas para o Swarm.               ║
║                                                                              ║
║  Modula os pesos dos agentes baseando-se no Brier Score (Precisão           ║
║  Probabilística) retroativa. Generais traidores perdem autoridade.          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
import time
from typing import List, Dict

from utils.logger import log

class ByzantineConsensusManager:
    def __init__(self, agents_count: int):
        self.brier_scores = np.zeros(agents_count)
        self.penalties = np.ones(agents_count) # 1.0 = Sem penalidade
        self.history = [] # Lista de (timestamp, signals, actual_outcome)

    def update_consensus(self, agents_signals: List[float], actual_outcome: float):
        """
        Atualiza os scores de Brier e aplica penalidades aos Generais Traidores.
        agents_signals: Lista de sinais [-1, 0, 1] de cada agente.
        actual_outcome: Resultado real observado [-1, 0, 1].
        """
        if len(agents_signals) != len(self.brier_scores):
            # Redimensionar se o swarm cresceu
            new_scores = np.zeros(len(agents_signals))
            new_penalties = np.ones(len(agents_signals))
            min_len = min(len(agents_signals), len(self.brier_scores))
            new_scores[:min_len] = self.brier_scores[:min_len]
            new_penalties[:min_len] = self.penalties[:min_len]
            self.brier_scores = new_scores
            self.penalties = new_penalties

        # Brier Score = (Forecast - Actual)^2
        # Como o sinal é [-1, 1], normalizamos para [0, 1] para o cálculo
        forecasts = (np.array(agents_signals) + 1.0) / 2.0
        outcome = (actual_outcome + 1.0) / 2.0
        
        current_errors = (forecasts - outcome)**2
        
        # Média móvel exponencial do erro
        # [Phase Ω-PhD-15] Alpha aumentado para 0.15 para recuperação mais rápida de regimes transitórios
        alpha = 0.15
        self.brier_scores = (1 - alpha) * self.brier_scores + alpha * current_errors
        
        # Penalidade = 1.0 - Brier Score (Quanto maior o erro, maior a penalidade)
        # Se BS = 0 (perfeito), penalidade = 1.0 (peso total)
        # Se BS = 1 (errado), penalidade = 0.1 (mínimo)
        self.penalties = np.clip(1.0 - self.brier_scores, 0.1, 1.0)
        
        # [Phase Ω-PhD-15] Graceful Recovery: Pequeno boost para quem está participando e não está errando
        # Agentes com erro muito baixo no ciclo atual ganham um bônus de recuperação de fôlego
        recovery_mask = (current_errors < 0.05) & (self.penalties < 0.95)
        self.penalties[recovery_mask] = np.minimum(1.0, self.penalties[recovery_mask] + 0.01)
        
        traitor_count = np.sum(self.penalties < 0.5)
        if traitor_count > 0:
            log.warning(f"⚔️ Byzantine: {traitor_count} Generais Traidores identificados e penalizados.")

    def get_modulated_weights(self, base_weights: np.ndarray) -> np.ndarray:
        """Retorna os pesos dos agentes multiplicados pela penalidade de consenso."""
        return base_weights * self.penalties
