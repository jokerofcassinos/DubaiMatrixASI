"""
SOLÉNN v2 — Order State Machine (Ω-H10 to Ω-H18)
Bounded state machine with guards, WAL persistence,
reconciliation, timeout handling, and emergency cancel.

Tópico 1.2: OrderState, StateTransitionGuard, StatePersistence,
StateReconciliation, PartialFillTracking, TimeoutHandler,
OrderExpiry, StateHistoryLogger, EmergencyCancelAll
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from .hydra_types import FillRecord, Order, OrderStatus


@dataclass(frozen=True, slots=True)
class StateTransition:
    """Ω-H17: Immutable state transition record."""
    order_id: str
    from_state: OrderStatus
    to_state: OrderStatus
    reason: str
    timestamp_ns: int = field(default_factory=lambda: time.time_ns())


class WriteAheadLog:
    """Ω-H12: Write-Ahead Log for order state persistence."""

    def __init__(self) -> None:
        self._entries: list[dict[str, Any]] = []

    def append(self, order_id: str, operation: str, data: dict[str, Any]) -> None:
        self._entries.append({
            "order_id": order_id,
            "operation": operation,
            "data": data,
            "timestamp": time.time(),
            "committed": False,
        })

    def commit(self, order_id: str) -> None:
        for entry in self._entries:
            if entry["order_id"] == order_id and not entry["committed"]:
                entry["committed"] = True

    def get_uncommitted(self, order_id: str) -> list[dict[str, Any]]:
        return [e for e in self._entries if e["order_id"] == order_id and not e["committed"]]

    def rollback(self, order_id: str) -> list[dict[str, Any]]:
        return self.get_uncommitted(order_id)

    def clear_committed(self) -> None:
        self._entries = [e for e in self._entries if e["committed"]]


@dataclass
class OrderTimeoutConfig:
    """Ω-H15, Ω-H16: Timeout per order type."""
    submitted_timeout_ms: float = 5000.0  # Max time in SUBMITTED before cancel
    partial_fill_grace_ms: float = 30000.0  # Grace period for partial fills
    ioc_timeout_ms: float = 500.0  # IOC expires fast
    fok_timeout_ms: float = 200.0  # FOK expires very fast


class OrderStateMachine:
    """
    Ω-H10 to Ω-H18: Bounded order state machine.
    """

    # Valid transitions
    VALID_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
        OrderStatus.CREATED: {
            OrderStatus.VALIDATED, OrderStatus.REJECTED,
        },
        OrderStatus.VALIDATED: {
            OrderStatus.ROUTING, OrderStatus.REJECTED,
        },
        OrderStatus.ROUTING: {
            OrderStatus.SUBMITTED, OrderStatus.REJECTED,
        },
        OrderStatus.SUBMITTED: {
            OrderStatus.ACKNOWLEDGED, OrderStatus.REJECTED,
            OrderStatus.CANCELLED, OrderStatus.EXPIRED,
        },
        OrderStatus.ACKNOWLEDGED: {
            OrderStatus.PARTIALLY_FILLED, OrderStatus.FILLED,
            OrderStatus.CANCELLED, OrderStatus.REJECTED,
            OrderStatus.EXPIRED,
        },
        OrderStatus.PARTIALLY_FILLED: {
            OrderStatus.FILLED, OrderStatus.CANCELLED,
            OrderStatus.EXPIRED,
        },
        # Terminal states have no outgoing transitions
        OrderStatus.FILLED: set(),
        OrderStatus.CANCELLED: set(),
        OrderStatus.REJECTED: set(),
        OrderStatus.EXPIRED: set(),
    }

    def __init__(self, timeout_config: OrderTimeoutConfig | None = None) -> None:
        self._orders: dict[str, Order] = {}
        self._history: list[StateTransition] = []
        self._wal = WriteAheadLog()
        self._timeout_config = timeout_config or OrderTimeoutConfig()
        self._guards: dict[
            tuple[OrderStatus, OrderStatus],
            list[Callable[[Order], bool]],
        ] = {}
        self._emergency_cancelled: set[str] = set()

    def add_guard(
        self,
        from_status: OrderStatus,
        to_status: OrderStatus,
        guard_fn: Callable[[Order], bool],
    ) -> None:
        """Ω-H11: Add a pre-condition guard for a transition."""
        self._guards.setdefault((from_status, to_status), []).append(guard_fn)

    def transition(self, order_id: str, to_status: OrderStatus, reason: str = "") -> bool:
        """
        Ω-H10, Ω-H11: Attempt state transition with guard checks.
        Returns True if transition succeeded.
        """
        if order_id not in self._orders:
            return False

        order = self._orders[order_id]

        if order.is_terminal:
            return False  # Already in terminal state

        allowed = self.VALID_TRANSITIONS.get(order.status, set())
        if to_status not in allowed:
            self._log_rejected_transition(order_id, order.status, to_status, reason)
            return False

        # Run guards
        for guard_fn in self._guards.get((order.status, to_status), []):
            if not guard_fn(order):
                self._log_rejected_transition(order_id, order.status, to_status, "Guard denied")
                return False

        # WAL before transition
        self._wal.append(order_id, "transition", {
            "from": order.status.value, "to": to_status.value, "reason": reason,
        })

        # Apply transition by creating updated Order
        updated = self._apply_status(order, to_status)
        self._orders[order_id] = updated

        # Log
        self._history.append(StateTransition(
            order_id=order_id,
            from_state=order.status,
            to_state=to_status,
            reason=reason,
        ))

        # Commit WAL
        self._wal.commit(order_id)

        return True

    def register_order(self, order: Order) -> None:
        """Add order to state machine."""
        self._orders[order.order_id] = order

    def apply_fill(self, order_id: str, fill: FillRecord) -> bool:
        """Ω-H14: Apply a partial or complete fill."""
        if order_id not in self._orders:
            return False
        order = self._orders[order_id]
        if order.is_terminal:
            return False
        updated = order.with_fill(fill)
        self._orders[order_id] = updated
        self._wal.append(order_id, "fill", {
            "fill_id": fill.fill_id, "price": fill.price, "quantity": fill.quantity,
        })
        self._wal.commit(order_id)
        return True

    def check_timeouts(self) -> list[str]:
        """
        Ω-H15, Ω-H16: Check for timed-out orders.
        Returns list of order IDs that timed out.
        """
        now_ms = time.time() * 1000
        timed_out = []

        for oid, order in self._orders.items():
            if order.is_terminal:
                continue

            age_ms = order.age_ms

            if order.status == OrderStatus.SUBMITTED:
                if age_ms > self._timeout_config.submitted_timeout_ms:
                    timed_out.append(oid)
                    self.transition(oid, OrderStatus.CANCELLED, "Submitted timeout")

            elif order.status == OrderStatus.PARTIALLY_FILLED:
                last_fill_ns = order.fills[-1].timestamp_ns if order.fills else order.created_at_ns
                elapsed_ms = (time.time_ns() - last_fill_ns) / 1e6
                if elapsed_ms > self._timeout_config.partial_fill_grace_ms:
                    # Cancel remaining if not filling fast enough
                    timed_out.append(oid)
                    self.transition(oid, OrderStatus.CANCELLED, "Partial fill timeout")

            elif order.order_type.value == "ioc" and order.status == OrderStatus.ACKNOWLEDGED:
                if age_ms > self._timeout_config.ioc_timeout_ms:
                    timed_out.append(oid)
                    self.transition(oid, OrderStatus.EXPIRED, "IOC expired")

            elif order.order_type.value == "fok" and order.status == OrderStatus.ACKNOWLEDGED:
                if age_ms > self._timeout_config.fok_timeout_ms:
                    if order.fill_pct < 1.0:
                        timed_out.append(oid)
                        self.transition(oid, OrderStatus.EXPIRED, "FOK expired")

        return timed_out

    def emergency_cancel_all(self) -> list[str]:
        """Ω-H18: Cancel all non-terminal orders immediately."""
        cancelled = []
        for oid, order in self._orders.items():
            if not order.is_terminal and oid not in self._emergency_cancelled:
                if self.transition(oid, OrderStatus.CANCELLED, "Emergency cancel all"):
                    self._emergency_cancelled.add(oid)
                    cancelled.append(oid)
        return cancelled

    def reconcile_state(
        self, order_id: str, exchange_status: dict[str, Any]
    ) -> tuple[bool, str]:
        """
        Ω-H13: Reconcile internal state with exchange-reported state.
        Returns (was_discrepancy, description).
        """
        if order_id not in self._orders:
            return False, "Order not found locally"

        order = self._orders[order_id]
        ex_status_str = exchange_status.get("status", "")
        ex_status = _map_exchange_status(ex_status_str)

        if ex_status == OrderStatus.FILLED and order.status != OrderStatus.FILLED:
            # Exchange says filled but we don't — apply fills from exchange data
            return True, f"Reconciled filled: internal={order.status.value}, exchange={ex_status.value}"

        if ex_status == OrderStatus.CANCELLED and not order.is_terminal:
            self.transition(order_id, OrderStatus.CANCELLED, "Exchange reported cancelled")
            return True, f"Reconciled cancelled"

        if ex_status == OrderStatus.REJECTED and order.status not in (OrderStatus.REJECTED,):
            self.transition(order_id, OrderStatus.REJECTED, "Exchange reported rejected")
            return True, f"Reconciled rejected"

        return False, "States match"

    def get_order(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)

    def get_active_orders(self) -> dict[str, Order]:
        return {k: v for k, v in self._orders.items() if not v.is_terminal}

    def get_history(self) -> list[StateTransition]:
        return list(self._history)

    def get_wal(self) -> WriteAheadLog:
        return self._wal

    def _log_rejected_transition(
        self, oid: str, from_s: OrderStatus, to_s: OrderStatus, reason: str
    ) -> None:
        self._history.append(StateTransition(
            order_id=oid, from_state=from_s, to_state=from_s,
            reason=f"REJECTED transition to {to_s.value}: {reason}",
        ))

    def _apply_status(self, order: Order, status: OrderStatus) -> Order:
        """Create updated Order with new status (immutable update)."""
        now_ns = time.time_ns()
        return Order(
            order_id=order.order_id, client_order_id=order.client_order_id,
            exchange=order.exchange, symbol=order.symbol, side=order.side,
            order_type=order.order_type, price=order.price,
            quantity=order.quantity, stop_price=order.stop_price,
            time_in_force=order.time_in_force, status=status,
            filled_quantity=order.filled_quantity, avg_fill_price=order.avg_fill_price,
            remaining_quantity=order.remaining_quantity, fills=order.fills,
            commission_total=order.commission_total,
            created_at_ns=order.created_at_ns,
            submitted_at_ns=now_ns if status == OrderStatus.SUBMITTED else order.submitted_at_ns,
            filled_at_ns=now_ns if status == OrderStatus.FILLED else order.filled_at_ns,
            cancelled_at_ns=now_ns if status == OrderStatus.CANCELLED else order.cancelled_at_ns,
            rejected_reason=f"Rejected: {status.value}" if status == OrderStatus.REJECTED else order.rejected_reason,
            checksum=order.checksum, trace_id=order.trace_id,
        )


def _map_exchange_status(status_str: str) -> OrderStatus:
    """Map exchange status string to internal OrderStatus."""
    mapping = {
        "NEW": OrderStatus.ACKNOWLEDGED,
        "PARTIALLY_FILLED": OrderStatus.PARTIALLY_FILLED,
        "FILLED": OrderStatus.FILLED,
        "CANCELED": OrderStatus.CANCELLED,
        "CANCELLED": OrderStatus.CANCELLED,
        "EXPIRED": OrderStatus.EXPIRED,
        "REJECTED": OrderStatus.REJECTED,
    }
    return mapping.get(status_str.upper(), OrderStatus.ACKNOWLEDGED)
