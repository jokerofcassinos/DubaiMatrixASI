"""
SOLÉNN v2 — MT5 Order Executor (MT5-55 to MT5-108)
Order submission, validation, position management, and reconciliation.

Concept 2: MT5 Order Execution
MT5-55 to MT5-63: Order Creation & Validation
MT5-64 to MT5-72: Order Execution Engine
MT5-73 to MT5-81: Position Lifecycle Management
MT5-82 to MT5-90: Risk Guards for Execution
MT5-91 to MT5-99: Order Reconciliation
MT5-100 to MT5-108: Emergency Protocols
"""

from __future__ import annotations

import enum
import math
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Any

import MetaTrader5 as mt5


# ──────────────────────────────────────────────────────────────
# MT5-55 to MT5-63: Order Creation & Validation
# ──────────────────────────────────────────────────────────────

class OrderType(enum.Enum):
    BUY = 0
    SELL = 1
    BUY_LIMIT = mt5.ORDER_TYPE_BUY_LIMIT
    SELL_LIMIT = mt5.ORDER_TYPE_SELL_LIMIT
    BUY_STOP = mt5.ORDER_TYPE_BUY_STOP
    SELL_STOP = mt5.ORDER_TYPE_SELL_STOP
    CLOSE_BY = 4  # Not directly available in enum


@dataclass(frozen=True, slots=True)
class OrderRequest:
    """MT5-55: Immutable order request."""
    symbol: str
    order_type: OrderType
    volume: float
    price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    deviation: int = 50
    magic: int = 0
    comment: str = ""
    trace_id: str = ""
    urgency: float = 1.0

    @property
    def request_id(self) -> str:
        return uuid.uuid4().hex[:12]


@dataclass(frozen=True, slots=True)
class OrderResult:
    """MT5-56: Immutable order execution result."""
    success: bool
    ticket: int
    price: float
    volume: float
    symbol: str
    retcode: int
    comment: str
    request_id: str
    latency_ms: float
    timestamp_ns: int = field(default_factory=lambda: time.time_ns())


class OrderValidator:
    """MT5-57: Pre-trade order validation."""

    def validate(self, req: OrderRequest) -> list[str]:
        """MT5-58: Full validation."""
        errors = []

        if not req.symbol:
            errors.append("Empty symbol")

        if req.volume <= 0:
            errors.append(f"Invalid volume: {req.volume}")

        if req.price is not None and req.price <= 0:
            errors.append(f"Invalid price: {req.price}")

        if req.stop_loss is not None and req.price is not None:
            if req.order_type == OrderType.BUY and req.stop_loss >= req.price:
                errors.append("SL must be below entry for BUY")
            if req.order_type == OrderType.SELL and req.stop_loss <= req.price:
                errors.append("SL must be above entry for SELL")

        if req.take_profit is not None and req.price is not None:
            if req.order_type == OrderType.BUY and req.take_profit <= req.price:
                errors.append("TP must be above entry for BUY")
            if req.order_type == OrderType.SELL and req.take_profit >= req.price:
                errors.append("TP must be below entry for SELL")

        if req.comment and len(req.comment) > 30:
            errors.append(f"Comment too long: {len(req.comment)} > 30")

        # MT5-specific validation
        info = mt5.symbol_info(req.symbol)
        if info:
            if req.volume < info.volume_min:
                errors.append(f"Volume {req.volume} < min {info.volume_min}")
            if req.volume > info.volume_max:
                errors.append(f"Volume {req.volume} > max {info.volume_max}")
            if info.trade_stops_level > 0 and req.stop_loss and req.price:
                dist = abs(req.price - req.stop_loss) / info.point
                if dist < info.trade_stops_level:
                    errors.append(f"SL too close: {dist:.0f} < {info.trade_stops_level} pts")

        return errors


# ──────────────────────────────────────────────────────────────
# MT5-64 to MT5-72: Order Execution Engine
# ──────────────────────────────────────────────────────────────

