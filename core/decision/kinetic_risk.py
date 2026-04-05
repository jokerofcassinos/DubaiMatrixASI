"""
SOLÉNN v2 — Kinetic Risk Engine (Ω-T55 to Ω-T108)
Kelly Criterion Bayesian sizing, 7-level circuit breaker system,
position risk monitoring, dynamic stop & exit engine, tail risk protection,
and portfolio risk optimization.

Concept 2: Kelly Bayesian Sizing (Ω-T55–T63)
Concept 2: Circuit Breaker System (Ω-T64–T72)
Concept 2: Position Risk Monitor (Ω-T73–T81)
Concept 2: Dynamic Stop & Exit Engine (Ω-T82–T90)
Concept 2: Tail Risk Protection (Ω-T91–T99)
Concept 2: Portfolio Risk Optimizer (Ω-T100–T108)
"""

from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from .omega_types import (
    CircuitBreakerLevel,
    TailRiskMetrics,
)


# ──────────────────────────────────────────────────────────────
# Ω-T55 to Ω-T63: Bayesian Kelly Criterion Sizing
# ──────────────────────────────────────────────────────────────

@dataclass
class _KellyState:
    alpha: float  # Beta distribution alpha (wins + prior)
    beta: float  # Beta distribution beta (losses + prior)
    payoff_mean: float  # Mean payoff ratio
    payoff_std: float  # Std of payoff ratio
    n_samples: int  # Number of observations
    current_kelly: float  # Current Kelly fraction
    kelly_history: deque[float]  # History of Kelly estimates


class BayesianKellyEstimator:
    """
    Ω-T55–T63: Bayesian Kelly Criterion with posterior distributions,
    fractional Kelly, uncertainty adjustment, drawdown adjustment,
    CVaR constraint, regime-specific weights, and anti-gambler cap.
    """

    def __init__(
        self,
        prior_wins: float = 50.0,
        prior_losses: float = 50.0,
        initial_payoff_mean: float = 1.5,
        initial_payoff_std: float = 0.8,
        kelly_fraction: float = 0.25,  # Quarter-Kelly default
        max_absolute_kelly: float = 0.25,  # Anti-gambler cap
    ) -> None:
        self._wins: int = 0
        self._losses: int = 0
        self._prior_alpha = prior_wins
        self._prior_beta = prior_losses
        self._payoff_mean = initial_payoff_mean
        self._payoff_std = initial_payoff_std
        self._kelly_fraction = kelly_fraction
        self._max_kelly = max_absolute_kelly
        self._payoff_samples: deque[float] = deque(maxlen=500)
        self._kelly_state = _KellyState(
            alpha=prior_wins,
            beta=prior_losses,
            payoff_mean=initial_payoff_mean,
            payoff_std=initial_payoff_std,
            n_samples=0,
            current_kelly=0.0,
            kelly_history=deque(maxlen=1000),
        )
        # Ω-T58: Per-regime Kelly trackers
        self._regime_payoffs: dict[str, list[float]] = {}
        # Ω-T59: Drawdown adjustment
        self._current_drawdown = 0.0

    def update(self, pnl: float, was_win: bool) -> float:
        """Ω-T55/T56/T57: Update posterior and compute new Kelly fraction."""
        self._payoff_samples.append(pnl)

        if was_win:
            self._wins += 1
        else:
            self._losses += 1

        # Ω-T21: Bayesian update (Beta-Bernoulli)
        alpha = self._wins + self._prior_alpha
        beta_p = self._losses + self._prior_beta

        # Win rate posterior mean
        win_rate = alpha / (alpha + beta_p)

        # Ω-T21: Payoff ratio posterior
        avg_win = self._compute_avg_payoff() if self._wins > 0 else 0.0
        avg_loss = self._compute_avg_loss() if self._losses > 0 else 0.0
        b = avg_loss if avg_loss > 0 else 1.0  # Payoff ratio = avg_win / _loss
        payoff_ratio = avg_win / b if b > 0 else 1.0

        # Ω-T55: Kelly f* = (bp - q) / b
        q = 1.0 - win_rate
        raw_kelly = (payoff_ratio * win_rate - q) / payoff_ratio if payoff_ratio > 0 else 0.0
        raw_kelly = max(0.0, raw_kelly)  # Never negative Kelly

        # Ω-T56: Fractional Kelly
        fractional_kelly = raw_kelly * self._kelly_fraction

        # Ω-T57: Uncertainty adjustment
        var = (alpha * beta_p) / ((alpha + beta_p) ** 2 * (alpha + beta_p + 1))
        cv = math.sqrt(var) / win_rate if win_rate > 0 else 1.0
        uncertainty_adjusted = fractional_kelly * (1.0 - cv)
        uncertainty_adjusted = max(0.0, uncertainty_adjusted)

        # Ω-T59: Drawdown adjustment
        dd_factor = self._compute_drawdown_factor()
        dd_adjusted = uncertainty_adjusted * dd_factor

        # Ω-T60: CVaR constraint
        cvar_limit = self._compute_cvar_limit()
        sizing = min(dd_adjusted, cvar_limit)

        # Anti-gambler cap
        sizing = min(sizing, self._max_kelly)

        # Update state
        self._kelly_state = _KellyState(
            alpha=alpha,
            beta=beta_p,
            payoff_mean=payoff_ratio,
            payoff_std=self._payoff_std,
            n_samples=self._kelly_state.n_samples + 1,
            current_kelly=sizing,
            kelly_history=self._kelly_state.kelly_history,
        )
        self._kelly_state.kelly_history.append(sizing)

        return sizing

    def _compute_avg_payoff(self) -> float:
        wins = [p for p in self._payoff_samples if p > 0]
        return sum(wins) / len(wins) if wins else 0.0

    def _compute_avg_loss(self) -> float:
        losses = [abs(p) for p in self._payoff_samples if p < 0]
        return sum(losses) / len(losses) if losses else 1.0

    def _compute_drawdown_factor(self) -> float:
        """Ω-T59: Reduce Kelly as drawdown increases."""
        if self._current_drawdown < 0.3:
            return 1.0
        elif self._current_drawdown < 1.0:
            return 0.5
        elif self._current_drawdown < 2.0:
            return 0.25
        else:
            return 0.0

    def _compute_cvar_limit(self) -> float:
        """Ω-T60: CVaR-based sizing constraint."""
        if len(self._payoff_samples) < 20:
            return 0.5  # Conservative default
        sorted_pnl = sorted(self._payoff_samples)
        n_tail = max(1, int(len(sorted_pnl) * 0.005))  # 99.5% CVaR
        tail = sorted_pnl[:n_tail]
        cvar = abs(sum(tail) / len(tail)) if tail else 0.0
        # Limit sizing so that max loss < 1% of capital
        return min(0.5, 0.01 / cvar) if cvar > 0 else 0.5

    def update_drawdown(self, drawdown_pct: float) -> None:
        """Ω-T59: Update current drawdown for adjustment."""
        self._current_drawdown = drawdown_pct

    def update_regime_payoff(self, regime_key: str, pnl: float) -> None:
        """Ω-T62: Track regime-specific payoffs."""
        if regime_key not in self._regime_payoffs:
            self._regime_payoffs[regime_key] = []
        self._regime_payoffs[regime_key].append(pnl)

    def get_regime_kelly(self, regime_key: str) -> float:
        """Ω-T62: Get Kelly fraction adjusted for specific regime."""
        if regime_key not in self._regime_payoffs or len(self._regime_payoffs[regime_key]) < 10:
            return self._kelly_state.current_kelly
        payoffs = self._regime_payoffs[regime_key]
        wins = sum(1 for p in payoffs if p > 0)
        n = len(payoffs)
        regime_wr = wins / n
        avg_regime_win = sum(p for p in payoffs if p > 0) / max(1, wins)
        avg_regime_loss = abs(sum(p for p in payoffs if p < 0)) / max(1, n - wins)
        b = avg_regime_win / avg_regime_loss if avg_regime_loss > 0 else 1.0
        regime_kelly = (b * regime_wr - (1 - regime_wr)) / b if b > 0 else 0.0
        regime_kelly = max(0.0, regime_kelly) * self._kelly_fraction * self._compute_drawdown_factor()
        return min(regime_kelly, self._max_kelly)

    def get_state(self) -> dict[str, Any]:
        return {
            "current_kelly": self._kelly_state.current_kelly,
            "wins": self._wins,
            "losses": self._losses,
            "win_rate": (self._wins + self._prior_alpha) / (self._wins + self._losses + self._prior_alpha + self._prior_beta),
            "payoff_ratio": self._kelly_state.payoff_mean,
            "n_samples": self._kelly_state.n_samples,
            "drawdown_factor": self._compute_drawdown_factor(),
        }


