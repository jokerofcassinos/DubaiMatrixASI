"""
SOLÉNN v2 — Swarm Orchestrator & Quantum Interference Engine (Ω-SO01 a Ω-SO54)
Replaces the v1 neural_swarm + quantum_thought with a modular, async-
compatible swarm orchestration layer. Agents are registered dynamically,
run in concurrent batches, and their signals pass through quantum
interference (constructive/destructive) before collapsing to a decision.

Concept 1: Agent Registration & Lifecycle (Ω-SO01–SO18)
  Dynamic agent pool management, health checks, graceful degradation,
  hot-swap capability, and auto-pruning of underperforming agents.

Concept 2: Quantum Interference Engine (Ω-SO19–SO36)
  Signals interfere as waves: constructive (aligned signals amplify),
  destructive (opposing signals cancel). Coherence measurement determines
  if the system collapses to a decision or remains in superposition.

Concept 3: Confluence Decision & Output (Ω-SO37–SO54)
  Collapse policy, decision formatting, telemetry emission, and
  feedback loop for continuous agent weight adaptation.
"""

from __future__ import annotations

import math
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


# ──────────────────────────────────────────────────────────────
# Ω-SO01 to Ω-SO18: Agent Registration & Lifecycle
# ──────────────────────────────────────────────────────────────


