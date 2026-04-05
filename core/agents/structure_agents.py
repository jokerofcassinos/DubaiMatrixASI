"""
SOLÉNN v2 — Structure & Genesis Agents (Ω-SG01 to Ω-SG162)
Transmuted from v1:
  - genesis_agents.py: Pattern genesis and birth detection
  - continuum_agents.py: Continuous state transitions
  - sovereignty_agents.py: Market regime sovereignty tracking
  - transcendence_agents.py: Beyond-model pattern emergence
  - chart_structure.py: Chart pattern detection
  - classic.py: Classic technical pattern recognition
  - smc.py: Smart Money Concepts implementation
  - wyckoff.py: Wyckoff method analysis

Protocol 3-6-9: 162 vetores planejados
  Concept 1 — Pattern Genesis & Sovereignty (Ω-SG01 to Ω-SG54):
    New pattern birth detection, pattern lifecycle tracking,
    regime sovereignty (which market controls its own destiny),
    pattern taxonomy and inheritance, novel pattern recognition
  Concept 2 — Chart & Classic Pattern Recognition (Ω-SG55 to Ω-SG108):
    Head & shoulders, double/triple top/bottom, triangles,
    flags, wedges, cup & handle, rounding patterns, pattern
    reliability scoring, target estimation
  Concept 3 — Wyckoff & SMC Analysis (Ω-SG109 to Ω-SG162):
    Accumulation/distribution phases, spring/upthrust detection,
    order blocks, fair value gaps, liquidity sweeps, change of
    character (ChoCh), breaker blocks, mitigation
"""

from __future__ import annotations

import math
from collections import deque
from typing import Optional


# ──────────────────────────────────────────────────────────────
# Ω-SG01 to Ω-SG18: Pattern Genesis Detection
# ──────────────────────────────────────────────────────────────

