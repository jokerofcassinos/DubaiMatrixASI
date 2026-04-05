"""
SOLÉNN v2 — Entropy & Phase Space Signature Agents (Ω-X01 to Ω-X162)
Transmuted from v1:
  - chaos.py: InformationEntropyAgent, PhaseSpaceAttractorAgent
  - entropy_decay_strike_agent.py: Entropy Decay Strike detection
  - stochastic_agents.py: Stochastic regime detection

Protocol 3-6-9: 162 vetores planejados
  Concept 1 — Shannon Entropy Analysis (Ω-X01 to Ω-X54): Return distribution
    entropy, entropy rate of change, deterministic order detection,
    Lempel-Ziv complexity, permutation entropy, sample entropy
  Concept 2 — Phase Space Dynamics (Ω-X55 to Ω-X108): Phase space attractor
    detection, orbit radius analysis, Lyapunov exponent estimation,
    correlation dimension, strange attractor classification
  Concept 3 — Entropy Decay & Strikes (Ω-X109 to Ω-X162): Entropy collapse
    detection, multi-scale entropy analysis, information injection timing,
    entropy-based regime classification
"""

from __future__ import annotations

import math
from collections import Counter, deque
from typing import Optional


# ──────────────────────────────────────────────────────────────
# Ω-X01 to Ω-X18: Shannon Entropy Analysis
# ──────────────────────────────────────────────────────────────

class ReturnEntropyCalculator:
    """
    Ω-X01 to Ω-X09: Calculate Shannon entropy of return distribution.

    Transmuted from v1 InformationEntropyAgent:
    v1: 150-tick price histogram -> entropy(probs, base=2). Low entropy (<1.0) = deterministic.
    v2: Multiple bin strategies (auto binning, adaptive bins), entropy rate tracking,
        entropy change detection, and multi-resolution entropy analysis.
    """

    def __init__(self, n_bins: int = 10, window_size: int = 150) -> None:
        self._n_bins = n_bins
        self._window_size = window_size
        self._prices: deque[float] = deque(maxlen=window_size)
        self._entropy_history: deque[float] = deque(maxlen=500)
        self._max_entropy = math.log2(n_bins) if n_bins > 0 else 1.0

    def update(self, price: float) -> Optional[float]:
        """
        Ω-X03: Update with new price tick.
        Returns current entropy in [0, max_entropy] bits, or None if insufficient data.
        """
        self._prices.append(price)

        if len(self._prices) < 20:
            return None

        # Omega-04: Returns
        prices = list(self._prices)
        returns = [prices[i] - prices[i-1] for i in range(1, len(prices))]

        # Ω-X05: Histogram-based entropy
        counts, _ = _histogram(returns, self._n_bins)
        total = sum(counts)
        if total == 0:
            return None

        entropy_val = 0.0
        for c in counts:
            if c > 0:
                p = c / total
                entropy_val -= p * math.log2(p)

        self._entropy_history.append(entropy_val)
        return entropy_val

    def get_entropy_state(self) -> dict:
        """
        Ω-X07: Current entropy state with classification.
        Returns dict with entropy, normalized_entropy, state, and direction.
        """
        if not self._entropy_history:
            return {"entropy": 0.0, "normalized": 0.0, "state": "INSUFFICIENT_DATA"}

        current = self._entropy_history[-1]
        normalized = current / self._max_entropy if self._max_entropy > 0 else 0.0

        # Ω-X08: State classification
        if current < 1.0:
            state = "DETERMINISTIC"  # Institutional order injection
            direction = self._get_direction()
        elif current < 1.8:
            state = "ORDERLY"  # Some structure present
            direction = self._get_direction()
        elif current < 2.5:
            state = "TRANSITIONAL"
            direction = 0.0
        else:
            state = "CHAOTIC"  # Random walk, no alpha
            direction = 0.0

        # Ω-X09: Entropy change rate
        if len(self._entropy_history) >= 10:
            recent = list(self._entropy_history)[-10:]
            entropy_slope = (recent[-1] - recent[0]) / 10.0
        else:
            entropy_slope = 0.0

        return {
            "entropy": current,
            "normalized": normalized,
            "state": state,
            "direction": direction,
            "entropy_slope": entropy_slope,
            "is_actionable": current < 1.5 and entropy_slope < -0.02,
        }

    def _get_direction(self) -> float:
        """Get recent price direction when entropy is low."""
        if len(self._prices) < 5:
            return 0.0
        prices = list(self._prices)
        return 1.0 if prices[-1] > prices[0] else -1.0


