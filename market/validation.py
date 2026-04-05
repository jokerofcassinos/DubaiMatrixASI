"""
SOLÉNN v2 — Data Validation Pipeline (Ω-D118 a Ω-D126)
Range checks, consistency checks, anomaly detection, gap detection,
duplicate detection, outlier classification, MAD robust z-score.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DataQuality(Enum):
    VALID = "valid"
    SUSPECT = "suspect"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class ValidationResult:
    quality: DataQuality
    reasons: tuple[str, ...] = ()
    flagged_fields: tuple[str, ...] = ()

    @property
    def is_valid(self) -> bool:
        return self.quality == DataQuality.VALID


def median_absolute_deviation(values: list[float]) -> tuple[float, float]:
    """Ω-D124: Robust z-score using Median Absolute Deviation."""
    if not values:
        return 0.0, 0.0
    sorted_v = sorted(values)
    n = len(sorted_v)
    median = sorted_v[n // 2] if n % 2 == 1 else (sorted_v[n // 2 - 1] + sorted_v[n // 2]) / 2
    abs_devs = sorted(abs(v - median) for v in values)
    mad = abs_devs[n // 2] if n % 2 == 1 else (abs_devs[n // 2 - 1] + abs_devs[n // 2]) / 2
    return median, mad


def robust_zscore(value: float, median_v: float, mad_v: float) -> float:
    """Compute robust z-score. Returns 0 if MAD is 0."""
    if mad_v == 0:
        return 0.0
    return 0.6745 * (value - median_v) / mad_v


class DataValidator:
    """Ω-D118 a Ω-D126: Validates incoming market data."""

    def __init__(self, vwap: float = 0.0, sigma_threshold: float = 5.0) -> None:
        self._vwap = vwap
        self._sigma_threshold = sigma_threshold
        self._recent_prices: list[float] = []
        self._last_timestamp: int | None = None
        self._seen_keys: set[tuple] = set()
        self._validation_counts: dict[str, int] = {"valid": 0, "suspect": 0, "invalid": 0}

    def set_vwap(self, vwap: float) -> None:
        self._vwap = vwap

    def validate_tick(self, exchange: str, symbol: str, price: float,
                      quantity: float, bid: float | None, ask: float | None,
                      timestamp_ns: int) -> ValidationResult:
        reasons: list[str] = []
        flagged: list[str] = []

        # Ω-D118: Range check — price within ±50% of VWAP
        if self._vwap > 0 and (price < self._vwap * 0.5 or price > self._vwap * 1.5):
            reasons.append(f"Price {price} outside ±50% of VWAP {self._vwap}")
            flagged.append("price")

        # Price must be positive
        if price <= 0:
            reasons.append("Price must be > 0")
            flagged.append("price")

        # Quantity must be non-negative
        if quantity < 0:
            reasons.append("Quantity must be >= 0")
            flagged.append("quantity")

        # Ω-D119: Consistency — bid < ask
        if bid is not None and ask is not None and bid >= ask:
            reasons.append(f"Bid {bid} >= Ask {ask} (crossed book)")
            flagged.append("bid_ask")

        # Price should be within bid-ask spread
        if bid is not None and ask is not None:
            if price < bid * 0.99 or price > ask * 1.01:
                reasons.append(f"Price {price} outside bid-ask range [{bid}, {ask}]")
                flagged.append("price")

        # Ω-D120: Anomaly — price spike > 5σ
        self._recent_prices.append(price)
        if len(self._recent_prices) > 100:
            self._recent_prices = self._recent_prices[-100:]
        if len(self._recent_prices) >= 30:
            med, mad = median_absolute_deviation(self._recent_prices)
            z = robust_zscore(price, med, mad)
            if abs(z) > self._sigma_threshold:
                reasons.append(f"Price spike: z-score={z:.1f} > threshold {self._sigma_threshold}")
                flagged.append("price_spike")

        # Ω-D121: Gap detection — timestamp must be monotonically increasing
        if self._last_timestamp is not None and timestamp_ns < self._last_timestamp:
            reasons.append(f"Timestamp {timestamp_ns} < last {self._last_timestamp} (non-monotonic)")
            flagged.append("timestamp")
        self._last_timestamp = timestamp_ns

        # Ω-D122: Duplicate detection
        key = (exchange, symbol, timestamp_ns, price, quantity)
        if key in self._seen_keys:
            reasons.append(f"Duplicate tick detected")
            flagged.append("duplicate")
        self._seen_keys.add(key)
        if len(self._seen_keys) > 100000:
            self._seen_keys = set(list(self._seen_keys)[-50000:])

        # Determine quality
        if len(reasons) == 0:
            quality = DataQuality.VALID
            self._validation_counts["valid"] += 1
        elif any(f in ("price", "quantity", "timestamp") for f in flagged):
            quality = DataQuality.INVALID
            self._validation_counts["invalid"] += 1
        else:
            quality = DataQuality.SUSPECT
            self._validation_counts["suspect"] += 1

        return ValidationResult(quality=quality, reasons=tuple(reasons), flagged_fields=tuple(flagged))

    def quality_score(self) -> float:
        """Ω-D126: Data quality score = valid / total."""
        total = sum(self._validation_counts.values())
        if total == 0:
            return 1.0
        return self._validation_counts["valid"] / total

    def get_stats(self) -> dict[str, int]:
        return dict(self._validation_counts)
