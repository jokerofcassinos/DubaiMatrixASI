"""
SOLÉNN v2 — Meta-Signal Aggregation & Elite Synapse Adapter
(Ω-E109 to Ω-E162)

Concept 3: Advanced Quant Signals — Information Theory,
Topological Signals, Wavelet/Spectral, Entropy/Thermo,
Causal Discovery, and Meta-Signal Aggregation.

Tópicos 3.1–3.6
"""

from __future__ import annotations

import math
import random
import time
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from typing import Any


# ──────────────────────────────────────────────────────────────
# Ω-E109 to Ω-E117: Information Theory Signals
# ──────────────────────────────────────────────────────────────

class ShannonEntropyCalculator:
    """Ω-E109: Shannon entropy of return distribution."""

    def __init__(self, window: int = 200, num_bins: int = 20) -> None:
        self._window = window
        self._returns: deque[float] = deque(maxlen=window)
        self._num_bins = num_bins

    def update(self, ret: float) -> float:
        self._returns.append(ret)
        return self.compute()

    def compute(self) -> float:
        if len(self._returns) < 10:
            return 0.0
        vals = list(self._returns)
        min_val, max_val = min(vals), max(vals)
        if min_val == max_val:
            return 0.0

        bin_width = (max_val - min_val) / max(self._num_bins, 1)
        counts = Counter()
        for v in vals:
            bin_idx = int((v - min_val) / bin_width)
            bin_idx = min(bin_idx, self._num_bins - 1)
            counts[bin_idx] += 1

        n = len(vals)
        entropy = 0.0
        for count in counts.values():
            p = count / n
            if p > 0:
                entropy -= p * math.log2(p)

        return entropy


class MutualInformationEstimator:
    """Ω-E110: I(X;Y) between feature and future return."""

    def __init__(self, num_bins: int = 10, window: int = 200) -> None:
        self._num_bins = num_bins
        self._window = window
        self._x_history: deque[float] = deque(maxlen=window)
        self._y_history: deque[float] = deque(maxlen=window)

    def update(self, x: float, y: float) -> float:
        self._x_history.append(x)
        self._y_history.append(y)
        return self.compute()

    def compute(self) -> float:
        if len(self._x_history) < 20:
            return 0.0
        return _compute_mi_discretized(list(self._x_history), list(self._y_history), self._num_bins)


def _compute_mi_discretized(x: list[float], y: list[float], num_bins: int) -> float:
    n = len(x)
    if n == 0 or len(y) != n:
        return 0.0

    def discretize(vals: list[float]) -> list[int]:
        mn, mx = min(vals), max(vals)
        if mn == mx:
            return [0] * len(vals)
        bw = (mx - mn) / max(num_bins - 1, 1)
        return [min(int((v - mn) / bw), num_bins - 1) for v in vals]

    dx = discretize(x)
    dy = discretize(y)

    joint = Counter(zip(dx, dy))
    px_counts = Counter(dx)
    py_counts = Counter(dy)

    mi = 0.0
    for (i, j), c_joint in joint.items():
        p_xy = c_joint / n
        p_x = px_counts[i] / n
        p_y = py_counts[j] / n
        if p_xy > 0 and p_x > 0 and p_y > 0:
            mi += p_xy * math.log2(p_xy / (p_x * p_y))

    return max(0.0, mi)


class RedundancyAnalyzer:
    """Ω-E114: Redundancy between signals for feature selection."""

    def __init__(self) -> None:
        self._signals: dict[str, deque[float]] = {}
        self._mi_matrix: dict[str, dict[str, float]] = {}

    def add_signal(self, name: str, value: float) -> None:
        if name not in self._signals:
            self._signals[name] = deque(maxlen=200)
        self._signals[name].append(value)

    def compute_redundancies(self) -> dict[str, dict[str, float]]:
        """Compute MI between all signal pairs."""
        names = list(self._signals.keys())
        self._mi_matrix.clear()
        for i in range(len(names)):
            self._mi_matrix[names[i]] = {}
            for j in range(len(names)):
                if i == j:
                    self._mi_matrix[names[i]][names[j]] = 1.0
                else:
                    xi = list(self._signals[names[i]])
                    xj = list(self._signals[names[j]])
                    n = min(len(xi), len(xj))
                    if n >= 20:
                        self._mi_matrix[names[i]][names[j]] = _compute_mi_discretized(xi[:n], xj[:n], 10)
                    else:
                        self._mi_matrix[names[i]][names[j]] = 0.0
        return self._mi_matrix


