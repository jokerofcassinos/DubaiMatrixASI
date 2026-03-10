"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — PARAGON AGENTS (Phase Ω)                    ║
║     Inteligência Suprema (Nível 10): Teoria dos Jogos Evolutiva, Assimetria ║
║     de Informação e Manipulação de Expectativas (Bait & Switch).             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal

class AsymmetricInformationAgent(BaseAgent):
    """
    [Phase Ω-Paragon] Sensor de Assimetria de Informação.
    Mede a divergência entre a 'Volatilidade Realizada' (Preço no Spot) e a 
    'Agressividade do Fluxo' (Tick Delta). Quando o preço fica parado mas o 
    Volume/Delta explode em uma direção, sabemos que 'Alguém Sabe de Algo' 
    (Information Asymmetry). A ASI se posiciona a favor desse fluxo oculto.
    """
    def __init__(self, weight=3.7):
        super().__init__("AsymmetricInfo", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 20:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)
        volumes = np.array(candles_m1["tick_volume"], dtype=np.float64)
        highs = np.array(candles_m1["high"], dtype=np.float64)
        lows = np.array(candles_m1["low"], dtype=np.float64)
        
        # O quão o preço andou (Realized Volatility)
        recent_price_change = abs(closes[-1] - closes[-5]) / closes[-5]
        
        # O quanto de 'esforço' foi aplicado (Volume Pressure)
        recent_vol = np.mean(volumes[-5:])
        avg_vol = np.mean(volumes[-20:-5]) + 1e-6
        vol_ratio = recent_vol / avg_vol
        
        signal = 0.0
        conf = 0.0
        reason = "SYMMETRIC_MARKET"
        
        # Anomalia: Muito esforço (Volume > 3x), nenhum resultado (Variação < 0.05%)
        # Indica que um Institutional está defendendo agressivamente o nível.
        if vol_ratio > 3.0 and recent_price_change < 0.0005:
            # Eles estão absorvendo tudo. Qual a direção original do preço antes do freio?
            macro_trend = closes[-5] - closes[-20]
            if macro_trend < 0:
                # Estava caindo, freou com volume brutal. Acumulação Institucional!
                signal = 1.0 # Buy
                conf = 0.95
                reason = f"INFO_ASYMMETRY_BULL_ABSORB (Vol={vol_ratio:.1f}x, PriceFlat)"
            else:
                # Estava subindo, freou com volume brutal. Distribuição Institucional!
                signal = -1.0 # Sell
                conf = 0.95
                reason = f"INFO_ASYMMETRY_BEAR_DISTRIB (Vol={vol_ratio:.1f}x, PriceFlat)"
                
        return AgentSignal(self.name, signal, conf, reason, self.weight)


class BaitAndSwitchDetectorAgent(BaseAgent):
    """
    [Phase Ω-Paragon] Teoria dos Jogos - Bait & Switch (A Isca e a Troca).
    Detecta o padrão de 'Violent Shakeout' (V-Reversals microscópicas).
    Grandes players jogam o preço rapidamente em uma direção (A Isca) para 
    estourar os stops de quem está certo, antes de levar o preço na direção real (A Troca).
    A ASI aprendeu a ignorar a isca e comprar o retorno.
    """
    def __init__(self, weight=3.9):
        super().__init__("BaitAndSwitch", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 10:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)
        opens = np.array(candles_m1["open"], dtype=np.float64)
        lows = np.array(candles_m1["low"], dtype=np.float64)
        highs = np.array(candles_m1["high"], dtype=np.float64)
        
        atr = snapshot.indicators.get("M1_atr_14", [20.0])[-1]
        
        c0, c1, c2 = closes[-1], closes[-2], closes[-3]
        o0, o1, o2 = opens[-1], opens[-2], opens[-3]
        
        signal = 0.0
        conf = 0.0
        reason = "NO_BAIT_DETECTED"
        
        # Bullish Bait & Switch (Bear Trap)
        # O candle -2 foi uma vela de queda MASSIVA (Isca: Assustar compradores)
        # O candle atual (-1) e o anterior (0) já engolfaram ou formaram pavio longo.
        if c2 < o2 and (o2 - c2) > atr * 1.5: # Drop brutal
            if c0 > c2 and (c0 - lows[-1]) > atr * 1.0: # Rejeição violenta de volta pra cima
                # O movimento de queda era falso.
                signal = 1.0
                conf = 0.98
                reason = "BEAR_TRAP_SHAKEOUT_COMPLETED (Buy the Real Move)"
                
        # Bearish Bait & Switch (Bull Trap)
        # O candle -2 foi uma vela verde MASSIVA (Isca: FOMO Retail)
        elif c2 > o2 and (c2 - o2) > atr * 1.5: # Pump brutal
            if c0 < c2 and (highs[-1] - c0) > atr * 1.0: # Rejeição violenta de volta pra baixo
                signal = -1.0
                conf = 0.98
                reason = "BULL_TRAP_SHAKEOUT_COMPLETED (Sell the Real Move)"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class EvolutionaryNashEquilibriumAgent(BaseAgent):
    """
    [Phase Ω-Paragon] Equilíbrio de Nash Evolutivo.
    Em um jogo PvP, se todos usam a mesma estratégia, a vantagem zera.
    A ASI tenta detectar quando o mercado atingiu um "Equilíbrio de Nash"
    (ex: baixa liquidez extrema onde ninguém tem vantagem de agir primeiro).
    Nesse momento, a ASI atua como um "Agente Caótico Aleatório", injetando 
    micro-ordens agressivas para forçar a quebra do equilíbrio e ver como os 
    outros algoritmos reagem.
    """
    def __init__(self, weight=3.2):
        super().__init__("EvolutionaryNash", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 30:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)
        atr = snapshot.indicators.get("M1_atr_14", [20.0])[-1]
        
        # Medimos a "paralisia" do mercado (Equilíbrio)
        recent_range = np.max(closes[-10:]) - np.min(closes[-10:])
        
        signal = 0.0
        conf = 0.0
        reason = "MARKET_OUT_OF_EQUILIBRIUM"
        
        if recent_range < atr * 0.2:
            # O mercado está totalmente morto/travado. Todos os bots estão esperando.
            # O Equilíbrio de Nash diz que quem se mover primeiro pode perder (pegar spread ruim)
            # A ASI detecta esse impasse e se prepara para o bote.
            
            # Olhamos a estrutura micro de 30 velas atrás. 
            bias = closes[-1] - closes[-30]
            
            # Nós sugerimos FORÇAR O ROMPIMENTO na direção estrutural
            direction = np.sign(bias) if bias != 0 else 1.0
            signal = direction * 0.8
            conf = 0.90 # Alta confiança de que o rompimento vai ser violento quando ocorrer
            reason = f"NASH_EQUILIBRIUM_DEADLOCK (Range={recent_range:.1f} < 0.2xATR). FORCING BREAKOUT."
            
        return AgentSignal(self.name, signal, conf, reason, self.weight)