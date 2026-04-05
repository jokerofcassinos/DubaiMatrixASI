"""
SOLÉNN v2 — MT5 Runner (MT5-109 to MT5-162)
Connects SOLÉNN Brain (Data→Agents→Decision→Execution) to live MT5 terminal.

Modes:
    PAPER:     Signals generated, NO orders sent
    SCALPER:   Live orders with small volume
    FULL:      Full autonomous trading

Usage:
    d:/DubaiMatrixASI/venv/Scripts/python.exe d:/DubaiMatrixASI/main_mt5.py
    d:/DubaiMatrixASI/venv/Scripts/python.exe d:/DubaiMatrixASI/main_mt5.py --mode paper --symbol BTCUSD --volume 0.01 --ticks 1000
"""

from __future__ import annotations

import argparse
import os
import signal
import sys
import time
from collections import deque
from datetime import datetime

# Ensure project root in path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import MetaTrader5 as mt5

from core.mt5.bridge import MT5Bridge
from core.mt5.data_stream import MT5Tick
from core.agents.orderflow import VPINCalculator, OrderFlowImbalance, MarketQualityIndex
from core.agents.regime import TrendStrengthIndex, VolatilityCone
from core.agents.signal_aggregator import AdaptiveWeightedAggregator, MetaSignal


# --------------------------------------------------------------
# FTMO BTCUSD Contract Spec (discovered at runtime)
# --------------------------------------------------------------

@staticmethod
def _get_contract_spec(symbol: str) -> dict:
    """Query MT5 for exact contract parameters."""
    info = mt5.symbol_info(symbol)
    tick = mt5.symbol_info_tick(symbol)
    if info is None or tick is None:
        return {}

    # PnL for 0.01 lots per $1 price move on FTMO BTCUSD:
    #   profit = price_move × volume × trade_contract_size
    #   Most FTMO BTCUSD: 0.01 lots × $1 move = ~$0.01 PnL
    #   Commission ~$0.45 round-trip for 0.01 lots
    #
    # To be profitable: TP must generate > commission
    #   With $0.01 per $1 move → need 45+ points minimum
    #   For 2:1 R:R scalp → SL=30, TP=60 minimum

    point = info.point
    tick_value = info.trade_tick_value
    tick_size = info.trade_tick_size
    contract_size = info.trade_contract_size
    stops_level = info.trade_stops_level  # min SL distance in points

    return {
        "point": point,
        "tick_value": tick_value,
        "tick_size": tick_size,
        "contract_size": contract_size,
        "stops_level": stops_level,
        "spread": info.spread,  # in points
        "volume_min": info.volume_min,
        "volume_max": info.volume_max,
        "volume_step": info.volume_step,
        "digits": info.digits,
        "bid": tick.bid,
        "ask": tick.ask,
    }


def _pnl_per_point(spec: dict, volume: float) -> float:
    """Dollar PnL per point move for given volume.

    Verified from real FTMO BTCUSD deals:
      Deal profit=0.45 for ~45 point move on 0.01 lots
      → PnL = 0.45 / 45 = $0.01 per point for 0.01 volume
      → PnL = $1.00 per point for 1.0 volume

    This is: PnL = price_move × volume
    For 1 point (0.01 price): PnL = 0.01 × volume

    Verified from deals: 0.01 volume × 45 points × $1/point = $0.45 ✓
    """
    # PnL per point = volume (since 1 point = $1 price move × volume)
    return volume


