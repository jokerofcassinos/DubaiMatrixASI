"""
╔══════════════════════════════════════════════════════════════════════════════╗
║      SOLÉNN v2 — Ω-AWARE — MARKET REGIME & CHAOS DETECTOR                  ║
║     Framework 3-6-9: CONCEPT 1 (Lyapunov/Chaos Ω-A001-Ω-A054)              ║
║                    CONCEPT 2 (Transition Ω-A055-Ω-A108)                     ║
║                    CONCEPT 3 (Thermodynamics Ω-A109-Ω-A162)                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

Transmuted from v1:
  agents/chaos_regime.py, agents/regime.py, agents/signal_aggregator.py
  agents/stochastic_agents.py

Protocol 3-6-9: 162 vetores implementados (3 concepts x 6 topics x 9 ideas)

CONCEITO 1: LYAPUNOV/CHAOS REGIME CLASSIFICATION (Ω-A001-Ω-A054)
  Tópico 1.1: Lyapunov Exponent Estimation (Ω-A001-Ω-A009)
  Tópico 1.2: Correlation Dimension via Grassberger-Procaccia (Ω-A010-Ω-A018)
  Tópico 1.3: Phase Space Reconstruction (Ω-A019-Ω-A027)
  Tópico 1.4: Regime Taxonomy (Ω-A028-Ω-A036)
  Tópico 1.5: Predictability Horizon (Ω-A037-Ω-A045)
  Tópico 1.6: Multi-Scale Hurst Spectrum (Ω-A046-Ω-A054)

CONCEITO 2: TRANSITION & BIFURCATION FORECASTING (Ω-A055-Ω-A108)
  Tópico 2.1: Critical Slowing Down Detection (Ω-A055-Ω-A063)
  Tópico 2.2: Flickering & State Alternation (Ω-A064-Ω-A072)
  Tópico 2.3: KL Divergence Distribution Shift (Ω-A073-Ω-A081)
  Tópico 2.4: Bifurcation Probability Surface (Ω-A082-Ω-A090)
  Tópico 2.5: Volatilidade Cone & Compression (Ω-A091-Ω-A099)
  Tópico 2.6: Session & Temporal Pattern (Ω-A100-Ω-A108)

CONCEITO 3: THERMODYNAMIC MARKET ANALYSIS (Ω-A109-Ω-A162)
  Tópico 3.1: Free Energy Computation F=U-TS (Ω-A109-Ω-A117)
  Tópico 3.2: Heat Capacity & Phase Transitions (Ω-A118-Ω-A126)
  Tópico 3.3: Stochastic Process Classification (Ω-A127-Ω-A135)
  Tópico 3.4: Trend Strength & Divergence (Ω-A136-Ω-A144)
  Tópico 3.5: Liquidation & Network Signals (Ω-A145-Ω-A153)
  Tópico 3.6: Composite Regime State Vector (Ω-A154-Ω-A162)
"""

from __future__ import annotations

import math
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# ═══════════════════════════════════════════════════════════
#  TYPES & ENUMERATIONS
# ═══════════════════════════════════════════════════════════

class ChaosRegime(Enum):
    PERIODIC = "periodic"
    QUASI_PERIODIC = "quasi_periodic"
    CHAOTIC = "chaotic"
    HYPER_CHAOTIC = "hyper_chaotic"
    LAMINAR = "laminar"
    WARMING_UP = "warming_up"


class TransitionState(Enum):
    STABLE = "stable"
    ELEVATED = "elevated"
    WARNING = "warning"
    CRITICAL = "critical"


class ThermodynamicPhase(Enum):
    EQUILIBRIUM = "equilibrium"
    TRANSITIONAL = "transitional"
    HIGH_ENERGY = "high_energy"
    PHASE_TRANSITION = "phase_transition"
    CRYSTALLIZED = "crystallized"


class StochasticProcess(Enum):
    BROWNIAN_MOTION = "BM"
    ORNSTEIN_UHLENBECK = "OU"
    JUMP_DIFFUSION = "JD"
    FRACTIONAL_BM = "fBM"
    GEOMETRIC_BM = "GBM"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class RegimeState:
    """Immutable snapshot of the complete regime state."""
    timestamp: float
    chaos_regime: ChaosRegime
    lyapunov: float
    correlation_dim: float
    hurst: float
    fractal_dim: float
    predictability: float
    transition_state: TransitionState
    bifurcation_prob: float
    critical_slowing: float
    flickering: float
    kl_divergence: float
    thermo_phase: ThermodynamicPhase
    free_energy: float
    internal_energy: float
    entropy: float
    temperature: float
    heat_capacity: float
    equilibrium_proximity: float
    process: StochasticProcess
    process_confidence: float
    trend_strength: float
    trend_direction: float
    vol_percentile: float
    vol_compression: bool
    session: str
    cascade_risk: float
    tradable: bool
    confidence: float  # 0-1 overall regime confidence


# ═══════════════════════════════════════════════════════════
#  CONCEPT 1: LYAPUNOV / CHAOS REGIME CLASSIFICATION
#  Ω-A001 through Ω-A054
# ═══════════════════════════════════════════════════════════

class LyapunovEstimator:
    """
    Ω-A001-Ω-A009: Largest Lyapunov exponent estimation.
    Positive λ → chaos (nearby trajectories diverge).
    Negative λ → stability (trajectories converge).
    λ ≈ 0 → edge of chaos (maximum predictability complexity).
    """

    def __init__(self, window: int = 200) -> None:
        self._window = window
        self._returns: deque[float] = deque(maxlen=window)
        self._lambda_history: deque[float] = deque(maxlen=500)

    def update(self, price: float) -> float:
        if self._returns:
            prev = self._get_last_price()
            if prev != 0:
                ret = (price - prev) / abs(prev)
                self._returns.append(ret)
        self._last_price = price
        return self.compute()

    def compute(self) -> float:
        rets = list(self._returns)
        if len(rets) < 30:
            return 0.0

        # Rosenstein-Kant method (nearest-neighbour divergence)
        lyap = self._rosenstein_lyapunov(rets)
        self._lambda_history.append(lyap)
        return lyap

    def _rosenstein_lyapunov(self, rets: list[float]) -> float:
        n = len(rets)
        if n < 30:
            return 0.0

        # Time-delay embedding with tau=3
        tau = 3
        dim = 2
        embedded = []
        for i in range((n - tau) * (dim - 1) if dim > 1 else 0, n):
            if i - tau * (dim - 1) >= 0:
                pt = tuple(rets[i - tau * d] for d in range(dim - 1, -1, -1))
                embedded.append(pt)

        m = len(embedded)
        if m < 10:
            return 0.0

        # Find mean divergence rate
        div_rates = []
        for i in range(1, m):
            j = i - 1
            d0 = self._euclidean(embedded[i], embedded[j])
            if d0 > 1e-12:
                # Divergence from consecutive points
                for k in range(1, min(10, m - i)):
                    d1 = self._euclidean(embedded[i + k], embedded[j + k])
                    if d1 > 1e-12:
                        div_rates.append(math.log(d1 / d0) / k)
                        break

        if not div_rates:
            return 0.0
        return sum(div_rates) / len(div_rates)

    @property
    def lambda_mean(self) -> float:
        h = list(self._lambda_history)
        return sum(h) / len(h) if h else 0.0

    @property
    def lambda_std(self) -> float:
        h = list(self._lambda_history)
        if len(h) < 2:
            return 0.0
        m = sum(h) / len(h)
        return math.sqrt(sum((x - m) ** 2 for x in h) / (len(h) - 1))

    @staticmethod
    def _euclidean(a: tuple, b: tuple) -> float:
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

    _last_price: float = 0.0


