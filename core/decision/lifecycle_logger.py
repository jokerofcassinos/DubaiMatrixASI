"""
SOLÉNN v2 — Lifecycle Logger: Trading Cycle Forensics (Ω-LL01 a Ω-LL54)
Replaces v1 lifecycle_logger.py. Captures the complete truth of each
trading cycle — signal formation, decision rationale, execution quality,
and post-trade analysis. Provides structured lifecycle blocks with
full audit trail for post-mortem investigation.

Concept 1: Cycle Capture & Truth Logging (Ω-LL01–LL18)
  Each trading cycle is captured as an atomic unit with: signal inputs,
  model confidence, state vector, swarm results, risk assessment, and
  final decision. No partial logging — the complete truth or nothing.

Concept 2: Structured Format & Export (Ω-LL19–LL36)
  Lifecycle blocks written in structured format with sections:
  signal_formation, decision_rationale, execution_result, post_trade.
  JSON export for automated analysis. Cycle ID provides traceability.

Concept 3: Post-Trade Forensics & Audit (Ω-LL37–LL54)
  Forensic analysis module for winning and losing trades. 12-layer
  investigation protocol for loss trades. Pattern extraction across
  lifecycle blocks to identify systemic issues.
"""

from __future__ import annotations

import json
import os
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ──────────────────────────────────────────────────────────────
# Ω-LL01 to Ω-LL18: Cycle Capture & Truth Logging
# ──────────────────────────────────────────────────────────────


class TradeOutcome(Enum):
    """Ω-LL01: Final outcome of a trade."""

    WIN = "win"
    LOSS = "loss"
    BREAK_EVEN = "break_even"
    UNKNOWN = "unknown"


@dataclass
class SignalFormation:
    """Ω-LL02: How the signal was formed this cycle."""

    action: str  # LONG, SHORT, WAIT
    raw_signal: float
    phi: float
    coherence: float
    n_bull_agents: int
    n_bear_agents: int
    n_neutral_agents: int
    swarm_direction: str
    swarm_strength: float
    swarm_confidence: float
    regime: str
    state_hash: str
    top_bull_agents: list[str]
    top_bear_agents: list[str]


@dataclass
class DecisionRationale:
    """Ω-LL03: Why the decision was made."""

    action: str
    confidence: float
    sizing_pct: float
    stop_loss: float = 0.0
    take_profit: float = 0.0
    risk_reward_ratio: float = 0.0
    veto_count: int = 0
    veto_reasons: list[str] = field(default_factory=list)
    supporting_factors: list[str] = field(default_factory=list)
    rejected_factors: list[str] = field(default_factory=list)


@dataclass
class ExecutionResult:
    """Ω-LL04: How the order was executed."""

    order_id: str = ""
    entry_price: float = 0.0
    exit_price: float = 0.0
    lot_size: float = 0.0
    slippage: float = 0.0
    commission: float = 0.0
    funding: float = 0.0
    net_pnl: float = 0.0
    gross_pnl: float = 0.0
    entry_latency_ms: float = 0.0
    exit_latency_ms: float = 0.0
    holding_time_sec: float = 0.0
    outcome: TradeOutcome = TradeOutcome.UNKNOWN
    reason: str = ""