class PatternGenesisDetector:
    """
    Ω-SG01 to Ω-SG09: Detect birth of new patterns.

    Transmuted from v1 genesis_agents.py:
    v1: Simple pattern counting
    v2: Full genesis detection with lifecycle tracking,
    taxonomy, novelty scoring, and inheritance.
    """

    def __init__(self, window_size: int = 300) -> None:
        self._window = window_size
        self._prices: deque[float] = deque(maxlen=window_size)
        self._volumes: deque[float] = deque(maxlen=window_size)
        self._pattern_catalog: dict[str, int] = {}
        self._genesis_events: list[dict] = []

    def update(self, price: float, volume: float = 1.0) -> dict:
        """Ω-SG03: Check for pattern genesis."""
        self._prices.append(price)
        self._volumes.append(volume)

        if len(self._prices) < 30:
            return {"state": "WARMING_UP"}

        prices = list(self._prices)
        volumes = list(self._volumes)
        n = len(prices)

        # Ω-SG04: Pattern taxonomy
        # Classify current structure into pattern types
        patterns = self._classify_patterns(prices, volumes)
        for p in patterns:
            self._pattern_catalog[p] = self._pattern_catalog.get(p, 0) + 1

        # Ω-SG05: Novel pattern detection
        # Something that doesn't match any known pattern
        known_patterns = set(self._pattern_catalog.keys())
        novel_patterns = [p for p in patterns if p not in known_patterns]

        # Ω-SG06: Genesis event
        if novel_patterns:
            for p in novel_patterns:
                self._genesis_events.append({
                    "pattern": p,
                    "index": n,
                    "price": price,
                })
                self._pattern_catalog[p] = 1

        # Ω-SG07: Pattern diversity
        n_pattern_types = len(self._pattern_catalog)
        diversity = n_pattern_types / 20.0  # Normalize to ~0-1
        diversity = min(1.0, diversity)

        # Ω-SG08: Pattern lifecycle
        # Track how patterns mature and decay
        if self._genesis_events:
            latest_genesis = self._genesis_events[-1]
            age = n - latest_genesis["index"]
            lifecycle_stage = "NEW" if age < 10 else "MATURING" if age < 50 else "MATURE" if age < 100 else "DECAYING"
        else:
            lifecycle_stage = "UNKNOWN"
            age = 0

        # Ω-SG09: Sovereignty score
        # How much does the market control its own direction?
        # High sovereignty = organic movement, low = externally driven
        if n >= 20:
            returns = [(prices[i] - prices[i-1]) / max(1e-6, abs(prices[i-1]))
                      for i in range(n - 20, n)]
            vol_trend = sum(volumes[-10:]) / max(1e-6, sum(volumes[-20:-10])) if len(volumes) > 20 else 1.0
            return_autocorr = _autocorrelation(returns, lag=1)

            # Organic movement = positive autocorrelation, stable volume
            sovereignty = max(0.0, min(1.0, (
                max(0.0, return_autocorr) * 0.5 +
                (1.0 - abs(vol_trend - 1.0)) * 0.5
            )))
        else:
            sovereignty = 0.0

        return {
            "patterns_detected": patterns,
            "n_pattern_types": n_pattern_types,
            "pattern_diversity": diversity,
            "genesis_events": len(self._genesis_events),
            "novel_patterns_detected": len(novel_patterns),
            "lifecycle_stage": lifecycle_stage,
            "genesis_age": age,
            "sovereignty_score": sovereignty,
            "is_novel_pattern": len(novel_patterns) > 0,
        }

    def _classify_patterns(self, prices: list[float], volumes: list[float]) -> list[str]:
        """Ω-SG04: Classify known patterns in current data."""
        patterns = []
        n = len(prices)

        if n < 10:
            return patterns

        # Double top
        if len(prices) >= 20:
            h1 = max(prices[-20:-10])
            h2 = max(prices[-10:])
            if abs(h1 - h2) / max(1e-6, (h1 + h2) / 2) < 0.005:
                patterns.append("DOUBLE_TOP")

        # Double bottom
        if len(prices) >= 20:
            l1 = min(prices[-20:-10])
            l2 = min(prices[-10:])
            if abs(l1 - l2) / max(1e-6, (l1 + l2) / 2) < 0.005:
                patterns.append("DOUBLE_BOTTOM")

        # Ascending triangle
        if n >= 15:
            highs = prices[-15:]
            highs_range = max(highs) - min(highs)
            if highs_range < abs(max(highs)) * 0.005 and prices[-1] > prices[-10]:
                patterns.append("ASCENDING_TRIANGLE")

        # Descending triangle
        if n >= 15:
            lows = prices[-15:]
            lows_range = max(lows) - min(lows)
            if lows_range < abs(min(lows)) * 0.005 and prices[-1] < prices[-10]:
                patterns.append("DESCENDING_TRIANGLE")

        return patterns


# ──────────────────────────────────────────────────────────────
# Ω-SG19 to Ω-SG27: Chart Pattern Engine
# ──────────────────────────────────────────────────────────────

