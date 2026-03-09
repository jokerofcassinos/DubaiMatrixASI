"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — ASI BRAIN                             ║
║         O Cérebro Central — Orquestra toda a consciência                    ║
║                                                                              ║
║  Ciclo: Percepção → Análise → Deliberação → Decisão → Ação → Reflexão     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import time
from datetime import datetime, timezone, timedelta
from typing import Optional
import subprocess
import socket
import threading

from market.mt5_bridge import MT5Bridge
from market.data_engine import DataEngine, MarketSnapshot
from market.orderflow_matrix import OrderFlowMatrix
from market.scraper.sentiment_scraper import SentimentScraper
from market.scraper.onchain_scraper import OnChainScraper
from market.scraper.macro_scraper import MacroScraper
from core.consciousness.neural_swarm import NeuralSwarm
from core.consciousness.quantum_thought import QuantumThoughtEngine
from core.consciousness.regime_detector import RegimeDetector
from market.memory.episodic_memory import EpisodicMemory
from market.scraper.narrative_distiller import EdgeLLMDistiller
from core.decision.trinity_core import TrinityCore, Action, Decision
from core.evolution.performance_tracker import PerformanceTracker
from core.evolution.self_optimizer import SelfOptimizer
from execution.trade_registry import registry as trade_registry
from execution.risk_quantum import RiskQuantumEngine
from execution.sniper_executor import SniperExecutor
from execution.position_manager import PositionManager
from execution.shadow_predator import ShadowPredatorEngine
from config.settings import ASIState, CONSCIOUSNESS_CYCLE_MS
from config.omega_params import OMEGA
from utils.logger import log
from utils.decorators import timed, catch_and_log, ast_self_heal


