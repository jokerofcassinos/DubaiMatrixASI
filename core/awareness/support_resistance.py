"""
SOLNN v2 — Support/Resistance, Swing Detection, Chart Patterns,
            and Market Structure Analysis.
Pure Python, no numpy, frozen dataclasses.
"""

from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ============================================================
# Types
# ============================================================

class MarketStructure(Enum):
    UPTREND = "uptrend"
    DOWNTREND = "downtrend"
    RANGING = "ranging"
    CHANGING = "changing"


class ChartPattern(Enum):
    UNKNOWN = "unknown"
    HEAD_AND_SHOULDERS = "head_shoulders"
    INV_HEAD_SHOULDERS = "inv_head_shoulders"
    DOUBLE_TOP = "double_top"
    DOUBLE_BOTTOM = "double_bottom"
    ASC_TRIANGLE = "ascending_triangle"
    DESC_TRIANGLE = "descending_triangle"
    SYM_TRIANGLE = "sym_triangle"
    BULL_FLAG = "bull_flag"
    BEAR_FLAG = "bear_flag"
    WEDGE_UP = "wedge_up"
    WEDGE_DOWN = "wedge_down"


@dataclass(frozen=True, slots=True)
class PriceLevel:
    price: float
    strength: float  # 0–1 how strong the level is
    touches: int
    last_touch_ts: float
    is_support: bool


@dataclass(frozen=True, slots=True)
class SwingPoint:
    price: float
    index: int
    is_high: bool
    timestamp: float


@dataclass(frozen=True, slots=True)
class FibonacciLevels:
    low: float
    high: float
    levels: List[Tuple[str, float]]  # (name, price)


@dataclass(frozen=True, slots=True)
class StructureState:
    structure: MarketStructure
    last_high: float
    last_low: float
    swing_highs: List[float]
    swing_lows: List[float]
    support_levels: List[PriceLevel]
    resistance_levels: List[PriceLevel]
    pattern: ChartPattern
    pattern_confidence: float
    fib_levels: List[Tuple[str, float]]
    order_blocks: List[Tuple[float, float]]  # (low, high)
    fair_value_gaps: List[Tuple[float, float]]  # (low, high)


# ============================================================
# Support/Resistance Detector
# ============================================================

class SupportResistanceDetector:
    def __init__(self, window: int = 100, swing_window: int = 5,
                 price_cluster_px: float = 0.002) -> None:
        self._window = window
        self._swing_w = swing_window
        self._cluster_px = price_cluster_px
        self._prices: deque[float] = deque(maxlen=window)
        self._swing_highs: List[SwingPoint] = []
        self._swing_lows: List[SwingPoint] = []

    def update(self, price: float) -> List[PriceLevel]:
        self._prices.append(price)
        idx = len(self._prices) - 1
        if idx < self._swing_w * 2:
            return []

        self._detect_swing_high(idx)
        self._detect_swing_low(idx)

        # Cluster swings into levels
        levels = self._cluster_levels()
        return levels

    def _detect_swing_high(self, idx: int) -> None:
        p = list(self._prices)
        n = len(p)
        w = self._swing_w
        if idx - w < 0 or idx + w >= n:
            return
        centre = p[idx]
        is_high = all(centre >= p[idx - i] for i in range(1, w + 1)) and \
                  all(centre >= p[idx + i] for i in range(1, w + 1))
        if is_high:
            ts = time.time()
            self._swing_highs.append(SwingPoint(centre, idx, True, ts))

    def _detect_swing_low(self, idx: int) -> None:
        p = list(self._prices)
        n = len(p)
        w = self._swing_w
        if idx - w < 0 or idx + w >= n:
            return
        centre = p[idx]
        is_low = all(centre <= p[idx - i] for i in range(1, w + 1)) and \
                 all(centre <= p[idx + i] for i in range(1, w + 1))
        if is_low:
            ts = time.time()
            self._swing_lows.append(SwingPoint(centre, idx, False, ts))

    def _cluster_levels(self, max_levels: int = 10) -> List[PriceLevel]:
        result = []
        now = time.time()
        # Cluster swing highs → resistance
        result.extend(
            self._cluster_points(self._swing_highs, is_support=False, max_levels=max_levels)
        )
        # Cluster swing lows → support
        result.extend(
            self._cluster_points(self._swing_lows, is_support=True, max_levels=max_levels)
        )
        return sorted(result, key=lambda l: -l.strength)

    def _cluster_points(
        self, swings: List[SwingPoint], is_support: bool, max_levels: int
    ) -> List[PriceLevel]:
        if not swings:
            return []
        used = set()
        levels = []
        now = time.time()
        for swing in swings:
            if swing.price in used:
                continue
            cluster_px = swing.price * self._cluster_px
            touches = []
            for s in swings:
                if abs(s.price - swing.price) <= cluster_px:
                    used.add(s.price)
                    touches.append(s)
            if touches:
                avg_price = sum(t.price for t in touches) / len(touches)
                strength = min(1.0, len(touches) / 5.0)
                # Recency boost
                ages = [now - t.timestamp for t in touches]
                youngest = min(ages)
                recency = math.exp(-youngest / 3600)  # 1hr decay
                strength = strength * 0.7 + recency * 0.3
                levels.append(PriceLevel(
                    price=avg_price, strength=strength,
                    touches=len(touches), last_touch_ts=max(t.timestamp for t in touches),
                    is_support=is_support
                ))
        return sorted(levels, key=lambda l: -l.strength)[:max_levels]

    @property
    def swing_highs(self) -> List[float]:
        return [s.price for s in self._swing_highs]

    @property
    def swing_lows(self) -> List[float]:
        return [s.price for s in self._swing_lows]


