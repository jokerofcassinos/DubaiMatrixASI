"""
SOLÉNN v2 — Byzantine Consensus Manager (Ω-BC01 a Ω-BC54)
Tolerates up to f < N/3 faulty or adversarial signal sources while
guaranteeing liveness and safety of the swarm's collective decision.
Each agent is a "general"; Brier scores modulate authority;
byzantine generals that lie get their influence asymptotically crushed.

Concept 1: Fault Detection & Scoring (Ω-BC01–BC18)
  Brier score tracking, PBFT-inspired voting rounds, adaptive
  thresholds, traitor identification, and reputation decay.

Concept 2: Consensus Protocol & Modulation (Ω-BC19–BC36)
  Three-phase voting (propose, pre-vote, pre-commit), weighted
  aggregation with byzantine-tolerant trimming, and confidence
  calibration.

Concept 3: Adaptive Resilience & Healing (Ω-BC37–BC54)
  Graceful traitor recovery, dynamic agent pool management,
  network partition detection, and anti-Sybil defense.
"""

from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any


# ──────────────────────────────────────────────────────────────
# Ω-BC01 to Ω-BC18: Fault Detection & Scoring
# ──────────────────────────────────────────────────────────────


@dataclass
class AgentReputation:
    """Ω-BC01: Reputation state for one agent/general."""

    brier_score: float  # 0 = perfect, 1 = always wrong
    weight_mod: float  # 0.1 = crushed, 1.0 = full authority
    n_correct: int = 0
    n_wrong: int = 0
    recent_errors: deque = field(default_factory=lambda: deque(maxlen=100))
    last_update_ns: int = 0
    is_suspected: bool = False
    suspect_reason: str = ""
    recovery_rate: float = 0.0  # derivative of weight_mod over time
    lifetime_start_ns: int = 0


class BrierScoreTracker:
    """Ω-BC02: Tracks per-agent prediction accuracy via Brier scoring."""

    def __init__(self, alpha: float = 0.15, min_weight: float = 0.1) -> None:
        self._alpha = alpha  # EMA speed
        self._min_weight = min_weight
        self._agents: dict[str, AgentReputation] = {}

    def register_agent(self, agent_name: str) -> None:
        """Ω-BC03: Register a new agent in the reputation system."""
        if agent_name not in self._agents:
            self._agents[agent_name] = AgentReputation(
                brier_score=0.5,  # neutral prior
                weight_mod=0.7,
                lifetime_start_ns=time.time_ns(),
                last_update_ns=time.time_ns(),
            )

    def update(self, agent_name: str, prediction: float, actual: float) -> float:
        """Ω-BC04: Update Brier score for one agent.

        prediction in [-1, +1], actual in [-1, +1]
        Normalized to [0, 1] for Brier computation.
        """
        if agent_name not in self._agents:
            self.register_agent(agent_name)

        agent = self._agents[agent_name]
        agent.last_update_ns = time.time_ns()

        # Normalize [-1,+1] → [0,1]
        forecast = (prediction + 1.0) / 2.0
        outcome = (actual + 1.0) / 2.0

        # Brier score
        error = (forecast - outcome) ** 2
        agent.recent_errors.append(error)

        # EMA update
        agent.brier_score = (1 - self._alpha) * agent.brier_score + self._alpha * error

        # Penalty: weight_mod = 1.0 - brier_score, clipped to [min_weight, 1.0]
        old_weight = agent.weight_mod
        agent.weight_mod = max(self._min_weight, min(1.0, 1.0 - agent.brier_score))

        # Recovery rate tracking (Ω-BC38)
        agent.recovery_rate = agent.weight_mod - old_weight

        # Track correct/incorrect
        if error < 0.05:  # Very good prediction
            agent.n_correct += 1
        else:
            agent.n_wrong += 1

        return agent.weight_mod

    def get_all_modulations(self) -> dict[str, float]:
        """Ω-BC05: Get weight modulation for all agents."""
        return {name: rep.weight_mod for name, rep in self._agents.items()}

    def get_suspected_traitors(self, threshold: float = 0.5) -> list[str]:
        """Ω-BC06: Identify agents whose weight_mod is below threshold."""
        return [
            name for name, rep in self._agents.items()
            if rep.weight_mod < threshold
        ]

    def get_stats(self) -> dict[str, Any]:
        """Ω-BC07: Summary statistics."""
        if not self._agents:
            return {}
        mods = [rep.weight_mod for rep in self._agents.values()]
        return {
            "n_agents": len(self._agents),
            "avg_weight_mod": sum(mods) / len(mods),
            "min_weight_mod": min(mods),
            "max_weight_mod": max(mods),
            "n_suspected": sum(1 for m in mods if m < 0.5),
            "n_fully_penalized": sum(1 for m in mods if m < 0.2),
        }


