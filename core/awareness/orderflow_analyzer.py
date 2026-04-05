"""
SOLÉNN v2 - Order Flow, Spoof Detection, Liquidity & Book Intelligence
Core/awareness layer: pure Python, no numpy, frozen dataclasses.
"""

from __future__ import annotations

import math
import os
import time
from collections import Counter, deque, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ============================================================
# Types
# ============================================================

@dataclass(frozen=True, slots=True)
class OrderBookSnapshot:
    timestamp_us: int
    bids: List[Tuple[float, float]]  # [(price, qty), ...]
    asks: List[Tuple[float, float]]


@dataclass(frozen=True, slots=True)
class TradeTick:
    timestamp_us: int
    price: float
    volume: float
    is_buy: bool  # aggressor side


@dataclass(frozen=True, slots=True)
class OrderEvent:
    timestamp_us: int
    order_id: str
    side: str  # "buy" / "sell"
    action: str  # "place" / "cancel" / "fill"
    price: float
    volume: float


# ============================================================
# VPIN - Volume-synchronized Probability of Informed Trading
# ============================================================

class VPINCalculator:
    def __init__(self, bucket_volume: float = 100.0, num_buckets: int = 50) -> None:
        self._bucket_volume = bucket_volume
        self._num_buckets = num_buckets
        self._current_buy = 0.0
        self._current_sell = 0.0
        self._buckets: deque[float] = deque(maxlen=num_buckets)
        self._total_trades = 0

    def update(self, volume: float, is_buy: bool) -> float | None:
        self._total_trades += 1
        if is_buy:
            self._current_buy += volume
        else:
            self._current_sell += volume

        total_in_bucket = self._current_buy + self._current_sell
        if total_in_bucket >= self._bucket_volume:
            denom = max(1e-10, self._bucket_volume)
            imbalance = abs(self._current_buy - self._current_sell) / denom
            self._buckets.append(imbalance)
            self._current_buy = 0.0
            self._current_sell = 0.0

        if len(self._buckets) >= self._num_buckets:
            return sum(self._buckets) / len(self._buckets)
        return None

    @property
    def is_warm(self) -> bool:
        return len(self._buckets) >= self._num_buckets

    @property
    def avg_vpin(self) -> float:
        return sum(self._buckets) / len(self._buckets) if self._buckets else 0.0


# ============================================================
# Flow Toxicity Monitor
# ============================================================

class FlowToxicityMonitor:
    def __init__(self, threshold: float = 0.7) -> None:
        self._threshold = threshold
        self._recent_vpin: deque[float] = deque(maxlen=50)
        self._toxic_streak = 0
        self._last_toxic_at = 0.0

    def update(self, vpin: float) -> Tuple[bool, float]:
        self._recent_vpin.append(vpin)
        is_toxic = vpin > self._threshold
        if is_toxic:
            self._toxic_streak += 1
            self._last_toxic_at = time.time()
        else:
            self._toxic_streak = 0
        avg = sum(self._recent_vpin) / len(self._recent_vpin) if self._recent_vpin else 0.0
        return is_toxic, avg

    @property
    def toxic_streak(self) -> int:
        return self._toxic_streak

    @property
    def seconds_since_last_toxic(self) -> float:
        return time.time() - self._last_toxic_at if self._last_toxic_at > 0 else float("inf")


# ============================================================
# Flow Direction Entropy (Lempel-Ziv)
# ============================================================

class FlowDirectionEntropy:
    def __init__(self, window: int = 200) -> None:
        self._directions: deque[str] = deque(maxlen=window)

    def update(self, direction: str) -> float:
        self._directions.append(direction)
        seq = "".join(self._directions)
        if len(seq) < 2:
            return 0.0
        return _lz_complexity(seq)


def _lz_complexity(seq: str) -> float:
    n = len(seq)
    seen = set()
    max_len = min(8, n)
    for length in range(1, max_len + 1):
        for start in range(n - length + 1):
            seen.add(seq[start:start + length])
    max_possible = sum(min(n - l + 1, 2 ** l) for l in range(1, max_len + 1))
    return len(seen) / max(max_possible, 1)


# ============================================================
# Aggressor Side Detector (Lee-Ready tick test)
# ============================================================

