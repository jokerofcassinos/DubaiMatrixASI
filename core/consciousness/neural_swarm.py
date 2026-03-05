"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — NEURAL SWARM                          ║
║    Enxame de agentes analíticos ultra-especializados — a CONSCIÊNCIA        ║
║                                                                              ║
║  Orquestrador leve que importa agentes de módulos separados.                ║
║  Cada módulo contém um "setor de consciência" escalável.                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import time
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils.logger import log

# ═══════════════════════════════════════════════════════════════
#  IMPORTAÇÃO MODULAR DE AGENTES
# ═══════════════════════════════════════════════════════════════

from core.consciousness.agents.base import AgentSignal, BaseAgent

# Phase 3 — Classic Agents (9)
from core.consciousness.agents.classic import (
    TrendAgent, MomentumAgent, VolumeAgent, VolatilityAgent,
    MicrostructureAgent, StatisticalAgent, FractalAgent,
    SupportResistanceAgent, DivergenceAgent,
)

# Phase 10 — Omega Agents (5)
from core.consciousness.agents.omega import (
    LiquidationVacuumAgent, TimeWarpAgent, HarmonicResonanceAgent,
    ReflexivityAgent, BlackSwanAgent,
)

# Phase 11 — Predator Agents (5)
from core.consciousness.agents.predator import (
    IcebergHunterAgent, StopHunterAgent, InstitutionalFootprintAgent,
    LiquiditySiphonAgent, OrderBookPressureAgent,
)

# Phase 12 — Chaos & Quantum Agents (5)
from core.consciousness.agents.chaos import (
    InformationEntropyAgent, PhaseSpaceAttractorAgent, VPINProxyAgent,
    OrderBookEvaporationAgent, CrossScaleConvergenceAgent,
)

# Phase 13 — Global Macro & Whale Agents (4)
from core.consciousness.agents.global_macro import (
    SentimentFearGreedAgent, OnChainPressureAgent, MacroBiasAgent,
    WhaleTrackerAgent,
)

# Phase 14 — Physics & Kinematics Agents (5)
from core.consciousness.agents.physics import (
    NavierStokesFluidAgent, MagneticPolarizationAgent,
    ThermalEquilibriumAgent, QuantumTunnelingAgent,
    DopplerShiftAgent,
)

# Phase 15 — Behavioral & Game Theory + C++ Accelerated Agents (5)
from core.consciousness.agents.behavioral import (
    RetailPsychologyAgent, GameTheoryNashAgent,
    CppAcceleratedFractalAgent, CppTickEntropyAgent,
    CppCrossScaleAgent,
)

# Phase 16 — Smart Money Concepts / ICT Agents (7)
from core.consciousness.agents.smc import (
    LiquiditySweepAgent, MarketStructureShiftAgent, FairValueGapAgent,
    LiquidityHeatmapAgent, OrderBlockAgent, PremiumDiscountAgent,
    BreakOfStructureAgent,
)

# Phase 17 — Chart Structure & Candle Anatomy Agents (2)
from core.consciousness.agents.chart_structure import (
    ChartStructureAgent, CandleAnatomyAgent,
)

# Phase 19 — Market Dynamics Agents (5)
from core.consciousness.agents.dynamics import (
    PriceGravityAgent, AggressivenessAgent, ExplosionDetectorAgent,
    PriceVelocityAgent, OscillationWaveAgent,
)

# Phase 26 — Meta-Swarm Agents (2)
from core.consciousness.agents.meta_swarm import (
    ConfidenceAggregatorAgent, ExecutionScalerAgent,
)


# ═══════════════════════════════════════════════════════════════
#  NEURAL SWARM — O ENXAME COMPLETO
# ═══════════════════════════════════════════════════════════════

