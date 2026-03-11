"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — SOVEREIGNTY AGENTS (Phase Ω)                ║
║     Inteligência Suprema (Nível 16): Mecanismo de Atenção Temporal         ║
║     (Transformer Proxy) e Foco Direcional.                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal

class TemporalAttentionAgent(BaseAgent):
    """
    [Phase Ω-Sovereignty] Mecanismo de Atenção Temporal.
    Inspirado na arquitetura Transformer (Attention is All You Need).
    Em vez de dar peso igual a todas as velas recentes, o agente calcula
    um 'Attention Score' para cada vela baseado no seu volume e amplitude.
    Ele foca a decisão na direção da vela com maior atenção, ignorando o
    ruído das velas menores recentes.
    """
    def __init__(self, weight=4.4): # Peso massivo, atua como farol direcional
        super().__init__("TemporalAttention", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 20:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)
        opens = np.array(candles_m1["open"], dtype=np.float64)
        highs = np.array(candles_m1["high"], dtype=np.float64)
        lows = np.array(candles_m1["low"], dtype=np.float64)
        volumes = np.array(candles_m1["tick_volume"], dtype=np.float64)
        
        # Considerar os últimos 15 candles para atenção
        recent_closes = closes[-15:]
        recent_opens = opens[-15:]
        recent_highs = highs[-15:]
        recent_lows = lows[-15:]
        recent_vols = volumes[-15:]
        
        # Calcular 'Query' (o estado atual) - Onde estamos agora?
        current_price = recent_closes[-1]
        
        # Calcular 'Keys' e 'Values' para o passado
        # O Attention Score de uma vela é (Amplitude * Volume)
        amplitudes = recent_highs - recent_lows
        attention_scores = amplitudes * recent_vols
        
        # Normalizar scores (Softmax Proxy)
        if np.sum(attention_scores) == 0:
            return AgentSignal(self.name, 0.0, 0.0, "ZERO_ATTENTION", self.weight)
            
        attention_weights = attention_scores / np.sum(attention_scores)
        
        # Encontrar a vela "Âncora" (A que tem maior atenção)
        anchor_idx = np.argmax(attention_weights)
        anchor_weight = attention_weights[anchor_idx]
        
        signal = 0.0
        conf = 0.0
        reason = "DISTRIBUTED_ATTENTION"
        
        # Se uma única vela domina a atenção da janela (peso > 30% do total)
        if anchor_weight > 0.30:
            anchor_open = recent_opens[anchor_idx]
            anchor_close = recent_closes[anchor_idx]
            
            # Qual foi a direção dessa vela monumental?
            anchor_dir = np.sign(anchor_close - anchor_open)
            
            # Se ainda não revertemos a vela âncora, a gravidade dela dita o mercado
            if anchor_dir == 1 and current_price > anchor_open:
                signal = 1.0
                conf = 0.90
                reason = f"ATTENTION_BULL_ANCHOR (Weight={anchor_weight:.0%}, {15-anchor_idx}m ago)"
            elif anchor_dir == -1 and current_price < anchor_open:
                signal = -1.0
                conf = 0.90
                reason = f"ATTENTION_BEAR_ANCHOR (Weight={anchor_weight:.0%}, {15-anchor_idx}m ago)"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class CrossExchangeDeltaAgent(BaseAgent):
    """
    [Phase Ω-Sovereignty] Arbitragem de Vontade Multidimensional (Simulado).
    Em vez de apenas olhar o fluxo do broker, detecta a anomalia clássica:
    Spot Price (Orgânico) vs Futures Price (Alavancado).
    Como não temos feed simultâneo real da Binance aqui, usamos um proxy termodinâmico:
    Se o preço move rápido mas a entropia de ticks cai a zero, é spoofing de futuros.
    Se a entropia explode junto com o preço, é adoção spot.
    """
    def __init__(self, weight=4.1):
        super().__init__("CrossExchangeDelta", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        tick_velocity = snapshot.metadata.get("tick_velocity", 0.0)
        entropy = snapshot.metadata.get("tick_entropy", 0.5)
        
        signal = 0.0
        conf = 0.0
        reason = "DELTA_SYNCED"
        
        # Movimento veloz (Futures push) mas sem entropia orgânica (Spot ausente)
        if tick_velocity > 25.0 and entropy < 0.2:
            # É um fake push alavancado que será revertido
            candles_m1 = snapshot.candles.get("M1")
            if candles_m1 and len(candles_m1["close"]) > 2:
                trend = candles_m1["close"][-1] - candles_m1["close"][-2]
                if trend != 0:
                    signal = -np.sign(trend) # Contrarian
                    conf = 0.95
                    reason = f"CROSS_DELTA_FAKE_PUSH (Vel={tick_velocity:.1f}, Ent={entropy:.2f})"
                    
        # Movimento com entropia extrema (Spot absorvendo e dominando os Futuros)
        elif tick_velocity > 20.0 and entropy > 0.85:
            # Movimento orgânico hiper-denso
            candles_m1 = snapshot.candles.get("M1")
            if candles_m1 and len(candles_m1["close"]) > 2:
                trend = candles_m1["close"][-1] - candles_m1["close"][-2]
                if trend != 0:
                    signal = np.sign(trend) # Follow
                    conf = 0.95
                    reason = f"CROSS_DELTA_ORGANIC_DRIVE (Vel={tick_velocity:.1f}, Ent={entropy:.2f})"
                    
        return AgentSignal(self.name, signal, conf, reason, self.weight)
