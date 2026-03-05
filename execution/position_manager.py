"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — POSITION MANAGER v2.0                  ║
║       Smart TP Letal: Profit Lock, Momentum Reversal, Trailing Nuke         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import time
import numpy as np
from typing import Dict, List, Optional

from market.mt5_bridge import MT5Bridge
from market.data_engine import MarketSnapshot
from config.omega_params import OMEGA
from utils.logger import log
from utils.decorators import catch_and_log


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
        # Callback chamado quando uma posição é fechada: fn(direction: str)
        self._on_close_callback = on_close_callback

    @catch_and_log(default_return=None)
    def monitor_positions(self, snapshot: MarketSnapshot, flow_analysis: Dict):
        """
        Rotina principal de monitoramento chamada a cada ciclo pela ASIBrain.
        Analisa cada posição aberta em paralelo contra 5 triggers de saída.
        """
        positions = self.bridge.get_open_positions()
        if not positions:
            self._positions_state.clear()
            return

        current_tickets = []

        # ═══ EXTRAIR DADOS DO ORDER FLOW ═══
        flow_delta = flow_analysis.get("delta", 0.0)
        flow_imbalance = flow_analysis.get("imbalance", 0.0)
        flow_signal = flow_analysis.get("signal", 0.0)
        exhaustion = flow_analysis.get("exhaustion", {})
        absorption = flow_analysis.get("absorption", {})
        climax_score = flow_analysis.get("volume_zscore", 0.0)
        tick_velocity = flow_analysis.get("tick_velocity", 0.0)

        # ═══ OBTER ATR PARA TRAILING ═══
        atr = 0.0
        atr_arr = snapshot.indicators.get("M5_atr_14")
        if atr_arr is not None and len(atr_arr) > 0:
            atr = float(atr_arr[-1])

        for pos in positions:
            ticket = pos['ticket']
            current_tickets.append(ticket)
            profit = pos['profit']
            is_buy = (pos['type'] == "BUY")
            current_price = pos['current_price']
            entry_price = pos['open_price']
            sl = pos['sl']
            tp = pos['tp']

            # ═══ INIT STATE ═══
            if ticket not in self._positions_state:
                self._positions_state[ticket] = {
                    "peak_profit": profit,
                    "entry_price": entry_price,
                    "is_buy": is_buy,
                    "start_time": time.time(),
                    "last_trail_price": entry_price,
                    "trail_activated": False,
                }

            state = self._positions_state[ticket]

            # ═══ UPDATE PEAK PROFIT ═══
            if profit > state['peak_profit']:
                state['peak_profit'] = profit

            # ═══════════════════════════════════════════════════
            #  TRIGGER 1: PROFIT DRAWDOWN LOCK
            #  Se o lucro caiu X% do pico → fecha para não devolver
            # ═══════════════════════════════════════════════════
            if profit > 0 and state['peak_profit'] > 5.0:  # Mínimo $5 de pico
                drawdown_from_peak = state['peak_profit'] - profit
                drawdown_pct = drawdown_from_peak / state['peak_profit']
                
                # Lock threshold: quanto mais lucro, mais laxo (protege runners)
                lock_threshold = 0.40  # Fecha se perdeu 40% do pico
                if state['peak_profit'] > 100:  # Lucro grande: mais conservador
                    lock_threshold = 0.30
                if state['peak_profit'] > 500:
                    lock_threshold = 0.20
                
                if drawdown_pct >= lock_threshold:
                    log.omega(
                        f"🔒 PROFIT LOCK: Ticket {ticket} | "
                        f"Pico=${state['peak_profit']:.2f} → Atual=${profit:.2f} "
                        f"(perdeu {drawdown_pct:.0%} do pico)"
                    )
                    self._close_with_notify(ticket, "BUY" if is_buy else "SELL")
                    continue

            # ═══════════════════════════════════════════════════
            #  TRIGGER 2: MOMENTUM REVERSAL (Order Flow Delta)
            #  Se o fluxo inverte fortemente contra a posição
            # ═══════════════════════════════════════════════════
            if profit > 2.0:  # Mínimo $2 de lucro para ativar
                # ═══ [OMEGA INJECTION] ANTI-FRAGILE SMART TP (Phase 23) ═══
                # Evita pular fora num pullback raso (micro-trap)
                buffer_tp = OMEGA.get("smart_tp_micro_reversal_buffer", 15.0)
                
                req_delta = 50 if profit > buffer_tp else 250
                req_signal = 0.3 if profit > buffer_tp else 0.85
                
                delta_against = False
                if is_buy and flow_delta < -req_delta and flow_signal < -req_signal:
                    delta_against = True
                elif not is_buy and flow_delta > req_delta and flow_signal > req_signal:
                    delta_against = True

                if delta_against:
                    log.omega(
                        f"🔄 MOMENTUM REVERSAL: Ticket {ticket} | "
                        f"Profit=${profit:.2f} | Delta={flow_delta:+.0f} | "
                        f"FlowSignal={flow_signal:+.2f}"
                    )
                    self._close_with_notify(ticket, "BUY" if is_buy else "SELL")
                    continue

            # ═══════════════════════════════════════════════════
            #  TRIGGER 3: FLOW EXHAUSTION / ABSORPTION
            #  Exaustão do comprador/vendedor com clímax de volume
            # ═══════════════════════════════════════════════════
            if profit > 1.0:
                is_exhausted = exhaustion.get("detected", False)
                is_absorbed = absorption.get("detected", False)
                
                buffer_tp = OMEGA.get("smart_tp_micro_reversal_buffer", 15.0)
                
                # Threshold de clímax adaptativo: mais alto quando há pouco lucro para ignorar ruído
                if profit > 50:
                    climax_threshold = 2.0
                elif profit > buffer_tp:
                    climax_threshold = 2.5
                else:
                    climax_threshold = 3.5  # Precisa de uma exaustão colossal para justificar TP minúsculo
                
                early_exit_reason = None
                if is_buy and (is_exhausted or is_absorbed) and climax_score > climax_threshold:
                    early_exit_reason = "SMART_TP_BUY_EXHAUSTION"
                elif not is_buy and (is_exhausted or is_absorbed) and climax_score > climax_threshold:
                    early_exit_reason = "SMART_TP_SELL_EXHAUSTION"

                if early_exit_reason:
                    log.omega(
                        f"👁️ {early_exit_reason}: Ticket {ticket} | "
                        f"Profit=${profit:.2f} | Climax={climax_score:.1f}"
                    )
                    self._close_with_notify(ticket, "BUY" if is_buy else "SELL")
                    continue

            # ═══════════════════════════════════════════════════
            #  TRIGGER 4: AGGRESSIVE TRAILING STOP
            #  Move o SL rapidamente para proteger ganhos
            # ═══════════════════════════════════════════════════
            if atr > 0 and profit > 0:
                trail_activation_atr = OMEGA.get("trailing_stop_atr_mult", 1.5)
                trail_step = atr * 0.3  # Agressivo: step de 30% do ATR
                
                price_move = abs(current_price - entry_price)
                activation_distance = atr * trail_activation_atr
                
                if price_move >= activation_distance:
                    state['trail_activated'] = True
                
                if state['trail_activated']:
                    if is_buy:
                        new_sl = current_price - atr * 0.8  # Trail apertado: 0.8 ATR
                        if sl == 0 or new_sl > sl + trail_step:
                            self.bridge.modify_position(ticket, sl=round(new_sl, 2))
                            state['last_trail_price'] = current_price
                    else:
                        new_sl = current_price + atr * 0.8
                        if sl == 0 or new_sl < sl - trail_step:
                            self.bridge.modify_position(ticket, sl=round(new_sl, 2))
                            state['last_trail_price'] = current_price

            # ═══════════════════════════════════════════════════
            #  TRIGGER 5: TIME DECAY
            #  Se o trade está estagnado → fecha para liberar capital
            # ═══════════════════════════════════════════════════
            elapsed_seconds = time.time() - state['start_time']
            max_hold_time = 300  # 5 minutos max para scalp/HFT
            
            if elapsed_seconds > max_hold_time:
                if profit > 0:
                    log.omega(
                        f"⏰ TIME DECAY EXIT: Ticket {ticket} | "
                        f"Aberto por {elapsed_seconds:.0f}s | Profit=${profit:.2f}"
                    )
                    self._close_with_notify(ticket, "BUY" if is_buy else "SELL")
                    continue
                elif profit > -10:  # Perda pequena: fecha para não piorar
                    log.omega(
                        f"⏰ TIME DECAY CUT: Ticket {ticket} | "
                        f"Aberto por {elapsed_seconds:.0f}s | Loss=${profit:.2f}"
                    )
                    self._close_with_notify(ticket, "BUY" if is_buy else "SELL")
                    continue

        # ═══ CLEANUP: Remover tickets fechados do state ═══
        closed = [t for t in self._positions_state if t not in current_tickets]
        for t in closed:
            del self._positions_state[t]

    def _close_with_notify(self, ticket: int, direction: str):
        """Fecha posição e notifica o executor para ativar post-close cooldown."""
        self.bridge.close_position(ticket)
        if self._on_close_callback:
            try:
                self._on_close_callback(direction)
            except Exception:
                pass  # Nunca bloquear o close por erro de callback

    def close_all(self):
        """Emergency Panic Mode — fecha tudo instantaneamente."""
        self.bridge.close_all_positions()
        self._positions_state.clear()
        log.omega("💀 EMERGENCY CLOSE ALL — Todas as posições liquidadas.")
