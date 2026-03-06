"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — SNIPER EXECUTOR                       ║
║          Execução cirúrgica — precisão de milissegundo                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from typing import Optional
from datetime import datetime, timezone

from core.decision.trinity_core import Decision, Action
from execution.risk_quantum import RiskQuantumEngine
from market.mt5_bridge import MT5Bridge
from config.settings import ASIState
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

    @timed(log_threshold_ms=500)
    @catch_and_log(default_return=None)
    def execute(self, decision: Decision, asi_state: ASIState,
                snapshot) -> Optional[dict]:
        """
        Executa uma decisão de trading no MT5.
        """
        if decision.action == Action.WAIT:
            return None

        # 0. Throttle de Ordens por Candle (Impede metralhadora no mesmo candle)
        # Usar timestamp ms nativo do snapshot ou datetime local se ausente
        ts_ms = getattr(snapshot, "raw_timestamp", int(datetime.now(timezone.utc).timestamp() * 1000))
        current_minute = int(ts_ms / 60000) * 60000  # Arredonda ms para o minuto atual
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
            log.debug(f"Pausa tática: Limite de {self._max_orders_per_candle} ordens por candle atingido. Aguardando próximo minuto.")
            return None

        # ═══ CANDLE DIRECTIONAL LOCK CHECK (Phase 20) ═══
        # Se já executamos nessa direção NESTE candle → bloqueia
        if self._candle_direction_lock == decision.action.value:
            log.debug(f"🔒 Candle Lock: já executou {decision.action.value} neste candle. Aguardando próximo.")
            return None

        # ═══ POST-CLOSE DIRECTIONAL COOLDOWN (Phase 20) ═══
        # Após Smart TP fechar posição, bloqueia re-entrada na MESMA direção por 2 candles
        if self._post_close_direction == decision.action.value:
            log.debug(
                f"⏸️ Post-Close Cooldown: aguardando {2 - self._post_close_candle_count} candle(s) "
                f"antes de re-{decision.action.value}"
            )
            return None

        # ═══ ANTI-METRALHADORA PHASE 1: COOLDOWN TIMER ═══
        # Impede re-entry dentro de N segundos da última entrada
        cooldown_s = OMEGA.get("entry_cooldown_seconds")
        now_epoch = datetime.now(timezone.utc).timestamp()
        if self._last_entry_timestamp > 0:
            elapsed = now_epoch - self._last_entry_timestamp
            if elapsed < cooldown_s:
                log.debug(f"⏳ Anti-metralhadora: cooldown ativo ({elapsed:.0f}s/{cooldown_s:.0f}s)")
                return None

        # ═══ ANTI-METRALHADORA PHASE 2: DISTÂNCIA MÍNIMA DE PREÇO ═══
        # Impede entrada se o preço atual está muito próximo da última entrada
        # RESET: Se não há posições abertas, o ghost-block é irrelevante
        open_positions_check = self.bridge.get_open_positions() or []
        if not open_positions_check and self._last_entry_price > 0:
            self._last_entry_price = 0.0
            self._last_entry_direction = None
        
        min_dist_atr = OMEGA.get("min_entry_distance_atr")
        if self._last_entry_price > 0:
            atr_values = snapshot.indicators.get("M5_atr_14")
            current_atr = float(atr_values[-1]) if atr_values is not None and len(atr_values) > 0 else 0
            if current_atr > 0:
                price_distance = abs(decision.entry_price - self._last_entry_price)
                min_distance = current_atr * min_dist_atr
                if price_distance < min_distance:
                    log.debug(
                        f"📏 Anti-metralhadora: preço muito próximo do último entry "
                        f"(dist={price_distance:.2f} < min={min_distance:.2f} [{min_dist_atr}×ATR])"
                    )
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
                if pos_dir == decision.action.value and pos_price > 0:
                    atr_values = snapshot.indicators.get("M5_atr_14")
                    current_atr = float(atr_values[-1]) if atr_values is not None and len(atr_values) > 0 else 0
                    if current_atr > 0:
                        dist = abs(decision.entry_price - pos_price)
                        if dist < current_atr * dup_dist_atr:
                            log.debug(
                                f"🚫 Anti-metralhadora: já existe {pos_dir} aberto @ {pos_price:.2f} "
                                f"(dist={dist:.2f} < {dup_dist_atr}×ATR={current_atr * dup_dist_atr:.2f})"
                            )
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
            log.omega(f"🐉 HYDRA MODE ACTIVATED! Confidence {decision.confidence:.2f} > 0.85 | Max Slots: {max_slots} | Max Orders/Candle: 15")
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
            log.omega(f"📏 SLOT CAPPING (Phase 39): Ajustando de {old_slots} para {max_slots} slots para respeitar o limite global de {MAX_OPEN_POSITIONS}")
            
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
                
                log.omega(
                    f"⚡ MARGIN CLAWBACK (Phase 37): Escalonando lote de {old_lot:.2f} para {final_lot:.2f} "
                    f"para caber na margem livre (${free_margin:.2f})"
                )
        
        # Calcular em quantos slots dividir o lote final (ajustado ou não)
        lot_chunks = self._split_lot(final_lot, max_slots)
        
        log.omega(
            f"⚡ EXECUTING {decision.action.value} "
            f"lot={final_lot:.2f} (em {len(lot_chunks)} slots) "
            f"price={decision.entry_price:.2f} "
            f"SL={decision.stop_loss:.2f} TP={decision.take_profit:.2f}"
        )

        results = []
        for i, chunk_lot in enumerate(lot_chunks):
            # TP progressivo opcional: se ativado, distribui os TPs dos slots
            tp_price = decision.take_profit
            
            res = self.bridge.send_market_order(
                action=decision.action.value,
                lot=chunk_lot,
                sl=decision.stop_loss,
                tp=tp_price,
                comment=f"ASI_{decision.regime[:5]}_{i+1}/{len(lot_chunks)}",
            )
            
            if res and res.get("success"):
                results.append(res)
            else:
                log.error(f"❌ Falha ao executar slot {i+1}")

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

        avg_price = sum(r.get("price", 0) * r.get("volume", chunk_lot) for r in results) / sum(r.get("volume", chunk_lot) for r in results)
        total_executed_lot = sum(r.get("volume", chunk_lot) for r in results)

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
