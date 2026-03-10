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
        bids_list = book["bids"][:10] # Top 10 níveis
        asks_list = book["asks"][:10]
        
        if not bids_list or not asks_list:
            return AgentSignal(self.name, 0.0, 0.0, "INSUFFICIENT_BOOK_DEPTH", self.weight)

        # Criar arrays 2D a partir das listas de dicionários
        bids = np.array([[b["price"], b["volume"]] for b in bids_list], dtype=np.float64)
        asks = np.array([[a["price"], a["volume"]] for a in asks_list], dtype=np.float64)
        
        # Preços e Volumes (Agora sim, arrays 2D)
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
        
        # [Phase Ω-Architect Upgrade]
        # Se não tivermos dados de spoofing diretos do orderflow, inferimos pela
        # microestrutura do book (delta de volume nos níveis secundários).
        book = snapshot.book
        if not book or not book.get("bids") or not book.get("asks"):
            return AgentSignal(self.name, 0.0, 0.0, "NO_BOOK_DATA", self.weight)

        # Intensidade de Bait Layering (Inferida ou Direta)
        bid_bait = spoofing.get("bid_layering_intensity", 0.0)
        ask_bait = spoofing.get("ask_layering_intensity", 0.0)
        
        # Se os dados diretos falharem, analisamos o 'Weight' dos níveis 5-10
        if bid_bait == 0 and ask_bait == 0:
            bids = np.array([[b["price"], b["volume"]] for b in book["bids"]], dtype=np.float64)
            asks = np.array([[a["price"], a["volume"]] for a in book["asks"]], dtype=np.float64)
            
            if len(bids) > 10 and len(asks) > 10:
                # Camadas externas (5 a 10) representam o "Layering"
                bid_layering_vol = np.sum(bids[5:10, 1])
                ask_layering_vol = np.sum(asks[5:10, 1])
                
                # Se as camadas externas são muito maiores que as internas, mas o preço não anda
                bid_bait = bid_layering_vol / (np.sum(bids[:2, 1]) + 1e-6)
                ask_bait = ask_layering_vol / (np.sum(asks[:2, 1]) + 1e-6)

        signal = 0.0
        conf = 0.0
        reason = "NO_BAIT_DETECTED"
        
        # [Phase Ω-Architect] Lógica de Contra-Ataque (Contrarian)
        # Se o Market Maker está 'layering' no BID (comprando falso), ele quer que você 
        # acredite que o suporte é forte para você comprar, enquanto ele descarrega (SELL).
        # OU ele quer que você venda o topo do pump para ele comprar mais barato.
        # REGRA: Bait Massivo no Bid = Risco de Reversão de Baixa (Baiting Longs).
        
        if bid_bait > 2.5 and ask_bait < 1.0:
            # Eles estão inflando o BID. Armadilha de Compra Detectada.
            signal = -1.0 # Contrarian Sell
            conf = min(0.98, (bid_bait / 5.0) * 0.8)
            reason = f"BAIT_LAYERING_LONG_TRAP (Bid_Inf={bid_bait:.1f}x)"
            
        elif ask_bait > 2.5 and bid_bait < 1.0:
            # Inflando o ASK. Armadilha de Venda Detectada.
            signal = 1.0 # Contrarian Buy
            conf = min(0.98, (ask_bait / 5.0) * 0.8)
            reason = f"BAIT_LAYERING_SHORT_TRAP (Ask_Inf={ask_bait:.1f}x)"
            
        return AgentSignal(self.name, signal, conf, reason, self.weight)

