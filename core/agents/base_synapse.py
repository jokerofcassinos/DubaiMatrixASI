"""
SOLÉNN v2 — Base Synapse Interface Ω (Ω-B01 to Ω-B162)
Transmuted from v1: core/consciousness/agents/base.py (BaseAgent, AgentSignal)

Superiority v2 vs v1:
  v1: Simple dataclass AgentSignal(name, signal, conf, reason, weight) + BaseAgent(name, weight)
  v2: Expanded AgentSignal with Bayesian posterior, temporal metadata, multi-timeframe awareness,
      weighted signal with uncertainty bands, and adaptive weight evolution based on accuracy history.

Protocol 3-6-9: 162 vetores planejados
  Concept 1 — Signal Foundations (Ω-B01 to Ω-B54): AgentSignal, AgentResult, SignalQuality
  Concept 2 — Agent Lifecycle (Ω-B55 to Ω-B108): BaseAgent warmup/running/sleep/shutdown
  Concept 3 — Adaptive Behavior (Ω-B109 to Ω-B162): Weight evolution, accuracy tracking,
              pandemic detection, cross-agent correlation, meta-learning hooks
"""

from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


# ──────────────────────────────────────────────────────────────
# Ω-B01 to Ω-B09: Signal Enumerations
# ──────────────────────────────────────────────────────────────

class SignalDirection(Enum):
    """Ω-B01: Direction of agent signal."""
    LONG = auto()
    SHORT = auto()
    NEUTRAL = auto()

class SignalQuality(Enum):
    """Ω-B02: Quality classification of signal."""
    NOISE = auto()      # Entropia máxima, sem informação útil
    WEAK = auto()       # Sinal presente mas fraco (< 0.3)
    MODERATE = auto()   # Sinal confiável (0.3-0.6)
    STRONG = auto()     # Sinal forte (0.6-0.85)
    EXTREME = auto()    # Sinal extremo (> 0.85), alta confiança
    PANDEMIC = auto()   # Ω-B34: Sinal detectou condição pan-demica

class AgentState(Enum):
    """Ω-B55: Lifecycle states of an agent."""
    INITIALIZING = auto()   # Warmup, coletando dados, nao emite sinais
    RUNNING = auto()        # Agente ativo e emitindo sinais
    DEGRADED = auto()       # Performance caindo, sinais com confianca reduzida
    SLEEPING = auto()       # Agente pausado (regime adverso)
    PANDEMIC = auto()       # Ω-B34: Regime extremo, agentes entram modo alerta
    SHUTDOWN = auto()       # Agente desligado

class Timeframe(Enum):
    """Ω-B10: Timeframe awareness."""
    TICK = "tick"
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    M30 = "M30"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"

