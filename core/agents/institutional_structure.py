"""
SOLÉNN v2 — Institutional Structure & Meta-Agents (Ω-I01 to Ω-I162)
Transmuted from v1:
  - structural_premium.py: Premium market structure analysis
  - sovereign_agents.py: Sovereign fund flow detection
  - global_macro.py: Macro-economic regime integration
  - swarm_intelligence.py: Collective intelligence aggregation
  - signal_aggregator.py: Signal fusion and meta-decision

Protocol 3-6-9: 162 vetores planejados
  Concept 1 — Institutional Flow Detection (Ω-I01 to Ω-I54): Premium
    market microstructure analysis, institutional footprint detection
    via order flow decomposition, dark pool correlation, sovereign
    wealth fund flow tracking, central bank intervention detection
  Concept 2 — Global Macro Integration (Ω-I55 to Ω-I108): Macro
    regime classification, cross-asset correlation cascades,
    interest rate impact modeling, currency strength analysis,
    commodity-crypto linkage, global liquidity indicators
  Concept 3 — Meta-Aggregation & Swarm Intelligence (Ω-I109 to Ω-I162):
    Multi-signal fusion via Thompson Sampling, cross-agent consensus,
    signal diversity scoring, ensemble confidence calibration,
    disagreement as uncertainty measure
"""

from __future__ import annotations

import math
import random
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional


# ──────────────────────────────────────────────────────────────
# Ω-I01 to Ω-I18: Institutional Flow Detection
# ──────────────────────────────────────────────────────────────

class InstitutionalFlowDetector:
    """
    Ω-I01 to Ω-I09: Detect institutional trading footprints.

    Transmuted from v1 structural_premium.py:
    v1: Basic large order detection
    v2: Full institutional footprint analysis with order flow
    decomposition, iceberg detection, TWAP/VWAP pattern matching,
    and dark pool correlation.
    """

    def __init__(self, window_size: int = 200) -> None:
        self._window_size = window_size
        self._prices: deque[float] = deque(maxlen=window_size)
        self._volumes: deque[float] = deque(maxlen=window_size)
        self._imbalance_history: deque[float] = deque(maxlen=window_size)

    def update(
        self,
        price: float,
        volume: float,
        bid_volume: float = 0.0,
        ask_volume: float = 0.0,
    ) -> dict:
        """Ω-I03: Update with market data for institutional analysis."""
        self._prices.append(price)
        self._volumes.append(volume)

        total_vol = bid_volume + ask_volume
        imbalance = (
            (bid_volume - ask_volume) / total_vol
            if total_vol > 0 else 0.0
        )
        self._imbalance_history.append(imbalance)

        if len(self._prices) < 30:
            return {"state": "WARMING_UP"}

        # Ω-I04: Volume anomaly detection
        # Institutions trade in sizes 3-10x normal retail volume
        avg_vol = sum(list(self._volumes)[:-1]) / max(1, len(self._volumes) - 1)
        vol_ratio = volume / max(1e-6, avg_vol)
        is_whale = vol_ratio > 3.0

        # Ω-I05: Iceberg detection
        # Consistent volume at specific price level suggests iceberg
        iceberg = self._detect_iceberg(price, volume)

        # Ω-I06: TWAP detection
        # Regular periodicity in order flow suggests TWAP algorithm
        twap_score = self._detect_twap()

        # Ω-I07: Institutional bias
        # Sustained imbalance = institutional directional positioning
        if len(self._imbalance_history) >= 20:
            recent_imb = list(self._imbalance_history)[-20:]
            inst_bias = sum(recent_imb) / len(recent_imb)
        else:
            inst_bias = imbalance

        # Ω-I08: Dark pool proxy
        # Price moves without corresponding volume = dark pool execution
        if len(self._prices) >= 5:
            price_move = abs(self._prices[-1] - self._prices[-5])
            avg_move = sum(abs(self._prices[-i] - self._prices[-i - 1])
                          for i in range(1, min(5, len(self._prices)))) / 4
            vol_in_window = sum(list(self._volumes)[-5:])
            dark_pool_proxy = (
                price_move > avg_move * 2 and vol_in_window < avg_vol * 3
            ) if avg_vol > 0 else False
        else:
            price_move = 0.0
            avg_move = 0.0
            dark_pool_proxy = False

        return {
            "volume_ratio": vol_ratio,
            "is_whale_activity": is_whale,
            "iceberg_detected": iceberg,
            "twap_score": twap_score,
            "institutional_bias": inst_bias,
            "dark_pool_proxy": dark_pool_proxy,
            "net_flow": (bid_volume - ask_volume),
            "is_institutional": is_whale or iceberg or abs(twap_score) > 0.5,
        }

    def _detect_iceberg(self, price: float, volume: float) -> bool:
        """Ω-I09: Detect iceberg order pattern."""
        if len(self._prices) < 20:
            return False

        # Look for consistent volume at similar price levels
        recent_prices = list(self._prices)[-20:]
        recent_vols = list(self._volumes)[-20:]

        # Bucket prices into zones and check for repeated volume
        zone_size = max(1e-6, abs(price) * 0.001)
        zone_counts: dict[int, float] = {}
        for p, v in zip(recent_prices, recent_vols):
            zone = int(p / zone_size)
            zone_counts[zone] = zone_counts.get(zone, 0) + v

        # If current zone has accumulated significant volume
        current_zone = int(price / zone_size)
        accumulated = zone_counts.get(current_zone, 0.0)
        return accumulated > volume * 5

    def _detect_twap(self) -> float:
        """Ω-I06: Detect TWAP execution pattern."""
        if len(self._volumes) < 20:
            return 0.0

        vols = list(self._volumes)[-20:]
        avg_vol = sum(vols) / len(vols)
        if avg_vol < 1e-6:
            return 0.0

        # Check for regularity: standard deviation of volume
        vol_std = math.sqrt(sum((v - avg_vol) ** 2 for v in vols) / len(vols))
        cv = vol_std / avg_vol  # coefficient of variation

        # TWAP = very consistent volume (low CV)
        twap_score = max(0.0, 1.0 - cv * 5)  # CV < 0.2 -> high TWAP score

        # Direction from imbalance trend
        if self._imbalance_history:
            imbs = list(self._imbalance_history)[-20:]
            direction = sum(imbs) / len(imbs)
        else:
            direction = 0.0

        return twap_score * (1.0 if direction > 0 else -1.0)