class AggressorSideDetector:
    def __init__(self) -> None:
        self._last_price: Optional[float] = None
        self._history: deque[str] = deque(maxlen=20)

    def classify(self, price: float, bid: float, ask: float) -> str:
        if self._last_price is None:
            self._last_price = price
            return "unknown"

        change = price - self._last_price
        if change > 0:
            result = "buy"
        elif change < 0:
            result = "sell"
        else:
            mid = (bid + ask) / 2.0 if (bid > 0 and ask > 0) else None
            if mid is not None:
                result = "buy" if price >= mid else "sell"
            else:
                prev = self._history[-1] if self._history else "unknown"
                result = prev if prev != "unknown" else "sell"

        self._history.append(result)
        self._last_price = price
        return result


# ============================================================
# Order Flow Imbalance
# ============================================================

class OrderFlowImbalance:
    def __init__(self, levels: int = 10) -> None:
        self._levels = levels

    @staticmethod
    def compute(bids: List[float], asks: List[float], levels: int = 10) -> float:
        n = min(len(bids), len(asks), levels)
        if n == 0:
            return 0.0
        total_bid = sum(bids[:n])
        total_ask = sum(asks[:n])
        total = total_bid + total_ask
        if total == 0:
            return 0.0
        return (total_bid - total_ask) / total

    @staticmethod
    def imbalance_ratio(bids: List[float], asks: List[float]) -> float:
        tb = sum(bids)
        ta = sum(asks)
        tot = tb + ta
        return (tb - ta) / tot if tot > 0 else 0.0


# ============================================================
# Depth Velocity Tracker
# ============================================================

class DepthVelocityTracker:
    def __init__(self, window: int = 50) -> None:
        self._snapshots: deque[List[float]] = deque(maxlen=window)

    def update(self, bids: List[float], asks: List[float]) -> float:
        current = list(bids) + list(asks)
        self._snapshots.append(current)
        if len(self._snapshots) < 2:
            return 0.0
        prev = self._snapshots[-2]
        if not prev:
            return 0.0
        return sum(abs(c - p) for c, p in zip(current, prev))


# ============================================================
# Book Pressure Gradient
# ============================================================

class BookPressureGradient:
    def __init__(self) -> None:
        self._prev: Optional[List[float]] = None

    def compute(self, bids: List[float], asks: List[float]) -> float:
        current = list(bids) + list(asks)
        if self._prev is None:
            self._prev = current
            return 0.0
        pressure = sum((i + 1) * (c - p) for i, (c, p) in enumerate(zip(current, self._prev)))
        self._prev = current
        return pressure


# ============================================================
# Liquidity Resilience Score
# ============================================================

class LiquidityResilienceScore:
    def __init__(self, recovery_window_s: float = 30.0) -> None:
        self._recovery_window = recovery_window_s
        self._events: List[Tuple[float, float]] = []
        self._score = 1.0

    def record_event(self, depth_lost: float, recovery_time_s: float) -> None:
        self._events.append((time.time(), depth_lost))
        if depth_lost > 0:
            speed = depth_lost / max(recovery_time_s, 0.1)
            self._score = min(1.0, speed / 100.0)

    @property
    def score(self) -> float:
        return max(0.0, self._score)


# ============================================================
# Book Shape Analyzer
# ============================================================

class BookShapeAnalyzer:
    @staticmethod
    def classify(bids: List[float], asks: List[float]) -> str:
        n = min(len(bids), len(asks), 10)
        if n < 2:
            return "unknown"

        b = bids[:n]
        a = asks[:n]

        # Wall
        sb = sum(b)
        sa = sum(a)
        if sb > 0 and max(b) > sb * 0.5:
            return "wall_bid"
        if sa > 0 and max(a) > sa * 0.5:
            return "wall_ask"

        # Flat
        if sb > 0 and sa > 0:
            mean_b = sb / n
            mean_a = sa / n
            cv_b = math.sqrt(sum((x - mean_b) ** 2 for x in b) / n) / mean_b if mean_b > 0 else 0
            cv_a = math.sqrt(sum((x - mean_a) ** 2 for x in a) / n) / mean_a if mean_a > 0 else 0
            if cv_b < 0.3 and cv_a < 0.3:
                return "flat"

        # Gap
        for levels in (b, a):
            for i in range(len(levels) - 1):
                if levels[i] > 0 and levels[i + 1] < levels[i] * 0.1:
                    return "gap"

        return "steep"

    @staticmethod
    def depth_ratio(bids: List[float], asks: List[float], top: int = 3) -> float:
        tb = sum(bids[:top])
        ta = sum(asks[:top])
        return tb / ta if ta > 0 else (2.0 if tb > 0 else 1.0)


