"""
SOLÉNN v2 — Microstructure Signal Agents (Ω-E01 to Ω-E54)
Order Flow Intelligence, Book Dynamics, Market Impact,
Spoof Detection, Volume Profile, and Liquidity/Spread signals.

Concept 1 Tópicos 1.1–1.6
"""

from __future__ import annotations

import math
import time
from collections import Counter, deque
from dataclasses import dataclass, field
from typing import Any


# ──────────────────────────────────────────────────────────────
# Ω-E01 to Ω-E09: Order Flow Intelligence
# ──────────────────────────────────────────────────────────────

class VPINCalculator:
    """Ω-E01: Volume-synchronized Probability of Informed Trading."""

    def __init__(self, bucket_volume: float = 100.0, num_buckets: int = 50) -> None:
        self._bucket_volume = bucket_volume
        self._num_buckets = num_buckets
        self._current_buy = 0.0
        self._current_sell = 0.0
        self._buckets: deque[float] = deque(maxlen=num_buckets)

    def update(self, volume: float, is_buy: bool) -> float | None:
        if is_buy:
            self._current_buy += volume
        else:
            self._current_sell += volume

        total_in_bucket = self._current_buy + self._current_sell
        if total_in_bucket >= self._bucket_volume:
            imbalance = abs(self._current_buy - self._current_sell) / self._bucket_volume
            self._buckets.append(imbalance)
            self._current_buy = 0.0
            self._current_sell = 0.0

        if len(self._buckets) == self._num_buckets:
            return sum(self._buckets) / self._num_buckets
        return None


class OrderFlowImbalance:
    """Ω-E02: Bid/ask volume imbalance per level."""

    def __init__(self, levels: int = 10) -> None:
        self._levels = levels

    def compute(self, bid_volumes: list[float], ask_volumes: list[float]) -> float:
        n = min(len(bid_volumes), len(ask_volumes), self._levels)
        total_bid = sum(bid_volumes[:n])
        total_ask = sum(ask_volumes[:n])
        total = total_bid + total_ask
        if total == 0:
            return 0.0
        return (total_bid - total_ask) / total


class AggressorSideDetector:
    """Ω-E03: Lee-Ready tick test for taker buy/sell classification."""

    def __init__(self) -> None:
        self._last_price: float | None = None
        self._price_changes: deque[float] = deque(maxlen=20)

    def classify(self, price: float, bid: float, ask: float) -> str:
        """Returns 'buy' if taker buy, 'sell' if taker sell, 'unknown'."""
        if self._last_price is None:
            self._last_price = price
            return "unknown"

        change = price - self._last_price
        if change > 0:
            result = "buy"
        elif change < 0:
            result = "sell"
        else:
            # Tick test: compare to previous trade
            result = "buy" if self._price_changes and self._price_changes[-1] > 0 else "sell"

        self._price_changes.append(change)
        self._last_price = price
        return result


class FlowToxicityMonitor:
    """Ω-E05: Monitor when VPIN exceeds threshold → toxic flow."""

    def __init__(self, threshold: float = 0.7) -> None:
        self._threshold = threshold
        self._recent_vpin: deque[float] = deque(maxlen=20)
        self._toxic_streak = 0

    def update(self, vpin: float) -> bool:
        self._recent_vpin.append(vpin)
        is_toxic = vpin > self._threshold
        if is_toxic:
            self._toxic_streak += 1
        else:
            self._toxic_streak = 0
        return is_toxic

    @property
    def avg_vpin(self) -> float:
        return sum(self._recent_vpin) / len(self._recent_vpin) if self._recent_vpin else 0.0


class FlowDirectionEntropy:
    """Ω-E09: Lempel-Ziv entropy of trade direction sequence."""

    def __init__(self, window: int = 200) -> None:
        self._directions: deque[str] = deque(maxlen=window)

    def update(self, direction: str) -> float:
        """Returns LZ complexity as proxy for entropy."""
        self._directions.append(direction)
        seq = "".join(self._directions)
        if not seq:
            return 0.0

        # Simplified LZ complexity
        n = len(seq)
        substrings: set[str] = set()
        for length in range(1, min(n + 1, 10)):
            for start in range(n - length + 1):
                substrings.add(seq[start:start + length])

        max_possible = sum(min(n - l + 1, 2 ** l) for l in range(1, min(n + 1, 10)))
        return len(substrings) / max(max_possible, 1)