# ============================================================
# Fibonacci Analyzer
# ============================================================

class FibonacciAnalyzer:
    RATIOS = {
        "0.0%": 0.0,
        "23.6%": 0.236,
        "38.2%": 0.382,
        "50.0%": 0.5,
        "61.8%": 0.618,
        "78.6%": 0.786,
        "100%": 1.0,
        "161.8%": 1.618,
        "261.8%": 2.618,
    }

    @staticmethod
    def retracement(high_price: float, low_price: float) -> FibonacciLevels:
        diff = high_price - low_price
        levels = [(name, low_price + diff * ratio)
                   for name, ratio in FibonacciAnalyzer.RATIOS.items()]
        return FibonacciLevels(low=low_price, high=high_price, levels=levels)


# ============================================================
# Chart Pattern Engine
# ============================================================

class ChartPatternEngine:
    def __init__(self, tolerance: float = 0.02) -> None:
        self._tolerance = tolerance
        self._prices: deque[float] = deque(maxlen=300)

    def detect(self) -> Tuple[ChartPattern, float]:
        ps = list(self._prices)
        if len(ps) < 30:
            return ChartPattern.UNKNOWN, 0.0

        # Detect head & shoulders
        hs = self._head_shoulders(ps)
        if hs:
            return ChartPattern.HEAD_AND_SHOULDERS, hs

        ihs = self._inverse_head_shoulders(ps)
        if ihs:
            return ChartPattern.INV_HEAD_SHOULDERS, ihs

        dt = self._double_top(ps)
        if dt:
            return ChartPattern.DOUBLE_TOP, dt

        db = self._double_bottom(ps)
        if db:
            return ChartPattern.DOUBLE_BOTTOM, db

        return ChartPattern.UNKNOWN, 0.0

    def update(self, price: float) -> None:
        self._prices.append(price)

    # --- Pattern detectors ---

    def _head_shoulders(self, ps: List[float]) -> float:
        """Left shoulder, head (higher), right shoulder (≈left shoulder)."""
        n = len(ps)
        swing_w = n // 10
        if swing_w < 3:
            return 0.0

        highs = _local_extrema(ps, swing_w, find_high=True)
        if len(highs) < 3:
            return 0.0

        # Check last 3 highs for H&S
        l_s = highs[-3]
        head = highs[-2]
        r_s = highs[-1]

        # Head is higher than both shoulders
        if head[0] <= l_s[0] or head[0] <= r_s[0]:
            return 0.0
        # Shoulders are similar height
        shoulder_diff = abs(l_s[0] - r_s[0])
        shoulder_avg = (l_s[0] + r_s[0]) / 2
        if shoulder_diff > shoulder_avg * self._tolerance * 3:
            return 0.0

        # Neckline between the lows
        lows = _local_extrema(ps, swing_w, find_high=False)
        if len(lows) < 2:
            return 0.0

        conf = min(1.0, 0.5 + (1.0 - shoulder_diff / max(shoulder_avg, 0.01)) * 0.5)
        return conf * 0.8  # Scale down

    def _inverse_head_shoulders(self, ps: List[float]) -> float:
        """Same logic inverted."""
        n = len(ps)
        swing_w = n // 10
        if swing_w < 3:
            return 0.0
        lows = _local_extrema(ps, swing_w, find_high=False)
        if len(lows) < 3:
            return 0.0
        l_s = lows[-3]
        head = lows[-2]
        r_s = lows[-1]
        if head[0] >= l_s[0] or head[0] >= r_s[0]:
            return 0.0
        shoulder_diff = abs(l_s[0] - r_s[0])
        shoulder_avg = (l_s[0] + r_s[0]) / 2
        if shoulder_diff > shoulder_avg * self._tolerance * 3:
            return 0.0
        conf = min(1.0, 0.5 + (1.0 - shoulder_diff / max(shoulder_avg, 0.01)) * 0.5)
        return conf * 0.8

    def _double_top(self, ps: List[float]) -> float:
        n = len(ps)
        swing_w = n // 10
        if swing_w < 3:
            return 0.0
        highs = _local_extrema(ps, swing_w, find_high=True)
        if len(highs) < 2:
            return 0.0
        h1 = highs[-2]
        h2 = highs[-1]
        diff = abs(h1[0] - h2[0])
        avg = (h1[0] + h2[0]) / 2
        if diff < avg * self._tolerance * 2:
            return 0.7
        return 0.0

    def _double_bottom(self, ps: List[float]) -> float:
        n = len(ps)
        swing_w = n // 10
        if swing_w < 3:
            return 0.0
        lows = _local_extrema(ps, swing_w, find_high=False)
        if len(lows) < 2:
            return 0.0
        l1 = lows[-2]
        l2 = lows[-1]
        diff = abs(l1[0] - l2[0])
        avg = (l1[0] + l2[0]) / 2
        if diff < avg * self._tolerance * 2:
            return 0.7
        return 0.0


