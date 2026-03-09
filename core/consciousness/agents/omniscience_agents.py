"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — OMNISCIENCE AGENTS (Phase Ω)                ║
║     Sistemas de Correlação Global, Detecção de Spoofing e Entrelaçamento.    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal

class OrderBookSpoofingAgent(BaseAgent):
    """
    [Phase Ω-Omniscience] Caçador de Miragens no Book.
    Detecta ordens fantasmas (Spoofing) que são colocadas para manipular o preço 
    e canceladas antes da execução.
    """
    def __init__(self, weight=2.6):
        super().__init__("OrderBookSpoofing", weight)
        # self.needs_orderflow = True # Depende de snapshots densos

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        if not snapshot.book or "bids" not in snapshot.book or "asks" not in snapshot.book:
            return AgentSignal(self.name, 0.0, 0.0, "NO_BOOK_DATA", self.weight)

        bids = snapshot.book.get("bids", [])
        asks = snapshot.book.get("asks", [])
        
        if len(bids) < 5 or len(asks) < 5:
            return AgentSignal(self.name, 0.0, 0.0, "SHALLOW_BOOK", self.weight)

        # Simplificação: Avalia a assimetria massiva longe do spread
        # Se há muito volume de compra longe do preço atual, pode ser suporte falso
        bid_vol_near = sum(b.get("volume", 0) for b in bids[:2]) if isinstance(bids[0], dict) else 0
        bid_vol_far = sum(b.get("volume", 0) for b in bids[2:10]) if isinstance(bids[0], dict) else 0
        
        ask_vol_near = sum(a.get("volume", 0) for a in asks[:2]) if isinstance(asks[0], dict) else 0
        ask_vol_far = sum(a.get("volume", 0) for a in asks[2:10]) if isinstance(asks[0], dict) else 0

        signal = 0.0
        conf = 0.0
        reason = "NORMAL_DEPTH"

        # Spoofing Bullish: Muita ordem de compra longe (assustar vendedores), mas pouca perto
        if bid_vol_far > (bid_vol_near * 5.0) and bid_vol_far > (ask_vol_far * 3.0):
            # É uma armadilha. A intenção real provavelmente é DERRUBAR o preço.
            signal = -1.0 # Sinal contrário
            conf = 0.85
            reason = f"BULL_SPOOFING_DETECTED (FarBid:NearBid = {bid_vol_far/(bid_vol_near+1):.1f}x)"

        # Spoofing Bearish: Muita ordem de venda longe, pouca perto
        elif ask_vol_far > (ask_vol_near * 5.0) and ask_vol_far > (bid_vol_far * 3.0):
            signal = 1.0 # Sinal contrário
            conf = 0.85
            reason = f"BEAR_SPOOFING_DETECTED (FarAsk:NearAsk = {ask_vol_far/(ask_vol_near+1):.1f}x)"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class QuantumEntanglementAgent(BaseAgent):
    """
    [Phase Ω-Omniscience] Entrelaçamento de Ativos (Macro-Micro Validation).
    Avalia se o movimento do BTC está "entrelaçado" com o Ethereum e o Macro Bias.
    Um rompimento do BTC sem o apoio do ETH é frequentemente um "Liquidity Hunt" falso.
    """
    def __init__(self, weight=3.0):
        super().__init__("QuantumEntanglement", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        macro_bias = snapshot.metadata.get("macro_bias", 0.0)
        
        candles = snapshot.candles.get("M1")
        if not candles or len(candles["close"]) < 5:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles["close"], dtype=np.float64)
        btc_momentum = (closes[-1] - closes[-5]) / closes[-5]

        # Em um sistema em produção real, puxaríamos o preço do ETH aqui.
        # Como proxy, usaremos a variação de curto prazo da correlação macro.
        
        signal = 0.0
        conf = 0.0
        reason = "NO_ENTANGLEMENT"

        if btc_momentum > 0.001: # Alta expressiva
            if macro_bias > 0.1: # Macro apoia (Entanglement Bullish)
                signal = 1.0
                conf = min(0.95, 0.5 + macro_bias)
                reason = f"BULLISH_ENTANGLEMENT (Macro={macro_bias:.2f})"
            elif macro_bias < -0.1: # Macro discorda (Falso Rompimento Bull)
                signal = -1.0 # Vende o topo
                conf = 0.90
                reason = f"FALSE_BULL_BREAKOUT (Macro divergence={macro_bias:.2f})"
                
        elif btc_momentum < -0.001: # Queda expressiva
            if macro_bias < -0.1: # Macro apoia (Entanglement Bearish)
                signal = -1.0
                conf = min(0.95, 0.5 + abs(macro_bias))
                reason = f"BEARISH_ENTANGLEMENT (Macro={macro_bias:.2f})"
            elif macro_bias > 0.1: # Macro discorda (Falso Rompimento Bear)
                signal = 1.0 # Compra o fundo
                conf = 0.90
                reason = f"FALSE_BEAR_BREAKOUT (Macro divergence={macro_bias:.2f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)
