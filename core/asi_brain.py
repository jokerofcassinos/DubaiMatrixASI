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
        self._last_pnl_prediction = None
        self._last_log_times = {} # key -> float
        # [Phase Ω-Darwin] Sincronização inicial: auditar as últimas 24h ou desde a última corrida
        self._last_history_poll = time.time() - 86400 

        # Iniciar Scrapers em background
        self.sentiment_scraper.start()
        self.onchain_scraper.start()
        self.macro_scraper.start()
        
        # Iniciar Java PnLPredictor
        self.java_daemon = None
        try:
            self.java_daemon = subprocess.Popen(
                ["java", "-cp", "d:\\DubaiMatrixASI\\java\\src", "com.dubaimatrix.PnLPredictor"],
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

        # ═══ 5. ANÁLISE NEURAL — Enxame de agentes ═══
        agent_signals = self.neural_swarm.analyze(snapshot, flow_analysis, regime_state=regime_state)

        # ═══ 6. PENSAMENTO QUÂNTICO — Convergência ═══
        regime_aggression = regime_state.aggression_multiplier if regime_state else 1.0
        quantum_state = self.quantum_thought.process(
            agent_signals, regime_weight=regime_aggression
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
            execution_result = self.executor.execute(
                decision, self.state, snapshot
            )
            
            # [PHASE 48] 🎯 IMMEDIATE IGNITION PULSE
            log.omega(
                f"🎯 IGNITION: {decision.action.value} {snapshot.symbol} | "
                f"S={quantum_state.raw_signal:+.3f} PHI={quantum_state.phi:.2f} "
                f"R={regime_state.current.value if regime_state else 'UNK'}"
            )

            if execution_result and execution_result.get("success"):
                result["executed"] = True
                result["ticket"] = execution_result.get("ticket")
                result["price"] = execution_result.get("price")

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
            self.self_optimizer.check_and_optimize(self._cycle_count)

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
                    msg = f"UPDATE:{account_balance}:{win_rate}:{avg_win}:{avg_loss}\n"
                    s.sendall(msg.encode('utf-8'))
                    
                    resp = s.recv(1024).decode('utf-8').strip()
                    if resp.startswith("ACK:"):
                        prediction = resp.split("ACK:")[1]
                        self._last_pnl_prediction = prediction
                        
                        # [PHASE Ω-RESILIENCE] Log Cooldown
                        now = time.time()
                        if now - self._last_log_times.get("pnl_pred", 0) > 60.0:
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
                    self.executor.execute(rec_decision, self.state, snapshot)

        # ═══ 12. REFLEXÃO (CONSCIOUSNESS FEEDBACK) ═══
        # A cada 600 ciclos (~1 minuto), audita o histórico real do MT5
        if self._cycle_count % 600 == 0:
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
        
        # [Phase Ω-Darwin] Sincronização Dinâmica via history_deals_get
        now = datetime.now()
        # Buscamos deals desde o último poll + um buffer de segurança de 30s
        last_poll_dt = datetime.fromtimestamp(self._last_history_poll, tz=timezone.utc)
        
        deals = self.bridge.get_closed_deals(last_poll_dt, now)
        self._last_history_poll = time.time()

        if not deals:
            return

        for deal in deals:
            # Entry Out (1) ou Out By (3) indica fechamento de posição
            if deal.get("entry") not in [1, 3]:
                continue
                
            # Recuperar P&L líquido real (Soma dos deals da posição)
            pos_id = deal.get("position_id")
            pos_deals = self.bridge.get_deals_by_position(pos_id)
            
            if not pos_deals:
                continue
                
            # Deal de entrada (IN)
            entry_deal = next((d for d in pos_deals if d.get('entry') == 0), None)
            if not entry_deal:
                continue
            
            # Consolidar custos (comissão, swap, fees de TODOS os deals da posição)
            total_comm = sum(d.get('commission', 0) for d in pos_deals)
            total_swap = sum(d.get('swap', 0) for d in pos_deals)
            total_fee = sum(d.get('fee', 0) for d in pos_deals)
            total_profit = sum(d.get('profit', 0) for d in pos_deals)
            
            # [Ω-Class] Alpha Líquido Real
            net_profit = total_profit + total_comm + total_swap + total_fee
            
            action_str = "BUY" if entry_deal['type'] == 0 else "SELL"
            
            record = TradeRecord(
                ticket=deal['ticket'],
                position_id=pos_id,
                symbol=deal['symbol'],
                action=action_str,
                lot_size=entry_deal['volume'],
                entry_price=entry_deal['price'],
                exit_price=deal['price'],
                profit=net_profit,
                commission=total_comm,
                swap=total_swap,
                fee=total_fee,
                entry_time=datetime.fromtimestamp(entry_deal['time'], tz=timezone.utc).isoformat(),
                exit_time=datetime.fromtimestamp(deal['time'], tz=timezone.utc).isoformat(),
                regime_at_entry=snapshot.regime.value if (snapshot and hasattr(snapshot.regime, 'value')) else str(snapshot.regime if snapshot else "UNKNOWN"),
                session=self._get_session_name(entry_deal['time']),
                duration_seconds=float(deal['time'] - entry_deal['time'])
            )
            
            # Registrar na consciência permanente
            is_new = self.performance_tracker.record_trade(record)
            
            # [PHASE Ω-ANTI-FRAGILITY] Notificar TrinityCore sobre perdas para o gate ANTI-PING-PONG
            # Apenas se for um trade NOVO e RECENTE (últimos 5 minutos)
            if is_new and net_profit < 0:
                trade_age = time.time() - deal.get('time', 0)
                if trade_age < 300: # 5 minutos
                    self.trinity_core.update_loss_event()

        # Atualizar relatório e estado da ASI
        report = self.performance_tracker.full_report
        self.state.update_from_report(report)
        
        # 4. Auto-Otimização Darwiniana (Phase 5)
        self.self_optimizer.check_and_optimize(self.performance_tracker)

        log.omega(f"🧠 REFLEXÃO CONCLUÍDA: {len(deals)} deals analisados. P&L Líquido: ${self.state.total_profit:+.2f}")

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
