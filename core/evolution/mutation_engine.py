"""
SOLÉNN v2 — Adaptive Mutation Engine: Actor-Critic Strategy Selection
(Ω-ME01 a Ω-ME54)
Replaces v1 mutation_engine.py. Applies controlled mutations to system
parameters based on performance feedback. Uses Actor-Critic (A2C-inspired)
policy: the Critic evaluates the performance state and directs the Actor
to choose between Gaussian refinement, uniform exploration, or targeted
mutation. Includes cooldown, sanity clamps, and automatic reversion on
degradation.

Concept 1: Adaptive Mutation Strategy Selection (Ω-ME01–ME18)
  Actor-Critic policy maps 5-dim performance state to mutation strategy
  (gaussian, uniform, targeted_rrr, targeted_precision, crossover).
  Critic evaluates fitness; Actor selects exploration vs exploitation.
  Temperature scheduling based on distance from best fitness.

Concept 2: Mutation Operators & Param Protection (Ω-ME19–ME36)
  Multiple mutation operators: Gaussian (refinement), Uniform (exploration),
  Targeted (directional based on metric deficits), Crossover (combining
  successful genomes). Critical parameter classes have mutation guardrails
  (no uniform exploration for thresholds, hard clamps on risk params).

Concept 3: Mutation Tracking, Analysis & Auto-Reversion (Ω-ME37–ME54)
  Full audit trail of mutations with before/after performance. Automatic
  reversion when mutations degrade fitness. Cooldown enforcement prevents
  mutation thrashing. Fitness landscape analysis over generations.
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ──────────────────────────────────────────────────────────────
# Ω-ME01 to Ω-ME18: Adaptive Mutation Strategy Selection
# ──────────────────────────────────────────────────────────────


class MutationStrategy(Enum):
    """Ω-ME01: Available mutation strategies."""

    GAUSSIAN = "gaussian"  # Small perturbations — exploitation
    UNIFORM = "uniform"  # Wide exploration — desperate when degrading
    TARGETED_RRR = "targeted_rrr"  # Target RRR-improving params
    TARGETED_PRECISION = "targeted_precision"  # Target WR-improving params
    CROSSOVER = "crossover"  # Combine two good genomes


@dataclass(frozen=True)
class PerformanceState:
    """Ω-ME02: Snapshot of system performance for mutation policy."""

    win_rate: float = 0.5
    profit_factor: float = 1.0
    total_pnl: float = 0.0
    max_drawdown: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 1.0
    rrr: float = 1.0
    total_trades: int = 0
    total_commission: float = 0.0
    timestamp_ns: int = field(default_factory=lambda: time.time_ns())

    @property
    def is_degraded(self) -> bool:
        return self.win_rate < 0.4 or self.profit_factor < 0.8

    @property
    def needs_precision(self) -> bool:
        return self.win_rate < 0.5

    @property
    def needs_rrr(self) -> bool:
        return self.rrr < 0.8


class MutationCritic:
    """Ω-ME03: Evaluates performance and selects mutation strategy."""

    def __init__(self, best_fitness: float = 0.0) -> None:
        self._best_fitness = best_fitness

    def evaluate_fitness(self, perf: PerformanceState) -> float:
        """Ω-ME04: Compute fitness from performance metrics.

        Fitness combines WR, PF, RRR, net profit, and drawdown penalty.
        Inspired by Kelly criterion: focus on growth rate, not expected value.
        """
        wr = perf.win_rate
        pf = perf.profit_factor
        total_profit = perf.total_pnl
        max_dd = perf.max_drawdown
        avg_win = perf.avg_win
        avg_loss = max(abs(perf.avg_loss), 1e-9)
        rrr = avg_win / avg_loss
        n_trades = perf.total_trades
        commission = abs(perf.total_commission)

        fitness = 0.0

        # Win Rate component (20 pts)
        fitness += wr * 20

        # Profit Factor component (20 pts, capped at PF=4)
        fitness += min(pf, 4) * 5

        # RRR — main driver for asymmetric risk
        if rrr >= 1.0:
            fitness += rrr * 30
        else:
            fitness -= (1.0 - rrr) * 50

        # Net profit (40 pts cap)
        fitness += min(total_profit / 100, 40)

        # Drawdown penalty
        fitness -= max_dd * 1.5

        # Volume bonus (only if PF and RRR are healthy)
        if pf > 1.2 and rrr > 0.8:
            fitness += min(n_trades, 200) * 0.1

        # Commission penalty
        if total_profit > 0 and commission > 0:
            gross = total_profit + commission
            if gross > 0:
                comm_ratio = commission / gross
                if comm_ratio > 0.4:
                    fitness *= 1.0 - comm_ratio

        return round(fitness, 4)

    def select_strategy(self, perf: PerformanceState) -> MutationStrategy:
        """Ω-ME05: Actor-Critic policy for mutation strategy selection."""
        fitness = self.evaluate_fitness(perf)

        # If system is degrading fast → broad exploration (high temperature)
        if self._best_fitness > 0 and fitness < self._best_fitness * 0.8:
            return MutationStrategy.UNIFORM

        # If RRR is terrible → target TP/SL parameters
        if perf.needs_rrr:
            return MutationStrategy.TARGETED_RRR

        # If precision is poor → tighten thresholds
        if perf.needs_precision:
            return MutationStrategy.TARGETED_PRECISION

        # Otherwise → refine good setup with small perturbations
        return MutationStrategy.GAUSSIAN

    def update_best_fitness(self, new_best: float) -> None:
        self._best_fitness = max(self._best_fitness, new_best)


@dataclass
class MutationRecord:
    """Ω-ME06: Audit trail record for a mutation."""

    timestamp_ns: int
    param_name: str
    old_value: float
    new_value: float
    mutation_type: str
    reason: str
    fitness_before: float
    reverted: bool = False


# ──────────────────────────────────────────────────────────────
# Ω-ME19 to Ω-ME36: Mutation Operators & Param Protection
# ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ParamSpec:
    """Ω-ME19: Parameter specification with bounds and criticality flag."""

    name: str
    value: float
    min_val: float
    max_val: float
    is_critical: bool = False  # Thresholds/confidence params get guardrails


class MutationOperators:
    """Ω-ME20: Low-level mutation operator implementations."""

    # Critical parameter keywords — these should NOT use uniform exploration
    CRITICAL_KEYWORDS = [
        "threshold", "confidence", "phi_min", "splits", "position_size",
        "max_dd", "circuit_breaker", "sl_multiplier", "tp_multiplier",
    ]

    def __init__(
        self,
        mutation_rate: float = 0.1,
        mutation_strength: float = 0.05,
    ) -> None:
        self._mutation_rate = mutation_rate
        self._mutation_strength = mutation_strength

    def should_mutate(self) -> bool:
        """Ω-ME21: Whether this parameter should be mutated this cycle."""
        return random.random() < self._mutation_rate

    def gaussian(
        self, value: float, min_val: float, max_val: float
    ) -> float:
        """Ω-ME22: Small Gaussian perturbation proportional to range."""
        spread = (max_val - min_val) * self._mutation_strength
        new_val = value + random.gauss(0, spread)
        return max(min_val, min(max_val, new_val))

    def uniform(self, min_val: float, max_val: float) -> float:
        """Ω-ME23: Uniform exploration across full range."""
        return random.uniform(min_val, max_val)

    def targeted_rrr(
        self, name: str, value: float, min_val: float, max_val: float
    ) -> float:
        """Ω-ME24: Target mutations that improve reward:risk ratio."""
        if "take_profit" in name.lower():
            # Stretch TP → bigger wins
            return min(max_val, value * (1.0 + random.random() * 0.3))
        elif "stop_loss" in name.lower():
            # Tighten SL → smaller losses
            return max(min_val, value * (1.0 - random.random() * 0.2))
        elif any(k in name.lower() for k in ["kelly", "size", "position", "risk"]):
            # Reduce aggression temporarily
            return max(min_val, value * 0.9)
        return self.gaussian(value, min_val, max_val)

    def targeted_precision(
        self, name: str, value: float, min_val: float, max_val: float
    ) -> float:
        """Ω-ME25: Target mutations that improve win rate."""
        if any(k in name.lower() for k in ["phi_min", "confidence", "threshold"]):
            # Require more certainty → fewer but better trades
            return min(max_val, value * (1.0 + random.random() * 0.15))
        elif "take_profit" in name.lower():
            # Shorten TP slightly → hit targets more often
            return max(min_val, value * 0.9)
        return self.gaussian(value, min_val, max_val)

    def crossover(
        self, genome_a: dict[str, float], genome_b: dict[str, float]
    ) -> dict[str, float]:
        """Ω-ME26: Uniform crossover between two genomes."""
        child: dict[str, float] = {}
        all_keys = set(genome_a.keys()) | set(genome_b.keys())

        for key in all_keys:
            if key in genome_a and key in genome_b:
                child[key] = random.choice([genome_a[key], genome_b[key]])
            elif key in genome_a:
                child[key] = genome_a[key]
            else:
                child[key] = genome_b[key]

            # Small mutation on child
            if random.random() < self._mutation_rate:
                child[key] *= 1.0 + random.gauss(0, self._mutation_strength)

        return child

    def safe_mutate(
        self,
        param: ParamSpec,
        strategy: MutationStrategy,
    ) -> tuple[float, MutationStrategy]:
        """Ω-ME27: Apply mutation with critical parameter protection."""
        # Critical params can't use uniform — too dangerous
        effective_strategy = strategy
        is_critical = any(
            k in param.name.lower() for k in self.CRITICAL_KEYWORDS
        )
        if is_critical and strategy == MutationStrategy.UNIFORM:
            effective_strategy = MutationStrategy.GAUSSIAN

        # Apply operator
        if effective_strategy == MutationStrategy.GAUSSIAN:
            new_val = self.gaussian(param.value, param.min_val, param.max_val)
        elif effective_strategy == MutationStrategy.UNIFORM:
            new_val = self.uniform(param.min_val, param.max_val)
        elif effective_strategy == MutationStrategy.TARGETED_RRR:
            new_val = self.targeted_rrr(param.name, param.value, param.min_val, param.max_val)
        elif effective_strategy == MutationStrategy.TARGETED_PRECISION:
            new_val = self.targeted_precision(param.name, param.value, param.min_val, param.max_val)
        else:
            new_val = self.gaussian(param.value, param.min_val, param.max_val)

        # Hard sanity clamps
        new_val = self._apply_sanity_clamps(param.name, new_val)

        return (new_val, effective_strategy)

    def _apply_sanity_clamps(self, name: str, value: float) -> float:
        """Ω-ME28: Hard bounds on critical params regardless of mutation."""
        name_lower = name.lower()

        # Phi threshold cap
        if "phi_min" in name_lower:
            value = min(0.35, value)

        # Max splits — prevent MT5 asphyxiation
        if "max_order_splits" in name_lower or "max_splits" in name_lower:
            value = min(15.0, value)

        # Position size — prevent suicidal exposure
        if "position_size" in name_lower or "max_position" in name_lower:
            value = min(100.0, max(1.0, value))

        # Max drawdown — non-negotiable
        if "max_dd" in name_lower or "max_drawdown" in name_lower:
            value = min(10.0, max(0.5, value))

        # Confidence threshold — bounded
        if "confidence" in name_lower:
            value = max(0.1, min(0.99, value))

        # Stop loss — positive and bounded
        if "stop_loss" in name_lower:
            value = max(0.1, value)

        return value


# ──────────────────────────────────────────────────────────────
# Ω-ME37 to Ω-ME54: Mutation Tracking, Analysis & Auto-Reversion
# ──────────────────────────────────────────────────────────────


class MutationEngine:
    """Ω-ME39: Master mutation engine with full lifecycle management."""

    def __init__(
        self,
        mutation_rate: float = 0.1,
        mutation_strength: float = 0.05,
        cooldown_cycles: int = 500,
    ) -> None:
        self.critic = MutationCritic()
        self.operators = MutationOperators(mutation_rate, mutation_strength)

        self._history: list[MutationRecord] = []
        self._generation: int = 0
        self._best_genome: dict[str, float] = {}
        self._best_fitness: float = float("-inf")
        self._cooldown_cycles = cooldown_cycles
        self._last_mutation_cycle: int = 0
        self._enabled: bool = True
        self._active_params: dict[str, ParamSpec] = {}

    def register_params(self, params: dict[str, ParamSpec]) -> None:
        """Register parameters that can be mutated."""
        self._active_params.update(params)

    def should_mutate(self, cycle: int) -> bool:
        """Ω-ME40: Check if mutation cooldown has elapsed."""
        if not self._enabled:
            return False
        if cycle - self._last_mutation_cycle < self._cooldown_cycles:
            return False
        return True

    def mutate(
        self,
        cycle: int,
        perf: dict[str, Any],
    ) -> list[MutationRecord]:
        """Ω-ME41: Main mutation entry point.

        Returns list of mutations applied (empty if skipped).
        """
        if not self.should_mutate(cycle):
            return []

        perf_state = PerformanceState(
            win_rate=perf.get("win_rate", 0.5),
            profit_factor=perf.get("profit_factor", 1.0),
            total_pnl=perf.get("total_pnl", 0.0),
            max_drawdown=perf.get("max_drawdown", 0.0),
            avg_win=perf.get("avg_win", 0.0),
            avg_loss=abs(perf.get("avg_loss", 1.0)),
            rrr=perf.get("rrr", perf.get("avg_win", 0) / max(abs(perf.get("avg_loss", 1)), 1e-9)),
            total_trades=perf.get("total_trades", 0),
            total_commission=abs(perf.get("total_commission", 0.0)),
        )

        self._generation += 1
        self._last_mutation_cycle = cycle

        fitness = self.critic.evaluate_fitness(perf_state)

        # Update best genome
        if fitness > self._best_fitness:
            self._best_fitness = fitness
            self._best_genome = {
                name: spec.value for name, spec in self._active_params.items()
            }

        strategy = self.critic.select_strategy(perf_state)
        mutations: list[MutationRecord] = []

        for name, spec in self._active_params.items():
            if not self.operators.should_mutate():
                continue

            old_value = spec.value
            new_value, effective_strategy = self.operators.safe_mutate(spec, strategy)

            # Update the param (in a real system, this would update the config store)
            self._active_params[name] = ParamSpec(
                name=spec.name,
                value=new_value,
                min_val=spec.min_val,
                max_val=spec.max_val,
                is_critical=spec.is_critical,
            )

            record = MutationRecord(
                timestamp_ns=time.time_ns(),
                param_name=name,
                old_value=old_value,
                new_value=new_value,
                mutation_type=effective_strategy.value,
                reason=f"Gen #{self._generation} strategy={effective_strategy.value} fitness={fitness:.4f}",
                fitness_before=fitness,
            )
            mutations.append(record)
            self._history.append(record)

        if mutations:
            self.critic.update_best_fitness(fitness)

        return mutations

    def revert_last_mutations(self) -> int:
        """Ω-ME42: Revert all params to best known genome."""
        if not self._best_genome:
            return 0

        reverted = 0
        for name, value in self._best_genome.items():
            if name in self._active_params:
                old = self._active_params[name].value
                if abs(old - value) > 1e-9:
                    self._active_params[name] = ParamSpec(
                        name=name,
                        value=value,
                        min_val=self._active_params[name].min_val,
                        max_val=self._active_params[name].max_val,
                        is_critical=self._active_params[name].is_critical,
                    )
                    # Mark recent mutations as reverted
                    for rec in reversed(self._history):
                        if rec.param_name == name and not rec.reverted:
                            rec.reverted = True
                            break
                    reverted += 1

        return reverted

    def revert_if_degraded(
        self,
        current_perf: dict[str, Any],
        threshold: float = 0.85,
    ) -> int:
        """Ω-ME43: Auto-revert if current fitness drops below threshold of best."""
        perf_state = PerformanceState(
            win_rate=current_perf.get("win_rate", 0.5),
            profit_factor=current_perf.get("profit_factor", 1.0),
            total_pnl=current_perf.get("total_pnl", 0.0),
            max_drawdown=current_perf.get("max_drawdown", 0.0),
            avg_win=current_perf.get("avg_win", 0.0),
            avg_loss=abs(current_perf.get("avg_loss", 1.0)),
            total_trades=current_perf.get("total_trades", 0),
            total_commission=abs(current_perf.get("total_commission", 0.0)),
        )

        current_fitness = self.critic.evaluate_fitness(perf_state)

        if self._best_fitness > 0 and current_fitness < self._best_fitness * threshold:
            return self.revert_last_mutations()
        return 0

    def set_current_values(self, params: dict[str, float]) -> None:
        """Σ-ME44: External update — sync current param values."""
        for name, value in params.items():
            if name in self._active_params:
                spec = self._active_params[name]
                self._active_params[name] = ParamSpec(
                    name=spec.name,
                    value=value,
                    min_val=spec.min_val,
                    max_val=spec.max_val,
                    is_critical=spec.is_critical,
                )

    def get_param_value(self, name: str) -> float | None:
        """Ω-ME45: Get current value of a registered parameter."""
        if name in self._active_params:
            return self._active_params[name].value
        return None

    def get_fitness_landscape(self) -> dict[str, Any]:
        """Ω-ME46: Fitness landscape across generations."""
        if not self._history:
            return {"generations": 0, "n_mutations": 0}

        gen_mutations: dict[int, list[MutationRecord]] = {}
        for rec in self._history:
            gen = self._generation  # approx — all history is current gen
            if gen not in gen_mutations:
                gen_mutations[gen] = []
            gen_mutations[gen].append(rec)

        return {
            "generations": self._generation,
            "best_fitness": self._best_fitness,
            "total_mutations": len(self._history),
            "reverted_mutations": sum(1 for r in self._history if r.reverted),
            "mutations_by_type": self._mutation_type_distribution(),
        }

    def _mutation_type_distribution(self) -> dict[str, int]:
        dist: dict[str, int] = {}
        for rec in self._history:
            dist[rec.mutation_type] = dist.get(rec.mutation_type, 0) + 1
        return dist

    @property
    def metrics(self) -> dict[str, Any]:
        return {
            "generation": self._generation,
            "total_mutations": len(self._history),
            "best_fitness": self._best_fitness,
            "best_genome_size": len(self._best_genome),
            "mutation_rate": self.operators._mutation_rate,
            "enabled": self._enabled,
            "active_params": len(self._active_params),
            "n_reverted": sum(1 for r in self._history if r.reverted),
        }
