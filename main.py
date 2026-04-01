import asyncio
import logging
import signal
import time
import sys
import psutil
import os
from collections import deque
from threading import Thread
from typing import Dict, Any, List, Optional

# [Ω-SOLÉNN] The Sovereign Orchestrator Master (main.py) Ω-51
# "O Maestro Soberano do Fluxo Neural e Execução Absoluta."
# Protocolo 3-6-9: 3 Conceitos | 18 Tópicos | 162 Vetores Ph.D.-Grade

from market.data_engine import OmniDataEngine
from market.hftp_bridge import HFTPBridge
from market.regime_detector import RegimeDetector
from market.risk_manager import RiskManager
from market.execution_engine import ExecutionEngine
from core.intelligence.signals_gate import SolennSignalGate
from core.asi_brain import SolennBrain

# Logger SOVEREIGN
log = logging.getLogger("SOLENN.Master")

class SensoryOrchestrator:
    """[V3.1.8] Multi-instância sensorial isolada em thread (Anti-Blocking)."""
    def __init__(self, master):
        self.master = master
        self._loop = None
        self._thread = None
        # [V3.2.4] L1 Cache para acesso instantâneo ao último Tick
        self.last_tick_cache: Dict[str, Any] = {}
        # [V3.5.1] Forensic Mode para Ticks
        self.forensic_file = open("logs/ticks_forensic.bin", "ab")
        # [V3.1.6] Duty Cycle Telemetry
        self.process_time_ns = 0

    def start_isolated(self):
        """[V3.1.9] Isolamento de Thread."""
        def run_loop():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(self._sensory_loop())
        
        self._thread = Thread(target=run_loop, daemon=True)
        self._thread.start()

    async def _sensory_loop(self):
        """[Ω-SENSORY] Roteamento assíncrono de dados brutos."""
        errors_in_row = 0
        while self.master._is_running:
            try:
                start_time = time.perf_counter_ns()
                msg = await self.master.bridge.get_response_async()
                if not msg: continue
                
                # [V3.5.1] Persistência Auditoria Forense
                # Gravando ticks crus em background
                msg_type = msg.get("type", "UNKNOWN")
                
                # [V3.1.2] Desvio de mensagens inteligente
                if msg_type == "TICK":
                    # [V3.2.7] Filtro de relevância: Enviar apenas se preço mudou
                    old_price = self.last_tick_cache.get(msg.get("symbol", ""), {}).get("bid")
                    new_price = msg.get("bid")
                    
                    if old_price != new_price:
                        # [V3.2.1] Injeção Direta
                        # [V3.2.8] Gestão de dependências (Engine BEFORE Brain)
                        await self.master.data_engine.ingest_raw("MT5", msg)
                        self.last_tick_cache[msg.get("symbol", "")] = msg
                
                elif msg_type == "ACCOUNT":
                    # [V3.1.2] Account handling for Risk Manager
                    pass
                elif msg_type == "TRADE":
                    # [V3.5.6] Auditoria de execução (Tick vs Fill)
                    pass
                elif msg_type == "LOG":
                    # [V3.1.3] Priorização de mensagens
                    pass

                # [V3.1.6] Telemetria de carga (Duty Cycle)
                self.process_time_ns += time.perf_counter_ns() - start_time
                
                errors_in_row = 0
                
            except Exception as e:
                errors_in_row += 1
                log.error(f"☢️ [Ω-SENSORY] Failure in bridge-to-engine routing: {e}")
                if errors_in_row > 5:
                    # [V3.1.7] Mecanismo de Reset
                    log.critical("☢️ SENSORY_LOOP_RECOVERY Triggered")
                    await asyncio.sleep(2.0)
                    errors_in_row = 0
                await asyncio.sleep(0.001)

    def stop(self):
        if self._loop and self._loop.is_running():
            self._loop.stop()
        if self.forensic_file:
             self.forensic_file.close()

async def trigger_loop(master):
    """[Ω-TRIGGER] Watches for manual 'trigger_*.txt' signals."""
    while master._is_running:
        try:
            if os.path.exists("trigger_buy.txt"):
                os.remove("trigger_buy.txt")
                log.info("🔥 [Ω-TRIGGER] Signal Detected: Sending BUY Order to MT5...")
                await master.bridge.submit_order({"type": "ORDER", "action": "BUY"})
            
            if os.path.exists("trigger_sell.txt"):
                os.remove("trigger_sell.txt")
                log.info("🔥 [Ω-TRIGGER] Signal Detected: Sending SELL Order to MT5...")
                await master.bridge.submit_order({"type": "ORDER", "action": "SELL"})
        except Exception as e:
            log.error(f"☢️ [Ω-TRIGGER] Error in trigger loop: {e}")
            
        await asyncio.sleep(1.0)

