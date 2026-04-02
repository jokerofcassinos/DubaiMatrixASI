"""
[Ω-SOLÉNN] ADAPTADORES SINÁPTICOS ELITE (elite_synapse_adapters.py)
═══════════════════════════════════════════════════════════════════
Ponte neuro-cognitiva entre os 14 Agentes Elite (core/agents/elite)
e o Protocolo BaseSynapse do SwarmOrchestrator (core/intelligence).

Cada adaptador:
1. Herda de BaseSynapse (contrato: process() -> {signal,confidence,phi})
2. Encapsula um agente elite específico
3. Alimenta o agente com dados extraídos do MarketData snapshot
4. Traduz o resultado proprietário para o formato {signal, confidence, phi}
5. Mantém buffer de preços interno para agentes que exigem arrays históricas

MAPEAMENTO VERIFICADO contra as dataclasses REAIS de cada agente:
  - FluidDynamicsVector: pressure_gradient, reynolds_number, kinetic_sweep_energy
  - ChaosThermoVector: max_lyapunov_exponent, helmholtz_free_energy, stochastic_resonance_ratio
  - FeynmanWave: path_of_least_resistance, tunnel_probability, constructive_interference
  - KolmogorovSignal: predicted_direction, entropy, compressibility_ratio
  - SwanSignal: crisis_intensity, ruin_probability, convexity_direction
  - LiquidatorPulse: vacuum_side, liquidation_proximity, max_pain_price
  - HunterVector: predator_bias, is_spoofed, dark_pool_shadow
  - SMCVector: structural_bias, fvg_gravitational_pull, is_mitigated
  - TensorGraphVector: spectral_gap, clustering_density, tensor_braiding_index
  - NexusHyperdimVector: macro_contagion_force, nexus_gravity_pull, structural_premium_skew
  - HolographicVector: lensing_directional_pull, ghost_inference_match, synaptic_spike_potential
  - OmniscienceVoidVector: void_pull_force, meta_swarm_consensus, supernova_capacitor_charge
  - RicciMetrics: scalar_curvature, betti_score, gauge_anomaly
  - GameTheoryVector: optimal_reaction, retail_pain_index, nash_equilibrium_drift

"A serenidade de quem já sabe o resultado antes da execução."
"""

import asyncio
import logging
import time
import numpy as np
from collections import deque
from typing import Any, Dict, Optional

from core.intelligence.base_synapse import BaseSynapse

# ═══════════════════════════════════════════════════════════════
# BUFFER COMPARTILHADO DE PREÇOS (Rolling Window para Agentes)
# ═══════════════════════════════════════════════════════════════

class SharedTickBuffer:
    """Buffer circular de preços/volumes para alimentar agentes que
    precisam de arrays históricas (Feynman, Chaos, Kolmogorov, etc.)."""
    
    def __init__(self, maxlen: int = 200):
        self.prices = deque(maxlen=maxlen)
        self.volumes = deque(maxlen=maxlen)
        self.returns = deque(maxlen=maxlen)
        self._last_price = None

    def push(self, price: float, volume: float):
        if self._last_price is not None and self._last_price > 0:
            ret = (price - self._last_price) / self._last_price
            self.returns.append(ret)
        self.prices.append(price)
        self.volumes.append(volume)
        self._last_price = price

    @property
    def prices_array(self) -> np.ndarray:
        return np.array(self.prices, dtype=np.float32) if self.prices else np.zeros(1, dtype=np.float32)

    @property
    def returns_array(self) -> np.ndarray:
        return np.array(self.returns, dtype=np.float32) if self.returns else np.zeros(1, dtype=np.float32)
    
    @property
    def volumes_array(self) -> np.ndarray:
        return np.array(self.volumes, dtype=np.float32) if self.volumes else np.zeros(1, dtype=np.float32)


# Instância singleton para todos os adaptadores
_SHARED_BUFFER = SharedTickBuffer(maxlen=200)


def _clamp(val: float, lo: float = -1.0, hi: float = 1.0) -> float:
    """Clamp escalar para range seguro."""
    if isinstance(val, np.ndarray):
        val = float(val.flat[0]) if val.size > 0 else 0.0
    return max(lo, min(hi, float(val)))