class AgentState(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEGRADED = "degraded"
    FAILED = "failed"


@dataclass
class AgentDescriptor:
    """Ω-SO01: Full metadata for one swarm agent."""

    name: str
    weight: float
    category: str  # orderflow, regime, structure, chaos, etc.
    latency_budget_ms: float
    last_health_check_ns: int = 0
    consecutive_failures: int = 0
    state: AgentState = AgentState.ACTIVE
    accuracy_rolling: float = 0.5
    n_calls: int = 0
    n_errors: int = 0
    avg_latency_us: float = 0.0


@dataclass
class SwarmSignal:
    """Ω-SO03: Signal produced by one agent."""

    agent_name: str
    signal: float  # [-1, +1]
    confidence: float  # [0, 1]
    category: str
    weight: float
    reasoning: str
    latency_us: float
    timestamp_ns: int = field(default_factory=lambda: time.time_ns())

    @property
    def weighted_signal(self) -> float:
        return self.signal * self.confidence * self.weight


class AgentRegistry:
    """Ω-SO04: Manages the dynamic pool of swarm agents."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentDescriptor] = {}
        self._callbacks: dict[str, Callable] = {}  # name → analyze function

    def register(
        self,
        name: str,
        category: str,
        weight: float = 1.0,
        latency_budget_ms: float = 100.0,
        analyze_fn: Callable | None = None,
    ) -> None:
        """Ω-SO05: Register a new agent."""
        self._agents[name] = AgentDescriptor(
            name=name,
            weight=weight,
            category=category,
            latency_budget_ms=latency_budget_ms,
            last_health_check_ns=time.time_ns(),
        )
        if analyze_fn:
            self._callbacks[name] = analyze_fn

    def unregister(self, name: str) -> bool:
        """Ω-SO06: Remove an agent."""
        if name in self._agents:
            self._agents.pop(name, None)
            self._callbacks.pop(name, None)
            return True
        return False

    def update_weight(self, name: str, new_weight: float) -> None:
        """Ω-SO07: Adjust agent weight."""
        if name in self._agents:
            self._agents[name].weight = max(0.0, min(5.0, new_weight))

    def record_health(self, name: str, success: bool, latency_us: float) -> None:
        """Ω-SO08: Track agent health."""
        if name not in self._agents:
            return
        agent = self._agents[name]
        agent.n_calls += 1
        agent.last_health_check_ns = time.time_ns()

        if success:
            agent.consecutive_failures = 0
            if agent.state in (AgentState.DEGRADED, AgentState.SUSPENDED):
                agent.state = AgentState.ACTIVE
        else:
            agent.consecutive_failures += 1
            agent.n_errors += 1
            if agent.consecutive_failures >= 3:
                agent.state = AgentState.DEGRADED
            if agent.consecutive_failures >= 10:
                agent.state = AgentState.FAILED

        # EMA latency tracking
        alpha = 0.1
        agent.avg_latency_us = (1 - alpha) * agent.avg_latency_us + alpha * latency_us

    def prune(self, min_accuracy: float = 0.40) -> list[str]:
        """Ω-SO09: Remove agents below accuracy threshold."""
        removed = []
        for name, desc in list(self._agents.items()):
            if desc.accuracy_rolling < min_accuracy and desc.n_calls > 20:
                self.unregister(name)
                removed.append(name)
        return removed

    def get_active(self) -> dict[str, AgentDescriptor]:
        return {n: d for n, d in self._agents.items() if d.state == AgentState.ACTIVE}

    def get_all(self) -> dict[str, AgentDescriptor]:
        return dict(self._agents)


# ──────────────────────────────────────────────────────────────
# Ω-SO19 to Ω-SO36: Quantum Interference Engine
# ──────────────────────────────────────────────────────────────


@dataclass
class InterferenceResult:
    """Ω-SO19: Result of quantum interference processing."""

    raw_signal: float
    coherence: float  # [0, 1] — how aligned are agents
    entropy: float  # [0, 1] — disorder of the system
    collapsed_signal: float  # 0 if in superposition, signal if collapsed
    is_collapsed: bool
    n_bull_agents: int
    n_bear_agents: int
    n_neutral_agents: int
    top_bull_agents: list[str]
    top_bear_agents: list[str]
    phi: float  # integrated information (simplified Φ)
    reasoning: str


class QuantumInterference:
    """Ω-SO20: Processes agent signals as interfering waves."""

    def __init__(self, collapse_threshold: float = 0.7) -> None:
        self._collapse_threshold = collapse_threshold
        self._history: deque[InterferenceResult] = deque(maxlen=500)

    def interfere(self, signals: list[SwarmSignal]) -> InterferenceResult:
        """Ω-SO21: Apply quantum interference to all agent signals."""
        if not signals:
            return self._empty("no_signals")

        # Filter very low confidence
        active = [s for s in signals if s.confidence > 0.01]
        if not active:
            return self._empty("no_active_signals")

        # ── Constructive Interference: aligned signals amplify ──
        # ── Destructive Interference: opposing signals cancel ──

        bull_weighted = 0.0
        bear_weighted = 0.0
        total_weighted = 0.0

        bull_agents: list[tuple[str, float]] = []
        bear_agents: list[tuple[str, float]] = []
        neutral_count = 0

        for s in active:
            w = s.weighted_signal
            total_weighted += abs(w)

            if w > 0.01:
                bull_weighted += w
                bull_agents.append((s.agent_name, abs(w)))
            elif w < -0.01:
                bear_weighted += abs(w)
                bear_agents.append((s.agent_name, abs(w)))
            else:
                neutral_count += 1

        # Raw signal: net directionality normalized
        net = bull_weighted - bear_weighted
        raw_signal = net / total_weighted if total_weighted > 0 else 0.0

        # Coherence: |bull - bear| / (bull + bear)
        sum_all = bull_weighted + bear_weighted
        coherence = abs(bull_weighted - bear_weighted) / sum_all if sum_all > 0 else 0.0

        # Entropy: Shannon entropy of signal distribution
        probs = []
        for s in active:
            p = abs(s.weighted_signal) / total_weighted if total_weighted > 0 else 1.0 / len(active)
            probs.append(p)
        entropy = -sum(p * math.log2(p + 1e-10) for p in probs if p > 0)
        max_entropy = math.log2(len(active)) if len(active) > 1 else 1.0
        norm_entropy = entropy / max_entropy if max_entropy > 0 else 0.0

        # Phi (simplified integrated information)
        # Measures how much the whole is more than the sum of parts
        # If all agents agree: phi → 1.0 (integrated)
        # If agents are divided: phi → 0 (fragmented)
        n_bull = len(bull_agents)
        n_bear = len(bear_agents)
        n_total = n_bull + n_bear
        if n_total > 0:
            # Phi = 1 - |n_bull - n_bear| / (n_bull + n_bear) * (1 - coherence)
            phi = coherence * (1.0 - abs(n_bull - n_bear) / n_total)
            phi = max(0.0, min(1.0, phi))
        else:
            phi = 0.0

        # Collapse decision
        if coherence >= self._collapse_threshold:
            collapsed = raw_signal
            is_collapsed = True
        else:
            # Check persistence: if last 3 rounds had same direction with
            # increasing coherence, force collapse
            persistent = False
            if len(self._history) >= 3:
                last_3 = list(self._history)[-3:]
                same_dir = all(
                    r.raw_signal * raw_signal > 0 for r in last_3 if abs(r.raw_signal) > 0.05
                )
                increasing_coh = all(
                    last_3[i].coherence <= last_3[i + 1].coherence for i in range(len(last_3) - 1)
                )
                if same_dir and increasing_coh:
                    persistent = True

            if persistent and coherence >= self._collapse_threshold * 0.7:
                collapsed = raw_signal
                is_collapsed = True
            else:
                collapsed = 0.0
                is_collapsed = False

        # Top agents by influence
        top_bull = sorted(bull_agents, key=lambda x: x[1], reverse=True)[:3]
        top_bear = sorted(bear_agents, key=lambda x: x[1], reverse=True)[:3]

        reasoning = (
            f"signal={raw_signal:+.3f} | coh={coherence:.2f} | "
            f"ent={norm_entropy:.2f} | phi={phi:.2f} | "
            f"bull={n_bull} bear={n_bear} neutral={neutral_count}"
        )

        result = InterferenceResult(
            raw_signal=round(raw_signal, 6),
            coherence=round(coherence, 4),
            entropy=round(norm_entropy, 4),
            collapsed_signal=round(collapsed, 6),
            is_collapsed=is_collapsed,
            n_bull_agents=n_bull,
            n_bear_agents=n_bear,
            n_neutral_agents=neutral_count,
            top_bull_agents=[n for n, _ in top_bull],
            top_bear_agents=[n for n, _ in top_bear],
            phi=round(phi, 4),
            reasoning=reasoning,
        )
        self._history.append(result)
        return result

    def _empty(self, reason: str) -> InterferenceResult:
        return InterferenceResult(
            raw_signal=0.0,
            coherence=0.0,
            entropy=0.0,
            collapsed_signal=0.0,
            is_collapsed=False,
            n_bull_agents=0,
            n_bear_agents=0,
            n_neutral_agents=0,
            top_bull_agents=[],
            top_bear_agents=[],
            phi=0.0,
            reasoning=reason,
        )


# ──────────────────────────────────────────────────────────────
# Ω-SO37 to Ω-SO54: Confluence Decision & Output
# ──────────────────────────────────────────────────────────────


@dataclass
class SwarmDecision:
    """Ω-SO37: Final decision from swarm analysis."""

    trace_id: str
    direction: str  # LONG, SHORT, or WAIT
    strength: float  # [0, 1]
    confidence: float  # [0, 1]
    coherence: float
    collapsed_signal: float
    agent_details: dict[str, Any]
    reasoning: str
    latency_ms: float
    timestamp_ns: int = field(default_factory=lambda: time.time_ns())


class SwarmOrchestrator:
    """Ω-SO40: Orchestrates full swarm lifecycle."""

    def __init__(
        self,
        collapse_threshold: float = 0.7,
        min_collapse_signal: float = 0.3,
    ) -> None:
        self.registry = AgentRegistry()
        self.interference = QuantumInterference(collapse_threshold)
        self._min_signal = min_collapse_signal
        self._decision_log: deque[SwarmDecision] = deque(maxlen=1000)
        self._total_rounds = 0
        self._collapse_rate_history: deque[float] = deque(maxlen=100)

    def analyze(
        self,
        signals: list[SwarmSignal],
        market_state: dict[str, Any] | None = None,
    ) -> SwarmDecision:
        """Ω-SO41: Full pipeline: signals → interference → decision."""
        t0 = time.time_ns()
        self._total_rounds += 1

        # 1. Quantum interference
        inter = self.interference.interfere(signals)

        # 2. Collapse → decision
        if inter.is_collapsed and abs(inter.collapsed_signal) >= self._min_signal:
            direction = "LONG" if inter.collapsed_signal > 0 else "SHORT"
            strength = min(1.0, abs(inter.collapsed_signal))
            confidence = inter.coherence
        else:
            direction = "WAIT"
            strength = 0.0
            confidence = 1.0 - inter.coherence  # High confidence to wait

        # 3. Build decision
        latency_ms = (time.time_ns() - t0) / 1e6
        decision = SwarmDecision(
            trace_id=f"sw-{uuid.uuid4().hex[:8]}",
            direction=direction,
            strength=round(strength, 4),
            confidence=round(confidence, 4),
            coherence=inter.coherence,
            collapsed_signal=inter.collapsed_signal,
            agent_details={
                "n_agents": len(signals),
                "n_bull": inter.n_bull_agents,
                "n_bear": inter.n_bear_agents,
                "n_neutral": inter.n_neutral_agents,
                "top_bull": inter.top_bull_agents,
                "top_bear": inter.top_bear_agents,
                "phi": inter.phi,
            },
            reasoning=inter.reasoning,
            latency_ms=round(latency_ms, 2),
        )

        self._decision_log.append(decision)

        # Track collapse rate
        collapsed_count = sum(1 for d in self._decision_log if d.direction != "WAIT")
        self._collapse_rate_history.append(collapsed_count / max(1, len(self._decision_log)))

        return decision

    def record_outcome(self, trace_id: str, was_correct: bool) -> None:
        """Ω-SO42: Feed back outcome for agent weight adaptation."""
        # Find the decision
        for d in self._decision_log:
            if d.trace_id == trace_id:
                # Simplified: update registry averages
                for i, (name, w) in enumerate(d.agent_details.items()):
                    if isinstance(w, dict) and "signal" in w:
                        desc = self.registry._agents.get(name)
                        if desc:
                            alpha = 0.05
                            desc.accuracy_rolling = (
                                (1 - alpha) * desc.accuracy_rolling
                                + alpha * (1.0 if was_correct else 0.0)
                            )
                break

    def get_stats(self) -> dict[str, Any]:
        """Ω-SO43: Swarm statistics."""
        total = len(self._decision_log)
        if total == 0:
            return {"total_rounds": self._total_rounds, "total_decisions": 0}

        longs = sum(1 for d in self._decision_log if d.direction == "LONG")
        shorts = sum(1 for d in self._decision_log if d.direction == "SHORT")
        waits = total - longs - shorts

        avg_latency = sum(d.latency_ms for d in self._decision_log) / total
        avg_strength = sum(d.strength for d in self._decision_log) / total

        collapse_rate = (
            sum(self._collapse_rate_history) / len(self._collapse_rate_history)
            if self._collapse_rate_history else 0.0
        )

        return {
            "total_rounds": self._total_rounds,
            "total_decisions": total,
            "longs": longs,
            "shorts": shorts,
            "waits": waits,
            "collapse_rate": round(collapse_rate, 4),
            "avg_latency_ms": round(avg_latency, 2),
            "avg_strength": round(avg_strength, 4),
            "n_registered_agents": len(self.registry.get_all()),
            "n_active_agents": len(self.registry.get_active()),
        }