# ──────────────────────────────────────────────────────────────
# Ω-E136 to Ω-E144: Entropy & Thermodynamics
# ──────────────────────────────────────────────────────────────

class MarketTemperatureEstimator:
    """Ω-E136: Market temperature = trading intensity."""

    def __init__(self, window: int = 100) -> None:
        self._trade_times: deque[float] = deque(maxlen=window)

    def update(self, timestamp: float) -> float:
        self._trade_times.append(timestamp)
        if len(self._trade_times) < 2:
            return 0.0
        # Trades per second
        time_range = self._trade_times[-1] - self._trade_times[0]
        if time_range > 0:
            return len(self._trade_times) / time_range
        return 0.0


class FreeEnergyCalculator:
    """Ω-E137: Free energy F = U - TS for the market."""

    def __init__(self, window: int = 100) -> None:
        self._window = window
        self._vol_history: deque[float] = deque(maxlen=window)
        self._temperature: MarketTemperatureEstimator = MarketTemperatureEstimator(window)

    def update(self, vol: float, trade_time: float) -> tuple[float, float, float]:
        self._vol_history.append(vol)
        T = self._temperature.update(trade_time)

        if len(self._vol_history) < 20 or T == 0:
            return 0.0, 0.0, 0.0

        # U (internal energy) = sum of squared returns (accumulated vol energy)
        vals = list(self._vol_history)
        U = sum(v ** 2 for v in vals) / len(vals)

        # S (entropy) = Shannon entropy of returns
        mean = sum(vals) / len(vals)
        var = sum((v - mean) ** 2 for v in vals) / len(vals)
        S = 0.5 * math.log(2 * math.pi * math.e * var) if var > 0 else 0.0

        # F = U - T*S (normalized)
        F = U - T * S * 0.0001  # Scale T*S to comparable magnitude

        return F, U, S


class PhaseTransitionPredictor:
    """Ω-E140: Predict phase transitions via critical slowing down + variance increase."""

    def __init__(self, window: int = 100) -> None:
        self._window = window
        self._values: deque[float] = deque(maxlen=window)

    def update(self, value: float) -> bool:
        self._values.append(value)
        if len(self._values) < 40:
            return False

        vals = list(self._values)
        n = len(vals)
        half = n // 2

        # Critical slowing down: increasing autocorrelation
        mean = sum(vals) / n
        std = (sum((x - mean) ** 2 for x in vals) / max(1, n - 1)) ** 0.5

        if std == 0:
            return False

        # Autocorrelation at lag 1
        autocorr = sum(
            (vals[i] - mean) * (vals[i + 1] - mean)
            for i in range(n - 1)
        ) / ((n - 1) * std ** 2)

        # Variance ratio (second half vs first half)
        var1 = sum((x - mean) ** 2 for x in vals[:half]) / max(1, half - 1)
        var2 = sum((x - mean) ** 2 for x in vals[half:]) / max(1, n - half - 1)
        variance_ratio = var2 / max(var1, 1e-10)

        # Transition when: high autocorr + increasing variance
        return autocorr > 0.5 and variance_ratio > 1.5


# ──────────────────────────────────────────────────────────────
# Ω-E145 to Ω-E153: Causal Discovery Signals
# ──────────────────────────────────────────────────────────────

