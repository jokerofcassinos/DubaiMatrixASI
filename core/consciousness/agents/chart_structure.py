"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          DUBAI MATRIX ASI — CHART STRUCTURE & CANDLE ANATOMY (Phase 17)     ║
║                                                                              ║
║  ChartStructureAgent: Análise gráfica complexa multi-timeframe.             ║
║  → Detecta topos e fundos macro para VETAR entradas suicidas.               ║
║  → Swing highs/lows, EMA distance, RSI extremes, BB position.              ║
║                                                                              ║
║  CandleAnatomyAgent: Anatomia de candle microscópica.                       ║
║  → Detecta se o preço está no topo/fundo do candle atual.                   ║
║  → Body/wick ratios, rejection patterns, hammer/shooting star.              ║
║  → Evita comprar no topo do candle e vender no fundo do candle.             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import Optional

from core.consciousness.agents.base import AgentSignal, BaseAgent
from utils.decorators import catch_and_log


# ═══════════════════════════════════════════════════════════════
#  AGENT 1: CHART STRUCTURE AGENT (Macro Top/Bottom Detection)
# ═══════════════════════════════════════════════════════════════

class ChartStructureAgent(BaseAgent):
    """
    Análise Gráfica Complexa Multi-Timeframe.
    
    MISSÃO: Evitar comprar no topo e vender no fundo.
    
    Detecta a posição do preço na ESTRUTURA MACRO do gráfico usando:
    1. Swing Highs/Lows detection (fractais de Williams)
    2. Distância do preço às EMAs (overextension)
    3. RSI multi-timeframe em zonas extremas
    4. Posição relativa nas Bollinger Bands cross-timeframe
    5. Higher Highs/Lower Lows structure analysis
    
    Sinal: NEGATIVO quando próximo de topo → não compre.
           POSITIVO quando próximo de fundo → não venda.
           NEUTRO quando no meio da estrutura → livre para agir.
    """

    def __init__(self, weight: float = 1.5):
        super().__init__("ChartStructureAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        signals = []
        reasons = []
        indicators = snapshot.indicators

        # ═══ ANÁLISE MULTI-TIMEFRAME ═══
        for tf in ["M1", "M5", "M15"]:
            candles = snapshot.candles.get(tf)
            if candles is None:
                continue
            
            close = np.array(candles["close"], dtype=np.float64)
            high = np.array(candles["high"], dtype=np.float64)
            low = np.array(candles["low"], dtype=np.float64)
            
            if len(close) < 30:
                continue

            # ─── 1. SWING HIGH/LOW DETECTION (Williams Fractals) ───
            swing_signal = self._detect_swing_position(close, high, low, tf)
            if swing_signal is not None:
                signals.append(swing_signal[0])
                reasons.append(swing_signal[1])

            # ─── 2. EMA OVEREXTENSION ───
            ema_signal = self._detect_ema_overextension(close, indicators, tf)
            if ema_signal is not None:
                signals.append(ema_signal[0])
                reasons.append(ema_signal[1])

            # ─── 3. RSI EXTREMES ───
            rsi_signal = self._detect_rsi_extreme(indicators, tf)
            if rsi_signal is not None:
                signals.append(rsi_signal[0])
                reasons.append(rsi_signal[1])

            # ─── 4. BOLLINGER BAND POSITION ───
            bb_signal = self._detect_bb_extreme(close, indicators, tf)
            if bb_signal is not None:
                signals.append(bb_signal[0])
                reasons.append(bb_signal[1])

        # ─── 5. HIGHER HIGHS / LOWER LOWS STRUCTURE ───
        struct_signal = self._detect_market_structure(snapshot)
        if struct_signal is not None:
            signals.append(struct_signal[0])
            reasons.append(struct_signal[1])

        if not signals:
            return AgentSignal(self.name, 0.0, 0.0, "STRUCTURE_NO_DATA", self.weight)

        avg_signal = float(np.mean(signals))
        
        # Confluência: se TODOS os sinais concordam, confiança alta
        same_direction = all(s > 0 for s in signals) or all(s < 0 for s in signals)
        confluence_bonus = 0.3 if same_direction and len(signals) >= 3 else 0.0
        confidence = min(1.0, abs(avg_signal) * 0.8 + 0.2 + confluence_bonus)

        return AgentSignal(
            self.name, float(np.clip(avg_signal, -1, 1)),
            float(np.clip(confidence, 0, 1)),
            " | ".join(reasons), self.weight
        )

    def _detect_swing_position(self, close, high, low, tf):
        """Detecta swing highs/lows usando fractais de Williams de 5 barras."""
        n = len(high)
        if n < 20:
            return None

        # Encontrar swing highs e lows (fractal de 5 barras)
        swing_highs = []
        swing_lows = []
        
        for i in range(2, n - 2):
            # Swing High: high[i] é maior que os 2 vizinhos de cada lado
            if high[i] > high[i-1] and high[i] > high[i-2] and \
               high[i] > high[i+1] and high[i] > high[i+2]:
                swing_highs.append((i, high[i]))
            # Swing Low: low[i] é menor que os 2 vizinhos de cada lado
            if low[i] < low[i-1] and low[i] < low[i-2] and \
               low[i] < low[i+1] and low[i] < low[i+2]:
                swing_lows.append((i, low[i]))

        current_price = close[-1]
        
        # Verificar proximidade a swing highs recentes (TOPO)
        if swing_highs:
            recent_high = max(swing_highs[-5:], key=lambda x: x[1]) if len(swing_highs) >= 5 else max(swing_highs, key=lambda x: x[1])
            dist_to_high_pct = (recent_high[1] - current_price) / current_price * 100
            
            if abs(dist_to_high_pct) < 0.15:  # Dentro de 0.15% do topo
                return (-0.8, f"{tf}:AT_SWING_HIGH({recent_high[1]:.0f})")
            elif 0 < dist_to_high_pct < 0.3:  # Muito próximo do topo
                return (-0.5, f"{tf}:NEAR_SWING_HIGH({recent_high[1]:.0f})")

        # Verificar proximidade a swing lows recentes (FUNDO)
        if swing_lows:
            recent_low = min(swing_lows[-5:], key=lambda x: x[1]) if len(swing_lows) >= 5 else min(swing_lows, key=lambda x: x[1])
            dist_to_low_pct = (current_price - recent_low[1]) / current_price * 100
            
            if abs(dist_to_low_pct) < 0.15:
                return (0.8, f"{tf}:AT_SWING_LOW({recent_low[1]:.0f})")
            elif 0 < dist_to_low_pct < 0.3:
                return (0.5, f"{tf}:NEAR_SWING_LOW({recent_low[1]:.0f})")

        return None

    def _detect_ema_overextension(self, close, indicators, tf):
        """Detecta quando o preço está excessivamente distante das EMAs."""
        ema_21 = indicators.get(f"{tf}_ema_21")
        ema_50 = indicators.get(f"{tf}_ema_50")
        
        if ema_21 is None or len(ema_21) < 5:
            return None
        
        price = close[-1]
        ema_val = ema_21[-1]
        
        if ema_val <= 0:
            return None
            
        # Distância percentual do preço à EMA21
        dist_pct = (price - ema_val) / ema_val * 100
        
        # ATR-normalized overextension
        atr = indicators.get(f"{tf}_atr_14")
        if atr is not None and len(atr) > 0 and atr[-1] > 0:
            dist_atr = abs(price - ema_val) / atr[-1]
            
            if dist_atr > 3.0:  # > 3 ATR de distância = hiperextendido
                if dist_pct > 0:
                    return (-0.7, f"{tf}:OVEREXTENDED_BULL({dist_atr:.1f}ATR)")
                else:
                    return (0.7, f"{tf}:OVEREXTENDED_BEAR({dist_atr:.1f}ATR)")
            elif dist_atr > 2.0:
                if dist_pct > 0:
                    return (-0.4, f"{tf}:STRETCHED_BULL({dist_atr:.1f}ATR)")
                else:
                    return (0.4, f"{tf}:STRETCHED_BEAR({dist_atr:.1f}ATR)")
        
        return None

    def _detect_rsi_extreme(self, indicators, tf):
        """Detecta RSI em zonas extremas como indicador de topo/fundo."""
        rsi = indicators.get(f"{tf}_rsi_14")
        if rsi is None or len(rsi) < 5:
            return None
        
        last_rsi = rsi[-1]
        
        # RSI > 80: FORTEMENTE overbought → possível topo
        if last_rsi > 80:
            return (-0.8, f"{tf}:RSI_EXTREME_OB({last_rsi:.0f})")
        elif last_rsi > 72:
            return (-0.5, f"{tf}:RSI_OB({last_rsi:.0f})")
        # RSI < 20: FORTEMENTE oversold → possível fundo
        elif last_rsi < 20:
            return (0.8, f"{tf}:RSI_EXTREME_OS({last_rsi:.0f})")
        elif last_rsi < 28:
            return (0.5, f"{tf}:RSI_OS({last_rsi:.0f})")
        
        return None

    def _detect_bb_extreme(self, close, indicators, tf):
        """Detecta preço nos extremos das Bollinger Bands."""
        bb_upper = indicators.get(f"{tf}_bb_upper")
        bb_lower = indicators.get(f"{tf}_bb_lower")
        
        if bb_upper is None or bb_lower is None:
            return None
        if len(bb_upper) < 5 or len(bb_lower) < 5:
            return None
        
        price = close[-1]
        upper = bb_upper[-1]
        lower = bb_lower[-1]
        
        if upper == lower:
            return None
        
        bb_pct = (price - lower) / (upper - lower)
        
        # > 98%: tocando/ultrapassando a banda superior → topo
        if bb_pct > 0.98:
            return (-0.6, f"{tf}:BB_UPPER_BREAK({bb_pct:.2f})")
        elif bb_pct > 0.90:
            return (-0.3, f"{tf}:BB_UPPER_ZONE({bb_pct:.2f})")
        # < 2%: tocando/ultrapassando a banda inferior → fundo
        elif bb_pct < 0.02:
            return (0.6, f"{tf}:BB_LOWER_BREAK({bb_pct:.2f})")
        elif bb_pct < 0.10:
            return (0.3, f"{tf}:BB_LOWER_ZONE({bb_pct:.2f})")
        
        return None

    def _detect_market_structure(self, snapshot):
        """Detecta se estamos em Higher Highs (uptrend top) ou Lower Lows (downtrend bottom)."""
        candles = snapshot.candles.get("M5")
        if candles is None:
            return None
        
        high = np.array(candles["high"], dtype=np.float64)
        low = np.array(candles["low"], dtype=np.float64)
        close = np.array(candles["close"], dtype=np.float64)
        
        if len(high) < 30:
            return None
        
        # Dividir em 3 blocos de 10 candles
        block_size = 10
        if len(high) < block_size * 3:
            return None
        
        # Highs e Lows de cada bloco
        h1 = np.max(high[-block_size*3:-block_size*2])
        h2 = np.max(high[-block_size*2:-block_size])
        h3 = np.max(high[-block_size:])
        
        l1 = np.min(low[-block_size*3:-block_size*2])
        l2 = np.min(low[-block_size*2:-block_size])
        l3 = np.min(low[-block_size:])
        
        current_price = close[-1]
        
        # Estrutura de HH + HL = uptrend → se preço próximo do H3 = TOPO
        if h3 > h2 > h1 and l3 > l2 > l1:  # Clear uptrend
            dist_to_top_pct = (h3 - current_price) / current_price * 100
            if dist_to_top_pct < 0.1:  # Muito próximo do topo da estrutura
                return (-0.6, "STRUCT:AT_UPTREND_TOP(HH+HL)")
        
        # Estrutura de LL + LH = downtrend → se preço próximo do L3 = FUNDO
        if l3 < l2 < l1 and h3 < h2 < h1:  # Clear downtrend
            dist_to_bottom_pct = (current_price - l3) / current_price * 100
            if dist_to_bottom_pct < 0.1:
                return (0.6, "STRUCT:AT_DOWNTREND_BOTTOM(LL+LH)")
        
        return None


# ═══════════════════════════════════════════════════════════════
#  AGENT 2: CANDLE ANATOMY AGENT (Micro Candle Top/Bottom)
# ═══════════════════════════════════════════════════════════════

class CandleAnatomyAgent(BaseAgent):
    """
    Anatomia de Candle Microscópica — O microscópio do timing perfeito.

    MISSÃO: Evitar comprar no topo de um candle altista e vender no fundo
            de um candle baixista (o pior timing possível).

    Análise multi-dimensional de cada candle:
    1. Posição do preço dentro do candle atual (perto do high? do low?)
    2. Padrões de rejeição (hammers, shooting stars, dojis, engulfing)
    3. Wicking ratio: se o candle tem pavio grande = rejeição = contra-sinal
    4. Sequência de candles: N candles consecutivos = exaustão do movement
    5. Tamanho relativo do body vs histórico (anomaly detection)
    
    Sinal: VETA BUY se o candle indica topo micro (pavio superior longo, 
           preço no topo da range, N verdes seguidos).
           VETA SELL se o candle indica fundo micro (pavio inferior longo,
           preço no fundo da range, N vermelhos seguidos).
    """

    def __init__(self, weight: float = 1.3):
        super().__init__("CandleAnatomyAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        signals = []
        reasons = []

        for tf in ["M1", "M5"]:
            candles = snapshot.candles.get(tf)
            if candles is None:
                continue
            
            open_arr = np.array(candles["open"], dtype=np.float64)
            high_arr = np.array(candles["high"], dtype=np.float64)
            low_arr = np.array(candles["low"], dtype=np.float64)
            close_arr = np.array(candles["close"], dtype=np.float64)
            
            if len(close_arr) < 10:
                continue

            # ─── 1. POSIÇÃO DO PREÇO DENTRO DO CANDLE ATUAL ───
            pos_signal = self._price_position_in_candle(
                open_arr[-1], high_arr[-1], low_arr[-1], close_arr[-1], tf
            )
            if pos_signal is not None:
                signals.append(pos_signal[0])
                reasons.append(pos_signal[1])

            # ─── 2. PADRÕES DE REJEIÇÃO (WICKS) ───
            wick_signal = self._detect_rejection_wicks(
                open_arr, high_arr, low_arr, close_arr, tf
            )
            if wick_signal is not None:
                signals.append(wick_signal[0])
                reasons.append(wick_signal[1])

            # ─── 3. SEQUÊNCIA CONSECUTIVA (EXAUSTÃO) ───
            seq_signal = self._detect_consecutive_candles(
                open_arr, close_arr, tf
            )
            if seq_signal is not None:
                signals.append(seq_signal[0])
                reasons.append(seq_signal[1])

            # ─── 4. ANOMALIA DE TAMANHO (CLIMAX CANDLE) ───
            size_signal = self._detect_climax_candle(
                open_arr, high_arr, low_arr, close_arr, tf
            )
            if size_signal is not None:
                signals.append(size_signal[0])
                reasons.append(size_signal[1])

            # ─── 5. ENGULFING PATTERN ───
            engulf_signal = self._detect_engulfing(
                open_arr, close_arr, tf
            )
            if engulf_signal is not None:
                signals.append(engulf_signal[0])
                reasons.append(engulf_signal[1])

        if not signals:
            return AgentSignal(self.name, 0.0, 0.0, "CANDLE_NO_DATA", self.weight)

        avg_signal = float(np.mean(signals))
        confidence = min(1.0, abs(avg_signal) * 0.9 + 0.15)

        return AgentSignal(
            self.name, float(np.clip(avg_signal, -1, 1)),
            float(np.clip(confidence, 0, 1)),
            " | ".join(reasons), self.weight
        )

    def _price_position_in_candle(self, o, h, l, c, tf):
        """Onde está o preço dentro do range do candle? Topo = risco BUY. Fundo = risco SELL."""
        candle_range = h - l
        if candle_range <= 0:
            return None
        
        # Percentual: 0 = low, 1 = high
        price_pct = (c - l) / candle_range
        
        # Fechou no topo absoluto do candle → Péssimo para BUY (já subiu tudo)
        if price_pct > 0.95:
            return (-0.5, f"{tf}:CLOSE_AT_HIGH({price_pct:.0%})")
        elif price_pct > 0.85:
            return (-0.3, f"{tf}:CLOSE_NEAR_HIGH({price_pct:.0%})")
        # Fechou no fundo absoluto → Péssimo para SELL (já caiu tudo)
        elif price_pct < 0.05:
            return (0.5, f"{tf}:CLOSE_AT_LOW({price_pct:.0%})")
        elif price_pct < 0.15:
            return (0.3, f"{tf}:CLOSE_NEAR_LOW({price_pct:.0%})")
        
        return None

    def _detect_rejection_wicks(self, opens, highs, lows, closes, tf):
        """
        Detecta padrões de rejeição via análise de wicks (pavios).
        
        - Pavio SUPERIOR longo + body pequeno = SHOOTING STAR → bearish
        - Pavio INFERIOR longo + body pequeno = HAMMER → bullish
        - Doji (body microscópico) = indecisão → neutro com flag
        """
        o, h, l, c = opens[-1], highs[-1], lows[-1], closes[-1]
        candle_range = h - l
        
        if candle_range <= 0:
            return None
        
        body = abs(c - o)
        upper_wick = h - max(o, c)
        lower_wick = min(o, c) - l
        
        body_ratio = body / candle_range
        upper_wick_ratio = upper_wick / candle_range
        lower_wick_ratio = lower_wick / candle_range
        
        # SHOOTING STAR: body pequeno + pavio superior > 60% do range
        if upper_wick_ratio > 0.60 and body_ratio < 0.25:
            return (-0.7, f"{tf}:SHOOTING_STAR(wick={upper_wick_ratio:.0%})")
        
        # HAMMER: body pequeno + pavio inferior > 60% do range
        if lower_wick_ratio > 0.60 and body_ratio < 0.25:
            return (0.7, f"{tf}:HAMMER(wick={lower_wick_ratio:.0%})")
        
        # Pavio superior dominante (>45%) = pressão vendedora
        if upper_wick_ratio > 0.45 and upper_wick_ratio > lower_wick_ratio * 2:
            return (-0.4, f"{tf}:UPPER_REJECTION(wick={upper_wick_ratio:.0%})")
        
        # Pavio inferior dominante (>45%) = pressão compradora
        if lower_wick_ratio > 0.45 and lower_wick_ratio > upper_wick_ratio * 2:
            return (0.4, f"{tf}:LOWER_REJECTION(wick={lower_wick_ratio:.0%})")
        
        # DOJI: body < 5% do range = indecisão total
        if body_ratio < 0.05:
            return (0.0, f"{tf}:DOJI(body={body_ratio:.0%})")
        
        return None

    def _detect_consecutive_candles(self, opens, closes, tf):
        """
        N candles consecutivos da mesma cor = exaustão do movimento.
        5+ verdes seguidos → provável reversão → VETA BUY
        5+ vermelhos seguidos → provável reversão → VETA SELL
        """
        n = len(closes)
        if n < 8:
            return None
        
        # Contar candles consecutivos da mesma direção
        green_streak = 0
        red_streak = 0
        
        for i in range(n - 1, max(n - 10, 0) - 1, -1):
            if closes[i] > opens[i]:  # Green
                if red_streak > 0:
                    break
                green_streak += 1
            elif closes[i] < opens[i]:  # Red
                if green_streak > 0:
                    break
                red_streak += 1
            else:
                break
        
        if green_streak >= 7:
            return (-0.8, f"{tf}:GREEN_STREAK_{green_streak}(EXHAUSTION)")
        elif green_streak >= 5:
            return (-0.5, f"{tf}:GREEN_STREAK_{green_streak}(CAUTION)")
        
        if red_streak >= 7:
            return (0.8, f"{tf}:RED_STREAK_{red_streak}(EXHAUSTION)")
        elif red_streak >= 5:
            return (0.5, f"{tf}:RED_STREAK_{red_streak}(CAUTION)")
        
        return None

    def _detect_climax_candle(self, opens, highs, lows, closes, tf):
        """
        Candle anormalmente grande = climax move = provável reversão.
        Se o candle atual é > 3x a média de body size das últimas 20 → exaustão.
        """
        bodies = np.abs(closes - opens)
        if len(bodies) < 20:
            return None
        
        avg_body = np.mean(bodies[-20:])
        if avg_body <= 0:
            return None
        
        current_body = bodies[-1]
        body_ratio = current_body / avg_body
        
        if body_ratio > 4.0:
            is_bullish = closes[-1] > opens[-1]
            if is_bullish:
                return (-0.7, f"{tf}:CLIMAX_BULL({body_ratio:.1f}x)")
            else:
                return (0.7, f"{tf}:CLIMAX_BEAR({body_ratio:.1f}x)")
        elif body_ratio > 3.0:
            is_bullish = closes[-1] > opens[-1]
            if is_bullish:
                return (-0.4, f"{tf}:BIG_BULL({body_ratio:.1f}x)")
            else:
                return (0.4, f"{tf}:BIG_BEAR({body_ratio:.1f}x)")
        
        return None

    def _detect_engulfing(self, opens, closes, tf):
        """
        Engulfing Pattern: O candle atual engolfa completamente o anterior.
        Bullish Engulfing: Candle verde que engolfa um vermelho → reversão para cima
        Bearish Engulfing: Candle vermelho que engolfa um verde → reversão para baixo
        """
        if len(opens) < 2:
            return None
        
        prev_o, prev_c = opens[-2], closes[-2]
        curr_o, curr_c = opens[-1], closes[-1]
        
        prev_body = abs(prev_c - prev_o)
        curr_body = abs(curr_c - curr_o)
        
        if prev_body <= 0:
            return None
        
        # Bullish Engulfing: prev was red, curr is green and engulfs
        if prev_c < prev_o and curr_c > curr_o:
            if curr_o <= prev_c and curr_c >= prev_o:
                engulf_ratio = curr_body / prev_body
                if engulf_ratio > 1.5:
                    return (0.6, f"{tf}:BULLISH_ENGULFING({engulf_ratio:.1f}x)")
        
        # Bearish Engulfing: prev was green, curr is red and engulfs
        if prev_c > prev_o and curr_c < curr_o:
            if curr_o >= prev_c and curr_c <= prev_o:
                engulf_ratio = curr_body / prev_body
                if engulf_ratio > 1.5:
                    return (-0.6, f"{tf}:BEARISH_ENGULFING({engulf_ratio:.1f}x)")
        
        return None
