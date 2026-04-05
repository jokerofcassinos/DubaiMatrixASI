"""
SOLÉNN v2 — Black Swan & Extreme Event Agents (Ω-E01 to Ω-E162)
Transmuted from v1:
  - black_swan_agent.py: Extreme event detection via tail analysis
  - omega_extreme.py: Omega index for extreme tail events
  - kolmogorov_inertia_agent.py: Kolmogorov complexity + inertia
  - feynman_path_agent.py: Path integral for extreme scenarios
  - quantum_field_agents.py: Quantum field analogy for market creation

Protocol 3-6-9: 162 vetores planejados
  Concept 1 — Extreme Event Detection (Ω-E01 to Ω-E54): Heavy tail
    modeling via GPD (Generalized Pareto Distribution), EVT-based
    risk metrics (VaR, CVaR), crash probability estimation, tail
    risk early warning signals
  Concept 2 — Kolmogorov Complexity & Inertia (Ω-E55 to Ω-E108):
    Algorithmic complexity as predictability proxy, Kolmogorov
    complexity rate for pattern detection, market inertia via
    complexity analysis, compressibility as trend strength
  Concept 3 — Path Integral Extreme Scenarios (Ω-E109 to Ω-E162):
    Path integral over rare event trajectories, action-based
    scenario weighting, quantum tunneling probability through
    barriers, field excitation events
"""

from __future__ import annotations

import math
import random
from collections import deque
from typing import Optional


# ──────────────────────────────────────────────────────────────
# Ω-E01 to Ω-E18: Extreme Tail Risk Detection (EVT/GPD)
# ──────────────────────────────────────────────────────────────

class ExtremeTailDetector:
    """
    Ω-E01 to Ω-E09: Detect extreme tail events using EVT.

    Transmuted from v1 black_swan_agent.py:
    v1: Simple tail percentile tracking
    v2: Full Extreme Value Theory framework with GPD fitting,
    Hill estimator for tail index, VaR/CVaR estimation,
    and exceedance probability via Pickands-Balkema-De Haan theorem.
    """

    def __init__(
        self,
        window_size: int = 500,
        threshold_percentile: float = 0.95,
    ) -> None:
        self._window = window_size
        self._threshold_p = threshold_percentile
        self._returns: deque[float] = deque(maxlen=window_size)
        self._exceedances: deque[float] = deque(maxlen=window_size)

    def update(self, price: float) -> dict:
        """Ω-E03: Update with new price, compute tail risk metrics."""
        prev = self._returns[-1] if self._returns else None
        if len(self._returns) > 0 and len(self._prices_data) > 0:
            pass  # handled below

        if not hasattr(self, '_prices_data'):
            self._prices_data: deque[float] = deque(maxlen=self._window)

        if self._prices_data:
            prev_price = self._prices_data[-1]
            if prev_price != 0:
                ret = (price - prev_price) / abs(prev_price)
            else:
                ret = 0.0
            self._returns.append(ret)
        self._prices_data.append(price)

        if len(self._returns) < 50:
            return {"state": "WARMING_UP", "tail_risk": 0.0}

        rets = list(self._returns)

        # Ω-E04: Threshold for exceedances
        threshold = _percentile(rets, self._threshold_p)
        threshold_low = _percentile(rets, 1.0 - self._threshold_p)

        # Ω-E05: Exceedances (both tails)
        upper_exceedances = [r - threshold for r in rets if r > threshold]
        lower_exceedances = [threshold_low - r for r in rets if r < threshold_low]

        for e in upper_exceedances:
            self._exceedances.append(e)
        for e in lower_exceedances:
            self._exceedances.append(e)

        # Ω-E06: Hill estimator for tail index
        tail_index = self._hill_estimator(rets)

        # Ω-E07: GPD fit for exceedances
        gpd_shape, gpd_scale = self._fit_gpd(list(self._exceedances))

        # Ω-E08: VaR and CVaR estimation
        var_95 = _value_at_risk(rets, 0.95)
        var_99 = _value_at_risk(rets, 0.99)
        cvar_95 = _conditional_var(rets, 0.95)
        cvar_99 = _conditional_var(rets, 0.99)

        # Ω-E09: Tail risk score
        tail_risk = 0.0
        if tail_index > 0:
            tail_risk += min(1.0, tail_index / 5.0) * 0.4
        if abs(gpd_shape) > 0.3:
            tail_risk += min(1.0, abs(gpd_shape) / 1.0) * 0.3
        if len(upper_exceedances) > 0:
            tail_risk += min(1.0, len(upper_exceedances) / 10.0) * 0.3

        return {
            "tail_index": tail_index,
            "gpd_shape": gpd_shape,
            "gpd_scale": gpd_scale,
            "var_95": var_95,
            "var_99": var_99,
            "cvar_95": cvar_95,
            "cvar_99": cvar_99,
            "tail_risk_score": min(1.0, tail_risk),
            "n_upper_exceedances": len(upper_exceedances),
            "n_lower_exceedances": len(lower_exceedances),
            "is_extreme_risk": tail_risk > 0.6,
        }

    def _hill_estimator(self, rets: list[float], k_frac: float = 0.1) -> float:
        """Ω-E10: Hill estimator for tail index (heavy tail detection)."""
        n = len(rets)
        if n < 20:
            return 2.0  # thin tail default

        abs_rets = sorted(abs(r) for r in rets)
        k = max(2, int(n * k_frac))

        # Top k order statistics
        top_k = abs_rets[n - k:]

        if not top_k or top_k[0] <= 0:
            return 2.0

        log_ratios = [math.log(top_k[i] / top_k[0]) for i in range(k)]
        gamma = sum(log_ratios) / k if k > 0 else 0

        return 1.0 / max(0.01, gamma) if gamma > 0 else 10.0

    def _fit_gpd(self, exceedances: list[float]) -> tuple[float, float]:
        """Ω-E11: Fit Generalized Pareto Distribution to exceedances."""
        if not exceedances or len(exceedances) < 5:
            return (0.0, 1.0)  # exponential default

        n = len(exceedances)
        mean_ex = sum(exceedances) / n
        var_ex = sum((x - mean_ex) ** 2 for x in exceedances) / n

        # Method of moments estimator for GPD
        if var_ex > 0 and mean_ex > 0:
            shape = 0.5 * (1.0 - (mean_ex ** 2 / var_ex))
            scale = mean_ex * (1.0 - shape)
        else:
            shape = 0.0
            scale = mean_ex

        return (shape, max(1e-12, scale))


