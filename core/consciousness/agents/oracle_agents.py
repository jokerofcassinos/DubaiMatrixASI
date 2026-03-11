"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — ORACLE AGENTS (Phase Ω)                     ║
║     Inteligência Suprema (Nível 22): Processos de Decisão de Markov (MDP)    ║
║     e Colapso da Função de Onda de Schrödinger.                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal

class MarkovDecisionProcessAgent(BaseAgent):
    """
    [Phase Ω-Oracle] Processo de Decisão de Markov (MDP).
    Modela o mercado não como uma série contínua, mas como transições discretas de estado.
    Estados: {Bull_Strong, Bull_Weak, Bear_Strong, Bear_Weak, Ranging}.
    Ele calcula a Matriz de Transição empírica dos últimos 60 minutos e prevê
    o estado mais provável do próximo minuto.
    """
    def __init__(self, weight=4.4):
        super().__init__("MarkovDecisionProcess", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 60:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)
        opens = np.array(candles_m1["open"], dtype=np.float64)
        atr = snapshot.indicators.get("M1_atr_14", [20.0])[-1]
        
        # 1. Discretizar os estados
        states = []
        for i in range(len(closes)):
            delta = closes[i] - opens[i]
            if delta > atr * 0.5:
                states.append(0) # Bull Strong
            elif delta > 0:
                states.append(1) # Bull Weak
            elif delta < -atr * 0.5:
                states.append(2) # Bear Strong
            elif delta < 0:
                states.append(3) # Bear Weak
            else:
                states.append(4) # Ranging
                
        # 2. Construir Matriz de Transição Empírica (5x5)
        transitions = np.zeros((5, 5))
        for i in range(len(states)-1):
            current_state = states[i]
            next_state = states[i+1]
            transitions[current_state, next_state] += 1
            
        # Normalizar as linhas para obter probabilidades
        row_sums = transitions.sum(axis=1)
        for i in range(5):
            if row_sums[i] > 0:
                transitions[i, :] /= row_sums[i]
            else:
                transitions[i, :] = 0.2 # Distribuição uniforme se não há dados
                
        # 3. Prever o próximo estado com base no estado ATUAL
        current_state = states[-1]
        probs = transitions[current_state, :]
        
        predicted_state = np.argmax(probs)
        max_prob = probs[predicted_state]
        
        signal = 0.0
        conf = 0.0
        reason = "MDP_UNCERTAIN"
        
        if max_prob > 0.45: # Probabilidade significativa de transição
            if predicted_state == 0:
                signal = 1.0
                conf = max_prob
                reason = f"MDP_PREDICT_BULL_STRONG (Prob={max_prob:.0%})"
            elif predicted_state == 2:
                signal = -1.0
                conf = max_prob
                reason = f"MDP_PREDICT_BEAR_STRONG (Prob={max_prob:.0%})"
            elif predicted_state == 1:
                signal = 0.5
                conf = max_prob * 0.8
                reason = f"MDP_PREDICT_BULL_WEAK (Prob={max_prob:.0%})"
            elif predicted_state == 3:
                signal = -0.5
                conf = max_prob * 0.8
                reason = f"MDP_PREDICT_BEAR_WEAK (Prob={max_prob:.0%})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class SchrodingerWaveAgent(BaseAgent):
    """
    [Phase Ω-Oracle] Equação de Schrödinger (Função de Onda de Preço).
    A 'Partícula' (Preço) não está em um local definido, mas em uma nuvem de probabilidades.
    A Volatilidade é a 'Energia Cinética' e os Order Blocks/Liquidez são o 'Potencial (V)'.
    O Agente calcula a probabilidade do preço tunelar a resistência ou reverter,
    baseado na assimetria da função de onda (Amplitude da onda na Venda vs Compra).
    """
    def __init__(self, weight=4.7):
        super().__init__("SchrodingerWave", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 20:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)
        highs = np.array(candles_m1["high"], dtype=np.float64)
        lows = np.array(candles_m1["low"], dtype=np.float64)
        
        # O Potencial V(x) é dado pelas extremidades (bandas de resistência)
        local_max = np.max(highs[-20:-1])
        local_min = np.min(lows[-20:-1])
        current_price = closes[-1]
        
        # Energia cinética (E) = variação recente de preço
        kinetic_e = abs(closes[-1] - closes[-5])
        
        # Barreira de Potencial (V)
        dist_up = local_max - current_price
        dist_down = current_price - local_min
        
        # Se estamos muito perto de uma barreira
        atr = snapshot.indicators.get("M1_atr_14", [20.0])[-1]
        
        signal = 0.0
        conf = 0.0
        reason = "WAVE_FUNCTION_STABLE"
        
        if dist_up < atr * 0.5:
            # Barreira de Alta. A Energia Cinética é maior que o Potencial?
            if kinetic_e > atr * 1.5:
                # Tunelamento Quântico. Vai romper.
                signal = 1.0
                conf = 0.95
                reason = f"SCHRODINGER_TUNNEL_UP (Kinetic={kinetic_e:.1f} > Barrier)"
            else:
                # Reflexão da Onda (Reversão)
                signal = -1.0
                conf = 0.88
                reason = f"SCHRODINGER_WAVE_REFLECTION_DOWN (Kinetic={kinetic_e:.1f} < Barrier)"
                
        elif dist_down < atr * 0.5:
            if kinetic_e > atr * 1.5:
                signal = -1.0
                conf = 0.95
                reason = f"SCHRODINGER_TUNNEL_DOWN (Kinetic={kinetic_e:.1f} > Barrier)"
            else:
                signal = 1.0
                conf = 0.88
                reason = f"SCHRODINGER_WAVE_REFLECTION_UP (Kinetic={kinetic_e:.1f} < Barrier)"

        return AgentSignal(self.name, signal, conf, reason, self.weight)