@dataclass
class CycleLog:
    """Ω-LL05: Complete trading cycle record."""

    cycle_id: int
    timestamp_ns: int
    signal: SignalFormation
    decision: DecisionRationale
    execution: ExecutionResult
    internal_logs: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    forensic_report: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "timestamp_ns": self.timestamp_ns,
            "signal": {
                "action": self.signal.action,
                "raw_signal": self.signal.raw_signal,
                "phi": self.signal.phi,
                "coherence": self.signal.coherence,
                "regime": self.signal.regime,
                "state_hash": self.signal.state_hash,
                "swarm_direction": self.signal.swarm_direction,
                "swarm_strength": self.signal.swarm_strength,
                "swarm_confidence": self.signal.swarm_confidence,
                "n_bull_agents": self.signal.n_bull_agents,
                "n_bear_agents": self.signal.n_bear_agents,
                "n_neutral_agents": self.signal.n_neutral_agents,
                "top_bull_agents": self.signal.top_bull_agents,
                "top_bear_agents": self.signal.top_bear_agents,
            },
            "decision": {
                "action": self.decision.action,
                "confidence": self.decision.confidence,
                "sizing_pct": self.decision.sizing_pct,
                "stop_loss": self.decision.stop_loss,
                "take_profit": self.decision.take_profit,
                "risk_reward_ratio": self.decision.risk_reward_ratio,
                "veto_count": self.decision.veto_count,
                "veto_reasons": self.decision.veto_reasons,
                "supporting_factors": self.decision.supporting_factors,
                "rejected_factors": self.decision.rejected_factors,
            },
            "execution": {
                "order_id": self.execution.order_id,
                "entry_price": self.execution.entry_price,
                "exit_price": self.execution.exit_price,
                "lot_size": self.execution.lot_size,
                "slippage": self.execution.slippage,
                "commission": self.execution.commission,
                "funding": self.execution.funding,
                "net_pnl": self.execution.net_pnl,
                "gross_pnl": self.execution.gross_pnl,
                "entry_latency_ms": self.execution.entry_latency_ms,
                "exit_latency_ms": self.execution.exit_latency_ms,
                "holding_time_sec": self.execution.holding_time_sec,
                "outcome": self.execution.outcome.value,
                "reason": self.execution.reason,
            },
            "n_internal_logs": len(self.internal_logs),
            "context": self.context,
            "forensic_report": self.forensic_report,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str, indent=2)


# ──────────────────────────────────────────────────────────────
# Ω-LL19 to Ω-LL36: Structured Format & Export
# ──────────────────────────────────────────────────────────────


class StructuredLogger:
    """Ω-LL20: Writes lifecycle blocks in structured format."""

    def __init__(self, log_dir: str = "logs") -> None:
        self._log_dir = log_dir
        self._log_path = os.path.join(log_dir, "lifecycle.log")
        self._json_path = os.path.join(log_dir, "lifecycle.jsonl")

    def write_block(self, cycle: CycleLog) -> None:
        """Ω-LL21: Write a formatted lifecycle block to file."""
        try:
            os.makedirs(self._log_dir, exist_ok=True)

            with open(self._log_path, "a", encoding="utf-8") as f:
                # Write formatted text block
                ts_fmt = cycle.to_dict()
                ts_fmt["timestamp"] = cycle.timestamp_ns / 1e9

                f.write("=" * 80 + "\n")
                f.write(f"CYCLE #{cycle.cycle_id} | ts={ts_fmt['timestamp']:.0f}s | Regime: {cycle.signal.regime}\n")
                f.write("-" * 80 + "\n")

                # Signal Formation
                f.write("SIGNAL FORMATION:\n")
                f.write(f"  Action: {cycle.signal.action} | Signal: {cycle.signal.raw_signal:+.4f} | "
                        f"Phi: {cycle.signal.phi:.4f} | Coherence: {cycle.signal.coherence:.2%}\n")
                f.write(f"  Swarm: {cycle.signal.swarm_direction} "
                        f"(strength={cycle.signal.swarm_strength:.2f}, "
                        f"conf={cycle.signal.swarm_confidence:.2f})\n")
                f.write(f"  Agents: BULL[{cycle.signal.n_bull_agents}] "
                        f"BEAR[{cycle.signal.n_bear_agents}] "
                        f"NEUTRAL[{cycle.signal.n_neutral_agents}]\n")

                # Decision Rationale
                f.write("DECISION:\n")
                f.write(f"  Action: {cycle.decision.action} | "
                        f"Confidence: {cycle.decision.confidence:.2%} | "
                        f"Sizing: {cycle.decision.sizing_pct:.1f}%\n")
                f.write(f"  R:R = {cycle.decision.risk_reward_ratio:.1f}:1 | "
                        f"SL={cycle.decision.stop_loss:.2f} | "
                        f"TP={cycle.decision.take_profit:.2f}\n")
                if cycle.decision.veto_count > 0:
                    f.write(f"  Vetoes: {cycle.decision.veto_count}\n")
                    for v in cycle.decision.veto_reasons:
                        f.write(f"    - {v}\n")

                # Execution
                f.write("EXECUTION:\n")
                f.write(f"  Entry: {cycle.execution.entry_price:.2f} | "
                        f"Exit: {cycle.execution.exit_price:.2f} | "
                        f"P&L: {cycle.execution.net_pnl:+.2f}\n")
                f.write(f"  Lot: {cycle.execution.lot_size} | "
                        f"Slippage: {cycle.execution.slippage:.2f} | "
                        f"Commission: {cycle.execution.commission:.2f}\n")
                f.write(f"  Outcome: {cycle.execution.outcome.value} | "
                        f"Holding: {cycle.execution.holding_time_sec:.1f}s\n")

                if cycle.execution.reason:
                    f.write(f"  Reason: {cycle.execution.reason}\n")

                if cycle.forensic_report:
                    f.write(f"FORENSIC:\n{cycle.forensic_report}\n")

                if cycle.internal_logs:
                    f.write("INTERNAL LOGS:\n")
                    for line in cycle.internal_logs[-20:]:  # Last 20 logs max
                        f.write(f"  {line}\n")

                f.write("=" * 80 + "\n\n")

            # Write JSON for automated analysis
            with open(self._json_path, "a", encoding="utf-8") as f:
                f.write(cycle.to_json() + "\n")

        except (OSError, PermissionError):
            pass  # Graceful degradation

    def write_json_line(self, cycle: CycleLog) -> None:
        """Write single JSON line for stream processing."""
        try:
            os.makedirs(self._log_dir, exist_ok=True)
            with open(self._json_path, "a", encoding="utf-8") as f:
                f.write(cycle.to_json() + "\n")
        except (OSError, PermissionError):
            pass


