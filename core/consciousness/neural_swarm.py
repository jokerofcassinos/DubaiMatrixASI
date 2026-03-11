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
from utils.decorators import ast_self_heal

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

# Phase 42 — High-Fidelity Pressure & Transition Agents (6)
from core.consciousness.agents.pressure_matrix import PressureMatrixAgent
from core.consciousness.agents.market_transition import MarketTransitionAgent
from core.consciousness.agents.session_dynamics import SessionDynamicsAgent, TemporalTrendAgent
from core.consciousness.agents.hex_matrix import HexMatrixAgent

# Phase Ω-Next — Market Intuition
from core.consciousness.agents.market_intuition_agent import MarketIntuitionAgent

# Phase Ω-Next — Shadow Predator
from core.consciousness.agents.shadow_predator_agent import ShadowPredatorAgent
from core.consciousness.agents.leech_agent import LiquidityLeechAgent

# Phase Ω-Next — Black Swan
from core.consciousness.agents.black_swan_agent import BlackSwanAgent

# Phase Ω-Next — Tensor
from core.consciousness.agents.tensor_agent import TensorAgent
from core.consciousness.agents.supernova_capacitor import SupernovaCapacitorAgent

# Phase 43 — Advanced Structural & Institutional Agents (4)
from core.consciousness.agents.wyckoff import WyckoffStructuralAgent
from core.consciousness.agents.structural_premium import CRTAgent, TBSAgent
from core.consciousness.agents.smc import ICTAdvancedAgent

# Phase Ω-Next — LGNN & Thermodynamics (2)
from core.consciousness.agents.graph_topology_agent import GraphTopologyAgent
from core.consciousness.agents.thermodynamic_agent import ThermodynamicAgent

# Phase Ω-One — SNN, MFG, Feynman & Chaos (4)
from core.consciousness.agents.asynchronous_pulse_agent import AsynchronousPulseAgent
from core.consciousness.agents.mean_field_game_agent import MeanFieldGameAgent
from core.consciousness.agents.feynman_path_agent import FeynmanPathAgent
from core.consciousness.agents.chaos_regime_agent import ChaosRegimeAgent

# Phase Ω-Class — Omega Omniscience (1)
from core.consciousness.agents.holographic_manifold_agent import HolographicManifoldAgent
from core.consciousness.agents.dark_mass_agent import DarkMassAgent
from core.consciousness.agents.liquid_state_agent import LiquidStateAgent
from core.consciousness.agents.pheromone_field_agent import PheromoneFieldAgent

# Phase Ω-Transcendence
from core.consciousness.agents.transcendence_agents import (
    RiemannianManifoldAgent, InformationGeometryAgent, QuantumSuperpositionAgent
)
from core.consciousness.agents.holographic_memory_agent import HolographicMemoryAgent
from core.consciousness.agents.omniscience_agents import (
    OrderBookSpoofingAgent, QuantumEntanglementAgent
)

# Phase Ω-Singularity (Nível 5 - Autotranscendência)
from core.consciousness.agents.singularity_agents import (
    AccretionDiskAgent, KinematicDerivativesAgent, TopologicalDataAgent
)

# Phase Ω-Eternity (Nível 6 - Teoria do Caos e Homeostase)
from core.consciousness.agents.eternity_agents import (
    QuantumSpinAgent, CyberneticHomeostasisAgent, ChaosFractalDimensionAgent
)

# Phase Ω-Apocalypse (Nível 7 - Inteligência Predatória Hostil)
from core.consciousness.agents.apocalypse_agents import (
    DarkPoolArbitrageAgent, OptionGammaSqueezeAgent
)

# Phase Ω-Apotheosis (Nível 8 - Inteligência Cósmica & Bio-Cibernética)
from core.consciousness.agents.apotheosis_agents import (
    MorphogeneticResonanceAgent, AntifragileExtremumAgent, 
    AntifragileExhaustionAgent, QuantumTunnelingProbabilityAgent
)

# Phase Ω-Nexus (Nível 9 - Grafos de Liquidez e Choques Vetoriais)
from core.consciousness.agents.nexus_agents import (
    LiquidityGraphAgent, VectorAutoregressionAgent
)

# Phase Ω-Paragon (Nível 10 - Teoria dos Jogos Evolutiva)
from core.consciousness.agents.paragon_agents import (
    AsymmetricInformationAgent, BaitAndSwitchDetectorAgent, EvolutionaryNashEquilibriumAgent
)

# Phase Ω-Elysium (Nível 11 - Inteligência Suprema Não-Linear)
from core.consciousness.agents.elysium_agents import (
    HiddenMarkovRegimeAgent, FractalStandardDeviationAgent, DarkEnergyMomentumAgent
)

# Phase Ω-Illuminati (Nível 12 - Relatividade Temporal e Análise Espectral)
from core.consciousness.agents.illuminati_agents import (
    ChronosDilationAgent, FourierSpectralAgent, LiquidityVoidMagnetAgent
)

