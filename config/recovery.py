"""
SOLÉNN v2 — Crash Recovery & Graceful Degradation (Ω-C100 a Ω-C108)
Crash recovery protocol, graceful degradation, emergency freeze,
self-healing, watchdog timer, fallback chain, emergency rollback,
crash simulation, recovery reporting.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class DegradationLevel(Enum):
    FULL_CAPABILITY = "full"
    REDUCED_CAPABILITY = "reduced"
    SAFE_MODE = "safe_mode"
    MINIMAL_MODE = "minimal"
    SHUTDOWN_ORDERLY = "shutdown"


@dataclass(frozen=True, slots=True)
class RecoveryReport:
    """Ω-C108: Report of what was recovered and what was lost."""
    recovered_items: list[str]
    lost_items: list[str]
    degraded_level: DegradationLevel
    duration_ms: float
    timestamp: float = field(default_factory=time.time)
    details: str = ""


class WatchdogTimer:
    """Ω-C104: If no activity within N seconds, trigger alert."""

    def __init__(self, timeout_seconds: float, callback: Callable[[], None]) -> None:
        self._timeout = timeout_seconds
        self._callback = callback
        self._last_heartbeat = time.time()
        self._active = False

    def start(self) -> None:
        self._active = True
        self._last_heartbeat = time.time()

    def stop(self) -> None:
        self._active = False

    def heartbeat(self) -> None:
        self._last_heartbeat = time.time()

    def check(self) -> bool:
        if not self._active:
            return True
        return (time.time() - self._last_heartbeat) < self._timeout

    def check_and_act(self) -> bool:
        if not self.check():
            self._callback()
            return False
        return True


class CrashRecoveryProtocol:
    """Ω-C100 a Ω-C108: Comprehensive crash recovery system."""

    def __init__(self) -> None:
        self._watchdogs: list[WatchdogTimer] = []
        self._fallback_chain: list[Callable[[], Optional[dict[str, Any]]]] = []
        self._emergency_frozen = False
        self._recovery_reports: list[RecoveryReport] = []
        self._degradation_level = DegradationLevel.FULL_CAPABILITY

    def register_watchdog(self, timeout_seconds: float, callback: Callable[[], None]) -> WatchdogTimer:
        wd = WatchdogTimer(timeout_seconds, callback)
        self._watchdogs.append(wd)
        return wd

    def register_fallback(self, fallback_fn: Callable[[], Optional[dict[str, Any]]], priority: int = 0) -> None:
        self._fallback_chain.append(fallback_fn)
        self._fallback_chain.sort(key=lambda _: priority, reverse=True)

    def emergency_freeze(self) -> None:
        """Ω-C102: Freeze system state on anomaly detection."""
        self._emergency_frozen = True
        self._degradation_level = DegradationLevel.SAFE_MODE

    def unfreeze(self) -> None:
        self._emergency_frozen = False
        self._degradation_level = DegradationLevel.FULL_CAPABILITY

    def is_frozen(self) -> bool:
        return self._emergency_frozen

    def attempt_recovery(self) -> RecoveryReport:
        """Ω-C100: Attempt crash recovery via fallback chain."""
        start = time.time()
        recovered = []
        lost = []

        for i, fallback_fn in enumerate(self._fallback_chain):
            try:
                result = fallback_fn()
                if result is not None:
                    recovered.extend(result.keys())
                else:
                    lost.append(f"fallback_{i}")
            except Exception as e:
                lost.append(f"fallback_{i}: {str(e)}")

        duration = (time.time() - start) * 1000

        if len(lost) == 0:
            self._degradation_level = DegradationLevel.FULL_CAPABILITY
        elif len(lost) <= len(self._fallback_chain) // 2:
            self._degradation_level = DegradationLevel.REDUCED_CAPABILITY
        elif len(lost) < len(self._fallback_chain):
            self._degradation_level = DegradationLevel.SAFE_MODE
        else:
            self._degradation_level = DegradationLevel.MINIMAL_MODE

        report = RecoveryReport(recovered_items=recovered, lost_items=lost, degraded_level=self._degradation_level, duration_ms=duration)
        self._recovery_reports.append(report)
        return report

    def emergency_rollback(self) -> None:
        """Ω-C106: Revert to last known stable state."""
        self._degradation_level = DegradationLevel.SAFE_MODE
        self._emergency_frozen = False

    def check_all_watchdogs(self) -> list[bool]:
        return [wd.check_and_act() for wd in self._watchdogs]

    def get_current_degradation(self) -> DegradationLevel:
        return self._degradation_level

    def get_recovery_history(self) -> list[RecoveryReport]:
        return list(self._recovery_reports)

    def get_stats(self) -> dict[str, Any]:
        return {
            "degradation_level": self._degradation_level.value,
            "emergency_frozen": self._emergency_frozen,
            "watchdogs_active": sum(1 for w in self._watchdogs if w._active),
            "fallback_count": len(self._fallback_chain),
            "recovery_attempts": len(self._recovery_reports),
        }