# ──────────────────────────────────────────────────────────────
# Ω-T64 to Ω-T72: Circuit Breaker System
# ──────────────────────────────────────────────────────────────

@dataclass
class CircuitBreakerState:
    current_level: CircuitBreakerLevel
    current_drawdown: float
    consecutive_losses: int
    volatility: float
    trigger_reason: str | None
    trigger_time: float | None
    cooldown_remaining: float  # Seconds remaining in cooldown
    recovery_stage: int  # 0 = not recovering, 1-4 = recovery stages


class CircuitBreakerSystem:
    """
    Ω-T64–T72: Seven-level circuit breaker with auto-recovery,
    FTMO compliance layer, and multi-trigger activation.
    """

    def __init__(
        self,
        daily_loss_limit: float = 5.0,  # FTMO-style 5%
        total_loss_limit: float = 10.0,  # FTMO-style 10%
        max_consecutive_losses: int = 5,
        extreme_vol_threshold: float = 10.0,
        max_latency_multiplier: float = 2.0,
    ) -> None:
        self._state = CircuitBreakerState(
            current_level=CircuitBreakerLevel.GREEN,
            current_drawdown=0.0,
            consecutive_losses=0,
            volatility=0.0,
            trigger_reason=None,
            trigger_time=None,
            cooldown_remaining=0.0,
            recovery_stage=0,
        )
        self._daily_loss_limit = daily_loss_limit
        self._total_loss_limit = total_loss_limit
        self._max_consecutive = max_consecutive_losses
        self._extreme_vol = extreme_vol_threshold
        self._latency_multiplier = max_latency_multiplier
        self._trigger_history: list[dict[str, Any]] = []
        self._recovery_active = False

    def evaluate(
        self,
        drawdown_pct: float,
        consecutive_losses: int,
        volatility: float,
        latency_ms: float,
        avg_latency_ms: float,
        data_quality_score: float,
    ) -> CircuitBreakerState:
        """Ω-T64–T70: Evaluate all circuit breaker triggers."""
        self._state.current_drawdown = drawdown_pct
        self._state.consecutive_losses = consecutive_losses
        self._state.volatility = volatility

        # Update cooldown
        if self._state.cooldown_remaining > 0:
            self._state.cooldown_remaining = max(0, self._state.cooldown_remaining)

        # Ω-T65: Drawdown triggers
        if drawdown_pct > 3.0:
            self._trigger(CircuitBreakerLevel.CATASTROPHIC, f"Drawdown {drawdown_pct}% > 3.0%")
        elif drawdown_pct > 2.0:
            self._trigger(CircuitBreakerLevel.EMERGENCY, f"Drawdown {drawdown_pct}% > 2.0%")
        elif drawdown_pct > 1.5:
            self._trigger(CircuitBreakerLevel.CRITICAL, f"Drawdown {drawdown_pct}% > 1.5%")
        elif drawdown_pct > 1.0:
            self._trigger(CircuitBreakerLevel.RED, f"Drawdown {drawdown_pct}% > 1.0%")
        elif drawdown_pct > 0.5:
            self._trigger(CircuitBreakerLevel.ORANGE, f"Drawdown {drawdown_pct}% > 0.5%")
        elif drawdown_pct > 0.3:
            self._trigger(CircuitBreakerLevel.YELLOW, f"Drawdown {drawdown_pct}% > 0.3%")

        # Ω-T66: Consecutive losses
        elif consecutive_losses > self._max_consecutive:
            self._trigger(
                CircuitBreakerLevel.RED,
                f"Consecutive losses {consecutive_losses} > {self._max_consecutive}",
            )

        # Ω-T67: Volatility
        elif volatility > self._extreme_vol:
            self._trigger(
                CircuitBreakerLevel.CRITICAL,
                f"Volatility {volatility} > {self._extreme_vol}",
            )

        # Ω-T68: Latency
        elif avg_latency_ms > 0 and latency_ms > avg_latency_ms * self._latency_multiplier:
            if self._state.current_level.value not in (
                CircuitBreakerLevel.RED.value,
                CircuitBreakerLevel.CRITICAL.value,
                CircuitBreakerLevel.EMERGENCY.value,
                CircuitBreakerLevel.CATASTROPHIC.value,
            ):
                self._trigger(
                    CircuitBreakerLevel.YELLOW,
                    f"Latency {latency_ms:.0f}ms > {avg_latency_ms * self._latency_multiplier:.0f}ms",
                )

        # Ω-T69: Data quality
        elif data_quality_score < 0.5:
            self._trigger(
                CircuitBreakerLevel.ORANGE,
                f"Data quality {data_quality_score} < 0.5",
            )

        else:
            # Clear to GREEN if no triggers
            if self._state.current_level != CircuitBreakerLevel.GREEN:
                self._state.current_level = CircuitBreakerLevel.GREEN
                self._state.trigger_reason = None
                self._state.trigger_time = None

        return self._state

    def _trigger(self, level: CircuitBreakerLevel, reason: str) -> None:
        """Activate circuit breaker and record history."""
        # Only escalate, never de-escalate in same evaluation
        if level.trigger_dd_pct > self._state.current_level.trigger_dd_pct:
            self._state.current_level = level
            self._state.trigger_reason = reason
            self._state.trigger_time = time.time()

            if level == CircuitBreakerLevel.RED:
                self._state.cooldown_remaining = 300.0  # 5 min
                self._state.recovery_stage = 0
            elif level == CircuitBreakerLevel.CRITICAL:
                self._state.cooldown_remaining = 900.0  # 15 min
                self._state.recovery_stage = 0
            elif level == CircuitBreakerLevel.EMERGENCY:
                self._state.cooldown_remaining = 3600.0  # 1 hour
                self._state.recovery_stage = 0
            elif level == CircuitBreakerLevel.CATASTROPHIC:
                self._state.cooldown_remaining = 7200.0  # 2 hours
                self._state.recovery_stage = 0
            elif level == CircuitBreakerLevel.ORANGE:
                self._state.cooldown_remaining = 60.0
                self._state.recovery_stage = 1
            elif level == CircuitBreakerLevel.YELLOW:
                self._state.cooldown_remaining = 30.0
                self._state.recovery_stage = 1

            self._trigger_history.append({
                "level": level.value,
                "reason": reason,
                "timestamp": time.time(),
            })

    def is_trading_allowed(self) -> bool:
        """Ω-T64: Check if trading is currently allowed."""
        if self._state.current_level in (
            CircuitBreakerLevel.RED,
            CircuitBreakerLevel.CRITICAL,
            CircuitBreakerLevel.EMERGENCY,
            CircuitBreakerLevel.CATASTROPHIC,
        ):
            return False

        if self._state.current_level == CircuitBreakerLevel.YELLOW:
            return True  # Reduced sizing but still allowed

        if self._state.current_level == CircuitBreakerLevel.ORANGE:
            return True  # Only A+ setups

        return True

    def get_sizing_multiplier(self) -> float:
        """Ω-T64: Get sizing multiplier based on circuit breaker level."""
        return self._state.current_level.sizing_multiplier

    def advance_recovery(self) -> None:
        """Ω-T70: Advance recovery stage after cooldown expires."""
        if self._state.cooldown_remaining <= 0 and self._state.recovery_stage < 4:
            self._state.recovery_stage += 1
            self._recovery_active = True

    def get_recovery_sizing_fraction(self) -> float:
        """Ω-T70: Sizing fraction during recovery."""
        if not self._recovery_active:
            return 1.0
        fractions = {1: 0.25, 2: 0.5, 3: 0.75, 4: 1.0}
        return fractions.get(self._state.recovery_stage, 0.25)

    def get_trigger_history(self) -> list[dict[str, Any]]:
        return list(self._trigger_history)

    def get_ftmo_compliance(self) -> dict[str, float]:
        """Ω-T72: FTMO compliance status."""
        return {
            "daily_loss_limit": self._daily_loss_limit,
            "total_loss_limit": self._total_loss_limit,
            "current_drawdown": self._state.current_drawdown,
            "daily_margin": self._daily_loss_limit - self._state.current_drawdown,
            "total_margin": self._total_loss_limit - self._state.current_drawdown,
            "ftmo_safe": self._state.current_drawdown < self._daily_loss_limit * 0.8,
        }