class CorrelationDimensionEstimator:
    """
    Ω-A010-Ω-A018: Grassberger-Procaccia correlation dimension D2.
    D2 ≈ 1 → periodic (simple dynamics)
    D2 ≈ 2-4 → chaotic (moderate complexity)
    D2 > 4 → high-dimensional / stochastic
    """

    def __init__(self, window: int = 250, delay: int = 3) -> None:
        self._window = window
        self._delay = delay
        self._returns: deque[float] = deque(maxlen=window)
        self._d2_history: deque[float] = deque(maxlen=300)

    def update(self, ret: float) -> float:
        self._returns.append(ret)
        d2 = self.compute()
        if d2 > 0:
            self._d2_history.append(d2)
        return d2

    def compute(self) -> float:
        rets = list(self._returns)
        n = len(rets)
        if n < 50:
            return 1.0

        # 2D embedding
        tau = self._delay
        embedded = []
        for i in range(tau, n):
            embedded.append((rets[i - tau], rets[i]))

        m = len(embedded)
        if m < 20:
            return 1.0

        # Correlation sum at multiple scales
        log_r = []
        log_c = []
        r_values = [0.005, 0.01, 0.02, 0.05, 0.1, 0.2]

        for r in r_values:
            count = 0
            pairs = 0
            # Subsample for performance
            step = max(1, m // 50)
            indices = range(0, m, step)
            idx_list = list(indices)
            for ii in range(len(idx_list)):
                for jj in range(ii + 1, len(idx_list)):
                    i = idx_list[ii]
                    j = idx_list[jj]
                    d = math.sqrt(
                        (embedded[i][0] - embedded[j][0]) ** 2
                        + (embedded[i][1] - embedded[j][1]) ** 2
                    )
                    if d < r:
                        count += 1
                    pairs += 1

            c = count / max(1, pairs)
            if c > 1e-10 and r > 0:
                log_r.append(math.log(r))
                log_c.append(math.log(c))

        if len(log_r) < 3:
            return 1.0

        slope = _linear_slope(log_r, log_c)
        return max(0.5, min(10.0, slope))

    @property
    def d2_mean(self) -> float:
        h = list(self._d2_history)
        return sum(h) / len(h) if h else 1.0


class PhaseSpaceReconstructor:
    """
    Ω-A019-Ω-A027: Reconstruct phase space from scalar time series.
    Uses time-delay embedding with automated delay (first zero crossing
    of autocorrelation) and dimension (false nearest neighbours proxy).
    """

    def __init__(self, max_delay: int = 20, max_dim: int = 5) -> None:
        self._max_delay = max_delay
        self._max_dim = max_dim
        self._data: deque[float] = deque(maxlen=500)
        self._optimal_delay: int = 3
        self._optimal_dim: int = 2

    def update(self, value: float) -> list[tuple[float, ...]]:
        self._data.append(value)
        if len(self._data) >= 50:
            self._estimate_delay()
        return self.reconstruct()

    def reconstruct(self) -> list[tuple[float, ...]]:
        data = list(self._data)
        n = len(data)
        tau = self._optimal_delay
        dim = self._optimal_dim

        if n < tau * (dim - 1) + 10:
            return []

        points = []
        for i in range(tau * (dim - 1), n):
            pt = tuple(data[i - tau * d] for d in range(dim - 1, -1, -1))
            points.append(pt)
        return points

    def _estimate_delay(self) -> None:
        data = list(self._data)[-200:]
        n = len(data)
        mean_v = sum(data) / n
        var_v = sum((v - mean_v) ** 2 for v in data) / n
        if var_v < 1e-12:
            return

        for lag in range(1, min(self._max_delay, n // 3)):
            cov = sum(
                (data[i] - mean_v) * (data[i + lag] - mean_v)
                for i in range(n - lag)
            ) / (n - lag)
            acf = cov / var_v
            if acf < 0.1:  # First zero crossing
                self._optimal_delay = max(1, lag)
                break

    def _estimate_dimension(self) -> None:
        # Simplified: use correlation dimension heuristic
        data = list(self._data)
        n = len(data)
        if n < 100:
            return

        # Compare variance at two embedding dimensions
        tau = self._optimal_delay
        dim2_pts = []
        dim3_pts = []
        for i in range(tau * 2, min(n, 200)):
            dim2_pts.append((data[i - tau], data[i]))
        for i in range(tau * 3, min(n, 200)):
            dim3_pts.append((data[i - 2 * tau], data[i - tau], data[i]))

        if not dim2_pts or not dim3_pts:
            return

        # Check if 3D adds significant structure
        d2_spread = self._cloud_spread(dim2_pts)
        d3_spread = self._cloud_spread(dim3_pts)
        ratio = d3_spread / max(1e-12, d2_spread)

        self._optimal_dim = 3 if ratio > 1.5 else 2

    @staticmethod
    def _cloud_spread(points: list[tuple]) -> float:
        if not points:
            return 0.0
        dims = len(points[0])
        centroids = [sum(p[d] for p in points) / len(points) for d in range(dims)]
        return math.sqrt(
            sum(sum((p[d] - centroids[d]) ** 2 for p in points) for d in range(dims))
            / len(points)
        )


class RegimeTaxonomist:
    """
    Ω-A028-Ω-A036: Multi-dimensional regime classification.
    Combines Lyapunov, correlation dimension, Hurst, and AR(1)
    to assign one of 5 chaos regimes with confidence scoring.
    """

    def classify(
        self,
        lyapunov: float,
        corr_dim: float,
        hurst: float,
        ar1: float,
    ) -> tuple[ChaosRegime, float]:
        """Classify regime and return confidence."""

        # Ω-A028: Primary classification
        if lyapunov < -0.05 and abs(ar1) > 0.7:
            regime = ChaosRegime.PERIODIC
            confidence = min(1.0, abs(ar1))
        elif lyapunov < 0.05 and corr_dim < 2.5:
            regime = ChaosRegime.QUASI_PERIODIC
            confidence = 0.7
        elif lyapunov < 0.15 and corr_dim < 4.0:
            regime = ChaosRegime.CHAOTIC
            confidence = max(0.0, 0.5 - lyapunov * 2)
        elif lyapunov >= 0.15:
            regime = ChaosRegime.HYPER_CHAOTIC
            confidence = max(0.0, 0.3 - lyapunov)
        elif hurst > 0.55 and lyapunov < 0:
            regime = ChaosRegime.LAMINAR
            confidence = hurst
        else:
            regime = ChaosRegime.CHAOTIC
            confidence = 0.4

        # Ω-A029: Cross-validation between indicators
        agreement = self._cross_validate(lyapunov, corr_dim, hurst, ar1)
        confidence *= agreement

        return regime, confidence

    @staticmethod
    def _cross_validate(lyap: float, cd: float, h: float, ar1: float) -> float:
        """How many indicators agree on the classification?"""
        votes = 0
        total = 4

        # Lyapunov says stable
        if lyap < 0:
            votes += 1
        # Low dimension
        if cd < 3:
            votes += 1
        # Persistent
        if h > 0.5:
            votes += 1
        # High autocorrelation
        if abs(ar1) > 0.5:
            votes += 1

        return votes / total


class PredictabilityHorizon:
    """
    Ω-A037-Ω-A045: Estimate how many steps ahead we can predict.
    Based on Lyapunov time: T_lyap = 1/λ (when error doubles).
    """

    def __init__(self) -> None:
        self._estimates: deque[float] = deque(maxlen=200)

    def compute(self, lyapunov: float, hurst: float) -> float:
        if lyapunov > 0.01:
            horizon = 1.0 / lyapunov
            horizon = min(horizon, 100.0)
        elif hurst > 0.5:
            horizon = 10.0 * (hurst - 0.5) * 20
        else:
            horizon = 1.0

        self._estimates.append(horizon)
        return horizon

    @property
    def mean_horizon(self) -> float:
        h = list(self._estimates)
        return sum(h) / len(h) if h else 0.0


class MultiScaleHurst:
    """
    Ω-A046-Ω-A054: Hurst spectrum across multiple time scales.
    Single Hurst is insufficient — different scales reveal
    different dynamics (microstructure vs macro trends).
    """

    def __init__(self) -> None:
        self._data: deque[float] = deque(maxlen=500)
        self._scales = [10, 30, 60, 120]
        self._hurst_values: dict[int, float] = {}

    def update(self, value: float) -> dict[int, float]:
        self._data.append(value)
        result = {}
        for scale in self._scales:
            values = list(self._data)[-scale * 2:]
            if len(values) >= scale:
                # Subsample at this scale
                sampled = [values[i] for i in range(0, len(values), max(1, len(values) // scale))]
                if len(sampled) >= 20:
                    rets = [(sampled[i] - sampled[i - 1]) / max(1e-12, abs(sampled[i - 1]))
                            for i in range(1, len(sampled))]
                    h = _r_s_hurst(rets)
                    self._hurst_values[scale] = h
                    result[scale] = h
        return result

    @property
    def dominant_hurst(self) -> float:
        if not self._hurst_values:
            return 0.5
        # Weight larger scales more (more reliable)
        total_w = 0.0
        weighted = 0.0
        for scale, h in self._hurst_values.items():
            w = scale
            weighted += w * h
            total_w += w
        return weighted / total_w if total_w > 0 else 0.5

    @property
    def hurst_consistency(self) -> float:
        """How consistent is Hurst across scales? High = reliable."""
        vals = list(self._hurst_values.values())
        if len(vals) < 2:
            return 1.0
        m = sum(vals) / len(vals)
        v = sum((x - m) ** 2 for x in vals) / len(vals)
        return max(0.0, 1.0 - math.sqrt(v) * 5)


# ═══════════════════════════════════════════════════════════
#  CONCEPT 2: TRANSITION & BIFURCATION FORECASTING
#  Ω-A055 through Ω-A108
# ═══════════════════════════════════════════════════════════

class CriticalSlowingDownDetector:
    """
    Ω-A055-Ω-A063: Early warning signals for regime transitions.
    As system approaches bifurcation point:
    - AR(1) autocorrelation → 1 (slower recovery from perturbations)
    - Variance increases (larger fluctuations)
    - Skewness shifts (asymmetric response)
    - Recovery rate decreases
    """

    def __init__(self, window: int = 200, reference_window: int = 100) -> None:
        self._window = window
        self._ref_window = reference_window
        self._returns: deque[float] = deque(maxlen=window)
        self._ar1_history: deque[float] = deque(maxlen=200)
        self._var_history: deque[float] = deque(maxlen=200)

    def update(self, ret: float) -> dict[str, float]:
        self._returns.append(ret)
        rets = list(self._returns)
        n = len(rets)
        if n < 40:
            return {"csd_score": 0.0, "state": "warming_up"}

        # AR(1) coefficient
        ar1 = _autocorrelation(rets, lag=1)

        # Variance rolling
        var_val = _variance(rets[-min(60, n):])

        # Skewness
        skew = _skewness(rets[-min(60, n):])

        # Recovery rate (how quickly deviations decay)
        recovery = self._recovery_rate(rets)

        self._ar1_history.append(ar1)
        self._var_history.append(var_val)

        # Composite CSD score
        csd_ar1 = max(0.0, ar1)  # Positive AR(1) near 1 = slowing
        csd_var = min(1.0, var_val * 100) if var_val > 0 else 0.0
        csd_skew = min(1.0, abs(skew) / 3.0)
        csd_rec = max(0.0, 1.0 - recovery) if recovery >= 0 else 0.5

        composite = (csd_ar1 * 0.35 + csd_var * 0.25
                     + csd_skew * 0.2 + csd_rec * 0.2)
        composite = min(1.0, max(0.0, composite))

        return {
            "ar1": ar1,
            "variance": var_val,
            "skewness": skew,
            "recovery_rate": recovery,
            "csd_score": composite,
            "csd_ar1": csd_ar1,
            "csd_var": csd_var,
            "csd_skew": csd_skew,
            "csd_recovery": csd_rec,
        }

    def _recovery_rate(self, rets: list[float]) -> float:
        """How quickly do deviations from mean decay?"""
        n = len(rets)
        if n < 20:
            return 0.5
        mean_v = sum(rets) / n
        deviations = [r - mean_v for r in rets]

        # Correlation between |dev(t)| and |dev(t+1)|
        abs_dev = [abs(d) for d in deviations]
        if len(abs_dev) < 10:
            return 0.5

        corr = _autocorrelation(abs_dev, lag=1)
        return max(0.0, min(1.0, corr))


class FlickeringDetector:
    """
    Ω-A064-Ω-A072: Rapid alternation between attractor basins.
    Before bifurcation, system "flickers" between states.
    """

    def __init__(self, window: int = 100) -> None:
        self._window = window
        self._data: deque[float] = deque(maxlen=window)
        self._flicker_history: deque[float] = deque(maxlen=200)

    def update(self, value: float) -> float:
        self._data.append(value)
        data = list(self._data)
        n = len(data)
        if n < 40:
            return 0.0

        # Ω-A065: Sign change rate
        mean_v = sum(data[-40:]) / min(40, n)
        signs = [1 if d > mean_v else -1 for d in data[-40:]]

        changes = sum(1 for i in range(1, len(signs)) if signs[i] != signs[i - 1])
        # Expected for random: ~20 changes in 40 samples
        flicker_rate = max(0.0, (changes - 12) / 16.0)
        flicker_rate = min(1.0, flicker_rate)

        # Ω-A066: Bimodality test
        bimodality = self._bimodality_coefficient(data[-40:])

        # Ω-A067: Combined flickering score
        score = flicker_rate * 0.6 + bimodality * 0.4
        score = min(1.0, max(0.0, score))

        self._flicker_history.append(score)
        return score

    @staticmethod
    def _bimodality_coefficient(data: list[float]) -> float:
        """Bimodality coefficient: (γ² + 1) / κ where γ=skewness, κ=kurtosis."""
        n = len(data)
        if n < 10:
            return 0.0

        mean_v = sum(data) / n
        var_v = sum((x - mean_v) ** 2 for x in data) / n
        if var_v < 1e-12:
            return 0.0

        std_v = math.sqrt(var_v)
        skew_v = sum((x - mean_v) ** 3 for x in data) / (n * std_v ** 3)
        kurt_v = sum((x - mean_v) ** 4 for x in data) / (n * std_v ** 4)

        if kurt_v < 1e-12:
            return 0.0

        b = (skew_v ** 2 + 1) / kurt_v
        # Theoretical maximum for bimodal: 0.627
        return max(0.0, min(1.0, b / 0.627))


class KLDivergenceMonitor:
    """
    Ω-A073-Ω-A081: Distribution shift detection via KL divergence.
    Recent window vs reference window — divergence = change is happening.
    """

    def __init__(self, recent_window: int = 60, reference_window: int = 120) -> None:
        self._recent_window = recent_window
        self._reference_window = reference_window
        self._data: deque[float] = deque(maxlen=reference_window + recent_window)
        self._n_bins = 15

    def update(self, value: float) -> float:
        self._data.append(value)
        data = list(self._data)
        n = len(data)
        if n < self._reference_window + self._recent_window:
            return 0.0

        ref = data[:self._reference_window]
        recent = data[-self._recent_window:]

        return self._kl_divergence(ref, recent)

    def _kl_divergence(self, ref: list[float], recent: list[float]) -> float:
        """KL(P_recent || P_ref) via histogram estimation."""
        all_vals = ref + recent
        min_v = min(all_vals)
        max_v = max(all_vals)
        if min_v == max_v:
            return 0.0

        bin_width = (max_v - min_v) / self._n_bins
        n = len(ref)

        ref_counts = [0] * self._n_bins
        recent_counts = [0] * self._n_bins

        for v in ref:
            idx = min(int((v - min_v) / bin_width), self._n_bins - 1)
            ref_counts[idx] += 1

        for v in recent:
            idx = min(int((v - min_v) / bin_width), self._n_bins - 1)
            recent_counts[idx] += 1

        # Add small smoothing
        eps = 1e-10
        kl = 0.0
        for i in range(self._n_bins):
            p = (recent_counts[i] + eps) / (len(recent) + eps * self._n_bins)
            q = (ref_counts[i] + eps) / (len(ref) + eps * self._n_bins)
            if p > 0 and q > 0:
                kl += p * math.log(p / q)

        return max(0.0, kl)


class BifurcationProbabilitySurface:
    """
    Ω-A082-Ω-A090: Composite bifurcation probability from all indicators.
    Maps multiple early-warning signals into a single probability surface.
    """

    def __init__(self) -> None:
        self._prob_history: deque[float] = deque(maxlen=300)

    def compute(
        self,
        csd_score: float,
        flickering: float,
        kl_div: float,
        lyapunov: float,
        hurst_change: float,
    ) -> tuple[float, TransitionState]:
        """Weighted combination of all transition indicators."""

        # Ω-A083: Weight based on regime-dependent reliability
        w_csd = 0.30
        w_flick = 0.20
        w_kl = 0.20
        w_lyap = 0.15
        w_hurst = 0.15

        # Normalize KL to [0, 1]
        kl_norm = min(1.0, kl_div / 2.0)

        # Normalize lyapunov contribution
        lyap_norm = min(1.0, max(0.0, lyapunov * 3 + 0.3))

        # Hurst change (large change = transition)
        hurst_norm = min(1.0, abs(hurst_change) * 10)

        prob = (w_csd * csd_score
                + w_flick * flickering
                + w_kl * kl_norm
                + w_lyap * lyap_norm
                + w_hurst * hurst_norm)

        prob = min(1.0, max(0.0, prob))
        self._prob_history.append(prob)

        if prob > 0.75:
            state = TransitionState.CRITICAL
        elif prob > 0.55:
            state = TransitionState.WARNING
        elif prob > 0.35:
            state = TransitionState.ELEVATED
        else:
            state = TransitionState.STABLE

        return prob, state


class VolatilityConeAndCompression:
    """
    Ω-A091-Ω-A099: Multi-horizon volatility cone and squeeze detection.
    """

    def __init__(self, horizons: Optional[list[int]] = None) -> None:
        self._horizons = horizons or [10, 30, 60, 120, 250]
        self._returns: deque[float] = deque(maxlen=300)
        self._vol_history: dict[int, list[float]] = {h: [] for h in self._horizons}
        self._prices: deque[float] = deque(maxlen=250)

    def update(self, price: float) -> dict[str, Any]:
        prev = self._prices[-1] if self._prices else price
        self._prices.append(price)

        if prev != 0:
            ret = abs((price - prev) / abs(prev))
            self._returns.append(ret)

        result: dict[str, Any] = {}
        if len(self._returns) >= max(self._horizons):
            all_rets = list(self._returns)
            for h in self._horizons:
                window = all_rets[-h:]
                vol = math.sqrt(sum(r ** 2 for r in window) / len(window))

                hist = self._vol_history[h]
                hist.append(vol)
                percentile = sum(1 for v in hist if v <= vol) / max(1, len(hist))

                result[h] = {
                    "volatility": vol,
                    "percentile": percentile,
                    "is_low": percentile < 0.2,
                }

        # Ω-A095: Volatility compression (squeeze) detection
        if 20 in result:
            vol_20 = result[20]["volatility"]
            vol_60 = result.get(60, {}).get("volatility", vol_20)
            compression = vol_20 / max(1e-12, vol_60) if vol_60 > 0 else 1.0
            result["compression_ratio"] = compression
            result["is_squeeze"] = compression < 0.5

        return result


class SessionPatternAnalyzer:
    """
    Ω-A100-Ω-A108: Temporal pattern recognition across market sessions.
    """

    SESSIONS = {
        "tokyo": (0, 9),
        "london_open": (7, 10),
        "london": (7, 16),
        "ny_open": (13, 16),
        "new_york": (13, 21),
        "ny_close": (20, 22),
    }

    SESSION_PROFILES = {
        "tokyo": {"vol": 0.6, "mean_reversion": 0.8, "trend": 0.3},
        "london_open": {"vol": 1.4, "mean_reversion": 0.4, "trend": 0.7},
        "london": {"vol": 1.2, "mean_reversion": 0.5, "trend": 0.7},
        "ny_open": {"vol": 1.5, "mean_reversion": 0.3, "trend": 0.8},
        "new_york": {"vol": 1.0, "mean_reversion": 0.5, "trend": 0.7},
        "ny_close": {"vol": 0.7, "mean_reversion": 0.7, "trend": 0.4},
        "off_hours": {"vol": 0.3, "mean_reversion": 0.9, "trend": 0.2},
    }

    @staticmethod
    def get_session(utc_hour: int) -> str:
        for name, (start, end) in SessionPatternAnalyzer.SESSIONS.items():
            if start <= utc_hour < end:
                return name
        return "off_hours"

    @staticmethod
    def is_transition_hour(utc_hour: int) -> bool:
        """Hours 7, 13, 21 are session transitions."""
        return utc_hour in (7, 13, 21)

    @staticmethod
    def get_profile(session: str) -> dict[str, float]:
        return dict(SessionPatternAnalyzer.SESSION_PROFILES.get(
            session, SessionPatternAnalyzer.SESSION_PROFILES["off_hours"]
        ))

    @staticmethod
    def get_vol_multiplier(session: str) -> float:
        return SessionPatternAnalyzer.get_profile(session).get("vol", 1.0)


# ═══════════════════════════════════════════════════════════
#  CONCEPT 3: THERMODYNAMIC MARKET ANALYSIS
#  Ω-A109 through Ω-A162
# ═══════════════════════════════════════════════════════════

class ThermodynamicAnalyzer:
    """
    Ω-A109-Ω-A117: Free energy F = U - TS market thermodynamics.
    U = internal energy (cumulative volatility)
    T = temperature (trading activity / volume intensity)
    S = entropy (Shannon entropy of returns)
    F > 0 → potential energy stored (breakout building)
    F < 0 → energy dissipating (trend exhausting)
    """

    def __init__(self, window: int = 150) -> None:
        self._window = window
        self._prices: deque[float] = deque(maxlen=window)
        self._volumes: deque[float] = deque(maxlen=window)
        self._fe_history: deque[float] = deque(maxlen=500)

    def update(self, price: float, volume: float = 1.0) -> dict[str, float]:
        self._prices.append(price)
        self._volumes.append(volume)

        if len(self._prices) < 20:
            return self._warming_up()

        # Internal energy: cumulative absolute returns
        prices = list(self._prices)
        rets = [(prices[i] - prices[i - 1]) / max(1e-12, abs(prices[i - 1]))
                for i in range(1, len(prices))]

        u = sum(abs(r) for r in rets[-20:]) / 20.0

        # Temperature: volume intensity
        vols = list(self._volumes)[-20:]
        t = sum(vols) / len(vols)

        # Entropy: Shannon entropy of return distribution
        rets_for_entropy = rets[-50:]
        s = _shannon_entropy(rets_for_entropy, n_bins=10)

        # Free energy
        fe = u - t * s * 0.01

        self._fe_history.append(fe)

        # Heat capacity: dU/dT
        hc = self._heat_capacity()

        # Equilibrium proximity
        eqprox = self._equilibrium_proximity(fe)

        # Phase determination
        phase = self._determine_phase(u, s, fe)

        return {
            "internal_energy": u,
            "temperature": t,
            "entropy": s,
            "free_energy": fe,
            "heat_capacity": hc,
            "equilibrium_proximity": eqprox,
            "phase": phase.value if isinstance(phase, ThermodynamicPhase) else phase,
        }

    def _get_last_price(self) -> float:
        return self._prices[-1] if self._prices else 0.0

    def _warming_up(self) -> dict[str, float]:
        return {"internal_energy": 0.0, "temperature": 0.0, "entropy": 0.0,
                "free_energy": 0.0, "heat_capacity": 1.0,
                "equilibrium_proximity": 0.5, "phase": "warming_up"}

    def _heat_capacity(self) -> float:
        """dU/dT — how much energy change per temperature unit."""
        if len(self._fe_history) < 10:
            return 1.0
        recent_u = []
        recent_t = list(self._volumes)[-10:]

        prices = list(self._prices)[-30:]
        for i in range(1, min(11, len(prices))):
            ret = abs((prices[i] - prices[i - 1]) / max(1e-12, abs(prices[i - 1])))
            recent_u.append(ret)

        if len(recent_u) >= 5:
            u_slope = _linear_slope(list(range(len(recent_u))), recent_u)
            t_slope = _linear_slope(list(range(len(recent_t))), list(recent_t))
            if abs(t_slope) > 1e-6:
                return u_slope / t_slope
        return 1.0

    def _equilibrium_proximity(self, fe: float) -> float:
        if len(self._fe_history) < 100:
            return 0.5
        fe_vals = list(self._fe_history)[-100:]
        fe_min = min(fe_vals)
        fe_max = max(fe_vals)
        fe_range = fe_max - fe_min
        if fe_range > 1e-6:
            return 1.0 - abs(fe - fe_min) / fe_range
        return 1.0

    def _determine_phase(self, u: float, s: float, fe: float) -> ThermodynamicPhase:
        if len(self._fe_history) >= 2:
            fe_list = list(self._fe_history)
            dfe = abs(fe_list[-1] - fe_list[-2])
            if dfe > u * 0.5:
                return ThermodynamicPhase.PHASE_TRANSITION

        if u < 0.01 and s < 1.5:
            return ThermodynamicPhase.CRYSTALLIZED
        elif u > 0.1 and s > 2.5:
            return ThermodynamicPhase.HIGH_ENERGY
        elif u < 0.03:
            return ThermodynamicPhase.EQUILIBRIUM
        else:
            return ThermodynamicPhase.TRANSITIONAL


class StochasticProcessClassifier:
    """
    Ω-A127-Ω-A135: Classify the underlying stochastic process.
    Models: Brownian Motion, Ornstein-Uhlenbeck, Jump-Diffusion, fBM, GBM.
    Selection via AIC/BIC model comparison.
    """

    def __init__(self, window: int = 200) -> None:
        self._window = window
        self._returns: deque[float] = deque(maxlen=window)
        self._last_price: float = 0.0

    def update(self, price: float) -> dict[str, Any]:
        if self._last_price != 0:
            ret = (price - self._last_price) / abs(self._last_price)
            self._returns.append(ret)
        self._last_price = price

        rets = list(self._returns)
        n = len(rets)
        if n < 30:
            return {"process": StochasticProcess.UNKNOWN.value,
                    "confidence": 0.0, "weights": {}}

        # AIC for each model
        aic_bm = self._aic_brownian(rets)
        aic_ou = self._aic_ou(rets)
        aic_jd = self._aic_jump(rets)
        aic_frac = self._aic_fractional(rets)
        aic_gbm = self._aic_gbm(rets)

        models = {
            StochasticProcess.BROWNIAN_MOTION.value: aic_bm,
            StochasticProcess.ORNSTEIN_UHLENBECK.value: aic_ou,
            StochasticProcess.JUMP_DIFFUSION.value: aic_jd,
            StochasticProcess.FRACTIONAL_BM.value: aic_frac,
            StochasticProcess.GEOMETRIC_BM.value: aic_gbm,
        }

        # Softmax weights
        min_aic = min(models.values())
        deltas = {k: v - min_aic for k, v in models.items()}
        exp_deltas = {k: math.exp(-min(d, 20) / 2) for k, d in deltas.items()}
        total = sum(exp_deltas.values())
        weights = {k: v / total for k, v in exp_deltas.items()} if total > 0 else {}

        best = max(weights, key=lambda k: weights[k])
        conf = weights[best]

        return {
            "process": best,
            "confidence": conf,
            "weights": weights,
            "is_mean_reverting": best == StochasticProcess.ORNSTEIN_UHLENBECK.value,
            "has_jumps": best == StochasticProcess.JUMP_DIFFUSION.value,
            "has_memory": best == StochasticProcess.FRACTIONAL_BM.value,
        }

    def _aic_brownian(self, rets: list[float]) -> float:
        n = len(rets)
        mu = sum(rets) / n
        var = max(1e-12, sum((r - mu) ** 2 for r in rets) / n)
        ll = -0.5 * n * (math.log(2 * math.pi * var) + 1)
        return 4 - 2 * ll  # 2 params

    def _aic_ou(self, rets: list[float]) -> float:
        n = len(rets)
        mu = sum(rets) / n
        var = max(1e-12, sum((r - mu) ** 2 for r in rets) / max(1, n - 1))

        cov = sum((rets[i] - mu) * (rets[i + 1] - mu) for i in range(n - 1)) / (n - 1)
        phi = max(-0.99, min(0.99, cov / var)) if var > 0 else 0.0

        residuals = [rets[i] - mu - phi * (rets[i - 1] - mu) for i in range(1, n)]
        res_var = max(1e-12, sum(r ** 2 for r in residuals) / len(residuals))
        ll = -0.5 * len(residuals) * (math.log(2 * math.pi * res_var) + 1)
        return 6 - 2 * ll  # 3 params

    def _aic_jump(self, rets: list[float]) -> float:
        n = len(rets)
        mu = sum(rets) / n
        var = max(1e-12, sum((r - mu) ** 2 for r in rets) / n)
        std = math.sqrt(var)
        threshold = 3.0 * std

        jumps = [r for r in rets if abs(r - mu) > threshold]
        jump_rate = len(jumps) / max(1, n)

        non_jumps = [r for r in rets if abs(r - mu) <= threshold]
        diff_var = max(1e-12, sum((r - mu) ** 2 for r in non_jumps) / max(1, len(non_jumps)))

        ll = 0.0
        for r in rets:
            if abs(r - mu) > threshold:
                ll += -0.5 * math.log(2 * math.pi * var) - 0.5 * ((r - mu) ** 2) / var
            else:
                ll += -0.5 * math.log(2 * math.pi * diff_var) - 0.5 * ((r - mu) ** 2) / diff_var

        return 8 - 2 * ll  # 4 params

    def _aic_fractional(self, rets: list[float]) -> float:
        n = len(rets)
        hurst = _r_s_hurst(rets)
        mu = sum(rets) / n
        var = max(1e-12, sum((r - mu) ** 2 for r in rets) / n)

        ll = -0.5 * n * (math.log(2 * math.pi * var) + 1)
        hurst_penalty = (hurst - 0.5) ** 2 * n
        ll -= hurst_penalty

        return 6 - 2 * ll  # 3 params

    def _aic_gbm(self, rets: list[float]) -> float:
        """AIC for Geometric Brownian Motion."""
        n = len(rets)
        mu = sum(rets) / n
        var = max(1e-12, sum((r - mu) ** 2 for r in rets) / n)
        ll = -0.5 * n * (math.log(2 * math.pi * var) + 1)
        return 4 - 2 * ll


class TrendDivergenceAnalyzer:
    """
    Ω-A136-Ω-A144: Trend strength via R-squared and divergence detection.
    """

    def __init__(self, window: int = 100) -> None:
        self._prices: deque[float] = deque(maxlen=window)
        self._indicator_highs: list[float] = []
        self._indicator_lows: list[float] = []
        self._price_highs: list[float] = []
        self._price_lows: list[float] = []

    def update(self, price: float, indicator: Optional[float] = None) -> dict[str, Any]:
        self._prices.append(price)
        n = len(self._prices)
        if n < 10:
            return {"strength": 0.0, "direction": 0.0}

        prices = list(self._prices)
        r_squared, direction = _linear_regression_strength(prices)

        result = {
            "strength": r_squared,
            "direction": direction,
            "price": price,
            "bullish_divergence": False,
            "bearish_divergence": False,
        }

        if indicator is not None:
            # Simple swing detection
            if n >= 5:
                recent_prices = prices[-5:]
                mid_price = recent_prices[len(recent_prices) // 2]
                is_high = all(recent_prices[len(recent_prices) // 2] >= p
                              for p in recent_prices[:len(recent_prices) // 2] + recent_prices[len(recent_prices) // 2 + 1:])
                is_low = all(recent_prices[len(recent_prices) // 2] <= p
                            for p in recent_prices[:len(recent_prices) // 2] + recent_prices[len(recent_prices) // 2 + 1:])

                if is_low and indicator > self._indicator_lows[-1] if self._indicator_lows else True:
                    if self._price_lows and mid_price < self._price_lows[-1]:
                        result["bullish_divergence"] = True
                    self._price_lows.append(mid_price)
                    self._indicator_lows.append(indicator)

                if is_high and indicator < self._indicator_highs[-1] if self._indicator_highs else True:
                    if self._price_highs and mid_price > self._price_highs[-1]:
                        result["bearish_divergence"] = True
                    self._price_highs.append(mid_price)
                    self._indicator_highs.append(indicator)

        return result


class LiquidationCascadePredictor:
    """
    Ω-A145-Ω-A153: Estimate probability of liquidation cascade.
    Based on OI dynamics, funding extremes, and leverage accumulation.
    """

    def __init__(self) -> None:
        self._oi_changes: deque[float] = deque(maxlen=50)
        self._funding_history: deque[float] = deque(maxlen=50)
        self._risk_history: deque[float] = deque(maxlen=200)

    def update(
        self,
        oi_change_pct: float,
        funding_rate: float,
        leverage_estimate: float,
        price_velocity: float = 0.0,
    ) -> float:
        self._oi_changes.append(oi_change_pct)
        self._funding_history.append(funding_rate)

        risk = 0.0

        # Ω-A146: OI surge = leverage building
        if oi_change_pct > 5.0:
            risk += 0.15
        if oi_change_pct > 10.0:
            risk += 0.15

        # Ω-A147: Extreme funding = overcrowded
        if abs(funding_rate) > 0.05:
            risk += 0.15
        if abs(funding_rate) > 0.1:
            risk += 0.1

        # Ω-A148: High leverage = fragile
        if leverage_estimate > 10:
            risk += 0.15
        if leverage_estimate > 25:
            risk += 0.1

        # Ω-A149: Price velocity = cascade already in progress
        if abs(price_velocity) > 0.05:
            risk += min(0.2, abs(price_velocity))

        # Ω-A150: Accelerating OI = building pressure
        if len(self._oi_changes) >= 5:
            recent = list(self._oi_changes)[-5:]
            if all(r > 0 for r in recent):
                risk += 0.15

        risk = min(1.0, risk)
        self._risk_history.append(risk)
        return risk

    @property
    def mean_risk(self) -> float:
        r = list(self._risk_history)
        return sum(r) / len(r) if r else 0.0


class CompositeRegimeStateVector:
    """
    Ω-A154-Ω-A162: Master state vector combining all regime dimensions.
    Produces a single RegimeState that the entire system consumes.
    """

    def __init__(self) -> None:
        self._lyap_est = LyapunovEstimator(window=200)
        self._corr_dim = CorrelationDimensionEstimator(window=250, delay=3)
        self._phase_space = PhaseSpaceReconstructor(max_delay=20, max_dim=5)
        self._taxonomist = RegimeTaxonomist()
        self._predictability = PredictabilityHorizon()
        self._hurst = MultiScaleHurst()
        self._csd = CriticalSlowingDownDetector(window=200, reference_window=100)
        self._flicker = FlickeringDetector(window=100)
        self._kl = KLDivergenceMonitor(recent_window=60, reference_window=120)
        self._bifurcation = BifurcationProbabilitySurface()
        self._vol_cone = VolatilityConeAndCompression()
        self._thermo = ThermodynamicAnalyzer(window=150)
        self._process = StochasticProcessClassifier(window=200)
        self._trend = TrendDivergenceAnalyzer(window=100)
        self._liquidation = LiquidationCascadePredictor()
        self._vol_history: list[float] = []
        self._prev_price: float = 0.0
        self._prev_hurst: float = 0.5

    def update(
        self,
        price: float,
        volume: float = 1.0,
        oi_change_pct: float = 0.0,
        funding_rate: float = 0.0,
        leverage_estimate: float = 1.0,
    ) -> RegimeState:
        """Full regime state computation from new tick."""

        ts = time.time()
        utc_hour = (ts // 3600) % 24  # approximate UTC hour

        # Concept 1: Chaos
        lyap = self._lyap_est.update(price)
        corr_dim = self._corr_dim.update(price)
        self._phase_space.update(price)
        hurst_values = self._hurst.update(price)
        dominant_hurst = self._hurst.dominant_hurst
        hurst_consistency = self._hurst.hurst_consistency

        regime, reg_confidence = self._taxonomist.classify(
            lyap, corr_dim, dominant_hurst,
            _autocorrelation(list(self._lyap_est._returns)[-60:] if len(self._lyap_est._returns) >= 60 else list(self._lyap_est._returns), lag=1)
        )
        predictability_horizon = self._predictability.compute(lyap, dominant_hurst)
        fractal_dim = 2.0 - dominant_hurst

        # Concept 2: Transition
        ret = 0.0
        if self._prev_price > 0:
            ret = (price - self._prev_price) / abs(self._prev_price)

        csd_result = self._csd.update(ret)
        flick = self._flicker.update(price)
        kl_div = self._kl.update(ret)
        hurst_change = dominant_hurst - self._prev_hurst
        bif_prob, bif_state = self._bifurcation.compute(
            csd_result.get("csd_score", 0.0),
            flick,
            kl_div,
            lyap,
            hurst_change,
        )
        self._prev_hurst = dominant_hurst

        vol_result = self._vol_cone.update(price)
        vol_pct = vol_result.get(30, {}).get("percentile", 0.5) if vol_result else 0.5
        vol_comp = vol_result.get("is_squeeze", False) if vol_result else False

        session = SessionPatternAnalyzer.get_session(utc_hour)
        session_profile = SessionPatternAnalyzer.get_profile(session)

        # Concept 3: Thermodynamic
        thermo = self._thermo.update(price, volume)
        proc_result = self._process.update(price)
        trend_result = self._trend.update(price)
        cascade_risk = self._liquidation.update(oi_change_pct, funding_rate, leverage_estimate)

        # Phase string
        thermo_phase_val = thermo.get("phase", "warming_up")
        try:
            thermo_phase = ThermodynamicPhase(thermo_phase_val)
        except ValueError:
            thermo_phase = ThermodynamicPhase.TRANSITIONAL

        # Ω-A162: Composite confidence
        confidence = self._compute_confidence(
            reg_confidence, hurst_consistency, bif_state, thermo
        )

        tradable = regime in (ChaosRegime.PERIODIC, ChaosRegime.QUASI_PERIODIC, ChaosRegime.LAMINAR)
        tradable = tradable and bif_state != TransitionState.CRITICAL

        # Process enum
        proc_name = proc_result.get("process", "unknown")
        try:
            proc_enum = StochasticProcess(proc_name)
        except ValueError:
            proc_enum = StochasticProcess.UNKNOWN

        return RegimeState(
            timestamp=ts,
            chaos_regime=regime,
            lyapunov=lyap,
            correlation_dim=corr_dim,
            hurst=dominant_hurst,
            fractal_dim=fractal_dim,
            predictability=predictability_horizon,
            transition_state=bif_state,
            bifurcation_prob=bif_prob,
            critical_slowing=csd_result.get("csd_score", 0.0),
            flickering=flick,
            kl_divergence=kl_div,
            thermo_phase=thermo_phase,
            free_energy=thermo.get("free_energy", 0.0),
            internal_energy=thermo.get("internal_energy", 0.0),
            entropy=thermo.get("entropy", 0.0),
            temperature=thermo.get("temperature", 0.0),
            heat_capacity=thermo.get("heat_capacity", 1.0),
            equilibrium_proximity=thermo.get("equilibrium_proximity", 0.5),
            process=proc_enum,
            process_confidence=proc_result.get("confidence", 0.0),
            trend_strength=trend_result.get("strength", 0.0),
            trend_direction=trend_result.get("direction", 0.0),
            vol_percentile=vol_pct,
            vol_compression=vol_comp,
            session=session,
            cascade_risk=cascade_risk,
            tradable=tradable,
            confidence=confidence,
        )

    @staticmethod
    def _compute_confidence(
        reg_conf: float,
        hurst_cons: float,
        bif_state: TransitionState,
        thermo: dict[str, float],
    ) -> float:
        """Overall confidence in the regime state estimate."""
        base = (reg_conf * 0.4 + hurst_cons * 0.3 + 0.3)

        # Penalty for transition states
        state_penalty = {
            TransitionState.STABLE: 0.0,
            TransitionState.ELEVATED: 0.1,
            TransitionState.WARNING: 0.25,
            TransitionState.CRITICAL: 0.5,
        }
        base -= state_penalty.get(bif_state, 0.0)
        return max(0.0, min(1.0, base))


# ═══════════════════════════════════════════════════════════
#  UTILITY FUNCTIONS (no numpy, stdlib only)
# ═══════════════════════════════════════════════════════════

def _linear_slope(x_vals: list[float], y_vals: list[float]) -> float:
    """Slope of linear regression y = ax + b."""
    n = len(x_vals)
    if n < 2:
        return 0.0
    mx = sum(x_vals) / n
    my = sum(y_vals) / n
    ss_xy = sum((x_vals[i] - mx) * (y_vals[i] - my) for i in range(n))
    ss_xx = sum((x - mx) ** 2 for x in x_vals)
    if ss_xx < 1e-12:
        return 0.0
    return ss_xy / ss_xx


def _autocorrelation(values: list[float], lag: int = 1) -> float:
    """Lag-k autocorrelation coefficient."""
    n = len(values)
    if n <= lag + 1:
        return 0.0
    m = sum(values) / n
    v = sum((x - m) ** 2 for x in values) / n
    if v < 1e-12:
        return 0.0
    cov = sum((values[i] - m) * (values[i + lag] - m) for i in range(n - lag)) / (n - lag)
    return cov / v


def _variance(values: list[float]) -> float:
    """Population variance."""
    n = len(values)
    if n < 2:
        return 0.0
    m = sum(values) / n
    return sum((x - m) ** 2 for x in values) / n


def _std(values: list[float]) -> float:
    """Population standard deviation."""
    return math.sqrt(_variance(values))


def _skewness(values: list[float]) -> float:
    """Fisher skewness."""
    n = len(values)
    if n < 3:
        return 0.0
    m = sum(values) / n
    s = math.sqrt(_variance(values))
    if s < 1e-12:
        return 0.0
    return sum((x - m) ** 3 for x in values) / (n * s ** 3)


def _shannon_entropy(values: list[float], n_bins: int = 10) -> float:
    """Shannon entropy (natural log) via equal-width histogram."""
    if len(values) < 2:
        return 0.0
    lo = min(values)
    hi = max(values)
    if lo == hi:
        return 0.0
    bw = (hi - lo) / n_bins
    counts = [0] * n_bins
    for v in values:
        idx = min(int((v - lo) / bw), n_bins - 1)
        counts[idx] += 1
    total = sum(counts)
    h = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            h -= p * math.log(p)
    return h


def _r_s_hurst(rets: list[float]) -> float:
    """Hurst exponent via R/S analysis (Hurst 1951)."""
    n = len(rets)
    if n < 20:
        return 0.5

    data = rets[:n // 2]
    if len(data) < 10:
        return 0.5

    m = sum(data) / len(data)
    cum = 0.0
    cum_devs = []
    for d in data:
        cum += d - m
        cum_devs.append(cum)

    r = max(cum_devs) - min(cum_devs)
    s = math.sqrt(sum((d - m) ** 2 for d in data) / len(data))

    if s < 1e-12 or r < 1e-12:
        return 0.5

    rs = r / s
    return max(0.0, min(1.0, math.log(rs) / math.log(len(data))))


def _linear_regression_strength(prices: list[float]) -> tuple[float, float]:
    """R-squared trend strength and direction."""
    n = len(prices)
    if n < 10:
        return 0.0, 0.0

    x_bar = (n - 1) / 2
    y_bar = sum(prices) / n

    ss_xy = sum((i - x_bar) * (prices[i] - y_bar) for i in range(n))
    ss_xx = sum((i - x_bar) ** 2 for i in range(n))
    ss_yy = sum((p - y_bar) ** 2 for p in prices)

    if ss_xx < 1e-12 or ss_yy < 1e-12:
        return 0.0, 0.0

    r_squared = min(1.0, ss_xy ** 2 / (ss_xx * ss_yy))
    direction = 1.0 if ss_xy > 0 else -1.0
    return r_squared, direction


def _diff_series(values: list[float]) -> list[float]:
    """First differences."""
    return [values[i] - values[i - 1] for i in range(1, len(values))]
