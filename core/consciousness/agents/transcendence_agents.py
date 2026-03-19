import numpy as np
import math
from typing import Dict, Any, List, Optional
from core.consciousness.agents.base import BaseAgent, AgentSignal
from cpp.asi_bridge import CPP_CORE
from utils.decorators import catch_and_log

class RiemannianManifoldAgent(BaseAgent):
    """
    [Ω-RIEMANNIAN] Computes the sectional curvature of the price-volume manifold.
    Positive curvature indicates a 'gravity well' (reversion), negative indicates 
    hyperbolic expansion (strong trend).
    """
    def __init__(self, weight: float = 2.5):
        super().__init__("RiemannianManifold", weight)
        
    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        if not CPP_CORE.is_loaded: return None
        
        closes = snapshot.m1_closes
        if len(closes) < 20: return None
        
        try:
            res = CPP_CORE.phase_space(closes)
            orbit = res.get("global_orbit", 0)
            is_compressed = res.get("is_compressed", False)
            
            vwap = getattr(snapshot, 'vwap', snapshot.price)

            if is_compressed: 
                bias = -1.0 if snapshot.price > vwap else 1.0
                return AgentSignal(self.name, bias, 0.85, f"Manifold Curvature Positive (Gravity Well)", self.weight)
            else:
                bias = 1.0 if snapshot.price > vwap else -1.0
                return AgentSignal(self.name, bias, 0.70, f"Hyperbolic Trend Expansion", self.weight)
        except:
            return None

class InformationGeometryAgent(BaseAgent):
    """
    [Ω-FISHER] Information Geometry Agent.
    Measures the distance between the current state and the equilibrium state
    using the Fisher Information Metric.
    """
    def __init__(self, weight: float = 2.2):
        super().__init__("InformationGeometry", weight)
        self.prev_dist = None
        
    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        if not CPP_CORE.is_loaded: return None
        
        # Proxy for market state distribution
        history = snapshot.m1_closes[-15:]
        if len(history) < 10: return None
        
        history_arr = np.array(history, dtype=np.float64)
        returns = np.diff(np.log(history_arr + 1e-9))
        if np.std(returns) < 1e-12:
            return AgentSignal(self.name, 0.0, 0.0, "Zero Variance in Returns", self.weight)
            
        curr_dist = np.histogram(returns, bins=10, range=(-0.005, 0.005), density=True)[0]
        
        if self.prev_dist is None:
            self.prev_dist = curr_dist
            return None
            
        try:
            metrics = CPP_CORE.calculate_fisher_metric(self.prev_dist, curr_dist)
            self.prev_dist = curr_dist
            
            kl_div = metrics.get("kl_div", 0)
            if kl_div > 2.5: # Extreme Paradigm Shift
                return AgentSignal(self.name, 0.0, 0.99, f"Information Geometry Paradigm Shift (KL: {kl_div:.2f})", self.weight, metadata={"kl_div": kl_div, "paradigm_shift": True})
                
            return AgentSignal(self.name, 0.0, 0.1, f"Metric Stability (KL: {kl_div:.2f})", self.weight, metadata={"kl_div": kl_div})
        except:
            return None

class QuantumSuperpositionAgent(BaseAgent):
    """
    [Ω-SCHRODINGER] Models the market as a superposition of states.
    Uses the Schrodinger Wave Function to calculate the probability of tunneling
    through price barriers.
    """
    def __init__(self, weight: float = 2.4):
        super().__init__("QuantumSuperposition", weight)
        
    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        if not CPP_CORE.is_loaded: return None
        
        history = snapshot.m1_closes
        if len(history) < 20: return None
        
        target = snapshot.price * 1.001 
        
        try:
            res = CPP_CORE.calculate_feynman_path(
                history, target, time_horizon=60.0, liquidity_friction=0.5
            )
            
            interference = res.get("interference", 0)
            if abs(interference) > 0.8: 
                sig = 1.0 if interference > 0 else -1.0
                return AgentSignal(self.name, sig, 0.92, f"Constructive Quantum Interference", self.weight)
                
            return AgentSignal(self.name, 0.0, 0.2, f"Quantum Decoherence", self.weight)
        except:
            return None

