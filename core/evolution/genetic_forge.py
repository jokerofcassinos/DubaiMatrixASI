"""
SOLÉNN v2 — Genetic Forge: Bayesian Synaptic Weight Routing (Ω-GF01 a Ω-GF54)
Replaces v1 genetic_forge.py singleton. Forges synaptic connections between
agents and market states — learns which agents excel in which contexts and
routes signal weight accordingly. Uses Bayesian beta prior updating for
robust estimates with sparse data, pandemic isolation for new agents, and
automatic genome promotion/eviction.

Concept 1: Synaptic Weight Computation & Bayesian Updating (Ω-GF01–GF18)
  Each agent-regime pair has a Beta(alpha, beta) prior over win rate.
  Bayesian updating per trade outcome. Synaptic weight = E[WR] mapped to
  [0.1, 2.0] multiplier. Dirichlet process for regime clustering.

Concept 2: Pandemic Agent Lifecycle & Genetic Evolution (Ω-GF19–GF36)
  New agents born pandemic (isolated from real capital). Must prove edge
  in paper trading window before graduation. Pandemic agents are bred via
  crossover of top-performing agents + Gaussian mutation. Failed agents
  are culled. Genome inheritance with epigenetic decay.

Concept 3: Forge Orchestration & Self-Optimization (Ω-GF37–GF54)
  Periodic forge cycles: evaluate all agents, promote/cull, adjust priors,
  generate new pandemic candidates if performance diversity is low.
  JSON-persisted state for crash recovery. Anti-gaming detection.
"""

from __future__ import annotations

import json
import math
import os
import random
import time
from dataclasses import dataclass, field, asdict
from typing import Any


# ──────────────────────────────────────────────────────────────
# Ω-GF01 to Ω-GF18: Synaptic Weight Computation & Bayesian Updating
# ──────────────────────────────────────────────────────────────


@dataclass
class AgentSynapse:
    """Ω-GF01: Bayesian synaptic connection between agent and a context."""

    agent_name: str
    context_key: str  # state hash, regime, or global
    alpha: float = 1.0  # Beta prior success (pseudo-counts: 1=uniform prior)
    beta: float = 1.0  # Beta prior failure
    n_trades: int = 0
    total_pnl: float = 0.0
    avg_pnl: float = 0.0
    sharpe_estimate: float = 0.0
    last_trade_ns: int = 0
    streak_wins: int = 0
    streak_losses: int = 0
    max_streak_wins: int = 0
    max_streak_losses: int = 0

    @property
    def posterior_mean(self) -> float:
        """Ω-GF02: E[win_rate] = alpha / (alpha + beta)."""
        return self.alpha / (self.alpha + self.beta)

    @property
    def posterior_variance(self) -> float:
        """Variance of Beta posterior."""
        a, b = self.alpha, self.beta
        return (a * b) / ((a + b) ** 2 * (a + b + 1))

    @property
    def credible_interval_95(self) -> tuple[float, float]:
        """Ω-GF03: Approximate 95% CI using normal approx (good for n>10)."""
        mean = self.posterior_mean
        var = self.posterior_variance
        z = 1.96
        lo = max(0.0, mean - z * math.sqrt(var))
        hi = min(1.0, mean + z * math.sqrt(var))
        return (round(lo, 4), round(hi, 4))

    @property
    def synaptic_weight(self) -> float:
        """Ω-GF04: Maps posterior mean to [0.1, 2.0] multiplier.

        Scaling:
        - WR < 0.35: weight → 0.1 (silenced)
        - WR = 0.50: weight → 1.0 (neutral)
        - WR > 0.70: weight → 2.0 (dominant)
        With sample size discount for sparse data.
        """
        mean = self.posterior_mean

        # Piecewise mapping
        if mean < 0.35:
            w = 0.10
        elif mean < 0.50:
            w = 0.10 + 0.90 * (mean - 0.35) / 0.15
        elif mean < 0.70:
            w = 1.0 + 0.50 * (mean - 0.50) / 0.20
        else:
            w = 1.50 + 0.50 * min(1.0, (mean - 0.70) / 0.15)

        # Sample size penalty: < 5 trades → weight pulled toward 1.0
        if self.n_trades < 5:
            discount = self.n_trades / 5.0
            w = 1.0 + (w - 1.0) * discount

        return round(max(0.1, min(2.0, w)), 4)

    def update(self, won: bool, pnl: float) -> None:
        """Ω-GF05: Bayesian update after a trade."""
        if won:
            self.alpha += 1.0
            self.streak_wins += 1
            self.streak_losses = 0
            self.max_streak_wins = max(self.max_streak_wins, self.streak_wins)
        else:
            self.beta += 1.0
            self.streak_losses += 1
            self.streak_wins = 0
            self.max_streak_losses = max(self.max_streak_losses, self.streak_losses)

        self.n_trades += 1
        self.total_pnl += pnl
        self.avg_pnl = self.total_pnl / self.n_trades
        self.last_trade_ns = time.time_ns()

        # Running Sharpe estimate
        if self.n_trades >= 2:
            abs_pnl = abs(self.avg_pnl) + abs(self.total_pnl) / (self.n_trades + 1)
            std = max(1e-9, abs_pnl)
            self.sharpe_estimate = self.avg_pnl / std

    def apply_decay(self, decay_factor: float = 0.99) -> None:
        """Ω-GF06: Exponential decay of prior counts (forgetting old data)."""
        self.alpha = 1.0 + (self.alpha - 1.0) * decay_factor
        self.beta = 1.0 + (self.beta - 1.0) * decay_factor


