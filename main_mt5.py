"""
SOLÉNN v2 — MT5 Runner (MT5-109 to MT5-162)
Connects SOLÉNN Brain (Data→Agents→Decision→Execution) to live MT5 terminal.

Modes:
    PAPER:     Signals generated, NO orders sent
    SCALPER:   Live orders with small volume
    FULL:      Full autonomous trading

Usage:
    python main_mt5.py
    python main_mt5.py --mode paper --symbol BTCUSD --volume 0.01 --ticks 1000
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
from datetime import datetime

# Ensure project root in path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import MetaTrader5 as mt5

from core.mt5.bridge import MT5Bridge
from core.mt5.data_stream import MT5Tick
from core.agents.orderflow import VPINCalculator, OrderFlowImbalance, MarketQualityIndex
from core.agents.regime import TrendStrengthIndex, VolatilityCone
from core.agents.signal_aggregator import AdaptiveWeightedAggregator, MetaSignal


class SOLÉNN_MT5_Runner:
    """
    MT5-109 to MT5-162: SOLÉNN Ω running in MT5 context.
    Full integration: MT5 → Data → Features → Signals → Decision → MT5 Order
    """

    def __init__(
        self,
        symbol: str = "BTCUSD",
        volume: float = 0.01,
        mode: str = "paper",
        max_ticks: int = 0,
        max_loss: float = 2000.0,
        max_positions: int = 1,
    ):
        self._symbol = symbol
        self._volume = volume
        self._mode = mode
        self._max_ticks = max_ticks
        self._max_loss = max_loss
        self._max_positions = max_positions
        self._running = False
        self._tick_count = 0
        self._n_signals = 0
        self._n_orders = 0
        self._n_rejected = 0
        self._total_pnl = 0.0
        self._start_time = 0.0

        # SOLÉNN Brain components
        self._vpin = VPINCalculator(bucket_volume=10.0, num_buckets=20)
        self._orderflow = OrderFlowImbalance()
        self._mqi = MarketQualityIndex()
        self._trend = TrendStrengthIndex(window=50)
        self._vola = VolatilityCone(horizons=[10, 30, 60])
        self._aggregator = AdaptiveWeightedAggregator()
        for s in ["vpin", "orderflow", "trend", "volatility", "market_quality"]:
            self._aggregator.register_signal(s)

        # MT5 Bridge
        self._bridge: MT5Bridge | None = None

        # Price tracking
        self._prices: list[float] = []

    def start(self) -> bool:
        """MT5-110: Initialize MT5 + connect bridge."""
        print(f"[SOLÉNN] Starting on {self._symbol} — Mode: {self._mode.upper()}")
        print(f"[SOLÉNN] Volume: {self._volume}, Max Loss: ${self._max_loss}")

        ok = mt5.initialize()
        if not ok:
            print("[ERROR] Failed to connect to MT5")
            return False

        print(f"[SOLÉNN] MT5 connected — {mt5.terminal_info().company}")
        acc = mt5.account_info()
        print(f"[SOLÉNN] Account: {acc.login}, Balance: ${acc.balance:.2f}")

        self._bridge = MT5Bridge(
            symbol=self._symbol,
            max_position_volume=self._volume * 10,
            max_open_positions=self._max_positions,
        )

        ok = self._bridge.start()
        if not ok:
            print("[ERROR] Failed to start bridge")
            return False

        sym = self._bridge.get_symbol_info()
        if sym:
            print(f"[SOLÉNN] Symbol: {sym.name} — Spread: {sym.spread}, "
                  f"Bid: {sym.bid}, Ask: {sym.ask}, Vol: {sym.volume_min}-{sym.volume_max}")

        self._running = True
        self._start_time = time.time()
        return True

    def stop(self) -> None:
        """MT5-116: Graceful shutdown."""
        self._running = False
        if self._bridge:
            elapsed = time.time() - self._start_time
            print(f"\n[SOLÉNN] Shutting down after {elapsed:.0f}s")
            print(f"[SOLÉNN] Ticks: {self._tick_count}, Signals: {self._n_signals}, "
                  f"Orders: {self._n_orders}, Rejected: {self._n_rejected}")
            print(f"[SOLÉNN] P&L: ${self._total_pnl:.2f}")
            pos = self._bridge.get_positions()
            if pos:
                print(f"[SOLÉNN] Open positions: {len(pos)}")
                for p in pos:
                    print(f"  #{p.ticket} {p.symbol} {'BUY' if p.is_long else 'SELL'} "
                          f"{p.volume} @ {p.open_price}, P&L: ${p.profit:.2f}")
            self._bridge.stop()
        mt5.shutdown()

    def _compute_signals(self, tick: MT5Tick) -> dict[str, tuple[str, float]]:
        """MT5-117: Compute SOLÉNN signals from tick data."""
        ret = tick.bid - (self._prices[-1] if self._prices else tick.bid)
        r2, direction = self._trend.update(tick.bid)
        vpin_val = self._vpin.update(tick.volume, tick.bid > tick.ask) or 0.5
        ofi_val = self._orderflow.compute([tick.volume], [tick.volume * 0.8])
        mq = self._mqi.update(
            tick.spread_bps, tick.volume, vpin_val
        )

        self._vola.update(abs(ret) if ret != 0 else tick.spread_bps / 10000)

        # Build agent signals
        is_long = r2 > 0.5 if direction > 0 else r2 < 0.3
        return {
            "vpin": ("short" if vpin_val > 0.5 else "long", abs(0.5 - vpin_val) * 2),
            "orderflow": ("long" if ofi_val > 0 else "short", abs(ofi_val)),
            "trend": ("long" if direction > 0 else "short", r2),
            "volatility": ("short" if mq < 30 else "long", mq / 100),
            "market_quality": ("long" if mq > 50 else "short", mq / 100),
        }

    def _execute(self, meta: MetaSignal, tick: MT5Tick) -> None:
        """MT5-118: Execute signal via MT5."""
        if self._mode == "paper":
            print(f"  [PAPER] {'BUY' if meta.direction == 'long' else 'SELL'} | "
                  f"Conf: {meta.confidence:.2f} | Price: {tick.bid:.2f}")
            self._n_signals += 1
            return

        # Live execution
        if meta.confidence < 0.6:
            return

        self._n_signals += 1

        if self._bridge is None:
            return

        # Check loss limit
        exposure = self._bridge.get_total_exposure()
        if self._max_loss > 0:
            profit = exposure.get("total_profit", 0.0)
            if profit < -self._max_loss:
                print(f"[EMERGENCY] Loss limit hit: ${profit:.2f} < -${self._max_loss}")
                self._bridge.execute_emergency_close()
                self._running = False
                return

        # Execute
        try:
            if meta.direction == "long":
                atr = max(100.0, tick.bid * 0.001)
                sl = tick.bid - atr * 2
                tp = tick.bid + atr * 4

                result = self._bridge.buy(self._symbol, self._volume, sl=sl, tp=tp, comment="SOL_OMEGA")
            else:
                atr = max(100.0, tick.bid * 0.001)
                sl = tick.bid + atr * 2
                tp = tick.bid - atr * 4
                result = self._bridge.sell(self._symbol, self._volume, sl=sl, tp=tp, comment="SOL_OMEGA")

            if result.success:
                self._n_orders += 1
                print(f"  [FILLED] #{result.ticket} {meta.direction.upper()} "
                      f"{self._volume} @ {result.price:.2f} | "
                      f"Lat: {result.latency_ms:.0f}ms")
            else:
                self._n_rejected += 1
                print(f"  [REJECTED] {result.comment}")
        except Exception as e:
            self._n_rejected += 1
            print(f"  [ERROR] {e}")

    def run_loop(self) -> None:
        """MT5-119: Main trading loop."""
        print(f"\n[SOLÉNN] {'='*60}")
        print(f"[SOLÉNN] Running loop — Press Ctrl+C to stop")
        print(f"[SOLÉNN] {'='*60}")

        print_interval = 50
        tick_offset = 0
        seen_times = set()
        try:
            while self._running:
                # Use candles for unique price points (M1)
                candles = self._bridge.get_candles("M1", 50) if self._bridge else []
                if not candles:
                    time.sleep(1.0)
                    continue

                for candle in candles:
                    tick_time = candle.time_ns
                    if tick_time in seen_times:
                        continue
                    seen_times.add(tick_time)
                    self._tick_count += 1
                    tick_offset += 1

                    # Create pseudo-tick from candle
                    tick = MT5Tick(
                        symbol=candle.symbol,
                        time_ns=tick_time,
                        bid=candle.close,
                        ask=candle.close + 1.0,  # Simulated spread
                        last=candle.close,
                        volume=candle.tick_volume,
                        flags=0,
                        spread_bps=1.0,
                    )

                    self._prices.append(tick.bid)
                    if len(self._prices) > 500:
                        self._prices = self._prices[-500:]

                    agent_signals = self._compute_signals(tick)
                    if self._bridge:
                        positions = self._bridge.get_positions()
                        if len(positions) >= self._max_positions:
                            continue

                    meta = self._aggregator.aggregate(agent_signals)
                    if meta.confidence < 0.50:
                        continue

                    self._execute(meta, tick)

                    if self._tick_count % print_interval == 0:
                        acc = self._bridge.get_account() if self._bridge else None
                        acc_str = ""
                        if acc:
                            acc_str = f" | Bal: ${acc.balance:.2f} | Eq: ${acc.equity:.2f}"
                        print(f"  [{self._tick_count}] Candle | Signals: {self._n_signals} | "
                              f"Orders: {self._n_orders} | "
                              f"Price: {tick.bid:.2f}{acc_str}")

                # Check max ticks
                if self._max_ticks > 0 and self._tick_count >= self._max_ticks:
                    print(f"\n[SOLÉNN] Max ticks reached: {self._max_ticks}")
                    break

                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"[ERROR] {e}")
            if self._bridge:
                self._bridge.execute_emergency_close()
        finally:
            self.stop()


def main():
    parser = argparse.ArgumentParser(description="SOLÉNN Ω MT5 Runner")
    parser.add_argument("--mode", default="paper", choices=["paper", "scalper", "full"])
    parser.add_argument("--symbol", default="BTCUSD")
    parser.add_argument("--volume", type=float, default=0.01)
    parser.add_argument("--max-ticks", type=int, default=0, help="0 = run forever")
    parser.add_argument("--max-loss", type=float, default=2000.0, help="Max loss before emergency close")
    parser.add_argument("--max-positions", type=int, default=1)
    args = parser.parse_args()

    runner = SOLÉNN_MT5_Runner(
        symbol=args.symbol,
        volume=args.volume,
        mode=args.mode,
        max_ticks=args.max_ticks,
        max_loss=args.max_loss,
        max_positions=args.max_positions,
    )

    # Graceful shutdown on SIGINT/SIGTERM
    def handler(sig, frame):
        runner.stop()
        sys.exit(0)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    if not runner.start():
        print("[ERROR] Failed to start SOLÉNN Ω")
        sys.exit(1)

    runner.run_loop()


if __name__ == "__main__":
    main()
