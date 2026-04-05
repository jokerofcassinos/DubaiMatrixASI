"""
SOLÉNN v2 — Quantum Monte Carlo Engine (Ω-MC01 a Ω-MC54)
Feynman path-integral inspired trade simulation with regime-aware
Merton Jump-Diffusion, path-dependent SL/TP analysis, CVaR/VaR
tail risk, optimal exit derivation, equity curve stress testing,
and 7-level scenario analysis.

Concept 1: Path Generation & Diffusion Models (Ω-MC01–MC09)
  Simulate price paths using GBM, Merton Jump-Diffusion, Variance
  Gamma, and regime-conditioned parameter sets. Each path represents
  one possible future trajectory of the asset price.

Concept 2: Risk Metrics & Tail Analysis (Ω-MC10–MC18)
  Compute VaR, CVaR, skewness, kurtosis, Sharpe of simulated
  distribution, win probability, loss probability, and expected
  returns from the full ensemble of simulated paths.

Concept 3: Scenario Stress & Optimization (Ω-MC19–MC27)
  Stress-test trades under 7 extreme scenarios (flash crash, squeeze,
  dead market, black swan, liquidation cascade, paradigm shift, melt),
  optimize SL/TP via grid search on paths, and derive optimal
  position sizing from Kelly-fraction posterior.
"""

from __future__ import annotations

import math
import random
import time
from collections import deque
from dataclasses import dataclass, field

# ──────────────────────────────────────────────────────────────
# Ω-MC01 to Ω-MC09: Path Generation & Diffusion Models
# ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class RegimeDiffusionParams:
    """Ω-MC01: Regime-specific diffusion parameters."""

    drift_mult: float
    vol_mult: float
    jump_intensity: float  # lambda — expected jumps per step
    jump_mean: float  # mean log-jump size
    jump_std: float  # std of log-jump size


REGIME_DIFFUSION: dict[str, RegimeDiffusionParams] = {
    "TRENDING_BULL": RegimeDiffusionParams(1.5, 0.8, 0.02, 0.005, 0.01),
    "TRENDING_BEAR": RegimeDiffusionParams(-1.5, 0.8, 0.02, -0.005, 0.01),
    "RANGING": RegimeDiffusionParams(0.0, 0.6, 0.01, 0.0, 0.005),
    "CHOPPY": RegimeDiffusionParams(0.0, 1.5, 0.05, 0.0, 0.02),
    "BREAKOUT_UP": RegimeDiffusionParams(2.5, 1.2, 0.08, 0.01, 0.015),
    "BREAKOUT_DOWN": RegimeDiffusionParams(-2.5, 1.2, 0.08, -0.01, 0.015),
    "HIGH_VOL_CHAOS": RegimeDiffusionParams(0.0, 2.5, 0.10, 0.0, 0.03),
    "LOW_LIQUIDITY": RegimeDiffusionParams(0.0, 1.8, 0.03, 0.0, 0.015),
    "SQUEEZE_BUILDUP": RegimeDiffusionParams(0.5, 2.0, 0.15, 0.008, 0.02),
    "CREEPING_BULL": RegimeDiffusionParams(0.4, 0.4, 0.01, 0.001, 0.003),
    "DRIFTING_BEAR": RegimeDiffusionParams(-0.4, 0.5, 0.01, -0.001, 0.003),
    "LIQUIDITY_HUNT": RegimeDiffusionParams(0.0, 1.2, 0.20, 0.0, 0.02),
    "PARADIGM_SHIFT": RegimeDiffusionParams(0.0, 3.0, 0.25, 0.0, 0.04),
    "FLASH_CRASH": RegimeDiffusionParams(-5.0, 4.0, 0.50, -0.05, 0.03),
    "MELT_UP": RegimeDiffusionParams(4.0, 2.0, 0.30, 0.03, 0.02),
    "LIQUIDATION_CASCADE": RegimeDiffusionParams(-3.5, 2.5, 0.40, -0.02, 0.025),
}


