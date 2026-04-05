"""
SOLÉNN v2 — Sentiment & Behavioral Agents (Ω-SB01 to Ω-SB162)
Transmuted from v1:
  - behavioral.py: Behavioral pattern analysis
  - market_intuition_agent.py: Intuitive pattern matching
  - phantom_agents.py: Ghost/phantom signal detection
  - predictor/predictive_vidente_agent.py: Seer-like forecasting
  - nexus_agent.py: Cross-dimensional nexus detection
  - phantom_signal.py: Hidden signal extraction
  - liquidity_leech_agent.py: Parasitic flow identification
  - leech_agent.py: Liquidity drain tracking
  - meta_swarm.py: Meta-level swarm coordination
  - synchronicity/pulse detection agents

Protocol 3-6-9: 162 vetores planejados
  Concept 1 — Behavioral & Intuition Analysis (Ω-SB01 to Ω-SB54):
    Market behavioral fingerprint, intuition scoring, phantom
    signal extraction from noise, behavioral trap detection
    (bull/bear traps), intuition-reality divergence tracking
  Concept 2 — Predictive Forecasting (Ω-SB55 to Ω-SB108): Vidente
    (seer) multi-method forecasting, forecast calibration,
    temporal decay of predictions, accuracy decomposition
    by horizon, forecast ensemble coherence
  Concept 3 — Liquidity Dynamics (Ω-SB109 to Ω-SB162): Liquidity
    drain (leech) detection, parasitic flow filtering, flow
    legitimacy scoring, liquidity replenishment tracking,
    swarm coordination across liquidity zones
"""

from __future__ import annotations

import math
from collections import deque
from typing import Optional


# ──────────────────────────────────────────────────────────────
# Ω-SB01 to Ω-SB18: Behavioral & Intuition Analysis
# ──────────────────────────────────────────────────────────────