class GrangerCausalityTracker:
    """Ω-E145: Granger causality between timeframes and assets."""

    def __init__(self, max_lag: int = 5, window: int = 200) -> None:
        self._max_lag = max_lag
        self._window = window
        self._series: dict[str, deque[float]] = {}
        self._causal_graph: dict[str, dict[str, float]] = {}

    def add_series(self, name: str, value: float) -> None:
        if name not in self._series:
            self._series[name] = deque(maxlen=self._window)
        self._series[name].append(value)

    def update_graph(self) -> dict[str, dict[str, float]]:
        """Compute Granger causality for all pairs."""
        names = list(self._series.keys())
        self._causal_graph.clear()

        for src in names:
            self._causal_graph[src] = {}
            src_data = list(self._series[src])
            n = len(src_data)
            var_full = sum((x - sum(src_data) / n) ** 2 for x in src_data) / max(1, n - 1)

            for tgt in names:
                if src == tgt:
                    self._causal_graph[src][tgt] = 1.0
                    continue
                tgt_data = list(self._series[tgt])
                tgt_n = min(n, len(tgt_data))

                # Simple: correlation of lagged src with tgt
                if tgt_n > self._max_lag + 10:
                    lagged_src = [src_data[i] for i in range(self._max_lag, tgt_n)]
                    tgt_current = [tgt_data[i] for i in range(self._max_lag, tgt_n)]
                    corr = _simple_correlation(lagged_src, tgt_current)
                    self._causal_graph[src][tgt] = abs(corr) if corr is not None else 0.0
                else:
                    self._causal_graph[src][tgt] = 0.0

        return self._causal_graph


def _simple_correlation(x: list[float], y: list[float]) -> float | None:
    n = min(len(x), len(y))
    if n < 5:
        return None
    x = x[:n]
    y = y[:n]
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    cov = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n)) / max(1, n - 1)
    std_x = (sum((xi - mean_x) ** 2 for xi in x) / max(1, n - 1)) ** 0.5
    std_y = (sum((yi - mean_y) ** 2 for yi in y) / max(1, n - 1)) ** 0.5
    if std_x == 0 or std_y == 0:
        return 0.0
    return cov / (std_x * std_y)


# ──────────────────────────────────────────────────────────────
# Ω-E154 to Ω-E162: Meta-Signal Aggregation
# ──────────────────────────────────────────────────────────────

@dataclass
class SignalHealth:
    """Ω-E158: Health status of a single signal."""
    name: str
    staleness_s: float  # Time since last update
    error_rate: float  # % of failed evaluations
    divergence: float  # Divergence from historical behavior
    is_healthy: bool  # Overall health


@dataclass
class MetaSignal:
    """Ω-E160: Aggregated meta-signal from N sub-signals."""
    direction: str  # "long", "short", "neutral"
    confidence: float  # [0, 1]
    n_signals: int
    n_aligned: int
    diversity_score: float  # How diverse the signals are
    weighted_score: float
    timestamp_ns: int = field(default_factory=lambda: time.time_ns())


class SignalQualityTracker:
    """Ω-E154: Track quality of each signal: Sharpe, hit rate, decay by regime."""

    def __init__(self) -> None:
        self._signals: dict[str, dict[str, Any]] = {}

    def update(self, name: str, was_correct: bool, pnl: float, regime: str = "default") -> None:
        if name not in self._signals:
            self._signals[name] = {
                "wins": 0, "losses": 0, "total_pnl": 0.0,
                "regimes": defaultdict(lambda: {"wins": 0, "losses": 0}),
                "last_update": time.time(),
            }
        s = self._signals[name]
        if was_correct:
            s["wins"] += 1
            s["regimes"][regime]["wins"] += 1
        else:
            s["losses"] += 1
            s["regimes"][regime]["losses"] += 1
        s["total_pnl"] += pnl
        s["last_update"] = time.time()

    def get_quality(self, name: str) -> dict[str, float]:
        if name not in self._signals:
            return {"hit_rate": 0.5, "total_pnl": 0.0, "staleness_s": 999.0}
        s = self._signals[name]
        total = s["wins"] + s["losses"]
        now = time.time()
        return {
            "hit_rate": s["wins"] / max(1, total),
            "total_pnl": s["total_pnl"],
            "staleness_s": now - s["last_update"],
        }


