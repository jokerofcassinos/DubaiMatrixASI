"""
SOLÉNN v2 — Meta-Learning Engine (Ω-T145 to Ω-T153)
Online learning, concept drift detection, multi-armed bandit allocation,
strategy pool management, auto-calibration, parameter stability monitoring,
model versioning, and autonomous/human approval routing.

Concept 3: Adaptive Meta-Learning (Ω-T145–T153)
"""

from __future__ import annotations

import math
import random
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from .omega_types import MetaLearningState, RegimeType


@dataclass
class _ParameterTracker:
    """Internal tracking for a single parameter."""
    name: str
    history: deque[float]
    last_value: float
    stability: float
    needs_recalibration: bool
    last_recalibrated: float


# ──────────────────────────────────────────────────────────────
# Ω-T146: Concept Drift Detection Ensemble
# ──────────────────────────────────────────────────────────────

class ConceptDriftDetector:
    """
    Ω-T146: Ensemble of drift detection methods —
    Page-Hinkley, ADWIN (simplified), DDM.
    """

    def __init__(
        self,
        page_hinkley_threshold: float = 0.005,
        window_size: int = 100,
    ) -> None:
        self._ph_threshold = page_hinkley_threshold
        self._ph_sum = 0.0
        self._ph_min = float("inf")
        self._ph_mean = 0.0
        self._ph_n = 0

        self._adwin_window: deque[float] = deque(maxlen=window_size)

        self._ddm_n = 0
        self._ddm_p = 0.0
        self._ddm_s = 0.0
        self._ddm_min_p = 1.0
        self._ddm_min_s = 1.0
        self._ddm_warning_mult = 2.0
        self._ddm_drift_mult = 3.0

        self._drift_detected = False
        self._warning_flag = False
        self._drift_time: float | None = None

    def update(self, value: float) -> dict[str, bool]:
        results: dict[str, bool] = {}

        # Page-Hinkley
        self._ph_n += 1
        self._ph_mean += (value - self._ph_mean) / self._ph_n
        self._ph_sum += value - self._ph_mean - self._ph_threshold
        self._ph_min = min(self._ph_min, self._ph_sum)
        results["page_hinkley"] = (self._ph_sum - self._ph_min) > self._ph_threshold * 50

        # DDM
        is_error = 1.0 if value > 0.5 else 0.0
        self._ddm_p = (self._ddm_p * self._ddm_n + is_error) / (self._ddm_n + 1)
        denom = max(1, self._ddm_n)
        self._ddm_s = math.sqrt(self._ddm_p * (1 - self._ddm_p) / denom) if 0 < self._ddm_p < 1 else 0.0
        self._ddm_n += 1

        if self._ddm_p + self._ddm_s < self._ddm_min_p + self._ddm_min_s:
            self._ddm_min_p = self._ddm_p
            self._ddm_min_s = self._ddm_s

        results["ddm_warning"] = (
            self._ddm_p + self._ddm_s * self._ddm_warning_mult
            > self._ddm_min_p + self._ddm_min_s * self._ddm_warning_mult
        )
        results["ddm_drift"] = (
            self._ddm_p + self._ddm_s * self._ddm_drift_mult
            > self._ddm_min_p + self._ddm_min_s * self._ddm_drift_mult
        )

        # ADWIN (simplified window split)
        self._adwin_window.append(value)
        results["adwin"] = False
        if len(self._adwin_window) >= 30:
            w = list(self._adwin_window)
            mid = len(w) // 2
            left, right = w[:mid], w[mid:]
            ml = sum(left) / len(left)
            mr = sum(right) / len(right)
            eps = math.sqrt(1.0 / (2 * min(len(left), len(right))) * math.log(2 / 0.001))
            results["adwin"] = abs(ml - mr) > eps

        self._drift_detected = (
            results["page_hinkley"] or results["ddm_drift"] or results["adwin"]
        )
        self._warning_flag = results["ddm_warning"]
        if self._drift_detected and self._drift_time is None:
            self._drift_time = time.time()

        return results

    def is_drift_detected(self) -> bool:
        return self._drift_detected

    def is_warning(self) -> bool:
        return self._warning_flag

    def reset(self) -> None:
        self._drift_detected = False
        self._warning_flag = False
        self._drift_time = None
        self._ph_sum = 0.0
        self._ph_min = float("inf")
        self._ph_mean = 0.0
        self._ph_n = 0
        self._ddm_min_p = 1.0
        self._ddm_min_s = 1.0


# ──────────────────────────────────────────────────────────────
# Ω-T148: Thompson Sampling Multi-Armed Bandit
# ──────────────────────────────────────────────────────────────

