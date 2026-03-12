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
