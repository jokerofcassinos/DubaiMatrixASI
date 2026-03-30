import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from core.execution.hydra_engine import HydraEngine
from core.execution.hydra_oms import HydraOMS, OrderStatus

# [Ω-WORMHOLE-PROTECTOR] SOLÉNN DEFENSE SHIELD (v2.2)
# Concept 1-3 | Event Horizon, Accelerated Exit, Delta Neutralizer

class WormholeProtector:
    """
    [Ω-WORMHOLE] The Shield of the Sovereign Mind.
    Prevents the singularity (capital collapse) via Event Horizon Monitoring. (162 vectors)
    """

    def __init__(self, engine: HydraEngine, oms: HydraOMS, bridge=None, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger("SOLENN.Wormhole")
        self.engine = engine
        self.oms = oms
        self.bridge = bridge
        self.config = config or {}
        
        # [V110-V117] Defense Thresholds
        self._horizon_ratio = self.config.get("horizon_ratio", 0.85) # 85% to SL
        self._is_active = True
        
        # [V112] Time-based limits (Ω-45)
        self._max_trade_lifetime = self.config.get("max_trade_lifetime", 3600) # 1 hour max for scalp

    async def run_monitoring(self):
        """
        [Ω-C1] Event Horizon Scan.
        Continuous monitoring of all active positions [V109].
        """
        self.logger.info("🛡️ Wormhole Protector Ω Online: Event Horizon Monitoring (500ms loop).")
        while self._is_active:
            try:
                # 1. Fetch current positions from reality (MT5 directly via bridge for speed)
                if self.bridge and hasattr(self.bridge, 'get_active_positions_detailed'):
                    positions = await self.bridge.get_active_positions_detailed()
                    
                    for ticket, pos in positions.items():
                        # [V110] Horizon Check
                        breached, reason = self.engine.check_wormhole(pos, pos.get('price_current', 0.0))
                        
                        if breached:
                            # [V110-V113] EMERGENCY ESCAPE
                            await self._emergency_escape(ticket, reason)
                        
                        # [V112] Time-based survival check
                        open_time = pos.get('time_setup', 0.0)
                        if (time.time() - open_time) > self._max_trade_lifetime:
                            await self._emergency_escape(ticket, "TIME_EXPIRATION_VETO")
                
                await asyncio.sleep(0.5) # Fast monitoring [V117]
                
            except Exception as e:
                self.logger.error(f"☢️ WORMHOLE_SCAN_FAULT: {e}")
                await asyncio.sleep(1)

    async def _emergency_escape(self, ticket: int, reason: str):
        """[V110/V113/V115] Accelerated Exit Protocol."""
        self.logger.warning(f"🚨 WORMHOLE_TRIGGERED: Ticket {ticket} | Reason: {reason} | EXEC_EXIT_NOW")
        
        # 1. Send immediate market close order
        if self.bridge:
            success = await self.bridge.close_position(ticket)
            
            # 2. Update OMS to reflect the escape
            order = self.oms.get_order_by_ticket(ticket)
            if order:
                await self.oms.update_status(
                    order.trace_id, 
                    OrderStatus.EXPIRED, 
                    metadata={"exit_reason": f"WORMHOLE_{reason}"}
                )
            
            if success:
                self.logger.info(f"✅ ESCAPE_SUCCESS: Ticket {ticket} terminated.")
            else:
                self.logger.error(f"❌ ESCAPE_FAILED: Ticket {ticket} still in gravity! Manual takeover needed.")

    async def stop(self):
        self._is_active = False
        self.logger.info("🛡️ Wormhole Shield Hibernated.")
