"""
SOLÉNN v2 — Feature Engineering Pipeline (Ω-D55 a Ω-D108)
Technical indicators, order flow features, volatility features,
momentum & trend features, statistical features, microstructure features.
All computed incrementally (O(1) per update).
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Any


def _ema(value: float, prev_ema: float, alpha: float) -> float:
    """Incremental EMA update."""
    if prev_ema is None:
        return value
    return alpha * value + (1 - alpha) * prev_ema


class TechnicalIndicators:
    """
    Ω-D55 a Ω-D63: Real-time technical indicators, all O(1) per update.
    """

    def __init__(self, rsi_period: int = 14, macd_fast: int = 12,
                 macd_slow: int = 26, macd_signal: int = 9,
                 bb_period: int = 20, bb_std: float = 2.0,
                 atr_period: int = 14) -> None:
        self._prices: deque[float] = deque(maxlen=max(rsi_period * 2, macd_slow * 2, bb_period * 2, atr_period * 2))
        self._gains: deque[float] = deque(maxlen=rsi_period)
        self._losses: deque[float] = deque(maxlen=rsi_period)
        self._rsi_period = rsi_period
        # MACD
        self._macd_fast_alpha = 2 / (macd_fast + 1)
        self._macd_slow_alpha = 2 / (macd_slow + 1)
        self._macd_signal_alpha = 2 / (macd_signal + 1)
        self._ema_fast: float | None = None
        self._ema_slow: float | None = None
        self._macd_line: float | None = None
        self._signal_line: float | None = None
        # BB
        self._bb_period = bb_period
        self._bb_mult = bb_std
        # ATR
        self._atr_period = atr_period
        self._atr_values: deque[float] = deque(maxlen=atr_period)
        self._prev_close: float | None = None

    def update(self, price: float) -> dict[str, float | None]:
        """Ω-D63: O(1) update all indicators."""
        self._prices.append(price)
        result: dict[str, float | None] = {}

        # Ω-D55: EMA/SMA
        ema_12 = _ema(price, self._prices[-12] if len(self._prices) >= 12 else None, 2 / 13) if self._prices else price
        ema_26 = _ema(price, self._prices[-26] if len(self._prices) >= 26 else None, 2 / 27) if self._prices else price
        sma = sum(self._prices) / len(self._prices) if self._prices else price
        result["ema_12"] = ema_12
        result["ema_26"] = ema_26
        result["sma"] = sma

        # Ω-D56: RSI
        if self._prev_close is not None:
            change = price - self._prev_close
            gain = max(0, change)
            loss = max(0, -change)
            self._gains.append(gain)
            self._losses.append(loss)
            if len(self._gains) == self._rsi_period:
                avg_gain = sum(self._gains) / self._rsi_period
                avg_loss = sum(self._losses) / self._rsi_period
                if avg_loss > 0:
                    result["rsi"] = 100 - (100 / (1 + avg_gain / avg_loss))
                else:
                    result["rsi"] = 100.0
            else:
                result["rsi"] = 50.0
        else:
            result["rsi"] = 50.0

        # Ω-D57: MACD
        if self._ema_fast is not None:
            self._ema_fast = _ema(price, self._ema_fast, self._macd_fast_alpha)
            self._ema_slow = _ema(price, self._ema_slow, self._macd_slow_alpha)
            macd_val = (self._ema_fast - self._ema_slow) if self._ema_fast and self._ema_slow else 0
            self._macd_line = macd_val
            if self._signal_line is not None:
                self._signal_line = _ema(macd_val, self._signal_line, self._macd_signal_alpha)
            result["macd"] = macd_val
            result["macd_signal"] = self._signal_line
        else:
            self._ema_fast = price
            self._ema_slow = price
            result["macd"] = 0
            result["macd_signal"] = None

        # Ω-D58: Bollinger Bands
        if len(self._prices) >= self._bb_period:
            window = list(self._prices)[-self._bb_period:]
            m = sum(window) / len(window)
            variance = sum((x - m) ** 2 for x in window) / len(window)
            std = math.sqrt(variance) if variance > 0 else 0
            result["bb_mid"] = m
            result["bb_upper"] = m + self._bb_mult * std
            result["bb_lower"] = m - self._bb_mult * std
            result["bb_width"] = (result["bb_upper"] - result["bb_lower"]) / m if m > 0 else 0
            result["bb_squeeze"] = 1.0 if result["bb_width"] < 0.02 else 0.0
        else:
            result["bb_mid"] = price
            result["bb_upper"] = price
            result["bb_lower"] = price
            result["bb_width"] = 0
            result["bb_squeeze"] = 0

        # Ω-D59: ATR
        if self._prev_close is not None:
            tr = max(price - self._prev_close, self._prev_close - price * 0.99, 0)
            self._atr_values.append(tr)
            result["atr"] = sum(self._atr_values) / len(self._atr_values)
        else:
            result["atr"] = 0

        self._prev_close = price

        # Ω-D61: Volume-weighted RSI (placeholder volume)
        result["vrsi"] = result["rsi"]

        # Ω-D63: All indicators O(1) per tick
        # Ω-D86: ADX placeholder
        result["adx"] = None

        return result


class VolatilityCalculator:
    """
    Ω-D73 a Ω-D81: Multi-method volatility estimation.
    """

    def __init__(self, window: int = 100) -> None:
        self._window = window
        self._log_returns: deque[float] = deque(maxlen=window * 2)

    def update(self, price: float) -> float | None:
        """Add new log return and compute realized vol."""
        n = len(self._log_returns)
        self._log_returns.append(math.log(price / price) if price > 0 else 0)
        # Use previous price for log return
        if n > 0:
            prev_prices = list(self._log_returns)
        if n >= 1:
            # Just return simple vol estimate for now
            return self.realized_vol()
        return None

    def update_with_prev(self, price: float, prev_price: float) -> float | None:
        if prev_price > 0 and price > 0:
            self._log_returns.append(math.log(price / prev_price))
            if len(self._log_returns) >= self._window:
                return self.realized_vol()
        return None

    def realized_vol(self) -> float:
        """Ω-D73: Realized volatility."""
        if len(self._log_returns) < self._window:
            return 0.0
        window = list(self._log_returns)[-self._window:]
        mean_r = sum(window) / len(window)
        var = sum((r - mean_r) ** 2 for r in window) / (len(window) - 1)
        return math.sqrt(var)

    def parkinson_vol(self, highs: list[float], lows: list[float]) -> float:
        """Ω-D74: Parkinson volatility using high-low range."""
        n = min(len(highs), len(lows), self._window)
        if n < 5:
            return 0.0
        sum_sq = sum((math.log(highs[-i] / lows[-i])) ** 2 for i in range(1, n + 1))
        return math.sqrt(sum_sq / (4 * n))

    def garman_klass(self, opens: list[float], highs: list[float],
                     lows: list[float], closes: list[float]) -> float:
        """Ω-D75: Garman-Klass volatility."""
        n = min(len(opens), len(highs), len(lows), len(closes), self._window)
        if n < 5:
            return 0.0
        s = 0.0
        for i in range(1, n + 1):
            o, h, l, c = opens[-i], highs[-i], lows[-i], closes[-i]
            if o > 0 and h > 0 and l > 0:
                s += 0.5 * (math.log(h / l)) ** 2 - (2 * math.log(2) - 1) * (math.log(c / o)) ** 2
        return math.sqrt(max(0, s / n))

    def yang_zhang(self, opens: list[float], highs: list[float],
                   lows: list[float], closes: list[float]) -> float:
        """Ω-D76: Yang-Zhang volatility."""
        n = min(len(opens), len(highs), len(lows), len(closes), self._window) - 1
        if n < 5:
            return 0.0
        closes_log = [math.log(closes[-i] / closes[-i - 1]) for i in range(1, n + 1)]
        opens_log = [math.log(opens[-i] / closes[-i - 1]) for i in range(1, n + 1)]
        mean_close = sum(closes_log) / n
        mean_open = sum(opens_log) / n
        sigma_oc = sum((c - mean_close) ** 2 for c in closes_log) / (n - 1)
        sigma_co = sum((o - mean_open) ** 2 for o in opens_log) / (n - 1)
        sum_rs = sum((math.log(highs[-i] / lows[-i]) - math.log(opens[-i] / closes[-i - 1])) ** 2
                     for i in range(1, n + 1))
        k = 0.34 / (1.34 + (n + 1) / (n - 1))
        sigma_rs = max(0, sum_rs / n)
        return math.sqrt(max(0, sigma_co + k * sigma_oc + (1 - k) * sigma_rs))


class MomentumEngine:
    """
    Ω-D82 a Ω-D90: Momentum and trend features.
    """

    def __init__(self, window: int = 100) -> None:
        self._window = window
        self._prices: deque[float] = deque(maxlen=window * 2)

    def update(self, price: float) -> dict[str, float]:
        self._prices.append(price)
        result: dict[str, float] = {}

        n = len(self._prices)
        if n < 10:
            return {"momentum": 0.0, "trend_strength": 0.0, "hurst": 0.5, "fractal_dim": 1.5}

        # Ω-D84: Momentum (rate of change)
        result["momentum"] = (self._prices[-1] / self._prices[0] - 1) * 100 if self._prices[0] > 0 else 0

        # Ω-D85: Trend strength (R² of linear regression)
        prices = list(self._prices)[-self._window:]
        n = len(prices)
        x_bar = (n - 1) / 2
        y_bar = sum(prices) / n
        ss_xy = sum((i - x_bar) * (prices[i] - y_bar) for i in range(n))
        ss_xx = sum((i - x_bar) ** 2 for i in range(n))
        ss_yy = sum((prices[i] - y_bar) ** 2 for i in range(n))
        if ss_xx > 0 and ss_yy > 0:
            r_squared = (ss_xy ** 2) / (ss_xx * ss_yy)
            result["trend_strength"] = r_squared
            result["trend_direction"] = 1.0 if ss_xy > 0 else -1.0
        else:
            result["trend_strength"] = 0.0
            result["trend_direction"] = 0.0

        # Ω-D82: Hurst exponent (simple R/S method)
        if n >= 20:
            result["hurst"] = self._compute_hurst(prices)
        else:
            result["hurst"] = 0.5

        # Ω-D87: Fractal dimension
        result["fractal_dim"] = 2.0 - result["hurst"]

        # Ω-D83: Autocorrelation at lag 1
        if n >= 2:
            returns = [prices[i] / prices[i - 1] - 1 for i in range(1, n) if prices[i - 1] > 0]
            if len(returns) >= 2:
                mean_r = sum(returns) / len(returns)
                num = sum((returns[i] - mean_r) * (returns[i + 1] - mean_r)
                         for i in range(len(returns) - 1))
                den = sum((r - mean_r) ** 2 for r in returns)
                result["autocorrelation"] = num / den if den > 0 else 0
            else:
                result["autocorrelation"] = 0
        else:
            result["autocorrelation"] = 0

        # Ω-D89: Spectral energy ratio (high vs low frequency)
        result["spectral_energy_ratio"] = 0.0  # Placeholder

        return result

    def _compute_hurst(self, prices: list[float]) -> float:
        """Simple R/S method for Hurst exponent."""
        half = len(prices) // 2
        if half < 10:
            return 0.5
        log_prices = [math.log(p) if p > 0 else 0 for p in prices]
        mean_lp = sum(log_prices) / len(log_prices)
        deviations = [lp - mean_lp for lp in log_prices]
        cum_dev = []
        s = 0
        for d in deviations:
            s += d
            cum_dev.append(s)
        r = max(cum_dev) - min(cum_dev)
        if r == 0:
            return 0.5
        ss = sum(d ** 2 for d in deviations)
        s_std = (ss / len(deviations)) ** 0.5
        if s_std == 0:
            return 0.5
        rs = r / s_std
        return math.log(rs) / math.log(len(log_prices)) if rs > 1 else 0.5


class StatisticalFeatures:
    """
    Ω-D91 a Ω-D99: Statistical features of return distributions.
    """

    def __init__(self, window: int = 200) -> None:
        self._window = window
        self._returns: deque[float] = deque(maxlen=window)

    def update(self, price: float, prev_price: float) -> dict[str, float]:
        if prev_price > 0:
            self._returns.append(math.log(price / prev_price))
        return self.compute()

    def compute(self) -> dict[str, float]:
        n = len(self._returns)
        if n < 10:
            return {"skewness": 0, "kurtosis": 3.0, "entropy": 0.0,
                    "zscore": 0.0, "tail_index": 2.0}

        returns = list(self._returns)
        mean_r = sum(returns) / n
        std_r = (sum((r - mean_r) ** 2 for r in returns) / (n - 1)) ** 0.5

        # Ω-D91: Skewness
        if std_r > 0:
            skewness = sum((r - mean_r) ** 3 for r in returns) / (n * std_r ** 3)
        else:
            skewness = 0

        # Ω-D92: Kurtosis
        if std_r > 0:
            kurtosis = sum((r - mean_r) ** 4 for r in returns) / (n * std_r ** 4)
        else:
            kurtosis = 3.0

        # Ω-D94: Shannon entropy (binned)
        histogram: dict[str, int] = {}
        for r in returns:
            bin_key = f"{r * 1000:.0f}"
            histogram[bin_key] = histogram.get(bin_key, 0) + 1
        total = len(returns)
        entropy = -sum((c / total) * math.log2(c / total) for c in histogram.values() if c > 0)

        # Ω-D93: Jarque-Bera test (simplified)
        jb = n * (skewness ** 2 / 6 + (kurtosis - 3) ** 2 / 24)

        # Ω-D97: Z-score vs moving average
        last_price = 1.0  # Placeholder — should be passed in
        zscore = 0.0

        return {
            "skewness": skewness,
            "kurtosis": kurtosis,
            "entropy": entropy,
            "jb_test": jb,
            "zscore": zscore,
            "std_return": std_r,
            "mean_return": mean_r,
        }


class MicrostructureFeatures:
    """
    Ω-D100 a Ω-D108: Microstructure features from order book and trades.
    """

    def __init__(self) -> None:
        self._spreads: deque[float] = deque(maxlen=100)
        self._kyle_values: list[float] = []
        self._price_changes: list[float] = []
        self._volumes: list[float] = []

    def update(self, spread: float, mid_price: float,
               signed_orderflow: float, trade_volume: float) -> dict[str, float]:
        """Update microstructure features."""
        self._spreads.append(spread)

        # Ω-D100: Effective spread
        effective_spread = spread / mid_price * 10000 if mid_price > 0 else 0

        # Ω-D102: Kyle's lambda (simplified)
        self._kyle_values.append(signed_orderflow)
        self._volumes.append(trade_volume)
        self._price_changes.append(0)  # Placeholder

        # Ω-D103: Amihud illiquidity
        amihud = abs(0) / trade_volume * 1e6 if trade_volume > 0 else 0

        return {
            "effective_spread_bps": effective_spread,
            "realized_spread_bps": effective_spread * 0.7,  # Placeholder
            "kyles_lambda": 0.0,
            "amihud_illiquidity": amihud,
            "roll_spread": 0.0,  # Placeholder
            "info_share": 0.0,   # Placeholder
            "market_quality": max(0, 100 - abs(effective_spread) - abs(amihud / 100)),
            "liquidity_resilience": 0.0,
        }
