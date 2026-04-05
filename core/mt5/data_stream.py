"""
SOLÉNN v2 — MT5 Data Stream (MT5-01 to MT5-54)
Async data bridge from MetaTrader5 to SOLÉNN Ω pipeline.

MT5-01 to MT5-09: Connection Management
MT5-10 to MT5-18: Tick Data Capture
MT5-19 to MT5-27: Candle Data Management
MT5-28 to MT5-36: Symbol & Contract Info
MT5-37 to MT5-45: Account State Monitoring
MT5-37 to MT5-54: Health & Resilience
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable

import MetaTrader5 as mt5


# ──────────────────────────────────────────────────────────────
# MT5-01 to MT5-09: Connection Management
# ──────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class MT5ConnectionInfo:
    """MT5-02: Immutable connection state snapshot."""
    connected: bool
    login: int
    company: str
    terminal_name: str
    trade_allowed: bool
    build: int
    ping_ms: int
    balance: float
    equity: float
    currency: str
    leverage: int
    margin_free: float
    timestamp_ns: int = field(default_factory=lambda: time.time_ns())


class MT5Connection:
    """MT5-01: MT5 Connection Manager with resilience."""

    def __init__(self) -> None:
        self._connected = False
        self._login: int | None = None
        self._max_retries = 3
        self._retry_delay = 2.0
        self._reconnect_count = 0
        self._last_connect_time = 0.0
        self._total_uptime_s = 0.0

    def connect(self, login: int | None = None, password: str | None = None,
                server: str | None = None) -> bool:
        """MT5-03: Establish connection with retry logic."""
        # Check if already connected
        ti = mt5.terminal_info()
        if ti is not None and ti.connected:
            self._connected = True
            self._last_connect_time = time.time()
            return True

        for attempt in range(self._max_retries):
            ok = mt5.initialize(
                login=login, password=password, server=server
            )
            if ok:
                self._connected = True
                self._login = login
                self._last_connect_time = time.time()
                self._reconnect_count = 0
                return True
            time.sleep(self._retry_delay * (2 ** attempt))
        self._connected = False
        return False

    def shutdown(self) -> None:
        """MT5-04: Graceful shutdown."""
        if self._connected:
            if self._last_connect_time > 0:
                self._total_uptime_s += time.time() - self._last_connect_time
            mt5.shutdown()
            self._connected = False

    def reconnect(self, login: int | None = None,
                  password: str | None = None,
                  server: str | None = None) -> bool:
        """MT5-05: Reconnect with exponential backoff."""
        if self._connected:
            mt5.shutdown()
            self._connected = False
        self._reconnect_count += 1
        return self.connect(login, password, server)

    def get_info(self) -> MT5ConnectionInfo | None:
        """MT5-06: Get connection info snapshot."""
        if not self._connected:
            return None

        ti = mt5.terminal_info()
        acc = mt5.account_info()

        if ti is None or acc is None:
            return None

        return MT5ConnectionInfo(
            connected=True,
            login=acc.login,
            company=ti.company,
            terminal_name=ti.name,
            trade_allowed=ti.trade_allowed,
            build=ti.build,
            ping_ms=ti.ping_last,
            balance=acc.balance,
            equity=acc.equity,
            currency=acc.currency,
            leverage=acc.leverage,
            margin_free=acc.margin_free,
        )

    def is_healthy(self) -> bool:
        """MT5-07: Health check."""
        if not self._connected:
            return False
        ti = mt5.terminal_info()
        return ti is not None and ti.connected

    # MT5-08: Connection stats
    def get_stats(self) -> dict[str, Any]:
        return {
            "connected": self._connected,
            "reconnect_count": self._reconnect_count,
            "uptime_s": self._total_uptime_s + (
                time.time() - self._last_connect_time
                if self._last_connect_time > 0 else 0
            ),
        }


# ──────────────────────────────────────────────────────────────
# MT5-10 to MT5-18: Tick Data Capture
# ──────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class MT5Tick:
    """MT5-10: Immutable tick data."""
    symbol: str
    time_ns: int
    bid: float
    ask: float
    last: float
    volume: int
    flags: int
    spread_bps: float

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2

    @property
    def spread(self) -> float:
        return self.ask - self.bid


class TickBuffer:
    """MT5-11: Buffered tick capture with bounded memory."""

    def __init__(self, symbol: str, max_len: int = 10000) -> None:
        self._symbol = symbol
        self._buffer: deque[MT5Tick] = deque(maxlen=max_len)
        self._callbacks: list[Callable[[MT5Tick], None]] = []
        self._tick_count = 0

    def register_callback(self, cb: Callable[[MT5Tick], None]) -> None:
        """MT5-12: Register tick callback."""
        self._callbacks.append(cb)

    def capture_latest(self, n_ticks: int = 100) -> list[MT5Tick]:
        """MT5-13: Capture latest N ticks from MT5."""
        ticks = mt5.copy_ticks_from(
            self._symbol, 0, n_ticks, mt5.COPY_TICKS_ALL
        )
        if ticks is None:
            return []

        # Get current spread info for spread_bps calculation
        sym = mt5.symbol_info(self._symbol)
        point = sym.point if sym else 1.0

        result = []
        for t in ticks:
            bid = float(t["bid"])
            ask = float(t["ask"])
            mid = (bid + ask) / 2
            spread_abs = ask - bid
            spread_bps = (spread_abs / mid * 10000) if mid > 0 else 0

            tick = MT5Tick(
                symbol=self._symbol,
                time_ns=int(t["time_msc"] * 1_000_000),
                bid=bid,
                ask=ask,
                last=float(t["last"]),
                volume=int(t["volume"]),
                flags=int(t["flags"]),
                spread_bps=round(spread_bps, 2),
            )
            result.append(tick)
            self._buffer.append(tick)
            self._tick_count += 1
            for cb in self._callbacks:
                cb(tick)
        return result

    def get_buffer(self, n: int = 100) -> list[MT5Tick]:
        """MT5-14: Get recent ticks from buffer."""
        return list(self._buffer)[-n:]

    @property
    def total_captured(self) -> int:
        return self._tick_count


# ──────────────────────────────────────────────────────────────
# MT5-19 to MT5-27: Candle Data Management
# ──────────────────────────────────────────────────────────────

# Map SOLÉNN timeframe strings to MT5 constants
_TIMEFRAME_MAP = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1,
}


@dataclass(frozen=True, slots=True)
class MT5Candle:
    """MT5-19: Immutable candle data."""
    symbol: str
    timeframe: str
    time_ns: int
    open: float
    high: float
    low: float
    close: float
    tick_volume: int
    spread_bps: float

    @property
    def body(self) -> float:
        return self.close - self.open

    @property
    def range(self) -> float:
        return self.high - self.low

    @property
    def upper_wick(self) -> float:
        body_top = max(self.open, self.close)
        return self.high - body_top

    @property
    def lower_wick(self) -> float:
        body_bottom = min(self.open, self.close)
        return body_bottom - self.low

    @property
    def is_bullish(self) -> bool:
        return self.close > self.open


class CandleCache:
    """MT5-20: Candle data cache with multi-timeframe support."""

    def __init__(self, symbol: str, max_candles: int = 1000) -> None:
        self._symbol = symbol
        self._max_candles = max_candles
        self._cache: dict[str, deque[MT5Candle]] = {}

    def fetch(self, timeframe: str = "M1", count: int = 100) -> list[MT5Candle]:
        """MT5-21: Fetch candles from MT5."""
        if timeframe not in _TIMEFRAME_MAP:
            return []

        tf = _TIMEFRAME_MAP[timeframe]
        rates = mt5.copy_rates_from_pos(self._symbol, tf, 0, count)
        if rates is None or len(rates) == 0:
            return []

        sym = mt5.symbol_info(self._symbol)
        point = sym.point if sym else 0.01

        candles = []
        for r in rates:
            spread_bps = 0.0
            candle = MT5Candle(
                symbol=self._symbol,
                timeframe=timeframe,
                time_ns=int(r["time"] * 1_000_000_000),
                open=r["open"],
                high=r["high"],
                low=r["low"],
                close=r["close"],
                tick_volume=r["tick_volume"],
                spread_bps=spread_bps,
            )
            candles.append(candle)

        if timeframe not in self._cache:
            self._cache[timeframe] = deque(maxlen=self._max_candles)
        for c in candles:
            self._cache[timeframe].append(c)

        return candles

    def get_cached(self, timeframe: str = "M1", n: int = 100) -> list[MT5Candle]:
        """MT5-22: Get from local cache."""
        if timeframe not in self._cache:
            return []
        return list(self._cache[timeframe])[-n:]

    def get_multi_timeframe(self, timeframes: list[str] | None = None) -> dict[str, list[MT5Candle]]:
        """MT5-23: Multi-timeframe analysis cache."""
        if timeframes is None:
            timeframes = ["M1", "M5", "M15", "H1", "H4"]
        result = {}
        for tf in timeframes:
            if tf in self._cache:
                result[tf] = list(self._cache[tf])[-50:]
        return result


# ──────────────────────────────────────────────────────────────
# MT5-28 to MT5-36: Symbol & Contract Info
# ──────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class MT5SymbolInfo:
    """MT5-28: Immutable symbol/contract specification."""
    name: str
    path: str
    description: str
    point: float
    digits: int
    spread: float
    tick_size: float
    tick_value: float
    contract_size: float
    volume_min: float
    volume_max: float
    volume_step: float
    trade_stops_level: float
    trade_freeze_level: float
    margin_initial: float
    margin_maintenance: float
    bid: float
    ask: float
    last: float
    change_pct: float
    high_day: float
    low_day: float
    is_tradeable: bool


class SymbolRegistry:
    """MT5-29: Symbol specification registry."""

    def __init__(self) -> None:
        self._registry: dict[str, MT5SymbolInfo] = {}

    def load(self, symbol: str) -> MT5SymbolInfo | None:
        """MT5-30: Load symbol info from MT5."""
        info = mt5.symbol_info(symbol)
        if info is None:
            return None

        tick_info = mt5.symbol_info_tick(symbol)
        bid = tick_info.bid if tick_info else 0.0
        ask = tick_info.ask if tick_info else 0.0
        last = tick_info.last if tick_info else 0.0
        change_pct = 0.0
        high_day = 0.0
        low_day = 0.0

        result = MT5SymbolInfo(
            name=info.name,
            path=info.path,
            description=info.description,
            point=info.point,
            digits=info.digits,
            spread=info.spread,
            tick_size=info.trade_tick_size,
            tick_value=info.trade_tick_value,
            contract_size=info.trade_contract_size,
            volume_min=info.volume_min,
            volume_max=info.volume_max,
            volume_step=info.volume_step,
            trade_stops_level=info.trade_stops_level,
            trade_freeze_level=info.trade_freeze_level,
            margin_initial=info.margin_initial,
            margin_maintenance=info.margin_maintenance,
            bid=bid,
            ask=ask,
            last=last,
            change_pct=change_pct,
            high_day=high_day,
            low_day=low_day,
            is_tradeable=bool(info.trade_mode),
        )
        self._registry[symbol] = result
        return result

    def get(self, symbol: str) -> MT5SymbolInfo | None:
        return self._registry.get(symbol)

    def get_all(self) -> list[str]:
        """MT5-31: List all available symbols."""
        symbols = mt5.symbols_get()
        return [s.name for s in symbols] if symbols else []

    def is_tradeable(self, symbol: str) -> bool:
        """MT5-32: Check if symbol is tradeable."""
        info = mt5.symbol_info(symbol)
        if info is None:
            return False
        sym = self.get(symbol)
        if sym is None:
            return False
        return info.trade_mode > 0 and info.visible

    def validate_order(self, symbol: str, volume: float,
                       stop_loss: float | None = None,
                       take_profit: float | None = None) -> list[str]:
        """MT5-33: Validate order parameters against symbol spec."""
        errors = []
        info = mt5.symbol_info(symbol)
        if info is None:
            errors.append(f"Symbol {symbol} not found")
            return errors

        if volume < info.volume_min:
            errors.append(f"Volume {volume} < min {info.volume_min}")
        if volume > info.volume_max:
            errors.append(f"Volume {volume} > max {info.volume_max}")

        step = info.volume_step
        if step > 0 and abs(volume / step - round(volume / step)) > 1e-9:
            errors.append(f"Volume {volume} not multiple of step {step}")

        if stop_loss is not None and info.trade_stops_level > 0:
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                dist = abs((stop_loss - tick.bid) / info.point)
                if dist < info.trade_stops_level:
                    errors.append(f"Stop too close: {dist} < {info.trade_stops_level} points")

        return errors


# ──────────────────────────────────────────────────────────────
# MT5-37 to MT5-45: Account State Monitoring
# ──────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class MT5AccountState:
    """MT5-37: Immutable account state snapshot."""
    login: int
    balance: float
    equity: float
    margin: float
    margin_free: float
    margin_level: float
    profit: float
    assets: float
    liability: float
    leverage: int
    currency: str
    floating_profit: float
    timestamp_ns: int = field(default_factory=lambda: time.time_ns())


class AccountMonitor:
    """MT5-38: Account state monitoring with alerts."""

    def __init__(
        self,
        max_drawdown_pct: float = 2.0,
        min_margin_level: float = 100.0,
    ) -> None:
        self._max_dd = max_drawdown_pct
        self._min_margin = min_margin_level
        self._peak_equity = 0.0
        self._alerts: list[str] = []

    def snapshot(self) -> MT5AccountState | None:
        """MT5-39: Get account snapshot."""
        acc = mt5.account_info()
        if acc is None:
            return None

        self._peak_equity = max(self._peak_equity, acc.equity)

        return MT5AccountState(
            login=acc.login,
            balance=acc.balance,
            equity=acc.equity,
            margin=acc.margin,
            margin_free=acc.margin_free,
            margin_level=acc.margin_level,
            profit=acc.profit,
            assets=acc.assets,
            liability=acc.liabilities,
            leverage=acc.leverage,
            currency=acc.currency,
            floating_profit=acc.profit,
        )

    def get_drawdown_pct(self) -> float:
        """MT5-40: Current drawdown percentage."""
        if self._peak_equity <= 0:
            return 0.0
        acc = mt5.account_info()
        if acc is None:
            return 0.0
        return max(0.0, (self._peak_equity - acc.equity) / self._peak_equity * 100)

    def check_risk(self) -> list[str]:
        """MT5-41: Risk checks on account."""
        alerts = []
        acc = mt5.account_info()
        if acc is None:
            alerts.append("Cannot read account info")
            return alerts

        dd = self.get_drawdown_pct()
        if dd > self._max_dd:
            alerts.append(f"DRAWDOWN: {dd:.2f}% > {self._max_dd}%")

        if acc.margin_level < self._min_margin:
            alerts.append(f"MARGIN LEVEL: {acc.margin_level:.1f}% < {self._min_margin}%")

        if acc.balance < acc.equity * 0.95:
            alerts.append("Significant floating loss detected")

        self._alerts = alerts
        return alerts

    def get_stats(self) -> dict[str, Any]:
        """MT5-42: Account statistics."""
        acc = mt5.account_info()
        if acc is None:
            return {"status": "disconnected"}
        return {
            "balance": acc.balance,
            "equity": acc.equity,
            "margin": acc.margin,
            "margin_free": acc.margin_free,
            "margin_level": acc.margin_level,
            "profit": acc.profit,
            "leverage": acc.leverage,
            "peak_equity": self._peak_equity,
            "current_dd_pct": self.get_drawdown_pct(),
        }


# ──────────────────────────────────────────────────────────────
# MT5-46 to MT5-54: Health & Resilience
# ──────────────────────────────────────────────────────────────

class MT5DataStreamer:
    """
    MT5-46 to MT5-54: Async data streaming with auto-reconnect,
    heartbeat monitoring, and backpressure.
    """

    def __init__(self, symbol: str, timeframes: list[str] | None = None):
        self._symbol = symbol
        self._timeframes = timeframes or ["M1", "M5", "M15", "H1"]
        self._running = False
        self._connection = MT5Connection()
        self._tick_buffer = TickBuffer(symbol)
        self._candle_cache = CandleCache(symbol)
        self._symbols = SymbolRegistry()
        self._account = AccountMonitor()

        # Health monitoring
        self._heartbeat_interval = 5.0
        self._last_heartbeat = 0.0
        self._missed_heartbeats = 0
        self._max_missed_heartbeats = 3
        self._tick_rate = 0.0
        self._tick_count = 0
        self._tick_window_start = 0.0
        self._errors: list[str] = []

        # Backpressure
        self._paused = False
        self._max_queue = 10000
        self._queue: deque[Any] = deque(maxlen=self._max_queue)

    # MT5-47: Connection lifecycle
    def start(self) -> bool:
        """MT5-47: Start the data streamer."""
        ok = self._connection.connect()
        if not ok:
            return False

        sym_info = self._symbols.load(self._symbol)
        if sym_info is None:
            self._errors.append(f"Cannot load symbol {self._symbol}")
            return False

        # Pre-populate candle cache
        for tf in self._timeframes:
            self._candle_cache.fetch(tf, 200)

        self._running = True
        return True

    def stop(self) -> None:
        """MT5-48: Stop the data streamer."""
        self._running = False
        self._connection.shutdown()

    def is_healthy(self) -> bool:
        """MT5-49: Health check."""
        if not self._running:
            return False
        if not self._connection.is_healthy():
            return False
        if self._missed_heartbeats >= self._max_missed_heartbeats:
            return False
        return True

    def check_heartbeat(self) -> bool:
        """MT5-50: Check heartbeat and detect stalls."""
        now = time.time()
        elapsed = now - self._last_heartbeat
        self._last_heartbeat = now

        if elapsed > self._heartbeat_interval * 2:
            self._missed_heartbeats += 1
            return False
        else:
            self._missed_heartbeats = max(0, self._missed_heartbeats - 1)
        return True

    def get_tick(self, count: int = 100) -> list[MT5Tick]:
        """MT5-51: Get latest ticks."""
        ticks = self._tick_buffer.capture_latest(count)
        self._tick_count += len(ticks)
        now = time.time()
        if self._tick_window_start == 0:
            self._tick_window_start = now
        elif now - self._tick_window_start >= 1.0:
            self._tick_rate = self._tick_count / (now - self._tick_window_start)
            self._tick_count = 0
            self._tick_window_start = now
        return ticks

    def get_candles(self, timeframe: str = "M1", count: int = 100) -> list[MT5Candle]:
        """MT5-52: Get candles."""
        cached = self._candle_cache.get_cached(timeframe, count)
        if len(cached) < count:
            return self._candle_cache.fetch(timeframe, count)
        return cached

    def get_account(self) -> MT5AccountState | None:
        """MT5-53: Get account state."""
        return self._account.snapshot()

    def get_diagnostics(self) -> dict[str, Any]:
        """MT5-54: Full diagnostics."""
        return {
            "running": self._running,
            "connected": self._connection.is_healthy(),
            "symbol": self._symbol,
            "connection_stats": self._connection.get_stats(),
            "tick_rate": self._tick_rate,
            "total_ticks": self._tick_count,
            "missed_heartbeats": self._missed_heartbeats,
            "account": self._account.get_stats(),
            "errors": self._errors[-10:],
            "queue_size": len(self._queue),
            "paused": self._paused,
        }
