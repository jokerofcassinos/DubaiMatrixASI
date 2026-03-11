"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — SYNAPSE AGENTS (Phase Ω)                    ║
║     Inteligência Suprema (Nível 19): Plasticidade Sináptica Direcional,      ║
║     Memória Persistente de Fila e Modelagem de Ruína HFT.                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal

class OrderFlowSynapticPlasticityAgent(BaseAgent):
    """
    [Phase Ω-Synapse] Plasticidade Sináptica de Order Flow.
    Redes neurais biológicas reforçam caminhos frequentemente usados (Plasticidade).
    Se os Market Makers passam 5 minutos absorvendo vendas (Bid walls não rompem),
    a 'sinapse' compradora se fortalece. Quando o rompimento finalmente ocorre, 
    o sinal de compra é massivamente amplificado porque a resistência (vendedores)
    gastou toda sua energia e a sinapse de suporte está hiper-reforçada.
    """
    def __init__(self, weight=4.6):
        super().__init__("OrderFlowSynapticPlasticity", weight)
        self.bull_synapse = 0.0
        self.bear_synapse = 0.0

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 5:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)
        opens = np.array(candles_m1["open"], dtype=np.float64)
        lows = np.array(candles_m1["low"], dtype=np.float64)
        highs = np.array(candles_m1["high"], dtype=np.float64)
        
        # Calcular rejeições de cauda (Wicks) como estímulos sinápticos
        last_wick_lower = min(opens[-2], closes[-2]) - lows[-2]
        last_wick_upper = highs[-2] - max(opens[-2], closes[-2])
        
        atr = snapshot.indicators.get("M1_atr_14", [20.0])[-1]
        
        # Reforçar a sinapse se o pavio foi grande (> 30% ATR)
        if last_wick_lower > atr * 0.3:
            self.bull_synapse += 0.2
            self.bear_synapse *= 0.5 # Enfraquece a oposta
        if last_wick_upper > atr * 0.3:
            self.bear_synapse += 0.2
            self.bull_synapse *= 0.5

        # Decaimento natural (Esquecimento)
        self.bull_synapse *= 0.9
        self.bear_synapse *= 0.9
        
        # Limitar força sináptica
        self.bull_synapse = min(1.0, self.bull_synapse)
        self.bear_synapse = min(1.0, self.bear_synapse)
        
        # Ignição da Sinapse
        current_dir = closes[-1] - opens[-1]
        
        signal = 0.0
        conf = 0.0
        reason = "SYNAPSE_NEUTRAL"
        
        # Se estamos subindo e a sinapse de suporte está hiper-reforçada
        if current_dir > 0 and self.bull_synapse > 0.7:
            signal = 1.0
            conf = self.bull_synapse
            reason = f"SYNAPTIC_BULL_FIRING (Plasticity={self.bull_synapse:.2f})"
            
        elif current_dir < 0 and self.bear_synapse > 0.7:
            signal = -1.0
            conf = self.bear_synapse
            reason = f"SYNAPTIC_BEAR_FIRING (Plasticity={self.bear_synapse:.2f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class HFTRuinProbabilityAgent(BaseAgent):
    """
    [Phase Ω-Synapse] Probabilidade de Ruína Estrutural.
    Não avalia se o preço vai subir ou descer, avalia a probabilidade da 
    VONTADE do mercado de romper o nível atual. Se o preço tenta romper uma
    resistência 5 vezes em 10 minutos (falhando em todas), a probabilidade
    dessa resistência ruir na 6ª vez converge para 1.
    """
    def __init__(self, weight=4.0):
        super().__init__("HFTRuinProbability", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["high"]) < 15:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        highs = np.array(candles_m1["high"], dtype=np.float64)
        lows = np.array(candles_m1["low"], dtype=np.float64)
        closes = np.array(candles_m1["close"], dtype=np.float64)
        
        current_price = closes[-1]
        
        # Identificar teto local
        local_ceiling = np.max(highs[-15:-1])
        local_floor = np.min(lows[-15:-1])
        
        # Contar "ataques" (wicks ou closes muito próximos ao teto/piso)
        atr = snapshot.indicators.get("M1_atr_14", [20.0])[-1]
        ceiling_attacks = np.sum(highs[-15:-1] > local_ceiling - (atr * 0.15))
        floor_attacks = np.sum(lows[-15:-1] < local_floor + (atr * 0.15))
        
        signal = 0.0
        conf = 0.0
        reason = "STRUCTURE_INTACT"
        
        # O preço está agredindo o teto agora? E o teto já foi atacado > 3 vezes?
        if current_price > local_ceiling - (atr * 0.2) and ceiling_attacks >= 4:
            # A resistência vai ruir por fadiga de material.
            signal = 1.0
            conf = min(0.98, 0.5 + (ceiling_attacks * 0.1))
            reason = f"CEILING_RUIN_IMMINENT (Attacks={ceiling_attacks}, Dist={local_ceiling-current_price:.1f})"
            
        elif current_price < local_floor + (atr * 0.2) and floor_attacks >= 4:
            # O suporte vai ruir por fadiga.
            signal = -1.0
            conf = min(0.98, 0.5 + (floor_attacks * 0.1))
            reason = f"FLOOR_RUIN_IMMINENT (Attacks={floor_attacks}, Dist={current_price-local_floor:.1f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)
