"""
SOLÉNN v2 — Risk Guards, Latency Optimization & Hydra Engine (Ω-H55 to Ω-H162)
Pre-trade guards, slippage prediction, market impact minimization,
stress handling, execution analytics, position lifecycle,
and unified Hydra engine orchestrator.

Tópico 2.2-2.6: Slippage, Market Impact, Stress, Analytics, Lifecycle
Tópico 3.1-3.6: Low-Latency, WS Channel, Latency Profiling, Memory, Concurrency, Integration
"""

from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from .execution_algos import ExecutionAlgoSelector, ExecutionSlice, ExecutionTelemetry, FillAnalyzer
from .hydra_types import (
    FillRecord,
    Order,
    OrderConstraints,
    OrderSide,
    OrderStatus,
    OrderType,
)
from .order_factory import OrderFactory, PreTradeRiskChecker
from .order_state import OrderStateMachine, OrderTimeoutConfig
from .smart_router import RoutingDecision, SmartOrderRouter


# ──────────────────────────────────────────────────────────────
# Tópico 2.2: Slippage Prediction & Control
# ──────────────────────────────────────────────────────────────

@dataclass
class SlippageModel:
    """Ω-H64 to Ω-H72: Slippage prediction and learning."""

    def __init__(self) -> None:
        self._observations: list[dict[str, float]] = []

    def predict(
        self,
        order_size: float,
        book_depth: float,
        volatility: float,
        urgency: float,
    ) -> float:
        """
        Ω-H64: Predict slippage in bps.
        Simplified model: f(size, depth, vol, urgency).
        """
        if book_depth <= 0:
            return 100.0  # No liquidity
        depth_ratio = order_size / book_depth
        vol_factor = 1.0 + volatility * 5.0
        urgency_factor = 1.0 + urgency * 2.0
        slippage = depth_ratio * 100 * vol_factor * urgency_factor
        return slippage

    def record_observation(
        self,
        order_size: float,
        book_depth: float,
        volatility: float,
        urgency: float,
        actual_slippage_bps: float,
    ) -> None:
        """Ω-H67: Learn from actual execution data."""
        self._observations.append({
            "size": order_size, "depth": book_depth,
            "vol": volatility, "urgency": urgency,
            "actual": actual_slippage_bps,
        })


class MarketImpactModel:
    """Ω-H73 to Ω-H81: Almgren-Chriss market impact model."""

    def __init__(self, eta: float = 0.1, gamma: float = 0.6) -> None:
        self._eta = eta  # Market impact constant
        self._gamma = gamma  # Concavity parameter

    def estimate_impact_bps(
        self, order_qty: float, book_depth: float,
    ) -> float:
        """Ω-H73: η(Q/D)^γ in basis points."""
        if book_depth <= 0:
            return 100.0
        ratio = order_qty / book_depth
        return self._eta * (ratio ** self._gamma) * 10000


# ──────────────────────────────────────────────────────────────
# Tópico 2.4: Stress Handlers
# ──────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class StressDecision:
    """Output of stress evaluation."""
    action: str  # "normal", "reduce_sizing", "no_trade", "emergency_exit", "flat_all"
    sizing_multiplier: float
    reason: str


class StressHandler:
    """
    Ω-H82 to Ω-H90: Execution under stress conditions.
    """

    def evaluate(
        self,
        volatility: float,
        spread_bps: float,
        depth_pct_drop: float,  # % drop in depth from baseline
        is_flash_crash: bool,
        exchange_online: bool,
        latency_mult: float,  # latency vs normal
        data_valid: bool,
    ) -> StressDecision:
        """Ω-H82-H90: Assess market conditions and return action."""

        # Ω-H82: Flash crash
        if is_flash_crash:
            return StressDecision(
                action="emergency_exit", sizing_multiplier=0.0,
                reason="Flash crash detected — exiting all positions",
            )

        # Ω-H83: Liquidity crisis
        if spread_bps > 100.0 and depth_pct_drop > 80.0:
            return StressDecision(
                action="no_trade", sizing_multiplier=0.0,
                reason="Liquidity crisis — spread too wide, depth evaporated",
            )

        # Ω-H84: Exchange down
        if not exchange_online:
            return StressDecision(
                action="flat_all", sizing_multiplier=0.0,
                reason="Exchange offline — flattening positions",
            )

        # Ω-H87: Data feed corrupted
        if not data_valid:
            return StressDecision(
                action="no_trade", sizing_multiplier=0.0,
                reason="Data feed corrupted — waiting for restoration",
            )

        # Ω-H86: Latency spike
        if latency_mult > 10.0:
            return StressDecision(
                action="reduce_sizing", sizing_multiplier=0.25,
                reason=f"Latency {latency_mult:.0f}x normal — reducing sizing to 25%",
            )

        # Normal operation
        # Ω-H88: Partial degradation
        if spread_bps > 50.0 or depth_pct_drop > 50.0:
            return StressDecision(
                action="reduce_sizing", sizing_multiplier=0.5,
                reason="Partial degradation — sizing reduced to 50%",
            )

        return StressDecision(
            action="normal", sizing_multiplier=1.0,
            reason="Normal conditions",
        )