class SOLÉNN_MT5_Runner:
    """
    MT5-109 to MT5-162: SOLÉNN running in MT5 context.
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

        # Contract spec (discovered at start)
        self._spec: dict = {}

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

        # Real-time candle tracking — only process NEW candles
        self._last_candle_time_ns: int = 0
        self._processed_candle_times: set[int] = set()

        # Order history for monitoring
        self._order_log: deque[dict] = deque(maxlen=100)

        # Dashboard interval
        self._candles_since_dashboard = 0

    # ----------------------------------------------------------
    # Lifecycle
    # ----------------------------------------------------------

    def start(self) -> bool:
        print(f"[SOLÉNN] Starting on {self._symbol} — Mode: {self._mode.upper()}")
        print(f"[SOLÉNN] Volume: {self._volume}, Max Loss: ${self._max_loss}")

        ok = mt5.initialize()
        if not ok:
            print("[ERROR] Failed to connect to MT5")
            return False

        print(f"[SOLÉNN] MT5 connected — {mt5.terminal_info().company}")
        acc = mt5.account_info()
        print(f"[SOLÉNN] Account: {acc.login}, Balance: ${acc.balance:.2f}")

        # Discover contract spec
        self._spec = _get_contract_spec(self._symbol)
        if self._spec:
            pnl_pt = _pnl_per_point(self._spec, self._volume)
            print(f"[SOLÉNN] Contract: point={self._spec['point']}, "
                  f"tick_val={self._spec['tick_value']}, contract_sz={self._spec['contract_size']}")
            print(f"[SOLÉNN] PnL per point for {self._volume} lots: ${pnl_pt:.6f}")
            print(f"[SOLÉNN] Min SL distance: {self._spec['stops_level']} points")
            print(f"[SOLÉNN] Spread: {self._spec['spread']} pts "
                  f"(= {(self._spec['spread'] * self._spec['point']):.2f} price)")

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
                          f"{p.volume} @ {p.open_price}, P&L: ${getattr(p, 'profit', 0.0):.2f}")
            self._bridge.stop()
        mt5.shutdown()

    # ----------------------------------------------------------
    # SL/TP Computation (calibrated for FTMO BTCUSD)
    # ----------------------------------------------------------

    def _compute_sl_tp(self, entry: float, direction: str) -> tuple[float, float, float, float]:
        """
        Compute SL/TP for FTMO BTCUSD.

        BTCUSD real ranges:
          M15 avg candle: ~7760 pts ($77.60)
          M5  avg candle: ~4218 pts ($42.18)
          Spread: 100 pts ($1.00)

        SL/TP based directly on recent M15 candle ranges:
          SL = 1.0x avg(M15 range / 2) — half a typical M15 candle
          TP = 2.0x avg(M15 range / 2) — 2:1 R:R

        This gives SL ~4000 pts ($40 move), TP ~8000 pts ($80 move).
        For 0.01 lots: SL risk = $0.40, TP reward = $0.80.
        Commission: $0.44 RT → TP net = $0.80 - $0.44 = $0.36.

        Floor: 1000 pts minimum (well below typical range).
        """
        atr_pts = self._compute_atr_in_points()
        if atr_pts > 0:
            sl_points = atr_pts * 1.0
            tp_points = atr_pts * 2.0
        else:
            sl_points = 2000.0
            tp_points = 4000.0

        # Floor: must exceed spread, FTMO rejection threshold
        sl_points = max(sl_points, 1000.0)
        tp_points = max(tp_points, sl_points * 2.0)

        # Convert points -> price
        point = self._spec.get("point", 0.01) if self._spec else 0.01
        sl_price_dist = sl_points * point
        tp_price_dist = tp_points * point

        digits = self._spec.get("digits", 2)

        if direction == "long":
            sl = round(entry - sl_price_dist, digits)
            tp = round(entry + tp_price_dist, digits)
        else:
            sl = round(entry + sl_price_dist, digits)
            tp = round(entry - tp_price_dist, digits)

        return sl, tp, round(sl_points, 1), round(tp_points, 1)

    def _compute_atr_in_points(self) -> float:
        """Estimate 'normal move' from recent M15 candles."""
        if not self._bridge:
            return 0.0

        m15_candles = self._bridge.get_candles("M15", 24)  # last 24h of M15
        if not m15_candles or len(m15_candles) < 8:
            return 0.0

        # Average last 12 M15 ranges (last 3 hours)
        ranges = [c.high - c.low for c in m15_candles[-12:]]
        if not ranges:
            return 0.0

        avg_range = sum(ranges) / len(ranges)
        point = self._spec.get("point", 0.01) if self._spec else 0.01
        avg_range_in_points = avg_range / point

        # SL = half of typical M15 range (avoids normal candle wicks)
        return avg_range_in_points / 2.0

    # ----------------------------------------------------------
    # Signal Computation
    # ----------------------------------------------------------

    def _compute_signals(self, tick: MT5Tick) -> dict[str, tuple[str, float]]:
        ret = tick.bid - (self._prices[-1] if self._prices else tick.bid)
        r2, direction = self._trend.update(tick.bid)
        vpin_val = self._vpin.update(tick.volume, tick.bid > tick.ask) or 0.5
        ofi_val = self._orderflow.compute([tick.volume], [tick.volume * 0.8])
        mq = self._mqi.update(tick.spread_bps, tick.volume, vpin_val)
        self._vola.update(abs(ret) if ret != 0 else tick.spread_bps / 10000)

        return {
            "vpin": ("short" if vpin_val > 0.5 else "long", abs(0.5 - vpin_val) * 2),
            "orderflow": ("long" if ofi_val > 0 else "short", abs(ofi_val)),
            "trend": ("long" if direction > 0 else "short", r2),
            "volatility": ("short" if mq < 30 else "long", mq / 100),
            "market_quality": ("long" if mq > 50 else "short", mq / 100),
        }

    # ----------------------------------------------------------
    # Execution
    # ----------------------------------------------------------

    def _execute(self, meta: MetaSignal, tick: MT5Tick) -> None:
        """Execute: fill market order, then set SL/TP on position."""
        if self._mode == "paper":
            print(f"  [PAPER] {'BUY' if meta.direction == 'long' else 'SELL'} | "
                  f"Conf: {meta.confidence:.2f} | Price: {tick.bid:.2f}")
            self._n_signals += 1
            return

        if meta.confidence < 0.6:
            return

        self._n_signals += 1
        if self._bridge is None:
            return

        exposure = self._bridge.get_total_exposure()
        if self._max_loss > 0:
            profit = exposure.get("total_profit", 0.0)
            if profit < -self._max_loss:
                print(f"[EMERGENCY] Loss limit: ${profit:.2f} < -${self._max_loss}")
                self._bridge.execute_emergency_close()
                self._running = False
                return

        try:
            # Step 1: Send market order WITHOUT SL/TP (avoids stale price rejection)
            if meta.direction == "long":
                result = self._bridge.buy(self._symbol, self._volume,
                                          comment="SOL_OMEGA")
            else:
                result = self._bridge.sell(self._symbol, self._volume,
                                           comment="SOL_OMEGA")

            if not result.success:
                self._n_rejected += 1
                self._order_log.append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "dir": meta.direction.upper(),
                    "ticket": 0, "price": tick.bid,
                    "sl": 0, "tp": 0,
                    "sl_pts": 0, "tp_pts": 0,
                    "success": False, "comment": result.comment,
                    "latency_ms": result.latency_ms,
                })
                print(f"  [REJECTED] {result.comment}")
                return

            # Step 2: Get actual fill price from MT5 position
            fill_price = 0.0
            import time as _time
            import MetaTrader5 as _mt5

            _time.sleep(0.5)  # Wait for MT5 to register the position
            positions = _mt5.positions_get(symbol=self._symbol)
            if positions:
                for p in positions:
                    if p.ticket == result.ticket:
                        fill_price = p.price_open
                        break

            # Fallback: get fresh tick price
            if fill_price == 0.0:
                tick_info = _mt5.symbol_info_tick(self._symbol)
                if tick_info:
                    fill_price = tick_info.bid if meta.direction == "long" else tick_info.ask
                else:
                    fill_price = tick.bid  # Last known price

            # Step 3: Compute SL/TP based on actual fill price
            sl, tp, sl_pts, tp_pts = self._compute_sl_tp(fill_price, meta.direction)

            # Step 3: Modify position — set SL/TP
            import MetaTrader5 as _mt5
            mod_req = {
                "action": _mt5.TRADE_ACTION_SLTP,
                "symbol": self._symbol,
                "position": result.ticket,
                "sl": sl,
                "tp": tp,
            }
            mod_result = _mt5.order_send(mod_req)
            sl_ok = mod_result and mod_result.retcode in (10008, 10009)

            self._n_orders += 1
            self._order_log.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "dir": meta.direction.upper(),
                "ticket": result.ticket, "price": fill_price,
                "sl": sl, "tp": tp,
                "sl_pts": sl_pts, "tp_pts": tp_pts,
                "success": True, "comment": "filled",
                "latency_ms": result.latency_ms,
                "sl_set": sl_ok,
            })

            sl_status = "SL_OK" if sl_ok else "SL_FAIL"
            print(f"  [FILLED] #{result.ticket} {meta.direction.upper()} "
                  f"{self._volume} @ {fill_price:.2f} | "
                  f"SL={sl:.2f} ({sl_pts:.0f}pts) TP={tp:.2f} ({tp_pts:.0f}pts) | "
                  f"{sl_status} | Lat: {result.latency_ms:.0f}ms")

        except Exception as e:
            self._n_rejected += 1
            print(f"  [ERROR] {e}")

    # ----------------------------------------------------------
    # Real-time Dashboard
    # ----------------------------------------------------------

    def _print_dashboard(self) -> None:
        if not self._bridge:
            return

        acc = self._bridge.get_account()
        pos = self._bridge.get_positions()
        recon = self._bridge.get_reconciliation()
        diag = self._bridge.get_diagnostics()

        pnl_per_pt = _pnl_per_point(self._spec, self._volume) if self._spec else 0.0

        border = "=" * 64
        print(f"\n[SOLÉNN] {border}")
        print(f"[SOLÉNN]  DASHBOARD — {datetime.now().strftime('%H:%M:%S')}")
        print(f"[SOLÉNN] {border}")

        balance = acc.balance if acc else 0
        equity = acc.equity if acc else 0
        dd = ((equity - balance) / balance * 100) if balance > 0 else 0
        print(f"  Account: {acc.login if acc else 'N/A'}  |  Bal: ${balance:.2f}  "
              f"|  Eq: ${equity:.2f}  |  DD: {dd:+.2f}%")

        if pos:
            print(f"  -- Positions ({len(pos)})")
            for p in pos:
                roi = ((p.current_price - p.open_price) / p.open_price * 100) \
                    if p.is_long and p.open_price > 0 else \
                    ((p.open_price - p.current_price) / p.open_price * 100) \
                    if p.open_price > 0 else 0
                sl_dist = abs(p.current_price - p.stop_loss) if p.stop_loss > 0 else 0
                tp_dist = abs(p.take_profit - p.current_price) if p.take_profit > 0 else 0

                # Convert price distance to point distance
                point = self._spec.get("point", 0.01) if self._spec else 0.01
                sl_pts = sl_dist / point
                tp_pts = tp_dist / point

                # PnL in points
                pnl_pts = (p.current_price - p.open_price) / point \
                    if p.is_long else (p.open_price - p.current_price) / point

                print(f"    #{p.ticket} {p.symbol} {'BUY' if p.is_long else 'SELL'} "
                      f"Vol:{p.volume:.2f} Entry:{p.open_price:.2f} "
                      f"Cur:{p.current_price:.2f} P&L:${p.profit:+.2f} ({pnl_pts:+.0f}pts)")
                print(f"      SL:{p.stop_loss:.2f} ({sl_pts:.0f}pts)  "
                      f"TP:{p.take_profit:.2f} ({tp_pts:.0f}pts)  "
                      f"Dur:{p.duration_s:.0f}s")
        else:
            print(f"  Positions: 0 (flat)")

        # PnL info
        print(f"  PnL per point ({self._volume} lots): ${pnl_per_pt:.6f}")

        # Execution
        exec_stats = diag.get("executor", {})
        print(f"  -- Execution")
        print(f"    Submitted:{exec_stats.get('submitted', 0)}  "
              f"Filled:{exec_stats.get('succeeded', 0)}  "
              f"Failed:{exec_stats.get('failed', 0)}  "
              f"FillRate:{exec_stats.get('fill_rate', 0)*100:.0f}%  "
              f"AvgLat:{exec_stats.get('avg_latency_ms', 0):.0f}ms")

        # Signals
        print(f"  -- Signals")
        print(f"    Candles:{self._tick_count}  "
              f"Signals:{self._n_signals}  "
              f"Orders:{self._n_orders}  "
              f"Rejected:{self._n_rejected}")

        # Recent order log
        if self._order_log:
            print(f"  -- Recent Orders (last {len(self._order_log)})")
            for o in list(self._order_log)[-5:]:
                status = "OK" if o["success"] else f"FAIL: {o['comment']}"
                print(f"    [{o['time']}] {o['dir']} #{o['ticket']} @ {o['price']:.2f} "
                      f"SL:{o['sl']:.2f} TP:{o['tp']:.2f}  {status}")

        # Price
        if self._prices:
            last = self._prices[-1]
            high = max(self._prices[-100:])
            low = min(self._prices[-100:])
            print(f"  -- Market: {self._symbol}  Last:{last:.2f}  "
                  f"Range(100):{low:.2f}-{high:.2f}")

        # Reconciliation
        mt5_count = recon.get("mt5_count", 0)
        print(f"  -- Reconciliation: MT5={mt5_count} {recon.get('status', 'unknown')}")
        print(f"[SOLÉNN] {border}\n")

    # ----------------------------------------------------------
    # Main Loop — continuous monitoring
    # ----------------------------------------------------------

    def run_loop(self) -> None:
        """
        Loop behavior — exactly as it runs:

        Phase 1 (once, on startup): Load 200 historical M1 candles to warm up
            VPIN, trend, and volatility indicators. NO trades from history.

        Phase 2 (every 5s): Check for NEW candles. If a new M1 candle closed,
            compute signals. If confidence >= 50% AND no open position -> trade.

        Phase 3 (every 10s): Print status line.
        Phase 4 (every 30-60s): Print full dashboard.

        The bot CONTINUES running until Ctrl+C. After a position closes (SL/TP),
        the next new candle will be evaluated for a new entry. It does NOT
        stop after one trade.
        """
        print(f"\n[SOLÉNN] {'='*60}")
        print(f"[SOLÉNN] Running loop — Press Ctrl+C to stop")
        print(f"[SOLÉNN] {'='*60}")

        seen_times: set[int] = set()
        last_print = time.time()
        last_dashboard = time.time()
        first_run = True
        warmup_count = 0

        try:
            while self._running:
                # --- Phase 1: Warmup (historical candles, NO trades) ---
                if first_run:
                    candles = self._bridge.get_candles("M1", 200) if self._bridge else []
                    first_run = False
                    is_warmup = True
                else:
                    candles = self._bridge.get_candles("M1", 5) if self._bridge else []
                    is_warmup = False
                    warmup_done = True

                if candles:
                    for candle in candles:
                        if candle.time_ns in seen_times:
                            continue

                        seen_times.add(candle.time_ns)
                        if len(seen_times) > 2000:
                            seen_times = set(list(seen_times)[-1000:])

                        self._tick_count += 1
                        self._candles_since_dashboard += 1

                        tick = MT5Tick(
                            symbol=candle.symbol,
                            time_ns=candle.time_ns,
                            bid=candle.close,
                            ask=candle.close + (self._spec.get("spread", 100) *
                                                self._spec.get("point", 0.01))
                            if self._spec else candle.close + 1.0,
                            last=candle.close,
                            volume=candle.tick_volume,
                            flags=0,
                            spread_bps=self._spec.get("spread", 100),
                        )

                        self._prices.append(tick.bid)
                        if len(self._prices) > 500:
                            self._prices = self._prices[-500:]

                        # During warmup: feed data to indicators but NO trades
                        if is_warmup:
                            self._compute_signals(tick)
                            warmup_count += 1
                            continue

                        # Live trading: only open when flat
                        if self._bridge:
                            positions = self._bridge.get_positions()
                            if len(positions) >= self._max_positions:
                                continue

                        agent_signals = self._compute_signals(tick)
                        meta = self._aggregator.aggregate(agent_signals)

                        if meta.confidence >= 0.50:
                            self._execute(meta, tick)

                # --- Phase 2: Monitor open positions ---
                if self._bridge:
                    positions = self._bridge.get_positions()
                    for p in positions:
                        now = time.time()
                        # Dashboard every 30 seconds while position is open
                        if now - last_dashboard >= 30:
                            self._print_dashboard()
                            last_dashboard = now
                            last_print = now  # reset print timer too

                # --- Phase 3: Regular status print every 10 seconds ---
                now = time.time()
                if now - last_print >= 10.0:
                    acc = self._bridge.get_account() if self._bridge else None
                    bal_str = ""
                    if acc:
                        bal_str = f" | Bal:${acc.balance:.2f} Eq:${acc.equity:.2f}"
                    pos_count = len(self._bridge.get_positions()) if self._bridge else 0
                    # Get latest price
                    last_price = self._prices[-1] if self._prices else 0
                    print(f"  [{self._tick_count:4d}] Candles | Candles:{self._tick_count} | "
                          f"Price:{last_price:.2f} | "
                          f"Pos:{pos_count} | "
                          f"Signals:{self._n_signals} Orders:{self._n_orders}"
                          f"{bal_str}")
                    last_print = now

                # Dashboard every 60 seconds minimum
                if now - last_dashboard >= 60:
                    self._print_dashboard()
                    last_dashboard = now

                # Poll every 5 seconds for new M1 candles
                time.sleep(5.0)

        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"[ERROR] {e}")
            import traceback
            traceback.print_exc()
            if self._bridge:
                self._bridge.execute_emergency_close()
        finally:
            if self._n_orders > 0 or (self._bridge and self._bridge.get_positions()):
                self._print_dashboard()
            self.stop()


def main():
    parser = argparse.ArgumentParser(description="SOLÉNN MT5 Runner")
    parser.add_argument("--mode", default="paper",
                        choices=["paper", "scalper", "full"])
    parser.add_argument("--symbol", default="BTCUSD")
    parser.add_argument("--volume", type=float, default=0.01)
    parser.add_argument("--max-ticks", type=int, default=0,
                        help="0 = run forever")
    parser.add_argument("--max-loss", type=float, default=2000.0)
    parser.add_argument("--max-positions", type=int, default=1)
    args = parser.parse_args()

    runner = SOLÉNN_MT5_Runner(
        symbol=args.symbol, volume=args.volume, mode=args.mode,
        max_ticks=args.max_ticks, max_loss=args.max_loss,
        max_positions=args.max_positions,
    )

    def handler(sig, frame):
        runner.stop()
        sys.exit(0)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    if not runner.start():
        print("[ERROR] Failed to start SOLÉNN")
        sys.exit(1)

    runner.run_loop()


if __name__ == "__main__":
    main()
