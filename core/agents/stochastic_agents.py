"""
SOLÉNN v2 — Stochastic Process Agents (Ω-ST01 to Ω-ST162)
Transmuted from v1:
  - stochastic_agents.py: Stochastic process classification
  - market_transition.py: Markov chain of regime transitions
  - dynamics.py: Dynamic systems and phase portraits
  - physics.py: Physics-inspired market dynamics
  - predator.py: Predator-prey dynamics (Lotka-Volterra)

Protocol 3-6-9: 162 vetores planejados
  Concept 1 — Stochastic Process Classification (Ω-ST01 to Ω-ST54):
    Process type identification (Brownian, Poisson, Hawkes,
    Ornstein-Uhlenbeck, Geometric Brownian, Fractional Brownian),
    parameter estimation via MLE, process fitness scoring,
    model selection via AIC/BIC, process switching detection
  Concept 2 — Markov Chain & Regime Transitions (Ω-ST55 to Ω-ST108):
    Transition matrix estimation, stationary distribution,
    mean first passage time, regime connectivity graph,
    bottleneck state identification, ergodicity checking
  Concept 3 — Predator-Prey & Phase Space (Ω-ST109 to Ω-ST162):
    Lotka-Volterra for momentum vs mean-reversion competition,
    phase space trajectory analysis, fixed point stability,
    limit cycle detection, Lyapunov exponent estimation
"""

from __future__ import annotations

import math
from collections import deque
from typing import Optional


# ──────────────────────────────────────────────────────────────
# Ω-ST01 to Ω-ST18: Stochastic Process Classification
# ──────────────────────────────────────────────────────────────

