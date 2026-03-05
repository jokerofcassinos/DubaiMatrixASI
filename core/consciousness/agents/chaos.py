"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — CHAOS & QUANTUM AGENTS (Phase 12)           ║
║     Agentes que operam baseados em Teoria do Caos, Teoria da Informação    ║
║     e Dinâmica Não-Linear.                                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import Optional
from scipy.stats import entropy

from core.consciousness.agents.base import AgentSignal, BaseAgent
from utils.decorators import catch_and_log


class InformationEntropyAgent(BaseAgent):
    """
    Teoria da Informação de Shannon:
    Calcula a entropia da distribuição dos retornos dos últimos ticks.
    Entropia alta = Caos / Ruído = Mercado aleatório.
    Entropia desabando rapidamente = Ordem surgindo = Dinheiro institucional
    injetando INFORMAÇÃO DIRECIONAL no preço.
    """
    def __init__(self, weight: float = 1.6):
        super().__init__("InformationEntropyAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        ticks = snapshot.recent_ticks
        if len(ticks) < 150:
            return None

        # Coletar preços dos últimos 150 ticks
        try:
            prices = np.array([t["bid"] for t in ticks[-150:]])
        except (KeyError, TypeError):
            return None

        # Calcular retornos
        returns = np.diff(prices)
        
        # Histograma de retornos (probabilidades de cada bin)
        counts, _ = np.histogram(returns, bins=10)
        probs = counts / np.sum(counts)
        
        # Filtrar zeros para o scipy.stats.entropy
        probs = probs[probs > 0]
        current_entropy = entropy(probs, base=2)

        signal = 0.0
        reason = f"Normal Entropy ({current_entropy:.2f} bits)"
        conf = 0.0

        # Se a entropia for muito baixa (< 1.5 bits), o mercado está extremamente determinístico
        if current_entropy < 1.0:
            direction = 1.0 if prices[-1] > prices[0] else -1.0
            signal = direction * 0.8
            conf = 0.9
            reason = f"CRITICAL LOW ENTROPY ({current_entropy:.2f} bits) — Deterministic Order Injection"
            
        # Se a entropia for muito alta, caos total (não operar)
        elif current_entropy > 2.8:
            signal = 0.0
            conf = 1.0  # Alta confiança de que é CAOS -> Força neutralidade
            reason = f"MAXIMUM CHAOS ({current_entropy:.2f} bits) — Random Walk"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class PhaseSpaceAttractorAgent(BaseAgent):
    """
    Dinâmica Não-Linear: Modelagem de Espaço de Fase.
    Plota a Velocidade do Preço (1ª derivada) vs Aceleração (2ª derivada).
    Se a trajetória coalescer em um "Atraente Estranho" (ponto central comprimido),
    indica que energia cinética está sendo armazenada para um rompimento massivo (Mola Comprimida).
    """
    def __init__(self, weight: float = 1.4):
        super().__init__("PhaseSpaceAttractorAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        closes = snapshot.m1_closes
        if len(closes) < 30:
            return None

        # Velocidade = Retorno M1
        velocity = np.diff(closes)
        # Aceleração = Mudança na Velocidade
        acceleration = np.diff(velocity)

        if len(acceleration) < 10:
            return None

        # Analisar os últimos 10 pontos no Espaço de Fase (Velocidade, Aceleração)
        recent_v = velocity[-10:]
        recent_a = acceleration[-10:]

        # Distância Euclidiana média da origem (0,0) indica a "órbita"
        orbit_radius = np.mean(np.sqrt(recent_v**2 + recent_a**2))
        
        # Desvio padrão global para contexto
        global_orbit = np.std(velocity) + np.std(acceleration)

        signal = 0.0
        reason = "Normal Phase Orbit"
        conf = 0.0

        if global_orbit > 0 and orbit_radius < (global_orbit * 0.1):
            # A mola está absurdamente comprimida no espaço de fase
            reason = f"PHASE SPACE COLLAPSE (Radius {orbit_radius:.4f}) — Kinetic Storage"
            conf = 0.7
            # Sem viés direcional, mas sinaliza bomba iminente. Vamos checar tendência macro para direção.
            macro_trend = 1.0 if closes[-1] > closes[-20] else -1.0
            signal = macro_trend * 0.4 
            
        elif global_orbit > 0 and orbit_radius > (global_orbit * 3.0):
            reason = f"PHASE SPACE EXPLOSION (Radius {orbit_radius:.4f}) — Chaotic Expansão"
            signal = 0.0 # Caos pós-rompimento

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class VPINProxyAgent(BaseAgent):
    """
    Volume-Synchronized Probability of Informed Trading (VPIN) Proxy.
    Mede a toxidade do fluxo institucional baseando-se em volume consumido em
    candles dominados por uma direção. Se VPIN é estratosférico, Market Makers
    vão recolher liquidez, e o preço continuará rasgando.
    """
    def __init__(self, weight: float = 1.5):
        super().__init__("VPINProxyAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        candles = snapshot.candles.get("M1")
        if candles is None:
            return None
            
        close = candles.get("close", [])
        open_p = candles.get("open", [])
        volume = candles.get("tick_volume", [])

        if len(close) < 20 or len(volume) < 20:
            return None

        # Calcular volume buy e sell aproximado 
        # (se bull candle, 70% buy / 30% sell; se bear, inverso)
        buy_vol = []
        sell_vol = []
        for i in range(len(close)):
            vol = volume[i]
            if close[i] > open_p[i]:
                buy_vol.append(vol * 0.7)
                sell_vol.append(vol * 0.3)
            else:
                buy_vol.append(vol * 0.3)
                sell_vol.append(vol * 0.7)

        recent_buy = sum(buy_vol[-5:])
        recent_sell = sum(sell_vol[-5:])
        total_recent = recent_buy + recent_sell

        if total_recent == 0:
            return None

        imbalance = abs(recent_buy - recent_sell) / total_recent

        signal = 0.0
        conf = 0.0
        reason = f"Normal toxic flow (Imb: {imbalance:.2f})"

        if imbalance > 0.8:
            direction = 1.0 if recent_buy > recent_sell else -1.0
            signal = direction * 0.9
            conf = 0.95
            reason = f"HIGH TOXIC FLOW (VPIN proxy {imbalance:.2f}) — Informed Institutional Trading"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class OrderBookEvaporationAgent(BaseAgent):
    """
    Dinâmica de Evaporação do DOM:
    Analisa não o volume estático do orderbook, mas a VELOCIDADE com que os bids/asks 
    desaparecem. Se bids desaparecem 3x mais rápido que o preço cai, é um 'Pull' (Spoofing reverso).
    """
    def __init__(self, weight: float = 1.7):
        super().__init__("OrderBookEvaporationAgent", weight)
        self.last_bid_vol = 0
        self.last_ask_vol = 0

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        book = snapshot.metadata.get("book")
        if not book:
            return None

        bids = book.get("bids", [])
        asks = book.get("asks", [])
        
        current_bid_vol = sum(b.get("volume", 0) for b in bids[:10])
        current_ask_vol = sum(a.get("volume", 0) for a in asks[:10])

        signal = 0.0
        reason = "DOM Stable"
        conf = 0.0

        if self.last_bid_vol > 0 and self.last_ask_vol > 0:
            bid_drop = (self.last_bid_vol - current_bid_vol) / self.last_bid_vol
            ask_drop = (self.last_ask_vol - current_ask_vol) / self.last_ask_vol

            # Se 60% dos bids sumiram subitamente num único ciclo (< 200ms)
            if bid_drop > 0.6:
                signal = -0.9 # Preço vai despencar rumo ao vácuo
                conf = 0.85
                reason = f"BID EVAPORATION ({bid_drop*100:.0f}% drops) — Liquidity Pulled, crashing"
                
            elif ask_drop > 0.6:
                signal = 0.9 # Preço vai disparar rumo ao vácuo
                conf = 0.85
                reason = f"ASK EVAPORATION ({ask_drop*100:.0f}% drops) — Offers Pulled, mooning"

        self.last_bid_vol = current_bid_vol
        self.last_ask_vol = current_ask_vol

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class CrossScaleConvergenceAgent(BaseAgent):
    """
    Ressonância de Frações Interdimensionais.
    Verifica se o fluxo de 1s, 1m, 5m e 15m estão ABSOLUTAMENTE apontando para
    o mesmo vetor. Alinhamento de astros.
    """
    def __init__(self, weight: float = 1.8):
        super().__init__("CrossScaleConvergenceAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        closes_m1 = snapshot.candles.get("M1", {}).get("close", [])
        closes_m5 = snapshot.candles.get("M5", {}).get("close", [])
        closes_m15 = snapshot.candles.get("M15", {}).get("close", [])
        ticks = snapshot.recent_ticks

        if len(closes_m1) < 2 or len(closes_m5) < 2 or len(closes_m15) < 2 or len(ticks) < 2:
            return None

        # Derivadas simples
        dir_tick = np.sign(ticks[-1].get("bid", 0) - ticks[0].get("bid", 0))
        dir_m1 = np.sign(closes_m1[-1] - closes_m1[-2])
        dir_m5 = np.sign(closes_m5[-1] - closes_m5[-2])
        dir_m15 = np.sign(closes_m15[-1] - closes_m15[-2])

        total_alignment = dir_tick + dir_m1 + dir_m5 + dir_m15

        signal = 0.0
        reason = "Scales Conflicting"
        conf = 0.0

        if total_alignment == 4:
            signal = 1.0
            conf = 1.0
            reason = "OMEGA ALIGNMENT (Tick, M1, M5, M15 ALL BULLISH)"
        elif total_alignment == -4:
            signal = -1.0
            conf = 1.0
            reason = "OMEGA ALIGNMENT (Tick, M1, M5, M15 ALL BEARISH)"

        return AgentSignal(self.name, signal, conf, reason, self.weight)
