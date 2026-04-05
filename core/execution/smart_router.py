"""
SOLÉNN v2 — Smart Order Router (Ω-H19 to Ω-H27)
Multi-exchange routing, order splitting, failover,
connection pooling, rate limiting, and arb protection.

Tópico 1.3: ExchangeSelector, OrderSplitter, LatencyMonitor,
FeeOptimizer, FailoverHandler, ConnectionPool, RateLimitTracker,
CrossExchangeArbProtector, RoutingHistory
"""

from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from .hydra_types import Exchange, Order, OrderSide


@dataclass(frozen=True, slots=True)
class ExchangeState:
    """Real-time state of an exchange."""
    exchange: str
    best_bid: float = 0.0
    best_ask: float = 0.0
    depth_bid: float = 0.0  # Total bid depth
    depth_ask: float = 0.0
    maker_fee: float = 0.001
    taker_fee: float = 0.001
    latency_ms: float = 0.0
    uptime_pct: float = 100.0
    is_online: bool = True
    rate_remaining: int = 1000
    last_updated_ns: int = field(default_factory=lambda: time.time_ns())


@dataclass(frozen=True, slots=True)
class RoutingDecision:
    """Ω-H27: Immutable routing decision record."""
    order_id: str
    target_exchanges: list[str]  # May be multiple for split orders
    allocation: dict[str, float]  # exchange -> qty fraction
    total_tce: float  # Estimated total cost of execution
    reasoning: str
    timestamp_ns: int = field(default_factory=lambda: time.time_ns())


