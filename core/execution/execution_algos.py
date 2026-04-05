"""
SOLÉNN v2 — Execution Algorithms & Fill Analyzer (Ω-H28 to Ω-H54)
8 execution algorithms, fill analysis, TCE calculation,
execution quality scoring, and telemetry.

Tópico 1.4: All 8 execution algorithms
Tópico 1.5: FillAnalyzer + all fill analysis features
Tópico 1.6: Execution telemetry
"""

from __future__ import annotations

import math
import random
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from .hydra_types import Order, OrderSide, OrderStatus


# ──────────────────────────────────────────────────────────────
# Tópico 1.4: Execution Algorithms
# ──────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class ExecutionSlice:
    """A single child order from an algo."""
    quantity: float
    price: float  # 0 for market
    execute_at_ns: int  # When to execute
    order_type: str  # "market", "limit", etc.
    algo_name: str


@dataclass
class TWAPState:
    """State for TWAP execution."""
    total_quantity: float
    executed_quantity: float
    num_slices: int
    current_slice: int
    slice_interval_ms: float
    avg_fill_price: float
    start_time_ns: int
    fills: list[tuple[float, float]]  # (qty, price)


class ExecutionAlgoSelector:
    """
    Ω-H28 to Ω-H35: 8 execution algorithms.
    Ω-H36: Selector based on urgency, size, regime, liquidity.
    """

    @staticmethod
    def immediate_slices(
        order: Order, best_price: float, urgency_pct: float = 1.0,
    ) -> list[ExecutionSlice]:
        """Ω-H28: Execute immediately, optionally split for large orders."""
        now = time.time_ns()
        # Split into up to 3 slices for large orders
        if order.quantity > 5.0:
            slices = []
            remaining = order.quantity
            for i, frac in enumerate([0.5, 0.3, 0.2]):
                qty = remaining * frac if i < 2 else remaining
                slices.append(ExecutionSlice(
                    quantity=qty, price=best_price,
                    execute_at_ns=now + i * 50_000_000,  # 50ms apart
                    order_type="market", algo_name="immediate",
                ))
                remaining -= qty
            return slices
        return [ExecutionSlice(
            quantity=order.quantity, price=best_price,
            execute_at_ns=now, order_type="market", algo_name="immediate",
        )]

    @staticmethod
    def vwap_slices(
        order: Order, target_window_seconds: float,
        volume_profile: list[float] | None = None,
    ) -> list[ExecutionSlice]:
        """
        Ω-H29: VWAP-based execution scheduling.
        volume_profile = expected volume per sub-interval.
        """
        now = time.time_ns()
        n_slices = max(4, int(target_window_seconds / 5.0))  # At least 4 slices
        if volume_profile is None:
            volume_profile = [1.0] * n_slices
        total_vol = sum(volume_profile)
        allocation = [v / total_vol for v in volume_profile[:n_slices]]

        slices = []
        for i, frac in enumerate(allocation):
            qty = order.quantity * frac
            execute_at = now + int(i * target_window_seconds / n_slices * 1e9)
            slices.append(ExecutionSlice(
                quantity=qty, price=0.0,  # Market at slice time
                execute_at_ns=execute_at,
                order_type="limit", algo_name="vwap",
            ))
        return slices

    @staticmethod
    def twap_slices(
        order: Order, target_window_seconds: float,
        num_slices: int | None = None,
    ) -> list[ExecutionSlice]:
        """Ω-H30: TWAP with randomization to avoid fingerprinting."""
        now = time.time_ns()
        n = num_slices or max(4, int(target_window_seconds / 10.0))
        qty_per_slice = order.quantity / n
        interval_ns = int(target_window_seconds / n * 1e9)

        slices = []
        for i in range(n):
            # Random jitter ±20% to avoid fingerprinting
            jitter = int(interval_ns * 0.2 * (random.random() - 0.5))
            execute_at = now + i * interval_ns + jitter
            slices.append(ExecutionSlice(
                quantity=qty_per_slice, price=0.0,
                execute_at_ns=execute_at,
                order_type="limit", algo_name="twap",
            ))
        return slices

    @staticmethod
    def iceberg_slices(
        order: Order, display_qty: float,
    ) -> list[ExecutionSlice]:
        """Ω-H31: Iceberg — show only display_qty at a time."""
        now = time.time_ns()
        n_slices = math.ceil(order.quantity / display_qty)
        slices = []
        for i in range(n_slices):
            remaining = order.quantity - i * display_qty
            qty = min(display_qty, remaining)
            slices.append(ExecutionSlice(
                quantity=qty, price=0.0,
                execute_at_ns=now + i * 100_000_000,  # 100ms between refreshes
                order_type="limit", algo_name="iceberg",
            ))
        return slices

    @staticmethod
    def passive_slices(
        order: Order, best_bid: float, best_ask: float,
        offset_ticks: float = 1.0,
    ) -> list[ExecutionSlice]:
        """Ω-H32: Passive — place limit orders inside spread."""
        now = time.time_ns()
        if order.side == OrderSide.BUY:
            # Place at best_bid + offset (slightly aggressive passive)
            price = best_bid + offset_ticks
        else:
            price = best_ask - offset_ticks
        return [ExecutionSlice(
            quantity=order.quantity, price=price,
            execute_at_ns=now, order_type="limit", algo_name="passive",
        )]

    @staticmethod
    def sniper_slices(
        order: Order, best_price: float,
    ) -> list[ExecutionSlice]:
        """Ω-H33: Sniper — execute all at once when liquidity spike detected."""
        now = time.time_ns()
        return [ExecutionSlice(
            quantity=order.quantity, price=best_price,
            execute_at_ns=now, order_type="market", algo_name="sniper",
        )]

    @staticmethod
    def momentum_slices(
        order: Order, best_price: float,
        momentum_direction: float,  # +1 = up, -1 = down
    ) -> list[ExecutionSlice]:
        """
        Ω-H34: Momentum — accelerate in trending direction.
        If buying in uptrend, go fast (more now). If buying in downtrend,
        stagger (wait for dip).
        """
        now = time.time_ns()
        if momentum_direction > 0.5 and order.side == OrderSide.BUY:
            # Urgent — buy now before price rises
            return [ExecutionSlice(
                quantity=order.quantity, price=best_price,
                execute_at_ns=now, order_type="market", algo_name="momentum",
            )]
        elif momentum_direction < -0.5 and order.side == OrderSide.SELL:
            # Urgent — sell now
            return [ExecutionSlice(
                quantity=order.quantity, price=best_price,
                execute_at_ns=now, order_type="market", algo_name="momentum",
            )]
        else:
            # Staggered
            twap = ExecutionAlgoSelector.twap_slices(order, 60.0, num_slices=4)
            for s in twap:
                s = ExecutionSlice(
                    quantity=s.quantity, price=s.price,
                    execute_at_ns=s.execute_at_ns,
                    order_type=s.order_type, algo_name="momentum",
                )
            return twap

    @staticmethod
    def stealth_slices(
        order: Order, best_price: float,
        min_slices: int = 8, max_slices: int = 20,
    ) -> list[ExecutionSlice]:
        """
        Ω-H35: Stealth — randomize timing, sizing, and order type.
        Maximum obfuscation to avoid fingerprinting.
        """
        now = time.time_ns()
        n = random.randint(min_slices, max_slices)
        # Random sizing: not uniform
        raw_weights = [random.random() for _ in range(n)]
        total_w = sum(raw_weights)
        weights = [w / total_w for w in raw_weights]

        # Random timing
        total_window = random.uniform(30.0, 300.0)  # 30s to 5min
        execute_times = sorted([
            now + int(random.uniform(0, total_window) * 1e9)
            for _ in range(n)
        ])

        # Randomize order types
        order_types = ["limit", "market", "ioc"]

        slices = []
        for i in range(n):
            qty = order.quantity * weights[i]
            # Randomize price slightly
            price_jitter = best_price * (1 + random.uniform(-0.001, 0.001))
            slices.append(ExecutionSlice(
                quantity=qty, price=price_jitter,
                execute_at_ns=execute_times[i],
                order_type=random.choice(order_types),
                algo_name="stealth",
            ))
        return slices

    @staticmethod
    def select_algo(
        order: Order,
        urgency: float = 0.5,  # 0-1: how fast we need to execute
        regime: str = "normal",
        liquidity_pct: float = 50.0,  # How much of ADV our order represents
    ) -> str:
        """Ω-H36: Select optimal algorithm based on context."""
        # High urgency → immediate or sniper
        if urgency > 0.8:
            return "sniper" if liquidity_pct > 20 else "immediate"

        # Low urgency + low liquidity cost → twap/stealth
        if urgency < 0.2 and liquidity_pct < 5:
            return "stealth" if regime == "normal" else "twap"

        # Passive if regime is favorable and we have time
        if regime == "ranging" and urgency < 0.5:
            return "passive"

        # Momentum if trending
        if regime.startswith("trending"):
            return "momentum"

        # Default: TWAP for balanced approach
        return "twap"


