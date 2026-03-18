"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — ETERNITY AGENTS (Phase Ω)                   ║
║     Sistemas Analíticos baseados em Teoria do Caos Dinâmico, Homeostase     ║
║     Cibernética e Mecânica Quântica Aplicada (Spin & Decoerência).          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
import math
from typing import Dict, Any, Optional
from core.consciousness.agents.base import BaseAgent, AgentSignal
from cpp.asi_bridge import CPP_CORE
from utils.decorators import catch_and_log

class QuantumSpinAgent(BaseAgent):
    """
    [Phase Ω-Eternity] Quantum Spin (Up/Down) & Decoherence.
    """
    def __init__(self, weight=2.9):
        super().__init__("QuantumSpin", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles = snapshot.candles.get("M1")
        if not candles or len(candles["close"]) < 20:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles["close"], dtype=np.float64)
        opens = np.array(candles["open"], dtype=np.float64)
        volumes = np.array(candles["tick_volume"], dtype=np.float64)

        body_sizes = closes - opens
        atr = snapshot.metadata.get("atr_m1", 10.0) + 1e-6

        spins = []
        for i in range(len(body_sizes[-15:])):
            b_size = body_sizes[-15:][i]
            if abs(b_size) < atr * 0.1:
                spins.append(0.0) 
            else:
                spin_dir = 0.5 if b_size > 0 else -0.5
                spins.append(spin_dir * (volumes[-15:][i] / (np.mean(volumes[-15:]) + 1e-6)))

        spin_coherence_5 = np.sum(spins[-5:])
        
        if spin_coherence_5 > 4.0:
            return AgentSignal(self.name, -1.0, min(0.95, spin_coherence_5 / 6.0), f"DECOHERENCE_IMMINENT_BEAR (SpinSum={spin_coherence_5:.2f})", self.weight)
        elif spin_coherence_5 < -4.0:
            return AgentSignal(self.name, 1.0, min(0.95, abs(spin_coherence_5) / 6.0), f"DECOHERENCE_IMMINENT_BULL (SpinSum={spin_coherence_5:.2f})", self.weight)
        else:
            trend_spin = np.sign(spin_coherence_5)
            if trend_spin != 0:
                return AgentSignal(self.name, trend_spin * 0.5, 0.60, "SPIN_ALIGNMENT_NORMAL", self.weight)

        return AgentSignal(self.name, 0.0, 0.0, "SPIN_CHAOS", self.weight)


class CyberneticHomeostasisAgent(BaseAgent):
    """
    [Phase Ω-Eternity] Cibernética de Ashby: Homeostase e Lei da Variedade Requisita.
    """
    def __init__(self, weight=2.7):
        super().__init__("CyberneticHomeostasis", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles = snapshot.candles.get("M5") 
        if not candles or len(candles["close"]) < 50:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles["close"], dtype=np.float64)
        highs = np.array(candles["high"], dtype=np.float64)
        lows = np.array(candles["low"], dtype=np.float64)
        volumes = np.array(candles["tick_volume"], dtype=np.float64)

        typical_prices = (highs[-50:] + lows[-50:] + closes[-50:]) / 3.0
        vwap = np.sum(typical_prices * volumes[-50:]) / (np.sum(volumes[-50:]) + 1e-6)

        current_price = snapshot.price
        variance = np.sum(volumes[-50:] * (typical_prices - vwap)**2) / (np.sum(volumes[-50:]) + 1e-6)
        std_dev = np.sqrt(variance)

        distance_from_vwap = current_price - vwap
        z_score = distance_from_vwap / (std_dev + 1e-6)

        if z_score > 2.5:
            return AgentSignal(self.name, -1.0, min(0.95, (z_score - 2.0) / 2.0), f"HOMEOSTATIC_REJECTION_BEAR (Z={z_score:.2f})", self.weight)
        elif z_score < -2.5:
            return AgentSignal(self.name, 1.0, min(0.95, (abs(z_score) - 2.0) / 2.0), f"HOMEOSTATIC_REJECTION_BULL (Z={z_score:.2f})", self.weight)

        return AgentSignal(self.name, 0.0, 0.0, "HOMEOSTASIS_MAINTAINED", self.weight)


