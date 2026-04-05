"""
SOLÉNN v2 — Order Factory & Validator (Ω-H01 to Ω-H09, Ω-H55 to Ω-H63)
Creates, validates, normalizes, and optimizes orders before dispatch.

Tópico 1.1: OrderFactory, OrderValidator, SizeOptimizer, TypeSelector,
Post-Only Guardian, PriceSnapper, QuantityNormalizer, OrderIdGenerator
Tópico 2.1: Pre-Trade Risk Checks
"""

from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass
from typing import Any

from .hydra_types import (
    Order,
    OrderConstraints,
    OrderSide,
    OrderStatus,
    OrderType,
)


@dataclass(frozen=True, slots=True)
class TickSizeRule:
    """Ω-H06: Tick size configuration per symbol."""
    min_price: float
    max_price: float
    tick_size: float


@dataclass(frozen=True, slots=True)
class LotSizeRule:
    """Ω-H07: Lot size configuration per symbol."""
    min_qty: float
    max_qty: float
    step_size: float


class PriceSnapper:
    """Ω-H06: Snap price to valid tick size."""

    def __init__(self, rules: list[TickSizeRule] | None = None) -> None:
        self._rules = rules or [TickSizeRule(0, 999999, 0.01)]

    def snap(self, price: float) -> float:
        for rule in self._rules:
            if rule.min_price <= price <= rule.max_price:
                snapped = round(math.floor(price / rule.tick_size) * rule.tick_size, 10)
                return max(snapped, rule.min_price)
        return price


class QuantityNormalizer:
    """Ω-H07: Normalize quantity to lot size/step size."""

    def __init__(self, rules: list[LotSizeRule] | None = None) -> None:
        self._rules = rules or [LotSizeRule(0.00001, 9999, 0.00001)]

    def normalize(self, qty: float) -> float:
        for rule in self._rules:
            if rule.min_qty <= qty <= rule.max_qty:
                steps = math.floor(qty / rule.step_size)
                return max(steps * rule.step_size, rule.min_qty)
        return max(qty, 0.00001)


class OrderIdGenerator:
    """Ω-H08: Deterministic unique order IDs with idempotency."""

    def __init__(self) -> None:
        self._counter = 0
        self._seen_ids: set[str] = set()

    def generate(self, trace_id: str = "") -> str:
        self._counter += 1
        oid = f"hydra-{int(time.time() * 1000)}-{self._counter:04d}"
        return oid

    def is_duplicate(self, client_order_id: str) -> bool:
        """Ω-H08, Ω-T35: Idempotency — reject duplicate order IDs."""
        return client_order_id in self._seen_ids

    def mark_seen(self, client_order_id: str) -> None:
        self._seen_ids.add(client_order_id)


class PreTradeRiskChecker:
    """Ω-H55 to Ω-H63: Pre-trade risk gate."""

    def __init__(self, constraints: OrderConstraints | None = None) -> None:
        self._constraints = constraints or OrderConstraints()
        self._current_positions: dict[str, float] = {}  # symbol -> size
        self._current_exposure = 0.0
        self._current_drawdown = 0.0
        self._order_timestamps: deque[float] = deque(maxlen=100)
        self._correlations: dict[str, dict[str, float]] = {}
        self._blacklist: set[str] = set()

    def check(self, order: Order, current_price: float) -> tuple[bool, str | None]:
        """
        Run all pre-trade checks. Returns (allowed, rejection_reason).
        """
        # Ω-H55: Position size limit
        symbol_size = self._current_positions.get(order.symbol, 0.0)
        if order.side == OrderSide.BUY:
            new_size = symbol_size + order.quantity
        else:
            new_size = symbol_size - order.quantity
        if abs(new_size) > self._constraints.max_position_size:
            return False, f"Position size {new_size} exceeds max {self._constraints.max_position_size}"

        # Ω-H56: Exposure limit
        if self._current_exposure > self._constraints.max_exposure_pct:
            return False, f"Exposure {self._current_exposure}% exceeds max {self._constraints.max_exposure_pct}%"

        # Ω-H58: Drawdown gate
        if self._current_drawdown > self._constraints.max_drawdown_pct:
            return False, f"Drawdown {self._current_drawdown}% exceeds limit {self._constraints.max_drawdown_pct}%"

        # Ω-H59: Frequency limiter
        now = time.time()
        recent = sum(1 for ts in self._order_timestamps if now - ts < 1.0)
        if recent >= self._constraints.max_orders_per_second:
            return False, f"Rate limit: {recent}/{self._constraints.max_orders_per_second} orders/sec"

        # Ω-H60: Fat finger check
        if order.price > 0 and current_price > 0:
            dev = abs(order.price - current_price) / current_price * 100
            if dev > self._constraints.max_price_deviation_pct:
                return False, f"Fat finger: price deviates {dev:.1f}% from market"

        # Ω-H62: Blacklist
        if order.symbol in self._blacklist:
            return False, f"Symbol {order.symbol} is blacklisted"

        # Ω-H61: Self-trade prevention (simplified)
        # In production: check against own open orders on same exchange

        # All checks passed
        self._order_timestamps.append(now)
        return True, None

    def update_position(self, symbol: str, delta: float) -> None:
        self._current_positions[symbol] = self._current_positions.get(symbol, 0.0) + delta

    def update_exposure(self, exposure_pct: float) -> None:
        self._current_exposure = exposure_pct

    def update_drawdown(self, dd_pct: float) -> None:
        self._current_drawdown = dd_pct

    def add_blacklist(self, symbol: str) -> None:
        self._blacklist.add(symbol)

    def remove_blacklist(self, symbol: str) -> None:
        self._blacklist.discard(symbol)


