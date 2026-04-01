import asyncio
import logging
import signal
import time
import sys
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
import os

async def trigger_loop(master):
    """[Ω-TRIGGER] Watches for 'trigger_buy.txt' or 'trigger_sell.txt' to fire test orders."""
    while master._is_running:
        try:
            if os.path.exists("trigger_buy.txt"):
                os.remove("trigger_buy.txt")
                log.info("🔥 [Ω-TRIGGER] Signal Detected: Sending BUY Order to MT5 (Plan-Text Header Mode)...")
                header = b"ORDER:BUY\x00"
                await master.bridge.submit_raw_order(header)
            
            if os.path.exists("trigger_sell.txt"):
                os.remove("trigger_sell.txt")
                log.info("🔥 [Ω-TRIGGER] Signal Detected: Sending SELL Order to MT5 (Plan-Text Header Mode)...")
                header = b"ORDER:SELL\x00"
                await master.bridge.submit_raw_order(header)
        except Exception as e:
            log.error(f"☢️ [Ω-TRIGGER] Error in trigger loop: {e}")
            
        await asyncio.sleep(1.0)

# Logger SOVEREIGN
log = logging.getLogger("SOLENN.Master")

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
        # [V1.1.1] Instanciação Master (Ω-13, Ω-6, Ω-4, Ω-5)
        self.bridge = HFTPBridge()
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

    async def initialize(self):
        """[Ω-STARTUP] Sequenciamento causal de ativação."""
        log.info(f"⚡ SOLÉNN Ω Master Orchestrator ({self.symbol}) Initializing...")
        
        # --- CONCEITO 2: MONITORAMENTO DE SAÚDE E RESILIÊNCIA NEURAL ---
        # [V2.2.1] Conexão com o Matrix MT5 (HFT-P Bridge)
        bridge_ok = await self.bridge.connect()
        if not bridge_ok:
            log.error("☢️ HFTP-P Bridge connection failed. Organism operating in ISOLATED mode.")
            # Dependendo da estratégia, aqui poderíamos pausar ou proceder em modo Shadow
        
        # [V2.3.5] Inicialização dos Órgãos Perceptivos
        await self.data_engine.initialize()
        await self.regime.initialize()
        
        # [V2.3.9] Ativação Cerebral (Master Heartbeat)
        await self.brain.initialize()
        
        self._is_running = True
        
        # [Ω-TRIGGER] Start the Sovereign Trigger loop in background
        asyncio.create_task(trigger_loop(self))
        
        log.info("👽 Organismo SOLÉNN Ω está consciente e ativo.")
        
        # [V2.1.162] Monitoramento contínuo de vitalidade
        while self._is_running:
            await asyncio.sleep(1.0)
            # Todo: Integrar telemetria de vitalidade centralizada

    async def shutdown(self):
        """[Ω-TERMINATE] Protocolo de Encerramento Soberano (Ω-51.3)."""
        if not self._is_running: return
        
        log.warning("🌑 Iniciando Protocolo de Encerramento Soberano...")
        self._is_running = False
        
        # --- CONCEITO 3: PROTOCOLO DE ENCERRAMENTO SOBERANO ---
        # [V3.3.1] Ordem de desligamento por prioridade inversa de impacto
        await self.brain.stop()
        await self.hydra.stop()
        await self.regime.stop()
        await self.data_engine.stop()
        
        # [V3.3.9] Fechamento da Ponte de Execução
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
    
    # [Ω-BOOT] Gênese da Realidade Financeira
    organism = SolennOmega()
    try:
        asyncio.run(organism.initialize())
    except (KeyboardInterrupt, SystemExit):
        # [V3.3.1] Shutdown forçado pela interface (CEO)
        # O runner do initialize encerrou o loop; criamos um para o shutdown
        try:
            asyncio.run(organism.shutdown())
        except: pass
    except Exception as e:
        log.critical(f"☢️ CATASTROPHIC_FAILURE in SOLÉNN Master: {e}")
        # Investigações forenses seriam disparadas aqui [Ω-FORENSIC]
