"""
SOLÉNN v2 — Eschaton & Extreme State Agents (Ω-ES01 to Ω-ES162)
Transmuted from v1:
  - apocalypse_agents.py: Market end-state detection
  - eschaton_agents.py: Terminal event preparation
  - eternity_agents.py: Infinite state pattern tracking
  - singularity_agents.py: Paradigm shift detection
  - elysium_agents.py: Optimal state equilibrium
  - paragon_agents.py: Exemplar pattern identification

Protocol 3-6-9: 162 vetores planejados
  Concept 1 — Apocalyptic State Detection (Ω-ES01 to Ω-ES54):
    Market end-state recognition, terminal cascade detection,
    systemic fragility scoring, crash severity estimation,
    recovery trajectory prediction
  Concept 2 — Singularity & Paradigm Shift (Ω-ES55 to Ω-ES108):
    Regime paradigm shift detection, structural break identification,
    novelty scoring, singularity point detection, phase transition
    energy measurement
  Concept 3 — Eternity & Exemplar Patterns (Ω-ES109 to Ω-ES162):
    Equilibrium state detection, paragon pattern matching,
    infinite state recurrence, quality scoring of current state
    against historical exemplars, Elysium (optimal market) detection
"""

from __future__ import annotations

import math
from collections import deque
from typing import Optional


# ──────────────────────────────────────────────────────────────
# Ω-ES01 to Ω-ES18: Apocalypse / End-State Detection
# ──────────────────────────────────────────────────────────────

class ApocalypseDetector:
    """
    Ω-ES01 to Ω-ES09: Detect market end-states and cascading failures.

    Transmuted from v1 apocalypse_agents.py:
    v1: Simple crash detection
    v2: Full end-state analysis with cascade detection,
    fragility scoring, severity estimation, and recovery pred.
    """

    def __init__(self, window_size: int = 200) -> None:
        self._window = window_size
        self._prices: deque[float] = deque(maxlen=window_size)
        self._volumes: deque[float] = deque(maxlen=window_size)
        self._crash_count: int = 0
        self._last_crash_idx: int = -100

    def update(self, price: float, volume: float = 1.0) -> dict:
        """Ω-ES03: Check for apocalyptic conditions."""
        self._prices.append(price)
        self._volumes.append(volume)

        if len(self._prices) < 30:
            return {"state": "WARMING_UP"}

        prices = list(self._prices)
        volumes = list(self._volumes)
        n = len(prices)
        idx = n - 1

        # Ω-ES04: Drawdown from recent high
        if n >= 30:
            recent_high = max(prices[-60:]) if len(prices) >= 60 else max(prices)
            drawdown = (recent_high - price) / max(1e-6, recent_high)
        else:
            recent_high = max(prices)
            drawdown = 0.0

        # Ω-ES05: Cascade velocity (accelerating decline)
        if n >= 10:
            returns = [
                (prices[i] - prices[i - 1]) / max(1e-6, abs(prices[i - 1]))
                for i in range(max(1, n - 20), n)
            ]
            neg_returns = [r for r in returns if r < 0]
            cascade_len = len(neg_returns)

            # Consecutive negative returns with increasing magnitude
            is_cascade = False
            cascade_acceleration = 0.0
            if len(neg_returns) >= 5:
                magnitudes = [abs(r) for r in neg_returns]
                is_cascade = all(
                    magnitudes[i] >= magnitudes[i - 1] * 0.8
                    for i in range(1, len(magnitudes))
                )
                if len(magnitudes) >= 3:
                    cascade_acceleration = (
                        (magnitudes[-1] - magnitudes[-3]) / max(1e-6, magnitudes[-3])
                    )
        else:
            cascade_len = 0
            is_cascade = False
            cascade_acceleration = 0.0

        # Ω-ES06: Volume panic
        if n >= 20:
            avg_vol = sum(volumes[:-10]) / max(1, len(volumes) - 10)
            panic_vol = sum(volumes[-10:]) / 10
            vol_surge = panic_vol / max(1e-6, avg_vol)
        else:
            avg_vol = panic_vol = 1.0
            vol_surge = 1.0

        # Ω-ES07: Systemic fragility score
        fragility = 0.0
        if drawdown > 0.05:
            fragility += 0.3 * min(3.0, drawdown / 0.05)
        if is_cascade:
            fragility += 0.3 * min(3.0, max(1.0, cascade_len / 3.0))
        if vol_surge > 1.5:
            fragility += 0.2 * min(3.0, vol_surge / 1.5)
        if cascade_acceleration > 0:
            fragility += 0.2 * min(3.0, cascade_acceleration / 0.01)

        fragility = min(1.0, fragility)

        # Ω-ES08: Crash detection
        crash_threshold = 0.7
        is_crash = fragility > crash_threshold and drawdown > 0.03
        if is_crash and idx - self._last_crash_idx > 20:
            self._crash_count += 1
            self._last_crash_idx = idx

        # Ω-ES09: Severity estimation
        severity = fragility * drawdown * 10  # Scale to interpretable range
        severity = min(1.0, severity)

        # Recovery trajectory (early stage)
        if n >= 10 and fragility < 0.5:
            recent_ret = (prices[-1] - prices[-5]) / max(1e-6, abs(prices[-5]))
            recovery_momentum = recent_ret if recent_ret > 0 else 0.0
        else:
            recovery_momentum = 0.0

        # Classification
        if fragility > 0.8:
            stage = "APOCALYPSE"
        elif fragility > 0.5:
            stage = "CRISIS"
        elif drawdown > 0.05:
            stage = "STRESSED"
        elif fragility > 0.3:
            stage = "ELEVATED"
        else:
            stage = "STABLE"

        return {
            "fragility_score": fragility,
            "drawdown_pct": drawdown * 100,
            "is_crash": is_crash,
            "severity": severity,
            "stage": stage,
            "cascade_length": cascade_len,
            "volume_surge": vol_surge,
            "recovery_momentum": recovery_momentum,
            "crash_count": self._crash_count,
            "needs_defensive_action": fragility > 0.5,
        }


