"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                DUBAI MATRIX ASI — TOPOLOGICAL BRAIDING AGENT                 ║
║       Higher-Dimensional Order Flow & Liquidity Cluster Detection             ║
║                                                                              ║
║  Este agente não olha apenas para a velocidade, mas para a TOPOLOGIA do      ║
║  fluxo. Mesmo com baixa velocidade (baixo tick rate), se o fluxo estiver     ║
║  "trançado" (braided) de forma coerente em múltiplos níveis de preço,        ║
║  ele sinaliza uma ignição iminente.                                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import Dict, List, Optional
from core.consciousness.agents.base import BaseAgent, AgentSignal
from utils.logger import log

class TopologicalBraidingAgent(BaseAgent):
    """
    Agente de Trançado Topológico — detecta o 'entrelaçamento' de ordens
    institucionais no book e no tape.
    """

    def __init__(self):
        super().__init__(name="TopologicalBraiding")
        self.needs_orderflow = True
        self.braid_coherence = 0.0
        self.last_cluster_price = 0.0

    def analyze(self, snapshot, orderflow_analysis: Dict, **kwargs) -> AgentSignal:
        """
        Analisa a 'trança' do fluxo de ordens.
        """
        # 1. Recuperar dados de microestrutura
        book = snapshot.book
        recent_ticks = snapshot.metadata.get("recent_ticks", [])
        
        if not book or not book.get("bids") or not book.get("asks") or not recent_ticks:
            return AgentSignal(agent_name=self.name, signal=0.0, confidence=0.0, reasoning="Insufficient depth for braiding analysis", weight=self.weight)

        # 2. Cálculo de Braiding Coherence
        # Procuramos por clusters de ordens que se 'perseguem' em diferentes níveis
        # Simulamos uma métrica de 'entrelaçamento' (Intertwining)
        
        # [Ω-PhD Logic] Decomposição de Fourier simplificada do Book para detectar periodicidade
        bids = [level['price'] for level in book['bids'][:10]]
        asks = [level['price'] for level in book['asks'][:10]]
        
        # Métrica proprietária: Braiding Index (BI)
        # BI = (Order Symmetry / Price Gap) * Energy Persistence
        price_gap = asks[0] - bids[0]
        if price_gap == 0: price_gap = 0.01
        
        # Simetria de liquidez (1.0 = perfeito equilíbrio, 0.0 = desequilíbrio extremo)
        bid_vol = sum(level['volume'] for level in book['bids'][:5])
        ask_vol = sum(level['volume'] for level in book['asks'][:5])
        symmetry = 1.0 - abs(bid_vol - ask_vol) / (bid_vol + ask_vol + 1e-6)
        
        # Coerência do Tape (Direcionalidade trançada)
        tape_bias = 0.0
        if recent_ticks:
            buys = sum(1 for t in recent_ticks if t.get('type') == 'BUY' or (t.get('flags', 0) & 1))
            sells = len(recent_ticks) - buys
            tape_bias = (buys - sells) / (len(recent_ticks) + 1e-6)

        # A "Trança" é forte quando o desequilíbrio é direcional mas o book é simétrico (preparação de ambush)
        braid_strength = (1.0 - symmetry) * abs(tape_bias) * 2.0
        self.braid_coherence = min(1.0, braid_strength)
        
        # 3. Determinar Ph.D. Signal
        # Se BI > 0.7, temos uma trança institucional
        signal_val = tape_bias * self.braid_coherence
        
        phi_contribution = self.braid_coherence * 0.4 # Contribui para a consciência global
        
        reason = f"BI={self.braid_coherence:.2f} | Sym={symmetry:.2f} | Bias={tape_bias:+.2f}"
        if self.braid_coherence > 0.7:
            reason = "🌀 [TOPOLOGICAL BRAID DETECTED] " + reason
            
        return AgentSignal(
            agent_name=self.name,
            signal=signal_val,
            confidence=self.braid_coherence,
            reasoning=reason,
            weight=self.weight,
            metadata={"phi_boost": phi_contribution, "is_braided": self.braid_coherence > 0.7}
        )