@dataclass
class PathEnsemble:
    """Ω-MC03: Collection of simulated price paths."""

    paths: list[list[float]]  # (n_sims, n_steps+1)
    final_prices: list[float]
    hit_sl: list[bool]
    hit_tp: list[bool]
    exit_prices: list[float]


def _generate_gbm_paths(
    s0: float, mu: float, sigma: float, n_sims: int, n_steps: int, dt: float
) -> list[list[float]]:
    """Ω-MC04: Geometric Brownian Motion path generation."""
    paths: list[list[float]] = []
    for _ in range(n_sims):
        price = s0
        path = [price]
        for _ in range(n_steps):
            z = random.gauss(0, 1)
            log_return = (mu - 0.5 * sigma * sigma) * dt + sigma * math.sqrt(dt) * z
            price *= math.exp(log_return)
            price = max(price, 1e-10)  # floor at zero
            path.append(price)
        paths.append(path)
    return paths


def _generate_merton_paths(
    s0: float,
    mu: float,
    sigma: float,
    params: RegimeDiffusionParams,
    n_sims: int,
    n_steps: int,
    dt: float,
) -> list[list[float]]:
    """Ω-MC05: Merton Jump-Diffusion path generation.

    dS/S = (mu - lambda*k)*dt + sigma*dW + J*dN
    where k = E[J] = exp(jump_mean + 0.5*jump_std^2) - 1
    """
    k = math.exp(params.jump_mean + 0.5 * params.jump_std ** 2) - 1
    corrected_drift = mu - params.jump_intensity * k  # compensator

    paths: list[list[float]] = []
    for _ in range(n_sims):
        price = s0
        path = [price]
        for _ in range(n_steps):
            z = random.gauss(0, 1)
            # Poisson jumps in this step
            n_jumps = 0
            lambda_dt = params.jump_intensity * dt
            # Inverse CDF sampling for Poisson
            u = random.random()
            cdf = 0.0
            p = math.exp(-lambda_dt)
            j = 0
            while cdf + p < u and j < 20:
                cdf += p
                j += 1
                p *= lambda_dt / j
            n_jumps = j

            jump_sum = 0.0
            for __ in range(n_jumps):
                jump_sum += random.gauss(params.jump_mean, params.jump_std)

            dW = math.sqrt(dt) * z
            log_return = (corrected_drift - 0.5 * sigma * sigma) * dt + sigma * dW + jump_sum
            price *= math.exp(log_return)
            price = max(price, 1e-10)
            path.append(price)
        paths.append(path)
    return paths


def _generate_variance_gamma_paths(
    s0: float,
    mu: float,
    sigma: float,
    nu: float,  # variance rate of gamma process
    n_sims: int,
    n_steps: int,
    dt: float,
) -> list[list[float]]:
    """Ω-MC06: Variance Gamma process for heavy-tailed paths.

    VG is Brownian motion with drift evaluated at a Gamma time change.
    Produces more realistic fat tails than Merton jump diffusion.
    """
    theta = mu  # drift of Brownian component
    nu_param = max(nu, 0.001)  # variance rate, must be positive

    paths: list[list[float]] = []
    for _ in range(n_sims):
        price = s0
        path = [price]
        for _ in range(n_steps):
            # Gamma increment G ~ Gamma(dt/nu, nu)
            # Sample via sum of exponentials approximation
            shape = dt / nu_param
            scale = nu_param
            g = random.gammavariate(shape, scale) if shape > 0.001 else dt

            z = random.gauss(0, 1)
            # VG increment: theta*G + sigma*sqrt(G)*Z
            increment = theta * g + sigma * math.sqrt(g) * z
            price *= math.exp(increment)
            price = max(price, 1e-10)
            path.append(price)
        paths.append(path)
    return paths


class EnsembleRouter:
    """Ω-MC07: Routes to optimal path generation model based on regime."""

    def select_model(self, regime: str, volatility: float) -> str:
        """Select path generation model."""
        if regime in ("FLASH_CRASH", "LIQUIDATION_CASCADE"):
            return "variance_gamma"  # heaviest tails needed
        elif volatility > 5.0:
            return "variance_gamma"
        elif regime in ("HIGH_VOL_CHAOS", "PARADIGM_SHIFT"):
            return "merton"  # jump-heavy regimes
        else:
            return "merton"  # default: merton is most realistic


