"""
SOLÉNN v2 — State Telemetry & Observability (Ω-C91 a Ω-C99)
State metrics export, health check, drift detection, entropy measurement,
audit trail, visualization data, prediction, stability score, correlation.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True, slots=True)
class StateMetrics:
    state: str
    duration: float
    transition_count: int
    avg_transition_latency_ms: float
    last_transition_ts: float
    state_stability_score: float


@dataclass(frozen=True, slots=True)
class HealthCheckResult:
    healthy: bool
    checks: dict[str, bool]
    details: str = ""


class StateMetricsCollector:
    """Ω-C91 a Ω-C99: Collects and computes state telemetry metrics."""

    def __init__(self, max_history: int = 1000) -> None:
        self._transitions: deque[tuple[str, float]] = deque(maxlen=max_history)
        self._start_time: float = time.time()
        self._state_entry_time: float = self._start_time
        self._current_state: str = "unknown"
        self._latencies: deque[float] = deque(maxlen=max_history)
        self._stability_scores: deque[float] = deque(maxlen=max_history)
        self._transition_counts_by_state: dict[str, int] = {}
        self._duration_per_state: dict[str, float] = {}
        self._external_events: deque[dict[str, Any]] = deque(maxlen=max_history)

    def record_transition(self, old_state: str, new_state: str) -> None:
        now = time.time()
        duration = now - self._state_entry_time
        self._transition_counts_by_state[old_state] = self._transition_counts_by_state.get(old_state, 0) + 1
        self._duration_per_state[old_state] = self._duration_per_state.get(old_state, 0.0) + duration

        self._transitions.append((new_state, now))
        self._latencies.append(now - self._state_entry_time)
        self._current_state = new_state
        self._state_entry_time = now

    def record_external_event(self, event: dict[str, Any]) -> None:
        event_with_ts = {"timestamp": time.time(), **event}
        self._external_events.append(event_with_ts)

    def compute_stability_score(self) -> float:
        if not self._stability_scores:
            recent_transitions = len([t for t in self._transitions if t[1] > time.time() - 300])
            if recent_transitions > 20:
                score = 30.0
            elif recent_transitions > 10:
                score = 60.0
            elif recent_transitions > 3:
                score = 80.0
            else:
                score = 95.0
        else:
            score = sum(self._stability_scores) / len(self._stability_scores)
        return max(0.0, min(100.0, score))

    def get_metrics(self) -> StateMetrics:
        return StateMetrics(
            state=self._current_state,
            duration=time.time() - self._state_entry_time,
            transition_count=len(self._transitions),
            avg_transition_latency_ms=sum(self._latencies) / len(self._latencies) * 1000 if self._latencies else 0.0,
            last_transition_ts=self._transitions[-1][1] if self._transitions else self._start_time,
            state_stability_score=self.compute_stability_score(),
        )

    def health_check(self, invariants_fn: Any) -> HealthCheckResult:
        results = invariants_fn() if invariants_fn else {}
        if isinstance(results, dict):
            healthy = all(results.values())
            details = "" if healthy else f"Failed: {[k for k, v in results.items() if not v]}"
            return HealthCheckResult(healthy=healthy, checks=results, details=details)
        return HealthCheckResult(healthy=True, checks={}, details="No invariants defined")

    def predict_next_state(self, ngram_size: int = 3) -> dict[str, float]:
        if len(self._transitions) < ngram_size + 1:
            return {}
        pattern = [t[0] for t in list(self._transitions)[-ngram_size:]]
        counts: dict[str, int] = {}
        for i in range(len(self._transitions) - ngram_size):
            window = [t[0] for t in list(self._transitions)[i: i + ngram_size]]
            if window == pattern:
                next_state = self._transitions[i + ngram_size][0]
                counts[next_state] = counts.get(next_state, 0) + 1
        total = sum(counts.values())
        return {s: c / total for s, c in counts.items()} if total > 0 else {}

    def compute_entropy(self, window_seconds: float = 300.0) -> float:
        import math
        now = time.time()
        recent = [t[0] for t in self._transitions if t[1] >= now - window_seconds]
        if not recent:
            return 0.0
        counts: dict[str, int] = {}
        for s in recent:
            counts[s] = counts.get(s, 0) + 1
        total = len(recent)
        return -sum((c / total) * math.log2(c / total) for c in counts.values())

    def get_stability_history(self) -> list[float]:
        return list(self._stability_scores)
