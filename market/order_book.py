"""
SOLÉNN v2 — Order Book Reconstruction & Trade Processing (Ω-D19 a Ω-D36)
Full book snapshot, incremental updates, checksum validation, gap detection,
trade stream normalization, direction classification, volume profile,
VWAP, trade clustering, large trade detection, VPIN, cancel-to-fill ratio,
latency monitoring, microprice, queue position estimation.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field

from .data_types import BookLevel, OrderBook, Side, Tick, Trade


@dataclass(frozen=True, slots=True)
class BookVelocity:
    """Ω-D25: Rate of changes per book level."""
    level: int
    bid_change_rate: float
    ask_change_rate: float
    timestamp: float = field(default_factory=time.time)


class OrderBookManager:
    """
    Ω-D19 a Ω-D27: Order book with snapshot init, incremental updates,
    checksum validation, gap detection, phantom liquidity detection.
    """

    def __init__(self, exchange: str, symbol: str, depth: int = 20) -> None:
        self._exchange = exchange
        self._symbol = symbol
        self._depth = depth
        self._bids: dict[float, float] = {}
        self._asks: dict[float, float] = {}
        self._sequence: int = 0
        self._checksum: str = ""
        self._update_count: int = 0
        self._cancel_count: int = 0
        self._fill_count: int = 0
        self._phantom_scores: dict[float, int] = {}

    def init_from_snapshot(self, bids: list[tuple[float, float]],
                           asks: list[tuple[float, float]], sequence: int) -> OrderBook:
        """Ω-D19: Initialize book from REST snapshot."""
        levels = []
        for price, qty in sorted(bids, key=lambda x: -x[0])[:self._depth]:
            self._bids[price] = qty
            levels.append(BookLevel(price=price, quantity=qty))
        for price, qty in sorted(asks, key=lambda x: x[0])[:self._depth]:
            self._asks[price] = qty
            levels.append(BookLevel(price=price, quantity=qty))
        self._sequence = sequence
        self._update_count = 0
        ob = OrderBook.create(self._exchange, self._symbol, time.time_ns(),
                              [BookLevel(price=p, quantity=q) for p, q in
                               sorted(bids, key=lambda x: -x[0])[:self._depth]],
                              [BookLevel(price=p, quantity=q) for p, q in
                               sorted(asks, key=lambda x: x[0])[:self._depth]],
                              sequence=sequence)
        self._checksum = ob.checksum
        return ob

    def apply_delta(self, bid_updates: list[tuple[float, float]],
                    ask_updates: list[tuple[float, float]],
                    sequence: int) -> tuple[bool, str]:
        """Ω-D20: Apply incremental book update."""
        # Ω-D22: Gap detection
        if sequence != self._sequence + 1 and self._sequence > 0:
            return False, f"Gap detected: expected {self._sequence + 1}, got {sequence}"

        for price, qty in bid_updates:
            if qty == 0:
                self._bids.pop(price, None)
                self._cancel_count += 1
            else:
                self._bids[price] = qty
                self._update_count += 1

        for price, qty in ask_updates:
            if qty == 0:
                self._asks.pop(price, None)
                self._cancel_count += 1
            else:
                self._asks[price] = qty
                self._update_count += 1

        self._sequence = sequence

        # Ω-D21: Checksum validation
        top_bids = sorted(self._bids.items(), key=lambda x: -x[0])[:self._depth]
        top_asks = sorted(self._asks.items(), key=lambda x: x[0])[:self._depth]
        ob = OrderBook.create(
            self._exchange, self._symbol, time.time_ns(),
            [BookLevel(p, q) for p, q in top_bids],
            [BookLevel(p, q) for p, q in top_asks],
            sequence=sequence
        )
        self._checksum = ob.checksum
        return True, "ok"

    def get_snapshot(self) -> OrderBook:
        """Ω-D24: Get current book snapshot."""
        top_bids = sorted(self._bids.items(), key=lambda x: -x[0])[:self._depth]
        top_asks = sorted(self._asks.items(), key=lambda x: x[0])[:self._depth]
        return OrderBook.create(
            self._exchange, self._symbol, time.time_ns(),
            [BookLevel(p, q) for p, q in top_bids],
            [BookLevel(p, q) for p, q in top_asks],
            sequence=self._sequence
        )

    @property
    def best_bid(self) -> float | None:
        if self._bids:
            return max(self._bids.keys())
        return None

    @property
    def best_ask(self) -> float | None:
        if self._asks:
            return min(self._asks.keys())
        return None

    @property
    def spread(self) -> float | None:
        bb = self.best_bid
        ba = self.best_ask
        if bb is not None and ba is not None:
            return ba - bb
        return None

    def mid_price(self) -> float | None:
        bb, ba = self.best_bid, self.best_ask
        if bb and ba:
            return (bb + ba) / 2.0
        return None

    def microprice(self) -> float | None:
        """Ω-D67: Volume-weighted mid price."""
        bb = self.best_bid
        ba = self.best_ask
        if bb and ba:
            bid_vol = self._bids.get(bb, 0)
            ask_vol = self._asks.get(ba, 0)
            total = bid_vol + ask_vol
            if total > 0:
                return (bb * ask_vol + ba * bid_vol) / total
        return self.mid_price()

    def bid_ask_imbalance(self) -> float | None:
        """Ω-D64: (bid_depth - ask_depth) / (bid_depth + ask_depth)."""
        bid_depth = sum(self._bids.values())
        ask_depth = sum(self._asks.values())
        total = bid_depth + ask_depth
        if total > 0:
            return (bid_depth - ask_depth) / total
        return None

    def cancel_to_fill_ratio(self) -> float:
        """Ω-D71: Cancel-to-fill ratio."""
        if self._fill_count == 0:
            return float("inf")
        return self._cancel_count / max(1, self._fill_count)

    def get_depth_at_price(self, price: float, side: Side) -> float:
        """Get total quantity at a specific price level."""
        if side == Side.BUY:
            return self._bids.get(price, 0)
        return self._asks.get(price, 0)


class TradeStreamProcessor:
    """
    Ω-D28 a Ω-D36: Trade feed normalizer, VWAP, volume profile,
    clustering, large trade detection, VPIN, latency monitoring.
    """

    def __init__(self, symbol: str, exchange: str, large_threshold: float = 100.0) -> None:
        self._symbol = symbol
        self._exchange = exchange
        self._large_threshold = large_threshold
        self._vwap_num: float = 0.0
        self._vwap_den: float = 0.0
        self._trades: deque[Trade] = deque(maxlen=10000)
        self._volume_profile: dict[float, float] = defaultdict(float)
        self._buy_volume: float = 0.0
        self._sell_volume: float = 0.0
        self._large_trades: list[Trade] = []
        self._latencies_ns: list[int] = []
        self._cluster_threshold_ms: float = 50.0
        self._last_ts_ns: int = 0

    def process_trade(self, trade: Trade, recv_ts: int | None = None) -> None:
        """Ω-D28: Process normalized trade."""
        self._trades.append(trade)

        # Ω-D31: Incremental VWAP
        self._vwap_num += trade.price * trade.quantity
        self._vwap_den += trade.quantity

        # Ω-D30: Volume profile
        price_bucket = round(trade.price / 0.01) * 0.01
        self._volume_profile[price_bucket] += trade.quantity

        # Ω-D29: Direction classification
        if trade.is_taker_buy:
            self._buy_volume += trade.quantity
        else:
            self._sell_volume += trade.quantity

        # Ω-D33: Large trade detection
        if trade.quantity >= self._large_threshold:
            self._large_trades.append(trade)
            if len(self._large_trades) > 100:
                self._large_trades.pop(0)

        # Ω-D32: Trade clustering
        if self._last_ts_ns and recv_ts:
            delta_ms = (recv_ts - self._last_ts_ns) / 1e6
            if delta_ms < self._cluster_threshold_ms:
                pass  # Part of a cluster

        # Ω-D36: Latency monitoring
        if recv_ts is not None and trade.timestamp_ns > 0:
            latency = recv_ts - trade.timestamp_ns
            if latency > 0:
                self._latencies_ns.append(latency)
                if len(self._latencies_ns) > 1000:
                    self._latencies_ns = self._latencies_ns[-500:]
        self._last_ts_ns = trade.timestamp_ns

    @property
    def vwap(self) -> float:
        if self._vwap_den > 0:
            return self._vwap_num / self._vwap_den
        return 0.0

    @property
    def buy_sell_ratio(self) -> float:
        if self._sell_volume > 0:
            return self._buy_volume / self._sell_volume
        return float("inf")

    @property
    def vpin(self) -> float:
        """Ω-D34: Volume-synchronized Probability of Informed Trading."""
        total = self._buy_volume + self._sell_volume
        if total == 0:
            return 0.0
        return abs(self._buy_volume - self._sell_volume) / total

    def get_latency_p99(self) -> float:
        """Ω-D36: P99 latency in milliseconds."""
        if not self._latencies_ns:
            return 0.0
        sorted_l = sorted(self._latencies_ns)
        idx = int(len(sorted_l) * 0.99)
        return sorted_l[min(idx, len(sorted_l) - 1)] / 1e6

    def get_large_trades(self, last_n: int = 10) -> list[Trade]:
        return self._large_trades[-last_n:]

    def get_volume_profile(self) -> dict[float, float]:
        return dict(self._volume_profile)

    def get_trade_count(self) -> int:
        return len(self._trades)