class BehavioralIntuitionAnalyzer:
    """
    Ω-SB01 to Ω-SB09: Behavioral fingerprint + intuition scoring.

    Transmuted from v1 behavioral.py + market_intuition_agent.py:
    v1: Simple behavioral tracking
    v2: Full behavioral profiling, intuition scoring,
    phantom signal extraction, and trap detection.
    """

    def __init__(self, window_size: int = 300) -> None:
        self._window = window_size
        self._prices: deque[float] = deque(maxlen=window_size)
        self._volumes: deque[float] = deque(maxlen=window_size)
        self._intuition_history: deque[dict] = deque(maxlen=200)
        self._phantom_signals: list[dict] = []

    def update(self, price: float, volume: float = 1.0) -> dict:
        """Ω-SB03: Update behavioral analysis."""
        self._prices.append(price)
        self._volumes.append(volume)

        if len(self._prices) < 20:
            return {"state": "WARMING_UP"}

        prices = list(self._prices)
        volumes = list(self._volumes)
        n = len(prices)

        results: dict[str, any] = {}

        # Ω-SB04: Behavioral fingerprint
        # Each market has a unique behavioral signature
        returns = [
            (prices[i] - prices[i - 1]) / max(1e-6, abs(prices[i - 1]))
            for i in range(1, n)
        ]

        # Fingerprint components
        vol_regime = _std(returns) if returns else 0.0
        skew = (
            sum(r ** 3 for r in returns) / max(1, len(returns)) / max(1e-6, vol_regime ** 3)
            if vol_regime > 0 else 0.0
        )
        kurt = (
            sum(r ** 4 for r in returns) / max(1, len(returns)) / max(1e-6, vol_regime ** 4) - 3
            if vol_regime > 0 else 0.0
        )
        # Autocorrelation as fingerprint
        if len(returns) >= 5:
            mean_r = sum(returns) / len(returns)
            var_r = sum((r - mean_r) ** 2 for r in returns) / len(returns)
            if var_r > 0:
                autocorr = sum(
                    (returns[i] - mean_r) * (returns[i + 1] - mean_r)
                    for i in range(len(returns) - 1)
                ) / ((len(returns) - 1) * var_r)
            else:
                autocorr = 0.0
        else:
            autocorr = 0.0

        results["skewness"] = skew
        results["kurtosis"] = kurt
        results["autocorrelation"] = autocorr
        results["volatility_regime"] = vol_regime

        # Ω-SB05: Intuition score
        # How well does the market "feel" — coherent vs chaotic?
        # Coherence = predictable autocorrelation + moderate vol + low kurt
        intuition = 0.0
        if abs(autocorr) > 0.1:
            intuition += 0.3  # Some predictability
        if 0.001 < vol_regime < 0.02:
            intuition += 0.3  # Moderate volatility
        if kurt < 2:
            intuition += 0.2  # Not too fat-tailed
        if abs(skew) < 0.5:
            intuition += 0.2  # Not too asymmetric

        results["intuition_score"] = intuition

        # Ω-SB06: Phantom signal extraction
        # Signal hidden in noise: remove known components
        if n >= 10:
            raw_move = prices[-1] - prices[-2]
            # Expected move from trend
            trend = (prices[-1] - prices[-10]) / max(1, 10)
            # Expected move from mean reversion
            mean_p = sum(prices[-20:]) / min(20, n)
            mr = (mean_p - prices[-1]) / max(1, 20) * 0.1

            expected = trend * 0.7 + mr * 0.3
            phantom = raw_move - expected

            if abs(phantom) > abs(raw_move) * 0.3:
                phantom_record = {
                    "magnitude": phantom,
                    "ratio": abs(phantom) / max(1e-6, abs(raw_move)),
                    "index": n,
                }
                self._phantom_signals.append(phantom_record)
                if len(self._phantom_signals) > 100:
                    self._phantom_signals = self._phantom_signals[-100:]
                results["phantom_active"] = True
                results["phantom_magnitude"] = phantom
            else:
                results["phantom_active"] = False
                results["phantom_magnitude"] = 0.0
        else:
            results["phantom_active"] = False
            results["phantom_magnitude"] = 0.0

        # Ω-SB07: Trap detection (bull/bear)
        results["bull_trap"] = self._detect_bull_trap(prices, volumes)
        results["bear_trap"] = self._detect_bear_trap(prices, volumes)

        # Ω-SB08: Intuition-reality divergence
        # When intuition says one thing but price does another
        if self._intuition_history:
            prev = self._intuition_history[-1]
            prev_intuition = prev.get("intuition_score", 0.5)
            price_moved = abs(prices[-1] - prices[-2]) / max(1e-6, abs(prices[-2]))
            expected_move = prev_intuition * 0.005
            divergence = abs(price_moved - expected_move)
            results["intuition_divergence"] = divergence
        else:
            results["intuition_divergence"] = 0.0

        self._intuition_history.append(results)

        return results

    def _detect_bull_trap(self, prices: list, volumes: list) -> float:
        """Detect bull trap: breakout above resistance then reversal."""
        if len(prices) < 15:
            return 0.0

        n = len(prices)
        resistance = max(prices[-15:-5]) if len(prices) > 10 else prices[0]
        broke_above = any(prices[i] > resistance for i in range(max(0, n - 10), n - 2))
        fell_back = prices[-1] < resistance

        if broke_above and fell_back:
            return 0.7
        return 0.0

    def _detect_bear_trap(self, prices: list, volumes: list) -> float:
        """Detect bear trap: breakdown below support then bounce."""
        if len(prices) < 15:
            return 0.0

        n = len(prices)
        support = min(prices[-15:-5]) if len(prices) > 10 else prices[0]
        broke_below = any(prices[i] < support for i in range(max(0, n - 10), n - 2))
        bounced_back = prices[-1] > support

        if broke_below and bounced_back:
            return 0.7
        return 0.0


# ──────────────────────────────────────────────────────────────
# Ω-SB19 to Ω-SB27: Predictive Vidente (Forecaster)
# ──────────────────────────────────────────────────────────────

