"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — GLOBAL & WHALE AGENTS (Phase 13)            ║
║     Agentes que leem dados fora do gráfico: Sentimento macro, On-chain,    ║
║     mempool, dominância e movimentações de baleias (Web Scrapers data).     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import Optional

from core.consciousness.agents.base import AgentSignal, BaseAgent
from utils.decorators import catch_and_log


class SentimentFearGreedAgent(BaseAgent):
    """
    Consome os dados do SentimentScraper (metadados do snapshot).
    Traduz Fear & Greed Index e dados do CoinGecko em força direcional.
    Mercado em Extreme Greed = Alinhamento de topo (possível reversão se acompanhado de divergência).
    Mercado em Extreme Fear = Alinhamento de fundo.
    """
    def __init__(self, weight: float = 1.1):
        super().__init__("SentimentFearGreedAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        metadata = snapshot.metadata
        sentiment_score = metadata.get("sentiment_score")

        if sentiment_score is None:
            return AgentSignal(self.name, 0.0, 0.0, "No Sentiment Data", self.weight)

        # sentiment_score varia de -1.0 (Extreme Fear) a +1.0 (Extreme Greed)
        # Na teoria reflexiva, extremo sentimento institucional costuma ser "dumb money".
        # Porém, no início da tendência, sentimento funciona a favor.
        # Nós usamos um modelo não-linear: se o preço está forte e sentiment é moderado -> trend following
        # Se spread/volatility indicam reversão e sentiment está em Extremes (>0.8 ou <-0.8) -> fade the crowd

        signal = sentiment_score * 0.5  # Bias básico na direção do sentimento
        conf = abs(sentiment_score) * 0.8
        
        reason = f"Sentiment Bias ({sentiment_score:+.2f})"

        # Se for extremo (Greed > 0.8), e nós detectarmos divergência M5, isso reverte.
        # (O QuantumThoughtEngine vai somar isso com a DivergenceAgent)
        if sentiment_score > 0.8:
            reason = f"EXTREME GREED ({sentiment_score:+.2f}) — Warning: Euphoria"
        elif sentiment_score < -0.8:
            reason = f"EXTREME FEAR ({sentiment_score:+.2f}) — Warning: Panic"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class OnChainPressureAgent(BaseAgent):
    """
    Consome métricas do OnChainScraper (Mempool, Fees, Hashrate).
    Mempool engarrafado + taxas altas = forte atividade especulativa (geralmente pump local 
    antes de grandes despejos ou adoção maciça).
    """
    def __init__(self, weight: float = 1.3):
        super().__init__("OnChainPressureAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        metadata = snapshot.metadata
        network_pressure = metadata.get("network_pressure")

        if network_pressure is None:
            return AgentSignal(self.name, 0.0, 0.0, "No OnChain Data", self.weight)

        # network_pressure: -1.0 (Rede morrendo/suave c/ viés baixa) a +1.0 (Rede explodindo/Bullish)
        signal = network_pressure
        conf = abs(network_pressure)
        
        reason = f"On-Chain Pressure ({network_pressure:+.2f})"

        if network_pressure > 0.7:
            reason = f"HIGH ON-CHAIN CONGESTION ({network_pressure:+.2f}) — Network Heating Up"
        elif network_pressure < -0.7:
            reason = f"ON-CHAIN CAPITULATION ({network_pressure:+.2f}) — Network Cooling"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class MacroBiasAgent(BaseAgent):
    """
    Consome dados do MacroScraper (S&P500 proxy, Gold/BTC ratio, ETH dominance).
    Determina o Risco Global. Se macro_bias for hiper negativo, Bitcoin sofre 
    gravidade e trades LONG devem ser vetados ou minimizados.
    """
    def __init__(self, weight: float = 1.4):
        super().__init__("MacroBiasAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        metadata = snapshot.metadata
        macro_bias = metadata.get("macro_bias")

        if macro_bias is None:
            return AgentSignal(self.name, 0.0, 0.0, "No Macro Data", self.weight)

        # Bias direto
        signal = macro_bias
        # Confiança cresce quadraticamente com a força do bias macro
        conf = macro_bias ** 2
        
        reason = f"Macro Bias Vector ({macro_bias:+.2f})"

        if macro_bias > 0.6:
            reason = f"BULLISH MACRO TAILWIND ({macro_bias:+.2f}) — Global liquidity flowing"
        elif macro_bias < -0.6:
            reason = f"BEARISH MACRO HEADWIND ({macro_bias:+.2f}) — Global risk-off regime"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class WhaleTrackerAgent(BaseAgent):
    """
    Dedução de Baleias via OrderFlow HFT. 
    Busca single-ticks com 'volume_real' bizarramente gigantesco (ex: trade de 50+ BTCs num milissegundo).
    Isso é marca de Smart Money / Whale market-taking.
    """
    def __init__(self, weight: float = 1.8):
        super().__init__("WhaleTrackerAgent", weight)
        # Limite do que consideramos whale. (Depende do instrumento, usar 25 lts para BTC)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        ticks = snapshot.recent_ticks
        if len(ticks) < 10:
            return None

        # Identificar o volume massivo
        whale_threshold = 20.0  # Lotes
        
        signal = 0.0
        conf = 0.0
        reason = "No Whale Prints Detected"

        # Procurar do mais recente pro mais antigo (olhar os ultimos 20 ticks)
        for t in reversed(ticks[-20:]):
            vol = t.get("volume_real", t.get("volume", 0))
            if vol >= whale_threshold:
                # Baleia disparou a mercado. Qual lado?
                flags = t.get("flags", 0)
                # 32 = TICK_FLAG_BUY, 64 = TICK_FLAG_SELL no MT5
                is_buy = bool(flags & 32)
                is_sell = bool(flags & 64)
                
                # Fallback: tentar olhar bid vs ask logic se flags nao funfar
                if not is_buy and not is_sell:
                    if len(ticks) > 2:
                        is_buy = ticks[-1]["bid"] > ticks[-2]["bid"]
                        is_sell = ticks[-1]["bid"] < ticks[-2]["bid"]

                if is_buy:
                    signal = 1.0
                    conf = 1.0
                    reason = f"WHALE MARKET BUY DETECTED! ({vol:.1f} lots at {t['bid']})"
                    break
                elif is_sell:
                    signal = -1.0
                    conf = 1.0
                    reason = f"WHALE MARKET SELL DETECTED! ({vol:.1f} lots at {t['bid']})"
                    break

        return AgentSignal(self.name, signal, conf, reason, self.weight)
