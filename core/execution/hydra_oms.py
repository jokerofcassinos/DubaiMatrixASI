import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

# [Ω-HYDRA-OMS] SOLÉNN Sovereign Order Management System (v2.2)
# Concept 1-3 | Atomic Lifecycle & Binary Reconciliation

class OrderStatus(Enum):
    PENDING = "PENDING"     # No MT5
    SUBMITTED = "SUBMITTED" # Sent to Bridge
    ACKNOWLEDGED = "ACK"    # Received by MT5
    FILLED = "FILLED"       # Execution success
    PARTIAL = "PARTIAL"     # Partial fill [V058]
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"   # Terminal error
    EXPIRED = "EXPIRED"

@dataclass
class OrderIntent:
    """[Ω-INTENT] The Immaculate Registry of Intent."""
    trace_id: str
    symbol: str
    action: str
    lot: float
    type: str = "MARKET"
    price_target: float = 0.0
    sl: float = 0.0
    tp: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    ticket: Optional[int] = None
    fill_price: float = 0.0
    slippage: float = 0.0
    latency_ms: float = 0.0
    submission_time: float = 0.0
    update_time: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

class HydraOMS:
    """
    [Ω-OMS] Order Management with 162 Vectors.
    Ensures that intent meets reality via Atomic Sync and Forensic reconciliation.
    """

    def __init__(self, bridge=None):
        self.logger = logging.getLogger("SOLENN.HydraOMS")
        self.bridge = bridge
        self._registry: Dict[str, OrderIntent] = {}
        self._active_tickets: Dict[int, str] = {} # ticket -> trace_id
        self._lock = asyncio.Lock()
        self._is_active = True
        
        # [V064] Performance Metric
        self._stats = {
            "total_orders": 0,
            "failed_orders": 0,
            "avg_latency": 0.0,
            "last_reconcile": 0.0
        }

    # --- CONCEPT 1: ATOMIC LIFECYCLE (V055-V108) ---

    async def register_intent(self, intent: OrderIntent):
        """[V055] Atomic registration of intent."""
        async with self._lock:
            self._registry[intent.trace_id] = intent
            self._stats["total_orders"] += 1
            self.logger.info(f"📋 INTENT_REG: {intent.trace_id} | {intent.action} {intent.lot} {intent.symbol}")

    async def update_status(self, trace_id: str, status: OrderStatus, ticket: Optional[int] = None, **kwargs):
        """[V056/V063] State Machine Transition & Tracking."""
        async with self._lock:
            if trace_id in self._registry:
                order = self._registry[trace_id]
                old_status = order.status
                order.status = status
                order.update_time = time.time()
                
                # Check latency if filled
                if status == OrderStatus.FILLED and order.submission_time > 0:
                    order.latency_ms = (time.time() - order.submission_time) * 1000.0
                
                if ticket:
                    order.ticket = ticket
                    self._active_tickets[ticket] = trace_id
                
                # Update optional fields (slippage, fill_price, etc.)
                for key, val in kwargs.items():
                    if hasattr(order, key):
                        setattr(order, key, val)
                
                self.logger.info(f"🔄 STATUS_CHG: {trace_id} | {old_status.value} -> {status.value} (Ticket: {ticket})")
            else:
                self.logger.warning(f"⚠️ UNKNOWN_TRACE_ID: {trace_id} during status update.")

    # --- CONCEPT 2: BINARY RECONCILIATION (V064-V117) ---

    async def reconcile_loop(self):
        """
        [Ω-C2-T2.1.5] Total Binary Reconciliation (Ω-21).
        Synchronizes internal memory with the bridge/MT5 truth every 250ms.
        """
        self.logger.info("📡 Reconciliação Binária Ω Ativada (250ms loop).")
        while self._is_active:
            try:
                # 1. Fetch live tickets from broker reality
                if self.bridge and hasattr(self.bridge, 'get_active_positions'):
                    # REAL-TIME SYNC
                    broker_reality = await self.bridge.get_active_positions()
                    
                    async with self._lock:
                        # [V064] Heartbeat of Truth
                        current_t = time.time()
                        self._stats["last_reconcile"] = current_t
                        
                        # [V067] Check for Orquestrated Orphancy
                        for ticket in broker_reality:
                            if ticket not in self._active_tickets:
                                # Order made at the terminal manually or lost sync
                                self.logger.error(f"🚑 ORPHAN_DETECTION: Ticket {ticket} detected! Manual intervention or protocol fault.")
                                # Action: Log and prepare for manual recovery sync
                        
                        # [V068] Check for Zombie intents
                        for trace_id, order in self._registry.items():
                            if order.status == OrderStatus.FILLED and order.ticket not in broker_reality:
                                # Order was closed at the broker (TP/SL/Manual) but local OMS didn't catch it
                                self.logger.info(f"💀 ZOMBIE_RECOVERY: Intent {trace_id} closed at broker side.")
                                order.status = OrderStatus.EXPIRED # Mark as closed
                
                await asyncio.sleep(0.250) # Sub-sec reconciliation [V064]
                
            except Exception as e:
                self.logger.error(f"☢️ OMS_RECONCILE_FAULT: {e}")
                await asyncio.sleep(1)

    # --- CONCEPT 3: RECOVERY & GUARDRAILS (V118-V162) ---

    def get_order(self, trace_id: str) -> Optional[OrderIntent]:
        """[V118] Lookup by TraceID."""
        return self._registry.get(trace_id)

    def get_order_by_ticket(self, ticket: int) -> Optional[OrderIntent]:
        trace_id = self._active_tickets.get(ticket)
        return self._registry.get(trace_id) if trace_id else None

    async def stop(self):
        self._is_active = False
        self.logger.info("🌑 Hydra OMS Hibernated. Sovereign memory preserved.")