class OrderFactory:
    """
    Ω-H01 to Ω-H09: Complete order creation pipeline.
    Factory + Validator + Optimizer pipeline.
    """

    def __init__(
        self,
        price_snapper: PriceSnapper | None = None,
        quantity_normalizer: QuantityNormalizer | None = None,
        risk_checker: PreTradeRiskChecker | None = None,
    ) -> None:
        self._snapper = price_snapper or PriceSnapper()
        self._normalizer = quantity_normalizer or QuantityNormalizer()
        self._risk = risk_checker or PreTradeRiskChecker()
        self._id_gen = OrderIdGenerator()

    def create_order(
        self,
        exchange: str,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: float = 0.0,
        stop_price: float = 0.0,
        time_in_force: str = "GTC",
        trace_id: str = "",
        current_market_price: float = 0.0,
    ) -> tuple[Order | None, str | None]:
        """
        Ω-H01 to Ω-H09 + Ω-H55 to Ω-H63:
        Create → normalize → validate → risk check → return Order or rejection reason.
        """
        # Ω-H08: Idempotency check (if trace_id already seen)
        if trace_id and self._id_gen.is_duplicate(trace_id):
            return None, f"Duplicate order: {trace_id}"

        # Ω-H06: Snap price to tick size
        snapped_price = self._snapper.snap(price) if price > 0 else price

        # Ω-H07: Normalize quantity to lot size
        normalized_qty = self._normalizer.normalize(quantity)
        if normalized_qty <= 0:
            return None, f"Quantity after normalization is zero: {quantity}"

        # Create order
        client_id = self._id_gen.generate(trace_id)
        order = Order.create(
            client_order_id=client_id,
            exchange=exchange,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=normalized_qty,
            price=snapped_price,
            stop_price=stop_price,
            time_in_force=time_in_force,
            trace_id=trace_id,
        )

        # Ω-H55-H63: Pre-trade risk checks
        market_price = current_market_price if current_market_price > 0 else price
        allowed, reason = self._risk.check(order, market_price)
        if not allowed:
            return None, reason

        self._id_gen.mark_seen(trace_id) if trace_id else None
        self._risk.update_position(symbol, normalized_qty if side == OrderSide.BUY else -normalized_qty)

        return order, None

    def post_only_check(self, order: Order, best_bid: float, best_ask: float) -> tuple[Order | None, str | None]:
        """Ω-H05: Post-only guardian — ensure limit order won't cross the spread."""
        if order.order_type != OrderType.POST_ONLY:
            return order, None

        if order.side == OrderSide.BUY and order.price >= best_ask:
            # Would cross ask → reject or adjust price
            adjusted = Order.create(
                client_order_id=order.client_order_id,
                exchange=order.exchange, symbol=order.symbol,
                side=order.side, order_type=order.order_type,
                quantity=order.quantity, price=best_bid - 0.01,
                trace_id=order.trace_id,
            )
            return adjusted, None
        if order.side == OrderSide.SELL and order.price <= best_bid:
            adjusted = Order.create(
                client_order_id=order.client_order_id,
                exchange=order.exchange, symbol=order.symbol,
                side=order.side, order_type=order.order_type,
                quantity=order.quantity, price=best_ask + 0.01,
                trace_id=order.trace_id,
            )
            return adjusted, None
        return order, None