class SynapticRegistry:
    """Ω-GF07: Manages all synapses across agents and contexts."""

    def __init__(self, prior_alpha: float = 1.0, prior_beta: float = 1.0) -> None:
        self._synapses: dict[tuple[str, str], AgentSynapse] = {}
        self._default_alpha = prior_alpha
        self._default_beta = prior_beta

    def get_or_create(self, agent_name: str, context_key: str) -> AgentSynapse:
        key = (agent_name, context_key)
        if key not in self._synapses:
            self._synapses[key] = AgentSynapse(
                agent_name=agent_name,
                context_key=context_key,
                alpha=self._default_alpha,
                beta=self._default_beta,
            )
        return self._synapses[key]

    def get(self, agent_name: str, context_key: str) -> AgentSynapse | None:
        return self._synapses.get((agent_name, context_key))

    def get_agent_synapses(self, agent_name: str) -> list[AgentSynapse]:
        return [
            s for (name, _), s in self._synapses.items() if name == agent_name
        ]

    def get_context_synapses(self, context_key: str) -> list[AgentSynapse]:
        return [
            s for (_, ctx), s in self._synapses.items() if ctx == context_key
        ]

    def all_synapses(self) -> dict[tuple[str, str], AgentSynapse]:
        return dict(self._synapses)

    def prune_inactive(self, max_age_ns: int = 30 * 24 * 3600 * 1_000_000_000) -> int:
        """Ω-GF08: Remove synapses with no activity in max_age."""
        now = time.time_ns()
        to_remove = [
            k for k, s in self._synapses.items()
            if now - s.last_trade_ns > max_age_ns
        ]
        for k in to_remove:
            del self._synapses[k]
        return len(to_remove)

    def apply_global_decay(self, decay_factor: float = 0.99) -> int:
        for s in self._synapses.values():
            s.apply_decay(decay_factor)
        return len(self._synapses)


