"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — MUTATION ENGINE                            ║
║     Motor de Mutação Genética de Parâmetros                                ║
║                                                                              ║
║  Aplica mutações controladas nos Omega Parameters baseado em              ║
║  performance observada — evolução darwiniana algorítmica.                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random
import time
import numpy as np
from datetime import datetime, timezone
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

from config.omega_params import OMEGA
from utils.logger import log
from utils.decorators import catch_and_log


@dataclass
class MutationRecord:
    """Registro de uma mutação aplicada."""
    timestamp: str
    param_name: str
    old_value: float
    new_value: float
    mutation_type: str         # "gaussian", "uniform", "targeted"
    reason: str
    performance_before: float  # Métrica before
    reverted: bool = False


class MutationEngine:
    """
    Motor de Mutação — evolui parâmetros da ASI via mutação genética controlada.

    Estratégias:
    1. GAUSSIAN DRIFT — pequenas mudanças proporcionais ao valor atual
    2. UNIFORM EXPLORATION — exploração uniforme dentro dos bounds
    3. TARGETED MUTATION — mutação direcionada por análise de performance
    4. CROSSOVER — combina valores de diferentes "gerações" bem-sucedidas
    """

    def __init__(self):
        self._mutation_history: List[MutationRecord] = []
        self._generation = 0
        self._best_genome: Dict[str, float] = {}       # Melhor configuração conhecida
        self._best_fitness: float = -float("inf")
        self._mutation_rate = 0.1       # 10% de chance de mutação por param
        self._mutation_strength = 0.05  # 5% do range como desvio padrão
        self._cooldown_cycles = 500     # Ciclos mínimos entre mutações
        self._last_mutation_cycle = 0
        self._enabled = True

    def should_mutate(self, cycle: int) -> bool:
        """Verifica se é hora de aplicar mutações."""
        if not self._enabled:
            return False
        if cycle - self._last_mutation_cycle < self._cooldown_cycles:
            return False
        return True

    @catch_and_log(default_return=[])
    def mutate(self, cycle: int, performance: dict) -> List[MutationRecord]:
        """
        Executa um ciclo de mutação.
        
        Args:
            cycle: Ciclo atual da consciousness
            performance: Dict com métricas (win_rate, profit_factor, etc.)
        
        Returns:
            Lista de mutações aplicadas
        """
        if not self.should_mutate(cycle):
            return []

        self._generation += 1
        self._last_mutation_cycle = cycle
        mutations = []

        # Extrair fitness atual
        fitness = self._compute_fitness(performance)

        # Salvar melhor genome se melhorou
        if fitness > self._best_fitness:
            self._best_fitness = fitness
            self._best_genome = OMEGA.to_dict()
            log.omega(f"🧬 Novo melhor genome! Fitness={fitness:.4f} Gen={self._generation}")

        # Decidir tipo de mutação
        mutation_type = self._choose_mutation_strategy(performance)

        # Aplicar mutações nos parâmetros Omega
        param_names = list(OMEGA.params.keys())
        
        for name in param_names:
            if random.random() > self._mutation_rate:
                continue  # Skip este param (não mutado)

            param = OMEGA.params[name]
            old_value = param.value
            
            # OMEGA: Shield para parâmetros críticos
            # thresholds e confidence NÃO podem usar uniform (exploração cega)
            # pois causam paralisia sensorial.
            is_critical = any(k in name.lower() for k in ["threshold", "confidence", "phi_min"])
            effective_strategy = "gaussian" if (is_critical and mutation_type == "uniform") else mutation_type

            if effective_strategy == "gaussian":
                new_value = self._gaussian_mutation(param.value, param.min_val, param.max_val)
            elif effective_strategy == "uniform":
                new_value = self._uniform_mutation(param.min_val, param.max_val)
            elif effective_strategy == "targeted":
                new_value = self._targeted_mutation(name, param.value, param.min_val, param.max_val, performance)
            else:
                new_value = self._gaussian_mutation(param.value, param.min_val, param.max_val)

            # Sanity Clamp para Φ (Não deixar mutação automática pedir > 0.35 base)
            if name == "phi_min_threshold":
                new_value = min(0.35, new_value)

            # Aplicar mutação
            OMEGA.set(name, new_value)

            record = MutationRecord(
                timestamp=datetime.now(timezone.utc).isoformat(),
                param_name=name,
                old_value=old_value,
                new_value=new_value,
                mutation_type=mutation_type,
                reason=f"Gen {self._generation} auto-evolution",
                performance_before=fitness,
            )
            mutations.append(record)
            self._mutation_history.append(record)

        if mutations:
            log.omega(
                f"🧬 Gen #{self._generation}: {len(mutations)} mutações aplicadas | "
                f"Tipo={mutation_type} | Fitness={fitness:.4f}"
            )

        return mutations

    def revert_last_mutations(self):
        """Reverte as últimas mutações se performance piorou."""
        if not self._best_genome:
            return

        for name, value in self._best_genome.items():
            OMEGA.set(name, value)

        log.omega("🧬 Mutações revertidas para melhor genome conhecido")

    def _compute_fitness(self, perf: dict) -> float:
        """Calcula fitness score baseado em performance."""
        wr = perf.get("win_rate", 0)
        pf = perf.get("profit_factor", 0)
        total_profit = perf.get("total_profit", 0)
        max_dd = perf.get("max_drawdown", 0)
        trades = perf.get("total_trades", 0)

        # Fitness: combinação ponderada de métricas
        fitness = 0.0
        fitness += wr * 40                              # Win rate (40 pontos max)
        fitness += min(pf, 5) * 10                      # Profit factor (50 pontos max)
        fitness += min(total_profit / 100, 20)           # Profit total (20 pontos max)
        fitness -= max_dd * 0.5                          # Penalidade por drawdown
        fitness += min(trades, 100) * 0.1                # Bônus por volume de trades

        return fitness

    def _choose_mutation_strategy(self, perf: dict) -> str:
        """Escolhe a estratégia de mutação baseado no estado atual."""
        wr = perf.get("win_rate", 0)
        trades = perf.get("total_trades", 0)

        # Poucos trades: exploração uniforme
        if trades < 20:
            return "uniform"

        # Win rate bom: mutação suave (gaussian)
        if wr > 0.6:
            return "gaussian"

        # Win rate ruim: mutação agressiva direcionada
        if wr < 0.4:
            return "targeted"

        return "gaussian"

    def _gaussian_mutation(self, value: float, min_val: float, max_val: float) -> float:
        """Mutação gaussiana — pequena perturbação."""
        spread = (max_val - min_val) * self._mutation_strength
        new_val = value + random.gauss(0, spread)
        return max(min_val, min(max_val, new_val))

    def _uniform_mutation(self, min_val: float, max_val: float) -> float:
        """Mutação uniforme — exploração completa."""
        return random.uniform(min_val, max_val)

    def _targeted_mutation(self, name: str, value: float,
                           min_val: float, max_val: float,
                           perf: dict) -> float:
        """Mutação direcionada baseada em análise de performance."""
        # Se win rate baixo, tentar ser mais conservador
        wr = perf.get("win_rate", 0.5)

        if "threshold" in name.lower() or "confidence" in name.lower():
            # Aumentar thresholds (mais seletivo)
            direction = 1 if wr < 0.5 else -1
            delta = (max_val - min_val) * 0.1 * direction
            return max(min_val, min(max_val, value + delta))

        if "aggression" in name.lower():
            # Diminuir agressividade se perdendo
            if wr < 0.5:
                return max(min_val, value * 0.9)
            else:
                return min(max_val, value * 1.1)

        # Default: gaussian
        return self._gaussian_mutation(value, min_val, max_val)

    @property
    def metrics(self) -> dict:
        return {
            "generation": self._generation,
            "total_mutations": len(self._mutation_history),
            "best_fitness": self._best_fitness,
            "mutation_rate": self._mutation_rate,
            "enabled": self._enabled,
            "cooldown_remaining": max(0, self._cooldown_cycles - 
                                       (self._last_mutation_cycle or 0)),
        }
