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
            # thresholds, confidence e limites de execução NÃO podem usar uniform (exploração cega)
            # pois causam paralisia sensorial ou gargalos de hardware.
            is_critical = any(k in name.lower() for k in ["threshold", "confidence", "phi_min", "splits", "position_size"])
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
            
            # Sanity Clamp para Fragmentação (Evitar asfixia do MT5)
            if name == "max_order_splits":
                new_value = min(15.0, new_value)
                
            # Sanity Clamp para Risco (Evitar exposição suicida > 75%)
            if name == "position_size_pct":
                new_value = min(75.0, new_value)

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
        """
        Calcula fitness score baseado em performance líquida (Net Alpha).
        [Phase Ω-Transcendence] Evolução focada em RRR (Risco-Retorno) e sobrevivência de longo prazo.
        """
        wr = perf.get("win_rate", 0)
        pf = perf.get("profit_factor", 0)
        total_profit = perf.get("total_profit", 0) # Já deve ser NET
        max_dd = perf.get("max_drawdown", 0)
        trades = perf.get("total_trades", 0)
        
        avg_win = perf.get("avg_win", 0.0)
        avg_loss = abs(perf.get("avg_loss", 1.0))
        rrr = avg_win / avg_loss if avg_loss > 0 else 1.0

        # Fitness: Foco absoluto em crescimento Real e Assimetria de Risco
        fitness = 0.0
        
        # Win Rate (20 pts) - Reduzido para dar lugar ao RRR
        fitness += wr * 20                              
        
        # Profit Factor (20 pts)
        fitness += min(pf, 4) * 5                      
        
        # [Phase Ω-Transcendence] Assimetria de Risco (RRR) - Motor principal
        # Se RRR > 1.0, bônus exponencial. Se RRR < 0.5, penalidade severa.
        if rrr >= 1.0:
            fitness += (rrr * 30) # Premia trades longos e lucrativos
        else:
            fitness -= (1.0 - rrr) * 50 # Punição brutal para "scalp medroso"
        
        # Alpha Líquido (40 pts)
        fitness += min(total_profit / 100, 40)           
        
        # Penalidade por Drawdown
        fitness -= max_dd * 1.5                         
        
        # Bônus por Volume (Apenas se PF > 1.2 e RRR > 0.8)
        if pf > 1.2 and rrr > 0.8:
            fitness += min(trades, 200) * 0.1
        
        # PENALIDADE DE COMISSÃO (Anti-Churn)
        if total_profit > 0:
            gross = total_profit + abs(perf.get("total_commission", 0))
            if gross > 0:
                comm_ratio = abs(perf.get("total_commission", 0)) / gross
                if comm_ratio > 0.4:
                    fitness *= (1.0 - comm_ratio)

        return fitness

    def _choose_mutation_strategy(self, perf: dict) -> str:
        """
        [Phase Ω-Apocalypse] Actor-Critic (A2C) Policy Selection.
        O 'Critic' avalia as métricas atuais e direciona o 'Actor' para a
        estratégia de exploração/explotação ótima.
        """
        fitness = self._compute_fitness(perf)
        
        # Critic State Evaluation
        rrr = (perf.get("avg_win", 0.0) / abs(perf.get("avg_loss", 1.0))) if perf.get("avg_loss", 1.0) != 0 else 1.0
        wr = perf.get("win_rate", 0.0)
        
        # Se o fitness está caindo, ativamos exploração (Temperatura alta do Annealing resolve isso também)
        if fitness < self._best_fitness * 0.8:
            # Sistema degradando rápido: Exploração ampla
            return "uniform"
        
        # Se o RRR está péssimo (< 0.8), focamos em Targeted para esticar lucros
        if rrr < 0.8:
            return "targeted_rrr"
            
        # Se o WR está péssimo (< 0.5), focamos em Targeted para melhorar a precisão
        if wr < 0.5:
            return "targeted_precision"

        # Refinamento de uma estratégia que já é boa
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
                           perf: dict, strategy: str = "targeted") -> float:
        """
        Mutação direcionada pelo Ator (Actor) baseada na Crítica (Critic).
        """
        # Se a estratégia for focada em RRR, atuamos nos TPs e SLs
        if strategy == "targeted_rrr":
            if "take_profit" in name.lower():
                # Esticar TP
                return min(max_val, value * (1.0 + random.random() * 0.3)) # +0 a +30%
            elif "stop_loss" in name.lower():
                # Encurtar SL
                return max(min_val, value * (1.0 - random.random() * 0.2)) # -0 a -20%
            elif "kelly" in name.lower() or "size" in name.lower():
                # Diminuir agressividade de lote até arrumar RRR
                return max(min_val, value * 0.9)

        # Se a estratégia for focada em Precisão (WR), atuamos em Phi e Confidence
        elif strategy == "targeted_precision":
            if "phi_min" in name.lower() or "confidence" in name.lower() or "threshold" in name.lower():
                # Exigir mais certeza
                return min(max_val, value * (1.0 + random.random() * 0.15))
            elif "take_profit" in name.lower():
                # Encurtar levemente o TP para acertar mais
                return max(min_val, value * 0.9)
                
        # Fallback para o direcionamento simples antigo (se aplicável)
        wr = perf.get("win_rate", 0.5)
        if "threshold" in name.lower() or "confidence" in name.lower():
            direction = 1 if wr < 0.5 else -1
            delta = (max_val - min_val) * 0.1 * direction
            return max(min_val, min(max_val, value + delta))

        if "aggression" in name.lower():
            if wr < 0.5:
                return max(min_val, value * 0.9)
            else:
                return min(max_val, value * 1.1)

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