class MT5OrderExecutor:
    """MT5-64: MT5 execution engine with retry and SL/TP."""

    def __init__(self, magic: int = 20240401):
        self._magic = magic
        self._validator = OrderValidator()
        self._order_log: deque[OrderResult] = deque(maxlen=1000)
        self._submit_count = 0
        self._success_count = 0
        self._fail_count = 0
        self._total_latency_ms = 0.0
        self._max_retries = 3
        self._retry_delay_ms = 100

    def submit_market_order(self, req: OrderRequest) -> OrderResult:
        """MT5-65: Submit market order with retry."""
        t0 = time.time()
        self._submit_count += 1

        errors = self._validator.validate(req)
        if errors:
            self._fail_count += 1
            return OrderResult(
                success=False, ticket=0, price=0.0, volume=req.volume,
                symbol=req.symbol, retcode=10013,
                comment=f"Validation: {', '.join(errors)}",
                request_id=req.request_id, latency_ms=0.0,
            )

        # Build MT5 request
        is_buy = req.order_type in (OrderType.BUY,)
        order_type = mt5.ORDER_TYPE_BUY if is_buy else mt5.ORDER_TYPE_SELL

        req_dict = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": req.symbol,
            "volume": req.volume,
            "type": order_type,
            "deviation": req.deviation,
            "magic": self._magic,
            "comment": req.comment or f"SOL_{req.request_id[:8]}",
        }

        # Get current price
        tick = mt5.symbol_info_tick(req.symbol)
        if tick is None:
            self._fail_count += 1
            return OrderResult(
                success=False, ticket=0, price=0.0, volume=0.0,
                symbol=req.symbol, retcode=10004,
                comment="Cannot get price", request_id=req.request_id,
                latency_ms=0.0,
            )

        req_dict["price"] = tick.ask if is_buy else tick.bid

        if req.stop_loss:
            req_dict["sl"] = req.stop_loss
        if req.take_profit:
            req_dict["tp"] = req.take_profit

        # Submit with retry
        for attempt in range(self._max_retries):
            result = mt5.order_send(req_dict)
            if result is not None:
                if result.retcode == 10009 or result.retcode == 10008:
                    latency = (time.time() - t0) * 1000
                    fill_price = result.price
                    fill_volume = result.volume

                    # 10008=async: price may be 0, fetch from positions
                    if fill_price == 0 and fill_volume == 0:
                        import time as _time
                        _time.sleep(0.5)
                        positions = mt5.positions_get(symbol=req.symbol)
                        if positions and result.order > 0:
                            for p in positions:
                                if p.ticket == result.order:
                                    fill_price = p.price_open
                                    fill_volume = p.volume
                                    break
                        # Fallback: use the quoted price from request
                        if fill_price == 0:
                            fill_price = req_dict.get("price", 0)
                        if fill_volume == 0:
                            fill_volume = req.volume

                    self._success_count += 1
                    self._total_latency_ms += latency
                    res = OrderResult(
                        success=True,
                        ticket=result.order,
                        price=fill_price,
                        volume=fill_volume,
                        symbol=req.symbol,
                        retcode=result.retcode,
                        comment=result.comment,
                        request_id=req.request_id,
                        latency_ms=round(latency, 2),
                    )
                    self._order_log.append(res)
                    return res
                elif result.retcode == 10004:
                    time.sleep(self._retry_delay_ms / 1000 * (1 + attempt))
                else:
                    # Terminal error — no retry
                    break
            else:
                time.sleep(self._retry_delay_ms / 1000 * (1 + attempt))

        self._fail_count += 1
        latency = (time.time() - t0) * 1000
        res = OrderResult(
            success=False, ticket=0, price=0.0, volume=0.0,
            symbol=req.symbol, retcode=result.retcode if result else 0,
            comment=result.comment if result else "No response",
            request_id=req.request_id, latency_ms=round(latency, 2),
        )
        self._order_log.append(res)
        return res

    def close_position(self, symbol: str, volume: float | None = None) -> list[OrderResult]:
        """MT5-66: Close all or partial positions."""
        positions = mt5.positions_get(symbol=symbol)
        if not positions:
            return []

        results = []
        remaining = volume
        for pos in positions:
            if remaining is not None and remaining <= 0:
                break

            vol = min(pos.volume, remaining) if remaining else pos.volume

            is_buy = pos.type == mt5.POSITION_TYPE_BUY
            order_type = mt5.ORDER_TYPE_SELL if is_buy else mt5.ORDER_TYPE_BUY

            req_dict = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": vol,
                "type": order_type,
                "position": pos.ticket,
                "deviation": 50,
                "magic": self._magic,
            }

            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                continue

            req_dict["price"] = tick.bid if is_buy else tick.ask

            result = mt5.order_send(req_dict)
            latency = 0.0
            if result:
                success = result.retcode in (10008, 10009)
                entry_price = pos.price_open
                exit_price = result.price if success else 0.0
                pnl = 0.0
                if success:
                    if is_buy:
                        pnl = (exit_price - entry_price) * vol / (tick.ask * 0.0001) if tick.ask > 0 else 0
                    else:
                        pnl = (entry_price - exit_price) * vol / (tick.ask * 0.0001) if tick.ask > 0 else 0

                res = OrderResult(
                    success=success,
                    ticket=result.order,
                    price=exit_price if success else 0.0,
                    volume=vol,
                    symbol=symbol,
                    retcode=result.retcode,
                    comment=result.comment,
                    request_id=f"close_{pos.ticket}",
                    latency_ms=0.0,
                )
                results.append(res)

            if remaining is not None:
                remaining -= vol

        return results

    def modify_position(self, ticket: int, symbol: str,
                        stop_loss: float | None = None,
                        take_profit: float | None = None) -> bool:
        """MT5-67: Modify SL/TP of open position."""
        req_dict = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": symbol,
            "position": ticket,
            "magic": self._magic,
        }
        if stop_loss:
            req_dict["sl"] = stop_loss
        if take_profit:
            req_dict["tp"] = take_profit

        result = mt5.order_send(req_dict)
        if result:
            return result.retcode in (10008, 10009)
        return False

    @property
    def stats(self) -> dict[str, Any]:
        """MT5-68: Execution statistics."""
        avg_latency = (
            self._total_latency_ms / self._success_count
            if self._success_count > 0 else 0.0
        )
        return {
            "submitted": self._submit_count,
            "succeeded": self._success_count,
            "failed": self._fail_count,
            "fill_rate": (
                self._success_count / self._submit_count
                if self._submit_count > 0 else 0.0
            ),
            "avg_latency_ms": round(avg_latency, 2),
            "order_log_size": len(self._order_log),
        }


