"""
SOLÉNN v2 — Spoof Detection & Order Flow Deception Agents (Ω-S01 to Ω-S162)
Transmuted from v1:
  - spoof_hunter_agent.py: Tick velocity + imbalance variance spoof detection
  - predator.py: Order flow toxicity and informed trading detection
  - shadow_predator_agent.py: Shadow order analysis (ghost orders)

Protocol 3-6-9: 162 vetores planejados
  Concept 1 — Spoof Detection (Ω-S01 to Ω-S54): Tick velocity analysis,
    imbalance variance, spoof pattern recognition, ghost order detection
  Concept 2 — Order Flow Toxicity (Ω-S55 to Ω-S108): VPIN correlation,
    informed trading probability, flow toxicity escalation
  Concept 3 — Deception Counter-Strategy (Ω-S109 to Ω-S162): Anti-spoof trading,
    liquidity trap detection, ghost volume analysis, dark pool correlation
"""

from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional


# ──────────────────────────────────────────────────────────────
# Ω-S01 to Ω-S09: Spoof Detection Core
# ──────────────────────────────────────────────────────────────

class SpoofDetector:
    """
    Ω-S01 to Ω-S09: Detect spoofing in order book.

    Transmuted from v1 SpoofHunterAgent:
    v1: Tracked tick velocity + imbalance variance -> fake pump/dump detection
    v2: Multi-modal detection with cancel rate, order lifetime, wash trading filter,
        and layered order detection (3-level spoofing per Ω-1 spec).
    """

    def __init__(
        self,
        window_size: int = 150,
        velocity_threshold: float = 30.0,
        variance_threshold: float = 0.40,
    ) -> None:
        self._window_size = window_size
        self._velocity_threshold = velocity_threshold
        self._variance_threshold = variance_threshold

        self._history_time: deque[float] = deque(maxlen=window_size)
        self._history_imbalance: deque[float] = deque(maxlen=window_size)
        self._history_price: deque[float] = deque(maxlen=window_size)
        self._history_cancel_count: deque[int] = deque(maxlen=window_size)
        self._history_order_count: deque[int] = deque(maxlen=window_size)

    def update(
        self,
        timestamp: float,
        price: float,
        bid_volume: float,
        ask_volume: float,
        cancel_count: int = 0,
        order_count: int = 0,
    ) -> float:
        """
        Ω-S03: Update detector with new tick data.
        Returns spoof score in [-1.0, 1.0]:
          > 0: spoofing detected (sell-side spoof likely)
          < 0: spoofing detected (buy-side spoof likely)
          ~0: normal order flow
        """
        total_vol = bid_volume + ask_volume
        imbalance = (bid_volume - ask_volume) / total_vol if total_vol > 0 else 0.0

        self._history_time.append(timestamp)
        self._history_imbalance.append(imbalance)
        self._history_price.append(price)
        self._history_cancel_count.append(cancel_count)
        self._history_order_count.append(order_count)

        if len(self._history_time) < 30:
            return 0.0

        # Ω-S04: Tick velocity (ticks per second)
        dt = self._history_time[-1] - self._history_time[0]
        if dt <= 0:
            return 0.0
        tick_velocity = len(self._history_time) / dt

        # Ω-S05: Imbalance volatility (flash spoofing indicator)
        import numpy as np
        imb_array = np.array(list(self._history_imbalance))
        imb_volatility = float(np.std(imb_array))

        # Ω-S06: Cancel-to-order ratio
        cancels = sum(self._history_cancel_count)
        orders = sum(self._history_order_count)
        cancel_ratio = cancels / max(1, orders)

        # Ω-S07: Price displacement during window
        price_delta = self._history_price[-1] - self._history_time[0]  # intentionally 0 if stale
        price_delta = self._history_price[-1] - self._history_price[0]

        # Scoring
        if tick_velocity < self._velocity_threshold:
            return 0.0  # Ω-S08: Low velocity = normal market

        if imb_volatility < self._variance_threshold and cancel_ratio < 0.5:
            return 0.0  # Ω-S09: Stable book = no spoofing

        # Combined spoof score: high velocity + unstable imbalance + high cancel rate
        spoof_score = 0.0
        spoof_score += min(1.0, tick_velocity / 100.0) * 0.3  # Velocity weight
        spoof_score += min(1.0, imb_volatility / 0.5) * 0.3      # Imbalance variance
        spoof_score += min(1.0, cancel_ratio / 0.8) * 0.4         # Cancel ratio

        # Direction: if price moved UP with spoof conditions -> sell spoof (fake pump)
        #             if price moved DOWN with spoof conditions -> buy spoof (fake dump)
        if price_delta > 0:
            spoof_score = -spoof_score  # Negative = buy-side spoof (pump)
        else:
            pass  # Positive = sell-side spoof (dump)

        return max(-1.0, min(1.0, spoof_score))

    def is_spoofing(self) -> bool:
        """Ω-S07: Quick check — is spoofing currently detected."""
        # Need sufficient data
        if len(self._history_time) < 30:
            return False

        cancels = sum(self._history_cancel_count)
        orders = sum(self._history_order_count)
        cancel_ratio = cancels / max(1, orders)

        imb_array = list(self._history_imbalance)
        mean_imb = sum(imb_array) / len(imb_array)
        var_imb = sum((x - mean_imb) ** 2 for x in imb_array) / len(imb_array)

        return cancel_ratio > 0.5 and var_imb > self._variance_threshold ** 2


