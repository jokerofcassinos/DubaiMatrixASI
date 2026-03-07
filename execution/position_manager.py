"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — POSITION MANAGER v2.0                  ║
║       Smart TP Letal: Profit Lock, Momentum Reversal, Trailing Nuke         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import time
import numpy as np
from typing import Dict, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor

from market.mt5_bridge import MT5Bridge
from market.data_engine import MarketSnapshot
from config.omega_params import OMEGA
from utils.logger import log
from utils.decorators import catch_and_log
from execution.wormhole_router import WormholeRouter

class PositionManager:
    """
    Gerenciador Letal de Posições v2.0 — Smart TP Multi-Trigger.
    
    5 Gatilhos Independentes de Saída Inteligente:
    
    1. PROFIT DRAWDOWN LOCK:
       Se o lucro atingiu um pico e caiu X% desse pico → fecha imediatamente.
       Não deixa lucro evaporar. "Garanta o que é seu."
       
    2. MOMENTUM REVERSAL:
       Se o order flow (delta) inverte contra a posição enquanto lucrando → fecha.
       O smart money está saindo, nós também.
       
    3. FLOW EXHAUSTION / ABSORPTION:
       O sistema original, refinado: detecta exaustão/absorção com threshold adaptativo
       baseado no tamanho do lucro (quanto mais lucro, menos agressivo o trigger).
       
    4. AGGRESSIVE TRAILING STOP:
       Trailing stop real enviado ao MT5 que se ajusta com o ATR. Move-se rapidamente
       para proteger ganhos, mais agressivo que um trailing convencional.
       
    5. TIME DECAY:
       Se a posição está aberta por mais de N segundos sem atingir X% do TP,
       fecha para liberar capital para o próximo strike.
    """

    def __init__(self, bridge: MT5Bridge, on_close_callback=None):
        self.bridge = bridge
        self._positions_state = {}
        self._closing_tickets: Set[int] = set()
        # Callback chamado quando uma posição é fechada: fn(direction: str)
        self._on_close_callback = on_close_callback

        self.wormhole_router = WormholeRouter(self.bridge)

        # Thread pool para disparos paralelos (Phase 44)
        self._close_pool = ThreadPoolExecutor(max_workers=20, thread_name_prefix="ClosePool")
    @catch_and_log(default_return=None)
    def monitor_positions(self, snapshot: MarketSnapshot, flow_analysis: Dict):
        """
        Rotina principal de monitoramento chamada a cada ciclo pela ASIBrain.
        Analisa cada posição aberta em paralelo contra 5 triggers de saída.
        """
        positions = self.bridge.get_open_positions()
        if not positions:
            self._positions_state.clear()
            self._closing_tickets.clear()
            return
        
        # ═══ Phase 45: Agrupamento Atômico ═══
        # Agrupa posições por (símbolo, tipo, tempo_abertura_bucket)
        # O bucket de 2s garante que uma rajada de slots seja tratada como um único Strike
        groups = {}
        # Agrupa posições por (símbolo, tipo, tempo_abertura_bucket)
        # O bucket de 2s garante que uma rajada de slots seja tratada como um único Strike
        groups = {}
        for pos in positions:
            # Robustez OMEGA: O MT5 às vezes retorna 'symbol' e às vezes 'symbol_name' 
            # dependendo da versão da bridge ou do wrapper
            ticket = pos.get('ticket')
            p_type = pos.get('type')
            p_symbol = pos.get('symbol') or pos.get('symbol_name')
            p_time = pos.get('time')
            p_open = pos.get('open_price')
            p_profit = pos.get('profit', 0.0)

            if not all([ticket, p_type, p_symbol, p_time]):
                continue

            is_buy = (p_type == "BUY")
            # Bucket de 2 segundos para agrupar disparos HFT
            group_key = (p_symbol, p_type, int(p_time / 2))
            
            # Chama a monitoração topológica de perdas em background (Wormhole Risk Router)
            self.wormhole_router.monitor_event_horizon(pos)
            
            if group_key not in groups:
                groups[group_key] = {
                    "tickets": [],
                    "total_profit": 0.0,
                    "max_profit": -999999.0,
                    "is_buy": is_buy,
                    "entry_price": p_open,
                    "time": p_time,
                    "symbol": p_symbol # Guardar o simbolo nominal
                }
            
            groups[group_key]["tickets"].append(pos)
            groups[group_key]["total_profit"] += p_profit
            if p_profit > groups[group_key]["max_profit"]:
                groups[group_key]["max_profit"] = p_profit

        current_tickets = [p['ticket'] for p in positions]

        # ═══ EXTRAIR DADOS DO ORDER FLOW ═══
        flow_delta = flow_analysis.get("delta", 0.0)
        flow_imbalance = flow_analysis.get("imbalance", 0.0)
        flow_signal = flow_analysis.get("signal", 0.0)
        exhaustion = flow_analysis.get("exhaustion", {})
        absorption = flow_analysis.get("absorption", {})
        climax_score = flow_analysis.get("volume_zscore", 0.0)
        tick_velocity = flow_analysis.get("tick_velocity", 0.0)

        # ═══ ANALISAR CADA GRUPO (STRIKE) ═══
        for g_key, g_data in groups.items():
            g_tickets = g_data["tickets"]
            g_is_buy = g_data["is_buy"]
            avg_profit = g_data["total_profit"] / len(g_tickets)
            max_p = g_data["max_profit"]
            
            # State ID para o grupo (usamos o ticket da primeira posição como âncora)
            anchor_ticket = g_tickets[0]['ticket']
            
            if anchor_ticket not in self._positions_state:
                self._positions_state[anchor_ticket] = {
                    "peak_avg_profit": avg_profit,
                    "start_time": g_data["time"],
                    "trail_activated": False,
                    "last_price_change_time": time.time(),
                    "last_cached_price": g_data["entry_price"]
                }
            
            state = self._positions_state[anchor_ticket]
            
            # Update peak avg profit & stagnation price tracking
            if avg_profit > state['peak_avg_profit']:
                state['peak_avg_profit'] = avg_profit
            
            # Usamos o ask/bid atual vindo do Snapshot no Brain para checar o preco do símbolo
            # Mas como o monitor_positions não recebe o tick bruto, usamos o avg_profit como proxy
            # Ou melhor, vamos verificar se o profit mudou significativamente
            if abs(avg_profit - state.get("last_cached_profit", -999)) > 0.01:
                state["last_cached_profit"] = avg_profit
                state["last_price_change_time"] = time.time()

            should_close = False
            reason = ""

            # ═══════════════════════════════════════════════════
            #  TRIGGER 1: ATOMIC PROFIT DRAWDOWN LOCK
            # ═══════════════════════════════════════════════════
            if avg_profit > 0 and state['peak_avg_profit'] > 1.0: # Pico de $1 avg/slot
                drawdown_pct = (state['peak_avg_profit'] - avg_profit) / state['peak_avg_profit']
                
                lock_threshold = 0.40
                if state['peak_avg_profit'] > 10: lock_threshold = 0.30
                if state['peak_avg_profit'] > 50: lock_threshold = 0.20
                
                if drawdown_pct >= lock_threshold:
                    should_close = True
                    reason = f"ATOMIC_PROFIT_LOCK: Pico_Avg=${state['peak_avg_profit']:.2f} -> Atual_Avg=${avg_profit:.2f}"

            # ═══════════════════════════════════════════════════
            #  TRIGGER 2: ATOMIC MOMENTUM REVERSAL
            # ═══════════════════════════════════════════════════
            if not should_close and avg_profit > 0.5:
                buffer_tp = OMEGA.get("smart_tp_micro_reversal_buffer", 15.0)
                req_delta = 50 if avg_profit * len(g_tickets) > buffer_tp else 250
                req_signal = 0.3 if avg_profit * len(g_tickets) > buffer_tp else 0.85
                
                if g_is_buy and flow_delta < -req_delta and flow_signal < -req_signal:
                    should_close = True
                    reason = "ATOMIC_MOMENTUM_REVERSAL (Flow Against)"
                elif not g_is_buy and flow_delta > req_delta and flow_signal > req_signal:
                    should_close = True
                    reason = "ATOMIC_MOMENTUM_REVERSAL (Flow Against)"

            # ═══════════════════════════════════════════════════
            #  TRIGGER 3: ATOMIC FLOW EXHAUSTION
            # ═══════════════════════════════════════════════════
            if not should_close and avg_profit > 0.2:
                is_exh = exhaustion.get("detected", False)
                is_abs = absorption.get("detected", False)
                if (is_exh or is_abs) and climax_score > 3.0:
                    should_close = True
                    reason = f"ATOMIC_EXHAUSTION (Climax={climax_score:.1f})"

            # ═══════════════════════════════════════════════════
            #  TRIGGER 4: MICRO-STAGNATION EXIT (Phase 46)
            #  Se o lucro médio parar por 2-3s → nuke
            # ═══════════════════════════════════════════════════
            if not should_close and avg_profit > 1.0:
                stag_time = time.time() - state.get("last_price_change_time", time.time())
                if stag_time >= 3.0:
                    should_close = True
                    reason = f"MICRO_STAGNATION (Flat for {stag_time:.1f}s)"

            # ═══════════════════════════════════════════════════
            #  TRIGGER 5: ATOMIC TIME DECAY
            # ═══════════════════════════════════════════════════
            if not should_close:
                elapsed = time.time() - state['start_time']
                if elapsed > 120 and avg_profit > 0: # 2min scalp
                    should_close = True
                    reason = f"ATOMIC_TIME_DECAY: {elapsed:.0f}s"
                elif elapsed > 300: # 5min total cut
                    should_close = True
                    reason = f"ATOMIC_TIME_CUT: {elapsed:.0f}s"

            #  EJETAR GRUPO INTEIRO
            # ═══════════════════════════════════════════════════
            if should_close:
                symbol = g_data.get('symbol', 'UNKNOWN')
                log.omega(f"💀 NUCLEAR STRIKE: {reason} | Closing {len(g_tickets)} slots para {symbol}")
                for p in g_tickets:
                    ticket = p.get('ticket')
                    if ticket:
                        self._close_with_notify(ticket, "BUY" if g_is_buy else "SELL")

        # ═══ CLEANUP: Remover tickets fechados do state e da lista de pendentes ═══
        closed = [t for t in list(self._positions_state.keys()) if t not in current_tickets]
        for t in closed:
            del self._positions_state[t]
            if t in self._closing_tickets:
                self._closing_tickets.remove(t)

    def _close_with_notify(self, ticket: int, direction: str):
        """Marca o ticket como fechando e dispara via pool paralela (Phase 44)."""
        if ticket in self._closing_tickets:
            return
            
        self._closing_tickets.add(ticket)
        
        def _exec_close():
            self.bridge.close_position(ticket)
            if self._on_close_callback:
                try:
                    self._on_close_callback(direction)
                except Exception:
                    pass

        # Disparo assíncrono para não travar o loop de monitoramento
        self._close_pool.submit(_exec_close)

    def close_all(self):
        """Emergency Panic Mode — fecha tudo instantaneamente."""
        self.bridge.close_all_positions()
        self._positions_state.clear()
        log.omega("💀 EMERGENCY CLOSE ALL — Todas as posições liquidadas.")
