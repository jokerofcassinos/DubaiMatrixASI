import asyncio
import logging
import time
import os
import signal
from typing import Dict, Any, Optional

# [Ω-SOLÉNN] The Sovereign Artificial Financial Superintelligence
# v2.1.2.v2.1.3.1.4.1 (Integrated Swarm + Fractal + Hydra)

from market.data_engine import DataEngine
from market.hftp_bridge import HFTPBridge
from core.solenn_regime import SolennRegime
from core.intelligence.swarm_orchestrator import SwarmOrchestrator
from core.intelligence.nexus_resonance import NexusResonance
from core.decision.trinity_core import TrinityCore
from core.intelligence.elite.fractal_synapse import FractalSynapse
from core.intelligence.elite.trend_synapse import TrendSynapse
from core.intelligence.elite.volatility_synapse import VolatilitySynapse
from core.intelligence.elite.nexus_synapse import NexusSynapse
from core.risk.risk_sanctum import RiskSanctum
from core.execution.hydra_engine import HydraEngine
from core.execution.hydra_oms import HydraOMS, OrderIntent, OrderStatus
from core.execution.wormhole_router import WormholeRouter
from core.intelligence.account_manager import AccountManager
from core.consciousness.monte_carlo_engine import MonteCarloEngine
from core.consciousness.genetic_forge import GeneticForge
from core.consciousness.neural_swarm import NeuralSwarm
from core.consciousness.reflexive_loop import ReflexiveLoop
from core.consciousness.state_observer import StateObserver
from core.evolution.performance_tracker import PerformanceTracker
from core.telemetry.lifecycle_logger import LifecycleLogger

# [Ω-SENSORS] Ecosystem Scrapers
from market.scraper.macro_scraper import MacroScraper
from market.scraper.onchain_scraper import OnChainScraper
from market.scraper.sentiment_scraper import SentimentScraper
from core.resonance_orchestrator import ResonanceOrchestrator

