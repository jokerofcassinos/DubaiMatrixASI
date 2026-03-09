"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — APOCALYPSE AGENTS (Phase Ω)                 ║
║     Inteligência Predatória Hostil: Dark Pools, Gamma Squeezes e            ║
║     Arbitragem de Microestrutura (Ataque a Market Makers).                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal

class DarkPoolArbitrageAgent(BaseAgent):
    """
    [Phase Ω-Apocalypse] Dark Pool Arbitrage Estimator.
    Rastreia "Pegadas Magnéticas" de grandes players. Institucionais não usam
    o Order Book público para grandes lotes; eles usam Dark Pools.
    Quando executam, causam uma divergência temporária entre o preço Spot 
    e o preço de Futuros (Basis). Este agente detecta micro-desvios de volatilidade
    que indicam absorção em Dark Pools antes que o movimento chegue ao varejo.
    """
    def __init__(self, weight=3.5):
        super().__init__("DarkPoolArbitrage", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles = snapshot.candles.get("M1")
        if not candles or len(candles["close"]) < 30:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles["close"], dtype=np.float64)
        volumes = np.array(candles["tick_volume"], dtype=np.float64)
        highs = np.array(candles["high"], dtype=np.float64)
        lows = np.array(candles["low"], dtype=np.float64)
        
        # O ideal seria comparar o preço Spot do MT5 com um feed de Futuros (Basis)
        # Como proxy holográfico: Medimos divergências anômalas entre Volume de Ticks e Range (Wick)
        # Se há volume massivo mas o preço não se move = Absorção Dark Pool
        
        recent_vol = np.mean(volumes[-5:])
        hist_vol = np.mean(volumes[-30:-5])
        
        recent_range = np.mean(highs[-5:] - lows[-5:])
        hist_range = np.mean(highs[-30:-5] - lows[-30:-5]) + 1e-6
        
        vol_anomaly = recent_vol / (hist_vol + 1e-6)
        range_anomaly = recent_range / hist_range
        
        signal = 0.0
        conf = 0.0
        reason = "NO_DARK_POOL_ACTIVITY"

        # Variação massiva de volume mas variação minúscula de range = ABSORÇÃO INSTITUCIONAL
        if vol_anomaly > 3.0 and range_anomaly < 0.8:
            # Tem gente grande enchendo/desovando a mão sem mover o preço visível.
            # Olhamos a direção do delta ou tendência M5 para adivinhar o lado
            trend = closes[-1] - closes[-15]
            if trend > 0:
                # Estão distribuindo (Vendendo) no topo do rally
                signal = -1.0
                conf = 0.95
                reason = f"DARK_POOL_DISTRIBUTION (Vol={vol_anomaly:.1f}x, Rng={range_anomaly:.1f}x)"
            else:
                # Estão acumulando (Comprando) no fundo do dump
                signal = 1.0
                conf = 0.95
                reason = f"DARK_POOL_ACCUMULATION (Vol={vol_anomaly:.1f}x, Rng={range_anomaly:.1f}x)"
                
        # Variação minúscula de volume mas variação GIGANTE de range = VÁCUO DE LIQUIDEZ (Stop Hunt)
        elif vol_anomaly < 0.5 and range_anomaly > 3.0:
            # Ninguém operou, os MMs apenas arrastaram o preço para caçar stops
            direction = np.sign(closes[-1] - closes[-3])
            signal = -direction # Reverter contra o movimento oco
            conf = 0.85
            reason = f"ILLIQUID_STOP_HUNT_DETECTED (Vol={vol_anomaly:.1f}x, Rng={range_anomaly:.1f}x)"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class OptionGammaSqueezeAgent(BaseAgent):
    """
    [Phase Ω-Apocalypse] Option Gamma Squeeze Extrapolator.
    Em grandes rompimentos do BTC, Market Makers que venderam Opções Call 
    precisam comprar o ativo base para se proteger (Delta Hedging), causando um Gamma Squeeze.
    Este agente modela a probabilidade matemática desse evento baseado na 
    aceleração parabólica do preço. Se o Squeeze é detectado, a ASI ataca junto com os MMs.
    """
    def __init__(self, weight=3.8):
        super().__init__("GammaSqueeze", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m5 = snapshot.candles.get("M5")
        if not candles_m5 or len(candles_m5["close"]) < 20:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m5["close"], dtype=np.float64)
        atr = snapshot.indicators.get("M5_atr_14", [50.0])[-1]
        
        # Gamma Squeeze é caracterizado por aceleração exponencial (o preço sobe e *acelera* a subida)
        p1 = closes[-1]
        p2 = closes[-3]
        p3 = closes[-6]
        
        # Velocidades em diferentes janelas de tempo
        v_short = p1 - p2
        v_long = p2 - p3
        
        signal = 0.0
        conf = 0.0
        reason = "NORMAL_DELTA_HEDGE"
        
        # Aceleração monstruosa (Squeeze Imminente)
        if v_short > atr * 2.0 and v_short > v_long * 3.0:
            # Preço rompeu para cima e acelerou 3x mais rápido que a onda anterior.
            # Market Makers estão em pânico comprando BTC para cobrir short calls.
            signal = 1.0
            conf = 0.95
            reason = f"BULLISH_GAMMA_SQUEEZE (Acc={v_short/max(1, v_long):.1f}x)"
            
        elif v_short < -atr * 2.0 and v_short < v_long * 3.0:
            # Preço desabou e Market Makers vendem para cobrir short puts.
            signal = -1.0
            conf = 0.95
            reason = f"BEARISH_GAMMA_SQUEEZE (Acc={v_short/min(-1, v_long):.1f}x)"

        return AgentSignal(self.name, signal, conf, reason, self.weight)
