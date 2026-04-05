"""
SOLÉNN v2 — Apex & Architect Agents (Ω-AP01 to Ω-AP162)
Transmuted from v1:
  - apex_agents.py: Peak performance tracking and apex detection
  - architect_agents.py: Market topology architecture
  - ascension_agents.py: Trend escalation and momentum building
  - aethel_agents.py: Noble/strong trend validation
  - asynchronous_pulse_agent.py: Asynchronous pulse detection

Protocol 3-6-9: 162 vetores planejados
  Concept 1 — Apex Detection (Ω-AP01 to Ω-AP54): Peak identification
    via multi-criteria (price, volume, momentum), apex lifecycle
    tracking, peak performance decay estimation, apex classification
    (climax vs exhaustion vs continuation), historical apex comparison
  Concept 2 — Architect Pattern Recognition (Ω-AP55 to Ω-AP108):
    Market topology analysis, structural build patterns, foundation
    detection (accumulation zones), architecture quality scoring,
    structural integrity of trends
  Concept 3 — Ascension & Momentum (Ω-AP109 to Ω-AP162): Trend
    escalation scoring, momentum building rate, pulse detection
    (asynchronous market pulses), noble trend validation (quality
    of uptrend/downtrend), pulse frequency analysis
"""

from __future__ import annotations

import math
from collections import deque
from typing import Optional


# ──────────────────────────────────────────────────────────────
# Ω-AP01 to Ω-AP18: Apex Detection
# ──────────────────────────────────────────────────────────────