def _safe_float(val: Any) -> float:
    """Converte qualquer valor para float de forma segura.
    Handles: int, float, bool, np.float64, np.int64, np.bool_, np.ndarray."""
    if val is None:
        return 0.0
    # Python bool first (subclass of int)
    if isinstance(val, bool):
        return 1.0 if val else 0.0
    if isinstance(val, (int, float)):
        return float(val)
    # NumPy scalar types
    if isinstance(val, np.bool_):
        return 1.0 if val else 0.0
    if isinstance(val, (np.floating, np.integer)):
        return float(val)
    # NumPy array
    if isinstance(val, np.ndarray):
        if val.size == 1:
            return float(val.item())
        if val.size > 1:
            return float(np.mean(val))
        return 0.0
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


# ═══════════════════════════════════════════════════════════════
# 1. RICCI — Geometria Diferencial Riemanniana & TDA
#    Dataclass: RicciMetrics {scalar_curvature, betti_score, gauge_anomaly}
# ═══════════════════════════════════════════════════════════════

class RicciSynapse(BaseSynapse):
    """Adaptador para SolennRicci (curvatura de manifold + persistent homology)."""
    
    def __init__(self):
        super().__init__("Ricci_Ω")
        from core.agents.elite.solenn_ricci import SolennRicci
        self.agent = SolennRicci()

    async def process(self, snapshot: Any, nexus_context: Any = None) -> Dict[str, Any]:
        _SHARED_BUFFER.push(snapshot.close, snapshot.volume)
        metrics = await self.agent.compute_manifold_state(snapshot.close, snapshot.volume)
        
        # Curvatura positiva = convergência (bullish), negativa = divergência (bearish)
        signal = _clamp(_safe_float(metrics.scalar_curvature) * 0.1)
        # Betti score alto + sem anomalia = confiança alta
        conf_factor = 0.9 if not metrics.gauge_anomaly else 0.3
        confidence = _clamp(_safe_float(metrics.betti_score) * conf_factor, 0.0, 1.0)
        phi = _clamp(_safe_float(metrics.scalar_curvature) * _safe_float(metrics.betti_score) * 0.05)
        
        return {"signal": signal, "confidence": confidence, "phi": phi}


# ═══════════════════════════════════════════════════════════════
# 2. GAME THEORY — Nash Equilibrium & Mean Field Games
#    Dataclass: GameTheoryVector {nash_equilibrium_drift, retail_pain_index,
#               is_pooling_equilibrium, optimal_reaction}
# ═══════════════════════════════════════════════════════════════

class GameTheorySynapse(BaseSynapse):
    """Adaptador para SolennGameTheory (equilíbrio de Nash + Theory of Mind)."""
    
    def __init__(self):
        super().__init__("GameTheory_Ω")
        from core.agents.elite.solenn_game_theory import SolennGameTheory
        self.agent = SolennGameTheory()

    async def process(self, snapshot: Any, nexus_context: Any = None) -> Dict[str, Any]:
        _SHARED_BUFFER.push(snapshot.close, snapshot.volume)
        pain = np.array([abs(snapshot.spread) * 100, abs(snapshot.book_imbalance)], dtype=np.float32)
        result = await self.agent.compute_nash_equilibrium(pain)
        
        # optimal_reaction: 1=Follow Smart, -1=Fade Retail, 0=Wait
        signal = _clamp(_safe_float(result.optimal_reaction) * 0.5)
        confidence = _clamp(0.5 + _safe_float(result.retail_pain_index) * 0.3, 0.0, 1.0)
        phi = _clamp(_safe_float(result.nash_equilibrium_drift))
        
        return {"signal": signal, "confidence": confidence, "phi": phi}


# ═══════════════════════════════════════════════════════════════
# 3. FLUID DYNAMICS — Navier-Stokes Order Flow
#    Dataclass: FluidDynamicsVector {reynolds_number, strouhal_frequency,
#               pressure_gradient, is_turbulent, kinetic_sweep_energy}
# ═══════════════════════════════════════════════════════════════

