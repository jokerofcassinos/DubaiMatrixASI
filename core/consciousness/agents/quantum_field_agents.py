"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — QUANTUM FIELD AGENTS (Phase Ω)              ║
║     Inteligência Suprema (Nível 27): Fluxo de Ricci, Gargalo de Informação ║
║     e Teoria de Campo Emergente.                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import Optional, Dict, Any
from core.consciousness.agents.base import BaseAgent, AgentSignal
from cpp.asi_bridge import CPP_CORE
from utils.decorators import catch_and_log

class RicciFlowAgent(BaseAgent):
    """
    [Phase Ω-Singularity] Fluxo de Ricci (Geometria Diferencial).
    """
    def __init__(self, weight=4.8):
        super().__init__("RicciFlow", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 20:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)[-20:]
        v = np.diff(closes)
        a = np.diff(v)
        k = a / (1 + v[:-1]**2)**1.5
        current_k = k[-1]

        signal = 0.0
        conf = 0.0
        reason = "FLAT_MANIFOLD"

        if abs(current_k) > 0.05:
            signal = -np.sign(current_k)
            conf = min(0.98, abs(current_k) * 10.0)
            reason = f"RICCI_SMOOTHING_FORCE (K={current_k:.4f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class InformationBottleneckAgent(BaseAgent):
    """
    [Phase Ω-Singularity] Princípio do Gargalo de Informaçaõ (Tishby).
    """
    def __init__(self, weight=4.5):
        super().__init__("InformationBottleneck", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        entropy = snapshot.metadata.get("tick_entropy", 0.5)
        velocity = snapshot.metadata.get("tick_velocity", 0.0)
        compression_ratio = abs(velocity) / (entropy + 1e-6)

        signal = 0.0
        conf = 0.0
        reason = "DIFFUSE_INFORMATION"

        if compression_ratio > 150.0:
            signal = np.sign(velocity)
            conf = 0.96
            reason = f"BOTTLENECK_COMPRESSION_OPTIMAL (Ratio={compression_ratio:.1f})"
        elif entropy > 0.85 and abs(velocity) < 5.0:
            signal = 0.0
            conf = 0.0
            reason = "INFORMATION_STALL (High Entropy)"

        return AgentSignal(self.name, signal, conf, reason, self.weight)

class DiracFermiPressureAgent(BaseAgent):
    """
    [Ω-FERMI] Dirac-Fermi Surface Pressure Agent.
    """
    def __init__(self, weight: float = 4.3):
        super().__init__("DiracFermiPressure", weight)
        
    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        if not CPP_CORE.is_loaded: return None
        book = snapshot.book
        if not book: return None
        
        bid_vols = np.array([item["volume"] for item in book.get("bids", [])[:10]], dtype=np.float64)
        ask_vols = np.array([item["volume"] for item in book.get("asks", [])[:10]], dtype=np.float64)
        
        if len(bid_vols) < 5 or len(ask_vols) < 5: return None
        
        try:
            atr_m1 = snapshot.indicators.get("M1_atr_14", [10.0])
            temp = atr_m1[-1] / snapshot.price * 1000
            
            p_bid = CPP_CORE.calculate_fermi_pressure(bid_vols, temp)
            p_ask = CPP_CORE.calculate_fermi_pressure(ask_vols, temp)
            
            tick_vel = snapshot.metadata.get("tick_velocity", 0.0)
            
            if tick_vel > p_ask * 1.5:
                return AgentSignal(self.name, 1.0, 0.90, f"Fermi Pressure Breached (UP)", self.weight)
            elif tick_vel < -p_bid * 1.5:
                return AgentSignal(self.name, -1.0, 0.90, f"Fermi Pressure Breached (DOWN)", self.weight)
                
            return None
        except:
            return None

class ChernSimonsTopologicalAgent(BaseAgent):
    """
    [Ω-CHERN] Chern-Simons Topological Protection Index.
    """
    def __init__(self, weight: float = 4.9):
        super().__init__("ChernSimonsTopological", weight)
        self.history_x = []
        self.history_y = []
        self.history_z = []
        
    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        if not CPP_CORE.is_loaded: return None
        
        x = snapshot.price
        y = snapshot.metadata.get("tick_velocity", 0.0)
        z = snapshot.metadata.get("tick_entropy", 0.5)
        
        self.history_x.append(x)
        self.history_y.append(y)
        self.history_z.append(z)
        
        if len(self.history_x) > 30:
            self.history_x.pop(0)
            self.history_y.pop(0)
            self.history_z.pop(0)
            
        if len(self.history_x) < 15: return None
        
        try:
            cs = CPP_CORE.calculate_chern_simons_index(
                np.array(self.history_x), 
                np.array(self.history_y), 
                np.array(self.history_z)
            )
            
            if abs(cs) > 5.0:
                return AgentSignal(self.name, np.sign(cs), min(0.99, abs(cs) / 10.0), f"Topological Protection (CS={cs:.2f})", self.weight)
                
            return None
        except:
            return None