# ──────────────────────────────────────────────────────────────
# Ω-E10 to Ω-E18: Book Dynamics
# ──────────────────────────────────────────────────────────────

class DepthVelocityTracker:
    """Ω-E10: Rate of liquidity entry/exit per level."""

    def __init__(self, window: int = 50) -> None:
        self._snapshots: deque[list[float]] = deque(maxlen=window)

    def update(self, bid_depths: list[float], ask_depths: list[float]) -> float:
        """Returns total depth velocity (rate of change)."""
        current = bid_depths + ask_depths
        self._snapshots.append(current)
        if len(self._snapshots) < 2:
            return 0.0
        prev = self._snapshots[-2]
        if not prev:
            return 0.0
        total_change = sum(abs(c - p) for c, p in zip(current, prev))
        return total_change


class BookPressureGradient:
    """Ω-E13: Change in book mass: pressure = Σ(level × depth_change)."""

    def __init__(self) -> None:
        self._prev_depths: list[float] | None = None

    def compute(self, bid_depths: list[float], ask_depths: list[float]) -> float:
        current = bid_depths + ask_depths
        if self._prev_depths is None:
            self._prev_depths = current
            return 0.0
        pressure = sum((i + 1) * (c - p) for i, (c, p) in enumerate(zip(current, self._prev_depths)))
        self._prev_depths = current
        return pressure


class LiquidityResilienceScore:
    """Ω-E15: Speed of book recovery after large trade."""

    def __init__(self, recovery_window_s: float = 30.0) -> None:
        self._recovery_window = recovery_window_s
        self._events: list[tuple[float, float]] = []  # (time, depth_lost)
        self._score = 1.0

    def record_event(self, depth_lost: float, recovery_time_s: float) -> None:
        self._events.append((time.time(), depth_lost))
        if depth_lost > 0:
            speed = depth_lost / max(recovery_time_s, 0.1)
            self._score = min(1.0, speed / 100.0)

    @property
    def score(self) -> float:
        return max(0.0, self._score)


class BookShapeAnalyzer:
    """Ω-E17: Classify book shape: flat, steep, wall, gap."""

    def classify(self, bid_depths: list[float], ask_depths: list[float]) -> str:
        n = min(len(bid_depths), len(ask_depths), 10)
        if n < 2:
            return "unknown"

        b = bid_depths[:n]
        a = ask_depths[:n]

        # Wall: large concentration at one level
        if max(b) > sum(b) * 0.5 or max(a) > sum(a) * 0.5:
            return "wall"

        # Flat: depth similar across levels
        total_b = sum(b)
        total_a = sum(a)
        if total_b > 0 and total_a > 0:
            cv_b = (sum((x - total_b / n) ** 2 for x in b) / n) ** 0.5 / (total_b / n) if total_b / n > 0 else 0
            cv_a = (sum((x - total_a / n) ** 2 for x in a) / n) ** 0.5 / (total_a / n) if total_a / n > 0 else 0
            if cv_b < 0.3 and cv_a < 0.3:
                return "flat"

        # Gap: large distance between levels
        if len(b) >= 3:
            for i in range(len(b) - 1):
                if b[i] > 0 and b[i + 1] < b[i] * 0.1:
                    return "gap"

        return "steep"


# ──────────────────────────────────────────────────────────────
# Ω-E19 to Ω-E27: Market Impact & Slippage
# ──────────────────────────────────────────────────────────────

@dataclass
class ImpactCalibration:
    """Ω-E19: Calibrated market impact parameters."""
    eta: float = 0.1
    gamma: float = 0.6
    n_observations: int = 0

    def impact_bps(self, order_qty: float, book_depth: float) -> float:
        if book_depth <= 0:
            return 100.0
        ratio = order_qty / book_depth
        return self.eta * (ratio ** self.gamma) * 10000


