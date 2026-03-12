"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — PHANTOM AGENTS (Phase Ω)                    ║
║     Inteligência Suprema (Nível 33): Liquidez Fantasma e Assimetria         ║
║     de Reversão Temporal.                                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal

class PhantomLiquidityAgent(BaseAgent):
    """
    [Phase Ω-Phantom] Liquidez Fantasma (Holographic Order Flow).
    Os Market Makers usam ordens 'Iceberg' ou Limits distantes para
    criar miragens (Liquidez Fantasma). Este agente mede a relação entre 
    o 'Slippage Realizado' e a 'Liquidez Anunciada'.
    Se uma vela grande absorve muito volume mas o preço desloca rápido,
    a liquidez anunciada era falsa (Phantom). O mercado irá reverter para
    caçar quem entrou nesse vácuo.
    """
    def __init__(self, weight=4.9):
        super().__init__("PhantomLiquidity", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles = snapshot.candles.get("M1")
        if not candles or len(candles["close"]) < 5:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        c0, c1 = candles["close"][-1], candles["close"][-2]
        o0 = candles["open"][-1]
        v0 = candles["tick_volume"][-1]
        
        atr = snapshot.indicators.get("M1_atr_14", [20.0])[-1]
        price_move = c0 - o0
        
        signal = 0.0
        conf = 0.0
        reason = "SOLID_LIQUIDITY"
        
        # Slippage vs Volume: Se moveu muito (> 1.5 ATR) mas o volume é < média, é um vácuo fantasma.
        avg_vol = np.mean(candles["tick_volume"][-10:-1]) + 1e-6
        vol_ratio = v0 / avg_vol
        
        if abs(price_move) > atr * 1.5 and vol_ratio < 0.8:
            # Movimento grande sem volume (Phantom). O mercado vai reverter para preencher o vácuo.
            signal = -np.sign(price_move)
            conf = 0.95
            reason = f"PHANTOM_VOID_DETECTED (Move={price_move:.1f}, VolRatio={vol_ratio:.2f})"
            
        return AgentSignal(self.name, signal, conf, reason, self.weight)


class TimeReversalAsymmetryAgent(BaseAgent):
    """
    [Phase Ω-Chronos] Assimetria de Reversão Temporal.
    Na física, processos macroscópicos são assimétricos no tempo (Entropia cresce).
    Se o mercado dá um dump brutal (venda) que leva 5 minutos, e em 30 segundos
    ele recupera 100% da queda, o tempo "correu mais rápido" na volta.
    Isso prova que a queda foi sintética (Stop Hunt) e a volta é o movimento real.
    A ASI opera a favor da ponta que violou a simetria temporal.
    """
    def __init__(self, weight=5.0):
        super().__init__("TimeReversalAsymmetry", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles = snapshot.candles.get("M1")
        if not candles or len(candles["close"]) < 15:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles["close"], dtype=np.float64)
        
        # Analisar os últimos 15 minutos. Procurar "V-Shapes" assimétricos.
        signal = 0.0
        conf = 0.0
        reason = "TIME_SYMMETRIC"
        
        atr = snapshot.indicators.get("M1_atr_14", [20.0])[-1]
        
        # Dump Lento, Pump Rápido (Bear Trap)
        # O preço caiu por X velas, e subiu a mesma quantia em Y velas (Y < X/3)
        dump_start_idx = -10
        bottom_idx = -3
        current_idx = -1
        
        if bottom_idx > dump_start_idx:
            dump_dist = closes[dump_start_idx] - closes[bottom_idx]
            pump_dist = closes[current_idx] - closes[bottom_idx]
            
            dump_time = bottom_idx - dump_start_idx
            pump_time = current_idx - bottom_idx
            
            if dump_dist > atr * 2.0 and pump_dist > dump_dist * 0.8:
                # Recuperou 80% do dump
                if pump_time < dump_time / 2.0:
                    # Assimetria Temporal Crítica: Subiu 2x mais rápido do que caiu
                    signal = 1.0
                    conf = 0.98
                    reason = f"TIME_ASYMMETRY_BULL_TRAP (Dump={dump_time}m, Pump={pump_time}m)"
                    
            # Simétrico: Pump Lento, Dump Rápido (Bull Trap)
            pump_dist_bear = closes[bottom_idx] - closes[dump_start_idx]
            dump_dist_bear = closes[bottom_idx] - closes[current_idx]
            
            if pump_dist_bear > atr * 2.0 and dump_dist_bear > pump_dist_bear * 0.8:
                if pump_time < dump_time / 2.0: # O tempo de queda foi fulminante
                    signal = -1.0
                    conf = 0.98
                    reason = f"TIME_ASYMMETRY_BEAR_TRAP (Pump={dump_time}m, Dump={pump_time}m)"

        return AgentSignal(self.name, signal, conf, reason, self.weight)

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
