"""
# [Ω-SOLÉNN] The Sovereign Orchestrator Master (main.py) Ω-51
# "O Maestro Soberano do Fluxo Neural, Interface Matrix e Execução Absoluta."
# Protocolo 3-6-9: 3 Conceitos | 18 Tópicos | 162 Vetores Ph.D.-Grade

# CONCEITO 1: GÊNESE DA MATRIZ (Sequência de Inicialização Ascendente)
#   Tópico 1.1: Inicialização de Todos os Órgãos do Organismo
#   Tópico 1.2: Acoplamento das 15 Sinapses ao Orquestrador
#   Tópico 1.3: Handshake MetaBridge (MT5/FTMO-Demo)
#   Tópico 1.4: Ativação do Sensor (Binance HFT WebSocket)
#   Tópico 1.5: Boot Sequence da Dashboard Matrix
#   Tópico 1.6: Graceful Shutdown Protocol

# CONCEITO 2: CICLO COGNITIVO (Pipeline Sensorial → Decisão → Execução)
#   Tópico 2.1: Rota: Binance → DataEngine → SwarmOrchestrator
#   Tópico 2.2: Colapso do QuantumState via Consenso Bizantino
#   Tópico 2.3: Filtro de Confluência Soberana (SignalGate Ω-1)
#   Tópico 2.4: Validação de Risco (Circuit Breakers Ω-5)
#   Tópico 2.5: Dispatch de Ordens ao MetaBridge (MT5 Thread-Pool)
#   Tópico 2.6: Registro de Trade e Forensic Trigger (P0 Bug)

# CONCEITO 3: INTERFACE HOLOGRÁFICA (Dashboard + Telemetria + SRE)
#   Tópico 3.1: Renderização Tática O(1) de Telemetria Real
#   Tópico 3.2: Feed de Logs Colapsados (Último Veredito)
#   Tópico 3.3: Monitoramento Bizantino em Tempo Real
#   Tópico 3.4: Heartbeat SRE (CPU/RAM/Latência)
#   Tópico 3.5: CEO Kill-Switch Intercept (Ctrl+C)
#   Tópico 3.6: Graceful Shutdown com Flatten de Posições
"""

import asyncio
import logging
import time
import sys
import os
import psutil
import numpy as np
from collections import deque
from typing import Dict, Any, Optional

# ━━━━━━━━━━━━ PATH RESOLUTION ━━━━━━━━━━━━
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# ━━━━━━━━━━━━ ORGAN IMPORTS ━━━━━━━━━━━━

# Sensory Organs (Dados de Mercado)
from market.exchanges.binance_hftp import BinanceHFTP
from market.data_engine import OmniDataEngine, MarketData, QuantumState

# Cognitive Organs (Inteligência de Enxame)
from core.intelligence.swarm_orchestrator import SwarmOrchestrator
from core.intelligence.solenn_bayesian import SolennBayesian
from core.intelligence.elite_synapse_adapters import create_all_elite_synapses
from core.intelligence.signals_gate import SolennSignalGate, SovereignSignal

# Executive Organs (Risco e Execução)
from market.risk_manager import RiskManager
from market.regime_detector import RegimeDetector
from market.exchanges.mt5_connector import MetaBridge

# Visual Organ (Dashboard Matrix)
from core.solenn_terminal import SolennTerminalMatrix

# ━━━━ CONSCIOUSNESS ORGANS (Self-Awareness) ━━━━
from core.consciousness.state_observer import StateObserver
from core.consciousness.reflexive_loop import ReflexiveLoop
from core.consciousness.genetic_forge import GeneticForge
from core.consciousness.quantum_thought import QuantumThought
from core.consciousness.neural_swarm import NeuralSwarm
from core.consciousness.monte_carlo_engine import MonteCarloEngine

# Configuration
from config.settings import (
    FTMO_LOGIN, FTMO_PASSWORD, FTMO_SERVER,
    MAX_DAILY_DRAWDOWN_PCT, MAX_TOTAL_DRAWDOWN_PCT,
)

