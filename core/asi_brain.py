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
from core.consciousness.quantum_thought import QuantumThoughtEngine, QuantumState
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
from core.decision.shadow_engine import ShadowCounterfactualEngine
from core.decision.lifecycle_logger import LifecycleLogger


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
        self.quantum_thought = QuantumThoughtEngine()
        self.trinity_core = TrinityCore()
        
        self.neural_swarm = NeuralSwarm(
            memory=self.memory, 
            predator_engine=self.predator_engine,
            t_cell=self.trinity_core.t_cell if hasattr(self.trinity_core, 't_cell') else None
        )
        
        self.risk_engine = RiskQuantumEngine()
        
        # ═══ PHASE 5: EDGE LLM DISTILLATION ═══
        self.llm_distiller = EdgeLLMDistiller()
        
        self.sniper = SniperExecutor(bridge, self.risk_engine)
        self.executor = self.sniper
        
        # Callback para Anti-Metralhadora Pós-Close
        def on_position_closed(result: dict):
            # [Phase 52 Fix] Receive dict from PositionManager and update state
            if not result or not result.get("success"):
                return

            # [Phase Ω-Darwin] Sincronização de Histórico já é feita no _audit_mt5_history
            # Portanto, não precisamos mais chamar self.performance_tracker.on_position_closed(result)
            
            # Anti-Metralhadora: Impedir reentrada imediata na mesma direção
            # O result contém o ticket e o close_price.
            # A direção vem originalmente do strike. No MT5 Bridge, close_position injeta o profit.
            # [Phase 52] Precisamos saber se era BUY ou SELL para o bloqueio.
            direction = result.get("direction", "UNKNOWN")
            if direction != "UNKNOWN":
                self.sniper._post_close_direction = direction
                self.sniper._post_close_candle_count = 0
            
        self.position_manager = PositionManager(bridge, on_close_callback=on_position_closed)

        # ═══ PHASE 5: WEB SCRAPERS (Zero-Cost External Intelligence) ═══
        self.sentiment_scraper = SentimentScraper()
        self.onchain_scraper = OnChainScraper()
        self.macro_scraper = MacroScraper()

        # ═══ ESTADO DA ASI ═══
        self.state = ASIState()
        self.state.load()  # Carregar estado anterior

        # ═══ PHASE 5: SELF-EVOLUTION ═══
        self.performance_tracker = PerformanceTracker()
        self.self_optimizer = SelfOptimizer(self.performance_tracker)
        self.lifecycle_logger = LifecycleLogger()
        
        # ═══ PHASE Ω-9: MOTOR CONTRAFACTUAL SOMBRA ═══
        self.shadow_engine = ShadowCounterfactualEngine()

        # Contadores
        self._cycle_count = 0
        self._last_snapshot = None
        self._last_nuke_time = 0.0 # [Phase Ω-Resilience] Track last global exit
        self._last_pnl_prediction = "STABLE"
        self._last_log_times = {} # {key: timestamp}
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
        self.lifecycle_logger.start_cycle()
        self._cycle_count += 1

        # ═══ 1. PERCEPÇÃO — Coletar dados ═══
        snapshot = self.data_engine.update()
        if snapshot is None:
            return {"cycle": self._cycle_count, "action": "NO_DATA"}

        self._last_snapshot = snapshot

        # [Phase 40] Self-Optimizer Cycle
        if self._cycle_count % self._evolution_check_interval == 0:
            self.self_optimizer.check_and_optimize(self._cycle_count, snapshot)

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
        if regime_state:
            snapshot.regime = regime_state.current
        else:
            from core.consciousness.regime_detector import MarketRegime
            snapshot.regime = MarketRegime.UNKNOWN

        # ═══ 4. INTELIGÊNCIA EXTERNA — Scrapers ═══
        snapshot.metadata["sentiment_score"] = self.sentiment_scraper.sentiment_score
        snapshot.metadata["network_pressure"] = self.onchain_scraper.network_pressure
        snapshot.metadata["macro_bias"] = self.macro_scraper.macro_bias
        snapshot.metadata["pnl_prediction"] = self._last_pnl_prediction
        snapshot.metadata["dynamic_commission_per_lot"] = OMEGA.get("commission_per_lot", 32.0)
        snapshot.metadata["phi_last"] = 0.0 # Will be updated after quantum thought

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
        # [PHASE Ω-EVOLUTION] Swarm Authority Modulation
        if quantum_state:
            self.neural_swarm.modulate_authority(quantum_state.coherence)
            
        snapshot.metadata["phi_last"] = quantum_state.phi
        snapshot.metadata["raw_signal"] = quantum_state.raw_signal
        snapshot.metadata["coherence_last"] = quantum_state.coherence
        
        # [Phase Ω-PhD-4] NRO: Extract Manifold Curvature from specialized agents
        manifold_curvature = 0.0
        for sig in agent_signals:
            if sig.agent_name in ["RiemannianManifold", "RiemannianManifoldGaussian"]:
                # Pega a curvatura da metadata se disponível
                if sig.metadata and isinstance(sig.metadata, dict):
                    manifold_curvature = sig.metadata.get("curvature", sig.signal * sig.confidence)
                else:
                    manifold_curvature = sig.signal * sig.confidence
                break
        snapshot.metadata["manifold_curvature"] = manifold_curvature

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
            "snapshot": snapshot,
            "quantum": quantum_state
        }
        
        # [Ω-LIFECYCLE] Persistir o ciclo completo no log de trades
        self.lifecycle_logger.end_cycle(self._cycle_count, decision, quantum_state, snapshot)

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
            
            # [Phase Ω-Anti-Spam] Nuke Cooldown: Se acabamos de fechar tudo, espere a poeira baixar
            nuke_cooldown = OMEGA.get("global_nuke_cooldown_seconds", 300.0)
            since_nuke = now - self.bridge.position_manager._last_nuke_time if hasattr(self.bridge, "position_manager") else 999.0
            
            last_ign = self._last_log_times.get(f"ign_{decision.action.value}", 0.0)
            
            if already_pending:
                if now - self._last_log_times.get("ign_bypass", 0) > 30:
                    log.debug(f"⏳ IGNITION Bypassed: Ordem {decision.action.value} já pendente no book.")
                    self._last_log_times["ign_bypass"] = now
            elif since_nuke < nuke_cooldown:
                if now - self._last_log_times.get("nuke_veto", 0) > 60:
                    log.omega(f"🛡️ [NUKE COOLDOWN] Bloqueando re-entrada pós-liquidação ({int(nuke_cooldown - since_nuke)}s restante)")
                    self._last_log_times["nuke_veto"] = now
            elif now - last_ign >= cooldown: # [FIX] Agora respeita o cooldown real do OMEGA
                # 5. EXECUÇÃO (Sniper Strike)
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
                    
                    # [Phase Ω-Stability] Explicit Audit Trace
                    from utils.audit_engine import AUDIT_ENGINE
                    audit_dir = AUDIT_ENGINE.get_active_audit_path(execution_result.get('ticket'))
                    if audit_dir:
                        log.info(f"📂 [AUDIT TRACE] Detail captured at: {audit_dir}")
                    
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
        elif decision and decision.action == Action.WAIT:
            # [Phase Ω-9] Registro de Trade Sombra para Oportunidades Vetadas
            if quantum_state and abs(quantum_state.raw_signal) > 0.15:
                # Obter ATR (se aplicável), senão assume proxy.
                atr = float(snapshot.atr)
                # Consideramos a intenção original do sinal antes do WAIT
                intended_action = Action.BUY if quantum_state.raw_signal > 0 else Action.SELL
                self.shadow_engine.register_shadow_trade(decision.reasoning, snapshot, quantum_state, intended_action, atr)

        # ═══ 8. MONITORAR POSIÇÕES ABERTAS (POSITION MANAGER / SMART TP) ═══
        self.position_manager.monitor_positions(snapshot, flow_analysis, quantum_state=quantum_state)
        
        # [Phase Ω-9] Atualizar PnL Virtual das Sombras
        self.shadow_engine.update_shadow_matrix(snapshot.price)

        # ═══ 8B. GRAVAR MEMÓRIA EPISÓDICA (a cada 60 ciclos) ═══
        if self._cycle_count % 60 == 0:
            # Geramos o embedding usando o agente de intuição
            intuition_agent = self.neural_swarm.get_agent_by_name("MarketIntuition")
            if intuition_agent:
                embedding = intuition_agent._generate_embedding(snapshot, flow_analysis)
                # O outcome será preenchido pelo PerformanceTracker futuramente, 
                # aqui gravamos o estado com o preço atual.
                self.memory.add_episode(embedding, {"price": snapshot.price, "time": snapshot.timestamp})

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
                    risk_frac = OMEGA.get("risk_fraction_per_trade", 0.05)
                    msg = f"UPDATE:{account_balance}:{win_rate}:{avg_win}:{avg_loss}:{is_relaxed}:{risk_frac}\n"
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
                        signal_strength=1.0, # [Ω-FIX] Mandatory arg for Decision
                        lot_size=0.01,       # [Ω-FIX] Mandatory arg (recalculated by Sniper)
                        regime=regime_state.current.value,
                        reasoning=recovery_strike["reason"],
                        metadata={"phi": 1.0, "is_god_mode": False, "phi_resonance": False, "is_tunneling": False, "is_hydra": False, "is_tec_active": False}
                    )
                    self.sniper.execute(rec_decision, self.state, snapshot)

        # ═══ 12. REFLEXÃO (CONSCIOUSNESS FEEDBACK) ═══
        # No primeiro ciclo e a cada 600 ciclos (~60 segundos), audita o histórico real do MT5
        if self._cycle_count == 1 or self._cycle_count % 600 == 0:
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
            # [Phase Ω-Optimization] Reduced initial scan from 30 to 7 days to minimize startup latency
            from_ts = int(time.time() - (86400 * 7))
            log.omega(f"🔍 [DEEP AUDIT] Sincronização inicial otimizada (7 dias).")
        else:
            from_ts = int(self._last_history_poll)

        deals = self.bridge.get_closed_deals(from_ts, None)
        
        if not deals:
            return

        # [Phase 52.2] Consolidação por Posição: Evitar tratar fragmentos como trades independentes
        # Agrupamos deals pelo position_id
        deals_by_pos = {}
        for d in deals:
            pid = d.get("position_id")
            if pid not in deals_by_pos:
                deals_by_pos[pid] = []
            deals_by_pos[pid].append(d)

        new_count = 0
        for pos_id, pos_deals in deals_by_pos.items():
            # Critério de Encerramento: Uma posição só é considerada 'trade' se houver deal tipo OUT (1, 2 ou 3)
            # e a soma dos volumes IN vs OUT for igual (posição fechada)
            in_vol = sum(d.get('volume', 0.0) for d in pos_deals if d.get('entry') == 0)
            out_deals = [d for d in pos_deals if d.get('entry') in [1, 2, 3]]
            out_vol = sum(d.get('volume', 0.0) for d in out_deals)
            
            if not out_deals or out_vol < in_vol * 0.99:
                # Posição ainda aberta ou parcialmente fechada - ignorar na reflexão p/ não corromper WR
                continue
            
            # Deal representativo para o encerramento (o último OUT)
            final_deal = sorted(out_deals, key=lambda x: x['time'])[-1]
            
            # Deal de entrada (IN)
            entry_deal = next((d for d in pos_deals if d.get('entry') == 0), None)
            
            if not entry_deal:
                entry_price = final_deal['price'] # Use liquidation/exit price as proxy if entry missing
                entry_time_val = final_deal['time']
                is_buy_position = (final_deal.get('type') == "SELL" or final_deal.get('type') == 1)
                action_str = "BUY" if is_buy_position else "SELL"
            else:
                entry_price = entry_deal['price']
                entry_time_val = entry_deal['time']
                is_buy_position = (entry_deal.get('type') == "BUY" or entry_deal.get('type') == 0)
                action_str = "BUY" if is_buy_position else "SELL"
            
            if entry_price == 0:
                entry_price = final_deal['price']
            
            # Cálculo de P&L Líquido Total
            total_comm = sum(d.get('commission', 0.0) for d in pos_deals)
            total_swap = sum(d.get('swap', 0.0) for d in pos_deals)
            total_fee = sum(d.get('fee', 0.0) for d in pos_deals)
            total_profit = sum(d.get('profit', 0.0) for d in pos_deals)
            net_profit = total_profit + total_comm + total_swap + total_fee
            
            # [PHASE Ω-EVOLVE] Recuperar contexto
            intent = trade_registry.get_intent(pos_id, ticket=final_deal['ticket'])
            
            if intent:
                regime_label = intent.get("regime", "UNKNOWN")
                coherence = intent.get("coherence", 0.0)
                signal_str = intent.get("signal_strength", 0.0)
                # [Phase Ω-Cleanup] Logar apenas se não estiver no tracker para evitar spam
                if not self.performance_tracker.has_trade(pos_id):
                    pass # log.debug(f"🧠 [MEMORY RECOVERED] Contexto recuperado para Position #{pos_id}: Regime={regime_label}")

            else:
                regime_label = snapshot.regime.value if (snapshot and hasattr(snapshot.regime, 'value')) else str(snapshot.regime if snapshot else "UNKNOWN")
                coherence = 0.0
                signal_str = 0.0

            record = TradeRecord(
                ticket=final_deal['ticket'],
                position_id=pos_id,
                symbol=final_deal['symbol'],
                action=action_str,
                lot_size=in_vol,
                entry_price=entry_price,
                exit_price=final_deal['price'],
                profit=net_profit,
                commission=total_comm,
                swap=total_swap,
                fee=total_fee,
                entry_time=datetime.fromtimestamp(entry_time_val, tz=timezone.utc).isoformat(),
                exit_time=datetime.fromtimestamp(final_deal['time'], tz=timezone.utc).isoformat(),
                regime_at_entry=regime_label,
                coherence_at_entry=coherence,
                signal_strength=signal_str,
                session=self._get_session_name(entry_time_val),
                duration_seconds=float(final_deal['time'] - entry_time_val)
            )
            
            # Registrar na consciência permanente
            is_new = self.performance_tracker.record_trade(record)
            if is_new:
                new_count += 1
                
                # [Phase 69] PhD Level Feedback Loop
                if net_profit < 0:
                    # 1. Biological Immunity: Register infection if it was a loss
                    from core.consciousness.agents.phd_agents import IMMUNITY
                    IMMUNITY.register_infection(snapshot, abs(net_profit))
                
                # 2. Byzantine Consensus: Update consensus weights if we have intent
                if intent and "agent_signals" in intent:
                    # O intent salva uma lista de dicts ou objetos AgentSignal
                    # Precisamos extrair apenas o valor do sinal bruto
                    raw_signals = [float(s.get("signal", 0.0) if isinstance(s, dict) else getattr(s, 'signal', 0.0)) 
                                   for s in intent["agent_signals"]]
                    actual_outcome = 1.0 if net_profit > 0 else -1.0
                    self.neural_swarm.byzantine.update_consensus(raw_signals, actual_outcome)
            
            # Anti-Ping-Pong
            if is_new and net_profit < 0:
                trade_age = time.time() - final_deal.get('time', 0)
                if trade_age < 300:
                    self.trinity_core.update_loss_event()

        # Atualizar relatório e estado da ASI
        report = self.performance_tracker.full_report
        self.state.update_from_report(report)
        # [Phase Ω-Evolve] Darwinian Self-Optimization
        if hasattr(self, 'self_optimizer'):
            self.self_optimizer.check_and_optimize(300, snapshot) # Force optimization every reflection window

        # [Phase Ω-Darwin] Sincronização: Manter rastro do último deal para evitar re-scan
        if deals_by_pos:
            all_deal_times = [d.get('time', 0) for deals in deals_by_pos.values() for d in deals]
            if all_deal_times:
                self._last_history_poll = max(all_deal_times) + 1 # +1s p/ segurança

        log.omega(f"🧠 REFLEXÃO CONCLUÍDA: {len(deals_by_pos)} posições auditadas, {new_count} novos registros finalizados. P&L Líquido Total: ${self.state.total_profit:+.2f}")


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