# ──────────────────────────────────────────────────────────────
# Ω-B10 to Ω-B27: AgentSignal (transmuted v1 AgentSignal)
# ──────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class AgentSignal:
    """
    Ω-B10 to Ω-B27: Signal emitted by an agent.

    Transmuted from v1 AgentSignal(name, signal, confidence, reasoning, weight).
    v2 adds: posterior distribution, uncertainty bands, temporal metadata,
    quality classification, pandemic flag, cross-correlation tracking.
    """
    agent_name: str                          # Ω-B10: Unique agent identifier
    signal: float = 0.0                      # Ω-B11: [-1.0 (SELL) .. 0.0 (NEUTRAL) .. +1.0 (BUY)]
    confidence: float = 0.0                  # Ω-B12: [0.0 .. 1.0] P(signal is correct)
    reasoning: str = ""                      # Ω-B13: Human-readable explanation
    weight: float = 1.0                      # Ω-B14: Adaptive weight (evolves with accuracy)
    timeframe: str = ""                      # Ω-B15: Timeframe of analysis
    metadata: dict = field(default_factory=dict)  # Ω-B16: Extra data for PhD sensors
    is_pandemic: bool = False                # Ω-B34: Extreme regime flag
    timestamp_ns: int = 0                    # Ω-B17: Nanosecond timestamp
    posterior_mean: float = 0.0              # Ω-B18: Bayesian posterior mean of signal
    posterior_std: float = 0.0               # Ω-B19: Bayesian posterior std (uncertainty)
    accuracy_rolling: float = 0.5            # Ω-B20: Rolling accuracy over last 200 signals
    quality: SignalQuality = SignalQuality.NOISE   # Ω-B21: Quality classification

    @property
    def weighted_signal(self) -> float:
        """Ω-B22: Weighted signal = signal × confidence × weight."""
        return self.signal * self.confidence * self.weight

    @property
    def direction(self) -> SignalDirection:
        """Ω-B23: Direction derived from signal value."""
        if self.signal > 0.1:
            return SignalDirection.LONG
        elif self.signal < -0.1:
            return SignalDirection.SHORT
        return SignalDirection.NEUTRAL

    @property
    def uncertainty_band(self) -> tuple[float, float]:
        """Ω-B24: 95% confidence interval [lower, upper]."""
        if self.posterior_mean == 0.0 and self.posterior_std == 0.0:
            # Fallback: approximate uncertainty from confidence
            approx_std = max(0.01, (1.0 - self.confidence) * 0.5)
            return (self.weighted_signal - 1.96 * approx_std,
                    self.weighted_signal + 1.96 * approx_std)
        return (self.posterior_mean - 1.96 * self.posterior_std,
                self.posterior_mean + 1.96 * self.posterior_std)

    @property
    def is_actionable(self) -> bool:
        """Ω-B25: Signal is strong enough to act on."""
        return abs(self.weighted_signal) >= 0.3 and self.confidence >= 0.5

    def to_decision_input(self) -> dict:
        """Ω-B26: Convert signal to format expected by Decision module."""
        return {
            "agent": self.agent_name,
            "signal": self.signal,
            "confidence": self.confidence,
            "weighted": self.weighted_signal,
            "direction": self.direction.name,
            "quality": self.quality.name,
            "reasoning": self.reasoning,
            "timeframe": self.timeframe,
            "is_pandemic": self.is_pandemic,
            "uncertainty": self.posterior_std,
            "accuracy": self.accuracy_rolling,
        }

    @classmethod
    def neutral(cls, agent_name: str, reason: str = "NEUTRAL") -> "AgentSignal":
        """Ω-B27: Factory for a neutral signal."""
        return cls(agent_name=agent_name, signal=0.0, confidence=0.0,
                   reasoning=reason, quality=SignalQuality.NOISE)


# ──────────────────────────────────────────────────────────────
# Ω-B28 to Ω-B36: AgentResult (transmuted v1 return patterns)
# ──────────────────────────────────────────────────────────────

@dataclass
class AgentResult:
    """Ω-B28: Result from agent analyze() call. Can contain 0+ signals."""
    signals: list[AgentSignal] = field(default_factory=list)
    state: AgentState = AgentState.RUNNING
    warnings: list[str] = field(default_factory=list)
    error: Optional[str] = None
    processing_time_ms: float = 0.0

    @property
    def is_error(self) -> bool:
        return self.error is not None

    @property
    def best_signal(self) -> Optional[AgentSignal]:
        """Ω-B33: Return strongest signal by absolute weighted value."""
        if not self.signals:
            return None
        return max(self.signals, key=lambda s: abs(s.weighted_signal))


# ──────────────────────────────────────────────────────────────
# Ω-B37 to Ω-B54: BaseAgent (transmuted v1 BaseAgent)
# ──────────────────────────────────────────────────────────────