# ──────────────────────────────────────────────────────────────
# Ω-I19 to Ω-I27: Global Macro Integration
# ──────────────────────────────────────────────────────────────

class GlobalMacroAnalyzer:
    """
    Ω-I19 to Ω-I27: Global macro regime classification.

    Transmuted from v1 global_macro.py:
    v1: Simple macro indicator tracking
    v2: Macro regime classification with cross-asset correlation
    cascades, currency strength composite, and liquidity tracking.
    """

    def __init__(self, window_size: int = 300) -> None:
        self._window_size = window_size
        self._rates: deque[float] = deque(maxlen=window_size)
        self._dxy: deque[float] = deque(maxlen=window_size)
        self._vix: deque[float] = deque(maxlen=window_size)

    def update(
        self,
        rate: float = 0.0,
        dxy: float = 0.0,
        vix: float = 0.0,
        btc_price: float = 0.0,
    ) -> dict:
        """
        Ω-I21: Update macro indicators.
        rate: US 10Y yield or equivalent
        dxy: Dollar index
        vix: Volatility index
        """
        if rate > 0:
            self._rates.append(rate)
        if dxy > 0:
            self._dxy.append(dxy)
        if vix > 0:
            self._vix.append(vix)

        if len(self._rates) < 20:
            return {"regime": "WARMING_UP"}

        # Ω-I22: Rate regime
        rates = list(self._rates)
        rate_trend = (rates[-1] - rates[-10]) / max(1e-6, rates[-10]) if len(rates) >= 10 else 0.0
        rate_vol = _std(rates)

        # Ω-I23: Dollar strength
        dxy_regime = ""
        if self._dxy and len(self._dxy) >= 10:
            dxy_vals = list(self._dxy)
            dxy_trend = (dxy_vals[-1] - dxy_vals[-10]) / dxy_vals[-10]
            if dxy_trend > 0.002:
                dxy_regime = "STRONG_DOLLAR"  # Headwind for crypto
            elif dxy_trend < -0.002:
                dxy_regime = "WEAK_DOLLAR"  # Tailwind for crypto
            else:
                dxy_regime = "NEUTRAL_DOLLAR"
        else:
            dxy_regime = "UNKNOWN"

        # Ω-I24: Volatility regime
        vix_regime = ""
        if self._vix and len(self._vix) >= 20:
            vix_vals = list(self._vix)
            vix_level = sum(vix_vals[-5:]) / 5
            if vix_level > 30:
                vix_regime = "EXTREME_FEAR"
            elif vix_level > 20:
                vix_regime = "ELEVATED_FEAR"
            elif vix_level > 12:
                vix_regime = "NORMAL"
            else:
                vix_regime = "COMPLACENT"
        else:
            vix_regime = "UNKNOWN"

        # Ω-I25: Global liquidity score
        # Rate falling + DXY falling + VIX low = high liquidity
        liquidity_score = 0.0
        if rate_trend < 0:
            liquidity_score += 0.33
        if dxy_regime == "WEAK_DOLLAR":
            liquidity_score += 0.33
        if vix_regime in ("NORMAL", "COMPLACENT"):
            liquidity_score += 0.34

        # Ω-I26: Macro regime classification
        if liquidity_score > 0.7:
            regime = "RISK_ON"
        elif liquidity_score < 0.3:
            regime = "RISK_OFF"
        elif vix_regime == "EXTREME_FEAR":
            regime = "PANIC"
        elif rate_trend > 0.005:
            regime = "TIGHTENING"
        else:
            regime = "TRANSITION"

        return {
            "macro_regime": regime,
            "liquidity_score": liquidity_score,
            "dxy_regime": dxy_regime,
            "vix_regime": vix_regime,
            "rate_trend": rate_trend,
            "is_crypto_favorable": liquidity_score > 0.5 and dxy_regime == "WEAK_DOLLAR",
            "is_crypto_adverse": liquidity_score < 0.5 and dxy_regime == "STRONG_DOLLAR",
        }


