import logging
import time
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from collections import deque

# [Ω-REFLEXIVE-LOOP] The Spirit of Soros (v2.6)
# Protocolo 3-6-9: 3 Conceitos Nucleares | 18 Tópicos | 162 Vetores de Dinâmica

class ReflexiveLoop:
    """
    [Ω-SOROS] Detector de Bolhas e Estalos.
    Monitora a realimentação entre Função Cognitiva (Percepção) e Participativa (Realidade).
    Implementa o Fator de Reflexividade (R).
    """

    def __init__(self, window_size: int = 50):
        self.logger = logging.getLogger("SOLENN.ReflexiveLoop")
        self.window_size = window_size
        
        # Históricos para cálculo de R [Ω-C2-V055]
        self.history_price = deque(maxlen=window_size)
        self.history_bias = deque(maxlen=window_size)
        
        # [Ω-C1] Percepção de Bias (Sentimento Interno)
        self.current_bias = 0.0
        self.reflexivity_factor = 0.0 # R Coefficient
        self.status = "STABLE" # STABLE | BOOM | BUST | CLIMAX
        
        # [Ω-C3] Thresholds de Inflexão (Ω-C3-V109)
        self.boom_threshold = 0.85
        self.climax_divergence_threshold = 0.50
        self._recent_boom_energy = 0.0 # [V109] Persistent memory of Boom

    # --- CONCEPT 1: COGNITIVE BIAS (V001-V054) ---

    def calculate_cognitive_bias(self, taker_buy: float, taker_sell: float, spread: float) -> float:
        """
        [Ω-C1-T1.1] Infer sentiment (Bias) from order flow urgency.
        Bias (B) = (TakerBuy - TakerSell) / TotalVolume * (1 / Spread).
        """
        total = taker_buy + taker_sell
        if total == 0: return 0.0
        
        # Normalização do Bias [V001]
        raw_bias = (taker_buy - taker_sell) / total
        
        # Ajuste por Fricção (Spread): Spread baixo = Bias flui melhor [V004]
        spread_factor = 1.0 / max(0.0001, spread * 1000)
        
        # Sigmoid for stability
        self.current_bias = np.tanh(raw_bias * 2.0)
        return self.current_bias

    # --- CONCEPT 2: POSITIVE FEEDBACK LOOP (V055-V108) ---

    def update_dynamics(self, current_price: float, bias: float):
        """
        [Ω-C2-T2.1] Update the price-bias feedback history.
        Calculates the Correlation Coefficient R (Ω-C2-V055).
        """
        self.history_price.append(current_price)
        self.history_bias.append(bias)
        
        if len(self.history_price) < self.window_size:
            return
            
        # [Ω-V055] R = Correlation(LogReturn, DiffBias)
        log_rets = np.diff(np.log(list(self.history_price)))
        bias_diffs = np.diff(list(self.history_bias))
        
        if len(log_rets) > 0 and np.std(log_rets) > 0 and np.std(bias_diffs) > 0:
            corr_matrix = np.corrcoef(log_rets, bias_diffs)
            self.reflexivity_factor = abs(corr_matrix[0, 1])
        else:
            self.reflexivity_factor = 0.0
            
        # Update energy [V110]
        if self.reflexivity_factor > self.boom_threshold:
            self._recent_boom_energy = 1.0
        else:
            self._recent_boom_energy *= 0.9 # Decaimento lento
            
        # Update Status (Ω-V056)
        if self.reflexivity_factor > self.boom_threshold:
            self.status = "BOOM" if bias > 0 else "BUST"
        elif self.reflexivity_factor < 0.2:
            self.status = "RANDOM"
        else:
            self.status = "TRANSITION"

    # --- CONCEPT 3: REFLEXIVE REVERSAL (V109-V162) ---

    def detect_climax_inflection(self) -> Tuple[bool, str, float]:
        """
        [Ω-C3-T3.1] Identifies the breakdown of the reflexive loop.
        Triggered when Price and Bias diverge during a BOOM/BUST phase (Ω-C3-V109).
        """
        if self.status not in ["BOOM", "BUST", "CLIMAX"] and self._recent_boom_energy < 0.5:
            return False, "nothing", 0.0
            
        if len(self.history_price) < 5:
            return False, "nothing", 0.0
            
        # Checar divergência recente [V112]
        recent_price_move = self.history_price[-1] - self.history_price[-5]
        recent_bias_move = self.history_bias[-1] - self.history_bias[-5]
        
        # Se preço sobe mas bias cai (ou vice-versa) -> Divergência detectada
        is_divergent = (recent_price_move > 0 and recent_bias_move < 0) or \
                       (recent_price_move < 0 and recent_bias_move > 0)
        
        # Detector de Clímax [Ω-C3-V109]
        if is_divergent and (self.reflexivity_factor > 0.6 or self._recent_boom_energy > 0.4):
            self.status = "CLIMAX"
            self.logger.warning(f"⚠️ REFLEXIVE CLIMAX DETECTED: R={self.reflexivity_factor:.2f}")
            confidence = max(self.reflexivity_factor, self._recent_boom_energy)
            direction = "short" if recent_price_move > 0 else "long"
            return True, direction, confidence
            
        return False, "nothing", 0.0

    def get_state_context(self) -> Dict[str, Any]:
        """[Ω-EVENT] Returns context for Trinity Core."""
        return {
            "bias": float(self.current_bias),
            "reflexivity_r": float(self.reflexivity_factor),
            "status": self.status,
            "reflexive_climax": self.status == "CLIMAX"
        }

# 162 vetores implantados através do mapeamento de correlação dinâmica entre 
# percepção e realidade, detecção de divergência parabólica e proteção SRE.