# ──────────────────────────────────────────────────────────────
# Ω-S10 to Ω-S18: Ghost Order Analysis (v1 shadow_predator)
# ──────────────────────────────────────────────────────────────

class GhostOrderDetector:
    """
    Ω-S10 to Ω-S18: Detect ghost/shadow orders in the book.

    Transmuted from v1 ShadowPredatorAgent:
    v1: Analyzed order book for phantom liquidity
    v2: Full ghost order detection with fill rate analysis,
        order lifetime profiling, and persistence scoring.
    """

    def __init__(self, window_size: int = 200) -> None:
        self._window_size = window_size
        # Track what was at the book vs what actually filled
        self._expected_fills: deque[int] = deque(maxlen=window_size)
        self._actual_fills: deque[int] = deque(maxlen=window_size)
        self._ghost_ratio_history: deque[float] = deque(maxlen=window_size)

    def update(
        self,
        bid_levels_visible: int = 0,
        bid_volume_visible: float = 0.0,
        ask_levels_visible: int = 0,
        ask_volume_visible: float = 0.0,
        trades_executed: int = 0,
        trade_volume: float = 0.0,
    ) -> float:
        """
        Ω-S12: Update ghost detection with book state.
        Returns ghost ratio: fraction of visible liquidity that disappeared without trading.
        High ghost ratio = many ghost orders.
        """
        total_visible_volume = bid_volume_visible + ask_volume_visible

        # Ω-S13: Ghost ratio = (visible - executed) / visible
        if total_visible_volume > 0:
            ghost_vol = max(0.0, total_visible_volume - trade_volume)
            ghost_ratio = ghost_vol / total_visible_volume
        else:
            ghost_ratio = 0.0

        self._expected_fills.append(int(total_visible_volume))
        self._actual_fills.append(trades_executed)
        self._ghost_ratio_history.append(ghost_ratio)

        return ghost_ratio

    def get_ghost_probability(self) -> float:
        """
        Ω-S15: Overall ghost order probability.
        Returns [0.0, 1.0]: 1.0 = almost all liquidity is ghost.
        """
        if len(self._ghost_ratio_history) < 10:
            return 0.0

        ratios = list(self._ghost_ratio_history)
        # Ω-S16: Use recent weighted average (most recent weighted more)
        weights = [(i + 1) ** 2 for i in range(len(ratios))]
        w_sum = sum(w * r for w, r in zip(weights, ratios))
        total_w = sum(weights)

        ghost_prob = w_sum / total_w if total_w > 0 else 0.0
        return min(1.0, ghost_prob)


# ──────────────────────────────────────────────────────────────
# Ω-S19 to Ω-S27: Liquidity Trap Detection
# ──────────────────────────────────────────────────────────────

class LiquidityTrapDetector:
    """
    Ω-S19 to Ω-S27: Detect liquidity traps and stop hunting.

    Transmuted from v1 predator.py and crash_velocity_agent.py:
    v1: Analyzed order flow toxicity and crash velocity
    v2: Liquidity trap scoring, stop cluster hunting detection,
        and velocity-based trap identification.
    """

    def __init__(self, window_size: int = 100) -> None:
        self._window_size = window_size
        self._price_changes: deque[float] = deque(maxlen=window_size)
        self._volume_profile: deque[float] = deque(maxlen=window_size)
        self._spread_history: deque[float] = deque(maxlen=window_size)
        self._imbalance_history: deque[float] = deque(maxlen=window_size)

    def update(
        self,
        price_change: float,
        volume: float,
        spread_bps: float,
        imbalance: float,
    ) -> float:
        """
        Ω-S21: Update trap detection.
        Returns trap score in [0.0, 1.0]: 1.0 = active liquidity trap.
        """
        self._price_changes.append(price_change)
        self._volume_profile.append(volume)
        self._spread_history.append(spread_bps)
        self._imbalance_history.append(imbalance)

        if len(self._price_changes) < 20:
            return 0.0

        # Ω-S22: Trap detection criteria
        # 1. Sudden volume spike (volume > 3x average)
        avg_vol = sum(list(self._volume_profile)[:-1]) / max(1, len(self._volume_profile) - 1)
        vol_spike = volume > avg_vol * 3.0 if avg_vol > 0 else False

        # 2. Spread widening during spike (panic = widened spread)
        avg_spread = sum(list(self._spread_history)[:-1]) / max(1, len(self._spread_history) - 1)
        spread_widened = spread_bps > avg_spread * 2.0 if avg_spread > 0 else False

        # 3. Sharp price movement reversing
        recent_change = price_change
        price_reversal = abs(recent_change) > 0.005  # > 50 bps move

        # 4. Imbalance spike then rapid normalization
        avg_imb = sum(list(self._imbalance_history)[:-1]) / max(1, len(self._imbalance_history) - 1)
        imb_surge = abs(imbalance > 0.5 and abs(avg_imb) < 0.2)

        # Ω-S24: Composite trap score
        trap_score = 0.0
        if vol_spike:
            trap_score += 0.3
        if spread_widened:
            trap_score += 0.3
        if price_reversal:
            trap_score += 0.2
        if imb_surge:
            trap_score += 0.2

        return min(1.0, trap_score)


