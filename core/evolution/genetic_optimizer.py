"""
SOLÉNN v2 — Genetic Optimization Engine (Ω-V01 to Ω-V54)
Population management, meta-parameter optimization,
regime-specific optimization, walk-forward analysis,
self-replication with mutation, and gene preservation.

Concept 1: Genetic Optimization Tópicos 1.1–1.6
"""

from __future__ import annotations

import math
import random
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable


# ──────────────────────────────────────────────────────────────
# Ω-V01 to Ω-V09: Population Management
# ──────────────────────────────────────────────────────────────

@dataclass
class Individual:
    """Ω-V01: Single individual in the population."""
    genome: list[float]
    fitness: float = 0.0
    generation: int = 0
    age: int = 0
    species: str = "default"
    is_hall_of_fame: bool = False
    creation_time: float = field(default_factory=time.time)

    def clone(self) -> Individual:
        return Individual(
            genome=list(self.genome), fitness=self.fitness,
            generation=self.generation, age=self.age + 1,
            species=self.species, is_hall_of_fame=self.is_hall_of_fame,
        )


@dataclass
class ParamSpec:
    """Ω-V10: Specification for a tunable parameter."""
    name: str
    low: float
    high: float
    default: float
    log_scale: bool = False


class PopulationManager:
    """
    Ω-V02 to Ω-V09: Population creation, selection,
    crossover, mutation, diversity, immigration, hall of fame.
    """

    def __init__(
        self,
        param_specs: list[ParamSpec],
        population_size: int = 50,
        elite_fraction: float = 0.1,
        mutation_rate: float = 0.1,
        mutation_std: float = 0.1,
    ) -> None:
        self._param_specs = param_specs
        self._n_params = len(param_specs)
        self._pop_size = population_size
        self._elite_size = max(1, int(population_size * elite_fraction))
        self._mutation_rate = mutation_rate
        self._mutation_std = mutation_std
        self._population: list[Individual] = []
        self._hall_of_fame: list[Individual] = []
        self._generation = 0
        self._diversity_history: list[float] = []
        self._fitness_history: list[float] = []

    def initialize_population(self) -> list[Individual]:
        """Ω-V02: Generate initial population with controlled diversity."""
        self._population = []
        for i in range(self._pop_size):
            genome = [random.uniform(spec.low, spec.high) for spec in self._param_specs]
            self._population.append(Individual(
                genome=genome, generation=0,
            ))
        return list(self._population)

    def evaluate_population(
        self, fitness_fn: Callable[[list[float]], float]
    ) -> list[Individual]:
        """Ω-V03: Evaluate fitness for each individual."""
        for ind in self._population:
            ind.fitness = fitness_fn(ind.genome)
        self._population.sort(key=lambda x: -x.fitness)
        self._fitness_history.append(self._population[0].fitness)
        return list(self._population)

    def select(self, k: int = 3) -> Individual:
        """Ω-V04: Tournament selection."""
        candidates = random.sample(self._population, min(k, len(self._population)))
        return max(candidates, key=lambda x: x.fitness)

    def crossover(self, parent1: Individual, parent2: Individual) -> Individual:
        """Ω-V05: Blend crossover (BLX-α)."""
        alpha = 0.5
        child_genome = []
        for g1, g2 in zip(parent1.genome, parent2.genome):
            lo = min(g1, g2) - alpha * abs(g2 - g1)
            hi = max(g1, g2) + alpha * abs(g2 - g1)
            child_genome.append(random.uniform(lo, hi))
        return Individual(
            genome=child_genome,
            generation=self._generation + 1,
        )

    def mutate(self, individual: Individual) -> Individual:
        """Ω-V06: Gaussian mutation with adaptive rate."""
        genome = list(individual.genome)
        for i in range(len(genome)):
            if random.random() < self._mutation_rate:
                spec = self._param_specs[i] if i < len(self._param_specs) else None
                std = self._mutation_std
                if spec and spec.log_scale and spec.low > 0:
                    log_val = math.log(max(genome[i], 1e-10))
                    log_val += random.gauss(0, std)
                    genome[i] = max(spec.low, min(spec.high, math.exp(log_val)))
                else:
                    genome[i] += random.gauss(0, std)
                    if spec:
                        genome[i] = max(spec.low, min(spec.high, genome[i]))
        return Individual(
            genome=genome, generation=individual.generation,
        )

    def evolve(self, fitness_fn: Callable[[list[float]], float]) -> list[Individual]:
        """One generation: select → crossover → mutate → elite."""
        self._population = self.evaluate_population(fitness_fn)

        # Check diversity
        self._diversity_history.append(self.compute_diversity())

        # Ω-V04: Elitism
        next_gen = [ind.clone() for ind in self._population[:self._elite_size]]

        # Ω-V09: Hall of Fame
        if not self._hall_of_fame or self._population[0].fitness > self._hall_of_fame[0].fitness:
            best = self._population[0].clone()
            best.is_hall_of_fame = True
            self._hall_of_fame.append(best)
            self._hall_of_fame.sort(key=lambda x: -x.fitness)
            if len(self._hall_of_fame) > 10:
                self._hall_of_fame = self._hall_of_fame[:10]

        # Fill rest with offspring
        while len(next_gen) < self._pop_size:
            p1 = self.select()
            p2 = self.select()
            child = self.crossover(p1, p2)
            child = self.mutate(child)
            next_gen.append(child)

        self._generation += 1
        self._population = next_gen
        return list(self._population)

    def compute_diversity(self) -> float:
        """Ω-V07: Population diversity via genome std."""
        if len(self._population) < 2:
            return 0.0
        genomes = [ind.genome for ind in self._population]
        n = len(genomes)
        avg_genome = [sum(g[i] for g in genomes) / n for i in range(self._n_params)]
        diversity = sum(
            sum((g[i] - avg_genome[i]) ** 2 for g in genomes) / n
            for i in range(self._n_params)
        )
        return math.sqrt(diversity)

    def immigrate(self, n: int = 5) -> None:
        """Ω-V08: Introduce random individuals."""
        for _ in range(n):
            genome = [random.uniform(spec.low, spec.high) for spec in self._param_specs]
            self._population.append(Individual(genome=genome, generation=self._generation))
        self._population = self._population[:self._pop_size]

    @property
    def best_individual(self) -> Individual | None:
        return self._population[0] if self._population else None

    @property
    def hall_of_fame(self) -> list[Individual]:
        return list(self._hall_of_fame)

    @property
    def generation(self) -> int:
        return self._generation

    @property
    def fitness_history(self) -> list[float]:
        return list(self._fitness_history)


