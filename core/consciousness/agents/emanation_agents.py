"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — EMANATION AGENTS (Phase Ω)                  ║
║     Inteligência Suprema (Nível 17): Geometria Não-Euclidiana, Teoria das  ║
║     Cordas Aplicada e Divergência de Shannon-Kullback-Leibler.              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal

class NonEuclideanGeometryAgent(BaseAgent):
    """
    [Phase Ω-Emanation] Geometria Hiperbólica (Disco de Poincaré).
    Em momentos de extrema volatilidade, o mercado não opera em um espaço
    Euclidiano plano. A distância entre os preços "encolhe" na percepção dos
    algoritmos HFT (o spread alarga e o book fica rarefeito).
    Este agente mede a distorção do espaço-tempo do Order Book.
    """
    def __init__(self, weight=4.5):
        super().__init__("NonEuclideanGeometry", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 20:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)
        atr = snapshot.indicators.get("M1_atr_14", [50.0])[-1]
        
        # Distância Euclidiana Clássica (Preço atual - Preço de 10 minutos atrás)
        euclidean_distance = abs(closes[-1] - closes[-10])
        
        # Distância Hiperbólica (Soma dos log-retornos absolutos)
        # O espaço hiperbólico penaliza grandes saltos em pequenos intervalos
        log_returns = np.abs(np.diff(np.log(closes[-11:])))
        hyperbolic_distance = np.sum(log_returns) * closes[-1]
        
        signal = 0.0
        conf = 0.0
        reason = "FLAT_SPACE"
        
        # Se a distância hiperbólica é massivamente maior que a euclidiana,
        # o espaço está "curvado" (muita volatilidade intra-vela sem sair do lugar).
        # É uma panela de pressão prestes a explodir.
        if hyperbolic_distance > (euclidean_distance * 3.0) and euclidean_distance < (atr * 0.5):
            # O espaço está distorcido. Procuramos o vetor de escape observando o macro.
            m5_trend = snapshot.indicators.get("M5_ema_9", [0])[-1] - snapshot.indicators.get("M5_ema_50", [0])[-1]
            direction = np.sign(m5_trend) if m5_trend != 0 else 1.0
            
            signal = direction * 1.0
            conf = 0.96
            reason = f"HYPERBOLIC_WARP_DETECTED (Hyp/Euc Ratio={hyperbolic_distance/(euclidean_distance+1e-6):.1f})"
            
        return AgentSignal(self.name, signal, conf, reason, self.weight)


class ShannonKLDivergenceAgent(BaseAgent):
    """
    [Phase Ω-Emanation] Divergência de Kullback-Leibler (Teoria da Informação).
    Mede como a distribuição de probabilidade do volume atual diverge da
    distribuição histórica. Se o mercado muda sua "assinatura informacional"
    abruptamente, uma mudança violenta de regime direcional é iminente.
    """
    def __init__(self, weight=4.2):
        super().__init__("ShannonKLDivergence", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["tick_volume"]) < 60:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        volumes = np.array(candles_m1["tick_volume"], dtype=np.float64)
        
        # P (Distribuição Histórica - 50 velas antigas)
        hist_vols = volumes[-60:-10]
        p_hist, _ = np.histogram(hist_vols, bins=10, density=True)
        p_hist = p_hist + 1e-10 # Evitar divisão por zero
        p_hist /= np.sum(p_hist)
        
        # Q (Distribuição Recente - 10 velas)
        recent_vols = volumes[-10:]
        q_recent, _ = np.histogram(recent_vols, bins=10, density=True)
        q_recent = q_recent + 1e-10
        q_recent /= np.sum(q_recent)
        
        # Divergência KL (P || Q)
        kl_divergence = np.sum(p_hist * np.log(p_hist / q_recent))
        
        signal = 0.0
        conf = 0.0
        reason = "INFO_SYMMETRY"
        
        # Se a divergência de informação for extrema (Mudança de Paradigma)
        if kl_divergence > 1.5:
            # O mercado está absorvendo nova informação crítica.
            # O preço vai seguir a última inércia forte.
            closes = np.array(candles_m1["close"], dtype=np.float64)
            momentum = closes[-1] - closes[-3]
            if momentum != 0:
                signal = np.sign(momentum)
                conf = min(0.95, kl_divergence * 0.4)
                reason = f"KL_PARADIGM_SHIFT (Divergence={kl_divergence:.2f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class StringTheoryVibrationAgent(BaseAgent):
    """
    [Phase Ω-Emanation] Teoria das Cordas em N-Dimensões Móveis.
    Trata as EMAs (9, 21, 50, 200) como "cordas" vibrando no espaço de preços.
    Se as cordas entram em "Ressonância Harmônica" (todas alinhadas e se afastando),
    o mercado atingiu um estado de energia perfeito. Se as cordas dão um "Nó"
    (todas se cruzam num único ponto), a singularidade vai ejetar o preço.
    """
    def __init__(self, weight=4.0):
        super().__init__("StringTheoryVibration", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        inds = snapshot.indicators
        if not all(k in inds for k in ["M1_ema_9", "M1_ema_21", "M1_ema_50", "M1_ema_200"]):
            return AgentSignal(self.name, 0.0, 0.0, "NO_STRINGS", self.weight)
            
        ema9 = inds["M1_ema_9"][-1]
        ema21 = inds["M1_ema_21"][-1]
        ema50 = inds["M1_ema_50"][-1]
        ema200 = inds["M1_ema_200"][-1]
        
        strings = np.array([ema9, ema21, ema50, ema200])
        
        # Calcular o "Nó" (Desvio padrão entre as cordas)
        string_variance = np.std(strings)
        atr = inds.get("M1_atr_14", [20.0])[-1]
        
        signal = 0.0
        conf = 0.0
        reason = "STRINGS_NORMAL"
        
        # NÓ QUÂNTICO (Singularidade): Todas as médias estão coladas umas nas outras
        if string_variance < (atr * 0.15):
            # Expansão violenta é iminente. Para qual lado? O lado em que o preço romper o nó.
            current_price = snapshot.price
            mean_string_price = np.mean(strings)
            
            if current_price > mean_string_price + (atr * 0.2):
                signal = 1.0
                conf = 0.90
                reason = "STRING_KNOT_BULL_EJECTION (Singularity Broken Up)"
            elif current_price < mean_string_price - (atr * 0.2):
                signal = -1.0
                conf = 0.90
                reason = "STRING_KNOT_BEAR_EJECTION (Singularity Broken Down)"
                
        # HARMONIA PERFEITA: Cordas perfeitamente alinhadas e esticadas
        elif ema9 > ema21 > ema50 > ema200 and (ema9 - ema21) > atr * 0.5:
            signal = 1.0
            conf = 0.85
            reason = "HARMONIC_STRING_RESONANCE (Bullish Expansion)"
        elif ema9 < ema21 < ema50 < ema200 and (ema21 - ema9) > atr * 0.5:
            signal = -1.0
            conf = 0.85
            reason = "HARMONIC_STRING_RESONANCE (Bearish Expansion)"

        return AgentSignal(self.name, signal, conf, reason, self.weight)