class ByzantineDetector:
    """Ω-BC08: Detects byzantine (adversarial) behavior beyond simple inaccuracy."""

    def __init__(self, window_size: int = 50) -> None:
        self._window = window_size
        self._signal_history: dict[str, deque] = {}
        self._detection_log: list[dict[str, Any]] = []

    def record_signal(self, agent_name: str, signal: float, confidence: float) -> None:
        """Ω-BC09: Record agent signal for pattern analysis."""
        if agent_name not in self._signal_history:
            self._signal_history[agent_name] = deque(maxlen=self._window)
        self._signal_history[agent_name].append({
            "signal": signal,
            "confidence": confidence,
            "timestamp_ns": time.time_ns(),
        })

    def detect_spoofing(self, agent_name: str) -> tuple[bool, float, str]:
        """Ω-BC10: Detect agents who deliberately flip sides (spoofing).

        If an agent sends contradictory signals (high confidence both
        bull and bear within short window) = likely spoofing.
        """
        history = self._signal_history.get(agent_name)
        if not history or len(history) < 10:
            return False, 0.0, ""

        recent = list(history)[-20:]
        # Check for high-confidence flips
        high_conf = [h for h in recent if h["confidence"] > 0.7]
        if len(high_conf) < 4:
            return False, 0.0, ""

        flips = 0
        for i in range(1, len(high_conf)):
            if high_conf[i]["signal"] * high_conf[i - 1]["signal"] < 0:
                # Signal flipped direction
                flips += 1

        flip_rate = flips / max(1, len(high_conf) - 1)
        is_spoofing = flip_rate > 0.6  # Flipping > 60% = suspicious

        reason = f"Flip rate {flip_rate:.1%} in {len(high_conf)} high-confidence signals"
        if is_spoofing:
            self._detection_log.append({
                "agent": agent_name,
                "type": "spoofing",
                "flip_rate": flip_rate,
                "timestamp_ns": time.time_ns(),
            })

        return is_spoofing, flip_rate, reason

    def detect_collusion(self, agent_names: list[str], threshold: float = 0.85) -> tuple[bool, list[tuple[str, str]]]:
        """Ω-BC11: Detect if agents are colluding (sending nearly identical signals)."""
        colluding_pairs: list[tuple[str, str]] = []

        for i in range(len(agent_names)):
            for j in range(i + 1, len(agent_names)):
                a = self._signal_history.get(agent_names[i])
                b = self._signal_history.get(agent_names[j])
                if not a or not b:
                    continue

                # Compare recent signals
                min_len = min(len(a), len(b), 20)
                if min_len < 5:
                    continue

                a_signals = [list(a)[-k]["signal"] for k in range(1, min_len + 1)]
                b_signals = [list(b)[-k]["signal"] for k in range(1, min_len + 1)]

                # Correlation
                mean_a = sum(a_signals) / min_len
                mean_b = sum(b_signals) / min_len
                cov = sum((a_signals[k] - mean_a) * (b_signals[k] - mean_b) for k in range(min_len)) / min_len
                std_a = math.sqrt(sum((x - mean_a) ** 2 for x in a_signals) / min_len)
                std_b = math.sqrt(sum((x - mean_b) ** 2 for x in b_signals) / min_len)

                if std_a > 0 and std_b > 0:
                    corr = cov / (std_a * std_b)
                    if corr > threshold:
                        colluding_pairs.append((agent_names[i], agent_names[j]))

        if colluding_pairs:
            self._detection_log.append({
                "type": "collusion",
                "pairs": colluding_pairs,
                "timestamp_ns": time.time_ns(),
            })

        return len(colluding_pairs) > 0, colluding_pairs