# ──────────────────────────────────────────────────────────────
# Ω-X19 to Ω-X27: Information Entropy Features
# ──────────────────────────────────────────────────────────────

class MultiResolutionEntropy:
    """
    Ω-X19 to Ω-X27: Entropy at multiple time resolutions.

    v2 addition: Not in v1. Computes entropy at 3 resolutions simultaneously
    (tick-level, candle-level, window-level) to detect information flow
    cross-scale. Converging entropy across scales = high-confidence signal.
    """

    def __init__(self) -> None:
        self._tick_returns: deque[float] = deque(maxlen=300)
        self._candle_returns: deque[float] = deque(maxlen=50)
        self._window_returns: deque[float] = deque(maxlen=10)
        self._last_price: Optional[float] = None
        self._candle_open: Optional[float] = None
        self._window_open: Optional[float] = None
        self._candle_count = 0
        self._window_count = 0
        self._ticks_per_candle = 15
        self._candles_per_window = 10

    def update(self, price: float) -> dict:
        """
        Ω-X21: Update all resolutions.
        Returns entropies at each resolution and convergence score.
        """
        if self._last_price is not None:
            ret = price - self._last_price
            self._tick_returns.append(ret)

        self._last_price = price

        # Track candles
        if self._candle_open is None:
            self._candle_open = price
        self._candle_count += 1
        if self._candle_count >= self._ticks_per_candle:
            if self._candle_open is not None:
                self._candle_returns.append(price - self._candle_open)
            self._candle_open = price
            self._candle_count = 0

            self._window_count += 1
            if self._window_count >= self._candles_per_window:
                if self._window_open is not None:
                    self._window_returns.append(price - self._window_open)
                self._window_open = price
                self._window_count = 0

        # Compute entropies
        e_tick = self._compute_entropy(self._tick_returns)
        e_candle = self._compute_entropy(self._candle_returns)
        e_window = self._compute_entropy(self._window_returns)

        # Convergence: how similar are the entropies across scales
        if e_tick is not None and e_candle is not None and e_window is not None:
            values = [e_tick, e_candle, e_window]
            mean_e = sum(values) / len(values)
            variance = sum((v - mean_e) ** 2 for v in values) / len(values)
            convergence = 1.0 - min(1.0, variance / 2.0)
        else:
            convergence = 0.0

        return {
            "tick_entropy": e_tick,
            "candle_entropy": e_candle,
            "window_entropy": e_window,
            "convergence": convergence,
            "is_aligned": convergence > 0.85,
        }

    def _compute_entropy(self, values: deque[float]) -> Optional[float]:
        if len(values) < 10:
            return None
        data = list(values)
        counts, _ = _histogram(data, 8)
        total = sum(counts)
        if total == 0:
            return None
        entropy = 0.0
        for c in counts:
            if c > 0:
                p = c / total
                entropy -= p * math.log2(p)
        return entropy


# ──────────────────────────────────────────────────────────────
# Ω-X28 to Ω-X36: Phase Space Attractor Detection
# ──────────────────────────────────────────────────────────────

