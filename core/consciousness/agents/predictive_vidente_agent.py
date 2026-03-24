import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal
from utils.logger import ASILogger
import time 

logger = ASILogger("PredictiveVidenteAgent")

class PredictiveVidenteAgent(BaseAgent):
    """
    Project Vidente (Ω-9)
    Simulates short-term 3-minute forward stochastic paths using Brownian jumps.
    If probability of ruin > 85%, emits an aggressive VETO signal to protect the swarm.
    """
    def __init__(self, weight=5.5):
        super().__init__("PredictiveVidenteAgent")
        self.weight = weight
        self._last_calc_time = 0
        self._last_log_time = 0
        self._last_context = ""
        self._last_signal_obj = AgentSignal(self.name, 0.0, 0.0, "Aguardando Init", self.weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        current_time = time.time()
        if current_time - self._last_calc_time < 1.0:
            return getattr(self, '_last_signal_obj', AgentSignal(self.name, 0.0, 0.0, "Cooldown", self.weight))
            
        price = snapshot.price
        atr = snapshot.atr
        regime = getattr(snapshot, 'regime', "UNKNOWN")
        regime_str = str(regime).upper()
        
        mu = 0.0
        if "BULL" in regime_str: mu = 0.00015
        elif "BEAR" in regime_str: mu = -0.00015
        
        sigma = (atr / price) * 0.5 
        if sigma <= 0 or price <= 0: return AgentSignal(self.name, 0.0, 0.0, "Sigma 0", self.weight)
        
        paths = 100
        steps = 180 
        dt = 1.0
        
        Z = np.random.standard_normal((paths, steps))
        dS = mu * dt + sigma * np.sqrt(dt) * Z
        log_returns = np.cumsum(dS, axis=1)
        
        simulated_prices = price * np.exp(log_returns)
        final_prices = simulated_prices[:, -1]
        
        ruin_barrier_down = price - atr
        ruin_barrier_up = price + atr
        
        bull_ruin = np.sum(final_prices < ruin_barrier_down) / paths
        bear_ruin = np.sum(final_prices > ruin_barrier_up) / paths
        
        signal = 0.0
        reason = "Amanhã é incerto (Stochastic Safe)"
        
        if bull_ruin > 0.85 and bear_ruin < 0.20:
            signal = -0.99
            reason = "90%+ chance of SL collapse in 3m. VETOING longs."
            self._log_vision("BEAR_STRIKE", reason, signal)
            
        elif bear_ruin > 0.85 and bull_ruin < 0.20:
            signal = 0.99
            reason = "90%+ chance of UPWARD explosion in 3m. Igniting longs."
            self._log_vision("BULL_EXPLOSION", reason, signal)
            
        sig_obj = AgentSignal(self.name, signal, abs(signal), reason, self.weight)
        self._last_signal_obj = sig_obj
        self._last_calc_time = current_time
        return sig_obj

    def _log_vision(self, context: str, msg: str, signal: float):
        current = time.time()
        if current - self._last_log_time > 15.0 or self._last_context != context:
            logger.omega(f"👁️‍🗨️ [VIDENTE Ω-9] {context} | S:{signal:+.2f} | {msg}")
            self._last_log_time = current
            self._last_context = context
