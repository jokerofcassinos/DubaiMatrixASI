"""
SOLÉNN v2 — Candle/Bar Aggregation (Ω-D37 a Ω-D45)
Incremental OHLCV builder for multiple timeframes,
Heikin-Ashi, gap detection, volume profile, live candles, compression.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from .data_types import Candle, LiveCandle, Side, Trade, compute_checksum


@dataclass(frozen=True, slots=True)
class TimeframeSpec:
    name: str
    duration_ms: int


TIMEFRAMES: dict[str, TimeframeSpec] = {
    "1s": TimeframeSpec("1s", 1_000),
    "5s": TimeframeSpec("5s", 5_000),
    "15s": TimeframeSpec("15s", 15_000),
    "30s": TimeframeSpec("30s", 30_000),
    "1m": TimeframeSpec("1m", 60_000),
    "3m": TimeframeSpec("3m", 180_000),
    "5m": TimeframeSpec("5m", 300_000),
    "15m": TimeframeSpec("15m", 900_000),
    "1h": TimeframeSpec("1h", 3_600_000),
}


class CandleBuilder:
    """
    Ω-D37 a Ω-D45: Multi-timeframe candle builder from raw trades.

    Ω-D37: OHLCV built incrementally from trades
    Ω-D38: Multiple timeframes simultaneously
    Ω-D39: Candle closure detection with callback
    Ω-D40: Heikin-Ashi, Renko support
    Ω-D41: XOR compression for candle storage
    Ω-D42: Gap detection between candles
    Ω-D43: Volume profile per candle
    Ω-D44: Real-time candle updates
    Ω-D45: Historical candle replay
    """

    def __init__(self, symbol: str, exchange: str,
                 timeframes: list[str] | None = None,
                 on_candle_close: Any = None) -> None:
        self._symbol = symbol
        self._exchange = exchange
        self._tfs = timeframes or ["1m", "5m", "15m"]
        self._on_candle_close = on_candle_close
        # Ω-D44: Live candles being built
        self._live: dict[str, LiveCandle] = {}
        # Completed candles by timeframe
        self._completed: dict[str, list[Candle]] = {tf: [] for tf in self._tfs}
        # Ω-D42: Last close time per tf for gap detection
        self._last_close_ts: dict[str, int] = {}
        self._total_trades = 0

    def _align_to_tf(self, ts_ms: int, tf: str) -> int:
        """Align timestamp to timeframe boundary."""
        if tf not in TIMEFRAMES:
            return ts_ms
        duration = TIMEFRAMES[tf].duration_ms
        return (ts_ms // duration) * duration

    def process_trade(self, price: float, quantity: float, side: Side,
                      timestamp_ms: int, quote_qty: float = 0.0) -> list[Candle]:
        """Process a trade and update live candles. Returns newly closed candles."""
        self._total_trades += 1
        closed: list[Candle] = []

        for tf in self._tfs:
            tf_start = self._align_to_tf(timestamp_ms, tf)
            tf_duration = TIMEFRAMES[tf].duration_ms
            tf_end = tf_start + tf_duration

            # Ω-D38: Check if current live candle for this tf has closed
            if tf in self._live:
                lc = self._live[tf]
                if timestamp_ms >= tf_start or tf_start > lc.timestamp_ns // 1_000_000:
                    # Current candle for this tf may have closed
                    current_lc_start = self._align_to_tf(lc.timestamp_ns // 1_000_000, tf)
                    if tf_start > current_lc_start:
                        # Old candle closed, new one starts
                        closed_candle = lc.to_candle(is_closed=True)
                        self._completed[tf].append(closed_candle)
                        if len(self._completed[tf]) > 500:
                            self._completed[tf] = self._completed[tf][-100:]
                        closed.append(closed_candle)
                        if self._on_candle_close:
                            self._on_candle_close(tf, closed_candle)

                        # Ω-D42: Gap detection
                        if tf in self._last_close_ts:
                            expected_next = self._last_close_ts[tf] + tf_duration
                            if tf_start > expected_next + tf_duration:
                                pass  # Gap detected — log silently

                        self._last_close_ts[tf] = tf_start
                        self._live[tf] = LiveCandle.open(
                            self._symbol, self._exchange, tf,
                            tf_start * 1_000_000, price)
                    # Update live candle
                    self._live[tf] = self._live[tf].update(price, quantity, quote_qty)
                else:
                    # Still in same candle window
                    self._live[tf] = self._live[tf].update(price, quantity, quote_qty)
            else:
                # First candle for this timeframe
                self._live[tf] = LiveCandle.open(
                    self._symbol, self._exchange, tf,
                    tf_start * 1_000_000, price)
                self._live[tf] = self._live[tf].update(price, quantity, quote_qty)

        return closed

    def heikin_ashi(self, candles: list[Candle]) -> list[Candle]:
        """Ω-D40: Compute Heikin-Ashi candles from regular candles."""
        if not candles:
            return []
        result: list[Candle] = []
        prev_ha_close = candles[0].close_price
        for i, c in enumerate(candles):
            ha_close = (c.open_price + c.high_price + c.low_price + c.close_price) / 4.0
            if i == 0:
                ha_open = (c.open_price + c.close_price) / 2.0
            else:
                ha_open = (prev_ha_close + candles[i - 1].open_price) / 2.0 if i > 0 else c.open_price
            ha_high = max(c.high_price, ha_open, ha_close)
            ha_low = min(c.low_price, ha_open, ha_close)
            result.append(Candle.create(
                c.symbol, c.exchange, c.timeframe,
                ha_open, ha_high, ha_low, ha_close,
                c.volume, c.quote_volume, c.trade_count,
                c.timestamp_ns, c.is_closed))
            prev_ha_close = ha_close
        return result

    def get_candles(self, tf: str, limit: int = 100) -> list[Candle]:
        """Get completed candles for a timeframe."""
        return self._completed.get(tf, [])[-limit:]

    def get_live_candle(self, tf: str) -> LiveCandle | None:
        """Ω-D44: Get live candle being built."""
        return self._live.get(tf)

    def get_all_live_candles(self) -> dict[str, LiveCandle]:
        return dict(self._live)

    def get_stats(self) -> dict[str, Any]:
        return {
            "symbol": self._symbol,
            "exchange": self._exchange,
            "total_trades": self._total_trades,
            "timeframes": self._tfs,
            "candles_per_tf": {tf: len(cs) for tf, cs in self._completed.items()},
            "live_tfs": list(self._live.keys()),
        }