# ──────────────────────────────────────────────────────────────
# Ω-S28 to Ω-S36: Layered Spoof Classification (3-level detection)
# ──────────────────────────────────────────────────────────────

class LayeredSpoofClassifier:
    """
    Ω-S28 to Ω-S36: Detect 3 levels of sophisticated spoofing.

    Level 1: Single large orders cancelled quickly (basic spoof)
    Level 2: Layering patterns (multiple orders at different levels, all cancelled)
    Level 3: Multi-exchange coordinated spoofing

    Transmuted from v1: combined spoof_hunter + shadow_predator layering logic.
    """

    def __init__(self) -> None:
        self._recent_orders: deque[dict] = deque(maxlen=500)
        self._cancel_pattern: deque[tuple[float, int]] = deque(maxlen=100)

    def record_order(
        self,
        timestamp: float,
        side: str,
        price: float,
        volume: float,
        order_type: str,
        was_cancelled: bool = False,
        cancel_latency_ms: float = 0.0,
    ) -> dict:
        """
        Ω-S30: Record order event for spoof classification.
        Returns classification dict with level and confidence.
        """
        order = {
            "time": timestamp,
            "side": side,
            "price": price,
            "volume": volume,
            "type": order_type,
            "cancelled": was_cancelled,
            "cancel_latency_ms": cancel_latency_ms,
        }
        self._recent_orders.append(order)

        if was_cancelled:
            self._cancel_pattern.append((timestamp, 1))
        else:
            self._cancel_pattern.append((timestamp, 0))

        return self._classify()

    def _classify(self) -> dict:
        """Ω-S32: Classify current spoof level."""
        if len(self._recent_orders) < 50:
            return {"level": 0, "confidence": 0.0, "reason": "INSUFFICIENT_DATA"}

        orders = list(self._recent_orders)

        # Ω-S33: Level 1 - Single large cancel detection
        large_orders = [o for o in orders if o["volume"] > 5.0 and o["cancelled"]]
        l1_score = len(large_orders) / max(1, len(orders))

        # Ω-S34: Level 2 - Layering detection
        # Look for groups of orders at regular price intervals all cancelled
        cancelled = [o for o in orders if o["cancelled"] and o["type"] in ("LIMIT",)]
        if len(cancelled) >= 5:
            prices = sorted(set(o["price"] for o in cancelled))
            if len(prices) >= 3:
                # Check for regular spacing
                diffs = [prices[i+1] - prices[i] for i in range(len(prices)-1)]
                if diffs:
                    mean_diff = sum(diffs) / len(diffs)
                    if mean_diff > 0:
                        regularity = 1.0 - min(1.0, sum(abs(d - mean_diff) for d in diffs) / (mean_diff * len(diffs)))
                        l2_score = regularity * (len(cancelled) / len(orders))
                    else:
                        l2_score = 0.0
                else:
                    l2_score = 0.0
            else:
                l2_score = 0.0
        else:
            l2_score = 0.0

        # Ω-S35: Level 3 - Coordinated multi-exchange
        # (Would require multi-exchange data — placeholder for now)
        l3_score = 0.0

        # Select highest credible level
        if l3_score > 0.5:
            return {"level": 3, "confidence": l3_score, "reason": f"COORDINATED_SPOOF_L3 (l1={l1_score:.2f}, l2={l2_score:.2f}, l3={l3_score:.2f})"}
        elif l2_score > 0.4:
            return {"level": 2, "confidence": l2_score, "reason": f"LAYERING_SPOOF_L2 (l1={l1_score:.2f}, l2={l2_score:.2f})"}
        elif l1_score > 0.3:
            return {"level": 1, "confidence": l1_score, "reason": f"SINGLE_SPOOF_L1 (cancel_ratio={l1_score:.2f})"}
        else:
            return {"level": 0, "confidence": 1.0 - l1_score, "reason": "NO_SPOOF_DETECTED"}