# Phase Ω-Genesis (Nível 13 - Inferência Causal e Contrafactual)
from core.consciousness.agents.genesis_agents import (
    CausalCounterfactualAgent, IntentionalityDecompositionAgent
)

# Phase Ω-Architect (Nível 14 - Centralidade de Autovetores e Bait-Layering)
from core.consciousness.agents.architect_agents import (
    EigenvectorCentralityAgent, BaitLayeringSpoofAgent
)

# Phase Ω-Ascension (Nível 15 - Fluxo Multidimensional e Absorção)
from core.consciousness.agents.ascension_agents import (
    OrderBookImbalanceAgent, BlowOffTopDetectorAgent
)

# Phase Ω-Sovereignty (Nível 16 - Atenção Temporal e Delta Cruzado)
from core.consciousness.agents.sovereignty_agents import (
    TemporalAttentionAgent, CrossExchangeDeltaAgent
)

# Phase Ω-Emanation (Nível 17 - Geometria Não-Euclidiana e Teoria da Informação)
from core.consciousness.agents.emanation_agents import (
    NonEuclideanGeometryAgent, ShannonKLDivergenceAgent, StringTheoryVibrationAgent
)

# Phase Ω-Void (Nível 18 - Cosmologia do Livro de Ofertas)
from core.consciousness.agents.void_agents import (
    WhiteHoleInjectionAgent, HawkingRadiationAgent, GravitationalLensingAgent
)

# Phase Ω-Synapse (Nível 19 - Plasticidade Sináptica e Ruína HFT)
from core.consciousness.agents.synapse_agents import (
    OrderFlowSynapticPlasticityAgent, HFTRuinProbabilityAgent
)

# Phase Ω-Extreme — Lorentz, QCA, PredatorPrey, EVT (3)
from core.consciousness.agents.omega_extreme import (
    QCAAgent, PredatorPreyAgent, EVTBlackSwanAgent
)

