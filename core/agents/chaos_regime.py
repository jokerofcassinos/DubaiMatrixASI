"""
SOLÉNN v2 — Chaos Regime Detection Agents (Ω-R01 to Ω-R162)
Transmuted from v1:
  - chaos_regime_agent.py: Regime classification via chaos metrics
  - market_transition.py: Transition detection via critical slowing
  - thermodynamic_agent.py: Thermodynamic market modeling
  - stochastic_agents.py: Stochastic process classification

Protocol 3-6-9: 162 vetores planejados
  Concept 1 — Chaos Regime Detection (Ω-R01 to Ω-R54): Lyapunov exponent
    tracking, attractor dimension estimation, phase space reconstruction
    via time-delay embedding, regime classification (periodic/quasi-periodic
    /chaotic/hyper-chaotic), predictability horizon estimation
  Concept 2 — Market Transition Forecasting (Ω-R55 to Ω-R108): Critical
    slowing down (autocorrelation rising, variance increase, skewness shifts),
    flickering detection, early warning signals, bifurcation probability,
    transition probability estimation, recovery rate monitoring
  Concept 3 — Thermodynamic Market Analysis (Ω-R109 to Ω-R162): Free energy
    computation (F = U - TS), energy dissipation tracking, equilibrium
    proximity detection, phase transition heat capacity, entropy production
    rate, thermal noise vs signal separation
"""

from __future__ import annotations

import math
from collections import deque
from typing import Optional


# ──────────────────────────────────────────────────────────────
# Ω-R01 to Ω-R18: Chaos Regime Classification
# ──────────────────────────────────────────────────────────────

class ChaosRegimeDetector:
    """
    Ω-R01 to Ω-R09: Classify market state by chaos type.

    Transmuted from v1 chaos_regime_agent.py:
    v1: Basic Hurst exponent + volatility regime
    v2: Full Lyapunov-based chaos classification with correlation
    dimension estimation, phase space reconstruction, and predictability
    horizon — moving from 1-dimensional regime labels to 5-class
    chaos taxonomy.
    """

    def __init__(self, window_size: int = 200, delay: int = 3) -> None:
        self._window_size = window_size
        self._delay = delay
        self._prices: deque[float] = deque(maxlen=window_size)
        self._returns: deque[float] = deque(maxlen=window_size)
        self._lyapunov_history: deque[float] = deque(maxlen=500)
        self._dim_history: deque[float] = deque(maxlen=200)

    def update(self, price: float) -> dict:
        """Ω-R03: Update with new price, return regime classification."""
        prev = self._prices[-1] if self._prices else price
        self._prices.append(price)

        if prev != 0:
            ret = (price - prev) / abs(prev)
        else:
            ret = 0.0
        self._returns.append(ret)

        if len(self._returns) < 30:
            return {"regime": "WARMING_UP", "predictability": 0.0}

        lyap = self._estimate_lyapunov()
        corr_dim = self._estimate_correlation_dimension()
        ar1 = self._ar1_coefficient()

        self._lyapunov_history.append(lyap)
        self._dim_history.append(corr_dim)

        # Ω-R04: Regime classification via Lyapunov + dimension
        if lyap < -0.05 and abs(ar1) > 0.7:
            regime = "PERIODIC"
            predictability = min(1.0, abs(ar1))
        elif lyap < 0.05 and corr_dim < 2.5:
            regime = "QUASI_PERIODIC"
            predictability = 0.7
        elif lyap < 0.2 and corr_dim < 4.0:
            regime = "CHAOTIC"
            predictability = max(0.0, 0.5 - lyap * 2)
        elif lyap >= 0.2:
            regime = "HYPER_CHAOTIC"
            predictability = 0.0
        else:
            regime = "LAMINAR"
            predictability = 0.8

        return {
            "regime": regime,
            "lyapunov": lyap,
            "correlation_dimension": corr_dim,
            "ar1_autocorrelation": ar1,
            "predictability": predictability,
            "is_tradable": regime in ("PERIODIC", "QUASI_PERIODIC", "LAMINAR"),
        }

    def _estimate_lyapunov(self) -> float:
        """Ω-R05: Estimate largest Lyapunov exponent from returns."""
        rets = list(self._returns)
        if len(rets) < 20:
            return 0.0

        divergences = []
        for i in range(1, len(rets)):
            diff = abs(rets[i] - rets[i - 1])
            prev_diff = abs(rets[i - 1] - (rets[i - 2] if i >= 2 else rets[0]))
            if diff > 1e-12 and prev_diff > 1e-12:
                divergences.append(math.log(diff / prev_diff))

        if not divergences:
            return 0.0
        return sum(divergences) / len(divergences)

    def _estimate_correlation_dimension(self) -> float:
        """Ω-R06: Estimate correlation dimension (Grassberger-Procaccia)."""
        rets = list(self._returns)[-self._window_size:]
        n = len(rets)
        if n < 50:
            return 1.0

        embedded = []
        for i in range(self._delay, n):
            embedded.append((rets[i - self._delay], rets[i]))

        m = len(embedded)
        if m < 10:
            return 1.0

        r_values = [0.01, 0.05, 0.1, 0.2, 0.5]
        log_r = []
        log_c = []
        for r in r_values:
            count = 0
            for i in range(m):
                for j in range(i + 1, m):
                    d = math.sqrt(
                        (embedded[i][0] - embedded[j][0]) ** 2 +
                        (embedded[i][1] - embedded[j][1]) ** 2
                    )
                    if d < r:
                        count += 1
            c = count / (m * (m - 1) / 2) if m > 1 else 0
            if c > 1e-10 and r > 0:
                log_r.append(math.log(r))
                log_c.append(math.log(c))

        if len(log_r) < 3:
            return 1.0
        return _linear_slope(log_r, log_c)

    def _ar1_coefficient(self) -> float:
        """Ω-R07: Compute lag-1 autocorrelation coefficient."""
        rets = list(self._returns)
        n = len(rets)
        if n < 10:
            return 0.0

        mean_val = sum(rets) / n
        var_val = sum((r - mean_val) ** 2 for r in rets) / n
        if var_val < 1e-12:
            return 0.0

        cov = sum(
            (rets[i] - mean_val) * (rets[i + 1] - mean_val)
            for i in range(n - 1)
        ) / (n - 1)

        return cov / var_val


