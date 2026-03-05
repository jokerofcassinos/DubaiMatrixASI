"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          DUBAI MATRIX ASI — MARKET DYNAMICS AGENTS (Phase 19)              ║
║                                                                              ║
║  5 SISTEMAS ASI DE ANÁLISE COMPLEXA DE GRÁFICO E CANDLES:                   ║
║                                                                              ║
║  1. PriceGravityAgent      — GRAVIDADE: Campos gravitacionais de preço      ║
║  2. AggressivenessAgent    — AGRESSIVIDADE: Força bruta do mercado          ║
║  3. ExplosionDetectorAgent — EXPLOSÃO: Detecção de movimentos explosivos    ║
║  4. PriceVelocityAgent     — VELOCIDADE: Cinemática vetorial de preço       ║
║  5. OscillationWaveAgent   — OSCILAÇÃO: Análise de ondas e ressonância      ║
║                                                                              ║
║  Cada agente transforma conceitos da Dinâmica Clássica e Quântica em        ║
║  ferramentas de leitura de mercado que NENHUM livro de AT documentou.       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import Optional

from core.consciousness.agents.base import AgentSignal, BaseAgent
from utils.decorators import catch_and_log


# ═══════════════════════════════════════════════════════════════
#  AGENT 1: PRICE GRAVITY — Campos Gravitacionais de Preço
# ═══════════════════════════════════════════════════════════════

