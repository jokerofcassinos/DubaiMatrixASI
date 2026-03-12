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