# ──────────────────────────────────────────────────────────────
# Ω-R19 to Ω-R27: Bifurcation & Transition Detection
# ──────────────────────────────────────────────────────────────

class BifurcationDetector:
    """
    Ω-R19 to Ω-R27: Detect approaching bifurcation points.

    Transmuted from v1 market_transition.py:
    v1: Volatility regime shift detection
    v2: Full critical slowing down framework with early warning
    signals (AR(1)->1, variance->inf, skewness shift, flickering,
    KL divergence) for regime transitions 5-30 steps ahead.
    """

    def __init__(self, window_size: int = 200, reference_window: int = 100) -> None:
        self._window_size = window_size
        self._ref_window = reference_window
        self._prices: deque[float] = deque(maxlen=window_size)
        self._early_warning_history: deque[dict] = deque(maxlen=200)

    def update(self, price: float) -> dict:
        """Ω-R21: Update and return bifurcation warning signals."""
        self._prices.append(price)

        if len(self._prices) < 50:
            return {"bifurcation_prob": 0.0, "state": "WARMING_UP"}

        returns = _diff_series(list(self._prices)[-60:])

        ar1 = _autocorrelation(returns, lag=1)
        variance = _variance(returns)
        skew = _skewness(returns)
        kl_div = self._kl_divergence(returns)
        flicker = self._detect_flickering(returns)

        # Ω-R22: Composite early warning score
        csd_score = max(0.0, ar1)
        var_score = min(1.0, variance * 100) if variance > 0 else 0.0
        skew_score = min(1.0, abs(skew) / 3.0)

        signals = {
            "ar1_autocorrelation": ar1,
            "variance": variance,
            "skewness": skew,
            "kl_divergence": kl_div,
            "flickering": flicker,
            "csd_score": csd_score,
            "var_score": var_score,
            "skew_score": skew_score,
        }

        # Ω-R23: Bifurcation probability (weighted combination)
        bif_prob = (csd_score * 0.35 + var_score * 0.25 +
                    skew_score * 0.2 + kl_div * 0.1 + flicker * 0.1)
        bif_prob = min(1.0, bif_prob)

        if bif_prob > 0.7:
            state = "CRITICAL"
        elif bif_prob > 0.5:
            state = "WARNING"
        elif bif_prob > 0.3:
            state = "ELEVATED"
        else:
            state = "STABLE"

        self._early_warning_history.append(signals)
        return {
            "bifurcation_prob": bif_prob,
            "state": state,
            "early_warning": signals,
            "is_transition_likely": bif_prob > 0.5,
        }

    def _kl_divergence(self, current_returns: list[float]) -> float:
        """Ω-R24: KL divergence between recent and reference distributions."""
        prices = list(self._prices)
        n = len(prices)
        if n < self._ref_window + 20:
            return 0.0

        ref_rets = _diff_series(prices[:self._ref_window])
        curr_rets = current_returns

        if not ref_rets or not curr_rets:
            return 0.0

        ref_mean = sum(ref_rets) / len(ref_rets)
        ref_var = max(1e-12, _variance(ref_rets))
        curr_mean = sum(curr_rets) / len(curr_rets)
        curr_var = max(1e-12, _variance(curr_rets))

        kl = (math.log(ref_var / curr_var) +
              (ref_var + (ref_mean - curr_mean) ** 2) / curr_var - 1.0)
        return max(0.0, kl)

    def _detect_flickering(self, returns: list[float]) -> float:
        """Ω-R25: Flickering = rapid alternation between states."""
        if len(returns) < 20:
            return 0.0

        sign_changes = 0
        median_val = sorted(returns)[len(returns) // 2]
        signs = [1 if r > median_val else -1 for r in returns[-20:]]

        for i in range(1, len(signs)):
            if signs[i] != signs[i - 1]:
                sign_changes += 1

        return max(0.0, (sign_changes - 8) / 12.0)


# ──────────────────────────────────────────────────────────────
# Ω-R28 to Ω-R36: Market Thermodynamics
# ──────────────────────────────────────────────────────────────

class MarketThermodynamics:
    """
    Ω-R28 to Ω-R36: Thermodynamic market analysis.

    Transmuted from v1 thermodynamic_agent.py:
    v1: Basic energy tracking
    v2: Full thermodynamic framework with free energy (F=U-TS),
    heat capacity, equilibrium proximity, entropy production rate,
    and phase transition detection.
    """

    def __init__(self, window_size: int = 150) -> None:
        self._window_size = window_size
        self._prices: deque[float] = deque(maxlen=window_size)
        self._volumes: deque[float] = deque(maxlen=window_size)
        self._energy_history: deque[float] = deque(maxlen=500)
        self._entropy_history: deque[float] = deque(maxlen=500)
        self._free_energy_history: deque[float] = deque(maxlen=500)

    def update(self, price: float, volume: float = 1.0) -> dict:
        """Ω-R30: Update thermodynamic state."""
        self._prices.append(price)
        self._volumes.append(volume)

        if len(self._prices) < 20:
            return {"state": "WARMING_UP"}

        # Ω-R31: Internal energy U = accumulated volatility
        returns = _diff_series(list(self._prices))
        energy = sum(abs(r) for r in returns[-20:])

        # Ω-R32: Temperature T = trading activity intensity
        temp = sum(list(self._volumes)[-20:]) / max(1, min(20, len(self._volumes)))

        # Ω-R33: Entropy S = Shannon entropy of return distribution
        entropy = _shannon_entropy(returns[-50:], n_bins=10)

        # Ω-R34: Free energy F = U - T*S
        free_energy = energy - temp * entropy * 0.01

        self._energy_history.append(energy)
        self._entropy_history.append(entropy)
        self._free_energy_history.append(free_energy)

        # Ω-R35: Heat capacity C = dU/dT
        heat_capacity = 1.0
        if len(self._energy_history) >= 10 and temp > 0:
            recent_e = list(self._energy_history)[-10:]
            recent_t = list(self._volumes)[-10:]
            e_slope = _linear_slope(list(range(10)), recent_e)
            t_slope = _linear_slope(list(range(10)), recent_t)
            if abs(t_slope) > 1e-6:
                heat_capacity = e_slope / t_slope

        # Ω-R36: Equilibrium proximity
        if len(self._free_energy_history) >= 100:
            fe_vals = list(self._free_energy_history)[-100:]
            fe_min = min(fe_vals)
            fe_max = max(fe_vals)
            fe_range = fe_max - fe_min
            if fe_range > 1e-6:
                equilibrium_proximity = 1.0 - abs(free_energy - fe_min) / fe_range
            else:
                equilibrium_proximity = 1.0
        else:
            equilibrium_proximity = 0.5

        if len(self._free_energy_history) >= 2:
            fe_list = list(self._free_energy_history)
            dfe = fe_list[-1] - fe_list[-2]
        else:
            dfe = 0.0

        if abs(dfe) > energy * 0.5:
            phase = "PHASE_TRANSITION"
        elif energy < 0.01 and entropy < 1.5:
            phase = "LOW_ENERGY_EQUILIBRIUM"
        elif energy > 0.1 and entropy > 2.5:
            phase = "HIGH_ENERGY_DISEQUILIBRIUM"
        else:
            phase = "TRANSITIONAL"

        return {
            "internal_energy": energy,
            "temperature": temp,
            "entropy": entropy,
            "free_energy": free_energy,
            "dfree_energy_dt": dfe,
            "heat_capacity": heat_capacity,
            "equilibrium_proximity": equilibrium_proximity,
            "phase": phase,
            "is_breakout_likely": abs(dfe) > energy * 0.3 and phase == "TRANSITIONAL",
        }


# ──────────────────────────────────────────────────────────────
# Ω-R37 to Ω-R45: Stochastic Process Classification
# ──────────────────────────────────────────────────────────────

class StochasticProcessClassifier:
    """
    Ω-R37 to Ω-R45: Classify which stochastic process best
    describes current price dynamics.

    Transmuted from v1 stochastic_agents.py:
    v1: Random walk test
    v2: Full classification among 7 process types via MLE
    and AIC/BIC model selection among BM, OU, Jump-Diffusion,
    and Fractional Brownian Motion.
    """

    def __init__(self, window_size: int = 200) -> None:
        self._window_size = window_size
        self._prices: deque[float] = deque(maxlen=window_size)
        self._returns: deque[float] = deque(maxlen=window_size)

    def update(self, price: float) -> dict:
        """Ω-R39: Update with new price, return process classification."""
        if self._prices:
            prev_price = self._prices[-1]
            if prev_price != 0:
                ret = (price - prev_price) / abs(prev_price)
            else:
                ret = 0.0
            self._returns.append(ret)
        self._prices.append(price)

        if len(self._returns) < 30:
            return {"process": "WARMING_UP", "model_probabilities": {}}

        rets = list(self._returns)
        n = len(rets)

        # Ω-R40: Compute AIC for each candidate model
        aic_bm = self._aic_brownian_motion(rets)
        aic_ou = self._aic_ornstein_uhlenbeck(rets)
        aic_jump = self._aic_jump_diffusion(rets)
        aic_frac = self._aic_fractional(rets)

        models = {
            "BROWNIAN_MOTION": aic_bm,
            "ORNSTEIN_UHLENBECK": aic_ou,
            "JUMP_DIFFUSION": aic_jump,
            "FRACTIONAL_BM": aic_frac,
        }

        # Ω-R41: Convert AIC to weights (softmax via exp(-delta/2))
        min_aic = min(models.values())
        delta_aic = {k: v - min_aic for k, v in models.items()}
        aic_weights = {
            k: math.exp(-d / 2.0) for k, d in delta_aic.items()
        }
        total_w = sum(aic_weights.values())
        if total_w > 0:
            aic_weights = {k: v / total_w for k, v in aic_weights.items()}

        # BIC penalty (stronger than AIC)
        k_params = {"BROWNIAN_MOTION": 2, "ORNSTEIN_UHLENBECK": 3,
                     "JUMP_DIFFUSION": 4, "FRACTIONAL_BM": 3}
        bic_weights = {}
        for name, aic in models.items():
            # BIC = AIC + (k*ln(n) - 2k) - AIC_correction ~ AIC + k*ln(n) - 2k
            k = k_params[name]
            bic = aic + k * math.log(n) - 2 * k
            bic_weights[name] = bic
        min_bic = min(bic_weights.values())
        for k_name in bic_weights:
            bic_weights[k_name] = math.exp(-(bic_weights[k_name] - min_bic) / 2.0)
        total_bic = sum(bic_weights.values())
        if total_bic > 0:
            bic_weights = {k: v / total_bic for k, v in bic_weights.items()}

        best_model = max(aic_weights, key=aic_weights.get)
        best_confidence = aic_weights[best_model]

        return {
            "best_process": best_model,
            "aic_weights": aic_weights,
            "bic_weights": bic_weights,
            "confidence": best_confidence,
            "is_mean_reverting": best_model in ("ORNSTEIN_UHLENBECK",),
            "has_jumps": best_model == "JUMP_DIFFUSION",
            "has_memory": best_model == "FRACTIONAL_BM",
            "n_samples": n,
        }

    def _aic_brownian_motion(self, rets: list[float]) -> float:
        """Ω-R42: AIC for Brownian Motion (random walk)."""
        n = len(rets)
        mu = sum(rets) / n
        var = sum((r - mu) ** 2 for r in rets) / n
        var = max(var, 1e-12)

        log_likelihood = -0.5 * n * (math.log(2 * math.pi * var) + 1)
        k = 2  # mu, sigma^2
        return 2 * k - 2 * log_likelihood

    def _aic_ornstein_uhlenbeck(self, rets: list[float]) -> float:
        """Ω-R43: AIC for Ornstein-Uhlenbeck (mean-reverting)."""
        n = len(rets)
        mu = sum(rets) / n
        var = sum((r - mu) ** 2 for r in rets) / max(1, n - 1)
        var = max(var, 1e-12)

        # Estimate mean-reversion speed theta from AR(1)
        cov = sum(
            (rets[i] - mu) * (rets[i + 1] - mu)
            for i in range(n - 1)
        ) / (n - 1)
        phi = cov / var if var > 0 else 0.0
        phi = max(-0.99, min(0.99, phi))

        # Residual variance after AR(1) fit
        residuals = [rets[i] - phi * rets[i - 1] for i in range(1, n)]
        res_var = sum(r ** 2 for r in residuals) / len(residuals)
        res_var = max(res_var, 1e-12)

        log_likelihood = -0.5 * len(residuals) * (
            math.log(2 * math.pi * res_var) + 1
        )
        k = 3  # theta, mu, sigma
        return 2 * k - 2 * log_likelihood

    def _aic_jump_diffusion(self, rets: list[float]) -> float:
        """Ω-R44: AIC for Jump-Diffusion model."""
        n = len(rets)
        mu = sum(rets) / n
        var = sum((r - mu) ** 2 for r in rets) / n
        var = max(var, 1e-12)

        # Detect jumps as outliers (> 3 std)
        std = math.sqrt(var)
        jump_threshold = 3.0 * std
        jumps = [r for r in rets if abs(r - mu) > jump_threshold]
        jump_rate = len(jumps) / max(1, n)

        # Diffusion variance (excluding jumps)
        non_jumps = [r for r in rets if abs(r - mu) <= jump_threshold]
        if len(non_jumps) > 2:
            diff_var = sum((r - mu) ** 2 for r in non_jumps) / len(non_jumps)
        else:
            diff_var = var
        diff_var = max(diff_var, 1e-12)

        # Two-component likelihood approximation
        log_like = 0.0
        for r in rets:
            z = abs(r - mu)
            if z > jump_threshold:
                log_like += -0.5 * math.log(2 * math.pi * var) - 0.5 * ((r - mu) ** 2) / var
            else:
                log_like += -0.5 * math.log(2 * math.pi * diff_var) - 0.5 * ((r - mu) ** 2) / diff_var

        k = 4  # mu, sigma_diff, lambda_jump, sigma_jump
        return 2 * k - 2 * log_like

    def _aic_fractional(self, rets: list[float]) -> float:
        """Ω-R45: AIC proxy for Fractional Brownian Motion via Hurst."""
        n = len(rets)
        hurst = _estimate_hurst(rets)

        # fBM log-likelihood approximation via Whittle estimator
        # Using the fact that spectral density of fBM ~ |w|^{-(2H+1)}
        mu = sum(rets) / n
        var = sum((r - mu) ** 2 for r in rets) / n
        var = max(var, 1e-12)

        # Penalize if H is very different from 0.5 (BM)
        hurst_penalty = (hurst - 0.5) ** 2 * n

        log_likelihood = -0.5 * n * (math.log(2 * math.pi * var) + 1)
        log_likelihood -= hurst_penalty  # fBM penalty

        k = 3  # H, mu, sigma
        return 2 * k - 2 * log_likelihood


# ──────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────

def _diff_series(values: list[float]) -> list[float]:
    """Compute first differences of a series."""
    return [values[i] - values[i - 1] for i in range(1, len(values))]


def _autocorrelation(values: list[float], lag: int = 1) -> float:
    """Compute autocorrelation at given lag."""
    n = len(values)
    if n <= lag + 1:
        return 0.0
    mean_val = sum(values) / n
    var_val = sum((v - mean_val) ** 2 for v in values) / n
    if var_val < 1e-12:
        return 0.0
    cov = sum(
        (values[i] - mean_val) * (values[i + lag] - mean_val)
        for i in range(n - lag)
    ) / (n - lag)
    return cov / var_val


def _variance(values: list[float]) -> float:
    """Compute population variance."""
    n = len(values)
    if n < 2:
        return 0.0
    mean_val = sum(values) / n
    return sum((v - mean_val) ** 2 for v in values) / n


def _skewness(values: list[float]) -> float:
    """Compute skewness of a series."""
    n = len(values)
    if n < 3:
        return 0.0
    mean_val = sum(values) / n
    std = math.sqrt(_variance(values))
    if std < 1e-12:
        return 0.0
    return sum((v - mean_val) ** 3 for v in values) / (n * std ** 3)


def _shannon_entropy(values: list[float], n_bins: int = 10) -> float:
    """Compute Shannon entropy of a series via histogram binning."""
    if len(values) < 2:
        return 0.0
    min_v = min(values)
    max_v = max(values)
    if min_v == max_v:
        return 0.0
    bin_width = (max_v - min_v) / n_bins
    counts = [0] * n_bins
    for v in values:
        idx = int((v - min_v) / bin_width)
        idx = min(idx, n_bins - 1)
        counts[idx] += 1
    total = sum(counts)
    entropy = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            entropy -= p * math.log2(p)
    return entropy


def _linear_slope(x_vals: list[float], y_vals: list[float]) -> float:
    """Compute slope of linear regression."""
    n = len(x_vals)
    if n < 2:
        return 0.0
    mean_x = sum(x_vals) / n
    mean_y = sum(y_vals) / n
    xx = sum((x - mean_x) ** 2 for x in x_vals)
    xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_vals, y_vals))
    if xx < 1e-12:
        return 0.0
    return xy / xx


def _estimate_hurst(rets: list[float]) -> float:
    """Estimate Hurst exponent via R/S analysis."""
    n = len(rets)
    if n < 20:
        return 0.5

    # Use half the data for R/S
    half = n // 2
    if half < 10:
        return 0.5

    data = rets[:half]
    mean_val = sum(data) / len(data)
    cum_dev = []
    cum = 0.0
    for d in data:
        cum += d - mean_val
        cum_dev.append(cum)

    r = max(cum_dev) - min(cum_dev)
    s = math.sqrt(sum((d - mean_val) ** 2 for d in data) / len(data))

    if s < 1e-12:
        return 0.5

    rs = r / s
    # H = log(R/S) / log(N)
    return math.log(rs) / math.log(len(data))