class PriceGravityAgent(BaseAgent):
    """
    GRAVIDADE — Lei da Gravitação Universal transposta para o mercado.
    
    CONCEITO FÍSICO:
    Na física, F = G * (m1 * m2) / r²
    A força gravitacional é proporcional à massa e inversamente proporcional
    ao quadrado da distância.
    
    TRANSPOSIÇÃO PARA MERCADO:
    - "Massa" = Volume acumulado em um nível de preço (Volume Profile).
      Quanto mais volume trocou num nível, maior sua "massa gravitacional".
    - "Distância" = Diferença de preço entre o nível atual e o atrator.
    - "Força Gravitacional" = Probabilidade de o preço ser PUXADO de volta
      para esse nível de alta massa.
    
    SINAIS:
    - Preço se afastando de um atrator massivo SEM momentum suficiente 
      → vai ser puxado de volta (contra-trend)
    - Preço rompendo a órbita gravitacional com velocidade de escape
      → breakout legítimo (trend continuation)
    - Múltiplos atratores na mesma direção → campo gravitacional direcional
    
    INOVAÇÃO PROPRIETÁRIA:
    - "Velocidade de Escape" = ATR * sqrt(Volume Ratio) — o momentum mínimo
      necessário para escapar de um campo gravitacional.
    - "Poço Gravitacional" = Cluster de volume onde o preço tende a orbitar.
    """

    def __init__(self, weight: float = 1.6):
        super().__init__("PriceGravityAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        signals = []
        reasons = []

        for tf in ["M1", "M5", "M15"]:
            candles = snapshot.candles.get(tf)
            if candles is None:
                continue

            close = np.array(candles["close"], dtype=np.float64)
            volume = np.array(candles["tick_volume"], dtype=np.float64)
            high = np.array(candles["high"], dtype=np.float64)
            low = np.array(candles["low"], dtype=np.float64)

            if len(close) < 30:
                continue

            current_price = close[-1]

            # ─── 1. CALCULAR CAMPO GRAVITACIONAL (Volume-Weighted Price Levels) ───
            # Discretizar range de preços em bins e acumular volume
            price_range = high.max() - low.min()
            if price_range <= 0:
                continue

            n_bins = 50
            bin_edges = np.linspace(low.min(), high.max(), n_bins + 1)
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            volume_profile = np.zeros(n_bins)

            for i in range(len(close)):
                # Cada candle distribui volume entre low e high
                low_idx = max(0, int((low[i] - low.min()) / price_range * n_bins) - 1)
                high_idx = min(n_bins - 1, int((high[i] - low.min()) / price_range * n_bins))
                for j in range(low_idx, high_idx + 1):
                    volume_profile[j] += volume[i] / max(1, high_idx - low_idx + 1)

            # Normalizar volume profile
            total_vol = volume_profile.sum()
            if total_vol <= 0:
                continue
            mass = volume_profile / total_vol

            # ─── 2. FORÇA GRAVITACIONAL SOBRE O PREÇO ATUAL ───
            gravity_force = 0.0
            for i in range(n_bins):
                dist = current_price - bin_centers[i]
                if abs(dist) < 1e-6:
                    continue
                # F = m / r² (força normalizada, sinal indica direção)
                force = mass[i] / (dist ** 2) * np.sign(-dist)  # Atração: puxa em direção ao cluster
                gravity_force += force

            # Normalizar para [-1, +1]
            gravity_signal = np.clip(gravity_force * 1e4, -1.0, 1.0)

            # ─── 3. DETECTAR POÇO GRAVITACIONAL DOMINANTE ───
            # O bin de maior massa é o POC (Point of Control gravitacional)
            poc_idx = np.argmax(mass)
            poc_price = bin_centers[poc_idx]
            poc_mass = mass[poc_idx]
            dist_to_poc = (current_price - poc_price) / current_price * 100

            # ─── 4. VELOCIDADE DE ESCAPE ───
            # Para escapar do poço gravitacional, o momentum (ATR relativo) deve superar a massa
            atr = snapshot.indicators.get(f"{tf}_atr_14")
            if atr is not None and len(atr) > 0 and atr[-1] > 0:
                current_atr = float(atr[-1])
                vol_ratio = volume[-1] / np.mean(volume[-20:]) if np.mean(volume[-20:]) > 0 else 1.0
                escape_velocity = current_atr * np.sqrt(max(vol_ratio, 0.1))
                price_momentum = abs(close[-1] - close[-3]) if len(close) >= 3 else 0

                if abs(dist_to_poc) < 0.1:
                    # Preço dentro do poço gravitacional → vai ficar preso (range)
                    gravity_signal *= 0.3  # Reduzir sinal (indecisão)
                    reasons.append(f"{tf}:GRAVITY_WELL(POC={poc_price:.0f} mass={poc_mass:.2f})")
                elif price_momentum > escape_velocity * 1.5:
                    # Velocidade de escape atingida → Breakout legítimo
                    direction = np.sign(close[-1] - close[-3])
                    gravity_signal = direction * 0.8
                    reasons.append(
                        f"{tf}:ESCAPE_VELOCITY(mom={price_momentum:.1f}>{escape_velocity:.1f})"
                    )
                else:
                    # Sendo puxado de volta pelo campo gravitacional
                    if dist_to_poc > 0.05:
                        gravity_signal = -0.6  # Preço acima do POC → gravidade puxa pra baixo
                        reasons.append(f"{tf}:GRAVITY_PULL_DOWN(dist={dist_to_poc:.2f}%)")
                    elif dist_to_poc < -0.05:
                        gravity_signal = 0.6  # Preço abaixo do POC → gravidade puxa pra cima
                        reasons.append(f"{tf}:GRAVITY_PULL_UP(dist={dist_to_poc:.2f}%)")

            signals.append(gravity_signal)

        if not signals:
            return AgentSignal(self.name, 0.0, 0.0, "GRAVITY_NO_DATA", self.weight)

        avg = float(np.mean(signals))
        conf = min(1.0, abs(avg) * 0.85 + 0.15)
        return AgentSignal(
            self.name, float(np.clip(avg, -1, 1)),
            float(np.clip(conf, 0, 1)),
            " | ".join(reasons) if reasons else "GRAVITY_NEUTRAL", self.weight
        )


# ═══════════════════════════════════════════════════════════════
#  AGENT 2: AGGRESSIVENESS — Medida de Força Bruta do Mercado
# ═══════════════════════════════════════════════════════════════

class AggressivenessAgent(BaseAgent):
    """
    AGRESSIVIDADE — Mede a INTENSIDADE e VIOLÊNCIA de cada movimento.
    
    CONCEITO:
    Agressividade não é simplesmente "o preço subiu". É a FORMA como subiu.
    Um preço que sobe 100 pontos em 1 minuto com volume 10x a média
    é radicalmente diferente de um que sobe 100 pontos em 30 minutos
    com volume normal.
    
    MÉTRICAS PROPRIETÁRIAS:
    1. Body-to-Range Ratio (BRR): Candles "cheios" = agressivos, wicks longas = hesitantes
    2. Volume Intensity Index (VII): Volume / Média normalizado pela amplitude do candle
    3. Candle Acceleration: 2ª derivada do tamanho do body (acelerando ou desacelerando?)
    4. Directional Aggression: Compara agressividade dos bulls vs bears
    5. Aggression Divergence: Agressividade subindo mas preço parando = armadilha
    
    SINAIS:
    - Alta agressividade compradora + momentum → BUY forte
    - Alta agressividade vendedora + momentum → SELL forte
    - Agressividade decaindo após pump → Exaustão iminente
    - Divergência preço×agressividade → Armadilha/Reversão
    """

    def __init__(self, weight: float = 1.7):
        super().__init__("AggressivenessAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        signals = []
        reasons = []

        for tf in ["M1", "M5"]:
            candles = snapshot.candles.get(tf)
            if candles is None:
                continue

            opens = np.array(candles["open"], dtype=np.float64)
            highs = np.array(candles["high"], dtype=np.float64)
            lows = np.array(candles["low"], dtype=np.float64)
            closes = np.array(candles["close"], dtype=np.float64)
            volumes = np.array(candles["tick_volume"], dtype=np.float64)

            n = len(closes)
            if n < 20:
                continue

            # ─── 1. BODY-TO-RANGE RATIO (BRR) — Último candle ───
            ranges = highs - lows
            bodies = np.abs(closes - opens)
            brr = np.divide(bodies, ranges, out=np.zeros_like(bodies), where=ranges > 0)
            current_brr = brr[-1]

            # ─── 2. VOLUME INTENSITY INDEX (VII) ───
            avg_vol_20 = np.mean(volumes[-20:])
            if avg_vol_20 > 0:
                vol_intensity = volumes[-1] / avg_vol_20
            else:
                vol_intensity = 1.0

            # ─── 3. CANDLE BODY ACCELERATION (2ª Derivada) ───
            if n >= 5:
                body_sizes = bodies[-5:]
                body_velocity = np.diff(body_sizes)  # 1ª derivada
                body_accel = np.diff(body_velocity)   # 2ª derivada
                is_accelerating = body_accel[-1] > 0 if len(body_accel) > 0 else False
            else:
                is_accelerating = False

            # ─── 4. DIRECTIONAL AGGRESSION ───
            # Separar candles em bull vs bear e medir agressividade média de cada
            bull_mask = closes > opens
            bear_mask = closes < opens

            bull_aggr = np.mean(brr[-10:][bull_mask[-10:]]) if np.any(bull_mask[-10:]) else 0
            bear_aggr = np.mean(brr[-10:][bear_mask[-10:]]) if np.any(bear_mask[-10:]) else 0

            # Aggression Score combinado
            is_bullish_candle = closes[-1] > opens[-1]
            direction = 1.0 if is_bullish_candle else -1.0

            # Alta BRR (corpo cheio) + Alto volume = agressão pura
            raw_aggression = current_brr * vol_intensity * direction

            # ─── 5. AGGRESSION DIVERGENCE ───
            # Se agressividade está subindo mas preço está plano → armadilha
            if n >= 10:
                aggr_trend = np.mean(brr[-3:] * volumes[-3:]) - np.mean(brr[-10:-3] * volumes[-10:-3])
                price_change = closes[-1] - closes[-10]

                if aggr_trend > 0 and abs(price_change) < np.mean(ranges[-10:]) * 0.3:
                    # Agressividade subindo, preço parado → absorção (contra-sinal)
                    raw_aggression *= -0.5
                    reasons.append(f"{tf}:AGGR_DIVERGENCE(aggr↑ price→)")

            # Construir sinal
            signal = np.clip(raw_aggression, -1.0, 1.0)

            if abs(signal) > 0.5:
                accel_str = "ACCEL" if is_accelerating else "DECEL"
                reasons.append(
                    f"{tf}:AGGRESSION({'BUY' if signal > 0 else 'SELL'} "
                    f"BRR={current_brr:.0%} VII={vol_intensity:.1f}x {accel_str})"
                )

            # Exaustão: alta agressividade decaindo
            if n >= 5 and current_brr < np.mean(brr[-5:-1]) * 0.5 and vol_intensity > 2.0:
                # O candle atual é fraco vs os anteriores que eram fortes
                signal *= -0.3  # Inversion por exaustão
                reasons.append(f"{tf}:AGGR_EXHAUSTION(BRR dropping)")
            elif vol_intensity > 15.0:  # Phase 29: Climax de Volume Absurdo (Squeeze Trap)
                signal *= 0.1
                reasons.append(f"{tf}:CLIMAX_DAMPING(vol > 15x)")

            signals.append(float(signal))

        if not signals:
            return AgentSignal(self.name, 0.0, 0.0, "AGGR_NO_DATA", self.weight)

        avg = float(np.mean(signals))
        conf = min(1.0, abs(avg) * 0.9 + 0.1)
        return AgentSignal(
            self.name, float(np.clip(avg, -1, 1)),
            float(np.clip(conf, 0, 1)),
            " | ".join(reasons) if reasons else "AGGR_NEUTRAL", self.weight
        )


# ═══════════════════════════════════════════════════════════════
#  AGENT 3: EXPLOSION DETECTOR — Movimentos Explosivos
# ═══════════════════════════════════════════════════════════════

class ExplosionDetectorAgent(BaseAgent):
    """
    EXPLOSÃO — Detecta e mede rupturas explosivas no mercado.
    
    CONCEITO FÍSICO:
    Uma explosão é uma liberação SÚBITA de energia acumulada.
    No mercado: compressão de volatilidade (squeeze) seguida de
    expansão violenta (explosion).
    
    MÉTRICAS PROPRIETÁRIAS:
    1. Squeeze Index: BB Width / ATR — quão comprimido o preço está
    2. Explosion Score: Tamanho do breakout vs tamanho da compressão
    3. Energy Release Rate: Velocidade de expansão da volatilidade
    4. Directional Conviction: Se a explosão tem direção clara ou é ruído
    5. Post-Explosion Phase: Se já explodiu → estamos na onda de choque ou no vácuo?
    
    CICLO COMPLETO:
    COMPRESSÃO → IGNIÇÃO → EXPLOSÃO → ONDA DE CHOQUE → EXAUSTÃO → COMPRESSÃO
    
    SINAIS:
    - Compressão extrema + volume crescente → EXPLOSÃO IMINENTE
    - Explosão ativa com sinal direcional → TRADE na direção
    - Pós-explosão (onda de choque) → CAUTION (instável)
    - Exaustão pós-explosão → REVERSÃO ou consolidação
    """

    def __init__(self, weight: float = 2.0):
        super().__init__("ExplosionDetectorAgent", weight)
        self._prev_phase = "UNKNOWN"

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        signals = []
        reasons = []

        for tf in ["M1", "M5"]:
            candles = snapshot.candles.get(tf)
            if candles is None:
                continue

            closes = np.array(candles["close"], dtype=np.float64)
            highs = np.array(candles["high"], dtype=np.float64)
            lows = np.array(candles["low"], dtype=np.float64)
            opens = np.array(candles["open"], dtype=np.float64)
            volumes = np.array(candles["tick_volume"], dtype=np.float64)
            indicators = snapshot.indicators

            if len(closes) < 30:
                continue

            # ─── 1. SQUEEZE INDEX (Compressão de Volatilidade) ───
            bb_width = indicators.get(f"{tf}_bb_width")
            atr = indicators.get(f"{tf}_atr_14")

            if bb_width is None or atr is None:
                continue
            if len(bb_width) < 20 or len(atr) < 20:
                continue

            current_bbw = float(bb_width[-1])
            avg_bbw = float(np.mean(bb_width[-20:]))
            current_atr = float(atr[-1])
            avg_atr = float(np.mean(atr[-20:]))

            if avg_bbw <= 0 or avg_atr <= 0:
                continue

            squeeze_index = current_bbw / avg_bbw  # < 0.5 = forte compressão
            energy_ratio = current_atr / avg_atr    # > 2.0 = explosão em curso

            # ─── 2. DETECTAR FASE DO CICLO ───
            ranges = highs - lows
            current_range = ranges[-1]
            avg_range = np.mean(ranges[-20:])
            range_ratio = current_range / avg_range if avg_range > 0 else 1.0

            vol_ratio = volumes[-1] / np.mean(volumes[-20:]) if np.mean(volumes[-20:]) > 0 else 1.0

            phase = "NEUTRAL"
            signal = 0.0

            if squeeze_index < 0.5:
                # COMPRESSÃO EXTREMA — Energia se acumulando
                phase = "COMPRESSION"
                if vol_ratio > 1.5:
                    # Volume crescendo na compressão = ignição iminente
                    phase = "IGNITION"
                    # Prever direção pela tendência sutil dentro da compressão
                    micro_trend = closes[-1] - closes[-5]
                    signal = np.sign(micro_trend) * 0.4
                    reasons.append(f"{tf}:IGNITION(squeeze={squeeze_index:.2f} vol={vol_ratio:.1f}x)")
                else:
                    signal = 0.0
                    reasons.append(f"{tf}:COMPRESSION(squeeze={squeeze_index:.2f})")

            elif range_ratio > 3.0 and energy_ratio > 1.8:
                # EXPLOSÃO ATIVA
                phase = "EXPLOSION"
                direction = np.sign(closes[-1] - opens[-1])
                conviction = min(1.0, range_ratio / 5.0)
                signal = direction * conviction
                reasons.append(
                    f"{tf}:EXPLOSION!({range_ratio:.1f}x range, "
                    f"energy={energy_ratio:.1f}x, dir={'UP' if direction > 0 else 'DOWN'})"
                )

            elif range_ratio > 2.0 and energy_ratio > 1.3:
                # ONDA DE CHOQUE — Pós-explosão, instável
                phase = "SHOCKWAVE"
                bodies = np.abs(closes[-3:] - opens[-3:])
                wicks = ranges[-3:] - bodies
                if np.mean(wicks) > np.mean(bodies):
                    # Mais wick que body = instabilidade = cautela
                    signal = 0.0
                    reasons.append(f"{tf}:SHOCKWAVE(instable, caution)")
                else:
                    direction = np.sign(closes[-1] - closes[-3])
                    signal = direction * 0.5
                    reasons.append(f"{tf}:SHOCKWAVE(momentum={direction:+.0f})")

            elif energy_ratio < 0.6 and self._prev_phase in ("EXPLOSION", "SHOCKWAVE"):
                # EXAUSTÃO PÓS-EXPLOSÃO
                phase = "EXHAUSTION"
                last_move = closes[-1] - closes[-5]
                signal = -np.sign(last_move) * 0.5
                reasons.append(f"{tf}:POST_EXPLOSION_EXHAUSTION(energy↓)")

            self._prev_phase = phase
            signals.append(float(signal))

        if not signals:
            return AgentSignal(self.name, 0.0, 0.0, "EXPLOSION_NO_DATA", self.weight)

        avg = float(np.mean(signals))
        conf = min(1.0, abs(avg) * 0.85 + 0.15)
        return AgentSignal(
            self.name, float(np.clip(avg, -1, 1)),
            float(np.clip(conf, 0, 1)),
            " | ".join(reasons) if reasons else "EXPLOSION_NEUTRAL", self.weight
        )


# ═══════════════════════════════════════════════════════════════
#  AGENT 4: PRICE VELOCITY — Cinemática Vetorial de Preço
# ═══════════════════════════════════════════════════════════════

class PriceVelocityAgent(BaseAgent):
    """
    VELOCIDADE — Leis da Cinemática (Newton) aplicadas ao preço.
    
    CONCEITO FÍSICO:
    - Posição = Preço
    - Velocidade = Δpreço/Δtempo (1ª derivada)
    - Aceleração = Δvelocidade/Δtempo (2ª derivada)
    - Jerk = Δaceleração/Δtempo (3ª derivada — mudança de aceleração)
    
    PRINCÍPIOS CINEMÁTICOS TRANSPOSTOS:
    1. Corpo em aceleração positiva → vai continuar subindo (inércia)
    2. Velocidade alta + aceleração negativa → vai parar e reverter
    3. Jerk positivo → aceleração está AUMENTANDO (início de impulso)
    4. Jerk negativo → aceleração está DIMINUINDO (fim de impulso)
    5. Velocidade zero mas aceleração não-zero → ponto de inflexão
    
    INOVAÇÃO: Velocidade multi-timeframe vetorial (MTV)
    Combina vetores de velocidade de M1, M5, M15 em um vetor
    resultante. Quando TODOS os timeframes apontam na mesma direção
    COM aceleração → alta convicção.
    """

    def __init__(self, weight: float = 1.8):
        super().__init__("PriceVelocityAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        velocity_vectors = []
        acceleration_vectors = []
        jerk_vectors = []
        reasons = []

        for tf in ["M1", "M5", "M15"]:
            candles = snapshot.candles.get(tf)
            if candles is None:
                continue

            closes = np.array(candles["close"], dtype=np.float64)
            if len(closes) < 15:
                continue

            # ─── CINEMÁTICA: Posição → Velocidade → Aceleração → Jerk ───
            # Normalizar preços para variação percentual
            pct_change = np.diff(closes) / closes[:-1] * 100

            if len(pct_change) < 5:
                continue

            # Velocidade instantânea (últimos 3 candles)
            velocity = np.mean(pct_change[-3:])

            # Aceleração (diferença entre velocidades recentes vs anteriores)
            v_recent = np.mean(pct_change[-3:])
            v_prev = np.mean(pct_change[-6:-3]) if len(pct_change) >= 6 else v_recent
            acceleration = v_recent - v_prev

            # Jerk (mudança de aceleração)
            if len(pct_change) >= 9:
                v_old = np.mean(pct_change[-9:-6])
                a_prev = v_prev - v_old
                jerk = acceleration - a_prev
            else:
                jerk = 0.0

            velocity_vectors.append(velocity)
            acceleration_vectors.append(acceleration)
            jerk_vectors.append(jerk)

            # ─── CLASSIFICAR REGIME CINEMÁTICO ───
            if abs(velocity) > 0.05:  # Threshold mínimo de velocidade
                if velocity > 0 and acceleration > 0:
                    reasons.append(f"{tf}:ACCEL_UP(v={velocity:+.3f}% a={acceleration:+.3f})")
                elif velocity > 0 and acceleration < 0:
                    reasons.append(f"{tf}:DECEL_UP(v={velocity:+.3f}% a={acceleration:+.3f})")
                elif velocity < 0 and acceleration < 0:
                    reasons.append(f"{tf}:ACCEL_DOWN(v={velocity:+.3f}% a={acceleration:+.3f})")
                elif velocity < 0 and acceleration > 0:
                    reasons.append(f"{tf}:DECEL_DOWN(v={velocity:+.3f}% a={acceleration:+.3f})")

        if not velocity_vectors:
            return AgentSignal(self.name, 0.0, 0.0, "VELOCITY_NO_DATA", self.weight)

        # ─── VETOR RESULTANTE MULTI-TIMEFRAME ───
        # Pesos crescentes para TFs mais altos (M15 > M5 > M1)
        tf_weights = [0.3, 0.4, 0.3][:len(velocity_vectors)]

        avg_velocity = sum(v * w for v, w in zip(velocity_vectors, tf_weights))
        avg_accel = sum(a * w for a, w in zip(acceleration_vectors, tf_weights))
        avg_jerk = sum(j * w for j, w in zip(jerk_vectors, tf_weights))

        # ─── SINAL FINAL ───
        # Velocidade dá a direção, aceleração confirma, jerk antecipa
        signal = 0.0

        if avg_velocity > 0 and avg_accel > 0:
            # Subindo + acelerando = FORTE compra
            signal = min(1.0, avg_velocity * 5 + avg_accel * 10)
        elif avg_velocity < 0 and avg_accel < 0:
            # Caindo + acelerando = FORTE venda
            signal = max(-1.0, avg_velocity * 5 + avg_accel * 10)
        elif avg_velocity > 0 and avg_accel < 0:
            # Subindo mas desacelerando → possível reversão
            signal = avg_velocity * 2  # Sinal mais fraco
            if avg_jerk < -0.01:
                signal *= 0.3  # Jerk negativo = desaceleração AUMENTANDO = iminente parada
                reasons.append("JERK_NEG(decel increasing)")
        elif avg_velocity < 0 and avg_accel > 0:
            # Caindo mas desacelerando → possível fundo
            signal = avg_velocity * 2
            if avg_jerk > 0.01:
                signal *= 0.3
                reasons.append("JERK_POS(decel increasing)")

        # Convergência multi-TF: se TODOS os TFs concordam → bônus de confiança
        all_same_dir = all(v > 0 for v in velocity_vectors) or all(v < 0 for v in velocity_vectors)
        conf_bonus = 0.2 if all_same_dir and len(velocity_vectors) >= 2 else 0.0

        confidence = min(1.0, abs(signal) * 0.7 + 0.15 + conf_bonus)
        
        # Phase 29: Damping Kinemático em Acelerações Irreais (Prevenção de topo/fundo)
        if abs(avg_velocity) > 0.3 and abs(avg_accel) > 0.2:
            signal *= 0.3  # Corta sinal para evitar compra de pico absoluto
            confidence *= 0.5
            reasons.append("KINEMATIC_DAMPING(extreme velocity/accel climax)")

        return AgentSignal(
            self.name, float(np.clip(signal, -1, 1)),
            float(np.clip(confidence, 0, 1)),
            " | ".join(reasons) if reasons else "VELOCITY_NEUTRAL", self.weight
        )


# ═══════════════════════════════════════════════════════════════
#  AGENT 5: OSCILLATION WAVE — Ondas e Ressonância
# ═══════════════════════════════════════════════════════════════

class OscillationWaveAgent(BaseAgent):
    """
    OSCILAÇÃO — Análise de ondas harmônicas e padrões oscilatórios.
    
    CONCEITO FÍSICO:
    Osciladores harmônicos (mola, pêndulo) possuem frequência natural.
    Quando uma força externa atinge essa frequência → RESSONÂNCIA → 
    amplitude explode.
    
    TRANSPOSIÇÃO PARA MERCADO:
    - O preço oscila em torno de uma "posição de equilíbrio" (VWAP/EMA).
    - A "constante da mola" é a volatilidade (ATR normalizado).
    - Quando a frequência de oscilação do preço se estabiliza (ciclo regular),
      o mercado está em modo OSCILATÓRIO → ideal para mean-reversion.
    - Quando a amplitude das oscilações CRESCE (ressonância) → breakout.
    - "Amortecimento" = mercado perdendo energia → consolidação.
    
    MÉTRICAS PROPRIETÁRIAS:
    1. Oscillation Frequency: Contagem de crossings do VWAP/EMA por período
    2. Amplitude Trend: As oscilações estão crescendo ou diminuindo?
    3. Phase Detection: Estamos no pico, no vale, ou cruzando o equilíbrio?
    4. Resonance Index: Convergência de oscilações multi-TF
    5. Damping Ratio: Taxa de amortecimento → mercado morrendo ou vivo?
    """

    def __init__(self, weight: float = 1.5):
        super().__init__("OscillationWaveAgent", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kw) -> Optional[AgentSignal]:
        signals = []
        reasons = []

        for tf in ["M1", "M5"]:
            candles = snapshot.candles.get(tf)
            if candles is None:
                continue

            closes = np.array(candles["close"], dtype=np.float64)
            highs = np.array(candles["high"], dtype=np.float64)
            lows = np.array(candles["low"], dtype=np.float64)
            indicators = snapshot.indicators

            if len(closes) < 30:
                continue

            # ─── 1. CENTRO DE OSCILAÇÃO (Equilíbrio) ───
            # Usar EMA21 como centro de oscilação
            ema_key = f"{tf}_ema_21"
            ema = indicators.get(ema_key)
            if ema is None or len(ema) < 20:
                continue

            ema_arr = np.array(ema[-len(closes):], dtype=np.float64)
            if len(ema_arr) != len(closes):
                min_len = min(len(ema_arr), len(closes))
                ema_arr = ema_arr[-min_len:]
                closes_local = closes[-min_len:]
            else:
                closes_local = closes

            # Sinal de desvio do equilíbrio
            deviation = closes_local - ema_arr

            # ─── 2. FREQUÊNCIA DE OSCILAÇÃO (Crossings) ───
            # Contar quantas vezes o preço cruza a EMA nos últimos 20 candles
            crossings = 0
            for i in range(1, min(20, len(deviation))):
                if deviation[i] * deviation[i-1] < 0:  # Mudou de sinal
                    crossings += 1

            frequency = crossings / 20.0  # Crossings per candle

            # ─── 3. AMPLITUDE TREND ───
            # Medir peaks e valleys das oscilações
            if len(deviation) >= 10:
                recent_abs = np.abs(deviation[-5:])
                older_abs = np.abs(deviation[-10:-5])
                amplitude_recent = np.mean(recent_abs) if len(recent_abs) > 0 else 0
                amplitude_older = np.mean(older_abs) if len(older_abs) > 0 else 0

                if amplitude_older > 0:
                    amplitude_ratio = amplitude_recent / amplitude_older
                else:
                    amplitude_ratio = 1.0
            else:
                amplitude_ratio = 1.0

            # ─── 4. PHASE DETECTION ───
            # Onde estamos na oscilação atual?
            current_dev = deviation[-1]
            dev_velocity = deviation[-1] - deviation[-2] if len(deviation) >= 2 else 0

            atr = indicators.get(f"{tf}_atr_14")
            current_atr = float(atr[-1]) if atr is not None and len(atr) > 0 else 1.0

            normalized_dev = current_dev / current_atr if current_atr > 0 else 0

            # ─── 5. DAMPING RATIO ───
            # Se amplitude está diminuindo → amortecido → mercado morrendo
            if amplitude_ratio < 0.5:
                damping = "OVER_DAMPED"
            elif amplitude_ratio < 0.8:
                damping = "DAMPED"
            elif amplitude_ratio > 1.5:
                damping = "RESONANCE"
            else:
                damping = "STABLE"

            # ─── CONSTRUIR SINAL ───
            signal = 0.0

            if frequency > 0.3:
                # Alta frequência de oscilação → mercado oscilatório → mean reversion
                if normalized_dev > 1.5:
                    # Preço no extremo superior da oscilação → vai voltar ao centro
                    signal = -0.7
                    reasons.append(f"{tf}:OSCILLATION_PEAK(dev={normalized_dev:.1f}ATR freq={frequency:.2f})")
                elif normalized_dev < -1.5:
                    # Preço no extremo inferior → vai subir
                    signal = 0.7
                    reasons.append(f"{tf}:OSCILLATION_VALLEY(dev={normalized_dev:.1f}ATR freq={frequency:.2f})")
                elif abs(normalized_dev) < 0.3 and abs(dev_velocity) > 0:
                    # Cruzando o equilíbrio com velocidade → continuar na direção
                    signal = np.sign(dev_velocity) * 0.4
                    reasons.append(f"{tf}:OSCILLATION_CROSS({'UP' if dev_velocity > 0 else 'DOWN'})")

            if damping == "RESONANCE":
                # Amplitude crescendo = ressonância = BREAKOUT iminente
                if abs(signal) < 0.3:
                    direction = np.sign(closes[-1] - closes[-5])
                    signal = direction * 0.6
                    reasons.append(f"{tf}:RESONANCE!(amplitude↑ {amplitude_ratio:.1f}x)")
            elif damping == "OVER_DAMPED":
                # Amplitude colapsando → mercado morto
                signal *= 0.3  # Reduzir confiança drasticamente
                reasons.append(f"{tf}:DAMPED(amplitude↓ {amplitude_ratio:.1f}x)")

            signals.append(float(signal))

        if not signals:
            return AgentSignal(self.name, 0.0, 0.0, "OSCILLATION_NO_DATA", self.weight)

        avg = float(np.mean(signals))
        conf = min(1.0, abs(avg) * 0.8 + 0.15)
        return AgentSignal(
            self.name, float(np.clip(avg, -1, 1)),
            float(np.clip(conf, 0, 1)),
            " | ".join(reasons) if reasons else "OSCILLATION_NEUTRAL", self.weight
        )
