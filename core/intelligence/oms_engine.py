"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              SOLÉNN — OMS ENGINE Ω (SOVEREIGN EXECUTION)                     ║
║     Order Management System: State Machine, Lifecycle, Audit                 ║
║     Implementing: Atomic Submission, TraceID Mapping, Latency Tracking       ║
║     Framework 3-6-9: Phase 4(Ω-21) - Concept 1.3                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import time
import logging
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

class OrderStatus(Enum):
    CREATED = "CREATED"
    SUBMITTED = "SUBMITTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"

@dataclass
class OrderState:
    """[Ω-V1.3.3] Atomic Order State Snapshot."""
    trace_id: str
    symbol: str
    action: str        # BUY, SELL, LIMIT
    lot_size: float
    status: OrderStatus = OrderStatus.CREATED
    ticket: Optional[int] = None
    entry_price: Optional[float] = None
    sl: float = 0.0
    tp: float = 0.0
    
    # [Ω-V1.3.8] Latency Metrics
    ts_created: float = field(default_factory=time.time)
    ts_submitted: Optional[float] = None
    ts_ack: Optional[float] = None
    ts_filled: Optional[float] = None
    
    metadata: Dict[str, Any] = field(default_factory=dict)

class OMSEngine:
    """
    [Ω-CORE] Sovereign Order Management System.
    Governs the lifecycle of every trade with aerospace-grade precision.
    """
    def __init__(self, hftp_server: Any):
        self.hftp = hftp_server
        self.logger = logging.getLogger("SOLENN.OMS")
        self._orders: Dict[str, OrderState] = {} # Keyed by trace_id (Ω-V1.3.4)
        
        # [Ω-V1.3.6] Rejection Mapping
        self._rejection_history: List[Dict[str, Any]] = []

    async def submit_order(self, 
                           trace_id: str, 
                           symbol: str, 
                           action: str, 
                           lot: float, 
                           sl: float = 0.0, 
                           tp: float = 0.0, 
                           client_id: str = "DEFAULT") -> bool:
        """[Ω-V1.3.1] Atomic Order Submission."""
        
        state = OrderState(
            trace_id=trace_id,
            symbol=symbol,
            action=action.upper(),
            lot_size=lot,
            sl=sl,
            tp=tp
        )
        self._orders[trace_id] = state
        
        # [Ω-V1.1.2] Build MessagePack Payload
        payload = {
            "tr_id": trace_id,
            "sym": symbol,
            "act": action.upper(),
            "vol": lot,
            "sl": sl,
            "tp": tp
        }
        
        state.ts_submitted = time.time()
        state.status = OrderStatus.SUBMITTED
        
        success = await self.hftp.send_message(client_id, "ORDER", payload)
        
        if not success:
            state.status = OrderStatus.REJECTED
            self.logger.error(f"❌ [Ω-OMS] Submission Hard Fail for {trace_id}")
            return False
            
        return True

    async def handle_response(self, payload: Dict[str, Any]):
        """[Ω-V1.3.4] Response Handler: Syncs Response with TraceID."""
        trace_id = payload.get("tr_id")
        if not trace_id or trace_id not in self._orders:
            self.logger.warning(f"⚠️ [Ω-OMS] Orphan Response: {trace_id}")
            return
            
        state = self._orders[trace_id]
        status_raw = payload.get("status")
        
        # [Ω-V1.3.8] Ack Latency
        state.ts_ack = time.time()
        latency = (state.ts_ack - (state.ts_submitted or state.ts_created)) * 1000
        
        if status_raw == "SUCCESS":
            state.status = OrderStatus.FILLED # Simplified for now
            state.ticket = payload.get("ticket")
            state.entry_price = payload.get("price")
            state.ts_filled = state.ts_ack
            self.logger.info(f"🎯 [Ω-OMS] Trade FILLED: {trace_id} | Ticket: {state.ticket} | Latency: {latency:.2f}ms")
            
        elif status_raw == "REJECTED":
            state.status = OrderStatus.REJECTED
            reason = payload.get("reason", "UNKNOWN")
            self._rejection_history.append({"tr_id": trace_id, "reason": reason, "ts": time.time()})
            self.logger.error(f"❌ [Ω-OMS] Trade REJECTED: {trace_id} | Reason: {reason}")
            
        # [Ω-V1.3.7] Slippage Tracking could be added here
        
    def get_order_state(self, trace_id: str) -> Optional[OrderState]:
        return self._orders.get(trace_id)

    async def cancel_order(self, trace_id: str, client_id: str = "DEFAULT") -> bool:
        """[Ω-V1.3.2] Cancellation Protocol."""
        state = self._orders.get(trace_id)
        if not state or not state.ticket: return False
        
        payload = {"tr_id": trace_id, "ticket": state.ticket, "act": "CANCEL"}
        success = await self.hftp.send_message(client_id, "CANCEL", payload)
        
        if success:
            state.status = OrderStatus.CANCELLED
            return True
        return False