# ──────────────────────────────────────────────────────────────
# Ω-T73 to Ω-T81: Position Risk Monitor
# ──────────────────────────────────────────────────────────────

@dataclass
class PositionRecord:
    position_id: str
    symbol: str
    direction: str  # "long" or "short"
    entry_price: float
    current_price: float
    size: float
    unrealized_pnl: float
    realized_pnl: float
    stop_loss: float
    take_profit: float
    entry_time: float
    regime: str
    correlation_to_portfolio: float
    funding_cost: float


class PositionRiskMonitor:
    """
    Ω-T73–T81: Real-time position risk monitoring with P&L tracking,
    drawdown monitoring, VaR/CVaR, correlation, leverage, and funding.
    """

    def __init__(self, max_drawdown_pct: float = 2.0, max_leverage: float = 3.0) -> None:
        self._positions: dict[str, PositionRecord] = {}
        self._peak_equity = 100.0  # Normalized to 100
        self._current_equity = 100.0
        self._max_drawdown = max_drawdown_pct
        self._max_leverage = max_leverage
        self._daily_pnl = 0.0
        self._total_realized_pnl = 0.0
        self._pnl_history: deque[float] = deque(maxlen=10000)
        self._funding_history: deque[float] = deque(maxlen=1000)
        self._correlation_matrix: dict[str, dict[str, float]] = {}

    def add_position(self, position: PositionRecord) -> None:
        self._positions[position.position_id] = position

    def update_position(self, position_id: str, current_price: float) -> None:
        if position_id in self._positions:
            pos = self._positions[position_id]
            old_price = pos.current_price
            pos = PositionRecord(
                position_id=position_id,
                symbol=pos.symbol,
                direction=pos.direction,
                entry_price=pos.entry_price,
                current_price=current_price,
                size=pos.size,
                unrealized_pnl=self._compute_pnl(pos, current_price),
                realized_pnl=pos.realized_pnl,
                stop_loss=pos.stop_loss,
                take_profit=pos.take_profit,
                entry_time=pos.entry_time,
                regime=pos.regime,
                correlation_to_portfolio=pos.correlation_to_portfolio,
                funding_cost=pos.funding_cost,
            )
            self._positions[position_id] = pos

    def _compute_pnl(self, pos: PositionRecord, price: float) -> float:
        if pos.direction == "long":
            return (price - pos.entry_price) * pos.size
        return (pos.entry_price - price) * pos.size

    def close_position(self, position_id: str, exit_price: float) -> float:
        if position_id not in self._positions:
            return 0.0
        pos = self._positions[position_id]
        pnl = self._compute_pnl(pos, exit_price)
        self._total_realized_pnl += pnl
        self._pnl_history.append(pnl)
        self._current_equity += pnl
        if self._current_equity > self._peak_equity:
            self._peak_equity = self._current_equity
        del self._positions[position_id]
        return pnl

    def get_current_drawdown(self) -> float:
        """Ω-T75: peak-to-trough drawdown percentage."""
        if self._peak_equity <= 0:
            return 0.0
        return max(0.0, (self._peak_equity - self._current_equity) / self._peak_equity * 100)

    def get_total_unrealized_pnl(self) -> float:
        """Ω-T73: Sum of all unrealized P&L."""
        return sum(pos.unrealized_pnl for pos in self._positions.values())

    def get_exposure_by_direction(self) -> dict[str, float]:
        """Ω-T81: Exposure summary by direction."""
        long_exp = sum(pos.size * pos.current_price for pos in self._positions.values() if pos.direction == "long")
        short_exp = sum(pos.size * pos.current_price for pos in self._positions.values() if pos.direction == "short")
        return {"long": long_exp, "short": short_exp, "total": long_exp + short_exp}

    def get_leverage(self, total_capital: float) -> float:
        """Ω-T79: Effective leverage ratio."""
        if total_capital <= 0:
            return 0.0
        total_notional = sum(
            pos.size * pos.current_price for pos in self._positions.values()
        )
        return total_notional / total_capital

    def get_var_historical(self, confidence: float = 0.99) -> float:
        """Ω-T76: Historical VaR at given confidence level."""
        if len(self._pnl_history) < 20:
            return 0.0
        sorted_pnl = sorted(self._pnl_history)
        idx = int(len(sorted_pnl) * (1 - confidence))
        return abs(sorted_pnl[idx]) if idx < len(sorted_pnl) else 0.0

    def get_cvar(self, confidence: float = 0.995) -> float:
        """Ω-T77: Conditional VaR (expected shortfall)."""
        if len(self._pnl_history) < 20:
            return 0.0
        sorted_pnl = sorted(self._pnl_history)
        n_tail = max(1, int(len(sorted_pnl) * (1 - confidence)))
        tail = sorted_pnl[:n_tail]
        return abs(sum(tail) / len(tail)) if tail else 0.0

    def get_correlation_risk(self, symbol_a: str, symbol_b: str) -> float:
        """Ω-T78: Get correlation between two symbols."""
        if symbol_a in self._correlation_matrix:
            return self._correlation_matrix[symbol_a].get(symbol_b, 0.0)
        return 0.0

    def update_correlation(self, symbol_a: str, symbol_b: str, corr: float) -> None:
        """Ω-T78: Update correlation estimate."""
        if symbol_a not in self._correlation_matrix:
            self._correlation_matrix[symbol_a] = {}
        self._correlation_matrix[symbol_a][symbol_b] = corr

    def record_funding(self, cost: float) -> None:
        """Ω-T80: Record funding cost."""
        self._funding_history.append(cost)

    def get_total_funding_cost(self) -> float:
        """Ω-T80: Total accumulated funding cost."""
        return sum(self._funding_history)

    def get_risk_dashboard(self) -> dict[str, Any]:
        """Ω-T81: Full risk dashboard."""
        return {
            "current_equity": self._current_equity,
            "peak_equity": self._peak_equity,
            "drawdown_pct": self.get_current_drawdown(),
            "unrealized_pnl": self.get_total_unrealized_pnl(),
            "total_realized_pnl": self._total_realized_pnl,
            "leverage": self.get_leverage(self._current_equity),
            "var_99": self.get_var_historical(0.99),
            "cvar_99_5": self.get_cvar(0.995),
            "n_open_positions": len(self._positions),
            "exposure": self.get_exposure_by_direction(),
            "total_funding_cost": self.get_total_funding_cost(),
        }