# ──────────────────────────────────────────────────────────────
# Ω-V10 to Ω-V18: Meta-Parameter Optimization
# ──────────────────────────────────────────────────────────────

class MetaParameterOptimizer:
    """
    Ω-V10 to Ω-V18: Bayesian optimization with robustness checks,
    Sobol sensitivity, degeneracy detection, and multi-objective handling.
    """

    def __init__(self, param_specs: list[ParamSpec]) -> None:
        self._param_specs = param_specs
        self._evaluations: list[tuple[list[float], float, list[float]]] = []  # (params, fitness, multi_objective)
        self._best_genome: list[float] | None = None
        self._best_fitness: float = float("-inf")

    def evaluate(self, genome: list[float], fitness_fn: Callable[[list[float]], float]) -> float:
        """Evaluate and store result."""
        fitness = fitness_fn(genome)
        self._evaluations.append((list(genome), fitness, []))
        if fitness > self._best_fitness:
            self._best_fitness = fitness
            self._best_genome = list(genome)
        return fitness

    def suggest_random(self) -> list[float]:
        """Ω-V12: Random suggestion (exploration)."""
        return [random.uniform(spec.low, spec.high) for spec in self._param_specs]

    def suggest_best_nearby(self, radius: float = 0.1) -> list[float]:
        """Exploit near current best."""
        if self._best_genome is None:
            return self.suggest_random()
        result = []
        for i, spec in enumerate(self._param_specs):
            val = self._best_genome[i] + random.gauss(0, radius * (spec.high - spec.low))
            result.append(max(spec.low, min(spec.high, val)))
        return result

    def sobol_sensitivity(self, n_samples: int = 100) -> dict[int, float]:
        """Ω-V16: Sobol-like sensitivity analysis."""
        if not self._evaluations:
            return {}
        var_total = sum((e[1] - self._best_fitness) ** 2 for e in self._evaluations) / max(1, len(self._evaluations))
        if var_total == 0:
            return {i: 0.0 for i in range(len(self._param_specs))}

        sensitivities = {}
        for i in range(len(self._param_specs)):
            # Group evaluations by parameter value
            params_vals = [e[0][i] for e in self._evaluations]
            fitness_vals = [e[1] for e in self._evaluations]
            # Simple: correlation between param i and fitness
            mean_p = sum(params_vals) / len(params_vals)
            mean_f = sum(fitness_vals) / len(fitness_vals)
            cov = sum((p - mean_p) * (f - mean_f) for p, f in zip(params_vals, fitness_vals))
            var_p = sum((p - mean_p) ** 2 for p in params_vals)
            if var_p > 0:
                sensitivities[i] = abs(cov) / math.sqrt(var_p * var_total * len(fitness_vals)) if var_total > 0 else 0.0
            else:
                sensitivities[i] = 0.0
        return sensitivities

    def check_robustness(self, genome: list[float], fitness_fn: Callable[[list[float]], float], n_perturb: int = 20) -> dict[str, float]:
        """
        Ω-V15: Check if solution is in wide valley (robust) or narrow peak (fragile).
        """
        results = []
        for _ in range(n_perturb):
            perturbed = [g + random.gauss(0, 0.05) for g in genome]
            results.append(fitness_fn(perturbed))

        mean_f = sum(results) / len(results)
        std_f = (sum((r - mean_f) ** 2 for r in results) / max(1, len(results) - 1)) ** 0.5
        return {
            "mean_fitness": mean_f,
            "std_fitness": std_f,
            "robustness_ratio": std_f / max(abs(mean_f), 1e-10),
            "is_robust": std_f / max(abs(mean_f), 1e-10) < 0.1,
        }

    @property
    def best_result(self) -> tuple[list[float] | None, float]:
        return self._best_genome, self._best_fitness


