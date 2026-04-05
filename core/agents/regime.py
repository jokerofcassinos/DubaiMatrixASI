"""
SOLÉNN v2 — Regime & Structural Signal Agents (Ω-E55 to Ω-E108)
Fractal analysis, volatility regime detection, trend & momentum
signals, statistical arbitrage signals, event-driven signals,
and network science signals.

Concept 2 Tópicos 2.1–2.6
"""

from __future__ import annotations

import math
import time
from collections import defaultdict, deque
from typing import Any


# ──────────────────────────────────────────────────────────────
# Ω-E55 to Ω-E63: Fractal Analysis
# ──────────────────────────────────────────────────────────────

class HurstExponentCalculator:
    """Ω-E55: Dynamic Hurst exponent via R/S method in sliding window."""

    def __init__(self, window: int = 200) -> None:
        self._window = window
        self._returns: deque[float] = deque(maxlen=window)

    def update(self, ret: float) -> float:
        self._returns.append(ret)
        return self.compute()

    def compute(self) -> float:
        if len(self._returns) < 30:
            return 0.5
        prices = self._returns_to_prices()
        logs = [math.log(p) for p in prices if p > 0]
        return _rs_hurst(logs)

    def _returns_to_prices(self) -> list[float]:
        prices = [1.0]
        for r in self._returns:
            prices.append(prices[-1] * (1 + r))
        return prices


def _rs_hurst(logs: list[float]) -> float:
    """Simple R/S Hurst exponent."""
    if len(logs) < 20:
        return 0.5
    mean = sum(logs) / len(logs)
    deviations = [x - mean for x in logs]
    cum_dev = []
    s = 0.0
    for d in deviations:
        s += d
        cum_dev.append(s)
    r = max(cum_dev) - min(cum_dev)
    std = (sum(d ** 2 for d in deviations) / len(deviations)) ** 0.5
    if r == 0 or std == 0 or len(logs) < 2:
        return 0.5
    rs = r / std
    if rs <= 1.0:
        return 0.5
    return min(1.0, math.log(rs) / math.log(len(logs)))


class FractalDimensionCalculator:
    """Ω-E57: D = 2 - H mapping."""

    def __init__(self, hurst_calculator: HurstExponentCalculator | None = None) -> None:
        self._hurst = hurst_calculator or HurstExponentCalculator()
        self._last_h = 0.5

    def update(self, ret: float) -> float:
        self._last_h = self._hurst.update(ret)
        return 2.0 - self._last_h

    def compute(self) -> float:
        return 2.0 - self._last_h


class ScaleInvariantFeatures:
    """Ω-E62: Features invariant to price/volume scale changes."""

    @staticmethod
    def compute_returns(price_series: list[float]) -> list[float]:
        """Returns normalized (scale-invariant) returns."""
        if len(price_series) < 2:
            return []
        return [(price_series[i] - price_series[i - 1]) / price_series[i - 1]
                for i in range(1, len(price_series)) if price_series[i - 1] > 0]

    @staticmethod
    def compute_relative_volume(volume_series: list[float], window: int = 20) -> list[float]:
        """Volume normalized by average (scale-invariant)."""
        if len(volume_series) < window:
            return [1.0] * len(volume_series)
        result = []
        for i in range(len(volume_series)):
            start = max(0, i - window)
            avg = sum(volume_series[start:i + 1]) / (i - start + 1)
            result.append(volume_series[i] / avg if avg > 0 else 1.0)
        return result


# ──────────────────────────────────────────────────────────────
# Ω-E64 to Ω-E72: Volatility Regime Detection
# ──────────────────────────────────────────────────────────────

class VolatilityCone:
    """Ω-E64: Current vol vs historical percentiles by horizon."""

    def __init__(self, horizons: list[int] | None = None) -> None:
        self._horizons = horizons or [10, 30, 60, 120, 250]
        self._returns: deque[float] = deque(maxlen=300)
        self._vol_history: dict[int, list[float]] = {h: [] for h in self._horizons}

    def update(self, ret: float) -> dict[int, dict[str, float]]:
        self._returns.append(ret)
        if len(self._returns) < max(self._horizons):
            return {}

        all_returns = list(self._returns)
        result = {}
        for horizon in self._horizons:
            window = all_returns[-horizon:]
            mean = sum(window) / len(window)
            vol = (sum((r - mean) ** 2 for r in window) / max(1, len(window) - 1)) ** 0.5

            # Store in history
            self._vol_history[horizon].append(vol)

            # Percentile
            hist = self._vol_history[horizon]
            pct = sum(1 for v in hist if v <= vol) / max(1, len(hist))

            result[horizon] = {"current_vol": vol, "percentile": pct, "mean_hist": sum(hist) / max(1, len(hist))}

        return result