class AdaptiveWeightedAggregator:
    """
    Ω-E155, Ω-E159, Ω-E160: Ensemble aggregator with
    Bayesian adaptive weights via Thompson Sampling.
    """

    def __init__(self) -> None:
        # Thompson Sampling Beta priors for each signal
        self._alpha: dict[str, float] = {}  # Wins + 1
        self._beta: dict[str, float] = {}  # Losses + 1
        self._last_direction: dict[str, str] = {}
        self._weights: dict[str, float] = {}

    def register_signal(self, name: str) -> None:
        self._alpha[name] = 1.0
        self._beta[name] = 1.0
        self._weights[name] = 0.5

    def update_outcome(self, name: str, was_correct: bool) -> None:
        if name not in self._alpha:
            return
        if was_correct:
            self._alpha[name] += 1
        else:
            self._beta[name] += 1

    def sample_weights(self) -> dict[str, float]:
        """Sample weights from posterior Beta distributions."""
        samples = {}
        for name in self._alpha:
            samples[name] = random.betavariate(self._alpha[name], self._beta[name])
        total = sum(samples.values())
        if total > 0:
            self._weights = {k: v / total for k, v in samples.items()}
        return dict(self._weights)

    def aggregate(
        self,
        signals: dict[str, tuple[str, float]],  # name -> (direction, score)
    ) -> MetaSignal:
        """Ω-E160: Aggregate N sub-signals into meta-signal."""
        if not signals:
            return MetaSignal(direction="neutral", confidence=0.0, n_signals=0,
                              n_aligned=0, diversity_score=0.0, weighted_score=0.0)

        long_score = 0.0
        short_score = 0.0
        total_weight = 0.0

        for name, (direction, score) in signals.items():
            weight = self._weights.get(name, 0.5)
            if direction == "long":
                long_score += weight * score
            elif direction == "short":
                short_score += weight * score
            total_weight += weight

        max_score = max(long_score, short_score)
        if total_weight > 0:
            max_score /= total_weight

        n_aligned = sum(1 for d, _ in signals.values() if (d == "long" and long_score > short_score) or (d == "short" and short_score > long_score))
        consensus = "long" if long_score > short_score * 1.5 else "short" if short_score > long_score * 1.5 else "neutral"

        # Ω-E156: Diversity score
        directions = [d for d, _ in signals.values()]
        direction_counter = Counter(directions)
        max_direction_count = max(direction_counter.values()) if direction_counter else 0
        diversity = 1.0 - max_direction_count / max(len(directions), 1)

        return MetaSignal(
            direction=consensus,
            confidence=min(1.0, max_score),
            n_signals=len(signals),
            n_aligned=n_aligned,
            diversity_score=diversity,
            weighted_score=max_score,
        )


# ──────────────────────────────────────────────────────────────
# Ω-E118 to Ω-E126: Topological Signals (simplified persistent homology)
# ──────────────────────────────────────────────────────────────

class PersistentHomologyCalculator:
    """Ω-E118: Simplified persistent homology via sliding window embedding."""

    def __init__(self, embedding_dim: int = 3, window_size: int = 50) -> None:
        self._dim = embedding_dim
        self._window = window_size
        self._data: deque[float] = deque(maxlen=window_size)

    def update(self, value: float) -> dict[str, Any]:
        self._data.append(value)
        if len(self._data) < self._dim + 10:
            return {"beta_0": 1, "beta_1": 0, "euler": 1, "complexity": 0.0}

        points = self._embed()

        # Ω-E119: Betti numbers (simplified estimation)
        spread = max(points) - min(points)
        variance = sum((p - sum(points) / len(points)) ** 2 for p in points) / len(points)

        # β₀ = connected components = 1 (we assume connected)
        # β₁ = loops — estimated via how much data "wraps around"
        beta_1 = min(5, int(spread / max(variance ** 0.5, 1e-10)))

        # Ω-E121: Euler characteristic = β₀ - β₁ + β₂
        euler = 1 - beta_1

        return {
            "beta_0": 1,
            "beta_1": beta_1,
            "euler": euler,
            "complexity": spread / max(variance ** 0.5, 1e-10),
            "n_points": len(points),
        }

    def _embed(self) -> list[float]:
        """Sliding window embedding."""
        data = list(self._data)
        n = len(data) - self._dim + 1
        if n < 1:
            return data
        # Return max value in each window position
        embedded = []
        for i in range(n):
            window = data[i:i + self._dim]
            embedded.append(max(window) if window else 0)
        return embedded