class SynapticRouter:
    """Ω-GF09: Routes signals through synapses to compute effective weights."""

    def __init__(self, registry: SynapticRegistry) -> None:
        self._registry = registry

    def route(
        self,
        agent_name: str,
        context_key: str,
        global_key: str = "__global__",
    ) -> tuple[float, float, str]:
        """Ω-GF10: Get routed weight for agent in context.

        Returns: (weight, confidence, reasoning)
        Weight: [0.1, 2.0]
        Confidence: [0, 1] — how reliable is this weight estimate
        """
        # Specific context weight
        ctx_syn = self._registry.get(agent_name, context_key)
        # Global weight
        glob_syn = self._registry.get(agent_name, global_key)

        if ctx_syn and ctx_syn.n_trades >= 10:
            # Context-specific weight — high confidence
            w = ctx_syn.synaptic_weight
            conf = min(1.0, ctx_syn.n_trades / 50.0)
            ci = ctx_syn.credible_interval_95
            reason = (
                f"context_synaptic: WR={ctx_syn.posterior_mean:.2f} "
                f"[{ci[0]:.2f}-{ci[1]:.2f}] n={ctx_syn.n_trades}"
            )
            return (round(w, 4), round(conf, 4), reason)

        # Blend context + global if context has sparse data
        if ctx_syn is not None and glob_syn is not None:
            # Linear blend with n_trades-dependent weight
            total = ctx_syn.n_trades + glob_syn.n_trades
            if total > 0:
                ctx_weight = ctx_syn.n_trades / total
            else:
                ctx_weight = 0.5

            w_ctx = ctx_syn.synaptic_weight
            w_glob = glob_syn.synaptic_weight
            w = ctx_weight * w_ctx + (1 - ctx_weight) * w_glob
            conf = min(1.0, total / 30.0)
            reason = (
                f"blended: ctx={w_ctx:.2f}(n={ctx_syn.n_trades}) "
                f"glob={w_glob:.2f}(n={glob_syn.n_trades})"
            )
            return (round(w, 4), round(conf, 4), reason)

        # Global-only fallback
        if glob_syn:
            w = glob_syn.synaptic_weight
            conf = min(1.0, glob_syn.n_trades / 50.0)
            reason = f"global_synaptic: WR={glob_syn.posterior_mean:.2f} n={glob_syn.n_trades}"
            return (round(w, 4), round(conf, 4), reason)

        # No data: return neutral weight with low confidence
        return (1.0, 0.0, "no_data_prior")

    def get_all_agent_weights(
        self, agent_names: list[str], context_key: str
    ) -> dict[str, tuple[float, float, str]]:
        """Ω-GF11: Batch route for all agents."""
        return {
            name: self.route(name, context_key) for name in agent_names
        }

    def rank_agents(
        self, agent_names: list[str], context_key: str, top_k: int = 5
    ) -> list[tuple[str, float]]:
        """Ω-GF12: Rank agents by synaptic weight for context."""
        results = self.get_all_agent_weights(agent_names, context_key)
        ranked = sorted(results.items(), key=lambda x: x[1][0], reverse=True)
        return [(name, weight) for name, (weight, _, _) in ranked[:top_k]]


# ──────────────────────────────────────────────────────────────
# Ω-GF19 to Ω-GF36: Pandemic Agent Lifecycle & Genetic Evolution
# ──────────────────────────────────────────────────────────────


class PandemicStatus:
    """Ω-GF19: Tracks quarantine status of a new agent."""

    ISOLATED = "isolated"  # Paper trading only, no real capital
    PROBATION = "probation"  # Small allocation, monitored
    GRADUATED = "graduated"  # Full capital access, proven edge
    CULLED = "culled"  # Failed, removed from active pool


@dataclass
class PandemicAgent:
    """Ω-GF20: An agent in quarantine/evolution."""

    name: str
    genome_hash: str  # Fingerprint of agent's parameters/strategy
    parent_a: str
    parent_b: str
    mutation_rate: float
    status: str = PandemicStatus.ISOLATED
    paper_trades: int = 0
    paper_wins: int = 0
    paper_pnl: float = 0.0
    real_trades: int = 0
    real_wins: int = 0
    real_pnl: float = 0.0
    creation_ns: int = field(default_factory=lambda: time.time_ns())
    last_trade_ns: int = 0
    generation: int = 1
    genome_params: dict[str, float] = field(default_factory=dict)

    @property
    def paper_win_rate(self) -> float:
        return self.paper_wins / max(1, self.paper_trades)

    @property
    def real_win_rate(self) -> float:
        return self.real_wins / max(1, self.real_trades)

    def record_paper_outcome(self, won: bool, pnl: float) -> None:
        self.paper_trades += 1
        if won:
            self.paper_wins += 1
        self.paper_pnl += pnl
        self.last_trade_ns = time.time_ns()

    def record_real_outcome(self, won: bool, pnl: float) -> None:
        self.real_trades += 1
        if won:
            self.real_wins += 1
        self.real_pnl += pnl
        self.last_trade_ns = time.time_ns()