# ──────────────────────────────────────────────────────────────
# Ω-E19 to Ω-E27: Omega Index for Extreme Events
# ──────────────────────────────────────────────────────────────

class OmegaIndex:
    """
    Ω-E19 to Ω-E27: Omega index for extreme event characterization.

    Transmuted from v1 omega_extreme.py:
    v1: Basic omega ratio
    v2: Full omega index computation with threshold optimization,
    temporal decomposition, and extremity scoring.
    """

    def __init__(self, window_size: int = 200) -> None:
        self._window = window_size
        self._returns: deque[float] = deque(maxlen=window_size)

    def update(self, price: float) -> dict:
        """Ω-E21: Update and compute omega index."""
        if hasattr(self, '_prices_data') and self._prices_data:
            prev = self._prices_data[-1]
            if prev != 0:
                self._returns.append((price - prev) / abs(prev))
        if not hasattr(self, '_prices_data'):
            self._prices_data: deque[float] = deque(maxlen=self._window)
        self._prices_data.append(price)

        if len(self._returns) < 30:
            return {"omega": 0.0, "state": "WARMING_UP"}

        rets = list(self._returns)

        # Ω-E22: Omega ratio at multiple thresholds
        thresholds = [-0.1, -0.05, -0.02, 0.0, 0.01, 0.02, 0.05]
        omega_values = {}
        for tau in thresholds:
            omega_values[tau] = _omega_ratio(rets, tau)

        # Ω-E23: Optimized threshold (where Omega is maximized)
        best_tau = max(thresholds, key=lambda t: omega_values[t])
        best_omega = omega_values[best_tau]

        # Ω-E24: Tail omega - only extreme returns
        extreme_rets = [r for r in rets if abs(r) > _percentile([abs(x) for x in rets], 0.95)]
        tail_omega = _omega_ratio(extreme_rets, 0.0) if extreme_rets else 1.0

        # Ω-E25: Temporal decomposition
        # Split into first half vs second half omega
        mid = len(rets) // 2
        omega_1 = _omega_ratio(rets[:mid], 0.0)
        omega_2 = _omega_ratio(rets[mid:], 0.0)
        omega_trend = omega_2 - omega_1  # positive = improving

        return {
            "omega_values": {str(k): round(v, 3) for k, v in omega_values.items()},
            "best_threshold": best_tau,
            "best_omega": best_omega,
            "tail_omega": tail_omega,
            "omega_trend": omega_trend,
            "is_favorable": best_omega > 1.0 and omega_trend > 0,
        }


