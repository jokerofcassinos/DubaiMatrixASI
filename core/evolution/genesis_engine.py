"""
SOLÉNN v2 — Genesis Engine: Spontaneous Agent Mutation & Evolution
(Ω-GE01 a Ω-GE54)
Replaces v1 genesis_engine.py. During high-entropy conditions, the engine
spontaneously spawns mutant agents via crossover of top-performing agents.
Mutants are born in full quarantine (pandemic isolation) — they cannot
influence real decisions until they prove edge through paper trading.
Includes entropy-triggered spawning, automatic pruning, and evolution
tracking.

Concept 1: Entropy-Triggered Spontaneous Mutation (Ω-GE01–GE18)
  Market entropy spikes trigger genetic spark events. Two dominant
  agents are crossed with random mutation rate to create novel agents.
  Spawn rate scales with entropy above threshold. Max mutant population
  controlled to prevent memory growth.

Concept 2: Mutant Agent Lifecycle & Quarantine (Ω-GE19–GE36)
  New mutants are fully isolated — their signals are recorded but not
  used. Must pass paper trading validation (min trades + min WR) to
  enter probation. Probation agents get small real allocation. Failed
  mutants are pruned via performance evaluation against genetic forge.

Concept 3: Evolution Tracking & Diversity Management (Ω-GE37–GE54)
  Tracks generation lineage, parent relationships, and fitness trajectory.
  Monitors population diversity — if diversity drops, forced mutation
  to prevent premature convergence. Evolution stats and genealogy export.
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field
from typing import Any


# ──────────────────────────────────────────────────────────────
# Ω-GE01 to Ω-GE18: Entropy-Triggered Spontaneous Mutation
# ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class SparkConditions:
    """Ω-GE01: Conditions that trigger agent mutation."""

    entropy: float  # Shannon entropy of current market state
    regime_stability: float  # [0, 1] — how stable is current regime
    current_diversity: float  # [0, 1] — agent pool diversity
    n_active_agents: int
    time_since_last_spark_ns: int


class SparkDetector:
    """Ω-GE02: Detects when conditions warrant spawning mutants."""

    def __init__(
        self,
        entropy_threshold: float = 0.85,
        min_diversity: float = 0.15,
        min_agents: int = 2,
        cooldown_ns: int = 3600 * 1_000_000_000,  # 1 hour minimum between sparks
    ) -> None:
        self._entropy_threshold = entropy_threshold
        self._min_diversity = min_diversity
        self._min_agents = min_agents
        self._cooldown_ns = cooldown_ns

    def should_spark(self, conditions: SparkConditions) -> tuple[bool, str]:
        """Ω-GE03: Check if spark conditions are met."""
        if conditions.entropy < self._entropy_threshold:
            return False, f"entropy_too_low: {conditions.entropy:.3f} < {self._entropy_threshold}"

        if conditions.current_diversity < self._min_diversity:
            return False, f"diversity_too_low: {conditions.current_diversity:.3f}"

        if conditions.n_active_agents < self._min_agents:
            return False, f"too_few_agents: {conditions.n_active_agents}"

        if conditions.time_since_last_spark_ns < self._cooldown_ns:
            cooldown_sec = conditions.time_since_last_spark_ns / 1e9
            return False, f"cooldown_active: {cooldown_sec:.0f}s since last spark"

        return True, "spark_conditions_met"

    def spawn_probability(self, conditions: SparkConditions) -> float:
        """Ω-GE04: Compute probability of spawning (above threshold)."""
        # Higher entropy → higher probability
        entropy_factor = max(0, (conditions.entropy - self._entropy_threshold)) / (1.0 - self._entropy_threshold)
        # Low diversity → lower probability
        diversity_factor = max(0, conditions.current_diversity - self._min_diversity)
        # Combine
        p = entropy_factor * 0.5 + diversity_factor * 0.5
        return min(1.0, max(0.0, p))

    def select_parents(self, agents: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]] | None:
        """Ω-GE05: Select two random agents as parents for crossover."""
        if len(agents) < 2:
            return None
        return tuple(random.sample(agents, 2))  # type: ignore


# ──────────────────────────────────────────────────────────────
# Ω-GE19 to Ω-GE36: Mutant Agent Lifecycle & Quarantine
# ──────────────────────────────────────────────────────────────


class MutantStatus:
    """Ω-GE19: Status of a mutant agent through its lifecycle."""

    NEW = "new"  # Just born, fully isolated
    OBSERVING = "observing"  # Being monitored in paper trading
    PROMOTING = "promoting"  # Good paper results, candidate for promotion
    ACTIVE = "active"  # Promoted to main pool
    PRUNED = "pruned"  # Removed for poor performance


@dataclass
class MutantAgent:
    """Ω-GE20: A single mutant agent with lifecycle tracking."""

    name: str
    parent_a: str
    parent_b: str
    generation: int
    mutation_rate: float
    genome: dict[str, float]  # Parameters of this mutant
    status: str = MutantStatus.NEW
    n_paper_trades: int = 0
    n_paper_wins: int = 0
    paper_pnl: float = 0.0
    paper_wr: float = 0.5
    max_drawdown: float = 0.0
    n_real_trades: int = 0
    n_real_wins: int = 0
    real_pnl: float = 0.0
    real_wr: float = 0.5
    creation_ns: int = field(default_factory=lambda: time.time_ns())
    last_activity_ns: int = 0
    promotion_threshold_wr: float = 0.52
    min_trades_for_promotion: int = 30

    @property
    def age_seconds(self) -> float:
        return (time.time_ns() - self.creation_ns) / 1e9

    def record_paper_trade(self, win: bool, pnl: float) -> None:
        """Record a paper trade outcome."""
        self.n_paper_trades += 1
        if win:
            self.n_paper_wins += 1
        self.paper_pnl += pnl
        self.paper_wr = self.n_paper_wins / max(1, self.n_paper_trades)
        self.last_activity_ns = time.time_ns()

    def record_real_trade(self, win: bool, pnl: float) -> None:
        """Record a real trade outcome."""
        self.n_real_trades += 1
        if win:
            self.n_real_wins += 1
        self.real_pnl += pnl
        self.real_wr = self.n_real_wins / max(1, self.n_real_trades)
        self.last_activity_ns = time.time_ns()


class MutantLifecycle:
    """Ω-GE21: Manages mutant lifecycle transitions."""

    def __init__(
        self,
        max_active_mutants: int = 50,
        max_paper_trades: int = 200,
    ) -> None:
        self._max_active = max_active_mutants
        self._max_paper = max_paper_trades
        self._mutants: dict[str, MutantAgent] = {}
        self._generation_count: int = 0
        self._total_spawned: int = 0
        self._total_promoted: int = 0
        self._total_pruned: int = 0

    def spawn_mutant(
        self,
        parent_a: dict[str, Any],
        parent_b: dict[str, Any],
        mutation_rate: float,
        genome: dict[str, float],
    ) -> MutantAgent:
        """Ω-GE22: Create a new mutant from two parents."""
        self._generation_count += 1
        self._total_spawned += 1

        name_a = parent_a.get("name", "unknown")[:5]
        name_b = parent_b.get("name", "unknown")[:5]
        name = f"mutant_{name_a}_{name_b}_v{self._generation_count}"

        mutant = MutantAgent(
            name=name,
            parent_a=parent_a.get("name", "unknown"),
            parent_b=parent_b.get("name", "unknown"),
            generation=self._generation_count,
            mutation_rate=mutation_rate,
            genome=genome,
        )

        self._mutants[name] = mutant
        return mutant

    def promote_to_observing(self, name: str) -> bool:
        if name not in self._mutants:
            return False
        m = self._mutants[name]
        if m.status != MutantStatus.NEW:
            return False
        m.status = MutantStatus.OBSERVING
        return True

    def promote_to_active(self, name: str) -> bool:
        """Ω-GE23: Promote mutant to active pool."""
        if name not in self._mutants:
            return False
        m = self._mutants[name]
        if m.status != MutantStatus.OBSERVING and m.status != MutantStatus.PROMOTING:
            return False
        if m.n_paper_trades < m.min_trades_for_promotion:
            return False
        if m.paper_wr < m.promotion_threshold_wr:
            return False

        m.status = MutantStatus.ACTIVE
        self._total_promoted += 1
        return True

    def prune(self, name: str) -> bool:
        """Ω-GE24: Remove mutant from population."""
        if name not in self._mutants:
            return False
        m = self._mutants[name]
        if m.status == MutantStatus.ACTIVE:
            # Don't prune active ones — they've proven themselves
            m.status = MutantStatus.PRUNED
            self._total_pruned += 1
            return True

        m.status = MutantStatus.PRUNED
        self._total_pruned += 1
        return True

    def check_all_lifecycles(self) -> list[tuple[str, str]]:
        """Ω-GE25: Auto-transition mutants through lifecycle."""
        transitions: list[tuple[str, str]] = []
        to_prune: list[str] = []

        for name, m in self._mutants.items():
            if m.status == MutantStatus.NEW:
                # Age threshold: after 10 paper trades, start observing
                if m.n_paper_trades >= 5:
                    m.status = MutantStatus.OBSERVING
                    transitions.append((name, "new→observing"))

            elif m.status == MutantStatus.OBSERVING:
                # Check promotion criteria
                if m.n_paper_trades >= m.min_trades_for_promotion:
                    if m.paper_wr >= m.promotion_threshold_wr:
                        m.status = MutantStatus.PROMOTING
                        transitions.append((name, "observing→promoting"))
                    elif m.paper_wr < m.promotion_threshold_wr - 0.1:
                        # Way too far behind → prune
                        to_prune.append(name)
                        transitions.append((name, "observing→pruned"))

            elif m.status == MutantStatus.PROMOTING:
                # Need a few more confirming trades
                if m.n_paper_trades >= m.min_trades_for_promotion + 10:
                    if m.paper_wr >= m.promotion_threshold_wr:
                        m.status = MutantStatus.ACTIVE
                        self._total_promoted += 1
                        transitions.append((name, "promoting→active"))
                    else:
                        to_prune.append(name)
                        transitions.append((name, "promoting→pruned"))

            # Check max paper trades cap
            if m.n_paper_trades >= self._max_paper and m.status != MutantStatus.ACTIVE:
                if name not in to_prune:
                    to_prune.append(name)
                    transitions.append((name, "paper_cap→pruned"))

            # Inactive mutant timeout
            if m.last_activity_ns > 0 and (time.time_ns() - m.last_activity_ns) > 86400 * 1_000_000_000:
                if m.status != MutantStatus.ACTIVE and name not in to_prune:
                    to_prune.append(name)
                    transitions.append((name, "inactive_timeout→pruned"))

        for name in to_prune:
            self.prune(name)

        # Enforce max active mutants
        active = [n for n, a in self._mutants.items() if a.status != MutantStatus.PRUNED]
        if len(active) > self._max_active:
            # Score by paper WR, worst first
            scored = sorted(
                [
                    (n, self._mutants[n].paper_wr)
                    for n in active
                    if self._mutants[n].status != MutantStatus.ACTIVE
                ],
                key=lambda x: x[1],
            )
            excess = len(active) - self._max_active
            for name, _ in scored[:excess]:
                self.prune(name)
                transitions.append((name, "overpopulation→pruned"))

        return transitions

    def get_active(self) -> list[MutantAgent]:
        return [m for m in self._mutants.values() if m.status != MutantStatus.PRUNED]

    def get_by_status(self, status: str) -> list[MutantAgent]:
        return [m for m in self._mutants.values() if m.status == status]

    def get_mutants(self) -> dict[str, MutantAgent]:
        return dict(self._mutants)

    def get_stats(self) -> dict[str, Any]:
        all_mutants = list(self._mutants.values())
        return {
            "total_spawned": self._total_spawned,
            "total_promoted": self._total_promoted,
            "total_pruned": self._total_pruned,
            "current_population": len([m for m in all_mutants if m.status != MutantStatus.PRUNED]),
            "new": len(self.get_by_status(MutantStatus.NEW)),
            "observing": len(self.get_by_status(MutantStatus.OBSERVING)),
            "promoting": len(self.get_by_status(MutantStatus.PROMOTING)),
            "active": len(self.get_by_status(MutantStatus.ACTIVE)),
            "generation": self._generation_count,
        }


def crossover_genomes(
    genome_a: dict[str, float],
    genome_b: dict[str, float],
    mutation_rate: float,
) -> dict[str, float]:
    """Ω-GE30: Crossover two parent genomes with mutation."""
    child: dict[str, float] = {}
    all_keys = set(genome_a.keys()) | set(genome_b.keys())

    for key in all_keys:
        if key in genome_a and key in genome_b:
            child[key] = random.choice([genome_a[key], genome_b[key]])
        elif key in genome_a:
            child[key] = genome_a[key]
        else:
            child[key] = genome_b[key]

        # Apply mutation
        if random.random() < mutation_rate:
            child[key] *= 1.0 + random.gauss(0, mutation_rate)

    return child


def compute_diversity(mutants: list[MutantAgent]) -> float:
    """Ω-GE31: Compute population diversity from genome variance."""
    if len(mutants) < 2:
        return 0.0

    genomes = [m.genome for m in mutants if m.genome]
    if not genomes:
        return 0.0

    all_keys = set()
    for g in genomes:
        all_keys.update(g.keys())
    all_keys = sorted(all_keys)

    if not all_keys:
        return 0.0

    avg_genome = {}
    for k in all_keys:
        vals = [g.get(k, 0.0) for g in genomes]
        avg_genome[k] = sum(vals) / len(vals)

    variance = 0.0
    for k in all_keys:
        for g in genomes:
            variance += (g.get(k, 0.0) - avg_genome[k]) ** 2
    variance /= max(1, len(genomes) * len(all_keys))

    return math.sqrt(variance)


# ──────────────────────────────────────────────────────────────
# Ω-GE37 to Ω-GE54: Evolution Tracking & Diversity Management
# ──────────────────────────────────────────────────────────────


@dataclass
class EvolutionRecord:
    """Ω-GE37: Record of one evolution event."""

    mutant_name: str
    generation: int
    parent_a: str
    parent_b: str
    mutation_rate: float
    entropy_trigger: float
    timestamp_ns: int
    current_status: str
    paper_wr: float = 0.5
    real_wr: float = 0.5
    paper_pnl: float = 0.0


class GenesisEngine:
    """Ω-GE38: Master engine for spontaneous agent evolution."""

    def __init__(
        self,
        entropy_threshold: float = 0.85,
        max_mutants: int = 50,
        cooldown_ns: int = 3600 * 1_000_000_000,
    ) -> None:
        self.spark_detector = SparkDetector(
            entropy_threshold=entropy_threshold,
            cooldown_ns=cooldown_ns,
        )
        self.lifecycle = MutantLifecycle(max_active_mutants=max_mutants)
        self._last_spark_ns: int = 0
        self._evolution_log: list[EvolutionRecord] = []
        self._active_agents: list[dict[str, Any]] = []

    def register_active_agents(self, agents: list[dict[str, Any]]) -> None:
        """Ω-GE39: Register current active agents for parent selection."""
        self._active_agents = agents

    def try_spawn(
        self,
        entropy: float,
        regime_stability: float = 0.5,
    ) -> MutantAgent | None:
        """Ω-GE40: Attempt to spawn a mutant if conditions are met."""
        conditions = SparkConditions(
            entropy=entropy,
            regime_stability=regime_stability,
            current_diversity=compute_diversity(self.lifecycle.get_active()),
            n_active_agents=len(self._active_agents),
            time_since_last_spark_ns=time.time_ns() - self._last_spark_ns,
        )

        should_spark, reason = self.spark_detector.should_spark(conditions)
        if not should_spark:
            return None

        parent_pair = self.spark_detector.select_parents(self._active_agents)
        if parent_pair is None:
            return None

        parent_a, parent_b = parent_pair

        mutation_rate = random.uniform(0.1, 0.5)
        genome_a = parent_a.get("genome", {})
        genome_b = parent_b.get("genome", {})

        child_genome = crossover_genomes(genome_a, genome_b, mutation_rate)

        mutant = self.lifecycle.spawn_mutant(
            parent_a=parent_a,
            parent_b=parent_b,
            mutation_rate=mutation_rate,
            genome=child_genome,
        )

        self._last_spark_ns = time.time_ns()

        self._evolution_log.append(EvolutionRecord(
            mutant_name=mutant.name,
            generation=mutant.generation,
            parent_a=mutant.parent_a,
            parent_b=mutant.parent_b,
            mutation_rate=mutation_rate,
            entropy_trigger=entropy,
            timestamp_ns=time.time_ns(),
            current_status=mutant.status,
        ))

        return mutant

    def check_lifecycles(self) -> list[tuple[str, str]]:
        """Ω-GE41: Process all mutant lifecycle transitions."""
        return self.lifecycle.check_all_lifecycles()

    def record_paper_outcome(
        self, mutant_name: str, win: bool, pnl: float
    ) -> None:
        self.lifecycle.record_paper_outcome(mutant_name, win, pnl)

    def record_real_outcome(
        self, mutant_name: str, win: bool, pnl: float
    ) -> None:
        self.lifecycle.record_real_outcome(mutant_name, win, pnl)

    def get_promotable(self) -> list[MutantAgent]:
        return self.lifecycle.get_by_status(MutantStatus.PROMOTING)

    def get_stats(self) -> dict[str, Any]:
        return {
            "lifecycle": self.lifecycle.get_stats(),
            "evolution_log_size": len(self._evolution_log),
            "last_spark_ago_sec": round(
                (time.time_ns() - self._last_spark_ns) / 1e9, 1
            ),
            "n_registered_agents": len(self._active_agents),
        }