# ──────────────────────────────────────────────────────────────
# Ω-T82 to Ω-T90: Dynamic Stop & Exit Engine
# ──────────────────────────────────────────────────────────────

class DynamicExitEngine:
    """
    Ω-T82–T90: Multi-trigger exit engine with adaptive stops,
    trailing, time-based, signal invalidation, regime change,
    counter-signal, emergency, and partial exits.
    """

    def __init__(self) -> None:
        self._exit_history: list[dict[str, Any]] = []

    def compute_adaptive_stop(
        self,
        entry_price: float,
        direction: str,
        atr: float,
        regime: str,
        stop_multiplier: float,
    ) -> float:
        """Ω-T82: Adaptive stop based on ATR × regime-specific multiplier."""
        stop_distance = atr * stop_multiplier
        if direction == "long":
            return entry_price - stop_distance
        return entry_price + stop_distance

    def compute_trailing_stop(
        self,
        current_stop: float,
        current_price: float,
        entry_price: float,
        direction: str,
        atr: float,
        trail_base_mult: float,
        acceleration_factor: float,
    ) -> float:
        """Ω-T83: Trailing stop that tightens as profit grows."""
        profit_pct = abs(current_price - entry_price) / entry_price if entry_price > 0 else 0.0
        # Stop gets tighter as profit increases
        dynamic_mult = trail_base_mult * math.exp(-acceleration_factor * profit_pct * 100)
        dynamic_mult = max(0.5, dynamic_mult)  # Never tighter than 0.5× ATR
        new_stop_distance = atr * dynamic_mult

        if direction == "long":
            new_stop = current_price - new_stop_distance
            return max(new_stop, current_stop)  # Never move stop down
        new_stop = current_price + new_stop_distance
        return min(new_stop, current_stop)  # Never move stop up

    def check_time_based_exit(
        self,
        entry_time: float,
        current_time: float,
        max_hold_seconds: float,
    ) -> bool:
        """Ω-T84: Exit if trade has been open too long without progress."""
        return (current_time - entry_time) > max_hold_seconds

    def check_signal_invalidation(
        self,
        original_conditions: dict[str, Any],
        current_conditions: dict[str, Any],
    ) -> bool:
        """Ω-T85: Check if original trade rationale has been invalidated."""
        for key in original_conditions:
            if key in current_conditions:
                orig = original_conditions[key]
                curr = current_conditions[key]
                if isinstance(orig, (int, float)) and isinstance(curr, (int, float)):
                    if orig > 0 and curr < orig * 0.5:
                        return True  # Condition weakened > 50%
        return False

    def check_regime_exit(
        self,
        original_regime: str,
        current_regime: str,
        no_trade_regimes: set[str] | None = None,
    ) -> bool:
        """Ω-T86: Exit if regime changed to adverse."""
        if no_trade_regimes is None:
            no_trade_regimes = {
                "choppy_expanding", "choppy_contracting",
                "flash_crash", "liquidation_cascade", "unknown",
            }
        return current_regime in no_trade_regimes and current_regime != original_regime

    def check_counter_signal(
        self,
        opposite_signal_strength: float,
        threshold: float,
    ) -> bool:
        """Ω-T87: Exit if opposing signal exceeds threshold."""
        return opposite_signal_strength >= threshold

    def check_emergency_exit(
        self,
        volatility: float,
        spread_bps: float,
        liquidity_usd: float,
        is_flash_crash: bool,
    ) -> bool:
        """Ω-T88: Emergency exit under extreme market conditions."""
        return (
            is_flash_crash
            or spread_bps > 50.0  # Spread > 5x normal (~10 bps)
            or liquidity_usd < 1000  # Liquidity evaporated
            or volatility > 15.0  # Extreme volatility
        )

    def compute_partial_exits(
        self,
        position_size: float,
        current_price: float,
        take_profit: float,
        entry_price: float,
        direction: str,
    ) -> list[tuple[float, float]]:
        """Ω-T89: Compute partial exit levels and sizes."""
        profit_range = abs(take_profit - entry_price)
        if profit_range <= 0:
            return []

        partials = []
        # Exit 50% at 50% TP
        if direction == "long":
            tp1 = entry_price + profit_range * 0.5
            tp2 = entry_price + profit_range * 0.8
        else:
            tp1 = entry_price - profit_range * 0.5
            tp2 = entry_price - profit_range * 0.8

        if (direction == "long" and current_price >= tp1) or (direction == "short" and current_price <= tp1):
            partials.append((position_size * 0.5, tp1))

        if (direction == "long" and current_price >= tp2) or (direction == "short" and current_price <= tp2):
            partials.append((position_size * 0.25, tp2))

        return partials

    def evaluate_all_exits(
        self,
        position: PositionRecord,
        atr: float,
        opposite_signal_strength: float,
        current_conditions: dict[str, Any],
        original_conditions: dict[str, Any],
        trail_base_mult: float = 2.0,
        acceleration_factor: float = 0.05,
        max_hold_seconds: float = 600.0,
        counter_signal_threshold: float = 0.7,
    ) -> dict[str, bool | float | str | list]:
        """
        Ω-T90: Evaluate ALL exit triggers and return comprehensive exit plan.
        Any True trigger → exit immediately.
        """
        now = time.time()
        results: dict[str, Any] = {}

        results["time_based_exit"] = self.check_time_based_exit(
            position.entry_time, now, max_hold_seconds
        )
        results["signal_invalidation"] = self.check_signal_invalidation(
            original_conditions, current_conditions
        )
        results["regime_exit"] = self.check_regime_exit(
            position.regime, current_conditions.get("regime", position.regime)
        )
        results["counter_signal"] = self.check_counter_signal(
            opposite_signal_strength, counter_signal_threshold
        )
        results["emergency_exit"] = self.check_emergency_exit(
            current_conditions.get("volatility", 0.0),
            current_conditions.get("spread_bps", 0.0),
            current_conditions.get("liquidity_usd", 1e9),
            current_conditions.get("is_flash_crash", False),
        )
        results["stop_loss_hit"] = (
            (position.direction == "long" and position.current_price <= position.stop_loss)
            or (position.direction == "short" and position.current_price >= position.stop_loss)
        )
        results["take_profit_hit"] = (
            (position.direction == "long" and position.current_price >= position.take_profit)
            or (position.direction == "short" and position.current_price <= position.take_profit)
        )

        # Compute trailing stop
        results["new_trailing_stop"] = self.compute_trailing_stop(
            position.stop_loss, position.current_price, position.entry_price,
            position.direction, atr, trail_base_mult, acceleration_factor
        )

        # Partial exits
        results["partial_exits"] = self.compute_partial_exits(
            position.size, position.current_price,
            position.take_profit, position.entry_price, position.direction
        )

        # Any trigger active?
        exit_triggers = [
            results["time_based_exit"], results["signal_invalidation"],
            results["regime_exit"], results["counter_signal"],
            results["emergency_exit"], results["stop_loss_hit"],
            results["take_profit_hit"],
        ]
        results["should_exit"] = any(exit_triggers)
        active_triggers = [k for k, v in results.items() if v is True and k not in ("should_exit",)]
        results["active_triggers"] = active_triggers
        results["exit_urgency"] = (
            "emergency" if results["emergency_exit"]
            else "high" if results["stop_loss_hit"] or results["take_profit_hit"]
            else "normal" if len(active_triggers) == 1
            else "none"
        )

        # Record exit decision
        if results["should_exit"]:
            self._exit_history.append({
                "position_id": position.position_id,
                "triggers": active_triggers,
                "urgency": results["exit_urgency"],
                "timestamp": now,
            })

        return results

    def get_exit_history(self) -> list[dict[str, Any]]:
        return list(self._exit_history)


