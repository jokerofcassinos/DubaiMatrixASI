"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — REGIME DETECTOR                       ║
║       Classificação e predição de regime de mercado                         ║
║                                                                              ║
║  O mercado NÃO é estacionário — ele muda de caráter constantemente.        ║
║  A ASI detecta o regime ATUAL e prevê TRANSIÇÕES antes que aconteçam.      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from enum import Enum
from typing import Optional, Tuple
from collections import deque
from dataclasses import dataclass

from utils.math_tools import MathEngine
from utils.decorators import catch_and_log
from utils.logger import log


class MarketRegime(Enum):
    """Regimes de mercado que a ASI reconhece."""
    TRENDING_BULL = "TRENDING_BULL"
    TRENDING_BEAR = "TRENDING_BEAR"
    RANGING = "RANGING"
    CHOPPY = "CHOPPY"
    BREAKOUT_UP = "BREAKOUT_UP"
    BREAKOUT_DOWN = "BREAKOUT_DOWN"
    HFT_BREAKDOWN = "HFT_BREAKDOWN"
    HIGH_VOL_CHAOS = "HIGH_VOL_CHAOS"
    LOW_LIQUIDITY = "LOW_LIQUIDITY"
    # Phase 24: High-Fidelity Micro Regimes
    SQUEEZE_BUILDUP = "SQUEEZE_BUILDUP"
    CREEPING_BULL = "CREEPING_BULL"
    DRIFTING_BEAR = "DRIFTING_BEAR"
    LIQUIDITY_HUNT = "LIQUIDITY_HUNT"
    MEAN_REVERTING = "MEAN_REVERTING"
    PARADIGM_SHIFT = "PARADIGM_SHIFT"
    UNKNOWN = "UNKNOWN"


@dataclass
class RegimeState:
    """Estado do regime detectado."""
    current: MarketRegime
    confidence: float           # [0, 1]
    transition_prob: float      # Probabilidade de transição iminente
    predicted_next: MarketRegime  # Regime previsível
    aggression_multiplier: float  # Multiplicador de agressividade para o regime
    reasoning: str
    duration_bars: int          # Há quantas barras estamos neste regime
    v_pulse_detected: bool = False # [PHASE 48] Flag de ignição instantânea


