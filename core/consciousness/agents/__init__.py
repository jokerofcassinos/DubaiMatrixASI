"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — NEURAL AGENTS PACKAGE                       ║
║     Cada arquivo = um setor de consciência. Escalável a centenas.           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from core.consciousness.agents.base import AgentSignal, BaseAgent
from core.consciousness.agents.classic import (
    TrendAgent, MomentumAgent, VolumeAgent, VolatilityAgent,
    MicrostructureAgent, StatisticalAgent, FractalAgent,
    SupportResistanceAgent, DivergenceAgent,
)
from core.consciousness.agents.omega import (
    LiquidationVacuumAgent, TimeWarpAgent, HarmonicResonanceAgent,
    ReflexivityAgent, BlackSwanAgent,
)
from core.consciousness.agents.predator import (
    IcebergHunterAgent, StopHunterAgent, InstitutionalFootprintAgent,
    LiquiditySiphonAgent, OrderBookPressureAgent,
)
from core.consciousness.agents.chaos import (
    InformationEntropyAgent, PhaseSpaceAttractorAgent, VPINProxyAgent,
    OrderBookEvaporationAgent, CrossScaleConvergenceAgent,
)
from core.consciousness.agents.global_macro import (
    SentimentFearGreedAgent, OnChainPressureAgent, MacroBiasAgent,
    WhaleTrackerAgent,
)
from core.consciousness.agents.physics import (
    NavierStokesFluidAgent, MagneticPolarizationAgent,
    ThermalEquilibriumAgent, QuantumTunnelingAgent,
    DopplerShiftAgent,
)
from core.consciousness.agents.behavioral import (
    RetailPsychologyAgent, GameTheoryNashAgent,
    CppAcceleratedFractalAgent, CppTickEntropyAgent,
    CppCrossScaleAgent,
)
from core.consciousness.agents.smc import (
    LiquiditySweepAgent, MarketStructureShiftAgent, FairValueGapAgent,
    LiquidityHeatmapAgent, OrderBlockAgent, PremiumDiscountAgent,
    BreakOfStructureAgent,
)

__all__ = [
    "AgentSignal", "BaseAgent",
    # Classic
    "TrendAgent", "MomentumAgent", "VolumeAgent", "VolatilityAgent",
    "MicrostructureAgent", "StatisticalAgent", "FractalAgent",
    "SupportResistanceAgent", "DivergenceAgent",
    # Omega
    "LiquidationVacuumAgent", "TimeWarpAgent", "HarmonicResonanceAgent",
    "ReflexivityAgent", "BlackSwanAgent",
    # Predator
    "IcebergHunterAgent", "StopHunterAgent", "InstitutionalFootprintAgent",
    "LiquiditySiphonAgent", "OrderBookPressureAgent",
    # Chaos
    "InformationEntropyAgent", "PhaseSpaceAttractorAgent", "VPINProxyAgent",
    "OrderBookEvaporationAgent", "CrossScaleConvergenceAgent",
    # Global Macro
    "SentimentFearGreedAgent", "OnChainPressureAgent", "MacroBiasAgent",
    "WhaleTrackerAgent",
    # Physics & Kinematics
    "NavierStokesFluidAgent", "MagneticPolarizationAgent",
    "ThermalEquilibriumAgent", "QuantumTunnelingAgent",
    "DopplerShiftAgent",
    # Behavioral & Game Theory + C++ Accelerated
    "RetailPsychologyAgent", "GameTheoryNashAgent",
    "CppAcceleratedFractalAgent", "CppTickEntropyAgent",
    "CppCrossScaleAgent",
    # SMC / ICT
    "LiquiditySweepAgent", "MarketStructureShiftAgent", "FairValueGapAgent",
    "LiquidityHeatmapAgent", "OrderBlockAgent", "PremiumDiscountAgent",
    "BreakOfStructureAgent",
]
