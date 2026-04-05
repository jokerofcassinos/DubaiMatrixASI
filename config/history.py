"""
SOLÉNN v2 — State History & Time-Travel (Ω-C82 a Ω-C90)
Historical state log, time-travel query, diff timeline, replay, branch,
garbage collection, frequency analysis, transition graph, anomaly detection.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class StateEntry:
    state_name: str
    data: dict[str, Any]
    timestamp: float
    version: int


class StateHistoryLog:
    """Ω-C82 a Ω-C90: State history with time-travel, replay, branching, and analysis."""

    def __init__(self, max_entries: int = 10000) -> None:
        self._entries: list[StateEntry] = []
        self._branches: dict[str, list[StateEntry]] = {}
        self._max = max_entries

    def append(self, state_name: str, data: dict[str, Any], version: int) -> None:
        self._entries.append(StateEntry(state_name=state_name, data=data, timestamp=time.time(), version=version))
        if len(self._entries) > self._max:
            self._entries = self._entries[-self._max:]

    def get_at_timestamp(self, timestamp: float) -> StateEntry | None:
        for entry in reversed(self._entries):
            if entry.timestamp <= timestamp:
                return entry
        return self._entries[0] if self._entries else None

    def get_at_version(self, version: int) -> StateEntry | None:
        for entry in reversed(self._entries):
            if entry.version == version:
                return entry
        return None

    def get_timeline(self, start: float | None = None, end: float | None = None) -> list[StateEntry]:
        return [e for e in self._entries if (start is None or e.timestamp >= start) and (end is None or e.timestamp <= end)]

    def create_branch(self, branch_name: str, from_timestamp: float | None = None) -> bool:
        if from_timestamp:
            entry = self.get_at_timestamp(from_timestamp)
            if entry is None:
                return False
            idx = self._entries.index(entry)
            self._branches[branch_name] = list(self._entries[: idx + 1])
        else:
            self._branches[branch_name] = list(self._entries)
        return True

    def get_branch(self, branch_name: str) -> list[StateEntry]:
        return list(self._branches.get(branch_name, []))

    def compute_frequency_analysis(self) -> dict[str, dict[str, float]]:
        counts: dict[str, int] = defaultdict(int)
        total_durations: dict[str, float] = defaultdict(float)
        for i in range(len(self._entries) - 1):
            state = self._entries[i].state_name
            counts[state] += 1
            total_durations[state] += self._entries[i + 1].timestamp - self._entries[i].timestamp
        result: dict[str, dict[str, float]] = {}
        total_transitions = max(1, sum(counts.values()))
        for state, count in counts.items():
            result[state] = {"count": count, "frequency": count / total_transitions, "avg_duration": total_durations[state] / max(1, count - 1)}
        return result

    def compute_transition_graph(self) -> dict[str, dict[str, int]]:
        graph: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for i in range(len(self._entries) - 1):
            graph[self._entries[i].state_name][self._entries[i + 1].state_name] += 1
        return {k: dict(v) for k, v in graph.items()}

    def detect_anomalies(self, rarity_threshold: int = 3) -> list[StateEntry]:
        counts: defaultdict = defaultdict(int)
        for entry in self._entries:
            counts[entry.state_name] += 1
        return [e for e in self._entries if counts[e.state_name] <= rarity_threshold]

    def garbage_collect(self, retention_seconds: float) -> None:
        cutoff = time.time() - retention_seconds
        self._entries = [e for e in self._entries if e.timestamp >= cutoff]
        for branch_name in list(self._branches.keys()):
            self._branches[branch_name] = [e for e in self._branches[branch_name] if e.timestamp >= cutoff]
            if not self._branches[branch_name]:
                del self._branches[branch_name]

    def get_stats(self) -> dict[str, Any]:
        return {"total_entries": len(self._entries), "branches": list(self._branches.keys()), "unique_states": len(set(e.state_name for e in self._entries))}