class NeuralSwarm:
    """
    Enxame Neural — orquestra todos os agentes.
    Cada agente é um neurônio. O enxame é a consciência coletiva.
    
    Arquitetura modular: agentes vivem em core/consciousness/agents/
    e são importados aqui. Para adicionar novos agentes, basta:
    1. Criar classe em agents/<modulo>.py herdando BaseAgent
    2. Se precisa de orderflow_analysis, setar self.needs_orderflow = True
    3. Adicionar instância na lista _initialize_agents() abaixo
    """

    def __init__(self):
        self.agents: List[BaseAgent] = []
        self._initialize_agents()
        # Thread pool para execução paralela (max_workers calibrado para o hardware e número de agentes)
        self._executor = ThreadPoolExecutor(max_workers=32)
        log.omega(f"🧠 Neural Swarm inicializado: {len(self.agents)} agentes ativos (Parallel Execution Enabled)")

    def shutdown(self):
        """Finaliza o executor."""
        self._executor.shutdown(wait=False)

    def _initialize_agents(self):
        """Spawna todos os agentes neurais de todos os setores."""
        self.agents = [
            # ═══ CLASSIC (Phase 3) ═══
            TrendAgent(weight=1.0),
            MomentumAgent(weight=1.0),
            VolumeAgent(weight=0.8),
            VolatilityAgent(weight=0.9),
            MicrostructureAgent(weight=1.2),
            StatisticalAgent(weight=0.8),
            FractalAgent(weight=0.6),
            SupportResistanceAgent(weight=0.9),
            DivergenceAgent(weight=0.7),

            # ═══ OMEGA (Phase 10) ═══
            LiquidationVacuumAgent(weight=1.5),
            TimeWarpAgent(weight=1.1),
            HarmonicResonanceAgent(weight=0.8),
            ReflexivityAgent(weight=1.3),
            BlackSwanAgent(weight=2.0),

            # ═══ PREDATOR (Phase 11) ═══
            IcebergHunterAgent(weight=1.4),
            StopHunterAgent(weight=1.6),
            InstitutionalFootprintAgent(weight=1.5),
            LiquiditySiphonAgent(weight=1.3),
            OrderBookPressureAgent(weight=1.2),

            # ═══ CHAOS & QUANTUM (Phase 12) ═══
            InformationEntropyAgent(weight=1.6),
            PhaseSpaceAttractorAgent(weight=1.4),
            VPINProxyAgent(weight=1.5),
            OrderBookEvaporationAgent(weight=1.7),
            CrossScaleConvergenceAgent(weight=1.8),

            # ═══ GLOBAL MACRO & WHALE (Phase 13) ═══
            SentimentFearGreedAgent(weight=1.1),
            OnChainPressureAgent(weight=1.3),
            MacroBiasAgent(weight=1.4),
            WhaleTrackerAgent(weight=1.8),

            # ═══ PHYSICS & KINEMATICS (Phase 14) ═══
            NavierStokesFluidAgent(weight=1.6),
            MagneticPolarizationAgent(weight=1.4),
            ThermalEquilibriumAgent(weight=1.2),
            QuantumTunnelingAgent(weight=1.9),
            DopplerShiftAgent(weight=1.5),

            # ═══ BEHAVIORAL & C++ CLUSTER (Phase 15) ═══
            RetailPsychologyAgent(weight=1.4),
            GameTheoryNashAgent(weight=1.5),
            CppAcceleratedFractalAgent(weight=0.9),
            CppTickEntropyAgent(weight=1.7),
            CppCrossScaleAgent(weight=1.6),

            # ═══ SMART MONEY CONCEPTS / ICT (Phase 16) ═══
            LiquiditySweepAgent(weight=2.0),
            MarketStructureShiftAgent(weight=1.9),
            FairValueGapAgent(weight=1.8),
            LiquidityHeatmapAgent(weight=1.6),
            OrderBlockAgent(weight=2.0),
            PremiumDiscountAgent(weight=1.5),
            BreakOfStructureAgent(weight=1.7),

            # ═══ CHART STRUCTURE & CANDLE ANATOMY (Phase 17) ═══
            ChartStructureAgent(weight=1.5),
            CandleAnatomyAgent(weight=1.3),

            # ═══ MARKET DYNAMICS (Phase 19) ═══
            PriceGravityAgent(weight=1.6),
            AggressivenessAgent(weight=1.7),
            ExplosionDetectorAgent(weight=2.0),
            PriceVelocityAgent(weight=1.8),
            OscillationWaveAgent(weight=1.5),

            # ═══ META-SWARM (Phase 26) ═══
            ConfidenceAggregatorAgent(),
            ExecutionScalerAgent(),
        ]

    def analyze(self, snapshot, orderflow_analysis: dict = None) -> List[AgentSignal]:
        """
        Executa TODOS os agentes EM PARALELO e coleta seus sinais.
        Retorna lista de AgentSignals para o Quantum Thought Engine.
        """
        # Usar map para reduzir overhead de criação de dict de futuros
        def _run_agent(agent):
            try:
                if agent.needs_orderflow:
                    return agent.analyze(snapshot, orderflow_analysis=orderflow_analysis)
                return agent.analyze(snapshot)
            except Exception as e:
                log.error(f"Agent {agent.name} falhou: {e}")
                return AgentSignal(agent.name, 0.0, 0.0, f"ERROR: {e}", agent.weight)

        # Execução paralela em massa
        results = list(self._executor.map(_run_agent, self.agents, timeout=0.6))
        
        # Filtrar None e retornar
        return [r for r in results if r is not None]

    def get_agent_by_name(self, name: str) -> Optional[BaseAgent]:
        """Busca agente pelo nome."""
        for agent in self.agents:
            if agent.name == name:
                return agent
        return None

    def update_weight(self, agent_name: str, new_weight: float):
        """Atualiza peso de um agente (auto-evolução)."""
        agent = self.get_agent_by_name(agent_name)
        if agent:
            old = agent.weight
            agent.weight = max(0.1, min(3.0, new_weight))
            log.info(f"⚖️ {agent_name} weight: {old:.2f} → {agent.weight:.2f}")

    def summary(self) -> dict:
        """Resumo do swarm."""
        return {
            "total_agents": len(self.agents),
            "agents": [
                {"name": a.name, "weight": a.weight, "accuracy": a.accuracy}
                for a in self.agents
            ]
        }
