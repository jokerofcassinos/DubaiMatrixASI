"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — PHEROMONE FIELD AGENT                 ║
║     Coordenação estigmérgica via rastro de ordens passadas (C++)            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import numpy as np
from typing import Optional
from core.consciousness.agents.base import BaseAgent, AgentSignal
from cpp.asi_bridge import CPP_CORE

class PheromoneFieldAgent(BaseAgent):
    """
    Agente MCDF Conceito 1 (Stigmergia - Pheromone Field).
    Sente o 'rastro' deixado por liquidações passadas e ordens institucionais.
    Se o executor está depositando feromônio em certas faixas de preço, 
    este agente detecta a densidade e atrai o enxame para a convergência.
    """
    
    def __init__(self, weight: float = 1.8):
        super().__init__("PheromoneFieldAgent", weight)
        
    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        price = snapshot.price
        if price <= 0: return None
        
        # 1. Atualizar o campo (decay temporal) via C++
        # Usamos delta de tempo de 1 segundo (ou o ciclo do bot)
        CPP_CORE._lib.asi_update_pheromone_field(1.0)
        
        # 2. Sentir a densidade de feromônio no preço atual
        density = CPP_CORE._lib.asi_sense_pheromone(price)
        
        # 3. Traduzir densidade em viés
        # O feromônio no DubaiMatrixASI é polarizado: 
        # Valores positivos = Atração de Compra (Sweet Spot)
        # Valores negativos = Atração de Venda (Gravity Spot)
        
        signal = 0.0
        conf = 0.0
        
        if abs(density) > 0.1:
            signal = float(np.tanh(density * 2.0))
            conf = min(0.95, abs(density) * 0.8)
            
        reason = f"Pheromone Density: {density:.4f}"
        
        if abs(signal) > 0.5:
            reason += " [STIGMERGIC ATTRACTION]"
            
        return AgentSignal(
            agent_name=self.name,
            signal=signal,
            confidence=conf,
            reasoning=reason,
            weight=self.weight
        )