# ──────────────────────────────────────────────────────────────
# Tópico 2.5: Execution Analytics
# ──────────────────────────────────────────────────────────────

class ExecutionAnalytics:
    """Ω-H91 to Ω-H99: Post-execution analytics."""

    def __init__(self) -> None:
        self._fill_analyzer = FillAnalyzer()
        self._tce_history: deque[float] = deque(maxlen=1000)
        self._execution_regimes: dict[str, list[dict[str, float]]] = {
            "easy": [], "normal": [], "stressed": [], "extreme": [],
        }

    def record_execution(self, order: Order, metrics: dict[str, float]) -> None:
        """Record execution for analytics."""
        tce = metrics.get("tce_usd", 0.0)
        self._tce_history.append(tce)

        # Classify execution regime
        slippage = metrics.get("slippage_bps", 0.0)
        if slippage < 2:
            regime = "easy"
        elif slippage < 10:
            regime = "normal"
        elif slippage < 30:
            regime = "stressed"
        else:
            regime = "extreme"

        self._execution_regimes[regime].append(metrics)

    def get_tce_trend(self) -> str:
        """Ω-H98: Is TCE improving or degrading?"""
        if len(self._tce_history) < 20:
            return "insufficient_data"
        recent = list(self._tce_history)
        first_half = sum(recent[: len(recent) // 2]) / (len(recent) // 2)
        second_half = sum(recent[len(recent) // 2:]) / (len(recent) - len(recent) // 2)
        if second_half < first_half * 0.9:
            return "improving"
        elif second_half > first_half * 1.1:
            return "degrading"
        return "stable"

    def get_fill_analyzer(self) -> FillAnalyzer:
        return self._fill_analyzer


# ──────────────────────────────────────────────────────────────
# Tópico 2.6: Position Lifecycle
# ──────────────────────────────────────────────────────────────

@dataclass
class PositionState:
    """Ω-H100: Position lifecycle state."""
    position_id: str
    symbol: str
    side: str
    entry_price: float
    current_price: float
    size: float
    realized_pnl: float
    unrealized_pnl: float
    state: str  # CREATED → OPEN → MANAGING → REDUCING → CLOSED
    exit_signals: list[str]
    lifecycle_changes: list[dict[str, str]]


class PositionLifecycle:
    """
    Ω-H100 to Ω-H108: Full position management.
    """

    VALID_TRANSITIONS = {
        "CREATED": {"OPEN"},
        "OPEN": {"MANAGING", "CLOSED"},
        "MANAGING": {"REDUCING", "CLOSED"},
        "REDUCING": {"MANAGING", "CLOSED"},
        "CLOSED": set(),
    }

    def __init__(self) -> None:
        self._positions: dict[str, PositionState] = {}

    def create_position(
        self, position_id: str, symbol: str, side: str,
        entry_price: float, size: float,
    ) -> PositionState:
        pos = PositionState(
            position_id=position_id, symbol=symbol, side=side,
            entry_price=entry_price, current_price=entry_price,
            size=size, realized_pnl=0.0, unrealized_pnl=0.0,
            state="CREATED", exit_signals=[],
            lifecycle_changes=[{"from": "CREATED", "to": "CREATED"}],
        )
        self._positions[position_id] = pos
        return pos

    def transition(self, position_id: str, to_state: str) -> bool:
        if position_id not in self._positions:
            return False
        pos = self._positions[position_id]
        allowed = self.VALID_TRANSITIONS.get(pos.state, set())
        if to_state not in allowed:
            return False
        old = pos.state
        pos = PositionState(
            position_id=pos.position_id, symbol=pos.symbol, side=pos.side,
            entry_price=pos.entry_price, current_price=pos.current_price,
            size=pos.size, realized_pnl=pos.realized_pnl,
            unrealized_pnl=pos.unrealized_pnl, state=to_state,
            exit_signals=pos.exit_signals,
            lifecycle_changes=pos.lifecycle_changes + [{"from": old, "to": to_state}],
        )
        self._positions[position_id] = pos
        return True

    def update_price(self, position_id: str, price: float) -> None:
        if position_id in self._positions:
            pos = self._positions[position_id]
            if pos.side == "long":
                unrealized = (price - pos.entry_price) * pos.size
            else:
                unrealized = (pos.entry_price - price) * pos.size
            pos = PositionState(
                position_id=pos.position_id, symbol=pos.symbol, side=pos.side,
                entry_price=pos.entry_price, current_price=price,
                size=pos.size, realized_pnl=pos.realized_pnl,
                unrealized_pnl=unrealized, state=pos.state,
                exit_signals=pos.exit_signals,
                lifecycle_changes=pos.lifecycle_changes,
            )
            self._positions[position_id] = pos

    def add_exit_signal(self, position_id: str, signal: str) -> None:
        if position_id in self._positions:
            pos = self._positions[position_id]
            if signal not in pos.exit_signals:
                pos = PositionState(
                    position_id=pos.position_id, symbol=pos.symbol, side=pos.side,
                    entry_price=pos.entry_price, current_price=pos.current_price,
                    size=pos.size, realized_pnl=pos.realized_pnl,
                    unrealized_pnl=pos.unrealized_pnl, state=pos.state,
                    exit_signals=pos.exit_signals + [signal],
                    lifecycle_changes=pos.lifecycle_changes,
                )
                self._positions[position_id] = pos

    def check_exit_conditions(
        self, position_id: str,
        time_in_position: float,
        max_hold_seconds: float,
        trailing_stop_price: float | None = None,
    ) -> bool:
        """Ω-H104-H106: Check if position should be exited."""
        pos = self._positions.get(position_id)
        if pos is None or pos.state == "CLOSED":
            return True

        # Time-based exit
        if time_in_position > max_hold_seconds:
            return True

        # Stop loss
        if trailing_stop_price is not None:
            if pos.side == "long" and pos.current_price <= trailing_stop_price:
                return True
            if pos.side == "short" and pos.current_price >= trailing_stop_price:
                return True

        # Signal invalidation
        if len(pos.exit_signals) >= 3:
            return True

        return False


# ──────────────────────────────────────────────────────────────
# Ω-H109 to Ω-H162: Hydra Engine (unified orchestrator)
# ──────────────────────────────────────────────────────────────

class HydraEngine:
    """
    SOLÉNN v2 — Hydra Execution Engine (Ω-H01 to Ω-H162)
    Unified orchestrator for all execution components.

    Main entry: submit_order(order, context) -> (Order, RoutingDecision)
    """

    def __init__(
        self,
        constraints: OrderConstraints | None = None,
    ) -> None:
        # Ω-H01-H09, Ω-H55-H63: Order factory with risk checks
        self.order_factory = OrderFactory()

        # Ω-H10-H18: Order state machine
        self.state_machine = OrderStateMachine(OrderTimeoutConfig())

        # Ω-H19-H27: Smart router
        self.router = SmartOrderRouter()

        # Ω-H36: Algo selection
        self.algo_selector = ExecutionAlgoSelector()

        # Ω-H37-H45: Fill analyzer
        self.fill_analyzer = FillAnalyzer()

        # Ω-H46-H54: Telemetry
        self.telemetry = ExecutionTelemetry()

        # Ω-H64-H72: Slippage model
        self.slippage_model = SlippageModel()

        # Ω-H73-H81: Market impact model
        self.impact_model = MarketImpactModel()

        # Ω-H82-H90: Stress handler
        self.stress_handler = StressHandler()

        # Ω-H100-H108: Position lifecycle
        self.position_lifecycle = PositionLifecycle()

        # Ω-H91-H99: Execution analytics
        self.analytics = ExecutionAnalytics()

        # Config
        self._constraints = constraints or OrderConstraints()

        # Metrics
        self._n_submitted = 0
        self._n_filled = 0
        self._n_rejected = 0
        self._n_cancelled = 0

    def register_exchange(
        self, exchange: str, best_bid: float = 0.0, best_ask: float = 0.0,
        depth_bid: float = 0.0, depth_ask: float = 0.0,
        maker_fee: float = 0.001, taker_fee: float = 0.001,
    ) -> None:
        """Register an exchange for routing."""
        self.router.register_exchange(
            exchange, best_bid, best_ask, depth_bid, depth_ask, maker_fee, taker_fee,
        )

    def submit_order(
        self,
        exchange: str,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: float = 0.0,
        trace_id: str = "",
        context: dict[str, Any] | None = None,
    ) -> tuple[Order | None, str | None]:
        """
        Main entry: create → validate → route → submit → track.
        Returns (Order, error_message).
        """
        t0 = time.time_ns()
        ctx = context or {}
        market_price = ctx.get("market_price", price)

        # Ω-H82-H90: Stress check FIRST (before creating order)
        stress = self.stress_handler.evaluate(
            volatility=ctx.get("volatility", 0.01),
            spread_bps=ctx.get("spread_bps", 5.0),
            depth_pct_drop=ctx.get("depth_pct_drop", 0.0),
            is_flash_crash=ctx.get("is_flash_crash", False),
            exchange_online=self.router._conn_pool.is_healthy(exchange),
            latency_mult=ctx.get("latency_mult", 1.0),
            data_valid=ctx.get("data_valid", True),
        )
        if stress.action in ("no_trade", "emergency_exit", "flat_all"):
            self._n_rejected += 1
            self.telemetry.emit("rejected_stress", "hydra", {"reason": stress.reason})
            return None, stress.reason

        # Ω-H55-H63: Create with pre-trade risk checks (apply stress sizing)
        effective_qty = quantity * stress.sizing_multiplier
        order, error = self.order_factory.create_order(
            exchange=exchange, symbol=symbol, side=side,
            order_type=order_type, quantity=effective_qty, price=price,
            trace_id=trace_id, current_market_price=market_price,
        )
        if order is None:
            self._n_rejected += 1
            self.telemetry.record_error("pre_trade_reject")
            self.telemetry.emit("order_rejected", "hydra", {"reason": error}, trace_id=trace_id)
            return None, error

        # Ω-H19-H27: Route
        routing = self.router.route_order(order)
        best_exchange = routing.target_exchanges[0] if routing.target_exchanges else exchange

        # Ω-H64: Check slippage budget
        predicted_slippage = self.slippage_model.predict(
            order_size=order.quantity,
            book_depth=ctx.get("depth_usd", 100000.0),
            volatility=ctx.get("volatility", 0.01),
            urgency=ctx.get("urgency", 0.5),
        )
        slippage_budget = self._constraints.max_price_deviation_pct * 100
        if predicted_slippage > slippage_budget:
            self._n_rejected += 1
            return None, f"Predicted slippage {predicted_slippage:.0f}bps exceeds budget {slippage_budget:.0f}bps"

        # Register and transition
        self.state_machine.register_order(order)
        self.state_machine.transition(order.order_id, OrderStatus.VALIDATED, "Validation passed")
        self.state_machine.transition(order.order_id, OrderStatus.ROUTING, "Routing initiated")
        self.state_machine.transition(order.order_id, OrderStatus.SUBMITTED, f"Submitted to {best_exchange}")

        # Return updated order from state machine (transitions are stored there)
        submitted_order = self.state_machine.get_order(order.order_id) or order

        # Ω-H36: Select execution algo
        algo = self.algo_selector.select_algo(
            submitted_order,
            urgency=ctx.get("urgency", 0.5),
            regime=ctx.get("regime", "normal"),
            liquidity_pct=ctx.get("liquidity_pct", 10.0),
        )

        price_for_algo = ctx.get("best_price", market_price)
        if submitted_order.side == OrderSide.BUY:
            price_for_algo = ctx.get("best_ask", market_price)
        else:
            price_for_algo = ctx.get("best_bid", market_price)

        slices = self._generate_slices(submitted_order, algo, price_for_algo, ctx)

        self._n_submitted += 1
        latency_us = max(1, (time.time_ns() - t0) // 1000)
        self.telemetry.emit("order_submitted", "hydra", {
            "order_id": submitted_order.order_id,
            "exchange": best_exchange,
            "algo": algo,
            "n_slices": len(slices),
            "routing": routing.reasoning,
            "stress_action": stress.action,
        }, latency_us=latency_us)

        return submitted_order, None

    def simulate_fill(
        self, order_id: str, fill_price: float, fill_qty: float,
        commission: float = 0.0, is_maker: bool = False,
        arrival_price: float = 0.0,
    ) -> bool:
        """Simulate a fill for the order (for paper trading / backtesting)."""
        order = self.state_machine.get_order(order_id)
        if order is None or order.is_terminal:
            return False

        fill = FillRecord(
            fill_id=f"fill-{order_id}-{time.time_ns()}",
            order_id=order_id, exchange=order.exchange,
            symbol=order.symbol, side=order.side,
            price=fill_price, quantity=fill_qty,
            commission=commission, is_maker=is_maker,
        )
        success = self.state_machine.apply_fill(order_id, fill)

        if success:
            self._n_filled += 1

            # Ω-H37-H45: Analyze fill
            t0_update = time.time_ns()
            metrics = self.fill_analyzer.analyze_fill(
                order=self.state_machine.get_order(order_id) or order,
                arrival_price=arrival_price or order.price,
                vwap_during_execution=fill_price,
                market_impact_bps=self.impact_model.estimate_impact_bps(fill_qty, 100000.0),
                avg_latency_ms=(time.time_ns() - t0_update) / 1e6,
            )

            # Record in analytics
            self.analytics.record_execution(
                self.state_machine.get_order(order_id) or order,
                {
                    "tce_usd": metrics.tce_usd,
                    "slippage_bps": metrics.slippage_bps,
                    "quality": metrics.execution_quality_score,
                },
            )

            # Latency recording
            self.router.update_latency(order.exchange, (time.time_ns() - t0_update) / 1e6)

        return success

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an active order."""
        success = self.state_machine.transition(order_id, OrderStatus.CANCELLED, "User cancel")
        if success:
            self._n_cancelled += 1
            self.telemetry.emit("order_cancelled", "hydra", {"order_id": order_id})
        return success

    def cancel_all(self) -> list[str]:
        """Emergency cancel all active orders."""
        cancelled = self.state_machine.emergency_cancel_all()
        self.telemetry.emit("emergency_cancel_all", "hydra", {"count": len(cancelled)})
        return cancelled

    def check_timeouts(self) -> list[str]:
        """Check for timed-out orders."""
        return self.state_machine.check_timeouts()

    def get_stats(self) -> dict[str, Any]:
        return {
            "submitted": self._n_submitted,
            "filled": self._n_filled,
            "rejected": self._n_rejected,
            "cancelled": self._n_cancelled,
            "fill_rate": self._n_filled / max(1, self._n_submitted),
            "avg_slippage_bps": self.fill_analyzer.get_avg_slippage_bps(),
            "avg_latency_ms": self.fill_analyzer.get_avg_fill_latency_ms(),
            "p99_latency_ms": self.telemetry.get_latency_p99(),
            "throughput_per_sec": self.telemetry.get_throughput_per_sec(),
            "error_counts": self.telemetry.get_error_rate(),
            "active_orders": len(self.state_machine.get_active_orders()),
            "tce_trend": self.analytics.get_tce_trend(),
        }

    def _generate_slices(
        self, order: Order, algo: str, price: float, ctx: dict[str, Any],
    ) -> list[ExecutionSlice]:
        """Generate execution slices based on selected algo."""
        if algo == "immediate":
            return self.algo_selector.immediate_slices(order, price, ctx.get("urgency", 1.0))
        elif algo == "vwap":
            return self.algo_selector.vwap_slices(order, ctx.get("target_window", 300.0))
        elif algo == "twap":
            return self.algo_selector.twap_slices(order, ctx.get("target_window", 300.0))
        elif algo == "iceberg":
            display = ctx.get("display_qty", order.quantity * 0.1)
            return self.algo_selector.iceberg_slices(order, display)
        elif algo == "passive":
            best_bid = ctx.get("best_bid", price - 0.5)
            best_ask = ctx.get("best_ask", price + 0.5)
            return self.algo_selector.passive_slices(order, best_bid, best_ask)
        elif algo == "sniper":
            return self.algo_selector.sniper_slices(order, price)
        elif algo == "momentum":
            return self.algo_selector.momentum_slices(order, price, ctx.get("momentum", 0))
        elif algo == "stealth":
            return self.algo_selector.stealth_slices(order, price)
        # Default: immediate
        return self.algo_selector.immediate_slices(order, price)