class VolCompressionDetector:
    """Ω-E65: Detect Bollinger squeeze / volatility contraction."""

    def __init__(self, squeeze_threshold: float = 0.02, window: int = 20) -> None:
        self._threshold = squeeze_threshold
        self._window = window
        self._prices: deque[float] = deque(maxlen=window * 2)

    def update(self, price: float) -> tuple[bool, float]:
        self._prices.append(price)
        if len(self._prices) < self._window:
            return False, 0.0

        window_prices = list(self._prices)[-self._window:]
        mean = sum(window_prices) / len(window_prices)
        vol = (sum((p - mean) ** 2 for p in window_prices) / len(window_prices)) ** 0.5
        squeeze = vol / mean < self._threshold if mean > 0 else False
        return squeeze, vol / mean if mean > 0 else 0.0


class VolRegimeTransitionPredictor:
    """Ω-E70: Predict vol regime transition via critical slowing down."""

    def __init__(self, window: int = 100) -> None:
        self._window = window
        self._vol_series: deque[float] = deque(maxlen=window)
        self._is_transitioning = False

    def update(self, current_vol: float) -> bool:
        self._vol_series.append(current_vol)
        if len(self._vol_series) < 40:
            return False

        vols = list(self._vol_series)
        first_half = vols[:len(vols) // 2]
        second_half = vols[len(vols) // 2:]

        mean1 = sum(first_half) / len(first_half)
        mean2 = sum(second_half) / len(second_half)

        std1 = (sum((x - mean1) ** 2 for x in first_half) / max(1, len(first_half) - 1)) ** 0.5
        std2 = (sum((x - mean2) ** 2 for x in second_half) / max(1, len(second_half) - 1)) ** 0.5

        # Increasing variance + increasing autocorrelation = transition
        variance_increasing = std2 > std1 * 1.5
        mean_shift = abs(mean2 - mean1) > mean1 * 0.3

        self._is_transitioning = variance_increasing or mean_shift
        return self._is_transitioning


# ──────────────────────────────────────────────────────────────
# Ω-E73 to Ω-E81: Trend & Momentum Signals
# ──────────────────────────────────────────────────────────────

class TrendStrengthIndex:
    """Ω-E73: R² of linear regression as trend strength measure."""

    def __init__(self, window: int = 100) -> None:
        self._prices: deque[float] = deque(maxlen=window)

    def update(self, price: float) -> tuple[float, float]:
        self._prices.append(price)
        n = len(self._prices)
        if n < 10:
            return 0.0, 0.0

        prices = list(self._prices)
        y_bar = sum(prices) / n
        x_bar = (n - 1) / 2
        ss_xy = sum((i - x_bar) * (prices[i] - y_bar) for i in range(n))
        ss_xx = sum((i - x_bar) ** 2 for i in range(n))
        ss_yy = sum((prices[i] - y_bar) ** 2 for i in range(n))

        if ss_xx == 0 or ss_yy == 0:
            return 0.0, 0.0

        r_squared = ss_xy ** 2 / (ss_xx * ss_yy)
        direction = 1.0 if ss_xy > 0 else -1.0
        return r_squared, direction


class DivergenceDetector:
    """Ω-E76: Divergences between price and indicators (RSI, MACD, volume)."""

    def __init__(self) -> None:
        self._price_highs: list[float] = []
        self._price_lows: list[float] = []
        self._indicator_highs: list[float] = []
        self._indicator_lows: list[float] = []

    def detect_bullish_divergence(
        self, price: float, indicator: float, is_swing_low: bool,
    ) -> bool:
        """Price makes lower low but indicator makes higher low."""
        if is_swing_low:
            self._price_lows.append(price)
            self._indicator_lows.append(indicator)

        if len(self._price_lows) >= 2:
            if self._price_lows[-1] < self._price_lows[-2] and self._indicator_lows[-1] > self._indicator_lows[-2]:
                return True
        return False

    def detect_bearish_divergence(
        self, price: float, indicator: float, is_swing_high: bool,
    ) -> bool:
        """Price makes higher high but indicator makes lower high."""
        if is_swing_high:
            self._price_highs.append(price)
            self._indicator_highs.append(indicator)

        if len(self._price_highs) >= 2:
            if self._price_highs[-1] > self._price_highs[-2] and self._indicator_highs[-1] < self._indicator_highs[-2]:
                return True
        return False


# ──────────────────────────────────────────────────────────────
# Ω-E82 to Ω-E90: Statistical Arbitrage Signals
# ──────────────────────────────────────────────────────────────

class CorrelationBreakdownDetector:
    """Ω-E82: Detect when historical correlations break."""

    def __init__(self, window: int = 100, threshold: float = 0.3) -> None:
        self._window = window
        self._threshold = threshold
        self._returns_a: deque[float] = deque(maxlen=window)
        self._returns_b: deque[float] = deque(maxlen=window)
        self._historical_corr: float | None = None

    def set_baseline_correlation(self, corr: float) -> None:
        self._historical_corr = corr

    def update(self, ret_a: float, ret_b: float) -> tuple[bool, float]:
        self._returns_a.append(ret_a)
        self._returns_b.append(ret_b)

        if len(self._returns_a) < 20:
            return False, 0.0

        # Rolling correlation
        corr = _compute_correlation(list(self._returns_a), list(self._returns_b))

        if self._historical_corr is not None and corr is not None:
            breakdown = abs(corr - self._historical_corr) > self._threshold
            return breakdown, corr
        return False, corr if corr is not None else 0.0


def _compute_correlation(x: list[float], y: list[float]) -> float | None:
    n = min(len(x), len(y))
    if n < 2:
        return None
    x = x[:n]
    y = y[:n]
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    cov = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n)) / (n - 1)
    std_x = (sum((xi - mean_x) ** 2 for xi in x) / (n - 1)) ** 0.5
    std_y = (sum((yi - mean_y) ** 2 for yi in y) / (n - 1)) ** 0.5
    if std_x == 0 or std_y == 0:
        return 0.0
    return cov / (std_x * std_y)