class ImpactModel:
    """Ω-E19: η(Q/D)^γ calibrated in real-time via regression."""

    def __init__(self) -> None:
        self._calibration = ImpactCalibration()
        self._observations: list[tuple[float, float, float]] = []  # (qty/depth, actual_impact_bps, time)

    def calibrate(self, order_qty: float, book_depth: float, actual_impact_bps: float) -> None:
        self._observations.append((order_qty / max(book_depth, 1e-10), actual_impact_bps, time.time()))
        if len(self._observations) >= 10:
            self._recalibrate()

    def _recalibrate(self) -> None:
        """Simple log-log regression to estimate eta and gamma."""
        recent = sorted(self._observations, key=lambda x: -x[2])[:100]
        x_vals = [math.log(max(r[0], 1e-10)) for r in recent]
        y_vals = [math.log(max(r[1], 1e-10)) for r in recent]
        n = len(x_vals)
        x_mean = sum(x_vals) / n
        y_mean = sum(y_vals) / n
        ss_xy = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, y_vals))
        ss_xx = sum((x - x_mean) ** 2 for x in x_vals)
        if ss_xx > 0:
            self._calibration.gamma = max(0.1, min(1.5, ss_xy / ss_xx))
            self._calibration.eta = math.exp(y_mean - self._calibration.gamma * x_mean)
            self._calibration.eta = max(0.01, min(10.0, self._calibration.eta))
            self._calibration.n_observations = n

    def predict(self, order_qty: float, book_depth: float) -> float:
        return self._calibration.impact_bps(order_qty, book_depth)


# ──────────────────────────────────────────────────────────────
# Ω-E28 to Ω-E36: Spoof Detection
# ──────────────────────────────────────────────────────────────

class SpoofPatternDetector:
    """Ω-E28: Detect spoofing level 1 — large orders cancelled quickly."""

    def __init__(self, large_order_bps: float = 0.05, cancel_time_ms: float = 500.0) -> None:
        self._large_threshold = large_order_bps  # % of book depth
        self._cancel_threshold_ms = cancel_time_ms
        self._placed_orders: dict[str, tuple[float, float]] = {}  # order_id -> (size, timestamp_ms)

    def record_placement(self, order_id: str, size: float, book_depth: float, timestamp_ms: float) -> None:
        if size > book_depth * self._large_threshold:
            self._placed_orders[order_id] = (size, timestamp_ms)

    def record_cancellation(self, order_id: str, timestamp_ms: float) -> tuple[bool, float]:
        """Returns (is_spoof, confidence)."""
        if order_id not in self._placed_orders:
            return False, 0.0
        size, placed_at = self._placed_orders.pop(order_id)
        lifetime_ms = timestamp_ms - placed_at
        is_spoof = lifetime_ms < self._cancel_threshold_ms
        confidence = 1.0 - (lifetime_ms / self._cancel_threshold_ms) if is_spoof else 0.0
        return is_spoof, max(0.0, min(1.0, confidence))


class LayeringDetector:
    """Ω-E29: Detect layering — multiple orders at different levels creating false depth."""

    def __init__(self, min_layers: int = 3, cancel_correlation: float = 0.8) -> None:
        self._min_layers = min_layers
        self._cancel_corr = cancel_correlation

    def detect(self, order_events: list[dict[str, Any]]) -> tuple[bool, float]:
        """
        order_events: [{type: place/cancel, level: int, time: ms, size: float}]
        """
        if len(order_events) < self._min_layers * 2:
            return False, 0.0

        # Look for pattern: N places at different levels → N cancels nearly simultaneously
        layers = [e for e in order_events if e.get("type") == "place"]
        cancels = [e for e in order_events if e.get("type") == "cancel"]

        if len(layers) >= self._min_layers and len(cancels) >= self._min_layers:
            levels = set(e.get("level", 0) for e in layers)
            if len(levels) >= self._min_layers:
                cancel_times = [e.get("time", 0) for e in cancels]
                if len(cancel_times) >= 2:
                    time_range = max(cancel_times) - min(cancel_times)
                    if time_range < 1000:  # Within 1 second
                        return True, min(1.0, len(layers) / (self._min_layers + 2))

        return False, 0.0


