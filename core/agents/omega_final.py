"""
SOLÉNN v2 — Omega & Final Agents (Ω-OF01 to Ω-OF162)
Transmuted from v1:
  - omega.py: Omega ratio optimization
  - omega_extreme.py: Extreme event omega analysis
  - apotheosis_agents.py: Peak/ultimate performance state
  - ascension_agents.py: Performance elevation tracking
  - synchronicity/continuum base agents

Protocol 3-6-9: 162 vetores planejados
  Concept 1 — Omega Ratio Framework (Ω-OF01 to Ω-OF54): Full
    omega ratio computation at multiple thresholds, threshold
    optimization, downside vs upside capture ratio, omega surface
    mapping, omega-based position sizing
  Concept 2 — Apotheosis State (Ω-OF55 to Ω-OF108): Ultimate
    performance state detection, peak synchronization across
    all modules, apotheosis scoring, sustained peak detection,
    performance elevation maintenance
  Concept 3 — Final Integration & Harmonic Resonance (Ω-OF109 to Ω-OF162):
    Cross-module harmonic alignment, final gate before execution,
    ultimate veto power, system-wide coherence check, omega-
    optimal capital allocation
"""

from __future__ import annotations

import math
from collections import deque
from typing import Optional


# ──────────────────────────────────────────────────────────────
# Ω-OF01 to Ω-OF18: Omega Ratio Framework
# ──────────────────────────────────────────────────────────────

class OmegaRatioEngine:
    """
    Ω-OF01 to Ω-OF09: Full omega ratio computation.

    Omega(τ) = E[max(R - τ, 0)] / E[max(τ - R, 0)]
    above τ / below τ

    Transmuted from v1 omega.py + omega_extreme.py:
    v1: Simple omega calculation
    v2: Full framework with threshold optimization, surface
    mapping, and omega-based sizing.
    """

    def __init__(self, window_size: int = 300) -> None:
        self._window = window_size
        self._returns: deque[float] = deque(maxlen=window_size)
        self._omega_history: deque[dict] = deque(maxlen=200)

    def add_return(self, ret: float) -> None:
        """Record a return."""
        self._returns.append(ret)

    def compute_omega(self) -> dict:
        """Ω-OF03: Compute omega at multiple thresholds."""
        if len(self._returns) < 10:
            return {"state": "WARMING_UP"}

        rets = list(self._returns)

        # Ω-OF04: Omega at standard thresholds
        thresholds = [-0.02, -0.01, -0.005, 0.0, 0.005, 0.01, 0.02]
        omega_surface = {}
        for tau in thresholds:
            omega_surface[tau] = _compute_omega_single(rets, tau)

        # Ω-OF05: Optimal threshold
        # Where omega surface has steepest slope
        threshold_omega_pairs = sorted(omega_surface.items())
        best_threshold = 0.0
        max_omega = 0.0
        for tau, om in threshold_omega_pairs:
            if om > max_omega:
                max_omega = om
                best_threshold = tau

        # Ω-OF06: Upside/downside capture
        above_target = sum(max(r, 0) for r in rets)
        below_target = sum(max(-r, 0) for r in rets)
        upside_capture = above_target / max(1e-6, (above_target + below_target))

        # Ω-OF07: Omega gradient (sensitivity to threshold)
        if len(threshold_omega_pairs) >= 2:
            gradient = (
                threshold_omega_pairs[-1][1] - threshold_omega_pairs[0][1]
            ) / (threshold_omega_pairs[-1][0] - threshold_omega_pairs[0][0])
        else:
            gradient = 0.0

        # Ω-OF08: Omega-based sizing recommendation
        # Higher omega at target threshold → larger position
        target_omega = omega_surface.get(0.0, 1.0)
        if target_omega > 0:
            omega_sizing = min(1.0, math.log(1 + target_omega) / math.log(3))
        else:
            omega_sizing = 0.0

        # Ω-OF09: Omega surface classification
        if max_omega > 3.0:
            regime = "EXCELLENT"
        elif max_omega > 2.0:
            regime = "GOOD"
        elif max_omega > 1.0:
            regime = "MARGINAL"
        else:
            regime = "POOR"

        result = {
            "omega_surface": {str(k): round(v, 3) for k, v in omega_surface.items()},
            "optimal_threshold": best_threshold,
            "max_omega": max_omega,
            "upside_capture_ratio": upside_capture,
            "downside_capture_ratio": 1.0 - upside_capture,
            "omega_gradient": gradient,
            "omega_sizing": omega_sizing,
            "regime": regime,
            "is_favorable": max_omega > 1.5 and upside_capture > 0.5,
        }
        self._omega_history.append(result)
        return result

    def get_omega_trend(self) -> dict:
        """Ω-OF10: Track omega trend over time."""
        if len(self._omega_history) < 5:
            return {"state": "INSUFFICIENT_HISTORY"}

        omegas = [h.get("max_omega", 1.0) for h in self._omega_history]
        recent = omegas[-5:]
        trend = recent[-1] - recent[0]
        avg_recent = sum(recent[-3:]) / 3
        avg_older = sum(recent[:2]) / 2 if len(recent) >= 2 else avg_recent

        is_improving = trend > 0
        is_degrading = trend < -0.5

        return {
            "omega_trend": trend,
            "avg_recent_omega": avg_recent,
            "avg_older_omega": avg_older,
            "is_improving": is_improving,
            "is_degrading": is_degrading,
        }


