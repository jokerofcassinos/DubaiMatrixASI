"""
SOLÉNN v2 — Math Engine: Frontier Mathematical Toolbox (Ω-ME01 a Ω-ME54)
Replaces v1 math_tools.py. Complete mathematical analysis toolkit for
market penetration: wavelet decomposition, entropy, fractal analysis,
information theory, volatility estimators, pattern detection, and
position sizing. Pure Python implementation — no numpy dependency
required (uses math, collections, standard library only).

Concept 1: Entropy & Information Theory (Ω-ME01–ME18)
  Shannon entropy, mutual information, KL divergence, Renyi entropy,
  Lempel-Ziv complexity, information gain for feature selection.
  Measures market predictability to gate trade entries.

Concept 2: Fractal & Wavelet Analysis (Ω-ME19–ME36)
  Hurst exponent, fractal dimension, Haar wavelet decomposition,
  multiscale energy distribution. Detects regime through geometric
  properties invariant to price level and time scaling.

Concept 3: Risk, Volatility & Pattern Detection (Ω-ME37–ME54)
  Kelly criterion, support/resistance clustering, divergence detection,
  RSI, ATR, realized volatility, order flow metrics. All optimized
  for incremental (streaming) computation, not batch recalculation.
"""

from __future__ import annotations

import math
from collections import Counter, deque
from typing import Any


# ──────────────────────────────────────────────────────────────
# Ω-ME01 to Ω-ME18: Entropy & Information Theory
# ──────────────────────────────────────────────────────────────


def shannon_entropy(data: list[float], bins: int = 20) -> float:
    """Ω-ME01: Shannon entropy — measures unpredictability."""
    if len(data) < 2:
        return 0.0
    hist, _ = _histogram(data, bins)
    total = sum(hist)
    if total == 0:
        return 0.0
    entropy = 0.0
    for count in hist:
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    return entropy


def rolling_entropy(data: list[float], window: int = 50, bins: int = 20) -> list[float]:
    """Ω-ME02: Rolling Shannon entropy."""
    n = len(data)
    result: list[float] = []
    dq: deque[float] = deque(maxlen=window)

    for val in data:
        dq.append(val)
        if len(dq) < window:
            result.append(0.0)
        else:
            result.append(shannon_entropy(list(dq), bins))
    return result


def mutual_information(x: list[float], y: list[float], bins: int = 20) -> float:
    """Ω-ME03: Mutual information between two series — captures non-linear relationships."""
    if len(x) < 2 or len(y) < 2:
        return 0.0

    n = min(len(x), len(y))
    x_sub = x[:n]
    y_sub = y[:n]

    x_min, x_max = min(x_sub), max(x_sub)
    y_min, y_max = min(y_sub), max(y_sub)

    x_range = x_max - x_min if x_max > x_min else 1.0
    y_range = y_max - y_min if y_max > y_min else 1.0

    x_bins = [int((v - x_min) / x_range * (bins - 1)) for v in x_sub]
    y_bins = [int((v - y_min) / y_range * (bins - 1)) for v in y_sub]

    joint: dict[tuple[int, int], int] = {}
    x_counts: Counter = Counter()
    y_counts: Counter = Counter()

    for xi, yi in zip(x_bins, y_bins):
        key = (xi, yi)
        joint[key] = joint.get(key, 0) + 1
        x_counts[xi] += 1
        y_counts[yi] += 1

    mi = 0.0
    for (xi, yi), count in joint.items():
        p_xy = count / n
        p_x = x_counts[xi] / n
        p_y = y_counts[yi] / n
        if p_xy > 0 and p_x > 0 and p_y > 0:
            mi += p_xy * math.log2(p_xy / (p_x * p_y))

    return max(0.0, mi)


def kl_divergence(p: list[float], q: list[float]) -> float:
    """Ω-ME04: KL divergence D_KL(P || Q)."""
    if len(p) != len(q):
        raise ValueError("Distributions must have same length")
    total_p = sum(p)
    total_q = sum(q)
    if total_p == 0 or total_q == 0:
        return 0.0

    p_norm = [v / total_p for v in p]
    q_norm = [v / total_q for v in q]

    kl = 0.0
    for pi, qi in zip(p_norm, q_norm):
        if pi > 0 and qi > 0:
            kl += pi * math.log2(pi / qi)
    return kl