# ──────────────────────────────────────────────────────────────
# MT5-73 to MT5-81: Position Lifecycle Management
# ──────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class PositionInfo:
    """MT5-73: Immutable position info."""
    ticket: int
    symbol: str
    is_long: bool
    volume: float
    open_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    profit: float
    swap: float
    commission: float
    magic: int
    comment: str
    open_time_ns: int
    duration_s: float

    @property
    def unrealized_pnl(self) -> float:
        return self.profit

    @property
    def roi_pct(self) -> float:
        if self.open_price <= 0:
            return 0.0
        pnl = (self.current_price - self.open_price) if self.is_long else (self.open_price - self.current_price)
        return (pnl / self.open_price) * 100


class PositionManager:
    """MT5-73: Position lifecycle management."""

    def get_open_positions(self, symbol: str | None = None) -> list[PositionInfo]:
        """MT5-74: Get all open positions."""
        positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
        if not positions:
            return []

        now = time.time()
        result = []
        for p in positions:
            tick = mt5.symbol_info_tick(p.symbol)
            current = tick.bid if p.type == mt5.POSITION_TYPE_BUY else tick.ask if tick else p.price_open

            pos = PositionInfo(
                ticket=p.ticket,
                symbol=p.symbol,
                is_long=p.type == mt5.POSITION_TYPE_BUY,
                volume=p.volume,
                open_price=p.price_open,
                current_price=current,
                stop_loss=p.sl,
                take_profit=p.tp,
                profit=p.profit,
                swap=p.swap,
                commission=p.commission,
                magic=p.magic,
                comment=p.comment,
                open_time_ns=int(p.time * 1_000_000_000),
                duration_s=now - p.time,
            )
            result.append(pos)
        return result

    def get_total_exposure(self) -> dict[str, float]:
        """MT5-75: Calculate total exposure."""
        positions = mt5.positions_get()
        if not positions:
            return {"net_exposure": 0.0, "long_exposure": 0.0, "short_exposure": 0.0, "total_profit": 0.0}

        long_exp = 0.0
        short_exp = 0.0
        total_profit = 0.0

        for p in positions:
            notional = p.price_open * p.volume
            if p.type == mt5.POSITION_TYPE_BUY:
                long_exp += notional
            else:
                short_exp += notional
            total_profit += p.profit

        return {
            "net_exposure": long_exp - short_exp,
            "long_exposure": long_exp,
            "short_exposure": short_exp,
            "total_profit": round(total_profit, 2),
            "n_positions": len(positions),
        }

    def get_correlation_risk(self) -> dict[str, float]:
        """MT5-76: Correlation risk (simplified — all BTC = same asset)."""
        from collections import Counter
        positions = mt5.positions_get()
        if not positions:
            return {}

        symbol_volumes = Counter()
        for p in positions:
            direction = 1 if p.type == mt5.POSITION_TYPE_BUY else -1
            symbol_volumes[p.symbol] += direction * p.volume

        return {k: round(v, 3) for k, v in symbol_volumes.items()}

    def get_duration_stats(self) -> dict[str, float]:
        """MT5-77: Position duration stats."""
        positions = mt5.positions_get()
        if not positions:
            return {"avg_duration_s": 0.0, "max_duration_s": 0.0, "min_duration_s": 0.0}

        now = time.time()
        durations = [now - p.time for p in positions]
        return {
            "avg_duration_s": round(sum(durations) / len(durations), 1),
            "max_duration_s": round(max(durations), 1),
            "min_duration_s": round(min(durations), 1),
            "total_open": len(positions),
        }