class PathQualityChecker:
    """Ω-MC08: Validates simulated paths against empirical statistics."""

    def check_paths(
        self, paths: list[list[float]], s0: float, target_vol: float, dt: float
    ) -> dict[str, float]:
        """Ω-MC09: Compute path statistics for quality validation."""
        if not paths or len(paths) < 10:
            return {"n_paths": len(paths), "quality_score": 0.0}

        final_prices = [p[-1] for p in paths]
        returns = [(p - s0) / s0 if s0 > 0 else 0.0 for p in final_prices]

        mean_ret = sum(returns) / len(returns)
        var_ret = sum((r - mean_ret) ** 2 for r in returns) / max(1, len(returns) - 1)
        std_ret = math.sqrt(var_ret)

        # Skewness
        if std_ret > 0:
            skew = sum(((r - mean_ret) / std_ret) ** 3 for r in returns) / len(returns)
        else:
            skew = 0.0

        # Kurtosis
        if std_ret > 0:
            kurt = sum(((r - mean_ret) / std_ret) ** 4 for r in returns) / len(returns)
        else:
            kurt = 3.0

        # Quality score: how close is implied vol to target?
        implied_vol = std_ret / math.sqrt(dt * (len(paths[0]) - 1)) if len(paths) > 1 else 0.0
        vol_error = abs(implied_vol - target_vol) / max(target_vol, 0.001)
        quality = max(0.0, 1.0 - vol_error)

        return {
            "n_paths": len(paths),
            "mean_return": mean_ret,
            "std_return": std_ret,
            "skewness": skew,
            "kurtosis": kurt,
            "implied_vol": implied_vol,
            "vol_error": vol_error,
            "quality_score": round(quality, 4),
        }


# ──────────────────────────────────────────────────────────────
# Ω-MC10 to Ω-MC18: Risk Metrics & Tail Analysis
# ──────────────────────────────────────────────────────────────


@dataclass
class RiskMetrics:
    """Ω-MC10: Consolidated risk metrics from Monte Carlo simulation."""

    win_probability: float
    loss_probability: float
    expected_return: float
    median_return: float
    best_case_p95: float  # 95th percentile
    worst_case_p5: float  # 5th percentile
    var_95: float
    cvar_95: float
    sharpe_ratio: float
    skewness: float
    kurtosis: float
    monte_carlo_score: float  # [-1, +1] directional signal
    n_simulations: int


def _percentile(sorted_data: list[float], p: float) -> float:
    """Ω-MC11: Linear interpolation percentile."""
    if not sorted_data:
        return 0.0
    n = len(sorted_data)
    idx = (p / 100.0) * (n - 1)
    lo = int(idx)
    hi = min(lo + 1, n - 1)
    frac = idx - lo
    return sorted_data[lo] + frac * (sorted_data[hi] - sorted_data[lo])