# ============================================================
# Market Impact Model (Almgren-Chriss)
# ============================================================

@dataclass
class ImpactCalibration:
    eta: float = 0.1
    gamma: float = 0.6
    n_observations: int = 0

    def impact_bps(self, order_qty: float, book_depth: float) -> float:
        if book_depth <= 0:
            return 100.0
        ratio = order_qty / book_depth
        return self.eta * (ratio ** self.gamma) * 10000


class ImpactModel:
    def __init__(self) -> None:
        self._calibration = ImpactCalibration()
        self._obs: List[Tuple[float, float]] = []

    def calibrate(self, order_qty: float, book_depth: float, actual_impact_bps: float) -> None:
        self._obs.append((order_qty / max(book_depth, 1e-10), actual_impact_bps))
        if len(self._obs) >= 10:
            self._recalibrate()

    def _recalibrate(self) -> None:
        recent = self._obs[-100:]
        x_vals = [math.log(max(r[0], 1e-10)) for r in recent]
        y_vals = [math.log(max(r[1], 1e-10)) for r in recent]
        n = len(x_vals)
        mx = sum(x_vals) / n
        my = sum(y_vals) / n
        ss_xy = sum((x_vals[i] - mx) * (y_vals[i] - my) for i in range(n))
        ss_xx = sum((x - mx) ** 2 for x in x_vals)
        if ss_xx > 0:
            self._calibration.gamma = max(0.1, min(1.5, ss_xy / ss_xx))
            self._calibration.eta = math.exp(my - self._calibration.gamma * mx)
            self._calibration.eta = max(0.01, min(10.0, self._calibration.eta))
            self._calibration.n_observations = n

    def predict(self, order_qty: float, book_depth: float) -> float:
        return self._calibration.impact_bps(order_qty, book_depth)

    @property
    def calibration(self) -> ImpactCalibration:
        return self._calibration


# ============================================================
# Spoof Pattern Detector
# ============================================================

class SpoofDetector:
    def __init__(self, large_order_bps: float = 0.05, cancel_time_ms: float = 500.0) -> None:
        self._large_threshold = large_order_bps
        self._cancel_ms = cancel_time_ms
        self._placed: Dict[str, Tuple[float, float]] = {}
        self._spoof_count = 0
        self._total_cancels = 0

    def record_placement(self, oid: str, size: float, book_depth: float, ts_ms: float) -> None:
        if size > book_depth * self._large_threshold:
            self._placed[oid] = (size, ts_ms)

    def record_cancellation(self, oid: str, ts_ms: float) -> Tuple[bool, float]:
        self._total_cancels += 1
        if oid not in self._placed:
            return False, 0.0
        size, placed_at = self._placed.pop(oid)
        lifetime = ts_ms - placed_at
        is_spoof = lifetime < self._cancel_ms
        if is_spoof:
            self._spoof_count += 1
        conf = max(0.0, 1.0 - (lifetime / self._cancel_ms)) if is_spoof else 0.0
        return is_spoof, conf

    @property
    def spoof_rate(self) -> float:
        return self._spoof_count / max(1, self._total_cancels)


# ============================================================
# Layering Detector
# ============================================================

class LayeringDetector:
    def __init__(self, min_layers: int = 3, cancel_window_ms: float = 1000.0) -> None:
        self._min_layers = min_layers
        self._cancel_window = cancel_window_ms

    def detect(self, events: List[Dict[str, Any]]) -> Tuple[bool, float]:
        if len(events) < self._min_layers * 2:
            return False, 0.0

        layers = [e for e in events if e.get("type") == "place"]
        cancels = [e for e in events if e.get("type") == "cancel"]
        if len(layers) < self._min_layers or len(cancels) < self._min_layers:
            return False, 0.0

        levels = set(e.get("level", 0) for e in layers)
        if len(levels) < self._min_layers:
            return False, 0.0

        cancel_times = [e.get("time", 0) for e in cancels]
        if len(cancel_times) < 2:
            return False, 0.0

        span = max(cancel_times) - min(cancel_times)
        if span < self._cancel_window:
            conf = min(1.0, len(layers) / (self._min_layers + 2))
            return True, conf
        return False, 0.0


# ============================================================
# Spoof Confidence Scorer
# ============================================================