class ThompsonSamplingAllocator:
    """
    Ω-T148: Thompson Sampling (Beta-Bernoulli) for capital
    allocation across strategies.
    """

    def __init__(self, strategies: list[str] | None = None) -> None:
        self._alpha: dict[str, float] = {}
        self._beta_p: dict[str, float] = {}
        self._n_trades: dict[str, int] = {}
        self._total_pnl: dict[str, float] = {}
        if strategies:
            for s in strategies:
                self.add_strategy(s)

    def add_strategy(self, strategy_id: str) -> None:
        self._alpha[strategy_id] = 1.0
        self._beta_p[strategy_id] = 1.0
        self._n_trades[strategy_id] = 0
        self._total_pnl[strategy_id] = 0.0

    def remove_strategy(self, strategy_id: str) -> None:
        self._alpha.pop(strategy_id, None)
        self._beta_p.pop(strategy_id, None)
        self._n_trades.pop(strategy_id, None)
        self._total_pnl.pop(strategy_id, None)

    def update_outcome(self, strategy_id: str, was_success: bool, pnl: float) -> None:
        """Ω-T148: Update posterior after trade outcome."""
        if strategy_id not in self._alpha:
            self.add_strategy(strategy_id)
        if was_success:
            self._alpha[strategy_id] += 1
        else:
            self._beta_p[strategy_id] += 1
        self._n_trades[strategy_id] += 1
        self._total_pnl[strategy_id] += pnl

    def sample_and_select(self) -> str | None:
        """Select strategy by sampling from posteriors."""
        if not self._alpha:
            return None
        best_strategy = None
        best_sample = -1.0
        for sid in self._alpha:
            a = self._alpha[sid]
            b = self._beta_p[sid]
            sample = random.betavariate(a, b)
            if sample > best_sample:
                best_sample = sample
                best_strategy = sid
        return best_strategy

    def get_expected_win_rates(self) -> dict[str, float]:
        """Return posterior mean win rate for each strategy."""
        return {
            sid: self._alpha[sid] / (self._alpha[sid] + self._beta_p[sid])
            for sid in self._alpha
            if (self._alpha[sid] + self._beta_p[sid]) > 0
        }

    def get_posteriors(self) -> dict[str, tuple[float, float]]:
        return {sid: (self._alpha[sid], self._beta_p[sid]) for sid in self._alpha}


# ──────────────────────────────────────────────────────────────
# Ω-T150-T151: Parameter Stability & Auto-Calibration
# ──────────────────────────────────────────────────────────────

class ParameterStabilityMonitor:
    """
    Ω-T150-T151: Tracks parameter values over time, computes
    stability scores, and flags parameters needing recalibration.
    """

    def __init__(self, window_size: int = 200, instability_threshold: float = 0.3) -> None:
        self._params: dict[str, _ParameterTracker] = {}
        self._window_size = window_size
        self._instability_threshold = instability_threshold

    def update(self, param_name: str, value: float) -> bool:
        """
        Update parameter value. Returns True if recalibration needed.
        """
        if param_name not in self._params:
            self._params[param_name] = _ParameterTracker(
                name=param_name,
                history=deque(maxlen=self._window_size),
                last_value=value,
                stability=1.0,
                needs_recalibration=False,
                last_recalibrated=time.time(),
            )

        tracker = self._params[param_name]
        tracker.history.append(value)

        # Compute stability: 1 / (1 + CV) where CV = coeff of variation
        if len(tracker.history) >= 10:
            values = list(tracker.history)
            mean_v = sum(values) / len(values)
            std_v = (sum((x - mean_v) ** 2 for x in values) / max(1, len(values) - 1)) ** 0.5
            cv = std_v / abs(mean_v) if mean_v != 0 else 0.0
            tracker.stability = 1.0 / (1.0 + cv)
            tracker.needs_recalibration = tracker.stability < self._instability_threshold

        tracker.last_value = value
        return tracker.needs_recalibration

    def get_stability_scores(self) -> dict[str, float]:
        return {name: t.stability for name, t in self._params.items()}

    def get_needing_recalibration(self) -> list[str]:
        return [name for name, t in self._params.items() if t.needs_recalibration]


# ──────────────────────────────────────────────────────────────
# Ω-T145-T153: MetaLearningEngine (unified)
# ──────────────────────────────────────────────────────────────

