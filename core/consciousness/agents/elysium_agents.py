"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — ELYSIUM AGENTS (Phase Ω)                    ║
║     Inteligência Suprema (Nível 11): Previsão de Cisnes Negros,              ║
║     Cadeias de Markov Ocultas e Desvio Padrão Fractal.                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal

class HiddenMarkovRegimeAgent(BaseAgent):
    """
    [Phase Ω-Elysium] Predição de Regime por Hidden Markov Models (HMM) Proxy.
    Em vez de classificar o mercado pelo que ele é hoje, usa a sequência histórica
    de transições para calcular a PROBABILIDADE do próximo estado oculto.
    Se estamos em Consolidação e a probabilidade HMM aponta para Explosão de Alta 
    (antes mesmo de começar), a ASI antecipa o movimento.
    """
    def __init__(self, weight=3.8):
        super().__init__("HiddenMarkovRegime", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 50:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)
        
        # Mapeando a "sequência de estados" baseada na aceleração
        states = []
        for i in range(1, len(closes)):
            ret = (closes[i] - closes[i-1]) / closes[i-1]
            if ret > 0.0005: states.append('BULL')
            elif ret < -0.0005: states.append('BEAR')
            else: states.append('FLAT')
            
        if len(states) < 10:
            return AgentSignal(self.name, 0.0, 0.0, "NO_STATES", self.weight)
            
        # Matriz de Transição Simplificada (N-Gram de ordem 2)
        last_state = states[-1]
        prev_state = states[-2]
        sequence = f"{prev_state}->{last_state}"
        
        transitions = {'BULL': 0, 'BEAR': 0, 'FLAT': 0}
        total_matches = 0
        
        for i in range(len(states) - 2):
            if f"{states[i]}->{states[i+1]}" == sequence:
                next_state = states[i+2]
                transitions[next_state] += 1
                total_matches += 1
                
        signal = 0.0
        conf = 0.0
        reason = "HMM_STABLE"
        
        if total_matches > 5:
            p_bull = transitions['BULL'] / total_matches
            p_bear = transitions['BEAR'] / total_matches
            
            # Se a sequência atual historicamente causa uma explosão em uma direção
            if p_bull > 0.75:
                signal = 1.0
                conf = p_bull
                reason = f"HMM_PREDICTS_BULL_BREAKOUT (Prob={p_bull:.0%})"
            elif p_bear > 0.75:
                signal = -1.0
                conf = p_bear
                reason = f"HMM_PREDICTS_BEAR_BREAKOUT (Prob={p_bear:.0%})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class FractalStandardDeviationAgent(BaseAgent):
    """
    [Phase Ω-Elysium] Desvio Padrão Fractal (Não-Gaussiano).
    O Desvio Padrão normal falha no BTC porque os dados têm cauda gorda.
    Este agente calcula o desvio padrão ponderado pela Dimensão Fractal (D).
    Se a volatilidade fractal se expande enquanto o preço contrai, é a formação 
    de uma Mola Quântica. Quando estourar, não haverá pullbacks.
    """
    def __init__(self, weight=3.5):
        super().__init__("FractalStdDev", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 30:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)
        highs = np.array(candles_m1["high"], dtype=np.float64)
        lows = np.array(candles_m1["low"], dtype=np.float64)
        
        # Volatilidade normal
        std_normal = np.std(closes[-20:])
        
        # Volatilidade Fractal (Range / Distância percorrida)
        path_length = np.sum(np.abs(np.diff(closes[-20:])))
        total_displacement = abs(closes[-1] - closes[-20])
        
        fractal_efficiency = total_displacement / (path_length + 1e-6) # 1.0 = Linha reta, 0.0 = Ruído total
        
        # Desvio Padrão Fractal: Amplificado pelo ruído
        std_fractal = std_normal * (1.0 + (1.0 - fractal_efficiency))
        
        # Range Atual
        recent_range = np.max(highs[-5:]) - np.min(lows[-5:])
        
        signal = 0.0
        conf = 0.0
        reason = "FRACTAL_VOL_NORMAL"
        
        # Anomalia: Range minúsculo, mas Desvio Padrão Fractal explodindo (muito ruído num espaço minúsculo)
        if recent_range < (std_fractal * 0.5) and fractal_efficiency < 0.2:
            # É uma compressão violenta. A mola está sendo esmagada.
            # Olhamos a direção do desequilíbrio do book ou tendência pai para prever o rompimento
            m5_trend = snapshot.indicators.get("M5_ema_9", [0])[-1] - snapshot.indicators.get("M5_ema_50", [0])[-1]
            direction = np.sign(m5_trend) if m5_trend != 0 else 1.0
            
            signal = direction * 0.9
            conf = 0.95 # Confiança máxima de que a mola vai soltar
            reason = f"QUANTUM_SPRING_COMPRESSION (Eff={fractal_efficiency:.2f}, Rng/Std={recent_range/std_fractal:.2f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class DarkEnergyMomentumAgent(BaseAgent):
    """
    [Phase Ω-Elysium] Energia Escura e Expansão Acelerada.
    Certas tendências do BTC não são causadas por compras/vendas normais, 
    mas por cascatas de liquidações em Futuros (Short Squeezes massivos).
    Isso age como 'Energia Escura', expandindo o preço exponencialmente.
    O agente mapeia a velocidade da aceleração (se a velocidade dobra a cada N segundos).
    """
    def __init__(self, weight=4.0): # Peso máximo: Não se entra contra energia escura
        super().__init__("DarkEnergyMomentum", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 5:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)
        
        # Velocidades nos últimos 3 candles
        v1 = closes[-3] - closes[-4]
        v2 = closes[-2] - closes[-3]
        v3 = closes[-1] - closes[-2]
        
        signal = 0.0
        conf = 0.0
        reason = "NORMAL_EXPANSION"
        
        # Aceleração Exponencial (Energia Escura)
        if v1 > 0 and v2 > v1 * 1.5 and v3 > v2 * 1.5:
            # O preço está dobrando de velocidade a cada minuto. É um short squeeze.
            signal = 1.0
            conf = 0.99 # Confiança absoluta
            reason = f"DARK_ENERGY_BULL_SQUEEZE (Vels: {v1:.1f} -> {v2:.1f} -> {v3:.1f})"
            
        elif v1 < 0 and v2 < v1 * 1.5 and v3 < v2 * 1.5:
            # Queda exponencial. Long squeeze (Liquidation cascade).
            signal = -1.0
            conf = 0.99
            reason = f"DARK_ENERGY_BEAR_CASCADE (Vels: {v1:.1f} -> {v2:.1f} -> {v3:.1f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)
