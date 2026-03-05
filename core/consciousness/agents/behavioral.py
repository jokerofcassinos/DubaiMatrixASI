"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — BEHAVIORAL & GAME THEORY AGENTS (Phase 15)  ║
║     Agentes baseados em Teoria dos Jogos, Psicologia Comportamental,       ║
║     e modelagem de adversários algorítmicos.                                ║
║                                                                              ║
║     "Nós modelamos o comportamento dos OUTROS BOTS no book."                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import Optional

from core.consciousness.agents.base import AgentSignal, BaseAgent
from utils.decorators import catch_and_log
from cpp.asi_bridge import CPP_CORE


class RetailPsychologyAgent(BaseAgent):
    """
    Psicologia Comportamental de Massa:
    Identifica comportamento de varejo "previsível":
    - Números redondos atraem ordens limit (BTC 100k, 95k, 90k)
    - Retardo de confirmação: o varejo entra DEPOIS do rompimento (late entry)
    - Panic selling em candles vermelhas grandes sem análise
    
    O agente FADA o varejo: se o varejo está comprando (late), vendemos. Se está em
    pânico, compramos.
    """
    def __init__(self, weight: float = 1.4):
        super().__init__("RetailPsychologyAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        closes = snapshot.m1_closes
        if len(closes) < 20:
            return None

        price = snapshot.price

        # Detectar proximidade a número redondo (magneto do varejo)
        round_levels = [int(price / 1000) * 1000 + i * 1000 for i in range(-2, 3)]
        min_dist = min(abs(price - rl) / price * 100 for rl in round_levels)

        signal = 0.0
        reason = "Retail neutral"
        conf = 0.0

        # Se recentemente teve candle violento (>0.5% em M1) e agora está voltando,
        # indica panic retail que já foi liquidado
        recent_return = (closes[-1] - closes[-3]) / closes[-3] * 100
        reversion = closes[-1] - closes[-2]

        if recent_return < -0.5 and reversion > 0:
            signal = 0.6
            conf = 0.7
            reason = f"Retail Panic Absorbed (Drop {recent_return:.2f}%, now reversing)"
        elif recent_return > 0.5 and reversion < 0:
            signal = -0.6
            conf = 0.7
            reason = f"Retail FOMO Exhausted (Pump {recent_return:.2f}%, now reversing)"

        # Boost se perto de número redondo
        if min_dist < 0.3:
            conf = min(1.0, conf + 0.2)
            reason += f" | Near Round ({price:.0f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class GameTheoryNashAgent(BaseAgent):
    """
    Equilíbrio de Nash Aplicado:
    Se ambos os lados (compradores e vendedores) estão num impasse de liquidez,
    o primeiro a "sair" do equilíbrio vence. 
    Nós calculamos a "estabilidade do Nash" e quando ela começa a falhar,
    sabemos que um lado vai ceder.
    """
    def __init__(self, weight: float = 1.5):
        super().__init__("GameTheoryNashAgent", weight)
        self.needs_orderflow = True

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, orderflow_analysis: dict = None, **kw) -> Optional[AgentSignal]:
        if not orderflow_analysis:
            return None

        delta = orderflow_analysis.get("delta", orderflow_analysis.get("cumulative_delta", 0.0))
        imbalance = orderflow_analysis.get("imbalance_ratio", orderflow_analysis.get("order_imbalance", 0.0))

        # Equilíbrio de Nash = delta ≈ 0 E imbalance ≈ 0 (ninguém ganha)
        signal = 0.0
        reason = "Nash Equilibrium Active"
        conf = 0.0

        nash_stability = 1.0 - (abs(delta) * 0.1 + abs(imbalance))

        if nash_stability < 0.3:
            # Nash está quebrando — quem tem momentum vence
            if delta > 0:
                signal = 0.75
                conf = 0.85
                reason = f"Nash BREAKDOWN — Buyers dominating (delta={delta:.1f})"
            else:
                signal = -0.75
                conf = 0.85
                reason = f"Nash BREAKDOWN — Sellers dominating (delta={delta:.1f})"
        elif nash_stability > 0.8:
            reason = f"Nash Stable — Stalemate (stability={nash_stability:.2f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class CppAcceleratedFractalAgent(BaseAgent):
    """
    Dimensão Fractal do preço calculada em C++ puro (50x speedup).
    Substitui o FractalAgent Python para séries grandes.
    """
    def __init__(self, weight: float = 0.9):
        super().__init__("CppFractalAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        closes = snapshot.m5_closes
        if len(closes) < 50:
            return None

        # USAR C++ PARA O CÁLCULO PESADO
        fd = CPP_CORE.fractal_dimension(np.array(closes, dtype=np.float64), 64)

        signal = 0.0
        reason = f"Fractal Dim (C++) = {fd:.3f}"
        conf = 0.3

        if fd < 1.3:
            direction = 1.0 if closes[-1] > closes[-10] else -1.0
            signal = direction * 0.6
            conf = 0.7
            reason = f"FD={fd:.3f}:SMOOTH_TREND (C++ Accelerated)"
        elif fd > 1.7:
            signal = 0.0
            conf = 0.8
            reason = f"FD={fd:.3f}:NOISY_CHAOTIC — Avoid (C++ Accel)"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class CppTickEntropyAgent(BaseAgent):
    """
    Entropia de Shannon sobre retornos de ticks calculada em C++ (100x speedup).
    Upgrade do InformationEntropyAgent usando engine compilado.
    """
    def __init__(self, weight: float = 1.7):
        super().__init__("CppTickEntropyAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        ticks = snapshot.recent_ticks
        if len(ticks) < 100:
            return None

        try:
            bids = np.array([t["bid"] for t in ticks[-200:]], dtype=np.float64)
        except (KeyError, TypeError):
            return None

        # USAR C++ PARA O CÁLCULO
        ent = CPP_CORE.tick_entropy(bids, bins=10)

        signal = 0.0
        reason = f"Tick Entropy (C++) = {ent:.2f} bits"
        conf = 0.0

        if ent < 1.0:
            direction = 1.0 if bids[-1] > bids[0] else -1.0
            signal = direction * 0.85
            conf = 0.95
            reason = f"DETERMINISTIC ({ent:.2f} bits) — Institutional Order Injection (C++ Accel)"
        elif ent > 2.8:
            signal = 0.0
            conf = 1.0
            reason = f"CHAOTIC ({ent:.2f} bits) — Pure Noise (C++ Accel)"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class CppCrossScaleAgent(BaseAgent):
    """
    Correlação Cross-Scale M1↔M5 calculada em C++.
    Se a correlação é ≈1.0, TODAS as escalas temporais concordam.
    """
    def __init__(self, weight: float = 1.6):
        super().__init__("CppCrossScaleAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        m1 = snapshot.candles.get("M1", {}).get("close", [])
        m5 = snapshot.candles.get("M5", {}).get("close", [])

        if len(m1) < 10 or len(m5) < 10:
            return None

        # USAR C++ PARA A CORRELAÇÃO
        corr = CPP_CORE.cross_scale_correlation(
            np.array(m1, dtype=np.float64),
            np.array(m5, dtype=np.float64)
        )

        signal = 0.0
        reason = f"Cross-Scale Corr (C++) = {corr:.3f}"
        conf = 0.0

        if corr > 0.85:
            direction = 1.0 if m1[-1] > m1[-3] else -1.0
            signal = direction * 0.8
            conf = 0.9
            reason = f"HIGH Cross-Scale Alignment ({corr:.3f}) — Trend Amplified (C++ Accel)"
        elif corr < -0.5:
            signal = 0.0
            conf = 0.7
            reason = f"NEGATIVE Cross-Scale ({corr:.3f}) — Timeframes conflicting"

        return AgentSignal(self.name, signal, conf, reason, self.weight)