# ──────────────────────────────────────────────────────────────
# Ω-T91 to Ω-T99: Tail Risk Protection
# ──────────────────────────────────────────────────────────────

class TailRiskProtector:
    """
    Ω-T91–T99: Tail risk detection, EVT modeling, hedge allocation,
    stress testing, liquidation cascade prediction, gap risk,
    black swan preparation, and recovery path planning.
    """

    def __init__(
        self,
        hedge_allocation_pct: float = 0.02,  # 2% for tail hedge
        insurance_fund_pct: float = 0.05,  # 5% reserve
    ) -> None:
        self._return_samples: deque[float] = deque(maxlen=5000)
        self._hedge_allocation = hedge_allocation_pct
        self._insurance_fund_pct = insurance_fund_pct
        self._tail_events: list[float] = []
        self._liquidation_levels: list[float] = []
        self._gamma_levels: list[float] = []
        self._max_pain: float = 0.0

    def update(self, pnl_return: float) -> None:
        """Record return for tail risk estimation."""
        self._return_samples.append(pnl_return)
        if abs(pnl_return) > 3.0:  # > 3σ event
            self._tail_events.append(pnl_return)

    def detect_tail_risk(
        self,
        skewness: float,
        kurtosis: float,
        correlation_breakdown: bool,
        liquidation_proximity_bps: float,
    ) -> float:
        """
        Ω-T91: Composite tail risk score [0, 1].
        Higher = more tail risk.
        """
        score = 0.0
        # Extreme skew
        score += min(0.3, abs(skewness) * 0.1) if skewness < -1.0 else 0.0
        # Exploding kurtosis
        score += min(0.3, (kurtosis - 3.0) * 0.05) if kurtosis > 5.0 else 0.0
        # Correlation breakdown
        score += 0.2 if correlation_breakdown else 0.0
        # Near liquidation clusters
        score += min(0.2, 200.0 / liquidation_proximity_bps) if liquidation_proximity_bps > 0 else 0.0
        return min(1.0, score)

    def fit_gpd(self, threshold_quantile: float = 0.95) -> tuple[float, float, float]:
        """
        Ω-T92: Fit Generalized Pareto Distribution to tail returns.
        Returns (xi/scale/num_samples).
        """
        if len(self._return_samples) < 50:
            return 0.0, 0.0, 0
        sorted_returns = sorted(abs(r) for r in self._return_samples)
        threshold_idx = int(len(sorted_returns) * threshold_quantile)
        if threshold_idx >= len(sorted_returns):
            return 0.0, 0.0, len(sorted_returns)
        threshold = sorted_returns[threshold_idx]
        exceedances = [x - threshold for x in sorted_returns[threshold_idx:] if x > threshold]
        if len(exceedances) < 5:
            return 0.0, threshold, len(exceedances)
        # Method of moments for GPD parameters
        mean_exc = sum(exceedances) / len(exceedances)
        var_exc = sum((x - mean_exc) ** 2 for x in exceedances) / max(1, len(exceedances) - 1)
        xi = 0.5 * (1 - mean_exc ** 2 / var_exc) if var_exc > 0 else 0.0
        xi = max(-0.5, min(1.0, xi))
        scale = mean_exc * (1 - xi)
        return xi, scale, len(exceedances)

    def estimate_tail_probability_beyond(self, n_sigma: float) -> float:
        """Ω-T92: Estimate P(|return| > n_sigma) using GPD fit."""
        xi, scale, n = self.fit_gpd()
        if n < 5 or scale <= 0:
            return 1e-10
        # P(X > nσ) under GPD approximation
        tq = 0.95
        tail_prob = (1 - tq) * (1 + xi * n_sigma / scale) ** (-1.0 / xi) if abs(xi) > 0.001 else 0
        return max(1e-15, tail_prob)

    def get_recommended_hedge_ratio(self, tail_risk_score: float) -> float:
        """Ω-T93: Recommended hedge allocation as % of capital."""
        base = self._hedge_allocation
        if tail_risk_score > 0.7:
            return base * 3.0  # Triple hedge in extreme risk
        elif tail_risk_score > 0.4:
            return base * 2.0
        return base

    def get_insurance_fund_status(self, total_capital: float) -> float:
        """Ω-T99: Current insurance fund level."""
        return total_capital * self._insurance_fund_pct

    def set_liquidation_levels(self, levels: list[float]) -> None:
        """Ω-T95: Set known liquidation cluster levels."""
        self._liquidation_levels = sorted(levels)

    def get_nearest_liquidation_distance(self, current_price: float) -> float:
        """Ω-T95: Distance to nearest liquidation cluster in bps."""
        if not self._liquidation_levels:
            return 999999.0
        distances = [abs(current_price - lvl) / current_price * 10000 for lvl in self._liquidation_levels if current_price > 0]
        return min(distances) if distances else 999999.0

    def estimate_cascade_potential(
        self,
        current_price: float,
        total_oi: float,
        oi_near_clusters: float,
    ) -> float:
        """Ω-T95: Estimate liquidation cascade potential [0, 1]."""
        if total_oi <= 0:
            return 0.0
        cascade_pct = oi_near_clusters / total_oi
        dist = self.get_nearest_liquidation_distance(current_price)
        proximity_mult = max(1.0, 100.0 / dist) if dist > 0 else 1.0
        return min(1.0, cascade_pct * proximity_mult)

    def generate_recovery_path(self, current_dd: float, target_dd: float = 0.0) -> dict[str, Any]:
        """Ω-T98: Recovery path plan after drawdown."""
        if current_dd <= target_dd:
            return {"status": "recovered", "steps": []}

        steps = []
        remaining = current_dd - target_dd
        # Conservative recovery: reduce sizing, focus on A+ setups
        steps.append({"phase": 1, "action": "Reduce sizing to 25%", "duration": "24h", "criteria": "No further losses"})
        steps.append({"phase": 2, "action": "Increase to 50%", "duration": "48h", "criteria": "Win rate > 55%"})
        steps.append({"phase": 3, "action": "Increase to 75%", "duration": "72h", "criteria": "Sharpe > 3"})
        steps.append({"phase": 4, "action": "Return to 100%", "duration": "ongoing", "criteria": "Sustained recovery"})

        return {"status": "recovering", "remaining_dd": remaining, "steps": steps}

    def get_tail_risk_metrics(self, current_price: float, total_oi: float = 0) -> TailRiskMetrics:
        """Ω-T91-T99: Comprehensive tail risk metrics."""
        xi, scale, n = self.fit_gpd()
        skew = 0.0
        kurt = 3.0
        if len(self._return_samples) >= 20:
            r = list(self._return_samples)
            m = sum(r) / len(r)
            s = (sum((x - m) ** 2 for x in r) / max(1, len(r) - 1)) ** 0.5
            if s > 0:
                skew = sum((x - m) ** 3 for x in r) / (len(r) * s ** 3)
                kurt = sum((x - m) ** 4 for x in r) / (len(r) * s ** 4)

        tail_risk = self.detect_tail_risk(
            skew, kurt,
            correlation_breakdown=False,
            liquidation_proximity_bps=self.get_nearest_liquidation_distance(current_price),
        )

        cvar = sum(sorted(abs(x) for x in self._return_samples)[: max(1, int(len(self._return_samples) * 0.005))]) / max(1, int(len(self._return_samples) * 0.005)) if len(self._return_samples) >= 50 else 0.0

        return TailRiskMetrics(
            skewness=skew,
            kurtosis=kurt,
            var_99=self._compute_var(0.99),
            cvar_99_5=cvar,
            gpd_tail_index=xi,
            tail_probability_10sigma=self.estimate_tail_probability_beyond(10.0),
            liquidation_distance_bps=self.get_nearest_liquidation_distance(current_price),
            cascade_potential=self.estimate_cascade_potential(current_price, total_oi, total_oi * 0.1),
            hedge_ratio=self.get_recommended_hedge_ratio(tail_risk),
            insurance_fund_pct=self._insurance_fund_pct,
            black_swan_readiness=max(0.0, 1.0 - tail_risk),
        )

    def _compute_var(self, confidence: float) -> float:
        """Simple historical VaR."""
        if len(self._return_samples) < 10:
            return 0.0
        sorted_abs = sorted(abs(r) for r in self._return_samples)
        idx = int(len(sorted_abs) * (1 - confidence))
        return sorted_abs[min(idx, len(sorted_abs) - 1)]