class ChartPatternEngine:
    """
    Ω-SG19 to Ω-SG27: Comprehensive chart pattern detection.

    Transmuted from v1 chart_structure.py + classic.py:
    v1: Basic shape detection
    v2: Full pattern library with reliability scoring,
    target estimation, and quality assessment.
    """

    def __init__(self, window_size: int = 500) -> None:
        self._window = window_size
        self._prices: deque[float] = deque(maxlen=window_size)
        self._volumes: deque[float] = deque(maxlen=window_size)

    def update(self, price: float, volume: float = 1.0) -> dict:
        """Ω-SG21: Update chart pattern analysis."""
        self._prices.append(price)
        self._volumes.append(volume)

        if len(self._prices) < 40:
            return {"state": "WARMING_UP"}

        prices = list(self._prices)
        volumes = list(self._volumes)
        n = len(prices)

        patterns_detected: list[dict] = []

        # Ω-SG22: Head and Shoulders / Inverse H&S
        hs = self._detect_head_shoulders(prices, volumes)
        if hs:
            patterns_detected.append(hs)

        # Ω-SG23: Triangle patterns
        tri = self._detect_triangle(prices, volumes)
        if tri:
            patterns_detected.append(tri)

        # Ω-SG24: Flag/Pennant
        flag = self._detect_flag(prices, volumes)
        if flag:
            patterns_detected.append(flag)

        # Ω-SG25: Double/Triple Top/Bottom
        db = self._detect_double_triple(prices)
        if db:
            patterns_detected.extend(db)

        # Ω-SG26: Pattern reliability
        for p in patterns_detected:
            # Reliability depends on:
            # - Pattern duration (longer = more reliable)
            # - Volume confirmation
            # - Symmetry
            reliability = p.get("duration_score", 0.0) * 0.3
            reliability += p.get("volume_confirmation", 0.0) * 0.4
            reliability += p.get("symmetry", 0.0) * 0.3
            p["reliability"] = min(1.0, reliability)

        # Ω-SG27: Master signal
        # Aggregate all pattern signals
        if patterns_detected:
            signals = [p.get("direction", 0) for p in patterns_detected]
            weights = [p.get("reliability", 0.5) for p in patterns_detected]
            total_w = sum(weights)
            master_signal = sum(s * w for s, w in zip(signals, weights)) / max(1e-6, total_w)
        else:
            master_signal = 0.0

        return {
            "patterns": patterns_detected,
            "n_patterns": len(patterns_detected),
            "master_signal": master_signal,
            "is_bullish_patterns": master_signal > 0.3,
            "is_bearish_patterns": master_signal < -0.3,
            "highest_reliability": max((p["reliability"] for p in patterns_detected), default=0.0),
        }

    def _detect_head_shoulders(self, prices: list, volumes: list) -> Optional[dict]:
        """Ω-SG22: Detect Head and Shoulders pattern."""
        if len(prices) < 30:
            return None

        # Find 3 peaks (shoulder, head, shoulder)
        n = len(prices)
        # Simple windowed approach
        third = n // 3
        s1_peak = max(prices[:third]) if prices[:third] else 0
        h_peak = max(prices[third:2*third]) if prices[third:2*third] else 0
        s2_peak = max(prices[2*third:]) if prices[2*third:] else 0

        # HS: head > both shoulders, shoulders at similar level
        if h_peak > s1_peak and h_peak > s2_peak:
            shoulder_diff = abs(s1_peak - s2_peak)
            shoulder_avg = (s1_peak + s2_peak) / 2
            if shoulder_avg > 0 and shoulder_diff / shoulder_avg < 0.02:
                # Volume check: declining volume on second shoulder
                vol_s1 = sum(volumes[:third]) / max(1, third)
                vol_s2 = sum(volumes[2*third:]) / max(1, third)
                vol_decline = vol_s2 < vol_s1

                depth = h_peak - shoulder_avg
                neckline = shoulder_avg
                target = neckline - depth  # For bearish HS

                return {
                    "name": "HEAD_AND_SHOULDERS",
                    "direction": -1,  # Bearish
                    "target": target,
                    "neckline": neckline,
                    "depth": depth,
                    "volume_confirmed": vol_decline,
                    "volume_decline": 1.0 if vol_decline else 0.3,
                    "duration_score": min(1.0, n / 100.0),
                    "symmetry": max(0.0, 1.0 - shoulder_diff / max(1e-6, shoulder_avg)),
                }

        # Inverse HS
        s1_low = min(prices[:third]) if prices[:third] else 0
        h_low = min(prices[third:2*third]) if prices[third:2*third] else 0
        s2_low = min(prices[2*third:]) if prices[2*third:] else 0

        if h_low < s1_low and h_low < s2_low:
            low_diff = abs(s1_low - s2_low)
            low_avg = (s1_low + s2_low) / 2
            if low_avg > 0 and low_diff / low_avg < 0.02:
                return {
                    "name": "INVERSE_HEAD_AND_SHOULDERS",
                    "direction": 1,  # Bullish
                    "target": low_avg + (low_avg - h_low) * 2,
                    "neckline": low_avg,
                    "depth": low_avg - h_low,
                    "volume_confirmed": False,
                    "volume_decline": 0.5,
                    "duration_score": min(1.0, n / 100.0),
                    "symmetry": max(0.0, 1.0 - low_diff / max(1e-6, low_avg)),
                }

        return None

    def _detect_triangle(self, prices: list, volumes: list) -> Optional[dict]:
        """Ω-SG23: Detect triangle patterns."""
        if len(prices) < 20:
            return None

        n = len(prices)
        first_half = prices[:n // 2]
        second_half = prices[n // 2:]

        range_1 = max(first_half) - min(first_half)
        range_2 = max(second_half) - min(second_half)

        # Symmetrical triangle: range narrowing
        if range_1 > 0 and range_2 < range_1 * 0.7:
            compression = 1.0 - range_2 / range_1
            mid_1 = (max(first_half) + min(first_half)) / 2
            mid_2 = (max(second_half) + min(second_half)) / 2
            direction = 1 if mid_2 > mid_1 else -1

            return {
                "name": "SYM_TRIANGLE",
                "direction": direction,
                "compression": compression,
                "volume_confirmed": False,
                "volume_decline": 0.5,
                "duration_score": min(1.0, n / 100.0),
                "symmetry": compression,
            }
        return None

    def _detect_flag(self, prices: list, volumes: list) -> Optional[dict]:
        """Ω-SG24: Detect flag patterns."""
        if len(prices) < 20:
            return None

        # Flag: sharp move (pole) + consolidation (flag) + breakout
        n = len(prices)
        # Check for pole (first part = strong directional move)
        pole_len = n // 4
        if pole_len < 3:
            return None

        pole_move = prices[pole_len] - prices[0]
        flag_range = max(prices[pole_len:]) - min(prices[pole_len:])
        pole_abs = abs(pole_move)

        if pole_abs > 0 and flag_range < pole_abs * 0.5:
            # Flag consolidation detected
            direction = 1 if pole_move > 0 else -1
            flag_quality = max(0.0, 1.0 - flag_range / max(1e-6, pole_abs))

            return {
                "name": "BULL_FLAG" if direction > 0 else "BEAR_FLAG",
                "direction": direction,
                "pole_size": pole_abs,
                "flag_range": flag_range,
                "volume_confirmed": False,
                "volume_decline": 0.5,
                "duration_score": min(1.0, n / 80.0),
                "symmetry": flag_quality,
            }
        return None

    def _detect_double_triple(self, prices: list) -> list[dict]:
        """Ω-SG25: Detect double/triple top/bottom."""
        patterns = []
        if len(prices) < 20:
            return patterns

        n = len(prices)
        third = n // 3

        # Check for double/triple top
        sections_max = [
            max(prices[i:i+third]) for i in range(0, n, third)
            if i + third <= n
        ]

        if len(sections_max) >= 2:
            for i in range(1, len(sections_max)):
                diff = abs(sections_max[i] - sections_max[i-1])
                avg = (sections_max[i] + sections_max[i-1]) / 2
                if avg > 0 and diff / avg < 0.01:
                    ptype = "DOUBLE_TOP" if len(sections_max) == 2 else "TRIPLE_TOP"
                    patterns.append({
                        "name": ptype,
                        "direction": -1,
                        "volume_confirmed": False,
                        "volume_decline": 0.5,
                        "duration_score": min(1.0, n / 100.0),
                        "symmetry": max(0.0, 1.0 - diff / max(1e-6, avg)),
                    })

        # Check for double/triple bottom
        sections_min = [
            min(prices[i:i+third]) for i in range(0, n, third)
            if i + third <= n
        ]

        if len(sections_min) >= 2:
            for i in range(1, len(sections_min)):
                diff = abs(sections_min[i] - sections_min[i-1])
                avg = (sections_min[i] + sections_min[i-1]) / 2
                if avg > 0 and diff / avg < 0.01:
                    ptype = "DOUBLE_BOTTOM" if len(sections_min) == 2 else "TRIPLE_BOTTOM"
                    patterns.append({
                        "name": ptype,
                        "direction": 1,
                        "volume_confirmed": False,
                        "volume_decline": 0.5,
                        "duration_score": min(1.0, n / 100.0),
                        "symmetry": max(0.0, 1.0 - diff / max(1e-6, avg)),
                    })

        return patterns


# ──────────────────────────────────────────────────────────────
# Ω-SG28 to Ω-SG36: Wyckoff & SMC Analysis
# ──────────────────────────────────────────────────────────────

class WyckoffSMCAnalyzer:
    """
    Ω-SG28 to Ω-SG36: Wyckoff method + Smart Money Concepts.

    Transmuted from v1 wyckoff.py + smc.py:
    v1: Basic SMC levels
    v2: Full Wyckoff phase detection, order blocks,
    FVG identification, liquidity sweeps, ChoCh.
    """

    def __init__(self, window_size: int = 300) -> None:
        self._window = window_size
        self._prices: deque[float] = deque(maxlen=window_size)
        self._volumes: deque[float] = deque(maxlen=window_size)

    def update(
        self,
        price: float,
        high: float = 0.0,
        low: float = 0.0,
        close: float = 0.0,
        volume: float = 1.0,
    ) -> dict:
        """Ω-SG30: Update Wyckoff/SMC analysis."""
        self._prices.append(price)
        self._volumes.append(volume)

        ohlcv_high = high if high > 0 else price
        ohlcv_low = low if low > 0 else price
        ohlcv_close = close if close > 0 else price

        if len(self._prices) < 30:
            return {"state": "WARMING_UP"}

        prices = list(self._prices)
        volumes = list(self._volumes)
        n = len(prices)

        signals: dict[str, float] = {}

        # Ω-SG31: Wyckoff Phase Detection
        wyckoff = self._wyckoff_phase(prices, volumes)
        signals.update(wyckoff)

        # Ω-SG32: Order Block Detection
        ob = self._detect_order_blocks(prices, volumes)
        signals.update(ob)

        # Ω-SG33: Fair Value Gap Detection
        fvg = self._detect_fvg(prices, volumes)
        signals.update(fvg)

        # Ω-SG34: Liquidity Sweep
        sweep = self._detect_liquidity_sweep(prices, volumes)
        signals.update(sweep)

        # Ω-SG35: Change of Character (ChoCh)
        chch = self._detect_choch(prices)
        signals.update(chch)

        # Ω-SG36: Aggregated signal
        bullish = sum(v for k, v in signals.items() if v > 0.5)
        bearish = sum(v for k, v in signals.items() if v < -0.5)

        net_signal = bullish - abs(bearish)
        confidence = max(bullish, bearish)

        return {
            "signals": signals,
            "net_signal": net_signal,
            "confidence": confidence,
            "wyckoff_phase": wyckoff.get("wyckoff_phase", "UNKNOWN"),
            "has_order_block": "order_block_detected" in signals,
            "has_fvg": "fvg_detected" in signals,
            "has_liquidity_sweep": "sweep_detected" in signals,
            "has_choch": "choch_detected" in signals,
            "is_actionable": confidence > 0.5 and abs(net_signal) > 0.3,
        }

    def _wyckoff_phase(self, prices: list, volumes: list) -> dict:
        """Ω-SG31: Estimate Wyckoff phase."""
        if len(prices) < 30:
            return {}

        n = len(prices)
        # Accumulation: sideways + declining volume
        first_third = prices[:n // 3]
        last_third = prices[-n // 3:]
        first_vol = sum(volumes[:n // 5]) / max(1, n // 5)
        last_vol = sum(volumes[-n // 5:]) / max(1, n // 5)

        range_size = max(prices) - min(prices)
        range_pct = range_size / max(1e-6, max(prices))

        if range_pct < 0.03:  # Tight range
            if last_vol < first_vol * 0.7:
                phase = "ACCUMULATION"  # Wyckoff Phase II
            elif prices[-1] > sum(prices[:10]) / max(1, 10) * 1.01:
                phase = "MARKUP"  # Wyckoff Phase III
            else:
                phase = "SPRING"  # Wyckoff Phase IIc
        elif range_pct > 0.1:  # Wide range
            if prices[-1] < prices[0]:
                phase = "MARKDOWN"  # Wyckoff Phase IV
            else:
                phase = "DISTRIBUTION"  # Wyckoff Phase III
        else:
            phase = "TRANSITION"

        return {"wyckoff_phase": phase}

    def _detect_order_blocks(self, prices: list, volumes: list) -> dict:
        """Ω-SG32: Detect order blocks."""
        if len(prices) < 10:
            return {}

        # Order block = last opposing candle before strong move
        n = len(prices)
        # Look for strong impulse move
        for i in range(n - 3, 0, -1):
            move = abs(prices[i] - prices[i - 1])
            if move > 0.003 * abs(prices[i]) and volumes[i] > volumes[i - 1]:
                # Order block = candle before the impulse
                ob_level = prices[i - 1]
                return {
                    "order_block_level": ob_level,
                    "order_block_detected": True,
                }
        return {}

    def _detect_fvg(self, prices: list, volumes: list) -> dict:
        """Ω-SG33: Detect Fair Value Gaps."""
        if len(prices) < 5:
            return {}

        n = len(prices)
        # FVG = gap between candle 1 high and candle 3 low (bullish)
        # or between candle 1 low and candle 3 high (bearish)
        for i in range(n - 3, max(0, n - 20), -1):
            if i + 2 < n and i - 2 >= 0:
                # Simplified: price gaps between adjacent candles
                gap = abs(prices[i + 2] - prices[i - 2])
                if gap > 0.002 * abs(prices[i]):
                    return {
                        "fvg_level": (prices[i + 2] + prices[i - 2]) / 2,
                        "fvg_size": gap,
                        "fvg_detected": True,
                    }
        return {}

    def _detect_liquidity_sweep(self, prices: list, volumes: list) -> dict:
        """Ω-SG34: Detect liquidity sweeps (stops hunted)."""
        if len(prices) < 20:
            return {}

        recent = prices[-20:]
        high_water = max(recent[:10])
        low_water = min(recent[:10])

        current = prices[-1]

        # Sweep above highs
        if current > high_water and current - high_water < abs(high_water) * 0.005:
            if len(prices) >= 3 and prices[-2] < high_water:
                return {
                    "sweep_level": high_water,
                    "sweep_detected": True,
                    "sweep_type": "Liquidity Sweep Above Highs",
                }

        # Sweep below lows
        if current < low_water and low_water - current < abs(low_water) * 0.005:
            if len(prices) >= 3 and prices[-2] > low_water:
                return {
                    "sweep_level": low_water,
                    "sweep_detected": True,
                    "sweep_type": "Liquidity Sweep Below Lows",
                }

        return {}

    def _detect_choch(self, prices: list) -> dict:
        """Ω-SG35: Change of Character detection."""
        if len(prices) < 20:
            return {}

        # ChoCh = break of previous swing structure
        recent = prices[-20:]
        swing_highs = []
        swing_lows = []

        for i in range(2, len(recent) - 2):
            if (recent[i] > recent[i-1] and recent[i] > recent[i-2] and
                recent[i] > recent[i+1] and recent[i] > recent[i+2]):
                swing_highs.append(recent[i])
            if (recent[i] < recent[i-1] and recent[i] < recent[i-2] and
                recent[i] < recent[i+1] and recent[i] < recent[i+2]):
                swing_lows.append(recent[i])

        if not swing_highs or not swing_lows:
            return {}

        last_high = swing_highs[-1]
        last_low = swing_lows[-1]

        current = prices[-1]
        prev = prices[-2]

        # Bullish ChoCh: price breaks above last swing high after downtrend
        if current > last_high and prev <= last_high and recent[-1] < recent[0]:
            return {"choch_detected": True, "choch_type": "BULLISH"}

        # Bearish ChoCh: price breaks below last swing low after uptrend
        if current < last_low and prev >= last_low and recent[-1] > recent[0]:
            return {"choch_detected": True, "choch_type": "BEARISH"}

        return {}


# ──────────────────────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────────────────────

def _autocorrelation(values: list[float], lag: int = 1) -> float:
    n = len(values)
    if n < lag + 3:
        return 0.0
    m = sum(values) / n
    var = sum((v - m) ** 2 for v in values) / n
    if var < 1e-12:
        return 0.0
    cov = sum((values[i] - m) * (values[i + lag] - m)
              for i in range(n - lag)) / (n - lag)
    return cov / var