class SpoofConfidenceScorer:
    def __init__(self) -> None:
        self._signals: List[float] = []

    def add(self, confidence: float) -> float:
        self._signals.append(confidence)
        if len(self._signals) > 20:
            self._signals = self._signals[-20:]
        return sum(self._signals) / len(self._signals)

    @property
    def average(self) -> float:
        return sum(self._signals) / len(self._signals) if self._signals else 0.0


# ============================================================
# Volume Profile
# ============================================================

class VolumeProfile:
    def __init__(self, num_bins: int = 100, low: float = 0.0, high: float = 100000.0) -> None:
        self._n = num_bins
        self._low = low
        self._high = high
        self._bs = (high - low) / max(1, num_bins)
        self._buy = [0.0] * num_bins
        self._sell = [0.0] * num_bins

    def add_trade(self, price: float, volume: float, is_buy: bool) -> None:
        if self._bs <= 0:
            return
        idx = int((price - self._low) / self._bs)
        idx = max(0, min(self._n - 1, idx))
        if is_buy:
            self._buy[idx] += volume
        else:
            self._sell[idx] += volume

    @property
    def poc(self) -> float:
        total = [b + s for b, s in zip(self._buy, self._sell)]
        mx = max(total) if total else 0.0
        if mx == 0:
            return (self._low + self._high) / 2
        idx = total.index(mx)
        return self._low + idx * self._bs + self._bs / 2

    @property
    def value_area(self) -> Tuple[float, float]:
        total = [(i, b + s) for i, (b, s) in enumerate(zip(self._buy, self._sell))]
        total.sort(key=lambda x: -x[1])
        tv = sum(x[1] for x in total)
        if tv == 0:
            return (self._low, self._high)
        cum = 0.0
        bins = set()
        for idx, vol in total:
            cum += vol
            bins.add(idx)
            if cum >= tv * 0.7:
                break
        lo = min(bins)
        hi = max(bins)
        return (self._low + lo * self._bs, self._low + (hi + 1) * self._bs)

    @property
    def cumulative_delta(self) -> float:
        return sum(self._buy) - sum(self._sell)

    def reset(self) -> None:
        self._buy = [0.0] * self._n
        self._sell = [0.0] * self._n


# ============================================================
# Market Quality Index
# ============================================================

class MarketQualityIndex:
    def __init__(self) -> None:
        self._spreads: deque[float] = deque(maxlen=100)
        self._depths: deque[float] = deque(maxlen=100)
        self._toxicity: deque[float] = deque(maxlen=100)

    def update(self, spread_bps: float, depth_usd: float, vpin: float) -> float:
        self._spreads.append(spread_bps)
        self._depths.append(depth_usd)
        self._toxicity.append(vpin)
        spread_score = max(0.0, 100.0 - spread_bps * 5.0)
        avg_depth = sum(self._depths) / len(self._depths) if self._depths else 0.0
        depth_score = min(100.0, avg_depth / 1000.0)
        avg_tox = sum(self._toxicity) / len(self._toxicity) if self._toxicity else 0.0
        tox_score = max(0.0, 100.0 - avg_tox * 200.0)
        return spread_score * 0.35 + depth_score * 0.35 + tox_score * 0.3

    @property
    def current(self) -> float:
        if not self._spreads:
            return 0.0
        s = self._spreads[-1]
        d = self._depths[-1] if self._depths else 0.0
        t = self._toxicity[-1] if self._toxicity else 0.0
        return (max(0.0, 100.0 - s * 5.0) * 0.35
                + min(100.0, d / 1000.0) * 0.35
                + max(0.0, 100.0 - t * 200.0) * 0.3)


# ============================================================
# Liquidity Absorption/Iceberg Detector
# ============================================================

class LiquidityAbsorptionDetector:
    def __init__(self, window: int = 50, vol_threshold: float = 3.0) -> None:
        self._window = window
        self._vol_thr = vol_threshold
        self._price_changes: deque[float] = deque(maxlen=window)
        self._volumes: deque[float] = deque(maxlen=window)
        self._signal = False

    def update(self, volume: float, price_change: float) -> bool:
        self._volumes.append(volume)
        self._price_changes.append(abs(price_change))
        if len(self._volumes) < 10:
            return False
        avg_vol = sum(list(self._volumes)[-20:]) / min(20, len(self._volumes))
        vol_z = (volume - avg_vol) / max(1e-10, _std(list(self._volumes)))
        avg_price_move = sum(self._price_changes) / len(self._price_changes)
        self._signal = (vol_z > self._vol_thr) and (avg_price_move < 0.001)
        return self._signal

    @property
    def is_absorbing(self) -> bool:
        return self._signal