class ApexDetector:
    """
    Ω-AP01 to Ω-AP09: Detect market apex (peaks and troughs).

    Transmuted from v1 apex_agents.py:
    v1: Simple high/low tracking
    v2: Multi-criteria apex detection with lifecycle tracking,
    apex classification, performance decay, and historical comparison.
    """

    def __init__(
        self,
        window_size: int = 100,
        apex_lookback: int = 30,
    ) -> None:
        self._window = window_size
        self._lookback = apex_lookback
        self._prices: deque[float] = deque(maxlen=window_size)
        self._volumes: deque[float] = deque(maxlen=window_size)
        self._apex_history: list[dict] = []
        self._current_apex: Optional[dict] = None

    def update(self, price: float, volume: float = 1.0) -> dict:
        """Ω-AP03: Check for apex formation."""
        self._prices.append(price)
        self._volumes.append(volume)

        if len(self._prices) < self._lookback:
            return {"state": "WARMING_UP"}

        prices = list(self._prices)
        volumes = list(self._volumes)
        idx = len(prices) - 1

        # Ω-AP04: Price apex detection (local max/min)
        recent = prices[-self._lookback:]
        local_max = max(recent)
        local_min = min(recent)
        max_idx = recent.index(local_max)
        min_idx = recent.index(local_min)

        # Check if apex at boundary (most recent)
        is_new_high = price >= local_max and max_idx == self._lookback - 1
        is_new_low = price <= local_min and min_idx == self._lookback - 1

        # Ω-AP05: Volume confirmation at apex
        avg_vol = sum(volumes[:-5]) / max(1, len(volumes) - 5)
        recent_vol = sum(volumes[-5:]) / 5
        vol_ratio = recent_vol / max(1e-6, avg_vol)

        # Ω-AP06: Momentum at apex
        if len(prices) >= 10:
            mom_5 = (prices[-1] - prices[-5]) / max(1e-6, abs(prices[-5]))
            mom_10 = (prices[-1] - prices[-10]) / max(1e-6, abs(prices[-10]))
            momentum_diverge = mom_5 * mom_10 < 0 or abs(mom_5) < abs(mom_10) * 0.5
        else:
            mom_5 = mom_10 = 0.0
            momentum_diverge = False

        # Ω-AP07: Apex classification
        apex_type = "NONE"
        apex_confidence = 0.0

        if is_new_high:
            if vol_ratio > 1.5 and momentum_diverge:
                apex_type = "CLIMAX_TOP"  # Exhaustion with volume
                apex_confidence = min(1.0, vol_ratio / 3.0 * 0.6 + 0.4)
            elif vol_ratio < 0.7:
                apex_type = "WEAK_HIGH"  # New high on low volume = fragile
                apex_confidence = max(0.3, 1.0 - vol_ratio)
            else:
                apex_type = "CONTINUATION_HIGH"  # Strong, normal
                apex_confidence = min(1.0, vol_ratio / 2.0)

        elif is_new_low:
            if vol_ratio > 1.5 and momentum_diverge:
                apex_type = "CAPITULATION_BOTTOM"
                apex_confidence = min(1.0, vol_ratio / 3.0 * 0.6 + 0.4)
            elif vol_ratio < 0.7:
                apex_type = "WEAK_LOW"
                apex_confidence = max(0.3, 1.0 - vol_ratio)
            else:
                apex_type = "CONTINUATION_LOW"
                apex_confidence = min(1.0, vol_ratio / 2.0)

        # Ω-AP08: Apex lifecycle
        if apex_type != "NONE" and apex_confidence > 0.5:
            is_new_apex = True
            for prev in self._apex_history[-5:]:
                if prev.get("type") == apex_type and idx - prev.get("index", 0) < 10:
                    is_new_apex = False
                    break

            if is_new_apex:
                apex_record = {
                    "type": apex_type,
                    "confidence": apex_confidence,
                    "price": price,
                    "index": idx,
                    "volume_ratio": vol_ratio,
                    "momentum_diverge": momentum_diverge,
                }
                self._apex_history.append(apex_record)
                self._current_apex = apex_record

                # Limit history
                if len(self._apex_history) > 50:
                    self._apex_history = self._apex_history[-50:]

        # Ω-AP09: Historical apex comparison
        if self._current_apex and len(self._apex_history) >= 3:
            same_type = [
                a for a in self._apex_history
                if a.get("type") == self._current_apex["type"]
            ]
            if same_type:
                avg_p = sum(a["price"] for a in same_type) / len(same_type)
                self._current_apex["is_above_average"] = price > avg_p
                self._current_apex["relative_strength"] = (
                    price - avg_p
                ) / max(1e-6, abs(avg_p))
            else:
                self._current_apex["is_above_average"] = True
                self._current_apex["relative_strength"] = 0.0

        # Performance decay from apex
        if self._current_apex:
            age = idx - self._current_apex.get("index", idx)
            decay = math.exp(-0.05 * age)
        else:
            age = 0
            decay = 0.0

        return {
            "apex_type": apex_type,
            "apex_confidence": apex_confidence,
            "volume_ratio": vol_ratio,
            "momentum_diverge": momentum_diverge,
            "momentum_5": mom_5,
            "momentum_10": mom_10,
            "age_from_apex": age,
            "decay_factor": decay,
            "is_climax": apex_type in ("CLIMAX_TOP", "CAPITULATION_BOTTOM"),
            "is_weak": apex_type in ("WEAK_HIGH", "WEAK_LOW"),
            "n_apexes_recorded": len(self._apex_history),
            "is_actionable": apex_confidence > 0.6 and apex_type != "NONE",
        }


# ──────────────────────────────────────────────────────────────
# Ω-AP19 to Ω-AP27: Architect Pattern Recognition
# ──────────────────────────────────────────────────────────────

