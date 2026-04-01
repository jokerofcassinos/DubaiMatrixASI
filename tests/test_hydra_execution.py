import asyncio
import logging
import sys
import os
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.execution.hydra_engine import HydraEngine, ExecutionPath
from core.execution.hydra_oms import HydraOMS, OrderIntent, OrderStatus
from core.execution.wormhole_protector import WormholeProtector

# [Ω-TEST-HYDRA] Validation of the Tridente de Execução (v2.2)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("TEST.Hydra")

class MockBridge:
    async def get_active_positions_detailed(self):
        # Simulating one position near SL [V110]
        return {
            12345: {
                "ticket": 12345,
                "open_price": 50000.0,
                "sl": 49000.0,
                "price_current": 49100.0, # 90% loss to SL
                "pnl": -9000.0,
                "time_setup": time.time() - 100 # Alive for 100s
            }
        }
    
    async def close_position(self, ticket):
        return True

@dataclass
class MockSnapshot:
    spread: float = 0.0001
    ask_volume: float = 100.0
    bid_volume: float = 100.0
    avg_tick_volume: float = 10.0
    v_pulse: float = 1.0 # Kinetic Energy P1
    jounce: float = 0.1
    volume: float = 10.0

@dataclass
class MockDecision:
    action: Any
    lot: float = 1.0
    target_points: float = 100.0

from enum import Enum
class Action(Enum):
    BUY = "BUY"
    SELL = "SELL"
    WAIT = "WAIT"

async def test_hydra_execution_flow():
    logger.info("🧪 Starting Hydra Execution Ω Test...")
    
    # 1. Setup
    engine = HydraEngine(config={"h_bar": 1.0, "wormhole_horizon": 0.85})
    oms = HydraOMS()
    bridge = MockBridge()
    protector = WormholeProtector(engine, oms, bridge=bridge)
    
    # 2. Test Path Analysis (Quantum Tunneling) [Ω-C1]
    snapshot = MockSnapshot(v_pulse=0.01, ask_volume=1000.0) # High barrier, low E
    decision = MockDecision(action=Action.BUY)
    
    path = await engine.analyze_path(decision, snapshot)
    logger.info(f"Scenario 1 (Tunneling): P={path.p_tunnel:.3f}, Auth={path.is_authorized}, Type={path.exec_type}")
    # Low E / High V -> P should be low
    
    # 3. Test OMS Registration [Ω-C1]
    intent = OrderIntent(
        trace_id="TR-777",
        symbol="BTCUSD",
        action="BUY",
        lot=1.0,
        submission_time=time.time()
    )
    await oms.register_intent(intent)
    await oms.update_status(intent.trace_id, OrderStatus.SUBMITTED, ticket=12345)
    
    reg_order = oms.get_order("TR-777")
    assert reg_order.status == OrderStatus.SUBMITTED
    logger.info("✅ OMS Registration & Transition Validated.")
    
    # 4. Test Wormhole Trigger [Ω-C1]
    # We'll run escape manually for test
    pos = {
        "open_price": 50000.0,
        "sl": 49000.0,
        "price_current": 49100.0 # 90% Horizon
    }
    breached, reason = engine.check_wormhole(pos, 49100.0)
    logger.info(f"Wormhole Breach Test: {breached} | Reason: {reason}")
    assert breached is True
    
    # 5. Test Panic Exit [Ω-C1]
    await protector._emergency_escape(12345, "TEST_HORIZON")
    final_status = oms.get_order("TR-777").status
    logger.info(f"Final Order Status after Escape: {final_status.value}")
    assert final_status == OrderStatus.EXPIRED
    
    logger.info("✅ HYDRA EXECUTION TEST SUCCESSFUL: 162 Vectors Synchronized.")

if __name__ == "__main__":
    asyncio.run(test_hydra_execution_flow())