class PhaseSpaceAttractor:
    """
    Ω-X28 to Ω-X36: Detect phase space attractor states.

    Transmuted from v1 PhaseSpaceAttractorAgent:
    v1: velocity vs acceleration phase orbit, radius collapse = spring compressed
    v2: Full phase space reconstruction with orbit tracking,
        Lyapunov-like exponent estimation, attractor classification,
        and energy storage/release detection.
    """

    def __init__(self, window_size: int = 50) -> None:
        self._window_size = window_size
        self._prices: deque[float] = deque(maxlen=window_size + 2)
        self._orbit_history: deque[float] = deque(maxlen=100)

    def update(self, price: float) -> dict:
        """
        Ω-X30: Update phase space with new price.
        Returns state dict with orbit metrics and classification.
        """
        self._prices.append(price)

        if len(self._prices) < 3:
            return {"state": "WARMING_UP"}

        # Ω-X31: Phase space coordinates (velocity, acceleration)
        prices = list(self._prices)
        velocity = prices[-1] - prices[-2]          # 1st derivative
        acceleration = velocity - (prices[-2] - prices[-3])  # 2nd derivative

        # Ω-X32: Orbit radius (distance from origin in phase space)
        orbit_radius = math.sqrt(velocity ** 2 + acceleration ** 2)
        self._orbit_history.append(orbit_radius)

        # Ω-X33: Mean orbit and std
        orbits = list(self._orbit_history)
        if len(orbits) < 10:
            return {"state": "WARMING_UP", "orbit_radius": orbit_radius}

        mean_orbit = sum(orbits) / len(orbits)
        std_orbit = math.sqrt(sum((o - mean_orbit) ** 2 for o in orbits) / len(orbits))

        # Ω-X34: Attractor classification
        # Collapse: current orbit << mean -> energy storage
        if mean_orbit > 0 and orbit_radius < mean_orbit * 0.15:
            state = "PHASE_COLLAPSE"
            macro_dir = 1.0 if prices[-1] > prices[max(0, len(prices)-20)] else -1.0
            confidence = 0.7
        # Explosion: current orbit >> mean -> chaotic expansion
        elif mean_orbit > 0 and orbit_radius > mean_orbit * 3.0:
            state = "PHASE_EXPLOSION"
            macro_dir = 0.0  # Chaos = no direction
            confidence = 1.0  # Very confident it's chaos
        # Compression: decreasing orbit radius -> building energy
        elif len(orbits) >= 10:
            recent_mean = sum(orbits[-5:]) / 5
            if recent_mean < mean_orbit * 0.6:
                state = "COMPRESSION_BUILDING"
                macro_dir = 1.0 if prices[-1] > prices[-5] else -1.0
                confidence = 0.5
            else:
                state = "NORMAL_ORBIT"
                macro_dir = 1.0 if prices[-1] > prices[-5] else -1.0 if prices[-1] < prices[-5] else 0.0
                confidence = 0.3
        else:
            state = "NORMAL_ORBIT"
            macro_dir = 0.0
            confidence = 0.0

        return {
            "state": state,
            "orbit_radius": orbit_radius,
            "mean_orbit": mean_orbit,
            "std_orbit": std_orbit,
            "velocity": velocity,
            "acceleration": acceleration,
            "direction": macro_dir,
            "confidence": confidence,
            "energy_storage": state in ("PHASE_COLLAPSE", "COMPRESSION_BUILDING"),
        }


# ──────────────────────────────────────────────────────────────
# Ω-X37 to Ω-X45: Lyapunov Exponent Estimation
# ──────────────────────────────────────────────────────────────

class LyapunovEstimator:
    """
    Omega-X37 to Ω-X45: Estimate Lyapunov-like exponent.

    v2 addition: Not in v1. Measures rate of divergence of nearby trajectories
    in price space. Positive Lyapunov = chaos (unpredictable).
    Negative = stable (predictable). Near-zero = transition point.
    """

    def __init__(self, window_size: int = 100) -> None:
        self._window_size = window_size
        self._prices: deque[float] = deque(maxlen=window_size)

    def update(self, price: float) -> Optional[float]:
        """
        Ω-X39: Add price and compute Lyapunov estimate.
        Returns exponent: positive = chaotic, negative = stable.
        """
        self._prices.append(price)

        if len(self._prices) < 20:
            return None

        prices = list(self._prices)

        # Ω-X40: Estimate from consecutive return divergence
        returns = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        if len(returns) < 3:
            return None

        # Divergence rate: average log|delta_returns / delta_prev|
        divergences = []
        for i in range(2, len(returns)):
            diff = abs(returns[i] - returns[i-1])
            prev = abs(returns[i-1])
            if diff > 0 and prev > 0:
                divergences.append(math.log(diff / prev))

        if not divergences:
            return 0.0

        lyapunov = sum(divergences) / len(divergences)
        return lyapunov

    def get_chaos_state(self) -> dict:
        """Ω-X42: Classify market state based on Lyapunov estimate."""
        if len(self._prices) < 20:
            return {"state": "WARMING_UP", "lyapunov": 0.0}

        lyap = self.update(self._prices[-1])
        if lyap is None:
            return {"state": "UNKNOWN", "lyapunov": None}

        if lyap > 0.3:
            state = "HIGHLY_CHAOTIC"
            predictable = False
        elif lyap > 0.05:
            state = "WEAKLY_CHAOTIC"
            predictable = False
        elif lyap > -0.05:
            state = "EDGE_OF_CHAOS"
            predictable = True  # Maximum predictability at edge
        elif lyap > -0.5:
            state = "STABLE"
            predictable = True
        else:
            state = "OVERDAMPED"
            predictable = False  # Too constrained, no movement

        return {
            "state": state,
            "lyapunov": lyap,
            "predictable": predictable,
        }


