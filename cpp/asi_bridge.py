"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — C++ FFI BRIDGE                             ║
║     Interface Python ↔ C++ via ctypes para módulos de alta performance    ║
║                                                                              ║
║  Carrega asi_core.dll e expõe todas as funções C++ como métodos Python    ║
║  com conversão automática numpy ↔ C arrays.                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import ctypes
import ctypes.util
import numpy as np
import os
import sys
from typing import Optional, Tuple

from utils.logger import log
from utils.decorators import catch_and_log

# ═══ STRUCT DEFINITIONS (espelhando asi_core.h) ═══

class TickData(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("bid", ctypes.c_double),
        ("ask", ctypes.c_double),
        ("last", ctypes.c_double),
        ("volume", ctypes.c_double),
        ("time_msc", ctypes.c_int64),
        ("time", ctypes.c_double),
    ]

class OrderFlowResult(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("cumulative_delta", ctypes.c_double),
        ("buy_volume", ctypes.c_double),
        ("sell_volume", ctypes.c_double),
        ("order_imbalance", ctypes.c_double),
        ("tick_velocity", ctypes.c_double),
        ("is_absorption", ctypes.c_int),
        ("is_exhaustion", ctypes.c_int),
        ("volume_climax_score", ctypes.c_double),
    ]

class AgentSignal(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("signal", ctypes.c_double),
        ("confidence", ctypes.c_double),
        ("weight", ctypes.c_double),
    ]

class QuantumState(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("raw_signal", ctypes.c_double),
        ("coherence", ctypes.c_double),
        ("weighted_signal", ctypes.c_double),
        ("energy", ctypes.c_double),
        ("should_collapse", ctypes.c_int),
    ]

class PhaseSpaceResultC(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("orbit_radius", ctypes.c_double),
        ("global_orbit", ctypes.c_double),
        ("compression_ratio", ctypes.c_double),
        ("is_compressed", ctypes.c_int),
    ]

class SwingResultC(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("index", ctypes.c_int),
        ("price", ctypes.c_double),
    ]

class MonteCarloInputC(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("S0", ctypes.c_double),
        ("mu", ctypes.c_double),
        ("sigma", ctypes.c_double),
        ("jump_intensity", ctypes.c_double),
        ("jump_mean", ctypes.c_double),
        ("jump_std", ctypes.c_double),
        ("dt", ctypes.c_double),
        ("n_sims", ctypes.c_int),
        ("n_steps", ctypes.c_int),
        ("stop_loss", ctypes.c_double),
        ("take_profit", ctypes.c_double),
        ("is_buy", ctypes.c_bool),
    ]

class MonteCarloOutputC(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("win_prob", ctypes.c_double),
        ("expected_return", ctypes.c_double),
        ("var_95", ctypes.c_double),
        ("cvar_95",  ctypes.c_double),
        ("simulation_time_ms", ctypes.c_double),
    ]

class AgentRawSignal(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("signal", ctypes.c_double),
        ("confidence", ctypes.c_double),
        ("weight", ctypes.c_double),
        ("is_hybrid", ctypes.c_int),
    ]

class ConvergenceResult(ctypes.Structure):
    _pack_ = 8 # Ensure 64-bit alignment parity with MSVC/GCC
    _fields_ = [
        ("final_signal", ctypes.c_double),
        ("final_confidence", ctypes.c_double),
        ("final_coherence", ctypes.c_double),
        ("entropy", ctypes.c_double),
        ("bull_count", ctypes.c_int32),
        ("bear_count", ctypes.c_int32),
        ("neutral_count", ctypes.c_int32),
        ("padding", ctypes.c_int32), # Explicit padding for 8-byte boundary
        ("computation_time_ms", ctypes.c_double),
    ]

class HyperspaceOutputC(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("confidence_boost", ctypes.c_double),
        ("expected_max_excursion", ctypes.c_double),
        ("probability_density", ctypes.c_double),
        ("hyperspace_time_ms", ctypes.c_double),
    ]

class GraphNodeC(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("price", ctypes.c_double),
        ("liquidity", ctypes.c_double),
        ("centrality", ctypes.c_double),
        ("velocity", ctypes.c_double),
    ]

class GraphResultC(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("clusters", GraphNodeC * 50),
        ("cluster_count", ctypes.c_int),
        ("avalanche_risk", ctypes.c_double),
        ("global_centrality", ctypes.c_double),
    ]

class ThermodynamicResultC(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("shannon_entropy", ctypes.c_double),
        ("temperature", ctypes.c_double),
        ("pressure", ctypes.c_double),
        ("compression_ratio", ctypes.c_double),
        ("is_critical_state", ctypes.c_int),
    ]

class CausalResultC(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("causal_effect", ctypes.c_double),
        ("counterfactual_loss", ctypes.c_double),
        ("do_impact_score", ctypes.c_double),
        ("confidence", ctypes.c_double)
    ]

class TopologyResultC(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("betti_0", ctypes.c_double),
        ("betti_1", ctypes.c_double),
        ("persistence_entropy", ctypes.c_double),
        ("critical_hole_size", ctypes.c_double),
        ("is_geometrically_unstable", ctypes.c_int)
    ]

class TensorResultC(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("entanglement_entropy", ctypes.c_double),
        ("compression_loss", ctypes.c_double),
        ("stability_index", ctypes.c_double),
        ("dominant_mode", ctypes.c_int)
    ]

class FisherResultC(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("fisher_information", ctypes.c_double),
        ("natural_gradient_x", ctypes.c_double),
        ("information_distance", ctypes.c_double),
        ("optimal_step_size", ctypes.c_double)
    ]

# PHASE Ω-ONE: SNN
class SpikeResultC(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("potential", ctypes.c_double),
        ("fired", ctypes.c_int),
        ("last_spike_time", ctypes.c_double),
    ]

# PHASE Ω-ONE: MFG
class MFGResultC(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("optimal_velocity", ctypes.c_double),
        ("crowd_density", ctypes.c_double),
        ("expected_drift", ctypes.c_double),
        ("stability_score", ctypes.c_double),
    ]

# PHASE Ω-EXTREME: Lorentz Clock
class LorentzClockResultC(ctypes.Structure):
    _fields_ = [
        ("internal_time_passed", ctypes.c_double),
        ("dilation_factor", ctypes.c_double),
        ("kinetic_energy", ctypes.c_double),
    ]

# PHASE Ω-ONE: FEYNMAN
class PathIntegralResultC(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("probability_amplitude_real", ctypes.c_double),
        ("probability_amplitude_imag", ctypes.c_double),
        ("stationary_phase_price", ctypes.c_double),
        ("quantum_interference_score", ctypes.c_double),
    ]

# PHASE Ω-ONE: CHAOS
class ChaosResultC(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("lyapunov_exponent", ctypes.c_double),
        ("predictability_limit", ctypes.c_double),
        ("entropy", ctypes.c_double),
        ("is_chaotic", ctypes.c_int),
    ]

# PHASE Ω-CLASS
class HolographicResultC(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("bulk_pressure", ctypes.c_double),
        ("entanglement_entropy", ctypes.c_double),
        ("geodesic_distance", ctypes.c_double),
        ("holographic_coherence", ctypes.c_double),
        ("is_manifold_stable", ctypes.c_int),
    ]


class ConsciousnessResultC(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("phi_value", ctypes.c_double),
        ("coherence_score", ctypes.c_double),
        ("integration_entropy", ctypes.c_double),
    ]

class QCAResultC(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("grid_entropy", ctypes.c_double),
        ("transition_speed", ctypes.c_double),
        ("is_critical", ctypes.c_int),
    ]

class PredatorPreyResultC(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("predator_biomass", ctypes.c_double),
        ("prey_biomass", ctypes.c_double),
        ("extinction_risk", ctypes.c_double),
        ("hunt_efficiency", ctypes.c_double),
    ]