# ============================================================
# Book Depth Analyzer
# ============================================================

class BookDepthAnalyzer:
    @staticmethod
    def wall_detect(depths: List[float]) -> Optional[Tuple[int, float]]:
        total = sum(depths)
        if total <= 0:
            return None
        for i, d in enumerate(depths):
            if d > total * 0.4:
                return (i, d)
        return None

    @staticmethod
    def imbalance(bids: List[float], asks: List[float], levels: int = 5) -> float:
        tb = sum(bids[:levels])
        ta = sum(asks[:levels])
        tot = tb + ta
        return (tb - ta) / tot if tot > 0 else 0.0

    @staticmethod
    def depth_trend(history: List[float]) -> str:
        if len(history) < 5:
            return "unknown"
        recent = history[-5:]
        m = sum(recent) / len(recent)
        first_half = sum(recent[:2]) / 2
        second_half = sum(recent[2:]) / (len(recent) - 2)
        if second_half > first_half * 1.1:
            return "increasing"
        elif second_half < first_half * 0.9:
            return "decreasing"
        return "stable"


# ============================================================
# Crash Velocity Tracker
# ============================================================

class CrashVelocityTracker:
    def __init__(self, lookback: int = 20) -> None:
        self._lookback = lookback
        self._prices: deque[float] = deque(maxlen=200)
        self._z_scores: deque[float] = deque(maxlen=lookback)

    def update(self, price: float) -> Tuple[float, bool]:
        self._prices.append(price)
        if len(self._prices) < 30:
            return 0.0, False
        rets = [(self._prices[i] - self._prices[i - 1]) / max(1e-10, abs(self._prices[i - 1]))
                for i in range(1, len(self._prices))]
        recent = rets[-self._lookback:]
        mean_ret = sum(recent) / len(recent)
        std_ret = _std(recent) if len(recent) > 1 else 1e-10
        last_z = (rets[-1] - mean_ret) / max(1e-10, std_ret)
        self._z_scores.append(last_z)
        cascade = all(z < -2.0 for z in list(self._z_scores)[-5:])
        return last_z, cascade

    @property
    def current_z(self) -> float:
        return self._z_scores[-1] if self._z_scores else 0.0


# ============================================================
# Liquid State Classifier
# ============================================================

class LiquidStateClassifier:
    def __init__(self) -> None:
        self._spread_history: deque[float] = deque(maxlen=50)
        self._depth_history: deque[float] = deque(maxlen=50)

    def update(self, spread_bps: float, depth_usd: float) -> str:
        self._spread_history.append(spread_bps)
        self._depth_history.append(depth_usd)
        avg_spread = sum(self._spread_history) / len(self._spread_history)
        avg_depth = sum(self._depth_history) / len(self._depth_history)
        if avg_spread < 2.0 and avg_depth > 500000:
            return "solid"
        elif avg_spread < 5.0 and avg_depth > 100000:
            return "liquid"
        elif avg_spread < 15.0 and avg_depth > 10000:
            return "fluid"
        elif avg_depth > 1000:
            return "gas"
        return "frozen"


# ============================================================
# Market Fluid Model (Navier-Stokes analogy)
# ============================================================

class MarketFluidModel:
    def __init__(self, window: int = 100) -> None:
        self._window = window
        self._velocities: deque[float] = deque(maxlen=window)
        self._pressures: deque[float] = deque(maxlen=window)
        self._last_price: float = 0.0

    def update(self, price: float, volume: float, spread_bps: float) -> Dict[str, float]:
        if self._last_price == 0.0:
            self._last_price = price
            return {}
        vel = abs(price - self._last_price) * volume
        self._velocities.append(vel)
        self._pressures.append(1.0 / max(spread_bps, 0.1))
        self._last_price = price
        return self._compute()

    def _compute(self) -> Dict[str, float]:
        vels = list(self._velocities)
        presses = list(self._pressures)
        n = len(vels)
        if n < 10:
            return {}
        mean_v = sum(vels) / n
        var_v = _variance(vels)
        mean_p = sum(presses) / n
        reynolds = math.sqrt(mean_v) / max(1e-10, math.sqrt(var_v)) if var_v > 0 else 0.0
        viscosity = 1.0 / max(1e-10, var_v)
        return {
            "mean_velocity": mean_v,
            "velocity_variance": var_v,
            "mean_pressure": mean_p,
            "reynolds": reynolds,
            "viscosity": viscosity,
            "is_turbulent": reynolds > 2.0,
        }


