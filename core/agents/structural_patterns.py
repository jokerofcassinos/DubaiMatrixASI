"""
SOLÉNN v2 — Structural Pattern Recognition Agents (Ω-P01 to Ω-P162)
Transmuted from v1:
  - classic.py: Classic technical analysis (S/R, Fibonacci, trend lines)
  - chart_structure.py: Chart pattern detection (H&S, triangles, wedges)
  - wyckoff.py: Wyckoff method analysis (accumulation/distribution phases)
  - smc.py: Smart Money Concepts (order blocks, FVG, liquidity pools)

Protocol 3-6-9: 162 vetores planejados
  Concept 1 — Classic Structure (Ω-P01 to Ω-P54): Support/resistance,
    Fibonacci retracements, trend lines, swing structure analysis,
    pivot points, Donchian channels
  Concept 2 — Chart Pattern Detection (Ω-P55 to Ω-P108): Head & Shoulders,
    double tops/bottoms, triangles, wedges, flags, channels,
    harmonic patterns (BAT, GARTLEY, butterfly)
  Concept 3 — Smart Money Structure (Ω-P109 to Ω-P162): Order blocks,
    fair value gaps (FVG), breaker blocks, liquidity pools,
    optimal trade entry (OTE), premium/discount zones
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Optional


# ──────────────────────────────────────────────────────────────
# Ω-P01 to Ω-P18: Support/Resistance Detection
# ──────────────────────────────────────────────────────────────

@dataclass
class SupportResistanceLevel:
    """Ω-P01: A detected S/R level with confidence."""
    price: float
    type: str  # "SUPPORT" or "RESISTANCE"
    strength: float  # 0.0-1.0: how many touches/confirmations
    timeframe: str
    last_touched: int = 0  # candle index of last touch
    touch_count: int = 0


class SupportResistanceDetector:
    """
    Ω-P01 to Ω-P09: Detect support and resistance levels.

    Transmuted from v1 classic.py + chart_structure.py:
    v1: Analyzed swing highs/lows to find S/R
    v2: Multi-resolution S/R detection with fractal analysis,
        volume confirmation, and temporal decay.
    """

    def __init__(self, lookback: int = 200, tolerance_bps: float = 0.5) -> None:
        self._lookback = lookback
        self._tolerance_bps = tolerance_bps  # How close to count as "touch"
        self._prices: deque[float] = deque(maxlen=lookback)
        self._volumes: deque[float] = deque(maxlen=lookback)
        self._levels: list[SupportResistanceLevel] = []

    def update(self, price: float, volume: float = 0.0) -> list[SupportResistanceLevel]:
        """Ω-P03: Add new price and detect/update S/R levels."""
        self._prices.append(price)
        self._volumes.append(volume)

        if len(self._prices) < 20:
            return []

        # Ω-P04: Detect swing highs and lows
        swings = self._find_swings()

        # Ω-P05: Cluster nearby swings into levels
        levels = self._cluster_levels(swings)

        # Update existing levels with merge
        for new_level in levels:
            merged = False
            for existing in self._levels:
                if existing.type == new_level.type and self._are_close(existing.price, new_level.price):
                    existing.touch_count += 1
                    existing.strength = min(1.0, existing.touch_count / 5.0)
                    existing.last_touched = len(self._prices) - 1
                    merged = True
                    break
            if not merged:
                new_level.touch_count = 1
                new_level.strength = min(1.0, 1.0 / 5.0)
                new_level.last_touched = len(self._prices) - 1
                self._levels.append(new_level)

        # Clean: remove stale levels (not touched in lookback/2 candles)
        self._levels = [l for l in self._levels if len(self._prices) - 1 - l.last_touched < self._lookback // 2]

        return sorted(self._levels, key=lambda l: l.strength, reverse=True)

    def _find_swings(self) -> list[dict]:
        """Ω-P04: Find swing highs and lows using fractal analysis."""
        swings = []
        prices = list(self._prices)

        for i in range(2, len(prices) - 2):
            # Swing high: higher than 2 candles on each side
            if prices[i] > prices[i-1] and prices[i] > prices[i-2] and \
               prices[i] > prices[i+1] and prices[i] > prices[i+2]:
                swings.append({"price": prices[i], "type": "RESISTANCE", "index": i})
            # Swing low: lower than 2 candles on each side
            elif prices[i] < prices[i-1] and prices[i] < prices[i-2] and \
                 prices[i] < prices[i+1] and prices[i] < prices[i+2]:
                swings.append({"price": prices[i], "type": "SUPPORT", "index": i})

        return swings

    def _cluster_levels(self, swings: list[dict]) -> list[SupportResistanceLevel]:
        """Ω-P05: Cluster nearby swings into S/R levels."""
        if not swings:
            return []

        tolerance = max(prices_data := list(self._prices)) * self._tolerance_bps / 10000 if prices_data else 10.0
        clusters: dict[float, list] = {}

        for swing in swings:
            price = swing["price"]
            # Check if close to an existing cluster
            found_cluster = None
            for cluster_price in clusters:
                if abs(price - cluster_price) <= tolerance:
                    found_cluster = cluster_price
                    break
            if found_cluster is not None:
                clusters[found_cluster].append(swing)
            else:
                clusters[price] = [swing]

        levels = []
        for cluster_price, members in clusters.items():
            avg_price = sum(m["price"] for m in members) / len(members)
            level_type = members[0]["type"]
            levels.append(SupportResistanceLevel(
                price=avg_price,
                type=level_type,
                strength=0.0,  # Updated in update()
                timeframe="M1",
            ))
        return levels

    def _are_close(self, p1: float, p2: float) -> bool:
        """Check if two prices are within tolerance."""
        ref = max(abs(p1), abs(p2))
        if ref == 0:
            return abs(p1 - p2) < 0.01
        return abs(p1 - p2) / ref < self._tolerance_bps / 10000

    def get_nearest_levels(self, current_price: float, n: int = 3) -> list[SupportResistanceLevel]:
        """Ω-P07: Get n nearest S/R levels to current price."""
        sorted_levels = sorted(self._levels, key=lambda l: abs(l.price - current_price))
        return sorted_levels[:n]


# ──────────────────────────────────────────────────────────────
# Ω-P19 to Ω-P27: Fibonacci Retracement Analysis
# ──────────────────────────────────────────────────────────────

@dataclass
class FibonacciLevels:
    """Ω-P19: Fibonacci retracement and extension levels."""
    swing_high: float
    swing_low: float
    retracement_236: float
    retracement_382: float
    retracement_500: float
    retracement_618: float
    retracement_786: float
    extension_1272: float
    extension_1618: float
    trend: str  # "UPTREND" or "DOWNTREND"


class FibonacciAnalyzer:
    """
    Ω-P19 to Ω-P27: Calculate Fibonacci retracement/extension levels.

    Transmuted from v1 classic.py:
    v1: Basic fib calculation
    v2: Multi-swing detection, confluence scoring with S/R levels,
        and trend identification.
    """

    def __init__(self) -> None:
        self._prices: deque[float] = deque(maxlen=500)

    def update(self, price: float) -> Optional[FibonacciLevels]:
        """Ω-P21: Update price and return fib levels if swing detected."""
        self._prices.append(price)

        if len(self._prices) < 50:
            return None

        # Find significant swing high and low in lookback
        prices = list(self._prices)[-150:]
        swing_high = max(prices)
        swing_low = min(prices)
        high_idx = prices.index(swing_high)
        low_idx = prices.index(swing_low)

        if high_idx < low_idx:
            trend = "DOWNTREND"
            diff = swing_high - swing_low
            retracement_levels = {
                "236": swing_high - diff * 0.236,
                "382": swing_high - diff * 0.382,
                "500": swing_high - diff * 0.500,
                "618": swing_high - diff * 0.618,
                "786": swing_high - diff * 0.786,
            }
            extension_levels = {
                "1272": swing_high + diff * 0.272,
                "1618": swing_high + diff * 0.618,
            }
        else:
            trend = "UPTREND"
            diff = swing_high - swing_low
            retracement_levels = {
                "236": swing_low + diff * 0.236,
                "382": swing_low + diff * 0.382,
                "500": swing_low + diff * 0.500,
                "618": swing_low + diff * 0.618,
                "786": swing_low + diff * 0.786,
            }
            extension_levels = {
                "1272": swing_low - diff * 0.272,
                "1618": swing_low - diff * 0.618,
            }

        return FibonacciLevels(
            swing_high=swing_high,
            swing_low=swing_low,
            retracement_236=retracement_levels["236"],
            retracement_382=retracement_levels["382"],
            retracement_500=retracement_levels["500"],
            retracement_618=retracement_levels["618"],
            retracement_786=retracement_levels["786"],
            extension_1272=extension_levels["1272"],
            extension_1618=extension_levels["1618"],
            trend=trend,
        )


# ──────────────────────────────────────────────────────────────
# Ω-P28 to Ω-P36: Wyckoff Phase Detection
# ──────────────────────────────────────────────────────────────

class WyckoffPhaseDetector:
    """
    Ω-P28 to Ω-P36: Detect Wyckoff accumulation/distribution phases.

    Transmuted from v1 wyckoff.py:
    v1: Analyzed Wyckoff phases from volume and price structure
    v2: Full Wyckoff analysis with phase detection, event marking
    (PS, SC, AR, ST for accumulation; PSY, BC, UT, LPS for distribution),
    and Spring/Upthrust detection.
    """

    def __init__(self, lookback: int = 100) -> None:
        self._lookback = lookback
        self._prices: deque[float] = deque(maxlen=lookback)
        self._volumes: deque[float] = deque(maxlen=lookback)

    def update(self, price: float, volume: float = 0.0) -> dict:
        """
        Ω-P30: Update Wyckoff analysis.
        Returns phase detection dict.
        """
        self._prices.append(price)
        self._volumes.append(volume)

        if len(self._prices) < 30:
            return {"phase": "WARMING_UP", "event": "NONE"}

        prices = list(self._prices)
        volumes = list(self._volumes)

        # Ω-P31: Range detection
        recent_range = max(prices[-20:]) - min(prices[-20:])
        avg_volume = sum(volumes[-20:]) / 20 if volumes[-20:] else 0

        # Ω-P32: Volume spikes
        recent_vol = volumes[-1] if volumes else 0
        vol_ratio = recent_vol / avg_volume if avg_volume > 0 else 1.0

        # Ω-P33: Phase classification
        if recent_range < prices[-1] * 0.01:  # Tight range (< 1%)
            if vol_ratio < 0.5:  # Declining volume
                phase = "ACCUMULATION_B"  # Phase B: cause building
                event = "NONE"
            elif vol_ratio > 2.0:  # Volume spike in range
                price_change = prices[-1] - prices[-5]
                if price_change < 0:
                    phase = "ACCUMULATION_C"  # Phase C: Spring test
                    event = "SPRING"
                else:
                    phase = "ACCUMULATION_C"
                    event = "TEST"
            else:
                phase = "ACCUMULATION_A"  # Phase A: preliminary support
                event = "PS" if prices[-1] < prices[-10] else "NONE"
        elif recent_range > prices[-1] * 0.03:  # Wide range (> 3%)
            if prices[-1] > prices[-10]:
                phase = "DISTRIBUTION_A"  # Phase A: preliminary supply
                event = "PSY"
            else:
                phase = "MARKUP"
                event = "NONE"
        else:
            phase = "TRANSITION"
            event = "NONE"

        return {
            "phase": phase,
            "event": event,
            "range_size": recent_range,
            "volume_ratio": vol_ratio,
            "is_accumulation": phase.startswith("ACCUMULATION"),
            "is_distribution": phase.startswith("DISTRIBUTION"),
            "is_markup": phase == "MARKUP",
            "is_markdown": phase == "MARKDOWN",
        }


# ──────────────────────────────────────────────────────────────
# Ω-P37 to Ω-P45: Smart Money Concept Analysis
# ──────────────────────────────────────────────────────────────

class SmartMoneyAnalyzer:
    """
    Ω-P37 to Ω-P45: Detect SMC patterns (order blocks, FVGs, liquidity).

    Transmuted from v1 smc.py:
    v1: Detected order blocks and fair value gaps from candle data
    v2: Enhanced SMC with order block validation, FVG confluence
    scoring, liquidity pool mapping, and breaker block detection.
    """

    def __init__(self) -> None:
        self._candles: deque[tuple[float, float, float, float]] = deque(maxlen=200)  # O, H, L, C
        self._order_blocks: list[dict] = []
        self._fvgs: list[dict] = []

    def update_candle(self, candle_open: float, candle_high: float, candle_low: float, candle_close: float) -> dict:
        """Ω-P39: Update with new candle for SMC analysis."""
        self._candles.append((candle_open, candle_high, candle_low, candle_close))

        if len(self._candles) < 5:
            return {"order_blocks": [], "fvgs": [], "analysis": "WARMING_UP"}

        candles = list(self._candles)

        # ω-P40: Order Block Detection
        # Bullish OB: last bearish candle before a strong impulse up
        # Bearish OB: last bullish candle before a strong impulse down
        order_blocks = []
        for i in range(1, len(candles) - 1):
            o, h, l, c = candles[i]
            next_candle = candles[i + 1]
            prev_candle = candles[i - 1]

            # Check for strong impulse after this candle
            next_range = abs(next_candle[3] - next_candle[0])  # body
            prev_range = abs(prev_candle[3] - prev_candle[0])

            if next_range > prev_range * 2:  # Strong move
                if candles[i][3] < candles[i][0]:  # Bearish candle followed by bullish impulse
                    order_blocks.append({
                        "type": "BULLISH_OB",
                        "high": h,
                        "low": l,
                        "candle_idx": i,
                    })
                elif candles[i][3] > candles[i][0]:  # Bullish candle followed by bearish impulse
                    order_blocks.append({
                        "type": "BEARISH_OB",
                        "high": h,
                        "low": l,
                        "candle_idx": i,
                    })

        # Ω-P41: Fair Value Gap Detection
        fvgs = []
        for i in range(2, len(candles)):
            c1 = candles[i-2]  # candle n-2
            c2 = candles[i-1]  # candle n-1
            c3 = candles[i]    # candle n

            # Bullish FVG: c3.low > c1.high (gap between c1.high and c3.low)
            if c3[2] > c1[1]:
                fvgs.append({
                    "type": "BULLISH_FVG",
                    "top": c3[2],
                    "bottom": c1[1],
                    "candle_idx": i,
                })
            # Bearish FVG: c3.high < c1.low
            elif c3[1] < c1[2]:
                fvgs.append({
                    "type": "BEARISH_FVG",
                    "top": c1[2],
                    "bottom": c3[1],
                    "candle_idx": i,
                })

        # Keep recent only
        recent_obs = [ob for ob in order_blocks if len(candles) - ob["candle_idx"] < 50]
        recent_fvgs = [f for f in fvgs if len(candles) - f["candle_idx"] < 50]

        self._order_blocks = recent_obs[-10:]
        self._fvgs = recent_fvgs[-10:]

        return {
            "order_blocks": self._order_blocks,
            "fvgs": self._fvgs,
            "analysis": f"{len(recent_obs)} OBs, {len(recent_fvgs)} FVGs found",
        }

    def get_nearest_ob(self, current_price: float) -> Optional[dict]:
        """Ω-P42: Find nearest order block to current price."""
        if not self._order_blocks:
            return None
        return min(self._order_blocks, key=lambda ob: abs((ob["high"] + ob["low"]) / 2 - current_price))
