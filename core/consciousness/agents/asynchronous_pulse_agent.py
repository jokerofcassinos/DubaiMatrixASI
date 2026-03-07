"""
╔══════════════════════════════════════════════════════════════════════════════╗
║             DUBAI MATRIX ASI — ASYNCHRONOUS PULSE AGENT (SNN)                ║
║     Agente que utiliza Neurônios LIF para cognição orientada a eventos.      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import time
from typing import Optional
from core.consciousness.agents.base import BaseAgent, AgentSignal
from cpp.asi_bridge import CPP_CORE

class AsynchronousPulseAgent(BaseAgent):
    """
    Agente de Pulsos Assíncronos (Spiking Neural Network).
    Acumula pressão de orderflow no 'potencial de membrana'.
    Dispara um spike quando a barreira de liquidez é rompida.
    """

    def __init__(self, weight=2.2):
        super().__init__("SpikingPulse", weight=weight)
        self.potential = -70.0  # mV (v_rest)
        self.last_update = time.time()
        
        # Parâmetros LIF (Leaky Integrate-and-Fire)
        self.v_rest = -70.0
        self.v_threshold = -50.0
        self.resistance = 10.0
        self.capacitance = 5.0
        
        self.needs_orderflow = True

    def analyze(self, snapshot, orderflow_analysis=None, **kwargs) -> Optional[AgentSignal]:
        if not orderflow_analysis:
            return None

        # 1. Calcular Delta T (tempo real entre ciclos)
        now = time.time()
        dt = (now - self.last_update) * 1000.0 # ms
        self.last_update = now

        # 2. Fonte de Corrente
        imbalance = float(orderflow_analysis.get('order_imbalance', 0.0))
        velocity = float(orderflow_analysis.get('tick_velocity', 1.0))
        
        input_current = imbalance * velocity

        # 3. Atualizar Neurônio via C++
        self.potential, fired = CPP_CORE.update_lif_neuron(
            input_current, dt, float(self.v_rest), float(self.v_threshold),
            float(self.resistance), float(self.capacitance), float(self.potential)
        )

        # 4. Resposta baseada em Spikes
        signal = 0.0
        confidence = 0.0
        reasoning = f"Pot: {self.potential:+.1f}mV"

        if fired:
            signal = 1.0 if input_current > 0 else -1.0
            confidence = 0.95
            reasoning += " | 🔥 SPIKE"
        else:
            signal = 0.0
            confidence = 0.1
            reasoning += " | ACC"

        return AgentSignal(
            agent_name=self.name,
            signal=float(signal),
            confidence=float(confidence),
            reasoning=reasoning
        )
