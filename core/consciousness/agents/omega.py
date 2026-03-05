"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — OMEGA AGENTS (Phase 10)                     ║
║     Vacuum, TimeWarp, Harmonic, Reflexivity, BlackSwan                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import Optional

from core.consciousness.agents.base import AgentSignal, BaseAgent
from config.omega_params import OMEGA
from utils.decorators import catch_and_log


class LiquidationVacuumAgent(BaseAgent):
    """
    Detecta quando a liquidez é rapidamente removida do book e o spread alarga
    imediatamente antes de um movimento violento (Liquidation Cascade / Vacuum).
    """
    def __init__(self, weight: float = 1.5):
        super().__init__("LiquidationVacuumAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        symbol_info = snapshot.symbol_info
        if not symbol_info:
            return None

        spread = symbol_info.get("spread", 0)
        avg_spread = OMEGA.get("normal_spread", 20)

        signal = 0.0
        reason = "Normal liquidity."
        conf = 0.0

        if spread > avg_spread * 3:
            ticks = snapshot.recent_ticks
            if len(ticks) > 10:
                last_price = ticks[-1]["bid"]
                first_price = ticks[0]["bid"]
                if last_price > first_price:
                    signal = 0.8
                    reason = f"Liquidity Vacuum UP ({spread} spr, Squeeze imminent)"
                    conf = 0.9
                else:
                    signal = -0.8
                    reason = f"Liquidity Vacuum DOWN ({spread} spr, Squeeze imminent)"
                    conf = 0.9

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class TimeWarpAgent(BaseAgent):
    """
    Analisa a aceleração/desaceleração do tempo entre os ticks.
    Alta frequência = Urgência institucional = Rompimento Direcional.
    """
    def __init__(self, weight: float = 1.1):
        super().__init__("TimeWarpAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        ticks = snapshot.recent_ticks
        if len(ticks) < 100:
            return None

        try:
            time_start = ticks[0]["time_msc"]
            time_end = ticks[-1]["time_msc"]
            dt_seconds = (time_end - time_start) / 1000.0
        except (IndexError, KeyError):
            return None

        if dt_seconds <= 0:
            return None

        tps = len(ticks) / dt_seconds

        signal = 0.0
        reason = f"Normal Time Velocity (TPS: {tps:.1f})"
        conf = 0.1

        if tps > 50:
            bid_end = ticks[-1]["bid"]
            bid_start = ticks[0]["bid"]
            if bid_end > bid_start:
                signal = 0.85
                reason = f"Time Warp UP (Urgent Buying, TPS: {tps:.1f})"
                conf = 0.85
            elif bid_end < bid_start:
                signal = -0.85
                reason = f"Time Warp DOWN (Urgent Selling, TPS: {tps:.1f})"
                conf = 0.85

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class HarmonicResonanceAgent(BaseAgent):
    """
    Detecta simetria cíclica e ressonância matemática (conceitos de Tesla 3-6-9).
    Aproximado comparando comprimentos de pernas de onda recentes.
    """
    def __init__(self, weight: float = 0.8):
        super().__init__("HarmonicResonanceAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        closes = snapshot.m5_closes
        if len(closes) < 30:
            return None

        w1 = (closes[-1] - closes[-4]) / closes[-4]
        w2 = (closes[-5] - closes[-8]) / closes[-8]
        w3 = (closes[-9] - closes[-12]) / closes[-12]

        signal = 0.0
        reason = "Sem ressonância"
        conf = 0.0

        if w1 * w2 < 0 and w2 * w3 < 0:
            if abs(w1) < abs(w2) < abs(w3):
                reason = "Resonance Compression (Coiling)"
                conf = 0.6

        if w1 > 0 and w2 > 0 and w3 > 0:
            signal = 0.6; conf = 0.5; reason = "Triple Harmonic Impulse UP"
        elif w1 < 0 and w2 < 0 and w3 < 0:
            signal = -0.6; conf = 0.5; reason = "Triple Harmonic Impulse DOWN"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class ReflexivityAgent(BaseAgent):
    """
    Teoria de George Soros: O mercado finta. Se os preços quebram um nível
    importante mas o orderflow é paradoxal, há trap.
    """
    def __init__(self, weight: float = 1.3):
        super().__init__("ReflexivityAgent", weight)
        self.needs_orderflow = True

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, orderflow_analysis: dict = None, **kw) -> Optional[AgentSignal]:
        if not orderflow_analysis:
            return None

        closes = snapshot.m1_closes
        if len(closes) < 20:
            return None

        recent_high = max(closes[-20:-1])
        recent_low = min(closes[-20:-1])
        current = closes[-1]

        breakout_up = current > recent_high
        breakout_down = current < recent_low

        delta = orderflow_analysis.get("delta", 0.0)

        signal = 0.0
        reason = "No Reflexive Trap"
        conf = 0.0

        if breakout_up and delta < -5.0:
            signal = -0.9; conf = 0.95
            reason = "Reflexive FAKE-OUT Bull Trap (Price breaking up, Delta dumping)"
        elif breakout_down and delta > 5.0:
            signal = 0.9; conf = 0.95
            reason = "Reflexive FAKE-OUT Bear Trap (Price breaking down, Delta pumping)"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class BlackSwanAgent(BaseAgent):
    """
    Avalia o risco de tail event usando Kurtosis e Volatilidade Anômala Extrema.
    Se o sinal piscar vermelho, significa "saia do mercado".
    """
    def __init__(self, weight: float = 2.0):
        super().__init__("BlackSwanAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        from scipy.stats import kurtosis

        closes = snapshot.m1_closes
        if len(closes) < 100:
            return None

        returns = np.diff(closes) / closes[:-1]

        k = kurtosis(returns, fisher=False)
        stdev = np.std(returns)
        current_ret = abs(returns[-1])

        signal = 0.0
        reason = "Normal Distribution"
        conf = 0.0

        if k > 10.0 and current_ret > stdev * 4:
            reason = f"BLACK SWAN ALERT! Kurtosis {k:.1f}, 4Sigma Move!"
            signal = 1.0 if returns[-1] > 0 else -1.0
            conf = 1.0

        return AgentSignal(self.name, signal, conf, reason, self.weight)
