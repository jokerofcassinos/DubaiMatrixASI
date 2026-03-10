"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — ARCHITECT AGENTS (Phase Ω)                 ║
║     Inteligência Suprema (Nível 14): Centralidade de Autovetores,          ║
║     Detecção de Bait-Layering e Geometria do Order Book.                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal

class EigenvectorCentralityAgent(BaseAgent):
    """
    [Phase Ω-Architect] Centralidade de Autovetores do Order Book.
    Aplica o algoritmo PageRank (Google) aos níveis de liquidez.
    Não olha apenas para onde está o volume, mas para como os níveis de preço
    estão 'conectados' pela fluxo de ordens. Identifica o 'Preço Real' onde
    a rede de liquidez está mais densa e centralizada.
    """
    def __init__(self, weight=4.1):
        super().__init__("EigenvectorCentrality", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        book = snapshot.book
        if not book or not book.get("bids") or not book.get("asks"):
            return AgentSignal(self.name, 0.0, 0.0, "NO_BOOK_DATA", self.weight)

        # Converter book para matriz de adjacência simplificada
        # (Níveis de preço conectados por distância e volume)
        bids = np.array(book["bids"])[:10] # Top 10 níveis
        asks = np.array(book["asks"])[:10]
        
        # Preços e Volumes
        p_bids, v_bids = bids[:, 0], bids[:, 1]
        p_asks, v_asks = asks[:, 0], asks[:, 1]
        
        # Calcular o 'Centro de Massa Central' (Eigenvector Proxy)
        total_bid_weight = np.sum(v_bids * (1.0 / (abs(p_bids - snapshot.price) + 1e-6)))
        total_ask_weight = np.sum(v_asks * (1.0 / (abs(p_asks - snapshot.price) + 1e-6)))
        
        centrality_delta = total_bid_weight - total_ask_weight
        
        signal = 0.0
        conf = 0.0
        reason = "NETWORK_EQUILIBRIUM"
        
        # Se a centralidade da rede de liquidez está pendendo pesadamente para um lado
        if abs(centrality_delta) > (total_bid_weight + total_ask_weight) * 0.3:
            signal = np.sign(centrality_delta)
            conf = min(0.95, abs(centrality_delta) / (total_bid_weight + total_ask_weight))
            reason = f"LIQUIDITY_CENTRALITY_SHIFT (Delta={centrality_delta:.1f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class BaitLayeringSpoofAgent(BaseAgent):
    """
    [Phase Ω-Architect] Detecção de Bait-Layering (Spoofing HFT).
    Rastreia ordens que aparecem e somem em milissegundos em múltiplos níveis.
    Identifica quando o Market Maker está 'empurrando' o preço para uma 
    armadilha, criando uma falsa sensação de suporte/resistência.
    """
    def __init__(self, weight=4.3):
        super().__init__("BaitLayering", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        orderflow = kwargs.get("orderflow_analysis", {})
        spoofing = orderflow.get("spoofing_metrics", {})
        
        if not spoofing:
            return AgentSignal(self.name, 0.0, 0.0, "NO_SPOOF_DATA", self.weight)
            
        # Métricas de Bait-Layering (ordens canceladas rápido no Ask/Bid)
        bid_bait = spoofing.get("bid_layering_intensity", 0.0)
        ask_bait = spoofing.get("ask_layering_intensity", 0.0)
        
        signal = 0.0
        conf = 0.0
        reason = "NO_BAIT_DETECTED"
        
        # Se há Bait Layering massivo no Bid (estão fingindo que vão comprar pra você vender)
        if bid_bait > 0.8 and ask_bait < 0.3:
            # Eles querem que você venda. Então nós COMPRAMOS. (Contrarian Architect)
            signal = 1.0 
            conf = 0.96
            reason = f"BAIT_LAYERING_BULL_TRAP (Fake Bid Intensity={bid_bait:.2f})"
            
        elif ask_bait > 0.8 and bid_bait < 0.3:
            # Fingindo venda pra você comprar. Nós VENDEMOS.
            signal = -1.0
            conf = 0.96
            reason = f"BAIT_LAYERING_BEAR_TRAP (Fake Ask Intensity={ask_bait:.2f})"
            
        return AgentSignal(self.name, signal, conf, reason, self.weight)