class FluidDynamicsSynapse(BaseSynapse):
    """Adaptador para SolennFluidDynamics (Navier-Stokes de order flow)."""
    
    def __init__(self):
        super().__init__("FluidDynamics_Ω")
        from core.agents.elite.solenn_fluid_dynamics import SolennFluidDynamics
        self.agent = SolennFluidDynamics()

    async def process(self, snapshot: Any, nexus_context: Any = None) -> Dict[str, Any]:
        _SHARED_BUFFER.push(snapshot.close, snapshot.volume)
        density = _SHARED_BUFFER.volumes_array[-10:] if len(_SHARED_BUFFER.volumes) >= 10 else np.ones(10, dtype=np.float32)
        velocity = _safe_float(_SHARED_BUFFER.returns_array[-1]) * 10000 if len(_SHARED_BUFFER.returns) > 0 else 0.0
        
        result = await self.agent.extract_fluid_tensors(density, velocity)
        
        # pressure_gradient: positivo = pressão bullish, negativo = bearish
        signal = _clamp(_safe_float(result.pressure_gradient) * 0.3)
        # reynolds_number alto = turbulento = menor confiança
        reynolds = _safe_float(result.reynolds_number)
        confidence = _clamp(max(0.1, 1.0 - reynolds * 0.01), 0.0, 1.0)
        phi = _clamp(_safe_float(result.kinetic_sweep_energy) * 0.1)
        
        return {"signal": signal, "confidence": confidence, "phi": phi}


# ═══════════════════════════════════════════════════════════════
# 4. CHAOS THERMODYNAMICS — Lyapunov & Free Energy
#    Dataclass: ChaosThermoVector {helmholtz_free_energy, max_lyapunov_exponent,
#               is_chaotic, stochastic_resonance_ratio}
# ═══════════════════════════════════════════════════════════════

class ChaosThermodynamicsSynapse(BaseSynapse):
    """Adaptador para SolennChaosThermodynamics (Lyapunov exponents + Helmholtz)."""
    
    def __init__(self):
        super().__init__("ChaosThermo_Ω")
        from core.agents.elite.solenn_chaos_thermodynamics import SolennChaosThermodynamics
        self.agent = SolennChaosThermodynamics()

    async def process(self, snapshot: Any, nexus_context: Any = None) -> Dict[str, Any]:
        _SHARED_BUFFER.push(snapshot.close, snapshot.volume)
        returns = _SHARED_BUFFER.returns_array
        if len(returns) < 5:
            return {"signal": 0.0, "confidence": 0.1, "phi": 0.0}
        
        result = await self.agent.compute_lyapunov_thermodynamics(returns[-120:], snapshot.vol_gk)
        
        # max_lyapunov_exponent negativo = sistema estável = previsível = confiança alta
        lyap = _safe_float(result.max_lyapunov_exponent)
        signal = _clamp(-lyap * 0.5)
        confidence = _clamp(0.5 + abs(_safe_float(result.helmholtz_free_energy)) * 0.1, 0.0, 1.0)
        phi = _clamp(_safe_float(result.stochastic_resonance_ratio) * 0.1)
        
        return {"signal": signal, "confidence": confidence, "phi": phi}


# ═══════════════════════════════════════════════════════════════
# 5. FEYNMAN — Path Integrals & Quantum Paths
#    Dataclass: FeynmanWave {tunnel_probability, path_of_least_resistance,
#               constructive_interference}
# ═══════════════════════════════════════════════════════════════

class FeynmanSynapse(BaseSynapse):
    """Adaptador para SolennFeynman (integrais de caminho financeiras)."""
    
    def __init__(self):
        super().__init__("Feynman_Ω")
        from core.agents.elite.solenn_feynman import SolennFeynman
        self.agent = SolennFeynman()

    async def process(self, snapshot: Any, nexus_context: Any = None) -> Dict[str, Any]:
        _SHARED_BUFFER.push(snapshot.close, snapshot.volume)
        prices = _SHARED_BUFFER.prices_array
        if len(prices) < 10:
            return {"signal": 0.0, "confidence": 0.1, "phi": 0.0}
        
        resistance = float(np.max(prices[-50:])) if len(prices) >= 50 else float(np.max(prices))
        result = await self.agent.compute_quantum_paths(prices[-50:], resistance)
        
        # path_of_least_resistance: 1=Up, -1=Down
        signal = _clamp(_safe_float(result.path_of_least_resistance) * 0.4)
        confidence = _clamp(_safe_float(result.tunnel_probability), 0.0, 1.0)
        # constructive_interference: bool -> phi boost quando True
        phi = _clamp(0.3 if result.constructive_interference else -0.1)
        
        return {"signal": signal, "confidence": confidence, "phi": phi}


