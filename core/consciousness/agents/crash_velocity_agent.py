"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          DUBAI MATRIX ASI — CRASH VELOCITY DETECTOR AGENT                  ║
║   PhD-Level Multi-Scale Drop/Crash Analysis Engine                         ║
║                                                                              ║
║  Detects market drops and cascades that the standard agent swarm misses:    ║
║  1. Multi-scale Rate-of-Change (ROC) cascade detection                     ║
║  2. Sequential candle body expansion tracking                               ║
║  3. Bollinger Band squeeze-to-expansion detection                          ║
║  4. Structural break cascade (consecutive swing low breaks)                 ║
║  5. Momentum acceleration divergence                                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal
from config.omega_params import OMEGA
from utils.decorators import catch_and_log


class CrashVelocityDetectorAgent(BaseAgent):
    """
    Omega-Class Crash/Drop Velocity Detector.

    The standard agent swarm votes on bull/bear direction but fails to
    detect STRUCTURAL CASCADES — when price breaks multiple swing lows
    in sequence with accelerating momentum. This agent specifically
    identifies drops-in-progress and imminent cascades.

    When crash_severity > threshold, the agent emits a high-confidence
    signal with `is_crash_sovereign: True`, which grants sovereignty
    in TrinityCore to bypass static vetoes (SYNERGY_VETO, ENTROPIC_VACUUM,
    DRIFT_COHERENCE_WEAK, COMM_REWARD_RATIO_LOW).

    Architecture:
    ┌─────────────────────────────────────────────────────┐
    │ Sensor 1: Multi-Scale ROC Cascade                   │
    │ Sensor 2: Sequential Body Expansion                 │
    │ Sensor 3: Bollinger Squeeze → Expansion             │
    │ Sensor 4: Structural Break Cascade                  │
    │ Sensor 5: Momentum Acceleration Divergence          │
    │           ↓                                         │
    │     Composite Crash Severity Score [0.0 - 1.0]      │
    └─────────────────────────────────────────────────────┘
    """

    def __init__(self, weight: float = 5.5):
        super().__init__("CrashVelocityDetector", weight)
        self._prev_severity = 0.0

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        if OMEGA.get("crash_detection_enabled", 1.0) < 0.5:
            return None

        candles_m1 = snapshot.candles.get("M1")
        candles_m5 = snapshot.candles.get("M5")
        candles_m15 = snapshot.candles.get("M15")

        if not candles_m1 or len(candles_m1.get("close", [])) < 15:
            return None
        if not candles_m5 or len(candles_m5.get("close", [])) < 15:
            return None

        price = snapshot.price
        signal = 0.0
        severity = 0.0
        cascade_depth = 0
        reasoning_parts = []

        m1_closes = np.array(candles_m1["close"], dtype=np.float64)
        m1_opens = np.array(candles_m1["open"], dtype=np.float64)
        m1_highs = np.array(candles_m1["high"], dtype=np.float64)
        m1_lows = np.array(candles_m1["low"], dtype=np.float64)
        m1_volumes = np.array(
            candles_m1.get("tick_volume", candles_m1.get("real_volume", [1] * len(m1_closes))),
            dtype=np.float64,
        )

        m5_closes = np.array(candles_m5["close"], dtype=np.float64)
        m5_lows = np.array(candles_m5["low"], dtype=np.float64)
        m5_highs = np.array(candles_m5["high"], dtype=np.float64)

        # ═══ SENSOR 1: MULTI-SCALE ROC CASCADE ═══
        # When ROC is negative on multiple timeframes simultaneously → cascade
        roc_m1 = self._rate_of_change(m1_closes, period=5)
        roc_m5 = self._rate_of_change(m5_closes, period=5)

        roc_m15 = 0.0
        if candles_m15 and len(candles_m15.get("close", [])) >= 5:
            m15_closes = np.array(candles_m15["close"], dtype=np.float64)
            roc_m15 = self._rate_of_change(m15_closes, period=3)

        roc_threshold = OMEGA.get("crash_roc_threshold", -0.002)

        # Bearish cascade: all timeframes show negative ROC
        bearish_roc_count = sum(1 for r in [roc_m1, roc_m5, roc_m15] if r < roc_threshold)
        # Bullish cascade (for upside crash/squeeze)
        bullish_roc_count = sum(1 for r in [roc_m1, roc_m5, roc_m15] if r > abs(roc_threshold))

        if bearish_roc_count >= 2:
            roc_severity = bearish_roc_count / 3.0
            severity += roc_severity * 0.30  # 30% weight
            signal -= roc_severity * 0.35
            reasoning_parts.append(
                f"ROC_CASCADE({bearish_roc_count}/3 TFs, M1={roc_m1:.4f} M5={roc_m5:.4f} M15={roc_m15:.4f})"
            )
        elif bullish_roc_count >= 2:
            roc_severity = bullish_roc_count / 3.0
            severity += roc_severity * 0.30
            signal += roc_severity * 0.35
            reasoning_parts.append(
                f"SURGE_CASCADE({bullish_roc_count}/3 TFs, M1={roc_m1:.4f} M5={roc_m5:.4f} M15={roc_m15:.4f})"
            )

        # ═══ SENSOR 2: SEQUENTIAL BODY EXPANSION ═══
        # 3+ consecutive candles with expanding bodies → acceleration phase
        body_expansion, expansion_dir = self._sequential_body_expansion(
            m1_opens[-8:], m1_closes[-8:], min_consecutive=3
        )

        if body_expansion > 0:
            severity += 0.25  # 25% weight
            body_signal = -0.3 if expansion_dir < 0 else 0.3
            signal += body_signal
            direction_str = "BEAR" if expansion_dir < 0 else "BULL"
            reasoning_parts.append(
                f"BODY_EXPANSION({body_expansion} consecutive {direction_str})"
            )

            # Volume confirmation: are volumes also expanding?
            vol_expanding = self._check_volume_expansion(m1_volumes[-8:], body_expansion)
            if vol_expanding:
                severity += 0.10  # Bonus for volume confirmation
                signal += body_signal * 0.3  # Amplify
                reasoning_parts.append("VOL_CONFIRMED_EXPANSION")

        # ═══ SENSOR 3: BOLLINGER BAND SQUEEZE → EXPANSION ═══
        bb_signal, bb_expansion_ratio = self._bollinger_squeeze_expansion(m5_closes)

        if abs(bb_signal) > 0:
            severity += 0.15 * abs(bb_expansion_ratio)  # 15% weight
            signal += bb_signal * 0.2
            bb_dir = "BEAR" if bb_signal < 0 else "BULL"
            reasoning_parts.append(
                f"BB_EXPANSION({bb_dir}, ratio={bb_expansion_ratio:.2f})"
            )

        # ═══ SENSOR 4: STRUCTURAL BREAK CASCADE ═══
        # Count how many recent M5 swing lows have been broken
        swing_lows_m5 = self._detect_swing_lows(m5_lows, fractal_bars=2)
        swing_highs_m5 = self._detect_swing_highs(m5_highs, fractal_bars=2)

        broken_lows = sum(1 for level in swing_lows_m5[-5:] if price < level)
        broken_highs = sum(1 for level in swing_highs_m5[-5:] if price > level)

        cascade_depth_min = int(OMEGA.get("crash_cascade_depth_min", 2.0))

        if broken_lows >= cascade_depth_min:
            cascade_depth = broken_lows
            cascade_severity = min(broken_lows / 4.0, 1.0)
            severity += cascade_severity * 0.20  # 20% weight
            signal -= cascade_severity * 0.3
            reasoning_parts.append(
                f"STRUCTURAL_CASCADE(broken {broken_lows} M5 swing lows)"
            )
        elif broken_highs >= cascade_depth_min:
            cascade_depth = broken_highs
            cascade_severity = min(broken_highs / 4.0, 1.0)
            severity += cascade_severity * 0.20
            signal += cascade_severity * 0.3
            reasoning_parts.append(
                f"STRUCTURAL_SURGE(broken {broken_highs} M5 swing highs)"
            )

        # ═══ SENSOR 5: MOMENTUM ACCELERATION DIVERGENCE ═══
        # Price dropping faster than the previous N candles → acceleration
        accel_score, accel_dir = self._momentum_acceleration(m1_closes[-10:])

        if abs(accel_score) > 0.3:
            severity += abs(accel_score) * 0.10  # 10% weight
            signal += accel_dir * abs(accel_score) * 0.15
            accel_label = "BEAR_ACCEL" if accel_dir < 0 else "BULL_ACCEL"
            reasoning_parts.append(f"{accel_label}({accel_score:.2f})")

        # ═══ COMPOSITE SEVERITY & SIGNAL ═══
        severity = float(np.clip(severity, 0.0, 1.0))
        signal = float(np.clip(signal, -1.0, 1.0))

        # Smooth severity with previous reading (EMA-style)
        severity = 0.7 * severity + 0.3 * self._prev_severity
        self._prev_severity = severity

        crash_severity_threshold = OMEGA.get("crash_severity_threshold", 0.7)
        is_crash_sovereign = severity >= crash_severity_threshold and cascade_depth >= cascade_depth_min

        if abs(signal) < 0.08 and severity < 0.2:
            return None  # No significant drop/crash pattern

        confidence = float(np.clip(0.3 + severity * 0.7, 0.0, 0.99))

        metadata = {
            "crash_severity": round(severity, 3),
            "cascade_depth": cascade_depth,
            "is_crash_sovereign": is_crash_sovereign,
            "roc_m1": round(roc_m1, 6),
            "roc_m5": round(roc_m5, 6),
            "roc_m15": round(roc_m15, 6),
            "body_expansion_count": body_expansion,
        }

        reasoning = f"CRASH_VELOCITY[severity={severity:.2f}]: {' | '.join(reasoning_parts)}"

        return AgentSignal(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            weight=self.weight,
            metadata=metadata,
        )

    # ═══════════════════════════════════════════════════════════
    #  INTERNAL SENSOR ENGINES
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def _rate_of_change(closes: np.ndarray, period: int = 5) -> float:
        """Rate of Change = (close[-1] - close[-period]) / close[-period]."""
        if len(closes) < period + 1:
            return 0.0
        base = closes[-period - 1]
        if base == 0:
            return 0.0
        return float((closes[-1] - base) / base)

    @staticmethod
    def _sequential_body_expansion(opens, closes, min_consecutive: int = 3):
        """
        Detect N consecutive candles where each body is larger than the previous.
        Returns (count_of_consecutive, direction: -1=bearish, +1=bullish).
        """
        if len(opens) < min_consecutive + 1 or len(closes) < min_consecutive + 1:
            return 0, 0

        bodies = closes - opens  # Positive = bullish, negative = bearish
        abs_bodies = np.abs(bodies)

        best_count = 0
        best_dir = 0

        # Check bearish expansion (consecutive growing bearish bodies)
        bear_count = 0
        for i in range(1, len(bodies)):
            if bodies[i] < 0 and abs_bodies[i] > abs_bodies[i - 1] * 0.8:
                bear_count += 1
            else:
                if bear_count >= min_consecutive:
                    if bear_count > best_count:
                        best_count = bear_count
                        best_dir = -1
                bear_count = 0
        if bear_count >= min_consecutive and bear_count > best_count:
            best_count = bear_count
            best_dir = -1

        # Check bullish expansion
        bull_count = 0
        for i in range(1, len(bodies)):
            if bodies[i] > 0 and abs_bodies[i] > abs_bodies[i - 1] * 0.8:
                bull_count += 1
            else:
                if bull_count >= min_consecutive:
                    if bull_count > best_count:
                        best_count = bull_count
                        best_dir = 1
                bull_count = 0
        if bull_count >= min_consecutive and bull_count > best_count:
            best_count = bull_count
            best_dir = 1

        return best_count, best_dir

    @staticmethod
    def _check_volume_expansion(volumes: np.ndarray, n_candles: int) -> bool:
        """Check if volumes are expanding over the last n_candles."""
        if len(volumes) < n_candles + 1:
            return False
        recent = volumes[-n_candles:]
        expanding = sum(1 for i in range(1, len(recent)) if recent[i] > recent[i - 1] * 0.9)
        return expanding >= n_candles * 0.6  # 60% of candles show volume growth

    @staticmethod
    def _bollinger_squeeze_expansion(closes: np.ndarray, period: int = 20, std_mult: float = 2.0):
        """
        Detect Bollinger Band squeeze → expansion.
        Returns (signal: -1/+1/0, expansion_ratio: float).
        """
        if len(closes) < period + 5:
            return 0.0, 0.0

        sma = np.convolve(closes, np.ones(period) / period, mode="valid")
        if len(sma) < 5:
            return 0.0, 0.0

        # Calculate rolling std
        stds = []
        for i in range(len(closes) - period + 1):
            stds.append(np.std(closes[i : i + period]))
        stds = np.array(stds)

        if len(stds) < 5:
            return 0.0, 0.0

        # Recent bandwidth vs historical
        recent_width = float(stds[-1])
        past_width = float(np.mean(stds[-10:-2])) if len(stds) >= 10 else float(np.mean(stds[:-1]))

        if past_width == 0:
            return 0.0, 0.0

        expansion_ratio = recent_width / past_width

        # Squeeze → expansion: past was tight, now expanding
        if expansion_ratio > 1.5 and past_width < np.mean(stds) * 0.8:
            # Direction: is price above or below the mean?
            direction = 1.0 if closes[-1] > sma[-1] else -1.0
            return direction, min(expansion_ratio, 3.0)

        return 0.0, 0.0

    @staticmethod
    def _detect_swing_lows(lows: np.ndarray, fractal_bars: int = 2):
        """Detect swing lows using fractal logic."""
        levels = []
        n = len(lows)
        for i in range(fractal_bars, n - fractal_bars):
            is_fractal = all(lows[i] < lows[i - j] for j in range(1, fractal_bars + 1)) and \
                         all(lows[i] < lows[i + j] for j in range(1, fractal_bars + 1))
            if is_fractal:
                levels.append(float(lows[i]))
        return levels

    @staticmethod
    def _detect_swing_highs(highs: np.ndarray, fractal_bars: int = 2):
        """Detect swing highs using fractal logic."""
        levels = []
        n = len(highs)
        for i in range(fractal_bars, n - fractal_bars):
            is_fractal = all(highs[i] > highs[i - j] for j in range(1, fractal_bars + 1)) and \
                         all(highs[i] > highs[i + j] for j in range(1, fractal_bars + 1))
            if is_fractal:
                levels.append(float(highs[i]))
        return levels

    @staticmethod
    def _momentum_acceleration(closes: np.ndarray):
        """
        Detect if price movement is accelerating (second derivative).
        Returns (score: 0-1, direction: -1/+1).
        """
        if len(closes) < 6:
            return 0.0, 0

        # First derivative (velocity)
        velocity = np.diff(closes)
        # Second derivative (acceleration)
        acceleration = np.diff(velocity)

        if len(acceleration) < 3:
            return 0.0, 0

        recent_accel = acceleration[-3:]
        avg_accel = float(np.mean(recent_accel))
        std_accel = float(np.std(acceleration)) if len(acceleration) > 1 else 1.0

        if std_accel == 0:
            return 0.0, 0

        # Normalized acceleration score
        accel_score = abs(avg_accel) / max(std_accel, 1e-10)
        accel_score = float(np.clip(accel_score, 0.0, 1.0))

        direction = -1 if avg_accel < 0 else 1

        return accel_score, direction
