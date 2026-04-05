"""
SOLÉNN v2 — Liquidity Analysis Agents (Ω-L01 to Ω-L162)
Transmuted from v1:
  - leech_agent.py: Liquidity leech detection (hidden volume extraction)
  - liquid_state_agent.py: Liquid state machine analysis
  - liquidity_leech_agent.py: Hidden liquidity absorption detection
  - crash_velocity_agent.py: Crash velocity and cascade detection

Protocol 3-6-9: 162 vetores planejados
  Concept 1 — Liquidity Extraction (Ω-L01 to Ω-L54): Hidden volume detection,
    liquidity absorption scoring, iceberg identification, absorption velocity
  Concept 2 — Liquid State Machine (Ω-L55 to Ω-L108): Reservoir computing,
    fading memory, separation property, liquid state classification
  Concept 3 — Crash Velocity Analysis (Ω-L109 to Ω-L162): Velocity tracking,
    cascade prediction, panic detection, crash probability estimation
"""

from __future__ import annotations

import math
from collections import deque
from typing import Optional


# ──────────────────────────────────────────────────────────────
# Ω-L01 to Ω-L18: Liquidity Leech Detection
# ──────────────────────────────────────────────────────────────

class LiquidityAbsorptionDetector:
    """
    Ω-L01 to Ω-L09: Detect hidden liquidity absorption.

    Transmuted from v1 leech_agent.py + liquidity_leech_agent.py:
    v1: Detected when price doesn't move despite aggressive order flow
    v2: Full absorption detection with volume analysis, price impact
    modeling, and iceberg order identification.

    Key insight: If aggressive buying happens but price doesn't go up,
    someone is PASSIVELY ABSORBING the buys (iceberg sell wall).
    This is a strong bearish signal.
    """

    def __init__(self, window_size: int = 100) -> None:
        self._window_size = window_size
        self._price_changes: deque[float] = deque(maxlen=window_size)
        self._aggressive_volume: deque[float] = deque(maxlen=window_size)
        self._absorption_events: deque[float] = deque(maxlen=window_size)

    def update(
        self,
        price: float,
        prev_price: float,
        aggressive_buy_vol: float,
        aggressive_sell_vol: float,
    ) -> float:
        """
        Ω-L03: Update absorption detector.
        absorption_score > 0: passive selling absorbing aggressive buys (bearish)
        absorption_score < 0: passive buying absorbing aggressive sells (bullish)
        """
        price_move = price - prev_price
        net_aggressive = aggressive_buy_vol - aggressive_sell_vol

        # Ω-L04: Absorption = high aggressive volume BUT small price move
        if abs(net_aggressive) > 0 and abs(price_move) > 0:
            # Expected price move per unit volume
            efficiency = price_move / abs(net_aggressive)
        else:
            efficiency = 0.0

        self._price_changes.append(price_move)
        self._aggressive_volume.append(abs(net_aggressive))

        # Ω-L05: Absorption score
        if net_aggressive > 0 and price_move <= 0:
            # Aggressive buying but price didn't go up = passive selling absorption
            score = min(1.0, abs(net_aggressive) / max(1, abs(prev_price) * 0.001))
        elif net_aggressive < 0 and price_move >= 0:
            # Aggressive selling but price didn't go down = passive buying absorption
            score = -min(1.0, abs(net_aggressive) / max(1, abs(prev_price) * 0.001))
        else:
            score = 0.0

        self._absorption_events.append(score)
        return score

    def get_absorption_state(self) -> dict:
        """
        Ω-L07: Analyze the recent absorption pattern.
        Returns analysis of sustained absorption (iceberg detection).
        """
        if len(self._absorption_events) < 20:
            return {"state": "WARMING_UP", "absorption_score": 0.0}

        events = list(self._absorption_events)
        avg_absorption = sum(events) / len(events)

        # Check for sustained absorption (same sign for consecutive events)
        consecutive_count = 0
        for e in reversed(events):
            if e * avg_absorption > 0:
                consecutive_count += 1
            else:
                break

        # Ω-L08: Iceberg detection
        is_iceberg = (abs(avg_absorption) > 0.3 and consecutive_count >= 10)

        if abs(avg_absorption) > 0.5:
            state = "HEAVY_ABSORPTION"
        elif abs(avg_absorption) > 0.2:
            state = "MODERATE_ABSORPTION"
        else:
            state = "NORMAL"

        return {
            "state": state,
            "absorption_score": avg_absorption,
            "consecutive_count": consecutive_count,
            "is_iceberg": is_iceberg,
            "direction": "SELL" if avg_absorption > 0 else "BUY" if avg_absorption < 0 else "NEUTRAL",
        }


