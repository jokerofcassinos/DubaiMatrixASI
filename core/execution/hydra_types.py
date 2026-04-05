"""
SOLÉNN v2 — Hydra Execution Types (Ω-H01 to Ω-H18)
Immutable typed data structures for orders, fills, execution state,
with CRC32 checksums, state machines, and idempotency.

Tópico 1.1: Order types and validation
Tópico 1.2: Order state machine
"""

from __future__ import annotations

import math
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_MARKET = "stop_market"
    STOP_LIMIT = "stop_limit"
    IOC = "ioc"  # Immediate-or-cancel
    FOK = "fok"  # Fill-or-kill
    POST_ONLY = "post_only"


class OrderStatus(Enum):
    CREATED = "created"
    VALIDATED = "validated"
    ROUTING = "routing"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ExecutionAlgo(Enum):
    IMMEDIATE = "immediate"
    VWAP = "vwap"
    TWAP = "twap"
    ICEBERG = "iceberg"
    PASSIVE = "passive"
    SNIPER = "sniper"
    MOMENTUM = "momentum"
    STEALTH = "stealth"


class Exchange(Enum):
    BINANCE = "binance"
    BINANCE_FUTURES = "binance_futures"
    BYBIT = "bybit"
    OKX = "okx"
    TESTNET = "testnet"


@dataclass(frozen=True, slots=True)
class OrderConstraints:
    """Ω-H55-H63: Pre-trade risk constraints."""
    max_position_size: float = 5.0
    max_exposure_pct: float = 50.0
    max_correlation: float = 0.8
    max_drawdown_pct: float = 2.0
    max_orders_per_second: int = 10
    max_price_deviation_pct: float = 5.0  # Fat finger check


@dataclass(frozen=True, slots=True)
class FillRecord:
    """Ω-H37: Immutable fill record."""
    fill_id: str
    order_id: str
    exchange: str
    symbol: str
    side: OrderSide
    price: float
    quantity: float
    commission: float
    commission_asset: str = "USDT"
    is_maker: bool = False
    timestamp_ns: int = field(default_factory=lambda: time.time_ns())

    @property
    def notional(self) -> float:
        return self.price * self.quantity

    @property
    def net_commission(self) -> float:
        return self.commission if not self.is_maker else -self.commission  # rebate


@dataclass(frozen=True, slots=True)
class Order:
    """
    Ω-H01 to Ω-H18: Immutable order with state,
    checksum, partial fill tracking, and idempotency.
    """
    order_id: str
    client_order_id: str  # Our internal ID for tracing
    exchange: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    price: float  # 0 for market orders
    quantity: float
    stop_price: float = 0.0  # For stop orders
    time_in_force: str = "GTC"
    status: OrderStatus = OrderStatus.CREATED
    filled_quantity: float = 0.0
    avg_fill_price: float = 0.0
    remaining_quantity: float = 0.0
    fills: tuple[FillRecord, ...] = ()
    commission_total: float = 0.0
    created_at_ns: int = field(default_factory=lambda: time.time_ns())
    submitted_at_ns: int = 0
    filled_at_ns: int = 0
    cancelled_at_ns: int = 0
    rejected_reason: str = ""
    checksum: str = ""
    trace_id: str = ""  # Link to TrinityCore decision trace

    @classmethod
    def create(
        cls,
        client_order_id: str,
        exchange: str,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: float = 0.0,
        stop_price: float = 0.0,
        time_in_force: str = "GTC",
        trace_id: str = "",
    ) -> Order:
        """Ω-H01, Ω-H08: Factory with checksum and client order ID."""
        oid = f"ord-{uuid.uuid4().hex[:12]}"
        cs = compute_checksum({
            "oid": oid, "cid": client_order_id, "ex": exchange,
            "sym": symbol, "s": side.value, "t": order_type.value,
            "p": price, "q": quantity,
        })
        return cls(
            order_id=oid, client_order_id=client_order_id,
            exchange=exchange, symbol=symbol, side=side,
            order_type=order_type, price=price, quantity=quantity,
            stop_price=stop_price, time_in_force=time_in_force,
            checksum=cs, trace_id=trace_id,
        )

    def with_fill(self, fill: FillRecord) -> Order:
        """Ω-H14: Update order with new partial fill."""
        new_fills = self.fills + (fill,)
        total_qty = sum(f.quantity for f in new_fills)
        total_val = sum(f.price * f.quantity for f in new_fills)
        avg_price = total_val / total_qty if total_qty > 0 else 0.0
        remaining = max(0.0, self.quantity - total_qty)
        status = OrderStatus.FILLED if remaining <= 0 else OrderStatus.PARTIALLY_FILLED
        return Order(
            order_id=self.order_id, client_order_id=self.client_order_id,
            exchange=self.exchange, symbol=self.symbol, side=self.side,
            order_type=self.order_type, price=self.price,
            quantity=self.quantity, stop_price=self.stop_price,
            time_in_force=self.time_in_force, status=status,
            filled_quantity=total_qty, avg_fill_price=avg_price,
            remaining_quantity=remaining, fills=new_fills,
            commission_total=sum(f.commission for f in new_fills),
            created_at_ns=self.created_at_ns, submitted_at_ns=self.submitted_at_ns,
            filled_at_ns=time.time_ns() if status == OrderStatus.FILLED else self.filled_at_ns,
            checksum=self.checksum, trace_id=self.trace_id,
        )

    @property
    def fill_pct(self) -> float:
        return self.filled_quantity / self.quantity if self.quantity > 0 else 0.0

    @property
    def is_terminal(self) -> bool:
        return self.status in (
            OrderStatus.FILLED, OrderStatus.CANCELLED,
            OrderStatus.REJECTED, OrderStatus.EXPIRED,
        )

    @property
    def age_ns(self) -> int:
        return time.time_ns() - self.created_at_ns

    @property
    def age_ms(self) -> float:
        return self.age_ns / 1e6


def compute_checksum(data: dict[str, Any]) -> str:
    import json, zlib
    serialized = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
    crc = zlib.crc32(serialized) & 0xFFFFFFFF
    return f"{crc:08x}"