# ============================================================
# Swing Detector
# ============================================================

class SwingDetector:
    def __init__(self, window: int = 5) -> None:
        self._w = window
        self._prices: deque[float] = deque(maxlen=500)
        self._structure = MarketStructure.RANGING
        self._higher_highs = 0
        self._lower_lows = 0
        self._swing_points: List[SwingPoint] = []

    def update(self, price: float) -> Tuple[MarketStructure, List[SwingPoint]]:
        self._prices.append(price)
        idx = len(self._prices) - 1
        self._detect_swing(idx)
        self._update_structure()
        return self._structure, self._swing_points

    def _detect_swing(self, idx: int) -> None:
        p = list(self._prices)
        n = len(p)
        w = self._w
        if idx < w or idx + w >= n:
            return
        centre = p[idx]
        is_high = all(centre >= p[idx - i] for i in range(1, w + 1)) and \
                  all(centre >= p[idx + i] for i in range(1, w + 1))
        is_low = all(centre <= p[idx - i] for i in range(1, w + 1)) and \
                 all(centre <= p[idx + i] for i in range(1, w + 1))
        if is_high:
            sp = SwingPoint(centre, idx, True, time.time())
            self._swing_points.append(sp)
        if is_low:
            sp = SwingPoint(centre, idx, False, time.time())
            self._swing_points.append(sp)

    def _update_structure(self) -> None:
        if len(self._swing_points) < 4:
            return
        # Check last 4 swings
        recent = self._swing_points[-4:]
        highs = [s.price for s in recent if s.is_high]
        lows = [s.price for s in recent if not s.is_high]

        hh = 0
        lh = 0
        ll = 0
        hl = 0

        if len(highs) >= 2:
            if highs[-1] > highs[-2]:
                hh += 1
            else:
                lh += 1
        if len(lows) >= 2:
            if lows[-1] > lows[-2]:
                hl += 1
            else:
                ll += 1

        if hh > lh and hl > ll:
            self._structure = MarketStructure.UPTREND
        elif ll > hl and lh > hh:
            self._structure = MarketStructure.DOWNTREND
        else:
            self._structure = MarketStructure.RANGING


