"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              SOLÉNN — TEST: SHADOW ENGINE Ω (OMEGA PROOF)                   ║
║     Validation of Opportunity Cost Oracle and Parallel Reality Loop           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, Any

from core.decision.trinity_core import TrinityCore, Action
from core.decision.shadow_engine import ShadowEngine

@dataclass
class MockState:
    signal: float = 0.5
    phi: float = 0.05 # VERY LOW PHI - Will cause VETO
    confidence: float = 0.9
    coherence: float = 0.8
    bull_agents: list = field(default_factory=lambda: ["A", "B", "C"])

@dataclass
class MockSnapshot:
    price: float = 70000.0
    spread: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=lambda: {
        "avg_spread": 1.0,
        "atr_14": 150.0,
        "lot_size": 2.0
    })

async def run_shadow_validation():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("SOLENN.TestShadow")
    
    trinity = TrinityCore()
    shadow = ShadowEngine() # Instance shared via singleton if implemented that way, or just pass it
    
    state = MockState()
    snapshot = MockSnapshot()
    
    print("\n[STEP 1] Generating Trinity Decision (Expecting VETO due to low Phi)...")
    decision = await trinity.decide(state, "TRENDING_UP", snapshot)
    
    print(f"Decision: {decision.action} | Reason: {decision.reason}")
    print(f"TraceID: {decision.trace_id}")
    
    # Wait a bit for the async task of register_ghost to finish
    await asyncio.sleep(0.5)
    
    report_initial = shadow.get_efficiency_report()
    print(f"\n[STEP 2] Initial Shadow Report:")
    print(f"Active Ghosts: {report_initial['active_ghosts_count']}")
    
    if report_initial['active_ghosts_count'] == 0:
        print("❌ Error: Ghost not registered.")
        return

    print("\n[STEP 3] Simulating Reality Movement... (Price moves toward TP)")
    # TP for BUY is entry + 3*ATR = 70000 + 450 = 70450
    await shadow.update_reality(70500.0)
    
    await asyncio.sleep(0.5)
    
    print("\n[STEP 4] Final Shadow Report (Should show False Negative / Profit Missed):")
    report_final = shadow.get_efficiency_report()
    print(f"Active Ghosts: {report_final['active_ghosts_count']}")
    print(f"Opportunity Cost: {report_final['opportunity_cost_usd']}")
    
    # Check if the filter that vetoed was PHI_COHERENCE (from TrinityCore logic)
    # The reason was "VETO:INCOHERENCE(Φ=0.050<0.120)"
    missed_filters = report_final['filter_matrix']
    for reason, stats in missed_filters.items():
        if "INCOHERENCE" in reason and stats["fp"] > 0:
            print(f"✅ Validation Success: Filter '{reason}' identified as False Negative.")
            print(f"   Profit Missed: ${stats['profit_missed']:.2f}")

if __name__ == "__main__":
    asyncio.run(run_shadow_validation())