class BasisAnomalyDetector:
    """Ω-E86: Spot-perpetual basis anomalies."""

    def __init__(self, normal_range_bps: tuple[float, float] = (-10.0, 10.0)) -> None:
        self._normal_range = normal_range_bps
        self._basis_history: deque[float] = deque(maxlen=200)

    def update(self, spot_price: float, perp_price: float) -> tuple[bool, float]:
        basis_bps = (perp_price - spot_price) / spot_price * 10000 if spot_price > 0 else 0.0
        self._basis_history.append(basis_bps)

        is_anomaly = (basis_bps < self._normal_range[0] or basis_bps > self._normal_range[1])
        return is_anomaly, basis_bps


# ──────────────────────────────────────────────────────────────
# Ω-E91 to Ω-E99: Event-Driven Signals
# ──────────────────────────────────────────────────────────────

class LiquidationCascadePredictor:
    """Ω-E92: Predict cascade of liquidations."""

    def __init__(self) -> None:
        self._oi_changes: deque[float] = deque(maxlen=50)
        self._funding_history: deque[float] = deque(maxlen=50)

    def update(self, oi_change_pct: float, funding_rate: float, leverage_estimate: float) -> float:
        """Returns estimated probability of liquidation cascade [0, 1]."""
        self._oi_changes.append(oi_change_pct)
        self._funding_history.append(funding_rate)

        risk = 0.0
        if oi_change_pct > 5.0:
            risk += 0.2
        if abs(funding_rate) > 0.05:
            risk += 0.2
        if leverage_estimate > 10:
            risk += 0.3

        # Accelerating OI increase
        if len(self._oi_changes) >= 5:
            recent = list(self._oi_changes)[-5:]
            if all(r > 0 for r in recent):
                risk += 0.2

        return min(1.0, risk)