class LatencyMonitor:
    """Ω-H21: Real-time latency monitoring per exchange."""

    def __init__(self, window: int = 200) -> None:
        self._latencies: dict[str, deque[float]] = {}
        self._window = window

    def record(self, exchange: str, latency_ms: float) -> None:
        if exchange not in self._latencies:
            self._latencies[exchange] = deque(maxlen=self._window)
        self._latencies[exchange].append(latency_ms)

    def get_p50(self, exchange: str) -> float:
        if exchange not in self._latencies or not self._latencies[exchange]:
            return 0.0
        s = sorted(self._latencies[exchange])
        return s[len(s) // 2]

    def get_p95(self, exchange: str) -> float:
        if exchange not in self._latencies or not self._latencies[exchange]:
            return 0.0
        s = sorted(self._latencies[exchange])
        idx = int(len(s) * 0.95)
        return s[min(idx, len(s) - 1)]

    def get_p99(self, exchange: str) -> float:
        if exchange not in self._latencies or not self._latencies[exchange]:
            return 0.0
        s = sorted(self._latencies[exchange])
        idx = int(len(s) * 0.99)
        return s[min(idx, len(s) - 1)]

    def get_avg(self, exchange: str) -> float:
        if exchange not in self._latencies or not self._latencies[exchange]:
            return 0.0
        return sum(self._latencies[exchange]) / len(self._latencies[exchange])

    def get_all_exchanges(self) -> list[str]:
        return list(self._latencies.keys())


class RateLimitTracker:
    """Ω-H25: Per-exchange rate limit tracking with adaptive throttling."""

    def __init__(self) -> None:
        # exchange -> (max_requests, window_seconds, current_window_start, count)
        self._limits: dict[str, tuple[int, float, float, int]] = {}
        self._throttle_until: dict[str, float] = {}  # exchange -> timestamp

    def set_limit(self, exchange: str, max_requests: int, window_seconds: float) -> None:
        now = time.time()
        self._limits[exchange] = (max_requests, window_seconds, now, 0)

    def record_request(self, exchange: str) -> bool:
        """Returns True if request is allowed, False if rate limited."""
        if exchange in self._throttle_until:
            if time.time() < self._throttle_until[exchange]:
                return False
            del self._throttle_until[exchange]

        if exchange not in self._limits:
            return True

        max_req, window, win_start, count = self._limits[exchange]
        now = time.time()

        if now - win_start >= window:
            # New window
            self._limits[exchange] = (max_req, window, now, 1)
            return True

        if count >= max_req:
            self._throttle_until[exchange] = win_start + window
            return False

        self._limits[exchange] = (max_req, window, win_start, count + 1)
        return True

    def get_remaining(self, exchange: str) -> int:
        if exchange not in self._limits:
            return 999
        max_req, _, _, count = self._limits[exchange]
        return max(0, max_req - count)


class ConnectionPool:
    """Ω-H24: Persistent connection pool with health check."""

    def __init__(self) -> None:
        self._connections: dict[str, dict[str, Any]] = {}
        self._health: dict[str, float] = {}  # exchange -> last_heartbeat

    def register(self, exchange: str, conn_id: str) -> None:
        self._connections[exchange] = {
            "conn_id": conn_id,
            "created_at": time.time(),
            "status": "active",
            "reconnect_count": 0,
        }
        self._health[exchange] = time.time()

    def heartbeat(self, exchange: str) -> None:
        self._health[exchange] = time.time()
        if exchange in self._connections:
            self._connections[exchange]["status"] = "active"

    def is_healthy(self, exchange: str, timeout_s: float = 5.0) -> bool:
        last = self._health.get(exchange, 0)
        return (time.time() - last) < timeout_s

    def mark_failed(self, exchange: str) -> None:
        if exchange in self._connections:
            self._connections[exchange]["status"] = "failed"
            self._connections[exchange]["reconnect_count"] += 1


class SmartOrderRouter:
    """
    Ω-H19 to Ω-H27: Smart order routing engine.
    """

    def __init__(self) -> None:
        self._states: dict[str, ExchangeState] = {}
        self._latency_monitor = LatencyMonitor()
        self._rate_limiter = RateLimitTracker()
        self._conn_pool = ConnectionPool()
        self._routing_history: list[RoutingDecision] = []
        # Ω-H26: Arb protection — track our own positions
        self._our_positions: dict[str, dict[str, float]] = {}  # exchange -> symbol -> qty

    def register_exchange(
        self, exchange: str, best_bid: float = 0.0, best_ask: float = 0.0,
        depth_bid: float = 0.0, depth_ask: float = 0.0,
        maker_fee: float = 0.001, taker_fee: float = 0.001,
    ) -> None:
        """Register exchange with initial state."""
        self._states[exchange] = ExchangeState(
            exchange=exchange, best_bid=best_bid, best_ask=best_ask,
            depth_bid=depth_bid, depth_ask=depth_ask,
            maker_fee=maker_fee, taker_fee=taker_fee,
        )
        self._conn_pool.register(exchange, f"conn-{exchange}")

    def update_exchange_state(self, exchange: str, **kwargs: Any) -> None:
        if exchange in self._states:
            current = self._states[exchange]
            updates = {k: v for k, v in kwargs.items() if hasattr(current, k)}
            import dataclasses
            self._states[exchange] = dataclasses.replace(current, **updates, last_updated_ns=time.time_ns())

    def select_best_exchange(
        self, order: Order, tce_budget_usd: float = 0.0,
    ) -> str | None:
        """
        Ω-H19, Ω-H22: Select best exchange minimizing TCE.
        TCE = fee + estimated_slippage + latency_cost
        """
        best_ex = None
        best_tce = float("inf")

        for ex_name, state in self._states.items():
            if not state.is_online:
                continue

            # Fee cost
            fee_rate = state.taker_fee if order.order_type.value == "market" else state.maker_fee
            fee_cost = order.quantity * state.best_ask * fee_rate if order.side == OrderSide.BUY else order.quantity * state.best_bid * fee_rate

            # Latency cost (higher latency = higher risk of adverse move)
            lat_cost = self._latency_monitor.get_avg(ex_name) * 0.01 * order.quantity  # Simplified

            total_tce = fee_cost + lat_cost

            if total_tce < best_tce:
                best_tce = total_tce
                best_ex = ex_name

        if tce_budget_usd > 0 and best_tce > tce_budget_usd:
            return None  # No exchange within budget

        return best_ex

    def split_order(
        self, order: Order, max_single_exchange_pct: float = 60.0,
        max_single_exchange_qty: float | None = None,
    ) -> list[tuple[str, float]]:
        """
        Ω-H20: Split large order across exchanges.
        Returns [(exchange, qty), ...].
        Splits when order exceeds max_single_exchange_pct of book depth.
        """
        import dataclasses
        online_exchanges = [
            (ex, st) for ex, st in self._states.items()
            if st.is_online and (st.depth_ask > 0 if order.side == OrderSide.BUY else st.depth_bid > 0)
        ]
        if not online_exchanges:
            return [(order.exchange, order.quantity)]

        # Check if splitting is needed
        best_ex, best_st = sorted(
            online_exchanges,
            key=lambda x: x[1].depth_ask if order.side == OrderSide.BUY else x[1].depth_bid,
            reverse=True,
        )[0]
        best_depth = best_st.depth_ask if order.side == OrderSide.BUY else best_st.depth_bid
        max_single = best_depth * (max_single_exchange_pct / 100.0)

        if max_single_exchange_qty:
            max_single = min(max_single, max_single_exchange_qty)

        if order.quantity <= max_single:
            return [(order.exchange, order.quantity)]  # No split needed

        # Split proportionally to depth
        remaining = order.quantity
        allocations: list[tuple[str, float]] = []

        for ex_name, state in sorted(
            online_exchanges,
            key=lambda x: x[1].depth_ask if order.side == OrderSide.BUY else x[1].depth_bid,
            reverse=True,
        ):
            if remaining <= 0:
                break
            depth = state.depth_ask if order.side == OrderSide.BUY else state.depth_bid
            alloc_qty = min(remaining, depth * (max_single_exchange_pct / 100.0), max_single)
            if alloc_qty > 0:
                allocations.append((ex_name, alloc_qty))
                remaining -= alloc_qty

        # Dump remaining on best exchange
        if remaining > 0.00001 and allocations:
            allocations[0] = (allocations[0][0], allocations[0][1] + remaining)
        elif remaining > 0.00001:
            allocations.append((order.exchange, remaining))

        return allocations

    def route_order(
        self,
        order: Order,
        tce_budget_usd: float = 0.0,
    ) -> RoutingDecision:
        """
        Ω-H19-H27: Full routing decision.
        """
        # Ω-H26: Arb protection — check we're not trading against ourselves
        if self._is_arb_against_self(order):
            return RoutingDecision(
                order_id=order.order_id, target_exchanges=[],
                allocation={}, total_tce=0,
                reasoning="BLOCKED: cross-exchange arb against own position",
            )

        # Select exchange
        exchanges_to_use = [order.exchange]
        allocation = {order.exchange: order.quantity}

        if len(self._states) > 1:
            splits = self.split_order(order)
            exchanges_to_use = [s[0] for s in splits]
            total_qty = sum(s[1] for s in splits)
            allocation = {ex: qty / total_qty for ex, qty in splits} if total_qty > 0 else {}

        tce = self._estimate_tce(order, exchanges_to_use)

        decision = RoutingDecision(
            order_id=order.order_id,
            target_exchanges=exchanges_to_use,
            allocation=allocation,
            total_tce=tce,
            reasoning=f"Routed to {', '.join(exchanges_to_use)}, TCE=${tce:.2f}",
        )
        self._routing_history.append(decision)
        return decision

    def update_latency(self, exchange: str, latency_ms: float) -> None:
        self._latency_monitor.record(exchange, latency_ms)

    def _is_arb_against_self(self, order: Order) -> bool:
        """Ω-H26: Detect if we're about to arb against our own position."""
        for ex_name in self._states:
            if ex_name == order.exchange:
                continue
            positions = self._our_positions.get(ex_name, {})
            qty = positions.get(order.symbol, 0.0)
            # If we're long on ex A and trying to buy on ex B → no arb risk
            # If we're long on ex A and trying to sell on ex B → potential arb
            if order.side == OrderSide.SELL and qty > 0:
                return True  # Selling on B while long on A
            if order.side == OrderSide.BUY and qty < 0:
                return True  # Buying on B while short on A
        return False

    def _estimate_tce(self, order: Order, exchanges: list[str]) -> float:
        """Estimate total cost of execution."""
        total = 0.0
        for ex_name in exchanges:
            st = self._states.get(ex_name)
            if not st:
                continue
            fee = st.taker_fee if order.order_type.value == "market" else st.maker_fee
            price = st.best_ask if order.side == OrderSide.BUY else st.best_bid
            total += order.quantity * price * fee
        return total

    def get_routing_history(self) -> list[RoutingDecision]:
        return list(self._routing_history)
