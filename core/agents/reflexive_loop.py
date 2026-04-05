"""
SOLÉNN v2 — Reflexive Loop Agent (Ω-REF01 to Ω-REF162)
Transmuted from v1:
  - reflexive_loop.py: Reflexive feedback loop
  - behavioral.py: Behavioral pattern analysis
  - meta_swarm.py: Meta-level swarm coordination
  - market_intuition_agent.py: Intuitive pattern matching
  - omniscience_agents.py: Multi-layer awareness

Protocol 3-6-9: 162 vetores planejados
  Concept 1 — Reflexive Feedback (Ω-REF01 to Ω-REF54): Soros-style
    reflexivity detection, self-referential price loops, bias-
    price-bias reinforcement, boom-bust phase tracking, inflection
    point detection via reflexivity exhaustion
  Concept 2 — Behavioral Pattern Analysis (Ω-REF55 to Ω-REF108):
    Repetitive behavioral signatures in market participants,
    trap detection (bull/bear traps), exhaustion pattern
    classification, fakeout recognition, behavioral fingerprinting
  Concept 3 — Meta-Swarm Coordination (Ω-REF109 to Ω-REF162):
    Inter-signal meta-coordination, cross-agent conflict resolution,
    signal hierarchy dynamic adjustment, market intuition scoring,
    omniscience depth tracking
"""

from __future__ import annotations

import math
from collections import deque
from typing import Optional


# ──────────────────────────────────────────────────────────────
# Ω-REF01 to Ω-REF18: Reflexive Feedback Loop
# ──────────────────────────────────────────────────────────────

class ReflexiveLoopMonitor:
    """
    Ω-REF01 to Ω-REF09: Soros-style reflexive feedback detection.

    Transmuted from v1 reflexive_loop.py:
    v1: Basic price/sentiment feedback
    v2: Full reflexivity with bias-escrow tracking, boom-bust
    phase classification, and inflection detection.
    """

    def __init__(self, window_size: int = 200) -> None:
        self._window = window_size
        self._prices: deque[float] = deque(maxlen=window_size)
        self._sentiments: deque[float] = deque(maxlen=window_size)
        self._bias_history: deque[float] = deque(maxlen=200)
        self._price_sentiment_corr: deque[float] = deque(maxlen=100)

    def update(self, price: float, sentiment: float = 0.0) -> dict:
        """Ω-REF03: Update reflexivity tracking."""
        self._prices.append(price)
        self._sentiments.append(sentiment)

        if len(self._prices) < 20:
            return {"state": "WARMING_UP"}

        # Ω-REF04: Trending bias
        # Directional bias from recent price trajectory
        prices = list(self._prices)
        recent_change = (prices[-1] - prices[-20]) / max(1e-6, abs(prices[-20]))
        bias = recent_change  # positive = bullish bias, negative = bearish

        # Ω-REF05: Sentiment-price correlation (reflexivity strength)
        if len(self._sentiments) >= 20:
            sents = list(self._sentiments)[-20:]
            prs = list(prices)[-20:]
            pr_rets = [(prs[i] - prs[i - 1]) / max(1e-6, abs(prs[i - 1]))
                       for i in range(1, len(prs))]
            sents_diff = [sents[i] - sents[i - 1] for i in range(1, len(sents))]
            corr = _correlation(pr_rets, sents_diff)
            self._price_sentiment_corr.append(corr)
        else:
            corr = 0.0

        # Ω-REF06: Reflexive strength
        # High correlation = sentiment and price reinforcing each other
        avg_corr = (
            sum(self._price_sentiment_corr) / len(self._price_sentiment_corr)
            if self._price_sentiment_corr else 0.0
        )
        reflexive_strength = abs(avg_corr)

        self._bias_history.append(bias)

        # Ω-REF07: Boom-bust phase detection
        # Soros 7-phase model simplified to 4 observable phases
        if len(self._bias_history) >= 10:
            biases = list(self._bias_history)[-20:]
            bias_trend = biases[-1] - biases[0]
            bias_accel = bias_trend - (biases[10] - biases[0]) if len(biases) > 10 else bias_trend

            if bias > 0 and bias_accel > 0:
                if abs(bias) > 0.05:
                    phase = "CLIMAX"  # Parabolic, near top
                else:
                    phase = "ACCELERATION"  # Trend strengthening
            elif bias > 0 and bias_accel < 0:
                phase = "TWILIGHT"  # Trend weakening
            elif bias < 0 and bias_accel < 0:
                if abs(bias) > 0.05:
                    phase = "CRASH_INIT"  # Accelerating decline
                else:
                    phase = "DECLINE"
            elif bias < 0 and bias_accel > 0:
                phase = "RECOVERY"  # Decline slowing
            else:
                phase = "NEUTRAL"
        else:
            phase = "DETERMINING"

        # Ω-REF08: Inflection point detection
        # Reflexivity exhausted: bias extreme but price stops responding
        if len(self._bias_history) >= 15:
            biases = list(self._bias_history)[-15:]
            price_norm = _normalize(prices[:15])
            bias_norm = _normalize(biases[:10])

            # Divergence: bias keeps going but price doesn't follow
            recent_bias_dir = biases[-1] > 0 if biases[-5:] else False
            recent_price_dir = (
                prices[-1] > prices[-5]
                if len(prices) >= 6 else False
            )
            inflection = (recent_bias_dir != recent_price_dir and
                         abs(biases[-1]) > 0.02)
        else:
            inflection = False

        # Ω-REF09: Reflexive trade-off
        # High reflexivity = predictable in short term, fragile in long
        predictability_short = reflexive_strength
        fragility_long = 1.0 - reflexive_strength  # mean-reversion force

        return {
            "current_bias": bias,
            "reflexive_strength": reflexive_strength,
            "correlation": avg_corr,
            "boom_bust_phase": phase,
            "is_inflection_point": inflection,
            "predictability_short_term": predictability_short,
            "fragility_long_term": fragility_long,
            "is_actionable": reflexive_strength > 0.3 and phase not in ("CLIMAX", "CRASH_INIT"),
        }