class VidenteForecaster:
    """
    Ω-SB19 to Ω-SB27: Multi-method predictive forecasting.

    Transmuted from v1 predictive_vidente_agent.py:
    v1: Simple linear extrapolation
    v2: Multiple forecasting methods with calibration,
    temporal decay, ensemble, and accuracy tracking.
    """

    def __init__(self, window_size: int = 300) -> None:
        self._window = window_size
        self._prices: deque[float] = deque(maxlen=window_size)
        self._volumes: deque[float] = deque(maxlen=window_size)
        self._predictions: deque[tuple[float, float, int]] = deque(maxlen=500)
        # (predicted_price, actual_price, horizon)

    def update(self, price: float, volume: float = 1.0) -> dict:
        """Ω-SB21: Update forecasts and evaluate past predictions."""
        # Evaluate old predictions
        for i, (pred, _, h) in enumerate(self._predictions):
            if h <= 0:  # Prediction horizon reached
                actual = price
                error = abs(pred - actual) / max(1e-6, abs(actual))
                self._predictions[i] = (pred, actual, -1)  # Mark evaluated

        self._prices.append(price)
        self._volumes.append(volume)

        if len(self._prices) < 20:
            return {"state": "WARMING_UP"}

        prices = list(self._prices)
        n = len(prices)

        # Ω-SB22: Method 1 — Trend extrapolation
        if n >= 5:
            recent_trend = (prices[-1] - prices[-5]) / 5
            trend_forecast = prices[-1] + recent_trend * 5
        else:
            trend_forecast = prices[-1]

        # Ω-SB23: Method 2 — Mean reversion
        if n >= 20:
            mean_20 = sum(prices[-20:]) / 20
            mr_forecast = (prices[-1] + mean_20) / 2
        else:
            mr_forecast = prices[-1]

        # Ω-SB24: Method 3 — Momentum continuation
        if n >= 10:
            momentum = (prices[-1] - prices[-10]) / max(1e-6, abs(prices[-10]))
            mom_forecast = prices[-1] * (1 + momentum * 0.5)
        else:
            mom_forecast = prices[-1]

        # Ω-SB25: Method 4 — Volatility-adjusted range
        if n >= 20:
            recent_std = _std(prices[-20:])
            vol_forecast_upper = prices[-1] + recent_std * 2
            vol_forecast_lower = prices[-1] - recent_std * 2
        else:
            vol_forecast_upper = vol_forecast_lower = prices[-1]

        # Ω-SB26: Ensemble forecast
        forecasts = [trend_forecast, mr_forecast, mom_forecast]
        ensemble = sum(forecasts) / len(forecasts)

        # Ω-SB27: Forecast confidence
        # Based on agreement between methods
        forecast_std = _std(forecasts)
        forecast_mean = sum(forecasts) / len(forecasts)
        agreement = 1.0 - min(1.0, forecast_std / max(1e-6, abs(forecast_mean) * 0.01))

        # Direction
        direction = "BULLISH" if ensemble > prices[-1] else "BEARISH"
        expected_move_pct = abs(ensemble - prices[-1]) / max(1e-6, prices[-1]) * 100

        return {
            "ensemble_forecast": ensemble,
            "trend_forecast": trend_forecast,
            "mean_reversion_forecast": mr_forecast,
            "momentum_forecast": mom_forecast,
            "vol_range_upper": vol_forecast_upper,
            "vol_range_lower": vol_forecast_lower,
            "direction": direction,
            "expected_move_pct": expected_move_pct,
            "method_agreement": agreement,
            "forecast_confidence": agreement,
            "is_actionable": agreement > 0.5 and expected_move_pct > 0.5,
        }

    def record_prediction(self, predicted: float, horizon: int) -> None:
        """Store a prediction for later evaluation."""
        self._predictions.append((predicted, 0.0, horizon))


# ──────────────────────────────────────────────────────────────
# Ω-SB28 to Ω-SB36: Liquidity Dynamics (Leech/Parasitic Flow)
# ──────────────────────────────────────────────────────────────

