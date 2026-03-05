"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — PREDATOR AGENTS (Phase 11)                  ║
║     Agentes de ATAQUE: detectam armadilhas institucionais e exploram.       ║
║                                                                              ║
║     "Nós não seguimos o smart money. Nós ANTECIPAMOS o smart money."        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import Optional

from core.consciousness.agents.base import AgentSignal, BaseAgent
from config.omega_params import OMEGA
from utils.decorators import catch_and_log


class IcebergHunterAgent(BaseAgent):
    """
    Caça ordens Iceberg no book: volume acumulado desproporcional num level
    de preço que 'não sai', enquanto o preço insiste contra ele.
    Sinal: se detectado absorção passiva num nível, esse nível é um muro
    real e o preço vai reverter para a direção do iceberg.
    """
    def __init__(self, weight: float = 1.4):
        super().__init__("IcebergHunterAgent", weight)
        self.needs_orderflow = True

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, orderflow_analysis: dict = None, **kw) -> Optional[AgentSignal]:
        if not orderflow_analysis:
            return None

        absorption = orderflow_analysis.get("absorption", {})
        if not absorption.get("detected"):
            return AgentSignal(self.name, 0.0, 0.0, "No iceberg detected", self.weight)

        abs_type = absorption.get("type", "")
        abs_strength = absorption.get("strength", 0.0)

        signal = 0.0
        reason = "Iceberg scan neutral"
        conf = 0.0

        # Absorção de compra = alguém absorve vendas passivamente => vai subir
        if "BUY" in abs_type.upper():
            signal = 0.8
            conf = min(1.0, abs_strength / 5.0)
            reason = f"ICEBERG BUY detected (strength={abs_strength:.1f}) — Hidden institutional bid"
        elif "SELL" in abs_type.upper():
            signal = -0.8
            conf = min(1.0, abs_strength / 5.0)
            reason = f"ICEBERG SELL detected (strength={abs_strength:.1f}) — Hidden institutional offer"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class StopHunterAgent(BaseAgent):
    """
    Prevê caçadas de stop-loss institucionais:
    Se o preço está se aproximando de um cluster de stops (highs/lows recentes),
    o agent prevê que market makers vão empurrar até o nível para liquidar stops
    e depois reverter brutalmente.
    """
    def __init__(self, weight: float = 1.6):
        super().__init__("StopHunterAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        closes = snapshot.m1_closes
        if len(closes) < 60:
            return None

        price = snapshot.price
        if price <= 0:
            return None

        # Identificar clusters de stops: topos e fundos recentes são onde stops se acumulam
        recent_high = max(closes[-30:])
        recent_low = min(closes[-30:])
        range_pct = (recent_high - recent_low) / price * 100

        # Distância do preço aos extremos (em %)
        dist_to_high = (recent_high - price) / price * 100
        dist_to_low = (price - recent_low) / price * 100

        signal = 0.0
        reason = "No stop hunt detected"
        conf = 0.0

        # Preço muito perto do topo (stops de short acima) — vai caçar e reverter
        if 0 < dist_to_high < 0.15 and range_pct > 0.3:
            signal = -0.7  # Espera-se spike para cima e reversão para baixo
            conf = 0.8
            reason = f"STOP HUNT UP imminent (dist={dist_to_high:.3f}%, shorts above {recent_high:.0f})"

        # Preço muito perto do fundo (stops de long abaixo) — vai caçar e reverter
        elif 0 < dist_to_low < 0.15 and range_pct > 0.3:
            signal = 0.7  # Espera-se spike para baixo e reversão para cima
            conf = 0.8
            reason = f"STOP HUNT DOWN imminent (dist={dist_to_low:.3f}%, longs below {recent_low:.0f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class InstitutionalFootprintAgent(BaseAgent):
    """
    Detecta pegadas institucionais: grandes trades fragmentados em
    sequências rápidas de volume consistente (TWAP/VWAP slicing).
    Quando detectado, segue a direção da acumulação.
    """
    def __init__(self, weight: float = 1.5):
        super().__init__("InstitutionalFootprintAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        ticks = snapshot.recent_ticks
        if len(ticks) < 50:
            return None

        # Analisar os últimos ticks: se volume consistente (mesmo tamanho, mesmo lado, rápido)
        # isso indica fragmentação institucional TWAP
        try:
            volumes = [t.get("volume_real", t.get("volume", 0)) for t in ticks[-50:]]
            bids = [t["bid"] for t in ticks[-50:]]
        except (KeyError, TypeError):
            return None

        if not volumes or sum(volumes) == 0:
            return AgentSignal(self.name, 0.0, 0.0, "No tick volume", self.weight)

        # Coeficiente de Variação do volume (CV < 0.3 = volume muito consistente = TWAP suspeito)
        vol_array = np.array(volumes, dtype=float)
        vol_array = vol_array[vol_array > 0]
        if len(vol_array) < 10:
            return AgentSignal(self.name, 0.0, 0.0, "Insufficient volume ticks", self.weight)

        cv = np.std(vol_array) / np.mean(vol_array) if np.mean(vol_array) > 0 else 999

        signal = 0.0
        reason = f"CV={cv:.2f} — Normal fragmentation"
        conf = 0.0

        if cv < 0.3:
            # Volume muito uniforme = TWAP institucional
            direction = 1.0 if bids[-1] > bids[0] else -1.0
            signal = direction * 0.75
            conf = 0.85
            reason = f"Institutional TWAP detected (CV={cv:.2f}), direction={'BUY' if direction > 0 else 'SELL'}"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class LiquiditySiphonAgent(BaseAgent):
    """
    Detecta quando a liquidez está sendo 'drenada' de um lado do book
    (muitas ordens limit canceladas rapidamente = spoofing/layering).
    Sinal: lado que está perdendo liquidez vai sofrer movimento violento.
    """
    def __init__(self, weight: float = 1.3):
        super().__init__("LiquiditySiphonAgent", weight)
        self.needs_orderflow = True

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, orderflow_analysis: dict = None, **kw) -> Optional[AgentSignal]:
        if not orderflow_analysis:
            return None

        # Usar imbalance como proxy para drenagem de liquidez
        imbalance_ratio = orderflow_analysis.get("imbalance_ratio", 0.0)
        delta = orderflow_analysis.get("delta", 0.0)

        signal = 0.0
        reason = "Balanced liquidity"
        conf = 0.0

        # Imbalance extremo: muito mais agressão de um lado
        if abs(imbalance_ratio) > 0.7:
            if imbalance_ratio > 0:
                signal = 0.7
                conf = 0.8
                reason = f"Liquidity Siphon BUY (imbalance={imbalance_ratio:.2f}, delta={delta:.1f})"
            else:
                signal = -0.7
                conf = 0.8
                reason = f"Liquidity Siphon SELL (imbalance={imbalance_ratio:.2f}, delta={delta:.1f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class OrderBookPressureAgent(BaseAgent):
    """
    Analisa a pressão do book de ofertas (DOM - Depth of Market).
    Se há muito mais volume em bids do que asks = pressão compradora.
    Peso desproporcional = muro institucional defendendo nível.
    """
    def __init__(self, weight: float = 1.2):
        super().__init__("OrderBookPressureAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        book = snapshot.metadata.get("book")
        if not book:
            return AgentSignal(self.name, 0.0, 0.0, "No DOM data", self.weight)

        bids = book.get("bids", [])
        asks = book.get("asks", [])

        if not bids or not asks:
            return AgentSignal(self.name, 0.0, 0.0, "Empty book", self.weight)

        # Somar volume dos primeiros 10 níveis de cada lado
        bid_vol = sum(b.get("volume", 0) for b in bids[:10])
        ask_vol = sum(a.get("volume", 0) for a in asks[:10])

        total = bid_vol + ask_vol
        if total == 0:
            return AgentSignal(self.name, 0.0, 0.0, "Zero book volume", self.weight)

        # Ratio: > 0.6 = pressão compradora, < 0.4 = pressão vendedora
        bid_ratio = bid_vol / total

        signal = 0.0
        reason = f"Book balanced (bid_ratio={bid_ratio:.2f})"
        conf = 0.0

        if bid_ratio > 0.65:
            signal = 0.6
            conf = min(1.0, (bid_ratio - 0.5) * 4)
            reason = f"BID PRESSURE (ratio={bid_ratio:.2f}, bid_vol={bid_vol:.0f} vs ask_vol={ask_vol:.0f})"
        elif bid_ratio < 0.35:
            signal = -0.6
            conf = min(1.0, (0.5 - bid_ratio) * 4)
            reason = f"ASK PRESSURE (ratio={bid_ratio:.2f}, bid_vol={bid_vol:.0f} vs ask_vol={ask_vol:.0f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)