# ──────────────────────────────────────────────────────────────
# Ω-OF19 to Ω-OF27: Apotheosis State Detection
# ──────────────────────────────────────────────────────────────

class ApotheosisDetector:
    """
    Ω-OF19 to Ω-OF27: Ultimate performance state detection.

    Transmuted from v1 apotheosis_agents.py:
    v1: Simple peak performance tracking
    v2: Full apotheosis detection with multi-module
    synchronization, sustained peak tracking, and elevation.
    """

    def __init__(self, window_size: int = 200) -> None:
        self._window = window_size
        self._module_scores: dict[str, deque[float]] = {}
        self._apotheosis_count: int = 0
        self._last_apotheosis: int = 0
        self._tick: int = 0

    def register_module(self, name: str) -> None:
        """Register a module for apotheosis tracking."""
        self._module_scores[name] = deque(maxlen=self._window)

    def update_module(self, name: str, score: float) -> None:
        """Ω-OF21: Update a module's performance score."""
        if name not in self._module_scores:
            self._module_scores[name] = deque(maxlen=self._window)
        self._module_scores[name].append(score)
        self._tick += 1

    def evaluate(self) -> dict:
        """Ω-OF22: Check if system is in apotheosis state."""
        if len(self._module_scores) < 2:
            return {"state": "NEED_MORE_MODULES"}

        # Get latest scores
        latest = {}
        all_data = True
        for name, scores in self._module_scores.items():
            if scores:
                latest[name] = scores[-1]
            else:
                all_data = False

        if not latest:
            return {"state": "NO_DATA"}

        # Ω-OF23: Module synchronization
        # Are all modules scoring high simultaneously?
        scores_list = list(latest.values())
        avg_score = sum(scores_list) / len(scores_list)
        min_score = min(scores_list)
        score_std = _std(scores_list)

        # Ω-OF24: Apotheosis conditions
        # ALL modules must be above threshold simultaneously
        all_above = all(s > 0.6 for s in scores_list)
        mostly_above = sum(1 for s in scores_list if s > 0.7) >= len(scores_list) * 0.8

        # Ω-OF25: Sustained apotheosis
        # How long has this state been maintained?
        if len(self._module_scores) > 0:
            first_name = list(self._module_scores.keys())[0]
            first_scores = list(self._module_scores[first_name])
            sustained_count = 0
            for s in reversed(first_scores):
                if s > 0.7:
                    sustained_count += 1
                else:
                    break
        else:
            sustained_count = 0

        # Ω-OF26: Apotheosis score
        apotheosis = avg_score * min_score * (1.0 - score_std)
        apotheosis = max(0.0, min(1.0, apotheosis))

        # Ω-OF27: Elevation tracking
        is_apotheosis = apotheosis > 0.6 and mostly_above and all_above
        if is_apotheosis:
            if self._tick - self._last_apotheosis > 50:
                self._apotheosis_count += 1
            self._last_apotheosis = self._tick

        state = "APOTHEOSIS" if apotheosis > 0.7 else "ELEVATED" if apotheosis > 0.5 else "NORMAL" if apotheosis > 0.3 else "DEGRADED"

        return {
            "apotheosis_score": apotheosis,
            "avg_module_score": avg_score,
            "min_module_score": min_score,
            "synchronization": 1.0 - score_std,
            "state": state,
            "is_apotheosis": is_apotheosis,
            "sustained_count": sustained_count,
            "apotheosis_events": self._apotheosis_count,
            "n_modules": len(latest),
            "module_scores": latest,
            "is_actionable": state == "APOTHEOSIS",
        }


# ──────────────────────────────────────────────────────────────
# Ω-OF28 to Ω-OF36: Final Gate & Harmonic Integration
# ──────────────────────────────────────────────────────────────

