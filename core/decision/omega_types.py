"""
SOLÉNN v2 — Omega Decision Types (Ω-T46, Ω-T01, Ω-T28, Ω-T55, Ω-T64, Ω-T154)
Immutable typed data structures for all decision pipeline outputs:
TradeSignal, Signal, ConfluenceResult, RegimeState, CircuitBreakerLevel,
DecisionCheckpoint, PostTradeAnalysis, PerformanceMetrics, TailRiskMetrics.
"""

from __future__ import annotations

import math
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Direction(Enum):
    LONG = "long"
    SHORT = "short"
    NEUTRAL = "neutral"


class Priority(Enum):
    """Ω-T52: Trade signal priority classification."""
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"


class CircuitBreakerLevel(Enum):
    """Ω-T64: Seven-level circuit breaker."""
    GREEN = ("green", 0.0, 1.0, "Normal operation")
    YELLOW = ("yellow", 0.3, 0.7, "Reduce sizing 30%")
    ORANGE = ("orange", 0.6, 0.4, "Reduce sizing 60%, only A+ setups")
    RED = ("red", 1.0, 0.0, "Pause 5 minutes, automatic analysis")
    CRITICAL = ("critical", 1.5, 0.0, "Close all positions, pause 15 minutes")
    EMERGENCY = ("emergency", 2.0, 0.0, "Shutdown complete, notify CEO")
    CATASTROPHIC = ("catastrophic", 3.0, 0.0, "Shutdown + tail hedge + multiple alerts")

    def __init__(self, name: str, trigger_dd_pct: float, sizing_mult: float, action: str) -> None:
        self._name = name
        self._trigger_dd_pct = trigger_dd_pct
        self._sizing_mult = sizing_mult
        self._action = action

    @property
    def trigger_dd_pct(self) -> float:
        return self._trigger_dd_pct

    @property
    def sizing_multiplier(self) -> float:
        return self._sizing_mult

    @property
    def action_description(self) -> str:
        return self._action


class DecisionState(Enum):
    """Ω-T28: Decision state machine states."""
    IDLE = "IDLE"
    OBSERVING = "OBSERVING"
    SIGNAL_DETECTED = "SIGNAL_DETECTED"
    CONFLUENCE_CHECK = "CONFLUENCE_CHECK"
    VALIDATION = "VALIDATION"
    RISK_CHECK = "RISK_CHECK"
    READY_TO_ENTER = "READY_TO_ENTER"
    ENTERED = "ENTERED"
    MANAGING = "MANAGING"
    EXITING = "EXITING"
    EXITED = "EXITED"
    POST_TRADE_ANALYSIS = "POST_TRADE_ANALYSIS"
    CIRCUIT_BREAKER = "CIRCUIT_BREAKER"
    RECONCILING = "RECONCILING"


class RegimeType(Enum):
    """Ω-T37: Regime types (≥20 states compressed into primary categories)."""
    TRENDING_UP_STRONG = "trending_up_strong"
    TRENDING_UP_WEAK = "trending_up_weak"
    TRENDING_DOWN_STRONG = "trending_down_strong"
    TRENDING_DOWN_WEAK = "trending_down_weak"
    RANGING_TIGHT = "ranging_tight"
    RANGING_WIDE = "ranging_wide"
    CHOPPY_EXPANDING = "choppy_expanding"
    CHOPPY_CONTRACTING = "choppy_contracting"
    FLASH_CRASH = "flash_crash"
    FLASH_CRASH_RECOVERY = "flash_crash_recovery"
    SHORT_SQUEEZE = "short_squeeze"
    LONG_SQUEEZE = "long_squeeze"
    LIQUIDATION_CASCADE = "liquidation_cascade"
    CROSS_MARKET_CONTAGION = "cross_market_contagion"
    UNKNOWN = "unknown"


class ValidationStage(Enum):
    """Ω-T10-T17: 47-stage validation pipeline groups."""
    DATA_QUALITY_1 = "data_quality_stage_1"
    DATA_QUALITY_2 = "data_quality_stage_2"
    REGIME_CONSISTENCY_1 = "regime_consistency_stage_1"
    REGIME_CONSISTENCY_2 = "regime_consistency_stage_2"
    TECHNICAL_CONFLUENCE_1 = "technical_confluence_stage_1"
    TECHNICAL_CONFLUENCE_2 = "technical_confluence_stage_2"
    ORDER_FLOW_1 = "order_flow_stage_1"
    ORDER_FLOW_2 = "order_flow_stage_2"
    MULTI_TIMEFRAME_1 = "multitimeframe_stage_1"
    MULTI_TIMEFRAME_2 = "multitimeframe_stage_2"
    RISK_PRECHECK_1 = "risk_precheck_stage_1"
    RISK_PRECHECK_2 = "risk_precheck_stage_2"
    MARKET_CONDITION_1 = "market_condition_stage_1"
    MARKET_CONDITION_2 = "market_condition_stage_2"
    FINAL_GATING = "final_gating"