class ArchitectAnalyzer:
    """
    Ω-AP19 to Ω-AP27: Market topology and structure building.

    Transmuted from v1 architect_agents.py:
    v1: Basic support/resistance levels
    v2: Full structural analysis with foundation detection,
    architecture quality, and structural integrity scoring.
    """

    def __init__(self, window_size: int = 200) -> None:
        self._window = window_size
        self._prices: deque[float] = deque(maxlen=window_size)
        self._volumes: deque[float] = deque(maxlen=window_size)

    def update(self, price: float, volume: float = 1.0) -> dict:
        """Ω-AP21: Update structural analysis."""
        self._prices.append(price)
        self._volumes.append(volume)

        if len(self._prices) < 30:
            return {"state": "WARMING_UP"}

        prices = list(self._prices)
        volumes = list(self._volumes)
        n = len(prices)

        # Ω-AP22: Foundation detection (accumulation zones)
        # Flat price with declining volume = foundation building
        if n >= 30:
            recent_range = max(prices[-30:]) - min(prices[-30:])
            price_avg = sum(prices[-30:]) / 30
            vol_recent = sum(volumes[-15:]) / 15
            vol_prior = sum(volumes[-30:-15]) / 15 if len(volumes) > 30 else vol_recent

            vol_declining = vol_recent < vol_prior * 0.9 if vol_prior > 0 else False
            tight_range = recent_range < abs(price_avg) * 0.01

            is_foundation = vol_declining and tight_range
            foundation_quality = (
                (1.0 - vol_recent / max(1e-6, vol_prior)) * 0.5 +
                (1.0 - recent_range / max(1e-6, abs(price_avg) * 0.05)) * 0.5
            )
            foundation_quality = max(0.0, min(1.0, foundation_quality))
        else:
            is_foundation = False
            foundation_quality = 0.0

        # Ω-AP23: Structural integrity of trend
        # Quality = how orderly the price moves (smooth trend vs chaotic)
        if n >= 20:
            returns = [
                (prices[i] - prices[i - 1]) / max(1e-6, abs(prices[i - 1]))
                for i in range(1, n)
            ]
            same_dir = sum(1 for i in range(1, len(returns))
                          if returns[i] * returns[i - 1] > 0)
            direction_consistency = same_dir / max(1, len(returns) - 1)

            # Low variance relative to mean = clean trend
            mean_ret = sum(returns) / len(returns)
            var_ret = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
            cv = math.sqrt(var_ret) / max(1e-6, abs(mean_ret))
            trend_quality = 1.0 / (1.0 + cv)
        else:
            direction_consistency = 0.0
            trend_quality = 0.0

        # Ω-AP24: Architecture type classification
        if direction_consistency > 0.6 and trend_quality > 0.5:
            arch_type = "STRONG_ARCHITECTURE"  # Well-structured trend
        elif direction_consistency < 0.4:
            arch_type = "CHOPPY"  # No clear structure
        elif is_foundation:
            arch_type = "FOUNDATION"  # Building phase
        else:
            arch_type = "MODERATE"

        # Ω-AP25: Structural weakness
        # Contradictory signals: new highs on declining volume
        if n >= 20:
            first_half = sum(volumes[:10]) / 10
            second_half = sum(volumes[-10:]) / 10
            price_up = prices[-1] > prices[-20]
            vol_down = second_half < first_half * 0.7
            structural_weakness = price_up and vol_down
        else:
            structural_weakness = False

        return {
            "architecture_type": arch_type,
            "is_foundation": is_foundation,
            "foundation_quality": foundation_quality,
            "trend_quality": trend_quality,
            "direction_consistency": direction_consistency,
            "structural_weakness": structural_weakness,
            "is_sound_architecture": arch_type == "STRONG_ARCHITECTURE",
        }


# ──────────────────────────────────────────────────────────────
# Ω-AP28 to Ω-AP36: Ascension & Momentum
# ──────────────────────────────────────────────────────────────