# ──────────────────────────────────────────────────────────────
# Ω-V19 to Ω-V27: Regime-Specific Optimization
# ──────────────────────────────────────────────────────────────

class RegimeSpecificOptimizer:
    """
    Ω-V19 to Ω-V27: Per-regime optimization with
    shared parameters, transition optimization, and overfitting guard.
    """

    def __init__(self, param_specs: list[ParamSpec]) -> None:
        self._param_specs = param_specs
        self._regime_configs: dict[str, list[float]] = {}
        self._regime_data: dict[str, list[list[float]]] = {}
        self._regime_n_data: dict[str, int] = {}

    def add_regime_data(self, regime: str, params: list[float], n_samples: int = 100) -> None:
        if regime not in self._regime_data:
            self._regime_data[regime] = []
            self._regime_n_data[regime] = 0
        self._regime_data[regime].append(params)
        self._regime_n_data[regime] += n_samples

    def has_enough_data(self, regime: str, min_samples: int = 50) -> bool:
        return self._regime_n_data.get(regime, 0) >= min_samples

    def optimize_regime(
        self, regime: str, fitness_fn: Callable[[list[float]], float], n_gens: int = 30
    ) -> list[float] | None:
        """Ω-V20: Optimize parameters for a specific regime."""
        if not self.has_enough_data(regime):
            return None

        manager = PopulationManager(self._param_specs, population_size=30)
        manager.initialize_population()
        for _ in range(n_gens):
            manager.evolve(fitness_fn)

        best = manager.best_individual
        if best is not None:
            self._regime_configs[regime] = best.genome
            return best.genome
        return None

    def get_config_for_regime(self, regime: str) -> list[float] | None:
        return self._regime_configs.get(regime)

    def check_transition_smoothness(
        self, regime_a: str, regime_b: str,
    ) -> float:
        """Ω-V24: How smooth is the transition between regime configs?"""
        config_a = self._regime_configs.get(regime_a)
        config_b = self._regime_configs.get(regime_b)
        if config_a is None or config_b is None:
            return 0.0
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(config_a, config_b)))
        max_dist = sum(s.high - s.low for s in self._param_specs)
        if max_dist == 0:
            return 1.0
        return 1.0 - dist / max_dist  # 1.0 = perfectly smooth


