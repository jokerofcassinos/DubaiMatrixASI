"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — AETHEL AGENTS (Phase Ω)                     ║
║     Inteligência Suprema (Nível 30): Teoria do Campo Unificado,             ║
║     Super-Simetria e Dinâmica de Fluidos de Éter.                           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal

class SupersymmetryAgent(BaseAgent):
    """
    [Phase Ω-Aethel] Super-Simetria (SUSY).
    Na física, cada partícula tem um super-parceiro. No mercado, o 'Preço'
    deveria ter um parceiro simétrico: o 'Momento do Volume'.
    Se a simetria quebra (ex: preço sobe mas o momento do volume cai), 
    o 'Super-parceiro' sumiu e o movimento é instável (Whipsaw iminente).
    A ASI detecta a quebra de simetria para evitar armadilhas de baixa massa.
    """
    def __init__(self, weight=4.7):
        super().__init__("Supersymmetry", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 10:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)
        vols = np.array(candles_m1["tick_volume"], dtype=np.float64)
        
        # Calcular 'Spins' (Direção e Força)
        price_spin = (closes[-1] - closes[-5]) / (np.std(closes[-10:]) + 1e-6)
        volume_spin = (vols[-1] - np.mean(vols[-5:])) / (np.std(vols[-10:]) + 1e-6)
        
        signal = 0.0
        conf = 0.0
        reason = "SYMMETRIC_STABILITY"
        
        # Quebra de Simetria (Preço e Volume em direções opostas em alta energia)
        if abs(price_spin) > 2.0 and np.sign(price_spin) != np.sign(volume_spin):
            # O parceiro de volume não sustenta o preço. É um blefe.
            signal = -np.sign(price_spin)
            conf = 0.94
            reason = f"SUSY_BREAK_DETECTED (PriceSpin={price_spin:.1f}, VolSpin={volume_spin:.1f})"
            
        elif abs(price_spin) > 1.5 and np.sign(price_spin) == np.sign(volume_spin):
            # Simetria Perfeita. Movimento autêntico.
            signal = np.sign(price_spin)
            conf = 0.90
            reason = "SUPERSYMMETRIC_FLOW_CONFIRMED"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class AethelViscosityAgent(BaseAgent):
    """
    [Phase Ω-Aethel] Viscosidade do Éter (Order Flow Fluid Dynamics).
    Modela o Livro de Ofertas como um fluido 'Éter' onde o preço se propaga.
    Mede a 'Viscosidade' (resistência do book ao preenchimento).
    Se a viscosidade cai a zero (vácuo de ordens), o preço vai 'escorregar' 
    violentamente (Flash Crash/Pump).
    """
    def __init__(self, weight=4.5):
        super().__init__("AethelViscosity", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        book = snapshot.book
        if not book or not book.get("bids") or not book.get("asks"):
            return AgentSignal(self.name, 0.0, 0.0, "NO_BOOK_DATA", self.weight)

        bids = np.array([[b["price"], b["volume"]] for b in book["bids"]], dtype=np.float64)
        asks = np.array([[a["price"], a["volume"]] for a in book["asks"]], dtype=np.float64)
        
        # Viscosidade = Densidade de volume por ponto de preço
        bid_viscosity = np.sum(bids[:5, 1]) / (abs(bids[0, 0] - bids[4, 0]) + 1e-6)
        ask_viscosity = np.sum(asks[:5, 1]) / (abs(asks[0, 0] - asks[4, 0]) + 1e-6)
        
        signal = 0.0
        conf = 0.0
        reason = "NORMAL_VISCOSITY"
        
        # Detecção de Vácuo (Super-Fluidez)
        if bid_viscosity < 1.0 and ask_viscosity > 10.0:
            # Vácuo de Compra. Preço vai despencar sem atrito.
            signal = -1.0
            conf = 0.96
            reason = f"AETHEL_VACUUM_BEAR (BidVisc={bid_viscosity:.2f} << AskVisc)"
        elif ask_viscosity < 1.0 and bid_viscosity > 10.0:
            # Vácuo de Venda.
            signal = 1.0
            conf = 0.96
            reason = f"AETHEL_VACUUM_BULL (AskVisc={ask_viscosity:.2f} << BidVisc)"
            
        return AgentSignal(self.name, signal, conf, reason, self.weight)
