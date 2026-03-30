"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              SOLÉNN — HEALTH GUARD Ω (SRE RESILIENCE)                        ║
║     Health Monitoring: Heartbeat, Failover, Circuit Breakers                 ║
║     Implementing: Heartbeat Failure Detection, Guardrail Enforcement          ║
║     Framework 3-6-9: Phase 4(Ω-21) - Concept 1.5                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional
from core.intelligence.hftp_server import HFTPServer
from core.intelligence.oms_engine import OMSEngine

class HealthGuard:
    """
    [Ω-CORE] Site Reliability Engineer.
    Protects the capital by monitoring system health and enforcing fail-safes.
    """
    def __init__(self, hftp: HFTPServer, oms: OMSEngine):
        self.hftp = hftp
        self.oms = oms
        self.logger = logging.getLogger("SOLENN.Health")
        
        # [Ω-V1.5.5] Heartbeat Thresholds
        self._last_heartbeat: Dict[str, float] = {}
        self._max_silence_sec = 5.0 # [Ω-Extreme Protection]
        self._is_safe_mode = False
        
        self.hftp.register_handler("PONG", self._on_pong)

    async def _on_pong(self, payload: Dict[str, Any], client_id: str):
        """[Ω-V1.1.5] Heartbeat Response Capture."""
        self._last_heartbeat[client_id] = time.time()
        
        if self._is_safe_mode:
            self.logger.info(f"❇️ [Ω-Health] EA {client_id} Pulsing again. Recovery initiated.")
            self._is_safe_mode = False

    async def start(self):
        """Starts the guardian watchdog."""
        asyncio.create_task(self._watchdog_loop())
        self.logger.info("🛡️ Health Guard Ω Watchdog Active (5s Sentinel)")

    async def _watchdog_loop(self):
        """[Ω-V1.5.9] Continuous health inspection."""
        while True:
            await asyncio.sleep(1.0)
            now = time.time()
            
            for client_id, last_time in list(self._last_heartbeat.items()):
                silence = now - last_time
                if silence > self._max_silence_sec and not self._is_safe_mode:
                    await self._trigger_safe_mode(client_id, silence)

    async def _trigger_safe_mode(self, client_id: str, silence: float):
        """[Ω-V1.5.5] Protective shutdown on connectivity loss."""
        self._is_safe_mode = True
        self.logger.critical(f"☢️ [Ω-Health] HEARTBEAT FAILURE on {client_id}: {silence:.1f}s silence.")
        
        # [Ω-V1.5.2] Isolation & Action
        # In a real scenario, we might try to emergency close via REST or alert the CEO.
        self.logger.warning("☣️ [Ω-Health] EMERGENCY: Execution Layer HALTED to protect capital.")
        
        # Kill pending orders in the OMSEngine locally to prevent ghost fills
        for trace_id, state in list(self.oms._orders.items()):
            if state.status.name in ["CREATED", "SUBMITTED"]:
                state.status.value = "REJECTED_HEALTH_FAIL"
                self.logger.warning(f"🚫 Canceled pending trade {trace_id} due to connection loss.")

    def is_healthy(self) -> bool:
        return not self._is_safe_mode