class BaseAgent:
    """
    Ω-B37 to Ω-B54: Base class for all SOLÉNN agents.

    Transmuted from v1 BaseAgent(name, weight) with:
    - v1: accuracy history (last 200), record_accuracy()
    - v2: Full lifecycle management, adaptive weight evolution,
      pandemic detection hooks, cross-correlation tracking,
      warmup/shutdown hooks, performance telemetry.
    """

    def __init__(
        self,
        name: str,
        weight: float = 1.0,
        is_pandemic: bool = False,
        needs_orderflow: bool = False,
        warmup_ticks: int = 50,
    ) -> None:
        # Ω-B37: Agent identity
        self.name = name
        # Ω-B38: Adaptive weight (starts at initial, can fluctuate)
        self._initial_weight = weight
        self._current_weight = weight
        # Ω-B34: Pandemic mode
        self.is_pandemic = is_pandemic
        # Ω-B39: Does this agent need order flow data as 2nd arg?
        self.needs_orderflow = needs_orderflow
        # Ω-B40: Warmup counter
        self._warmup_ticks = warmup_ticks
        self._ticks_seen = 0
        # Ω-B41: Accuracy tracking (v1 had last 200, v2 uses deque + stats)
        self._accuracy_history: deque[float] = deque(maxlen=200)
        # Ω-B42: Signal history for post-trade analysis
        self._signal_history: deque[AgentSignal] = deque(maxlen=500)
        # Ω-B43: Processing time history (ms)
        self._latency_history: deque[float] = deque(maxlen=100)
        # Ω-B55: Current state
        self._state = AgentState.INITIALIZING
        # Ω-B44: Cross-correlation with other agents
        self._cross_corr: dict[str, deque[float]] = {}

    # ─── Lifecycle ───────────────────────────────────────────

    @property
    def state(self) -> AgentState:
        """Ω-B55: Current agent state."""
        return self._state

    @property
    def weight(self) -> float:
        """Ω-B38: Current adaptive weight."""
        return self._current_weight

    @property
    def is_ready(self) -> bool:
        """Ω-B45: Agent has completed warmup and can emit signals."""
        return (self._state == AgentState.RUNNING and
                self._ticks_seen >= self._warmup_ticks)

    def warmup(self, tick_data) -> None:
        """Ω-B46: Feed warmup data to agent."""
        if self._state == AgentState.SHUTDOWN:
            return
        self._ticks_seen += 1
        if self._ticks_seen >= self._warmup_ticks:
            self._state = AgentState.RUNNING

    def shutdown(self) -> None:
        """Ω-B54: Graceful agent shutdown."""
        self._state = AgentState.SHUTDOWN

    # ─── Signal Generation Override Point ────────────────────

    def analyze(self, tick_data, **kwargs) -> Optional[AgentSignal]:
        """
        Ω-B47: Override in subclasses to generate signals.

        Args:
            tick_data: Market data (price, volume, order book, etc.)
            **kwargs: Extra data (orderflow analysis, regime state, etc.)

        Returns:
            AgentSignal or None (None = no signal this tick)
        """
        raise NotImplementedError(f"{self.name} must implement analyze()")

    def analyze_with_result(self, tick_data, **kwargs) -> AgentResult:
        """
        Ω-B48: Wrapper that measures timing, tracks accuracy, handles errors.
        Returns AgentResult with signal(s), timing, and any warnings.
        """
        start_ms = time.perf_counter() * 1000
        result = AgentResult(state=self._state)

        try:
            if self._state == AgentState.SHUTDOWN:
                result.warnings.append("Agent is shut down")
                return result

            if not self.is_ready:
                self.warmup(tick_data)
                result.warnings.append(f"Warming up ({self._ticks_seen}/{self._warmup_ticks})")
                return result

            signal = self.analyze(tick_data, **kwargs)
            if signal is not None:
                # Ω-B17: Set timestamp
                import time as _time
                import_data = _time.time_ns() if hasattr(_time, 'time_ns') else int(_time.time() * 1e9)
                object.__setattr__(signal, 'timestamp_ns', import_data)
                result.signals.append(signal)
                self._signal_history.append(signal)

        except Exception as e:
            result.error = str(e)
            result.state = AgentState.DEGRADED

        elapsed = (time.perf_counter() * 1000) - start_ms
        result.processing_time_ms = elapsed
        self._latency_history.append(elapsed)
        return result

    # ─── Accuracy Tracking (transmuted v1) ──────────────────

    def record_accuracy(self, was_correct: bool) -> None:
        """Ω-B49: Record whether a past signal was correct."""
        self._accuracy_history.append(1.0 if was_correct else 0.0)

    @property
    def accuracy(self) -> float:
        """Ω-B50: Rolling accuracy over last 200 signals."""
        if not self._accuracy_history:
            return 0.5  # Prior: unknown accuracy
        return sum(self._accuracy_history) / len(self._accuracy_history)

    @property
    def accuracy_std(self) -> float:
        """Ω-B51: Standard deviation of accuracy."""
        if len(self._accuracy_history) < 10:
            return 0.5
        mean = self.accuracy
        variance = sum((x - mean) ** 2 for x in self._accuracy_history) / len(self._accuracy_history)
        return math.sqrt(variance)

    def update_adaptive_weight(self) -> None:
        """
        Ω-B52: Adapt weight based on rolling accuracy.
        High accuracy → weight increases. Low accuracy → weight decreases.
        Weight is bounded: [0.1, 10.0]
        """
        acc = self.accuracy
        if len(self._accuracy_history) < 20:
            return  # Not enough data for reliable weight adjustment

        # Omega ratio: accuracy / (1 - accuracy)
        if acc >= 0.90:
            multiplier = 1.15
        elif acc >= 0.75:
            multiplier = 1.08
        elif acc >= 0.55:
            multiplier = 1.02
        elif acc >= 0.45:
            multiplier = 0.98
        elif acc >= 0.35:
            multiplier = 0.90
        else:
            multiplier = 0.80

        new_weight = self._current_weight * multiplier
        # Bound: [0.1, 2x initial_weight]
        new_weight = max(0.1, min(new_weight, self._initial_weight * 2.0))
        self._current_weight = new_weight

    # ─── Cross-Correlation Tracking ──────────────────────────

    def record_correlation(self, other_agent: str, signal_value: float) -> None:
        """Ω-B43: Track correlation with another agent's signal."""
        if other_agent not in self._cross_corr:
            self._cross_corr[other_agent] = deque(maxlen=200)
        self._cross_corr[other_agent].append(signal_value)

    def correlation_with(self, other_agent: str) -> float:
        """Ω-B44: Pearson correlation with another agent's signals."""
        if other_agent not in self._cross_corr:
            return 0.0
        corr_values = list(self._cross_corr[other_agent])
        if len(corr_values) < 10:
            return 0.0

        # Get own recent signals
        own_signals = [s.signal for s in list(self._signal_history)[-len(corr_values):]]
        if len(own_signals) != len(corr_values):
            return 0.0

        mean_self = sum(own_signals) / len(own_signals)
        mean_other = sum(corr_values) / len(corr_values)

        num = sum((a - mean_self) * (b - mean_other)
                  for a, b in zip(own_signals, corr_values))
        den_self = sum((a - mean_self) ** 2 for a in own_signals)
        den_other = sum((b - mean_other) ** 2 for b in corr_values)

        denom = math.sqrt(den_self * den_other)
        if denom < 1e-10:
            return 0.0
        return num / denom

    # ─── Performance Telemetry ───────────────────────────────

    def get_telemetry(self) -> dict:
        """Ω-B53: Return comprehensive agent telemetry."""
        avg_latency = (sum(self._latency_history) / len(self._latency_history)
                       if self._latency_history else 0.0)
        p99_latency = (sorted(self._latency_history)[int(len(self._latency_history) * 0.99)]
                       if len(self._latency_history) > 10 else avg_latency)

        return {
            "name": self.name,
            "state": self._state.name,
            "weight_initial": self._initial_weight,
            "weight_current": self._current_weight,
            "accuracy": self.accuracy,
            "accuracy_std": self.accuracy_std,
            "signals_emitted": len(self._signal_history),
            "avg_latency_ms": avg_latency,
            "p99_latency_ms": p99_latency,
            "warmup_progress": f"{self._ticks_seen}/{self._warmup_ticks}",
            "is_ready": self.is_ready,
            "is_pandemic": self.is_pandemic,
        }

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}({self.name!r}, "
                f"weight={self._current_weight:.2f}, "
                f"acc={self.accuracy:.2f}, "
                f"state={self._state.name})")