class ASIBrain:
    """
    Cérebro Central da ASI — orquestra todos os setores.

    Ciclo de consciência:
    1. PERCEPÇÃO  — DataEngine coleta dados do mercado
    2. ANÁLISE    — NeuralSwarm analisa com milhares de agentes
    3. DELIBERAÇÃO — QuantumThought converge sinais
    4. DECISÃO    — TrinityCore decide BUY/SELL/WAIT
    5. AÇÃO       — SniperExecutor executa no MT5
    6. REFLEXÃO   — Auto-evolução e registro de performance
    """

    def __init__(self, bridge: MT5Bridge):
        self.bridge = bridge

        # ═══ SETORES DE CONSCIÊNCIA ═══
        self.data_engine = DataEngine(bridge)
        self.orderflow = OrderFlowMatrix()
        
        # ═══ PHASE 3: EPISODIC MEMORY (Market Intuition) ═══
        self.memory = EpisodicMemory(vector_dim=64)
        
        # ═══ PHASE 4: ADVERSARIAL COUNTER-AI ═══
        self.predator_engine = ShadowPredatorEngine()
        
        self.regime_detector = RegimeDetector()
        self.neural_swarm = NeuralSwarm(memory=self.memory, predator_engine=self.predator_engine)
        self.quantum_thought = QuantumThoughtEngine()
        
        self.trinity_core = TrinityCore()
        
        self.risk_engine = RiskQuantumEngine()
        
        # ═══ PHASE 5: EDGE LLM DISTILLATION ═══
        self.llm_distiller = EdgeLLMDistiller()
        
        self.executor = SniperExecutor(bridge, self.risk_engine)
        
        # Callback para Anti-Metralhadora Pós-Close
        def on_position_closed(direction: str):
            self.executor._post_close_direction = direction
            self.executor._post_close_candle_count = 0
            
        self.position_manager = PositionManager(bridge, on_close_callback=on_position_closed)

        # ═══ PHASE 5: WEB SCRAPERS (Zero-Cost External Intelligence) ═══
        self.sentiment_scraper = SentimentScraper()
        self.onchain_scraper = OnChainScraper()
        self.macro_scraper = MacroScraper()

        # ═══ PHASE 5: SELF-EVOLUTION ═══
        self.performance_tracker = PerformanceTracker()
        self.self_optimizer = SelfOptimizer(self.performance_tracker)

        # ═══ ESTADO DA ASI ═══
        self.state = ASIState()
        self.state.load()  # Carregar estado anterior

        # Contadores
        self._cycle_count = 0
        self._last_snapshot = None
        self._last_pnl_prediction = "STABLE"
        self._last_log_times = {} # key -> float
        self._history_synced = False # [Phase Ω-Darwin]
        self._reflection_interval = 5      # [Phase Ω-Darwin] 5s p/ Sincronização de Histórico
        self._last_reflection_time = time.time()
        
        # [Phase 40] Self-Optimizer Patch
        self._evolution_cycle_count = 0
        self._evolution_check_interval = 200 # Ciclos p/ rodar otimizador
        # [Phase Ω-Darwin] Sincronização inicial: auditar os últimos 7 dias para garantir histórico completo
        self._last_history_poll = time.time() - (86400 * 7) 

        # Iniciar Scrapers em background
        self.sentiment_scraper.start()
        self.onchain_scraper.start()
        self.macro_scraper.start()
        
        # Iniciar Java PnLPredictor
        self.java_daemon = None
        try:
            self.java_daemon = subprocess.Popen(
                ["java", "-cp", "d:\\DubaiMatrixASI\\java\\bin", "com.dubaimatrix.PnLPredictor"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            log.omega("☕ Java Enterprise PnLPredictor INICIADO (Daemon na porta 5556)")
        except Exception as e:
            log.warning(f"⚠️ Falha ao iniciar Java Daemon: {e}")

        log.omega(f"🧠 Neural Swarm inicializado: {len(self.neural_swarm.agents)} agentes ativos")
        log.omega("🧠 ASI BRAIN ONLINE — Todos os setores neurais ativados")

    @timed(log_threshold_ms=1000)
    @ast_self_heal
    @catch_and_log(default_return=None)
    def think(self) -> Optional[dict]:
        """
        UM CICLO DE PENSAMENTO COMPLETO.
        Chamado pelo loop principal a cada CONSCIOUSNESS_CYCLE_MS.
        """
        self._cycle_count += 1

        # ═══ 1. PERCEPÇÃO — Coletar dados ═══
        snapshot = self.data_engine.update()
        if snapshot is None:
            return {"cycle": self._cycle_count, "action": "NO_DATA"}

        self._last_snapshot = snapshot

        # ═══ 2. ANÁLISE DE ORDER FLOW ═══
        ticks = self.bridge.get_ticks_range(30)  # Últimos 30s
        flow_analysis = {}
        if ticks:
            flow_analysis = self.orderflow.analyze_ticks(ticks)

        book = snapshot.book
        book_analysis = {}
        if book:
            book_analysis = self.orderflow.analyze_book(book)
            flow_analysis.update(book_analysis)

        # ═══ 3. DETECÇÃO DE REGIME ═══
        regime_state = self.regime_detector.detect(snapshot)

        # ═══ 4. INTELIGÊNCIA EXTERNA — Scrapers ═══
        snapshot.metadata["sentiment_score"] = self.sentiment_scraper.sentiment_score
        snapshot.metadata["network_pressure"] = self.onchain_scraper.network_pressure
        snapshot.metadata["macro_bias"] = self.macro_scraper.macro_bias
        snapshot.metadata["pnl_prediction"] = self._last_pnl_prediction
        snapshot.metadata["dynamic_commission_per_lot"] = OMEGA.get("commission_per_lot", 32.0)

        # ═══ 5. ANÁLISE NEURAL — Enxame de agentes ═══
        agent_signals = self.neural_swarm.analyze(snapshot, flow_analysis, regime_state=regime_state)

        # ═══ 4. COLAPSO QUÂNTICO (Matematização da Consciência) ═══
        regime_aggression = regime_state.aggression_multiplier if regime_state else 1.0
        quantum_state = self.quantum_thought.process(
            agent_signals,
            snapshot=snapshot,
            regime_weight=regime_aggression,
            v_pulse_detected=snapshot.metadata.get("v_pulse_detected", False)
        )

        # ═══ 6. DECISÃO — Trinity Core ═══
        decision = self.trinity_core.decide(
            quantum_state, regime_state, snapshot, self.state
        )

        result = {
            "cycle": self._cycle_count,
            "action": decision.action.value if decision else "NONE",
            "signal": quantum_state.raw_signal if quantum_state else 0,
            "coherence": quantum_state.coherence if quantum_state else 0,
            "regime": regime_state.current.value if regime_state else "UNKNOWN",
            "agents_active": len(agent_signals),
            "reasoning": decision.reasoning if decision else "",
        }

        # ═══ 7. EXECUÇÃO — Se não é WAIT ═══
        if decision and decision.action != Action.WAIT:
            # [Phase Ω-Singularity] Pending Order Veto: Evita duplicar ignição se já houver LIMIT pendente
            pending = self.bridge.get_pending_orders()
            already_pending = False
            if pending:
                for po in pending:
                    po_type = "BUY" if "BUY" in po['type'] else "SELL"
                    if po_type == decision.action.value:
                        already_pending = True
                        break
            
            # [Phase Ω-Resilience] Ignition Cooldown: Evita spam de tentativas se o mercado estiver 'fast'
            now = time.time()
            cooldown = OMEGA.get("entry_cooldown_seconds", 60.0)
            last_ign = self._last_log_times.get(f"ign_{decision.action.value}", 0.0)
            
            if already_pending:
                if now - self._last_log_times.get("ign_bypass", 0) > 30:
                    log.debug(f"⏳ IGNITION Bypassed: Ordem {decision.action.value} já pendente no book.")
                    self._last_log_times["ign_bypass"] = now
            elif now - last_ign >= 5.0: # Cooldown mínimo de 5s entre tentativas de disparo
                # 5. EXECUÇÃO (Sniper Strike)
                # [PHASE 48] EXECUTION ATTRIBUTE FIX
                # O executor é instanciado como self.executor, mas o loop chamava self.sniper
                execution_result = None
                if hasattr(self, "executor") and snapshot and decision:
                    execution_result = self.executor.execute(decision, self.state, snapshot)
                elif hasattr(self, "sniper") and snapshot and decision:
                    execution_result = self.sniper.execute(decision, self.state, snapshot)
                
                if execution_result and execution_result.get("success"):
                    # [Phase 48] Dubai-Grade Ignition Observability
                    phi_val = decision.metadata.get("phi", 0.0)
                    ignite_badge = "🚀 [V-PULSE IGNITION]" if snapshot.metadata.get("v_pulse_detected") else "🎯 [SNIPER STRIKE]"
                    
                    log.omega(
                        f"{ignite_badge} SUCCESS: {decision.action.value} {snapshot.symbol} | "
                        f"lots={execution_result.get('lot'):.2f} @ {execution_result.get('price'):.2f} | "
                        f"Φ={phi_val:.2f} | CONF={decision.confidence:.2f} | "
                        f"REGIME={decision.regime}"
                    )
                    
                    self.state.last_trade_time = datetime.now(timezone.utc)
                    self._last_log_times[f"ign_{decision.action.value}"] = now
                    result["executed"] = True
                    result["ticket"] = execution_result.get("ticket")
                    result["price"] = execution_result.get("price")
                    
                    # [PHASE 52] 🎯 PREMIUM IGNITION LOG (Full Detail)
                    bull_agents = quantum_state.metadata.get("bull_agents", [])
                    bear_agents = quantum_state.metadata.get("bear_agents", [])
                    bull_str = ", ".join(bull_agents) if bull_agents else "None"
                    bear_str = ", ".join(bear_agents) if bear_agents else "None"
                    
                    log.omega(
                        f"🎯 IGNITION SUCCESS: {decision.action.value} {snapshot.symbol} | "
                        f"S={quantum_state.raw_signal:+.3f} PHI={quantum_state.phi:.2f}\n"
                        f"  🐂 BULL[{len(bull_agents)}]: {bull_str}\n"
                        f"  🐻 BEAR[{len(bear_agents)}]: {bear_str}\n"
                        f"  🎯 Reason: {decision.reasoning}"
                    )

        # ═══ 8. MONITORAR POSIÇÕES ABERTAS (POSITION MANAGER / SMART TP) ═══
        self.position_manager.monitor_positions(snapshot, flow_analysis)

        # ═══ 8B. GRAVAR MEMÓRIA EPISÓDICA (a cada 60 ciclos) ═══
        if self._cycle_count % 60 == 0:
            # Geramos o embedding usando o agente de intuição
            intuition_agent = self.neural_swarm.get_agent_by_name("MarketIntuition")
            if intuition_agent:
                embedding = intuition_agent._generate_embedding(snapshot, flow_analysis)
                # O outcome será preenchido pelo PerformanceTracker futuramente, 
                # aqui gravamos o estado com o preço atual.
                self.memory.add_episode(embedding, {"price": snapshot.price, "time": snapshot.timestamp})

        # ═══ 9. AUTO-EVOLUÇÃO (a cada 200 ciclos) ═══
        if self._cycle_count % 200 == 0:
            self.self_optimizer.check_and_optimize(self._cycle_count, snapshot)

        # ═══ 10. PERSISTIR ESTADO (a cada 100 ciclos) ═══
        if self._cycle_count % 100 == 0:
            self.state.save()
            OMEGA.save()

        # ═══ 11. JAVA ENTERPRISE PNL PREDICTOR (Phase 25) ═══
        if self._cycle_count % 250 == 0:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1.0)
                    s.connect(('127.0.0.1', 5556))
                    
                    win_rate = self.state.win_rate if self.state.total_trades > 10 else 0.5
                    
                    # Se não temos histórico suficiente, assumimos um R:R base promissor para não enviesar em 0
                    if self.state.total_wins > 0:
                        avg_win = max(0.01, self.state.gross_profit / self.state.total_wins)
                    else:
                        avg_win = max(0.01, snapshot.price * 0.002) # Ex: 0.2% de move como estimativa

                    if self.state.total_losses > 0:
                        avg_loss = max(0.01, self.state.gross_loss / self.state.total_losses)
                    else:
                        avg_loss = max(0.01, snapshot.price * 0.001) # Ex: 0.1% de move como estimativa
                    
                    account_balance = snapshot.account.get("balance", 0.0) if snapshot.account else 0.0
                    is_relaxed = "true" if self.self_optimizer._is_relaxed_mode else "false"
                    msg = f"UPDATE:{account_balance}:{win_rate}:{avg_win}:{avg_loss}:{is_relaxed}\n"
                    s.sendall(msg.encode('utf-8'))
                    
                    resp = s.recv(1024).decode('utf-8').strip()
                    if resp.startswith("ACK:"):
                        prediction = resp.split("ACK:")[1]
                        self._last_pnl_prediction = prediction
                        
                        now = time.time()
                        if now - self._last_log_times.get("pnl_pred", 0) > 60.0:
                            if "RELAXED" in prediction:
                                log.omega(f"🥂 [RELAXED MODE] PnL Predictor: {prediction}")
                            elif "WARNING" in prediction:
                                log.warning(f"⚠️ [PNL WARNING] {prediction}")
                            else:
                                log.omega(f"🔮 [JAVA PnL PREDICTOR] {prediction}")
                            self._last_log_times["pnl_pred"] = now
            except Exception as e:
                log.debug(f"Pausa tática: Java PnL Predictor indisponível - {e}")
            # ═══ [PHASE Ω-TRANSCENDENCE] WORMHOLE RECOVERY ═══
            # Se posições existentes estão em perigo, tentamos o Gamma Hedge
            positions = self.bridge.get_open_positions() or []
            for pos in positions:
                recovery_strike = self.risk_engine.evaluate_wormhole_trigger(pos, snapshot)
                if recovery_strike:
                    # Executar hedge via Sniper
                    rec_decision = Decision(
                        action=Action.BUY if recovery_strike["action"] == "BUY" else Action.SELL,
                        entry_price=snapshot.price,
                        stop_loss=0, # Hedge não usa SL convencional
                        take_profit=snapshot.price + (recovery_strike["tp_points"] * snapshot.symbol_info.get("point", 0.01)) 
                                    if recovery_strike["action"] == "BUY" else 
                                    snapshot.price - (recovery_strike["tp_points"] * snapshot.symbol_info.get("point", 0.01)),
                        confidence=0.99,
                        regime=regime_state.current.value,
                        reasoning=recovery_strike["reason"]
                    )
                    self.sniper.execute(rec_decision, self.state, snapshot)

        # ═══ 12. REFLEXÃO (CONSCIOUSNESS FEEDBACK) ═══
        # No primeiro ciclo e a cada 300 ciclos (~30 segundos), audita o histórico real do MT5
        if self._cycle_count == 1 or self._cycle_count % 300 == 0:
            self._reflection_phase(snapshot)

        # Log periódico (a cada 30 ciclos - [PHASE 48] ELEVATED HEARTBEAT)
        if self._cycle_count % 30 == 0:
            self._log_status(result, quantum_state, regime_state)

        return result

    def _reflection_phase(self, snapshot: MarketSnapshot):
        """
        Fase de Reflexão: Audita o histórico real para sincronizar a consciência.
        Deduz comissões e atualiza a evolução darwiniana.
        """
        from core.evolution.performance_tracker import TradeRecord
        
        # [Phase 49] Auto-detect Commission
        detected_comm = self.bridge.detect_broker_commission(snapshot.symbol)
        if detected_comm != OMEGA.get("commission_per_lot"):
            log.omega(f"📈 [COMMISSION ADAPTATION] Ajustando comissão: ${OMEGA.get('commission_per_lot')} -> ${detected_comm}")
            OMEGA.set("commission_per_lot", detected_comm, "Phase 49 Auto-Detection")
            OMEGA.save()
        
        # [Phase Ω-Resilience] Sincronizar saldo inicial para Drawdown real
        if snapshot and snapshot.account:
            current_balance = snapshot.account.get('balance', 100000.0)
            # O saldo inicial real = Saldo Atual - Lucro Total Registrado
            # Isso garante que a curva de equidade termine exatamente no saldo atual.
            total_hist_profit = self.performance_tracker.total_profit
            inferred_initial = current_balance - total_hist_profit
            self.performance_tracker.set_initial_balance(inferred_initial)
        
        # [Phase Ω-Darwin] Sincronização Dinâmica via history_deals_get
        # Na primeira vez, forçamos um scan profundo de 30 dias se o histórico estiver muito curto
        if not self._history_synced and self.performance_tracker.total_trades < 100:
            from_ts = int(time.time() - (86400 * 30))
            log.omega(f"🔍 [DEEP AUDIT] Sincronização inicial profunda ativada (30 dias).")
        else:
            from_ts = int(self._last_history_poll)
        
        # Polling do histórico usando a nova assinatura de timestamp
        deals = self.bridge.get_closed_deals(from_ts, None)
        
        if deals:
            # Só atualiza o marcador se de fato consultamos e houve deals
            self._last_history_poll = time.time()
            self._history_synced = True

        if not deals:
            return

        processed_count = 0
        new_count = 0
        for deal in deals:
            # Entry Out (1), INOUT (2) ou Out By (3) indica fechamento de posição ou reversão
            if deal.get("entry") not in [1, 2, 3]:
                continue
            
            processed_count += 1
            # Recuperar P&L líquido real consolidando TODOS os deals da posição
            pos_id = deal.get("position_id")
            pos_deals = self.bridge.get_deals_by_position(pos_id)
            
            if not pos_deals:
                pos_deals = [deal] # Fallback caso a API falhe em agrupar
                
            # Deal de entrada (IN)
            entry_deal = next((d for d in pos_deals if d.get('entry') == 0), None)
            if not entry_deal:
                # Se não achou o IN, foi uma posição aberta antes da janela de scan
                # Precisamos registrar o P&L mesmo assim para não corromper o Gross Profit/Loss
                entry_price = 0.0
                entry_time_val = deal['time']
                
                # Tipo do Deal OUT inverte o lado. Se deal = SELL(1), a posicao era BUY.
                # No MT5, mt5.DEAL_TYPE_BUY é 0, mt5.DEAL_TYPE_SELL é 1.
                is_buy_position = (deal.get('type') == "SELL" or deal.get('type') == 1)
                action_str = "BUY" if is_buy_position else "SELL"
            else:
                entry_price = entry_deal['price']
                entry_time_val = entry_deal['time']
                # Entry deal action é a direção da posição.
                is_buy_position = (entry_deal.get('type') == "BUY" or entry_deal.get('type') == 0)
                action_str = "BUY" if is_buy_position else "SELL"
            
            # Soma total de TUDO daquela posição (Profit + Comm + Swap + Fee)
            total_comm = sum(d.get('commission', 0.0) for d in pos_deals)
            total_swap = sum(d.get('swap', 0.0) for d in pos_deals)
            total_fee = sum(d.get('fee', 0.0) for d in pos_deals)
            total_profit = sum(d.get('profit', 0.0) for d in pos_deals)
            
            net_profit = total_profit + total_comm + total_swap + total_fee
            
            # [PHASE Ω-EVOLVE] Recuperar contexto original da intenção (Resolvendo Amnésia Financeira)
            intent = trade_registry.get_intent(pos_id, ticket=deal['ticket'])
            
            if intent:
                regime_label = intent.get("regime", "UNKNOWN")
                coherence = intent.get("coherence", 0.0)
                signal_str = intent.get("signal_strength", 0.0)
                log.info(f"🧠 [MEMORY RECOVERED] Contexto recuperado para Position #{pos_id}: Regime={regime_label}")
            else:
                # Fallback para o snapshot atual (Legado - Indesejado mas necessário para trades órfãos)
                regime_label = snapshot.regime.value if (snapshot and hasattr(snapshot.regime, 'value')) else str(snapshot.regime if snapshot else "UNKNOWN")
                coherence = 0.0
                signal_str = 0.0
                if pos_id > 0:
                    log.warning(f"⚠️ [AMNESIA] Intent não encontrada para Position #{pos_id}. Usando fallback.")

            record = TradeRecord(
                ticket=deal['ticket'],
                position_id=pos_id,
                symbol=deal['symbol'],
                action=action_str,
                lot_size=deal['volume'],
                entry_price=entry_price,
                exit_price=deal['price'],
                profit=net_profit,
                commission=total_comm,
                swap=total_swap,
                fee=total_fee,
                entry_time=datetime.fromtimestamp(entry_time_val, tz=timezone.utc).isoformat(),
                exit_time=datetime.fromtimestamp(deal['time'], tz=timezone.utc).isoformat(),
                regime_at_entry=regime_label,
                coherence_at_entry=coherence,
                signal_strength=signal_str,
                session=self._get_session_name(entry_time_val),
                duration_seconds=float(deal['time'] - entry_time_val)
            )
            
            # Registrar na consciência permanente
            is_new = self.performance_tracker.record_trade(record)
            if is_new:
                new_count += 1
            
            # [PHASE Ω-ANTI-FRAGILITY] Notificar TrinityCore sobre perdas para o gate ANTI-PING-PONG
            # Apenas se for um trade NOVO e RECENTE (últimos 5 minutos)
            if is_new and net_profit < 0:
                trade_age = time.time() - deal.get('time', 0)
                if trade_age < 300: # 5 minutos
                    self.trinity_core.update_loss_event()

        # Atualizar relatório e estado da ASI
        report = self.performance_tracker.full_report
        self.state.update_from_report(report)
        # [Phase Ω-Evolve] Darwinian Self-Optimization
        if hasattr(self, 'self_optimizer'):
            self.self_optimizer.check_and_optimize(300, snapshot) # Force optimization every reflection window

        log.omega(f"🧠 REFLEXÃO CONCLUÍDA: {len(deals)} deals na fita, {processed_count} fechamentos analisados, {new_count} novos registros. P&L Líquido: ${self.state.total_profit:+.2f}")

    def _get_session_name(self, timestamp: float) -> str:
        """Determina a sessão de mercado baseada na hora (UTC)."""
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        hour = dt.hour
        
        if 0 <= hour < 8: return "ASIA"
        if 8 <= hour < 14: return "EUROPE"
        if 14 <= hour < 21: return "US"
        return "LATE_US"

    def _log_status(self, result, quantum_state, regime_state):
        """Log periódico de status com visibilidade total do sinal."""
        # Extrair nomes dos agentes para exibição completa
        bull_agents = quantum_state.metadata.get("bull_agents", [])
        bear_agents = quantum_state.metadata.get("bear_agents", [])
        
        bull_str = ", ".join(bull_agents) if bull_agents else "None"
        bear_str = ", ".join(bear_agents) if bear_agents else "None"
        
        # Cálculo de latência de decisão real (total do think cycle)
        think_time = getattr(self, '_last_think_time', 0.0) * 1000.0

        log.info(
            f"💫 Cycle #{self._cycle_count} | "
            f"Action={result.get('action')} | "
            f"Signal={result.get('signal', 0):+.3f} | "
            f"Coherence={result.get('coherence', 0):.2f} | "
            f"Regime={result.get('regime')} | "
            f"TotalThink={think_time:.1f}ms | "
            f"P&L=${self.state.total_profit:+.2f}"
            f"\n  🎯 Reason: {result.get('reasoning')}"
            f"\n  🧬 Quantum: SIGNAL={result.get('signal', 0):+.3f} COHERENCE={result.get('coherence', 0):.2f} PHI={quantum_state.phi:.2f}"
            f"\n  🐂 BULL[{len(bull_agents)}]: {bull_str}"
            f"\n  🐻 BEAR[{len(bear_agents)}]: {bear_str}"
        )

    def shutdown(self):
        """Desligamento graceful — salva tudo."""
        log.omega("🔴 ASI BRAIN SHUTTING DOWN...")
        # Parar scrapers
        self.sentiment_scraper.stop()
        self.onchain_scraper.stop()
        self.macro_scraper.stop()
        # Parar data engine background worker
        self.data_engine.shutdown()
        # Matar subprocesso Java (Phase 25)
        if hasattr(self, 'java_daemon') and self.java_daemon:
            try:
                self.java_daemon.terminate()
            except Exception as e:
                pass
        # Salvar estado
        self.state.save()
        OMEGA.save()
        log.omega("💾 Estado salvo. Consciência preservada.")

    @property
    def diagnostics(self) -> dict:
        """Diagnóstico completo do cérebro."""
        return {
            "cycles": self._cycle_count,
            "state": {
                "total_trades": self.state.total_trades,
                "win_rate": self.state.win_rate,
                "total_profit": self.state.total_profit,
                "consecutive_losses": self.state.consecutive_losses,
                "circuit_breaker": self.state.circuit_breaker_active,
            },
            "regime": self.regime_detector.current_regime.value,
            "quantum_collapse_rate": self.quantum_thought.get_collapse_rate(),
            "trinity_stats": self.trinity_core.stats,
            "executor_stats": self.executor.stats,
            "swarm": self.neural_swarm.summary(),
        }