class ChaosFractalDimensionAgent(BaseAgent):
    """
    [Phase Ω-Eternity] Dimensão Fractal do Caos (Mandelbrot / Hurst Evolution).
    """
    def __init__(self, weight=3.2):
        super().__init__("ChaosFractalDim", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        if not CPP_CORE.is_loaded: return AgentSignal(self.name, 0.0, 0.0, "CPP_NOT_LOADED", self.weight)
        
        closes = snapshot.m1_closes
        if len(closes) < 64:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        d_current = CPP_CORE.fractal_dimension(closes[-64:], max_box=16)
        
        momentum_dir = np.sign(snapshot.price - closes[-10])
        if momentum_dir == 0: momentum_dir = 1.0

        if d_current < 1.35:
            return AgentSignal(self.name, momentum_dir, 0.90, f"FRACTAL_SMOOTHING_TREND (D={d_current:.2f})", self.weight)
        elif d_current > 1.65:
            return AgentSignal(self.name, -momentum_dir, 0.85, f"FRACTAL_ROUGHNESS_REVERSAL (D={d_current:.2f})", self.weight)

        return AgentSignal(self.name, 0.0, 0.1, f"RANDOM_WALK (D={d_current:.2f})", self.weight)

class RGScalingInvariance(BaseAgent):
    """
    [Ω-RG] Renormalization Group Scaling Invariance.
    """
    def __init__(self, weight: float = 4.5):
        super().__init__("RGScalingInvariance", weight)
        
    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        if not CPP_CORE.is_loaded: return None
        
        ticks = np.array([t.get("last", snapshot.price) for t in snapshot.recent_ticks[-50:]])
        m1 = snapshot.m1_closes[-30:]
        m5 = snapshot.m5_closes[-20:]
        
        if len(ticks) < 10 or len(m1) < 10 or len(m5) < 5:
            return None
            
        try:
            score = CPP_CORE.calculate_rg_scaling_invariance(ticks, m1, m5)
            direction = np.sign(score)
            invariance = abs(score)
            
            if invariance > 0.85: 
                return AgentSignal(self.name, direction, invariance, f"RG Scaling Invariant (Score: {invariance:.2f})", self.weight)
            
            return AgentSignal(self.name, 0.0, 0.1, f"Low Scaling Consistency ({invariance:.2f})", self.weight)
        except:
            return None

class StrangeAttractorFoldingAgent(BaseAgent):
    """
    [Ω-ATTRACTOR] Strange Attractor (Lorenz) Orbital Divergence.
    """
    def __init__(self, weight: float = 4.2):
        super().__init__("StrangeAttractorFolding", weight)
        
    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        if not CPP_CORE.is_loaded: return None
        
        history = snapshot.m1_closes[-50:]
        if len(history) < 20: return None
        
        try:
            divergence = CPP_CORE.estimate_attractor_folding(history, dt=1.0)
            
            if divergence > 5.0: 
                momentum_dir = np.sign(snapshot.price - history[-5])
                return AgentSignal(self.name, -momentum_dir, 0.92, f"Attractor Folding Detected (Divergence: {divergence:.2f})", self.weight)
                
            return AgentSignal(self.name, 0.0, 0.1, f"Stable Orbital Path ({divergence:.2f})", self.weight)
        except:
            return None

class BraidTopologyAgent(BaseAgent):
    """
    [Ω-BRAID] Topological Braiding of Agent Signals.
    """
    def __init__(self, weight: float = 4.8):
        super().__init__("BraidTopology", weight)
        self.strand_history = []
        
    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        if not CPP_CORE.is_loaded: return None
        
        raw_signals = kwargs.get("swarm_raw_signals", [])
        if not raw_signals: return None
        
        top_agents = sorted(raw_signals, key=lambda x: x.weight * x.confidence, reverse=True)[:5]
        current_strands = [s.signal for s in top_agents]
        
        if len(current_strands) < 2: return None
        
        self.strand_history.append(current_strands)
        if len(self.strand_history) > 20: self.strand_history.pop(0)
        
        if len(self.strand_history) < 10: return None
        
        try:
            flat_history = np.array(self.strand_history).T.flatten()
            braid_index = CPP_CORE.calculate_braid_index(flat_history, len(current_strands), len(self.strand_history))
            
            if abs(braid_index) > 0.5:
                direction = np.sign(braid_index)
                return AgentSignal(self.name, direction, min(0.99, abs(braid_index)), f"Topological Braid Locked (Index: {braid_index:.2f})", self.weight)
                
            return AgentSignal(self.name, 0.0, 0.1, f"Loose Braid Topology ({braid_index:.2f})", self.weight)
        except:
            return None

class KaldorHicksEfficiencyAgent(BaseAgent):
    """
    [Ω-ECON] Kaldor-Hicks Market Efficiency.
    """
    def __init__(self, weight: float = 3.5):
        super().__init__("KaldorHicksEfficiency", weight)
        
    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        if not CPP_CORE.is_loaded: return None
        
        raw_signals = kwargs.get("swarm_raw_signals", [])
        if not raw_signals: return None
        
        avg_signal = np.mean([s.signal for s in raw_signals])
        expected_alpha_points = abs(avg_signal) * snapshot.atr * 1.5 
        
        slippage_est = snapshot.spread * 0.2
        commission = snapshot.metadata.get("commission_points", 50.0)
        
        try:
            efficiency_ratio = CPP_CORE.calculate_kaldor_hicks_ratio(expected_alpha_points, slippage_est, snapshot.spread, commission)
            
            if efficiency_ratio > 2.0: 
                return AgentSignal(self.name, np.sign(avg_signal), 0.95, f"Kaldor-Hicks Efficient Entry (Ratio: {efficiency_ratio:.2f})", self.weight)
            elif efficiency_ratio < 0.8: 
                return AgentSignal(self.name, 0.0, 0.99, f"Kaldor-Hicks Social Waste ({efficiency_ratio:.2f})", self.weight)
                
            return AgentSignal(self.name, 0.0, 0.1, f"Market Friction OK ({efficiency_ratio:.2f})", self.weight)
        except:
            return None
