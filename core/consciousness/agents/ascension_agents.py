"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — ASCENSION AGENTS (Phase Ω)                  ║
║     Inteligência Suprema (Nível 15): Arquitetura de Fluxo Multidimensional, ║
║     Diferenciação de Absorção Institucional e Filtro de Fake Breakouts.      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal

class OrderBookImbalanceAgent(BaseAgent):
    """
    [Phase Ω-Ascension] Desequilíbrio Multidimensional do Order Book.
    Enquanto a maioria olha para o 'Volume do Tick' (passado), este agente olha para
    a pressão da 'Fila de Ordens' (futuro). Se o preço está subindo rápido (pump), 
    mas a parede de Ask (venda) está crescendo muito mais rápido que o Bid (compra),
    o movimento de alta é oco. É uma subida apenas para preencher a liquidez de venda.
    """
    def __init__(self, weight=4.0):
        super().__init__("OrderBookImbalance", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        book = snapshot.book
        if not book or not book.get("bids") or not book.get("asks"):
            return AgentSignal(self.name, 0.0, 0.0, "NO_BOOK_DATA", self.weight)

        bids = np.array([[b["price"], b["volume"]] for b in book["bids"]], dtype=np.float64)
        asks = np.array([[a["price"], a["volume"]] for a in book["asks"]], dtype=np.float64)
        
        if len(bids) == 0 or len(asks) == 0:
            return AgentSignal(self.name, 0.0, 0.0, "EMPTY_SIDES", self.weight)

        # Concentrar nas camadas iniciais onde ocorre o HFT
        near_bid_vol = np.sum(bids[:5, 1])
        near_ask_vol = np.sum(asks[:5, 1])
        
        total_vol = near_bid_vol + near_ask_vol
        if total_vol == 0:
            return AgentSignal(self.name, 0.0, 0.0, "NO_LIQUIDITY", self.weight)

        imbalance = (near_bid_vol - near_ask_vol) / total_vol
        
        # O preço de fechamento (para verificar divergência)
        candles_m1 = snapshot.candles.get("M1")
        if candles_m1 and len(candles_m1["close"]) >= 3:
            closes = np.array(candles_m1["close"], dtype=np.float64)
            price_delta = closes[-1] - closes[-3]
        else:
            price_delta = 0.0

        signal = 0.0
        conf = 0.0
        reason = "BALANCED_BOOK"
        
        # Se o preço está subindo forte, mas o book está pesadamente carregado no Ask (Venda)
        if price_delta > 0 and imbalance < -0.4:
            # Fake Breakout Bullish. Subindo contra uma parede invisível.
            signal = -1.0
            conf = 0.95
            reason = f"OFI_BULL_TRAP (Price UP, Book Ask Heavy: Imb={imbalance:.2f})"
            
        # Se o preço está caindo forte, mas o book está pesadamente carregado no Bid (Compra)
        elif price_delta < 0 and imbalance > 0.4:
            # Fake Breakout Bearish. Caindo num colchão de absorção.
            signal = 1.0
            conf = 0.95
            reason = f"OFI_BEAR_TRAP (Price DOWN, Book Bid Heavy: Imb={imbalance:.2f})"
        else:
            # Segue a força do book se não houver divergência
            if imbalance > 0.5:
                signal = 1.0
                conf = 0.80
                reason = f"OFI_BULL_PULL (Imb={imbalance:.2f})"
            elif imbalance < -0.5:
                signal = -1.0
                conf = 0.80
                reason = f"OFI_BEAR_PUSH (Imb={imbalance:.2f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class BlowOffTopDetectorAgent(BaseAgent):
    """
    [Phase Ω-Ascension] Detector de 'Blow-Off Top' e 'Climax Bottom'.
    Uma métrica fatal: quando o volume alcança um pico histórico EXATAMENTE 
    no momento em que o preço atinge as bandas externas (exaustão), é o fim
    da festa institucional. O 'Smart Money' usou a liquidez do FOMO para sair.
    """
    def __init__(self, weight=4.2):
        super().__init__("BlowOffDetector", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 50:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)
        highs = np.array(candles_m1["high"], dtype=np.float64)
        lows = np.array(candles_m1["low"], dtype=np.float64)
        volumes = np.array(candles_m1["tick_volume"], dtype=np.float64)
        
        # Volumetria de pico (Z-Score de Volume)
        vol_mean = np.mean(volumes[-50:-2])
        vol_std = np.std(volumes[-50:-2]) + 1e-6
        current_vol_z = (volumes[-1] - vol_mean) / vol_std
        
        atr = snapshot.indicators.get("M5_atr_14", [30.0])[-1]
        
        # Cinemática da última vela
        c0, o0 = closes[-1], candles_m1["open"][-1]
        h0, l0 = highs[-1], lows[-1]
        
        signal = 0.0
        conf = 0.0
        reason = "NORMAL_KINEMATICS"
        
        # BLOW-OFF TOP: Preço disparou (vela verde longa), volume é bizarro de alto (Z > 3),
        # mas o fechamento já está longe da máxima (pavio superior se formando).
        if current_vol_z > 3.0 and c0 > o0:
            wick_size = h0 - c0
            body_size = c0 - o0
            if body_size > atr * 0.5 and wick_size > body_size * 0.3:
                # É um Blow-Off Top. Exaustão fatal.
                signal = -1.0
                conf = 0.98
                reason = f"BLOW_OFF_TOP_FATAL (VolZ={current_vol_z:.1f}, Wick={wick_size:.1f})"
                
        # CLIMAX BOTTOM: Preço despencou, volume absurdo, mas deixou pavio inferior.
        elif current_vol_z > 3.0 and c0 < o0:
            wick_size = c0 - l0
            body_size = o0 - c0
            if body_size > atr * 0.5 and wick_size > body_size * 0.3:
                signal = 1.0
                conf = 0.98
                reason = f"CLIMAX_BOTTOM_FATAL (VolZ={current_vol_z:.1f}, Wick={wick_size:.1f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)
