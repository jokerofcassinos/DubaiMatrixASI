"""
SOLÉNN v2 — Market Intelligence Hub (Ω-MI01 a Ω-MI54)
Replaces v1 macro_scraper.py, onchain_scraper.py, sentiment_scraper.py,
narrative_distiller.py, nexus_resonance.py, and mt5_bridge.py.

Pure-Python multi-intelligence orchestration: macroeconomic scoring,
on-chain metrics, sentiment analysis, narrative distillation, cross-asset
resonance detection, and master hub coordination.

Concept 1: MacroCalendar & Economic Event Scoring (Ω-MI01–MI18)
  Tracks and scores economic calendar events (FOMC, CPI, NFP, PMI,
  GDP, rate decisions, etc.). Each event has impact scoring, historical
  deviation analysis, and timing windows. Impact propagation model
  estimates effect on crypto with configurable delay distributions.

Concept 2: OnChainMetrics & SentimentMetrics (Ω-MI19–MI36)
  Exchange flow tracking, whale movement detection, miner flow analysis,
  Fear & Greed indices, social volume, put/call ratios — all combined
  into composite scores that feed the decision engine.

Concept 3: NarrativeDistiller, NexusResonance & IntelligenceHub (Ω-MI37–MI54)
  Distills macro narratives from multiple feeds, detects cross-asset
  resonance patterns, and orchestrates all intelligence sources through
  a master hub with health monitoring, fallback handling, and priority
  scoring.
"""

from __future__ import annotations

import math
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


# ──────────────────────────────────────────────────────────────
# Ω-MI01 to Ω-MI18: MacroCalendar & Economic Event Scoring
# ──────────────────────────────────────────────────────────────


class ImpactLevel(Enum):
    """Ω-MI01: Economic event impact severity."""
    NEGLIGIBLE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class EventType(Enum):
    """Ω-MI02: Categories of economic events."""
    INTEREST_RATE = "interest_rate"
    CPI = "cpi"
    PPI = "ppi"
    NFP = "nonfarm_payrolls"
    GDP = "gdp"
    PMI = "pmi"
    RETAIL_SALES = "retail_sales"
    UNEMPLOYMENT = "unemployment"
    FOMC_MINUTES = "fomc_minutes"
    FED_SPEECH = "fed_speech"
    TREASURY_AUCTION = "treasury_auction"
    HOUSING_DATA = "housing_data"
    CONSUMER_CONFIDENCE = "consumer_confidence"
    ISM_MANUFACTURING = "ism_manufacturing"
    TRADE_BALANCE = "trade_balance"
    JOLTS = "jolts"
    PCE_DEFLATOR = "pce_deflator"
    MACRO_OTHER = "other"


@dataclass(frozen=True)
class MacroEvent:
    """Ω-MI03: Immutable economic calendar event with scoring."""

    event_id: str
    event_type: EventType
    title: str
    timestamp_ns: int
    scheduled_ns: int
    impact: ImpactLevel
    country: str
    currency: str
    forecast: float | None = None
    previous: float | None = None
    actual: float | None = None
    surprise: float = 0.0  # actual - forecast
    surprise_score: float = 0.0  # normalized -1.0 to +1.0
    resolved: bool = False
    crypto_correlation: float = 0.0  # Historical correlation with BTC
    propagation_delay_min: int = 30  # Minutes until full effect on crypto
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "title": self.title,
            "impact": self.impact.name,
            "country": self.country,
            "currency": self.currency,
            "forecast": self.forecast,
            "previous": self.previous,
            "actual": self.actual,
            "surprise": self.surprise,
            "surprise_score": self.surprise_score,
            "resolved": self.resolved,
            "crypto_correlation": self.crypto_correlation,
            "propagation_delay_min": self.propagation_delay_min,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class EventImpactScore:
    """Ω-MI04: Computed impact score from a resolved macro event."""

    event_id: str
    direction: float  # -1.0 (bearish) to +1.0 (bullish) for BTC
    magnitude: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    time_to_peak_effect_min: int
    time_to_decay_min: int
    affected_channels: list[str]  # e.g. ["liquidity", "correlation", "risk_appetite"]