# ──────────────────────────────────────────────────────────────
# Tópico 1.5: Fill Analyzer
# ──────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class ExecutionMetrics:
    """Ω-H37-H45: Complete execution quality metrics."""
    order_id: str
    fill_price: float
    arrival_price: float  # Price when order was decided
    vwap: float  # VWAP during execution window
    slippage_bps: float  # (fill - arrival) / arrival * 10000
    market_impact_bps: float  # Δp attributed to our order
    fill_rate: float  # Filled qty / ordered qty
    avg_latency_ms: float  # Average fill latency
    tce_usd: float  # Total cost of execution
    execution_quality_score: float  # 0-100 composite score
    timestamp_ns: int = field(default_factory=lambda: time.time_ns())


class FillAnalyzer:
    """
    Ω-H37 to Ω-H45: Post-trade fill analysis.
    """

    def __init__(self) -> None:
        self._metrics: list[ExecutionMetrics] = []
        self._slippage_history: deque[float] = deque(maxlen=1000)
        self._fill_latencies: deque[float] = deque(maxlen=1000)

    def analyze_fill(
        self,
        order: Order,
        arrival_price: float,
        vwap_during_execution: float,
        market_impact_bps: float = 0.0,
        avg_latency_ms: float = 0.0,
    ) -> ExecutionMetrics:
        """Ω-H37-H45: Analyze a completed fill."""
        if order.avg_fill_price <= 0:
            return ExecutionMetrics(
                order_id=order.order_id, fill_price=0,
                arrival_price=arrival_price, vwap=vwap_during_execution,
                slippage_bps=0, market_impact_bps=0, fill_rate=0,
                avg_latency_ms=0, tce_usd=0, execution_quality_score=0,
            )

        fill_px = order.avg_fill_price

        # Ω-H37: Slippage
        if arrival_price > 0:
            if order.side == OrderSide.BUY:
                slippage_bps = (fill_px - arrival_price) / arrival_price * 10000
            else:
                slippage_bps = (arrival_price - fill_px) / arrival_price * 10000
        else:
            slippage_bps = 0.0

        self._slippage_history.append(slippage_bps)
        self._fill_latencies.append(avg_latency_ms)

        # Ω-H44: TCE
        commission_cost = order.commission_total
        slippage_cost_usd = abs(slippage_bps / 10000) * fill_px * order.filled_quantity
        impact_cost_usd = market_impact_bps / 10000 * fill_px * order.filled_quantity
        tce = commission_cost + slippage_cost_usd + impact_cost_usd

        # Ω-H43: Quality score (0-100)
        # Penalize for slippage, impact, low fill rate, high latency
        fill_rate = order.fill_pct
        slippage_penalty = min(30, abs(slippage_bps) * 2)
        impact_penalty = min(20, market_impact_bps * 3)
        fill_rate_penalty = (1 - fill_rate) * 25
        latency_penalty = min(15, avg_latency_ms * 0.5)
        quality = max(0, 100 - slippage_penalty - impact_penalty - fill_rate_penalty - latency_penalty)

        metrics = ExecutionMetrics(
            order_id=order.order_id,
            fill_price=fill_px,
            arrival_price=arrival_price,
            vwap=vwap_during_execution,
            slippage_bps=slippage_bps,
            market_impact_bps=market_impact_bps,
            fill_rate=fill_rate,
            avg_latency_ms=avg_latency_ms,
            tce_usd=tce,
            execution_quality_score=quality,
        )
        self._metrics.append(metrics)
        return metrics

    def get_avg_slippage_bps(self) -> float:
        if not self._slippage_history:
            return 0.0
        return sum(self._slippage_history) / len(self._slippage_history)

    def get_avg_fill_latency_ms(self) -> float:
        if not self._fill_latencies:
            return 0.0
        return sum(self._fill_latencies) / len(self._fill_latencies)

    def get_metrics(self) -> list[ExecutionMetrics]:
        return list(self._metrics)


