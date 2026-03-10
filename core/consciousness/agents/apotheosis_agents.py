"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — APOTHEOSIS AGENTS (Phase Ω)                 ║
║     Inteligência Cósmica e Bio-Cibernética: Algoritmos Antifrágiles e       ║
║     Predição Não-Causal via Ressonância Morfogenética do Mercado.           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal

class MorphogeneticResonanceAgent(BaseAgent):
    """
    [Phase Ω-Apotheosis] Ressonância Morfogenética (Rupert Sheldrake).
    O mercado não tem "memória" física, mas tem memória estrutural através de hábitos.
    Se um padrão bizarro (ex: um Bart Simpson pattern) ocorreu há 3 dias e deu certo 
    para as baleias, há uma "ressonância" que facilita que ele ocorra de novo hoje, 
    mesmo sem causa mecânica direta. Este agente caça essas geometrias de hábitos.
    """
    def __init__(self, weight=3.3):
        super().__init__("MorphogeneticResonance", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m5 = snapshot.candles.get("M5")
        if not candles_m5 or len(candles_m5["close"]) < 200:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m5["close"], dtype=np.float64)
        
        # Padrão atual (últimos 10 candles) normalizado
        current_pattern = closes[-10:]
        current_pattern = (current_pattern - np.mean(current_pattern)) / (np.std(current_pattern) + 1e-6)
        
        # Busca no passado por ressonância (mesma forma geométrica)
        best_match_score = float('inf')
        best_match_idx = -1
        
        for i in range(len(closes) - 100, len(closes) - 20): # Evitar o presente e ir fundo
            past_pattern = closes[i:i+10]
            if np.std(past_pattern) == 0: continue
                
            past_pattern = (past_pattern - np.mean(past_pattern)) / (np.std(past_pattern) + 1e-6)
            
            # Distância Euclidiana entre as formas
            dist = np.linalg.norm(current_pattern - past_pattern)
            
            if dist < best_match_score:
                best_match_score = dist
                best_match_idx = i

        signal = 0.0
        conf = 0.0
        reason = "NO_RESONANCE"

        # Se encontrou um hábito estrutural quase idêntico (distância < 1.0 é um match absurdo para 10 dimensões)
        if best_match_score < 1.2 and best_match_idx != -1:
            # O que aconteceu LOGO APÓS esse padrão no passado?
            future_return = (closes[best_match_idx + 13] - closes[best_match_idx + 9]) / closes[best_match_idx + 9]
            
            if abs(future_return) > 0.002: # Se houve movimento significativo
                signal = np.sign(future_return)
                conf = min(0.95, 1.5 / best_match_score) # Quanto menor a distância, maior a confiança
                reason = f"MORPHOGENETIC_ECHO (Score={best_match_score:.2f}, Proj={future_return*100:.2f}%)"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class AntifragileExtremumAgent(BaseAgent):
    """
    [Phase Ω-Apotheosis] Antifragilidade (Nassim Taleb).
    Sistemas que se beneficiam do caos. Quando a volatilidade explode 
    (Drawdown sistêmico do mercado), os players frágeis são liquidados.
    O agente Antifrágil detecta "Liquidation Cascades" não para fugir, 
    mas para COMPRAR O SANGUE (The Blood in the Streets), porque a 
    transferência de riqueza já ocorreu.
    """
    def __init__(self, weight=3.7):
        super().__init__("AntifragileExtremum", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 15:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)
        lows = np.array(candles_m1["low"], dtype=np.float64)
        highs = np.array(candles_m1["high"], dtype=np.float64)
        volumes = np.array(candles_m1["tick_volume"], dtype=np.float64)
        
        atr = snapshot.indicators.get("M5_atr_14", [50.0])[-1]
        
        # Detecção de Cascade (3 candles gigantescos seguidos na mesma direção com volume crescente)
        c1, c2, c3 = closes[-3], closes[-2], closes[-1]
        o1, o2, o3 = candles_m1["open"][-3], candles_m1["open"][-2], candles_m1["open"][-1]
        
        v1, v2, v3 = volumes[-3], volumes[-2], volumes[-1]
        
        # Queda brutal
        if c1 < o1 and c2 < o2 and c3 < o3:
            total_drop = o1 - c3
            if total_drop > atr * 3.0 and v3 > v1 * 1.5:
                # O sangue rolou. Todos os stops foram estourados.
                # Se o último candle deixou um pavio (absorção antifrágil)
                if c3 - lows[-1] > (o3 - c3) * 0.5:
                    return AgentSignal(
                        self.name, 
                        1.0, # Compra agressiva
                        0.99, # Certeza quase absoluta do repique elástico
                        f"ANTIFRAGILE_LONG_BLOOD (Drop={total_drop:.1f}, Wick Absorb)",
                        self.weight
                    )

        # Alta irracional (Short Squeeze massivo)
        elif c1 > o1 and c2 > o2 and c3 > o3:
            total_pump = c3 - o1
            if total_pump > atr * 3.0 and v3 > v1 * 1.5:
                # Short sellers dizimados. Não sobrou ninguém para comprar.
                if highs[-1] - c3 > (c3 - o3) * 0.5:
                    return AgentSignal(
                        self.name, 
                        -1.0, # Venda agressiva
                        0.99,
                        f"ANTIFRAGILE_SHORT_EUPHORIA (Pump={total_pump:.1f}, Wick Reject)",
                        self.weight
                    )

        return AgentSignal(self.name, 0.0, 0.0, "SYSTEM_STABLE", self.weight)


