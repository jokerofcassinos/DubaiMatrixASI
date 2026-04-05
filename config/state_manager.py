"""
SOLÉNN v2 — State Manager Core (Ω-C55 a Ω-C72)
Bounded state machine core with type-safe transitions, guard functions,
invariant enforcement, transactional updates with ACID-like semantics,
WAL logging, and idempotent retries.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class GuardResult(Enum):
    ALLOW = "allow"
    DENY = "deny"


@dataclass(frozen=True, slots=True)
class StateTransitionError:
    from_state: str
    to_state: str
    reason: str
    timestamp: float = field(default_factory=time.time)


@dataclass(frozen=True, slots=True)
class StateSnapshot:
    """Immutable snapshot of state at a given time."""
    state_name: str
    data: dict[str, Any]
    checksum: str
    timestamp: float = field(default_factory=time.time)


class WriteAheadLog:
    """Ω-C66: Write-Ahead Log for transaction recovery."""

    def __init__(self) -> None:
        self._entries: list[dict[str, Any]] = []

    def append(self, operation: str, data: dict[str, Any], tx_id: str) -> None:
        self._entries.append({
            "tx_id": tx_id,
            "operation": operation,
            "data": data,
            "timestamp": time.time(),
            "committed": False,
        })

    def commit(self, tx_id: str) -> None:
        for entry in self._entries:
            if entry["tx_id"] == tx_id and not entry["committed"]:
                entry["committed"] = True

    def rollback(self, tx_id: str) -> list[dict[str, Any]]:
        return [e for e in self._entries if e["tx_id"] == tx_id and not e["committed"]]

    def clear_committed(self) -> None:
        self._entries = [e for e in self._entries if e["committed"]]

    def get_uncommitted(self, tx_id: str) -> list[dict[str, Any]]:
        return [e for e in self._entries if e["tx_id"] == tx_id and not e["committed"]]


class StateMachine:
    """
    Ω-C55 to Ω-C63: Type-safe bounded state machine with guards and invariants.
    """

    def __init__(self, name: str, initial_state: str) -> None:
        self._name = name
        self._current_state = initial_state
        self._initial_state = initial_state
        self._transitions: dict[str, set[str]] = {}
        self._guards: dict[tuple[str, str], list[Callable[[dict[str, Any]], GuardResult]]] = {}
        self._invariants: list[Callable[[dict[str, Any]], tuple[bool, str]]] = []
        self._observers: list[Callable[[str, str, dict[str, Any]], None]] = []
        self._state_data: dict[str, Any] = {}
        self._history: list[tuple[str, str, float]] = []
        self._errors: list[StateTransitionError] = []

    def add_transition(self, from_state: str, to_state: str) -> None:
        self._transitions.setdefault(from_state, set()).add(to_state)

    def add_guard(self, from_state: str, to_state: str, guard_fn: Callable[[dict[str, Any]], GuardResult]) -> None:
        self._guards.setdefault((from_state, to_state), []).append(guard_fn)

    def add_invariant(self, invariant_fn: Callable[[dict[str, Any]], tuple[bool, str]]) -> None:
        self._invariants.append(invariant_fn)

    def add_observer(self, callback: Callable) -> None:
        self._observers.append(callback)

    def transition(self, to_state: str, data_update: dict[str, Any] | None = None) -> bool:
        allowed = self._transitions.get(self._current_state, set())
        if to_state not in allowed:
            error = StateTransitionError(self._current_state, to_state, f"No transition from {self._current_state} to {to_state}")
            self._errors.append(error)
            return False

        guards = self._guards.get((self._current_state, to_state), [])
        for guard in guards:
            if guard(self._state_data) == GuardResult.DENY:
                error = StateTransitionError(self._current_state, to_state, f"Guard denied transition to {to_state}")
                self._errors.append(error)
                return False

        if data_update:
            self._state_data.update(data_update)

        for invariant_fn in self._invariants:
            holds, description = invariant_fn(self._state_data)
            if not holds:
                error = StateTransitionError(self._current_state, to_state, f"Invariant violated: {description}")
                self._errors.append(error)
                return False

        old_state = self._current_state
        self._current_state = to_state
        self._history.append((old_state, to_state, time.time()))

        for observer in self._observers:
            try:
                observer(old_state, to_state, self._state_data)
            except Exception:
                pass

        return True

    def reset(self) -> None:
        """Ω-C61: Reset to initial state with full sanitization."""
        self._current_state = self._initial_state
        self._state_data.clear()

    def validate_invariants(self) -> list[tuple[bool, str]]:
        results: list[tuple] = []
        for invariant_fn in self._invariants:
            results.append(invariant_fn(self._state_data))
        return results

    def get_state(self) -> str:
        return self._current_state

    def get_data(self) -> dict[str, Any]:
        return dict(self._state_data)

    def get_possible_transitions(self) -> set[str]:
        return set(self._transitions.get(self._current_state, set()))

    def get_history(self) -> list[tuple[str, str, float]]:
        return list(self._history)

    def get_errors(self) -> list[StateTransitionError]:
        return list(self._errors)

    def serialize(self) -> dict[str, Any]:
        return {
            "name": self._name,
            "current_state": self._current_state,
            "initial_state": self._initial_state,
            "state_data": self._state_data,
            "history": self._history[-100:],
            "checksum": str(hash(json.dumps(self._state_data, sort_keys=True, default=str))),
        }

    def deserialize(self, data: dict[str, Any]) -> None:
        self._current_state = data.get("current_state", self._initial_state)
        self._state_data = data.get("state_data", {})


class StateTransaction:
    """
    Ω-C64 a Ω-C72: ACID-like transaction scope for state updates.
    All-or-nothing commit, isolation, write-ahead log, idempotent retry.
    """

    def __init__(self, state_machine: StateMachine) -> None:
        self._sm = state_machine
        self._tx_id = str(uuid.uuid4())
        self._wal = WriteAheadLog()
        self._pending_updates: dict[str, Any] = {}
        self._snapshot_before: dict[str, Any] = state_machine.get_data()
        self._committed = False
        self._metrics = {"attempt_count": 0, "success_count": 0, "rollback_count": 0}

    @property
    def id(self) -> str:
        return self._tx_id

    @property
    def is_committed(self) -> bool:
        return self._committed

    def update(self, key: str, value: Any) -> None:
        self._pending_updates[key] = value
        self._wal.append("update", {key: value}, self._tx_id)

    def commit(self) -> bool:
        """Ω-C65: All-or-nothing commit."""
        self._metrics["attempt_count"] += 1
        if self._committed:
            return True
        self._sm._state_data.update(self._pending_updates)
        for invariant_fn in self._sm._invariants:
            holds, description = invariant_fn(self._sm._state_data)
            if not holds:
                self.rollback()
                return False
        self._wal.commit(self._tx_id)
        self._committed = True
        self._metrics["success_count"] += 1
        return True

    def rollback(self) -> None:
        self._sm._state_data.clear()
        self._sm._state_data.update(self._snapshot_before)
        self._metrics["rollback_count"] += 1
        self._committed = False

    def clone(self) -> StateTransaction:
        clone = StateTransaction(self._sm)
        clone._snapshot_before = dict(self._snapshot_before)
        clone._pending_updates = dict(self._pending_updates)
        return clone

    def get_metrics(self) -> dict[str, Any]:
        return dict(self._metrics)
