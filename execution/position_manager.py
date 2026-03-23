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
from config.exchange_config import MAGIC_NUMBER
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
        self._last_nuke_time = 0.0     # [Phase Ω-Resilience] Global cooldown tracker
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
            
            # [Phase Ω-SwingCrash] Metadata-Aware Relaxation
            intent = trade_registry.get_intent(position_id=anchor_ticket)
            custom_meta = (intent.get("custom_metadata") or {}) if intent else {}
            is_swing = custom_meta.get("is_swing_trade", False)
            is_crash = custom_meta.get("is_crash_sovereign", False)
            
            relaxation_mult = 1.0
            if is_swing:
                relaxation_mult *= OMEGA.get("swing_trailing_relaxation", 2.5)
            elif is_crash:
                relaxation_mult *= OMEGA.get("crash_trailing_relaxation", 2.0)
            
            if abs(total_profit - state.get("last_cached_profit", -999)) > 0.01:
                state["last_cached_profit"] = total_profit
                state["last_price_change_time"] = time.time()

            should_close = False
            reason = ""

            # ═══ [PHASE Ω-GREEN LIGHT] Lógica de Sinal Verde ═══
            # Prevenção de "Cortada na Fase de Captação": Não deixa o bot fechar por Trailing
            # se ainda não cobrimos a comissão com uma margem de segurança.
            comm_per_lot = snapshot.metadata.get("dynamic_commission_per_lot", 32.0)
            commission_cost = lot_scale * comm_per_lot
            
            # Sinal Verde: Profit > Comissão * Multiplicador
            green_light_mult = OMEGA.get("commission_protection_mult", 1.5)
            # Para Swing/Crash, somos ainda mais exigentes no sinal verde
            if is_swing or is_crash: green_light_mult *= 2.0
            
            has_green_light = total_profit > (commission_cost * green_light_mult)
            is_emergency = False # Será setado se for um trigger de urgência (Wormhole, etc)

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
            #  TRIGGER 1: DUAL-PHASE BREAKEVEN GUARD (Phase 7)
            # ═══════════════════════════════════════════════════
            # [Phase Ω-Fix] O piso seguro deve ser estritamente a comissão + minúscula folga.
            # Removido piso fixo de $15 que matava trades pequenos (0.01-0.10 lotes).
            safe_floor = max(commission_cost * 1.15, 1.0) # 15% de folga ou $1 min
            min_breakeven_activation = max(commission_cost * 2.0, 5.0)
            
            # Só armamos o BE via progresso (35% do TP) se o pico atual já permite pagar o safe_floor sem fechar na hora.
            can_activate_by_progress = (profit_progress > 0.35) and (state['peak_profit'] > safe_floor * 1.5)
            
            if not state.get("breakeven_active", False) and (can_activate_by_progress or state['peak_profit'] > min_breakeven_activation):
                state["breakeven_active"] = True
                log.omega(f"🛡️ [BREAKEVEN GUARD] Peak (${state['peak_profit']:.2f}) cobriu comissões ou alvo proxy. Real Breakeven armado no Strike #{anchor_ticket}.")

            if state.get("breakeven_active", False) and not is_proximity_zone:
                # NADA de sair com "10 dólares", sair com o peso exato da comissão + gordura para o spread da exchange.
                if total_profit <= safe_floor:
                    should_close = True
                    reason = f"TRUE_BREAKEVEN_PROTECTION (Fell to safe floor ${safe_floor:.2f})"

            # ═══════════════════════════════════════════════════
            #  TRIGGER 1.5: ATOMIC PROFIT DRAWDOWN LOCK (Trailing Multi-Tier)
            # ═══════════════════════════════════════════════════
            peak = state['peak_profit']
            atr_val = snapshot.atr if snapshot.atr > 0 else 50.0
            
            # Floor dinâmico macro
            target_net_profit_per_lot = OMEGA.get("min_profit_per_ticket", 25.0) 
            target_net_profit = lot_scale * target_net_profit_per_lot
            
            # [Phase Ω-SwingCrash] Scale floor for swing trades to prevent early T1/T2 activation
            if is_swing:
                target_net_profit *= OMEGA.get("swing_min_profit_mult", 10.0)
                
            dynamic_peak_floor = commission_cost + target_net_profit

            # Noise Shield Active: 1.5x do floor deve ser atingido antes de aceitar "ruído"
            reached_noise_shield = (total_profit >= dynamic_peak_floor * 1.5)

            # --- Multi-Tier Trailing Stop ---
            trailing_stop_profit = 0.0
            reason_prefix = ""
            phi_relax = 1.0 + (phi_val * OMEGA.get("smart_tp_phi_relaxation_mult", 0.5))

            if peak > dynamic_peak_floor:
                # Tier 2 e 3: O pico atingiu o topo! Acima do dynamic_peak_floor.
                if is_proximity_zone:
                    lock_threshold = OMEGA.get("proximity_lock_threshold", 0.05) * phi_relax * relaxation_mult
                    reason_prefix = "PROXIMITY_STRIKE"
                elif peak > dynamic_peak_floor * 2.0:
                    curvature_adj = max(0, climax_score - 2.5) * 0.03
                    lock_threshold = max(0.05, (0.25 - curvature_adj) * phi_relax * relaxation_mult) 
                    reason_prefix = f"RIEMANNIAN_TRAILING_STOP (T3{'[RELAX]' if relaxation_mult > 1 else ''})"
                elif peak > dynamic_peak_floor * 1.5:
                    curvature_adj = max(0, climax_score - 3.0) * 0.02
                    lock_threshold = max(0.05, (0.15 - curvature_adj) * phi_relax * relaxation_mult)
                    reason_prefix = f"RIEMANNIAN_TRAILING_STOP (T2{'[RELAX]' if relaxation_mult > 1 else ''})"
                else:
                    vol_mult = 1.0 if atr_val < 150 else 0.7 
                    lock_threshold = OMEGA.get("smart_tp_lock_threshold_low", 0.25) * vol_mult * phi_relax * relaxation_mult
                    reason_prefix = f"RIEMANNIAN_TRAILING_STOP (T1{'[RELAX]' if relaxation_mult > 1 else ''})"
                
                # Trava de Segurança Absoluta pós-floor (Nunca cai abaixo de 1.0x do floor)
                trailing_stop_profit = max(dynamic_peak_floor * 1.0, peak * (1.0 - lock_threshold))
                
            elif peak > commission_cost * 2.0:
                # Tier 1 (Early Trailing): O pico está entre as comissões x2 e o floor macro.
                # Escalonamento agressivo para lucro que ainda não atingiu o ideal, mas é significativo.
                # Retemos a comissão + buffer + 25% da gordura do topo.
                lock_value = commission_cost * 1.25 + (peak - commission_cost * 1.25) * 0.25
                trailing_stop_profit = lock_value
                reason_prefix = "EARLY_TRAILING_LOCK"

            if not should_close and trailing_stop_profit > 0.0 and total_profit <= trailing_stop_profit:
                # SÓ FECHA se tiver Sinal Verde OU se for o Breakeven Guard (Proteção de Capital)
                if has_green_light or state.get("breakeven_active", False):
                    should_close = True
                    reason = f"{reason_prefix} (Peak=${peak:.2f}, Locked=${trailing_stop_profit:.2f}, Progress={profit_progress:.1%})"
                else:
                    # Logando uma vez por strike para não spammar
                    if time.time() - self._last_nuke_log_time.get(anchor_ticket, 0) > 30.0:
                        log.omega(f"🛡️ [SOFT VETO] {reason_prefix} ignorado: Sem Sinal Verde (Profit ${total_profit:.2f} < Comm ${commission_cost:.2f} * {green_light_mult})")
                        self._last_nuke_log_time[anchor_ticket] = time.time()

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
                    if has_green_light: # Momentum Reversal é "Soft", respeita sinal verde
                        should_close, reason = True, "LETHAL_MOMENTUM_REVERSAL (Bearish)"
                elif not g_is_buy and flow_signal > 0.4:
                    if has_green_light:
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
                        
                        if is_flow_favorable or is_trend or is_swing or is_crash:
                            persistence = OMEGA.get("trend_persistence_buffer", 2.0)
                            if is_swing or is_crash: persistence *= 2.0 # Extra time for structural evolution
                            max_stag_time *= persistence # Damos mais tempo se a inércia ainda empurra ou regime é trend
                            
                        if stag_time >= max_stag_time:
                            label = f"{'SWING' if is_swing else 'CRASH' if is_crash else 'TIME'}_DECAY"
                            should_close, reason = True, f"{label}_LOCK ({stag_time:.1f}s below peak ${peak:.2f} | R={regime})"

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

                # ═══════════════════════════════════════════════════
                #  TRIGGER 8: DRIFT_TIME_EXHAUSTION (Phase 7.2)
                # ═══════════════════════════════════════════════════
                if not should_close:
                    regime = snapshot.regime.value if hasattr(snapshot.regime, 'value') else str(snapshot.regime)
                    if "DRIFTING" in regime or "CREEPING" in regime or "CHOPPY" in regime:
                        trade_age = time.time() - state["start_time"]
                        # Se a trade mofou por > 20 min (1200s) e já cobriu comissão, ejetamos.
                        if trade_age > 1200 and total_profit > commission_cost * 1.1:
                            should_close = True
                            reason = f"DRIFT_TIME_EXHAUSTION (Age={trade_age/60:.1f}m | Profit=${total_profit:.2f})"

            #  EJETAR GRUPO INTEIRO (STRIKE NUKE)
            if should_close:
                symbol = g_data.get('symbol', 'UNKNOWN')
                log.omega(f"💀 LETHAL BATCH CLOSE: {reason} | P&L Total: ${total_profit:+.2f} | Lots: {lot_scale:.2f} | Nodes: {num_slots}")
                # [Optimization Ω-1000%] Dispara fechamento em massa
                self.bridge.close_batch(symbol, "BUY" if g_is_buy else "SELL")
                self._last_nuke_time = time.time() # [Ω-Anti-Spam] Registra tempo do Nuke
                
                # Registra o fechamento no tracking local para não tentar de novo
                for p in g_tickets:
                    self._closing_tickets.add(p['ticket'])
                    self._close_attempt_time[p['ticket']] = time.time()

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

        # [Ω-RESILIENCE] Obter tempo do servidor para comparar com o tempo da ordem (Broker Time vs Broker Time)
        # O tick do socket retorna time.time() (local), o que quebra a comparação com o.time_setup (server).
        # Precisamos forçar a leitura do tempo do terminal via API nativa se possível.
        import MetaTrader5 as mt5
        now_server = time.time() # Fallback local
        
        if self.bridge.connected and mt5 is not None:
            last_tick = mt5.symbol_info_tick(self.bridge.symbol)
            if last_tick:
                now_server = last_tick.time
        
        for order in pending:
            ticket = order.get('ticket')
            
            # [Ω-FILTER] Apenas ordens deste bot (Sovereignty Check)
            if order.get('magic') != MAGIC_NUMBER:
                continue
                
            setup_time = order.get('time', now_server)
            order_price = order.get('price', 0.0)

            # GC 1: Tempo de Vida (60s Cooldown - Solicitado pelo CEO)
            # Se now_server < setup_time (fuso horário bizarro), age será negativo, e não cancela.
            # Se a diferença for muito grande, assumimos que é válida.
            age = now_server - setup_time
            
            # [Fix Timezone] Se a idade for negativa (Server Time vs Local Time mismatch extremo no fallback),
            # tentamos usar o time.time() local vs time local estimado.
            # Mas como mudamos now_server para ser Broker Time, isso deve resolver.
            
            is_stale = (age > 60)
            
            # GC 2: Slippage Residual (Preço fugiu mais de 1.5 ATR)
            price_runaway = (abs(current_price - order_price) > atr * 1.5) if (atr > 0 and order_price > 0) else False

            if age > 60:
                if is_stale or price_runaway:
                    if ticket:
                        reason = "STALE" if is_stale else f"RUNAWAY({abs(current_price-order_price):.1f} pts)"
                        log.omega(f"🧹 GC: Cancelando ordem LIMIT #{ticket} - Reason: {reason} | Age: {age:.1f}s")
                        self.bridge.cancel_pending_order(ticket)
    def _cleanup_tracking(self, current_tickets: List[int]):
        """Remove estados de tickets que não existem mais e detecta fechamentos automáticos (TP/SL)."""
        closed = [t for t in list(self._positions_state.keys()) 
                  if t not in current_tickets and t not in self._closing_tickets]
        
        for t in closed:
            # [Ω-AUDIT] Detecção de Ghost Closure (TP/SL via Corretora)
            # Se o ticket sumiu sem passar pelo set '_closing_tickets', foi fechado fora do bot.
            log.omega(f"👻 GHOST CLOSURE: Position #{t} sumiu do rastro (Broker TP/SL detected).")
            
            try:
                # 1. Recuperar resultado real via Histórico
                deals = self.bridge.get_deals_by_position(t)
                last_deal = deals[-1] if deals else None
                
                if last_deal:
                    result = {
                        "ticket": t,
                        "profit": last_deal.get("profit", 0.0),
                        "close_price": last_deal.get("price", 0.0),
                        "direction": last_deal.get("type", "UNKNOWN"),
                        "success": True,
                        "reason": "AUTO_EXIT_BROKER"
                    }
                else:
                    # Fallback caso o histórico falhe por lag
                    result = {"ticket": t, "profit": 0.0, "success": True, "reason": "AUTO_EXIT_BROKER_LAG"}
                
                # 2. Finalizar Auditoria com captura visual do momento da percepção
                from utils.audit_engine import AUDIT_ENGINE
                intent_data = trade_registry.get_intent(position_id=t)
                strike_id = intent_data.get("strike_id") if intent_data else None
                AUDIT_ENGINE.end_audit(ticket=t, result=result, strike_id=strike_id)
                
                # 3. Disparar callback se houver
                if self._on_close_callback:
                    self._on_close_callback(result)
                    
            except Exception as e:
                log.error(f"❌ Erro ao processar auditoria de ghost closure para #{t}: {e}")

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