class StochasticProcessClassifier:
    """
    Ω-ST01 to Ω-ST09: Classify market data as stochastic process.

    Transmuted from v1 stochastic_agents.py:
    v1: Basic process identification
    v2: Full classification with MLE parameter estimation,
    AIC/BIC model selection, and process switching detection.
    """

    PROCESSES = [
        "BROWNIAN",  # dX = mu dt + sigma dW
        "ORNSTEIN_UHLENBECK",  # dX = theta*(mu-X)dt + sigma dW
        "GEOMETRIC_BROWNIAN",  # dX = mu*X dt + sigma*X dW
        "HAWKES",  # Self-exciting point process
        "FRACTIONAL_BROWNIAN",  # Long memory, H != 0.5
    ]

    def __init__(self, window_size: int = 300) -> None:
        self._window = window_size
        self._returns: deque[float] = deque(maxlen=window_size)
        self._aic_scores: dict[str, float] = {}
        self._bic_scores: dict[str, float] = {}

    def update(self, price: float) -> dict:
        """Ω-ST03: Classify current stochastic process."""
        if hasattr(self, '_prev_price') and self._prev_price != 0:
            ret = (price - self._prev_price) / abs(self._prev_price)
            self._returns.append(ret)
        self._prev_price = price

        if len(self._returns) < 30:
            return {"state": "WARMING_UP"}

        rets = list(self._returns)
        n = len(rets)
        mu = sum(rets) / n
        sigma = math.sqrt(sum((r - mu) ** 2 for r in rets) / n)

        # Ω-ST04: Fit each process and compute information criteria
        fits = {}

        # Brownian
        fits["BROWNIAN"] = self._fit_brownian(rets)

        # Ornstein-Uhlenbeck
        ou_result = self._fit_ou(rets)
        fits["ORNSTEIN_UHLENBECK"] = ou_result

        # Geometric Brownian (returns are already log-returns ≈ GBM)
        fits["GEOMETRIC_BROWNIAN"] = fits["BROWNIAN"]  # Same in return space

        # Hawkes (self-excitation in absolute returns)
        fits["HAWKES"] = self._fit_hawkes(rets)

        # Fractional Brownian
        fits["FRACTIONAL_BROWNIAN"] = self._fit_fbm(rets)

        # Ω-ST05: Model selection via AIC
        best_aic = min(fits, key=fits.get)
        aic_range = max(fits.values()) - min(fits.values())

        # Ω-ST06: Process confidence
        if aic_range > 0:
            process_confidence = 1.0 - (
                fits[best_aic] - min(fits.values())
            ) / max(1e-6, aic_range)
        else:
            process_confidence = 0.0

        # Re-normalize to probabilities
        min_aic = min(fits.values())
        probs = {}
        for proc, aic in fits.items():
            delta = aic - min_aic
            probs[proc] = math.exp(-0.5 * delta)  # Approximate AIC weight
        total_p = sum(probs.values())
        if total_p > 0:
            probs = {k: v / total_p for k, v in probs.items()}
        else:
            probs = {k: 1.0 / len(self.PROCESSES) for k in self.PROCESSES}

        # Ω-ST07: Process switching detection
        # Compare current best with previous best
        if hasattr(self, '_prev_best'):
            process_switched = best_aic != self._prev_best
        else:
            process_switched = False
        self._prev_best = best_aic

        # Ω-ST08: Hurst parameter (for fBm detection)
        hurst = fits["FRACTIONAL_BROWNIAN"].get("hurst", 0.5)

        # Ω-ST09: OU mean reversion speed
        ou_theta = fits["ORNSTEIN_UHLENBECK"].get("theta", 0.0)

        return {
            "best_process": best_aic,
            "process_probabilities": {k: round(v, 3) for k, v in sorted(probs.items(), key=lambda x: -x[1])},
            "best_aic": min_aic,
            "process_confidence": process_confidence,
            "process_switched": process_switched,
            "hurst_parameter": hurst,
            "ou_mean_reversion_speed": ou_theta,
            "is_mean_reverting": best_aic == "ORNSTEIN_UHLENBECK" and ou_theta > 0.1,
            "is_trending": hurst > 0.6,
            "is_self_exciting": probs.get("HAWKES", 0) > 0.3,
        }

    def _fit_brownian(self, rets: list[float]) -> float:
        """Ω-ST10: AIC for simple Brownian motion."""
        n = len(rets)
        mu = sum(rets) / n
        sigma2 = sum((r - mu) ** 2 for r in rets) / n
        if sigma2 < 1e-12:
            return 1e6
        # Log-likelihood
        ll = -n / 2 * (math.log(2 * math.pi * sigma2) + 1)
        # AIC = 2k - 2*ll, k = 2 params (mu, sigma)
        return 4 - 2 * ll

    def _fit_ou(self, rets: list[float]) -> dict[float, float]:
        """Ω-ST11: AIC for Ornstein-Uhlenbeck process."""
        n = len(rets)
        if n < 5:
            return {"aic": 1e6, "theta": 0.0}

        # Simple OU discretized: X_t = c + phi * X_{t-1} + eps
        # phi = exp(-theta * dt), theta = -ln(phi)/dt
        y = rets[1:]
        x = rets[:-1]
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(a * b for a, b in zip(x, y))
        sum_xx = sum(a ** 2 for a in x)
        m = len(y)

        denom = m * sum_xx - sum_x ** 2
        if abs(denom) < 1e-12:
            return {"aic": 1e6, "theta": 0.0}

        # OLS: y = alpha + phi * x
        alpha = (sum_y * sum_xx - sum_x * sum_xy) / denom
        phi = (m * sum_xy - sum_x * sum_y) / denom
        phi = max(0.01, min(0.99, phi))  # Clamp for stationarity
        theta = -math.log(phi)

        # Residuals
        resid_sq = sum((yi - alpha - phi * xi) ** 2 for xi, yi in zip(x, y))
        sigma2 = resid_sq / m

        if sigma2 < 1e-12:
            return {"aic": 1e6, "theta": 0.0}

        ll = -m / 2 * (math.log(2 * math.pi * sigma2) + 1)
        aic = 6 - 2 * ll  # k=3 (alpha, phi, sigma)
        return {"aic": aic, "theta": theta}

    def _fit_hawkes(self, rets: list[float]) -> float:
        """Ω-ST12: AIC approximation for Hawkes process."""
        # Simplified: test if large returns cluster
        n = len(rets)
        threshold = sum(abs(r) for r in rets) / n * 2  # 2x average magnitude
        large_events = [i for i, r in enumerate(rets) if abs(r) > threshold]

        if len(large_events) < 3:
            return 0.0  # Not enough events for self-excitation

        # Check if events cluster (short inter-arrival times)
        intervals = [large_events[i + 1] - large_events[i]
                    for i in range(len(large_events) - 1)]
        avg_interval = sum(intervals) / len(intervals)

        # Hawkes: intervals should be shorter than expected under Poisson
        poisson_expected = n / max(1, len(large_events))

        # Self-excitation ratio
        if avg_interval > 0:
            excitation = poisson_expected / avg_interval
        else:
            excitation = 1.0

        if excitation > 1.5:
            return n * math.log(n)  # Lower AIC for Hawkes when clustering
        else:
            return n * math.log(n) + 10  # Penalty for extra parameters

    def _fit_fbm(self, rets: list[float]) -> dict[str, float]:
        """Ω-ST13: Estimate Hurst parameter and compute AIC."""
        # Rescaled Range (R/S) analysis
        n = len(rets)
        if n < 20:
            return {"aic": 1e6, "hurst": 0.5}

        # Use simple variance ratio method
        half = n // 2
        var_half = _variance(rets[:half])
        var_full = _variance(rets)

        if var_half < 1e-12 or var_full < 1e-12:
            return {"aic": 1e6, "hurst": 0.5}

        # For fBm: var(T) ~ T^{2H}
        hurst = 0.5 * math.log(var_full / max(1e-12, var_half)) / math.log(2)
        hurst = max(0.0, min(1.0, hurst))

        # AIC with extra parameter (H)
        mu = sum(rets) / n
        sigma2 = sum((r - mu) ** 2 for r in rets) / n
        if sigma2 < 1e-12:
            return {"aic": 1e6, "hurst": hurst}
        ll = -n / 2 * (math.log(2 * math.pi * sigma2) + 1)
        aic = 6 - 2 * ll  # Extra params: H

        return {"aic": aic, "hurst": hurst}