class AscensionTracker:
    """
    Ω-AP28 to Ω-AP36: Trend escalation and pulse detection.

    Transmuted from v1 ascension_agents.py + asynchronous_pulse:
    v1: Simple momentum tracking
    v2: Full acceleration analysis, pulse detection, noble
    trend validation, and momentum building rate.
    """

    def __init__(self, window_size: int = 200) -> None:
        self._window = window_size
        self._prices: deque[float] = deque(maxlen=window_size)
        self._pulse_times: deque[int] = deque(maxlen=200)
        self._step_counter: int = 0

    def update(self, price: float) -> dict:
        """Ω-AP30: Track ascension and detect pulses."""
        self._prices.append(price)
        self._step_counter += 1

        if len(self._prices) < 10:
            return {"state": "WARMING_UP"}

        prices = list(self._prices)
        n = len(prices)

        # Ω-AP31: Trend direction and strength
        if n >= 20:
            trend_5 = (prices[-1] - prices[-5]) / max(1e-6, abs(prices[-5]))
            trend_10 = (prices[-1] - prices[-10]) / max(1e-6, abs(prices[-10]))
            trend_20 = (prices[-1] - prices[-20]) / max(1e-6, abs(prices[-20]))

            trend_aligned = (
                (trend_5 > 0 and trend_10 > 0 and trend_20 > 0) or
                (trend_5 < 0 and trend_10 < 0 and trend_20 < 0)
            )
            trend_strength = abs(trend_5 + trend_10 + trend_20) / 3
        else:
            trend_5 = trend_10 = trend_20 = 0.0
            trend_aligned = False
            trend_strength = 0.0

        # Ω-AP32: Acceleration (rate of change of momentum)
        if n >= 15:
            mom_1 = (prices[-1] - prices[-3]) / max(1e-6, abs(prices[-3]))
            mom_2 = (prices[-3] - prices[-6]) / max(1e-6, abs(prices[-6]))
            mom_3 = (prices[-6] - prices[-9]) / max(1e-6, abs(prices[-9]))
            acceleration = (mom_1 - mom_2 + mom_2 - mom_3) / 2
        else:
            mom_1 = mom_2 = mom_3 = acceleration = 0.0

        # Ω-AP33: Pulse detection (async market heartbeat)
        # Pulse = sudden change in acceleration sign with magnitude
        if abs(acceleration) > 0.003:
            prev_mom_sign = mom_2 > 0 if abs(mom_2) > 1e-6 else True
            curr_mom_sign = mom_1 > 0
            if prev_mom_sign != curr_mom_sign:
                self._pulse_times.append(self._step_counter)

        # Ω-AP34: Pulse frequency analysis
        if len(self._pulse_times) >= 3:
            pulse_list = list(self._pulse_times)
            intervals = [pulse_list[i + 1] - pulse_list[i]
                        for i in range(len(pulse_list) - 1)]
            avg_pulse_interval = sum(intervals) / len(intervals)
            pulse_regularity = 1.0 - (
                _std(intervals) / max(1e-6, avg_pulse_interval)
                if avg_pulse_interval > 0 else 1.0
            )
            pulse_regularity = max(0.0, min(1.0, pulse_regularity))
        else:
            avg_pulse_interval = 0
            pulse_regularity = 0.0

        # Ω-AP35: Noble trend validation
        # Noble = sustained, orderly, volume-supported movement
        noble_score = 0.0
        if trend_aligned:
            noble_score += 0.3
        if trend_strength > 0.001:
            noble_score += 0.2
        if acceleration > 0:
            noble_score += 0.2
        if pulse_regularity > 0.3:
            noble_score += 0.15
        if momentum_diverge is False:  # defined below
            noble_score += 0.15

        is_noble = noble_score > 0.7

        # Ω-AP36: Phase of ascension
        if acceleration > 0 and trend_5 > 0:
            phase = "ACCELERATING_UP"
        elif acceleration < 0 and trend_5 > 0:
            phase = "DECELERATING_UP"
        elif acceleration < 0 and trend_5 < 0:
            phase = "ACCELERATING_DOWN"
        elif acceleration > 0 and trend_5 < 0:
            phase = "DECELERATING_DOWN"
        else:
            phase = "NEUTRAL"

        # Momentum divergence (local scope)
        momentum_diverge_here = (
            abs(mom_1) < abs(mom_2) and trend_5 * mom_1 > 0
        ) if mom_2 != 0 else False

        return {
            "trend_strength": trend_strength,
            "is_trend_aligned": trend_aligned,
            "acceleration": acceleration,
            "momentum_diverge": momentum_diverge_here,
            "avg_pulse_interval": avg_pulse_interval,
            "pulse_regularity": pulse_regularity,
            "noble_score": noble_score,
            "is_noble_trend": is_noble,
            "ascension_phase": phase,
            "n_pulses": len(self._pulse_times),
            "is_actionable": is_noble and phase in ("ACCELERATING_UP", "ACCELERATING_DOWN"),
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