# ──────────────────────────────────────────────────────────────
# Ω-T100 to Ω-T108: Portfolio Risk Optimizer
# ──────────────────────────────────────────────────────────────

class PortfolioRiskOptimizer:
    """
    Ω-T100–T108: Portfolio-wide risk optimization including
    variance decomposition, risk parity, correlation forecasting,
    concentration risk, factor exposure, risk budget allocation,
    drawdown contribution tracking, optimal hedge ratio, and
    capital efficiency scoring.
    """

    def __init__(self) -> None:
        self._strategy_returns: dict[str, list[float]] = {}
        self._factor_exposures: dict[str, float] = {}
        self._risk_budgets: dict[str, float] = {}
        self._strategy_pnls: dict[str, float] = {}

    def record_strategy_return(self, strategy_id: str, ret: float) -> None:
        if strategy_id not in self._strategy_returns:
            self._strategy_returns[strategy_id] = []
        self._strategy_returns[strategy_id].append(ret)

    def get_variance_contribution(self) -> dict[str, float]:
        """Ω-T100: How much each strategy contributes to portfolio variance."""
        if len(self._strategy_returns) < 2:
            return {}
        # Compute covariance matrix contribution
        result = {}
        total_var = 0.0
        for sid, rets in self._strategy_returns.items():
            if len(rets) < 10:
                result[sid] = 0.0
                continue
            m = sum(rets) / len(rets)
            var = sum((r - m) ** 2 for r in rets) / max(1, len(rets) - 1)
            result[sid] = var
            total_var += var
        # Normalize
        if total_var > 0:
            result = {k: v / total_var for k, v in result.items()}
        return result

    def get_risk_parity_weights(self) -> dict[str, float]:
        """Ω-T101: Risk parity — each strategy contributes equally to risk."""
        contributions = self.get_variance_contribution()
        if not contributions:
            return {}
        n = len(contributions)
        target = 1.0 / n
        # Simple inverse volatility weighting
        result = {}
        total = 0.0
        for sid, contr in contributions.items():
            if contr > 0:
                w = 1.0 / contr
            else:
                w = 1.0
            result[sid] = w
            total += w
        if total > 0:
            result = {k: v / total for k, v in result.items()}
        return result

    def compute_hhi(self) -> float:
        """Ω-T103: Herfindahl-Hirschman Index for concentration."""
        total = sum(
            sum(rets) for rets in self._strategy_returns.values()
        )
        if total == 0:
            return 0.0
        result = 0.0
        for rets in self._strategy_returns.values():
            s = sum(rets)
            share = s / total
            result += share ** 2
        return result

    def set_factor_exposure(self, factor: str, exposure: float) -> None:
        """Ω-T104: Set portfolio exposure to a known factor."""
        self._factor_exposures[factor] = exposure

    def get_factor_exposures(self) -> dict[str, float]:
        """Ω-T104: Current factor exposures."""
        return dict(self._factor_exposures)

    def allocate_risk_budget(self, budgets: dict[str, float]) -> None:
        """Ω-T105: Set risk budget per strategy (must sum to 1.0)."""
        total = sum(budgets.values())
        if total > 0:
            self._risk_budgets = {k: v / total for k, v in budgets.items()}
        else:
            self._risk_budgets = {}

    def track_drawdown_contribution(self) -> dict[str, float]:
        """Ω-T106: How much each strategy contributed to current drawdown."""
        contributions = {}
        total_dd = 0.0
        for sid, rets in self._strategy_returns.items():
            if not rets:
                contributions[sid] = 0.0
                continue
            cum_ret = 1.0
            peak = 1.0
            max_dd = 0.0
            for r in rets:
                cum_ret *= (1 + r)
                if cum_ret > peak:
                    peak = cum_ret
                dd = (peak - cum_ret) / peak
                max_dd = max(max_dd, dd)
            contributions[sid] = max_dd
            total_dd += max_dd
        if total_dd > 0:
            contributions = {k: v / total_dd for k, v in contributions.items()}
        return contributions

    def compute_min_variance_hedge_ratio(
        self,
        portfolio_rets: list[float],
        hedge_rets: list[float],
    ) -> float:
        """Ω-T107: Minimum variance hedge ratio."""
        n = min(len(portfolio_rets), len(hedge_rets))
        if n < 10:
            return 0.0
        p = portfolio_rets[-n:]
        h = hedge_rets[-n:]
        mean_p = sum(p) / n
        mean_h = sum(h) / n
        cov = sum((p[i] - mean_p) * (h[i] - mean_h) for i in range(n)) / (n - 1)
        var_h = sum((x - mean_h) ** 2 for x in h) / (n - 1)
        if var_h <= 0:
            return 0.0
        return cov / var_h

    def compute_capital_efficiency(self) -> dict[str, float]:
        """Ω-T108: Return per unit of capital for each strategy."""
        result = {}
        for sid, rets in self._strategy_returns.items():
            if not rets:
                result[sid] = 0.0
                continue
            total_return = sum(rets)
            max_capital_used = max(abs(r) for r in rets) if any(r != 0 for r in rets) else 1.0
            result[sid] = total_return / max_capital_used
        return result

    def get_portfolio_dashboard(self) -> dict[str, Any]:
        """Ω-T108: Full portfolio risk dashboard."""
        return {
            "variance_contribution": self.get_variance_contribution(),
            "risk_parity_weights": self.get_risk_parity_weights(),
            "concentration_hhi": self.compute_hhi(),
            "factor_exposures": self.get_factor_exposures(),
            "risk_budgets": dict(self._risk_budgets),
            "drawdown_contribution": self.track_drawdown_contribution(),
            "capital_efficiency": self.compute_capital_efficiency(),
            "n_strategies": len(self._strategy_returns),
        }