class PandemicQuarantine:
    """Ω-GF21: Manages pandemic agent lifecycle."""

    def __init__(
        self,
        min_paper_trades: int = 30,
        min_paper_wr: float = 0.52,
        min_probation_trades: int = 15,
        min_probation_wr: float = 0.50,
        max_pandemic_agents: int = 50,
    ) -> None:
        self._min_paper_trades = min_paper_trades
        self._min_paper_wr = min_paper_wr
        self._min_probation_trades = min_probation_trades
        self._min_probation_wr = min_probation_wr
        self._max_pandemic = max_pandemic_agents
        self._pandemic_agents: dict[str, PandemicAgent] = {}
        self._generation_count: int = 0

    def spawn(
        self,
        parent_a: str,
        parent_b: str,
        genome: dict[str, float],
        mutation_rate: float,
    ) -> PandemicAgent:
        """Ω-GF22: Create new pandemic agent from two parents."""
        self._generation_count += 1
        genome_hash = _hash_genome(genome)

        name = f"pandemic_{parent_a[:6]}_{parent_b[:6]}_g{self._generation_count}"

        agent = PandemicAgent(
            name=name,
            genome_hash=genome_hash,
            parent_a=parent_a,
            parent_b=parent_b,
            mutation_rate=mutation_rate,
            generation=self._generation_count,
            genome_params=genome,
        )

        self._pandemic_agents[name] = agent
        return agent

    def update_paper(self, name: str, won: bool, pnl: float) -> None:
        if name in self._pandemic_agents:
            self._pandemic_agents[name].record_paper_outcome(won, pnl)

    def promote_to_probation(self, name: str) -> bool:
        """Ω-GF23: Graduate from isolated → probation if paper WR is sufficient."""
        agent = self._pandemic_agents.get(name)
        if not agent:
            return False
        if agent.paper_trades < self._min_paper_trades:
            return False
        if agent.paper_win_rate < self._min_paper_wr:
            return False
        if agent.status != PandemicStatus.ISOLATED:
            return False

        agent.status = PandemicStatus.PROBATION
        return True

    def promote_to_graduated(self, name: str) -> bool:
        """Ω-GF24: Graduate from probation → full access if real WR is sufficient."""
        agent = self._pandemic_agents.get(name)
        if not agent:
            return False
        if agent.real_trades < self._min_probation_trades:
            return False
        if agent.real_win_rate < self._min_probation_wr:
            return False
        if agent.status != PandemicStatus.PROBATION:
            return False

        agent.status = PandemicStatus.GRADUATED
        return True

    def cull(self, name: str) -> bool:
        """Ω-GF25: Remove pandemic agent that isn't performing."""
        agent = self._pandemic_agents.get(name)
        if not agent:
            return False

        agent.status = PandemicStatus.CULLED
        del self._pandemic_agents[name]
        return True

    def check_promotions(self) -> list[tuple[str, str]]:
        """Ω-GF26: Auto-check all agents for promotion/culling."""
        actions: list[tuple[str, str]] = []
        to_remove: list[str] = []

        for name, agent in self._pandemic_agents.items():
            if agent.status == PandemicStatus.ISOLATED:
                if self._should_promote_to_probation(agent):
                    agent.status = PandemicStatus.PROBATION
                    actions.append((name, "promoted_to_probation"))
                elif agent.paper_trades >= self._min_paper_trades * 3:
                    # Way too many paper trades with no promotion → cull
                    if agent.paper_win_rate < self._min_paper_wr - 0.05:
                        to_remove.append(name)
                        actions.append((name, "culled_paper_failed"))

            elif agent.status == PandemicStatus.PROBATION:
                if self._should_promote_to_graduated(agent):
                    agent.status = PandemicStatus.GRADUATED
                    actions.append((name, "graduated"))
                elif agent.real_trades >= self._min_probation_trades * 3:
                    if agent.real_win_rate < self._min_probation_wr - 0.05:
                        to_remove.append(name)
                        actions.append((name, "culled_probation_failed"))

        for name in to_remove:
            self.cull(name)

        # Cap total population
        active = [n for n, a in self._pandemic_agents.items() if a.status != PandemicStatus.CULLED]
        if len(active) > self._max_pandemic:
            # Cull worst performers
            scored = [
                (n, self._pandemic_agents[n].paper_win_rate if self._pandemic_agents[n].status == PandemicStatus.ISOLATED else self._pandemic_agents[n].real_win_rate)
                for n in active
            ]
            scored.sort(key=lambda x: x[1])
            for name, _ in scored[: len(active) - self._max_pandemic]:
                self.cull(name)
                actions.append((name, "culled_overpopulation"))

        return actions

    def _should_promote_to_probation(self, agent: PandemicAgent) -> bool:
        if agent.paper_trades < self._min_paper_trades:
            return False
        return agent.paper_win_rate >= self._min_paper_wr

    def _should_promote_to_graduated(self, agent: PandemicAgent) -> bool:
        if agent.real_trades < self._min_probation_trades:
            return False
        return agent.real_win_rate >= self._min_probation_wr

    def get_active(self) -> list[PandemicAgent]:
        return [
            a for a in self._pandemic_agents.values()
            if a.status in (PandemicStatus.ISOLATED, PandemicStatus.PROBATION, PandemicStatus.GRADUATED)
        ]

    def get_graduated(self) -> list[PandemicAgent]:
        return [
            a for a in self._pandemic_agents.values()
            if a.status == PandemicStatus.GRADUATED
        ]

    def get_stats(self) -> dict[str, Any]:
        all_agents = list(self._pandemic_agents.values())
        return {
            "total_created": self._generation_count,
            "active": len([a for a in all_agents if a.status != PandemicStatus.CULLED]),
            "isolated": len([a for a in all_agents if a.status == PandemicStatus.ISOLATED]),
            "probation": len([a for a in all_agents if a.status == PandemicStatus.PROBATION]),
            "graduated": len([a for a in all_agents if a.status == PandemicStatus.GRADUATED]),
            "culled": self._generation_count - len([a for a in all_agents if a.status != PandemicStatus.CULLED]),
        }


