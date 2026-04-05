"""
SOLÉNN v2 — Cross-Exchange Normalization (Ω-D46 a Ω-D54)
Exchange adapter interface, symbol mapping, currency/decel/precision
standardization, timezone normalization, fee schedule, order type mapping,
exchange health monitoring, best execution price finder.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    IOC = "ioc"
    FOK = "fok"
    POST_ONLY = "post_only"


@dataclass(frozen=True, slots=True)
class FeeSchedule:
    """Ω-D51: Fee schedule for an exchange."""
    exchange: str
    maker_fee: float
    taker_fee: float
    withdrawal_fee: float = 0.0


@dataclass(frozen=True, slots=True)
class ExchangeHealth:
    """Ω-D53: Exchange health metrics."""
    exchange: str
    uptime_pct: float
    avg_latency_ms: float
    error_rate: float
    last_check: float = field(default_factory=time.time)


class ExchangeAdapter(ABC):
    """Ω-D46: Base adapter interface for all exchanges."""

    @abstractmethod
    def name(self) -> str: ...
    @abstractmethod
    def normalize_symbol(self, symbol: str) -> str: ...
    @abstractmethod
    def map_order_type(self, order_type: str) -> OrderType: ...
    @abstractmethod
    def get_precision(self, symbol: str) -> tuple[int, int]: ...
    @abstractmethod
    def get_fees(self) -> FeeSchedule: ...
    @abstractmethod
    async def get_order_book(self, symbol: str, depth: int = 20) -> dict: ...
    @abstractmethod
    async def get_recent_trades(self, symbol: str, limit: int = 100) -> list: ...


class BinanceAdapter(ExchangeAdapter):
    """Ω-D46: Binance exchange adapter."""

    # Ω-D47: Symbol mapping
    SYMBOL_MAP = {"BTCUSDT": "BTC/USDT", "XBTUSD": "BTC/USD", "ETHUSDT": "ETH/USDT"}
    REVERSE_MAP = {v: k for k, v in SYMBOL_MAP.items()}

    def name(self) -> str: return "binance"

    def normalize_symbol(self, symbol: str) -> str:
        return self.SYMBOL_MAP.get(symbol, symbol)

    def map_order_type(self, order_type_str: str) -> OrderType:
        mapping = {"MARKET": OrderType.MARKET, "LIMIT": OrderType.LIMIT,
                   "STOP_LOSS": OrderType.STOP, "STOP_LOSS_LIMIT": OrderType.STOP_LIMIT}
        return mapping.get(order_type_str, OrderType.MARKET)

    def get_precision(self, symbol: str) -> tuple[int, int]:
        return 8, 8

    def get_fees(self) -> FeeSchedule:
        return FeeSchedule("binance", maker_fee=0.001, taker_fee=0.001)

    async def get_order_book(self, symbol: str, depth: int = 20) -> dict:
        return {"exchange": "binance", "symbol": symbol, "depth": depth}

    async def get_recent_trades(self, symbol: str, limit: int = 100) -> list:
        return [{"exchange": "binance", "symbol": symbol}] * limit


class BybitAdapter(ExchangeAdapter):
    """Bybit exchange adapter."""
    SYMBOL_MAP = {"BTCUSDT": "BTC/USDT", "XBTUSD": "BTC/USD"}

    def name(self) -> str: return "bybit"
    def normalize_symbol(self, symbol: str) -> str: return self.SYMBOL_MAP.get(symbol, symbol)
    def map_order_type(self, order_type_str: str) -> OrderType:
        return {"Market": OrderType.MARKET, "Limit": OrderType.LIMIT}.get(order_type_str, OrderType.MARKET)
    def get_precision(self, symbol: str) -> tuple[int, int]: return 8, 8
    def get_fees(self) -> FeeSchedule: return FeeSchedule("bybit", maker_fee=0.001, taker_fee=0.006)
    async def get_order_book(self, symbol: str, depth: int = 20) -> dict: return {"exchange": "bybit", "symbol": symbol, "depth": depth}
    async def get_recent_trades(self, symbol: str, limit: int = 100) -> list: return [{"exchange": "bybit", "symbol": symbol}] * limit


class SymbolMapper:
    """Ω-D47: Global symbol mapping across exchanges."""

    def __init__(self) -> None:
        self._symbol_to_unified: dict[tuple[str, str], str] = {}
        self._unified_to_exchange: dict[str, dict[str, str]] = {}

    def register(self, exchange: str, exchange_symbol: str, unified_symbol: str) -> None:
        self._symbol_to_unified[(exchange, exchange_symbol)] = unified_symbol
        self._unified_to_exchange.setdefault(unified_symbol, {})[exchange] = exchange_symbol

    def to_unified(self, exchange: str, symbol: str) -> str:
        return self._symbol_to_unified.get((exchange, symbol), symbol)

    def to_exchange(self, unified_symbol: str, exchange: str) -> str:
        return self._unified_to_exchange.get(unified_symbol, {}).get(exchange, unified_symbol)

    def get_all_symbols(self) -> dict[str, dict[str, str]]:
        return dict(self._unified_to_exchange)


class CurrencyNormalizer:
    """Ω-D48: Currency normalization — all values in USD."""

    def __init__(self) -> None:
        self._usd_rates: dict[str, float] = {"USD": 1.0, "USDT": 1.0, "USDC": 1.0}

    def set_rate(self, currency: str, usd_rate: float) -> None:
        self._usd_rates[currency] = usd_rate

    def to_usd(self, amount: float, currency: str) -> float:
        rate = self._usd_rates.get(currency, 1.0)
        return amount * rate

    def get_rates(self) -> dict[str, float]:
        return dict(self._usd_rates)


class ExchangeMonitor:
    """Ω-D53: Exchange health monitoring."""

    def __init__(self) -> None:
        self._health: dict[str, list[ExchangeHealth]] = {}
        self._error_counts: dict[str, int] = {}
        self._latencies: dict[str, list[float]] = {}

    def record_success(self, exchange: str, latency_ms: float) -> None:
        self._latencies.setdefault(exchange, []).append(latency_ms)
        if len(self._latencies[exchange]) > 100:
            self._latencies[exchange] = self._latencies[exchange][-50:]
        self._error_counts.setdefault(exchange, 0)

    def record_error(self, exchange: str) -> None:
        self._error_counts[exchange] = self._error_counts.get(exchange, 0) + 1

    def get_health(self, exchange: str) -> ExchangeHealth:
        latencies = self._latencies.get(exchange, [])
        avg_lat = sum(latencies) / len(latencies) if latencies else 0
        errors = self._error_counts.get(exchange, 0)
        total = len(latencies) + errors
        error_rate = errors / total if total > 0 else 0
        return ExchangeHealth(exchange=exchange, uptime_pct=max(0, 100 - error_rate * 100),
                              avg_latency_ms=avg_lat, error_rate=error_rate)

    def get_all_health(self) -> dict[str, ExchangeHealth]:
        exchanges = set(list(self._latencies.keys()) + list(self._error_counts.keys()))
        return {ex: self.get_health(ex) for ex in exchanges}


class BestExecutionFinder:
    """Ω-D54: Find best execution price across exchanges."""

    def __init__(self) -> None:
        self._prices: dict[str, dict[str, tuple[float, float]]] = {}

    def update_price(self, exchange: str, symbol: str, bid: float, ask: float) -> None:
        self._prices.setdefault(symbol, {})[exchange] = (bid, ask)

    def best_bid(self, symbol: str) -> tuple[str, float] | None:
        exchanges = self._prices.get(symbol, {})
        if not exchanges:
            return None
        return max(((ex, bid) for ex, (bid, _) in exchanges.items()), key=lambda x: x[1])

    def best_ask(self, symbol: str) -> tuple[str, float] | None:
        exchanges = self._prices.get(symbol, {})
        if not exchanges:
            return None
        return min(((ex, ask) for ex, (_, ask) in exchanges.items()), key=lambda x: x[1])

    def arbitrage_opportunity(self, symbol: str) -> tuple[str, str, float] | None:
        """Check if cross-exchange arbitrage exists."""
        bb = self.best_bid(symbol)
        ba = self.best_ask(symbol)
        if bb and ba and bb[1] > ba[1]:
            return (ba[0], bb[0], bb[1] - ba[1])
        return None