# ============================================================
# Order Block Detector
# ============================================================

class OrderBlockDetector:
    def __init__(self) -> None:
        self._blocks: List[Tuple[float, float]] = []

    def find_order_blocks(self, swing_points: List[SwingPoint]) -> List[Tuple[float, float]]:
        """Bearish OB before large up moves, bullish OB before large down moves."""
        if len(swing_points) < 2:
            return []
        blocks = []
        for i in range(1, len(swing_points)):
            prev = swing_points[i - 1]
            curr = swing_points[i]
            move = abs(curr.price - prev.price)
            if move > prev.price * 0.005:  # > 0.5% move
                if prev.is_high and curr.price > prev.price:
                    # Bearish OB before the move up (failed drop)
                    ob_low = prev.price * 0.998
                    ob_high = prev.price
                    blocks.append((ob_low, ob_high))
                elif not prev.is_high and curr.price < prev.price:
                    # Bullish OB before the move down
                    ob_low = prev.price
                    ob_high = prev.price * 1.002
                    blocks.append((ob_low, ob_high))
        self._blocks = blocks
        return blocks


# ============================================================
# Fair Value Gap Detector
# ============================================================

class FairValueGapDetector:
    def __init__(self) -> None:
        self._gaps: List[Tuple[float, float]] = []
        self._prices: deque[float] = deque(maxlen=500)
        self._highs: deque[float] = deque(maxlen=500)
        self._lows: deque[float] = deque(maxlen=500)

    def update(self, high: float, low: float, close: float) -> List[Tuple[float, float]]:
        self._highs.append(high)
        self._lows.append(low)
        self._prices.append(close)
        if len(self._highs) < 3:
            return []
        h = list(self._highs)
        l = list(self._lows)
        gaps = []
        # Check last 3 candles for FVG
        if h[-3] < l[-1]:
            gaps.append((h[-3], l[-1]))
        if l[-3] > h[-1]:
            gaps.append((l[-3], h[-1]))
        self._gaps = gaps
        return gaps


# ============================================================
# Wyckoff/SMC Analyzer
# ============================================================

class WyckoffSMCAnalyzer:
    def __init__(self, window: int = 100) -> None:
        self._window = window
        self._prices: deque[float] = deque(maxlen=window)
        self._volumes: deque[float] = deque(maxlen=window)

    def update(self, price: float, volume: float = 1.0) -> Dict[str, str]:
        self._prices.append(price)
        self._volumes.append(volume)
        if len(self._prices) < 30:
            return {"phase": "warming_up"}

        ps = list(self._prices)
        vs = list(self._volumes)
        phase = self._detect_phase(ps, vs)
        return {"phase": phase}

    def _detect_phase(self, ps: List[float], vs: List[float]) -> str:
        n = len(ps)
        recent = ps[-20:]
        vol_recent = vs[-20:]
        mean_p = sum(recent) / len(recent)
        mean_v = sum(vol_recent) / len(vol_recent)
        trend = (recent[-1] - recent[0]) / max(1e-10, recent[0])
        vol_trend = (vol_recent[-1] - vol_recent[0]) / max(1e-10, max(1, vol_recent[0]))

        if trend > 0.02 and vol_trend > 0.3:
            return "markup"
        elif trend < -0.02 and vol_trend > 0.3:
            return "markdown"
        elif abs(trend) < 0.01 and mean_v < self._get_avg_volume() * 0.7:
            return "accumulation" if recent[-1] < ps[0] else "distribution"
        else:
            return "neutral"

    def _get_avg_volume(self) -> float:
        vs = list(self._volumes)
        return sum(vs) / len(vs) if vs else 1.0


# ============================================================
# Pattern Genesis Detector
# ============================================================