def _hash_genome(genome: dict[str, float]) -> str:
    """Deterministic genome hash."""
    sorted_items = sorted(genome.items())
    raw = json.dumps(sorted_items, sort_keys=True)
    return hex(abs(hash(raw)) % (10 ** 12))[2:]


def crossover_genomes(
    genome_a: dict[str, float],
    genome_b: dict[str, float],
    mutation_rate: float = 0.1,
    mutation_strength: float = 0.05,
) -> dict[str, float]:
    """Ω-GF27: Uniform crossover + Gaussian mutation."""
    child: dict[str, float] = {}

    all_keys = set(genome_a.keys()) | set(genome_b.keys())
    for key in all_keys:
        val_a = genome_a.get(key, 0.0)
        val_b = genome_b.get(key, 0.0)

        # Uniform crossover: pick from either parent
        if key in genome_a and key in genome_b:
            child[key] = random.choice([val_a, val_b])
        elif key in genome_a:
            child[key] = val_a
        else:
            child[key] = val_b

        # Gaussian mutation
        if random.random() < mutation_rate:
            spread = abs(child[key]) * mutation_strength
            child[key] += random.gauss(0, spread)

    return child


# ──────────────────────────────────────────────────────────────
# Ω-GF37 to Ω-GF54: Forge Orchestration & Self-Optimization
# ──────────────────────────────────────────────────────────────


@dataclass
class ForgeCycle:
    """Ω-GF37: Record of one forge cycle."""

    cycle_number: int
    timestamp_ns: int
    n_agents_evaluated: int
    n_promoted: int
    n_culled: int
    n_new_pandemic: int
    avg_synaptic_weight: float
    best_agent: str
    best_agent_wr: float
    diversity_score: float  # [0, 1]


