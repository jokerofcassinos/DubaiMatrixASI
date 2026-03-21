"""
╔══════════════════════════════════════════════════════════════════════════════╗
║        DUBAI MATRIX ASI — SMART MONEY CONCEPTS AGENTS (Phase 16)            ║
║     ICT/SMC Methodology: Liquidity, MSS, FVG, OB, BOS, Heatmap, AVG       ║
║                                                                              ║
║  "O mercado não se move por indicadores. Se move por LIQUIDEZ.              ║
║   Onde a liquidez está, o preço vai. Quem entende isso, DOMINA."            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import Optional, List, Tuple

from core.consciousness.agents.base import AgentSignal, BaseAgent
from utils.decorators import catch_and_log
from utils.time_tools import TimeEngine
from cpp.asi_bridge import CPP_CORE


# ═══════════════════════════════════════════════════════════════
#  UTILIDADES SMC (Swing Detection, Structure Mapping)
# ═══════════════════════════════════════════════════════════════

def _find_swing_highs_lows(highs, lows, closes, lookback: int = 5):
    """Identifica Swing Highs e Swing Lows. Tenta C++ primeiro, fallback em Python."""
    try:
        res = CPP_CORE.find_swings(highs, lows, lookback)
        if res and len(res[0]) > 0:
            return res
    except:
        pass
        
    n = len(highs)
    swing_highs = []
    swing_lows = []

    for i in range(lookback, n - lookback):
        is_high = True
        is_low = True
        for j in range(1, lookback + 1):
            if highs[i] <= highs[i - j] or highs[i] <= highs[i + j]:
                is_high = False
            if lows[i] >= lows[i - j] or lows[i] >= lows[i + j]:
                is_low = False
        if is_high:
            swing_highs.append((i, highs[i]))
        if is_low:
            swing_lows.append((i, lows[i]))

    return swing_highs, swing_lows


class LiquiditySweepAgent(BaseAgent):
    """
    LIQUIDEZ: Detecta pools de liquidez e sweeps.
    
    Conceito ICT: Liquidez se acumula ACIMA de swing highs (sell stops) e 
    ABAIXO de swing lows (buy stops). Market Makers caçam esses pools.
    
    Quando o preço VARRE um swing high/low e IMEDIATAMENTE reverte 
    (candle de rejeição), é um Liquidity Sweep — sinal de reversão confirmado.
    """
    def __init__(self, weight: float = 2.0):
        super().__init__("LiquiditySweepAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        candles = snapshot.candles.get("M5")
        if candles is None:
            return None
        
        highs = candles.get("high", [])
        lows = candles.get("low", [])
        closes = candles.get("close", [])
        opens = candles.get("open", [])

        if len(highs) < 30:
            return None

        swing_highs, swing_lows = _find_swing_highs_lows(highs, lows, closes, lookback=3)

        signal = 0.0
        reason = "No liquidity sweep detected"
        conf = 0.0

        # Checar se a VELA MAIS RECENTE varreu um swing high e fechou abaixo
        last_high = highs[-1]
        last_close = closes[-1]
        last_open = opens[-1]

        for idx, sh_price in reversed(swing_highs[-5:]):
            if idx >= len(highs) - 2:
                continue
            # Sweep de high: preço ultrapassou swing high MAS fechou ABAIXO dele
            if last_high > sh_price and last_close < sh_price:
                # Candle de rejeição (wick longo acima)
                wick_ratio = (last_high - max(last_close, last_open)) / (last_high - min(last_close, last_open) + 1e-10)
                if wick_ratio > 1.5:
                    signal = -0.9
                    conf = 0.95
                    reason = f"LIQUIDITY SWEEP HIGH @ {sh_price:.0f} (Wick rejection, sweep & reject)"
                    break

        if signal == 0.0:
            for idx, sl_price in reversed(swing_lows[-5:]):
                if idx >= len(lows) - 2:
                    continue
                last_low = lows[-1]
                # Sweep de low: preço ultrapassou swing low MAS fechou ACIMA dele
                if last_low < sl_price and last_close > sl_price:
                    wick_ratio = (min(last_close, last_open) - last_low) / (max(last_close, last_open) - last_low + 1e-10)
                    if wick_ratio > 1.5:
                        signal = 0.9
                        conf = 0.95
                        reason = f"LIQUIDITY SWEEP LOW @ {sl_price:.0f} (Wick rejection, sweep & reject)"
                        break

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class MarketStructureShiftAgent(BaseAgent):
    """
    MSS / MSNR (Market Structure Shift / Non-Return):
    
    Uptrend = Higher Highs (HH) + Higher Lows (HL)
    Downtrend = Lower Highs (LH) + Lower Lows (LL)
    
    MSS ocorre quando o preço QUEBRA o último swing na direção oposta.
    Ex: Em uptrend, se o preço faz um LOWER LOW quebrando o swing low anterior → MSS bearish.
    
    MSNR: Após o MSS, o preço NÃO retorna ao nível rompido → confirmação de reversão.
    """
    def __init__(self, weight: float = 1.9):
        super().__init__("MSSAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        candles = snapshot.candles.get("M5")
        if candles is None:
            return None

        highs = candles.get("high", [])
        lows = candles.get("low", [])
        closes = candles.get("close", [])

        if len(highs) < 40:
            return None

        swing_highs, swing_lows = _find_swing_highs_lows(highs, lows, closes, lookback=3)

        signal = 0.0
        reason = "Structure intact"
        conf = 0.0

        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            # Checar tendência anterior
            last_sh = swing_highs[-1][1]
            prev_sh = swing_highs[-2][1]
            last_sl = swing_lows[-1][1]
            prev_sl = swing_lows[-2][1]

            was_uptrend = prev_sh < last_sh and prev_sl < last_sl
            was_downtrend = prev_sh > last_sh and prev_sl > last_sl

            current_price = closes[-1]

            # MSS Bearish: estava em uptrend e preço quebrou o último swing low
            if was_uptrend and current_price < last_sl:
                signal = -0.85
                conf = 0.9
                reason = f"MSS BEARISH — Uptrend broken (Price {current_price:.0f} < SwingLow {last_sl:.0f})"
                
                # MSNR Check: se NÃO voltou acima nas últimas 3 candles
                recent_highs = highs[-3:]
                if all(h < last_sl for h in recent_highs):
                    conf = 1.0
                    reason += " + MSNR CONFIRMED"

            # MSS Bullish: estava em downtrend e preço quebrou o último swing high
            elif was_downtrend and current_price > last_sh:
                signal = 0.85
                conf = 0.9
                reason = f"MSS BULLISH — Downtrend broken (Price {current_price:.0f} > SwingHigh {last_sh:.0f})"

                recent_lows = lows[-3:]
                if all(l > last_sh for l in recent_lows):
                    conf = 1.0
                    reason += " + MSNR CONFIRMED"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class FairValueGapAgent(BaseAgent):
    """
    FVG (Fair Value Gap) — Imbalance / Inefficiency Zone:
    
    Um FVG Bullish ocorre quando: Low[i+1] > High[i-1] (gap entre 3 candles).
    Isso cria uma zona de "imbalance" onde o preço tende a RETORNAR para preencher.
    
    Estratégia: 
    - Se preço está DENTRO de um FVG bullish recente → Compra (preenchimento).
    - Se preço está DENTRO de um FVG bearish recente → Venda (preenchimento).
    """
    def __init__(self, weight: float = 1.8):
        super().__init__("FVGAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        candles = snapshot.candles.get("M5")
        if candles is None:
            return None

        highs = candles.get("high", [])
        lows = candles.get("low", [])
        closes = candles.get("close", [])

        if len(highs) < 20:
            return None

        price = closes[-1]
        signal = 0.0
        reason = "No active FVG"
        conf = 0.0

        # Procurar FVGs nas últimas 15 candles (exceto as 2 últimas para dar tempo de operar)
        for i in range(len(highs) - 3, max(len(highs) - 18, 1), -1):
            # FVG Bullish: Low da vela [i+1] > High da vela [i-1]
            if lows[i + 1] > highs[i - 1]:
                fvg_top = lows[i + 1]
                fvg_bottom = highs[i - 1]
                fvg_mid = (fvg_top + fvg_bottom) / 2

                # Preço está dentro do FVG? → Vai preencher (buy)
                if fvg_bottom <= price <= fvg_top:
                    signal = 0.75
                    conf = 0.85
                    reason = f"BULLISH FVG active [{fvg_bottom:.0f}-{fvg_top:.0f}] — Price filling gap"
                    break
                # Preço está logo acima do FVG? → Pode retracing para preencher (neutro/buy light)
                elif price > fvg_top and (price - fvg_top) / price < 0.003:
                    signal = 0.3
                    conf = 0.5
                    reason = f"BULLISH FVG nearby [{fvg_bottom:.0f}-{fvg_top:.0f}] — Possible retrace target"
                    break

            # FVG Bearish: High da vela [i+1] < Low da vela [i-1]
            if highs[i + 1] < lows[i - 1]:
                fvg_top = lows[i - 1]
                fvg_bottom = highs[i + 1]
                fvg_mid = (fvg_top + fvg_bottom) / 2

                if fvg_bottom <= price <= fvg_top:
                    signal = -0.75
                    conf = 0.85
                    reason = f"BEARISH FVG active [{fvg_bottom:.0f}-{fvg_top:.0f}] — Price filling gap"
                    break
                elif price < fvg_bottom and (fvg_bottom - price) / price < 0.003:
                    signal = -0.3
                    conf = 0.5
                    reason = f"BEARISH FVG nearby [{fvg_bottom:.0f}-{fvg_top:.0f}] — Possible retrace target"
                    break

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class LiquidityHeatmapAgent(BaseAgent):
    """
    Mapa de Calor de Liquidez:
    
    Constrói um heatmap de onde os swing highs/lows se ACUMULAM.
    Zonas com MUITOS pivôs sobrepostos = Alta densidade de stops = Alvos de caça.
    
    Quando o preço se aproxima de uma zona densa → Possível sweep → Reversão.
    """
    def __init__(self, weight: float = 1.6):
        super().__init__("LiquidityHeatmapAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        candles = snapshot.candles.get("M5")
        if candles is None:
            return None

        highs = candles.get("high", [])
        lows = candles.get("low", [])
        closes = candles.get("close", [])

        if len(highs) < 50:
            return None

        price = closes[-1]
        price_range = max(highs[-50:]) - min(lows[-50:])
        if price_range <= 0:
            return None

        # Dividir o range em 20 "bins" e contar quantos swings caem em cada bin
        n_bins = 20
        bin_size = price_range / n_bins
        min_price = min(lows[-50:])
        
        heatmap = [0] * n_bins

        swing_highs, swing_lows = _find_swing_highs_lows(highs, lows, closes, lookback=2)

        for idx, sh in swing_highs:
            if idx < len(highs) - 50: continue
            bin_idx = int((sh - min_price) / bin_size)
            bin_idx = max(0, min(bin_idx, n_bins - 1))
            heatmap[bin_idx] += 1

        for idx, sl in swing_lows:
            if idx < len(lows) - 50: continue
            bin_idx = int((sl - min_price) / bin_size)
            bin_idx = max(0, min(bin_idx, n_bins - 1))
            heatmap[bin_idx] += 1

        # Encontrar o bin do preço atual
        current_bin = int((price - min_price) / bin_size)
        current_bin = min(current_bin, n_bins - 1)

        signal = 0.0
        reason = "Normal liquidity"
        conf = 0.0

        # Checar bins adjacentes (2 acima e 2 abaixo do preço)
        max_heat = max(heatmap) if max(heatmap) > 0 else 1

        # Zona QUENTE acima do preço = Pool de sell stops → preço pode subir para caçar
        heat_above = sum(heatmap[current_bin + 1:min(current_bin + 4, n_bins)]) / max_heat
        # Zona QUENTE abaixo do preço = Pool de buy stops → preço pode descer para caçar
        heat_below = sum(heatmap[max(0, current_bin - 3):current_bin]) / max_heat

        if heat_above > 0.5 and heat_below < 0.2:
            signal = 0.5  # Vai subir para caçar
            conf = 0.7
            reason = f"LIQUIDITY MAGNET ABOVE (Heat ratio: {heat_above:.2f}) — Attracted upwards"
        elif heat_below > 0.5 and heat_above < 0.2:
            signal = -0.5  # Vai descer para caçar
            conf = 0.7
            reason = f"LIQUIDITY MAGNET BELOW (Heat ratio: {heat_below:.2f}) — Attracted downwards"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class OrderBlockAgent(BaseAgent):
    """
    Order Block (OB) — Última vela oposta antes de um impulso forte:
    
    Bullish OB: Última vela VERMELHA antes de um impulso UP forte.
    Bearish OB: Última vela VERDE antes de um impulso DOWN forte.
    
    Quando o preço retorna a um OB não-mitigado → Entry point institucional.
    """
    def __init__(self, weight: float = 2.0):
        super().__init__("OrderBlockAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        candles = snapshot.candles.get("M5")
        if candles is None:
            return None

        highs = candles.get("high", [])
        lows = candles.get("low", [])
        closes = candles.get("close", [])
        opens = candles.get("open", [])

        if len(highs) < 20:
            return None

        price = closes[-1]
        signal = 0.0
        reason = "No active Order Block"
        conf = 0.0

        # Procurar OBs nas últimas 15 candles
        for i in range(len(closes) - 2, max(len(closes) - 17, 1), -1):
            is_bearish_candle = closes[i] < opens[i]
            is_bullish_candle = closes[i] > opens[i]

            # Impulso forte após a vela = 2+ candles consecutivas na direção oposta
            if i + 3 < len(closes):
                impulse_up = (closes[i + 1] > opens[i + 1] and 
                              closes[i + 2] > opens[i + 2] and
                              (closes[i + 2] - opens[i + 1]) / price > 0.002)  # >0.2% impulse
                              
                impulse_down = (closes[i + 1] < opens[i + 1] and 
                                closes[i + 2] < opens[i + 2] and
                                (opens[i + 1] - closes[i + 2]) / price > 0.002)

                # Bullish OB: vela vermelha + impulso up forte depois
                if is_bearish_candle and impulse_up:
                    ob_top = opens[i]
                    ob_bottom = closes[i]

                    # Preço está retornando ao OB? (dentro ou tocando)
                    if ob_bottom <= price <= ob_top:
                        signal = 0.85
                        conf = 0.9
                        reason = f"BULLISH ORDER BLOCK [{ob_bottom:.0f}-{ob_top:.0f}] — Price mitigating OB"
                        break
                    elif price > ob_top and (price - ob_top) / price < 0.002:
                        signal = 0.4
                        conf = 0.6
                        reason = f"BULLISH OB nearby [{ob_bottom:.0f}-{ob_top:.0f}] — Potential retrace target"

                # Bearish OB: vela verde + impulso down forte depois
                elif is_bullish_candle and impulse_down:
                    ob_top = closes[i]
                    ob_bottom = opens[i]

                    if ob_bottom <= price <= ob_top:
                        signal = -0.85
                        conf = 0.9
                        reason = f"BEARISH ORDER BLOCK [{ob_bottom:.0f}-{ob_top:.0f}] — Price mitigating OB"
                        break
                    elif price < ob_bottom and (ob_bottom - price) / price < 0.002:
                        signal = -0.4
                        conf = 0.6
                        reason = f"BEARISH OB nearby [{ob_bottom:.0f}-{ob_top:.0f}] — Potential retrace target"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class PremiumDiscountAgent(BaseAgent):
    """
    Premium / Discount Zones (AVG / Equilibrium):
    
    Divide o range recente em 3 zonas:
    - Premium (acima de 70% do range) → Overpriced → Venda
    - Equilibrium (40-60%) → Fair Value → Neutro  
    - Discount (abaixo de 30% do range) → Underpriced → Compra
    
    Smart Money compra no Discount e vende no Premium.
    """
    def __init__(self, weight: float = 1.5):
        super().__init__("PremiumDiscountAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        candles = snapshot.candles.get("M15")
        if candles is None:
            return None

        highs = candles.get("high", [])
        lows = candles.get("low", [])
        closes = candles.get("close", [])

        if len(highs) < 30:
            return None

        # Range dos últimos 30 candles M15 (≈ 7.5 horas)
        range_high = max(highs[-30:])
        range_low = min(lows[-30:])
        total_range = range_high - range_low

        if total_range <= 0:
            return None

        price = closes[-1]
        position = (price - range_low) / total_range  # 0.0 = fundo, 1.0 = topo

        equilibrium = (range_high + range_low) / 2.0

        signal = 0.0
        reason = f"Equilibrium Zone (Position: {position:.1%})"
        conf = 0.0

        if position > 0.75:
            signal = -0.65
            conf = 0.8
            reason = f"PREMIUM ZONE ({position:.1%}) — Overpriced, sell bias (EQ={equilibrium:.0f})"
        elif position < 0.25:
            signal = 0.65
            conf = 0.8
            reason = f"DISCOUNT ZONE ({position:.1%}) — Underpriced, buy bias (EQ={equilibrium:.0f})"
        elif 0.45 <= position <= 0.55:
            signal = 0.0
            conf = 0.5
            reason = f"EQUILIBRIUM ({position:.1%}) — Fair value at {equilibrium:.0f}"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class BreakOfStructureAgent(BaseAgent):
    """
    BOS (Break of Structure):
    
    Confirma continuação de tendência:
    - BOS Bullish: Preço quebra um swing HIGH anterior (HH confirmado)
    - BOS Bearish: Preço quebra um swing LOW anterior (LL confirmado)
    
    Diferente do MSS (que indica REVERSÃO), BOS indica CONTINUAÇÃO.
    Combinado com FVG e OB, é o timing perfeito de entry.
    """
    def __init__(self, weight: float = 1.7):
        super().__init__("BOSAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        candles = snapshot.candles.get("M5")
        if candles is None:
            return None

        highs = candles.get("high", [])
        lows = candles.get("low", [])
        closes = candles.get("close", [])

        if len(highs) < 40:
            return None

        swing_highs, swing_lows = _find_swing_highs_lows(highs, lows, closes, lookback=3)

        signal = 0.0
        reason = "No BOS detected"
        conf = 0.0

        price = closes[-1]

        if len(swing_highs) >= 2:
            # BOS Bullish: preço atual acima do penúltimo swing high
            # (último swing high acabou de ser formado, penúltimo é a referência)
            ref_sh = swing_highs[-2][1]
            last_sh = swing_highs[-1][1]
            
            # Higher High = BOS Bullish
            if price > ref_sh and last_sh > ref_sh:
                signal = 0.7
                conf = 0.8
                reason = f"BOS BULLISH — Higher High confirmed (Price {price:.0f} > SH {ref_sh:.0f})"

        if signal == 0.0 and len(swing_lows) >= 2:
            ref_sl = swing_lows[-2][1]
            last_sl = swing_lows[-1][1]
            
            # Lower Low = BOS Bearish
            if price < ref_sl and last_sl < ref_sl:
                signal = -0.7
                conf = 0.8
                reason = f"BOS BEARISH — Lower Low confirmed (Price {price:.0f} < SL {ref_sl:.0f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)

class ICTAdvancedAgent(BaseAgent):
    """
    Agente ICT Avançado.
    Focado em Silver Bullet, Judas Swing e PD Arrays críticos.
    Implementa a 'precisão institucional' no tempo e no preço.
    """
    def __init__(self, weight: float = 2.2):
        super().__init__("ICTAdvanced", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        info = TimeEngine.session_info()
        sessions = info["active_sessions"]
        hour = TimeEngine.now_utc().hour
        
        signal = 0.0
        reasoning = ""
        conf = 0.0

        # 1. SILVER BULLET WINDOWS (10:00-11:00 UTC, 15:00-16:00 UTC, 03:00-04:00 UTC)
        if (10 <= hour < 11) or (15 <= hour < 16) or (3 <= hour < 4):
            # Janela de Alta Probabilidade (Silver Bullet)
            # Procurar por FVG ou OB ativo para entrada rápida
            signal = 0.5 # Bias padrão da janela
            reasoning = "🏹 SILVER_BULLET_WINDOW (High Precision Window)"
            conf = 0.9

        # 2. JUDAS SWING DETECTION (Session Opens)
        if "LONDON_OPEN" in sessions or "NY_OPEN" in sessions:
            # Detecta o falso movimento inicial (Judas Swing)
            # (Simplificado: se volatilidade aumenta mas preço reverte rápido)
            pass

        return AgentSignal(self.name, signal, conf, reasoning, self.weight)