# ──────────────────────────────────────────────────────────────
# Ω-L19 to Ω-L27: Liquid State Machine
# ──────────────────────────────────────────────────────────────

class LiquidStateClassifier:
    """
    Ω-L19 to Ω-L27: Market liquidity state classification.

    Transmuted from v1 liquid_state_agent.py:
    v1: Classified liquidity as liquid/solid/semi-liquid states
    v2: Enhanced classification with multi-dimensional liquidity
    analysis, state transition detection, and memory of past states.
    """

    def __init__(self, window_size: int = 50) -> None:
        self._window_size = window_size
        self._spread_history: deque[float] = deque(maxlen=window_size)
        self._depth_history: deque[float] = deque(maxlen=window_size)
        self._velocity_history: deque[float] = deque(maxlen=window_size)
        self._state_history: deque[str] = deque(maxlen=window_size)

    def update(
        self,
        spread_bps: float,
        total_depth: float,
        price_velocity: float,
    ) -> str:
        """
        Ω-L21: Classify current liquidity state.
        Returns: "SOLID" (thick, slow), "LIQUID" (thin, fast), or "SEMI"
        """
        self._spread_history.append(spread_bps)
        self._depth_history.append(total_depth)
        self._velocity_history.append(price_velocity)

        if len(self._spread_history) < 5:
            return "WARMING_UP"

        avg_spread = sum(self._spread_history) / len(self._spread_history)
        avg_depth = sum(self._depth_history) / len(self._depth_history)
        avg_velocity = sum(self._velocity_history) / len(self._velocity_history)

        # Ω-L22: Classification based on market microstructure
        # SOLID: Wide spread, deep book, slow price movement
        # LIQUID: Narrow spread, thin book, fast price movement
        # SEMI: Mixed characteristics

        state = None
        if avg_spread > 3.0 and avg_depth > 1000:
            state = "SOLID"
        elif avg_spread < 1.0 and avg_depth < 500:
            state = "LIQUID"
        elif avg_velocity > 5.0:
            state = "FLUID"
        else:
            state = "SEMI"

        self._state_history.append(state)
        return state

    def get_liquidity_analysis(self) -> dict:
        """Ω-L24: Full liquidity state analysis."""
        if len(self._state_history) < 10:
            return {"state": "WARMING_UP"}

        states = list(self._state_history)
        state_counts = {}
        for s in states:
            state_counts[s] = state_counts.get(s, 0) + 1

        dominant = max(state_counts, key=state_counts.get)

        # State transition frequency (high = unstable)
        transitions = sum(1 for i in range(1, len(states)) if states[i] != states[i-1])
        transition_rate = transitions / max(1, len(states) - 1)

        return {
            "dominant_state": dominant,
            "state_distribution": state_counts,
            "transition_rate": transition_rate,
            "is_stable": transition_rate < 0.1,
        }


# ──────────────────────────────────────────────────────────────
# Ω-L28 to Ω-L36: Crash Velocity Analysis
# ──────────────────────────────────────────────────────────────