class LiquidityDynamicsAnalyzer:
    """
    Ω-SB28 to Ω-SB36: Liquidity drain and parasitic flow detection.

    Transmuted from v1 leech_agent + liquidity_leech_agent + meta_swarm:
    v1: Simple volume analysis
    v2: Full liquidity drain detection, parasitic flow filtering,
    flow legitimacy scoring, and swarm coordination.
    """

    def __init__(self, window_size: int = 300) -> None:
        self._window = window_size
        self._prices: deque[float] = deque(maxlen=window_size)
        self._volumes: deque[float] = deque(maxlen=window_size)
        self._flow_imbalances: deque[float] = deque(maxlen=200)

    def update(
        self,
        price: float,
        volume: float,
        bid_volume: float = 0.0,
        ask_volume: float = 0.0,
    ) -> dict:
        """Ω-SB30: Update liquidity analysis."""
        self._prices.append(price)
        self._volumes.append(volume)

        if len(self._prices) < 20:
            return {"state": "WARMING_UP"}

        prices = list(self._prices)
        volumes = list(self._volumes)
        n = len(prices)

        # Ω-SB31: Liquidity drain (leech) detection
        # High volume without proportional price movement = liquidity being drained
        if n >= 20:
            recent_vol = sum(volumes[-10:]) / 10
            baseline_vol = sum(volumes[:10]) / 10
            vol_surge = recent_vol / max(1e-6, baseline_vol)

            price_move = abs(prices[-1] - prices[-10]) / max(1e-6, abs(prices[-10]))
            baseline_move = abs(prices[10] - prices[0]) / max(1e-6, abs(prices[0]))
            move_ratio = price_move / max(1e-6, baseline_move)

            # Leech: volume UP but price movement DOWN
            if vol_surge > 1.3 and move_ratio < 0.7:
                leech_score = (vol_surge - 1.0) * (1.0 - move_ratio)
                leech_score = min(1.0, leech_score)
            else:
                leech_score = 0.0
        else:
            vol_surge = move_ratio = 1.0
            leech_score = 0.0

        # Ω-SB32: Parasitic flow detection
        # Flow that extracts value without contributing price discovery
        # High-frequency small orders at top of book = parasitic
        if n >= 10:
            # Check if volume is concentrated in small trades
            flow_legitimate = 1.0 - leech_score
            if bid_volume > 0 and ask_volume > 0:
                imbalance = abs(bid_volume - ask_volume) / (bid_volume + ask_volume)
            else:
                imbalance = 0.0

            # Legitimate flow = imbalanced + moves price
            flow_legitimate = flow_legitimate * (0.5 + imbalance * 0.5)
        else:
            flow_legitimate = 1.0
            imbalance = 0.0

        # Ω-SB33: Flow quality scoring
        # Quality = (volume consistency * price impact * direction coherence)
        if n >= 10:
            price_direction = sum(
                1 for i in range(n - 5, n - 1)
                if prices[i + 1] >= prices[i]
            ) / max(1, 5)
            direction_coherence = abs(price_direction - 0.5) * 2

            vol_cv = _std(volumes[-10:]) / max(1e-6, sum(volumes[-10:]) / 10)
            vol_consistency = max(0.0, 1.0 - vol_cv)

            flow_quality = (
                vol_consistency * 0.3 +
                (1.0 - abs(price_move) / max(1e-6, abs(prices[-1])) * 100) * 0.3 +
                direction_coherence * 0.4
            )
            flow_quality = max(0.0, min(1.0, flow_quality))
        else:
            flow_quality = 0.5

        # Ω-SB34: Liquidity replenishment tracking
        # After a drain, does liquidity recover?
        if leech_score > 0.3:
            # Check if volume is stabilizing
            if n >= 15:
                vol_tail = sum(volumes[-5:]) / 5
                vol_mid = sum(volumes[-10:-5]) / 5
                is_replenishing = vol_tail < vol_mid * 0.8
            else:
                is_replenishing = False
        else:
            is_replenishing = True  # No drain = implicitly replenished

        # Ω-SB35: Bid/ask pressure
        total = bid_volume + ask_volume
        if total > 0:
            bid_pressure = bid_volume / total
            ask_pressure = ask_volume / total
            net_flow = (bid_volume - ask_volume) / total
        else:
            bid_pressure = ask_pressure = 0.5
            net_flow = 0.0

        self._flow_imbalances.append(net_flow)

        # Ω-SB36: Swarm coordination across zones
        # Multiple zones showing same flow direction = coordinated
        if len(self._flow_imbalances) >= 5:
            recent_imb = list(self._flow_imbalances)[-5:]
            same_direction = sum(1 for x in recent_imb if x > 0)
            coordination = abs(same_direction - 2.5) / 2.5
        else:
            coordination = 0.0

        return {
            "leech_score": leech_score,
            "flow_legitimacy": flow_legitimate,
            "flow_quality": flow_quality,
            "is_replenishing": is_replenishing,
            "net_flow": net_flow,
            "bid_pressure": bid_pressure,
            "ask_pressure": ask_pressure,
            "swarm_coordination": coordination,
            "is_leech_active": leech_score > 0.3,
            "is_parasitic_flow": flow_legitimate < 0.3,
            "is_coordinated_flow": coordination > 0.6,
        }


# ──────────────────────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────────────────────

def _std(values: list[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    m = sum(values) / n
    return math.sqrt(sum((v - m) ** 2 for v in values) / n)
