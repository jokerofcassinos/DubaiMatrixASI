"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — ESCHATON AGENTS (Phase Ω)                   ║
║     Inteligência Suprema (Nível 20): Singular Spectrum Analysis (SSA)        ║
║     e Teoria de Matrizes Aleatórias (RMT) aplicados à Microestrutura.        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal

class SingularSpectrumAnalysisAgent(BaseAgent):
    """
    [Phase Ω-Eschaton] Singular Spectrum Analysis (SSA).
    Aplica decomposição de valores singulares (SVD) na matriz de trajetória do preço.
    Em vez de usar médias móveis (que têm atraso), o SSA extrai o autovetor principal
    (o verdadeiro "sinal" limpo de ruído HFT) no tempo zero. Se o sinal puro
    vira antes do preço sujo, antecipamos a reversão.
    """
    def __init__(self, weight=4.8):
        super().__init__("SingularSpectrumAnalysis", weight)
        self.window_length = 10 # L

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        # Precisamos de 30 velas para uma matriz de trajetória razoável
        if not candles_m1 or len(candles_m1["close"]) < 30:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)[-30:]
        
        # 1. Embedding (Construção da Matriz de Trajetória X)
        N = len(closes)
        L = self.window_length
        K = N - L + 1
        X = np.column_stack([closes[i:i+L] for i in range(K)])
        
        # 2. SVD (Decomposição de Valores Singulares)
        try:
            U, Sigma, VT = np.linalg.svd(X)
        except np.linalg.LinAlgError:
            return AgentSignal(self.name, 0.0, 0.0, "SVD_CONVERGENCE_ERROR", self.weight)
            
        # 3. Reconstrução do Sinal Principal (1º Autovetor = Tendência Primária Oculta)
        # Aproximação de rank 1
        X_elem = Sigma[0] * np.outer(U[:, 0], VT[0, :])
        
        # Diagonal averaging para reconstruir a série temporal da tendência pura
        pure_trend = np.zeros(N)
        counts = np.zeros(N)
        for i in range(L):
            for j in range(K):
                pure_trend[i+j] += X_elem[i, j]
                counts[i+j] += 1
        pure_trend /= counts
        
        signal = 0.0
        conf = 0.0
        reason = "SSA_NEUTRAL"
        
        # Analisar a derivada da tendência pura nos últimos 3 períodos
        # A derivada do SSA muda de direção ANTES da média móvel
        derivative = np.diff(pure_trend[-4:])
        
        if derivative[-1] > 0 and derivative[-2] < 0:
            # Ponto de inflexão de alta detectado na matemática espectral
            signal = 1.0
            conf = 0.95
            reason = "SSA_BULL_INFLECTION (Clean Spectrum Reversal)"
        elif derivative[-1] < 0 and derivative[-2] > 0:
            # Ponto de inflexão de baixa
            signal = -1.0
            conf = 0.95
            reason = "SSA_BEAR_INFLECTION (Clean Spectrum Reversal)"
        else:
            # Se não há inflexão, seguir a tendência principal purificada
            if derivative[-1] > 0:
                signal = 1.0
                conf = 0.85
                reason = "SSA_BULL_TREND"
            elif derivative[-1] < 0:
                signal = -1.0
                conf = 0.85
                reason = "SSA_BEAR_TREND"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class RandomMatrixTheoryAgent(BaseAgent):
    """
    [Phase Ω-Eschaton] Teoria de Matrizes Aleatórias (RMT).
    Aplica princípios da Física Quântica (Níveis de energia de núcleos pesados)
    para o Order Book. Compara os autovalores empíricos da matriz de correlação 
    do book com a distribuição teórica de Marchenko-Pastur.
    Se um autovalor escapa da distribuição, é sinal INSTITUCIONAL.
    Se todos estão dentro, é ruído de mercado (HFT noise) e operamos mean-reversion.
    """
    def __init__(self, weight=4.2):
        super().__init__("RandomMatrixTheory", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        # Precisamos de profundidade histórica do book. 
        # Como não armazenamos o book completo ao longo do tempo aqui, 
        # faremos uma aproximação usando a variação de volume/preço nas últimas 15 velas.
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 20:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)
            
        c = np.array(candles_m1["close"], dtype=np.float64)[-20:]
        h = np.array(candles_m1["high"], dtype=np.float64)[-20:]
        l = np.array(candles_m1["low"], dtype=np.float64)[-20:]
        v = np.array(candles_m1["tick_volume"], dtype=np.float64)[-20:]
        
        # Matriz de observações (4 variáveis, 19 observações de retorno)
        ret_c = np.diff(np.log(c))
        ret_h = np.diff(np.log(h))
        ret_l = np.diff(np.log(l))
        ret_v = np.diff(np.log(v + 1e-6))
        
        M = np.vstack([ret_c, ret_h, ret_l, ret_v])
        
        # Matriz de Correlação Empírica
        try:
            corr_matrix = np.corrcoef(M)
            eigenvalues, _ = np.linalg.eigh(corr_matrix)
        except Exception:
            return AgentSignal(self.name, 0.0, 0.0, "MATH_ERROR", self.weight)
            
        max_eigenvalue = np.max(eigenvalues)
        
        signal = 0.0
        conf = 0.0
        reason = "RMT_NOISE"
        
        # O limite teórico de Marchenko-Pastur para este ratio é em torno de 1.8 a 2.5
        # Se max_eigenvalue > 3.0, o sistema está sendo governado por um "Fator Comum" massivo
        # ou seja, Manipulação Institucional Centralizada.
        if max_eigenvalue > 2.8:
            # Existe uma força externa quebrando a aleatoriedade natural do mercado.
            # O mercado está "ensaiado" (Scripted). Acompanhamos a inércia primária.
            trend = c[-1] - c[-5]
            if trend != 0:
                signal = np.sign(trend)
                conf = 0.95
                reason = f"RMT_INSTITUTIONAL_COMMON_FACTOR (Eigenval={max_eigenvalue:.2f})"
        else:
            # O mercado está em estado de passeios aleatórios estritos.
            # Ideal para "Fading" (Reversão à Média).
            vel = c[-1] - c[-2]
            if vel != 0:
                signal = -np.sign(vel)
                conf = 0.85
                reason = f"RMT_RANDOM_NOISE_FADING (Eigenval={max_eigenvalue:.2f})"
                
        return AgentSignal(self.name, signal, conf, reason, self.weight)