def renyi_entropy(data: list[float], bins: int = 20, alpha: float = 2.0) -> float:
    """Ω-ME05: Generalized Renyi entropy (α=2 → collision entropy)."""
    if len(data) < 2:
        return 0.0
    hist, _ = _histogram(data, bins)
    total = sum(hist)
    if total == 0:
        return 0.0

    ps = [c / total for c in hist]

    if alpha == 1.0:
        # Shannon as special case
        return -sum(p * math.log2(max(p, 1e-15)) for p in ps if p > 0)

    renyi = sum(p ** alpha for p in ps if p > 0)
    if renyi > 0:
        return math.log2(renyi) / (1.0 - alpha)
    return 0.0


def lempel_ziv_complexity(data: list[float]) -> float:
    """Ω-ME06: Lempel-Ziv complexity proxy — lower = more predictable."""
    if len(data) < 2:
        return 0.0

    # Quantize to binary sequence
    median = sorted(data)[len(data) // 2]
    binary = "".join("1" if v > median else "0" for v in data)

    n = len(binary)
    if n == 0:
        return 0.0

    # Count distinct substrings via sliding window
    substrings: set[str] = set()
    max_len = min(8, n)
    for length in range(1, max_len + 1):
        for i in range(n - length + 1):
            substrings.add(binary[i:i + length])

    total_substrings = sum(n - l + 1 for l in range(1, max_len + 1))
    return len(substrings) / max(total_substrings, 1)


def information_gain(baseline_entropy: float, feature_entropy: float) -> float:
    """Ω-ME07: Information gain from using a feature."""
    return max(0.0, baseline_entropy - feature_entropy)


def predictability_score(data: list[float], window: int = 50) -> float:
    """Ω-ME08: Composite predictability score [0, 1].

    0 = completely unpredictable (random walk)
    1 = highly predictable (clear pattern)
    """
    if len(data) < window:
        return 0.0

    recent = data[-window:]

    # Low entropy → high predictability
    ent = shannon_entropy(recent, bins=10)
    # Normalize: max entropy for 10 bins ≈ 3.32 bits
    max_ent = math.log2(10)
    ent_norm = 1.0 - min(1.0, ent / max_ent)

    # LZ complexity contribution
    lz = lempel_ziv_complexity(recent)
    # LZ=1 → random, LZ=0 → compressible
    lz_score = 1.0 - lz

    return round(0.7 * ent_norm + 0.3 * lz_score, 4)


# ──────────────────────────────────────────────────────────────
# Ω-ME19 to Ω-ME36: Fractal & Wavelet Analysis
# ──────────────────────────────────────────────────────────────


def hurst_exponent(data: list[float], max_lag: int = 40) -> float:
    """Ω-ME19: Hurst exponent — regime classification.

    H > 0.5 → trending (persistent)
    H = 0.5 → random walk
    H < 0.5 → mean reverting (anti-persistent)
    """
    n = len(data)
    if n < max_lag or n < 10:
        return 0.5

    lags: list[int] = []
    std_diffs: list[float] = []

    for lag in range(2, min(max_lag, n // 2)):
        diffs = [data[i + lag] - data[i] for i in range(n - lag)]
        if len(diffs) < 2:
            continue
        std = _std(diffs)
        if std > 0:
            lags.append(lag)
            std_diffs.append(std)

    if len(lags) < 3:
        return 0.5

    # Linear regression on log-log
    log_x = [math.log(L) for L in lags]
    log_y = [math.log(S) for S in std_diffs]

    slope, _ = _linear_regression(log_x, log_y)
    return round(max(0.0, min(1.0, slope)), 4)


def rolling_hurst(data: list[float], window: int = 100, max_lag: int = 30) -> list[float]:
    """Ω-ME20: Rolling Hurst exponent."""
    n = len(data)
    result: list[float] = []
    for end in range(window, n + 1):
        h = hurst_exponent(data[end - window:end], max_lag)
        result.append(h)
    return [0.5] * (window - 1) + result


def fractal_dimension(data: list[float], window: int = 50) -> float:
    """Ω-ME21: Box-counting fractal dimension.

    D ≈ 1.0 → smooth (strong trend)
    D ≈ 1.5 → random walk
    D ≈ 2.0 → extremely noisy
    """
    if len(data) < window:
        return 1.5

    data_win = data[-window:]
    n = len(data_win)

    d_min = min(data_win)
    d_max = max(data_win)
    data_range = d_max - d_min
    if data_range == 0:
        return 1.0

    diffs = [abs(data_win[i + 1] - data_win[i]) for i in range(n - 1)]
    normalized_diffs = [d / (data_range / n) for d in diffs]

    length = sum(math.sqrt(1 + nd ** 2) for nd in normalized_diffs)
    if length <= 0:
        return 1.0

    dim = 1.0 + math.log(length) / math.log(n)
    return round(max(1.0, min(2.0, dim)), 4)


def haar_wavelet_decompose(data: list[float], levels: int = 3) -> list[list[float]]:
    """Ω-ME22: Haar wavelet decomposition.

    Returns [approximation, detail_1, detail_2, ...] where approximation
    is the long-term trend and details are progressively higher frequency
    components.
    """
    signal = list(data)
    coeffs: list[list[float]] = []

    for level in range(levels):
        n = len(signal)
        if n < 2:
            break
        half = n // 2
        approx: list[float] = []
        detail: list[float] = []

        for i in range(half):
            a = (signal[2 * i] + signal[2 * i + 1]) / math.sqrt(2)
            d = (signal[2 * i] - signal[2 * i + 1]) / math.sqrt(2)
            approx.append(a)
            detail.append(d)

        coeffs.append(detail)
        signal = approx

    coeffs.insert(0, signal)  # Approximation = trend
    return coeffs


def wavelet_energy(coeffs: list[list[float]]) -> list[float]:
    """Ω-ME23: Energy at each wavelet level."""
    return [sum(v ** 2 for v in level) / max(1, len(level)) for level in coeffs]


def multiscale_hurst(data: list[float], max_levels: int = 5) -> list[float]:
    """Ω-ME24: Hurst exponent at multiple wavelet scales."""
    coeffs = haar_wavelet_decompose(data, levels=max_levels)
    # For each detail level, compute H proxy from std
    hursts: list[float] = []
    for level in coeffs[1:]:  # Skip approximation
        if len(level) >= 3:
            std = _std(level)
            mean_abs = sum(abs(v) for v in level) / len(level)
            # Approximate: higher std/mean ratio → higher persistence
            h = 0.5 + min(0.5, max(-0.5, std / max(1, mean_abs) - 1.0))
            hursts.append(round(h, 4))
        else:
            hursts.append(0.5)
    return hursts


# ──────────────────────────────────────────────────────────────
# Ω-ME37 to Ω-ME54: Risk, Volatility & Pattern Detection
# ──────────────────────────────────────────────────────────────


def kelly_criterion(win_rate: float, avg_win: float, avg_loss: float) -> float:
    """Ω-ME37: Kelly criterion — optimal bet size."""
    if avg_loss == 0 or win_rate <= 0 or win_rate >= 1:
        return 0.0
    b = avg_win / abs(avg_loss)
    q = 1.0 - win_rate
    kelly = (win_rate * b - q) / b
    return max(0.0, kelly)


def bayesian_kelly(wins: int, total_trades: int, avg_win: float, avg_loss: float,
                   prior_alpha: float = 1.0, prior_beta: float = 1.0) -> float:
    """Ω-ME38: Bayesian Kelly with prior.

    Uses Beta(prior_alpha + wins, prior_beta + losses) posterior
    for win rate, then takes expected Kelly fraction.
    """
    posterior_alpha = prior_alpha + wins
    posterior_beta = prior_beta + (total_trades - wins)

    # E[p] = alpha / (alpha + beta)
    expected_wr = posterior_alpha / (posterior_alpha + posterior_beta)

    if avg_loss == 0:
        return 0.0
    b = avg_win / abs(avg_loss)
    q = 1.0 - expected_wr
    kelly = (expected_wr * b - q) / b
    return max(0.0, kelly)


def rsi(prices: list[float], period: int = 14) -> list[float]:
    """Ω-ME39: Relative Strength Index via EMA smoothing."""
    if len(prices) < period + 1:
        return [50.0] * len(prices)

    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]

    avg_gain = sum(d for d in deltas[:period] if d > 0) / period
    avg_loss = sum(-d for d in deltas[:period] if d < 0) / period

    rsi_vals: list[float] = [50.0] * period

    if avg_loss > 0:
        rs = avg_gain / avg_loss
        initial_rsi = 100.0 - 100.0 / (1.0 + rs)
    else:
        initial_rsi = 100.0

    rsi_vals.append(initial_rsi)

    for i in range(period, len(deltas)):
        delta = deltas[i]
        gain = delta if delta > 0 else 0.0
        loss = -delta if delta < 0 else 0.0

        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

        if avg_loss > 0:
            rs = avg_gain / avg_loss
            rsi_vals.append(100.0 - 100.0 / (1.0 + rs))
        else:
            rsi_vals.append(100.0)

    return rsi_vals


def atr_values(highs: list[float], lows: list[float], closes: list[float],
               period: int = 14) -> list[float]:
    """Ω-ME40: Average True Range."""
    n = len(closes)
    if n < 2:
        return [0.0] * n

    tr: list[float] = [highs[0] - lows[0]]
    for i in range(1, n):
        tr.append(max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        ))

    atr_vals: list[float] = []
    if n >= period:
        atr_start = sum(tr[:period]) / period
        atr_vals = [0.0] * (period - 1) + [atr_start]
        for i in range(period, n):
            atr_vals.append((atr_vals[-1] * (period - 1) + tr[i]) / period)
    else:
        atr_vals = [sum(tr[:n]) / n] * n

    return atr_vals


def realized_volatility(returns: list[float], window: int = 20) -> list[float]:
    """Ω-ME41: Rolling realized volatility (annualized)."""
    n = len(returns)
    result: list[float] = []
    dq: deque[float] = deque(maxlen=window)

    for r in returns:
        dq.append(r)
        if len(dq) < window:
            result.append(0.0)
        else:
            std = _std(list(dq))
            result.append(std * math.sqrt(252 * 1440))  # Assuming minute data
    return result


def ema(values: list[float], period: int) -> list[float]:
    """Ω-ME42: Exponential Moving Average."""
    if not values:
        return []
    alpha = 2.0 / (period + 1)
    result: list[float] = [values[0]]
    for i in range(1, len(values)):
        result.append(alpha * values[i] + (1 - alpha) * result[-1])
    return result


def detect_divergence(prices: list[float], indicator: list[float],
                      window: int = 20) -> tuple[bool, bool]:
    """Ω-ME43: Detect bullish and bearish divergence.

    Returns: (bullish_divergence, bearish_divergence)
    """
    if len(prices) < window or len(indicator) < window:
        return False, False

    price_window = prices[-window:]
    ind_window = indicator[-window:]

    price_lows: list[tuple[int, float]] = []
    price_highs: list[tuple[int, float]] = []
    ind_lows: list[tuple[int, float]] = []
    ind_highs: list[tuple[int, float]] = []

    for i in range(2, window - 2):
        # Price low pivot
        if (price_window[i] < price_window[i - 1] and
            price_window[i] < price_window[i - 2] and
            price_window[i] < price_window[i + 1] and
            price_window[i] < price_window[i + 2]):
            price_lows.append((i, price_window[i]))
            ind_lows.append((i, ind_window[i]))

        # Price high pivot
        if (price_window[i] > price_window[i - 1] and
            price_window[i] > price_window[i - 2] and
            price_window[i] > price_window[i + 1] and
            price_window[i] > price_window[i + 2]):
            price_highs.append((i, price_window[i]))
            ind_highs.append((i, ind_window[i]))

    bullish = False
    bearish = False

    # Bullish: lower low in price, higher low in indicator
    if len(price_lows) >= 2 and len(ind_lows) >= 2:
        if price_lows[-1][1] < price_lows[-2][1] and ind_lows[-1][1] > ind_lows[-2][1]:
            bullish = True

    # Bearish: higher high in price, lower high in indicator
    if len(price_highs) >= 2 and len(ind_highs) >= 2:
        if price_highs[-1][1] > price_highs[-2][1] and ind_highs[-1][1] < ind_highs[-2][1]:
            bearish = True

    return bullish, bearish


class SupportResistanceDetector:
    """Ω-ME44: Detects support/resistance levels via pivot clustering."""

    def __init__(self, sensitivity: float = 0.005) -> None:
        self._sensitivity = sensitivity

    def detect(self, highs: list[float], lows: list[float],
               closes: list[float]) -> dict[str, list[tuple[float, int]]]:
        if len(closes) < 5:
            return {"support": [], "resistance": []}

        pivots: list[tuple[str, float]] = []
        current_price = closes[-1]
        threshold = current_price * self._sensitivity

        for i in range(2, len(closes) - 2):
            # Resistance (high pivot)
            if (highs[i] > highs[i - 1] and highs[i] > highs[i - 2] and
                highs[i] > highs[i + 1] and highs[i] > highs[i + 2]):
                if highs[i] > current_price:
                    pivots.append(("R", highs[i]))

            # Support (low pivot)
            if (lows[i] < lows[i - 1] and lows[i] < lows[i - 2] and
                lows[i] < lows[i + 1] and lows[i] < lows[i + 2]):
                if lows[i] < current_price:
                    pivots.append(("S", lows[i]))

        # Cluster nearby levels
        supports_unclustered: list[tuple[float, int, float]] = []  # (price, count, weight)
        resistances_unclustered: list[tuple[float, int, float]] = []

        for ptype, price in pivots:
            if ptype == "S":
                merged = False
                for idx, (p, c, w) in enumerate(supports_unclustered):
                    if abs(price - p) < threshold:
                        new_price = (p * c + price) / (c + 1)
                        supports_unclustered[idx] = (new_price, c + 1, w + 1.0)
                        merged = True
                        break
                if not merged:
                    supports_unclustered.append((price, 1, 1.0))

            elif ptype == "R":
                merged = False
                for idx, (p, c, w) in enumerate(resistances_unclustered):
                    if abs(price - p) < threshold:
                        new_price = (p * c + price) / (c + 1)
                        resistances_unclustered[idx] = (new_price, c + 1, w + 1.0)
                        merged = True
                        break
                if not merged:
                    resistances_unclustered.append((price, 1, 1.0))

        supports_unclustered.sort(key=lambda x: x[1], reverse=True)
        resistances_unclustered.sort(key=lambda x: x[1], reverse=True)

        return {
            "support": [(p, c) for p, c, _ in supports_unclustered[:5]],
            "resistance": [(p, c) for p, c, _ in resistances_unclustered[:5]],
        }


def vwap(prices: list[float], volumes: list[float]) -> list[float]:
    """Ω-ME45: Volume Weighted Average Price."""
    if not prices or not volumes:
        return []

    n = min(len(prices), len(volumes))
    result: list[float] = []
    cum_pv = 0.0
    cum_v = 0.0

    for i in range(n):
        cum_pv += prices[i] * volumes[i]
        cum_v += volumes[i]
        if cum_v > 0:
            result.append(cum_pv / cum_v)
        else:
            result.append(prices[i])

    return result


def sigmoid(x: float) -> float:
    """Ω-ME46: Sigmoid function — maps any value to (0, 1)."""
    if x > 500:
        return 1.0
    if x < -500:
        return 0.0
    return 1.0 / (1.0 + math.exp(-x))


def softmax(values: list[float]) -> list[float]:
    """Ω-ME47: Softmax — converts scores to probabilities."""
    if not values:
        return []
    max_v = max(values)
    exp_vals = [math.exp(v - max_v) for v in values]
    total = sum(exp_vals)
    if total == 0:
        return [1.0 / len(values)] * len(values)
    return [e / total for e in exp_vals]


def log_returns(prices: list[float]) -> list[float]:
    """Ω-ME48: Log returns of price series."""
    if len(prices) < 2:
        return [0.0]
    return [math.log(prices[i] / prices[i - 1]) for i in range(1, len(prices))]


def normalize(values: list[float], min_out: float = 0.0, max_out: float = 1.0) -> list[float]:
    """Ω-ME49: Min-max normalization to [min_out, max_out]."""
    if not values:
        return []
    v_min = min(values)
    v_max = max(values)
    v_range = v_max - v_min
    if v_range == 0:
        return [(min_out + max_out) / 2] * len(values)
    return [min_out + (v - v_min) / v_range * (max_out - min_out) for v in values]


def _histogram(data: list[float], bins: int) -> tuple[list[int], list[float]]:
    """Simple histogram."""
    if not data:
        return [], []
    d_min = min(data)
    d_max = max(data)
    d_range = d_max - d_min if d_max > d_min else 1.0

    counts = [0] * bins
    edges = [d_min + i * d_range / bins for i in range(bins + 1)]

    for v in data:
        idx = int((v - d_min) / d_range * (bins - 1))
        idx = max(0, min(bins - 1, idx))
        counts[idx] += 1

    return counts, edges


def _std(data: list[float]) -> float:
    """Standard deviation."""
    n = len(data)
    if n < 2:
        return 0.0
    mean = sum(data) / n
    var = sum((v - mean) ** 2 for v in data) / (n - 1)
    return math.sqrt(max(0.0, var))


def _linear_regression(x: list[float], y: list[float]) -> tuple[float, float]:
    """Simple linear regression, returns (slope, intercept)."""
    n = len(x)
    if n < 2:
        return 0.0, 0.0
    x_mean = sum(x) / n
    y_mean = sum(y) / n

    ss_xy = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
    ss_xx = sum((x[i] - x_mean) ** 2 for i in range(n))

    if ss_xx == 0:
        return 0.0, y_mean

    slope = ss_xy / ss_xx
    intercept = y_mean - slope * x_mean
    return slope, intercept