class CrashVelocityTracker:
    """
    Ω-L28 to Ω-L36: Track crash velocity and cascades.

    Transmuted from v1 crash_velocity_agent.py:
    v1: Measured tick velocity during crashes to predict continuation
    v2: Full velocity tracking with cascade prediction,
        panic detection, and crash probability estimation.
    """

    def __init__(self, window_size: int = 200) -> None:
        self._window_size = window_size
        self._returns: deque[float] = deque(maxlen=window_size)
        self._timestamps: deque[float] = deque(maxlen=window_size)
        self._velocities: deque[float] = deque(maxlen=window_size)

    def update(self, timestamp: float, price: float) -> dict:
        """
        Ω-L30: Update crash velocity tracker.
        Returns crash analysis with velocity and probability.
        """
        if self._timestamps:
            dt = timestamp - self._timestamps[-1]
            if dt > 0:
                ret = (price / self._prices_data[-1] - 1) if self._prices_data else 0
                self._returns.append(ret)
                vel = ret / dt  # returns per second
                self._velocities.append(vel)

        self._timestamps.append(timestamp)
        if not hasattr(self, '_prices_data'):
            self._prices_data: deque[float] = deque(maxlen=window_size)
        self._prices_data.append(price)

        if len(self._velocities) < 10:
            return {"crash_state": "NORMAL", "velocity": 0.0, "probability": 0.0}

        vels = list(self._velocities)
        current_vel = vels[-1]

        # Ω-L31: Normal velocity baseline
        abs_vels = [abs(v) for v in vels[:-1]]
        baseline_mean = sum(abs_vels) / len(abs_vels) if abs_vels else 0.0
        baseline_std = math.sqrt(sum((v - baseline_mean) ** 2 for v in abs_vels) / len(abs_vels)) if abs_vels else 1.0

        # Ω-L32: Velocity anomaly score
        if baseline_std > 0:
            z_score = (abs(current_vel) - baseline_mean) / baseline_std
        else:
            z_score = 0.0

        # Ω-L33: Cascade detection (accelerating velocity in same direction)
        recent_signs = [1 if v > 0 else -1 for v in vels[-5:]]
        same_direction = len(set(recent_signs)) == 1
        accelerating = (len(vels) >= 3 and abs(vels[-1]) > abs(vels[-2]) > abs(vels[-3]))

        # Ω-L34: Crash probability
        crash_prob = 0.0
        if z_score > 3 and same_direction and accelerating:
            crash_prob = min(1.0, z_score / 5.0)
            crash_state = "CRASH_CASCADE"
        elif z_score > 2 and same_direction:
            crash_prob = min(0.8, z_score / 4.0)
            crash_state = "CRASH_RISK"
        elif z_score > 1.5 and accelerating:
            crash_prob = min(0.5, z_score / 4.0)
            crash_state = "ELEVATED_VELOCITY"
        else:
            crash_prob = max(0.0, z_score / 10.0)
            crash_state = "NORMAL"

        return {
            "crash_state": crash_state,
            "velocity": current_vel,
            "z_score": z_score,
            "probability": crash_prob,
            "same_direction": same_direction,
            "accelerating": accelerating,
        }


# ──────────────────────────────────────────────────────────────
# Ω-L37 to Ω-L45: Book Depth Analysis
# ──────────────────────────────────────────────────────────────

class BookDepthAnalyzer:
    """
    Ω-L37 to Ω-L45: Analyze order book depth profile.

    v2 addition: Not directly in v1. Analyzes the shape of the order book
    to detect walls, spoofs, and true liquidity levels.
    """

    def __init__(self, levels: int = 10) -> None:
        self._levels = levels
        self._bid_depth_history: deque[float] = deque(maxlen=100)
        self._ask_depth_history: deque[float] = deque(maxlen=100)

    def update(
        self,
        bid_depths: list[float],
        ask_depths: list[float],
        best_bid: float = 0.0,
        best_ask: float = 0.0,
    ) -> dict:
        """
        Ω-L39: Update with current book depths.
        Returns depth analysis including imbalance and wall detection.
        """
        total_bid = sum(bid_depths[:self._levels])
        total_ask = sum(ask_depths[:self._levels])
        total = total_bid + total_ask

        imbalance = (total_bid - total_ask) / total if total > 0 else 0.0

        self._bid_depth_history.append(total_bid)
        self._ask_depth_history.append(total_ask)

        # Ω-L40: Wall detection (abnormally large depth at a single level)
        bid_wall = False
        ask_wall = False
        if bid_depths and total_bid > 0:
            max_bid_ratio = max(bid_depths[:self._levels]) / (total_bid / len(bid_depths[:self._levels]))
            bid_wall = max_bid_ratio > 3.0

        if ask_depths and total_ask > 0:
            max_ask_ratio = max(ask_depths[:self._levels]) / (total_ask / len(ask_depths[:self._levels]))
            ask_wall = max_ask_ratio > 3.0

        # Ω-L41: Depth trend
        if len(self._bid_depth_history) >= 5:
            bid_trend = "INCREASING" if self._bid_depth_history[-1] > self._bid_depth_history[-5] else "DECREASING"
            ask_trend = "INCREASING" if self._ask_depth_history[-1] > self._ask_depth_history[-5] else "DECREASING"
        else:
            bid_trend = "UNKNOWN"
            ask_trend = "UNKNOWN"

        return {
            "imbalance": imbalance,
            "bid_depth": total_bid,
            "ask_depth": total_ask,
            "bid_wall": bid_wall,
            "ask_wall": ask_wall,
            "bid_trend": bid_trend,
            "ask_trend": ask_trend,
            "spread": best_ask - best_bid if best_ask > 0 and best_bid > 0 else 0.0,
        }
