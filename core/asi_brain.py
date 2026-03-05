"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — ASI BRAIN                             ║
║         O Cérebro Central — Orquestra toda a consciência                    ║
║                                                                              ║
║  Ciclo: Percepção → Análise → Deliberação → Decisão → Ação → Reflexão     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import time
from datetime import datetime, timezone
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
from core.decision.trinity_core import TrinityCore, Action
from core.evolution.performance_tracker import PerformanceTracker
from core.evolution.self_optimizer import SelfOptimizer
from execution.risk_quantum import RiskQuantumEngine
from execution.sniper_executor import SniperExecutor
from execution.position_manager import PositionManager
from config.settings import ASIState, CONSCIOUSNESS_CYCLE_MS
from config.omega_params import OMEGA
from utils.logger import log
from utils.decorators import timed, catch_and_log


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
        self.neural_swarm = NeuralSwarm()
        self.quantum_thought = QuantumThoughtEngine()
        self.regime_detector = RegimeDetector()
        self.trinity_core = TrinityCore()
        self.risk_engine = RiskQuantumEngine()
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

        # ═══ 5. ANÁLISE NEURAL — Enxame de agentes ═══
        agent_signals = self.neural_swarm.analyze(snapshot, flow_analysis)

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

            if execution_result and execution_result.get("success"):
                result["executed"] = True
                result["ticket"] = execution_result.get("ticket")
                result["price"] = execution_result.get("price")

        # ═══ 8. MONITORAR POSIÇÕES ABERTAS (POSITION MANAGER / SMART TP) ═══
        self.position_manager.monitor_positions(snapshot, flow_analysis)

        # ═══ 9. AUTO-EVOLUÇÃO (a cada 200 ciclos) ═══
        if self._cycle_count % 200 == 0:
            self.self_optimizer.optimize(self._cycle_count)

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
                    avg_win = max(1.0, self.state.total_profit / max(1, self.state.total_wins))
                    avg_loss = max(1.0, abs(self.state.total_profit) / max(1, self.state.total_losses))
                    
                    account_balance = snapshot.account.get("balance", 0.0) if snapshot.account else 0.0
                    msg = f"UPDATE:{account_balance}:{win_rate}:{avg_win}:{avg_loss}\n"
                    s.sendall(msg.encode('utf-8'))
                    
                    resp = s.recv(1024).decode('utf-8').strip()
                    if resp.startswith("ACK:"):
                        prediction = resp.split("ACK:")[1]
                        log.omega(f"🔮 [JAVA PnL PREDICTOR] {prediction}")
            except Exception as e:
                log.debug(f"Pausa tática: Java PnL Predictor indisponível - {e}")

        # Log periódico (a cada 50 ciclos)
        if self._cycle_count % 50 == 0:
            self._log_status(result, quantum_state, regime_state)

        return result

    def _log_status(self, result, quantum_state, regime_state):
        """Log periódico de status."""
        log.info(
            f"💫 Cycle #{self._cycle_count} | "
            f"Action={result.get('action')} | "
            f"Signal={result.get('signal', 0):+.3f} | "
            f"Coherence={result.get('coherence', 0):.2f} | "
            f"Regime={result.get('regime')} | "
            f"Trades={self.state.total_trades} | "
            f"WinRate={self.state.win_rate:.1%} | "
            f"P&L=${self.state.total_profit:+.2f} | "
            f"Reason={result.get('reasoning')}"
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