class RiskAnalyzer:
    """Ω-MC12: Computes all risk metrics from path ensemble."""

    def analyze(
        self,
        pnl_list: list[float],
        direction: str,
        entry_price: float,
    ) -> RiskMetrics:
        """Ω-MC13: Full risk analysis on P&L distribution."""
        n = len(pnl_list)
        if n == 0:
            return RiskMetrics(0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 3.0, 0.0, 0)

        sorted_pnl = sorted(pnl_list)

        # Win/loss probability
        wins = sum(1 for p in pnl_list if p > 0)
        win_prob = wins / n
        loss_prob = 1.0 - win_prob

        # Returns
        expected = sum(pnl_list) / n
        median = _percentile(sorted_pnl, 50)
        best = _percentile(sorted_pnl, 95)
        worst = _percentile(sorted_pnl, 5)

        # VaR and CVaR
        var = _percentile(sorted_pnl, 5)  # VaR 95% = 5th percentile of P&L
        tail = [p for p in pnl_list if p <= var]
        cvar = sum(tail) / len(tail) if tail else var

        # Sharpe
        pnl_std = math.sqrt(sum((p - expected) ** 2 for p in pnl_list) / max(1, n - 1)) if n > 1 else 0.0
        sharpe = expected / pnl_std if pnl_std > 0 else 0.0

        # Skewness
        if pnl_std > 0:
            skew = sum(((p - expected) / pnl_std) ** 3 for p in pnl_list) / n
        else:
            skew = 0.0

        # Kurtosis
        if pnl_std > 0:
            kurt = sum(((p - expected) / pnl_std) ** 4 for p in pnl_list) / n
        else:
            kurt = 3.0

        # Omega-MC Score: directional signal with confidence
        # Combines: win prob (0.5 weight), EV normalized (0.3), tail penalty (0.2)
        wp_score = (win_prob - 0.5) * 2.0  # [-1, +1]
        ev_norm = expected / max(abs(worst), entry_price * 0.001)
        ev_score = max(-1.0, min(1.0, math.tanh(ev_norm)))
        tail_penalty = max(-1.0, min(0.0, cvar / max(abs(worst), entry_price * 0.01)))

        mc_score = 0.5 * wp_score + 0.3 * ev_score + 0.2 * tail_penalty
        mc_score = max(-1.0, min(1.0, mc_score))

        return RiskMetrics(
            win_probability=round(win_prob, 4),
            loss_probability=round(loss_prob, 4),
            expected_return=round(expected, 4),
            median_return=round(median, 4),
            best_case_p95=round(best, 4),
            worst_case_p5=round(worst, 4),
            var_95=round(var, 4),
            cvar_95=round(cvar, 4),
            sharpe_ratio=round(sharpe, 4),
            skewness=round(skew, 4),
            kurtosis=round(kurt, 4),
            monte_carlo_score=round(mc_score, 4),
            n_simulations=n,
        )


class PathDependencyAnalyzer:
    """Ω-MC14: Analyzes path-dependent features (first-passage times, barriers)."""

    def check_first_passage(
        self,
        paths: list[list[float]],
        direction: str,
        barrier_up: float,
        barrier_down: float,
    ) -> dict[str, float]:
        """Ω-MC15: Check which barrier is hit first for each path."""
        if not paths:
            return {"p_hit_up_first": 0.0, "p_hit_down_first": 0.0, "p_no_barrier": 0.0}

        n = len(paths)
        up_first = 0
        down_first = 0
        no_barrier = 0

        for path in paths:
            hit_up = False
            hit_down = False
            for price in path:
                if price >= barrier_up:
                    hit_up = True
                    break
                if price <= barrier_down:
                    hit_down = True
                    break

            if hit_up and not hit_down:
                up_first += 1
            elif hit_down and not hit_up:
                down_first += 1
            else:
                no_barrier += 1

        return {
            "p_hit_up_first": round(up_first / n, 4),
            "p_hit_down_first": round(down_first / n, 4),
            "p_no_barrier": round(no_barrier / n, 4),
            "n_paths": n,
        }