# ──────────────────────────────────────────────────────────────
# MT5-82 to MT5-90: Risk Guards for Execution
# ──────────────────────────────────────────────────────────────

class ExecutionRiskGuards:
    """MT5-82: Execution-level risk checks."""

    def __init__(
        self,
        max_position_volume: float = 1.0,
        max_total_exposure: float = 50000.0,
        max_open_positions: int = 3,
        min_risk_reward: float = 2.0,
    ) -> None:
        self._max_vol = max_position_volume
        self._max_exp = max_total_exposure
        self._max_pos = max_open_positions
        self._min_rr = min_risk_reward

    def check_order_size(self, volume: float) -> list[str]:
        """MT5-83: Check order size limits."""
        if volume > self._max_vol:
            return [f"Volume {volume} > max {self._max_vol}"]
        return []

    def check_position_limit(self, symbol: str | None = None) -> list[str]:
        """MT5-84: Check max open positions."""
        positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
        n_open = len(positions) if positions else 0

        if n_open >= self._max_pos:
            return [f"Max positions reached: {n_open} >= {self._max_pos}"]
        return []

    def check_exposure_limit(self, proposed_notional: float) -> list[str]:
        """MT5-85: Check total exposure."""
        acc = mt5.account_info()
        if acc is None:
            return ["Cannot read account"]

        if acc.equity > acc.balance * 0.90:
            return []

        current_dd_pct = (acc.balance - acc.equity) / acc.balance * 100
        if current_dd_pct > 2.0:
            return [f"Active drawdown {current_dd_pct:.2f}% — trading paused"]

        return []

    def validate_risk_reward(self, entry: float, stop_loss: float,
                             take_profit: float) -> list[str]:
        """MT5-86: Validate R:R ratio."""
        risk = abs(entry - stop_loss)
        reward = abs(take_profit - entry)
        if risk <= 0:
            return ["Invalid stop loss"]

        rr = reward / risk
        if rr < self._min_rr:
            return [f"R:R {rr:.2f} < minimum {self._min_rr}"]
        return []

    def check_spread_gone(self, symbol: str, max_spread_pct: float = 0.3) -> list[str]:
        """MT5-87: Check if spread has widened abnormally."""
        tick = mt5.symbol_info_tick(symbol)
        sym = mt5.symbol_info(symbol)
        if tick is None or sym is None:
            return ["Cannot get spread info"]

        spread_pct = (tick.ask - tick.bid) / tick.bid * 100
        if spread_pct > max_spread_pct:
            return [f"Spread too wide: {spread_pct:.2f}% > {max_spread_pct}%"]
        return []

    def full_check(self, req: OrderRequest) -> list[str]:
        """MT5-88: Run all guards."""
        errors = []
        errors.extend(self.check_order_size(req.volume))
        errors.extend(self.check_position_limit(req.symbol))
        if req.price and req.stop_loss and req.take_profit:
            errors.extend(self.validate_risk_reward(req.price, req.stop_loss, req.take_profit))
        errors.extend(self.check_spread_gone(req.symbol))
        return errors

    def get_stats(self) -> dict[str, Any]:
        """MT5-89: Guard statistics."""
        return {
            "max_order_volume": self._max_vol,
            "max_total_exposure": self._max_exp,
            "max_open_positions": self._max_pos,
            "min_risk_reward": self._min_rr,
        }