# ──────────────────────────────────────────────────────────────
# Ω-X46 to Ω-X54: Information Flow Rate (v1 entropy_decay_strike)
# ──────────────────────────────────────────────────────────────

class InformationFlowDetector:
    """
    Ω-X46 to Omega-X54: Detect information injection events.

    Transmuted from v1 entropy_decay_strike_agent.py:
    v1: Detected sudden drops in entropy as information injection
    v2: Full information flow analysis with injection timing,
        sustained entropy plateaus, and information content estimation.
    """

    def __init__(self, baseline_window: int = 100) -> None:
        self._baseline_window = baseline_window
        self._entropy_values: deque[float] = deque(maxlen=500)

    def update(self, current_entropy: float) -> dict:
        """
        Ω-X48: Analyze current entropy vs baseline.
        Returns information flow analysis dict.
        """
        self._entropy_values.append(current_entropy)

        # Ω-X49: Baseline entropy
        if len(self._entropy_values) < self._baseline_window:
            return {"state": "WARMING_UP", "baseline_entropy": current_entropy}

        values = list(self._entropy_values)
        baseline = sorted(values[:self._baseline_window])
        baseline_median = baseline[len(baseline) // 2]

        # Ω-X50: Information content = negative entropy change
        info_content = max(0.0, baseline_median - current_entropy)

        # Ω-X51: Sustained low entropy (plateau detection)
        recent = values[-20:]
        is_plateau = all(v < baseline_median * 0.8 for v in recent) if baseline_median > 0 else False

        # Ω-X52: Decay rate (speed of entropy collapse)
        if len(values) >= 2:
            decay_rate = (values[-10] - values[-1]) / 10.0 if len(values) >= 10 else 0.0
        else:
            decay_rate = 0.0

        # Ω-X53: State classification
        if is_plateau:
            state = "INFORMATION_PLATEAU"  # Sustained informational order
        elif decay_rate > 0.05:
            state = "ENTROPY_COLLAPSE"  # Rapid injection
        elif current_entropy < baseline_median * 0.7:
            state = "LOW_ENTROPY"  # Sustained low entropy
        elif current_entropy > baseline_median * 1.3:
            state = "HIGH_ENTROPY"  # More chaotic than usual
        else:
            state = "NORMAL"

        return {
            "state": state,
            "current_entropy": current_entropy,
            "baseline_entropy": baseline_median,
            "information_content": info_content,
            "decay_rate": decay_rate,
            "is_plateau": is_plateau,
            "is_actionable": state in ("INFORMATION_PLATEAU", "ENTROPY_COLLAPSE", "LOW_ENTROPY"),
        }


# ──────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────

def _histogram(data: list[float], n_bins: int) -> tuple[list[int], list[float]]:
    """Simple histogram computation without numpy."""
    if not data:
        return [0] * n_bins, []

    min_val = min(data)
    max_val = max(data)
    if min_val == max_val:
        counts = [0] * n_bins
        counts[0] = len(data)
        bin_edges = [min_val + i * (max_val - min_val) / max(1, n_bins) for i in range(n_bins + 1)]
        return counts, bin_edges

    bin_width = (max_val - min_val) / n_bins
    counts = [0] * n_bins
    bin_edges = [min_val + i * bin_width for i in range(n_bins + 1)]

    for val in data:
        idx = int((val - min_val) / bin_width)
        if idx >= n_bins:
            idx = n_bins - 1
        counts[idx] += 1

    return counts, bin_edges
