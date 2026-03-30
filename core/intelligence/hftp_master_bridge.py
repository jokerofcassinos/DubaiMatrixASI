"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              SOLÉNN — HFTP MASTER BRIDGE Ω (SOVEREIGN CENTER)                ║
║     Master Bridge: Centralizing Connectivity, Data & Execution               ║
║     Implementing: Full Stack Integration (Server, Tel, OMS, Acc, Health)     ║
║     Framework 3-6-9: Phase 4(Ω-21) - Sovereign Core                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from core.intelligence.hftp_server import HFTPServer
from core.intelligence.telemetry_manager import TelemetryManager
from core.intelligence.oms_engine import OMSEngine
from core.intelligence.account_manager import AccountManager
from core.intelligence.health_guard import HealthGuard
from market.data_engine import DataEngine

class HFTPMasterBridge:
    """
    [Ω-SOVEREIGN] The Master Orchestrator of Connectivity.
    Integrates all HFT-P components into a single, unified interface for the Brain.
    """
    def __init__(self, symbol: str, host: str = "127.0.0.1", port: int = 5555):
        self.symbol = symbol
        self.logger = logging.getLogger("SOLENN.MasterBridge")
        
        # 1. Connectivity Layer (Sovereign Portal)
        self.server = HFTPServer(host=host, port=port)
        
        # 2. Perceptual Layer (Cortex)
        self.cortex = DataEngine(symbol=symbol)
        
        # 3. Capital Layer (Sovereign Account)
        self.account = AccountManager(hftp_server=self.server)
        
        # 4. Execution Layer (Sovereign OMS)
        self.execution = OMSEngine(hftp_server=self.server)
        
        # 5. SRE Layer (Health Guard)
        self.guardian = HealthGuard(hftp=self.server, oms=self.execution)
        
        # 6. Synchronization Layer (Telemetry Manager)
        self.telemetry = TelemetryManager(
            hftp=self.server, 
            data_engine=self.cortex, 
            oms=self.execution
        )
        
        self.logger.info(f"💎 HFTP Master Bridge Ω for {symbol} Ready (Port {port})")

    async def start(self):
        """Launches the entire connectivity stack (Phase 4)."""
        self.logger.info("⚡ Powering up Sovereign Bridge Ω...")
        
        # Order of operations is critical
        await self.telemetry.start()
        await self.guardian.start()
        
        # Start Server in background
        asyncio.create_task(self.server.start())
        
        self.logger.info("🚀 SOLÉNN Ω is now listening for MQL5 Agents.")

    async def submit_trade(self, 
                           trace_id: str, 
                           action: str, 
                           lot: float, 
                           sl: float = 0.0, 
                           tp: float = 0.0) -> bool:
        """[Ω-Decision-Link] High-level entry for TrinityCore."""
        if not self.guardian.is_healthy():
            self.logger.error(f"☢️ Blocked trade {trace_id} - System UNHEALTHY.")
            return False
            
        # Get first client (or specific based on symbol/account)
        if not self.server._clients:
            self.logger.error("🚫 No EAs connected. Order rejected.")
            return False
            
        client_id = list(self.server._clients.keys())[0]
        return await self.execution.submit_order(trace_id, self.symbol, action, lot, sl, tp, client_id)

    async def stop(self):
        """Total shutdown."""
        await self.telemetry.stop()
        await self.server.stop()
        self.logger.info("🛑 Sovereign Bridge Ω Shutdown.")
