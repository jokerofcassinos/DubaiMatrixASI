import random
import time
import logging
import json
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

from config.omega_params import OMEGA
from core.intelligence.base_synapse import BaseSynapse
from config.settings import DATA_DIR

log = logging.getLogger("SOLENN.MutationEngine")

@dataclass
class MutationRecord:
    """V25: Registro de uma mutação aplicada (V138)."""
    timestamp: float
    param_name: str
    old_value: float
    new_value: float
    strategy: str # gaussian, uniform, targeted
    fitness_before: float
    reverted: bool = False

class MutationEngine(BaseSynapse):
    """
    Ω-7.NAS, Ω-34 & Ω-40: O Motor de Busca de Ótimos da SOLÉNN.
    
    Aplica mutações genéticas controladas (v2) para otimizar 
    os parâmetros Omega baseados na performance real.
    """
    
    def __init__(self):
        super().__init__("MutationEngine")
        self.history_path = os.path.join(DATA_DIR, "evolution", "mutation_history.json")
        self.history: List[MutationRecord] = []
        self.best_genome: Dict[str, float] = OMEGA.to_dict()
        self.best_fitness: float = -1.0
        self.generation: int = 0
        
        # Parâmetros de Motor
        self.mutation_rate = 0.2 # 20% p/ cada parâmetro
        self.mutation_strength = 0.05 # 5% do range
        self.cooldown_trades = 50 # trades entre mutações
        self.trades_since_mutation = 0

    def compute_fitness(self, performance: Dict[str, Any]) -> float:
        """
        V10: Função de Fitness multi-objetivo (Sharpe, RRR, WinRate).
        """
        wr = performance.get("win_rate", 0.5)
        pf = performance.get("profit_factor", 1.0)
        rrr = performance.get("rrr", 1.0)
        net_profit = performance.get("net_profit", 0.0)
        max_dd = performance.get("max_drawdown", 1.0)
        
        # Fórmula de Fitness (Ω-Transcendence)
        # Priorização de RRR e Sobrevivência
        fitness = (wr * 20) + (min(pf, 5) * 5)
        
        if rrr >= 1.0:
            fitness += (rrr * 30)
        else:
            fitness -= (1.0 - rrr) * 50 # Punição brutal para RRR ruim
            
        fitness += min(net_profit / 100, 40)
        fitness -= max_dd * 2.0
        
        return round(float(fitness), 4)

    def select_strategy(self, fitness: float, performance: Dict[str, Any]) -> str:
        """
        V19-V27: Actor-Critic Policy Selection.
        """
        if fitness < self.best_fitness * 0.8:
            return "uniform" # Exploração ampla se degradando (V2)
            
        if performance.get("rrr", 1.0) < 0.8:
            return "targeted_rrr" # Foco em RRR
            
        return "gaussian" # Refinamento (V1)

    def apply_mutation(self, performance: Dict[str, Any]) -> List[MutationRecord]:
        """
        V1-V9: Ciclo de Mutação Genética.
        """
        self.generation += 1
        current_fitness = self.compute_fitness(performance)
        
        # Salva o melhor genoma (V18)
        if current_fitness > self.best_fitness:
            self.best_fitness = current_fitness
            self.best_genome = OMEGA.to_dict()
            log.info(f"🧬 [Ω-FORGE] Novo Melhor Genoma! Fitness: {current_fitness:.4f}")
        
        # Reversão (V37) se performance cair muito
        if current_fitness < self.best_fitness * 0.7:
             log.warning("⏪ [Ω-FORGE] Regressão detectada! Revertendo para Best Genome.")
             self.rollback()
             return []

        strategy = self.select_strategy(current_fitness, performance)
        mutations = []
        
        for name, p in OMEGA.params.items():
            if random.random() > self.mutation_rate:
                continue
                
            old_value = p.value
            new_value = old_value
            
            # V1: Gaussian
            if strategy == "gaussian":
                range_width = p.max_val - p.min_val
                new_value = old_value + random.gauss(0, range_width * self.mutation_strength)
            
            # V2: Uniform
            elif strategy == "uniform":
                new_value = random.uniform(p.min_val, p.max_val)
                
            # V3-V28: Targeted
            elif strategy == "targeted_rrr":
                if "take_profit" in name.lower():
                    new_value = old_value * 1.1 # Esticar TP
                elif "stop_loss" in name.lower():
                    new_value = old_value * 0.9 # Encurtar SL (V29)
            
            OMEGA.set(name, new_value)
            
            mutations.append(MutationRecord(
                timestamp=time.time(),
                param_name=name,
                old_value=old_value,
                new_value=OMEGA.params[name].value, # Pega o valor clampado
                strategy=strategy,
                fitness_before=current_fitness
            ))
            
        self.history.extend(mutations)
        self.trades_since_mutation = 0
        OMEGA.save()
        return mutations

    def rollback(self):
        """V37: Reversão para o melhor estado conhecido."""
        for name, value in self.best_genome.items():
            OMEGA.set(name, value)
        OMEGA.save()

    async def process(self, snapshot: Any, nexus_context: Any = None) -> Dict[str, Any]:
        """[Ω-EXEC] Gateway evolutivo."""
        return {
            "node": self.name,
            "generation": self.generation,
            "best_fitness": self.best_fitness,
            "history_size": len(self.history)
        }

# Motor de Mutação Ω (v2) inicializado.
# Otimizando a busca de ótimos em tempo real.