class MetaLearningEngine:
    """
    SOLÉNN v2 — Meta-Learning Engine (Ω-T145 to Ω-T153)
    Orchestrates drift detection, Thompson Sampling,
    parameter stability, model versioning, and approval routing.
    """

    AUTONOMOUS_THRESHOLD = 0.8  # Parameters with stability >= this are auto-adjusted

    def __init__(self, strategy_ids: list[str] | None = None) -> None:
        self.drift_detector = ConceptDriftDetector()
        self.bandit = ThompsonSamplingAllocator(strategy_ids)
        self.param_monitor = ParameterStabilityMonitor()

        # Ω-T152: Model versioning
        self._versions: dict[str, str] = {}
        self._version_history: dict[str, list[tuple[str, float]]] = {}  # component -> [(version, timestamp)]

        # Ω-T153: Autonomous vs human routing
        self._pending_approvals: list[dict[str, Any]] = {}
        self._autonomous_count = 0
        self._human_approval_count = 0

        # Ω-T150: Learning velocity
        self._bug_discovery_times: dict[str, float] = {}
        self._patch_deploy_times: dict[str, float] = {}
        self._learning_velocities: deque[float] = deque(maxlen=100)

        # Ω-T145: Online learning state
        self._global_win_count = 0
        self._global_loss_count = 0
        self._learning_rate = 0.01

    def record_trade_outcome(
        self,
        strategy_id: str,
        pnl: float,
        was_win: bool,
        parameter_values: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """
        Master entry point: update all meta-learning components
        after a trade outcome.
        """
        # Ω-T148: Update Thompson Sampling
        self.bandit.update_outcome(strategy_id, was_win, pnl)

        # Ω-T145: Update global counts
        if was_win:
            self._global_win_count += 1
        else:
            self._global_loss_count += 1

        # Ω-T146: Check for concept drift (on loss)
        drift_result = None
        if not was_win:
            drift_result = self.drift_detector.update(1.0)  # 1.0 = error signal
        else:
            drift_result = self.drift_detector.update(0.0)

        # Ω-T150-T151: Update parameter stability
        params_needing_recal = []
        if parameter_values:
            for param_name, value in parameter_values.items():
                needs_recal = self.param_monitor.update(param_name, value)
                if needs_recal:
                    params_needing_recal.append(param_name)

        return {
            "drift_detected": self.drift_detector.is_drift_detected(),
            "drift_result": drift_result,
            "params_needing_recalibration": params_needing_recal,
            "recommended_strategy": self.bandit.sample_and_select(),
        }

    def get_strategy_allocation(self) -> dict[str, float]:
        """Ω-T148: Get recommended capital allocation across strategies."""
        win_rates = self.bandit.get_expected_win_rates()
        if not win_rates:
            return {}
        # Normalize to sum to 1.0
        total = sum(win_rates.values())
        if total > 0:
            return {s: wr / total for s, wr in win_rates.items()}
        return {s: 1.0 / len(win_rates) for s in win_rates}

    def get_meta_state(self) -> MetaLearningState:
        """Ω-T145-T153: Full meta-learning state for serialization."""
        return MetaLearningState(
            strategy_win_rates=self.bandit.get_expected_win_rates(),
            strategy_posteriors=self.bandit.get_posteriors(),
            concept_drift_detected=self.drift_detector.is_drift_detected(),
            drift_detected_at=self.drift_detector._drift_time,
            parameters_needing_recalibration=self.param_monitor.get_needing_recalibration(),
            parameter_stability=self.param_monitor.get_stability_scores(),
            model_versions=dict(self._versions),
            autonomous_adjustments_count=self._autonomous_count,
            pending_human_approvals=list(self._pending_approvals.values()),
            learning_velocity=self._compute_learning_velocity(),
        )

    # ── Ω-T152: Model versioning ──

    def register_version(self, component: str, version: str) -> None:
        self._versions[component] = version
        if component not in self._version_history:
            self._version_history[component] = []
        self._version_history[component].append((version, time.time()))

    def rollback_version(self, component: str) -> str | None:
        """Rollback to previous version."""
        history = self._version_history.get(component)
        if not history or len(history) < 2:
            return None
        history.pop()
        prev_version = history[-1][0]
        self._versions[component] = prev_version
        return prev_version

    # ── Ω-T153: Autonomous vs human routing ──

    def propose_change(
        self,
        component: str,
        change_type: str,
        current_value: Any,
        proposed_value: Any,
        stability_score: float,
        justification: str,
    ) -> str:
        """
        Ω-T153: Route change proposal to autonomous or human approval.
        High stability → autonomous. Low stability or structural → human.
        """
        change_id = f"change-{uuid.uuid4().hex[:8]}"

        if stability_score >= self.AUTONOMOUS_THRESHOLD and change_type == "parameter":
            # Autonomous adjustment
            self._autonomous_count += 1
            return change_id  # Applied immediately
        else:
            # Requires human approval
            self._pending_approvals[change_id] = {
                "component": component,
                "change_type": change_type,
                "current_value": current_value,
                "proposed_value": proposed_value,
                "stability_score": stability_score,
                "justification": justification,
                "timestamp": time.time(),
            }
            self._human_approval_count += 1
            return change_id

    def approve_change(self, change_id: str, approved: bool) -> bool:
        """Human approves or rejects a pending change."""
        if change_id not in self._pending_approvals:
            return False
        if approved:
            change = self._pending_approvals[change_id]
            self._autonomous_count += 1  # Count as applied
        del self._pending_approvals[change_id]
        return approved

    def record_bug_discovery(self, bug_id: str) -> None:
        """Ω-T135: Record time of bug discovery."""
        self._bug_discovery_times[bug_id] = time.time()

    def record_patch_deploy(self, bug_id: str) -> None:
        """Ω-T135: Record time of patch deployment."""
        self._patch_deploy_times[bug_id] = time.time()
        if bug_id in self._bug_discovery_times:
            elapsed = self._patch_deploy_times[bug_id] - self._bug_discovery_times[bug_id]
            self._learning_velocities.append(elapsed)

    def _compute_learning_velocity(self) -> float:
        if not self._learning_velocities:
            return 0.0
        return 1.0 / (sum(self._learning_velocities) / len(self._learning_velocities) + 1e-10)

    def get_pending_approvals(self) -> list[dict[str, Any]]:
        return list(self._pending_approvals.values())
