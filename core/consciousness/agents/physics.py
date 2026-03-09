"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — PHYSICS & KINEMATICS AGENTS (Phase 14)      ║
║     Transmutação de conceitos da Física (Fluidodinâmica, Eletromagnetismo,  ║
║     Termodinâmica) para o Order Book e Price Action.                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import Optional

from core.consciousness.agents.base import AgentSignal, BaseAgent
from utils.decorators import catch_and_log
from cpp.asi_bridge import CPP_CORE


def _find_swing_highs_lows(highs, lows, closes, lookback: int = 5):
    """Fallback Python swing detection."""
    # ... (remains for reference if CPP_CORE fails, but agents will use C++)
    return CPP_CORE.find_swings(np.array(highs), np.array(lows), lookback)


class NavierStokesFluidAgent(BaseAgent):
    """
    Equação de Navier-Stokes (Fluidodinâmica) transposta para o DOM.
    Trata Bids e Asks como dois fluidos com viscosidade diferente se chocando.
    Áreas sem liquidez são "vácuos de baixa pressão". O preço flui 
    inevitavelmente para onde a densidade do fluido oposto é menor.
    """
    def __init__(self, weight: float = 1.6):
        super().__init__("NavierStokesFluidAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        book = snapshot.metadata.get("book")
        if not book:
            return None

        bids = book.get("bids", [])
        asks = book.get("asks", [])
        if len(bids) < 5 or len(asks) < 5:
            return None

        # Densidade e Pressão via C++ (Navier-Stokes)
        bid_vols = np.array([b.get("volume", 0) for b in bids[:5]], dtype=np.float64)
        ask_vols = np.array([a.get("volume", 0) for a in asks[:5]], dtype=np.float64)
        
        # ratio: balance bid/ask, pressure: turbulência acumulada
        ratio, pressure = CPP_CORE.navier_stokes_pressure(bid_vols, ask_vols)

        # Pressão cinética = Velocidade do tape 
        ticks = snapshot.recent_ticks
        if len(ticks) < 10:
            return None

        time_delta = (ticks[-1].get("time_msc", 1) - ticks[0].get("time_msc", 0)) / 1000.0
        if time_delta <= 0: return None
        kinetic_pressure = len(ticks) / time_delta # Ticks per sec

        signal = 0.0
        reason = "Fluid in Equilibrium"
        conf = 0.0

        # [Phase 51] Fluid Dynamics Reversal Detection
        # Se a pressão (turbulência) está extrema, o fluido vai 'explodir' na direção do vácuo.
        if pressure > 0.8: # Alta turbulência
            conf = 0.90
            if ratio > 2.5:
                signal = 0.85
                reason = f"Turbulent UP-FLOW (Ratio {ratio:.1f}, Pres {pressure:.2f})"
            elif ratio < 0.4:
                signal = -0.85
                reason = f"Turbulent DOWN-FLOW (Ratio {ratio:.1f}, Pres {pressure:.2f})"
        elif kinetic_pressure > 15.0: # Fluxo rápido mas laminar
            if ratio > 1.5:
                signal = 0.6
                conf = 0.75
                reason = f"Kinetic UP-STREAM (Ratio {ratio:.1f}, K-Pres {kinetic_pressure:.1f})"
            elif ratio < 0.66:
                signal = -0.6
                conf = 0.75
                reason = f"Kinetic DOWN-STREAM (Ratio {ratio:.1f}, K-Pres {kinetic_pressure:.1f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class MagneticPolarizationAgent(BaseAgent):
    """
    Eletromagnetismo. Identifica "Polos Magnéticos" no gráfico.
    Níveis de preço onde bilhões de dólares trocaram de mãos no passado
    criam um campo gravitacional/magnético. O preço é atraído pelo polo
    e depois violentamente repelido ao tocá-lo.
    """
    def __init__(self, weight: float = 1.4):
        super().__init__("MagneticPolarizationAgent", weight)
        self.poles = []

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        # Para simplificar, usamos o Volume Profile Peak (POC - Point of Control) 
        # como o Polo Magnético Supermassivo
        indicators = snapshot.indicators
        poc = indicators.get("M15_volume_poc")
        current_price = snapshot.price

        if poc is None or current_price <= 0:
            return None

        dist = (current_price - poc) / poc * 100

        signal = 0.0
        reason = "Outside magnetic field"
        conf = 0.0

        if abs(dist) < 0.05:
            # Preço tocou o polo. Efeito de repulsão eletromagnética.
            # Se bateu vindo de cima, repele pra cima.
            closes = snapshot.m1_closes
            if len(closes) > 5:
                if closes[-5] > poc: 
                    signal = 0.7 # Ricochete UP
                    reason = f"Magnetic Repulsion UP (Touched North Pole @ {poc:.0f})"
                else:
                    signal = -0.7 # Ricochete DOWN
                    reason = f"Magnetic Repulsion DOWN (Touched South Pole @ {poc:.0f})"
                conf = 0.8

        elif abs(dist) < 0.3:
            # Sendo atraído pelo polo (Gravitação)
            signal = -np.sign(dist) * 0.4
            conf = 0.6
            reason = f"Magnetic Attraction towards {poc:.0f} (Dist={dist:.2f}%)"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class ThermalEquilibriumAgent(BaseAgent):
    """
    Termodinâmica. Mercado como sistema fechado trocando calor.
    RSI Extremo = Superaquecimento (Entalpia máxima).
    Quando a 1ª Derivada da temperatura (mudança de RSI) vira zero no pico,
    o sistema cede ao ambiente (Mean Reversion inevitável).
    """
    def __init__(self, weight: float = 1.2):
        super().__init__("ThermalEquilibriumAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        rsi = snapshot.indicators.get("M5_rsi_14")
        if rsi is None or len(rsi) < 5:
            return None

        current_heat = rsi[-1]
        prev_heat = rsi[-2]
        delta_heat = current_heat - prev_heat

        signal = 0.0
        reason = f"Thermal Stable (Temp: {current_heat:.1f})"
        conf = 0.0

        if current_heat > 85 and delta_heat <= 0:
            signal = -0.8
            conf = 0.9
            reason = f"THERMAL OVERLOAD ({current_heat:.1f}) — Heat Dissipation (Short)"
        elif current_heat < 15 and delta_heat >= 0:
            signal = 0.8
            conf = 0.9
            reason = f"CRYOGENIC FREEZE ({current_heat:.1f}) — Heat Absorption (Long)"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class QuantumTunnelingAgent(BaseAgent):
    """
    Efeito Túnel Quântico. 
    Uma barreira de suporte/resistência massiva atua como uma barreira de potencial.
    Classicamente o preço não passaria (Bate e volta). Mas se a variância 
    microestrutural for hiperativa logo na borda do muro, o preço "tunela" pro outro lado
    (Slippage violento / Rompimento fantasma).
    """
    def __init__(self, weight: float = 1.9):
        super().__init__("QuantumTunnelingAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        sr = snapshot.indicators.get("M5_sr_levels")
        if not sr:
            return None

        price = snapshot.price
        ticks = snapshot.recent_ticks
        if len(ticks) < 50:
            return None

        # Medir Variância microestrutural via C++
        bids = np.array([t.get("bid", 0) for t in ticks[-50:]], dtype=np.float64)
        micro_var = CPP_CORE.calc_micro_variance(bids)

        signal = 0.0
        reason = "No Quantum Barrier"
        conf = 0.0

        for r_price, touches in sr.get("resistance", []):
            dist = (r_price - price) / price * 100
            if 0 < dist < 0.05 and touches >= 3:
                # Na borda da resistência dura
                if micro_var > np.mean(price)*0.0001: # Alta agitação vibracional na borda
                    signal = 0.9 
                    conf = 0.95
                    reason = f"QUANTUM TUNNELING UP IMMINENT (High Micro-Variance at barrier {r_price:.0f})"
                return AgentSignal(self.name, signal, conf, reason, self.weight)

        for s_price, touches in sr.get("support", []):
            dist = (price - s_price) / price * 100
            if 0 < dist < 0.05 and touches >= 3:
                # Na borda do suporte duro
                if micro_var > np.mean(price)*0.0001:
                    signal = -0.9
                    conf = 0.95
                    reason = f"QUANTUM TUNNELING DOWN IMMINENT (High Micro-Variance at barrier {s_price:.0f})"
                return AgentSignal(self.name, signal, conf, reason, self.weight)

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class DopplerShiftAgent(BaseAgent):
    """
    Efeito Doppler nas Ondas de Fluxo de Ordens.
    Se a onda de compra está se comprimindo no tempo (maior frequência = Blueshift), 
    o comprador institucional está acelerando rumo ao topo do book. 
    Se está se afastando (Redshift), exaustão.
    """
    def __init__(self, weight: float = 1.5):
        super().__init__("DopplerShiftAgent", weight)
        self.needs_orderflow = True

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, orderflow_analysis: dict = None, **kw) -> Optional[AgentSignal]:
        if not orderflow_analysis:
            return None

        # Frequência de agressão do comprador vs vendedor
        buy_freq = orderflow_analysis.get("buy_frequency_hz", 0) # Trades/sec
        sell_freq = orderflow_analysis.get("sell_frequency_hz", 0)

        signal = 0.0
        conf = 0.0
        reason = "No Doppler Shift"

        if buy_freq > 0 and sell_freq > 0:
            ratio = buy_freq / sell_freq

            if ratio > 4.0:
                signal = 0.75
                conf = 0.8
                reason = f"BLUESHIFT BUY WAVES (Freq Ratio {ratio:.1f}x) — Institutional acceleration"
            elif ratio < 0.25:
                signal = -0.75
                conf = 0.8
                reason = f"REDSHIFT SELL WAVES (Freq Ratio {ratio:.1f}x) — Institutional dumping"

        return AgentSignal(self.name, signal, conf, reason, self.weight)
