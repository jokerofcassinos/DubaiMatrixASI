"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              SOLÉNN — TELEMETRY MANAGER Ω (SENSORY ORCHESTRATION)            ║
║     Telemetry Manager: DataEngine & HFT-P Sychronization                     ║
║     Implementing: Tick Streaming, Latency Monitoring, Sequence Consistency   ║
║     Framework 3-6-9: Phase 4(Ω-21) - Concept 1.2                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, List
from market.data_engine import DataEngine, MarketSnapshot
from core.intelligence.hftp_server import HFTPServer
from core.intelligence.oms_engine import OMSEngine

class TelemetryManager:
    """
    [Ω-CORE] Sensory Orchestrator.
    Wires the HFT-P Server with the DataEngine and OMS.
    """
    def __init__(self, hftp: HFTPServer, data_engine: DataEngine, oms: OMSEngine):
        self.hftp = hftp
        self.data_engine = data_engine
        self.oms = oms
        self.logger = logging.getLogger("SOLENN.Telemetry")
        
        # [Ω-V1.2.9] Sequence consistency
        self._last_tick_seq = 0
        self._stale_threshold_ms = 100.0 # 100ms [Ω-V1.2.8]
        
        # [Ω-V1.2.6] Distribution Pipeline
        self.hftp.register_handler("TICK", self._on_tick_received)
        self.hftp.register_handler("RESPONSE", self._on_oms_response)
        
        self.logger.info("📡 Telemetry Manager Ω Online (Sync 1:1)")

    async def _on_tick_received(self, payload: Dict[str, Any], client_id: str):
        """[Ω-V1.2.1] Real-time binary tick ingestion."""
        
        # 1. Sequence Validation [Ω-V1.2.9]
        seq = payload.get("seq", 0)
        if seq <= self._last_tick_seq and seq != 0:
            self.logger.warning(f"⚠️ [Ω-Tel] Out of Order Tick: {seq} <= {self._last_tick_seq}")
            # Optional: Drop or log out-of-order data
        self._last_tick_seq = seq
        
        # 2. Arrival Timestamp [Ω-V1.2.5]
        arrival_ts = time.time()
        source_ts_msc = payload.get("time_msc", 0)
        
        # 3. Stale Detection [Ω-V1.2.8]
        if source_ts_msc > 0:
            latency = (arrival_ts * 1000) - source_ts_msc
            if latency > self._stale_threshold_ms:
                self.logger.error(f"🚨 [Ω-Tel] Stale Data Detected: {latency:.2f}ms latency")
        
        # 4. Ingest into Cortex [Ω-V1.2.1]
        await self.data_engine.ingest_tick(payload)

    async def _on_oms_response(self, payload: Dict[str, Any], client_id: str):
        """[Ω-V1.3.4] Directs OMS responses to the engine for state syncing."""
        await self.oms.handle_response(payload)

    async def start(self):
        """Launches the sensory loop."""
        await self.data_engine.start()
        self.logger.info("🧠 Cortex (DataEngine) Activated via Telemetry.")

    async def stop(self):
        """Graceful shutdown."""
        await self.data_engine.stop()
        self.logger.info("🛑 Telemetry Manager Shutdown.")
