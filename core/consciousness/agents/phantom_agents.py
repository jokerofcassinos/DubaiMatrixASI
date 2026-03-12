"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — PHANTOM AGENTS (Phase Ω)                    ║
║     Inteligência Suprema (Nível 24): Reconstrução Holográfica do Book        ║
║     e Detecção de Liquidez Fantasma sem L2 Data.                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal

class HolographicDOMAgent(BaseAgent):
    """
    [Phase Ω-Phantom] Reconstrução Holográfica do Order Book (DOM).
    Quando a corretora (Prop Firms) oculta os dados de L2 (Depth of Market), 
    este agente infere a localização de grandes paredes de ordens usando a 
    fricção do preço. Se o preço toca um nível, o volume de ticks explode,
    mas o preço não avança, ele matematicamente materializa uma "Parede Fantasma"
    nesse nível e opera a rejeição (Spring/Upthrust).
    """
    def __init__(self, weight=4.8):
        super().__init__("HolographicDOM", weight)
        self.ghost_bids = {}
        self.ghost_asks = {}

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 30:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)
        highs = np.array(candles_m1["high"], dtype=np.float64)
        lows = np.array(candles_m1["low"], dtype=np.float64)
        volumes = np.array(candles_m1["tick_volume"], dtype=np.float64)
        
        current_price = closes[-1]
        atr = snapshot.indicators.get("M1_atr_14", [20.0])[-1]
        
        # 1. Decay da memória fantasma
        keys_to_remove_bids = []
        for p in self.ghost_bids:
            self.ghost_bids[p] *= 0.95 # Evaporação natural
            if self.ghost_bids[p] < 10:
                keys_to_remove_bids.append(p)
        for k in keys_to_remove_bids: del self.ghost_bids[k]
        
        keys_to_remove_asks = []
        for p in self.ghost_asks:
            self.ghost_asks[p] *= 0.95
            if self.ghost_asks[p] < 10:
                keys_to_remove_asks.append(p)
        for k in keys_to_remove_asks: del self.ghost_asks[k]

        # 2. Materialização de Paredes (Scanning)
        avg_vol = np.mean(volumes[-20:-1]) + 1e-6
        for i in range(-5, 0): # Últimos 5 candles
            vol_ratio = volumes[i] / avg_vol
            if vol_ratio > 2.0: # Volume massivo
                body = abs(closes[i] - candles_m1["open"][i])
                wick_up = highs[i] - max(closes[i], candles_m1["open"][i])
                wick_down = min(closes[i], candles_m1["open"][i]) - lows[i]
                
                # Se o preço caiu, bateu, o volume explodiu e deixou pavio -> Parede Fantasma de Compra (Bid)
                if wick_down > atr * 0.3 and wick_down > body:
                    level = round(lows[i] / 10) * 10 # Agrupar a cada 10 pontos
                    self.ghost_bids[level] = self.ghost_bids.get(level, 0) + (volumes[i] * wick_down)
                    
                # Se o preço subiu, bateu, o volume explodiu e deixou pavio -> Parede Fantasma de Venda (Ask)
                if wick_up > atr * 0.3 and wick_up > body:
                    level = round(highs[i] / 10) * 10
                    self.ghost_asks[level] = self.ghost_asks.get(level, 0) + (volumes[i] * wick_up)

        signal = 0.0
        conf = 0.0
        reason = "NO_PHANTOM_WALL"
        
        # 3. Decisão: O preço atual está "batendo" em uma parede fantasma monstruosa?
        current_level = round(current_price / 10) * 10
        
        # Procurar parede de Bid (Suporte fantasma) logo abaixo
        nearest_bid_wall = 0
        for p, strength in self.ghost_bids.items():
            if current_price >= p and (current_price - p) < atr:
                if strength > nearest_bid_wall: nearest_bid_wall = strength
                
        # Procurar parede de Ask (Resistência fantasma) logo acima
        nearest_ask_wall = 0
        for p, strength in self.ghost_asks.items():
            if current_price <= p and (p - current_price) < atr:
                if strength > nearest_ask_wall: nearest_ask_wall = strength

        threshold = avg_vol * atr * 0.5 # Threshold dinâmico de força
        
        # A lógica de armadilha: O preço está mergulhando violentamente na direção da parede fantasma?
        # A maioria dos robôs (e a ASI) veria o momentum de queda e venderia.
        # Nós COMPRAMOS a rejeição antes do wick se formar completamente.
        velocity = closes[-1] - closes[-2]
        
        if velocity < -atr * 0.5 and nearest_bid_wall > threshold:
            # Mergulho cego direto num bloco institucional oculto (Bear Trap Imminente)
            signal = 1.0 # COMPRA (Absorção)
            conf = min(0.98, 0.5 + (nearest_bid_wall / (threshold * 5)))
            reason = f"PHANTOM_BID_WALL_IMPACT (Velocity={velocity:.1f}, WallStrength={nearest_bid_wall:.0f})"
            
        elif velocity > atr * 0.5 and nearest_ask_wall > threshold:
            # Voo cego direto numa muralha de venda (Bull Trap Imminente)
            signal = -1.0 # VENDA (Distribuição)
            conf = min(0.98, 0.5 + (nearest_ask_wall / (threshold * 5)))
            reason = f"PHANTOM_ASK_WALL_IMPACT (Velocity={velocity:.1f}, WallStrength={nearest_ask_wall:.0f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class FractionalCalculusVelocityAgent(BaseAgent):
    """
    [Phase Ω-Phantom] Cálculo Fracionário da Velocidade.
    Velocidade e Aceleração tradicionais (1ª e 2ª derivadas) são "limpas" demais.
    O mercado tem memória longa (rugosidade fracionária). Aplicando derivadas
    de ordem fracionária (ex: 0.5), detectamos "viscosidade" no movimento.
    Se o preço cai muito rápido (derivada 1.0) mas a derivada fracionária (0.5) 
    não acompanha, a queda é oca (Bear Trap) e o preço vai rebater como mola.
    """
    def __init__(self, weight=4.3):
        super().__init__("FractionalCalculusVelocity", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 20:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)[-20:]
        
        # Derivada clássica (1ª Ordem)
        v_classical = closes[-1] - closes[-2]
        
        # Aproximação de Derivada Fracionária (Ordem 0.5 - Grünwald-Letnikov modificada)
        # Usa memória de longo prazo com pesos decrescentes
        weights = [1.0, -0.5, -0.125, -0.0625, -0.039]
        if len(closes) >= 5:
            v_fractional = sum(w * c for w, c in zip(weights, reversed(closes[-5:])))
        else:
            v_fractional = v_classical
            
        signal = 0.0
        conf = 0.0
        reason = "VISCOSITY_NORMAL"
        
        atr = snapshot.indicators.get("M1_atr_14", [20.0])[-1]
        
        # Divergência Fracionária:
        # Se o preço mergulhou (v_classical < -ATR) mas a memória fracionária rejeita (v_frac > 0)
        # Isso significa que o movimento é uma ruptura falsa que não possui inércia passada.
        if v_classical < -atr * 0.8 and v_fractional > 0:
            signal = 1.0 # COMPRA (Rejeita o mergulho oco)
            conf = 0.94
            reason = f"FRACTIONAL_DIVERGENCE_BEAR_TRAP (V={v_classical:.1f}, V_Frac={v_fractional:.1f})"
            
        elif v_classical > atr * 0.8 and v_fractional < 0:
            signal = -1.0 # VENDA (Rejeita o voo oco)
            conf = 0.94
            reason = f"FRACTIONAL_DIVERGENCE_BULL_TRAP (V={v_classical:.1f}, V_Frac={v_fractional:.1f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)