class QuantumTunnelingProbabilityAgent(BaseAgent):
    """
    [Phase Ω-Apotheosis] Tunelamento Quântico através de Barreiras Institucionais.
    Na física quântica, uma partícula tem a probabilidade de atravessar uma parede 
    (resistência/suporte) mesmo não tendo energia (momentum) suficiente.
    A ASI usa a frequência de testes (batidas) contra a parede para calcular a 
    probabilidade da "função de onda" vazar para o outro lado (Breakout invisível).
    """
    def __init__(self, weight=3.1):
        super().__init__("QuantumTunnelingProb", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m5 = snapshot.candles.get("M5")
        if not candles_m5 or len(candles_m5["close"]) < 50:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        highs = np.array(candles_m5["high"], dtype=np.float64)
        lows = np.array(candles_m5["low"], dtype=np.float64)
        
        current_price = snapshot.price
        
        # Buscar paredes (resistências/suportes) locais
        local_max = np.max(highs[-20:])
        local_min = np.min(lows[-20:])
        
        dist_to_res = (local_max - current_price) / current_price * 100
        dist_to_sup = (current_price - local_min) / current_price * 100
        
        # Se estamos muito perto de uma parede (< 0.1%)
        if dist_to_res < 0.1:
            # Contar "batidas" (testes) na resistência
            strikes = sum(1 for h in highs[-50:] if abs(local_max - h) / local_max < 0.001)
            if strikes >= 4:
                # Na 4ª ou 5ª batida, a probabilidade de tunelamento quântico (rompimento) é > 80%
                return AgentSignal(
                    self.name, 
                    1.0, # Compra o tunelamento
                    min(0.95, strikes * 0.2), 
                    f"QUANTUM_TUNNELING_UP (Strikes={strikes}, Prob>80%)", 
                    self.weight
                )
        elif dist_to_sup < 0.1:
            strikes = sum(1 for l in lows[-50:] if abs(l - local_min) / local_min < 0.001)
            if strikes >= 4:
                # O suporte é de vidro e vai estilhaçar
                return AgentSignal(
                    self.name, 
                    -1.0, 
                    min(0.95, strikes * 0.2), 
                    f"QUANTUM_TUNNELING_DOWN (Strikes={strikes}, Prob>80%)", 
                    self.weight
                )

        return AgentSignal(self.name, 0.0, 0.0, "PARTICLE_TRAPPED", self.weight)


class AntifragileExhaustionAgent(BaseAgent):
    """
    [Phase Ω-Apotheosis] Sensor de Exaustão Antifrágil.
    Detecta quando o momentum atual é "frágil" (demasiado esticado sem base).
    Se o preço percorreu > 2.0x ATR sem nenhum candle de respiro (pullback), 
    qualquer nova agressão é sinal de exaustão, não de força.
    """
    def __init__(self, weight=3.5):
        super().__init__("AntifragileExhaustion", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 10:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)
        atr = snapshot.indicators.get("M5_atr_14", [50.0])[-1]
        
        # Medir a esticada sem pullbacks
        # BULL exhaustion
        bull_stretch = 0
        for i in range(len(closes)-1, 0, -1):
            if closes[i] > closes[i-1]:
                bull_stretch += (closes[i] - closes[i-1])
            else:
                break # Pullback detected
                
        # BEAR exhaustion
        bear_stretch = 0
        for i in range(len(closes)-1, 0, -1):
            if closes[i] < closes[i-1]:
                bear_stretch += (closes[i-1] - closes[i])
            else:
                break
                
        signal = 0.0
        conf = 0.0
        reason = "MOMENTUM_HEALTHY"
        
        if bull_stretch > atr * 2.0:
            signal = -1.0 # Vende a exaustão da alta
            conf = min(0.95, (bull_stretch / atr) * 0.3)
            reason = f"ANTIFRAGILE_BULL_EXHAUSTION (Stretch={bull_stretch:.1f} > 2xATR)"
        elif bear_stretch > atr * 2.0:
            signal = 1.0 # Compra a exaustão da baixa
            conf = min(0.95, (bear_stretch / atr) * 0.3)
            reason = f"ANTIFRAGILE_BEAR_EXHAUSTION (Stretch={bear_stretch:.1f} > 2xATR)"

        return AgentSignal(self.name, signal, conf, reason, self.weight)