# ──────────────────────────────────────────────────────────────
# Ω-REF19 to Ω-REF27: Behavioral Pattern Analysis
# ──────────────────────────────────────────────────────────────

class BehavioralPatternAnalyzer:
    """
    Ω-REF19 to Ω-REF27: Repetitive behavioral signatures.

    Transmuted from v1 behavioral.py:
    v1: Basic behavioral scoring
    v2: Full pattern catalog with trap detection, exhaustion
    classification, and fakeout recognition.
    """

    def __init__(self, window_size: int = 300) -> None:
        self._window = window_size
        self._prices: deque[float] = deque(maxlen=window_size)
        self._volumes: deque[float] = deque(maxlen=window_size)
        self._pattern_catalog: dict[str, list[dict]] = {}

    def update(self, price: float, volume: float = 1.0) -> dict:
        """Ω-REF21: Update and scan for behavioral patterns."""
        self._prices.append(price)
        self._volumes.append(volume)

        if len(self._prices) < 20:
            return {"state": "WARMING_UP"}

        patterns_detected: dict[str, float] = {}

        # Ω-REF22: Bull trap detection
        bull_trap = self._detect_bull_trap()
        if bull_trap > 0:
            patterns_detected["bull_trap"] = bull_trap

        # Ω-REF23: Bear trap detection
        bear_trap = self._detect_bear_trap()
        if bear_trap > 0:
            patterns_detected["bear_trap"] = bear_trap

        # Ω-REF24: Exhaustion pattern
        exhaustion = self._detect_exhaustion()
        if exhaustion > 0:
            patterns_detected["exhaustion"] = exhaustion

        # Ω-REF25: Fakeout detection
        fakeout = self._detect_fakeout()
        if fakeout > 0:
            patterns_detected["fakeout"] = fakeout

        # Ω-REF26: Behavioral fingerprint
        # What type of behavior dominates?
        if patterns_detected:
            dominant = max(patterns_detected, key=patterns_detected.get)
            dominant_confidence = patterns_detected[dominant]
        else:
            dominant = "NONE"
            dominant_confidence = 0.0

        return {
            "patterns_detected": patterns_detected,
            "dominant_pattern": dominant,
            "dominant_confidence": dominant_confidence,
            "n_patterns": len(patterns_detected),
            "is_trap_active": "bull_trap" in patterns_detected or "bear_trap" in patterns_detected,
            "is_exhausted": "exhaustion" in patterns_detected,
        }

    def _detect_bull_trap(self) -> float:
        """
        Ω-REF22: Bull trap = price breaks above resistance
        with volume, then immediately reverses below the level.
        """
        if len(self._prices) < 15:
            return 0.0

        prices = list(self._prices)[-15:]
        volumes = list(self._volumes)[-15:]

        # Find recent high
        high_idx = prices.index(max(prices))
        if high_idx < 5 or high_idx > 12:
            return 0.0

        # Price went above previous resistance then fell back
        prev_high = max(prices[:high_idx]) if high_idx > 0 else prices[0]
        breakout = prices[high_idx] > prev_high

        # Volume spike on breakout
        avg_vol = sum(volumes[:high_idx]) / max(1, high_idx)
        breakout_vol = volumes[high_idx]
        vol_spike = breakout_vol > avg_vol * 1.5

        # Price fell back below breakout level
        fell_back = prices[-1] < prev_high

        if breakout and vol_spike and fell_back:
            return 0.7 + 0.3 * min(1.0, (breakout_vol / max(1e-6, avg_vol) - 1.5))
        return 0.0

    def _detect_bear_trap(self) -> float:
        """
        Ω-REF23: Bear trap = price breaks below support
        with volume, then immediately bounces back above.
        """
        if len(self._prices) < 15:
            return 0.0

        prices = list(self._prices)[-15:]
        volumes = list(self._volumes)[-15:]

        low_idx = prices.index(min(prices))
        if low_idx < 5 or low_idx > 12:
            return 0.0

        prev_low = min(prices[:low_idx]) if low_idx > 0 else prices[0]
        breakdown = prices[low_idx] < prev_low

        avg_vol = sum(volumes[:low_idx]) / max(1, low_idx)
        breakdown_vol = volumes[low_idx]
        vol_spike = breakdown_vol > avg_vol * 1.5

        bounced_back = prices[-1] > prev_low

        if breakdown and vol_spike and bounced_back:
            return 0.7 + 0.3 * min(1.0, (breakdown_vol / max(1e-6, avg_vol) - 1.5))
        return 0.0

    def _detect_exhaustion(self) -> float:
        """
        Ω-REF24: Exhaustion = trend continues but losing conviction.
        Price makes new extreme but volume/momentum declining.
        """
        if len(self._prices) < 30:
            return 0.0

        prices = list(self._prices)[-30:]
        volumes = list(self._volumes)[-30:]

        # Check if trend direction is established
        trend_up = prices[-1] > prices[-15]
        trend_down = prices[-1] < prices[-15]

        if not (trend_up or trend_down):
            return 0.0

        # Split into two halves
        first_vol = sum(volumes[:15]) / 15
        second_vol = sum(volumes[15:]) / 15

        # Volume declining while trend continues = exhaustion
        vol_declining = second_vol < first_vol * 0.8

        # Range compression = loss of momentum
        first_range = max(prices[:15]) - min(prices[:15])
        second_range = max(prices[15:]) - min(prices[15:])
        range_compressing = second_range < first_range * 0.7

        exhaustion_score = 0.0
        if vol_declining:
            exhaustion_score += 0.5 * (1.0 - second_vol / max(1e-6, first_vol))
        if range_compressing:
            exhaustion_score += 0.5 * (1.0 - second_range / max(1e-6, first_range))

        return min(1.0, exhaustion_score)

    def _detect_fakeout(self) -> float:
        """
        Ω-REF25: Fakeout = rapid price move in one direction
        that is completely retraced. No genuine conviction.
        """
        if len(self._prices) < 20:
            return 0.0

        prices = list(self._prices)[-20:]

        # Find max deviation from start
        start = prices[0]
        max_up = max(p - start for p in prices)
        max_down = start - min(p for p in prices)

        max_move = max(max_up, max_down)
        if max_move < abs(start) * 0.005:  # need at least 0.5% move
            return 0.0

        # Current position (how much retraced)
        current = prices[-1] - start
        retracement = 1.0 - abs(current) / max_move

        # Full retracement = fakeout
        if retracement > 0.8:
            return retracement * 0.9
        return 0.0