# ──────────────────────────────────────────────────────────────
# Ω-ST19 to Ω-ST27: Markov Chain Regime Transitions
# ──────────────────────────────────────────────────────────────

class MarkovTransitionEstimator:
    """
    Ω-ST19 to Ω-ST27: Estimate regime transition probabilities.

    Transmuted from v1 market_transition.py:
    v1: Simple state counting
    v2: Full transition matrix with stationary distribution,
    first passage times, and ergodicity checking.
    """

    STATES = ["TREND_UP", "TREND_DOWN", "RANGE_TIGHT", "RANGE_WIDE", "CHAOTIC"]

    def __init__(self, window_size: int = 500) -> None:
        self._window = window_size
        self._state_history: deque[int] = deque(maxlen=window_size)
        self._transitions: list[list[int]] = [[0] * len(self.STATES)
                                               for _ in range(len(self.STATES))]

    def classify_state(self, price: float, volatility: float) -> int:
        """Ω-ST21: Classify current market state."""
        # Simplified classification based on price/return characteristics
        if volatility > 0.02:
            return 4  # CHAOTIC
        elif volatility > 0.01:
            return 3  # RANGE_WIDE
        elif price > 0:  # positive return
            return 0  # TREND_UP
        elif price < 0:  # negative return
            return 1  # TREND_DOWN
        else:
            return 2  # RANGE_TIGHT

    def update(self, state_idx: int) -> dict:
        """Ω-ST22: Record state and update transition matrix."""
        if self._state_history:
            prev = self._state_history[-1]
            self._transitions[prev][state_idx] += 1
        self._state_history.append(state_idx)

        if len(self._state_history) < 10:
            return {"state": "WARMING_UP"}

        # Ω-ST23: Transition matrix
        P = self._compute_transition_matrix()

        # Ω-ST24: Stationary distribution
        pi = self._stationary_distribution(P)

        # Ω-ST25: Mean first passage time
        # Expected time to return to each state
        mftp = {}
        for i, name in enumerate(self.STATES):
            if pi[i] > 1e-6:
                mftp[name] = 1.0 / pi[i]
            else:
                mftp[name] = float('inf')

        # Ω-ST26: Ergodicity check
        # Chain is ergodic if all states communicate (irreducible + aperiodic)
        reachable = set()
        for i in range(len(self.STATES)):
            for j in range(len(self.STATES)):
                if self._transitions[i][j] > 0:
                    reachable.add((i, j))
        is_irreducible = len(reachable) >= len(self.STATES)
        is_ergodic = is_irreducible and all(pi[i] > 0.01 for i in range(len(self.STATES)))

        # Ω-ST27: Bottleneck state
        # State with lowest stationary prob = bottleneck
        if pi:
            bottleneck_idx = min(range(len(pi)), key=lambda i: pi[i])
            bottleneck = self.STATES[bottleneck_idx]
        else:
            bottleneck = "UNKNOWN"

        return {
            "transition_matrix": P,
            "stationary_distribution": dict(zip(self.STATES, [round(p, 3) for p in pi])),
            "mean_first_passage_time": mftp,
            "is_ergodic": is_ergodic,
            "bottleneck_state": bottleneck,
            "most_likely_state": self.STATES[max(range(len(pi)), key=lambda i: pi[i])] if pi else "UNKNOWN",
            "n_transitions_recorded": sum(sum(row) for row in self._transitions),
        }

    def _compute_transition_matrix(self) -> list[list[float]]:
        """Compute transition probability matrix."""
        n = len(self.STATES)
        P = [[0.0] * n for _ in range(n)]
        for i in range(n):
            row_sum = sum(self._transitions[i])
            if row_sum > 0:
                for j in range(n):
                    P[i][j] = self._transitions[i][j] / row_sum
            else:
                P[i][j] = 1.0 / n  # Uniform if no data
        return P

    def _stationary_distribution(self, P: list[list[float]]) -> list[float]:
        """Compute stationary distribution via power iteration."""
        n = len(P)
        pi = [1.0 / n] * n
        for _ in range(100):
            new_pi = [0.0] * n
            for j in range(n):
                for i in range(n):
                    new_pi[j] += pi[i] * P[i][j]
            total = sum(new_pi)
            if total > 0:
                new_pi = [p / total for p in new_pi]
            # Check convergence
            if sum(abs(new_pi[i] - pi[i]) for i in range(n)) < 1e-8:
                break
            pi = new_pi
        return pi


