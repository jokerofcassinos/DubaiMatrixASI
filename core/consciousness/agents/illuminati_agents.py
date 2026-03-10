"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — ILLUMINATI AGENTS (Phase Ω)                 ║
║     Inteligência Suprema (Nível 12): Relatividade Temporal, Análise         ║
║     Espectral Avançada (Fourier) e Atração de Vácuo.                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal

class ChronosDilationAgent(BaseAgent):
    """
    [Phase Ω-Illuminati] Dilatação Relativística do Tempo.
    Mede a compressão do tempo entre ticks/velas. Se o mercado, que normalmente
    leva 1 minuto para mover 10 pontos, subitamente move 10 pontos em 2 segundos,
    o 'tempo' do mercado dilatou. Isso precede ondas de choque HFT (High-Frequency).
    """
    def __init__(self, weight=3.9):
        super().__init__("ChronosDilation", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        tick_velocity = snapshot.metadata.get("tick_velocity", 0.0)
        
        signal = 0.0
        conf = 0.0
        reason = "NORMAL_TIME_FLOW"
        
        if tick_velocity > 40.0:
            # Tempo comprimido: muita ação em milissegundos
            # Para determinar a direção, olhamos o delta de preço nos últimos ticks
            if snapshot.tick and snapshot.book:
                # Usamos a relação Bid/Ask momentânea
                spread = snapshot.tick['ask'] - snapshot.tick['bid']
                if spread < snapshot.symbol_info.get("point", 1.0) * 10:
                    # Spread fechando rápido com alta velocidade = Ignição de Momentum
                    trend = snapshot.indicators.get("M1_ema_9", [0])[-1] - snapshot.indicators.get("M1_ema_21", [0])[-1]
                    direction = np.sign(trend) if trend != 0 else 1.0
                    
                    signal = float(direction)
                    conf = 0.90
                    reason = f"TIME_DILATION_SHOCKWAVE (Vel={tick_velocity:.1f} Ticks/s)"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class FourierSpectralAgent(BaseAgent):
    """
    [Phase Ω-Illuminati] Transformada de Fourier Rápida (FFT).
    Decompõe o gráfico de preço em suas ondas senoidais constituintes (Espectro).
    Se a frequência dominante repentinamente mudar de "Ondas Longas" para "Micro-Ondas",
    significa que os algoritmos de Market Making mudaram a marcha, sinalizando
    o fim de uma consolidação e o início de um Breakout Caótico.
    """
    def __init__(self, weight=3.4):
        super().__init__("FourierSpectral", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 64: # Potência de 2 para FFT
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)[-64:]
        
        # Remove a tendência (detrend) para focar apenas nas oscilações (ciclos)
        detrended = closes - np.polyval(np.polyfit(np.arange(64), closes, 1), np.arange(64))
        
        # FFT
        fft_vals = np.fft.fft(detrended)
        power_spectrum = np.abs(fft_vals)**2
        
        # Ignorar o componente DC (índice 0) e pegar a metade simétrica
        freqs = np.fft.fftfreq(64)
        pos_freqs = freqs[1:32]
        pos_power = power_spectrum[1:32]
        
        dominant_freq_idx = np.argmax(pos_power)
        dominant_freq = pos_freqs[dominant_freq_idx]
        
        # Frequência normalizada
        signal = 0.0
        conf = 0.0
        reason = "HARMONIC_BALANCE"
        
        # Frequência alta = ciclos curtíssimos = Choppy/Ruído
        # Frequência baixa = ciclos longos = Tendência Direcional
        if dominant_freq < 0.05:
            # O mercado está sendo dominado por uma força massiva e lenta (Baleias).
            # É seguro seguir a tendência primária.
            trend = closes[-1] - closes[0]
            direction = np.sign(trend)
            signal = float(direction)
            conf = 0.85
            reason = f"LOW_FREQ_DOMINANCE (Whale Trend, Freq={dominant_freq:.3f})"
            
        elif dominant_freq > 0.25:
            # O mercado está vibrando rápido demais (HFTs brigando).
            # Altíssimo risco de reversão de ruído.
            trend = closes[-1] - closes[-5]
            signal = -np.sign(trend) # Apostar contra o micro-momentum
            conf = 0.80
            reason = f"HIGH_FREQ_CHAOS_REVERSAL (HFT War, Freq={dominant_freq:.3f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class LiquidityVoidMagnetAgent(BaseAgent):
    """
    [Phase Ω-Illuminati] Atração Eletromagnética de Vácuos de Liquidez.
    Quando ocorre um deslocamento de preço muito agressivo sem "overlap" de velas 
    (Fair Value Gaps gigantes), cria-se um Vácuo de Liquidez.
    Esses vácuos atuam como super-ímãs. Se o preço demonstra *fraqueza* na direção 
    da tendência, este agente sinaliza a atração magnética inevitável de volta ao vácuo.
    """
    def __init__(self, weight=3.6):
        super().__init__("LiquidityVoidMagnet", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m5 = snapshot.candles.get("M5")
        if not candles_m5 or len(candles_m5["close"]) < 20:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        highs = np.array(candles_m5["high"], dtype=np.float64)
        lows = np.array(candles_m5["low"], dtype=np.float64)
        closes = np.array(candles_m5["close"], dtype=np.float64)
        
        atr = snapshot.indicators.get("M5_atr_14", [20.0])[-1]
        current_price = closes[-1]
        
        signal = 0.0
        conf = 0.0
        reason = "NO_VOID_DETECTED"
        
        # Procurar o vácuo (FVG) mais proeminente nos últimos 15 candles
        # Bullish FVG: Low do candle 3 > High do candle 1
        # Bearish FVG: High do candle 3 < Low do candle 1
        
        largest_void = 0
        void_target = 0
        void_type = 0 # 1 = Bullish (abaixo do preço), -1 = Bearish (acima do preço)
        
        for i in range(len(closes) - 15, len(closes) - 2):
            # Bullish Void (Gap de Alta)
            if lows[i+2] > highs[i]:
                gap = lows[i+2] - highs[i]
                if gap > largest_void and current_price > lows[i+2]: # O preço está acima, será sugado para baixo
                    largest_void = gap
                    void_target = (lows[i+2] + highs[i]) / 2.0
                    void_type = -1 # Sinal de Venda para cobrir o gap
                    
            # Bearish Void (Gap de Baixa)
            elif highs[i+2] < lows[i]:
                gap = lows[i] - highs[i+2]
                if gap > largest_void and current_price < highs[i+2]: # O preço está abaixo, será sugado para cima
                    largest_void = gap
                    void_target = (lows[i] + highs[i+2]) / 2.0
                    void_type = 1 # Sinal de Compra para cobrir o gap
                    
        if largest_void > atr * 0.8:
            # Encontramos um super ímã
            dist_to_void = abs(current_price - void_target)
            if dist_to_void < atr * 2.0: # Está perto o suficiente para sentir a atração
                # Verificar fraqueza momentânea na direção oposta ao ímã
                momentum_m1 = closes[-1] - closes[-3]
                
                # Se quer subir pra cobrir o gap, e a queda de curto prazo perdeu força
                if void_type == 1 and momentum_m1 > -atr * 0.1:
                    signal = 1.0
                    conf = 0.90
                    reason = f"MAGNETIC_VOID_PULL_UP (Target={void_target:.0f}, Gap={largest_void:.1f})"
                
                # Se quer descer pra cobrir o gap, e a alta perdeu força
                elif void_type == -1 and momentum_m1 < atr * 0.1:
                    signal = -1.0
                    conf = 0.90
                    reason = f"MAGNETIC_VOID_PULL_DOWN (Target={void_target:.0f}, Gap={largest_void:.1f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)