@dataclass(frozen=True, slots=True)
class Signal:
    """Ω-T02: Normalized signal from any source module."""
    signal_id: str
    source: str
    direction: Direction
    score: float  # [0, 1] normalized
    confidence: float  # [0, 1]
    timestamp_ns: int
    features: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not (0.0 <= self.score <= 1.0):
            raise ValueError(f"Signal score must be in [0,1], got {self.score}")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"Signal confidence must be in [0,1], got {self.confidence}")


@dataclass(frozen=True, slots=True)
class ConfluenceResult:
    """Ω-T09: Result of the confluence scoring engine."""
    confluence_score: float  # Weighted sum: Σ wᵢ × sᵢ × cᵢ × dᵢ
    n_signals_aligned: int
    n_signals_total: int
    alignment_ratio: float  # n_aligned / n_total
    consensus_direction: Direction
    signal_details: dict[str, dict[str, float]]  # {signal_id: {score, weight, confidence, decay}}
    conflict_detected: bool
    conflict_pairs: list[str]  # List of conflicting signal_id pairs
    timestamp_ns: int

    @property
    def is_strong_confluence(self) -> bool:
        """Confluence score > 0.7 with ≥ 70% signals aligned."""
        return self.confluence_score >= 0.7 and self.alignment_ratio >= 0.7

    @property
    def is_moderate_confluence(self) -> bool:
        """Confluence score > 0.5 with ≥ 50% signals aligned."""
        return self.confluence_score >= 0.5 and self.alignment_ratio >= 0.5


@dataclass(frozen=True, slots=True)
class RegimeState:
    """Ω-T37: Current market regime with probabilities."""
    primary_regime: RegimeType
    probabilities: dict[RegimeType, float]  # Posterior probabilities for all regimes
    confidence: float  # P(primary_regime | data)
    transition_predicted: RegimeType | None  # Predicted next regime if transition imminent
    transition_probability: float  # P(transition to next regime in next N seconds)
    critical_slowing_down: float  # CSD indicator (autocorrelation + variance trend)
    hurst: float  # Current Hurst exponent
    entropy: float  # Shannon entropy of regime distribution
    timestamp_ns: int

    def __post_init__(self) -> None:
        total = sum(self.probabilities.values())
        if total > 0 and abs(total - 1.0) > 0.01:
            raise ValueError(f"Regime probabilities must sum to ~1.0, got {total}")


@dataclass(frozen=True, slots=True)
class ValidationStageResult:
    """Ω-T18: Result of a single validation stage group."""
    stage: ValidationStage
    stages_passed: int
    stages_total: int
    failed_stages: list[str]  # Names of stages that failed
    failure_reasons: dict[str, str]  # stage_name → reason for failure
    pass_rate: float  # stages_passed / stages_total

    @property
    def is_pass(self) -> bool:
        return self.stages_passed == self.stages_total

    @property
    def is_reject(self) -> bool:
        return self.stages_passed < self.stages_total


@dataclass(frozen=True, slots=True)
class ExitPlan:
    """Ω-T50: Complete exit plan generated BEFORE entry."""
    stop_loss: float
    take_profit: float
    trailing_stop_distance: float
    time_based_exit_seconds: float
    partial_exits: list[tuple[float, float]]  # (price_level, fraction_to_exit)
    invalidation_condition: str  # Human-readable description
    regime_exit_condition: str  # Regime change that triggers exit
    counter_signal_threshold: float  # Opposite signal strength that triggers exit
    emergency_exit_trigger: str  # Market condition that triggers emergency exit


@dataclass(frozen=True, slots=True)
class TradeSignal:
    """
    Ω-T46: Final trade decision output. Immutable, fully traceable.
    Published to execution layer via pub-sub.
    """
    signal_id: str
    direction: Direction
    symbol: str
    exchange: str
    entry_price: float
    stop_loss: float
    take_profit: float
    size_fraction: float  # Fraction of Kelly-optimal
    confidence: float  # [0, 1] from confluence + validation
    priority: Priority
    regime: RegimeState
    confluence: ConfluenceResult
    validation_results: list[ValidationStageResult]
    exit_plan: ExitPlan
    reasoning: str  # Ω-T47: Human-readable rationale
    alternatives_rejected: list[str]  # Ω-T48: Alternatives considered and rejected
    risk_disclosure: str  # Ω-T49: Explicit risk statement
    max_expected_loss: float  # Worst case loss at stop
    expected_reward_risk_ratio: float  # R:R ratio
    estimated_tce: float  # Total Cost of Execution estimate
    trace_id: str  # Distributed tracing ID
    timestamp_ns: int = field(default_factory=lambda: time.time_ns())

    @property
    def is_viable(self) -> bool:
        """Ω-T17 (Stage 43-47): Check if trade passes minimum viability."""
        return (self.expected_reward_risk_ratio >= 7.0
                and self.confidence >= 0.7
                and self.priority in (Priority.A_PLUS, Priority.A))

    def compute_max_loss(self, current_price: float | None = None) -> float:
        """Compute maximum expected loss if stop is hit."""
        price = current_price or self.entry_price
        price_diff = abs(price - self.stop_loss)
        return price_diff * self.size_fraction