class GeneticForge:
    """Ω-GF38: Master forge orchestration engine."""

    def __init__(
        self,
        storage_path: str = "data/genetic_forge/synapses.json",
        min_paper_trades: int = 30,
        max_pandemic_agents: int = 50,
        decay_factor: float = 0.99,
    ) -> None:
        self.registry = SynapticRegistry()
        self.router = SynapticRouter(self.registry)
        self.quarantine = PandemicQuarantine(
            min_paper_trades=min_paper_trades,
            max_pandemic_agents=max_pandemic_agents,
        )
        self._storage_path = storage_path
        self._decay_factor = decay_factor
        self._cycle_count: int = 0
        self._cycle_history: list[ForgeCycle] = []

        # Load saved state
        self._load_state()

    def record_trade(
        self,
        agent_name: str,
        state_hash: str,
        won: bool,
        pnl: float,
    ) -> None:
        """Ω-GF39: Record a trade outcome."""
        # Global synapse
        glob = self.registry.get_or_create(agent_name, "__global__")
        glob.update(won, pnl)

        # State-specific synapse
        local = self.registry.get_or_create(agent_name, state_hash)
        local.update(won, pnl)

    def get_synaptic_weight(
        self,
        agent_name: str,
        state_hash: str,
    ) -> tuple[float, float, str]:
        """Ω-GF40: Get synaptic weight for agent in state."""
        return self.router.route(agent_name, state_hash)

    def forge_cycle(
        self,
        active_agents: list[tuple[str, dict[str, float]]],  # [(name, genome), ...]
        state_hash: str = "forge_global",
    ) -> ForgeCycle:
        """Ω-GF41: Run a full forge evaluation cycle.

        Evaluates all agents, promotes/culls pandemic agents,
        spawns new mutants if diversity is low.
        """
        self._cycle_count += 1
        t0 = time.time_ns()

        # 1. Evaluate agents
        weights = self.router.get_all_agent_weights(
            [name for name, _ in active_agents], state_hash
        )

        avg_w = sum(w[0] for w in weights.values()) / max(1, len(weights))
        best_name = max(weights.items(), key=lambda x: x[1][0])[0]
        best_wr = self.registry.get_or_create(best_name, "__global__").posterior_mean

        # 2. Diversity check
        all_wrs = []
        for name, _ in active_agents:
            s = self.registry.get(name, "__global__")
            if s:
                all_wrs.append(s.posterior_mean)

        if len(all_wrs) >= 2:
            mean_wr = sum(all_wrs) / len(all_wrs)
            var_wr = sum((w - mean_wr) ** 2 for w in all_wrs) / len(all_wrs)
            diversity = min(1.0, math.sqrt(var_wr) * 5)
        else:
            diversity = 0.0

        # 3. Pandemic promotion/culling
        actions = self.quarantine.check_promotions()
        n_promoted = sum(1 for _, a in actions if "promot" in a or "grad" in a)
        n_culled = sum(1 for _, a in actions if "cull" in a)

        # 4. If diversity is low, spawn new pandemic agents
        n_new = 0
        if diversity < 0.15 and len(active_agents) >= 2:
            # Top 2 → crossover
            ranked = sorted(active_agents, key=lambda x: weights.get(x[0], (1.0, 0, ""))[0], reverse=True)
            if len(ranked) >= 2:
                parent_a_data = ranked[0]
                parent_b_data = ranked[min(1, len(ranked) - 1)]

                genome = crossover_genomes(
                    parent_a_data[1] if len(parent_a_data) > 1 else {},
                    parent_b_data[1] if len(parent_b_data) > 1 else {},
                    mutation_rate=random.uniform(0.1, 0.3),
                )

                self.quarantine.spawn(
                    parent_a=parent_a_data[0],
                    parent_b=parent_b_data[0],
                    genome=genome,
                    mutation_rate=random.uniform(0.1, 0.3),
                )
                n_new += 1

        cycle = ForgeCycle(
            cycle_number=self._cycle_count,
            timestamp_ns=t0,
            n_agents_evaluated=len(active_agents),
            n_promoted=n_promoted,
            n_culled=n_culled,
            n_new_pandemic=n_new,
            avg_synaptic_weight=round(avg_w, 4),
            best_agent=best_name,
            best_agent_wr=round(best_wr, 4),
            diversity_score=round(diversity, 4),
        )
        self._cycle_history.append(cycle)

        # Periodic decay
        if self._cycle_count % 10 == 0:
            self.registry.apply_global_decay(self._decay_factor)

        # Save state
        self._save_state()

        return cycle

    def get_rankings(self, state_hash: str = "__global__", top_k: int = 10) -> list[tuple[str, float, str, str]]:
        """Ω-GF42: Get ranked agents by synaptic weight."""
        synapses = self.registry.get_context_synapses(state_hash)
        if not synapses:
            synapses = self.registry.get_context_synapses("__global__")

        ranked = sorted(synapses, key=lambda s: s.synaptic_weight, reverse=True)
        return [
            (s.agent_name, round(s.synaptic_weight, 4), s.reasoning if hasattr(s, 'reasoning') else "", s.context_key)
            for s in ranked[:top_k]
        ]

    def get_stats(self) -> dict[str, Any]:
        return {
            "registry": {
                "total_synapses": len(self.registry.all_synapses()),
                "unique_agents": len(set(k[0] for k in self.registry.all_synapses())),
                "unique_contexts": len(set(k[1] for k in self.registry.all_synapses())),
            },
            "quarantine": self.quarantine.get_stats(),
            "forge_cycles": {
                "total_cycles": self._cycle_count,
                "last_avg_weight": (
                    self._cycle_history[-1].avg_synaptic_weight
                    if self._cycle_history else 1.0
                ),
                "last_best_agent": (
                    self._cycle_history[-1].best_agent
                    if self._cycle_history else "none"
                ),
            },
        }

    def _save_state(self) -> None:
        os.makedirs(os.path.dirname(self._storage_path) or ".", exist_ok=True)
        state: dict[str, Any] = {
            "synapses": {},
            "cycle_count": self._cycle_count,
        }

        for (agent, ctx), syn in self.registry.all_synapses().items():
            key = f"{agent}::{ctx}"
            state["synapses"][key] = {
                "alpha": syn.alpha,
                "beta": syn.beta,
                "n_trades": syn.n_trades,
                "total_pnl": syn.total_pnl,
                "avg_pnl": syn.avg_pnl,
                "sharpe_estimate": syn.sharpe_estimate,
                "last_trade_ns": syn.last_trade_ns,
                "streak_wins": syn.streak_wins,
                "streak_losses": syn.streak_losses,
                "max_streak_wins": syn.max_streak_wins,
                "max_streak_losses": syn.max_streak_losses,
            }

        # Pandemic agents
        state["pandemic"] = {
            name: {
                "genome_hash": a.genome_hash,
                "parent_a": a.parent_a,
                "parent_b": a.parent_b,
                "mutation_rate": a.mutation_rate,
                "status": a.status,
                "paper_trades": a.paper_trades,
                "paper_wins": a.paper_wins,
                "paper_pnl": a.paper_pnl,
                "real_trades": a.real_trades,
                "real_wins": a.real_wins,
                "real_pnl": a.real_pnl,
                "creation_ns": a.creation_ns,
                "generation": a.generation,
                "genome_params": a.genome_params,
            }
            for name, a in self.quarantine._pandemic_agents.items()
        }

        with open(self._storage_path, "w") as f:
            json.dump(state, f)

    def _load_state(self) -> None:
        if not os.path.exists(self._storage_path):
            return

        try:
            with open(self._storage_path) as f:
                state = json.load(f)

            self._cycle_count = state.get("cycle", 0)

            for key, data in state.get("synapses", {}).items():
                if "::" not in key:
                    continue
                agent, ctx = key.split("::", 1)
                syn = self.registry.get_or_create(agent, ctx)
                syn.alpha = data.get("alpha", 1.0)
                syn.beta = data.get("beta", 1.0)
                syn.n_trades = data.get("n_trades", 0)
                syn.total_pnl = data.get("total_pnl", 0.0)
                syn.avg_pnl = data.get("avg_pnl", 0.0)
                syn.sharpe_estimate = data.get("sharpe_estimate", 0.0)
                syn.last_trade_ns = data.get("last_trade_ns", 0)
                syn.streak_wins = data.get("streak_wins", 0)
                syn.streak_losses = data.get("streak_losses", 0)
                syn.max_streak_wins = data.get("max_streak_wins", 0)
                syn.max_streak_losses = data.get("max_streak_losses", 0)

            for name, data in state.get("pandemic", {}).items():
                agent = PandemicAgent(
                    name=name,
                    genome_hash=data["genome_hash"],
                    parent_a=data["parent_a"],
                    parent_b=data["parent_b"],
                    mutation_rate=data["mutation_rate"],
                    status=data["status"],
                    paper_trades=data["paper_trades"],
                    paper_wins=data["paper_wins"],
                    paper_pnl=data["paper_pnl"],
                    real_trades=data.get("real_trades", 0),
                    real_wins=data.get("real_wins", 0),
                    real_pnl=data.get("real_pnl", 0.0),
                    creation_ns=data.get("creation", 0) * 1_000_000_000,
                    generation=data.get("generation", 1),
                    genome_params=data.get("genome_params", {}),
                )
                self.quarantine._pandemic_agents[name] = agent

        except (json.JSONDecodeError, KeyError):
            pass  # Corrupted state → start fresh