# ──────────────────────────────────────────────────────────────
# Ω-ES19 to Ω-ES27: Singularity & Paradigm Shift
# ──────────────────────────────────────────────────────────────

class SingularityDetector:
    """
    Ω-ES19 to Ω-ES27: Paradigm shift and structural break detection.

    Transmuted from v1 singularity_agents.py:
    v1: Simple regime change detection
    v2: Full singularity analysis with structural break testing,
    novelty scoring, transition energy, and paradigm mapping.
    """

    def __init__(self, window_size: int = 200) -> None:
        self._window = window_size
        self._prices: deque[float] = deque(maxlen=window_size)
        self._volumes: deque[float] = deque(maxlen=window_size)
        self._baseline_stats: Optional[dict] = None
        self._shift_count: int = 0

    def update(self, price: float, volume: float = 1.0) -> dict:
        """Ω-ES21: Check for singularity/paradigm shift."""
        self._prices.append(price)
        self._volumes.append(volume)

        if len(self._prices) < 40:
            return {"state": "WARMING_UP"}

        prices = list(self._prices)
        volumes = list(self._volumes)
        n = len(prices)

        # Ω-ES22: Establish baseline (first half)
        if self._baseline_stats is None and n >= 40:
            first_half = prices[:n // 2]
            self._baseline_stats = {
                "mean": sum(first_half) / len(first_half),
                "std": _std(first_half),
                "vol_mean": sum(volumes[:n // 2]) / max(1, n // 2),
            }

        if self._baseline_stats is None:
            return {"state": "CALIBRATING"}

        bl = self._baseline_stats

        # Ω-ES23: Structural break test
        # Compare recent stats vs baseline using t-test approximation
        recent = prices[-n // 4:]
        recent_mean = sum(recent) / len(recent)
        recent_std = _std(recent)

        # t-statistic approximation
        pooled_se = math.sqrt(
            (bl["std"] ** 2 / max(1, n // 2)) +
            (recent_std ** 2 / max(1, len(recent)))
        )
        t_stat = (
            abs(recent_mean - bl["mean"]) / max(1e-6, pooled_se)
            if pooled_se > 0 else 0.0
        )

        # Ω-ES24: Novelty score
        # How novel is the current state vs all historical?
        all_std = _std(prices)
        novelty = abs(recent_mean - bl["mean"]) / max(1e-6, all_std + abs(bl["mean"]) * 0.01)
        novelty = min(1.0, novelty)

        # Ω-ES25: Transition energy
        # Energy released during regime change = volatility spike
        if len(volumes) >= n // 4:
            vol_recent = sum(volumes[-n // 4:]) / (n // 4)
            vol_baseline = bl["vol_mean"]
            transition_energy = (vol_recent / max(1e-6, vol_baseline)) - 1.0
            transition_energy = max(0.0, min(3.0, transition_energy))
        else:
            vol_recent = vol_baseline = 1.0
            transition_energy = 0.0

        # Ω-ES26: Paradigm classification
        is_significant_break = t_stat > 2.0  # Roughly p < 0.05
        is_paradigm_shift = novelty > 0.5 and transition_energy > 0.5

        if is_paradigm_shift:
            if recent_mean > bl["mean"]:
                paradigm = "BULLISH_SHIFT"
            else:
                paradigm = "BEARISH_SHIFT"
            self._shift_count += 1
            # Reset baseline to new paradigm
            self._baseline_stats = {
                "mean": recent_mean,
                "std": recent_std,
                "vol_mean": vol_recent,
            }
        elif is_significant_break:
            paradigm = "MINOR_SHIFT"
        else:
            paradigm = "STABLE"

        return {
            "t_statistic": t_stat,
            "novelty_score": novelty,
            "transition_energy": transition_energy,
            "is_significant_break": is_significant_break,
            "is_paradigm_shift": is_paradigm_shift,
            "paradigm": paradigm,
            "shift_count": self._shift_count,
            "is_actionable": is_paradigm_shift,
        }


# ──────────────────────────────────────────────────────────────
# Ω-ES28 to Ω-ES36: Eternity & Exemplar Patterns
# ──────────────────────────────────────────────────────────────

class EternityTracker:
    """
    Ω-ES28 to Ω-ES36: Equilibrium detection and exemplar matching.

    Transmuted from v1 eternity_agents.py + elysium + paragon:
    v1: Simple pattern matching
    v2: Full exemplar pattern library with quality scoring,
    equilibrium detection, and optimal state identification.
    """

    def __init__(self, window_size: int = 200) -> None:
        self._window = window_size
        self._prices: deque[float] = deque(maxlen=window_size)
        self._volumes: deque[float] = deque(maxlen=window_size)
        self._exemplars: list[dict] = []
        self._equilibrium_history: deque[float] = deque(maxlen=100)

    def update(self, price: float, volume: float = 1.0) -> dict:
        """Ω-ES30: Update equilibrium and exemplar tracking."""
        self._prices.append(price)
        self._volumes.append(volume)

        if len(self._prices) < 30:
            return {"state": "WARMING_UP"}

        prices = list(self._prices)
        volumes = list(self._volumes)
        n = len(prices)

        # Ω-ES31: Equilibrium detection
        # Price near its mean with low oscillation = equilibrium
        if n >= 30:
            mean = sum(prices) / n
            std = _std(prices)
            recent_deviation = abs(prices[-1] - mean) / max(1e-6, std + abs(mean) * 0.01)

            # Oscillation: count reversals
            diffs = [prices[i] - prices[i - 1] for i in range(n - 20, n)]
            reversals = sum(
                1 for i in range(1, len(diffs))
                if diffs[i] * diffs[i - 1] < 0
            )
            reversal_rate = reversals / max(1, len(diffs) - 1)

            # Equilibrium: near mean + moderate oscillation
            eq_score = 1.0 - min(1.0, recent_deviation)
            if 0.3 < reversal_rate < 0.7:
                eq_score *= (1.0 - abs(reversal_rate - 0.5) * 2)  # Peak at 0.5
            else:
                eq_score *= 0.3

            is_equilibrium = eq_score > 0.5
        else:
            mean = std = recent_deviation = reversal_rate = 0.0
            eq_score = 0.0
            is_equilibrium = False

        self._equilibrium_history.append(eq_score)

        # Ω-ES32: Exemplar pattern creation
        # When a high-quality pattern completes, store it
        if is_equilibrium and len(self._exemplars) < 50:
            recent_returns = [
                (prices[i] - prices[i - 1]) / max(1e-6, abs(prices[i - 1]))
                for i in range(max(1, n - 20), n)
            ]
            exemplar = {
                "mean_return": sum(recent_returns) / max(1, len(recent_returns)),
                "volatility": _std(recent_returns),
                "price_range": (max(prices[-20:]) - min(prices[-20:])) / max(1e-6, mean),
                "eq_score": eq_score,
                "index": n,
            }
            # Only store if distinctly different from existing exemplars
            is_new = True
            for ex in self._exemplars[-10:]:
                diff = abs(exemplar["mean_return"] - ex["mean_return"])
                if diff < 0.001:
                    is_new = False
                    break
            if is_new:
                self._exemplars.append(exemplar)

        # Ω-ES33: Paragon scoring (quality ranking)
        if self._exemplars:
            best = max(self._exemplars, key=lambda e: e["eq_score"])
            current_vs_paragon = eq_score / max(1e-6, best["eq_score"])
        else:
            best = {}
            current_vs_paragon = 0.0

        # Ω-ES34: Recurrence detection
        # Are we in a pattern similar to a historical exemplar?
        nearest_similarity = 0.0
        nearest_exemplar_idx = -1
        if self._exemplars:
            for idx, ex in enumerate(self._exemplars):
                # Simple similarity on volatility and return
                if n >= 20:
                    cur_returns = [
                        (prices[i] - prices[i - 1]) / max(1e-6, abs(prices[i - 1]))
                        for i in range(max(1, n - 20), n)
                    ]
                    cur_vol = _std(cur_returns)
                    cur_mean = sum(cur_returns) / max(1, len(cur_returns))

                    vol_sim = 1.0 - min(1.0, abs(cur_vol - ex["volatility"]) / max(1e-6, cur_vol + ex["volatility"]))
                    mean_sim = 1.0 - min(1.0, abs(cur_mean - ex["mean_return"]) / max(1e-6, abs(cur_mean) + abs(ex["mean_return"]) + 1e-6))
                    similarity = (vol_sim + mean_sim) / 2

                    if similarity > nearest_similarity:
                        nearest_similarity = similarity
                        nearest_exemplar_idx = idx

        # Ω-ES35: Elysium (optimal market state)
        # High equilibrium + low volatility + stable reversal rate
        is_elysium = (
            eq_score > 0.6 and
            (std / max(1e-6, mean)) < 0.01 and
            0.3 < reversal_rate < 0.7
        ) if mean != 0 else False

        return {
            "equilibrium_score": eq_score,
            "is_equilibrium": is_equilibrium,
            "reversal_rate": reversal_rate,
            "is_elysium": is_elysium,
            "n_exemplars": len(self._exemplars),
            "current_vs_paragon": current_vs_paragon,
            "nearest_exemplar_similarity": nearest_similarity,
            "is_recurrence": nearest_similarity > 0.7,
            "recurrence_exemplar_idx": nearest_exemplar_idx,
        }


# ──────────────────────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────────────────────

def _std(values: list[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    m = sum(values) / n
    return math.sqrt(sum((v - m) ** 2 for v in values) / n)