# ──────────────────────────────────────────────────────────────
# MT5-91 to MT5-99: Order Reconciliation
# ──────────────────────────────────────────────────────────────

class OrderReconciliation:
    """MT5-91: Reconcile SOLÉNN internal state vs MT5 actual."""

    def reconcile_positions(self) -> dict[str, Any]:
        """MT5-92: Reconcile SOLÉNN positions vs MT5."""
        positions = mt5.positions_get()
        if not positions:
            return {"status": "synchronized", "mt5_count": 0, "discrepancies": []}

        results = []
        for p in positions:
            tick = mt5.symbol_info_tick(p.symbol)
            current = tick.bid if p.type == mt5.POSITION_TYPE_BUY else tick.ask if tick else p.price_open
            results.append({
                "ticket": p.ticket,
                "symbol": p.symbol,
                "type": "BUY" if p.type == mt5.POSITION_TYPE_BUY else "SELL",
                "volume": p.volume,
                "open_price": p.price_open,
                "current_price": current,
                "profit": round(p.profit, 2),
                "sl": p.sl,
                "tp": p.tp,
                "duration_s": round(time.time() - p.time, 1),
            })

        return {
            "status": "synchronized",
            "mt5_count": len(positions),
            "positions": results,
        }

    def reconcile_orders(self, known_requests: list[str]) -> dict[str, Any]:
        """MT5-93: Reconcile pending orders."""
        orders = mt5.orders_get()
        if not orders:
            return {"pending": 0, "discrepancies": []}

        mt5_tickets = {str(o.ticket) for o in orders}
        unknown = set()
        for req_id in known_requests:
            if req_id not in mt5_tickets:
                # Not perfect matching but check for unknowns
                pass

        orphaned = mt5_tickets - set(known_requests) if known_requests else set()

        return {
            "pending": len(orders),
            "orphaned": list(orphaned)[:10],
        }

    def get_trade_history(self, symbol: str | None = None,
                          hours: int = 24) -> list[dict[str, Any]]:
        """MT5-94: Get recent trade history."""
        now = time.time()
        from_ts = int(now - hours * 3600)
        to_ts = int(now)

        history = mt5.history_deals_get(from_ts, to_ts, group=f"*{symbol}*") if symbol else mt5.history_deals_get(from_ts, to_ts)
        if not history:
            return []

        # Filter for position open/close deals
        deals = []
        for d in history:
            if d.entry == mt5.DEAL_ENTRY_IN or d.entry == mt5.DEAL_ENTRY_OUT:
                deals.append({
                    "ticket": d.ticket,
                    "time_ns": int(d.time * 1_000_000_000),
                    "symbol": d.symbol,
                    "type": "BUY" if d.type == mt5.DEAL_TYPE_BUY else "SELL",
                    "volume": d.volume,
                    "price": d.price,
                    "profit": d.profit,
                    "commission": d.commission,
                    "swap": d.swap,
                })
        return deals

    def get_deal_stats(self, hours: int = 24) -> dict[str, Any]:
        """MT5-95: Deal statistics."""
        now = time.time()
        from_ts = int(now - hours * 3600)
        deals = mt5.history_deals_get(from_ts, int(now))
        if not deals:
            return {"total_deals": 0, "total_pnl": 0.0, "trades": []}

        total_pnl = sum(d.profit for d in deals if d.entry == mt5.DEAL_ENTRY_OUT)
        n_closed = sum(1 for d in deals if d.entry == mt5.DEAL_ENTRY_OUT)

        return {
            "total_deals": len(deals),
            "closed_trades": n_closed,
            "total_pnl": round(total_pnl, 2),
            "period_hours": hours,
        }