# ═══════════════════════════════════════════════════════════════
# 6. KOLMOGOROV — Entropy & Complexity
#    Dataclass: KolmogorovSignal {compressibility_ratio, entropy,
#               is_entropy_dead, predicted_direction}
# ═══════════════════════════════════════════════════════════════

class KolmogorovSynapse(BaseSynapse):
    """Adaptador para SolennKolmogorov (complexidade Lempel-Ziv + entropia)."""
    
    def __init__(self):
        super().__init__("Kolmogorov_Ω")
        from core.agents.elite.solenn_kolmogorov import SolennKolmogorov
        self.agent = SolennKolmogorov()

    async def process(self, snapshot: Any, nexus_context: Any = None) -> Dict[str, Any]:
        _SHARED_BUFFER.push(snapshot.close, snapshot.volume)
        returns = _SHARED_BUFFER.returns_array
        if len(returns) < 5:
            return {"signal": 0.0, "confidence": 0.1, "phi": 0.0}
        
        sequence = (returns[-100:] > 0).astype(np.float32) if len(returns) >= 100 else (returns > 0).astype(np.float32)
        result = await self.agent.calculate_entropic_state(sequence)
        
        # predicted_direction: 1=Up, -1=Down
        signal = _clamp(_safe_float(result.predicted_direction) * 0.5)
        # Entropia baixa = previsível = confiança alta
        entropy = _safe_float(result.entropy)
        confidence = _clamp(max(0.1, 1.0 - entropy), 0.0, 1.0)
        phi = _clamp(_safe_float(result.compressibility_ratio) * 0.2)
        
        return {"signal": signal, "confidence": confidence, "phi": phi}


# ═══════════════════════════════════════════════════════════════
# 7. BLACK SWAN — Tail Risk & Ruin Defense
#    Dataclass: SwanSignal {trigger_active, ruin_probability,
#               convexity_direction, crisis_intensity}
# ═══════════════════════════════════════════════════════════════

class BlackSwanSynapse(BaseSynapse):
    """Adaptador para SolennBlackSwan (proteção de cisne negro + convexidade)."""
    
    def __init__(self):
        super().__init__("BlackSwan_Ω")
        from core.agents.elite.solenn_black_swan import SolennBlackSwan
        self.agent = SolennBlackSwan()

    async def process(self, snapshot: Any, nexus_context: Any = None) -> Dict[str, Any]:
        _SHARED_BUFFER.push(snapshot.close, snapshot.volume)
        result = await self.agent.check_ruin_defenses(snapshot)
        
        # crisis_intensity alto = signal negativo (reduzir exposição)
        signal = _clamp(-_safe_float(result.crisis_intensity) * 0.8)
        # ruin_probability baixa = confiança alta (invertida)
        confidence = _clamp(max(0.1, 1.0 - _safe_float(result.ruin_probability)), 0.0, 1.0)
        # convexity_direction: direcional da convexidade
        phi = _clamp(_safe_float(result.convexity_direction) * 0.3)
        
        return {"signal": signal, "confidence": confidence, "phi": phi}


# ═══════════════════════════════════════════════════════════════
# 8. LIQUIDATOR — Liquidation Cascade Detection
#    Dataclass: LiquidatorPulse {leech_activated, vacuum_side,
#               liquidation_proximity, max_pain_price}
# ═══════════════════════════════════════════════════════════════