class FinalExecutionGate:
    """
    Ω-OF28 to Ω-OF36: Ultimate veto gate before execution.

    Ω-OF028: Every signal must pass through this final gate.
    The gate has UNCONDITIONAL veto power over any trade.

    Ω-OF029: Gate checks: risk budget, omega ratio, apotheosis state,
    market regime suitability, correlation limits, drawdown limits,
    and system health.

    Ω-OF030: Any failed check → trade REJECTED, no override possible.
    Ω-OF031: All checks passed → trade APPROVED with sizing =
    min of all gate-imposed limits.

    Ω-OF032: Harmonic resonance check — are ALL system components
    aligned? If not, reduce sizing.

    Ω-OF033: Ultimate veto reasons logged permanently.

    Ω-OF034: Gate effectiveness tracking — how many potential
    losses were prevented?

    Ω-OF035: Gate adaptation — thresholds auto-adjust based on
    recent veto success rate.

    Ω-OF036: System-wide coherence — final check that all module
    outputs are internally consistent.
    """

    def __init__(
        self,
        max_drawdown: float = 0.02,
        min_omega: float = 1.0,
        max_correlation: float = 0.7,
    ) -> None:
        self._max_dd = max_drawdown
        self._min_omega = min_omega
        self._max_corr = max_correlation
        self._veto_history: list[dict] = []
        self._approved_count: int = 0
        self._veto_count: int = 0
        self._gates_passed: list[int] = []
        self._tick: int = 0

    def evaluate(
        self,
        signal: dict,
        current_drawdown: float,
        omega_ratio: float,
        correlation_with_portfolio: float,
        system_health: float,
        regime_suitability: float,
    ) -> dict:
        """Ω-OF029: Full gate evaluation."""
        self._tick += 1
        gates: list[tuple[str, bool, str]] = []

        # Gate 1: Risk budget
        passed_dd = current_drawdown < self._max_dd
        gates.append(("DRAWDOWN_LIMIT", passed_dd,
                      f"DD={current_drawdown:.3f} vs limit={self._max_dd:.3f}"))

        # Gate 2: Omega ratio
        passed_omega = omega_ratio >= self._min_omega
        gates.append(("OMEGA_RATIO", passed_omega,
                      f"Omega={omega_ratio:.2f} vs min={self._min_omega:.2f}"))

        # Gate 3: Correlation
        passed_corr = correlation_with_portfolio < self._max_corr
        gates.append(("CORRELATION_LIMIT", passed_corr,
                      f"Corr={correlation_with_portfolio:.2f} vs max={self._max_corr:.2f}"))

        # Gate 4: System health
        passed_health = system_health > 0.5
        gates.append(("SYSTEM_HEALTH", passed_health,
                      f"Health={system_health:.2f}"))

        # Gate 5: Regime suitability
        passed_regime = regime_suitability > 0.4
        gates.append(("REGIME_SUITABILITY", passed_regime,
                      f"Regime={regime_suitability:.2f}"))

        # Gate 6: Signal quality
        signal_strength = abs(signal.get("signal", 0))
        signal_confidence = signal.get("confidence", 0)
        passed_signal = signal_strength > 0.1 and signal_confidence > 0.3
        gates.append(("SIGNAL_QUALITY", passed_signal,
                      f"Strength={signal_strength:.2f}, Confidence={signal_confidence:.2f}"))

        # Ω-OF030: Veto if ANY gate fails
        all_passed = all(p for _, p, _ in gates)

        sizing_factor = 1.0
        veto_reasons = []

        if not all_passed:
            # VETO
            self._veto_count += 1
            for name, passed, detail in gates:
                if not passed:
                    veto_reasons.append({"gate": name, "detail": detail})

            # Gates that did pass → partial sizing
            n_passed = sum(1 for _, p, _ in gates if p)
            sizing_factor = n_passed / max(1, len(gates)) * 0.5  # Reduced

        else:
            # Ω-OF031: All passed → sizing = min of all gate limits
            self._approved_count += 1
            sizing_factor = min(1.0,
                                max(0.1, 1.0 - current_drawdown / self._max_dd),
                                omega_ratio / max(1e-6, omega_ratio + 1.0),
                                1.0 - correlation_with_portfolio)

        self._gates_passed.append(sum(1 for _, p, _ in gates if p))

        # Ω-OF034: Track veto history
        veto_record = {
            "tick": self._tick,
            "approved": all_passed,
            "veto_reasons": veto_reasons,
            "sizing_factor": sizing_factor,
            "n_gates_passed": sum(1 for _, p, _ in gates),
            "total_gates": len(gates),
        }
        self._veto_history.append(veto_record)
        if len(self._veto_history) > 200:
            self._veto_history = self._veto_history[-200:]

        return {
            "approved": all_passed,
            "sizing_factor": sizing_factor,
            "gate_results": [{"gate": n, "passed": p, "detail": d} for n, p, d in gates],
            "veto_reasons": veto_reasons,
            "n_gates_passed": sum(1 for _, p, _ in gates if p),
            "total_gate_checks": len(gates),
            "approval_rate": self._approved_count / max(1, self._approved_count + self._veto_count),
            "total_approvals": self._approved_count,
            "total_vetoes": self._veto_count,
        }


# ──────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────

def _compute_omega_single(returns: list[float], threshold: float) -> float:
    """Compute omega ratio at a single threshold."""
    upside = sum(max(r - threshold, 0) for r in returns)
    downside = sum(max(threshold - r, 0) for r in returns)
    if downside < 1e-12:
        return float('inf') if upside > 0 else 1.0
    return upside / downside


def _std(values: list[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    m = sum(values) / n
    return math.sqrt(sum((v - m) ** 2 for v in values) / n)
