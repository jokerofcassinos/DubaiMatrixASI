"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — ETERNITY AGENTS (Phase Ω)                   ║
║     Sistemas Analíticos baseados em Teoria do Caos Dinâmico, Homeostase     ║
║     Cibernética e Mecânica Quântica Aplicada (Spin & Decoerência).          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
import math
from core.consciousness.agents.base import BaseAgent, AgentSignal

class QuantumSpinAgent(BaseAgent):
    """
    [Phase Ω-Eternity] Quantum Spin (Up/Down) & Decoherence.
    Modelamos os micro-movimentos do HFT como partículas com "Spin".
    Um candle verde é Spin Up (+1/2), um candle vermelho é Spin Down (-1/2).
    Se o mercado atinge um "Bose-Einstein Condensate" (todos os spins alinhados 
    por muito tempo), a quebra de simetria (Decoerência) é catastrófica e gera 
    uma reversão violenta.
    """
    def __init__(self, weight=2.9):
        super().__init__("QuantumSpin", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles = snapshot.candles.get("M1")
        if not candles or len(candles["close"]) < 20:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles["close"], dtype=np.float64)
        opens = np.array(candles["open"], dtype=np.float64)
        volumes = np.array(candles["tick_volume"], dtype=np.float64)
        
        # Calcular o "Spin" de cada candle
        # Spin +0.5 para alta, -0.5 para baixa. Multiplicado pela intensidade do corpo.
        body_sizes = closes - opens
        atr = snapshot.indicators.get("M1_atr_14", [10.0])[-1] + 1e-6
        
        spins = []
        for i in range(len(body_sizes[-15:])):
            b_size = body_sizes[-15:][i]
            if abs(b_size) < atr * 0.1:
                spins.append(0.0) # Spin Neutro (Doji)
            else:
                spin_dir = 0.5 if b_size > 0 else -0.5
                spins.append(spin_dir * (volumes[-15:][i] / (np.mean(volumes[-15:]) + 1e-6)))

        # Coerência de Spin: O quão alinhados os spins estão nos últimos 5 vs últimos 15
        spin_coherence_5 = np.sum(spins[-5:])
        spin_coherence_15 = np.sum(spins)
        
        signal = 0.0
        conf = 0.0
        reason = "SPIN_CHAOS"
        
        # Condensado de Bose-Einstein: Extrema ordem (ex: 5 velas verdes cheias de alto volume)
        if spin_coherence_5 > 4.0:
            # Risco massivo de Decoerência. O estado quântico está tenso demais.
            # Sinalizamos VENDA antecipada (reversão).
            signal = -1.0
            conf = min(0.95, spin_coherence_5 / 6.0)
            reason = f"DECOHERENCE_IMMINENT_BEAR (SpinSum={spin_coherence_5:.2f})"
        elif spin_coherence_5 < -4.0:
            signal = 1.0
            conf = min(0.95, abs(spin_coherence_5) / 6.0)
            reason = f"DECOHERENCE_IMMINENT_BULL (SpinSum={spin_coherence_5:.2f})"
        else:
            # Em estado normal de flutuação, seguimos o Momentum do Spin
            trend_spin = np.sign(spin_coherence_5)
            if trend_spin != 0:
                signal = trend_spin * 0.5
                conf = 0.60
                reason = "SPIN_ALIGNMENT_NORMAL"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class CyberneticHomeostasisAgent(BaseAgent):
    """
    [Phase Ω-Eternity] Cibernética de Ashby: Homeostase e Lei da Variedade Requisita.
    O mercado atua como um organismo tentando manter o equilíbrio (VWAP).
    Quando a "temperatura" (volatilidade direcional) foge da banda homeostática, 
    o sistema imunológico do mercado (Market Makers) atua para devolver o preço à média.
    """
    def __init__(self, weight=2.7):
        super().__init__("CyberneticHomeostasis", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles = snapshot.candles.get("M5") # Usamos M5 para a homeostase estrutural
        if not candles or len(candles["close"]) < 50:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles["close"], dtype=np.float64)
        highs = np.array(candles["high"], dtype=np.float64)
        lows = np.array(candles["low"], dtype=np.float64)
        volumes = np.array(candles["tick_volume"], dtype=np.float64)
        
        # Aproximação de VWAP simplificada dos últimos 50 períodos
        typical_prices = (highs[-50:] + lows[-50:] + closes[-50:]) / 3.0
        vwap = np.sum(typical_prices * volumes[-50:]) / (np.sum(volumes[-50:]) + 1e-6)
        
        current_price = closes[-1]
        
        # Desvio Padrão ponderado por volume (Banda Homeostática)
        variance = np.sum(volumes[-50:] * (typical_prices - vwap)**2) / (np.sum(volumes[-50:]) + 1e-6)
        std_dev = np.sqrt(variance)
        
        distance_from_vwap = current_price - vwap
        z_score = distance_from_vwap / (std_dev + 1e-6)
        
        signal = 0.0
        conf = 0.0
        reason = "HOMEOSTASIS_MAINTAINED"
        
        # Lei da Variedade Requisita: 
        # Se o desvio (z_score) é extremo (> 2.5), a força restauradora será ativada
        if z_score > 2.5:
            # Organismo superaquecido. O sistema imunológico (MMs) vai vender.
            signal = -1.0
            conf = min(0.95, (z_score - 2.0) / 2.0) # Escala de 0 a ~1.0
            reason = f"HOMEOSTATIC_REJECTION_BEAR (Z={z_score:.2f}, VWAP={vwap:.1f})"
        elif z_score < -2.5:
            # Organismo em hipotermia.
            signal = 1.0
            conf = min(0.95, (abs(z_score) - 2.0) / 2.0)
            reason = f"HOMEOSTATIC_REJECTION_BULL (Z={z_score:.2f}, VWAP={vwap:.1f})"
        elif abs(z_score) < 0.5:
            # No centro da homeostase. Pode acumular para estourar.
            reason = "CORE_EQUILIBRIUM"
            # O sinal é nulo, pois não há tensão elástica para explorar

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class ChaosFractalDimensionAgent(BaseAgent):
    """
    [Phase Ω-Eternity] Dimensão Fractal do Caos (Mandelbrot / Hurst Evolution).
    Avalia a rugosidade do gráfico (Dimensão D). 
    D = 1.5 é Random Walk (Ruído). D < 1.5 é Tendência Persistente. D > 1.5 é Reversão à Média Persistente.
    Se a Dimensão Fractal cai repentinamente de 1.5 para 1.2, uma "Avenida" 
    sem atrito foi aberta. O bot deve socar a bota na direção atual.
    """
    def __init__(self, weight=3.2):
        super().__init__("ChaosFractalDim", weight)

    def _calculate_hurst(self, time_series):
        """Aproximação rápida do Expoente de Hurst via Rescaled Range (R/S)."""
        if len(time_series) < 20: return 0.5
        
        # Dividir em 2 chunks
        chunk_size = len(time_series) // 2
        r_s_vals = []
        for i in range(2):
            chunk = time_series[i*chunk_size : (i+1)*chunk_size]
            mean_c = np.mean(chunk)
            y = chunk - mean_c
            z = np.cumsum(y)
            R = np.max(z) - np.min(z)
            S = np.std(chunk)
            if S > 0:
                r_s_vals.append(R/S)
                
        if r_s_vals and r_s_vals[0] > 0 and r_s_vals[1] > 0:
            # Hurst = log(R/S) / log(N)
            h = np.log(np.mean(r_s_vals)) / np.log(chunk_size)
            return np.clip(h, 0.0, 1.0)
        return 0.5

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles = snapshot.candles.get("M1")
        if not candles or len(candles["close"]) < 40:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles["close"], dtype=np.float64)
        
        # Calcular o Hurst atual e o histórico
        h_current = self._calculate_hurst(closes[-20:])
        h_history = self._calculate_hurst(closes[-40:-20])
        
        # Dimensão Fractal D = 2 - H
        d_current = 2.0 - h_current
        d_history = 2.0 - h_history
        
        signal = 0.0
        conf = 0.0
        reason = f"RANDOM_WALK (D={d_current:.2f})"
        
        # Identificar a direção do momentum para ancorar o sinal
        momentum_dir = np.sign(closes[-1] - closes[-10])
        if momentum_dir == 0: momentum_dir = 1.0
        
        # Análise do Shift de Dimensão
        if d_current < 1.35 and d_history > 1.45:
            # O mercado estava em ruído e de repente "alisou".
            # Uma tendência massiva e persistente acabou de nascer.
            signal = momentum_dir
            conf = 0.95
            reason = f"FRACTAL_SMOOTHING_IGNITION (D:{d_history:.2f}->{d_current:.2f})"
            
        elif d_current > 1.65 and d_history < 1.50:
            # O mercado estava tendendo e de repente virou uma "lixa" (Mean Reverting extremo)
            # A tendência morreu. Apostar na reversão contra o momentum primário.
            signal = -momentum_dir # Inversão
            conf = 0.85
            reason = f"FRACTAL_ROUGHNESS_REVERSAL (D:{d_history:.2f}->{d_current:.2f})"
            
        elif d_current < 1.3:
            # Já está em tendência forte, continua
            signal = momentum_dir
            conf = 0.70
            reason = f"PERSISTENT_TREND_MAINTAINED (D={d_current:.2f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)