class MacroCalendar:
    """
    Ω-MI05: Tracks, scores, and forecasts impact of economic events.

    Maintains a rolling window of past events with outcomes, upcoming
    events from known schedules, and computes impact propagation
    models for BTC/crypto correlation.

    The calendar auto-resolves events when actuals are posted and
    generates impact scores that feed the decision engine.
    """

    # Default crypto correlation by event type (empirically derived)
    _DEFAULT_CRYPTO_CORR: dict[EventType, float] = {
        EventType.INTEREST_RATE: 0.75,
        EventType.CPI: 0.70,
        EventType.NFP: 0.60,
        EventType.GDP: 0.50,
        EventType.PMI: 0.45,
        EventType.RETAIL_SALES: 0.40,
        EventType.UNEMPLOYMENT: 0.50,
        EventType.FOMC_MINUTES: 0.65,
        EventType.FED_SPEECH: 0.55,
        EventType.TREASURY_AUCTION: 0.35,
        EventType.HOUSING_DATA: 0.25,
        EventType.CONSUMER_CONFIDENCE: 0.30,
        EventType.ISM_MANUFACTURING: 0.35,
        EventType.TRADE_BALANCE: 0.20,
        EventType.JOLTS: 0.40,
        EventType.PCE_DEFLATOR: 0.65,
        EventType.MACRO_OTHER: 0.10,
    }

    _DEFAULT_IMPACT: dict[EventType, ImpactLevel] = {
        EventType.INTEREST_RATE: ImpactLevel.CRITICAL,
        EventType.CPI: ImpactLevel.CRITICAL,
        EventType.NFP: ImpactLevel.HIGH,
        EventType.GDP: ImpactLevel.HIGH,
        EventType.PMI: ImpactLevel.MEDIUM,
        EventType.RETAIL_SALES: ImpactLevel.MEDIUM,
        EventType.UNEMPLOYMENT: ImpactLevel.MEDIUM,
        EventType.FOMC_MINUTES: ImpactLevel.HIGH,
        EventType.FED_SPEECH: ImpactLevel.MEDIUM,
        EventType.TREASURY_AUCTION: ImpactLevel.LOW,
        EventType.HOUSING_DATA: ImpactLevel.LOW,
        EventType.CONSUMER_CONFIDENCE: ImpactLevel.LOW,
        EventType.ISM_MANUFACTURING: ImpactLevel.LOW,
        EventType.TRADE_BALANCE: ImpactLevel.LOW,
        EventType.JOLTS: ImpactLevel.MEDIUM,
        EventType.PCE_DEFLATOR: ImpactLevel.HIGH,
        EventType.MACRO_OTHER: ImpactLevel.LOW,
    }

    def __init__(self, history_window: int = 500) -> None:
        self._events: dict[str, MacroEvent] = {}
        self._upcoming: list[str] = []  # event_ids
        self._resolved: deque[MacroEvent] = deque(maxlen=history_window)
        self._impact_history: deque[EventImpactScore] = deque(maxlen=1000)
        self._last_update_ns: int = 0
        self._update_interval_ns: int = 60 * 1_000_000_000  # 1 minute
        self._event_schedules: dict[str, dict[str, Any]] = {}

    def add_event(
        self,
        event_type: EventType,
        title: str,
        scheduled_dt: datetime,
        forecast: float | None = None,
        previous: float | None = None,
        country: str = "US",
        currency: str = "USD",
        impact: ImpactLevel | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MacroEvent:
        """Ω-MI06: Add an economic event to the calendar."""
        eid = f"macro_{uuid.uuid4().hex[:8]}"
        scheduled_ns = int(scheduled_dt.timestamp() * 1e9)
        event = MacroEvent(
            event_id=eid,
            event_type=event_type,
            title=title,
            timestamp_ns=scheduled_ns,
            scheduled_ns=scheduled_ns,
            impact=impact or self._DEFAULT_IMPACT.get(event_type, ImpactLevel.LOW),
            country=country,
            currency=currency,
            forecast=forecast,
            previous=previous,
            crypto_correlation=self._DEFAULT_CRYPTO_CORR.get(event_type, 0.3),
            metadata=metadata or {},
        )
        self._events[eid] = event
        self._upcoming.append(eid)
        return event

    def resolve_event(
        self,
        event_id: str,
        actual: float,
        timestamp_ns: int | None = None,
    ) -> EventImpactScore | None:
        """Ω-MI07: Post actual value for a scheduled event and compute impact."""
        event = self._events.get(event_id)
        if event is None:
            return None

        surprise = actual
        if event.forecast is not None:
            surprise = actual - event.forecast
        elif event.previous is not None:
            surprise = actual - event.previous

        # Compute surprise score: normalize by forecast or previous magnitude
        baseline = abs(event.forecast) if event.forecast is not None else (abs(event.previous) if event.previous is not None else 1.0)
        surprise_pct = surprise / max(baseline, 1e-9)
        surprise_score = max(-1.0, min(1.0, surprise_pct))

        resolved_event = MacroEvent(
            event_id=event.event_id,
            event_type=event.event_type,
            title=event.title,
            timestamp_ns=timestamp_ns or time.time_ns(),
            scheduled_ns=event.scheduled_ns,
            impact=event.impact,
            country=event.country,
            currency=event.currency,
            forecast=event.forecast,
            previous=event.previous,
            actual=actual,
            surprise=surprise,
            surprise_score=surprise_score,
            resolved=True,
            crypto_correlation=event.crypto_correlation,
            propagation_delay_min=event.propagation_delay_min,
            metadata=event.metadata,
        )

        self._events[event_id] = resolved_event
        self._resolved.append(resolved_event)

        # Remove from upcoming
        if event_id in self._upcoming:
            self._upcoming.remove(event_id)

        # Compute and store impact score
        impact_score = self._compute_impact(resolved_event)
        if impact_score is not None:
            self._impact_history.append(impact_score)

        return impact_score

    def _compute_impact(self, event: MacroEvent) -> EventImpactScore | None:
        """Ω-MI08: Compute impact score from a resolved event."""
        if not event.resolved:
            return None

        # Direction: positive surprise = typically bearish for BTC (strong USD)
        # Except when it signals recession fear
        is_rate_event = event.event_type in (EventType.INTEREST_RATE, EventType.CPI, EventType.PCE_DEFLATOR)

        if is_rate_event:
            # Higher rates/CPI → hawkish Fed → bearish BTC
            direction = -event.surprise_score
        elif event.event_type in (EventType.GDP, EventType.ISM_MANUFACTURING):
            # Strong economy → risk-on → bullish BTC (usually)
            direction = event.surprise_score * 0.3  # Lower magnitude
        elif event.event_type in (EventType.NFP, EventType.UNEMPLOYMENT, EventType.JOLTS):
            # Strong labor → hawkish → bearish BTC
            nfp_mult = -1.0 if event.event_type == EventType.NFP else 1.0
            direction = event.surprise_score * nfp_mult * 0.5
        else:
            direction = event.surprise_score * 0.2  # Default: mild correlation

        # Magnitude: scaled by surprise and base impact
        magnitude = abs(event.surprise_score) * (event.impact.value / ImpactLevel.CRITICAL.value)

        # Confidence: proportional to event's historical correlation with crypto
        confidence = magnitude * min(1.0, event.crypto_correlation * 1.5)

        time_to_peak = event.propagation_delay_min
        time_to_decay = event.propagation_delay_min * 3  # Effect lasts ~3x propagation time

        channels: list[str] = []
        if is_rate_event:
            channels.extend(["risk_appetite", "dxy_correlation", "liquidity"])
        elif event.event_type in (EventType.NFP, EventType.GDP):
            channels.extend(["risk_appetite", "growth_outlook"])
        else:
            channels.append("secondary")

        return EventImpactScore(
            event_id=event.event_id,
            direction=round(direction, 4),
            magnitude=round(magnitude, 4),
            confidence=round(confidence, 4),
            time_to_peak_effect_min=time_to_peak,
            time_to_decay_min=time_to_decay,
            affected_channels=channels,
        )

    def get_active_impacts(self, current_ns: int | None = None) -> list[EventImpactScore]:
        """Ω-MI09: Get currently active macro impacts."""
        now = current_ns or time.time_ns()
        active: list[EventImpactScore] = []

        for impact in self._impact_history:
            # Impact is active if within decay window
            event = self._events.get(impact.event_id)
            if event is not None and event.resolved:
                event_time_ns = event.timestamp_ns
                decay_ns = impact.time_to_decay_min * 60 * 1e9
                if now - event_time_ns < decay_ns:
                    active.append(impact)

        return active

    def compute_macro_bias(self) -> float:
        """
        Ω-MI10: Net macroeconomic bias for BTC [-1.0 to +1.0].
        Weighted sum of all active impacts.
        """
        active = self.get_active_impacts()
        if not active:
            return 0.0

        weighted_bias = 0.0
        total_weight = 0.0

        for impact in active:
            # Time decay: effects are strongest near peak, weaker near end
            event = self._events.get(impact.event_id)
            if event is None:
                continue
            now = time.time_ns()
            elapsed_ns = now - event.timestamp_ns
            peak_ns = impact.time_to_peak_effect_min * 60 * 1e9
            decay_ns = impact.time_to_decay_min * 60 * 1e9

            # Gaussian-like time weighting
            time_weight = math.exp(-0.5 * ((elapsed_ns - peak_ns) / (decay_ns * 0.3)) ** 2)
            w = impact.confidence * time_weight
            weighted_bias += impact.direction * w
            total_weight += w

        if total_weight == 0:
            return 0.0

        return max(-1.0, min(1.0, round(weighted_bias / total_weight, 4)))

    def get_upcoming_events(self, look_ahead_min: int = 120) -> list[MacroEvent]:
        """Ω-MI11: Get events scheduled in the next N minutes."""
        now_ns = time.time_ns()
        cutoff_ns = now_ns + look_ahead_min * 60 * 1e9
        upcoming: list[MacroEvent] = []

        for eid in self._upcoming:
            event = self._events.get(eid)
            if event is not None and event.scheduled_ns <= cutoff_ns and not event.resolved:
                upcoming.append(event)

        upcoming.sort(key=lambda e: e.scheduled_ns)
        return upcoming

    def get_event_history(self, n: int = 20) -> list[MacroEvent]:
        """Ω-MI12: Get most recently resolved events."""
        return list(self._resolved)[-n:]

    def get_impact_history(self, n: int = 50) -> list[EventImpactScore]:
        """Ω-MI13: Get recent impact scores."""
        return list(self._impact_history)[-n:]

    def event_risk_assessment(self) -> dict[str, Any]:
        """Ω-MI14: Assess macro risk for next 24h."""
        upcoming = self.get_upcoming_events(look_ahead_min=24 * 60)
        critical_count = sum(1 for e in upcoming if e.impact == ImpactLevel.CRITICAL)
        high_count = sum(1 for e in upcoming if e.impact == ImpactLevel.HIGH)

        risk_score = min(1.0, (critical_count * 0.5 + high_count * 0.25))

        # Check if any event is within the next 15 minutes (quiet period broken)
        now_ns = time.time_ns()
        imminent = [e for e in upcoming if 0 <= (e.scheduled_ns - now_ns) <= 15 * 60 * 1e9]

        return {
            "risk_score": round(risk_score, 4),
            "critical_events": critical_count,
            "high_impact_events": high_count,
            "total_upcoming_24h": len(upcoming),
            "imminent_events": len(imminent),
            "macro_bias": self.compute_macro_bias(),
            "imminent_titles": [e.title for e in imminent],
        }

    def get_event_stats(self) -> dict[str, Any]:
        """Ω-MI15: Statistics of all tracked events."""
        total = len(self._events)
        resolved = sum(1 for e in self._events.values() if e.resolved)
        upcoming = len(self._upcoming)

        avg_surprise = 0.0
        if resolved > 0:
            avg_surprise = sum(
                e.surprise for e in self._events.values() if e.resolved and e.surprise != 0
            ) / max(1, sum(1 for e in self._events.values() if e.resolved and e.surprise != 0))

        return {
            "total_tracked": total,
            "resolved": resolved,
            "upcoming": upcoming,
            "impact_scores_recorded": len(self._impact_history),
            "avg_surprise": round(avg_surprise, 6),
            "current_macro_bias": self.compute_macro_bias(),
        }

    def clear_expired(self) -> int:
        """Ω-MI16: Remove expired events (past + decay window) from active tracking."""
        now_ns = time.time_ns()
        cleared = 0
        expired_ids: list[str] = []

        for eid, event in self._events.items():
            if not event.resolved:
                if now_ns > event.scheduled_ns + 24 * 60 * 60 * 1e9:
                    expired_ids.append(eid)
            else:
                impact = next((i for i in self._impact_history if i.event_id == eid), None)
                if impact is not None:
                    decay_ns = impact.time_to_decay_min * 60 * 1e9
                    if now_ns - event.timestamp_ns > decay_ns * 2:
                        expired_ids.append(eid)

        for eid in expired_ids:
            del self._events[eid]
            if eid in self._upcoming:
                self._upcoming.remove(eid)
            cleared += 1

        return cleared

    def health(self) -> dict[str, Any]:
        """Ω-MI17: Health of the macro calendar."""
        stats = self.get_event_stats()
        risk = self.event_risk_assessment()
        return {
            **stats,
            "risk_assessment": risk,
        }

    def reset(self) -> None:
        """Ω-MI18: Clear all macro calendar data."""
        self._events.clear()
        self._upcoming.clear()
        self._resolved.clear()
        self._impact_history.clear()


# ──────────────────────────────────────────────────────────────
# Ω-MI19 to Ω-MI36: OnChainMetrics & SentimentMetrics
# ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class OnChainMetrics:
    """
    Ω-MI19: Immutable snapshot of blockchain network metrics.
    Captures exchange flows, whale movements, miner flows,
    and network health indicators.
    """

    timestamp_ns: int
    hash_rate_th_s: float = 0.0
    difficulty: float = 0.0
    mempool_count: int = 0
    mempool_bytes: int = 0
    avg_fee_sat: float = 0.0
    blocks_24h: int = 0
    avg_block_time_s: float = 600.0
    exchange_inflow_btc: float = 0.0
    exchange_outflow_btc: float = 0.0
    net_exchange_flow_btc: float = 0.0
    whale_tx_count_24h: int = 0
    whale_volume_btc_24h: float = 0.0
    miner_outflow_btc: float = 0.0
    stablecoin_supply_change_24h: float = 0.0
    exchange_reserve_btc: float = 0.0
    long_term_holder_supply: float = 0.0
    short_term_holder_supply: float = 0.0
    network_health: float = 0.5
    sop_r: float = 1.0  # Spent Output Profitability Ratio
    mvrv_ratio: float = 1.0  # Market Value to Realized Value
    sources_active: int = 0

    @property
    def network_pressure(self) -> float:
        """
        Ω-MI20: Composite network pressure score [-1.0 to +1.0].
        Positive = selling pressure. Negative = accumulation pressure.
        """
        pressure = 0.0

        # Exchange flow pressure
        if self.net_exchange_flow_btc > 0:
            pressure += min(0.4, self.net_exchange_flow_btc / 5000.0)
        elif self.net_exchange_flow_btc < 0:
            pressure -= min(0.4, abs(self.net_exchange_flow_btc) / 5000.0)

        # Miner flow pressure (miner selling = bearish)
        if self.miner_outflow_btc > 100:
            pressure += min(0.2, self.miner_outflow_btc / 500.0)

        # Whale activity
        if self.whale_volume_btc_24h > 10000:
            pressure += 0.1  # Whale selling

        # Stablecoin supply (increasing = bullish — dry powder incoming)
        if self.stablecoin_supply_change_24h > 1e9:  # > $1B added
            pressure -= 0.15
        elif self.stablecoin_supply_change_24h < -1e9:
            pressure += 0.1

        # MVRV ratio
        if self.mvrv_ratio > 3.0:
            pressure += 0.15  # Overvalued — sell pressure
        elif self.mvrv_ratio < 0.8:
            pressure -= 0.15  # Undervalued — buy pressure

        return max(-1.0, min(1.0, pressure))

    @property
    def health_score(self) -> float:
        """Ω-MI21: Network health composite [0.0 to 1.0]."""
        health = 0.5

        if self.hash_rate_th_s > 0:
            health += 0.1
        if self.mempool_count < 100_000:
            health += 0.1
        elif self.mempool_count > 500_000:
            health -= 0.15
        if 5 < self.avg_fee_sat < 50:
            health += 0.1
        elif self.avg_fee_sat > 200:
            health -= 0.15
        if self.exchange_outflow_btc > self.exchange_inflow_btc:
            health += 0.1  # Accumulation phase

        return max(0.0, min(1.0, health))

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp_ns": self.timestamp_ns,
            "hash_rate_th_s": self.hash_rate_th_s,
            "difficulty": self.difficulty,
            "mempool_count": self.mempool_count,
            "avg_fee_sat": self.avg_fee_sat,
            "net_exchange_flow_btc": self.net_exchange_flow_btc,
            "whale_tx_count_24h": self.whale_tx_count_24h,
            "miner_outflow_btc": self.miner_outflow_btc,
            "network_pressure": self.network_pressure,
            "network_health": self.health_score,
            "mvrv_ratio": self.mvrv_ratio,
            "sop_r": self.sop_r,
        }