class LiquidatorSynapse(BaseSynapse):
    """Adaptador para SolennLiquidator (detecção de cascata de liquidação)."""
    
    def __init__(self):
        super().__init__("Liquidator_Ω")
        from core.agents.elite.solenn_liquidator import SolennLiquidator
        self.agent = SolennLiquidator()

    async def process(self, snapshot: Any, nexus_context: Any = None) -> Dict[str, Any]:
        _SHARED_BUFFER.push(snapshot.close, snapshot.volume)
        result = await self.agent.scan_phantom_vacuum(snapshot)
        
        # vacuum_side: 1 = Buy Vacuum, -1 = Sell Vacuum 
        signal = _clamp(_safe_float(result.vacuum_side) * 0.4)
        # liquidation_proximity: quão perto de cascata (0-1)
        confidence = _clamp(_safe_float(result.liquidation_proximity), 0.0, 1.0)
        # max_pain_price normalizado pelo preço atual
        pain_distance = abs(snapshot.close - _safe_float(result.max_pain_price)) / max(snapshot.close, 1.0)
        phi = _clamp(pain_distance * 0.1)
        
        return {"signal": signal, "confidence": confidence, "phi": phi}


# ═══════════════════════════════════════════════════════════════
# 9. SPOOF HUNTER — Spoofing & Dark Pool Detection
#    Dataclass: HunterVector {is_spoofed, dark_pool_shadow, predator_bias}
# ═══════════════════════════════════════════════════════════════

class SpoofHunterSynapse(BaseSynapse):
    """Adaptador para SolennSpoofHunter (contra-inteligência algorítmica Ω-18)."""
    
    def __init__(self):
        super().__init__("SpoofHunter_Ω")
        from core.agents.elite.solenn_spoof_hunter import SolennSpoofHunter
        self.agent = SolennSpoofHunter()

    async def process(self, snapshot: Any, nexus_context: Any = None) -> Dict[str, Any]:
        _SHARED_BUFFER.push(snapshot.close, snapshot.volume)
        dom = np.array([snapshot.close, snapshot.volume, snapshot.spread, snapshot.book_imbalance], dtype=np.float32).reshape(1, -1)
        trades = _SHARED_BUFFER.prices_array[-20:].reshape(-1, 1) if len(_SHARED_BUFFER.prices) >= 20 else np.zeros((1, 1), dtype=np.float32)
        
        result = await self.agent.scan_dark_pools_and_spoof(dom, trades)
        
        # predator_bias: 1=Injeção Compra, -1=Injeção Venda (invertido se spoofed)
        spoof_multiplier = -1.0 if result.is_spoofed else 1.0
        signal = _clamp(_safe_float(result.predator_bias) * 0.5 * spoof_multiplier)
        # is_spoofed: se True, confiança no sinal contrário é alta
        confidence = _clamp(0.7 if result.is_spoofed else 0.3, 0.0, 1.0)
        phi = _clamp(_safe_float(result.dark_pool_shadow) * 0.2)
        
        return {"signal": signal, "confidence": confidence, "phi": phi}


# ═══════════════════════════════════════════════════════════════
# 10. INSTITUTIONAL STRUCTURE — Smart Money Concepts
#     Dataclass: SMCVector {is_mitigated, structural_bias,
#                fvg_gravitational_pull}
# ═══════════════════════════════════════════════════════════════

class InstitutionalSynapse(BaseSynapse):
    """Adaptador para SolennInstitutionalStructure (SMC, order blocks, FVG)."""
    
    def __init__(self):
        super().__init__("Institutional_Ω")
        from core.agents.elite.solenn_institutional_structure import SolennInstitutionalStructure
        self.agent = SolennInstitutionalStructure()

    async def process(self, snapshot: Any, nexus_context: Any = None) -> Dict[str, Any]:
        _SHARED_BUFFER.push(snapshot.close, snapshot.volume)
        result = await self.agent.compute_structural_bias(snapshot.close, snapshot.volume)
        
        # structural_bias: 1=Bullish, -1=Bearish
        signal = _clamp(_safe_float(result.structural_bias) * 0.5)
        # fvg_gravitational_pull como proxy de confiança (FVG forte = confiança)
        confidence = _clamp(abs(_safe_float(result.fvg_gravitational_pull)), 0.0, 1.0)
        # is_mitigated: se True, order block já mitigado = phi neutro
        phi = _clamp(_safe_float(result.fvg_gravitational_pull) * (0.1 if not result.is_mitigated else 0.02))
        
        return {"signal": signal, "confidence": confidence, "phi": phi}


