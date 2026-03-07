"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — Ω-EXTREME NEURAL AGENTS                      ║
║     QCA (Cellular Automata) + Predator-Prey + Black Swan EVT                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import Optional, List
from core.consciousness.agents.base import BaseAgent, AgentSignal
from cpp.asi_bridge import CPP_CORE

class QCAAgent(BaseAgent):
    """
    Agente de Autômatos Celulares Quânticos (QCA).
    Mapeia a densidade do Order Book em um grid e simula a propagação de ordens.
    Identifica 'Super-Support' e 'Super-Resistance' via padrões de vida no grid.
    """
    def __init__(self, weight: float = 1.5):
        super().__init__("QCA", weight=weight)
        
    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        if not snapshot.book:
            return None
            
        bids = np.array([p['price'] for p in snapshot.book.get('bids', []) if isinstance(p, dict)], dtype=np.float64)
        asks = np.array([p['price'] for p in snapshot.book.get('asks', []) if isinstance(p, dict)], dtype=np.float64)
        
        if len(bids) < 5 or len(asks) < 5:
            return None
            
        # Processa via C++ (Grid 64x64)
        # alpha=1.0 como threshold de volume por célula
        qca_result = CPP_CORE.process_qca_grid(bids, asks, alpha=1.0)
        
        if not qca_result:
            return None
            
        signal = 0.0
        # Se a densidade está maior no lado Buy (bid cells > ask cells)
        # Nota: QCAResultC em C++ tem grid_entropy e transition_speed
        if qca_result['transition_speed'] > 0.5:
            # Simplificação: se crítico, sinal direcional baseado no price_slope (pode ser refinado)
            signal = 1.0 if np.mean(bids) > np.mean(asks) else -1.0
            
        confidence = min(1.0, qca_result.get('transition_speed', 0.5))
        reasoning = (f"QCA_TRANSITION: {qca_result['transition_speed']:.2f} | ENT: {qca_result['entropy']:.2f} "
                     f"CRIT={qca_result['critical']}")
                     
        return AgentSignal(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning
        )

class PredatorPreyAgent(BaseAgent):
    """
    Agente de Dinâmica Predador-Presa de Lotka-Volterra.
    Modela Compradores vs Vendedores como espécies em competição.
    Identifica desequilíbrios ecológicos no mercado (exaustão de 'vítimas').
    """
    def __init__(self, weight: float = 1.4):
        super().__init__("PredatorPrey", weight=weight)
        
    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        recent_ticks = snapshot.metadata.get("recent_ticks", [])
        if len(recent_ticks) < 10:
            return None
            
        # Simplificação: compradores = volume verde, vendedores = volume vermelho
        buyers = sum(t.get('volume', 0) for t in recent_ticks if t.get('ask', 0) - t.get('bid', 0) > 0)
        sellers = sum(t.get('volume', 0) for t in recent_ticks if t.get('ask', 0) - t.get('bid', 0) <= 0)
        
        # solve_lotka_volterra(dt, params, prey, predator)
        pp_params = {"alpha": 0.1, "beta": 0.02, "delta": 0.02, "gamma": 0.1}
        new_b, new_s, pp_result = CPP_CORE.solve_lotka_volterra(0.1, pp_params, float(buyers), float(sellers))
        
        if not pp_result:
            return None
            
        signal = 0.0
        # Se o risco de extinção é alto, o lado dominante está saturado (reversão iminente)
        if pp_result['risk'] > 0.8:
            signal = -1.0 if buyers > sellers else 1.0 # Reversão
        else:
            # Seguir eficiência de caça
            signal = 1.0 if buyers > sellers else -1.0
            
        confidence = min(1.0, pp_result['efficiency'] / 10.0)
        reasoning = f"LV_ECOLOGY: Risk={pp_result['risk']:.2f} Eff={pp_result['efficiency']:.2f}"
        
        return AgentSignal(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning
        )

class EVTBlackSwanAgent(BaseAgent):
    """
    Agente de Teoria do Valor Extremo (Black Swan Harvester).
    Usa Distribuição de Pareto Generalizada (GPD) e Cópulas para prever 
    a cauda longa do risco e capturar reversões violentas.
    """
    def __init__(self, weight: float = 2.0):
        super().__init__("BlackSwanEVT", weight=weight)
        
    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        prices = snapshot.get_recent_prices(500)
        if len(prices) < 200:
            return None
            
        # Retornos logarítmicos
        returns = np.diff(np.log(prices))
        
        # solve via C++ (GPD / Tail Index)
        # threshold de 0.001 (0.1% de movimento por tick/snapshot)
        evt_result = CPP_CORE.harvest_black_swan(returns, threshold=0.001)
        
        if not evt_result:
            return None
            
        signal = 0.0
        if evt_result['is_black_swan']:
            # Capitulação de cauda -> Compra se queda violenta
            signal = 1.0 if np.mean(returns[-10:]) < 0 else -1.0
                
        confidence = min(1.0, evt_result['tail_risk'] * 2.0)
        reasoning = (f"EVT_SWAN: Tail={evt_result['tail_risk']:.4f} EXC={evt_result['exceedance']:.4f}")
                     
        return AgentSignal(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning
        )