class PatternGenesisDetector:
    def __init__(self, window: int = 100) -> None:
        self._window = window
        self._prices: deque[float] = deque(maxlen=window)
        self._known_patterns: Dict[str, int] = {}

    def update(self, price: float) -> Dict[str, Any]:
        self._prices.append(price)
        if len(self._prices) < 50:
            return {"novelty": 0.0, "pattern": "unknown"}

        # Detect novel patterns via autocorrelation analysis
        ps = list(self._prices)
        acf = _autocorrelation_f(ps, list(range(1, 11)))
        novelty = self._measure_novelty(acf)
        return {"novelty": novelty, "pattern": "novel" if novelty > 0.7 else "known"}

    def _measure_novelty(self, acf: List[float]) -> float:
        if not acf:
            return 0.0
        # Novel = unusual autocorrelation structure
        mean_acf = sum(acf) / len(acf)
        variance = sum((x - mean_acf) ** 2 for x in acf)
        return min(1.0, math.sqrt(variance) * 5)


# ============================================================
# Apex / Trend Extremity Detector
# ============================================================

class ApexDetector:
    def __init__(self, window: int = 100) -> None:
        self._w = window
        self._prices: deque[float] = deque(maxlen=window + 1)

    def update(self, price: float) -> Dict[str, Any]:
        self._prices.append(price)
        if len(self._prices) < 30:
            return {"apex": False, "type": "none", "confidence": 0.0}

        ps = list(self._prices)
        n = len(ps)
        mean_p = sum(ps) / n
        var_p = _variance(ps)
        current_deviation = abs(ps[-1] - mean_p) / max(1e-10, math.sqrt(var_p))

        # Detect climax
        is_climax = current_deviation > 3.0
        is_capitulation = ps[-1] < mean_p and current_deviation > 3.0

        if is_climax and ps[-1] > mean_p:
            apex_type = "CLIMAX_TOP"
        elif is_capitulation:
            apex_type = "CAPITULATION_BOTTOM"
        else:
            apex_type = "none"

        conf = min(1.0, (current_deviation - 2.0) / 3.0) if current_deviation > 2.0 else 0.0
        return {"apex": is_climax or is_capitulation, "type": apex_type, "confidence": conf}


class ArchitectAnalyzer:
    """Analyzes market structure quality."""
    def __init__(self) -> None:
        self._prices: deque[float] = deque(maxlen=200)

    def update(self, price: float) -> Dict[str, Any]:
        self._prices.append(price)
        if len(self._prices) < 30:
            return {"quality": 0.0}
        ps = list(self._prices)
        trend_strength, direction = _linear_regression_strength(ps)
        return {
            "quality": trend_strength,
            "direction": direction,
            "is_trending": trend_strength > 0.7,
        }


# ============================================================
# Supernova Capacitor (Volatility Compression + Volume Anomaly)
# ============================================================

class SupernovaCapacitor:
    def __init__(self, compression_window: int = 30, charge_threshold: float = 0.95) -> None:
        self._cw = compression_window
        self._threshold = charge_threshold
        self._prices: deque[float] = deque(maxlen=100)
        self._volumes: deque[float] = deque(maxlen=100)
        self._charge = 0.0

    def update(self, price: float, volume: float) -> Dict[str, Any]:
        self._prices.append(price)
        self._volumes.append(volume)
        if len(self._prices) < 20:
            return {"charge": 0.0, "triggered": False}

        # Volatility compression
        recent = list(self._prices)[-self._cw:]
        mean_p = sum(recent) / len(recent)
        vol = math.sqrt(sum((p - mean_p) ** 2 for p in recent) / len(recent)) / max(1e-10, mean_p)

        # Volume anomaly
        avg_vol = sum(self._volumes) / len(self._volumes)
        vol_spike = volume / max(1e-10, avg_vol)

        # Charge = compression * vol_spike
        compression = max(0.0, 1.0 - vol * 50)
        self._charge = min(1.0, compression * vol_spike * 0.5)

        triggered = self._charge > self._threshold
        return {"charge": self._charge, "triggered": triggered, "volatility": vol}


# ============================================================
# Market Composite State
# ============================================================

