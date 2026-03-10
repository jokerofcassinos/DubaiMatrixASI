"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — GENESIS AGENTS (Phase Ω)                   ║
║     Inteligência Suprema (Nível 13): Inferência Causal, Raciocínio          ║
║     Contrafactual e Decomposição de Intencionalidade.                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal

class CausalCounterfactualAgent(BaseAgent):
    """
    [Phase Ω-Genesis] Raciocínio Contrafactual (Inferência Causal).
    O que o preço seria se um determinado choque de volume não tivesse ocorrido?
    Calcula o 'Preço Orgânico' (Baseline) versus o 'Preço Manipulado' (Choque).
    Se a divergência for muito alta, a ASI aposta na volta imediata ao orgânico.
    """
    def __init__(self, weight=4.2): # Peso colossal: Baseado em causalidade real
        super().__init__("CausalCounterfactual", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 30:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)
        volumes = np.array(candles_m1["tick_volume"], dtype=np.float64)
        
        # 1. Identificar o "Preço Orgânico" (Média ponderada por volume estável)
        # Removemos os outliers de volume (choques) para calcular o orgânico
        vol_mean = np.mean(volumes)
        vol_std = np.std(volumes)
        organic_mask = volumes < (vol_mean + vol_std)
        
        if not np.any(organic_mask):
            return AgentSignal(self.name, 0.0, 0.0, "NO_ORGANIC_DATA", self.weight)
            
        # O preço orgânico é a tendência sem os picos de volume institucional
        organic_trend = np.polyval(np.polyfit(np.arange(len(closes))[organic_mask], closes[organic_mask], 1), len(closes)-1)
        
        current_price = closes[-1]
        divergence = current_price - organic_trend
        
        # 2. Identificar a "Intencionalidade" (Volume anormal recente)
        recent_vol = np.mean(volumes[-3:])
        vol_shock = recent_vol / (vol_mean + 1e-6)
        
        atr = snapshot.indicators.get("M5_atr_14", [20.0])[-1]
        
        signal = 0.0
        conf = 0.0
        reason = "CAUSAL_EQUILIBRIUM"
        
        # Se houve um choque de volume (Alguém agiu) E o preço divergiu muito do orgânico
        if vol_shock > 2.5 and abs(divergence) > atr * 1.0:
            # Temos um desvio causal. A 'Causa' foi o choque de volume.
            # Qual a probabilidade do mercado sustentar esse desvio?
            # Se a aceleração (v-pulse) está caindo, a causa está morrendo.
            tick_velocity = snapshot.metadata.get("tick_velocity", 0.0)
            
            if tick_velocity < 20.0: # A energia da agressão acabou, mas o preço ficou 'pendurado'
                # Sinal de reversão contrafactual: "Se a agressão parou, o preço deve voltar"
                signal = -np.sign(divergence)
                conf = 0.92
                reason = f"CAUSAL_REVERSION (Div={divergence:.1f}, Shock={vol_shock:.1f}x)"
            else:
                # A agressão continua. É uma mudança de patamar orgânico real.
                signal = np.sign(divergence)
                conf = 0.85
                reason = f"CAUSAL_MOMENTUM (New organic level forming)"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class IntentionalityDecompositionAgent(BaseAgent):
    """
    [Phase Ω-Genesis] Decomposição de Intencionalidade Institucional.
    Separa ordens PASSIVAS (Absorção) de ordens ATIVAS (Agressão).
    Mapeia a 'Vontade' do mercado. Se o preço sobe mas a 'Vontade de Venda'
    (absorção no Ask) é maior que a 'Vontade de Compra', o movimento é uma 
    armadilha de exaustão.
    """
    def __init__(self, weight=4.0):
        super().__init__("IntentDecomposition", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        orderflow = kwargs.get("orderflow_analysis", {})
        if not orderflow:
            return AgentSignal(self.name, 0.0, 0.0, "NO_ORDERFLOW", self.weight)
            
        imbalance = orderflow.get("imbalance", 0.0) # Delta agressivo
        absorption = orderflow.get("absorption", {}) # Detecção de Icebergs/Paredes
        
        buy_abs = absorption.get("buy_absorption", 0.0)
        sell_abs = absorption.get("sell_absorption", 0.0)
        
        signal = 0.0
        conf = 0.0
        reason = "INTENT_NEUTRAL"
        
        # Se há muita agressão de compra (imbalance > 0.6) mas também muita absorção de venda (sell_abs > threshold)
        # Significa que as baleias estão vendendo passivamente tudo que o varejo compra.
        if imbalance > 0.6 and sell_abs > 0.7:
            signal = -1.0 # Bearish (Armadilha de Compra)
            conf = 0.95
            reason = f"INTENT_DECEPTION_BEAR (Aggressive BUY absorbed by Passive SELL)"
            
        elif imbalance < -0.6 and buy_abs > 0.7:
            signal = 1.0 # Bullish (Armadilha de Venda)
            conf = 0.95
            reason = f"INTENT_DECEPTION_BULL (Aggressive SELL absorbed by Passive BUY)"
            
        return AgentSignal(self.name, signal, conf, reason, self.weight)