class RegimeDetector:
    """
    Detector de Regime — classifica e prevê mudanças no caráter do mercado.

    Usa múltiplos sinais:
    - Hurst exponent (trending vs mean-reverting)
    - ATR (volatilidade)
    - Fractal dimension (complexidade)
    - Bollinger width (compressão)
    - Volume (confirmação)
    - EMA alignment (tendência)
    """

    # Multiplicadores de agressividade por regime
    REGIME_AGGRESSION = {
        MarketRegime.TRENDING_BULL:   1.3,   # Mais agressivo em tendência
        MarketRegime.TRENDING_BEAR:   1.3,
        MarketRegime.RANGING:         0.8,   # Mais conservador em range
        MarketRegime.CHOPPY:          0.3,   # Muito conservador em chop
        MarketRegime.BREAKOUT_UP:     1.5,   # Agressivo em breakout
        MarketRegime.BREAKOUT_DOWN:   1.5,
        MarketRegime.HFT_BREAKDOWN:   1.8,   # Agressividade Máxima em Breakdown (Strike)
        MarketRegime.HIGH_VOL_CHAOS:  0.2,   # Mínimo em caos
        MarketRegime.LOW_LIQUIDITY:   0.4,   # Conservador em baixa liquidez
        # Phase 24 Additions
        MarketRegime.SQUEEZE_BUILDUP: 0.5,   # Preparação para o bote
        MarketRegime.CREEPING_BULL:   1.1,   # Tendência rasteira
        MarketRegime.DRIFTING_BEAR:   1.1,   # Sangramento lento
        MarketRegime.LIQUIDITY_HUNT:  0.3,   # Manipulação de stops
        MarketRegime.MEAN_REVERTING:  0.6,   # Ping-pong de algoritmos
        MarketRegime.PARADIGM_SHIFT:  0.25,  # Observação defensiva
        MarketRegime.UNKNOWN:         0.5,
    }

    def __init__(self):
        self.math = MathEngine()
        self._current_regime = MarketRegime.UNKNOWN
        self._regime_duration = 0
        self._regime_history = deque(maxlen=500)
        self._transition_matrix = {}  # P(next_regime | current_regime)

    @catch_and_log(default_return=None)
    def detect(self, snapshot) -> Optional[RegimeState]:
        """
        Detecta o regime atual do mercado e prevê transições.
        """
        indicators = snapshot.indicators
        candles = snapshot.candles.get("M5")

        if candles is None or len(candles["close"]) < 50:
            return RegimeState(
                MarketRegime.UNKNOWN, 0.0, 0.0, MarketRegime.UNKNOWN,
                0.5, "INSUFFICIENT_DATA", 0
            )

        close = candles["close"]
        high = candles["high"]
        low = candles["low"]
        volume = candles["tick_volume"]

        # ═══ Features para classificação ═══
        features = {}

        # Hurst Exponent
        hurst = indicators.get("M5_hurst")
        features["hurst"] = hurst if isinstance(hurst, (int, float)) else 0.5

        # ATR relativo (normalizado pelo preço)
        atr = indicators.get("M5_atr_14")
        if atr is not None and len(atr) > 0 and close[-1] > 0:
            features["atr_pct"] = (atr[-1] / close[-1]) * 100
        else:
            features["atr_pct"] = 0

        # Bollinger Width
        bb_width = indicators.get("M5_bb_width")
        if bb_width is not None and len(bb_width) > 20:
            features["bb_width"] = bb_width[-1]
            features["bb_width_avg"] = np.mean(bb_width[-50:])
        else:
            features["bb_width"] = 0
            features["bb_width_avg"] = 0

        # Fractal Dimension
        features["fractal_dim"] = self.math.fractal_dimension(close, 50)

        # EMA alignment
        ema_9 = indicators.get("M5_ema_9")
        ema_21 = indicators.get("M5_ema_21")
        ema_50 = indicators.get("M5_ema_50")
        if all(e is not None and len(e) > 0 for e in [ema_9, ema_21, ema_50]):
            features["ema_aligned_bull"] = (ema_9[-1] > ema_21[-1] > ema_50[-1])
            features["ema_aligned_bear"] = (ema_9[-1] < ema_21[-1] < ema_50[-1])
        else:
            features["ema_aligned_bull"] = False
            features["ema_aligned_bear"] = False

        # Volume
        vol_ratio = indicators.get("M5_volume_ratio")
        features["vol_ratio"] = vol_ratio[-1] if vol_ratio is not None and len(vol_ratio) > 0 else 1.0

        # Shannon Entropy
        entropy = indicators.get("M5_entropy")
        features["entropy"] = entropy if isinstance(entropy, (int, float)) else 3.0

        # ═══ Classificação baseada em regras multi-feature ═══
        regime, confidence, reasoning = self._classify_regime(features, snapshot)

        # ═══ Detectar transição ═══
        transition_prob = self._estimate_transition_probability(regime, features)
        predicted_next = self._predict_next_regime(regime, features)

        # ═══ [PHASE 48] V-PULSE OVERRIDE ═══
        v_pulse = self._detect_v_pulse(snapshot)
        v_pulse_detected = False
        if v_pulse:
            regime = v_pulse
            confidence = max(confidence, 0.90)
            reasoning = f"[PHASE 48: V-PULSE] {reasoning}"
            v_pulse_detected = True

        # Atualizar duração
        if regime == self._current_regime:
            self._regime_duration += 1
        else:
            self._regime_history.append({
                "regime": self._current_regime.value,
                "duration": self._regime_duration,
            })
            self._update_transition_matrix(self._current_regime, regime)
            self._current_regime = regime
            self._regime_duration = 1
            log.omega(f"🌊 REGIME CHANGE → {regime.value} (conf={confidence:.2f})")

        aggression = self.REGIME_AGGRESSION.get(regime, 0.5)

        return RegimeState(
            current=regime,
            confidence=confidence,
            transition_prob=transition_prob,
            predicted_next=predicted_next,
            aggression_multiplier=aggression,
            reasoning=reasoning,
            duration_bars=self._regime_duration,
            v_pulse_detected=v_pulse_detected
        )

    def _detect_v_pulse(self, snapshot) -> Optional[MarketRegime]:
        """
        Detecta pulsações de alta velocidade (V-Pulse) via M1.
        Evita a inércia do M5 em reversões violentas.
        """
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1.get("close", [])) < 5:
            return None

        closes = np.array(candles_m1["close"], dtype=np.float64)
        tick_velocity = snapshot.metadata.get("tick_velocity", 0.0)
        
        # [PHASE Ω-BREAKDOWN] HFT Acceleration Detection
        # Detecta quando o preço "some" (liquidity vacuum)
        if len(closes) >= 3:
            v1 = closes[-1] - closes[-2]
            v2 = closes[-2] - closes[-3]
            acceleration = v1 - v2 # Aceleração (Jerk proxy)
            
            # Se a aceleração negativa é brutal (> 1.0 ATR) e a velocidade é negativa
            atr_m5_list = snapshot.indicators.get("M5_atr_14")
            current_atr = atr_m5_list[-1] if atr_m5_list is not None and len(atr_m5_list) > 0 else 1.0
            
            if v1 < 0 and acceleration < -current_atr * 1.0 and abs(tick_velocity) > 25.0:
                 # Se estamos em CREEPING_BULL, isso é um "Breakdown" iminente
                 if self._current_regime == MarketRegime.CREEPING_BULL:
                      return MarketRegime.HFT_BREAKDOWN

        # 1. Delta Instantâneo (V-Shape)
        # Se os últimos 2 candles M1 anularam a queda dos 3 anteriores
        if len(closes) >= 5:
            d3 = closes[-3] - closes[-5] # Queda anterior
            d2 = closes[-1] - closes[-3] # Recuperação atual
            
            atr_m5_list = snapshot.indicators.get("M5_atr_14")
            current_atr = atr_m5_list[-1] if atr_m5_list is not None and len(atr_m5_list) > 0 else 0
            
            # [Liquidity Hole Detection] Spread widening + Tick Velocity > 40
            # Se o spread pontos disparou e a velocidade é HFT, ignoramos ATR e focamos no pulso
            max_spread = snapshot.symbol_info.get("spread", 0) if snapshot.symbol_info else 0
            is_liquidity_hole = max_spread > 5000 and tick_velocity > 40.0
            
            # Se caiu X e subiu > X * 0.8 (V-Recovery)
            if d3 < 0 and d2 > abs(d3) * 0.8 and (abs(d3) > current_atr * 1.5 or is_liquidity_hole) and current_atr > 0:
                return MarketRegime.BREAKOUT_UP

            # Se subiu X e caiu > X * 0.8 (V-Reversal Top)
            if d3 > 0 and d2 < -d3 * 0.8 and (d3 > current_atr * 1.5 or is_liquidity_hole) and current_atr > 0:
                return MarketRegime.BREAKOUT_DOWN

        # 2. HFT Explosion (Supernova Ignition)
        if tick_velocity > 30.0: # Reduzido de 35 para 30 para maior sensibilidade
            # Se o preço está se movendo na direção oposta ao regime atual ou em regimes de "Drift"
            price_delta_m1 = closes[-1] - closes[-2]
            
            # Alvos de reversão em regimes lentos
            slow_regimes = [MarketRegime.DRIFTING_BEAR, MarketRegime.CREEPING_BULL, MarketRegime.RANGING, MarketRegime.MEAN_REVERTING]
            
            if price_delta_m1 > 0:
                if self._current_regime == MarketRegime.TRENDING_BEAR or self._current_regime == MarketRegime.DRIFTING_BEAR:
                    return MarketRegime.BREAKOUT_UP
            
            if price_delta_m1 < 0:
                if self._current_regime == MarketRegime.TRENDING_BULL or self._current_regime == MarketRegime.CREEPING_BULL:
                    # Se for violento o suficiente, vira Breakdown
                    if abs(price_delta_m1) > current_atr * 0.8:
                        return MarketRegime.HFT_BREAKDOWN
                    return MarketRegime.BREAKOUT_DOWN
            
            # Se for regime de Drift e o pulso for na mesma direção, mas muito forte, confirma ignição
            # [Phase Ω-Apocalypse] Squeeze Exit Detection
            if self._current_regime == MarketRegime.SQUEEZE_BUILDUP:
                bb_width_list = snapshot.indicators.get("M5_bb_width", [0.0])
                if len(bb_width_list) > 1 and bb_width_list[-1] > bb_width_list[-2] * 1.5:
                    return MarketRegime.BREAKOUT_UP if price_delta_m1 > 0 else MarketRegime.BREAKOUT_DOWN

            if tick_velocity > 45.0:
                if price_delta_m1 > 0 and self._current_regime == MarketRegime.CREEPING_BULL:
                    return MarketRegime.BREAKOUT_UP
                if price_delta_m1 < 0 and self._current_regime == MarketRegime.DRIFTING_BEAR:
                    return MarketRegime.BREAKOUT_DOWN

        return None

    def _classify_regime(self, f: dict, snapshot) -> Tuple[MarketRegime, float, str]:
        """Classifica o regime baseado em features."""
        
        # ═══ [PHASE Ω-EPISTEMIC] PARADIGM SHIFT DETECTION ═══
        kl_div = snapshot.metadata.get("kl_divergence", 0.0)
        if kl_div > 1.5:  # Threshold cirúrgico para mudança de paradigma
            return MarketRegime.PARADIGM_SHIFT, min(1.0, kl_div / 5.0), \
                   f"PARADIGM_SHIFT: KL_DIV={kl_div:.4f} (Information Geometry Breach)"
        
        reasons = []

        # HIGH VOL CHAOS — sobrecarrega tudo apenas se ATR for muito extremo
        if f["atr_pct"] > 3.0 and f["entropy"] > 4.5:
            # [Phase Ω-Apocalypse] Blow-off Climax detection
            jounce = snapshot.metadata.get("jounce", 0.0)
            if abs(jounce) > 5.0: # Aceleração da aceleração colapsando ou explodindo
                 return MarketRegime.HIGH_VOL_CHAOS, 0.98, "CLIMAX_BLOW_OFF (High Jounce + Chaos)"
            return MarketRegime.HIGH_VOL_CHAOS, 0.9, "ATR_EXTREME + HIGH_ENTROPY"

        # BREAKOUT — BB squeeze + volume spike
        if f["bb_width_avg"] > 0:
            squeeze_ratio = f["bb_width"] / f["bb_width_avg"]
            if squeeze_ratio > 2.0 and f["vol_ratio"] > 2.0:
                if f.get("ema_aligned_bull"):
                    return MarketRegime.BREAKOUT_UP, 0.75, \
                           f"BB_EXPAND={squeeze_ratio:.1f}x VOL={f['vol_ratio']:.1f}x"
                elif f.get("ema_aligned_bear"):
                    return MarketRegime.BREAKOUT_DOWN, 0.75, \
                           f"BB_EXPAND={squeeze_ratio:.1f}x VOL={f['vol_ratio']:.1f}x"

        # SQUEEZE_BUILDUP (Phase 24) — Compressão brutal pré-breakout
        if f["bb_width_avg"] > 0 and f["bb_width"] < f["bb_width_avg"] * 0.4 and f["vol_ratio"] < 0.5:
            return MarketRegime.SQUEEZE_BUILDUP, 0.8, \
                   f"BB_COMPRESSION={(f['bb_width']/f['bb_width_avg']):.2f}x VOL_LOW={f['vol_ratio']:.1f}x"

        # LIQUIDITY_HUNT (Phase 24) — Volatilidade monstruosa + Hurt indicando mean reversion (Caça a stops)
        if f["atr_pct"] > 1.5 and f["hurst"] < 0.45 and f["entropy"] > 3.5:
            return MarketRegime.LIQUIDITY_HUNT, 0.75, \
                   f"ATR_HIGH={f['atr_pct']:.2f}% HURST={f['hurst']:.2f} (Caçador de Liquidez)"

        # TRENDING BEAR - Prioridade Máxima Se Alinhado ou Momentum Forte
        if f["ema_aligned_bear"]:
            if f["atr_pct"] > 0.8 and f["hurst"] > 0.6:
                confidence = min(1.0, f["hurst"] * 0.6 + 0.4)
                return MarketRegime.TRENDING_BEAR, confidence, \
                       f"STRONG_BEAR HURST={f['hurst']:.2f} ATR={f['atr_pct']:.2f}%"
            elif f["atr_pct"] < 0.6 and f["hurst"] > 0.5:
                # DRIFTING BEAR (Phase 24) - Sangramento lento
                return MarketRegime.DRIFTING_BEAR, 0.7, \
                       f"SLOW_BLEED HURST={f['hurst']:.2f} ATR={f['atr_pct']:.2f}%"

        # TRENDING BULL - Prioridade Máxima Se Alinhado ou Momentum Forte
        if f["ema_aligned_bull"]:
            if f["atr_pct"] > 0.8 and f["hurst"] > 0.6:
                confidence = min(1.0, f["hurst"] * 0.6 + 0.4)
                return MarketRegime.TRENDING_BULL, confidence, \
                       f"STRONG_BULL HURST={f['hurst']:.2f} ATR={f['atr_pct']:.2f}%"
            elif f["atr_pct"] < 0.6 and f["hurst"] > 0.5:
                # CREEPING BULL (Phase 24) - Alta lenta persistente
                return MarketRegime.CREEPING_BULL, 0.7, \
                       f"SLOW_GRIND HURST={f['hurst']:.2f} ATR={f['atr_pct']:.2f}%"

        # RANGING
        if f["hurst"] < 0.45 and f["fractal_dim"] < 1.5 and f["atr_pct"] < 1.0:
            return MarketRegime.RANGING, 0.7, \
                   f"HURST={f['hurst']:.2f}:MEAN_REV FD={f['fractal_dim']:.2f}"

        # MEAN_REVERTING (Phase 24) - Algoritmos Ping-Pong, Hurst Baixíssimo, ATR estagnado
        if f["hurst"] < 0.40 and f["entropy"] < 3.0:
            return MarketRegime.MEAN_REVERTING, 0.8, \
                   f"PING_PONG HURST={f['hurst']:.2f} ENTROPY={f['entropy']:.2f}"

        # CHOPPY
        if f["fractal_dim"] > 1.6 and f["hurst"] < 0.5:
            return MarketRegime.CHOPPY, 0.7, \
                   f"FD={f['fractal_dim']:.2f}:NOISY HURST={f['hurst']:.2f}"

        # LOW LIQUIDITY
        if f["vol_ratio"] < 0.3 and f["atr_pct"] < 0.5:
            return MarketRegime.LOW_LIQUIDITY, 0.6, \
                   f"VOL_LOW={f['vol_ratio']:.2f} ATR_LOW={f['atr_pct']:.2f}"

        # Default (Raro agora, mas mantido por safety)
        return MarketRegime.UNKNOWN, 0.3, "NO_CLEAR_REGIME_FOUND"

    def _estimate_transition_probability(self, current: MarketRegime,
                                          features: dict) -> float:
        """Estima probabilidade de o regime mudar em breve."""
        prob = 0.1  # Base

        # Duração longa aumenta probabilidade de transição
        if self._regime_duration > 50:
            prob += 0.2
        if self._regime_duration > 100:
            prob += 0.3

        # BB squeeze forte = breakout iminente
        if features.get("bb_width_avg", 0) > 0:
            if features["bb_width"] < features["bb_width_avg"] * 0.3:
                prob += 0.3

        # Volume spike = mudança possível
        if features.get("vol_ratio", 1) > 3.0:
            prob += 0.2

        return min(1.0, prob)

    def _predict_next_regime(self, current: MarketRegime,
                              features: dict) -> MarketRegime:
        """Prevê o próximo regime mais provável."""
        # Usar transition matrix se tiver dados
        if current in self._transition_matrix:
            transitions = self._transition_matrix[current]
            if transitions:
                most_likely = max(transitions, key=transitions.get)
                return most_likely

        # Heurísticas
        if current == MarketRegime.RANGING:
            return MarketRegime.BREAKOUT_UP  # Range geralmente precede breakout
        if current == MarketRegime.CHOPPY:
            return MarketRegime.TRENDING_BULL  # Chop precede tendência
        if current in (MarketRegime.BREAKOUT_UP, MarketRegime.BREAKOUT_DOWN):
            return MarketRegime.TRENDING_BULL  # Breakout vira tendência

        return MarketRegime.UNKNOWN

    def _update_transition_matrix(self, from_regime: MarketRegime,
                                   to_regime: MarketRegime):
        """Atualiza a matrix de transição empírica."""
        if from_regime not in self._transition_matrix:
            self._transition_matrix[from_regime] = {}
        transitions = self._transition_matrix[from_regime]
        transitions[to_regime] = transitions.get(to_regime, 0) + 1

    @property
    def current_regime(self) -> MarketRegime:
        return self._current_regime

    @property
    def regime_duration(self) -> int:
        return self._regime_duration
