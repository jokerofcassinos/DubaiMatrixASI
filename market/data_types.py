"""
SOLÉNN v2 — Frozen Data Types (Ω-D109 a Ω-D117)
Immutable dataclasses for Trade, OrderBook, Candle, Tick with
CRC32 checksums, deep freeze, and integrity verification.
"""

from __future__ import annotations

import zlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Side(Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass(frozen=True, slots=True)
class Tick:
    """Ω-D112: Immutable single tick of market data."""
    exchange: str
    symbol: str
    price: float
    quantity: float
    side: Side
    timestamp_ns: int
    checksum: str = ""

    def __post_init__(self) -> None:
        if self.price <= 0:
            raise ValueError(f"Tick price must be > 0, got {self.price}")
        if self.quantity < 0:
            raise ValueError(f"Tick quantity must be >= 0, got {self.quantity}")

    @classmethod
    def create(cls, exchange: str, symbol: str, price: float, quantity: float,
               side: Side, timestamp_ns: int) -> Tick:
        cs = compute_tick_checksum(exchange, symbol, price, quantity, side, timestamp_ns)
        return cls(exchange=exchange, symbol=symbol, price=price, quantity=quantity,
                   side=side, timestamp_ns=timestamp_ns, checksum=cs)

    def verify(self) -> bool:
        return self.checksum == compute_tick_checksum(
            self.exchange, self.symbol, self.price, self.quantity, self.side, self.timestamp_ns)


@dataclass(frozen=True, slots=True)
class Trade:
    """Ω-D109: Immutable trade record."""
    trade_id: str
    exchange: str
    symbol: str
    price: float
    quantity: float
    side: Side
    timestamp_ns: int
    is_taker_buy: bool = True
    checksum: str = ""

    @classmethod
    def create(cls, trade_id: str, exchange: str, symbol: str, price: float,
               quantity: float, side: Side, timestamp_ns: int, is_taker_buy: bool = True) -> Trade:
        cs = compute_checksum({"tid": trade_id, "ex": exchange, "sym": symbol,
                               "p": price, "q": quantity, "s": side.value, "ts": timestamp_ns})
        return cls(trade_id=trade_id, exchange=exchange, symbol=symbol, price=price,
                   quantity=quantity, side=side, timestamp_ns=timestamp_ns,
                   is_taker_buy=is_taker_buy, checksum=cs)

    def verify(self) -> bool:
        """Ω-D114: Integrity verification via checksum."""
        return self.checksum == compute_checksum({
            "tid": self.trade_id, "ex": self.exchange, "sym": self.symbol,
            "p": self.price, "q": self.quantity, "s": self.side.value, "ts": self.timestamp_ns})


@dataclass(frozen=True, slots=True)
class BookLevel:
    """Single level of an order book (immutable)."""
    price: float
    quantity: float
    order_count: int = 1


@dataclass(frozen=True, slots=True)
class OrderBook:
    """Ω-D110: Immutable order book snapshot."""
    exchange: str
    symbol: str
    timestamp_ns: int
    bids: tuple[BookLevel, ...] = ()
    asks: tuple[BookLevel, ...] = ()
    sequence: int = 0
    checksum: str = ""

    def __post_init__(self) -> None:
        if self.bids:
            max_bid = max(b.price for b in self.bids)
            if self.asks:
                min_ask = min(a.price for a in self.asks)
                if max_bid >= min_ask:
                    raise ValueError(f"Book has cross: best bid {max_bid} >= best ask {min_ask}")

    @classmethod
    def create(cls, exchange: str, symbol: str, timestamp_ns: int,
               bids: list[BookLevel], asks: list[BookLevel], sequence: int = 0) -> OrderBook:
        bid_tuple = tuple(b for b in sorted(bids, key=lambda x: -x.price))
        ask_tuple = tuple(a for a in sorted(asks, key=lambda x: x.price))
        cs = compute_checksum({"ex": exchange, "sym": symbol, "ts": timestamp_ns,
                               "b": [(b.price, b.quantity) for b in bid_tuple],
                               "a": [(a.price, a.quantity) for a in ask_tuple]})
        return cls(exchange=exchange, symbol=symbol, timestamp_ns=timestamp_ns,
                   bids=bid_tuple, asks=ask_tuple, sequence=sequence, checksum=cs)

    @property
    def best_bid(self) -> float | None:
        return self.bids[0].price if self.bids else None

    @property
    def best_ask(self) -> float | None:
        return self.asks[0].price if self.asks else None

    @property
    def mid_price(self) -> float | None:
        if self.best_bid and self.best_ask:
            return (self.best_bid + self.best_ask) / 2.0
        return None

    @property
    def spread(self) -> float | None:
        if self.best_bid and self.best_ask:
            return self.best_ask - self.best_bid
        return None

    @property
    def spread_bps(self) -> float | None:
        if self.mid_price and self.spread:
            return (self.spread / self.mid_price) * 10000.0
        return None

    def verify(self) -> bool:
        return self.checksum == compute_checksum({
            "ex": self.exchange, "sym": self.symbol, "ts": self.timestamp_ns,
            "b": [(b.price, b.quantity) for b in self.bids],
            "a": [(a.price, a.quantity) for a in self.asks]})


@dataclass(frozen=True, slots=True)
class Candle:
    """Ω-D111: Immutable OHLCV candle."""
    symbol: str
    exchange: str
    timeframe: str
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    quote_volume: float = 0.0
    trade_count: int = 0
    timestamp_ns: int = 0
    is_closed: bool = True
    checksum: str = ""

    @classmethod
    def create(cls, symbol: str, exchange: str, timeframe: str,
               open_price: float, high_price: float, low_price: float,
               close_price: float, volume: float, quote_volume: float = 0.0,
               trade_count: int = 0, timestamp_ns: int = 0,
               is_closed: bool = True) -> Candle:
        cs = compute_checksum({"s": symbol, "ex": exchange, "tf": timeframe,
                               "o": open_price, "h": high_price, "l": low_price,
                               "c": close_price, "v": volume})
        return cls(symbol=symbol, exchange=exchange, timeframe=timeframe,
                   open_price=open_price, high_price=high_price, low_price=low_price,
                   close_price=close_price, volume=volume, quote_volume=quote_volume,
                   trade_count=trade_count, timestamp_ns=timestamp_ns,
                   is_closed=is_closed, checksum=cs)

    def verify(self) -> bool:
        return self.checksum == compute_checksum({
            "s": self.symbol, "ex": self.exchange, "tf": self.timeframe,
            "o": self.open_price, "h": self.high_price, "l": self.low_price,
            "c": self.close_price, "v": self.volume})

    def body(self) -> float:
        return self.close_price - self.open_price

    def range(self) -> float:
        return self.high_price - self.low_price

    def is_bullish(self) -> bool:
        return self.close_price > self.open_price


@dataclass(frozen=True, slots=True)
class LiveCandle:
    """Mutable-in-progress candle that becomes Candle when closed."""
    symbol: str
    exchange: str
    timeframe: str
    timestamp_ns: int
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    quote_volume: float
    trade_count: int

    @classmethod
    def open(cls, symbol: str, exchange: str, timeframe: str,
             timestamp_ns: int, first_price: float, first_vol: float = 0.0) -> LiveCandle:
        return cls(symbol=symbol, exchange=exchange, timeframe=timeframe,
                   timestamp_ns=timestamp_ns, open_price=first_price,
                   high_price=first_price, low_price=first_price,
                   close_price=first_price, volume=0.0, quote_volume=0.0, trade_count=0)

    def update(self, price: float, quantity: float, quote_qty: float = 0.0) -> LiveCandle:
        """Return new LiveCandle with updated values (immutable update)."""
        return LiveCandle(
            symbol=self.symbol, exchange=self.exchange, timeframe=self.timeframe,
            timestamp_ns=self.timestamp_ns, open_price=self.open_price,
            high_price=max(self.high_price, price), low_price=min(self.low_price, price),
            close_price=price, volume=self.volume + quantity,
            quote_volume=self.quote_volume + quote_qty,
            trade_count=self.trade_count + 1,
        )

    def to_candle(self, is_closed: bool = True) -> Candle:
        """Ω-D39: Convert to immutable Candle on closure."""
        return Candle.create(
            symbol=self.symbol, exchange=self.exchange, timeframe=self.timeframe,
            open_price=self.open_price, high_price=self.high_price,
            low_price=self.low_price, close_price=self.close_price,
            volume=self.volume, quote_volume=self.quote_volume,
            trade_count=self.trade_count, timestamp_ns=self.timestamp_ns,
            is_closed=is_closed,
        )


def compute_checksum(data: dict[str, Any]) -> str:
    """Ω-D113: CRC32 checksum for data integrity."""
    import json
    serialized = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
    crc = zlib.crc32(serialized) & 0xFFFFFFFF
    return f"{crc:08x}"


def compute_tick_checksum(exchange: str, symbol: str, price: float,
                          quantity: float, side: Side, timestamp_ns: int) -> str:
    return compute_checksum({"ex": exchange, "sym": symbol, "p": price,
                             "q": quantity, "s": side.value, "ts": timestamp_ns})
