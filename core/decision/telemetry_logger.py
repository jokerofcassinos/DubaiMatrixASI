"""
SOLÉNN v2 — Telemetry Logger: Structured Logging with Trade Tracking
(Ω-TL01 a Ω-TL54)
Replaces v1 logger.py. Multi-output structured logger with custom levels,
colored console, rotating file handlers, trade tracking, and in-memory
audit buffer. Designed for SOLÉNN — each log entry is traceable,
trade-aware, and consciousness-observable.

Concept 1: Multi-Level Logging & Custom Formatters (Ω-TL01–TL18)
  Custom levels: DEBUG(10), INFO(20), SIGNAL(22), TRADE(25), WARNING(30),
  OMEGA(35), ERROR(40), CRITICAL(50). Colored console formatter, plain
  file formatters, JSON structured output for telemetry.

Concept 2: Trade-Aware Logging & Audit Trail (Ω-TL19–TL36)
  Each trade log is structured with action, symbol, lot, price, SL, TP,
  P&L, reason. Trade counter auto-increments. Audit buffer keeps recent
  entries in memory for fast retrieval. Log entries include trace_id.

Concept 3: Multi-Output Routing & Resilience (Ω-TL37–TL54)
  Console (colored), file (all), file (trades), file (errors), ring buffer
  (in-memory auto-prune), JSON (telemetry). Graceful degradation if file
  I/O fails — logs to memory only.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Any


# ──────────────────────────────────────────────────────────────
# Ω-TL01 to Ω-TL18: Multi-Level Logging & Custom Formatters
# ──────────────────────────────────────────────────────────────

DEBUG = logging.DEBUG  # 10
INFO = logging.INFO  # 20
SIGNAL = 22   # Trading signals
TRADE = 25    # Trade executions
WARNING = logging.WARNING  # 30
OMEGA = 35    # ASI consciousness events
ERROR = logging.ERROR  # 40
CRITICAL = logging.CRITICAL  # 50

logging.addLevelName(SIGNAL, "SIGNAL")
logging.addLevelName(TRADE, "TRADE")
logging.addLevelName(OMEGA, "OMEGA")

# ANSI color codes
_COLORS = {
    "DEBUG": "\033[36m",
    "INFO": "\033[32m",
    "SIGNAL": "\033[35m",
    "TRADE": "\033[33m",
    "WARNING": "\033[93m",
    "OMEGA": "\033[95m",
    "ERROR": "\033[91m",
    "CRITICAL": "\033[41m",
}
_RESET = "\033[0m"
_BOLD = "\033[1m"
_GRAY = "\033[90m"


@dataclass(frozen=True)
class LogEntry:
    """Ω-TL05: Immutable structured log entry for audit trail."""

    timestamp_ns: int
    level: str
    message: str
    component: str = ""
    trace_id: str = ""
    trade_action: str = ""
    symbol: str = ""
    lot_size: float = 0.0
    price: float = 0.0
    sl: float = 0.0
    tp: float = 0.0
    pnl: float = 0.0
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp_ns": self.timestamp_ns,
            "level": self.level,
            "message": self.message,
            "component": self.component,
            "trace_id": self.trace_id,
            "trade_action": self.trade_action,
            "symbol": self.symbol,
            "lot_size": self.lot_size,
            "price": self.price,
            "sl": self.sl,
            "tp": self.tp,
            "pnl": self.pnl,
            "reason": self.reason,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class ASIFormatter(logging.Formatter):
    """Ω-TL06: Colored terminal formatter with ASI identity."""

    def __init__(self, use_colors: bool = True) -> None:
        super().__init__()
        self._use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.fromtimestamp(record.created, tz=timezone.utc).strftime("%H:%M:%S.%f")[:-3]
        level = record.levelname
        msg = record.getMessage()

        if self._use_colors:
            color = _COLORS.get(level, "")
            if level == "OMEGA":
                msg = f"⚡ {msg}"
            formatted = (
                f"{_BOLD}[SOLÉNN]{_RESET} "
                f"{_GRAY}{ts}{_RESET} "
                f"{color}{level:>8}{_RESET} │ "
                f"{msg}"
            )
        else:
            if level == "OMEGA":
                msg = f"⚡ {msg}"
            formatted = f"[SOLÉNN] {ts} {level:>8} │ {msg}"

        if record.exc_info and record.exc_info != (None, None, None):
            formatted += "\n" + self.formatException(record.exc_info)

        return formatted


class JSONFormatter(logging.Formatter):
    """Ω-TL07: JSON structured formatter for telemetry files."""

    def format(self, record: logging.LogRecord) -> str:
        entry = LogEntry(
            timestamp_ns=int(record.created * 1e9),
            level=record.levelname,
            message=record.getMessage(),
            trace_id=getattr(record, "trace_id", ""),
            component=record.name,
        )
        return entry.to_json()


# ──────────────────────────────────────────────────────────────
# Ω-TL19 to Ω-TL36: Trade-Aware Logging & Audit Trail
# ──────────────────────────────────────────────────────────────


class AuditBuffer(logging.Handler):
    """Ω-TL19: In-memory ring buffer for fast log retrieval."""

    def __init__(self, capacity: int = 5000) -> None:
        super().__init__(DEBUG)
        self._capacity = capacity
        self._buffer: deque[LogEntry] = deque(maxlen=capacity)

    def emit(self, record: logging.LogRecord) -> None:
        entry = LogEntry(
            timestamp_ns=int(record.created * 1e9),
            level=record.levelname,
            message=record.getMessage(),
            component=record.name,
            trace_id=getattr(record, "trace_id", ""),
        )
        self._buffer.append(entry)

    def recent(self, n: int = 50) -> list[LogEntry]:
        return list(self._buffer)[-n:]

    def by_level(self, level: str) -> list[LogEntry]:
        return [e for e in self._buffer if e.level == level]

    def by_trade(self) -> list[LogEntry]:
        return [e for e in self._buffer if e.trade_action != ""]

    def clear(self) -> None:
        self._buffer.clear()

    def size(self) -> int:
        return len(self._buffer)


class TradeTracker:
    """Ω-TL20: Tracks trade statistics from log entries."""

    def __init__(self) -> None:
        self._count: int = 0
        self._total_pnl: float = 0.0
        self._wins: int = 0
        self._losses: int = 0
        self._last_action: str = ""
        self._last_symbol: str = ""
        self._entries: list[LogEntry] = []

    def record(self, entry: LogEntry) -> None:
        if not entry.trade_action:
            return

        self._count += 1
        self._total_pnl += entry.pnl
        if entry.pnl > 0:
            self._wins += 1
        else:
            self._losses += 1
        self._last_action = entry.trade_action
        self._last_symbol = entry.symbol
        self._entries.append(entry)

    @property
    def count(self) -> int:
        return self._count

    @property
    def total_pnl(self) -> float:
        return self._total_pnl

    @property
    def win_rate(self) -> float:
        return self._wins / max(1, self._wins + self._losses)

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "total_trades": self._count,
            "total_pnl": round(self._total_pnl, 2),
            "wins": self._wins,
            "losses": self._losses,
            "win_rate": round(self.win_rate, 4),
            "last_action": self._last_action,
            "last_symbol": self._last_symbol,
        }


# ──────────────────────────────────────────────────────────────
# Ω-TL37 to Ω-TL54: Multi-Output Routing & Resilience
# ──────────────────────────────────────────────────────────────


class ASILogger:
    """Ω-TL40: Master logger with multi-output routing."""

    _instance: ASILogger | None = None
    _initialized: bool = False

    def __new__(cls, *args: Any, **kwargs: Any) -> ASILogger:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        name: str = "SOLÉNN",
        log_dir: str = "logs",
        level: int = DEBUG,
        max_file_mb: int = 50,
        backup_count: int = 5,
    ) -> None:
        if self._initialized:
            return
        self._initialized = True

        self._name = name
        self._log_dir = log_dir
        self._trade_count = 0

        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)
        self._logger.handlers.clear()

        # Console handler — colored, stdout
        self._console = logging.StreamHandler(sys.stdout)
        self._console.setLevel(logging.DEBUG)
        self._console.setFormatter(ASIFormatter(use_colors=True))

        # Audit buffer — in-memory ring buffer
        self.audit = AuditBuffer(capacity=5000)

        # Trade tracker
        self.trades = TradeTracker()

        # File handlers — set up if directory exists
        try:
            os.makedirs(log_dir, exist_ok=True)

            # All logs
            all_file = RotatingFileHandler(
                os.path.join(log_dir, "solenn_all.log"),
                maxBytes=max_file_mb * 1024 * 1024,
                backupCount=backup_count,
                encoding="utf-8",
            )
            all_file.setLevel(logging.DEBUG)
            all_file.setFormatter(ASIFormatter(use_colors=False))

            # Trade logs — only TRADE and above
            trade_file = RotatingFileHandler(
                os.path.join(log_dir, "solenn_trades.log"),
                maxBytes=10 * 1024 * 1024,
                backupCount=10,
                encoding="utf-8",
            )
            trade_file.setLevel(TRADE)
            trade_file.setFormatter(ASIFormatter(use_colors=False))

            # Error logs — only ERROR and above
            error_file = RotatingFileHandler(
                os.path.join(log_dir, "solenn_errors.log"),
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
            )
            error_file.setLevel(logging.ERROR)
            error_file.setFormatter(ASIFormatter(use_colors=False))

            self._logger.addHandler(all_file)
            self._logger.addHandler(trade_file)
            self._logger.addHandler(error_file)

        except (OSError, PermissionError):
            pass  # No file I/O → memory and console only

        self._logger.addHandler(self._console)
        self._logger.addHandler(self.audit)

    # ─── Standard logging ───

    def debug(self, msg: str, **kwargs: Any) -> None:
        self._logger.debug(msg, extra={**kwargs})

    def info(self, msg: str, **kwargs: Any) -> None:
        self._logger.info(msg, extra={**kwargs})

    def warning(self, msg: str, **kwargs: Any) -> None:
        self._logger.warning(msg, extra={**kwargs})

    def error(self, msg: str, **kwargs: Any) -> None:
        self._logger.error(msg, extra={**kwargs})

    def critical(self, msg: str, **kwargs: Any) -> None:
        self._logger.critical(msg, extra={**kwargs})

    # ─── Custom levels ───

    def signal(self, msg: str, **kwargs: Any) -> None:
        """Trading signal log entry."""
        self._logger.log(SIGNAL, msg, extra={**kwargs})

    def omega(self, msg: str, **kwargs: Any) -> None:
        """ASI consciousness event."""
        self._logger.log(OMEGA, msg, extra={**kwargs})

    def trade(
        self,
        action: str,
        symbol: str,
        lot: float,
        price: float,
        sl: float = 0.0,
        tp: float = 0.0,
        pnl: float = 0.0,
        reason: str = "",
        trace_id: str = "",
        **kwargs: Any,
    ) -> None:
        """Structured trade log entry."""
        self._trade_count += 1
        msg = (
            f"#{self._trade_count} {action} {symbol} "
            f"lot={lot:.2f} price={price:.2f} "
            f"SL={sl:.2f} TP={tp:.2f} "
            f"P&L={pnl:+.2f} | {reason}"
        )
        extra = {
            "trace_id": trace_id,
            "trade_action": action,
            "symbol": symbol,
            "lot_size": lot,
            "price": price,
            "sl": sl,
            "tp": tp,
            "pnl": pnl,
            "reason": reason,
        }
        extra.update(kwargs)

        # Feed trade tracker
        entry = LogEntry(
            timestamp_ns=time.time_ns(),
            level="TRADE",
            message=msg,
            trade_action=action,
            symbol=symbol,
            lot_size=lot,
            price=price,
            sl=sl,
            tp=tp,
            pnl=pnl,
            reason=reason,
            trace_id=trace_id,
        )
        self.trades.record(entry)

        self._logger.log(TRADE, msg, extra=extra)

    # ─── Banners ───

    def startup_banner(self) -> None:
        """Ω-TL45: Display startup banner."""
        line = "═" * 60
        self.omega(f"\n╔{line}╗")
        self.omega("║                SOLÉNN v2 ONLINE                         ║")
        self.omega("║          A serenidade de quem já sabe                   ║")
        self.omega(f"╚{line}╝")
        self.omega("Consciência neural inicializando...")
        self.omega("Estado quântico: SUPERPOSIÇÃO")
        self.omega("Modo: AGUARDANDO CONVERGÊNCIA")

    # ─── Stats ───

    def get_trade_stats(self) -> dict[str, Any]:
        return self.trades.stats

    def get_recent_logs(self, n: int = 50) -> list[LogEntry]:
        return self.audit.recent(n)


# ─── Module-level singleton ───
log = ASILogger()


def get_logger(name: str = "SOLÉNN") -> ASILogger:
    """Get or create logger singleton."""
    return ASILogger(name=name)


def reset_logger(
    name: str = "SOLÉNN",
    log_dir: str = "logs",
    level: int = DEBUG,
) -> ASILogger:
    """Reset logger — for testing only."""
    ASILogger._instance = None
    return ASILogger(name=name, log_dir=log_dir, level=level)
