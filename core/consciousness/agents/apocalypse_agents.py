"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — APOCALYPSE AGENTS (Phase Ω)                 ║
║     Inteligência Predatória Hostil: Dark Pools, Gamma Squeezes e            ║
║     Arbitragem de Microestrutura (Ataque a Market Makers).                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal

class DarkPoolArbitrageAgent(BaseAgent):
    """
    [Phase Ω-Apocalypse] Dark Pool Arbitrage Estimator.
    """
    def __init__(self, weight=3.5):
        super().__init__("DarkPoolArbitrage", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles = snapshot.candles.get("M1")
        if not candles or len(candles["close"]) < 30:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles["close"], dtype=np.float64)
        volumes = np.array(candles["tick_volume"], dtype=np.float64)
        highs = np.array(candles["high"], dtype=np.float64)
        lows = np.array(candles["low"], dtype=np.float64)

        recent_vol = np.mean(volumes[-5:])
        hist_vol = np.mean(volumes[-30:-5])

        recent_range = np.mean(highs[-5:] - lows[-5:])
        hist_range = np.mean(highs[-30:-5] - lows[-30:-5]) + 1e-6

        vol_anomaly = recent_vol / (hist_vol + 1e-6)
        range_anomaly = recent_range / hist_range

        signal = 0.0
        conf = 0.0
        reason = "NO_DARK_POOL_ACTIVITY"

        if vol_anomaly > 3.0 and range_anomaly < 0.8:
            trend = closes[-1] - closes[-15]
            if trend > 0:
                signal = -1.0
                conf = 0.95
                reason = f"DARK_POOL_DISTRIBUTION (Vol={vol_anomaly:.1f}x, Rng={range_anomaly:.1f}x)"
            else:
                signal = 1.0
                conf = 0.95
                reason = f"DARK_POOL_ACCUMULATION (Vol={vol_anomaly:.1f}x, Rng={range_anomaly:.1f}x)"
        elif vol_anomaly < 0.5 and range_anomaly > 3.0:
            direction = np.sign(closes[-1] - closes[-3])
            signal = -direction 
            conf = 0.85
            reason = f"ILLIQUID_STOP_HUNT_DETECTED (Vol={vol_anomaly:.1f}x, Rng={range_anomaly:.1f}x)"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class OptionGammaSqueezeAgent(BaseAgent):
    """
    [Phase Ω-Apocalypse] Option Gamma Squeeze Extrapolator.
    """
    def __init__(self, weight=3.8):
        super().__init__("GammaSqueeze", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m5 = snapshot.candles.get("M5")
        if not candles_m5 or len(candles_m5["close"]) < 20:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m5["close"], dtype=np.float64)
        atr = snapshot.indicators.get("M5_atr_14", [50.0])[-1]

        p1 = closes[-1]
        p2 = closes[-3]
        p3 = closes[-6]

        v_short = p1 - p2
        v_long = p2 - p3

        signal = 0.0
        conf = 0.0
        reason = "NORMAL_DELTA_HEDGE"

        if v_short > atr * 2.0 and v_short > v_long * 3.0:
            signal = 1.0
            conf = 0.95
            reason = f"BULLISH_GAMMA_SQUEEZE (Acc={v_short/max(1, v_long):.1f}x)"
        elif v_short < -atr * 2.0 and v_short < v_long * 3.0:
            signal = -1.0
            conf = 0.95
            reason = f"BEARISH_GAMMA_SQUEEZE (Acc={v_short/min(-1, v_long):.1f}x)"

        return AgentSignal(self.name, signal, conf, reason, self.weight)

class TCellWeaponizedAgent(BaseAgent):
    """
    [Ω-WEAPONIZATION] Transforma o Epistemic Memory (Defensivo) em Arma Ofensiva.
    Se a situação atual é idêntica a um erro passado, opera na direção oposta com fúria.
    """
    def __init__(self, weight: float = 5.0):
        super().__init__("TCellWeaponizedAgent", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        # Recuperamos matches de memória tóxica passados pelo Brain/Swarm
        matches = kwargs.get("toxic_memory_matches", [])
        
        if not matches:
            return AgentSignal(self.name, 0.0, 0.0, "NO_PATHOGEN_DETECTED", self.weight)
            
        # O sistema ia errar de novo. Invertemos a mão com confiança absoluta.
        past_failed_direction = matches[0].get("direction", "UNKNOWN")
        
        if past_failed_direction == "BUY":
            return AgentSignal(self.name, -1.0, 1.0, "OFFENSIVE_IMMUNITY: FADING_PAST_BULL_TRAP", self.weight)
        elif past_failed_direction == "SELL":
            return AgentSignal(self.name, 1.0, 1.0, "OFFENSIVE_IMMUNITY: FADING_PAST_BEAR_TRAP", self.weight)
            
        return AgentSignal(self.name, 0.0, 0.0, "PATHOGEN_NEUTRAL", self.weight)