@dataclass(frozen=True, slots=True)
class DecisionCheckpoint:
    """Ω-T51: Serializable snapshot of complete decision state for replay/debug."""
    checkpoint_id: str
    trace_id: str
    state: DecisionState
    input_snapshot: dict[str, Any]
    signals: list[dict[str, Any]]
    confluence_score: float | None
    validation_results: list[dict[str, Any]]
    risk_checks: list[dict[str, Any]]
    output: dict[str, Any] | None  # TradeSignal dict if created
    latency_ms: float  # Time from data availability to this checkpoint
    timestamp_ns: int = field(default_factory=lambda: time.time_ns())


@dataclass(frozen=True, slots=True)
class TailRiskMetrics:
    """Ω-T91-T99: Tail risk assessment metrics."""
    skewness: float
    kurtosis: float
    var_99: float  # Value at Risk 99%
    cvar_99_5: float  # Conditional VaR 99.5%
    gpd_tail_index: float  # ξ (xi) from GPD fit; > 0 = heavy tails
    tail_probability_10sigma: float  # Estimated P(return > 10σ)
    liquidation_distance_bps: float  # Distance to nearest liquidation cluster in bps
    cascade_potential: float  # [0, 1] estimated cascade risk
    hedge_ratio: float  # Optimal hedge ratio for current exposure
    insurance_fund_pct: float  # % of total capital in reserve
    black_swan_readiness: float  # [0, 1] system readiness score


@dataclass(frozen=True, slots=True)
class PostTradeAnalysis:
    """Ω-T118-T126: Comprehensive post-trade forensic analysis."""
    trade_id: str
    signal_id: str
    direction: Direction
    symbol: str
    entry_price: float
    exit_price: float
    pnl: float
    pnl_pct: float
    holding_time_seconds: float
    exit_reason: str
    was_profitable: bool

    # Forensic layers (Ω-T118-T126)
    data_integrity_ok: bool
    feature_computation_ok: bool
    signal_generation_ok: bool
    confluence_evaluation_ok: bool
    regime_context_ok: bool
    risk_assessment_ok: bool
    execution_quality_ok: bool
    exit_logic_ok: bool
    market_condition_adverse: bool

    # Contrafactual (Ω-T109-T117)
    contrafactual_results: dict[str, dict[str, float]]
    root_cause: str | None  # If trade was a loss
    patch_proposed: str | None

    timestamp_ns: int = field(default_factory=lambda: time.time_ns())


@dataclass(frozen=True, slots=True)
class PerformanceAttribution:
    """Ω-T136-T144: Performance decomposition by source."""
    total_pnl: float
    signal_attribution: dict[str, float]  # signal_id → pnl contribution
    regime_attribution: dict[str, float]  # regime_type → pnl contribution
    execution_cost: float
    gross_alpha: float
    net_alpha: float  # Gross alpha - execution cost - fees
    timing_attribution: float  # How much P&L came from timing
    direction_attribution: float  # How much from direction vs timing
    luck_component: float  # estimated stochastic component
    skill_component: float  # estimated systematic component
    information_ratio: float
    sharpe_gross: float
    sharpe_net: float
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    opportunity_cost_rejected_right: float
    opportunity_cost_rejected_wrong: float
    timestamp_ns: int = field(default_factory=lambda: time.time_ns())


@dataclass(frozen=True, slots=True)
class MetaLearningState:
    """Ω-T145-T153: Meta-learning system state."""
    strategy_win_rates: dict[str, float]  # strategy_id → current win rate estimate
    strategy_posteriors: dict[str, tuple[float, float]]  # strategy_id → (alpha, beta) for Beta dist
    concept_drift_detected: bool
    drift_detected_at: float | None
    parameters_needing_recalibration: list[str]
    parameter_stability: dict[str, float]  # param_name → stability score [0, 1]
    model_versions: dict[str, str]  # component → current version
    autonomous_adjustments_count: int
    pending_human_approvals: list[dict[str, Any]]
    learning_velocity: float  # Trades between discovery and patch deployment (inverse)
    timestamp_ns: int = field(default_factory=lambda: time.time_ns())


@dataclass(frozen=True, slots=True)
class DecisionTelemetryEvent:
    """Ω-T154: Structured telemetry event for each decision."""
    event_id: str
    trace_id: str
    span_id: str
    event_type: str  # "signal_received", "confluence_computed", "validation_passed", etc.
    component: str  # Which decision component emitted this
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    latency_us: int  # Microseconds for this processing step
    confidence: float | None
    timestamp_ns: int = field(default_factory=lambda: time.time_ns())


def generate_trace_id() -> str:
    """Generate unique distributed tracing ID."""
    return f"tr-{uuid.uuid4().hex[:16]}"


def generate_signal_id() -> str:
    """Generate unique signal ID."""
    return f"sig-{uuid.uuid4().hex[:12]}"


def generate_checkpoint_id() -> str:
    """Generate unique checkpoint ID."""
    return f"chk-{uuid.uuid4().hex[:8]}"