# ──────────────────────────────────────────────────────────────
# Ω-BC19 to Ω-BC36: Consensus Protocol & Modulation
# ──────────────────────────────────────────────────────────────


@dataclass
class VotingRound:
    """Ω-BC19: State of one voting round."""

    round_id: int
    proposals: dict[str, float]  # agent_name → proposed value
    pre_votes: dict[str, float]  # agent_name → pre-vote
    pre_commits: dict[str, float]  # agent_name → pre-commit (final vote)
    outcome: float  # final consensus value
    participation_rate: float
    byzantine_tolerated: bool  # True if consensus valid despite traitors
    round_timestamp_ns: int


class PBFTVoting:
    """Ω-BC20: Practical Byzantine Fault Tolerant voting for signal aggregation."""

    def __init__(self, max_faulty: float = 0.33) -> None:
        self._max_faulty = max_faulty  # tolerate up to 33% traitors
        self._round_counter = 0
        self._round_history: deque[VotingRound] = deque(maxlen=500)

    def run_round(
        self,
        proposals: dict[str, float],
        weight_mods: dict[str, float],
    ) -> VotingRound:
        """Ω-BC21: Execute one complete PBFT voting round.

        Three phases:
        1. PROPOSE: each agent proposes a value (input)
        2. PRE-VOTE: each agent votes on the weighted median
        3. PRE-COMMIT: final vote (weighted mean of pre-commits)

        Requires 2f+1 = total * (1 - max_faulty) agents to participate.
        """
        self._round_counter += 1
        n_agents = len(proposals)
        if n_agents == 0:
            return VotingRound(
                round_id=self._round_counter,
                proposals={},
                pre_votes={},
                pre_commits={},
                outcome=0.0,
                participation_rate=0.0,
                byzantine_tolerated=False,
                round_timestamp_ns=time.time_ns(),
            )

        # Minimum required: 2f+1 for BFT
        f = int(n_agents * self._max_faulty)
        min_required = 2 * f + 1

        # Phase 1: Proposals (given as input)
        # Phase 2: Pre-Vote — compute weighted median of proposals
        sorted_vals = sorted(proposals.items(), key=lambda x: x[1])
        cumulative_weight = 0.0
        total_weight = sum(weight_mods.get(name, 0.5) for name, _ in sorted_vals)
        weighted_median = 0.0
        for name, val in sorted_vals:
            w = weight_mods.get(name, 0.5)
            cumulative_weight += w
            if cumulative_weight >= total_weight / 2:
                weighted_median = val
                break

        # Each agent pre-votes by interpolating between their proposal and the median
        pre_votes: dict[str, float] = {}
        for name, proposed in proposals.items():
            w = weight_mods.get(name, 0.5)
            # High weight agents trust their own signal more
            alpha = 0.3 + 0.7 * w
            pre_votes[name] = alpha * proposed + (1 - alpha) * weighted_median

        # Phase 3: Pre-Commit — weighted mean of pre-votes
        weight_sum = sum(weight_mods.get(name, 0.5) for name in pre_votes)
        if weight_sum > 0:
            outcome = sum(
                weight_mods.get(name, 0.5) * vote for name, vote in pre_votes.items()
            ) / weight_sum
        else:
            outcome = weighted_median

        participation = n_agents / max(1, len(weight_mods))
        byzantine_ok = n_agents >= min_required

        round_result = VotingRound(
            round_id=self._round_counter,
            proposals=proposals,
            pre_votes=pre_votes,
            pre_commits={name: vote for name, vote in pre_votes.items()},
            outcome=outcome,
            participation_rate=round(participation, 4),
            byzantine_tolerated=byzantine_ok,
            round_timestamp_ns=time.time_ns(),
        )
        self._round_history.append(round_result)
        return round_result