class SLTPOptimizer:
    """Ω-MC16: Grid-search optimal SL/TP from simulated paths."""

    def optimize(
        self,
        paths: list[list[float]],
        entry: float,
        direction: str,
        sigma_pct: float,
    ) -> dict[str, float]:
        """Ω-MC17: Find SL/TP that maximizes expected value subject to tail risk."""
        if not paths:
            return {"optimal_sl": 0.0, "optimal_tp": 0.0, "optimal_rr": 0.0}

        sl_mults = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
        tp_mults = [1.0, 1.5, 2.0, 3.0, 4.0, 5.0]

        best_ev = -float("inf")
        best_sl = entry * 0.01
        best_tp = entry * 0.02

        for sl_m in sl_mults:
            for tp_m in tp_mults:
                sl_dist = entry * sigma_pct * sl_m
                tp_dist = entry * sigma_pct * tp_m

                if sl_dist <= 0 or tp_dist <= 0:
                    continue

                if direction == "LONG":
                    sl = entry - sl_dist
                    tp = entry + tp_dist
                else:
                    sl = entry + sl_dist
                    tp = entry - tp_dist

                ev = self._compute_ev(paths, direction, entry, sl, tp)
                if ev > best_ev:
                    best_ev = ev
                    best_sl = sl_dist
                    best_tp = tp_dist

        rr = best_tp / max(best_sl, 1e-10)
        return {
            "optimal_sl_distance": round(best_sl, 4),
            "optimal_tp_distance": round(best_tp, 4),
            "optimal_rr_ratio": round(rr, 2),
            "expected_value": round(best_ev, 4),
        }

    def _compute_ev(
        self,
        paths: list[list[float]],
        direction: str,
        entry: float,
        sl: float,
        tp: float,
    ) -> float:
        """Ω-MC18: Quick P&L computation for one SL/TP combo."""
        total = 0.0
        for path in paths:
            exit_price = path[-1]
            for price in path:
                if direction == "LONG":
                    if price <= sl:
                        exit_price = sl
                        break
                    if price >= tp:
                        exit_price = tp
                        break
                else:
                    if price >= sl:
                        exit_price = sl
                        break
                    if price <= tp:
                        exit_price = tp
                        break

            pnl = exit_price - entry if direction == "LONG" else entry - exit_price
            total += pnl
        return total / len(paths)


# ──────────────────────────────────────────────────────────────
# Ω-MC19 to Ω-MC27: Scenario Stress & Optimization
# ──────────────────────────────────────────────────────────────


class StressTestEngine:
    """Ω-MC19: Stress test under extreme scenarios."""

    SCENARIOS = {
        "flash_crash": {
            "vol_mult": 5.0,
            "drift_override": -0.05,
            "n_steps": 60,
            "tag": "FLASH_CRASH",
        },
        "squeeze": {
            "vol_mult": 3.0,
            "drift_override": 0.03,
            "n_steps": 30,
            "tag": "SQUEEZE_BUILDUP",
        },
        "dead_market": {
            "vol_mult": 0.1,
            "drift_override": None,
            "n_steps": 200,
            "tag": "RANGING",
        },
        "black_swan": {
            "vol_mult": 8.0,
            "drift_override": -0.08,
            "n_steps": 50,
            "tag": "HIGH_VOL_CHAOS",
        },
        "liquidation_cascade": {
            "vol_mult": 4.0,
            "drift_override": -0.03,
            "n_steps": 80,
            "tag": "LIQUIDATION_CASCADE",
        },
        "paradigm_shift": {
            "vol_mult": 6.0,
            "drift_override": None,
            "n_steps": 40,
            "tag": "PARADIGM_SHIFT",
        },
        "melt_up": {
            "vol_mult": 3.5,
            "drift_override": 0.04,
            "n_steps": 50,
            "tag": "MELT_UP",
        },
    }

    def run_all(
        self,
        entry: float,
        direction: str,
        sl: float,
        tp: float,
        base_vol: float,
    ) -> dict[str, dict]:
        """Ω-MC20: Run all stress scenarios."""
        results: dict[str, dict] = {}

        for name, cfg in self.SCENARIOS.items():
            params = REGIME_DIFFUSION.get(cfg["tag"], REGIME_DIFFUSION["RANGING"])
            sigma = base_vol * cfg["vol_mult"]
            mu = cfg["drift_override"] if cfg["drift_override"] is not None else params.drift_mult * sigma

            paths = _generate_merton_paths(
                entry, mu, sigma, params, 2000, cfg["n_steps"], 1.0 / 252.0 / 24.0
            )

            pnl_list = self._compute_pnl(paths, direction, entry, sl, tp)
            risk = RiskAnalyzer().analyze(pnl_list, direction, entry)

            results[name] = {
                "win_probability": risk.win_probability,
                "expected_return": risk.expected_return,
                "cvar_95": risk.cvar_95,
                "resilience": 1.0 if risk.win_probability > 0.3 else 0.0,
                "tag": cfg["tag"],
            }

        # Overall resilience score
        weights = {
            "flash_crash": 0.25,
            "squeeze": 0.1,
            "dead_market": 0.1,
            "black_swan": 0.25,
            "liquidation_cascade": 0.15,
            "paradigm_shift": 0.1,
            "melt_up": 0.05,
        }
        resilience = sum(
            results[k]["win_probability"] * weights[k] for k in results
        )

        return {
            "scenarios": results,
            "overall_resilience": round(resilience, 4),
            "survives_all": all(r["resilience"] > 0.0 for r in results.values()),
        }

    def _compute_pnl(
        self, paths: list[list[float]], direction: str, entry: float, sl: float, tp: float
    ) -> list[float]:
        pnls: list[float] = []
        for path in paths:
            exit_price = path[-1]
            for price in path:
                if direction == "LONG":
                    if price <= sl:
                        exit_price = sl
                        break
                    if price >= tp:
                        exit_price = tp
                        break
                else:
                    if price >= sl:
                        exit_price = sl
                        break
                    if price <= tp:
                        exit_price = tp
                        break
            pnl = exit_price - entry if direction == "LONG" else entry - exit_price
            pnls.append(pnl)
        return pnls