class MultiTimeframeStructure:
    """Master orchestrator combining S/R, swings, patterns, OBs, FVGs."""

    def __init__(self, window: int = 200, swing_window: int = 5) -> None:
        self._sr = SupportResistanceDetector(window=window, swing_window=swing_window)
        self._pattern = ChartPatternEngine(tolerance=0.02)
        self._swing = SwingDetector(window=swing_window)
        self._ob = OrderBlockDetector()
        self._fvg = FairValueGapDetector()
        self._wyckoff = WyckoffSMCAnalyzer(window=window)
        self._genesis = PatternGenesisDetector(window=window)
        self._apex = ApexDetector(window=window)
        self._architect = ArchitectAnalyzer()
        self._supernova = SupernovaCapacitor()
        self._highs: deque[float] = deque(maxlen=200)
        self._lows: deque[float] = deque(maxlen=200)
        self._closes: deque[float] = deque(maxlen=200)
        self._volume = 1.0

    def on_tick(self, price: float, volume: float = 1.0) -> StructureState:
        self._closes.append(price)
        self._volume = volume
        self._pattern.update(price)

        levels = self._sr.update(price)
        structure, swings = self._swing.update(price)
        ob = self._ob.find_order_blocks(swings)

        # FVG needs OHLC; use tick as H/L/C
        self._highs.append(price * 1.001)
        self._lows.append(price * 0.999)
        self._closes.append(price)
        fvg = []
        if len(self._highs) >= 3:
            fvg = self._fvg.update(self._highs[-1], self._lows[-1], self._closes[-1])

        pat, pat_conf = self._pattern.detect()
        apex = self._apex.update(price)
        arch = self._architect.update(price)
        nova = self._supernova.update(price, volume)

        # Fibonacci
        sl = self._sr.swing_lows
        sh = self._sr.swing_highs
        fib_levels = []
        if sl and sh:
            fib = FibonacciAnalyzer.retracement(max(sh), min(sl))
            fib_levels = fib.levels

        sup_levels = [l for l in levels if l.is_support][:5]
        res_levels = [l for l in levels if not l.is_support][:5]

        return StructureState(
            structure=structure,
            last_high=sh[-1] if sh else price,
            last_low=sl[-1] if sl else price,
            swing_highs=sh[-10:],
            swing_lows=sl[-10:],
            support_levels=sup_levels,
            resistance_levels=res_levels,
            pattern=pat,
            pattern_confidence=pat_conf,
            fib_levels=fib_levels,
            order_blocks=ob,
            fair_value_gaps=fvg,
        )


# ============================================================
# Helpers
# ============================================================

def _local_extrema(data: List[float], window: int, find_high: bool) -> List[Tuple[float, int]]:
    """Find local maxima or minima in data."""
    result = []
    for i in range(window, len(data) - window):
        neighbours = data[i - window:i + window + 1]
        if find_high:
            if data[i] == max(neighbours):
                result.append((data[i], i))
        else:
            if data[i] == min(neighbours):
                result.append((data[i], i))
    return result


def _variance(values: List[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    m = sum(values) / n
    return sum((x - m) ** 2 for x in values) / n


def _std(values: List[float]) -> float:
    return math.sqrt(max(0.0, _variance(values)))


def _linear_regression_strength(prices: List[float]) -> Tuple[float, float]:
    n = len(prices)
    if n < 10:
        return 0.0, 0.0
    x_bar = (n - 1) / 2
    y_bar = sum(prices) / n
    ss_xy = sum((i - x_bar) * (prices[i] - y_bar) for i in range(n))
    ss_xx = sum((i - x_bar) ** 2 for i in range(n))
    ss_yy = sum((p - y_bar) ** 2 for p in prices)
    if ss_xx < 1e-12 or ss_yy < 1e-12:
        return 0.0, 0.0
    r2 = min(1.0, ss_xy ** 2 / (ss_xx * ss_yy))
    direction = 1.0 if ss_xy > 0 else -1.0
    return r2, direction


def _autocorrelation_f(values: List[float], lags: List[int]) -> List[float]:
    n = len(values)
    m = sum(values) / n
    var = sum((x - m) ** 2 for x in values) / n
    if var < 1e-12:
        return [0.0] * len(lags)
    result = []
    for lag in lags:
        if lag >= n:
            result.append(0.0)
            continue
        cov = sum((values[i] - m) * (values[i + lag] - m) for i in range(n - lag)) / (n - lag)
        result.append(cov / var)
    return result