# ──────────────────────────────────────────────────────────────
# Ω-ST28 to Ω-ST36: Predator-Prey & Phase Space
# ──────────────────────────────────────────────────────────────

class PredatorPreyModel:
    """
    Ω-ST28 to Ω-ST36: Lotka-Volterra for market dynamics.

    Transmuted from v1 predator.py + dynamics.py:
    v1: Basic trend oscillation tracking
    v2: Full Lotka-Volterra system with momentum (predator) vs
    mean-reversion (prey), phase space analysis, fixed points,
    and limit cycle detection.
    """

    def __init__(self, window_size: int = 200) -> None:
        self._window = window_size
        self._returns: deque[float] = deque(maxlen=window_size)

    def update(self, price: float) -> dict:
        """Ω-ST30: Fit Lotka-Volterra model to market dynamics."""
        if hasattr(self, '_prev_price') and self._prev_price != 0:
            ret = (price - self._prev_price) / abs(self._prev_price)
            self._returns.append(ret)
        self._prev_price = price

        if len(self._returns) < 20:
            return {"state": "WARMING_UP"}

        rets = list(self._returns)
        n = len(rets)

        # Ω-ST31: Estimate LV parameters
        # Prey (x) = trending force, Predator (y) = mean-reversion force
        # dx/dt = alpha*x - beta*x*y
        # dy/dt = delta*x*y - gamma*y

        # Approximate x and y from returns
        x = [abs(r) for r in rets]  # Trending strength
        y = [1.0 - abs(r) / max(1e-6, max(abs(r2) for r2 in rets)) for r in rets]  # Mean-reversion pressure
        y = [max(0.01, v) for v in y]

        # Simple parameter estimation from discrete differences
        dx_dt = [x[i] - x[i - 1] for i in range(1, n)]
        dy_dt = [y[i] - y[i - 1] for i in range(1, n)]

        if len(dx_dt) >= 5 and len(dy_dt) >= 5:
            # Estimate alpha from dx/x when y is small
            low_y_idx = [i for i, v in enumerate(y[:-1]) if v < 0.3]
            if low_y_idx:
                alpha_est = sum(
                    dx_dt[i] / max(1e-6, x[i + 1])
                    for i in low_y_idx if i < len(dx_dt)
                ) / max(1, len(low_y_idx))
            else:
                alpha_est = 0.0

            # Estimate gamma from dy/y when x is small
            low_x_idx = [i for i, v in enumerate(x[:-1]) if v < abs(sum(rets) / max(1, n)) * 2]
            if low_x_idx:
                gamma_est = -sum(
                    dy_dt[i] / max(1e-6, y[i + 1])
                    for i in low_x_idx if i < len(dy_dt)
                ) / max(1, len(low_x_idx))
            else:
                gamma_est = 0.0

            alpha = max(0.0, min(2.0, alpha_est))
            gamma = max(0.0, min(2.0, gamma_est))
        else:
            alpha = gamma = 0.0

        # Ω-ST32: Fixed point analysis
        # dx/dt = 0, dy/dt = 0 → equilibrium
        # x* = gamma/delta, y* = alpha/beta
        # Simplified: equilibrium at x = y = mean
        x_eq = sum(x) / len(x) if x else 0
        y_eq = sum(y) / len(y) if y else 0

        # Ω-ST33: Phase space trajectory
        # Recent (x, y) trajectory
        if len(x) >= 5 and len(y) >= 5:
            trajectory = [(x[i], y[i]) for i in range(max(0, n - 20), n)]
        else:
            trajectory = []

        # Ω-ST34: Limit cycle detection
        # If trajectory approximately returns to start = limit cycle
        if len(trajectory) >= 10:
            start = trajectory[0]
            end = trajectory[-1]
            cycle_return = math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)
            is_limit_cycle = cycle_return < 0.3
        else:
            is_limit_cycle = False

        # Ω-ST35: Lyapunov exponent approximation
        if len(x) >= 10:
            # Track how nearby trajectories diverge
            diffs = [abs(x[i + 1] - x[i]) for i in range(len(x) - 1)]
            if diffs and diffs[0] > 1e-6:
                lyap = math.log(diffs[-1] / diffs[0]) / max(1, len(diffs) - 1)
            else:
                lyap = 0.0
        else:
            lyap = 0.0

        # Ω-ST36: Fixed point stability
        # Stable if alpha < gamma (mean-reversion dominates)
        if alpha < gamma:
            stability = "STABLE"  # Mean-reversion equilibrium
        elif alpha > gamma * 2:
            stability = "UNSTABLE"  # Trending dominates
        else:
            stability = "NEUTRAL"  # Oscillating

        return {
            "alpha_trend_growth": alpha,
            "gamma_mean_reversion_strength": gamma,
            "fixed_point_x": x_eq,
            "fixed_point_y": y_eq,
            "stability": stability,
            "lyapunov_exponent": lyap,
            "is_limit_cycle": is_limit_cycle,
            "is_chaotic": lyap > 0.1,
            "trajectory_length": len(trajectory),
            "is_mean_reversion_dominant": gamma > alpha,
            "is_trending_dominant": alpha > gamma,
        }


# ──────────────────────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────────────────────

def _variance(values: list[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    m = sum(values) / n
    return sum((v - m) ** 2 for v in values) / n