# ──────────────────────────────────────────────────────────────
# Tópico 1.6: Execution Telemetry
# ──────────────────────────────────────────────────────────────

class ExecutionTelemetry:
    """
    Ω-H46 to Ω-H54: End-to-end execution monitoring and telemetry.
    """

    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []
        self._latency_history: deque[float] = deque(maxlen=500)
        self._throughput: deque[tuple[float, int]] = deque(maxlen=100)  # (timestamp, count)
        self._error_counts: dict[str, int] = {}

    def emit(
        self, event_type: str, component: str, data: dict[str, Any],
        latency_us: int = 0,
    ) -> None:
        self._events.append({
            "type": event_type, "component": component,
            "data": data, "latency_us": latency_us,
            "timestamp": time.time(),
        })
        if latency_us > 0:
            self._latency_history.append(latency_us / 1000.0)

        # Ω-H47: Throughput counting
        now = time.time()
        if not self._throughput or now - self._throughput[-1][0] > 1.0:
            self._throughput.append((now, 1))
        else:
            ts, cnt = self._throughput[-1]
            self._throughput[-1] = (ts, cnt + 1)

    def record_error(self, error_type: str) -> None:
        """Ω-H48: Track error rates."""
        self._error_counts[error_type] = self._error_counts.get(error_type, 0) + 1

    def get_latency_p99(self) -> float:
        """Ω-H46: P99 end-to-end latency."""
        if not self._latency_history:
            return 0.0
        s = sorted(self._latency_history)
        idx = int(len(s) * 0.99)
        return s[min(idx, len(s) - 1)]

    def get_throughput_per_sec(self) -> float:
        """Ω-H47: Current throughput."""
        if len(self._throughput) < 2:
            return 0.0
        # Average of last 5 seconds
        recent = list(self._throughput)[-5:]
        return sum(cnt for _, cnt in recent) / max(1, len(recent))

    def get_error_rate(self) -> dict[str, int]:
        """Ω-H48: Error rates by type."""
        return dict(self._error_counts)
