"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — GENESIS AGENTS (Phase Ω)                   ║
║     Inteligência Suprema (Nível 13): Inferência Causal, Raciocínio          ║
║     Contrafactual e Decomposição de Intencionalidade.                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
import math
from typing import Dict, Any, Optional
from core.consciousness.agents.base import BaseAgent, AgentSignal
from cpp.asi_bridge import CPP_CORE
from utils.decorators import catch_and_log

class CausalCounterfactualAgent(BaseAgent):
    """
    [Phase Ω-Genesis] Raciocínio Contrafactual (Inferência Causal).
    """
    def __init__(self, weight=4.2):
        super().__init__("CausalCounterfactual", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 30:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)
        volumes = np.array(candles_m1["tick_volume"], dtype=np.float64)
        
        vol_mean = np.mean(volumes)
        vol_std = np.std(volumes)
        organic_mask = volumes < (vol_mean + vol_std)
        
        if not np.any(organic_mask):
            return AgentSignal(self.name, 0.0, 0.0, "NO_ORGANIC_DATA", self.weight)
            
        organic_trend = np.polyval(np.polyfit(np.arange(len(closes))[organic_mask], closes[organic_mask], 1), len(closes)-1)
        
        current_price = closes[-1]
        divergence = current_price - organic_trend
        
        recent_vol = np.mean(volumes[-3:])
        vol_shock = recent_vol / (vol_mean + 1e-6)
        
        atr = snapshot.metadata.get("atr_m5", 20.0)
        
        signal = 0.0
        conf = 0.0
        reason = "CAUSAL_EQUILIBRIUM"
        
        if vol_shock > 2.5 and abs(divergence) > atr * 1.0:
            tick_velocity = snapshot.metadata.get("tick_velocity", 0.0)
            if tick_velocity < 20.0: 
                signal = -np.sign(divergence)
                conf = 0.92
                reason = f"CAUSAL_REVERSION"
            else:
                signal = np.sign(divergence)
                conf = 0.85
                reason = f"CAUSAL_MOMENTUM"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class IntentionalityDecompositionAgent(BaseAgent):
    """
    [Phase Ω-Genesis] Decomposição de Intencionalidade Institucional.
    """
    def __init__(self, weight=4.0):
        super().__init__("IntentDecomposition", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        orderflow = kwargs.get("orderflow_analysis", {})
        if not orderflow:
            return AgentSignal(self.name, 0.0, 0.0, "NO_ORDERFLOW", self.weight)
            
        imbalance = orderflow.get("imbalance", 0.0)
        absorption = orderflow.get("absorption", {})
        
        buy_abs = absorption.get("buy_absorption", 0.0)
        sell_abs = absorption.get("sell_absorption", 0.0)
        
        if imbalance > 0.6 and sell_abs > 0.7:
            return AgentSignal(self.name, -1.0, 0.95, "INTENT_DECEPTION_BEAR", self.weight)
        elif imbalance < -0.6 and buy_abs > 0.7:
            return AgentSignal(self.name, 1.0, 0.95, "INTENT_DECEPTION_BULL", self.weight)
            
        return AgentSignal(self.name, 0.0, 0.0, "INTENT_NEUTRAL", self.weight)

class SpectralInformationFluxAgent(BaseAgent):
    """
    [Ω-FLUX] Spectral Information Flux.
    """
    def __init__(self, weight: float = 4.5):
        super().__init__("SpectralInformationFlux", weight)
        
    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        if not CPP_CORE.is_loaded: return None
        
        history = snapshot.m1_closes[-64:]
        if len(history) < 32: return None
        
        try:
            flux = CPP_CORE.calculate_spectral_flux(history)
            
            if flux > 1.5:
                direction = np.sign(snapshot.price - history[-10])
                return AgentSignal(self.name, direction, min(0.99, flux / 3.0), f"Spectral Flux Ignition", self.weight)
            elif flux < 0.5:
                return AgentSignal(self.name, 0.0, 0.80, f"Spectral Energy Dissipation", self.weight)
                
            return None
        except:
            return None

class GeometricBerryCurvatureAgent(BaseAgent):
    """
    [Ω-BERRY] Quantum Geometric Tensor & Berry Curvature.
    """
    def __init__(self, weight: float = 4.7):
        super().__init__("GeometricBerryCurvature", weight)
        self.signal_history = []
        
    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        if not CPP_CORE.is_loaded: return None
        
        raw_signals = kwargs.get("swarm_raw_signals", [])
        if not raw_signals: return None
        
        top_agents = sorted(raw_signals, key=lambda x: x.weight, reverse=True)[:8]
        current_signals = [s.signal for s in top_agents]
        
        if len(current_signals) < 2: return None
        
        self.signal_history.append(current_signals)
        if len(self.signal_history) > 20: self.signal_history.pop(0)
        
        if len(self.signal_history) < 10: return None
        
        try:
            flat_signals = np.array(self.signal_history).T.flatten()
            curvature = CPP_CORE.calculate_berry_curvature(flat_signals, len(current_signals), len(self.signal_history))
            
            if abs(curvature) > 0.3:
                direction = np.sign(curvature)
                return AgentSignal(self.name, direction, min(0.99, abs(curvature) * 2.0), f"Geometric Singularity", self.weight)
                
            return None
        except:
            return None

class NeuralTransferEntropyAgent(BaseAgent):
    """
    [Ω-CAUSALITY] Neural Transfer Entropy (Information Theory).
    Calculates lead-lag information flow from ETH to BTC.
    If ETH is leaking information to BTC, we strike in ETH's direction.
    """
    def __init__(self, weight: float = 4.9):
        super().__init__("NeuralTransferEntropy", weight)
        self.eth_history = []
        self.btc_history = []
        
    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        if not CPP_CORE.is_loaded: return None
        
        eth_price = snapshot.metadata.get("macro_update_eth", 0.0) or snapshot.metadata.get("eth_price", 0.0)
        if eth_price == 0: return None
        
        self.eth_history.append(eth_price)
        self.btc_history.append(snapshot.price)
        
        if len(self.eth_history) > 50:
            self.eth_history.pop(0)
            self.btc_history.pop(0)
            
        if len(self.eth_history) < 30: return None
        
        try:
            te_eth_to_btc = CPP_CORE.calculate_transfer_entropy(np.array(self.eth_history), np.array(self.btc_history), len(self.eth_history), bins=10)
            
            if te_eth_to_btc > 0.15: # High Information Flow
                eth_trend = np.sign(self.eth_history[-1] - self.eth_history[-10])
                return AgentSignal(self.name, eth_trend, min(0.99, te_eth_to_btc * 4.0), f"ETH Information Leakage (TE={te_eth_to_btc:.2f})", self.weight)
                
            return None
        except:
            return None

class KramersKronigDispersiveAgent(BaseAgent):
    """
    [Ω-DISPERSION] Kramers-Kronig Dispersive Relation.
    Detects causality breakdown when volatility (imaginary) decouples from price move (real).
    Predicts snap-backs in over-extended dispersive states.
    """
    def __init__(self, weight: float = 4.4):
        super().__init__("KramersKronigDispersive", weight)
        
    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        if not CPP_CORE.is_loaded: return None
        
        history = snapshot.m1_closes[-20:]
        if len(history) < 15: return None
        
        try:
            returns = np.diff(np.log(history + 1e-9))
            susceptibility = CPP_CORE.calculate_kramers_kronig_anomaly(returns)
            
            # Ratio < 0.1 means huge volatility with almost zero real price move (Absorption/Exhaustion)
            if susceptibility < 0.1:
                direction = -np.sign(snapshot.price - history[0])
                return AgentSignal(self.name, direction, 0.94, f"Dispersive Causality Breakdown (Ratio={susceptibility:.3f})", self.weight)
                
            return None
        except:
            return None
