"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — VOID AGENTS (Phase Ω)                       ║
║     Inteligência Suprema (Nível 18): Cosmologia do Livro de Ofertas,         ║
║     Radiação Hawking, Buracos Brancos e Lente Gravitacional.                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal

class WhiteHoleInjectionAgent(BaseAgent):
    """
    [Phase Ω-Void] Injeção de Buraco Branco.
    Enquanto Buracos Negros (Liquidity Pools) absorvem preço, Buracos Brancos
    são injeções explosivas e repentinas de liquidez no spread, "empurrando" 
    violentamente o mercado. Detecta o surgimento instantâneo de ordens limitadas 
    maciças (Market Maker ativando o modo de propulsão).
    """
    def __init__(self, weight=4.4):
        super().__init__("WhiteHoleInjection", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        book = snapshot.book
        if not book or not book.get("bids") or not book.get("asks"):
            return AgentSignal(self.name, 0.0, 0.0, "NO_BOOK_DATA", self.weight)

        bids = np.array([[b["price"], b["volume"]] for b in book["bids"]], dtype=np.float64)
        asks = np.array([[a["price"], a["volume"]] for a in book["asks"]], dtype=np.float64)
        
        if len(bids) < 3 or len(asks) < 3:
            return AgentSignal(self.name, 0.0, 0.0, "SHALLOW_BOOK", self.weight)
            
        # Analisar a parede nas 3 primeiras camadas do spread
        bid_wall = np.sum(bids[:3, 1])
        ask_wall = np.sum(asks[:3, 1])
        
        # Média móvel de volume do tick (para saber o que é "maciço")
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["tick_volume"]) < 10:
            return AgentSignal(self.name, 0.0, 0.0, "NO_VOL_DATA", self.weight)
            
        avg_tick_vol = np.mean(candles_m1["tick_volume"][-10:]) + 1e-6
        
        signal = 0.0
        conf = 0.0
        reason = "NO_WHITE_HOLE"
        
        # Se a parede de Bid for monstruosa comparada ao volume histórico normal (Injeção)
        # e muito maior que a parede de Ask
        if bid_wall > (avg_tick_vol * 5.0) and bid_wall > (ask_wall * 4.0):
            signal = 1.0 # Propulsão de alta
            conf = 0.95
            reason = f"WHITE_HOLE_BULL_INJECTION (BidWall={bid_wall:.0f} vs Ask={ask_wall:.0f})"
            
        elif ask_wall > (avg_tick_vol * 5.0) and ask_wall > (bid_wall * 4.0):
            signal = -1.0 # Propulsão de baixa
            conf = 0.95
            reason = f"WHITE_HOLE_BEAR_INJECTION (AskWall={ask_wall:.0f} vs Bid={bid_wall:.0f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class HawkingRadiationAgent(BaseAgent):
    """
    [Phase Ω-Void] Radiação Hawking (Evaporação de Liquidez).
    Buracos Negros (paredes de liquidez) evaporam com o tempo devido ao cancelamento
    de ordens (Spoofing que desiste) ou micro-agressões (Radiação Hawking).
    Se o agente percebe que uma resistência gigante está encolhendo mais rápido
    do que o preço a ataca, ele prevê a evaporação total e o rompimento subsequente.
    """
    def __init__(self, weight=3.8):
        super().__init__("HawkingRadiation", weight)
        self.last_bid_wall = 0.0
        self.last_ask_wall = 0.0

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        book = snapshot.book
        if not book or not book.get("bids") or not book.get("asks"):
            return AgentSignal(self.name, 0.0, 0.0, "NO_BOOK_DATA", self.weight)

        bids = np.array([[b["price"], b["volume"]] for b in book["bids"]], dtype=np.float64)
        asks = np.array([[a["price"], a["volume"]] for a in book["asks"]], dtype=np.float64)
        
        if len(bids) < 10 or len(asks) < 10:
            return AgentSignal(self.name, 0.0, 0.0, "SHALLOW_BOOK", self.weight)
            
        current_bid_wall = np.max(bids[:, 1])
        current_ask_wall = np.max(asks[:, 1])
        
        signal = 0.0
        conf = 0.0
        reason = "NO_RADIATION_DETECTED"
        
        # Se nós temos estado anterior para comparar a "evaporação"
        if self.last_bid_wall > 0 and self.last_ask_wall > 0:
            # Se a parede vendedora está "evaporando" rapidamente (-30% em um tick de análise)
            if current_ask_wall < self.last_ask_wall * 0.7:
                # O bloqueio de alta está sumindo (radiação hawking / remoção). Preço vai subir.
                signal = 1.0
                conf = 0.85
                reason = f"HAWKING_EVAPORATION_ASK (Wall shrink {self.last_ask_wall:.0f} -> {current_ask_wall:.0f})"
                
            # Se a parede compradora está "evaporando"
            elif current_bid_wall < self.last_bid_wall * 0.7:
                # O suporte está sumindo. Preço vai cair.
                signal = -1.0
                conf = 0.85
                reason = f"HAWKING_EVAPORATION_BID (Wall shrink {self.last_bid_wall:.0f} -> {current_bid_wall:.0f})"
                
        # Atualizar memória do estado da parede
        self.last_bid_wall = current_bid_wall
        self.last_ask_wall = current_ask_wall

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class GravitationalLensingAgent(BaseAgent):
    """
    [Phase Ω-Void] Lente Gravitacional.
    Objetos de massa extrema curvam o caminho da luz. No mercado, grandes blocos
    institucionais curvam a trajetória do preço. O preço não necessariamente atinge
    o bloco, mas "orbita" ao redor dele (Lente). Se o preço tenta subir, sofre lente
    por um bloco massivo de Ask, oscila sem força e começa a curvar para baixo,
    a ASI executa o "slingshot" (Estilingue) na direção oposta.
    """
    def __init__(self, weight=4.0):
        super().__init__("GravitationalLensing", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 5:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)
        
        book = snapshot.book
        if not book or not book.get("bids") or not book.get("asks"):
            return AgentSignal(self.name, 0.0, 0.0, "NO_BOOK_DATA", self.weight)

        bids = np.array([[b["price"], b["volume"]] for b in book["bids"]], dtype=np.float64)
        asks = np.array([[a["price"], a["volume"]] for a in book["asks"]], dtype=np.float64)
        
        # Encontrar o ponto de maior massa (gravidade) no book
        max_bid_idx = np.argmax(bids[:, 1])
        max_ask_idx = np.argmax(asks[:, 1])
        
        max_bid_vol = bids[max_bid_idx, 1]
        max_ask_vol = asks[max_ask_idx, 1]
        
        avg_vol = (np.mean(bids[:, 1]) + np.mean(asks[:, 1])) / 2.0 + 1e-6
        
        signal = 0.0
        conf = 0.0
        reason = "NO_LENSING_EFFECT"
        
        # Se existe um "Buraco Negro" massivo de Ask (Resistência brutal)
        if max_ask_vol > avg_vol * 5.0:
            # Verificar se o preço está sendo "curvado" por ele
            # O preço tentou subir nas últimas velas mas falhou e começou a cair (Slingshot effect)
            if closes[-3] < closes[-2] and closes[-1] < closes[-2]:
                # Trajetória curvada (Lensing). A gravidade repeliu/orbitou o preço.
                signal = -1.0
                conf = 0.92
                reason = f"GRAVITATIONAL_LENSING_BEAR (Orbiting Ask Wall Vol={max_ask_vol:.0f})"
                
        # Buraco Negro massivo de Bid (Suporte brutal)
        elif max_bid_vol > avg_vol * 5.0:
            # Preço tentou cair, orbitou a massa e começou a subir
            if closes[-3] > closes[-2] and closes[-1] > closes[-2]:
                signal = 1.0
                conf = 0.92
                reason = f"GRAVITATIONAL_LENSING_BULL (Orbiting Bid Wall Vol={max_bid_vol:.0f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)