# ──────────────────────────────────────────────────────────────
# Ω-E28 to Ω-E36: Kolmogorov Complexity & Inertia
# ──────────────────────────────────────────────────────────────

class KolmogorovInertiaDetector:
    """
    Ω-E28 to Ω-E36: Kolmogorov complexity as predictability proxy.

    Transmuted from v1 kolmogorov_inertia_agent.py:
    v1: Simple Lempel-Ziv compression ratio
    v2: Full complexity analysis with LZ78 approximation,
    market inertia measurement, compressibility as trend
    strength indicator.
    """

    def __init__(self, window_size: int = 200) -> None:
        self._window = window_size
        self._prices: deque[float] = deque(maxlen=window_size)
        self._history: deque[dict] = deque(maxlen=200)

    def update(self, price: float) -> dict:
        """Ω-E30: Update compression analysis."""
        self._prices.append(price)

        if len(self._prices) < 20:
            return {"state": "WARMING_UP"}

        # Ω-E31: Encode price changes as discrete sequence
        diffs = [(self._prices[i] - self._prices[i - 1])
                 for i in range(1, len(self._prices))]
        sequence = _discretize(diffs, n_bins=4)

        # Ω-E32: Lempel-Ziv complexity approximation
        lz_complexity = _lz_complexity(sequence)

        # Ω-E33: Normalized complexity (0-1)
        n = len(sequence)
        max_complexity = n / math.log2(n) if n > 1 else 1.0
        normalized_complexity = min(1.0, lz_complexity / max_complexity)

        # Ω-E34: Compressibility as trend strength
        # Low complexity = compressible = trending/deterministic
        # High complexity = incompressible = noisy
        compressibility = 1.0 - normalized_complexity
        is_trending = compressibility > 0.5

        # Ω-E35: Market inertia
        # If recent complexity has been decreasing, momentum building
        self._history.append({
            "complexity": normalized_complexity,
            "compressibility": compressibility,
        })
        if len(self._history) >= 5:
            recent = list(self._history)[-5:]
            prev_complexity = recent[0]["complexity"]
            current_complexity = recent[-1]["complexity"]
            inertia = -(current_complexity - prev_complexity)  # decreasing complexity = +inertia
        else:
            inertia = 0.0

        # Ω-E36: Predictability estimate
        predictability = max(0.0, compressibility * (1.0 + inertia))

        return {
            "lz_complexity": lz_complexity,
            "normalized_complexity": normalized_complexity,
            "compressibility": compressibility,
            "is_trending": is_trending,
            "market_inertia": inertia,
            "predictability": predictability,
            "sequence_length": n,
        }


# ──────────────────────────────────────────────────────────────
# Ω-E37 to Ω-E45: Path Integral Extreme Scenarios
# ──────────────────────────────────────────────────────────────