@dataclass(frozen=True)
class SentimentMetrics:
    """
    Ω-MI22: Immutable snapshot of market sentiment metrics.
    Fear & Greed indices, social volume, put/call ratios,
    and derived sentiment scores.
    """

    timestamp_ns: int
    fear_greed_index: float = 50.0  # 0–100
    fear_greed_label: str = "Neutral"
    btc_dominance: float = 0.0
    total_market_cap_usd: float = 0.0
    btc_24h_change_pct: float = 0.0
    btc_7d_change_pct: float = 0.0
    social_volume_index: float = 0.0  # 0–1
    put_call_ratio: float = 1.0  # >1 = bearish
    long_short_ratio: float = 1.0   # >1 = more longs
    funding_rate_avg: float = 0.0
    open_interest_change_24h: float = 0.0
    sentiment_score: float = 0.0     # Derived -1.0 to +1.0
    data_quality: float = 0.0
    sources_active: int = 0

    @property
    def sentiment_normalized(self) -> float:
        """Ω-MI23: Comprehensive sentiment score [-1.0 to +1.0]."""
        if self.data_quality < 0.3:
            return 0.0

        components: list[tuple[float, float]] = []

        # Fear & Greed: normalize 0–100 to -1 to +1
        if self.fear_greed_index > 0:
            fg = (self.fear_greed_index - 50) / 50.0
            components.append((fg, 0.30))

        # Put/call ratio: >1 = bearish
        if self.put_call_ratio > 0:
            pc = max(-1.0, min(1.0, -(self.put_call_ratio - 1.0)))
            components.append((pc, 0.15))

        # Long/short ratio: >1 = bullish (more longs)
        if self.long_short_ratio > 0:
            ls = max(-1.0, min(1.0, long_short_ratio - 1.0))
            components.append((ls, 0.10))

        # Funding rate: positive = longs paying shorts = bullish but risky
        if self.funding_rate_avg != 0:
            fr = max(-1.0, min(1.0, self.funding_rate_avg * 100))
            components.append((fr, 0.15))

        # 24h price change
        if self.btc_24h_change_pct != 0:
            ch = max(-1.0, min(1.0, self.btc_24h_change_pct / 10.0))
            components.append((ch, 0.10))

        # Social volume (high volume at extremes = reversal signal)
        if self.social_volume_index > 0.8:
            components.append((-0.1 * (2 * fg if fg > 0.5 else -1), 0.10))
            components.append((ch, 0.10))

        if components:
            total_w = sum(w for _, w in components)
            score = sum(s * w for s, w in components) / total_w
        else:
            score = 0.0

        return max(-1.0, min(1.0, score))

    @property
    def extremes(self) -> list[str]:
        """Ω-MI24: Identify extreme sentiment conditions."""
        extremes: list[str] = []
        if self.fear_greed_index <= 15:
            extremes.append("extreme_fear")
        elif self.fear_greed_index >= 85:
            extremes.append("extreme_greed")
        if self.put_call_ratio > 2.0:
            extremes.append("extreme_puts")
        elif self.put_call_ratio < 0.5:
            extremes.append("extreme_calls")
        if self.funding_rate_avg > 0.05:
            extremes.append("extreme_long_funding")
        elif self.funding_rate_avg < -0.05:
            extremes.append("extreme_short_funding")
        if self.social_volume_index > 0.9:
            extremes.append("viral_social")
        return extremes

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp_ns": self.timestamp_ns,
            "fear_greed_index": self.fear_greed_index,
            "fear_greed_label": self.fear_greed_label,
            "sentiment_score": self.sentiment_normalized,
            "btc_dominance": self.btc_dominance,
            "social_volume": self.social_volume_index,
            "put_call_ratio": self.put_call_ratio,
            "funding_rate": self.funding_rate_avg,
            "extremes": self.extremes,
            "data_quality": self.data_quality,
        }


