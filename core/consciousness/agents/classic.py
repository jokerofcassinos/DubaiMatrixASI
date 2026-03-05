"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — CLASSIC AGENTS (Phase 3)                    ║
║     9 agentes fundacionais: Trend, Momentum, Volume, Vol, Micro, etc.      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import Optional

from core.consciousness.agents.base import AgentSignal, BaseAgent
from utils.decorators import catch_and_log


class TrendAgent(BaseAgent):
    """Analisa tendência em múltiplos timeframes via EMAs."""

    def __init__(self, weight: float = 1.0):
        super().__init__("TrendAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        signals = []
        reasons = []

        for tf in ["M1", "M5", "M15"]:
            indicators = snapshot.indicators
            ema_9 = indicators.get(f"{tf}_ema_9")
            ema_21 = indicators.get(f"{tf}_ema_21")
            ema_50 = indicators.get(f"{tf}_ema_50")

            if ema_9 is None or ema_21 is None or ema_50 is None:
                continue
            if len(ema_9) < 5:
                continue

            last_9, last_21, last_50 = ema_9[-1], ema_21[-1], ema_50[-1]

            if last_9 > last_21 > last_50:
                signals.append(1.0)
                reasons.append(f"{tf}:BULL_ALIGNED")
            elif last_9 < last_21 < last_50:
                signals.append(-1.0)
                reasons.append(f"{tf}:BEAR_ALIGNED")
            else:
                if len(ema_9) > 2:
                    if ema_9[-2] <= ema_21[-2] and ema_9[-1] > ema_21[-1]:
                        signals.append(0.6)
                        reasons.append(f"{tf}:BULL_CROSS")
                    elif ema_9[-2] >= ema_21[-2] and ema_9[-1] < ema_21[-1]:
                        signals.append(-0.6)
                        reasons.append(f"{tf}:BEAR_CROSS")
                    else:
                        signals.append(0.0)
                        reasons.append(f"{tf}:NO_TREND")

        if not signals:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        avg_signal = np.mean(signals)
        confidence = abs(avg_signal) * 0.8 + 0.2 * (1.0 if len(set(np.sign(signals))) == 1 else 0.0)

        return AgentSignal(
            self.name, float(np.clip(avg_signal, -1, 1)),
            float(np.clip(confidence, 0, 1)),
            " | ".join(reasons), self.weight
        )


class MomentumAgent(BaseAgent):
    """Analisa momentum: RSI, MACD, velocidade de preço."""

    def __init__(self, weight: float = 1.0):
        super().__init__("MomentumAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        signals = []
        reasons = []
        tf = "M5"
        indicators = snapshot.indicators

        rsi = indicators.get(f"{tf}_rsi_14")
        if rsi is not None and len(rsi) > 5:
            last_rsi = rsi[-1]
            if last_rsi > 70:
                signals.append(-0.7); reasons.append(f"RSI={last_rsi:.0f}:OVERBOUGHT")
            elif last_rsi < 30:
                signals.append(0.7); reasons.append(f"RSI={last_rsi:.0f}:OVERSOLD")
            elif last_rsi > 55:
                signals.append(0.3); reasons.append(f"RSI={last_rsi:.0f}:BULL")
            elif last_rsi < 45:
                signals.append(-0.3); reasons.append(f"RSI={last_rsi:.0f}:BEAR")
            else:
                signals.append(0.0)

        macd_hist = indicators.get(f"{tf}_macd_histogram")
        if macd_hist is not None and len(macd_hist) > 2:
            current_hist = macd_hist[-1]
            prev_hist = macd_hist[-2]

            if current_hist > 0 and current_hist > prev_hist:
                signals.append(0.6); reasons.append("MACD:BULL_ACCELERATING")
            elif current_hist < 0 and current_hist < prev_hist:
                signals.append(-0.6); reasons.append("MACD:BEAR_ACCELERATING")
            elif current_hist > 0 and current_hist < prev_hist:
                signals.append(0.2); reasons.append("MACD:BULL_DECELERATING")
            elif current_hist < 0 and current_hist > prev_hist:
                signals.append(-0.2); reasons.append("MACD:BEAR_DECELERATING")

            macd = indicators.get(f"{tf}_macd")
            macd_sig = indicators.get(f"{tf}_macd_signal")
            if macd is not None and macd_sig is not None and len(macd) > 2:
                if macd[-2] <= macd_sig[-2] and macd[-1] > macd_sig[-1]:
                    signals.append(0.8); reasons.append("MACD:BULLISH_CROSS")
                elif macd[-2] >= macd_sig[-2] and macd[-1] < macd_sig[-1]:
                    signals.append(-0.8); reasons.append("MACD:BEARISH_CROSS")

        if not signals:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        avg = np.mean(signals)
        conf = min(1.0, abs(avg) + 0.2)
        return AgentSignal(self.name, float(np.clip(avg, -1, 1)), float(np.clip(conf, 0, 1)),
                           " | ".join(reasons), self.weight)


class VolumeAgent(BaseAgent):
    """Analisa volume: anomalias, climax, confirmação de movimento."""

    def __init__(self, weight: float = 0.8):
        super().__init__("VolumeAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        indicators = snapshot.indicators
        tf = "M5"
        vol_ratio = indicators.get(f"{tf}_volume_ratio")
        if vol_ratio is None or len(vol_ratio) < 5:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        candles = snapshot.candles.get(tf)
        if candles is None:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        close = candles["close"]
        last_vol_ratio = vol_ratio[-1]
        price_change = (close[-1] - close[-2]) / close[-2] * 100 if len(close) > 1 else 0

        reasons = []
        signal = 0.0

        if last_vol_ratio > 4.0:
            signal = -np.sign(price_change) * 0.3
            reasons.append(f"VOL_CLIMAX({last_vol_ratio:.1f}x):EXHAUSTION_RISK")
        elif last_vol_ratio > 2.0:
            if price_change > 0:
                signal = 0.6; reasons.append(f"VOL_SPIKE({last_vol_ratio:.1f}x):BULL_CONFIRMED")
            elif price_change < 0:
                signal = -0.6; reasons.append(f"VOL_SPIKE({last_vol_ratio:.1f}x):BEAR_CONFIRMED")
            else:
                reasons.append(f"VOL_SPIKE({last_vol_ratio:.1f}x):NO_DIRECTION")
        elif last_vol_ratio < 0.5:
            signal = 0.0
            reasons.append(f"VOL_DRY({last_vol_ratio:.1f}x):LOW_CONVICTION")

        confidence = min(1.0, abs(signal) + 0.1)
        return AgentSignal(self.name, float(np.clip(signal, -1, 1)), float(confidence),
                           " | ".join(reasons) if reasons else "NORMAL_VOLUME", self.weight)


class VolatilityAgent(BaseAgent):
    """Analisa volatilidade: BB squeeze, ATR, regime de vol."""

    def __init__(self, weight: float = 0.9):
        super().__init__("VolatilityAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        indicators = snapshot.indicators
        tf = "M5"
        bb_width = indicators.get(f"{tf}_bb_width")
        atr = indicators.get(f"{tf}_atr_14")

        if bb_width is None or atr is None:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)
        if len(bb_width) < 20 or len(atr) < 5:
            return AgentSignal(self.name, 0.0, 0.0, "INSUFFICIENT_DATA", self.weight)

        reasons = []
        signal = 0.0

        current_width = bb_width[-1]
        avg_width = np.mean(bb_width[-50:]) if len(bb_width) >= 50 else np.mean(bb_width)

        if current_width < avg_width * 0.5:
            reasons.append("BB_SQUEEZE:BREAKOUT_IMMINENT")
        elif current_width > avg_width * 2.0:
            reasons.append("BB_EXPANDED:HIGH_VOL")

        bb_upper = indicators.get(f"{tf}_bb_upper")
        bb_lower = indicators.get(f"{tf}_bb_lower")
        candles = snapshot.candles.get(tf)

        if bb_upper is not None and bb_lower is not None and candles is not None:
            close = candles["close"]
            if len(close) > 0 and bb_upper[-1] != bb_lower[-1]:
                bb_pct = (close[-1] - bb_lower[-1]) / (bb_upper[-1] - bb_lower[-1])
                if bb_pct > 0.95:
                    signal -= 0.4; reasons.append(f"BB_PCT={bb_pct:.2f}:UPPER_TOUCH")
                elif bb_pct < 0.05:
                    signal += 0.4; reasons.append(f"BB_PCT={bb_pct:.2f}:LOWER_TOUCH")

        confidence = 0.5 + abs(signal) * 0.3
        return AgentSignal(self.name, float(np.clip(signal, -1, 1)),
                           float(np.clip(confidence, 0, 1)),
                           " | ".join(reasons) if reasons else "NORMAL_VOL", self.weight)


class MicrostructureAgent(BaseAgent):
    """Analisa microestrutura: order flow, delta, imbalance."""

    def __init__(self, weight: float = 1.2):
        super().__init__("MicrostructureAgent", weight)
        self.needs_orderflow = True

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, orderflow_analysis: dict = None, **kw) -> Optional[AgentSignal]:
        if not orderflow_analysis:
            return AgentSignal(self.name, 0.0, 0.0, "NO_FLOW_DATA", self.weight)

        signal = orderflow_analysis.get("signal", 0.0)
        delta_dir = orderflow_analysis.get("delta_direction", "NEUTRAL")
        imbalance_sig = orderflow_analysis.get("imbalance_signal", "NEUTRAL")
        absorption = orderflow_analysis.get("absorption", {})
        exhaustion = orderflow_analysis.get("exhaustion", {})

        reasons = [f"DELTA:{delta_dir}", f"IMBALANCE:{imbalance_sig}"]
        if absorption.get("detected"):
            reasons.append(f"ABSORPTION:{absorption['type']}")
        if exhaustion.get("detected"):
            reasons.append(f"EXHAUSTION:{exhaustion['type']}")

        confidence = min(1.0, abs(signal) * 1.5 + 0.2)
        return AgentSignal(self.name, float(np.clip(signal, -1, 1)),
                           float(np.clip(confidence, 0, 1)),
                           " | ".join(reasons), self.weight)


class StatisticalAgent(BaseAgent):
    """Analisa estatísticas: z-score, Hurst, entropia, mean reversion."""

    def __init__(self, weight: float = 0.8):
        super().__init__("StatisticalAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        indicators = snapshot.indicators
        tf = "M5"
        zscore = indicators.get(f"{tf}_price_zscore")
        hurst = indicators.get(f"{tf}_hurst")
        entropy = indicators.get(f"{tf}_entropy")

        if zscore is None:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        reasons = []
        signal = 0.0

        if hasattr(zscore, '__len__') and len(zscore) > 0:
            z = zscore[-1]
            if z > 2.5: signal -= 0.7; reasons.append(f"Z={z:.2f}:EXTREME_HIGH")
            elif z > 1.5: signal -= 0.3; reasons.append(f"Z={z:.2f}:HIGH")
            elif z < -2.5: signal += 0.7; reasons.append(f"Z={z:.2f}:EXTREME_LOW")
            elif z < -1.5: signal += 0.3; reasons.append(f"Z={z:.2f}:LOW")

        if hurst is not None and isinstance(hurst, (int, float)):
            if hurst > 0.6: reasons.append(f"HURST={hurst:.2f}:TRENDING")
            elif hurst < 0.4:
                reasons.append(f"HURST={hurst:.2f}:MEAN_REVERTING")
                signal *= 1.3
            else: reasons.append(f"HURST={hurst:.2f}:RANDOM")

        if entropy is not None and isinstance(entropy, (int, float)):
            if entropy > 4.0:
                reasons.append(f"ENTROPY={entropy:.2f}:CHAOTIC"); signal *= 0.5
            elif entropy < 2.0:
                reasons.append(f"ENTROPY={entropy:.2f}:PREDICTABLE"); signal *= 1.2

        confidence = min(1.0, abs(signal) * 0.8 + 0.15)
        return AgentSignal(self.name, float(np.clip(signal, -1, 1)),
                           float(np.clip(confidence, 0, 1)),
                           " | ".join(reasons) if reasons else "STATISTICAL_NEUTRAL", self.weight)


class FractalAgent(BaseAgent):
    """Analisa dimensão fractal e auto-similaridade."""

    def __init__(self, weight: float = 0.6):
        super().__init__("FractalAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        candles = snapshot.candles.get("M5")
        if candles is None or len(candles["close"]) < 50:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        close = candles["close"]
        fd = self.math.fractal_dimension(close, 50)

        reasons = []
        signal = 0.0

        if fd < 1.3:
            reasons.append(f"FD={fd:.2f}:SMOOTH_TREND")
            price_dir = 1.0 if close[-1] > close[-10] else -1.0
            signal = price_dir * 0.5
        elif fd > 1.7:
            reasons.append(f"FD={fd:.2f}:NOISY_CHAOTIC"); signal = 0.0
        else:
            reasons.append(f"FD={fd:.2f}:MODERATE")

        confidence = max(0.2, 1.0 - abs(fd - 1.0))
        return AgentSignal(self.name, float(np.clip(signal, -1, 1)),
                           float(np.clip(confidence, 0, 1)),
                           " | ".join(reasons), self.weight)


class SupportResistanceAgent(BaseAgent):
    """Analisa proximidade a suporte/resistência."""

    def __init__(self, weight: float = 0.9):
        super().__init__("SRAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        sr = snapshot.indicators.get("M5_sr_levels")
        if not sr:
            return AgentSignal(self.name, 0.0, 0.0, "NO_SR", self.weight)

        price = snapshot.price
        if price <= 0:
            return AgentSignal(self.name, 0.0, 0.0, "NO_PRICE", self.weight)

        supports = sr.get("support", [])
        resistances = sr.get("resistance", [])
        reasons = []
        signal = 0.0

        for s_price, touches in supports[:3]:
            dist_pct = (price - s_price) / price * 100
            if 0 < dist_pct < 0.5:
                strength = min(1.0, touches / 3.0)
                signal += 0.5 * strength
                reasons.append(f"NEAR_SUPPORT({s_price:.0f},T={touches})")

        for r_price, touches in resistances[:3]:
            dist_pct = (r_price - price) / price * 100
            if 0 < dist_pct < 0.5:
                strength = min(1.0, touches / 3.0)
                signal -= 0.5 * strength
                reasons.append(f"NEAR_RESISTANCE({r_price:.0f},T={touches})")

        confidence = min(1.0, abs(signal) + 0.3) if reasons else 0.1
        return AgentSignal(self.name, float(np.clip(signal, -1, 1)),
                           float(np.clip(confidence, 0, 1)),
                           " | ".join(reasons) if reasons else "NO_NEARBY_SR", self.weight)


class DivergenceAgent(BaseAgent):
    """Divergência: Price faz Higher High, Oscillator faz Lower High = Venda."""

    def __init__(self, weight: float = 0.7):
        super().__init__("DivergenceAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        closes = snapshot.m1_closes
        if len(closes) < 50:
            return None

        rsi = self.math.rsi(closes, period=14)
        if len(rsi) < 10:
            return None

        price_hh = closes[-1] > closes[-5]
        rsi_lh = rsi[-1] < rsi[-5]
        price_ll = closes[-1] < closes[-5]
        rsi_hl = rsi[-1] > rsi[-5]

        signal = 0.0
        reason = "Sem divergêcia clara."

        if price_hh and rsi_lh:
            signal = -0.7; reason = "Bearish Divergence (Price HH, RSI LH)"
        elif price_ll and rsi_hl:
            signal = 0.7; reason = "Bullish Divergence (Price LL, RSI HL)"

        return AgentSignal(self.name, signal, abs(signal) + 0.1, reason, self.weight)
