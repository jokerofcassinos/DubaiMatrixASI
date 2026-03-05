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
        self._max_orders_per_candle = 5
        
        # ═══ ANTI-METRALHADORA: Previne re-entry no mesmo nível de preço ═══
        self._last_entry_price = 0.0          # Último preço de entrada
        self._last_entry_direction = None     # Última direção (BUY/SELL)
        self._last_entry_timestamp = 0        # Timestamp da última entrada (epoch seconds)
        self._min_entry_cooldown_s = 60       # Mínimo 60 segundos entre entradas
        self._min_price_distance_atr = 0.5    # Distância mínima: 0.5 ATR do último entry

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
        
        if self._orders_in_candle >= self._max_orders_per_candle:
            log.debug(f"Pausa tática: Limite de {self._max_orders_per_candle} ordens por candle atingido. Aguardando próximo minuto.")
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
        )

        # 3. Validação de risco
        approved, final_lot, reason = self.risk.validate_trade(
            balance, asi_state, lot_size
        )

        if not approved:
            log.warning(f"⚠️ Trade REJEITADO pelo Risk Engine: {reason}")
            return None

        # 4. EXECUTAR! (Order Split & Margin Check)
        max_slots = int(OMEGA.get("max_order_splits", 5))

        # 4.1. Pre-flight Slot Check (Evitar log spam quando limite atingido)
        from config.exchange_config import MAX_OPEN_POSITIONS
        current_positions = len(self.bridge.get_open_positions() or [])
        if current_positions + max_slots > MAX_OPEN_POSITIONS:
            # log silencioso em nível debug para não spamar
            log.debug(f"Pausa tática: Limite de posições ({MAX_OPEN_POSITIONS}) atingiria excesso com +{max_slots} slots.")
            return None
        
        # Calcular em quantos slots dividir
        lot_chunks = self._split_lot(final_lot, max_slots)
        
        # Verificar margem do lote total
        required_margin = self.bridge.calculate_margin(decision.action.value, final_lot, decision.entry_price)
        free_margin = account.get("free_margin", 0)
        
        if required_margin is not None:
            if required_margin > free_margin * 0.9: # 10% de folga
                log.error(f"❌ MARGEM INSUFICIENTE. Req: ${required_margin:.2f}, Livre: ${free_margin:.2f}")
                return None
        
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