class OnChainMonitor:
    """
    Ω-MI25: Tracks on-chain metrics over time with history and
    anomaly detection.
    """

    def __init__(self, history_size: int = 500) -> None:
        self._current: OnChainMetrics = OnChainMetrics(timestamp_ns=time.time_ns())
        self._history: deque[OnChainMetrics] = deque(maxlen=history_size)

    def update(self, snapshot: OnChainMetrics) -> None:
        """Ω-MI26: Update current metrics and add to history."""
        self._current = snapshot
        self._history.append(snapshot)

    @property
    def data(self) -> OnChainMetrics:
        return self._current

    def detect_anomalies(self) -> list[dict[str, Any]]:
        """Ω-MI27: Detect anomalous on-chain conditions vs. history."""
        anomalies: list[dict[str, Any]] = []
        if len(self._history) < 20:
            return anomalies

        hist_list = list(self._history)

        # Check for exchange flow anomaly
        flows = [m.net_exchange_flow_btc for m in hist_list]
        mean_flow = sum(flows) / len(flows)
        std_flow = math.sqrt(sum((f - mean_flow) ** 2 for f in flows) / len(flows))
        if std_flow > 0:
            z_flow = (self._current.net_exchange_flow_btc - mean_flow) / std_flow
            if abs(z_flow) > 2.5:
                anomalies.append({
                    "type": "exchange_flow_anomaly",
                    "z_score": round(z_flow, 2),
                    "value": self._current.net_exchange_flow_btc,
                    "mean": round(mean_flow, 2),
                    "direction": "inflow_spike" if z_flow > 0 else "outflow_spike",
                })

        # Check for mempool congestion anomaly
        mempool_sizes = [m.mempool_count for m in hist_list]
        mean_mp = sum(mempool_sizes) / len(mempool_sizes)
        std_mp = math.sqrt(sum((s - mean_mp) ** 2 for s in mempool_sizes) / len(mempool_sizes))
        if std_mp > 0:
            z_mp = (self._current.mempool_count - mean_mp) / std_mp
            if z_mp > 2.5:
                anomalies.append({
                    "type": "mempool_congestion",
                    "z_score": round(z_mp, 2),
                    "current": self._current.mempool_count,
                    "mean": round(mean_mp, 0),
                })

        # Check for whale activity spike
        whale_counts = [m.whale_tx_count_24h for m in hist_list]
        mean_wh = sum(whale_counts) / len(whale_counts)
        std_wh = math.sqrt(sum((w - mean_wh) ** 2 for w in whale_counts) / len(whale_counts))
        if std_wh > 0:
            z_wh = (self._current.whale_tx_count_24h - mean_wh) / std_wh
            if z_wh > 2.0:
                anomalies.append({
                    "type": "whale_activity_spike",
                    "z_score": round(z_wh, 2),
                    "current": self._current.whale_tx_count_24h,
                    "mean": round(mean_wh, 0),
                })

        return anomalies

    def get_trend(self, field_name: str, window: int = 50) -> str:
        """Ω-MI28: Determine trend direction for a metric field."""
        if len(self._history) < window // 2:
            return "insufficient_data"

        hist_list = list(self._history)[-window:]
        values = [getattr(m, field_name, 0) for m in hist_list]
        if len(values) < 2:
            return "insufficient_data"

        first_half = values[:len(values) // 2]
        second_half = values[len(values) // 2:]

        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)

        if avg_first == 0:
            return "flat" if avg_second == 0 else ("rising" if avg_second > 0 else "falling")

        change = (avg_second - avg_first) / abs(avg_first)
        if change > 0.05:
            return "rising"
        elif change < -0.05:
            return "falling"
        return "flat"


class SentimentMonitor:
    """
    Ω-MI29: Tracks sentiment metrics over time with history,
    extremes detection, and contrarian signal generation.
    """

    def __init__(self, history_size: int = 1000) -> None:
        self._current: SentimentMetrics = SentimentMetrics(timestamp_ns=time.time_ns())
        self._history: deque[SentimentMetrics] = deque(maxlen=history_size)

    def update(self, snapshot: SentimentMetrics) -> None:
        """Ω-MI30: Update current sentiment and add to history."""
        self._current = snapshot
        self._history.append(snapshot)

    @property
    def sentiment(self) -> SentimentMetrics:
        return self._current

    def get_contrarian_signal(self) -> dict[str, Any]:
        """
        Ω-MI31: Generate contrarian signal from extreme sentiment.
        When sentiment reaches extremes, contrarian trade may be warranted.
        """
        extremes = self._current.extremes
        if not extremes:
            return {"signal": "neutral", "confidence": 0.0, "action": "none"}

        signal = "neutral"
        confidence = len(extremes) * 0.15

        if "extreme_fear" in extremes:
            signal = "potential_buy"
        if "extreme_greed" in extremes:
            signal = "potential_sell"
        if "extreme_puts" in extremes:
            signal = "potential_buy"
        elif "extreme_calls" in extremes:
            signal = "potential_sell"

        return {
            "signal": signal,
            "confidence": min(0.8, confidence),
            "action": f"Consider contrarian position — extremes detected: {extremes}",
            "extremes": extremes,
        }

    def get_sentiment_trend(self, window: int = 24) -> dict[str, Any]:
        """Ω-MI32: Sentiment trend analysis over a window."""
        hist = list(self._history)[-window:]
        if len(hist) < 2:
            return {"trend": "insufficient_data", "avg_score": 0.0}

        scores = [h.sentiment_normalized for h in hist]
        avg = sum(scores) / len(scores)
        first = scores[0]
        last = scores[-1]
        change = last - first

        return {
            "trend": "improving" if change > 0.05 else "deteriorating" if change < -0.05 else "stable",
            "avg_score": round(avg, 4),
            "current_score": round(last, 4),
            "change": round(change, 4),
            "window_size": len(hist),
        }

    def get_fear_greed_percentile(self) -> float:
        """Ω-MI33: Current F&G index as percentile within history."""
        hist = list(self._history)
        if len(hist) < 10:
            return 0.5

        values = sorted(h.fear_greed_index for h in hist)
        current = self._current.fear_greed_index
        rank = sum(1 for v in values if v <= current)
        return rank / max(1, len(values))


# ──────────────────────────────────────────────────────────────
# Ω-MI37 to Ω-MI54: NarrativeDistiller, NexusResonance & Hub
# ──────────────────────────────────────────────────────────────


class NarrativeDistiller:
    """
    Ω-MI37: Distills market narratives from multiple intelligence feeds.

    Combines macro events, on-chain data, sentiment, and cross-asset
    signals into coherent narratives with directional bias and
    confidence scores. Replaces LLM-based distillation with
    deterministic, explainable narrative scoring.
    """

    def __init__(self) -> None:
        self._narratives: deque[dict[str, Any]] = deque(maxlen=100)

    def distill(
        self,
        macro_bias: float,
        onchain_pressure: float,
        sentiment_score: float,
        cross_asset_resonance: float = 0.0,
        macro_events: list[MacroEvent] | None = None,
        sentiment_extremes: list[str] | None = None,
        onchain_anomalies: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Ω-MI38: Distill a narrative from all intelligence inputs.

        Combines signals and identifies the dominant narrative theme,
        direction, and confidence. Identifies convergent vs. divergent
        signals across feeds.
        """
        now_ns = time.time_ns()

        # Weighted combination
        weights = {
            "macro": 0.25,
            "onchain": 0.30,
            "sentiment": 0.20,
            "cross_asset": 0.25,
        }

        combined_bias = (
            weights["macro"] * macro_bias
            + weights["onchain"] * onchain_pressure
            + weights["sentiment"] * sentiment_score
            + weights["cross_asset"] * cross_asset_resonance
        )

        # Confidence from convergence
        signals = [macro_bias, onchain_pressure, sentiment_score, cross_asset_resonance]
        non_zero = [s for s in signals if abs(s) > 0.05]
        if len(non_zero) < 2:
            convergence = 0.1
        else:
            same_direction = all(s > 0 for s in non_zero) or all(s <= 0 for s in non_zero)
            convergence = 0.8 if same_direction else 0.3

        # Adjust confidence by data quality and anomalies
        data_quality_penalty = 0.0
        if onchain_anomalies and len(onchain_anomalies) > 0:
            data_quality_penalty = min(0.2, len(onchain_anomalies) * 0.05)
        if sentiment_extremes and len(sentiment_extremes) > 0:
            data_quality_penalty = min(0.2, len(sentiment_extremes) * 0.03)

        confidence = max(0.0, min(1.0, convergence * 0.5 + min(0.5, len(non_zero) / 4.0) - data_quality_penalty))

        # Determine narrative theme
        theme = self._classify_theme(macro_bias, onchain_pressure, sentiment_score, macro_events, sentiment_extremes)

        # Identify convergent/divergent signals
        convergence_detail = self._analyze_convergence(signals)

        narrative = {
            "narrative_id": f"narr_{uuid.uuid4().hex[:8]}",
            "timestamp_ns": now_ns,
            "theme": theme,
            "bias": round(combined_bias, 4),
            "direction": "bullish" if combined_bias > 0.05 else "bearish" if combined_bias < -0.05 else "neutral",
            "confidence": round(confidence, 4),
            "convergence_detail": convergence_detail,
            "data_quality_penalty": round(data_quality_penalty, 4),
            "signal_count": len(non_zero),
            "macro_bias": round(macro_bias, 4),
            "onchain_pressure": round(onchain_pressure, 4),
            "sentiment_score": round(sentiment_score, 4),
            "cross_asset_resonance": round(cross_asset_resonance, 4),
        }

        self._narratives.append(narrative)
        return narrative

    def _classify_theme(
        self,
        macro: float,
        onchain: float,
        sentiment: float,
        macro_events: list[MacroEvent] | None,
        extremes: list[str] | None,
    ) -> str:
        """Ω-MI39: Classify dominant narrative theme."""
        if extremes:
            if "extreme_fear" in extremes:
                return "capitulation_opportunity"
            if "extreme_greed" in extremes:
                return "euforia_warning"

        if macro < -0.3 and onchain < -0.2:
            return "macro_headwind_accumulation"
        if macro > 0.3 and onchain > 0.2:
            return "macro_tailwind_distribution"

        if macro_events and len(macro_events) > 0:
            for ev in macro_events:
                if ev.impact == ImpactLevel.CRITICAL and not ev.resolved:
                    return "upcoming_catalyst_caution"

        if abs(onchain) > abs(macro) and abs(onchain) > abs(sentiment):
            return "onchain_driven"
        if abs(sentiment) > 0.5:
            return "sentiment_driven"

        return "mixed_signals"

    def _analyze_convergence(self, signals: list[float]) -> dict[str, Any]:
        """Ω-MI40: Analyze convergence of signals."""
        non_zero = [s for s in signals if abs(s) > 0.05]
        if len(non_zero) < 2:
            return {"type": "divergent", "aligned_signals": 0, "total_signals": len(non_zero)}

        same_dir = all(s > 0 for s in non_zero) or all(s <= 0 for s in non_zero)
        return {
            "type": "convergent" if same_dir else "divergent",
            "aligned_signals": sum(1 for s in non_zero if (s > 0 and non_zero[0] > 0) or (s < 0 and non_zero[0] < 0)),
            "total_signals": len(non_zero),
            "agreement_pct": round(sum(1 for s in non_zero if s * non_zero[0] > 0) / len(non_zero), 2),
        }

    @property
    def latest_narrative(self) -> dict[str, Any] | None:
        """Ω-MI41: Most recent distillation."""
        return self._narratives[-1] if self._narratives else None

    def get_narrative_history(self, n: int = 20) -> list[dict[str, Any]]:
        return list(self._narratives)[-n:]


class NexusResonance:
    """
    Ω-MI42: Cross-asset resonance detection.

    Tracks momentum and movements across correlated assets (gold,
    equity indices, DXY, ETH) to detect resonance patterns that
    precede BTC movements. Models lead-lag relationships between
    assets and computes a composite resonance score.

    Pure Python — no numpy.
    """

    def __init__(self, history_size: int = 120) -> None:
        """Initialize with 120 seconds of per-asset price history."""
        self._history: dict[str, deque[tuple[int, float]]] = {}
        self._resolved_symbols: dict[str, str] = {}
        self._target_assets = ["GOLD", "NASDAQ", "SP500", "ETH", "DXY"]

        for asset in self._target_assets:
            self._history[asset] = deque(maxlen=history_size)

        self.resonance_score = 0.0
        self.breakout_signals: list[dict[str, Any]] = []
        self._last_breakout_ns: int = 0

    def record_tick(self, asset: str, price: float, timestamp_ns: int | None = None) -> None:
        """Ω-MI43: Record a price tick for a cross-asset."""
        if asset not in self._history:
            self._history[asset] = deque(maxlen=120)
        ts = timestamp_ns or time.time_ns()
        self._history[asset].append((ts, price))

    def compute_resonance(self) -> dict[str, Any]:
        """
        Ω-MI44: Compute cross-asset resonance score.

        BTC is directionally aligned with NASDAQ/SP500 (risk on/off).
        BTC and Gold react negatively to DXY.
        ETH typically follows BTC with slight lag.

        Resonance occurs when multiple correlated assets move together,
        amplifying the directional signal.
        """
        self.breakout_signals.clear()
        now_ns = time.time_ns()
        window_ns = 10 * 1_000_000_000  # 10 second window

        asset_momentums: dict[str, float] = {}

        for asset, ticks in self._history.items():
            if len(ticks) < 10:
                continue

            # Get last 10 seconds of data
            cutoff = now_ns - window_ns
            recent = [(ts, p) for ts, p in ticks if ts >= cutoff]
            if len(recent) < 2:
                continue

            p_old = recent[0][1]
            p_current = recent[-1][1]
            if p_old == 0:
                continue

            delta_pct = (p_current - p_old) / p_old

            # Normalize by typical volatility
            if asset in ("NASDAQ", "SP500"):
                momentum = delta_pct / 0.0005  # 0.05% move = 1.0
            elif asset == "GOLD":
                momentum = delta_pct / 0.0003
            elif asset == "ETH":
                momentum = delta_pct / 0.0010
            elif asset == "DXY":
                momentum = -delta_pct / 0.0002  # Inverse: DXY up = BTC down
            else:
                momentum = delta_pct / 0.0010

            asset_momentums[asset] = momentum

            if abs(momentum) > 1.5:
                direction = "bullish" if momentum > 0 else "bearish"
                self.breakout_signals.append({
                    "asset": asset,
                    "direction": direction,
                    "momentum": round(momentum, 4),
                    "timestamp_ns": now_ns,
                })

        # Compute composite score
        if asset_momentums:
            n = len(asset_momentums)
            momentum_values = list(asset_momentums.values())
            raw_score = sum(momentum_values) / n

            # Amplify if assets are moving in same direction (resonance)
            same_direction = all(m > 0 for m in momentum_values) or all(m < 0 for m in momentum_values)
            resonance_multiplier = 1.5 if same_direction and n >= 3 else 1.0

            self.resonance_score = max(-1.0, min(1.0, raw_score * resonance_multiplier))
        else:
            self.resonance_score = 0.0

        return {
            "resonance_score": round(self.resonance_score, 4),
            "asset_momentums": {k: round(v, 6) for k, v in asset_momentums.items()},
            "breakout_signals": self.breakout_signals,
            "total_assets_tracked": sum(1 for t in self._history.values() if len(t) > 0),
            "assets_with_data": len(asset_momentums),
        }

    def detect_lead_lag(self, leader: str, follower: str, window_s: int = 30) -> dict[str, Any]:
        """
        Ω-MI45: Detect lead-lag relationship between two assets.
        Uses cross-correlation with time lag to find optimal delay.
        """
        if leader not in self._history or follower not in self._history:
            return {"error": "missing_data", "lead_asset": leader, "follow_asset": follower}

        leader_ticks = list(self._history[leader])
        follower_ticks = list(self._history[follower])

        if len(leader_ticks) < 20 or len(follower_ticks) < 20:
            return {"error": "insufficient_data", "leader_count": len(leader_ticks), "follower_count": len(follower_ticks)}

        # Compute returns
        leader_prices = [p for _, p in leader_ticks]
        follower_prices = [p for _, p in follower_ticks]

        # Equalize lengths
        min_len = min(len(leader_prices), len(follower_prices))
        leader_prices = leader_prices[-min_len:]
        follower_prices = follower_prices[-min_len:]

        leader_returns = [(leader_prices[i] - leader_prices[i - 1]) / max(1, leader_prices[i - 1]) for i in range(1, min_len)]
        follower_returns = [(follower_prices[i] - follower_prices[i - 1]) / max(1, follower_prices[i - 1]) for i in range(1, min_len)]

        # Cross-correlation at different lags
        max_lag = min(30, len(leader_returns) // 2)
        best_lag = 0
        best_corr = 0.0

        for lag in range(-max_lag, max_lag + 1):
            corr = self._correlate(leader_returns, follower_returns, lag)
            if abs(corr) > abs(best_corr):
                best_corr = corr
                best_lag = lag

        return {
            "leader_asset": leader,
            "follower_asset": follower,
            "optimal_lag_seconds": best_lag,
            "correlation_at_lag": round(best_corr, 4),
            "interpretation": (
                f"{leader} leads {follower} by {best_lag}s" if best_lag > 0
                else f"{follower} leads {leader} by {-best_lag}s" if best_lag < 0
                else f"{leader} and {follower} are synchronous"
            ),
        }

    def _correlate(self, a: list[float], b: list[float], lag: int) -> float:
        """Ω-MI46: Pure-Python cross-correlation at given lag."""
        n = len(a)
        if lag >= 0:
            slice_a = a[:n - lag] if lag < n else []
            slice_b = b[lag:] if lag < n else []
        else:
            abs_lag = abs(lag)
            slice_a = a[abs_lag:] if abs_lag < n else []
            slice_b = b[:n - abs_lag] if abs_lag < n else []

        if len(slice_a) < 3:
            return 0.0

        mean_a = sum(slice_a) / len(slice_a)
        mean_b = sum(slice_b) / len(slice_b)

        numerator = sum((a_i - mean_a) * (b_i - mean_b) for a_i, b_i in zip(slice_a, slice_b))
        denom_a = math.sqrt(sum((a_i - mean_a) ** 2 for a_i in slice_a))
        denom_b = math.sqrt(sum((b_i - mean_b) ** 2 for b_i in slice_b))

        if denom_a == 0 or denom_b == 0:
            return 0.0

        return numerator / (denom_a * denom_b)

    def health(self) -> dict[str, Any]:
        """Ω-MI47: Health of resonance detection."""
        return {
            "resonance_score": round(self.resonance_score, 4),
            "active_assets": sum(1 for t in self._history.values() if len(t) > 0),
            "breakout_signals_count": len(self.breakout_signals),
        }


class IntelligenceHub:
    """
    Ω-MI48: Master hub orchestrating all intelligence feeds.

    Aggregates MacroCalendar, OnChainMonitor, SentimentMonitor,
    NarrativeDistiller, and NexusResonance into a single access
    point for the decision engine. Provides health monitoring,
    priority scoring, and fallback handling.
    """

    def __init__(
        self,
        macro_calendar: MacroCalendar | None = None,
        update_interval_ns: int = 60 * 1_000_000_000,
    ) -> None:
        self.macro = macro_calendar or MacroCalendar()
        self.onchain = OnChainMonitor()
        self.sentiment = SentimentMonitor()
        self.narrative = NarrativeDistiller()
        self.resonance = NexusResonance()

        self._update_interval_ns = update_interval_ns
        self._last_update_ns: int = 0
        self._update_count: int = 0
        self._health_scores: dict[str, float] = {}

    def update_intelligence(self) -> dict[str, Any]:
        """
        Ω-MI49: Main update cycle — gather all intelligence and
        produce a consolidated assessment.
        """
        now_ns = time.time_ns()
        if now_ns - self._last_update_ns < self._update_interval_ns and self._update_count > 0:
            return self.get_latest_assessment()

        self._last_update_ns = now_ns
        self._update_count += 1

        # Gather from all sources
        macro_bias = self.macro.compute_macro_bias()
        onchain_pressure = self.onchain.data.network_pressure
        sentiment_score = self.sentiment.sentiment.sentiment_normalized
        onchain_anomalies = self.onchain.detect_anomalies()
        sentiment_extremes = self.sentiment.sentiment.extremes

        # Cross-asset resonance
        resonance_data = self.resonance.compute_resonance()
        cross_asset_score = resonance_data["resonance_score"]

        # Impending events
        upcoming_events = self.macro.get_upcoming_events(look_ahead_min=60)

        # Distill narrative
        narrative = self.narrative.distill(
            macro_bias=macro_bias,
            onchain_pressure=onchain_pressure,
            sentiment_score=sentiment_score,
            cross_asset_resonance=cross_asset_score,
            macro_events=upcoming_events,
            sentiment_extremes=sentiment_extremes,
            onchain_anomalies=onchain_anomalies,
        )

        # Contrarian signal
        contrarian = self.sentiment.get_contrarian_signal()

        # Lead-lag analysis
        lead_lag = self.resonance.detect_lead_lag("NASDAQ", "ETH")

        assessment = {
            "timestamp_ns": now_ns,
            "update_count": self._update_count,
            "narrative": narrative,
            "macro_bias": round(macro_bias, 4),
            "onchain_pressure": round(onchain_pressure, 4),
            "sentiment_score": round(sentiment_score, 4),
            "cross_asset_resonance": round(cross_asset_score, 4),
            "contrarian_signal": contrarian,
            "onchain_anomalies": onchain_anomalies,
            "sentiment_extremes": sentiment_extremes,
            "upcoming_macro_events": [{"title": e.title, "impact": e.impact.name} for e in upcoming_events],
            "lead_lag": lead_lag,
            "consensus_direction": self._consensus_direction(macro_bias, onchain_pressure, sentiment_score, cross_asset_score),
            "consensus_strength": self._consensus_strength(macro_bias, onchain_pressure, sentiment_score, cross_asset_score),
            "risk_level": self._risk_level(macro_bias, onchain_anomalies, sentiment_extremes, upcoming_events),
        }

        self._health_scores["intelligence"] = assessment["consensus_strength"]
        self._latest_assessment = assessment

        return assessment

    @property
    def latest_assessment(self) -> dict[str, Any]:
        """Ω-MI50: Return latest assessment."""
        return getattr(self, "_latest_assessment", {})

    def _consensus_direction(self, *signals: float) -> str:
        """Ω-MI51: Determine consensus direction from all signals."""
        non_zero = [s for s in signals if abs(s) > 0.05]
        if not non_zero:
            return "neutral"
        positive = sum(1 for s in non_zero if s > 0)
        return "bullish" if positive > len(non_zero) / 2 else "bearish"

    def _consensus_strength(self, *signals: float) -> float:
        """Ω-MI52: Consensus strength — agreement and magnitude."""
        non_zero = [s for s in signals if abs(s) > 0.05]
        if len(non_zero) < 2:
            return min(0.2, abs(non_zero[0]) if non_zero else 0.0)

        same_dir = all(s > 0 for s in non_zero) or all(s <= 0 for s in non_zero)
        avg_magnitude = sum(abs(s) for s in non_zero) / len(non_zero)
        alignment_bonus = 0.3 if same_dir else -0.2

        return max(0.0, min(1.0, avg_magnitude * 0.5 + (len(non_zero) / len(signals)) * 0.2 + alignment_bonus))

    def _risk_level(
        self,
        macro_bias: float,
        onchain_anomalies: list[dict[str, Any]],
        sentiment_extremes: list[str],
        upcoming_events: list[MacroEvent],
    ) -> str:
        """Ω-MI53: Assess overall risk level."""
        risk_score = 0.0

        # Macro risk
        risk_score += abs(macro_bias) * 0.25

        # Anomaly risk
        if onchain_anomalies:
            risk_score += min(0.3, len(onchain_anomalies) * 0.1)

        # Sentiment extreme risk
        if sentiment_extremes:
            risk_score += min(0.2, len(sentiment_extremes) * 0.05)

        # Event risk
        critical_events = sum(1 for e in upcoming_events if e.impact == ImpactLevel.CRITICAL)
        risk_score += min(0.3, critical_events * 0.15)

        if risk_score > 0.6:
            return "high"
        elif risk_score > 0.3:
            return "moderate"
        return "low"

    def health(self) -> dict[str, Any]:
        """Ω-MI54: Overall intelligence hub health."""
        return {
            "macro": self.macro.health(),
            "onchain": {
                "active": self.onchain.data.sources_active > 0,
                "anomalies": len(self.onchain.detect_anomalies()),
                "network_pressure": self.onchain.data.network_pressure,
                "history_size": len(self.onchain._history),
            },
            "sentiment": {
                "active": self.sentiment.sentiment.sources_active > 0,
                "score": self.sentiment.sentiment.sentiment_normalized,
                "extremes": self.sentiment.sentiment.extremes,
            },
            "resonance": self.resonance.health(),
            "update_count": self._update_count,
            "latest_assessment_available": hasattr(self, "_latest_assessment"),
        }
