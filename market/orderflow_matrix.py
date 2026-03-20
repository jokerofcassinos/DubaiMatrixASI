"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — ORDER FLOW MATRIX                     ║
║       Análise de microestrutura: penetrando a Matrix do mercado            ║
║                                                                              ║
║  Vê o que ninguém vê: acumulação, distribuição, absorção, exaustão,        ║
║  spoofing, iceberg orders, e a intenção real por trás de cada tick.        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from collections import deque
from typing import Optional, Dict
from datetime import datetime, timezone

from utils.math_tools import MathEngine
from utils.decorators import catch_and_log, asi_safe
from cpp.asi_bridge import CPP_CORE


class OrderFlowMatrix:
    """
    Análise de Order Flow — a visão matrix do mercado.

    O preço é apenas a superfície. Abaixo dele existe:
    - Fluxo de ordens (quem está comprando/vendendo de verdade)
    - Absorção (alguém absorvendo pressão sem mover o preço)
    - Exaustão (volume alto sem resultado = fim do movimento)
    - Acumulação/Distribuição (smart money posicionando)
    - Imbalance (desequilíbrio de poder entre compra/venda)
    """

    def __init__(self):
        self.math = MathEngine()
        self._delta_buffer = deque(maxlen=5000)     # Delta acumulativo
        self._imbalance_buffer = deque(maxlen=5000)  # Imbalance por tick
        self._absorption_events = deque(maxlen=100)  # Eventos de absorção
        self._exhaustion_events = deque(maxlen=100)  # Eventos de exaustão

    # ═══════════════════════════════════════════════════════════
    #  ANÁLISE DE TICK-BY-TICK
    # ═══════════════════════════════════════════════════════════

    @catch_and_log(default_return={})
    def analyze_ticks(self, ticks: list) -> dict:
        """
        Análise profunda de sequência de ticks.
        Cada tick contém informação sobre intenção.
        """
        if not ticks or len(ticks) < 10:
            return self._empty_analysis()

        # ═══ Delegação para C++ Core (Zero-Latency) ═══
        cpp_result = CPP_CORE.process_orderflow(ticks)
        if not cpp_result:
            return self._empty_analysis()

        current_delta = cpp_result["cumulative_delta"]
        avg_imbalance = cpp_result["order_imbalance"]
        avg_velocity = cpp_result["tick_velocity"]
        is_volume_climax = cpp_result["volume_climax_score"] > 3.0
        
        # Adaptação para manter interface Python (Type / Strength)
        is_absorption = cpp_result["is_absorption"]
        
        abs_type = None
        if is_absorption:
            buy_p = cpp_result["buy_volume"]
            sell_p = cpp_result["sell_volume"]
            if buy_p > sell_p * 1.5:
                # Compras passivamente absorvidas (Iceberg SELL) -> preço vai cair
                abs_type = "BEARISH_ABSORPTION"
            elif sell_p > buy_p * 1.5:
                # Vendas passivamente absorvidas (Iceberg BUY) -> preço vai subir
                abs_type = "BULLISH_ABSORPTION"
            else:
                abs_type = "NEUTRAL_ABSORPTION"
                
        absorption = {"detected": is_absorption, "type": abs_type, "strength": 0.8 if is_absorption else 0.0}
        
        is_exhaustion = cpp_result["is_exhaustion"]
        exhaustion = {"detected": is_exhaustion, "type": "CPP_EXHAUSTION" if is_exhaustion else None, "strength": 0.8 if is_exhaustion else 0.0}

        # ═══ Python Spread Analysis (ainda local) ═══
        bids = np.array([t.get("bid", 0) for t in ticks], dtype=np.float64)
        asks = np.array([t.get("ask", 0) for t in ticks], dtype=np.float64)
        spreads = asks - bids
        avg_spread = np.mean(spreads[-50:]) if len(spreads) >= 50 else (np.mean(spreads) if len(spreads) > 0 else 0)
        spread_expanding = False
        if len(spreads) > 20:
            recent_spread = np.mean(spreads[-10:])
            older_spread = np.mean(spreads[-20:-10])
            spread_expanding = recent_spread > older_spread * 1.5

        # ═══ Compilar análise ═══
        analysis = {
            "delta": float(current_delta),
            "delta_direction": "BUY" if current_delta > 0 else "SELL" if current_delta < 0 else "NEUTRAL",
            "imbalance": float(avg_imbalance),
            "imbalance_signal": self._classify_imbalance(avg_imbalance),
            "tick_velocity": float(avg_velocity),
            "volume_climax": is_volume_climax,
            "volume_zscore": cpp_result["volume_climax_score"],
            "absorption": absorption,
            "exhaustion": exhaustion,
            "spread_avg": float(avg_spread),
            "spread_expanding": spread_expanding,
            "buy_pressure": cpp_result["buy_volume"],
            "sell_pressure": cpp_result["sell_volume"],
            "tick_count": len(ticks),
            "signal": self._compute_flow_signal(
                current_delta, avg_imbalance, absorption, exhaustion
            ),
        }

        return analysis

    # ═══════════════════════════════════════════════════════════
    #  ANÁLISE DE BOOK
    # ═══════════════════════════════════════════════════════════

    @catch_and_log(default_return={})
    def analyze_book(self, book: dict) -> dict:
        """Análise do book de ofertas (depth of market)."""
        if not book:
            return {"book_imbalance": 0.0, "book_signal": "NEUTRAL"}

        bid_total = book.get("bid_total", 0)
        ask_total = book.get("ask_total", 0)
        total = bid_total + ask_total

        if total == 0:
            return {"book_imbalance": 0.0, "book_signal": "NEUTRAL"}

        imbalance = (bid_total - ask_total) / total

        # Detectar walls (grandes volumes em um nível)
        bids = book.get("bids", [])
        asks = book.get("asks", [])

        bid_wall = max((b["volume"] for b in bids), default=0)
        ask_wall = max((a["volume"] for a in asks), default=0)

        return {
            "book_imbalance": float(imbalance),
            "book_signal": self._classify_imbalance(imbalance),
            "bid_total": bid_total,
            "ask_total": ask_total,
            "bid_wall_size": bid_wall,
            "ask_wall_size": ask_wall,
            "bid_wall_price": next(
                (b["price"] for b in bids if b["volume"] == bid_wall), 0
            ) if bid_wall > 0 else 0,
            "ask_wall_price": next(
                (a["price"] for a in asks if a["volume"] == ask_wall), 0
            ) if ask_wall > 0 else 0,
        }

    # ═══════════════════════════════════════════════════════════
    #  DETECÇÃO DE PATTERNS OCULTOS
    # ═══════════════════════════════════════════════════════════

    def _detect_absorption(self, prices: np.ndarray, volumes: np.ndarray,
                           buy_vol: np.ndarray, sell_vol: np.ndarray) -> dict:
        """
        Absorção = alto volume sem movimento de preço.
        Indica smart money absorvendo pressão → reversão provável.
        """
        if len(prices) < 20:
            return {"detected": False, "type": None, "strength": 0.0}

        # Últimos 20 ticks
        recent_prices = prices[-20:]
        recent_volumes = volumes[-20:]

        price_range = np.max(recent_prices) - np.min(recent_prices)
        avg_vol = np.mean(recent_volumes)

        # Absorção: volume alto com range baixo
        price_norm = price_range / max(recent_prices.mean(), 1) * 100
        vol_norm = avg_vol / max(np.mean(volumes), 1e-10)

        if price_norm < 0.05 and vol_norm > 2.0:
            # Determinar tipo: quem está absorvendo?
            buy_sum = np.sum(buy_vol[-20:])
            sell_sum = np.sum(sell_vol[-20:])

            if buy_sum > sell_sum * 1.5:
                abs_type = "BEARISH_ABSORPTION"  # Compras absorvidas = bearish
            elif sell_sum > buy_sum * 1.5:
                abs_type = "BULLISH_ABSORPTION"  # Vendas absorvidas = bullish
            else:
                abs_type = "NEUTRAL_ABSORPTION"

            strength = min(1.0, vol_norm / 5.0)

            event = {"detected": True, "type": abs_type, "strength": strength,
                     "time": datetime.now(timezone.utc).isoformat()}
            self._absorption_events.append(event)
            return event

        return {"detected": False, "type": None, "strength": 0.0}

    def _detect_exhaustion(self, prices: np.ndarray, volumes: np.ndarray,
                           delta: np.ndarray) -> dict:
        """
        Exaustão = último suspiro de um movimento.
        Alto volume + delta extremo → final do movimento.
        """
        if len(prices) < 30:
            return {"detected": False, "type": None, "strength": 0.0}

        recent_delta = delta[-10:] if len(delta) >= 10 else delta
        delta_change = recent_delta[-1] - recent_delta[0] if len(recent_delta) > 1 else 0

        recent_vol = volumes[-10:]
        vol_spike = np.mean(recent_vol) / max(np.mean(volumes), 1e-10)

        price_momentum = (prices[-1] - prices[-10]) / max(prices[-10], 1) * 100 if len(prices) >= 10 else 0

        # Exaustão bullish: preço subindo com delta enfraquecendo
        if price_momentum > 0.1 and delta_change < 0 and vol_spike > 1.5:
            strength = min(1.0, vol_spike / 3.0 * abs(delta_change) / max(abs(recent_delta[-1]), 1))
            event = {"detected": True, "type": "BULL_EXHAUSTION", "strength": strength}
            self._exhaustion_events.append(event)
            return event

        # Exaustão bearish: preço caindo com delta fortalecendo
        if price_momentum < -0.1 and delta_change > 0 and vol_spike > 1.5:
            strength = min(1.0, vol_spike / 3.0 * abs(delta_change) / max(abs(recent_delta[-1]), 1))
            event = {"detected": True, "type": "BEAR_EXHAUSTION", "strength": strength}
            self._exhaustion_events.append(event)
            return event

        return {"detected": False, "type": None, "strength": 0.0}

    # ═══════════════════════════════════════════════════════════
    #  UTILIDADES
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def _classify_imbalance(imbalance: float) -> str:
        """Classifica imbalance em signal."""
        if imbalance > 0.3:
            return "STRONG_BUY"
        elif imbalance > 0.1:
            return "LEAN_BUY"
        elif imbalance < -0.3:
            return "STRONG_SELL"
        elif imbalance < -0.1:
            return "LEAN_SELL"
        return "NEUTRAL"

    @asi_safe(min_val=-1.0, max_val=1.0, param_name="flow_signal")
    def _compute_flow_signal(self, delta: float, imbalance: float,
                              absorption: dict, exhaustion: dict) -> float:
        """
        Sinal composto de order flow [-1.0, +1.0].
        Combinação de delta, imbalance, absorção e exaustão.
        """
        if np.isnan(delta) or np.isnan(imbalance):
            return 0.0
            
        signal = 0.0

        # Delta contribui com direção
        if delta != 0:
            delta_norm = np.tanh(delta / 1000)  # Normalizar com tanh
            signal += delta_norm * 0.4

        # Imbalance contribui
        signal += imbalance * 0.3

        # Absorção inverte
        if absorption.get("detected"):
            if absorption["type"] == "BULLISH_ABSORPTION":
                signal += absorption["strength"] * 0.2
            elif absorption["type"] == "BEARISH_ABSORPTION":
                signal -= absorption["strength"] * 0.2

        # Exaustão inverte
        if exhaustion.get("detected"):
            if exhaustion["type"] == "BULL_EXHAUSTION":
                signal -= exhaustion["strength"] * 0.1
            elif exhaustion["type"] == "BEAR_EXHAUSTION":
                signal += exhaustion["strength"] * 0.1

        return signal

    @staticmethod
    def _empty_analysis() -> dict:
        return {
            "delta": 0.0, "delta_direction": "NEUTRAL",
            "imbalance": 0.0, "imbalance_signal": "NEUTRAL",
            "tick_velocity": 0.0, "volume_climax": False,
            "absorption": {"detected": False},
            "exhaustion": {"detected": False},
            "spread_avg": 0.0, "spread_expanding": False,
            "signal": 0.0,
        }