class SpoofConfidenceScorer:
    """Ω-E31: Aggregate spoof confidence from multiple detectors."""

    def __init__(self) -> None:
        self._spoof_signals: list[float] = []

    def add_signal(self, confidence: float) -> float:
        self._spoof_signals.append(confidence)
        if len(self._spoof_signals) > 20:
            self._spoof_signals = self._spoof_signals[-20:]
        return sum(self._spoof_signals) / len(self._spoof_signals)


# ──────────────────────────────────────────────────────────────
# Ω-E37 to Ω-E45: Volume Profile Analysis
# ──────────────────────────────────────────────────────────────

class VolumeProfile:
    """Ω-E37 to Ω-E45: Volume profile with POC, value area, delta."""

    def __init__(self, num_bins: int = 100, price_range: tuple[float, float] = (0.0, 100000.0)) -> None:
        self._num_bins = num_bins
        self._low, self._high = price_range
        self._bin_size = (self._high - self._low) / num_bins
        self._buy_volume: list[float] = [0.0] * num_bins
        self._sell_volume: list[float] = [0.0] * num_bins

    def add_trade(self, price: float, volume: float, is_buy: bool) -> None:
        if self._bin_size <= 0:
            return
        idx = int((price - self._low) / self._bin_size)
        idx = max(0, min(self._num_bins - 1, idx))
        if is_buy:
            self._buy_volume[idx] += volume
        else:
            self._sell_volume[idx] += volume

    @property
    def poc(self) -> float:
        """Ω-E39: Point of Control — price with maximum volume."""
        total = [b + s for b, s in zip(self._buy_volume, self._sell_volume)]
        if not total or max(total) == 0:
            return (self._low + self._high) / 2
        idx = total.index(max(total))
        return self._low + idx * self._bin_size + self._bin_size / 2

    @property
    def value_area(self) -> tuple[float, float]:
        """Ω-E38: Value area — 70% volume around POC."""
        total = [(i, b + s) for i, (b, s) in enumerate(zip(self._buy_volume, self._sell_volume))]
        total.sort(key=lambda x: -x[1])
        total_volume = sum(x[1] for x in total)
        if total_volume == 0:
            return (self._low, self._high)

        cumulative = 0.0
        va_bins = set()
        for idx, vol in total:
            cumulative += vol
            va_bins.add(idx)
            if cumulative >= total_volume * 0.7:
                break

        min_bin = min(va_bins)
        max_bin = max(va_bins)
        return (self._low + min_bin * self._bin_size,
                self._low + (max_bin + 1) * self._bin_size)

    @property
    def cumulative_delta(self) -> float:
        """Ω-E44: Cumulative delta (buy volume - sell volume)."""
        return sum(self._buy_volume) - sum(self._sell_volume)


# ──────────────────────────────────────────────────────────────
# Ω-E46 to Ω-E54: Liquidity & Spread Signals
# ──────────────────────────────────────────────────────────────

class MarketQualityIndex:
    """Ω-E51: Composite market quality index."""

    def __init__(self) -> None:
        self._spreads: deque[float] = deque(maxlen=100)
        self._depths: deque[float] = deque(maxlen=100)
        self._toxicity: deque[float] = deque(maxlen=100)

    def update(self, spread_bps: float, depth_usd: float, vpin: float) -> float:
        self._spreads.append(spread_bps)
        self._depths.append(depth_usd)
        self._toxicity.append(vpin)

        # Score components (0-100 each)
        spread_score = max(0, 100 - spread_bps * 5)  # Low spread = high score
        avg_depth = sum(self._depths) / len(self._depths) if self._depths else 0
        depth_score = min(100, avg_depth / 1000)  # High depth = high score
        avg_toxic = sum(self._toxicity) / len(self._toxicity) if self._toxicity else 0
        toxicity_score = max(0, 100 - avg_toxic * 200)  # Low toxicity = high score

        return (spread_score * 0.35 + depth_score * 0.35 + toxicity_score * 0.3)
