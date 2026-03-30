"""
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                                 SOLÉNN                                       ║
    ║                      REGIME DETECTOR Ω (CONSCIOUSNESS)                        ║
    ║                                                                              ║
    ║  "O regime não é um rótulo — é uma probabilidade sustentada no tempo          ║
    ║   que define a agressividade e o risco do organismo sistêmico."               ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
"""

import torch
import torch.nn.functional as F
import numpy as np
from enum import Enum
from typing import Optional, Tuple, Dict, Any, List
from collections import deque
from dataclasses import dataclass

from core.intelligence.vae_encoder import VaeEncoder
from core.intelligence.hmm_engine import HmmEngine

class MarketRegime(Enum):
    """Regimes Soberanos Ω (Ω-4 Taxonomy)."""
    TRENDING_BULL = "TRENDING_BULL"
    TRENDING_BEAR = "TRENDING_BEAR"
    RANGING_STABLE = "RANGING_STABLE"
    CHOP_NOISE = "CHOP_NOISE"
    LIQUIDITY_VOID = "LIQUIDITY_VOID"
    PARADIGM_SHIFT = "PARADIGM_SHIFT"
    UNKNOWN = "UNKNOWN"

@dataclass(frozen=True, slots=True)
class RegimeState:
    """Snapshot da Consciência de Regime (Ω-4 State)."""
    current_regime: MarketRegime
    confidence: float
    transition_prob: float
    latent_z: np.ndarray
    predicted_next: MarketRegime
    regime_id: int
    reasoning: str

class RegimeDetector:
    """
    Detector de Regime Ω: A Glândula Pineal da SOLÉNN. (Ω-4)
    Integração de HMM-VAE + TDA + Physics para consciência absoluta.
    """
    
    def __init__(self, n_states: int = 12, latent_dim: int = 12):
        self.n_states = n_states
        self._vae = VaeEncoder(input_dim=15, latent_dim=latent_dim)
        self._hmm = HmmEngine(n_states=n_states, latent_dim=latent_dim)
        
        self._current_state = 0
        self._regime_duration = 0
        self._history = deque(maxlen=200) # [Ω-1.1] Window for VAE (Price/Vol/Indics)
        
        # [Ω-V6.3.2] Leading indicators of transition
        self._csd_score = 0.0 # Critical Slowing Down

    # [Ω-V6.1.4] Context Injection
    def process_snapshot(self, snapshot: Any) -> RegimeState:
        """
        Processa um snapshot do Cortex Ω e gera a consciência de regime.
        """
        # Transformando snapshot em vetor de entrada para o Encoder [Ω-V6.1.1]
        input_vec = self._extract_features(snapshot)
        self._history.append(input_vec)
        
        if len(self._history) < 50:
             return self._default_state()

        # Step 1: VAE Encoding (Ω-6.1)
        # B x C x W (Batch x Channels x Window)
        # Garantindo janela fixa de 50 snapshots para o VAE [Ω-V6.1.1]
        history_list = list(self._history)[-50:]
        x_batch = torch.stack(history_list).t().unsqueeze(0)
        
        with torch.no_grad():
            mu, _ = self._vae.encode(x_batch)
            z = mu # Latent representation
            
        # Step 2: HMM Decoding (Ω-6.2)
        # [Ω-V6.3.1] Instant State Inference
        gamma = self._hmm.get_posterior(z)
        state_id = int(torch.argmax(gamma[-1]))
        confidence = float(gamma[-1, state_id])
        
        # Step 3: Transition Prediction (Ω-6.3)
        transition_prob = self._estimate_transition_prob(gamma)
        next_state_id = int(torch.argmax(self._hmm.A[state_id]))
        
        regime = self._map_state_to_regime(state_id, snapshot)
        predicted_next = self._map_state_to_regime(next_state_id, snapshot)
        
        # [Ω-V6.3.2] Critical Slowing Down (Cálculo de Inércia)
        self._update_csd(z)
        
        return RegimeState(
            current_regime=regime,
            confidence=confidence,
            transition_prob=transition_prob,
            latent_z=z.cpu().numpy().flatten(),
            predicted_next=predicted_next,
            regime_id=state_id,
            reasoning=f"LATENT_STATE_{state_id} CONF={confidence:.2f} CSD={self._csd_score:.2f}"
        )

    def _extract_features(self, s: Any) -> torch.Tensor:
        """Extrai 15-dim features do snapshot [Ω-V6.1.1]."""
        return torch.tensor([
            s.bid, s.ask, s.last_price, s.spread,
            s.ema_fast, s.ema_slow, s.rsi_14, s.atr_14,
            s.hurst, s.entropy, s.vol_gk, s.v_pulse,
            s.jounce, s.lorentz_factor, s.book_imbalance
        ], dtype=torch.float32)

    def _map_state_to_regime(self, state_id: int, snapshot: Any) -> MarketRegime:
        """Mapeamento dinâmico de estados latentes para taxonomias humanas Ω."""
        # Heurística inicial baseada em macro-features (Hurst/Entropy) [Ω-V6.1.8]
        if snapshot.hurst > 0.6:
             return MarketRegime.TRENDING_BULL if snapshot.ema_fast > snapshot.ema_slow else MarketRegime.TRENDING_BEAR
        if snapshot.entropy < 2.5:
             return MarketRegime.RANGING_STABLE
        if snapshot.entropy > 4.0:
             return MarketRegime.CHOP_NOISE
        return MarketRegime.UNKNOWN

    def _estimate_transition_prob(self, gamma: torch.Tensor) -> float:
        """Cálculo de incerteza transicional (Entropia local de estados)."""
        probs = gamma[-1]
        entropy = -torch.sum(probs * torch.log(probs + 1e-9))
        return float(entropy / np.log(self.n_states))

    def _update_csd(self, z: torch.Tensor):
        """[Ω-V6.3.2] Medição de desaceleração de transição."""
        # Autocorrelação de lag 1 do vetor latente (CSD precursor)
        if hasattr(self, '_last_z'):
             corr = F.cosine_similarity(z, self._last_z)
             self._csd_score = 0.9 * self._csd_score + 0.1 * (1.0 - float(corr))
        self._last_z = z

    def _default_state(self) -> RegimeState:
        return RegimeState(MarketRegime.UNKNOWN, 0.0, 0.0, np.zeros(12), MarketRegime.UNKNOWN, -1, "CALIBRATING")