class CasimirEffectAgent(BaseAgent):
    """
    [Ω-QED] Quantum Electrodynamics of Order Flow.
    """
    def __init__(self, weight: float = 2.8):
        super().__init__("CasimirEffect", weight)
        self.history_cancels = []
        
    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        if not CPP_CORE.is_loaded: return None
        spread = snapshot.spread
        fluctuation = snapshot.metadata.get("tick_velocity", 0.0) 
        
        self.history_cancels.append(abs(fluctuation))
        if len(self.history_cancels) > 20: self.history_cancels.pop(0)
            
        if len(self.history_cancels) < 10 or spread == 0:
            return None
            
        try:
            cancels_arr = np.array(self.history_cancels, dtype=np.float64)
            force = CPP_CORE.calculate_casimir_force(cancels_arr, float(spread))
            
            vwap = getattr(snapshot, 'vwap', snapshot.price)
            bias = 1.0 if snapshot.price > vwap else -1.0
            
            if force > 1000.0:
                return AgentSignal(self.name, bias, min(1.0, force / 5000.0), f"Casimir Vacuum Collapse (Force: {force:.1f})", self.weight)
            return None
        except:
            return None

class InformationBottleneckMetaAgent(BaseAgent):
    """ [Ω-MDL] Information Bottleneck Theory. """
    def __init__(self, weight: float = 3.1):
        super().__init__("InformationBottleneckMeta", weight)
        self.compression_ratio = 0.75

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        raw_signals = kwargs.get("swarm_raw_signals", [])
        if not raw_signals: return None
        
        entropy = snapshot.metadata.get("tick_entropy", 0.5)
        
        if entropy > 0.85: # Over-noisy environment
            # Filter the consensus
            filtered_signal = np.mean([s.signal for s in raw_signals if s.confidence < 0.90])
            if not np.isnan(filtered_signal):
                return AgentSignal(self.name, filtered_signal, 0.95, "MDL_NOISE_COMPRESSION_ACTIVE", self.weight)
        
        return None

class RicciFlowRegimeAgent(BaseAgent):
    """
    [Ω-RICCI] Geometric Market Evolution Agent.
    Smooths the market manifold using Ricci Flow to detect structural regime changes 
    before they appear in price filters.
    """
    def __init__(self, weight: float = 3.5):
        super().__init__("RicciRegime", weight)
        self._history_curvature = []

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        if not CPP_CORE.is_loaded: return None
        
        closes = snapshot.m1_closes[-30:]
        if len(closes) < 20: return None
        
        try:
            # Ricci Flow smoothing simulation via CPP
            res = CPP_CORE.calculate_ricci_flow(closes, iterations=5, step=0.01)
            curvature = res.get("scalar_curvature", 0.0)
            is_singularity = res.get("is_singularity", False)
            
            self._history_curvature.append(curvature)
            if len(self._history_curvature) > 10: self._history_curvature.pop(0)
            
            # Singularities or jump in curvature indicates a hidden regime transition
            if is_singularity or (len(self._history_curvature) >= 2 and abs(curvature - self._history_curvature[-2]) > 0.8):
                # Positive curvature surge usually precedes a sharp reversal/reversion
                # Negative curvature surge usually precedes a trend acceleration (Breakout)
                bias = -1.0 if curvature > 0 else 1.0
                conf = 0.95
                return AgentSignal(self.name, bias, conf, f"Ricci Flow Singularity: Manifold Smoothness Collapse (K={curvature:.3f})", self.weight, metadata={"ricci_singularity": True, "curvature": curvature})
                
            return AgentSignal(self.name, 0.0, 0.1, f"Ricci Flow Stable (K={curvature:.3f})", self.weight, metadata={"curvature": curvature})
        except:
            return None

