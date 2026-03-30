"""
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                                 SOLÉNN                                       ║
    ║                      HMM ENGINE Ω (TRANSITION LOGIC)                         ║
    ║                                                                              ║
    ║  "O mercado é uma sequência de estados ocultos. A transição não é            ║
    ║   aleatória — ela é regida por uma matriz de densidade de probabilidade."      ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
"""

import torch
import numpy as np
from typing import Tuple, Dict, Any, List

class HmmEngine:
    """
    Motor de Markov Oculto (HMM) de Alta Performance Ω. (Ω-4)
    Framework 3-6-9: Fase 6(Ω-31) - Conceito 1.2 (PhD Level).
    """
    
    def __init__(self, n_states: int = 12, latent_dim: int = 12):
        self.n_states = n_states
        self.latent_dim = latent_dim
        
        # [Ω-V6.2.1] Transition Matrix (A) - P(S_t | S_{t-1})
        # Inicialização uniforme com leve perturbação p/ quebra de simetria (Lei Ω-36)
        self.A = torch.full((n_states, n_states), 1.0 / n_states)
        self.A += torch.randn_like(self.A) * 0.01
        self.A = torch.softmax(self.A, dim=1) # Normalização de probabilidade
        
        # [Ω-V6.2.2] Emission Parameters (Gaussian Mixture per State)
        self.means = torch.randn(n_states, latent_dim) * 0.1
        self.covs = torch.ones(n_states, latent_dim) * 0.5
        
        # [Ω-V6.2.6] Initial State Prior (π)
        self.pi = torch.full((n_states,), 1.0 / n_states)
        
        self.history_len = 500
        self._latent_history = []

    # [Ω-V6.2.3] Viterbi Path Decoding (Reconstrução Histórica)
    def viterbi(self, observations: torch.Tensor) -> List[int]:
        """Algoritmo de decodificação do caminho mais provável."""
        T = observations.shape[0]
        N = self.n_states
        
        viterbi_table = torch.zeros((T, N))
        backpointer = torch.zeros((T, N), dtype=torch.long)
        
        # Inicialização (t=0)
        emissions = self._log_gaussian_pdf(observations[0], self.means, self.covs)
        viterbi_table[0] = torch.log(self.pi) + emissions
        
        # Iteração (t=1..T-1)
        for t in range(1, T):
            emissions = self._log_gaussian_pdf(observations[t], self.means, self.covs)
            for s in range(N):
                trans_probs = viterbi_table[t-1] + torch.log(self.A[:, s])
                viterbi_table[t, s], backpointer[t, s] = torch.max(trans_probs, dim=0)
                viterbi_table[t, s] += emissions[s]
                
        # Backtracking
        best_path = [int(torch.argmax(viterbi_table[-1]))]
        for t in range(T-1, 0, -1):
            best_path.insert(0, int(backpointer[t, best_path[0]]))
            
        return best_path

    # [Ω-V6.2.4] Forward-Backward Algorithm (Posterior Inference)
    def get_posterior(self, observations: torch.Tensor) -> torch.Tensor:
        """Calcula γ_t(i) = P(S_t = i | O)."""
        T = observations.shape[0]
        N = self.n_states
        
        # Forward pass (α)
        alpha = torch.zeros((T, N))
        alpha[0] = torch.log(self.pi) + self._log_gaussian_pdf(observations[0], self.means, self.covs)
        for t in range(1, T):
            for s in range(N):
                alpha[t, s] = torch.logsumexp(alpha[t-1] + torch.log(self.A[:, s]), dim=0) + \
                              self._log_gaussian_pdf(observations[t], self.means, self.covs)[s]
        
        # Backward pass (β)
        beta = torch.zeros((T, N))
        for t in range(T-2, -1, -1):
            for s in range(N):
                emissions_next = self._log_gaussian_pdf(observations[t+1], self.means, self.covs)
                beta[t, s] = torch.logsumexp(torch.log(self.A[s, :]) + emissions_next + beta[t+1], dim=0)
                
        # Computing γ (normalize in log space)
        gamma = alpha + beta
        gamma = torch.exp(gamma - torch.logsumexp(gamma, dim=1, keepdim=True))
        return gamma

    def _log_gaussian_pdf(self, x: torch.Tensor, mu: torch.Tensor, sigma: torch.Tensor) -> torch.Tensor:
        """Cálculo do log-PDF multivariado diagonal (Lei Ω-30)."""
        log_2pi = np.log(2 * np.pi)
        # Assumindo covariância diagonal para latência micro-atômica
        term = -0.5 * (log_2pi + torch.log(sigma) + (x - mu).pow(2) / (sigma + 1e-9))
        return torch.sum(term, dim=1)

    # [Ω-V6.2.7] Adaptation Logic (Incremental Update)
    def update_parameters(self, gamma: torch.Tensor, observations: torch.Tensor):
        """Atualiza médias e covariâncias baseado no feedback bayesiano."""
        # Weighted mean update
        weights = gamma.sum(dim=0).unsqueeze(1) # [N, 1]
        new_means = (gamma.t() @ observations) / (weights + 1e-9)
        self.means = 0.95 * self.means + 0.05 * new_means # EMA smoothing