class SessionTransitionSignal:
    """Ω-E98: Signals from session transitions (Tokyo→London→NY)."""

    SESSIONS = {
        "tokyo": (0, 9),
        "london": (7, 16),
        "new_york": (13, 21),
    }

    @staticmethod
    def get_current_session(utc_hour: int) -> str:
        for name, (start, end) in SessionTransitionSignal.SESSIONS.items():
            if start <= utc_hour < end:
                return name
        return "off_hours"

    @staticmethod
    def is_transition(utc_hour: int) -> bool:
        """Hour 7 (Tokyo→London), 13 (London→NY), 21 (NY close) are transitions."""
        return utc_hour in (7, 13, 21)

    @staticmethod
    def get_session_characteristics(session: str) -> dict[str, Any]:
        profiles = {
            "tokyo": {"vol_multiplier": 0.6, "mean_reversion_favored": True, "trend_favored": False},
            "london": {"vol_multiplier": 1.2, "mean_reversion_favored": False, "trend_favored": True},
            "new_york": {"vol_multiplier": 1.0, "mean_reversion_favored": False, "trend_favored": True},
            "off_hours": {"vol_multiplier": 0.4, "mean_reversion_favored": True, "trend_favored": False},
        }
        return profiles.get(session, profiles["off_hours"])


# ──────────────────────────────────────────────────────────────
# Ω-E100 to Ω-E108: Network Science Signals
# ──────────────────────────────────────────────────────────────

class CorrelationNetworkBuilder:
    """Ω-E100: Dynamic correlation network between assets."""

    def __init__(self, window: int = 100, threshold: float = 0.7) -> None:
        self._window = window
        self._threshold = threshold
        self._asset_returns: dict[str, deque[float]] = {}
        self._edges: dict[str, dict[str, float]] = defaultdict(dict)

    def add_asset(self, name: str) -> None:
        if name not in self._asset_returns:
            self._asset_returns[name] = deque(maxlen=self._window)

    def update_returns(self, returns: dict[str, float]) -> dict[str, dict[str, float]]:
        for name, ret in returns.items():
            if name not in self._asset_returns:
                self.add_asset(name)
            self._asset_returns[name].append(ret)

        # Build correlation network
        assets = list(self._asset_returns.keys())
        self._edges.clear()
        for i in range(len(assets)):
            for j in range(i + 1, len(assets)):
                a, b = assets[i], assets[j]
                ra = list(self._asset_returns[a])
                rb = list(self._asset_returns[b])
                corr = _compute_correlation(ra, rb)
                if corr is not None and abs(corr) >= self._threshold:
                    self._edges[a][b] = corr
                    self._edges[b][a] = corr

        return dict(self._edges)

    def get_connected_components(self) -> list[set[str]]:
        """Ω-E102: Find clusters of correlated assets."""
        visited = set()
        components = []
        for node in list(self._edges.keys()):
            if node not in visited:
                component = set()
                queue = [node]
                while queue:
                    current = queue.pop(0)
                    if current not in visited:
                        visited.add(current)
                        component.add(current)
                        queue.extend(self._edges.get(current, {}).keys() - visited)
                if component:
                    components.append(component)
        return components


class InformationFlowTracker:
    """Ω-E106: Transfer entropy for directional information flow."""

    def __init__(self, window: int = 200, k: int = 3) -> None:
        self._window = window
        self._k = k  # lag depth
        self._series: dict[str, deque[float]] = {}

    def add_series(self, name: str) -> None:
        if name not in self._series:
            self._series[name] = deque(maxlen=self._window)

    def update(self, name: str, value: float) -> None:
        if name not in self._series:
            self.add_series(name)
        self._series[name].append(value)

    def transfer_entropy(self, source: str, target: str) -> float:
        """Estimate TE(source → target) via simple conditional MI."""
        if source not in self._series or target not in self._series:
            return 0.0
        s = list(self._series[source])
        t = list(self._series[target])
        n = min(len(s), len(t)) - self._k
        if n < self._k + 5:
            return 0.0

        # Simplified: correlation of lagged source with target
        source_lagged = s[self._k:n + self._k]
        target_current = t[self._k:n + self._k]

        corr = _compute_correlation(source_lagged, target_current)
        if corr is None:
            return 0.0
        return max(0.0, corr ** 2)  # R² as simplified TE estimate