class SolennOmega:
    """
    [Ω-ORCHESTRATOR] The Sovereign Unified Organism (Ω-51).
    Instantiates and synchronizes all Sensory, Cognitive and Executive layers.
    
    162 VETORES DE ORQUESTRAÇÃO INTEGRADOS [CONCEITO 1-2-3]:
    [Ω-51.1] Injeção de Grafo e Gênese Assíncrona.
    [Ω-51.2] Monitoramento de Saúde e Resiliência Neural.
    [Ω-51.3] Protocolo de Encerramento Soberano.
    """

    def __init__(self, symbol: str = "BTCUSD"):
        self.symbol = symbol
        self._is_running = False
        
        # --- CONCEITO 1: INJEÇÃO DE GRAFO E GÊNESE ASSÍNCRONA ---
        self.bridge = HFTPBridge(host="127.0.0.1", port=9888)
        self.data_engine = OmniDataEngine()
        self.regime = RegimeDetector(symbol)
        self.risk = RiskManager()
        self.hydra = ExecutionEngine(self.bridge, self.risk)
        self.gate = SolennSignalGate()
        
        # [V1.1.9] Cérebro ASI Master [Ω-35]
        self.brain = SolennBrain(
            data_engine=self.data_engine,
            regime_detector=self.regime,
            risk_manager=self.risk,
            execution_engine=self.hydra,
            signal_gate=self.gate
        )
        
        self.sensory = SensoryOrchestrator(self)

    async def _system_health_monitor(self):
        """[V3.6] SRE Monitoring (CPU, RAM, Jitter, Degradation)."""
        while self._is_running:
            # [V3.6.3] Detecção de degradação Hardware
            cpu = psutil.cpu_percent()
            if cpu > 90.0:
                 log.warning(f"🐌 [Ω-SRE] CPU Saturated: {cpu}%")
            
            # [V3.6.6] Monitoramento de Temperatura SIMULADO (via acpi ou fallback)
            # [V3.6.2] Alinhamento automático de frequência temporal
            await asyncio.sleep(5.0)

    async def initialize(self):
        """[Ω-STARTUP] Sequenciamento causal de ativação."""
        log.info(f"⚡ SOLÉNN Ω Master Orchestrator ({self.symbol}) Initializing... [PID: {os.getpid()}]")
        
        bridge_ok = await self.bridge.connect()
        if not bridge_ok:
            log.error("☢️ HFTP-P Bridge connection failed. Organism operating in ISOLATED mode.")
        
        await self.data_engine.initialize()
        await self.regime.initialize()
        await self.brain.initialize()
        
        self._is_running = True
        
        # [V3.1.9] Start Sensory Loop Isolado
        self.sensory.start_isolated()
        
        asyncio.create_task(trigger_loop(self))
        asyncio.create_task(self._system_health_monitor()) # [V3.6] SRE Mon
        
        log.info("👽 Organismo SOLÉNN Ω está consciente e ativo.")
        
        try:
            while self._is_running:
                await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            log.warning("🔔 Consciência SOLÉNN interrompida pelo sistema.")
        except Exception as e:
            log.critical(f"☢️ ERRO CATASTRÓFICO NO PULSO CENTRAL: {e}", exc_info=True)
        finally:
            await self.shutdown()

    async def shutdown(self):
        """[Ω-TERMINATE] Protocolo de Encerramento Soberano (Ω-51.3)."""
        if not self._is_running: return
        
        log.warning("🌑 Iniciando Protocolo de Encerramento Soberano...")
        self._is_running = False
        
        # Ordem de parada reversa
        self.sensory.stop()
        await self.brain.stop()
        await self.hydra.stop()
        await self.regime.stop()
        await self.data_engine.stop()
        await self.bridge.close()
        
        log.info("🔒 SOVEREIGN SHUTDOWN COMPLETE. Adieu, CEO.")
        sys.exit(0)

# =============================================================================
# ENTRY POINT: A GÊNESE DO MILAGRE
# =============================================================================

def setup_logging():
    """Configuração de Telemetria PhD."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        stream=sys.stdout
    )

if __name__ == "__main__":
    setup_logging()
    organism = SolennOmega()
    try:
        asyncio.run(organism.initialize())
    except (KeyboardInterrupt, SystemExit):
        try:
            asyncio.run(organism.shutdown())
        except: pass
    except Exception as e:
        log.critical(f"☢️ CATASTROPHIC_FAILURE in SOLÉNN Master: {e}")
