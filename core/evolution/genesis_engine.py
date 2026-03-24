"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — GENESIS ENGINE (HNP)                   ║
║                                                                              ║
║  Módulo responsável pela geração espontânea e mutação abstrata de agentes.   ║
║  Eles nascem com 'is_pandemic=True' para isolamento total do capital real.   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import List, Optional
from utils.logger import log

from core.consciousness.agents.base import BaseAgent, AgentSignal
from core.evolution.genetic_forge import GENETIC_FORGE

class MutantPandemicAgent(BaseAgent):
    """
    Um agente sintético nascido no Genesis Engine. 
    Aplica permutações matemáticas aos inputs do snapshot.
    """
    def __init__(self, name: str, parent_a: str, parent_b: str, mutation_rate: float):
        super().__init__(name=name, weight=1.0, is_pandemic=True)
        self.parent_a = parent_a
        self.parent_b = parent_b
        self.mutation_rate = mutation_rate
        # [Phase Ω-Phoenix] - In the future, this will hold neural weights / genome

    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        # Para um mutante genérico, votamos com base em ruído filtrado de momentum
        # A verdadeira lógica surgiria cruzando o '__dict__' ou os pesos dos pais.
        tick_vel = snapshot.metadata.get("tick_velocity", 0.0)
        
        # Sintetizador abstrato
        signal_val = np.tanh(tick_vel * np.random.normal(1.0, self.mutation_rate))
        conf = min(1.0, abs(signal_val) + np.random.uniform(0, 0.2))

        return AgentSignal(
            agent_name=self.name,
            signal=signal_val,
            confidence=conf,
            reasoning=f" [🦠 PANDEMIC_MUTATION: {self.parent_a} x {self.parent_b} | Mut={self.mutation_rate:.2f}]",
            is_pandemic=True
        )


class GenesisEngine:
    def __init__(self):
        self.active_mutants: dict[str, BaseAgent] = {}
        self.generation = 1
        log.omega(f"🦠 [GENESIS ENGINE] Desperto. Aguardando ciclos de entropia para mutação.")

    def spawn_mutants(self, base_swarm_agents: List[BaseAgent], snapshot) -> List[BaseAgent]:
        """
        Ocasionalmente, durante picos de entropia, o motor cruza os 2 agentes mais dominantes 
        para gerar versões mutantes isoladas (Pandemic).
        """
        # Limita a quantidade de agentes mutantes simultâneos na memória para evitar memory leak
        if len(self.active_mutants) > 50:
            self._prune_failed_mutants(snapshot)
            return list(self.active_mutants.values())

        if snapshot.metadata.get("M1_entropy", 0.0) > 0.85 and np.random.random() < 0.1:
            # Seleciona dois pais aleatórios dos atuais do swarm (baseado no histórico real)
            if len(base_swarm_agents) >= 2:
                parents = np.random.choice(base_swarm_agents, 2, replace=False)
                new_name = f"Mutant_{parents[0].name[:5]}_{parents[1].name[:5]}_v{self.generation}"
                
                mutant = MutantPandemicAgent(
                    name=new_name, 
                    parent_a=parents[0].name, 
                    parent_b=parents[1].name,
                    mutation_rate=np.random.uniform(0.1, 0.5)
                )
                
                self.active_mutants[new_name] = mutant
                self.generation += 1
                log.omega(f"🧬 [GENESIS SPARK] Nova mutação criada: {new_name}")

        return list(self.active_mutants.values())

    def _prune_failed_mutants(self, snapshot):
        """
        Remove mutantes que têm uma taxa de acerto péssima no GeneticForge.
        """
        sv_hash = snapshot.metadata.get("state_vector_hash", "UNKNOWN")
        if sv_hash == "UNKNOWN":
            return

        to_remove = []
        for name in self.active_mutants.keys():
            # Peso base 1.0. Se o Forge retornar < 0.5, é fracasso.
            # Se for > 1.0, é sucesso (pode ser promovido).
            w = GENETIC_FORGE.get_synaptic_weight(name, sv_hash)
            if w < 0.8:
                to_remove.append(name)
        
        for name in to_remove:
            del self.active_mutants[name]
            log.warning(f"☠️ [GENESIS PRUNE] Mutante {name} eliminado por ineficiência natural.")

# Singleton
GENESIS = GenesisEngine()