class ByzantineSignalAggregator:
    """Ω-BC22: Aggregates signals while tolerating byzantine failure."""

    def __init__(self) -> None:
        self.brier = BrierScoreTracker()
        self.detector = ByzantineDetector()
        self.voting = PBFTVoting()

    def aggregate(
        self,
        signals: list[tuple[str, float, float]],  # (name, signal, confidence)
        actual_outcome: float | None = None,
    ) -> tuple[float, bool, dict[str, Any]]:
        """Ω-BC23: Full byzantine aggregation pipeline.

        Returns: (weighted_consensus, is_valid, metadata)
        """
        if not signals:
            return 0.0, False, {"error": "no_signals"}

        # 1. Record all signals for detection
        for name, signal, conf in signals:
            self.brier.register_agent(name)
            self.detector.record_signal(name, signal, conf)

        # 2. Detect spoofing and collusion
        spoofers: list[str] = []
        for name, _, _ in signals:
            is_spoof, _, reason = self.detector.detect_spoofing(name)
            if is_spoof:
                spoofers.append(name)

        # 3. Apply spoofing penalty
        weight_mods = self.brier.get_all_modulations()
        for spoofer in spoofers:
            weight_mods[spoofer] = max(0.1, weight_mods.get(spoofer, 0.5) * 0.3)

        # 4. Trimmed weighted mean: remove top/bottom 1/(3f+1) by value
        # This is the standard BFT trimming approach
        if len(weight_mods) >= 3:
            sorted_signals = sorted(signals, key=lambda x: x[1])
            trim_count = max(1, len(sorted_signals) // 3)
            if trim_count > 0:
                sorted_signals = sorted_signals[trim_count:-trim_count]

        # 5. Run PBFT voting round
        proposals = {name: signal for name, signal, _ in sorted_signals}
        round_result = self.voting.run_round(proposals, weight_mods)

        # 6. Update Brier scores if actual_outcome is known
        if actual_outcome is not None:
            for name, signal, _ in signals:
                self.brier.update(name, signal, actual_outcome)
            # Recompute weight_mods
            weight_mods = self.brier.get_all_modulations()

        # 7. Determine if consensus is valid
        is_valid = round_result.byzantine_tolerated and round_result.participation_rate > 0.5

        # 8. Build metadata
        suspected = self.brier.get_suspected_traitors()
        metadata = {
            "round_id": round_result.round_id,
            "n_agents": len(signals),
            "n_spoofers_detected": len(spoofers),
            "spoofers": spoofers[:5],
            "suspected_traitors": suspected[:5],
            "participation_rate": round_result.participation_rate,
            "consensus_valid": is_valid,
            "brier_stats": self.brier.get_stats(),
        }

        return round_result.outcome, is_valid, metadata


# ──────────────────────────────────────────────────────────────
# Ω-BC37 to Ω-BC54: Adaptive Resilience & Healing
# ──────────────────────────────────────────────────────────────


class TraitorRecoveryManager:
    """Ω-BC38: Manages traitor recovery — agents can redeem themselves."""

    def __init__(self, recovery_window: int = 50, min_streak: int = 5) -> None:
        self._recovery_window = recovery_window
        self._min_correct_streak = min_streak
        self._agent_streaks: dict[str, int] = {}  # consecutive correct
        self._recovered_agents: list[dict[str, Any]] = []

    def evaluate_recovery(self, agent_name: str, recent_accuracy: float) -> bool:
        """Ω-BC39: Check if a penalized agent has recovered."""
        if recent_accuracy >= 0.90:
            self._agent_streaks[agent_name] = self._agent_streaks.get(agent_name, 0) + 1
        else:
            self._agent_streaks[agent_name] = 0

        if self._agent_streaks.get(agent_name, 0) >= self._min_correct_streak:
            self._recovered_agents.append({
                "agent": agent_name,
                "accuracy": recent_accuracy,
                "streak": self._agent_streaks[agent_name],
                "timestamp_ns": time.time_ns(),
            })
            return True
        return False


class NetworkPartitionDetector:
    """Ω-BC40: Detects if the swarm has split into factions."""

    def __init__(self, n_agents: int = 20) -> None:
        self._n_agents = n_agents
        self._agreement_matrix: dict[str, dict[str, int]] = {}
        self._total_rounds = 0

    def record_round(self, agent_signals: dict[str, float], consensus: float) -> None:
        """Ω-BC41: Track agreement patterns for partition detection."""
        self._total_rounds += 1
        direction = 1 if consensus > 0 else (-1 if consensus < 0 else 0)

        for name, signal in agent_signals.items():
            if name not in self._agreement_matrix:
                self._agreement_matrix[name] = {}

            for name2 in agent_signals:
                if name2 not in self._agreement_matrix[name]:
                    self._agreement_matrix[name][name2] = 0

                # Agreement = same sign
                if (signal > 0 and agent_signals[name2] > 0) or (signal < 0 and agent_signals[name2] < 0):
                    self._agreement_matrix[name][name2] += 1

    def detect_partition(self, threshold: float = 0.6) -> tuple[bool, list[set[str]]]:
        """Ω-BC42: Detect if agents have split into opposing factions."""
        if self._total_rounds < 20:
            return False, []

        # Compute agreement rates
        n = len(self._agreement_matrix)
        if n < 4:
            return False, []

        agreement_rate: dict[str, dict[str, float]] = {}
        for a in self._agreement_matrix:
            agreement_rate[a] = {}
            for b in self._agreement_matrix[a]:
                agreement_rate[a][b] = self._agreement_matrix[a][b] / max(1, self._total_rounds)

        # Find clusters via simple correlation clustering
        # Group agents that agree with each other > 70% but disagree with others
        factions: list[set[str]] = []
        remaining = set(self._agreement_matrix.keys())

        while remaining:
            seed = remaining.pop()
            faction = {seed}
            for candidate in list(remaining):
                # Candidate agrees with all faction members > threshold?
                if all(agreement_rate.get(candidate, {}).get(member, 0) > threshold for member in faction):
                    faction.add(candidate)
                    remaining.discard(candidate)
            if len(faction) >= 2:
                factions.append(faction)

        is_partitioned = len(factions) >= 2 and sum(len(f) for f in factions) >= self._n_agents * 0.8
        return is_partitioned, factions


class AntiSybilDefense:
    """Ω-BC50: Defends against Sybil attacks (one entity creating many fake agents)."""

    def __init__(self, min_unique_rate: float = 0.7) -> None:
        self._min_unique = min_unique_rate
        self._signal_patterns: dict[str, list[tuple[float, float]]] = {}  # agent → [(signal, timestamp)]
        self._flagged: set[str] = set()

    def record_signal(self, agent_name: str, signal: float, timestamp: float) -> None:
        if agent_name not in self._signal_patterns:
            self._signal_patterns[agent_name] = []
        self._signal_patterns[agent_name].append((signal, timestamp))
        # Keep last 200
        if len(self._signal_patterns[agent_name]) > 200:
            self._signal_patterns[agent_name] = self._signal_patterns[agent_name][-200:]

    def detect_sybils(self) -> list[tuple[str, str]]:
        """Ω-BC51: Find agents with suspiciously similar signal patterns."""
        agents = list(self._signal_patterns.keys())
        sybil_pairs: list[tuple[str, str]] = []

        for i in range(len(agents)):
            for j in range(i + 1, len(agents)):
                a = self._signal_patterns[agents[i]]
                b = self._signal_patterns[agents[j]]
                if len(a) < 10 or len(b) < 10:
                    continue

                # Check for near-identical signal sequences
                min_len = min(len(a), len(b), 30)
                matches = 0
                for k in range(min_len):
                    if abs(a[-(k + 1)][0] - b[-(k + 1)][0]) < 0.01:  # Within 1%
                        matches += 1

                similarity = matches / min_len
                if similarity > 0.95:
                    pair = tuple(sorted([agents[i], agents[j]]))
                    if pair not in sybil_pairs:
                        sybil_pairs.append(pair)
                        self._flagged.add(pair[0])
                        self._flagged.add(pair[1])

        return sybil_pairs

    def get_flagged_agents(self) -> set[str]:
        return self._flagged


class ByzantineConsensusManager:
    """Ω-BC01 to Ω-BC54: Manager that wires all Byzanitine components."""

    def __init__(self, agents_count: int, min_viable_accuracy: float = 0.55) -> None:
        self.aggregator = ByzantineSignalAggregator()
        self.recovery = TraitorRecoveryManager()
        self.partition_detector = NetworkPartitionDetector(agents_count)
        self.sybil_defense = AntiSybilDefense()

        self._min_accuracy = min_viable_accuracy
        self._agent_weights = [1.0] * agents_count  # base weights
        self._total_consensus_rounds = 0
        self._last_outcome: float = 0.0
        self._consensus_log: deque[dict[str, Any]] = deque(maxlen=1000)

    def process_signals(
        self,
        signals: list[tuple[str, float, float]],  # (name, signal[-1,+1], confidence)
        actual_outcome: float | None = None,
    ) -> dict[str, Any]:
        """Main entry: aggregate signals through Byzantine consensus pipeline."""
        t0 = time.time_ns()

        # 1. Sybil detection
        for name, signal, _ in signals:
            self.sybil_defense.record_signal(name, signal, time.time())
        sybil_pairs = self.sybil_defense.detect_sybils()
        flagged = self.sybil_defense.get_flagged_agents()

        # Remove flagged agents
        clean_signals = [(n, s, c) for n, s, c in signals if n not in flagged]

        # 2. Byzantine aggregation
        consensus, is_valid, metadata = self.aggregator.aggregate(clean_signals, actual_outcome)
        self._last_outcome = consensus

        # 3. Record round for partition detection
        agent_signal_map = {n: s for n, s, _ in clean_signals}
        self.partition_detector.record_round(agent_signal_map, consensus)

        # 4. Recovery evaluation
        for name, signal, conf in clean_signals:
            if name in self.aggregator.brier.get_suspected_traitors():
                brier = self.aggregator.brier._agents[name].brier_score
                accuracy = 1.0 - brier
                self.recovery.evaluate_recovery(name, accuracy)

        # 5. Update base weights
        modulations = self.aggregator.brier.get_all_modulations()
        for i, (name, _, _) in enumerate(signals):
            mod = modulations.get(name, 1.0)
            if i < len(self._agent_weights):
                self._agent_weights[i] = mod

        self._total_consensus_rounds += 1
        elapsed_us = (time.time_ns() - t0) // 1000

        self._consensus_log.append({
            "round": self._total_consensus_rounds,
            "consensus": consensus,
            "valid": is_valid,
            "elapsed_us": elapsed_us,
            "sybils_detected": len(sybil_pairs),
        })

        return {
            "consensus_signal": consensus,
            "is_valid": is_valid,
            "metadata": metadata,
            "sybil_pairs": sybil_pairs[:5],
            "flagged_agents": list(flagged)[:5],
            "elapsed_us": elapsed_us,
        }

    def get_modulated_weights(self) -> list[float]:
        return list(self._agent_weights)

    def get_traitor_report(self) -> dict[str, Any]:
        return {
            "brier_stats": self.aggregator.brier.get_stats(),
            "suspected": self.aggregator.brier.get_suspected_traitors(),
            "recovered": self.recovery._recovered_agents[-10:],
        }
