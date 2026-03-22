"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          DUBAI MATRIX ASI — SWING POSITION DETECTOR AGENT                  ║
║   PhD-Level Multi-Timeframe Structural Analysis for Long Positions         ║
║                                                                              ║
║  Detects distribution tops and accumulation bottoms via:                    ║
║  1. Multi-TF swing fractal analysis (M5/M15/H1)                           ║
║  2. Wyckoff distribution/accumulation phase detection                       ║
║  3. Liquidity pool mapping and untested level targeting                     ║
║  4. Volume-weighted effort-vs-result divergence                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal
from config.omega_params import OMEGA
from utils.decorators import catch_and_log


class SwingPositionDetectorAgent(BaseAgent):
    """
    Omega-Class Swing Position Detector.

    Unlike scalp-focused agents that analyze M1 fractals, this agent
    operates on M5/M15/H1 timeframes to identify structural distribution
    and accumulation zones suitable for swing trades (100-500+ point targets).

    Architecture:
    ┌─────────────────────────────────────────────────────┐
    │ Layer 1: Multi-TF Fractal Detection (H1 > M15 > M5)│
    │ Layer 2: Equal Highs/Lows Clustering                │
    │ Layer 3: Volume Profile Divergence (Effort/Result)  │
    │ Layer 4: Liquidity Pool Mapping (Untested Levels)   │
    │ Layer 5: Structural Break Confirmation              │
    └─────────────────────────────────────────────────────┘
    """

    def __init__(self, weight: float = 5.0):
        super().__init__("SwingPositionDetector", weight)
        # Internal state for tracking swing levels across cycles
        self._swing_highs_h1 = []
        self._swing_lows_h1 = []
        self._last_distribution_price = 0.0
        self._last_accumulation_price = 0.0

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        if OMEGA.get("swing_mode_enabled", 1.0) < 0.5:
            return None

        # ═══ MULTI-TIMEFRAME DATA EXTRACTION ═══
        candles_m5 = snapshot.candles.get("M5")
        candles_m15 = snapshot.candles.get("M15")
        candles_h1 = snapshot.candles.get("H1")

        # Require at least M5 and M15 with sufficient depth
        if not candles_m5 or len(candles_m5.get("close", [])) < 30:
            return None
        if not candles_m15 or len(candles_m15.get("close", [])) < 30:
            return None

        price = snapshot.price
        signal = 0.0
        confidence = 0.0
        reasoning_parts = []
        metadata = {
            "is_swing_trade": False,
            "swing_type": "NONE",
            "target_liquidity_level": 0.0,
            "structure_timeframe": "M15",
        }

        # ═══ LAYER 1: MULTI-TF FRACTAL SWING DETECTION ═══
        m15_highs = np.array(candles_m15["high"], dtype=np.float64)
        m15_lows = np.array(candles_m15["low"], dtype=np.float64)
        m15_closes = np.array(candles_m15["close"], dtype=np.float64)
        m15_volumes = np.array(candles_m15.get("tick_volume", candles_m15.get("real_volume", [1]*len(m15_closes))), dtype=np.float64)

        m5_closes = np.array(candles_m5["close"], dtype=np.float64)
        m5_highs = np.array(candles_m5["high"], dtype=np.float64)
        m5_lows = np.array(candles_m5["low"], dtype=np.float64)

        # Detect swing highs/lows on M15 (5-bar fractal)
        swing_highs_m15 = self._detect_fractals(m15_highs, fractal_bars=3, mode="high")
        swing_lows_m15 = self._detect_fractals(m15_lows, fractal_bars=3, mode="low")

        # H1 fractal detection (deeper structure)
        h1_swing_highs = []
        h1_swing_lows = []
        h1_atr = 0.0
        if candles_h1 and len(candles_h1.get("close", [])) >= 20:
            h1_highs = np.array(candles_h1["high"], dtype=np.float64)
            h1_lows = np.array(candles_h1["low"], dtype=np.float64)
            h1_closes = np.array(candles_h1["close"], dtype=np.float64)
            h1_swing_highs = self._detect_fractals(h1_highs, fractal_bars=2, mode="high")
            h1_swing_lows = self._detect_fractals(h1_lows, fractal_bars=2, mode="low")
            # H1 ATR (14-period true range approximation)
            h1_ranges = np.abs(np.diff(h1_closes[-15:]))
            h1_atr = float(np.mean(h1_ranges)) if len(h1_ranges) > 0 else 0.0
            metadata["structure_timeframe"] = "H1"

        # ═══ LAYER 2: EQUAL HIGHS/LOWS CLUSTERING (Distribution/Accumulation) ═══
        dist_score = 0.0
        acc_score = 0.0

        if len(swing_highs_m15) >= 2:
            dist_score, dist_level = self._detect_equal_levels(
                swing_highs_m15, price, tolerance_pct=0.08, mode="resistance"
            )
            if dist_score > 0:
                reasoning_parts.append(
                    f"DISTRIBUTION_ZONE({dist_score:.0f} equal highs near {dist_level:.0f})"
                )

        if len(swing_lows_m15) >= 2:
            acc_score, acc_level = self._detect_equal_levels(
                swing_lows_m15, price, tolerance_pct=0.08, mode="support"
            )
            if acc_score > 0:
                reasoning_parts.append(
                    f"ACCUMULATION_ZONE({acc_score:.0f} equal lows near {acc_level:.0f})"
                )

        # ═══ LAYER 3: VOLUME PROFILE DIVERGENCE (Effort vs Result) ═══
        vol_divergence = self._volume_effort_result(m15_closes, m15_volumes)
        if abs(vol_divergence) > 0.3:
            reasoning_parts.append(f"VOL_DIVERGENCE({vol_divergence:+.2f})")

        # ═══ LAYER 4: LIQUIDITY POOL MAPPING ═══
        # Find untested swing lows (below price) as SELL targets
        untested_lows = self._find_untested_levels(
            swing_lows_m15, m5_lows[-20:], price, mode="below"
        )
        # Find untested swing highs (above price) as BUY targets
        untested_highs = self._find_untested_levels(
            swing_highs_m15, m5_highs[-20:], price, mode="above"
        )

        # Include H1 untested levels (higher priority — deeper liquidity pools)
        if h1_swing_lows:
            h1_untested_lows = self._find_untested_levels(
                h1_swing_lows, m5_lows[-30:], price, mode="below"
            )
            untested_lows = h1_untested_lows + untested_lows  # H1 first

        if h1_swing_highs:
            h1_untested_highs = self._find_untested_levels(
                h1_swing_highs, m5_highs[-30:], price, mode="above"
            )
            untested_highs = h1_untested_highs + untested_highs

        # ═══ LAYER 5: STRUCTURAL BREAK CONFIRMATION ═══
        # Check if M5 is breaking recent M15 swing lows (bearish) or highs (bullish)
        recent_m15_low = float(np.min(m15_lows[-5:])) if len(m15_lows) >= 5 else 0.0
        recent_m15_high = float(np.max(m15_highs[-5:])) if len(m15_highs) >= 5 else 0.0

        is_breaking_lows = price < recent_m15_low and len(m5_closes) >= 3 and all(
            m5_closes[-i] < m5_closes[-i-1] for i in range(1, min(4, len(m5_closes)))
        )
        is_breaking_highs = price > recent_m15_high and len(m5_closes) >= 3 and all(
            m5_closes[-i] > m5_closes[-i-1] for i in range(1, min(4, len(m5_closes)))
        )

        # ═══ COMPOSITE SIGNAL SYNTHESIS ═══
        # Distribution (SELL signal): price at/near equal highs + vol divergence + structure
        if dist_score >= 2 and price > 0:
            # Price must be near the distribution zone (within 0.15% of the equal highs level)
            dist_proximity = abs(price - dist_level) / price * 100 if dist_level > 0 else 999
            if dist_proximity < 0.20:
                signal -= 0.4 * min(dist_score / 3.0, 1.0)  # -0.13 to -0.40
                confidence += 0.3
                reasoning_parts.append("PRICE_AT_DISTRIBUTION")

                if vol_divergence < -0.3:  # High volume, low result at top → absorption
                    signal -= 0.25
                    confidence += 0.15
                    reasoning_parts.append("CLIMAX_VOLUME_AT_TOP")

                if is_breaking_lows:
                    signal -= 0.2
                    confidence += 0.1
                    reasoning_parts.append("STRUCTURAL_BREAK_DOWN")

                # Set swing trade target
                if untested_lows:
                    target = untested_lows[0]  # Nearest untested low
                    metadata["target_liquidity_level"] = target
                    metadata["is_swing_trade"] = True
                    metadata["swing_type"] = "DISTRIBUTION"
                    reasoning_parts.append(f"TARGET_LIQUIDITY={target:.0f}")

        # Accumulation (BUY signal): price at/near equal lows + vol divergence + structure
        if acc_score >= 2 and price > 0:
            acc_proximity = abs(price - acc_level) / price * 100 if acc_level > 0 else 999
            if acc_proximity < 0.20:
                signal += 0.4 * min(acc_score / 3.0, 1.0)
                confidence += 0.3
                reasoning_parts.append("PRICE_AT_ACCUMULATION")

                if vol_divergence > 0.3:  # High volume, low result at bottom → accumulation
                    signal += 0.25
                    confidence += 0.15
                    reasoning_parts.append("CLIMAX_VOLUME_AT_BOTTOM")

                if is_breaking_highs:
                    signal += 0.2
                    confidence += 0.1
                    reasoning_parts.append("STRUCTURAL_BREAK_UP")

                if untested_highs:
                    target = untested_highs[0]
                    metadata["target_liquidity_level"] = target
                    metadata["is_swing_trade"] = True
                    metadata["swing_type"] = "ACCUMULATION"
                    reasoning_parts.append(f"TARGET_LIQUIDITY={target:.0f}")

        # ═══ LIQUIDITY SWEEP REVERSAL (Highest confidence pattern) ═══
        # Price sweeps below swing low then closes back above → Spring
        if len(swing_lows_m15) >= 1 and len(m5_closes) >= 3:
            nearest_low = float(swing_lows_m15[-1])
            swept_and_reclaimed = (
                float(m5_lows[-2]) < nearest_low  # Wick below
                and float(m5_closes[-1]) > nearest_low  # Close back above
                and float(m5_closes[-1]) > float(m5_closes[-2])  # Bullish close
            )
            if swept_and_reclaimed:
                signal += 0.5
                confidence += 0.3
                metadata["is_swing_trade"] = True
                metadata["swing_type"] = "SPRING"
                reasoning_parts.append(f"LIQUIDITY_SPRING(swept={nearest_low:.0f})")

        # Inverse: sweep above swing high then close below → Upthrust After Distribution
        if len(swing_highs_m15) >= 1 and len(m5_closes) >= 3:
            nearest_high = float(swing_highs_m15[-1])
            swept_and_rejected = (
                float(m5_highs[-2]) > nearest_high  # Wick above
                and float(m5_closes[-1]) < nearest_high  # Close back below
                and float(m5_closes[-1]) < float(m5_closes[-2])  # Bearish close
            )
            if swept_and_rejected:
                signal -= 0.5
                confidence += 0.3
                metadata["is_swing_trade"] = True
                metadata["swing_type"] = "UTAD"
                reasoning_parts.append(f"LIQUIDITY_UTAD(swept={nearest_high:.0f})")

        # ═══ FINAL SIGNAL NORMALIZATION ═══
        signal = float(np.clip(signal, -1.0, 1.0))
        confidence = float(np.clip(confidence, 0.0, 1.0))

        if abs(signal) < 0.1:
            return None  # No significant swing pattern detected

        reasoning = f"SWING_POSITION: {' | '.join(reasoning_parts)}"

        return AgentSignal(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            weight=self.weight,
            metadata=metadata,
        )

    # ═══════════════════════════════════════════════════════════
    #  INTERNAL ENGINES
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def _detect_fractals(data: np.ndarray, fractal_bars: int = 3, mode: str = "high"):
        """
        Detect fractal swing points.
        A fractal high: data[i] > all neighbors within fractal_bars.
        Returns list of price levels.
        """
        levels = []
        n = len(data)
        for i in range(fractal_bars, n - fractal_bars):
            if mode == "high":
                is_fractal = all(data[i] > data[i - j] for j in range(1, fractal_bars + 1)) and \
                             all(data[i] > data[i + j] for j in range(1, fractal_bars + 1))
            else:
                is_fractal = all(data[i] < data[i - j] for j in range(1, fractal_bars + 1)) and \
                             all(data[i] < data[i + j] for j in range(1, fractal_bars + 1))
            if is_fractal:
                levels.append(float(data[i]))
        return levels

    @staticmethod
    def _detect_equal_levels(levels, price, tolerance_pct=0.08, mode="resistance"):
        """
        Detect clusters of equal price levels (equal highs/lows).
        Returns (count, average_level) of the largest cluster near price.
        """
        if len(levels) < 2:
            return 0, 0.0

        best_count = 0
        best_level = 0.0

        for i, lvl in enumerate(levels):
            # Count how many other levels are within tolerance
            cluster = [l for l in levels if abs(l - lvl) / max(lvl, 1) * 100 < tolerance_pct]
            if len(cluster) > best_count:
                best_count = len(cluster)
                best_level = float(np.mean(cluster))

        # Only relevant if price is near the cluster
        if best_level > 0:
            dist_pct = abs(price - best_level) / price * 100
            if dist_pct > 0.5:  # Too far from current price
                return 0, 0.0

        return best_count, best_level

    @staticmethod
    def _volume_effort_result(closes: np.ndarray, volumes: np.ndarray, lookback: int = 10):
        """
        Wyckoff Effort vs Result analysis.
        Returns divergence score:
          > 0 = bullish divergence (high volume at support, price not falling)
          < 0 = bearish divergence (high volume at resistance, price not rising)
        """
        if len(closes) < lookback + 1 or len(volumes) < lookback + 1:
            return 0.0

        recent_closes = closes[-lookback:]
        recent_volumes = volumes[-lookback:]

        # Price change direction
        price_change = recent_closes[-1] - recent_closes[0]
        avg_volume = float(np.mean(volumes[:-lookback])) if len(volumes) > lookback else 1.0
        recent_avg_vol = float(np.mean(recent_volumes))

        volume_ratio = recent_avg_vol / max(avg_volume, 1.0)
        price_range = float(np.max(recent_closes) - np.min(recent_closes))

        # High effort (volume) + low result (small price range) = divergence
        historical_range = float(np.std(np.diff(closes[-30:]))) * lookback if len(closes) >= 30 else price_range
        result_ratio = price_range / max(historical_range, 1.0)

        if volume_ratio > 1.5 and result_ratio < 0.6:
            # Effort > Result divergence
            if price_change > 0:
                return -0.5  # Rising with exhaustion → bearish
            else:
                return 0.5   # Falling with absorption → bullish
        return 0.0

    @staticmethod
    def _find_untested_levels(fractal_levels, recent_data, price, mode="below"):
        """
        Find fractal levels that have NOT been retested by recent price action.
        These are liquidity pools — untested swing lows/highs where stops cluster.
        """
        untested = []
        recent_min = float(np.min(recent_data)) if len(recent_data) > 0 else price
        recent_max = float(np.max(recent_data)) if len(recent_data) > 0 else price

        for level in fractal_levels:
            if mode == "below" and level < price:
                # Untested = price hasn't gone back down to this level recently
                if level < recent_min:
                    untested.append(float(level))
            elif mode == "above" and level > price:
                if level > recent_max:
                    untested.append(float(level))

        # Sort by proximity to current price
        untested.sort(key=lambda x: abs(x - price))
        return untested