# ━━━━━━━━━━━━ LOGGING MATRIX REDIRECT ━━━━━━━━━━━━

class MatrixLogHandler(logging.Handler):
    """ Redireciona logs do Python para o buffer da UI Matrix. """
    def emit(self, record):
        try:
            msg = self.format(record)
            # Remove prefixo de data se houver, pois a UI adiciona timestamp próprio
            if " | " in msg:
                msg = msg.split(" | ", 2)[-1]
            SolennTerminalMatrix.add_log(msg)
        except Exception:
            self.handleError(record)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)-18s | %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(_ROOT, "logs", "solenn_omega.log"), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger("SOLENN.Omega")


class SolennOmega:
    """
    [Ω-ORGANISM] O Organismo SOLÉNN Completo.
    
    Pipeline Neural Integrado:
      BinanceWSS → OmniDataEngine → SwarmOrchestrator (15 Sinapses) 
      → SignalGate (Confluência) → RiskManager (Circuit Breakers) 
      → MetaBridge (MT5/FTMO)
    
    Dashboard Matrix renderiza telemetria em tempo real.
    """

    SYMBOL = "BTCUSD"

    def __init__(self):
        self._is_running = False
        self._cognitive_ticks = 0
        self._trades_executed = 0
        self._trades_rejected = 0
        self._last_verdict: Optional[SovereignSignal] = None

        # ━━━━ Telemetria Holográfica ━━━━
        self._tick_latencies = deque(maxlen=5000)
        self._quantum_history = deque(maxlen=200)
        self.telemetry: Dict[str, Any] = {
            "bridge_latency_ms": 0.0,
            "regime_label": "BOOTING",
            "volatility_tensile": 0.0,
            "live_pnl": 0.0,
            "drawdown_pct": 0.0,
            "slots_active": 0,
            "elite_1_status": "INITIALIZING",
            "elite_2_status": "INITIALIZING",
            "global_confidence": 0.0,
            "last_log": "Gênese Omega: Inicializando órgãos do organismo...",
        }

        # ━━━━ SENSORY ORGANS ━━━━
        self.sensor = BinanceHFTP()
        self.data_engine = OmniDataEngine()

        # ━━━━ COGNITIVE ORGANS ━━━━
        self.orchestrator = SwarmOrchestrator()
        self.gate = SolennSignalGate()
        self.regime = RegimeDetector(self.SYMBOL)

        # ━━━━ EXECUTIVE ORGANS ━━━━
        self.risk = RiskManager(initial_balance=100_000.0)
        self.mt5_bridge: Optional[MetaBridge] = None

        # ━━━━ CONSCIOUSNESS ORGANS ━━━━
        self.observer = StateObserver(latency_threshold_ms=3.0)
        self.reflexive = ReflexiveLoop(window_size=50)
        self.forge = GeneticForge()
        self.quantum = QuantumThought()
        self.swarm = NeuralSwarm(max_agents=50)
        self.oracle = MonteCarloEngine(target_profit=70000.0)

    # ═══════════════════════════════════════════════════════════════
    # CONCEITO 1: GÊNESE DA MATRIZ
    # ═══════════════════════════════════════════════════════════════

    async def _genesis_synapses(self):
        """[C1-T1.2] Acoplar TODAS as 15 sinapses ao orquestrador."""
        log.info("━" * 60)
        log.info("  FASE 1: GÊNESE DO ENXAME (15 SINAPSES)")
        log.info("━" * 60)

        # SolennBayesian (fundacional)
        bayesian = SolennBayesian(data_engine=self.data_engine)
        self.orchestrator.synapses["SolennBayesian_01"] = bayesian
        log.info("  ✅ Sinapse 'SolennBayesian_01' acoplada.")

        # 14 Agentes Elite via Factory
        elite = create_all_elite_synapses()
        for name, synapse in elite.items():
            self.orchestrator.synapses[name] = synapse

        total = len(self.orchestrator.synapses)
        log.info(f"  🐝 TOTAL DE SINAPSES ATIVAS: {total}")
        for name in self.orchestrator.synapses:
            log.info(f"    🧬 {name}")
        log.info("━" * 60)

    async def _genesis_mt5(self) -> bool:
        """[C1-T1.3] Handshake com MetaTrader 5 (FTMO-Demo)."""
        log.info("━" * 60)
        log.info("  FASE 2: HANDSHAKE MT5 (MetaBridge Ω-45)")
        log.info("━" * 60)

        login = FTMO_LOGIN
        password = FTMO_PASSWORD
        server = FTMO_SERVER

        if login == 0 or password == "PWD":
            log.warning("⚠️ Credenciais MT5 não configuradas no .env. Operando em modo OBSERVAÇÃO.")
            return False

        try:
            self.mt5_bridge = MetaBridge(login=login, password=password, server=server)
            # Timeout de 15s para o handshake não travar o bot se o MT5 estiver fechado
            success = await asyncio.wait_for(self.mt5_bridge.initialize(), timeout=15.0)

            if success:
                log.info(f"✅ MetaBridge CONECTADA: Login {login} @ {server}")
                asyncio.create_task(self._mt5_equity_sync_loop())
                return True
            else:
                log.error(f"☢️ MetaBridge FALHOU no Handshake. Verifique se o MT5 está aberto.")
                self.mt5_bridge = None
                return False

        except asyncio.TimeoutError:
            log.error("☢️ MT5_HANDSHAKE_TIMEOUT: MetaTrader 5 não respondeu em 15s. Abortando conexão.")
            self.mt5_bridge = None
            return False
        except Exception as e:
            log.error(f"☢️ MT5_BRIDGE_FAULT: {e}")
            self.mt5_bridge = None
            return False

    async def _genesis_sensor(self):
        """[C1-T1.4] Ativar pipeline sensorial: Binance → DataEngine → Swarm."""
        log.info("━" * 60)
        log.info("  FASE 3: ATIVAÇÃO SENSOR BINANCE (Pipeline HFT)")
        log.info("━" * 60)

        # Iniciar DataEngine
        await self.data_engine.initialize()
        await self.data_engine.register_consumer(self._on_market_data)
        log.info("  ✅ OmniDataEngine (Aorta Core) Online + Consumidor Registrado.")

        # Risk Manager
        await self.risk.initialize()
        log.info("  ✅ RiskManager Ω-5 Ativado.")

        # Roteador Binance → DataEngine
        def binance_router(payload):
            asyncio.create_task(self.data_engine.ingest_raw("BINANCE", payload))
        self.sensor.register_callback(binance_router)

        # Conectar WebSocket
        await self.sensor.connect()
        log.info("  ✅ BinanceHFTP WebSocket LIVE!")
        log.info("━" * 60)

    async def _genesis_consciousness(self):
        """[C1-T1.5] Ativação dos Órgãos de Consciência e Background Tasks."""
        log.info("━" * 60)
        log.info("  FASE 4: IGNICRÃO DA CONSCIÊNCIA Ω (Poder de Turing)")
        log.info("━" * 60)

        # 1. Iniciar NeuralSwarm com Hall of Fame
        if self.forge.hall_of_fame:
            self.swarm.populate(self.forge.hall_of_fame)
        else:
            log.info("  ⚠️ Hall of Fame vazio. O GeneticForge iniciará a evolução inicial.")
        
        # 2. Lançar Background Loops
        asyncio.create_task(self.forge.start_background_forge(self.data_engine))
        asyncio.create_task(self.oracle.start_background_loop(self.risk))
        asyncio.create_task(self._consciousness_sync_loop())

        log.info("  ✅ StateObserver Monitorando Integridade Ontológica.")
        log.info("  ✅ ReflexiveLoop Rastreando Bias de Soros.")
        log.info("  ✅ QuantumThought Operacional (Wave Collapse).")
        log.info("  ✅ GeneticForge Evoluindo em Background.")
        log.info("  ✅ MonteCarlo Oracle Projetando Trajetórias.")
        log.info("━" * 60)

    async def _consciousness_sync_loop(self):
        """Loop de sincronização de saúde e metadados de consciência."""
        while self._is_running:
            try:
                # Atualizar telemetria com saúde do StateObserver
                report = self.observer.get_health_report()
                mc_stats = self.oracle.last_stats
                reflexive_ctx = self.reflexive.get_state_context()
                
                self.telemetry["sre_status"] = report["status"]
                self.telemetry["safe_mode"] = report["safe_mode"]
                self.telemetry["brier_score"] = report["brier_score"]
                
                if mc_stats:
                    self.telemetry["prob_success"] = mc_stats.prob_success
                    self.telemetry["prob_ruin"] = mc_stats.prob_ruin
                
                self.telemetry["reflexivity_r"] = reflexive_ctx["reflexivity_r"]
                self.telemetry["bias"] = reflexive_ctx["bias"]
                
            except Exception as e:
                log.error(f"☢️ Consciousness Sync Error: {e}")
            await asyncio.sleep(2.0)

    # ═══════════════════════════════════════════════════════════════
    # CONCEITO 2: CICLO COGNITIVO
    # ═══════════════════════════════════════════════════════════════

    async def _on_market_data(self, snapshot: MarketData):
        """
        [C2-T2.1] O Pulso Central: agora INTEGRADO com Consciência Superior.
        Binance → Swarm → Reflexive → QuantumCollapse → SignalGate → Risk → MT5
        """
        self._cognitive_ticks += 1
        log.info(f"🧬 TICKER_RECEIVED: {snapshot.symbol} {snapshot.close:.2f} (Vol: {snapshot.volume:.2f})")
        t0 = time.time()
        self.observer.heart_pulse(t0) # Início do monitoramento de homeostase

        try:
            # ━━━ STEP 0: Integridade Ontológica ━━━
            if not self.observer.verify_interface_integrity("OmniData", snapshot.metadata):
                return

            # ━━━ STEP 1: Reflexividade de Soros (Ω-1.1) ━━━
            bias = self.reflexive.calculate_cognitive_bias(
                taker_buy=snapshot.taker_buy_vol,
                taker_sell=snapshot.taker_sell_vol,
                spread=snapshot.spread
            )
            self.reflexive.update_dynamics(snapshot.close, bias)
            reflexive_climax, climax_dir, climax_conf = self.reflexive.detect_climax_inflection()

            # ━━━ STEP 2: Neural Swarm Consensus (Ω-33) ━━━
            # Criar contexto para os agentes evoluídos
            ctx = {
                "price": snapshot.close,
                "rsi": snapshot.metadata.get("rsi", 50.0),
                "phi": snapshot.metadata.get("phi", 0.0),
                "bias": bias,
                "reflexivity": self.reflexive.reflexivity_factor,
                "vol": snapshot.vol_gk
            }
            swarm_res = await self.swarm.get_consensus_signal(ctx)

            # ━━━ STEP 3: Quantum Wave Collapse (Ω-2) ━━━
            # Colapsar a função de onda baseado em IG e Entropia
            mc_paths = self.oracle.last_stats.final_outcomes if self.oracle.last_stats else [] 
            
            quantum_input = {
                "swarm_signal": swarm_res["signal"],
                "mc_paths": mc_paths,
                "regime_confidence": 0.8
            }
            quantum_verdict = await self.quantum.run_quantum_gate(quantum_input)
            self.telemetry["quantum_entropy"] = quantum_verdict["entropy"]

            # ━━━ STEP 4: Colapsar QuantumState via Enxame Original ━━━
            quantum_state = await self.orchestrator.get_quantum_state(
                snapshot=snapshot, nexus_context=None
            )
            self._quantum_history.append(quantum_state)

            # ━━━ STEP 5: Identificar Regime ━━━
            regime_state = await self.regime.process_matrix_signal(
                phi=snapshot.metadata.get("phi", 0.0),
                vpin=snapshot.metadata.get("vpin", 0.0),
                urgency=snapshot.metadata.get("urgency", 0.0),
                meta=snapshot.metadata,
            )

            # ━━━ STEP 6: SignalGate — Veredito de Confluência ━━━
            # Injetar Veto Quântico
            if not quantum_verdict["is_authorized"]:
                self._last_verdict = SovereignSignal(action="NONE", confidence=0.0, reasoning="Quantum Uncertainty (IG < Threshold)")
                return

            verdict: SovereignSignal = await self.gate.evaluate(
                snapshot=snapshot,
                quantum_state=quantum_state,
                regime_state_identity=regime_state.identity,
                bayes_conviction=quantum_state.confidence,
            )
            
            # Integrar Clímax de Soros se detectado
            if reflexive_climax and verdict.action == "NONE":
                verdict = SovereignSignal(
                    action=climax_dir.upper(),
                    confidence=climax_conf,
                    reasoning=f"Reflexive Inflection (Soros Climax) R={self.reflexive.reflexivity_factor:.2f}",
                    net_ev=1000.0, # Alta expectativa em clímax
                    metadata={"source": "reflexive"}
                )

            self._last_verdict = verdict

            # ━━━ STEP 7: Decisão de Execução ━━━
            if verdict.action != "NONE":
                # Risk Validation
                can_execute = self.risk.validate_execution()
                if can_execute:
                    lot_size = self.risk.calculate_optimal_sizing(
                        regime_state, matrix_confidence=verdict.confidence
                    )
                    if lot_size > 0 and self.mt5_bridge is not None:
                        # ━━━ STEP 5: ENVIAR ORDEM AO MT5 ━━━
                        ticket = await self.mt5_bridge.execute_order(
                            symbol=self.SYMBOL,
                            side=verdict.action,
                            volume=lot_size,
                        )
                        if ticket:
                            self._trades_executed += 1
                            log.info(
                                f"🚀 [Ω-EXEC] {verdict.action} {self.SYMBOL} | "
                                f"Lots: {lot_size:.2f} | Ticket: #{ticket} | "
                                f"NetEV: ${verdict.net_ev:.2f} | "
                                f"Confidence: {verdict.confidence:.4f}"
                            )
                        else:
                            self._trades_rejected += 1
                            log.warning(f"⚠️ [Ω-REJECT] MT5 rejeitou ordem: {verdict.action} {lot_size}")
                    elif lot_size > 0:
                        # Modo observação (sem MT5)
                        self._trades_rejected += 1
                        log.info(
                            f"👁️ [OBSERVE] {verdict.action} {self.SYMBOL} | "
                            f"Lots: {lot_size:.2f} | NetEV: ${verdict.net_ev:.2f} | "
                            f"(MT5 Offline — modo observação)"
                        )
                    else:
                        self._trades_rejected += 1
                else:
                    self._trades_rejected += 1

        except Exception as e:
            log.error(f"☢️ COGNITIVE_FAULT: {e}")

        # ━━━ Telemetria ━━━
        latency = (time.perf_counter() - t0) * 1000
        self._tick_latencies.append(latency)
        self._update_telemetry(snapshot, quantum_state if 'quantum_state' in dir() else None, latency)

    def _update_telemetry(self, snapshot: MarketData, qs: Optional[QuantumState], latency: float):
        """[C3-T3.1] Atualização atômica da telemetria holográfica."""
        self.telemetry["bridge_latency_ms"] = latency

        if qs:
            self.telemetry["global_confidence"] = qs.confidence

            if qs.signal > 0.15:
                direction = "🟢 BULLISH"
            elif qs.signal < -0.15:
                direction = "🔴 BEARISH"
            else:
                direction = "⚪ NEUTRAL"

            self.telemetry["elite_1_status"] = f"{direction} ({qs.signal:+.3f})"
            self.telemetry["elite_2_status"] = f"Coh:{qs.coherence:.3f} Φ:{qs.phi:+.3f}"

        self.telemetry["regime_label"] = self._last_verdict.metadata.get("regime", "?") if self._last_verdict and self._last_verdict.metadata else "SCANNING"
        self.telemetry["volatility_tensile"] = snapshot.vol_gk if snapshot else 0.0
        self.telemetry["slots_active"] = self._trades_executed

        # Drawdown
        if hasattr(self.risk, 'current_equity') and self.risk.initial_balance > 0:
            dd = (1 - self.risk.current_equity / self.risk.initial_balance) * 100
            self.telemetry["drawdown_pct"] = max(0.0, dd)

        # Log
        if self._last_verdict:
            self.telemetry["last_log"] = (
                f"#{self._cognitive_ticks:04d} "
                f"{self._last_verdict.action} | "
                f"Conf:{self._last_verdict.confidence:.3f} | "
                f"{self._last_verdict.reasoning[:60]}"
            )

    # ═══════════════════════════════════════════════════════════════
    # CONCEITO 3: TELEMETRIA E BACKGROUND LOOPS
    # ═══════════════════════════════════════════════════════════════

    async def _mt5_equity_sync_loop(self):
        """[C3-T3.2] Sincronização de equity MT5 → RiskManager."""
        while self._is_running and self.mt5_bridge:
            try:
                info = self.mt5_bridge.account_info
                if info and info.connected:
                    await self.risk.update_equity(info.equity)
                    self.telemetry["live_pnl"] = info.equity - self.risk.initial_balance
            except Exception as e:
                log.error(f"☢️ Equity Sync Fault: {e}")
            await asyncio.sleep(1.0)

    async def _system_health_monitor(self):
        """[C3-T3.4] SRE Monitoring (CPU/RAM)."""
        while self._is_running:
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            if cpu > 90:
                log.warning(f"⚠️ [SRE] CPU crítico: {cpu}%")
            if mem > 90:
                log.warning(f"⚠️ [SRE] RAM crítico: {mem}%")
            await asyncio.sleep(5.0)

    async def _ui_render_loop(self):
        """[C3-T3.1] Dashboard Matrix O(1) @ 10 FPS."""
        while self._is_running:
            try:
                SolennTerminalMatrix.render_tactical_dashboard(self.telemetry)
            except Exception:
                pass
            await asyncio.sleep(0.1)

    async def _periodic_report(self):
        """[C3-T3.3] Relatório periódico a cada 30 segundos."""
        while self._is_running:
            await asyncio.sleep(30)
            if self._tick_latencies:
                arr = np.array(list(self._tick_latencies))
                n_synapses = len(self.orchestrator.synapses)
                log.info(
                    f"📊 [REPORT] Ticks:{self._cognitive_ticks} | "
                    f"Synapses:{n_synapses} | "
                    f"Executed:{self._trades_executed} | "
                    f"Rejected:{self._trades_rejected} | "
                    f"Lat P50:{np.median(arr):.2f}ms P99:{np.percentile(arr, 99):.2f}ms"
                )

                # Byzantine health summary
                byz = self.orchestrator.byzantine
                if byz.reputation:
                    honest = sum(1 for r in byz.reputation.values() if r.status.value == "HONEST")
                    total = len(byz.reputation)
                    log.info(f"🛡️ Byzantine: {honest}/{total} honestos")

    # ═══════════════════════════════════════════════════════════════
    # CICLO DE VIDA PRINCIPAL
    # ═══════════════════════════════════════════════════════════════

    async def run(self):
        """[Ω-MAIN] O Maestro Soberano desperta."""
        # ━━━ FASE 0: Redirecionamento de Logs (Matrix UI Resilience) ━━━
        if sys.stdout.isatty():
            # Limpar handlers existentes para o root e adicionar o MatrixHandler
            root_logger = logging.getLogger()
            # Guardamos os handlers originais para restauração se necessário
            original_handlers = root_logger.handlers[:]
            
            # Criar e configurar o handler da Matrix
            matrix_handler = MatrixLogHandler()
            matrix_handler.setFormatter(logging.Formatter('%(message)s'))
            
            # Adicionar apenas o MatrixHandler e o FileHandler
            root_logger.handlers = [h for h in original_handlers if isinstance(h, logging.FileHandler)]
            root_logger.addHandler(matrix_handler)

        log.info("=" * 78)
        log.info("   ██████╗ ██████╗ ██╗     ███████╗███╗   ██╗███╗   ██╗")
        log.info("   ██╔════╝██╔═══██╗██║     ██╔════╝████╗  ██║████╗  ██║")
        log.info("   ███████╗██║   ██║██║     █████╗  ██╔██╗ ██║██╔██╗ ██║")
        log.info("   ╚════██║██║   ██║██║     ██╔══╝  ██║╚██╗██║██║╚██╗██║")
        log.info("   ██████╔╝╚██████╔╝███████╗███████╗██║ ╚████║██║ ╚████║")
        log.info("   ╚═════╝  ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═══╝╚═╝  ╚═══╝")
        log.info("=" * 78)
        log.info("   [Ω-SOLÉNN] ORGANISMO COGNITIVO FINANCEIRO — DESPERTAR TOTAL")
        log.info("=" * 78)

        self._is_running = True

        # Boot Sequence Visual
        try:
            SolennTerminalMatrix.boot_sequence()
        except Exception:
            pass

        # ━━━ FASE 1: Gênese das Sinapses ━━━
        await self._genesis_synapses()

        # ━━━ FASE 2: Handshake MT5 ━━━
        mt5_online = await self._genesis_mt5()
        mode = "EXECUÇÃO AO VIVO" if mt5_online else "OBSERVAÇÃO (MT5 Offline)"
        log.info(f"  🎯 Modo de operação: {mode}")

        # ━━━ FASE 3: Consciência Ω ━━━
        await self._genesis_consciousness()

        # ━━━ FASE 4: Sensor + Pipeline ━━━
        await self._genesis_sensor()

        # ━━━ Background Tasks ━━━
        asyncio.create_task(self._ui_render_loop())
        asyncio.create_task(self._periodic_report())

        log.info("=" * 78)
        log.info("   [Ω-ACTIVE] SOLÉNN Ω OPERACIONAL — TODOS OS ÓRGÃOS ESTÃO VIVOS.")
        log.info("   Pipeline: Binance → DataEngine → 15 Sinapses → SignalGate → Risk → MT5")
        log.info(f"   Modo: {mode}")
        log.info("   Ctrl+C para Shutdown Gracioso.")
        log.info("=" * 78)

        # ━━━ Heartbeat ━━━
        try:
            while self._is_running:
                await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            log.warning("Consciência interrompida via Cancel.")
        except Exception as e:
            log.error(f"☢️ MAIN_LOOP_FAULT: {e}")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """[C1-T1.6] Graceful Shutdown: desacoplar todos os órgãos."""
        log.info("━" * 60)
        log.info("  [Ω-SHUTDOWN] Desmontagem Sistêmica Iniciada")
        log.info("━" * 60)

        self._is_running = False

        # 1. Sensor
        try:
            await self.sensor.disconnect()
            log.info("  ✅ Sensor Binance desconectado.")
        except Exception as e:
            log.error(f"  ☢️ Sensor shutdown fault: {e}")

        # 2. DataEngine
        try:
            await self.data_engine.stop()
            log.info("  ✅ OmniDataEngine parado.")
        except Exception as e:
            log.error(f"  ☢️ DataEngine shutdown fault: {e}")

        # 3. Orchestrator
        try:
            await self.orchestrator.shutdown()
            log.info("  ✅ SwarmOrchestrator encerrado.")
        except Exception as e:
            log.error(f"  ☢️ Orchestrator shutdown fault: {e}")

        # 4. MT5
        if self.mt5_bridge:
            try:
                await self.mt5_bridge.stop()
                log.info("  ✅ MetaBridge MT5 hibernada.")
            except Exception as e:
                log.error(f"  ☢️ MT5 shutdown fault: {e}")

        # 5. Relatório Final
        self._print_final_report()

        # 6. Restaurar Terminal
        try:
            SolennTerminalMatrix.restore()
        except Exception:
            pass

        log.info("━" * 60)
        log.info("  SOLÉNN — A serenidade de quem já sabe o resultado antes da execução.")
        log.info("━" * 60)

    def _print_final_report(self):
        """[C3-T3.3] Relatório final do organismo."""
        log.info("")
        log.info("=" * 78)
        log.info("   [Ω-SOLÉNN] RELATÓRIO FINAL DO ORGANISMO")
        log.info("=" * 78)
        log.info(f"  📊 Ticks cognitivos processados: {self._cognitive_ticks}")
        log.info(f"  🚀 Trades executados: {self._trades_executed}")
        log.info(f"  ⛔ Trades rejeitados: {self._trades_rejected}")
        log.info(f"  🧬 Sinapses ativas: {len(self.orchestrator.synapses)}")

        if self._tick_latencies:
            arr = np.array(list(self._tick_latencies))
            log.info(f"  ⚡ Latência Cognitiva:")
            log.info(f"     P50: {np.median(arr):.3f}ms")
            log.info(f"     P95: {np.percentile(arr, 95):.3f}ms")
            log.info(f"     P99: {np.percentile(arr, 99):.3f}ms")
            log.info(f"     Max: {np.max(arr):.3f}ms")

        if self._quantum_history:
            signals = np.array([qs.signal for qs in self._quantum_history])
            confs = np.array([qs.confidence for qs in self._quantum_history])
            cohs = np.array([qs.coherence for qs in self._quantum_history])
            log.info(f"  🌊 QuantumState Distribution (últimos {len(self._quantum_history)}):")
            log.info(f"     Signal → μ:{np.mean(signals):+.4f} σ:{np.std(signals):.4f}")
            log.info(f"     Conf   → μ:{np.mean(confs):.4f}  σ:{np.std(confs):.4f}")
            log.info(f"     Coher  → μ:{np.mean(cohs):.4f}  σ:{np.std(cohs):.4f}")

            bullish_pct = np.mean(signals > 0.1) * 100
            bearish_pct = np.mean(signals < -0.1) * 100
            neutral_pct = 100 - bullish_pct - bearish_pct
            log.info(f"  📈 Bias: 🟢 Bull:{bullish_pct:.1f}% | 🔴 Bear:{bearish_pct:.1f}% | ⚪ Neutral:{neutral_pct:.1f}%")

        # Byzantine Health
        byz = self.orchestrator.byzantine
        if byz.reputation:
            log.info(f"  🛡️ Saúde Bizantina ({len(byz.reputation)} agentes):")
            for name, rep in sorted(byz.reputation.items(), key=lambda x: x[1].trust_score, reverse=True):
                icon = "✅" if rep.status.value == "HONEST" else "⚠️" if rep.status.value == "NOISY" else "❌"
                log.info(f"     {icon} {name:30s} Trust:{rep.trust_score:.3f} Outliers:{rep.consecutive_outliers}")

        log.info("=" * 78)


if __name__ == "__main__":
    organism = SolennOmega()
    try:
        asyncio.run(organism.run())
    except (KeyboardInterrupt, SystemExit):
        try:
            SolennTerminalMatrix.restore()
        except Exception:
            pass
        log.info("⛔ SOLÉNN interrompida pelo CEO (Ctrl+C).")
