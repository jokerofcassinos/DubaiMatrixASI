"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — SNIPER EXECUTOR                       ║
║          Execução cirúrgica — precisão de milissegundo                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from typing import Optional
import os
import time
import concurrent.futures
from datetime import datetime, timezone

from core.decision.trinity_core import Decision, Action
from execution.risk_quantum import RiskQuantumEngine
from market.mt5_bridge import MT5Bridge
from concurrent.futures import ThreadPoolExecutor
from config.settings import ASIState, MAX_SLOTS_PER_CANDLE, EXECUTION_COOLDOWN_MS
from cpp.asi_bridge import CPP_CORE
import numpy as np

from config.omega_params import OMEGA
from config.exchange_config import MIN_LOT_SIZE
from utils.logger import log
from utils.decorators import retry, timed, catch_and_log


class SniperExecutor:
    """
    Executor Sniper — transforma decisões em ordens no MT5.

    Responsabilidades:
    1. Receber Decision do Trinity Core
    2. Validar risco via RiskQuantumEngine
    3. Calcular lot size ótimo
    4. Executar no MT5 com retry
    5. Confirmar execução
    """

    def __init__(self, bridge: MT5Bridge, risk_engine: RiskQuantumEngine):
        self.bridge = bridge
        self.risk = risk_engine
        self._execution_count = 0
        self._last_execution_time = None
        
        # Throttling por candle: evita infinite re-entry no mesmo candle
        self._current_candle_time = 0
        self._orders_in_candle = 0
        self._max_orders_per_candle = 2  # Phase 20: Reduzido de 5 → 2 (anti-metralhadora)
        
        # ═══ ANTI-METRALHADORA: Previne re-entry no mesmo nível de preço ═══
        self._last_entry_price = 0.0          # Último preço de entrada
        self._last_entry_direction = None     # Última direção (BUY/SELL)
        self._last_entry_timestamp = 0        # Timestamp da última entrada (epoch seconds)
        self._min_entry_cooldown_s = 60       # Mínimo 60 segundos entre entradas
        self._min_price_distance_atr = 0.3    # Distância mínima: 0.3 ATR do último entry
        
        # ═══ CANDLE DIRECTIONAL LOCK (Phase 20) ═══
        # Após executar numa direção, bloqueia re-entrada na MESMA direção
        # até o candle M1 atual fechar. Previne sell-TP-re-sell no mesmo candle.
        self._candle_direction_lock = None     # "BUY" ou "SELL" ou None
        self._candle_lock_time = 0             # Candle minute timestamp do lock
        self._post_close_direction = None      # Direção da última posição fechada
        self._post_close_candle_count = 0      # Candles passados desde o último close
        self._post_close_candle_time = 0       # Candle timestamp do close
        
        # Phase 40 — Ultra-Fast Execution Pool
        self._order_pool = ThreadPoolExecutor(max_workers=25)
        
        # OMEGA-CLASS: Sonar State
        self._last_sonar_time = 0
        self._sonar_cooldown_ms = 5000 # 5 segundos entre sondagens
        
        # [PHASE Ω-RESILIENCE] Log Cooldowns (Avoid spam)
        self._last_log_times = {} # key -> timestamp

    @timed(log_threshold_ms=400) # Phase 50: Elevado de 200ms para reduzir spam
    @catch_and_log(default_return=None)
    def execute(self, decision: Decision, asi_state: ASIState,
                snapshot) -> Optional[dict]:
        """
        Executa uma decisão de trading no MT5.
        """
        if decision.action == Action.WAIT:
            # Ativar Sonar se estivermos em WAIT mas com volatilidade interessante
            self._maybe_sonar_probe(snapshot)
            return None

        # 0. Throttle de Ordens por Candle (Impede metralhadora no mesmo candle)
        # Usar timestamp ms nativo do snapshot ou datetime local se ausente
        ts_ms = getattr(snapshot, "raw_timestamp", int(datetime.now(timezone.utc).timestamp() * 1000))
        current_minute = int(ts_ms / 60000) * 60000  # Arredonda ms para o minuto atual
        
        # OMEGA-CLASS: Acuidade sensorial - obter ATR uma única vez
        atr_values = snapshot.indicators.get("M5_atr_14")
        current_atr = float(atr_values[-1]) if atr_values is not None and len(atr_values) > 0 else 0
        
        if current_minute != self._current_candle_time:
            self._current_candle_time = current_minute
            self._orders_in_candle = 0
            # ═══ CANDLE DIRECTIONAL LOCK RESET ═══
            # Novo candle → liberar o lock direcional
            self._candle_direction_lock = None
            # Incrementar contador de candles pós-close
            if self._post_close_direction is not None:
                self._post_close_candle_count += 1
                if self._post_close_candle_count >= 2:  # 2 candles de cooldown pós-close
                    self._post_close_direction = None
                    self._post_close_candle_count = 0
        
        if self._orders_in_candle >= self._max_orders_per_candle:
            # [PHASE Ω-RESILIENCE] Log Cooldown
            now = time.time()
            if now - self._last_log_times.get("candle_limit", 0) > 60.0:
                log.debug(f"Pausa tática: Limite de {self._max_orders_per_candle} ordens por candle atingido. Aguardando próximo minuto.")
                self._last_log_times["candle_limit"] = now
            return None

        # ═══ CANDLE DIRECTIONAL LOCK CHECK (Phase 20) ═══
        # Se já executamos nessa direção NESTE candle → bloqueia
        if self._candle_direction_lock == decision.action.value:
            # [PHASE Ω-RESILIENCE] Log Cooldown
            now = time.time()
            if now - self._last_log_times.get("candle_lock", 0) > 30.0:
                log.debug(f"🔒 Candle Lock: já executou {decision.action.value} neste candle. Aguardando próximo.")
                self._last_log_times["candle_lock"] = now
            return None

        # ═══ POST-CLOSE DIRECTIONAL COOLDOWN (Phase 20) ═══
        # Após Smart TP fechar posição, bloqueia re-entrada na MESMA direção por 2 candles
        if self._post_close_direction == decision.action.value:
            # [PHASE Ω-RESILIENCE] Log Cooldown
            now = time.time()
            if now - self._last_log_times.get("post_close_cooldown", 0) > 30.0:
                log.debug(
                    f"⏸️ Post-Close Cooldown: aguardando {2 - self._post_close_candle_count} candle(s) "
                    f"antes de re-{decision.action.value}"
                )
                self._last_log_times["post_close_cooldown"] = now
            return None

        # ═══ ANTI-METRALHADORA PHASE 1: COOLDOWN TIMER ═══
        # Impede re-entry dentro de N segundos da última entrada
        cooldown_s = OMEGA.get("entry_cooldown_seconds")
        now_epoch = datetime.now(timezone.utc).timestamp()
        if self._last_entry_timestamp > 0:
            elapsed = now_epoch - self._last_entry_timestamp
            if elapsed < cooldown_s:
                # [PHASE Ω-RESILIENCE] Log Cooldown
                now = time.time()
                if now - self._last_log_times.get("metralhadora_time", 0) > 30.0:
                    log.debug(f"⏳ Anti-metralhadora: cooldown ativo ({elapsed:.0f}s/{cooldown_s:.0f}s)")
                    self._last_log_times["metralhadora_time"] = now
                return None

        # ═══ ANTI-METRALHADORA PHASE 2: DISTÂNCIA MÍNIMA DE PREÇO ═══
        # Impede entrada se o preço atual está muito próximo da última entrada
        # RESET: Se não há posições abertas, o ghost-block é irrelevante
        open_positions_check = self.bridge.get_open_positions() or []
        if not open_positions_check and self._last_entry_price > 0:
            self._last_entry_price = 0.0
            self._last_entry_direction = None
        
        min_dist_atr = OMEGA.get("min_entry_distance_atr")
        if self._last_entry_price > 0 and current_atr > 0:
            price_distance = abs(decision.entry_price - self._last_entry_price)
            min_distance = current_atr * min_dist_atr
            if price_distance < min_distance:
                # [PHASE Ω-RESILIENCE] Log Cooldown
                now = time.time()
                if now - self._last_log_times.get("metralhadora_dist", 0) > 30.0:
                    log.debug(
                        f"📏 Anti-metralhadora: preço muito próximo do último entry "
                        f"(dist={price_distance:.2f} < min={min_distance:.2f} [{min_dist_atr}×ATR])"
                    )
                    self._last_log_times["metralhadora_dist"] = now
                return None

        # ═══ ANTI-METRALHADORA PHASE 3: CONFLITO DIRECIONAL ═══
        # Impede abrir BUY se já tem BUY aberto no mesmo nível, e vice-versa
        dup_dist_atr = OMEGA.get("duplicate_position_distance_atr")
        open_positions = self.bridge.get_open_positions() or []
        if open_positions:
            for pos in open_positions:
                pos_type = pos.get("type", -1)  # 0=BUY, 1=SELL no MT5
                pos_price = pos.get("price_open", 0)
                pos_dir = "BUY" if pos_type == 0 else "SELL"
                
                # Se já temos posição na MESMA direção perto do mesmo preço → BLOQUEIA
                if pos_dir == decision.action.value and pos_price > 0 and current_atr > 0:
                    dist = abs(decision.entry_price - pos_price)
                    if dist < current_atr * dup_dist_atr:
                        # [PHASE Ω-RESILIENCE] Log Cooldown
                        now = time.time()
                        if now - self._last_log_times.get("metralhadora_dup", 0) > 30.0:
                            log.debug(
                                f"🚫 Anti-metralhadora: já existe {pos_dir} aberto @ {pos_price:.2f} "
                                f"(dist={dist:.2f} < {dup_dist_atr}×ATR={current_atr * dup_dist_atr:.2f})"
                            )
                            self._last_log_times["metralhadora_dup"] = now
                        return None


        # 1. Obter dados para sizing
        account = snapshot.account
        if not account:
            log.error("❌ Sem info de conta para sizing")
            return None

        balance = account.get("balance", 0)
        if balance <= 0:
            log.error("❌ Saldo zero")
            return None

        # 2. Calcular lot size via Risk Engine
        sl_distance = abs(decision.entry_price - decision.stop_loss)
        lot_size = self.risk.calculate_lot_size(
            balance=balance,
            stop_loss_distance=sl_distance,
            win_rate=asi_state.win_rate if asi_state.total_trades > 10 else 0.5,
            avg_win=max(1.0, asi_state.total_profit / max(1, asi_state.total_wins)),
            avg_loss=max(1.0, abs(asi_state.total_profit) / max(1, asi_state.total_losses)),
            symbol_info=snapshot.symbol_info,
            confidence=decision.confidence, # OMEGA Phase 22
            asi_state=asi_state,
            snapshot=snapshot,
        )

        # 3. Validação de risco
        approved, final_lot, reason = self.risk.validate_trade(
            balance, asi_state, lot_size
        )

        if not approved:
            log.warning(f"⚠️ Trade REJEITADO pelo Risk Engine: {reason}")
            return None

        # 4. EXECUTAR! (Order Split & Margin Check) (Phase 26: Hydra Execution)
        base_max_slots = int(OMEGA.get("max_order_splits", 5))
        
        # Hydra Logic: Multiplica os slots baseados na confiança e tipo de regime
        if decision.confidence > 0.85:
            # Extrema convicção (ex: gerada pelo Meta-Swarm) -> Ativar Hydra Mode
            hydra_multiplier = 3 
            if decision.regime in ["TRENDING_BULL", "TRENDING_BEAR", "SQUEEZE_BUILDUP"]:
                hydra_multiplier = 5 # Até 25 slots progressivos em modo demente
                
            max_slots = base_max_slots * hydra_multiplier
            
            # Libera a metralhadora temporariamente para esta vela
            self._max_orders_per_candle = 15
            
            # [PHASE Ω-RESILIENCE] Log Cooldown
            now = time.time()
            if now - self._last_log_times.get("hydra", 0) > 60.0:
                log.omega(f"🐉 HYDRA MODE ACTIVATED! Confidence {decision.confidence:.2f} > 0.85 | Max Slots: {max_slots} | Max Orders/Candle: 15")
                self._last_log_times["hydra"] = now
        else:
            max_slots = base_max_slots
            self._max_orders_per_candle = 2 # Default safety

        # 4.1. Pre-flight Slot Check & Dynamic Capping (Phase 39)
        from config.exchange_config import MAX_OPEN_POSITIONS
        current_positions = len(self.bridge.get_open_positions() or [])
        
        # Se os novos slots excederem o limite, capsulamos o excesso ao invés de ignorar o sinal
        if current_positions + max_slots > MAX_OPEN_POSITIONS:
            old_slots = max_slots
            max_slots = max(1, MAX_OPEN_POSITIONS - current_positions)
            
            # [PHASE Ω-RESILIENCE] Log Cooldown
            now = time.time()
            if now - self._last_log_times.get("slot_capping", 0) > 60.0:
                log.omega(f"📏 SLOT CAPPING (Phase 39): Ajustando de {old_slots} para {max_slots} slots para respeitar o limite global de {MAX_OPEN_POSITIONS}")
                self._last_log_times["slot_capping"] = now
            
            if max_slots <= 0:
                log.warning("❌ Limite de posições EXAURIDO. Não é possível abrir novas ordens.")
                return None
        
        # 4.2. Margin Check & Maximum Margin Extraction (Phase 37)
        required_margin = self.bridge.calculate_margin(decision.action.value, final_lot, decision.entry_price)
        free_margin = account.get("free_margin", 0)
        
        if required_margin is not None and free_margin > 0:
            if required_margin > free_margin * 0.9: # Se usa > 90% da margem livre, faz clawback
                old_lot = final_lot
                # Calcula o fator de redução para usar no máximo 95% da margem livre disponível
                scaling_factor = (free_margin * 0.95) / required_margin
                final_lot = final_lot * scaling_factor
                
                # Arredondar para o step do lote
                from config.exchange_config import LOT_STEP
                final_lot = round(final_lot / LOT_STEP) * LOT_STEP
                final_lot = max(MIN_LOT_SIZE, final_lot)
                
                # [PHASE Ω-RESILIENCE] Log Cooldown
                now = time.time()
                if now - self._last_log_times.get("margin_clawback", 0) > 60.0:
                    log.omega(
                        f"⚡ MARGIN CLAWBACK (Phase 37): Escalonando lote de {old_lot:.2f} para {final_lot:.2f} "
                        f"para caber na margem livre (${free_margin:.2f})"
                    )
                    self._last_log_times["margin_clawback"] = now
        
        # ═══════════════════════════════════════════════════════════
        #  PHASE Ω-ZERO: DO-CALCULUS CAUSAL GATEKEEPER
        # ═══════════════════════════════════════════════════════════
        if hasattr(CPP_CORE, 'calculate_causal_impact'):
            # Geramos uma matriz de features simplificada para o motor causal
            # Col 0: Volume, Col 1: Volatilidade, Col 2: Preço
            prices = snapshot.m1_closes
            if len(prices) > 20:
                feat_mat = np.column_stack([
                    snapshot.candles.get('M1', {}).get('tick_volume', np.zeros_like(prices))[-50:],
                    np.full(min(50, len(prices)), snapshot.indicators.get('M1_atr_14', [0.0])[-1]),
                    prices[-50:]
                ])
                
                causal = CPP_CORE.calculate_causal_impact(feat_mat, final_lot, target_index=2)
                if causal and causal['do_impact'] > 0.05: # Se nosso trade distorce > 5% do movimento
                    log.warning(f"⚠️ CAUSAL VETO: High Market Impact Projected ({causal['do_impact']:.2%})")
                    if causal['confidence'] > 0.7:
                        return None # Veto absoluto se a confiança no DAG for alta
        
        # ═══ PASSED ALL FILTERS: Log the actual realization of the decision ═══
        log.signal(f"🎯 DECISION: {decision.action.value} | {decision.reasoning}")

        # Iniciar execução de slots via Membrana P-Brane (Phase Ω-Transcendence)
        # Ao invés de blocos lineares rápidos, criamos uma rede fractal estendida (Brane)
        # [Phase Ω-Singularity] Automated Node Selection
        # Scale nodes based on total lot size to ensure each chunk is tradable and statistically significant.
        # $30k account / HFT context: each slot should ideally be > 0.05 lot.
        if final_lot < 0.1:
            target_nodes = 1
        elif final_lot < 0.5:
            target_nodes = min(3, max_slots)
        elif final_lot < 1.0:
            target_nodes = min(5, max_slots)
        else:
            target_nodes = min(10, max_slots)
            
        num_nodes = target_nodes # Use absolute count
        # Se for um único node, apenas envia. Se for múltiplos, gera a Brane
        if num_nodes <= 1:
            lot_chunks = [final_lot]
            delays = [0.0]
        else:
            # Distribuição P-Brane Estigmérgica: Combina Gaussiana com Feromônios Institucionais
            offsets = np.linspace(-2, 2, num_nodes)
            weights = np.exp(-(offsets**2) / 2.0)
            
            # [PHASE Ω-ASCENSION] Pheromone Routing (Stigmergy)
            # Lê o campo de atração do C++ no nível de preço atual
            if hasattr(CPP_CORE, 'read_pheromones'):
                try:
                    ph_field = CPP_CORE.read_pheromones(decision.entry_price, num_nodes)
                    if ph_field is not None and len(ph_field) == num_nodes:
                        # Modula o peso gaussiano com a densidade do feromônio institucional
                        ph_weights = np.array(ph_field)
                        if np.sum(ph_weights) > 0:
                            ph_weights /= np.sum(ph_weights)
                            # Mistura 60% Gaussiana natural, 40% Foco de Atração Institucional
                            weights = (weights * 0.6) + (ph_weights * 0.4)
                except Exception as e:
                    log.debug(f"Pheromone read error: {e}")
            
            # [PHASE Ω-TRANSCENDENCE] P-Brane Execution (Gaussian Cloud)
            # Ao invés de um ponto fixo, distribuímos em uma 'Brane' topológica
            jitter_atr = current_atr * 0.05 if current_atr > 0 else 2.0 # 5% do ATR ou 2 points BTC
            offsets = np.random.normal(0, jitter_atr, num_nodes)
            
            # Ordenar offsets para evitar overlaps de ordens limites se possível
            offsets = np.sort(offsets)
            
            lot_chunks = [max(MIN_LOT_SIZE, round(final_lot / num_nodes, 2)) for _ in range(num_nodes)]
            # Ajuste de resíduo
            diff = final_lot - sum(lot_chunks)
            if abs(diff) > 0.01:
                lot_chunks[0] = max(MIN_LOT_SIZE, round(lot_chunks[0] + diff, 2))
            
            # Micro-delays camaleônicos (Anti-HFT Footprint)
            delays = [abs(np.random.normal(0.03, 0.01)) for _ in range(num_nodes)]
            
        log.omega(
            f"⚡ EXECUTING P-BRANE {decision.action.value} "
            f"lot={final_lot:.2f} (em {num_nodes} nodes) "
            f"price={decision.entry_price:.2f} "
            f"SL={decision.stop_loss:.2f} TP={decision.take_profit:.2f}"
        )

        # 4.3. Parallel Order Dispatch (Phase 40/42)
        # Obter preço uma única vez para o burst
        current_tick = self.bridge.get_tick()
        if not current_tick:
            log.error("❌ Falha crítica: Impossível obter tick para execução HFT")
            return None
            
        entry_price = current_tick["ask"] if decision.action.value == "BUY" else current_tick["bid"]

        def _send_slot(i, chunk_lot, delay_sec):
            if delay_sec > 0:
                time.sleep(delay_sec)
                
            # [Phase Ω-Singularity] P-Brane Execution Logic
            # Switches between Maker (Limit) and Taker (Market) based on metadata
            use_limit = decision.metadata.get("limit_execution", False)
            
            if use_limit:
                # Maker Logic: Position orders at/near the spread boundaries
                tick_bid = current_tick["bid"]
                tick_ask = current_tick["ask"]
                spread = tick_ask - tick_bid
                
                # [QUANTUM JITTER] Adaptive Noise Injection
                # Using p_brane_jitter_offset_points from metadata (calibrated by Trinity EPA)
                jitter_points = decision.metadata.get("jitter_offset", 0.0)
                # Random factor: +/- 50% of the jitter setting
                random_jitter = jitter_points * (0.5 + np.random.random())
                jitter_price = random_jitter * snapshot.symbol_info.get("point", 0.0001)
                
                if decision.action.value == "BUY":
                    # Buy Limit must be <= Bid
                    limit_price = min(tick_bid, tick_bid + (np.linspace(-1.5, -0.1, num_nodes)[i] * spread))
                    limit_price -= jitter_price # Push slightly deeper into the book
                else:
                    # Sell Limit must be >= Ask
                    limit_price = max(tick_ask, tick_ask + (np.linspace(0.1, 1.5, num_nodes)[i] * spread))
                    limit_price += jitter_price # Push slightly higher

                return self.bridge.send_limit_order(
                    action=decision.action.value,
                    lot=chunk_lot,
                    sl=decision.stop_loss,
                    tp=decision.take_profit,
                    comment=f"ASI_MAKER_{i+1}/{num_nodes}",
                    price=limit_price
                )
            else:
                # Taker Logic: Aggressive Market Order (Phase 40 priority)
                return self.bridge.send_market_order(
                    action=decision.action.value,
                    lot=chunk_lot,
                    sl=decision.stop_loss,
                    tp=decision.take_profit,
                    comment=f"ASI_TAKER_{i+1}/{num_nodes}"
                )


        # Mapeamento paralelo via ThreadPool com delays P-Brane
        futures = [self._order_pool.submit(_send_slot, i, lot, delays[i]) for i, lot in enumerate(lot_chunks)]
        
        results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                res = future.result(timeout=5.0) # Aumentar timeout para suportar rede lenta
                if res and res.get("success"):
                    results.append(res)
                else:
                    log.error(f"❌ Falha ao executar slot")
            except Exception as e:
                log.error(f"❌ Exceção no disparo do slot: {e}")

        if not results:
            log.error("❌ Execução falhou: todas as tentativas retornaram erro no MT5")
            return None

        # 5. Sucesso!
        self._execution_count += 1
        self._orders_in_candle += 1  # Incrementa o contador do throttle por candle
        self._last_execution_time = datetime.now(timezone.utc)
        
        # ═══ ANTI-METRALHADORA: Registrar última entrada ═══
        self._last_entry_price = decision.entry_price
        self._last_entry_direction = decision.action.value
        self._last_entry_timestamp = datetime.now(timezone.utc).timestamp()
        
        # ═══ CANDLE DIRECTIONAL LOCK: Ativar lock ═══
        self._candle_direction_lock = decision.action.value

        # Atualizar peak balance
        if balance > asi_state.peak_balance:
            asi_state.peak_balance = balance

        # Cálculo robusto com base nos resultados reais
        total_executed_lot = sum(r.get("volume", 0) for r in results)
        if total_executed_lot > 0:
            avg_price = sum(r.get("price", 0) * r.get("volume", 0) for r in results) / total_executed_lot
        else:
            avg_price = decision.entry_price

        log.omega(
            f"✅ TRADE EXECUTADO #{self._execution_count} | "
            f"{decision.action.value} lot={total_executed_lot:.2f} "
            f"@ {avg_price:.2f} | "
            f"{len(results)} tickets gerados | "
            f"{decision.reasoning[:80]}"
        )

        return {
            "success": True,
            "tickets": [r.get("ticket") for r in results],
            "price": avg_price,
            "lot": total_executed_lot,
            "action": decision.action.value,
            "sl": decision.stop_loss,
            "tp": decision.take_profit,
            "reasoning": decision.reasoning,
        }

    def _maybe_sonar_probe(self, snapshot):
        """
        Executa uma 'Sonda Sonar' se as condições de mercado permitirem.
        O objetivo é perturbar o book para detectar liquidez oculta.
        """
        now_ms = int(time.time() * 1000)
        if now_ms - self._last_sonar_time < self._sonar_cooldown_ms:
            return

        # Condição: Volatilidade alta mas sem sinal claro
        atr = snapshot.indicators.get("M1_atr_14", [0])[0]
        if atr <= 0: return
        
        # O Sonar é uma ordem limite MIN_LOT a 1 tick de distância do preço real
        # que é cancelada em 50ms (pelo EA).
        self._last_sonar_time = now_ms
        
        # Usar paridade do tempo ou waves do reservatório para decidir o lado
        waves = snapshot.metadata.get("reservoir_waves", [0.5])
        side = "BUY" if waves[0] > 0 else "SELL"
        
        # Preço: 1 ponto de distância do bid/ask
        point = snapshot.symbol_info.get("point", 0.0001) if snapshot.symbol_info else 0.0001
        price = (snapshot.tick["ask"] + point) if side == "BUY" else (snapshot.tick["bid"] - point)
        
        # [PHASE Ω-RESILIENCE] Log Cooldown
        now_s = time.time()
        if now_s - self._last_log_times.get("sonar", 0) > 30.0:
            log.omega(f"📡 QUANTUM SONAR: Probing {side} liquidity @ {price:.2f}")
            self._last_log_times["sonar"] = now_s
        self.bridge.send_sonar_probe(side=side, lot=MIN_LOT_SIZE, price=price, duration_ms=50)

    def _split_lot(self, total_lot: float, max_splits: int) -> list:
        """Divide o lote total em N chunks para permitir parciais."""
        import math
        
        if total_lot < MIN_LOT_SIZE * 2:
            return [total_lot]
            
        splits = min(max_splits, int(total_lot / MIN_LOT_SIZE))
        if splits <= 1:
            return [total_lot]
            
        chunk = round(total_lot / splits, 2)
        # Garantir chunk minimo
        if chunk < MIN_LOT_SIZE:
             chunk = MIN_LOT_SIZE
             splits = int(total_lot / chunk)
             
        chunks = [chunk] * (splits - 1)
        # O último slot pega o resto para não ter erro de arredondamento
        last_chunk = round(total_lot - sum(chunks), 2)
        if last_chunk >= MIN_LOT_SIZE:
            chunks.append(last_chunk)
        else:
            chunks[-1] += last_chunk
            
        return [round(c, 2) for c in chunks]

    @property
    def stats(self) -> dict:
        return {
            "total_executions": self._execution_count,
            "last_execution": (
                self._last_execution_time.isoformat()
                if self._last_execution_time else None
            ),
        }