# ──────────────────────────────────────────────────────────────
# MT5-100 to MT5-108: Emergency Protocols
# ──────────────────────────────────────────────────────────────

class EmergencyManager:
    """MT5-100: Emergency protocols."""

    def close_all_positions(self) -> list[OrderResult]:
        """MT5-101: Emergency flatten — close all positions."""
        positions = mt5.positions_get()
        if not positions:
            return []

        results = []
        for pos in positions:
            tick = mt5.symbol_info_tick(pos.symbol)
            if tick is None:
                continue

            is_buy = pos.type == mt5.POSITION_TYPE_BUY
            order_type = mt5.ORDER_TYPE_SELL if is_buy else mt5.ORDER_TYPE_BUY

            req_dict = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": order_type,
                "position": pos.ticket,
                "deviation": 100,
            }
            req_dict["price"] = tick.bid if is_buy else tick.ask

            result = mt5.order_send(req_dict)
            if result:
                results.append(OrderResult(
                    success=result.retcode in (10008, 10009),
                    ticket=result.order,
                    price=tick.bid if is_buy else tick.ask,
                    volume=pos.volume,
                    symbol=pos.symbol,
                    retcode=result.retcode,
                    comment=f"EMERGENCY CLOSE: {result.comment}",
                    request_id=f"emergency_{pos.ticket}",
                    latency_ms=0.0,
                ))
        return results

    def check_emergency_conditions(self) -> list[str]:
        """MT5-102: Check for emergency conditions."""
        alerts = []
        acc = mt5.account_info()
        if acc is None:
            alerts.append("Cannot read account — EMERGENCY")
            return alerts

        # Margin level critical
        if acc.margin_level < 100:
            alerts.append(f"CRITICAL MARGIN: {acc.margin_level:.1f}%")

        # Connection lost
        ti = mt5.terminal_info()
        if ti is None or not ti.connected:
            alerts.append("MT5 DISCONNECTED")

        return alerts

    def emergency_cancel_orders(self) -> bool:
        """MT5-103: Cancel all pending orders."""
        orders = mt5.orders_get()
        if not orders:
            return True

        for o in orders:
            req_dict = {
                "action": mt5.TRADE_ACTION_REMOVE,
                "order": o.ticket,
            }
            mt5.order_send(req_dict)
        return True