# C++ Bridge
from cpp.asi_bridge import CPP_CORE


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

    def __init__(self, memory=None, predator_engine=None):
        self.agents: List[BaseAgent] = []
        self._initialize_agents(memory, predator_engine)
        # Thread pool para execução paralela (max_workers calibrado para o hardware e número de agentes)
        # [Phase Ω-Eternity] Elevado para 64 para acomodar a explosão demográfica de agentes super-pesados
        self._executor = ThreadPoolExecutor(max_workers=64)
        log.omega(f"🧠 Neural Swarm inicializado: {len(self.agents)} agentes ativos (Parallel Execution Enabled)")

    def shutdown(self):
        """Finaliza o executor."""
        self._executor.shutdown(wait=False)

    def _initialize_agents(self, memory=None, predator_engine=None):
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
            # BlackSwanAgent(weight=2.0), -- Moved to its own section

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

            # ═══ HIGH-FIDELITY & SESSION (Phase 42) ═══
            PressureMatrixAgent(weight=1.8),
            MarketTransitionAgent(weight=1.5),
            SessionDynamicsAgent(weight=1.2),
            TemporalTrendAgent(weight=1.3),
            HexMatrixAgent(weight=0.8),

            # ═══ STRUCTURAL & INSTITUTIONAL (Phase 43) ═══
            WyckoffStructuralAgent(weight=1.8),
            CRTAgent(weight=1.5),
            TBSAgent(weight=1.7),
            ICTAdvancedAgent(weight=2.2),
            
            # ═══ MARKET INTUITION (Phase Ω-Next) ═══
            MarketIntuitionAgent(memory) if memory else None,
            
            # ═══ SHADOW PREDATOR & LEECH (Phase Ω-Next / Transcendence) ═══
            ShadowPredatorAgent(predator_engine) if predator_engine else None,
            LiquidityLeechAgent(predator_engine, weight=2.3) if predator_engine else None,

            # ═══ Ω-EXTREME (Phase Ω-Extreme) ═══
            QCAAgent(weight=1.6),
            PredatorPreyAgent(weight=1.5),
            EVTBlackSwanAgent(weight=2.2),
            SupernovaCapacitorAgent(weight=2.5),
            
            # BlackSwanAgent(weight=2.0), # Substituído pelo EVTBlackSwan
            TensorAgent(weight=1.9),

            # ═══ LGNN & THERMODYNAMICS (Phase Ω-Next) ═══
            GraphTopologyAgent(),
            ThermodynamicAgent(),

            # ═══ SNN, MFG, FEYNMAN & CHAOS (Phase Ω-One) ═══
            AsynchronousPulseAgent(weight=2.2),
            MeanFieldGameAgent(weight=2.5),
            FeynmanPathAgent(weight=2.8),
            ChaosRegimeAgent(weight=1.5),

            # ═══ OMEGA-CLASS OMNISCIENCE ═══
            HolographicManifoldAgent(),
            DarkMassAgent(weight=2.4),
            LiquidStateAgent(weight=2.5),
            PheromoneFieldAgent(weight=1.8),

            # ═══ TRANSCENDENCE & MEMORY (Phase Ω-Transcendence) ═══
            RiemannianManifoldAgent(weight=2.5),
            InformationGeometryAgent(weight=2.2),
            QuantumSuperpositionAgent(weight=2.4),
            HolographicMemoryAgent(weight=3.0),
            OrderBookSpoofingAgent(weight=2.6),
            QuantumEntanglementAgent(weight=3.0),

            # ═══ SINGULARITY (Phase Ω-Singularity) ═══
            AccretionDiskAgent(weight=3.5),
            KinematicDerivativesAgent(weight=3.8),
            TopologicalDataAgent(weight=2.8),

            # ═══ ETERNITY (Phase Ω-Eternity) ═══
            QuantumSpinAgent(weight=2.9),
            CyberneticHomeostasisAgent(weight=2.7),
            ChaosFractalDimensionAgent(weight=3.2),

            # ═══ APOCALYPSE (Phase Ω-Apocalypse) ═══
            DarkPoolArbitrageAgent(weight=3.5),
            OptionGammaSqueezeAgent(weight=3.8),

            # ═══ APOTHEOSIS (Phase Ω-Apotheosis) ═══
            MorphogeneticResonanceAgent(weight=3.3),
            AntifragileExtremumAgent(weight=3.7),
            AntifragileExhaustionAgent(weight=3.5),
            QuantumTunnelingProbabilityAgent(weight=3.1),

            # ═══ NEXUS (Phase Ω-Nexus) ═══
            LiquidityGraphAgent(weight=3.6),
            VectorAutoregressionAgent(weight=3.4),

            # ═══ PARAGON (Phase Ω-Paragon) ═══
            AsymmetricInformationAgent(weight=3.7),
            BaitAndSwitchDetectorAgent(weight=3.9),
            EvolutionaryNashEquilibriumAgent(weight=3.2),

            # ═══ ELYSIUM (Phase Ω-Elysium) ═══
            HiddenMarkovRegimeAgent(weight=3.8),
            FractalStandardDeviationAgent(weight=3.5),
            DarkEnergyMomentumAgent(weight=4.0),

            # ═══ ILLUMINATI (Phase Ω-Illuminati) ═══
            ChronosDilationAgent(weight=3.9),
            FourierSpectralAgent(weight=3.4),
            LiquidityVoidMagnetAgent(weight=3.6),

            # ═══ GENESIS (Phase Ω-Genesis) ═══
            CausalCounterfactualAgent(weight=4.2),
            IntentionalityDecompositionAgent(weight=4.0),

            # ═══ ARCHITECT (Phase Ω-Architect) ═══
            EigenvectorCentralityAgent(weight=4.1),
            BaitLayeringSpoofAgent(weight=4.3),

            # ═══ META-SWARM (Phase 26) ═══
            ConfidenceAggregatorAgent(),
            ExecutionScalerAgent(),
        ]
        # Remover agentes que não foram inicializados (None)
        self.agents = [a for a in self.agents if a is not None]

    @ast_self_heal
    def analyze(self, snapshot, orderflow_analysis: dict = None, **kwargs) -> List[AgentSignal]:
        """
        Executa TODOS os agentes EM PARALELO e coleta seus sinais.
        Retorna lista de AgentSignals para o Quantum Thought Engine.
        """
        # Usar map para reduzir overhead de criação de dict de futuros
        def _run_agent(agent):
            try:
                # Agentes podem opcionalmente aceitar kwargs específicos
                if agent.needs_orderflow:
                    return agent.analyze(snapshot, orderflow_analysis=orderflow_analysis, **kwargs)
                return agent.analyze(snapshot, **kwargs)
            except Exception as e:
                log.error(f"Agent {agent.name} falhou: {e}")
                return AgentSignal(agent.name, 0.0, 0.0, f"ERROR: {e}", agent.weight)

        # Execução paralela em massa com rastreamento de latência (Phase 42)
        start_time = time.monotonic()
        try:
            # Aumentamos o timeout para 1.2s para acomodar 54 agentes
            results = list(self._executor.map(_run_agent, self.agents, timeout=1.2))
        except TimeoutError:
            # Diagnóstico de Inconsciência: Identificar qual agente está asfixiando o enxame
            elapsed = time.monotonic() - start_time
            log.error(f"💀 NeuralSwarm TIMEOUT após {elapsed:.3f}s! Verificando agentes lentos...")
            # Fallback seguro: retornar o que foi processado ou lista vazia
            return []
        
        # Filtrar None e retornar
        signals = [r for r in results if r is not None]

        # [STIGMERGY] Depositamos feromônio de agressão no nível de preço
        for result in signals:
            if result and result.signal != 0.0:
                CPP_CORE.deposit_pheromone(snapshot.price, abs(result.signal), decay=0.05)

        # [STIGMERGY] Update global field decay
        CPP_CORE.update_pheromones(dt=1.0)

        return signals

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