class NonBondedRepulsionAgent(BaseAgent):
    """
    [Ω-CHEMISTRY] Van der Waals Market Repulsion.
    Detects when price 'repels' from a major liquidity cluster without 
    physical contact (non-bonded interaction). High-signal for 'Limit Order' reversals.
    """
    def __init__(self, weight: float = 3.2):
        super().__init__("NonBondedRepulsion", weight)
        self.repulsion_potential = 0.0

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        if not snapshot.book: return None
        
        # Calculate potential ENERGY at current price vs book clusters
        bids = snapshot.book.get("bids", [])[:20]
        asks = snapshot.book.get("asks", [])[:20]
        
        # Lennard-Jones Potential approximation
        p = snapshot.price
        r_sigma = snapshot.atr * 0.5 # Interaction radius
        
        def potential(levels):
            if not levels: return 0.0
            return sum( (1.0/(abs(p - l['price'])/r_sigma)**12) - (1.0/(abs(p - l['price'])/r_sigma)**6) for l in levels if p != l['price'])

        bid_pot = potential(bids)
        ask_pot = potential(asks)
        
        diff = bid_pot - ask_pot
        if abs(diff) > 10.0: # Significant repulsion
            bias = 1.0 if diff > 0 else -1.0
            return AgentSignal(self.name, bias, 0.96, f"Van der Waals Repulsion (Pot={diff:.1f})", self.weight, metadata={"repulsion": diff})
            
        return None

class RogueWaveNLSEAgent(BaseAgent):
    """ [Ω-WAVE] Gross-Pitaevskii Rogue Waves. """
    def __init__(self, weight: float = 2.9):
        super().__init__("RogueWaveNLSE", weight)
        self.amplitudes = []
        self.phases = []
        
    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        if not CPP_CORE.is_loaded: return None
        
        vol = snapshot.metadata.get("tick_velocity", 0.0)
        phase = math.atan2(vol, 1.0)
        
        self.amplitudes.append(abs(vol))
        self.phases.append(phase)
        if len(self.amplitudes) > 30:
            self.amplitudes.pop(0)
            self.phases.pop(0)
        if len(self.amplitudes) < 15: return None
        try:
            rogue_prob = CPP_CORE.solve_nlse_rogue_wave(np.array(self.amplitudes), np.array(self.phases), 1.5)
            if rogue_prob > 50.0:
                sig = 1.0 if np.mean(self.phases[-3:]) > 0 else -1.0
                return AgentSignal(self.name, sig, 0.99, f"NLSE Rogue Wave imminent (Prob: {rogue_prob:.1f})", self.weight)
            return None
        except: return None

class AutocatalyticHypercycleMetaAgent(BaseAgent):
    """ [Ω-ORIGIN] Autocatalytic Hypercycles. """
    def __init__(self, weight: float = 3.5):
        super().__init__("AutocatalyticHypercycle", weight)
        
    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        hit_rates = kwargs.get("agent_hit_rates", {})
        if not hit_rates: return None
        elite_count = sum(1 for rate in hit_rates.values() if rate > 0.85)
        if elite_count >= 3:
            return AgentSignal(self.name, 0.0, 0.99, f"Hypercycle Active ({elite_count} elite nodes)", self.weight)
        return None

class HolographicEntanglementAgent(BaseAgent):
    """ [Ω-HOLOGRAPHY] Ryu-Takayanagi Entanglement. """
    def __init__(self, weight: float = 3.0):
        super().__init__("HolographicEntanglement", weight)
        self.btc_history = []
        self.macro_history = []
        
    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        macro_bias = snapshot.metadata.get("macro_bias", 0.0) 
        
        self.btc_history.append(snapshot.price)
        self.macro_history.append(macro_bias)
        if len(self.btc_history) > 20:
            self.btc_history.pop(0)
            self.macro_history.pop(0)
        if len(self.btc_history) < 10: return None
        
        if np.std(self.btc_history) < 1e-12 or np.std(self.macro_history) < 1e-12:
            corr = 0.0
        else:
            corr = np.corrcoef(self.btc_history, self.macro_history)[0, 1]
        
        if math.isnan(corr): corr = 0.0
        
        if abs(corr) < 0.15: # Disconnected from reality
            # Fade the BTC move
            trend = self.btc_history[-1] - self.btc_history[-5]
            sig = -1.0 if trend > 0 else 1.0
            return AgentSignal(self.name, sig, 0.90, f"Holographic Disconnection (Corr: {corr:.2f})", self.weight)
            
        return None