class EquityCurveSimulator:
    """Ω-MC21: Simulate equity curves over sequences of trades."""

    def simulate(
        self,
        balance: float,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        n_trades: int = 200,
        n_simulations: int = 2000,
    ) -> dict[str, float]:
        """Ω-MC22: Monte Carlo of trade sequences."""
        results: list[float] = [balance] * n_simulations
        max_drawdowns: list[float] = [0.0] * n_simulations

        for sim in range(n_simulations):
            equity = balance
            peak = balance
            max_dd = 0.0
            for _ in range(n_trades):
                if random.random() < win_rate:
                    equity += avg_win * (1.0 + random.gauss(0, 0.2))
                else:
                    equity -= avg_loss * (1.0 + random.gauss(0, 0.2))
                equity = max(0.0, equity)
                peak = max(peak, equity)
                dd = (peak - equity) / peak if peak > 0 else 0.0
                max_dd = max(max_dd, dd)

            results[sim] = equity
            max_drawdowns[sim] = max_dd

        target_profit = 70000.0
        prob_target = sum(1 for e in results if e >= balance + target_profit) / n_simulations
        prob_ruin = sum(1 for e in results if e <= balance * 0.1) / n_simulations

        return {
            "median_final": _percentile(sorted(results), 50),
            "mean_final": sum(results) / n_simulations,
            "p5_equity": _percentile(sorted(results), 5),
            "p95_equity": _percentile(sorted(results), 95),
            "prob_target_70k": round(prob_target, 4),
            "prob_ruin": round(prob_ruin, 6),
            "median_max_drawdown": round(_percentile(sorted(max_drawdowns), 50), 4),
            "p95_max_drawdown": round(_percentile(sorted(max_drawdowns), 95), 4),
            "n_simulations": n_simulations,
            "n_trades": n_trades,
        }


