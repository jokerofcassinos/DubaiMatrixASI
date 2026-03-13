"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — STOCHASTIC AGENTS (Phase Ω)                 ║
║     Inteligência Suprema (Nível 34): Processos de Hawkes e Ornstein-        ║
║     Uhlenbeck. Erradicação de compras de topos e vendas de fundos.          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal

class HawkesProcessAgent(BaseAgent):
    """
    [Phase Ω-Stochastic] Processo de Hawkes (Auto-Excitação).
    Modela os ticks como um processo pontual auto-excitante. Um trade grande
    "excita" o mercado, causando uma cascata de outros trades (Stop Hunts).
    Se a taxa de chegada de ordens (intensidade lambda) atinge um pico parabólico
    e começa a decair, a "cascata" acabou. Comprar/vender após o pico da excitação 
    é suicídio. O agente reverte o sinal assim que a excitação colapsa.
    """
    def __init__(self, weight=5.0):
        super().__init__("HawkesProcess", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        tick_buffer = snapshot.metadata.get("tick_buffer", [])
        if len(tick_buffer) < 30:
            return AgentSignal(self.name, 0.0, 0.0, "INSUFFICIENT_TICKS", self.weight)

        # Usar timestamps e volumes para calcular a intensidade de chegada
        # Simplificação: Intensidade = Volume recente / tempo decorrido
        times = [t.get("time_msc", 0) for t in tick_buffer]
        volumes = [t.get("volume", 1.0) for t in tick_buffer]
        
        # Dividir em duas janelas: Passado recente (cascata) vs Presente imediato (agora)
        recent_v = sum(volumes[-10:])
        recent_dt = max(1, times[-1] - times[-10])
        lambda_recent = recent_v / recent_dt
        
        past_v = sum(volumes[-30:-10])
        past_dt = max(1, times[-10] - times[-30])
        lambda_past = past_v / past_dt
        
        signal = 0.0
        conf = 0.0
        reason = "NORMAL_EXCITATION"
        
        # Se a intensidade no passado era brutal (cascata) e agora desabou
        if lambda_past > lambda_recent * 3.0 and lambda_past > 0.5:
            # A excitação acabou. O movimento linear exauriu.
            tick_velocity = snapshot.metadata.get("tick_velocity", 0.0)
            if abs(tick_velocity) > 0:
                signal = -np.sign(tick_velocity) # Aposta na reversão elástica
                conf = 0.95
                reason = f"HAWKES_CASCADE_EXHAUSTED (Pastλ={lambda_past:.2f} > Curλ={lambda_recent:.2f})"
        elif lambda_recent > lambda_past * 3.0 and lambda_recent > 0.5:
            # Cascata recém iniciada, acompanhar.
            tick_velocity = snapshot.metadata.get("tick_velocity", 0.0)
            signal = np.sign(tick_velocity)
            conf = 0.85
            reason = f"HAWKES_CASCADE_IGNITION"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class OrnsteinUhlenbeckAgent(BaseAgent):
    """
    [Phase Ω-Stochastic] Processo de Ornstein-Uhlenbeck (Reversão à Média).
    Modela o preço como uma partícula sujeita a uma força elástica que a puxa 
    de volta para uma média dinâmica (equilibrium). dx_t = theta * (mu - x_t)dt + sigma * dW_t
    Se o desvio é massivo (puxou muito o elástico) e não há choque exógeno, 
    a força de restauração 'theta' força o preço de volta.
    """
    def __init__(self, weight=4.9):
        super().__init__("OrnsteinUhlenbeck", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 20:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)
        current_price = closes[-1]
        
        # Estimativa da média de equilíbrio (mu)
        mu = np.mean(closes[-20:])
        
        # Desvio absoluto
        deviation = current_price - mu
        
        atr_list = snapshot.indicators.get("M1_atr_14", [20.0])
        atr = atr_list[-1] if len(atr_list) > 0 else 20.0
        
        signal = 0.0
        conf = 0.0
        reason = "EQUILIBRIUM"
        
        # Se puxou o elástico demais (> 2.5 ATRs da média M1)
        if abs(deviation) > atr * 2.5:
            signal = -np.sign(deviation) # Força de restauração
            conf = min(0.99, abs(deviation) / (atr * 3.0))
            reason = f"ORNSTEIN_UHLENBECK_REVERSION (Dev={deviation:.1f}, ATR={atr:.1f})"
            
        return AgentSignal(self.name, signal, conf, reason, self.weight)