# ============================================================
# Order Flow Kinetics (Maxwell-Boltzmann distribution)
# ============================================================

class OrderFlowKinetics:
    def __init__(self, window: int = 200) -> None:
        self._sizes: deque[float] = deque(maxlen=window)

    def update(self, size: float) -> Dict[str, float]:
        self._sizes.append(abs(size))
        if len(self._sizes) < 30:
            return {}
        sizes = list(self._sizes)
        n = len(sizes)
        mean_s = sum(sizes) / n
        var_s = _variance(sizes)
        hist_counts, hist_centres = _histogram(sizes, 20)
        mode_idx = max(range(len(hist_counts)), key=lambda i: hist_counts[i])
        mode_s = hist_centres[mode_idx]
        return {
            "mean_size": mean_s,
            "std_size": math.sqrt(max(0.0, var_s)),
            "mode_size": mode_s,
            "n_orders": n,
        }


# ============================================================
# Ghost Order Detector
# ============================================================

class GhostOrderDetector:
    def __init__(self, vanish_threshold_pct: float = 0.5) -> None:
        self._threshold = vanish_threshold_pct
        self._ghost_events = 0
        self._total_checks = 0

    def check(self, prev_depth: float, curr_depth: float, executed_volume: float) -> bool:
        self._total_checks += 1
        vanished = max(0.0, prev_depth - curr_depth - executed_volume)
        if vanished > prev_depth * self._threshold:
            self._ghost_events += 1
            return True
        return False

    @property
    def ghost_rate(self) -> float:
        return self._ghost_events / max(1, self._total_checks)


# ============================================================
# Liquidity Trap Detector
# ============================================================

class LiquidityTrapDetector:
    def __init__(self, window: int = 20) -> None:
        self._window = window
        self._volume_history: deque[float] = deque(maxlen=window)
        self._spread_history: deque[float] = deque(maxlen=window)
        self._price_history: deque[float] = deque(maxlen=window)

    def update(self, volume: float, spread_bps: float, price_change: float) -> bool:
        self._volume_history.append(volume)
        self._spread_history.append(spread_bps)
        self._price_history.append(abs(price_change))
        if len(self._volume_history) < 10:
            return False
        vols = list(self._volume_history)
        spreads = list(self._spread_history)
        vol_surge = vols[-1] > sum(vols[:-1]) / len(vols[:-1]) * 2.0
        spread_widen = spreads[-1] > max(spreads[:-1]) * 1.5
        return vol_surge and spread_widen


# ============================================================
# Composite Order Flow Intelligence
# ============================================================

@dataclass
class FlowState:
    timestamp: float
    vpin: float
    flow_imbalance: float
    aggressor_side: str
    toxicity: bool
    lz_entropy: float
    spoof_rate: float
    book_shape: str
    market_quality: float
    impact_eta: float
    impact_gamma: float
    cumulative_delta: float
    poc: float
    absorption: bool
    crash_z: float
    liquidity_state: str
    reynolds: float
    tradable: bool