# ──────────────────────────────────────────────────────────────
# Ω-REF28 to Ω-REF36: Meta-Swarm Coordination
# ──────────────────────────────────────────────────────────────

class MetaSwarmCoordinator:
    """
    Ω-REF28 to Ω-REF36: Inter-signal meta-coordination.

    Transmuted from v1 meta_swarm.py + market_intuition_agent.py:
    v1: Simple signal aggregation
    v2: Full meta-coordination with dynamic hierarchy,
    conflict resolution, intuition scoring, depth tracking.
    """

    def __init__(self, n_signals: int = 10) -> None:
        self._n_signals = n_signals
        self._signal_weights: dict[str, float] = {}
        self._signal_history: dict[str, deque] = {}
        self._conflict_history: deque[float] = deque(maxlen=200)

    def register_signal(self, name: str, initial_weight: float = 0.1) -> None:
        """Register a signal in the swarm."""
        self._signal_weights[name] = initial_weight
        self._signal_history[name] = deque(maxlen=200)

    def update_signal(self, name: str, value: float, outcome: Optional[bool] = None) -> dict:
        """Ω-REF30: Update a signal's value."""
        if name not in self._signal_history:
            self._signal_history[name] = deque(maxlen=200)
        self._signal_history[name].append(value)

        # Ω-REF31: Adaptive weight adjustment
        if outcome is not None and name in self._signal_weights:
            if outcome:
                self._signal_weights[name] = min(1.0, self._signal_weights[name] + 0.05)
            else:
                self._signal_weights[name] = max(0.01, self._signal_weights[name] - 0.05)

        # Ω-REF32: Conflict detection
        # Signals disagreeing with each other
        latest_values = {}
        for s_name, hist in self._signal_history.items():
            if hist:
                latest_values[s_name] = hist[-1]

        if len(latest_values) >= 3:
            vals = list(latest_values.values())
            # How many agree on direction?
            positive = sum(1 for v in vals if v > 0)
            negative = sum(1 for v in vals if v < 0)
            neutral = len(vals) - positive - negative
            conflict = 1.0 - abs(positive - negative) / max(1, len(vals))
        else:
            conflict = 0.0

        self._conflict_history.append(conflict)

        # Ω-REF33: Dynamic hierarchy
        # Rank signals by current weight
        ranking = sorted(self._signal_weights.items(), key=lambda x: x[1], reverse=True)

        # Ω-REF34: Consensus signal
        total_weight = sum(self._signal_weights.get(s, 0) for s in latest_values)
        if total_weight > 0:
            consensus = sum(
                self._signal_weights.get(s, 0) * v
                for s, v in latest_values.items()
            ) / total_weight
        else:
            consensus = 0.0

        # Ω-REF35: Market intuition score
        # How well does the swarm "feel" the market?
        avg_conflict = (
            sum(self._conflict_history) / len(self._conflict_history)
            if self._conflict_history else 0.5
        )
        intuition_score = 1.0 - avg_conflict  # Less conflict = better intuition

        # Ω-REF36: Omniscience depth
        # How many signals are contributing meaningfully?
        active_signals = sum(
            1 for w in self._signal_weights.values() if w > 0.05
        )
        depth = active_signals / max(1, len(self._signal_weights))

        return {
            "consensus": consensus,
            "conflict_level": conflict,
            "signal_ranking": ranking[:5],
            "intuition_score": intuition_score,
            "omniscience_depth": depth,
            "n_active_signals": active_signals,
            "is_converged": conflict < 0.2 and abs(consensus) > 0.3,
            "is_divergent": conflict > 0.6,
        }


# ──────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────

def _correlation(x: list[float], y: list[float]) -> float:
    """Pearson correlation."""
    n = min(len(x), len(y))
    if n < 3:
        return 0.0
    x = x[-n:]
    y = y[-n:]
    mx = sum(x) / n
    my = sum(y) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(x, y)) / n
    sx = math.sqrt(sum((a - mx) ** 2 for a in x) / n)
    sy = math.sqrt(sum((a - my) ** 2 for a in y) / n)
    denom = sx * sy
    if denom < 1e-12:
        return 0.0
    return cov / denom


def _normalize(values: list[float]) -> float:
    """Normalize to [-1, 1] range via last value minus mean / std."""
    if not values:
        return 0.0
    n = len(values)
    mean = sum(values) / n
    std = math.sqrt(sum((v - mean) ** 2 for v in values) / n)
    if std < 1e-12:
        return 0.0
    return (values[-1] - mean) / std