# ═══════════════════════════════════════════════════════════════
# 11. TENSOR GRAPH — Graph Neural Network Topology
#     Dataclass: TensorGraphVector {clustering_density, percolation_threshold_dist,
#                spectral_gap, lie_symmetry_violation, tensor_braiding_index}
# ═══════════════════════════════════════════════════════════════

class TensorGraphSynapse(BaseSynapse):
    """Adaptador para SolennTensorGraph (GNN + rede de correlação Ω-24)."""
    
    def __init__(self):
        super().__init__("TensorGraph_Ω")
        from core.agents.elite.solenn_tensor_graph import SolennTensorGraph
        self.agent = SolennTensorGraph()

    async def process(self, snapshot: Any, nexus_context: Any = None) -> Dict[str, Any]:
        _SHARED_BUFFER.push(snapshot.close, snapshot.volume)
        nodes = _SHARED_BUFFER.prices_array[-20:] if len(_SHARED_BUFFER.prices) >= 20 else np.ones(20, dtype=np.float32) * snapshot.close
        
        result = await self.agent.compute_tensor_topology(nodes)
        
        # spectral_gap alto = rede estável, baixo = instável
        signal = _clamp(_safe_float(result.spectral_gap) * 0.4)
        # clustering_density como proxy de confiança (alta = mais estrutura)
        confidence = _clamp(_safe_float(result.clustering_density), 0.0, 1.0)
        phi = _clamp(_safe_float(result.tensor_braiding_index) * 0.15)
        
        return {"signal": signal, "confidence": confidence, "phi": phi}


# ═══════════════════════════════════════════════════════════════
# 12. NEXUS HYPERDIM — Cross-Asset Macro Intelligence
#     Dataclass: NexusHyperdimVector {macro_contagion_force, volatility_spillover,
#                hex_matrix_entropy, nexus_gravity_pull, structural_premium_skew}
# ═══════════════════════════════════════════════════════════════

class NexusSynapse(BaseSynapse):
    """Adaptador para SolennNexusHyperdim (inteligência macro multi-ativo Ω-10)."""
    
    def __init__(self):
        super().__init__("NexusHyperdim_Ω")
        from core.agents.elite.solenn_nexus_hyperdim import SolennNexusHyperdim
        self.agent = SolennNexusHyperdim()

    async def process(self, snapshot: Any, nexus_context: Any = None) -> Dict[str, Any]:
        _SHARED_BUFFER.push(snapshot.close, snapshot.volume)
        dxy = 0.0  # DXY neutro em live sem dados macro
        momentum = _safe_float(_SHARED_BUFFER.returns_array[-1]) * 10000 if len(_SHARED_BUFFER.returns) > 0 else 0.0
        
        result = await self.agent.compute_macro_nexus(dxy, momentum)
        
        # macro_contagion_force: direção da força de contágio macro
        signal = _clamp(_safe_float(result.macro_contagion_force) * 0.3)
        # nexus_gravity_pull normalizado como confiança
        confidence = _clamp(abs(_safe_float(result.nexus_gravity_pull)), 0.0, 1.0)
        phi = _clamp(_safe_float(result.structural_premium_skew) * 0.1)
        
        return {"signal": signal, "confidence": confidence, "phi": phi}


# ═══════════════════════════════════════════════════════════════
# 13. HOLOGRAPHIC MEMORY — Temporal Pattern Recall
#     Dataclass: HolographicVector {pheromone_evaporation_rate,
#                ghost_inference_match, geodesic_time_dilation,
#                lensing_directional_pull, synaptic_spike_potential}
# ═══════════════════════════════════════════════════════════════

class HolographicSynapse(BaseSynapse):
    """Adaptador para SolennHolographicMemory (memória holográfica temporal Ω-23)."""
    
    def __init__(self):
        super().__init__("Holographic_Ω")
        from core.agents.elite.solenn_holographic_memory import SolennHolographicMemory
        self.agent = SolennHolographicMemory()

    async def process(self, snapshot: Any, nexus_context: Any = None) -> Dict[str, Any]:
        _SHARED_BUFFER.push(snapshot.close, snapshot.volume)
        returns = _SHARED_BUFFER.returns_array
        if len(returns) < 5:
            return {"signal": 0.0, "confidence": 0.1, "phi": 0.0}
        
        spikes = np.abs(returns[-50:]) if len(returns) >= 50 else np.abs(returns)
        micro_vol = float(np.std(returns[-20:])) if len(returns) >= 20 else 0.01
        
        result = await self.agent.extract_holographic_continuum(spikes, micro_vol)
        
        # lensing_directional_pull: direção da memória gravitacional
        signal = _clamp(_safe_float(result.lensing_directional_pull) * 0.4)
        # ghost_inference_match: grau de match com padrão holográfico
        confidence = _clamp(abs(_safe_float(result.ghost_inference_match)), 0.0, 1.0)
        phi = _clamp(_safe_float(result.synaptic_spike_potential) * 0.15)
        
        return {"signal": signal, "confidence": confidence, "phi": phi}


