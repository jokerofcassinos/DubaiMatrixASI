"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — PHD LEVEL AGENTS (Phase 69)                ║
║     Agentes de Alta Complexidade: Laser, Navier-Stokes, Dark Matter e      ║
║     Imunidade Biológica.                                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal
from cpp.asi_bridge import CPP_CORE
from core.evolution.biological_immunity import TCellImmunitySystem
from config.omega_params import OMEGA

# Singleton da Imunidade (Pode ser inicializado no Brain também)
IMMUNITY = TCellImmunitySystem()

class LaserHedgingAgent(BaseAgent):
    """
    [Phase Ω-Singularity] Attosecond Laser Hedging.
    Detecta compressão extrema de energia em janelas de milissegundos.
    """
    def __init__(self, weight=4.5):
        super().__init__("LaserHedging", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        tick_buffer = snapshot.metadata.get("tick_buffer", [])
        if len(tick_buffer) < 10:
            return AgentSignal(self.name, 0.0, 0.0, "INSUFFICIENT_TICKS", self.weight)

        # Extrair energia (Variação de preço ao quadrado)
        energy_window = np.array([abs(t["last"] - tick_buffer[i-1]["last"]) if i > 0 else 0 
                                  for i, t in enumerate(tick_buffer)], dtype=np.float64)
        
        compression = CPP_CORE.calculate_laser_compression(energy_window, len(energy_window))
        
        signal = 0.0
        conf = 0.0
        reason = "LOW_ENERGY_DENSITY"
        
        if compression > 10.0: # 10x a densidade média
            tick_velocity = snapshot.metadata.get("tick_velocity", 0.0)
            signal = np.sign(tick_velocity)
            conf = min(0.98, compression / 50.0)
            reason = f"LASER_PULSE_DETECTION (Compression={compression:.1f}x)"

        return AgentSignal(self.name, signal, conf, reason, self.weight)

class NavierStokesTurbulenceAgent(BaseAgent):
    """
    [Phase Ω-Singularity] Navier-Stokes Fluid Turbulence.
    Mede o Número de Reynolds do Order Flow.
    """
    def __init__(self, weight=4.2):
        super().__init__("NavierStokesTurbulence", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        tick_buffer = snapshot.metadata.get("tick_buffer", [])
        if len(tick_buffer) < 15:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        velocities = np.array([t.get("last", 0) - tick_buffer[i-1].get("last", 0) if i>0 else 0 
                               for i, t in enumerate(tick_buffer)], dtype=np.float64)
        densities = np.array([t.get("volume", 1.0) for t in tick_buffer], dtype=np.float64)
        
        reynolds = CPP_CORE.calculate_navier_stokes_reynolds(velocities, densities, len(velocities))
        
        signal = 0.0
        conf = 0.0
        reason = "LAMINAR_FLOW"
        
        # Transição de Fase: Re > 4000
        if reynolds > 4000:
            # Fluxo Turbulento: Exaustão iminente ou rompimento caótico
            # Se a velocidade está caindo no topo da turbulência, operamos a exaustão
            if abs(np.mean(velocities[-3:])) < abs(np.mean(velocities[-10:-3])):
                signal = -np.sign(np.mean(velocities))
                conf = 0.92
                reason = f"TURBULENT_EXHAUSTION (Reynolds={reynolds:.0f})"
        else:
            # Fluxo Laminar: Tendência saudável
            signal = np.sign(np.mean(velocities))
            conf = 0.80
            reason = f"LAMINAR_TREND_FOLLOW (Reynolds={reynolds:.0f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)

class DarkMatterGravityAgent(BaseAgent):
    """
    [Phase Ω-Singularity] Dark Matter Gravitational Pull.
    Inferência de massa não-visível no Book.
    """
    def __init__(self, weight=4.0):
        super().__init__("DarkMatterGravity", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        tick_velocity = snapshot.metadata.get("tick_velocity", 0.0)
        # Simplificação: Aceleração é a variação da velocidade entre snapshots
        accel = tick_velocity # Aproximado
        visible_mass = snapshot.metadata.get("buy_volume", 0.0) + snapshot.metadata.get("sell_volume", 0.0)
        
        dark_mass = CPP_CORE.calculate_dark_matter_gravity(accel, visible_mass)
        
        signal = 0.0
        conf = 0.0
        reason = "VISIBLE_UNIVERSE_STABLE"
        
        if dark_mass > 0:
            signal = np.sign(tick_velocity)
            conf = 0.95
            reason = f"DARK_MATTER_PULL (InferredHiddenMass={dark_mass:.0f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)

class TCellImmunityAgent(BaseAgent):
    """
    [Phase Ω-Singularity] Biological Immunity (Veto).
    Veta se o padrão atual assemelha-se a infecções (losses) passadas.
    """
    def __init__(self, weight=5.0): # Peso máximo para override/veto
        super().__init__("TCellImmunity", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        if IMMUNITY.is_infected(snapshot):
            return AgentSignal(self.name, 0.0, 0.0, "ANTIGEN_DETECTED_VETO", self.weight)
        
        return AgentSignal(self.name, 0.0, 0.0, "SYSTEM_CLEAN", self.weight)


class OrderFlowSingularityAgent(BaseAgent):
    """
    [Phase Ω-Singularity] Order Flow Singularity Detector.
    Mede a compressão topológica extrema do book e fluxo de negócios. 
    Prevê rompimentos a partir do colapso de spread e anomalia entrópica.
    """
    def __init__(self, weight=4.8):
        super().__init__("OrderFlowSingularity", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        tick_buffer = snapshot.metadata.get("tick_buffer", [])
        if len(tick_buffer) < 20:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)
            
        # Calcula a aceleração do volume (delta escondido) e compressão de range
        velocities = np.array([t.get("last", 0) - tick_buffer[i-1].get("last", 0) if i>0 else 0 
                               for i, t in enumerate(tick_buffer)], dtype=np.float64)
                               
        vol_ratios = np.array([t.get("volume", 1.0) for t in tick_buffer], dtype=np.float64)
        
        # Singularity Index = (sum(vol) / var(velocities)) se var for tendendo a zero
        var_vel = np.var(velocities) + 1e-6
        total_mass = np.sum(vol_ratios)
        
        singularity_index = total_mass / (var_vel * 1000.0) # normalização empírica
        
        signal = 0.0
        conf = 0.0
        reason = "NORMAL_EXPANSION"
        
        if singularity_index > 9.0:
            # Singularidade detectada. Para onde vai explodir? Segue o micro-delta.
            micro_delta = np.sum(velocities[-5:]) # Últimos 5 ticks decidem a gravidade direcional
            signal = np.sign(micro_delta) if micro_delta != 0 else 0.0
            conf = min(0.99, singularity_index / 15.0)
            reason = f"SINGULARITY_COLLAPSE (Index={singularity_index:.1f})"
            
        return AgentSignal(self.name, signal, conf, reason, self.weight)

from scipy.stats import kurtosis

class LevyFlightFatTailAgent(BaseAgent):
    """
    [Phase Ω-Apotheosis] Levy Flight / Fat Tail Detector.
    Mede a curtose (kurtosis) da distribuição dos retornos em milissegundos.
    Se a variância é predominada por extremos (cauda longa), os alvos (RRR)
    podem e devem ser massivamente expandidos (1:10).
    """
    def __init__(self, weight=4.7):
        super().__init__("LevyFlightFatTail", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        tick_buffer = snapshot.metadata.get("tick_buffer", [])
        if len(tick_buffer) < 50:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)
            
        # Variações base (1 tick step)
        returns = np.array([t.get("last", 0) - tick_buffer[i-1].get("last", 0) if i>0 else 0 
                               for i, t in enumerate(tick_buffer)], dtype=np.float64)
                               
        # Filtra os zeros (movimentos irrelevantes)
        returns = returns[returns != 0]
        if len(returns) < 10:
             return AgentSignal(self.name, 0.0, 0.0, "NO_VARIANCE", self.weight)
             
        # Calcula a Curtose (Excesso de curtose)
        k_score = kurtosis(returns, fisher=True)
        
        signal = 0.0
        conf = 0.0
        reason = "GAUSSIAN_DISTRIBUTION"
        
        # Uma normal tem excesso 0. Uma distribuição de Laplace tem 3.
        # Estamos caçando regimes de Salto (Black Swan / Levy Flight). Kurtosis > 5.0.
        threshold = OMEGA.get("levy_flight_kurtosis_threshold", 5.0) if 'OMEGA' in globals() else 5.0
        
        if k_score > threshold:
            # Extremos puxam o mercado assimetrico. A inercia atual (ultimos 5 returns) dita o voo.
            recent_drift = np.sum(returns[-5:])
            signal = np.sign(recent_drift) if recent_drift != 0 else 0.0
            conf = min(0.98, k_score / 15.0)
            reason = f"LEVY_FLIGHT_DETECTED (Kurtosis={k_score:.1f} > {threshold:.1f})"
            
        return AgentSignal(self.name, signal, conf, reason, self.weight)

class VPINToxicityAgent(BaseAgent):
    """
    [Phase Ω-Pangalactic] VPIN Toxicity Detector.
    Mede a Probabilidade de Trading Informado Sincronizado por Volume.
    Prevê Squeezes ou Flash Crashes pelo envenenamento extremo do Order Flow.
    """
    def __init__(self, weight=4.9):
        super().__init__("VPINToxicity", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        tick_buffer = snapshot.metadata.get("tick_buffer", [])
        if len(tick_buffer) < 50:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        buy_vol = 0.0
        sell_vol = 0.0
        
        for i in range(1, len(tick_buffer)):
            t_prev = tick_buffer[i-1]
            t = tick_buffer[i]
            p_diff = t.get("last", 0) - t_prev.get("last", 0)
            vol = t.get("volume", 1.0)
            if p_diff > 0:
                buy_vol += vol
            elif p_diff < 0:
                sell_vol += vol
            else:
                buy_vol += vol * 0.5
                sell_vol += vol * 0.5
                
        total_vol = buy_vol + sell_vol + 1e-9
        vpin = abs(buy_vol - sell_vol) / total_vol
        
        threshold = OMEGA.get("vpin_toxicity_limit", 0.75) if 'OMEGA' in globals() else 0.75
        signal = 0.0
        conf = 0.0
        reason = f"HEALTHY_LIQUIDITY (VPIN={vpin:.2f})"
        
        if vpin >= threshold:
            # Toxicidade crítica! Tubarões drenando o book.
            signal = 1.0 if buy_vol > sell_vol else -1.0
            conf = min(0.99, vpin * 1.2)
            reason = f"FLASH_CRASH_WARNING: VPIN_TOXICITY ({vpin:.2f} >= {threshold:.2f})"
            
        return AgentSignal(self.name, signal, conf, reason, self.weight)

class FisherInformationAgent(BaseAgent):
    """
    [Phase Ω-Pangalactic] Fisher Information Memory Collapse.
    Mede a Informação Termodinâmica do Tape. Quando a informação colapsa a zero,
    o mercado 'esquece' sua âncora paramétrica, sinalizando um Squeeze Quântico.
    """
    def __init__(self, weight=4.8):
        super().__init__("FisherInformation", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        tick_buffer = snapshot.metadata.get("tick_buffer", [])
        if len(tick_buffer) < 50:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)
            
        returns = np.array([t.get("last", 0) - tick_buffer[i-1].get("last", 0) if i>0 else 0 
                               for i, t in enumerate(tick_buffer)], dtype=np.float64)
                               
        returns = returns[returns != 0]
        if len(returns) < 5:
            return AgentSignal(self.name, 0.0, 0.0, "NO_FISHER_INFO", self.weight)
            
        # Proxy Empírico Padrão para Informação de Fisher (I = 1 / Var)
        var = np.var(returns) + 1e-9
        fisher_info = 1.0 / var
        
        threshold = OMEGA.get("fisher_critical_collapse", 0.05) if 'OMEGA' in globals() else 0.05
        
        signal = 0.0
        conf = 0.0
        reason = f"STRUCTURAL_MEMORY_INTACT (FI={fisher_info:.3f})"
        
        # Se a variância de alta frequência expandir insamente, FI vai a zero.
        if fisher_info < threshold:
            recent_drift = np.sum(returns[-3:])
            signal = np.sign(recent_drift) if recent_drift != 0 else 0.0
            conf = min(0.98, (threshold / fisher_info) * 0.1)
            reason = f"THERMODYNAMIC_MEMORY_COLLAPSE (FI={fisher_info:.4f} < {threshold:.4f})"
            
        return AgentSignal(self.name, signal, conf, reason, self.weight)

# ═══ PHASE Ω-THERMODYNAMIC (AGI TRANSITION) ═══

class FristonFreeEnergyAgent(BaseAgent):
    """
    [Phase Ω-Thermodynamic] Active Inference (Karl Friston).
    Computes "Free Energy" (Surprisal/Prediction Error) of the market state.
    If the market deviates drastically from the Bayesian prior (V-Pulse inertia),
    Free Energy explodes, signaling a "Black Swan" paradigm shift.
    The agent minimizes surprise by aligning with the entropic force.
    """
    def __init__(self, weight=5.0):
        super().__init__("FristonFreeEnergy", weight)
        
    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        signal = 0.0
        confidence = 0.0
        
        friston_threshold = OMEGA.get("friston_surprise_threshold", 3.0)
        free_energy = 0.0
        
        if len(snapshot.recent_ticks) >= 200:
            # Simple generative model: tick moving average vs actual ticks
            ticks = np.array([t.get("last", t.get("mid", 0)) for t in snapshot.recent_ticks[-200:]])
            mu = np.mean(ticks[:-50])
            sigma = np.std(ticks[:-50]) + 1e-9
            
            recent_mean = np.mean(ticks[-50:])
            # Surprisal (Log probability deviation)
            z_score = abs(recent_mean - mu) / sigma
            free_energy = z_score ** 2 # proxy for variational free energy
            
            if free_energy > friston_threshold:
                # Paradigm shift detected
                confidence = min(0.95, free_energy / (friston_threshold * 2.0))
                # Align with the force of the surprise
                signal = 1.0 if recent_mean > mu else -1.0
                
        return AgentSignal(self.name, signal, confidence, f"FRISTON_SURPRISE: {free_energy:.2f}", self.weight)

class KolmogorovComplexityAgent(BaseAgent):
    """
    [Phase Ω-Thermodynamic] Algorithmic Information Theory.
    Estimates the compressibility of the tick flow.
    If the flow is highly compressible (low complexity), it's synthetic/algorithmic (TWAP/VWAP).
    If it's incompressible, it's retail chaos. The agent rides the algorithmic tape.
    """
    def __init__(self, weight=4.8):
        super().__init__("KolmogorovComplexity", weight)
        
    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        signal = 0.0
        confidence = 0.0
        
        kolmogorov_ratio = OMEGA.get("kolmogorov_compression_ratio", 0.35)
        compression_ratio = 1.0
        
        if len(snapshot.recent_ticks) >= 100:
            # Binarize ticks: 1 for up, 0 for down
            ticks = [t.get("last", t.get("mid", 0)) for t in snapshot.recent_ticks[-100:]]
            diffs = np.diff(ticks)
            binary_seq = "".join(["1" if d > 0 else "0" for d in diffs if d != 0])
            
            if len(binary_seq) > 20:
                import zlib
                compressed = zlib.compress(binary_seq.encode('utf-8'))
                compression_ratio = len(compressed) / len(binary_seq)
                
                # If highly compressible (synthetic tape)
                if compression_ratio < kolmogorov_ratio:
                    confidence = 0.85
                    # Determine vector
                    ups = binary_seq.count("1")
                    signal = 1.0 if ups > len(binary_seq)/2 else -1.0
                    
        return AgentSignal(self.name, signal, confidence, f"KOLMOGOROV_COMPRESSION: {compression_ratio:.2f}", self.weight)

class PrigogineDissipativeAgent(BaseAgent):
    """
    [Phase Ω-Thermodynamic] Far-From-Equilibrium Thermodynamics (Ilya Prigogine).
    Analyzes the order book and tick flow as a dissipative structure.
    A trend is sustained by absorbing liquidity. When entropy saturates,
    the structure undergoes a climatic bifurcation (exhaustion reversal).
    """
    def __init__(self, weight=4.9):
        super().__init__("PrigogineDissipative", weight)
        
    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        signal = 0.0
        confidence = 0.0
        
        entropy_saturation = OMEGA.get("prigogine_entropy_saturation", 0.90)
        entropy_raw = snapshot.indicators.get("M1_entropy")
        entropy = float(entropy_raw[-1]) if isinstance(entropy_raw, np.ndarray) and len(entropy_raw) > 0 else (float(entropy_raw) if entropy_raw is not None else 0.0)
        
        if entropy > 0:
            # If entropy is absolutely saturated while velocity is dropping
            if entropy > entropy_saturation:
                candles_m1 = snapshot.candles.get("M1")
                if candles_m1 and len(candles_m1["close"]) >= 5:
                    closes = candles_m1["close"][-5:]
                    trend = closes[-1] - closes[0]
                    # Bifurcation: Revert against the dead trend structure
                    if abs(trend) > snapshot.atr * 1.5: # Structure over-extended
                        signal = -1.0 if trend > 0 else 1.0
                        confidence = 0.92
                        
        return AgentSignal(self.name, signal, confidence, f"PRIGOGINE_BIFURCATION (Entropy={entropy:.2f})", self.weight)

class NavierStokesIgnitionAgent(BaseAgent):
    """
    [Phase 73] Navier-Stokes Ignition Detector.
    Detecta a transição rápida de fluxo Laminar para Turbulento (Ignição).
    Baseado na variação de entalpia do order flow em janelas sub-tick.
    """
    def __init__(self, weight=5.0):
        super().__init__("NavierStokesIgnition", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        has_v_pulse = snapshot.metadata.get("v_pulse_detected", False)
        v_pulse_intensity = snapshot.metadata.get("v_pulse_capacitor", 0.0)
        
        # O V-Pulse já é um proxy para a turbulência capturada em C++
        if has_v_pulse and v_pulse_intensity > 0.75:
            # Ignição Letal detectada
            tick_velocity = snapshot.metadata.get("tick_velocity", 0.0)
            signal = np.sign(tick_velocity) if tick_velocity != 0 else 0.0
            conf = min(0.99, v_pulse_intensity * 1.1)
            reason = f"LETHAL_IGNITION_TURBULENCE (Intensity={v_pulse_intensity:.2f})"
            return AgentSignal(self.name, signal, conf, reason, self.weight)
            
        return AgentSignal(self.name, 0.0, 0.0, "LAMINAR_FLOW_STABLE", self.weight)

class AsymmetricInformationEntropyAgent(BaseAgent):
    """
    [Phase Ω-Nexus] Asymmetric Information Entropy.
    Analisa a divergência entre a entropia de preço (H_p) e a entropia de volume (H_v).
    Divergência alta indica que o preço está sendo "segurado" ou "puxado" por mãos institucionais.
    """
    def __init__(self, weight=5.0):
        super().__init__("AsymmetricInformationEntropy", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        tick_buffer = snapshot.metadata.get("tick_buffer", [])
        if len(tick_buffer) < 30:
            return AgentSignal(self.name, 0.0, 0.0, "INSUFFICIENT_DATA", self.weight)

        prices = np.array([t["last"] for t in tick_buffer])
        volumes = np.array([t["volume"] for t in tick_buffer])

        def entropy(x):
            counts = np.histogram(x, bins=10)[0]
            p = counts / np.sum(counts)
            return -np.sum(p * np.log2(p + 1e-9))

        h_p = entropy(np.diff(prices))
        h_v = entropy(volumes)
        
        # Kl-Divergence feeling
        divergence = abs(h_p - h_v)
        
        signal = 0.0
        conf = 0.0
        reason = "SYMMETRIC_INFORMATION"

        if divergence > 1.2: # Threshold de assimetria
            tick_velocity = snapshot.metadata.get("tick_velocity", 0.0)
            signal = np.sign(tick_velocity)
            conf = min(0.95, divergence / 3.0)
            reason = f"ASYMMETRIC_INFO_FLOW (Div={divergence:.2f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)

class RelativisticManifoldAgent(BaseAgent):
    """
    [Phase Ω-Nexus] Relativistic Time-Series Manifold.
    Mapeia o preço em uma variedade onde o tempo é distorcido pela volatilidade.
    Identifica "Gargalhos de Tempo" onde a compressão precede a singularidade (breakout).
    """
    def __init__(self, weight=4.9):
        super().__init__("RelativisticManifold", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        v_pulse = snapshot.metadata.get("v_pulse_detected", False)
        v_intensity = snapshot.metadata.get("v_pulse_accumulator", 0.0)
        
        # Local "Gravity" (Volatility^2 / density)
        gravity = (snapshot.atr ** 2) / (snapshot.metadata.get("buy_volume", 1.0) + 1e-9)
        
        signal = 0.0
        conf = 0.0
        reason = "STRAIGHT_SPACE_TIME"

        if v_pulse and gravity > 0.05:
            tick_velocity = snapshot.metadata.get("tick_velocity", 0.0)
            signal = np.sign(tick_velocity)
            conf = min(0.97, v_intensity * 1.5)
            reason = f"TIME_DILATION_STRIKE (Gravity={gravity:.4f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)

class NeuralFlowODEAgent(BaseAgent):
    """
    [Phase Ω-Nexus] Neural Flow Ordinary Differential Equation.
    Modela o fluxo de ordens como uma equação diferencial contínua.
    Prevê o ponto de equilíbrio dinâmico (Attractor) nos próximos milissegundos.
    """
    def __init__(self, weight=5.0):
        super().__init__("NeuralFlowODE", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        tick_buffer = snapshot.metadata.get("tick_buffer", [])
        if len(tick_buffer) < 10:
             return AgentSignal(self.name, 0.0, 0.0, "NO_FLOW", self.weight)

        # Vector field approximation (du/dt)
        prices = np.array([t["last"] for t in tick_buffer])
        velocity = np.diff(prices)
        acceleration = np.diff(velocity)
        
        if len(acceleration) < 5:
             return AgentSignal(self.name, 0.0, 0.0, "LAMINAR_FLOW", self.weight)
             
        # Lyapunov Stability feeling: Se acc > 0 e vel > 0, instabilidade divergente (Explosão)
        drift = np.mean(velocity[-5:])
        accel = np.mean(acceleration[-3:])
        
        signal = 0.0
        conf = 0.0
        reason = "STABLE_FLOW"

        if abs(drift) > 0 and np.sign(drift) == np.sign(accel):
            # Fluxo acelerado na direção do drift (Atrator Divergente)
            signal = np.sign(drift)
            conf = 0.94
            reason = f"FLOW_ODE_IGNITION (Drift={drift:.4f}, Accel={accel:.4f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)