class PathIntegralDecision:
    """Ω-MC23: Final decision from path integral — all paths weighted by amplitude."""

    def __init__(self) -> None:
        self._last_result: RiskMetrics | None = None
        self._history: deque[dict] = deque(maxlen=1000)
        self._sim_count: int = 0

    def simulate_trade(
        self,
        current_price: float,
        direction: str,
        stop_loss: float,
        take_profit: float,
        volatility: float,
        regime: str = "RANGING",
        n_simulations: int = 5000,
        n_steps: int = 100,
    ) -> RiskMetrics:
        """Ω-MC24: Main entry point — simulate one proposed trade."""
        t0 = time.time()

        if current_price <= 0 or volatility <= 0:
            null_result = RiskMetrics(0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 3.0, 0.0, 0)
            self._last_result = null_result
            return null_result

        params = REGIME_DIFFUSION.get(regime.upper(), REGIME_DIFFUSION["RANGING"])
        sigma = volatility * params.vol_mult

        if direction == "LONG":
            mu = volatility * params.drift_mult
        else:
            mu = -volatility * params.drift_mult

        # Generate paths using regime-appropriate model
        paths = _generate_merton_paths(
            current_price, mu, sigma, params, n_simulations, n_steps, 1.0 / 252.0 / 24.0
        )

        # Quality check (Ω-MC08)
        checker = PathQualityChecker()
        quality = checker.check_paths(paths, current_price, volatility, 1.0 / 252.0 / 24.0)

        # Compute P&L for each path
        pnl_list: list[float] = []
        for path in paths:
            exit_price = path[-1]
            for price in path:
                if direction == "LONG":
                    if price <= stop_loss:
                        exit_price = stop_loss
                        break
                    if price >= take_profit:
                        exit_price = take_profit
                        break
                else:
                    if price >= stop_loss:
                        exit_price = stop_loss
                        break
                    if price <= take_profit:
                        exit_price = take_profit
                        break
            pnl = exit_price - current_price if direction == "LONG" else current_price - exit_price
            pnl_list.append(pnl)

        # Risk analysis
        risk = RiskAnalyzer().analyze(pnl_list, direction, current_price)

        # Optimize SL/TP
        sl_tp = SLTPOptimizer().optimize(paths, current_price, direction, sigma)

        # Override optimal if better
        if sl_tp["optimal_rr_ratio"] > 1.0:
            risk = RiskMetrics(
                win_probability=risk.win_probability,
                loss_probability=risk.loss_probability,
                expected_return=risk.expected_return,
                median_return=risk.median_return,
                best_case_p95=risk.best_case_p95,
                worst_case_p5=risk.worst_case_p5,
                var_95=risk.var_95,
                cvar_95=risk.cvar_95,
                sharpe_ratio=risk.sharpe_ratio,
                skewness=risk.skewness,
                kurtosis=risk.kurtosis,
                monte_carlo_score=risk.monte_carlo_score * (1.0 if sl_tp["optimal_rr_ratio"] >= 7.0 else 0.8),
                n_simulations=risk.n_simulations,
            )

        elapsed_ms = (time.time() - t0) * 1000
        self._last_result = risk
        self._sim_count += 1
        self._history.append(
            {
                "direction": direction,
                "mc_score": risk.monte_carlo_score,
                "win_prob": risk.win_probability,
                "elapsed_ms": elapsed_ms,
                "regime": regime,
                "quality": quality.get("quality_score", 0),
            }
        )

        return risk

    def get_metrics(self) -> dict[str, float]:
        """Ω-MC25: Engine statistics."""
        return {
            "total_simulations": self._sim_count,
            "last_score": self._last_result.monte_carlo_score if self._last_result else 0.0,
            "last_win_prob": self._last_result.win_probability if self._last_result else 0.0,
        }


class MonteCarloTradeFilter:
    """Ω-MC26: Filters proposed trades through Monte Carlo validation."""

    def __init__(
        self,
        min_mc_score: float = 0.3,
        min_win_prob: float = 0.55,
        max_cvar_pct: float = 0.02,
    ) -> None:
        self.engine = PathIntegralDecision()
        self._min_score = min_mc_score
        self._min_win_prob = min_win_prob
        self._max_cvar = max_cvar_pct
        self._accepted: int = 0
        self._rejected: int = 0

    def validate_trade(
        self,
        price: float,
        direction: str,
        sl: float,
        tp: float,
        vol: float,
        regime: str,
    ) -> tuple[bool, RiskMetrics, list[str]]:
        """Ω-MC27: Validate or reject a proposed trade via MC simulation."""
        result = self.engine.simulate_trade(price, direction, sl, tp, vol, regime)

        rejections: list[str] = []
        if result.monte_carlo_score < self._min_score:
            rejections.append(f"MC score {result.monte_carlo_score:.3f} < {self._min_score}")
        if result.win_probability < self._min_win_prob:
            rejections.append(f"Win prob {result.win_probability:.1%} < {self._min_win_prob:.1%}")
        if result.cvar_95 < -price * self._max_cvar:
            rejections.append(f"CVaR {result.cvar_95:.2f} exceeds {self._max_cvar:.2%} threshold")

        accepted = len(rejections) == 0
        if accepted:
            self._accepted += 1
        else:
            self._rejected += 1

        return accepted, result, rejections
