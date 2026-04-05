"""
SOLÉNN v2 — Health & Monitoring (Ω-D154 a Ω-D162)
Data freshness, connectivity, quality dashboard, alert thresholds,
latency histogram, throughput, memory bounds, error rate, self-healing.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class DataFreshnessReport:
    exchange: str
    symbol: str
    last_valid_tick_ms: float
    current_time_ms: float
    age_ms: float
    is_fresh: bool


@dataclass(frozen=True, slots=True)
class LatencyHistogram:
    p50_ms: float
    p95_ms: float
    p99_ms: float
    count: int


class HealthMonitor:
    """
    Ω-D154 a Ω-D162: Comprehensive data health monitoring.
    """

    def __init__(self, freshness_threshold_ms: float = 5000.0) -> None:
        self._freshness_threshold = freshness_threshold_ms
        self._last_ticks: dict[tuple[str, str], float] = {}
        self._connectivity: dict[str, bool] = {}
        self._latencies: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=1000))
        self._error_counts: dict[str, deque[int]] = defaultdict(lambda: deque(maxlen=100))
        self._throughput: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=100))
        self._alert_thresholds: dict[str, float] = {
            "max_latency_ms": 1000.0,
            "max_error_rate": 0.01,
            "min_freshness_ms": freshness_threshold_ms,
        }
        self._alerts: deque[dict[str, Any]] = deque(maxlen=500)
        self._memory_bytes: int = 0
        self._memory_limit_bytes: int = 500 * 1024 * 1024  # 500 MB

    def record_tick(self, exchange: str, symbol: str, ts_ms: float) -> None:
        """Ω-D154: Record last valid tick timestamp."""
        self._last_ticks[(exchange, symbol)] = ts_ms

    def get_freshness(self) -> list[DataFreshnessReport]:
        """Ω-D155: Check freshness of all data sources."""
        now = time.time() * 1000
        reports = []
        for (exchange, symbol), last_ts in self._last_ticks.items():
            age = now - last_ts
            reports.append(DataFreshnessReport(
                exchange=exchange, symbol=symbol,
                last_valid_tick_ms=last_ts, current_time_ms=now,
                age_ms=age, is_fresh=age < self._freshness_threshold))
        return reports

    def update_connectivity(self, exchange: str, connected: bool) -> None:
        """Ω-D155: Update exchange connectivity status."""
        self._connectivity[exchange] = connected

    def record_latency(self, exchange: str, latency_ms: float) -> None:
        """Ω-D158: Record latency sample."""
        self._latencies[exchange].append(latency_ms)
        if latency_ms > self._alert_thresholds.get("max_latency_ms", 1000):
            self._alerts.append({
                "type": "LATENCY_SPIKE",
                "exchange": exchange,
                "value": latency_ms,
                "timestamp": time.time(),
            })

    def get_latency_histogram(self, exchange: str) -> LatencyHistogram | None:
        """Ω-D159: Latency histogram p50/p95/p99."""
        lats = list(self._latencies.get(exchange, []))
        if not lats:
            return None
        lats.sort()
        n = len(lats)
        return LatencyHistogram(
            p50_ms=lats[n // 2],
            p95_ms=lats[int(n * 0.95)],
            p99_ms=lats[int(n * 0.99)],
            count=n,
        )

    def record_error(self, exchange: str) -> None:
        """Ω-D160: Record error event."""
        window = list(self._error_counts.get(exchange, []))
        current_errors = sum(window)
        self._error_counts[exchange].append(current_errors + 1)

        error_rate = self._error_rate(exchange)
        if error_rate > self._alert_thresholds.get("max_error_rate", 0.01):
            self._alerts.append({
                "type": "HIGH_ERROR_RATE",
                "exchange": exchange,
                "value": error_rate,
                "timestamp": time.time(),
            })

    def _error_rate(self, exchange: str) -> float:
        """Ω-D161: Compute error rate for an exchange."""
        errors = list(self._error_counts.get(exchange, []))
        if not errors:
            return 0.0
        return errors[-1] / max(len(errors), 1)

    def record_throughput(self, exchange: str, ticks_per_second: float) -> None:
        """Ω-D159: Record throughput metric."""
        self._throughput[exchange].append(ticks_per_second)

    def check_alerts(self) -> list[dict[str, Any]]:
        """Ω-D157: Evaluate all alert conditions."""
        freshness = self.get_freshness()
        for report in freshness:
            if not report.is_fresh:
                self._alerts.append({
                    "type": "STALE_DATA",
                    "exchange": report.exchange,
                    "symbol": report.symbol,
                    "age_ms": report.age_ms,
                    "timestamp": time.time(),
                })

        for exchange in self._connectivity:
            if not self._connectivity[exchange]:
                self._alerts.append({
                    "type": "DISCONNECTED",
                    "exchange": exchange,
                    "timestamp": time.time(),
                })
        return list(self._alerts)[-50:]

    def set_memory_usage(self, bytes_used: int) -> None:
        """Ω-D160: Update bounded memory usage."""
        self._memory_bytes = bytes_used
        if bytes_used > self._memory_limit_bytes:
            self._alerts.append({
                "type": "MEMORY_LIMIT_EXCEEDED",
                "current_bytes": bytes_used,
                "limit_bytes": self._memory_limit_bytes,
                "timestamp": time.time(),
            })

    def self_heal(self) -> list[str]:
        """Ω-D162: Auto-recovery actions."""
        actions: list[str] = []

        # Check for stale data sources — flag them
        for (exchange, symbol), last_ts in self._last_ticks.items():
            age = time.time() * 1000 - last_ts
            if age > self._freshness_threshold * 3:
                actions.append(f"RECONNECT: {exchange}/{symbol} stale for {age / 1000:.0f}s")
                del self._last_ticks[(exchange, symbol)]

        # Clear old alerts
        cutoff = time.time() - 3600
        self._alerts = deque(
            [a for a in self._alerts if a.get("timestamp", 0) > cutoff],
            maxlen=500
        )

        return actions

    def dashboard(self) -> dict[str, Any]:
        """Ω-D156: Data quality dashboard."""
        return {
            "freshness": [{"exchange": r.exchange, "symbol": r.symbol, "age_ms": r.age_ms, "fresh": r.is_fresh}
                         for r in self.get_freshness()],
            "connectivity": dict(self._connectivity),
            "latency": {ex: self.get_latency_histogram(ex) for ex in self._latencies},
            "alerts": len(self._alerts),
            "memory_bytes": self._memory_bytes,
            "memory_limit": self._memory_limit_bytes,
        }