class ExtremeValueResultC(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("threshold_exceedance", ctypes.c_double),
        ("tail_risk", ctypes.c_double),
        ("copula_correlation", ctypes.c_double),
        ("is_black_swan", ctypes.c_int),
    ]

class CppASICore:
    """
    Interface Python para o módulo C++ de alta performance.
    Carrega a DLL compilada e expõe as funções como métodos Python.
    """

    def __init__(self):
        self._lib = None
        self._loaded = False
        self._available = False # Initialize _available
        self._load_library()

    def _load_library(self):
        """Tenta carregar a DLL compilada com busca dinâmica de dependências."""
        dll_name = "asi_core.dll" if sys.platform == "win32" else "libasi_core.so"
        
        # [PHASE Ω-STRICT] Dynamic MSYS2/MinGW DLL Resolution
        import shutil
        env_msys = os.getenv("MSYS2_PATH") or os.getenv("MSYS2_ROOT")
        possible_msys_roots = [env_msys] if env_msys else []
        
        # [Phase 14] Dynamic Inference via GCC
        gcc_path = shutil.which("gcc")
        if gcc_path:
            # If gcc is in C:/msys64/mingw64/bin/gcc.exe, root is C:/msys64
            norm_gcc = gcc_path.replace("\\", "/")
            if "/bin/gcc" in norm_gcc:
                parts = norm_gcc.split("/")
                try:
                    # Find 'msys64' or similar in the path
                    for i, part in enumerate(parts):
                        if "msys" in part.lower():
                            root = "/".join(parts[:i+1])
                            if root not in possible_msys_roots:
                                possible_msys_roots.append(root)
                            break
                except: pass

        # Fallbacks (Ordered by probability)
        for drive in ["C", "D", "E", "F", "G"]:
            root = f"{drive}:/msys64"
            if root not in possible_msys_roots:
                possible_msys_roots.append(root)
        
        for root in possible_msys_roots:
            if not root or not os.path.exists(root):
                continue
            
            # Subdiretórios comuns de binários no MSYS2 (UCRT64 é o padrão moderno)
            for sub in ["ucrt64/bin", "mingw64/bin", "usr/bin", "bin"]:
                mpath = os.path.join(root, sub).replace("\\", "/")
                if os.path.isdir(mpath):
                    try:
                        # [PHASE Ω-SECURITY] Persistent DLL injection for Windows
                        if hasattr(os, "add_dll_directory"):
                            os.add_dll_directory(mpath)
                        
                        # Fallback for older Python or specific environment needs
                        if mpath not in os.environ.get("PATH", ""):
                            os.environ["PATH"] = mpath + os.pathsep + os.environ.get("PATH", "")
                        
                        log.debug(f"💉 MSYS2 path injected: {mpath}")
                    except Exception as e:
                        log.debug(f"Failed to add DLL directory {mpath}: {e}")
        
        # Possíveis locais da DLL (Ordem de preferência: Versões novas -> Coração do projeto)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        search_paths = [
            os.path.join(base_dir, "..", "asi_core_v3.dll"),
            os.path.join(base_dir, "..", dll_name),
            os.path.join(base_dir, dll_name),
            os.path.join(base_dir, "build", dll_name),
            os.path.join(base_dir, "build", "Release", dll_name),
        ]

        for path in search_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                try:
                    self._lib = ctypes.CDLL(abs_path)
                    self._setup_signatures()
                    
                    # Manual override for signatures not in _setup_signatures
                    if hasattr(self._lib, "asi_converge_signals"):
                        self._lib.asi_converge_signals.argtypes = [
                            ctypes.POINTER(AgentRawSignal), ctypes.c_int,
                            ctypes.c_double, ctypes.c_double,
                            ctypes.POINTER(ConvergenceResult)
                        ]
                        self._lib.asi_converge_signals.restype = None
                    
                    self._available = True
                    self._loaded = True
                    log.omega(f"⚡ C++ ASI Core carregado: {abs_path}")
                    return
                except Exception as e:
                    log.warning(f"Falha ao carregar C++ DLL de {abs_path}: {e}")
        
        log.critical("⚠️ C++ ASI Core (asi_core.dll) NÃO ENCONTRADO!")
        log.info("Certifique-se que o módulo foi compilado e está na raiz ou na pasta /cpp")

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def _setup_signatures(self):
        """Configura as assinaturas de tipos das funções C."""
        lib = self._lib
        
        # EMA
        lib.asi_ema.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_double)]
        lib.asi_ema.restype = None
        
        # RSI
        lib.asi_rsi.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_double)]
        lib.asi_rsi.restype = None
        
        # ATR
        lib.asi_atr.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_double)]
        lib.asi_atr.restype = None

        # Bollinger
        lib.asi_bollinger.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int, ctypes.c_double,
                                      ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]
        lib.asi_bollinger.restype = None

        # MACD
        lib.asi_macd.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                  ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]
        lib.asi_macd.restype = None

        # VWAP
        lib.asi_vwap.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_int]
        lib.asi_vwap.restype = ctypes.c_double
        
        # Shannon Entropy
        lib.asi_shannon_entropy.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int]
        lib.asi_shannon_entropy.restype = ctypes.c_double
        
        # Hurst
        lib.asi_hurst_exponent.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
        lib.asi_hurst_exponent.restype = ctypes.c_double
        
        # Z-Score
        lib.asi_zscore.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_double)]
        lib.asi_zscore.restype = None

        # OrderFlow
        lib.asi_process_orderflow.argtypes = [ctypes.POINTER(TickData), ctypes.c_int, ctypes.POINTER(OrderFlowResult)]
        lib.asi_process_orderflow.restype = None

        # Signals
        lib.asi_aggregate_signals.argtypes = [ctypes.POINTER(AgentSignal), ctypes.c_int, ctypes.c_double, 
                                              ctypes.c_double, ctypes.c_double, ctypes.POINTER(QuantumState)]
        lib.asi_aggregate_signals.restype = None

        # Kelly
        lib.asi_kelly_criterion.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double]
        lib.asi_kelly_criterion.restype = ctypes.c_double

        # Lot Size
        lib.asi_optimal_lot_size.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double]
        lib.asi_optimal_lot_size.restype = ctypes.c_double

        # Ergodicity (Phase Ω-Class)
        lib.asi_non_ergodic_growth_rate.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double]
        lib.asi_non_ergodic_growth_rate.restype = ctypes.c_double

        lib.asi_ito_lot_sizing.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double]
        lib.asi_ito_lot_sizing.restype = ctypes.c_double

        # ═══ AGENT CLUSTER ENGINE ═══
        lib.asi_fractal_dimension.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int]
        lib.asi_fractal_dimension.restype = ctypes.c_double

        lib.asi_vpin_proxy.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double),
                                        ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int]
        lib.asi_vpin_proxy.restype = ctypes.c_double

        lib.asi_phase_space.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int,
                                         ctypes.POINTER(PhaseSpaceResultC)]
        lib.asi_phase_space.restype = None

        lib.asi_kurtosis.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
        lib.asi_kurtosis.restype = ctypes.c_double

        lib.asi_cross_scale_correlation.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int,
                                                     ctypes.POINTER(ctypes.c_double), ctypes.c_int]
        lib.asi_cross_scale_correlation.restype = ctypes.c_double

        lib.asi_tick_entropy.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int]
        lib.asi_tick_entropy.restype = ctypes.c_double

        # Latency Optimization (Phase 18)
        lib.asi_find_swings.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), 
                                        ctypes.c_int, ctypes.c_int, 
                                        ctypes.POINTER(SwingResultC), ctypes.POINTER(ctypes.c_int), 
                                        ctypes.POINTER(SwingResultC), ctypes.POINTER(ctypes.c_int)]
        lib.asi_find_swings.restype = ctypes.c_int

        lib.asi_navier_stokes_pressure.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), 
                                                ctypes.c_int, ctypes.POINTER(ctypes.c_double), 
                                                ctypes.POINTER(ctypes.c_double)]
        lib.asi_navier_stokes_pressure.restype = None

        lib.asi_calc_micro_variance.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
        lib.asi_calc_micro_variance.restype = ctypes.c_double

        lib.asi_monte_carlo_merton.argtypes = [ctypes.POINTER(MonteCarloInputC), ctypes.POINTER(MonteCarloOutputC)]
        lib.asi_monte_carlo_merton.restype = None

        lib.asi_simulate_4096_hyperspace.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_double, ctypes.POINTER(HyperspaceOutputC)]
        lib.asi_simulate_4096_hyperspace.restype = None

        # [Ω-FIX] Lorentz Clock (Phase Ω-Extreme)
        lib.asi_lorentz_clock_update.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.POINTER(LorentzClockResultC)]
        lib.asi_lorentz_clock_update.restype = None

        # Phase Ω-Next: LGNN & Thermodynamics
        lib.asi_calculate_lgnn.argtypes = [
            ctypes.POINTER(TickData), ctypes.c_int,
            ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double),
            ctypes.c_int, ctypes.POINTER(GraphResultC)
        ]
        lib.asi_calculate_lgnn.restype = None

        lib.asi_calculate_thermodynamics.argtypes = [
            ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double),
            ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double),
            ctypes.c_int, ctypes.POINTER(ThermodynamicResultC)
        ]
        lib.asi_calculate_thermodynamics.restype = None

        lib.asi_vector_search.argtypes = [
            ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double),
            ctypes.c_int, ctypes.c_int,
            ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_int),
            ctypes.c_int
        ]
        lib.asi_vector_search.restype = ctypes.c_int

        lib.asi_calculate_causal_impact.argtypes = [
            ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int,
            ctypes.c_double, ctypes.c_int,
            ctypes.POINTER(CausalResultC)
        ]
        lib.asi_calculate_causal_impact.restype = None

        lib.asi_calculate_topology.argtypes = [
            ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double),
            ctypes.c_int, ctypes.POINTER(TopologyResultC)
        ]
        lib.asi_calculate_topology.restype = None

        lib.asi_calculate_tensor_swarm.argtypes = [
            ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double),
            ctypes.c_int, ctypes.c_int, ctypes.POINTER(TensorResultC)
        ]
        lib.asi_calculate_tensor_swarm.restype = None

        lib.asi_map_poincare_dist.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double]
        lib.asi_map_poincare_dist.restype = ctypes.c_double

        # PHASE Ω-CLASS: Reservoir
        lib.asi_init_reservoir.argtypes = [ctypes.c_int, ctypes.c_double, ctypes.c_double]
        lib.asi_init_reservoir.restype = None
        lib.asi_perturb_reservoir.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
        lib.asi_perturb_reservoir.restype = None
        lib.asi_read_reservoir_output.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
        lib.asi_read_reservoir_output.restype = None

        lib.asi_infer_holographic_pressure.argtypes = [
            ctypes.POINTER(ctypes.c_double), ctypes.c_int,
            ctypes.POINTER(ctypes.c_double), ctypes.c_int,
            ctypes.POINTER(HolographicResultC)
        ]
        lib.asi_infer_holographic_pressure.restype = None

        lib.asi_deposit_pheromone.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double]
        lib.asi_deposit_pheromone.restype = None

        lib.asi_sense_pheromone.argtypes = [ctypes.c_double]
        lib.asi_sense_pheromone.restype = ctypes.c_double

        lib.asi_update_pheromone_field.argtypes = [ctypes.c_double]
        lib.asi_update_pheromone_field.restype = None

        lib.asi_calculate_fisher_metric.argtypes = [
            ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), 
            ctypes.c_int, ctypes.POINTER(FisherResultC)
        ]
        lib.asi_calculate_fisher_metric.restype = None

        # PHASE Ω-ONE: SNN
        lib.asi_update_lif_neuron.argtypes = [
            ctypes.c_double, ctypes.c_double, ctypes.c_double,
            ctypes.c_double, ctypes.c_double, ctypes.c_double,
            ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_int)
        ]
        lib.asi_update_lif_neuron.restype = None

        # PHASE Ω-ONE: MFG
        lib.asi_solve_mfg.argtypes = [
            ctypes.POINTER(ctypes.c_double), ctypes.c_int,
            ctypes.c_double, ctypes.c_double,
            ctypes.c_double, ctypes.c_double,
            ctypes.POINTER(ctypes.c_double), ctypes.POINTER(MFGResultC)
        ]
        lib.asi_solve_mfg.restype = None

        # PHASE Ω-ONE: FEYNMAN
        lib.asi_calculate_feynman_path.argtypes = [
            ctypes.POINTER(ctypes.c_double), ctypes.c_int,
            ctypes.c_double, ctypes.c_double,
            ctypes.c_double, ctypes.POINTER(PathIntegralResultC)
        ]
        lib.asi_calculate_feynman_path.restype = None

        # PHASE Ω-ONE: CHAOS
        lib.asi_calculate_chaos.argtypes = [
            ctypes.POINTER(ctypes.c_double), ctypes.c_int,
            ctypes.c_double, ctypes.POINTER(ChaosResultC)
        ]
        lib.asi_calculate_chaos.restype = None

        # PHASE Ω-EXTREME (Lorentz is already defined above)

        lib.asi_calculate_phi.argtypes = [ctypes.POINTER(AgentSignal), ctypes.c_int, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ConsciousnessResultC)]
        lib.asi_calculate_phi.restype = None

        lib.asi_process_qca_grid.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_double, ctypes.POINTER(QCAResultC)]
        lib.asi_process_qca_grid.restype = None

        lib.asi_solve_lotka_volterra.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, 
                                                 ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(PredatorPreyResultC)]
        lib.asi_solve_lotka_volterra.restype = None

        lib.asi_harvest_black_swan.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_double, ctypes.POINTER(ExtremeValueResultC)]
        lib.asi_harvest_black_swan.restype = None

        # ═══ PHD OMEGA MATH (Phase 69) ═══
        lib.calculate_laser_compression.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
        lib.calculate_laser_compression.restype = ctypes.c_double

        lib.calculate_navier_stokes_reynolds.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_int]
        lib.calculate_navier_stokes_reynolds.restype = ctypes.c_double

        lib.calculate_dark_matter_gravity.argtypes = [ctypes.c_double, ctypes.c_double]
        lib.calculate_dark_matter_gravity.restype = ctypes.c_double

        lib.calculate_aethel_viscosity.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
        lib.calculate_aethel_viscosity.restype = ctypes.c_double

        lib.detect_soliton_wave.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
        lib.detect_soliton_wave.restype = ctypes.c_double

        # ═══ TRANSCENDENCE ENGINES (QED & NLSE) ═══
        lib.calculate_casimir_force.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_double]
        lib.calculate_casimir_force.restype = ctypes.c_double

        lib.solve_nlse_rogue_wave.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_double]
        lib.solve_nlse_rogue_wave.restype = ctypes.c_double

        # ═══ QUANTUM GRAVITY (Phase Ω-Apocalypse) ═══
        lib.calculate_eigenvector_centrality.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_double, ctypes.POINTER(ctypes.c_double)]
        lib.calculate_eigenvector_centrality.restype = None

        # ═══ NON-LINEAR DYNAMICS (Phase Ω-Eternity) ═══
        lib.calculate_rg_scaling_invariance.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.POINTER(ctypes.c_double), ctypes.c_int]
        lib.calculate_rg_scaling_invariance.restype = ctypes.c_double

        lib.estimate_attractor_folding.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_double]
        lib.estimate_attractor_folding.restype = ctypes.c_double

        # ═══ TOPOLOGICAL BRAIDING (Phase Ω-Continuum) ═══
        lib.calculate_braid_index.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int]
        lib.calculate_braid_index.restype = ctypes.c_double

        lib.calculate_kaldor_hicks_ratio.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double]
        lib.calculate_kaldor_hicks_ratio.restype = ctypes.c_double

        # ═══ GEOMETRIC SPECTRAL ANALYSIS (Phase Ω-Genesis) ═══
        lib.calculate_spectral_flux.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
        lib.calculate_spectral_flux.restype = ctypes.c_double

        lib.calculate_berry_curvature.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int]
        lib.calculate_berry_curvature.restype = ctypes.c_double

        # ═══ QUANTUM FIELD THEORY (Phase Ω-Aethel) ═══
        lib.calculate_fermi_pressure.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_double]
        lib.calculate_fermi_pressure.restype = ctypes.c_double

        lib.calculate_chern_simons_index.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_int]
        lib.calculate_chern_simons_index.restype = ctypes.c_double

        # ═══ INFORMATION CAUSALITY (Phase Ω-Genesis) ═══
        lib.calculate_transfer_entropy.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int]
        lib.calculate_transfer_entropy.restype = ctypes.c_double

        lib.calculate_kramers_kronig_anomaly.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
        lib.calculate_kramers_kronig_anomaly.restype = ctypes.c_double

        lib.calculate_byzantine_penalties.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.POINTER(ctypes.c_double)]
        lib.calculate_byzantine_penalties.restype = None

    # ═══ HELPER: numpy array → C pointer ═══
    @staticmethod
    def _ptr(arr: np.ndarray):
        """Converte numpy array para ponteiro ctypes."""
        return arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double))

    @staticmethod
    def _ensure_f64(arr) -> np.ndarray:
        """Garante que o array é float64 contíguo."""
        return np.ascontiguousarray(arr, dtype=np.float64)

    # ═══════════════════════════════════════════════════════════
    #  INDICADORES
    # ═══════════════════════════════════════════════════════════

    def ema(self, close: np.ndarray, period: int) -> np.ndarray:
        if not self._lib or close is None or len(close) == 0:
            return np.zeros_like(close) if close is not None else np.array([])
        
        close = self._ensure_f64(close)
        # [PHASE Ω-STRICT] Input Validation Guard
        if np.any(np.isnan(close)) or np.any(np.isinf(close)):
            log.warning("⚠️ [FFI] NaN/Inf detected in EMA input. Bailing to avoid C++ crash.")
            return np.zeros_like(close)

        out = np.zeros(len(close), dtype=np.float64)
        self._lib.asi_ema(self._ptr(close), len(close), period, self._ptr(out))
        return out

    def rsi(self, close: np.ndarray, period: int = 14) -> np.ndarray:
        if not self._lib or close is None or len(close) == 0:
            return np.zeros_like(close) if close is not None else np.array([])
            
        close = self._ensure_f64(close)
        if np.any(np.isnan(close)) or np.any(np.isinf(close)):
            log.warning("⚠️ [FFI] NaN/Inf detected in RSI input.")
            return np.zeros_like(close)

        out = np.zeros(len(close), dtype=np.float64)
        self._lib.asi_rsi(self._ptr(close), len(close), period, self._ptr(out))
        return out

    def atr(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        if not self._lib or any(x is None or len(x) == 0 for x in [high, low, close]):
            return np.zeros_like(close) if close is not None else np.array([])
            
        high, low, close = self._ensure_f64(high), self._ensure_f64(low), self._ensure_f64(close)
        
        # [PHASE Ω-STRICT] Input Validation Guard
        for arr, name in zip([high, low, close], ["High", "Low", "Close"]):
            if np.any(np.isnan(arr)) or np.any(np.isinf(arr)):
                log.warning(f"⚠️ [FFI] NaN/Inf detected in ATR {name} input.")
                return np.zeros_like(close)

        out = np.zeros(len(close), dtype=np.float64)
        self._lib.asi_atr(self._ptr(high), self._ptr(low), self._ptr(close), len(close), period, self._ptr(out))
        return out

    def bollinger(self, close: np.ndarray, period: int = 20, num_std: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        if not self._lib or close is None or len(close) == 0: 
            z = np.zeros_like(close) if close is not None else np.array([])
            return z, z, z, z
            
        close = self._ensure_f64(close)
        if np.any(np.isnan(close)) or np.any(np.isinf(close)):
            log.warning("⚠️ [FFI] NaN/Inf detected in Bollinger input.")
            z = np.zeros_like(close)
            return z, z, z, z

        n = len(close)
        upper = np.zeros(n, dtype=np.float64)
        middle = np.zeros(n, dtype=np.float64)
        lower = np.zeros(n, dtype=np.float64)
        width = np.zeros(n, dtype=np.float64)
        self._lib.asi_bollinger(self._ptr(close), n, period, num_std,
                                 self._ptr(upper), self._ptr(middle), self._ptr(lower), self._ptr(width))
        return upper, middle, lower, width

    def macd(self, close: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        if not self._lib or close is None or len(close) == 0:
            z = np.zeros_like(close) if close is not None else np.array([])
            return z, z, z
            
        close = self._ensure_f64(close)
        if np.any(np.isnan(close)) or np.any(np.isinf(close)):
            log.warning("⚠️ [FFI] NaN/Inf detected in MACD input.")
            z = np.zeros_like(close)
            return z, z, z

        n = len(close)
        macd_line = np.zeros(n, dtype=np.float64)
        signal_line = np.zeros(n, dtype=np.float64)
        histogram = np.zeros(n, dtype=np.float64)
        self._lib.asi_macd(self._ptr(close), n, fast, slow, signal,
                            self._ptr(macd_line), self._ptr(signal_line), self._ptr(histogram))
        return macd_line, signal_line, histogram

    def vwap(self, close: np.ndarray, volume: np.ndarray) -> float:
        close, volume = self._ensure_f64(close), self._ensure_f64(volume)
        return self._lib.asi_vwap(self._ptr(close), self._ptr(volume), len(close))

    def shannon_entropy(self, data: np.ndarray, bins: int = 50) -> float:
        data = self._ensure_f64(data)
        return self._lib.asi_shannon_entropy(self._ptr(data), len(data), bins)

    def hurst_exponent(self, data: np.ndarray) -> float:
        data = self._ensure_f64(data)
        return self._lib.asi_hurst_exponent(self._ptr(data), len(data))

    def zscore(self, data: np.ndarray, window: int = 20) -> np.ndarray:
        data = self._ensure_f64(data)
        out = np.zeros(len(data), dtype=np.float64)
        self._lib.asi_zscore(self._ptr(data), len(data), window, self._ptr(out))
        return out

    # ═══════════════════════════════════════════════════════════
    #  ORDER FLOW
    # ═══════════════════════════════════════════════════════════

    def process_orderflow(self, ticks: list) -> dict:
        if not self._lib: return {}
        """Processa lista de dicts de ticks em C++."""
        count = len(ticks)
        if count == 0:
            return {}
        
        tick_array = (TickData * count)()
        for i, t in enumerate(ticks):
            tick_array[i].bid = t.get("bid", 0.0)
            tick_array[i].ask = t.get("ask", 0.0)
            tick_array[i].last = t.get("last", 0.0)
            tick_array[i].volume = t.get("volume", 0.0)
            tick_array[i].time_msc = t.get("time_msc", 0)

        result = OrderFlowResult()
        self._lib.asi_process_orderflow(tick_array, count, ctypes.byref(result))

        return {
            "cumulative_delta": result.cumulative_delta,
            "buy_volume": result.buy_volume,
            "sell_volume": result.sell_volume,
            "order_imbalance": result.order_imbalance,
            "tick_velocity": result.tick_velocity,
            "is_absorption": bool(result.is_absorption),
            "is_exhaustion": bool(result.is_exhaustion),
            "volume_climax_score": result.volume_climax_score,
        }

    # ═══════════════════════════════════════════════════════════
    #  SIGNAL AGGREGATION
    # ═══════════════════════════════════════════════════════════

    def aggregate_signals(self, signals: list, regime_weight: float = 1.0, 
                          signal_threshold: float = 0.3, coherence_threshold: float = 0.6) -> dict:
        if not self._lib: return {}
        """Agrega sinais de agentes neurais em C++."""
        count = len(signals)
        if count == 0:
            return {}

        sig_array = (AgentSignal * count)()
        for i, s in enumerate(signals):
            sig_array[i].signal = s.get("signal", 0.0)
            sig_array[i].confidence = s.get("confidence", 0.0)
            sig_array[i].weight = s.get("weight", 1.0)

        state = QuantumState()
        self._lib.asi_aggregate_signals(sig_array, count, regime_weight, 
                                         signal_threshold, coherence_threshold, 
                                         ctypes.byref(state))

        return {
            "raw_signal": state.raw_signal,
            "coherence": state.coherence,
            "weighted_signal": state.weighted_signal,
            "energy": state.energy,
            "should_collapse": bool(state.should_collapse),
        }

    # ═══════════════════════════════════════════════════════════
    #  RISK UTILITIES
    # ═══════════════════════════════════════════════════════════

    def kelly_criterion(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        if not self._lib: return 0.5
        return self._lib.asi_kelly_criterion(win_rate, avg_win, avg_loss)

    def optimal_lot_size(self, balance: float, risk_pct: float,
                          sl_distance: float, point_value: float) -> float:
        if not self._lib: return 0.01
        return self._lib.asi_optimal_lot_size(balance, risk_pct, sl_distance, point_value)

    def non_ergodic_growth_rate(self, win_rate: float, avg_win_pct: float, avg_loss_pct: float, leverage: float) -> float:
        if not self._lib: return 0.0
        return self._lib.asi_non_ergodic_growth_rate(win_rate, avg_win_pct, avg_loss_pct, leverage)

    def ito_lot_sizing(self, balance: float, win_rate: float, mu: float, sigma: float, dt: float) -> float:
        if not self._lib: return 0.01
        return self._lib.asi_ito_lot_sizing(balance, win_rate, mu, sigma, dt)

    # ═══════════════════════════════════════════════════════════
    #  AGENT CLUSTER ENGINE (C++ Accelerated)
    # ═══════════════════════════════════════════════════════════

    def fractal_dimension(self, data: np.ndarray, max_box: int = 64) -> float:
        if not self._lib or data is None or len(data) == 0:
            return 1.5
        data = self._ensure_f64(data)
        if np.any(np.isnan(data)) or np.any(np.isinf(data)):
             return 1.5
        return self._lib.asi_fractal_dimension(self._ptr(data), len(data), max_box)

    def vpin_proxy(self, open_p: np.ndarray, close: np.ndarray, volume: np.ndarray, lookback: int = 5) -> float:
        if not self._lib or any(x is None or len(x) == 0 for x in [open_p, close, volume]):
            return 0.5
        open_p, close, volume = self._ensure_f64(open_p), self._ensure_f64(close), self._ensure_f64(volume)
        if any(np.any(np.isnan(x)) or np.any(np.isinf(x)) for x in [open_p, close, volume]):
            return 0.5
        return self._lib.asi_vpin_proxy(self._ptr(open_p), self._ptr(close), self._ptr(volume), len(close), lookback)

    def phase_space(self, closes: np.ndarray, lookback: int = 10) -> dict:
        def_ret = {"orbit_radius": 0.0, "global_orbit": 0.0, "compression_ratio": 1.0, "is_compressed": False}
        if not self._lib or not self._loaded or closes is None or len(closes) == 0:
            return def_ret
        closes = self._ensure_f64(closes)
        if np.any(np.isnan(closes)) or np.any(np.isinf(closes)):
            return def_ret
            
        result = PhaseSpaceResultC()
        self._lib.asi_phase_space(self._ptr(closes), len(closes), lookback, ctypes.byref(result))
        return {
            "orbit_radius": result.orbit_radius,
            "global_orbit": result.global_orbit,
            "compression_ratio": result.compression_ratio,
            "is_compressed": bool(result.is_compressed),
        }

    def kurtosis(self, data: np.ndarray) -> float:
        if not self._lib: return 3.0
        data = self._ensure_f64(data)
        return self._lib.asi_kurtosis(self._ptr(data), len(data))

    def cross_scale_correlation(self, series_a: np.ndarray, series_b: np.ndarray) -> float:
        if not self._lib: return 0.0
        series_a, series_b = self._ensure_f64(series_a), self._ensure_f64(series_b)
        return self._lib.asi_cross_scale_correlation(self._ptr(series_a), len(series_a), self._ptr(series_b), len(series_b))

    def tick_entropy(self, bids: np.ndarray, bins: int = 10) -> float:
        if not self._lib: return 0.0
        bids = self._ensure_f64(bids)
        return self._lib.asi_tick_entropy(self._ptr(bids), len(bids), bins)

    def find_swings(self, highs: np.ndarray, lows: np.ndarray, lookback: int = 5) -> Tuple[list, list]:
        if not self._lib: return [], []
        highs = self._ensure_f64(highs)
        lows = self._ensure_f64(lows)
        n = len(highs)
        
        out_highs = (SwingResultC * 100)()
        out_lows = (SwingResultC * 100)()
        h_count = ctypes.c_int(0)
        l_count = ctypes.c_int(0)
        
        self._lib.asi_find_swings(self._ptr(highs), self._ptr(lows), n, lookback,
                                   out_highs, ctypes.byref(h_count),
                                   out_lows, ctypes.byref(l_count))
        
        sw_highs = [(out_highs[i].index, out_highs[i].price) for i in range(h_count.value)]
        sw_lows = [(out_lows[i].index, out_lows[i].price) for i in range(l_count.value)]
        return sw_highs, sw_lows

    def navier_stokes_pressure(self, bid_vols: np.ndarray, ask_vols: np.ndarray) -> Tuple[float, float]:
        if not self._lib: return 0.5, 0.0
        bid_vols = self._ensure_f64(bid_vols)
        ask_vols = self._ensure_f64(ask_vols)
        ratio = ctypes.c_double(0.0)
        pressure = ctypes.c_double(0.0)
        self._lib.asi_navier_stokes_pressure(self._ptr(bid_vols), self._ptr(ask_vols), 
                                              len(bid_vols), ctypes.byref(ratio), 
                                              ctypes.byref(pressure))
        return ratio.value, pressure.value

    def calc_micro_variance(self, data: np.ndarray) -> float:
        if not self._lib: return 0.0
        data = self._ensure_f64(data)
        return self._lib.asi_calc_micro_variance(self._ptr(data), len(data))

    def monte_carlo_merton(self, params: dict) -> dict:
        if not self._lib: return {"win_prob": 0.5, "expected_return": 0.0, "var_95": 0.0, "cvar_95": 0.0, "simulation_time_ms": 0.0}
        inp = MonteCarloInputC()
        inp.S0 = params["S0"]
        inp.mu = params["mu"]
        inp.sigma = params["sigma"]
        inp.jump_intensity = params["jump_intensity"]
        inp.jump_mean = params["jump_mean"]
        inp.jump_std = params["jump_std"]
        inp.dt = params["dt"]
        inp.n_sims = params["n_sims"]
        inp.n_steps = params["n_steps"]
        inp.stop_loss = params["stop_loss"]
        inp.take_profit = params["take_profit"]
        inp.is_buy = params["is_buy"]
        
        out = MonteCarloOutputC()
        self._lib.asi_monte_carlo_merton(ctypes.byref(inp), ctypes.byref(out))
        
        return {
            "win_prob": out.win_prob,
            "expected_return": out.expected_return,
            "var_95": out.var_95,
            "cvar_95": out.cvar_95,
            "simulation_time_ms": out.simulation_time_ms
        }

    @catch_and_log(default_return=None)
    def converge_signals(self, signals_list: list, interference_weight: float, decay: float) -> dict:
        """Agrega sinais de 50+ agentes em velocidade nativa (Phase 41)."""
        if not self._loaded: return None
        
        count = len(signals_list)
        if count == 0: return None
        
        signal_array = (AgentRawSignal * count)()
        
        for i, s in enumerate(signals_list):
            signal_array[i].signal = float(getattr(s, 'signal', 0.0))
            signal_array[i].confidence = float(getattr(s, 'confidence', 0.0))
            signal_array[i].weight = float(getattr(s, 'weight', 1.0))
            signal_array[i].is_hybrid = 0 
            
        result = ConvergenceResult()
        self._lib.asi_converge_signals(signal_array, count, interference_weight, decay, ctypes.byref(result))
        
        return {
            "signal": result.final_signal,
            "confidence": result.final_confidence,
            "coherence": result.final_coherence,
            "entropy": result.entropy,
            "bull_count": result.bull_count,
            "bear_count": result.bear_count,
            "neutral_count": result.neutral_count,
            "time_ms": result.computation_time_ms
        }

    def simulate_4096_hyperspace(self, closes: np.ndarray, current_volatility: float) -> dict:
        if not self._lib: return {"confidence_boost": 0.0, "expected_max_excursion": 0.0, "probability_density": 0.0, "hyperspace_time_ms": 0.0}
        closes = self._ensure_f64(closes)
        out = HyperspaceOutputC()
        self._lib.asi_simulate_4096_hyperspace(self._ptr(closes), len(closes), current_volatility, ctypes.byref(out))
        return {
            "confidence_boost": out.confidence_boost,
            "expected_max_excursion": out.expected_max_excursion,
            "probability_density": out.probability_density,
            "hyperspace_time_ms": out.hyperspace_time_ms
        }

    # ═══════════════════════════════════════════════════════════
    #  LGNN & THERMODYNAMICS (Phase Ω-Next)
    # ═══════════════════════════════════════════════════════════

    @catch_and_log(default_return=None)
    def calculate_lgnn(self, ticks: list, book_prices: np.ndarray, book_vols: np.ndarray) -> dict:
        if not self._loaded: return None
        count = len(ticks)
        tick_array = (TickData * count)()
        for i, t in enumerate(ticks):
            tick_array[i].bid = t.get("bid", 0.0)
            tick_array[i].ask = t.get("ask", 0.0)
            tick_array[i].last = t.get("last", 0.0)
            tick_array[i].volume = t.get("volume", 0.0)
            tick_array[i].time_msc = t.get("time_msc", 0)

        book_prices = self._ensure_f64(book_prices)
        book_vols = self._ensure_f64(book_vols)
        
        result = GraphResultC()
        self._lib.asi_calculate_lgnn(tick_array, count, self._ptr(book_prices), self._ptr(book_vols), len(book_prices), ctypes.byref(result))
        
        clusters = []
        for i in range(result.cluster_count):
            clusters.append({
                "price": result.clusters[i].price,
                "liquidity": result.clusters[i].liquidity,
                "centrality": result.clusters[i].centrality,
                "velocity": result.clusters[i].velocity
            })
            
        return {
            "clusters": clusters,
            "avalanche_risk": result.avalanche_risk,
            "global_centrality": result.global_centrality
        }

    @catch_and_log(default_return=None)
    def calculate_thermodynamics(self, bid_p: np.ndarray, bid_v: np.ndarray, ask_p: np.ndarray, ask_v: np.ndarray) -> dict:
        if not self._loaded: return None
        bid_p, bid_v = self._ensure_f64(bid_p), self._ensure_f64(bid_v)
        ask_p, ask_v = self._ensure_f64(ask_p), self._ensure_f64(ask_v)
        
        result = ThermodynamicResultC()
        self._lib.asi_calculate_thermodynamics(self._ptr(bid_p), self._ptr(bid_v), self._ptr(ask_p), self._ptr(ask_v), len(bid_p), ctypes.byref(result))
        
        return {
            "entropy": result.shannon_entropy,
            "temperature": result.temperature,
            "pressure": result.pressure,
            "compression": result.compression_ratio,
            "is_critical": bool(result.is_critical_state)
        }

    @catch_and_log(default_return=(None, None))
    def vector_search(self, query: np.ndarray, database: np.ndarray, top_k: int = 5) -> Tuple[np.ndarray, np.ndarray]:
        if not self._loaded: return None, None
        query = self._ensure_f64(query)
        database = self._ensure_f64(database)
        
        query_dim = len(query)
        db_size = len(database) // query_dim
        
        out_similarities = np.zeros(top_k, dtype=np.float64)
        out_indices = np.zeros(top_k, dtype=np.int32)
        
        actual_k = self._lib.asi_vector_search(
            self._ptr(query), self._ptr(database),
            query_dim, db_size,
            self._ptr(out_similarities), 
            out_indices.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
            top_k
        )
        
        return out_similarities[:actual_k], out_indices[:actual_k]

    @catch_and_log(default_return=None)
    def calculate_causal_impact(self, feature_matrix: np.ndarray, our_order_size: float, target_index: int = -1) -> dict:
        if not self._loaded: return None
        mat = self._ensure_f64(feature_matrix)
        rows, cols = mat.shape
        if target_index == -1: target_index = cols - 1
        
        result = CausalResultC()
        self._lib.asi_calculate_causal_impact(self._ptr(mat), rows, cols, our_order_size, target_index, ctypes.byref(result))
        
        return {
            "causal_effect": result.causal_effect,
            "counterfactual_loss": result.counterfactual_loss,
            "do_impact": result.do_impact_score,
            "confidence": result.confidence
        }

    @catch_and_log(default_return=None)
    def calculate_topology(self, prices: np.ndarray, volumes: np.ndarray) -> dict:
        if not self._loaded: return None
        prices = self._ensure_f64(prices)
        volumes = self._ensure_f64(volumes)
        levels = len(prices)
        
        result = TopologyResultC()
        self._lib.asi_calculate_topology(self._ptr(prices), self._ptr(volumes), levels, ctypes.byref(result))
        
        return {
            "betti_0": result.betti_0,
            "betti_1": result.betti_1,
            "entropy": result.persistence_entropy,
            "max_hole": result.critical_hole_size,
            "unstable": bool(result.is_geometrically_unstable)
        }

    @catch_and_log(default_return=None)
    def calculate_tensor_swarm(self, spot_data: np.ndarray, deriv_data: np.ndarray, bond_dim: int = 16) -> dict:
        if not self._loaded: return None
        spot = self._ensure_f64(spot_data)
        deriv = self._ensure_f64(deriv_data)
        length = len(spot)
        
        result = TensorResultC()
        self._lib.asi_calculate_tensor_swarm(self._ptr(spot), self._ptr(deriv), length, bond_dim, ctypes.byref(result))
        
        return {
            "entanglement": result.entanglement_entropy,
            "loss": result.compression_loss,
            "stability": result.stability_index,
            "mode": result.dominant_mode
        }

    # ═══ STIGMERGY ═══
    def deposit_pheromone(self, price: float, intensity: float, decay: float = 0.05):
        if not self._lib: return
        self._lib.asi_deposit_pheromone(price, intensity, decay)

    def sense_pheromone(self, price: float) -> float:
        if not self._lib: return 0.0
        return self._lib.asi_sense_pheromone(price)

    def update_pheromones(self, dt: float = 1.0):
        if not self._lib: return
        self._lib.asi_update_pheromone_field(dt)

    @catch_and_log(default_return=None)
    def calculate_fisher_metric(self, prev_dist: np.ndarray, curr_dist: np.ndarray) -> dict:
        if not self._loaded: return None
        p = self._ensure_f64(prev_dist)
        q = self._ensure_f64(curr_dist)
        n = len(p)
        
        result = FisherResultC()
        self._lib.asi_calculate_fisher_metric(self._ptr(p), self._ptr(q), n, ctypes.byref(result))
        
        return {
            "fisher": result.fisher_information,
            "nat_grad": result.natural_gradient_x,
            "kl_div": result.information_distance,
            "step": result.optimal_step_size
        }

    # ═══════════════════════════════════════════════════════════
    #  PHASE Ω-ONE: SNN
    # ═══════════════════════════════════════════════════════════

    @catch_and_log(default_return=(0.0, 0))
    def update_lif_neuron(self, current: float, dt: float, v_rest: float, v_threshold: float,
                          r: float, c: float, potential: float) -> Tuple[float, int]:
        """Atualiza um neurônio LIF e retorna novo potencial e se disparou."""
        if not self._loaded: return potential, 0
        
        v_ptr = ctypes.c_double(potential)
        fired_ptr = ctypes.c_int(0)
        self._lib.asi_update_lif_neuron(
            ctypes.c_double(current), ctypes.c_double(dt), 
            ctypes.c_double(v_rest), ctypes.c_double(v_threshold), 
            ctypes.c_double(r), ctypes.c_double(c),
            ctypes.byref(v_ptr), ctypes.byref(fired_ptr)
        )
        return float(v_ptr.value), int(fired_ptr.value)

    @catch_and_log(default_return=None)
    def solve_mfg(self, density_profile: np.ndarray, price_min: float, price_step: float,
                   current_price: float, volatility: float, reward_function: np.ndarray) -> dict:
        """Resolve Mean Field Games (HJB + Fokker-Planck) para trajetória ótima."""
        if not self._loaded: return None
        
        density = self._ensure_f64(density_profile)
        rewards = self._ensure_f64(reward_function)
        
        result = MFGResultC()
        self._lib.asi_solve_mfg(
            self._ptr(density), len(density), price_min, price_step,
            current_price, volatility, self._ptr(rewards), ctypes.byref(result)
        )
        
        return {
            "optimal_velocity": result.optimal_velocity,
            "crowd_density": result.crowd_density,
            "expected_drift": result.expected_drift,
            "stability": result.stability_score
        }

    @catch_and_log(default_return=None)
    def calculate_feynman_path(self, history: np.ndarray, target_price: float, 
                                time_horizon: float, liquidity_friction: float) -> dict:
        """Calcula o Propagador Quântico via Integrais de Trajetória de Feynman."""
        if not self._loaded: return None
        
        hist = self._ensure_f64(history)
        result = PathIntegralResultC()
        self._lib.asi_calculate_feynman_path(
            self._ptr(hist), len(hist), target_price,
            time_horizon, liquidity_friction, ctypes.byref(result)
        )
        
        return {
            "amplitude_real": result.probability_amplitude_real,
            "amplitude_imag": result.probability_amplitude_imag,
            "stationary_price": result.stationary_phase_price,
            "interference": result.quantum_interference_score
        }

    @catch_and_log(default_return=None)
    def calculate_chaos(self, ticks: np.ndarray, sample_rate: float) -> dict:
        """Calcula o Expoente de Lyapunov e Horizonte de Previsibilidade."""
        if not self._loaded: return None
        
        data = self._ensure_f64(ticks)
        result = ChaosResultC()
        self._lib.asi_calculate_chaos(self._ptr(data), len(data), sample_rate, ctypes.byref(result))
        
        return {
            "lyapunov": result.lyapunov_exponent,
            "horizon": result.predictability_limit,
            "entropy": result.entropy,
            "chaotic": bool(result.is_chaotic)
        }

    # ═══ OMEGA-CLASS PHASE ════
    
    def map_poincare_dist(self, r1: float, theta1: float, r2: float, theta2: float) -> float:
        if not self._loaded: return 0.0
        return self._lib.asi_map_poincare_dist(r1, theta1, r2, theta2)

    def init_reservoir(self, n_neurons: int, spectral_radius: float, connectivity: float):
        if not self._loaded: return
        self._lib.asi_init_reservoir(n_neurons, spectral_radius, connectivity)

    def perturb_reservoir(self, inputs: np.ndarray):
        if not self._loaded: return
        inputs = self._ensure_f64(inputs)
        self._lib.asi_perturb_reservoir(self._ptr(inputs), len(inputs))

    def read_reservoir_output(self, n_outputs: int) -> np.ndarray:
        if not self._loaded: return np.array([])
        out = np.zeros(n_outputs, dtype=np.float64)
        self._lib.asi_read_reservoir_output(self._ptr(out), n_outputs)
        return out

    @catch_and_log(default_return=None)
    def infer_holographic_pressure(self, ticks: np.ndarray, imbalance: np.ndarray) -> dict:
        if not self._loaded: return None
        ticks = self._ensure_f64(ticks)
        imbalance = self._ensure_f64(imbalance)
        
        result = HolographicResultC()
        self._lib.asi_infer_holographic_pressure(
            self._ptr(ticks), len(ticks),
            self._ptr(imbalance), len(imbalance),
            ctypes.byref(result)
        )
        
        return {
            "pressure": result.bulk_pressure,
            "entropy": result.entanglement_entropy,
            "geodesic": result.geodesic_distance,
            "coherence": result.holographic_coherence,
            "stable": bool(result.is_manifold_stable)
        }

    # ═══════════════════════════════════════════════════════════
    #  PHASE Ω-EXTREME
    # ═══════════════════════════════════════════════════════════

    @catch_and_log(default_return=None)
    def lorentz_clock_update(self, volatility: float, volume: float, physical_dt: float, market_c_scale: float = 1000.0) -> dict:
        if not self._loaded: return None
        result = LorentzClockResultC()
        self._lib.asi_lorentz_clock_update(
            ctypes.c_double(volatility), 
            ctypes.c_double(volume), 
            ctypes.c_double(physical_dt), 
            ctypes.c_double(market_c_scale),
            ctypes.byref(result)
        )
        return {
            "internal_dt": result.internal_time_passed,
            "dilation": result.dilation_factor,
            "energy": result.kinetic_energy
        }

    @catch_and_log(default_return=None)
    def calculate_phi(self, signals: list, weights: Optional[np.ndarray] = None) -> dict:
        if not self._lib or not self._loaded: return None
        count = len(signals)
        sig_array = (AgentSignal * count)()
        for i, s in enumerate(signals):
            # AgentSignal é uma dataclass (Python side), acessar atributos diretamente
            sig_array[i].signal = float(s.signal)
            sig_array[i].confidence = float(s.confidence)
            sig_array[i].weight = float(s.weight)
        
        w_ptr = None
        if weights is not None:
            weights = self._ensure_f64(weights)
            w_ptr = self._ptr(weights)
            
        result = ConsciousnessResultC()
        self._lib.asi_calculate_phi(sig_array, count, w_ptr, ctypes.byref(result))
        return {
            "phi": result.phi_value,
            "coherence": result.coherence_score,
            "entropy": result.integration_entropy
        }

    @catch_and_log(default_return=None)
    def process_qca_grid(self, bids: np.ndarray, asks: np.ndarray, alpha: float) -> dict:
        if not self._loaded: return None
        bids, asks = self._ensure_f64(bids), self._ensure_f64(asks)
        result = QCAResultC()
        self._lib.asi_process_qca_grid(self._ptr(bids), self._ptr(asks), len(bids), alpha, ctypes.byref(result))
        return {
            "entropy": result.grid_entropy,
            "speed": result.transition_speed,
            "critical": bool(result.is_critical)
        }

    @catch_and_log(default_return=None)
    def solve_lotka_volterra(self, dt: float, params: dict, prey: float, predator: float) -> Tuple[float, float, dict]:
        if not self._loaded: return prey, predator, None
        p_ptr = ctypes.c_double(prey)
        d_ptr = ctypes.c_double(predator)
        result = PredatorPreyResultC()
        self._lib.asi_solve_lotka_volterra(
            dt, params["alpha"], params["beta"], params["delta"], params["gamma"],
            ctypes.byref(p_ptr), ctypes.byref(d_ptr), ctypes.byref(result)
        )
        return p_ptr.value, d_ptr.value, {
            "prey": result.prey_biomass,
            "predator": result.predator_biomass,
            "risk": result.extinction_risk,
            "efficiency": result.hunt_efficiency
        }

    @catch_and_log(default_return=None)
    def harvest_black_swan(self, extreme_ticks: np.ndarray, threshold: float) -> dict:
        if not self._loaded: return None
        ticks = self._ensure_f64(extreme_ticks)
        result = ExtremeValueResultC()
        self._lib.asi_harvest_black_swan(self._ptr(ticks), len(ticks), threshold, ctypes.byref(result))
        return {
            "exceedance": result.threshold_exceedance,
            "tail_risk": result.tail_risk,
            "is_black_swan": bool(result.is_black_swan)
        }

    # ═══════════════════════════════════════════════════════════
    #  PHD OMEGA MATH (Phase 69)
    # ═══════════════════════════════════════════════════════════

    def calculate_laser_compression(self, energy_window: np.ndarray) -> float:
        if not self._loaded: return 0.0
        window = self._ensure_f64(energy_window)
        return self._lib.calculate_laser_compression(self._ptr(window), len(window))

    def calculate_navier_stokes_reynolds(self, velocities: np.ndarray, densities: np.ndarray) -> float:
        if not self._loaded: return 0.0
        v = self._ensure_f64(velocities)
        rho = self._ensure_f64(densities)
        return self._lib.calculate_navier_stokes_reynolds(self._ptr(v), self._ptr(rho), len(v))

    def calculate_dark_matter_gravity(self, acceleration: float, visible_mass: float) -> float:
        if not self._loaded: return 0.0
        return self._lib.calculate_dark_matter_gravity(ctypes.c_double(acceleration), ctypes.c_double(visible_mass))

    def calculate_aethel_viscosity(self, vwap_deltas: np.ndarray) -> float:
        if not self._loaded: return 1.0
        deltas = self._ensure_f64(vwap_deltas)
        return self._lib.calculate_aethel_viscosity(self._ptr(deltas), len(deltas))

    def detect_soliton_wave(self, velocities: np.ndarray) -> float:
        if not self._loaded: return 0.0
        v = self._ensure_f64(velocities)
        return self._lib.detect_soliton_wave(self._ptr(v), len(v))

    # ═══ TRANSCENDENCE ENGINES (QED & NLSE) ═══

    def calculate_casimir_force(self, virtual_cancellations: np.ndarray, spread_distance: float) -> float:
        if not self._loaded: return 0.0
        v_cancels = self._ensure_f64(virtual_cancellations)
        return self._lib.calculate_casimir_force(self._ptr(v_cancels), len(v_cancels), ctypes.c_double(spread_distance))

    def solve_nlse_rogue_wave(self, amplitudes: np.ndarray, phases: np.ndarray, nonlinear_coupling: float) -> float:
        if not self._loaded: return 0.0
        amps = self._ensure_f64(amplitudes)
        phs = self._ensure_f64(phases)
        return self._lib.solve_nlse_rogue_wave(self._ptr(amps), self._ptr(phs), len(amps), ctypes.c_double(nonlinear_coupling))

    # ═══ QUANTUM GRAVITY (Phase Ω-Apocalypse) ═══

    def calculate_eigenvector_centrality(self, price_levels: np.ndarray, volumes: np.ndarray, damping_factor: float = 0.85) -> np.ndarray:
        if not self._loaded: return np.zeros_like(price_levels)
        prices = self._ensure_f64(price_levels)
        vols = self._ensure_f64(volumes)
        size = len(prices)
        out_centralities = np.zeros(size, dtype=np.float64)
        
        self._lib.calculate_eigenvector_centrality(self._ptr(prices), self._ptr(vols), size, ctypes.c_double(damping_factor), self._ptr(out_centralities))
        return out_centralities

    # ═══ NON-LINEAR DYNAMICS (Phase Ω-Eternity) ═══

    def calculate_rg_scaling_invariance(self, tick_data: np.ndarray, m1_data: np.ndarray, m5_data: np.ndarray) -> float:
        if not self._loaded: return 0.0
        t = self._ensure_f64(tick_data)
        m1 = self._ensure_f64(m1_data)
        m5 = self._ensure_f64(m5_data)
        return self._lib.calculate_rg_scaling_invariance(
            self._ptr(t), len(t), 
            self._ptr(m1), len(m1), 
            self._ptr(m5), len(m5)
        )

    def estimate_attractor_folding(self, prices: np.ndarray, dt: float = 1.0) -> float:
        if not self._loaded: return 0.0
        p = self._ensure_f64(prices)
        return self._lib.estimate_attractor_folding(self._ptr(p), len(p), ctypes.c_double(dt))

    # ═══ TOPOLOGICAL BRAIDING (Phase Ω-Continuum) ═══

    def calculate_braid_index(self, strands: np.ndarray, n_agents: int, lookback: int) -> float:
        if not self._loaded: return 0.0
        s = self._ensure_f64(strands)
        return self._lib.calculate_braid_index(self._ptr(s), n_agents, lookback)

    def calculate_kaldor_hicks_ratio(self, expected_alpha: float, slippage_est: float, spread: float, commission: float) -> float:
        if not self._loaded: return 1.0
        return self._lib.calculate_kaldor_hicks_ratio(
            ctypes.c_double(expected_alpha), 
            ctypes.c_double(slippage_est), 
            ctypes.c_double(spread), 
            ctypes.c_double(commission)
        )

    # ═══ GEOMETRIC SPECTRAL ANALYSIS (Phase Ω-Genesis) ═══

    def calculate_spectral_flux(self, data: np.ndarray) -> float:
        if not self._lib: return 0.0
        d = self._ensure_f64(data)
        return self._lib.calculate_spectral_flux(self._ptr(d), len(d))

    def calculate_berry_curvature(self, signals: np.ndarray, n_agents: int, n_steps: int) -> float:
        if not self._lib: return 0.0
        s = self._ensure_f64(signals)
        return self._lib.calculate_berry_curvature(self._ptr(s), n_agents, n_steps)

    # ═══ QUANTUM FIELD THEORY (Phase Ω-Aethel) ═══

    def calculate_fermi_pressure(self, volumes: np.ndarray, temperature: float) -> float:
        if not self._lib: return 0.0
        v = self._ensure_f64(volumes)
        return self._lib.calculate_fermi_pressure(self._ptr(v), len(v), ctypes.c_double(temperature))

    def calculate_chern_simons_index(self, x: np.ndarray, y: np.ndarray, z: np.ndarray) -> float:
        if not self._lib: return 0.0
        vx = self._ensure_f64(x)
        vy = self._ensure_f64(y)
        vz = self._ensure_f64(z)
        return self._lib.calculate_chern_simons_index(self._ptr(vx), self._ptr(vy), self._ptr(vz), len(vx))

    def calculate_byzantine_penalties(self, errors: np.ndarray, penalties: np.ndarray):
        if not self._lib: return
        e = self._ensure_f64(errors)
        p = self._ensure_f64(penalties)
        self._lib.calculate_byzantine_penalties(self._ptr(e), len(e), self._ptr(p))
        np.copyto(penalties, p)


# ═══ SINGLETON ═══
CPP_CORE = CppASICore()
