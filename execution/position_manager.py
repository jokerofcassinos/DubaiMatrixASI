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
from execution.trade_registry import registry as trade_registry
from core.decision.trinity_core import Action, Decision

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
        
        # Cooldown de logging para evitar spam (Phase Ω-Resilience)
        self._last_nuke_log_time = {} # anchor_ticket -> float
        self._close_attempt_time = {} # ticket -> float (diagnostic)
    @catch_and_log(default_return=None)
    def monitor_positions(self, snapshot: MarketSnapshot, flow_analysis: Dict, quantum_state=None):
        """
        Rotina principal de monitoramento chamada a cada ciclo pela ASIBrain.
        Analisa posições abertas e ordens pendentes.
        """
        # 1. GESTÃO DE ORDENS PENDENTES (LIMITS)
        self._manage_pending_orders(snapshot.price, snapshot.atr)

        # 2. GESTÃO DE POSIÇÕES ABERTAS
        positions = self.bridge.get_open_positions()
        
        # OMEGA: Se for None, houve erro na ponte. Mantemos o estado para evitar amnésia.
        if positions is None:
            return
            
        # OMEGA: Se for [], as posições foram realmente fechadas.
        if not positions:
            self._positions_state.clear()
            self._closing_tickets.clear()
            return
        
        # ═══ Phase 45: Agrupamento Atômico ═══
        groups = {}
        for pos in positions:
            ticket = pos.get('ticket')
            p_type = pos.get('type')
            p_symbol = pos.get('symbol') or pos.get('symbol_name')
            p_time = pos.get('time')
            p_open = pos.get('open_price')
            p_profit = pos.get('profit', 0.0)

            if not all([ticket, p_type, p_symbol, p_time]):
                continue

            is_buy = (p_type == "BUY")
            # [Phase Ω-Resilience] Bucket de 1 segundo para agrupar disparos HFT (Reduzido de 5s para Precisão)
            # Evita que slots de um mesmo strike fiquem órfãos por lag do broker.
            group_key = (p_symbol, p_type, int(p_time))
            
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
                    "symbol": p_symbol,
                    "lot_total": 0.0
                }
            
            groups[group_key]["tickets"].append(pos)
            groups[group_key]["total_profit"] += p_profit
            groups[group_key]["lot_total"] += pos.get('volume', 0.0)
            if p_profit > groups[group_key]["max_profit"]:
                groups[group_key]["max_profit"] = p_profit

            # [PHASE Ω-EVOLVE] Anti-Amnesia: Se não há intenção registrada, criamos uma agora
            # Isso evita o aviso [AMNESIA] durante a reflexão e permite que o SelfOptimizer use o trade.
            if not trade_registry.get_intent(position_id=ticket):
                # Usar log.debug para evitar spam no terminal
                log.debug(f"🧠 [MEMORY RECOVERY] Reconstruindo intenção para Position #{ticket}")
                trade_registry.register_intent(
                    ticket=ticket,
                    intent=Decision(
                        action=Action.BUY if is_buy else Action.SELL,
                        confidence=0.5, # Fallback conservative
                        signal_strength=0.0,
                        entry_price=p_open,
                        stop_loss=pos.get('sl', 0),
                        take_profit=pos.get('tp', 0),
                        lot_size=pos.get('volume', 0.01),
                        regime=snapshot.regime.value if hasattr(snapshot.regime, 'value') else str(snapshot.regime),
                        reasoning="RECOVERED_INTENT (Original lost during async strike)"
                    ),
                    snapshot=snapshot,
                    position_id=ticket
                )

        current_tickets = [p['ticket'] for p in positions]

        # ═══ [PHASE Ω-RESILIENCE] ANTI-STUCK CLOSE GUARD ═══
        # Se um ticket está em _closing_tickets há mais de 5s e ainda consta como aberto,
        # removemos do set para permitir que o loop de monitoramento tente fechar novamente.
        now = time.time()
        for t in list(self._closing_tickets):
            if t in current_tickets:
                if now - self._close_attempt_time.get(t, now) > 5.0:
                    log.warning(f"♻️ RETRY_CLOSE: Ticket {t} travado em fechamento. Resetando lock.")
                    self._closing_tickets.remove(t)

        # ═══ EXTRAIR DADOS DO ORDER FLOW ═══
        flow_delta = flow_analysis.get("delta", 0.0)
        flow_signal = flow_analysis.get("signal", 0.0)
        exhaustion = flow_analysis.get("exhaustion", {})
        absorption = flow_analysis.get("absorption", {})
        climax_score = flow_analysis.get("volume_zscore", 0.0)
        phi_val = snapshot.metadata.get("phi_last", 0.0) # Assume PHI injection or 0

        # ═══ ANALISAR CADA GRUPO (STRIKE) ═══
        for g_key, g_data in groups.items():
            g_tickets = g_data["tickets"]
            g_is_buy = g_data["is_buy"]
            total_profit = g_data["total_profit"]
            num_slots = len(g_tickets)
            lot_scale = g_data["lot_total"]
            
            # Usamos o primeiro ticket do grupo como âncora para o estado persistente do strike
            anchor_ticket = g_tickets[0]['ticket']
            if anchor_ticket not in self._positions_state:
                self._positions_state[anchor_ticket] = {
                    "peak_profit": total_profit,
                    "peak_time": time.time(),
                    "start_time": g_data["time"],
                    "trail_activated": False,
                    "last_price_change_time": time.time(),
                    "last_cached_profit": total_profit
                }
            
            state = self._positions_state[anchor_ticket]
            if total_profit > state['peak_profit']:
                state['peak_profit'] = total_profit
                state['peak_time'] = time.time()
            
            if abs(total_profit - state.get("last_cached_profit", -999)) > 0.01:
                state["last_cached_profit"] = total_profit
                state["last_price_change_time"] = time.time()

            should_close = False
            reason = ""

            # ═══════════════════════════════════════════════════
            #  TRIGGER 0: PROXIMITY & SMART TP (Phase Ω)
            # ═══════════════════════════════════════════════════
            # Calculamos o alvo teórico em $ para este strike
            # Usamos o primeiro ticket do grupo como referência de preço/TP
            ref_pos = g_tickets[0]
            target_profit = abs(ref_pos.get('tp', 0) - ref_pos.get('price_open', ref_pos.get('open_price', 0))) * lot_scale
            
            # [PHASE Ω-PROXIMITY] TP Front-Running Logic
            # Se o preço atual está muito perto do TP (utilizando progressão do lucro)
            profit_progress = total_profit / target_profit if target_profit > 0 else 0
            is_proximity_zone = profit_progress > OMEGA.get("proximity_trailing_threshold", 0.90)

            # ═══════════════════════════════════════════════════
            #  TRIGGER 1: HALF-WAY BREAKEVEN PROTECTION (Legacy)
            # ═══════════════════════════════════════════════════
            # Se atingimos 50% do alvo, mas o mercado reverteu para o preço de entrada,
            # saímos no 0x0 para não transformar um quase-gain em loss total.
            if not state.get("breakeven_active", False) and profit_progress > 0.5:
                state["breakeven_active"] = True
                log.omega(f"🛡️ [HALF-WAY PROTECTION] Strike {anchor_ticket} atingiu 50% do alvo. Breakeven armado.")

            if state.get("breakeven_active", False) and total_profit <= 10.0 and not is_proximity_zone: 
                # Buffer de $10. Só dispara se NÃO estivermos na zona de TP (onde o proximity strike manda)
                should_close = True
                reason = "HALF_WAY_BREAKEVEN_PROTECTION (Returned to entry after 50% progress)"

            # ═══════════════════════════════════════════════════
            #  TRIGGER 1: ATOMIC PROFIT DRAWDOWN LOCK (Trailing)
            # ═══════════════════════════════════════════════════
            peak = state['peak_profit']
            atr_val = snapshot.atr if snapshot.atr > 0 else 50.0
            comm_per_lot = snapshot.metadata.get("dynamic_commission_per_lot", 32.0)
            commission_cost = lot_scale * comm_per_lot
            
            # Floor dinâmico para garantir lucro líquido (Phase 52 Refinement)
            # [Phase 52.1] Noise Shield: Elevado p/ $50 conforme OMEGA.
            target_net_profit_per_lot = OMEGA.get("min_profit_per_ticket", 50.0) 
            target_net_profit = lot_scale * target_net_profit_per_lot
            
            dynamic_peak_floor = commission_cost + target_net_profit

            # [Phase 52.1] Noise Shield Active: 1.5x do floor deve ser atingido 
            # antes de permitirmos saídas por "ruído" (Momentum/Exaustão). Queremos esticar ganhos.
            reached_noise_shield = (total_profit >= dynamic_peak_floor * 1.5)

            if peak > dynamic_peak_floor:
                # [Phase Ω-Singularity] Trailing Stop Absoluto.
                # Calculamos o threshold com base no PICO (Peak) e não no lucro atual.
                
                # [OMISCIENCE RELAXATION] PHI-Based Expansion
                phi_relax = 1.0 + (phi_val * OMEGA.get("smart_tp_phi_relaxation_mult", 0.5))
                
                if is_proximity_zone:
                    # Trava de lucro ultra-agressiva na zona de morte
                    lock_threshold = OMEGA.get("proximity_lock_threshold", 0.05) * phi_relax
                    reason_prefix = "PROXIMITY_STRIKE"
                elif peak > dynamic_peak_floor * 2.0:
                    # Quantum Tunneling Trailing (Permite 25% de pullback em grandes runs)
                    curvature_adj = max(0, climax_score - 2.5) * 0.03 # More tolerant to volume climax in big runs
                    lock_threshold = max(0.05, (0.25 - curvature_adj) * phi_relax) 
                    reason_prefix = "RIEMANNIAN_TRAILING_STOP"
                elif peak > dynamic_peak_floor * 1.5:
                    curvature_adj = max(0, climax_score - 3.0) * 0.02
                    lock_threshold = max(0.05, (0.15 - curvature_adj) * phi_relax)
                    reason_prefix = "RIEMANNIAN_TRAILING_STOP"
                else:
                    vol_mult = 1.0 if atr_val < 150 else 0.7 
                    lock_threshold = OMEGA.get("smart_tp_lock_threshold_low", 0.25) * vol_mult * phi_relax
                    reason_prefix = "RIEMANNIAN_TRAILING_STOP"
                
                # Trava de Segurança Absoluta (Nunca deixar o lucro cair abaixo de 1.0x do Noise Shield depois de bater no alvo)
                trailing_stop_profit = max(dynamic_peak_floor * 1.0, peak * (1.0 - lock_threshold))
                
                if total_profit <= trailing_stop_profit:
                    should_close = True
                    reason = f"{reason_prefix} (Peak=${peak:.2f}, Locked=${trailing_stop_profit:.2f}, Φ_Relax={phi_relax:.2f}, Curv={climax_score:.1f}, Progress={profit_progress:.1%})"

                # ═══════════════════════════════════════════════════
                #  ADVANCED ASI LAYERS (KDS & OFAE)
                # ═══════════════════════════════════════════════════
                if not should_close and is_proximity_zone:
                    # 1. Kinematic Deceleration Sensor (KDS)
                    # Se velocity caiu drásticamente perto do alvo
                    velocity_score = flow_analysis.get("velocity_score", 0.0)
                    if abs(velocity_score) < 0.2 and abs(flow_signal) < 0.1:
                        should_close = True
                        reason = f"KDS_VELOCITY_BURN (Velocity={velocity_score:.2f} near TP)"
                    
                    # 2. Order Flow Absorption Exit (OFAE)
                    # Se há sinais de absorção pesada na cara do TP
                    if (absorption.get("detected", False) and climax_score > 3.0):
                        should_close = True
                        reason = f"OFAE_FRONT_RUN (Absorption detected at TP boundary)"

            # ═══════════════════════════════════════════════════════════
            #  SOFT TRIGGERS: Só ativam se o Noise Shield foi rompido
            # ═══════════════════════════════════════════════════════════
            if not should_close and reached_noise_shield:
                #  TRIGGER 2: ATOMIC MOMENTUM REVERSAL
                if g_is_buy and flow_signal < -0.4:
                    should_close, reason = True, "LETHAL_MOMENTUM_REVERSAL (Bearish)"
                elif not g_is_buy and flow_signal > 0.4:
                    should_close, reason = True, "LETHAL_MOMENTUM_REVERSAL (Bullish)"

                #  TRIGGER 3: ATOMIC FLOW EXHAUSTION
                if not should_close:
                    if (exhaustion.get("detected", False) or absorption.get("detected", False)) and climax_score > 2.5:
                        should_close, reason = True, f"FLOW_EXHAUSTION (Z={climax_score:.1f})"

                # [Phase Ω-Apocalypse] TRIGGER 4: TIME-DECAY PROFIT LOCK
                # O preço não faz nova máxima/mínima há muito tempo. Fuga de Theta.
                if not should_close:
                    # Medimos o tempo desde o ÚLTIMO PICO, e não da última variação de micro-lucro
                    stag_time = time.time() - state.get("peak_time", state["start_time"])
                    
                    # [Phase Ω-Pleroma] Trava de Tempo Inteligente
                    # Só fechamos por tempo se o lucro já pagou as comissões COM FOLGA
                    if peak > dynamic_peak_floor * 1.5:
                        if peak > dynamic_peak_floor * 4.0:
                            max_stag_time = 300.0 # Em corridas massivas, deixamos respirar 5 minutos
                        elif peak > dynamic_peak_floor * 3.0:
                            max_stag_time = 180.0 
                        elif peak > dynamic_peak_floor * 2.0:
                            max_stag_time = 90.0  
                        else:
                            max_stag_time = 45.0  
                            
                        # [Phase Ω-Chronos] VETO DO TIME DECAY
                        # Se o fluxo subjacente ainda está a nosso favor, ignoramos o tempo!
                        is_flow_favorable = (g_is_buy and flow_signal > 0.25) or (not g_is_buy and flow_signal < -0.25)
                        
                        regime = snapshot.regime.value if hasattr(snapshot.regime, 'value') else str(snapshot.regime)
                        is_trend = "TRENDING" in regime or "IGNITION" in regime
                        
                        if is_flow_favorable or is_trend:
                            persistence = OMEGA.get("trend_persistence_buffer", 2.0)
                            max_stag_time *= persistence # Damos mais tempo se a inércia ainda empurra ou regime é trend
                            
                        if stag_time >= max_stag_time:
                            should_close, reason = True, f"TIME_DECAY_LOCK ({stag_time:.1f}s below peak ${peak:.2f} | R={regime})"

                # ═══════════════════════════════════════════════════
                #  TRIGGER 6: THERMODYNAMIC BIFURCATION (Prigogine)
                # ═══════════════════════════════════════════════════
                if not should_close and quantum_state:
                    prigogine_signal = next((s for s in quantum_state.agent_signals if s.agent_name == "PrigogineDissipative"), None)
                    if prigogine_signal and prigogine_signal.confidence > 0.85:
                        # Se o sinal aponta contra a posição (Bifurcação Detectada)
                        if (g_is_buy and prigogine_signal.signal < 0) or (not g_is_buy and prigogine_signal.signal > 0):
                            # Se já temos algum lucro ou o drawdown é aceitável, ejetamos antes do colapso
                            should_close = True
                            reason = f"PRIGOGINE_BIFURCATION (Entropy saturation reversal detected | Conf: {prigogine_signal.confidence:.2f})"

                #  TRIGGER 7: NON-BONDED REPULSION (Van der Waals)
                if not should_close and quantum_state:
                    rep_signal = next((s for s in quantum_state.agent_signals if s.agent_name == "NonBondedRepulsion"), None)
                    if rep_signal and abs(rep_signal.signal) > 0.8:
                        if (g_is_buy and rep_signal.signal < 0) or (not g_is_buy and rep_signal.signal > 0):
                            should_close = True
                            rep_pot = (getattr(rep_signal, 'metadata', {}) or {}).get('repulsion', 0.0)
                            reason = f"NON_BONDED_REPULSION (Potential Rejection | Pot={rep_pot:.1f})"

            #  EJETAR GRUPO INTEIRO (STRIKE)
            if should_close:
                symbol = g_data.get('symbol', 'UNKNOWN')
                log.omega(f"💀 LETHAL CLOSE STRIKE: {reason} | P&L Total: ${total_profit:+.2f} | Lots: {lot_scale:.2f} | Nodes: {num_slots}")
                self._close_strike_group(g_tickets, "BUY" if g_is_buy else "SELL")

        # Cleanup e monitoramento de lag permanecem os mesmos...
        self._cleanup_tracking(current_tickets)

    def _close_strike_group(self, tickets: List[dict], direction: str):
        """Fecha todos os tickets de um strike em paralelo total."""
        for p in tickets:
            ticket = p.get('ticket')
            if ticket not in self._closing_tickets:
                self._close_with_notify(ticket, direction)

    def _manage_pending_orders(self, current_price: float, atr: float):
        """Cancela ordens pendentes que não foram executadas e expiraram ou estão fora de preço (Phase Ω-Apocalypse)."""
        pending = self.bridge.get_pending_orders()
        if not pending:
            return

        now = time.time()
        for order in pending:
            ticket = order.get('ticket')
            setup_time = order.get('time', now)
            order_price = order.get('price_open', 0.0)

            # O MT5 retorna setup_time em epoch local/server. 
            if setup_time > now + 3600: setup_time = now

            # GC 1: Tempo de Vida (30s)
            is_stale = (now - setup_time > 30)
            
            # GC 2: Slippage Residual (Preço fugiu mais de 1.5 ATR)
            price_runaway = (abs(current_price - order_price) > atr * 1.5) if atr > 0 else False

            if is_stale or price_runaway:
                if ticket:
                    reason = "STALE" if is_stale else f"RUNAWAY({abs(current_price-order_price):.1f} pts)"
                    log.omega(f"🧹 GC: Cancelando ordem LIMIT #{ticket} - Reason: {reason}")
                    self.bridge.cancel_pending_order(ticket)
    def _cleanup_tracking(self, current_tickets: List[int]):
        """Remove estados de tickets que não existem mais."""
        closed = [t for t in list(self._positions_state.keys()) 
                  if t not in current_tickets and t not in self._closing_tickets]
        for t in closed:
            if t in self._positions_state: del self._positions_state[t]
            if t in self._close_attempt_time: del self._close_attempt_time[t]
            if t in self._last_nuke_log_time: del self._last_nuke_log_time[t]
        
        for t in list(self._closing_tickets):
            if t not in current_tickets:
                self._closing_tickets.remove(t)

    def _close_with_notify(self, ticket: int, direction: str):
        """Marca o ticket como fechando e dispara via pool paralela (Phase 44)."""
        if ticket in self._closing_tickets:
            return
            
        self._closing_tickets.add(ticket)
        self._close_attempt_time[ticket] = time.time()
        
        def _exec_close():
            result = self.bridge.close_position(ticket)
            
            # [Ω-AUDIT] Finalize Post-Mortem Capture
            from utils.audit_engine import AUDIT_ENGINE
            intent_data = trade_registry.get_intent(position_id=ticket)
            strike_id = intent_data.get("strike_id") if intent_data else None
            
            AUDIT_ENGINE.end_audit(ticket=ticket, result=result or {"ticket": ticket, "success": False}, strike_id=strike_id)

            if self._on_close_callback:
                try:
                    # [Phase 52 Fix] Pass the full result dict (containing profit/ticket)
                    # instead of just the direction string.
                    self._on_close_callback(result or {"ticket": ticket, "success": False})
                except Exception as e:
                    log.error(f"❌ Erro ao disparar callback de fechamento: {e}")

        # Disparo assíncrono para não travar o loop de monitoramento
        self._close_pool.submit(_exec_close)

    def close_all(self):
        """Emergency Panic Mode — fecha tudo instantaneamente."""
        self.bridge.close_all_positions()
        self._positions_state.clear()
        log.omega("💀 EMERGENCY CLOSE ALL — Todas as posições liquidadas.")