class OrderFlowIntelligence:
    def __init__(self) -> None:
        self._vpin = VPINCalculator(bucket_volume=100.0, num_buckets=50)
        self._imbalance = OrderFlowImbalance(levels=10)
        self._aggressor = AggressorSideDetector()
        self._toxicity = FlowToxicityMonitor(threshold=0.7)
        self._entropy = FlowDirectionEntropy(window=200)
        self._spoof = SpoofDetector(large_order_bps=0.05, cancel_time_ms=500.0)
        self._layering = LayeringDetector(min_layers=3, cancel_window_ms=1000.0)
        self._layer_events: deque[Dict[str, Any]] = deque(maxlen=50)
        self._impact = ImpactModel()
        self._vol_profile = VolumeProfile(num_bins=100, low=0.0, high=200000.0)
        self._quality = MarketQualityIndex()
        self._absorption = LiquidityAbsorptionDetector(window=50, vol_threshold=3.0)
        self._crash = CrashVelocityTracker(lookback=20)
        self._liquid_state = LiquidStateClassifier()
        self._fluid = MarketFluidModel(window=100)
        self._ghost = GhostOrderDetector()
        self._depth_velocity = DepthVelocityTracker(window=50)
        self._pressure = BookPressureGradient()
        self._book_shape = BookShapeAnalyzer()
        self._prev_bid_prices: list[float] = []

    def on_tick(self, price: float, volume: float, bid: float, ask: float, is_buy: bool) -> FlowState:
        vp = self._vpin.update(volume, is_buy) or 0.0
        tox, _ = self._toxicity.update(vp)
        ent = self._entropy.update("B" if is_buy else "S")
        side = self._aggressor.classify(price, bid, ask)

        self._vol_profile.add_trade(price, volume, is_buy)

        spread_bps = (ask - bid) / max(1e-10, price) * 10000 if ask > bid else 0.0
        mq = self._quality.update(spread_bps, bid + ask, vp)

        prev_price = self._prev_bid_prices[-1] if self._prev_bid_prices else price
        self._prev_bid_prices.append(price)
        pc = abs(price - prev_price) / max(1e-10, abs(prev_price))
        absorbed = self._absorption.update(volume, pc)

        cz, _ = self._crash.update(price)
        ls = self._liquid_state.update(spread_bps, bid + ask)

        fluid = self._fluid.update(price, volume, spread_bps)
        reynolds = fluid.get("reynolds", 0.0)

        tradable = (not tox
                    and vp < 0.8
                    and not absorbed
                    and spread_bps < 20.0
                    and abs(cz) < 5.0)

        return FlowState(
            timestamp=time.time(),
            vpin=vp,
            flow_imbalance=0.0,
            aggressor_side=side,
            toxicity=tox,
            lz_entropy=ent,
            spoof_rate=self._spoof.spoof_rate,
            book_shape="unknown",
            market_quality=mq,
            impact_eta=self._impact.calibration.eta,
            impact_gamma=self._impact.calibration.gamma,
            cumulative_delta=self._vol_profile.cumulative_delta,
            poc=self._vol_profile.poc,
            absorption=absorbed,
            crash_z=cz,
            liquidity_state=ls,
            reynolds=reynolds,
            tradable=tradable,
        )

    def on_book_update(self, bids: List[Tuple[float, float]], asks: List[Tuple[float, float]]) -> Dict[str, Any]:
        bid_depths = [q for _, q in bids]
        ask_depths = [q for _, q in asks]
        imb = OrderFlowImbalance.compute(bid_depths, ask_depths)
        shape = self._book_shape.classify(bid_depths, ask_depths)
        dv = self._depth_velocity.update(bid_depths, ask_depths)
        pg = self._pressure.compute(bid_depths, ask_depths)
        return {
            "imbalance": imb,
            "shape": shape,
            "depth_velocity": dv,
            "pressure_gradient": pg,
        }

    def on_order_event(self, event: OrderEvent) -> None:
        ts_ms = event.timestamp_us / 1000.0
        if event.action == "place":
            self._spoof.record_placement(event.order_id, event.volume, 1.0, ts_ms)
            self._layer_events.append({
                "type": "place", "level": int(event.price), "time": ts_ms, "size": event.volume,
            })
        elif event.action == "cancel":
            is_s, conf = self._spoof.record_cancellation(event.order_id, ts_ms)
            self._layer_events.append({
                "type": "cancel", "level": int(event.price), "time": ts_ms, "size": event.volume,
            })
        elif event.action == "fill":
            self._impact.calibrate(event.volume, 1.0, max(1.0, abs(event.price - 100.0)))


# ============================================================
# Helpers
# ============================================================

def _variance(values: List[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    m = sum(values) / n
    return sum((x - m) ** 2 for x in values) / n


def _std(values: List[float]) -> float:
    return math.sqrt(max(0.0, _variance(values)))


def _histogram(values: List[float], n_bins: int = 20) -> Tuple[List[int], List[float]]:
    if not values:
        return [], []
    lo = min(values)
    hi = max(values)
    if lo == hi:
        return [len(values)], [lo]
    bw = (hi - lo) / n_bins
    counts = [0] * n_bins
    centres = [lo + bw / 2 + i * bw for i in range(n_bins)]
    for v in values:
        idx = min(int((v - lo) / bw), n_bins - 1)
        counts[idx] += 1
    return counts, centres
