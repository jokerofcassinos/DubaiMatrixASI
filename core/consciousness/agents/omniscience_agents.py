"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — OMNISCIENCE AGENTS (Phase Ω)                ║
║     Sistemas de Correlação Global, Detecção de Spoofing e Entrelaçamento.    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import Optional
from core.consciousness.agents.base import BaseAgent, AgentSignal
from utils.decorators import catch_and_log

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

class OrderFlowShannonSentimentAgent(BaseAgent):
    """
    [Phase Ω-8] Entropia de Shannon aplicada ao Fluxo de Ordens Direcional.
    Mede matematicamente a incerteza do comportamento de fluxo.
    Calcula a probabilidade do próximo tick baseada na distribuição de Volume Comprador vs Vendedor.
    """
    def __init__(self, weight=2.8):
        super().__init__("OrderFlowShannonSentiment", weight)
        self.needs_orderflow = False # Computa via snapshot.recent_ticks (TICK DOMAIN)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        ticks = snapshot.recent_ticks
        if not ticks or len(ticks) < 100:
            return AgentSignal(self.name, 0.0, 0.0, "NOT_ENOUGH_TICKS", self.weight)

        # Analisar os últimos 200 ticks de altíssima latência
        analyze_ticks = ticks[-200:]
        
        buy_vol = 0.0
        sell_vol = 0.0
        
        for t in analyze_ticks:
            try:
                last = float(t.get("last", 0.0))
                bid = float(t.get("bid", 0.0))
                ask = float(t.get("ask", 0.0))
                vol = float(t.get("volume", 0.0) or t.get("volume_real", 0.0))
                
                if last >= ask:
                    buy_vol += vol
                elif last <= bid:
                    sell_vol += vol
            except (ValueError, TypeError):
                continue

        total_vol = buy_vol + sell_vol
        if total_vol <= 0:
            return AgentSignal(self.name, 0.0, 0.0, "NO_VOLUME", self.weight)

        p_buy = buy_vol / total_vol
        p_sell = sell_vol / total_vol
        
        # Calcular Entropia de Shannon (H) em bits -> máx 1.0 para sistema binário (Buy/Sell)
        h_buy = -p_buy * np.log2(p_buy) if p_buy > 0 else 0.0
        h_sell = -p_sell * np.log2(p_sell) if p_sell > 0 else 0.0
        entropy = h_buy + h_sell

        signal = 0.0
        conf = 0.0
        reason = f"SHANNON_ENTROPY: {entropy:.3f} (Balanced)"

        # [Ω-8] COLAPSO DE ENTROPIA
        # Se entropia cai abaixo de 0.25, a distribuição tá ~95/5. Extrema previsibilidade.
        if entropy < 0.25:
            # Fluxo previsível e violento (Sweep Institucional / Tape Ripping)
            if p_buy > p_sell:
                signal = 0.90 # Forte sinal de Compra agressiva (Ripping the asks)
                conf = 1.0 - entropy # Quanto menor a entropia, maior a certeza (max 1.0)
                reason = f"BUY_SHANNON_COLLAPSE (H={entropy:.3f}, p_buy={p_buy*100:.1f}%)"
            else:
                signal = -0.90 # Forte sinal de Venda agressiva (Smashing the bids)
                conf = 1.0 - entropy
                reason = f"SELL_SHANNON_COLLAPSE (H={entropy:.3f}, p_sell={p_sell*100:.1f}%)"
                
        # [Ω-8] TENDÊNCIA ESTRUTURAL
        elif entropy < 0.85:
            if p_buy > p_sell:
                signal = 0.40
                conf = 0.70
                reason = f"BUY_FLOW_TENDENCY (H={entropy:.3f}, p_buy={p_buy*100:.1f}%)"
            else:
                signal = -0.40
                conf = 0.70
                reason = f"SELL_FLOW_TENDENCY (H={entropy:.3f}, p_sell={p_sell*100:.1f}%)"

        return AgentSignal(self.name, signal, conf, reason, self.weight)