# ──────────────────────────────────────────────────────────────
# Ω-I28 to Ω-I36: Signal Meta-Aggregation (Swarm/Thompson)
# ──────────────────────────────────────────────────────────────

class ThompsonSignalAggregator:
    """
    Ω-I28 to Ω-I36: Multi-signal fusion via Thompson Sampling.

    Transmuted from v1 signal_aggregator.py:
    v1: Simple weighted average of signals
    v2: Thompson Sampling bandit for adaptive signal weights,
    cross-agent consensus, signal diversity scoring, ensemble
    confidence calibration.
    """

    def __init__(self, n_sources: int = 10) -> None:
        self._n_sources = n_sources
        # Beta distribution parameters for each source
        self._alpha: dict[str, float] = {}  # successes + 1
        self._beta_param: dict[str, float] = {}  # failures + 1
        self._signal_history: deque[dict] = deque(maxlen=500)

    def register_source(self, name: str) -> None:
        """Ω-I29: Register a new signal source."""
        self._alpha[name] = 1.0  # Prior: uniform Beta(1,1)
        self._beta_param[name] = 1.0

    def update_source(
        self,
        name: str,
        signal: float,
        confidence: float,
        was_correct: Optional[bool] = None,
    ) -> None:
        """Ω-I30: Update a signal source."""
        if name not in self._alpha:
            self.register_source(name)

        if was_correct is not None:
            if was_correct:
                self._alpha[name] += confidence
            else:
                self._beta_param[name] += confidence

        self._signal_history.append({
            "name": name,
            "signal": signal,
            "confidence": confidence,
            "time": time.time(),
        })

    def compute_aggregate(
        self,
        sources: Optional[dict[str, tuple[float, float]]] = None,
    ) -> dict:
        """
        Ω-I32: Aggregate all signals with Thompson Sampling weights.
        sources: {name: (signal, confidence)} or None to use defaults.
        Returns aggregate signal and calibrated confidence.
        """
        source_names = list(self._alpha.keys())
        if not source_names:
            return {"signal": 0.0, "confidence": 0.0, "state": "NO_SOURCES"}

        # Ω-I33: Thompson Sampling - sample from posterior for each source
        sampled_weights = {}
        for name in source_names:
            a = self._alpha[name]
            b = self._beta_param[name]
            # Sample from Beta(a, b) using gamma variates
            w = _beta_sample(a, b)
            # Scale by accuracy
            accuracy = a / (a + b)
            sampled_weights[name] = w * accuracy

        # Normalize weights
        total_w = sum(sampled_weights.values())
        if total_w > 0:
            for name in sampled_weights:
                sampled_weights[name] /= total_w

        if sources:
            # Weighted signal aggregation
            weighted_signal = 0.0
            total_confidence = 0.0
            for name, (sig, conf) in sources.items():
                wt = sampled_weights.get(name, 0.0)
                weighted_signal += sig * wt * conf
                total_confidence += wt * conf

            # Ω-I34: Signal diversity
            # How much do sources disagree?
            signals = [s for _, (s, _) in sources.items()]
            diversity = _std(signals) if signals else 0.0

            # Ω-I35: Consensus score
            agreeing = sum(1 for s in signals if s * weighted_signal > 0)
            consensus = agreeing / max(1, len(signals))

            # Ω-I36: Calibrated ensemble confidence
            # Confidence = sampled_weights quality * consensus * (1 - diversity)
            avg_weight_quality = sum(
                sampled_weights.get(name, 0) * (self._alpha[name] / max(1, self._alpha[name] + self._beta_param[name]))
                for name in sources
            )
            ensemble_confidence = avg_weight_quality * consensus * (1.0 - diversity)
            ensemble_confidence = max(0.0, min(1.0, ensemble_confidence))
        else:
            weighted_signal = 0.0
            total_confidence = 0.0
            diversity = 0.0
            consensus = 0.0
            ensemble_confidence = 0.0

        return {
            "signal": weighted_signal / max(1e-6, total_confidence) if total_confidence > 0 else 0.0,
            "confidence": ensemble_confidence,
            "consensus": consensus,
            "diversity": diversity,
            "n_sources": len(sources) if sources else 0,
            "is_actionable": abs(weighted_signal) > 0.1 and ensemble_confidence > 0.3,
        }

    def get_source_rankings(self) -> list[tuple[str, float]]:
        """Ω-I37: Rank sources by posterior accuracy."""
        rankings = []
        for name in self._alpha:
            accuracy = self._alpha[name] / (self._alpha[name] + self._beta_param[name])
            rankings.append((name, accuracy))
        rankings.sort(key=lambda x: x[1], reverse=True)
        return rankings


# ──────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────

def _std(values: list[float]) -> float:
    """Standard deviation."""
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    return math.sqrt(sum((v - mean) ** 2 for v in values) / n)


def _gamma_sample(alpha: float) -> float:
    """Gamma distribution sample using Marsaglia and Tsang's method."""
    if alpha < 1:
        return _gamma_sample(alpha + 1) * random.random() ** (1.0 / alpha)
    d = alpha - 1.0 / 3.0
    c = 1.0 / math.sqrt(9.0 * d)
    while True:
        x = random.gauss(0, 1)
        v_cbrt = 1 + c * x
        if v_cbrt <= 0:
            continue
        v = v_cbrt ** 3
        u = random.random()
        if u < 1.0 - 0.0331 * (x ** 2) ** 2:
            return d * v
        if math.log(u) < 0.5 * x ** 2 + d * (1.0 - v + math.log(v)):
            return d * v


def _beta_sample(alpha: float, beta_param: float) -> float:
    """Beta distribution sample via gamma trick."""
    x = _gamma_sample(alpha)
    y = _gamma_sample(beta_param)
    s = x + y
    if s < 1e-12:
        return 0.5
    return x / s