class PathIntegralScenarios:
    """
    Ω-E37 to Ω-E45: Path integral over rare event trajectories.

    Transmuted from v1 feynman_path_agent.py:
    v1: Monte Carlo crash scenarios
    v2: Path integral approximation with action-based weighting,
    quantum tunneling probability through barriers.
    """

    def __init__(self, n_paths: int = 100, horizon: int = 20) -> None:
        self._n_paths = n_paths
        self._horizon = horizon
        self._returns: deque[float] = deque(maxlen=500)

    def update(self, price: float) -> dict:
        """Ω-E39: Generate path integral scenarios."""
        if hasattr(self, '_prices_data') and self._prices_data:
            prev = self._prices_data[-1]
            if prev != 0:
                self._returns.append((price - prev) / abs(prev))
        if not hasattr(self, '_prices_data'):
            self._prices_data: deque[float] = deque(maxlen=500)
        self._prices_data.append(price)

        if len(self._returns) < 30:
            return {"state": "WARMING_UP"}

        rets = list(self._returns)
        mu = sum(rets) / len(rets)
        sigma = math.sqrt(sum((r - mu) ** 2 for r in rets) / len(rets))
        sigma = max(sigma, 1e-6)

        current_price = price

        # Ω-E40: Generate paths with action-based weighting
        extreme_paths = 0
        total_action = 0.0
        crash_count = 0

        for _ in range(self._n_paths):
            path = [current_price]
            action = 0.0
            for step in range(self._horizon):
                # Path with fat-tailed innovations
                innovation = _fat_tail_sample(mu, sigma)
                new_price = path[-1] * (1 + innovation)
                path.append(new_price)

                # Action contribution (deviation from classical path)
                action += innovation ** 2

            total_action += action

            max_draw = min(0.0, (min(path) - current_price) / current_price)
            if max_draw < -0.05:
                extreme_paths += 1
            if max_draw < -0.10:
                crash_count += 1

        # Ω-E41: Tunneling probability through barrier
        # P(tunnel) ~ exp(-2 * integral sqrt(2m(V-E))/hbar dx)
        # Approximation: tunneling through resistance level
        barrier_distance = 0.05  # 5% barrier
        tunneling_prob = math.exp(-2 * barrier_distance / sigma)

        return {
            "crash_probability": extreme_paths / self._n_paths,
            "extreme_crash_probability": crash_count / self._n_paths,
            "avg_action": total_action / self._n_paths,
            "tunneling_probability": tunneling_prob,
            "n_paths": self._n_paths,
            "horizon_steps": self._horizon,
            "is_tail_risk_elevated": extreme_paths / self._n_paths > 0.05,
        }


# ──────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────

def _percentile(values: list[float], p: float) -> float:
    """Compute p-th percentile of values."""
    if not values:
        return 0.0
    sorted_v = sorted(values)
    idx = int(p * (len(sorted_v) - 1))
    return sorted_v[idx]


def _value_at_risk(returns: list[float], confidence: float) -> float:
    """Compute Value at Risk at given confidence level."""
    return -_percentile(returns, 1.0 - confidence)


def _conditional_var(returns: list[float], confidence: float) -> float:
    """Compute Conditional VaR (Expected Shortfall)."""
    var = _value_at_risk(returns, confidence)
    tail = [-r for r in returns if -r > var]
    return sum(tail) / len(tail) if tail else var


def _omega_ratio(returns: list[float], threshold: float = 0.0) -> float:
    """Compute Omega ratio at threshold."""
    gains = [r - threshold for r in returns if r > threshold]
    losses = [threshold - r for r in returns if r < threshold]
    sum_gains = sum(gains) if gains else 0.0
    sum_losses = sum(losses) if losses else 1e-12
    return sum_gains / max(sum_losses, 1e-12)


def _discretize(values: list[float], n_bins: int = 4) -> list[str]:
    """Discretize continuous values into symbol sequence."""
    if not values:
        return []
    min_v, max_v = min(values), max(values)
    if min_v == max_v:
        return ["0"] * len(values)
    symbols = []
    for v in values:
        bucket = int((v - min_v) / (max_v - min_v) * n_bins)
        bucket = min(bucket, n_bins - 1)
        symbols.append(str(bucket))
    return symbols


def _lz_complexity(sequence: list[str]) -> int:
    """Lempel-Ziv complexity: count distinct parsed phrases."""
    if not sequence:
        return 0
    n = len(sequence)
    parsed = set()
    i = 0
    while i < n:
        j = i + 1
        while j <= n and tuple(sequence[i:j]) not in parsed:
            j += 1
        # Add the longest new phrase
        phrase = tuple(sequence[i:j - 1]) if j > i + 1 else tuple(sequence[i:i + 1])
        parsed.add(phrase)
        i = j - 1 if j > i + 1 else i + 1
    return len(parsed)


def _fat_tail_sample(mu: float, sigma: float) -> float:
    """Generate fat-tailed innovation via t-distribution approximation."""
    # Use ratio of normals to approximate t(3) distribution
    u1 = random.gauss(0, 1)
    u2 = random.gauss(0, 1)
    u3 = random.gauss(0, 1)
    # Approximate t with 3 df: Z / sqrt(chi2_3 / 3)
    chi2 = u1 ** 2 + u2 ** 2 + u3 ** 2
    if chi2 < 1e-6:
        return mu
    t = random.gauss(0, 1) / math.sqrt(chi2 / 3)
    return mu + sigma * t * 0.5  # scaled for realistic returns
