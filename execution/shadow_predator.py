"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — SHADOW PREDATOR ENGINE                     ║
║     Identificação de assinaturas algorítmicas adversárias (GAN-ready).      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import List, Optional
from utils.logger import log

class ShadowPredatorEngine:
    """
    Motor Adversário para detecção de spoofing, layering e injeção de latência.
    Atua como um sentinela que identifica quando outros HFTs estão manipulando o book.
    """

    def __init__(self):
        self.signatures = []
        self._last_book_state = None
        self.predator_mode_active = False

    def analyze_signature(self, snapshot, flow_analysis) -> dict:
        """
        Detecta manipulações no order book.
        Spoofing: Grandes ordens que aparecem e somem logo antes do preço chegar.
        Layering: Múltiplas camadas de ordens pequenas induzindo movimento.
        """
        results = {
            "spoofing_detected": False,
            "layering_detected": False,
            "adversarial_pressure": 0.0, # [-1.0, 1.0]
            "hostile_signature": None
        }

        book = snapshot.book
        if not book or not self._last_book_state:
            self._last_book_state = book
            return results

        # 1. Detecção de Spoofing (Flash Orders)
        # Compara variações de volume nos níveis sem execução correspondente no flow
        bid_diff = self._calculate_book_delta(self._last_book_state['bids'], book['bids'])
        ask_diff = self._calculate_book_delta(self._last_book_state['asks'], book['asks'])
        
        # Se volume sumiu mas não houve "buy_volume" ou "sell_volume" no gap de tempo
        if flow_analysis:
            real_buy = flow_analysis.get('buy_volume', 0.0)
            real_sell = flow_analysis.get('sell_volume', 0.0)
            
            if bid_diff < -real_sell * 2: # Sumiu mais do que foi vendido
                results["spoofing_detected"] = True
                results["adversarial_pressure"] = -0.5 # Manipulação vendedora (induzindo queda)
                
            if ask_diff < -real_buy * 2: # Sumiu mais do que foi comprado
                results["spoofing_detected"] = True
                results["adversarial_pressure"] = 0.5 # Manipulação compradora
                
        # 2. Detecção de Layering
        # Book com muitas camadas uniformes e preço "driftando" sem volume real
        if flow_analysis and flow_analysis.get('order_imbalance', 0.0) > 0.8:
            if abs(snapshot.close - snapshot.open) < 0.0001: # Preço não moveu apesar do book torto
                 results["layering_detected"] = True
                 
        self._last_book_state = book
        return results

    def _calculate_book_delta(self, old_levels, new_levels) -> float:
        """Calcula a variação líquida de volume no book."""
        old_vol = sum([l['volume'] if isinstance(l, dict) else l[1] for l in old_levels])
        new_vol = sum([l['volume'] if isinstance(l, dict) else l[1] for l in new_levels])
        return new_vol - old_vol