class SolennOmega:
    """
    [Ω-ENTITY] The Unified Organism of SOLÉNN.
    Integrating 30+ Founding Minds into a single Operational Singularity.
    """

    def __init__(self, symbol: str = "BTCUSDT"):
        self.symbol = symbol
        self.logger = logging.getLogger("SOLENN.Core")
        
        # 1. Sensory Perception (DataEngine)
        self.engine = DataEngine(symbol)
        
        # 2. Institutional Bridge (HFTP-P Server)
        self.bridge = HFTPBridge()
        
        # 3. Intelligence Layers (Regime + Swarm + Nexus + Monte Carlo + Genetic Forge)
        self.account = AccountManager(self.bridge)
        self.monte_carlo = MonteCarloEngine()
        self.forge = GeneticForge()
        self.neural_swarm = NeuralSwarm()
        self.reflex_loop = ReflexiveLoop()
        self.observer = StateObserver()
        self.performance = PerformanceTracker()
        self.regime = SolennRegime()
        
        # [Ω-RESONANCE] The Third Eye (Ecosystem Consciousness)
        self.macro = MacroScraper()
        self.onchain = OnChainScraper()
        self.sentiment = SentimentScraper()
        self.resonance = ResonanceOrchestrator(scrapers={
            "macro": self.macro,
            "onchain": self.onchain,
            "sentiment": self.sentiment
        })
        self.trinity = TrinityCore()
        self.swarm = SwarmOrchestrator()
        self.nexus = NexusResonance()
        
        # [Ω-ELITE-FORMATION] Registering Founding Minds
        self.swarm.register_synapse(FractalSynapse())
        self.swarm.register_synapse(TrendSynapse())
        self.swarm.register_synapse(VolatilitySynapse())
        self.swarm.register_synapse(NexusSynapse())
        
        # 4. Risk & Execution (Sanctum + Hydra + Wormhole)
        self.risk = RiskSanctum()
        self.hydra = HydraEngine()
        self.oms = HydraOMS(self.bridge)
        self.wormhole = WormholeRouter(self.bridge)
        
        # 5. Telemetry & Sovereignty
        self.telemetry = LifecycleLogger()
        self._is_running = True

    async def run(self):
        """[Ω-LOOP] The continuous cognitive cycle of alpha extraction."""
        self.logger.info("⚡ SOLÉNN Ω Initializing. Sovereignty standing by.")
        
        # Connect to MT5 Bridge [V073]
        if not await self.bridge.connect():
             self.logger.error("☢️ HFTP-P Connection Failed. Entering OBSERVER mode.")
        
        # 4. Neural Swarm Population [Ω-C1-T1.2]
        self.neural_swarm.populate(self.forge.hall_of_fame)
        self.swarm.attach_genetic_swarm(self.neural_swarm)
        
        # Start Background Tasks [Ω-C3-T3.1.5]
        asyncio.create_task(self.oms.reconcile())
        asyncio.create_task(self.monte_carlo.start_background_loop(self.account))
        asyncio.create_task(self.forge.start_background_forge(self.engine))
        await self.nexus.start()
        
        try:
            while self._is_running:
                # Start Cognitive Cycle Heart Monitoring [Ω-C2-V055]
                cycle_start = time.time()
                
                # Step 0: Sensory Ingestion (Simulation for test/v2 startup)
                raw_tick = {"time": cycle_start, "price": 65000.0, "spread": 2.0, "volume": 1.5}
                self.engine.update(raw_tick)
                
                snapshot = self.engine.get_snapshot()
                if not snapshot:
                    await asyncio.sleep(0.1)
                    continue

                # Step 1: Regime Identification (Ω-4)
                regime_state = self.regime.identify(snapshot)
                
                # Step 2: Nexus Global Context (Ω-NEXUS)
                nexus_context = self.nexus.get_context()
                
                # Step 2.1: Reflexive Dynamics (Ω-SOROS-LOOP)
                taker_buy = getattr(snapshot, "buy_volume", 0)
                taker_sell = getattr(snapshot, "sell_volume", 0)
                bias = self.reflex_loop.calculate_cognitive_bias(taker_buy, taker_sell, snapshot.spread)
                self.reflex_loop.update_dynamics(snapshot.price, bias)
                snapshot.metadata.update(self.reflex_loop.get_state_context())
                
                # Step 3: Swarm Consensus (Ω-CORTEX)
                quantum_state = await self.swarm.get_quantum_state(snapshot, nexus_context)

                # Step 3.5: Trinity Decision (Ω-GRAVITY-VETO)
                decision = await self.trinity.decide(quantum_state, self.regime, snapshot, res_snapshot)

                # Step 4: Risk Sanctum Assessment (Ω-FORTRESS)
                risk_report = await self.risk.assess(decision, snapshot, self.account)
                
                # Step 4: Hydra Path Analysis (Ω-HYDRA)
                exec_path = self.hydra.analyze_execution_path(decision, snapshot)
                
                # Step 5: Execution Protocol [Ω-C2-V055-V108]
                if decision.action.value != "WAIT" and risk_report.is_safe and exec_path["authorize"]:
                    intent = OrderIntent(
                        trace_id=f"SOLENN_{int(time.time()*1000)}",
                        symbol=self.symbol,
                        action=decision.action.value,
                        lot=risk_report.lot_size,
                        type=exec_path["type"],
                        sl=risk_report.stop_loss,
                        tp=risk_report.take_profit
                    )
                    
                    # Log Intent to Causal Tracing
                    self.telemetry.trace_event("HYDRA_ORDER_INTENT", intent.__dict__)
                    
                    # Execute binary command [V074]
                    success = await self.bridge.execute(intent.__dict__)
                    if success:
                        await self.oms.register_intent(intent)
                        # Protect via Wormhole [V145]
                        self.wormhole.register_position(int(time.time()), intent.__dict__)

                # Step 6: Position Protection (Wormhole Ω) [V109-V135]
                await self.wormhole.pulse_defense(snapshot)

                # Step 7: Evolutionary Feedback (Performance Ω) [V109]
                # In production, check for closed trades and register
                # if trade_closed: self.performance.register_trade(outcome)

                # Cognitive Cycle Complete: Pulse Heart [V112]
                self.observer.heart_pulse(cycle_start)
                health_report = self.observer.get_health_report()
                if health_report["safe_mode"]:
                    self.logger.critical("☢️ SAFE MODE TRIGGERED BY OBSERVER. HIBERNATING.")
                    break

                # Cognitive Throttling (Budget Control)
                await asyncio.sleep(0.01) # 10ms loop speed

        except asyncio.CancelledError:
            self.logger.info("🌑 SOLÉNN Ω Shutting Down Orderly.")
        finally:
            await self.shutdown()

    async def shutdown(self):
        self._is_running = False
        await self.bridge.close()
        await self.oms.stop()
        self.logger.info("🔒 SOVEREIGN SHUTDOWN COMPLETE.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
    
    bot = SolennOmega()
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        pass