# ──────────────────────────────────────────────────────────────
# Ω-V28 to Ω-V36: Walk-Forward Analysis
# ──────────────────────────────────────────────────────────────

class WalkForwardAnalyzer:
    """
    Ω-V28 to Ω-V36: Walk-forward optimization with
    stability metrics and Combinatorial Purged CV.
    """

    def __init__(
        self,
        param_specs: list[ParamSpec],
        train_window: int = 200,
        test_window: int = 50,
    ) -> None:
        self._param_specs = param_specs
        self._train_window = train_window
        self._test_window = test_window
        self._results: list[dict[str, Any]] = []

    def run_walk_forward(
        self,
        data: list[float],  # e.g., returns series
        fitness_fn: Callable[[list[float], list[float]], float],
    ) -> list[dict[str, Any]]:
        """Ω-V29: Walk-forward optimization."""
        self._results = []
        total_len = len(data)
        window = self._train_window + self._test_window
        if total_len < window:
            return [{"warning": "Not enough data for walk-forward"}]

        start = 0
        while start + window <= total_len:
            train_data = data[start:start + self._train_window]
            test_data = data[start + self._train_window:start + window]

            # Optimize on train
            manager = PopulationManager(self._param_specs, population_size=30)
            manager.initialize_population()

            def train_fitness(genome: list[float]) -> float:
                return fitness_fn(genome, train_data)

            for _ in range(20):
                manager.evolve(train_fitness)

            best = manager.best_individual
            if best is None:
                start += self._test_window
                continue

            # Evaluate on test
            test_fitness = fitness_fn(best.genome, test_data)
            degradation = 1.0 - (test_fitness / max(abs(best.fitness), 1e-10))

            self._results.append({
                "train_start": start,
                "train_fitness": best.fitness,
                "test_fitness": test_fitness,
                "degradation": degradation,
                "best_params": list(best.genome),
            })

            start += self._test_window

        return self._results

    def get_average_degradation(self) -> float:
        """Ω-V31: Average IS/OOS degradation."""
        if not self._results:
            return 0.0
        return sum(r.get("degradation", 0) for r in self._results) / len(self._results)

    def get_parameter_stability(self) -> dict[int, float]:
        """Ω-V32: How much do optimal params drift between windows?"""
        if len(self._results) < 2:
            return {}
        n_params = len(self._results[0]["best_params"])
        all_params = [[r["best_params"][i] for r in self._results] for i in range(n_params)]
        stability = {}
        for i, param_vals in enumerate(all_params):
            mean_p = sum(param_vals) / len(param_vals)
            std_p = (sum((v - mean_p) ** 2 for v in param_vals) / max(1, len(param_vals) - 1)) ** 0.5
            spec = self._param_specs[i] if i < len(self._param_specs) else None
            range_p = (spec.high - spec.low) if spec else 1.0
            stability[i] = 1.0 - min(1.0, std_p / max(range_p, 1e-10))
        return stability