# ──────────────────────────────────────────────────────────────
# Ω-LL37 to Ω-LL54: Post-Trade Forensics & Audit
# ──────────────────────────────────────────────────────────────


class ForensicAnalyzer:
    """Ω-LL38: Post-trade forensic investigation."""

    def __init__(self) -> None:
        self._cycles: deque[CycleLog] = deque(maxlen=10000)
        self._loss_trades: list[CycleLog] = []

    def record(self, cycle: CycleLog) -> None:
        self._cycles.append(cycle)
        if cycle.execution.outcome == TradeOutcome.LOSS:
            self._loss_trades.append(cycle)

    def investigate_loss(self, cycle: CycleLog) -> str:
        """Ω-LL39: 12-layer forensic investigation of a loss trade."""
        layers: list[str] = []

        # Layer 1: Data integrity
        layers.append(f"[L1:DATA] Regime: {cycle.signal.regime} | State: {cycle.signal.state_hash}")

        # Layer 2: Signal quality
        layers.append(f"[L2:SIGNAL] Raw={cycle.signal.raw_signal:+.4f} | Phi={cycle.signal.phi:.4f} | Coherence={cycle.signal.coherence:.2%}")

        # Layer 3: Swarm consensus
        layers.append(f"[L3:SWARM] Dir={cycle.signal.swarm_direction} | "
                      f"Bull={cycle.signal.n_bull_agents} vs Bear={cycle.signal.n_bear_agents}")

        # Layer 4: Risk assessment
        layers.append(f"[L4:RISK] Sizing={cycle.decision.sizing_pct:.1f}% | "
                      f"R:R={cycle.decision.risk_reward_ratio:.1f}:1")

        # Layer 5: Execution quality
        layers.append(f"[L5:EXEC] Slippage={cycle.execution.slippage:.2f} | "
                      f"Commission={cycle.execution.commission:.2f} | "
                      f"Entry latency={cycle.execution.entry_latency_ms:.2f}ms")

        # Layer 6: Was the exit correct?
        is_correct_exit = cycle.execution.reason not in ("error", "timeout", "disconnected")
        layers.append(f"[L6:EXIT] Correct exit procedure: {is_correct_exit} | "
                      f"Reason: {cycle.execution.reason}")

        # Layer 7: Market conditions
        layers.append(f"[L7:MARKET] Holding time: {cycle.execution.holding_time_sec:.1f}s | "
                      f"Outcome: {cycle.execution.outcome.value}")

        # Layer 8: Against vetoes?
        if cycle.decision.veto_count > 0:
            layers.append(f"[L8:VETO] WARNING: Trade proceeded despite {cycle.decision.veto_count} veto(s)")
            for v in cycle.decision.veto_reasons[:5]:
                layers.append(f"       - {v}")

        # Layer 9: Commission ate the alpha?
        if cycle.execution.commission > abs(cycle.execution.gross_pnl):
            layers.append(f"[L9:COMM] WARNING: Commission ({cycle.execution.commission:.2f}) exceeded gross P&L ({cycle.execution.gross_pnl:.2f})")

        # Layer 10: Similar historical losses
        similar_hist = self.find_similar_losses(cycle, top_k=3)
        if similar_hist:
            layers.append(f"[L10:HISTORY] {len(similar_hist)} similar losses found")

        # Layer 11: What changed between signal and execution?
        layers.append(f"[L11:TIMING] Entry latency: {cycle.execution.entry_latency_ms:.2f}ms")

        # Layer 12: Root cause summary
        layers.append(f"[L12:ROOT_CAUSE] Net P&L: {cycle.execution.net_pnl:+.2f} | "
                      f"Forensic conclusion: investigate regime={cycle.signal.regime}, "
                      f"state={cycle.signal.state_hash}")

        return "\n".join(layers)

    def find_similar_losses(
        self, cycle: CycleLog, top_k: int = 3
    ) -> list[CycleLog]:
        """Ω-LL40: Find similar historical loss trades."""
        scored: list[tuple[float, CycleLog]] = []

        for hist in self._loss_trades:
            if hist.cycle_id == cycle.cycle_id:
                continue
            score = 0.0
            if hist.signal.regime == cycle.signal.regime:
                score += 0.3
            if hist.signal.state_hash == cycle.signal.state_hash:
                score += 0.3
            if abs(hist.signal.phi - cycle.signal.phi) < 0.05:
                score += 0.2
            if hist.decision.action == cycle.decision.action:
                score += 0.2
            scored.append((score, hist))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:top_k]]

    def extract_patterns(self) -> dict[str, Any]:
        """Ω-LL41: Extract recurring loss patterns from lifecycle data."""
        if not self._loss_trades:
            return {"total_losses": 0, "patterns": []}

        regime_counts: dict[str, int] = {}
        state_counts: dict[str, int] = {}
        hour_counts: dict[int, int] = {}

        for loss in self._loss_trades:
            regime = loss.signal.regime
            regime_counts[regime] = regime_counts.get(regime, 0) + 1

            sh = loss.signal.state_hash
            state_counts[sh] = state_counts.get(sh, 0) + 1

            ts_sec = loss.timestamp_ns / 1e9
            hour = int((ts_sec / 3600) % 24)
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

        # Top patterns
        top_regimes = sorted(regime_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_states = sorted(state_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]

        return {
            "total_losses": len(self._loss_trades),
            "top_regimes": top_regimes,
            "top_states": top_states,
            "top_hours": top_hours,
        }


class LifecycleLogger:
    """Ω-LL42: Master logger orchestrating cycle capture, export, and forensics."""

    def __init__(self, log_dir: str = "logs") -> None:
        self.writer = StructuredLogger(log_dir)
        self.forensics = ForensicAnalyzer()
        self._next_cycle_id: int = 1

    def log_cycle(
        self,
        signal: SignalFormation,
        decision: DecisionRationale,
        execution: ExecutionResult,
        internal_logs: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> CycleLog:
        """Ω-LL43: Log a complete trading cycle."""
        cycle_id = self._next_cycle_id
        self._next_cycle_id += 1

        cycle = CycleLog(
            cycle_id=cycle_id,
            timestamp_ns=time.time_ns(),
            signal=signal,
            decision=decision,
            execution=execution,
            internal_logs=internal_logs or [],
            context=context or {},
        )

        # Run forensics on loss trades
        if cycle.execution.outcome == TradeOutcome.LOSS:
            cycle.forensic_report = self.forensics.investigate_loss(cycle)

        # Record for pattern analysis
        self.forensics.record(cycle)

        # Write to files
        self.writer.write_block(cycle)

        return cycle

    def log_wait_cycle(
        self,
        signal: SignalFormation,
        decision: DecisionRationale,
        reason: str = "No setup met criteria",
        internal_logs: list[str] | None = None,
    ) -> CycleLog:
        """Ω-LL44: Log a WAIT (no trade) cycle — minimal but complete."""
        exec_result = ExecutionResult(outcome=TradeOutcome.UNKNOWN, reason=reason)
        return self.log_cycle(signal, decision, exec_result, internal_logs)

    def get_cycle_stats(self) -> dict[str, Any]:
        """Ω-LL45: Overall statistics."""
        patterns = self.forensics.extract_patterns()
        return {
            "last_cycle_id": self._next_cycle_id - 1,
            "patterns": patterns,
        }
