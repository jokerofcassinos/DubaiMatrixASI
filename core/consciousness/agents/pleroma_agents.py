"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — PLEROMA AGENTS (Phase Ω)                    ║
║     Inteligência Suprema (Nível 32): Fluidos de Dirac e Simetria CPT.       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal

class DiracFluidAgent(BaseAgent):
    """
    [Phase Ω-Pleroma] Fluidos de Dirac (Hidrodinâmica Quântica).
    Modelagem do fluxo de alta frequência como elétrons no grafeno (Fluido de Dirac).
    Neste estado, as colisões são tão frequentes que a viscosidade cinemática colapsa
    e o fluxo de ordens comporta-se como um fluido perfeito, transmitindo momento
    sem atrito térmico. Identifica os raros instantes em que o mercado se move 
    em "onda perfeita" antes do preço disparar graficamente.
    """
    def __init__(self, weight=5.0):
        super().__init__("DiracFluid", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        tick_buffer = snapshot.metadata.get("tick_buffer", [])
        if len(tick_buffer) < 20:
            return AgentSignal(self.name, 0.0, 0.0, "INSUFFICIENT_PARTICLES", self.weight)

        # Extrair frequências de colisão (Deltas de tempo entre ticks)
        times = [t.get("time_msc", 0) for t in tick_buffer]
        dt = np.diff(times)
        
        if len(dt) == 0 or np.mean(dt) == 0:
            return AgentSignal(self.name, 0.0, 0.0, "NO_COLLISION_DATA", self.weight)
            
        collision_rate = 1000.0 / (np.mean(dt) + 1e-6) # Colisões por segundo
        
        # Num fluido de Dirac, a entropia flui em "ondas de calor" (Second Sound)
        entropy = snapshot.metadata.get("tick_entropy", 0.5)
        
        signal = 0.0
        conf = 0.0
        reason = "CLASSICAL_FLUID"
        
        # Se a taxa de colisão é extrema (> 150 ticks/segundo) e a entropia está perfeitamente organizada
        if collision_rate > 150.0 and entropy < 0.25:
            tick_velocity = snapshot.metadata.get("tick_velocity", 0.0)
            signal = np.sign(tick_velocity)
            conf = 0.98
            reason = f"DIRAC_FLUID_RESONANCE (Collisions={collision_rate:.0f}/s, Entropy={entropy:.2f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class CPTSymmetryAgent(BaseAgent):
    """
    [Phase Ω-Pleroma] Simetria CPT (Charge, Parity, Time).
    Na física de partículas, a simetria CPT é absoluta. 
    Charge = Direção (Compradores vs Vendedores)
    Parity = Estrutura Espacial (Imbalance de Bid vs Ask)
    Time = Ritmo Temporal (Aceleração do Tick)
    Se o mercado tenta fazer um movimento (Charge), mas a Paridade (Book) e o Tempo (Aceleração) 
    não invertem simetricamente (Quebra de CPT), o movimento é uma Falsidade Quântica (Fakeout).
    """
    def __init__(self, weight=4.9):
        super().__init__("CPTSymmetry", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        charge = np.sign(snapshot.metadata.get("tick_velocity", 0.0))
        parity = np.sign(snapshot.metadata.get("order_imbalance", 0.0))
        
        # Time Reversal Proxy (Está acelerando ou desacelerando?)
        jounce = snapshot.metadata.get("kinematic_jounce", 0.0)
        time_arrow = np.sign(jounce)
        
        signal = 0.0
        conf = 0.0
        reason = "CPT_SYMMETRIC"
        
        # Se os três vetores não concordam, há quebra de simetria fundamental
        if charge != 0 and parity != 0 and time_arrow != 0:
            if charge != parity or charge != time_arrow:
                # O movimento de preço (Charge) é falso porque não possui paridade no order book 
                # ou não possui aceleração temporal sustentável. Veto a favor da estrutura subjacente.
                signal = -charge # Aposta contra o movimento falso
                conf = 0.96
                reason = f"CPT_SYMMETRY_VIOLATION (C={charge}, P={parity}, T={time_arrow})"
            else:
                signal = charge
                conf = 0.95
                reason = "CPT_PERFECT_SYMMETRY"
                
        return AgentSignal(self.name, signal, conf, reason, self.weight)
