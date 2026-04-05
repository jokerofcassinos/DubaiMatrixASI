"""
SOLÉNN v2 — MT5 Bridge: Unifies Data Stream + Executor (MT5-01 to MT5-108)
Single entry point that connects all data and execution capabilities.
"""

from __future__ import annotations

import time
from typing import Any

import MetaTrader5 as mt5

from core.mt5.data_stream import (
    MT5Connection,
    MT5Tick,
    MT5Candle,
    TickBuffer,
    CandleCache,
    SymbolRegistry,
    AccountMonitor,
    MT5DataStreamer,
    MT5ConnectionInfo,
    MT5AccountState,
    MT5SymbolInfo,
)
from core.mt5.executor import (
    OrderRequest,
    OrderResult,
    OrderValidator,
    OrderType,
    MT5OrderExecutor,
    PositionManager,
    PositionInfo,
    ExecutionRiskGuards,
    OrderReconciliation,
    EmergencyManager,
)


class MT5Bridge:
    """
    Unified bridge to MetaTrader5.
    Combines MT5DataStream + MT5Executor + reconciliation + emergency.

    Usage:
        bridge = MT5Bridge(symbol='BTCUSD')
        bridge.start()

        # Data
        ticks = bridge.get_ticks(100)
        candles = bridge.get_candles('M1', 50)
        account = bridge.get_account()

        # Execution
        result = bridge.buy('BTCUSD', volume=0.1, sl=66000, tp=68000)
        positions = bridge.get_positions()

        # Stop
        bridge.stop()
    """

    def __init__(
        self,
        symbol: str = "BTCUSD",
        timeframes: list[str] | None = None,
        magic: int = 20240401,
        max_position_volume: float = 1.0,
        max_open_positions: int = 3,
        max_drawdown_pct: float = 2.0,
    ):
        # Data
        self._symbol = symbol
        self._streamer = MT5DataStreamer(symbol, timeframes or ["M1", "M5", "M15", "H1"])
        self._data = self._streamer  # alias

        # Execution
        self._executor = MT5OrderExecutor(magic=magic)
        self._positions = PositionManager()
        self._risk_guards = ExecutionRiskGuards(
            max_position_volume=max_position_volume,
            max_open_positions=max_open_positions,
        )
        self._account = AccountMonitor(max_drawdown_pct=max_drawdown_pct)
        self._reconciliation = OrderReconciliation()
        self._emergency = EmergencyManager()

        self._started = False
        self._start_time = 0.0

    # ── Lifecycle ──

    def start(self) -> bool:
        ok = self._streamer.start()
        if ok:
            self._started = True
            self._start_time = time.time()
        return ok

    def stop(self) -> None:
        self._streamer.stop()
        self._started = False

    def is_running(self) -> bool:
        return self._started and self._streamer.is_healthy()

    # ── Data ──

    def get_ticks(self, count: int = 100) -> list[MT5Tick]:
        return self._streamer.get_tick(count)

    def get_candles(self, timeframe: str = "M1", count: int = 100) -> list[MT5Candle]:
        return self._streamer.get_candles(timeframe, count)

    def get_account(self) -> MT5AccountState | None:
        return self._streamer.get_account()

    def get_symbol_info(self) -> MT5SymbolInfo | None:
        return self._data._symbols.get(self._symbol)

    # ── Execution ──

    def buy(self, symbol: str, volume: float,
            sl: float | None = None, tp: float | None = None,
            comment: str = "") -> OrderResult:
        errors = self._risk_guards.full_check(OrderRequest(
            symbol=symbol, order_type=OrderType.BUY, volume=volume,
            stop_loss=sl, take_profit=tp, comment=comment,
        ))
        if errors:
            return OrderResult(
                success=False, ticket=0, price=0.0, volume=volume,
                symbol=symbol, retcode=10030,
                comment="Risk guard: " + ", ".join(errors),
                request_id="risk_rejected", latency_ms=0.0,
            )
        req = OrderRequest(
            symbol=symbol, order_type=OrderType.BUY, volume=volume,
            stop_loss=sl, take_profit=tp, comment=comment,
        )
        return self._executor.submit_market_order(req)

    def sell(self, symbol: str, volume: float,
             sl: float | None = None, tp: float | None = None,
             comment: str = "") -> OrderResult:
        errors = self._risk_guards.full_check(OrderRequest(
            symbol=symbol, order_type=OrderType.SELL, volume=volume,
            stop_loss=sl, take_profit=tp, comment=comment,
        ))
        if errors:
            return OrderResult(
                success=False, ticket=0, price=0.0, volume=volume,
                symbol=symbol, retcode=10030,
                comment="Risk guard: " + ", ".join(errors),
                request_id="risk_rejected", latency_ms=0.0,
            )
        req = OrderRequest(
            symbol=symbol, order_type=OrderType.SELL, volume=volume,
            stop_loss=sl, take_profit=tp, comment=comment,
        )
        return self._executor.submit_market_order(req)

    def close_all(self) -> list[OrderResult]:
        return self._executor.close_position(self._symbol)

    def close_specific(self, symbol: str, volume: float | None = None) -> list[OrderResult]:
        return self._executor.close_position(symbol, volume)

    # ── State ──

    def get_positions(self) -> list[PositionInfo]:
        return self._positions.get_open_positions(self._symbol)

    def get_total_exposure(self) -> dict[str, float]:
        return self._positions.get_total_exposure()

    def get_reconciliation(self) -> dict[str, Any]:
        return self._reconciliation.reconcile_positions()

    def execute_emergency_close(self) -> list[OrderResult]:
        return self._emergency.close_all_positions()

    # ── Diagnostics ──

    def get_diagnostics(self) -> dict[str, Any]:
        return {
            "running": self.is_running(),
            "runtime_s": round(time.time() - self._start_time, 1) if self._started else 0.0,
            "data": self._streamer.get_diagnostics(),
            "executor": self._executor.stats,
            "positions": [p.ticket for p in self._positions.get_open_positions(self._symbol)],
            "exposure": self._positions.get_total_exposure(),
            "risk": self._risk_guards.get_stats(),
            "emergency": self._emergency.check_emergency_conditions(),
            "account": self._account.get_stats(),
        }