# ═══════════════════════════════════════════════════════════════
# 14. OMNISCIENCE VOID — Dark Liquidity & Phantom Detection
#     Dataclass: OmniscienceVoidVector {void_pull_force, dark_mass_density,
#                supernova_capacitor_charge, meta_swarm_consensus,
#                omni_apotheosis_trigger}
# ═══════════════════════════════════════════════════════════════

class OmniscienceSynapse(BaseSynapse):
    """Adaptador para SolennOmniscienceVoid (detecção de liquidez fantasma Ω-0)."""
    
    def __init__(self):
        super().__init__("Omniscience_Ω")
        from core.agents.elite.solenn_omniscience_void import SolennOmniscienceVoid
        self.agent = SolennOmniscienceVoid()

    async def process(self, snapshot: Any, nexus_context: Any = None) -> Dict[str, Any]:
        _SHARED_BUFFER.push(snapshot.close, snapshot.volume)
        
        result = await self.agent.compute_omniscience_collapse(
            aggregate_volume=snapshot.volume, 
            phantom_imbalance=snapshot.book_imbalance
        )
        
        # void_pull_force: direção da força gravitacional do vazio
        signal = _clamp(_safe_float(result.void_pull_force) * 0.4)
        # meta_swarm_consensus: consenso meta do enxame 
        confidence = _clamp(abs(_safe_float(result.meta_swarm_consensus)), 0.0, 1.0)
        phi = _clamp(_safe_float(result.supernova_capacitor_charge) * 0.1)
        
        return {"signal": signal, "confidence": confidence, "phi": phi}


# ═══════════════════════════════════════════════════════════════
# FACTORY: Instanciação Atômica de Todos os 14 Adaptadores
# ═══════════════════════════════════════════════════════════════

def create_all_elite_synapses() -> Dict[str, BaseSynapse]:
    """
    [Ω-FACTORY] Cria e retorna todos os 14 adaptadores sinápticos elite.
    Cada agente é instanciado com lazy import para evitar crashes de dependência.
    Agentes que falharem no import são silenciosamente omitidos com log de warning.
    """
    log = logging.getLogger("SOLENN.EliteFactory")
    
    adapter_classes = [
        ("Ricci_Ω", RicciSynapse),
        ("GameTheory_Ω", GameTheorySynapse),
        ("FluidDynamics_Ω", FluidDynamicsSynapse),
        ("ChaosThermo_Ω", ChaosThermodynamicsSynapse),
        ("Feynman_Ω", FeynmanSynapse),
        ("Kolmogorov_Ω", KolmogorovSynapse),
        ("BlackSwan_Ω", BlackSwanSynapse),
        ("Liquidator_Ω", LiquidatorSynapse),
        ("SpoofHunter_Ω", SpoofHunterSynapse),
        ("Institutional_Ω", InstitutionalSynapse),
        ("TensorGraph_Ω", TensorGraphSynapse),
        ("NexusHyperdim_Ω", NexusSynapse),
        ("Holographic_Ω", HolographicSynapse),
        ("Omniscience_Ω", OmniscienceSynapse),
    ]
    
    synapses = {}
    for name, cls in adapter_classes:
        try:
            synapses[name] = cls()
            log.info(f"🧬 Elite Synapse '{name}' acoplada com sucesso.")
        except Exception as e:
            log.warning(f"⚠️ Elite Synapse '{name}' falhou no acoplamento: {e}")
    
    log.info(f"🐝 Total de Sinapses Elite ativas: {len(synapses)}/14")
    return synapses
