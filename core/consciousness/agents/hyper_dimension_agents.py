"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — HYPER-DIMENSION AGENTS (Phase Ω)            ║
║     Inteligência Suprema (Nível 26): Padrões de Turing, Bio-Metabolismo      ║
║     e Decoerência de Estados-Próprios (Eigenstate).                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal

class TuringPatternAgent(BaseAgent):
    """
    [Phase Ω-Hyper-Dimension] Padrões de Turing (Morfogênese).
    Baseado na teoria de Alan Turing sobre como padrões (listras de zebra, manchas)
    se formam na natureza via reações-difusão. No mercado, a liquidez (Bid/Ask)
    se difunde e reage às agressões. O agente detecta a formação de "Manchas de Liquidez"
    estáveis que precedem a criação de novos Order Blocks.
    """
    def __init__(self, weight=4.6):
        super().__init__("TuringPattern", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        book = snapshot.book
        if not book or not book.get("bids") or not book.get("asks"):
            return AgentSignal(self.name, 0.0, 0.0, "NO_BOOK_DATA", self.weight)

        bids = np.array([[b["price"], b["volume"]] for b in book["bids"]], dtype=np.float64)
        asks = np.array([[a["price"], a["volume"]] for a in book["asks"]], dtype=np.float64)
        
        if len(bids) < 10 or len(asks) < 10:
            return AgentSignal(self.name, 0.0, 0.0, "SHALLOW_BOOK", self.weight)

        # Simular Difusão de Liquidez (Laplaciano Discreto do Volume)
        # L(v) = v[i+1] - 2*v[i] + v[i-1]
        bid_vol = bids[:, 1]
        ask_vol = asks[:, 1]
        
        bid_laplacian = np.diff(bid_vol, n=2)
        ask_laplacian = np.diff(ask_vol, n=2)
        
        # Padrões de Turing emergem quando o laplaciano mostra "ilhas" de alta densidade
        # cercadas por zonas de depleção.
        bid_islands = np.sum(bid_laplacian > np.mean(bid_laplacian) * 2.0)
        ask_islands = np.sum(ask_laplacian > np.mean(ask_laplacian) * 2.0)
        
        signal = 0.0
        conf = 0.0
        reason = "HOMOGENEOUS_LIQUIDITY"
        
        # Se existem ilhas de Turing (Clusters instáveis) se formando
        if bid_islands > ask_islands + 2:
            # Compradores estão se agrupando em padrões defensivos (Morfogênese Bullish)
            signal = 1.0
            conf = 0.92
            reason = f"TURING_BULL_MORPHOGENESIS (Islands={bid_islands} vs {ask_islands})"
        elif ask_islands > bid_islands + 2:
            # Vendedores estão se agrupando
            signal = -1.0
            conf = 0.92
            reason = f"TURING_BEAR_MORPHOGENESIS (Islands={ask_islands} vs {bid_islands})"
            
        return AgentSignal(self.name, signal, conf, reason, self.weight)


class EigenstateDecoherenceAgent(BaseAgent):
    """
    [Phase Ω-Hyper-Dimension] Decoerência de Estados-Próprios.
    Mede a velocidade com que a "Matriz de Covariância" do enxame perde estabilidade.
    Na física quântica, a decoerência é o fim da superposição. No mercado,
    é o momento em que a indecisão (superposição) colapsa e todos os robôs
    atiram na mesma direção. O agente detecta a decoerência ANTES do sinal bruto explodir.
    """
    def __init__(self, weight=4.9):
        super().__init__("EigenstateDecoherence", weight)
        self.last_entropy = 0.5

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        # Pega a entropia sistêmica reportada pelo snapshot/metadados
        current_entropy = snapshot.metadata.get("tick_entropy", 0.5)
        
        # Decoerência = Redução súbita de entropia informacional
        decoherence_speed = self.last_entropy - current_entropy
        self.last_entropy = current_entropy
        
        signal = 0.0
        conf = 0.0
        reason = "COHERENT_VACUUM"
        
        # Se a entropia está caindo rápido (Decoerência), o colapso está próximo
        if decoherence_speed > 0.15:
            # O sistema está se organizando. Para qual lado?
            tick_velocity = snapshot.metadata.get("tick_velocity", 0.0)
            if abs(tick_velocity) > 5.0:
                signal = np.sign(tick_velocity)
                conf = 0.97
                reason = f"QUANTUM_DECOHERENCE_COLLAPSE (Speed={decoherence_speed:.2f}, Vector={signal})"
                
        return AgentSignal(self.name, signal, conf, reason, self.weight)
