import asyncio
import logging
import sys
import os
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Adjust path to import solaris modules
sys.path.append(os.getcwd())

from core.intelligence.elite.nexus_synapse import NexusSynapse
from core.intelligence.nexus_resonance import NexusGlobalContext

@dataclass
class MockSnapshot:
    price: float = 65000.0
    ema_slow: float = 64500.0
    atr_14: float = 150.0

async def test_nexus_oracle():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
    logger = logging.getLogger("TEST.NexusAgent")
    
    logger.info("🧪 Starting Nexus Agent Oracle Test...")
    
    agent = NexusSynapse()
    snapshot = MockSnapshot()
    
    # scenario 1: Extreme Fear + High Confidence [V010]
    ctx1 = NexusGlobalContext(
        timestamp=time.time(),
        sentiment_bias=-0.8, # Extreme Fear
        onchain_pressure=-0.5, # Bullish outflow
        macro_risk=0.2, # Stable macro
        confidence=0.9,
        nexus_bias=0.0
    )
    
    res1 = await agent.process(snapshot, ctx1)
    logger.info(f"Scenario 1 (Fear/Bullish): Signal={res1['signal']:.3f}, Conf={res1['confidence']:.3f}, Phi={res1['phi']:.3f}")
    assert res1['signal'] > 0, "Extreme fear should trigger contrarian BUY"
    
    # scenario 2: Macro Veto [V064]
    ctx2 = NexusGlobalContext(
        timestamp=time.time(),
        sentiment_bias=0.2,
        onchain_pressure=0.1,
        macro_risk=0.9, # Extreme Risk (Event iminente)
        confidence=0.9,
        nexus_bias=0.0
    )
    res2 = await agent.process(snapshot, ctx2)
    logger.info(f"Scenario 2 (Macro Veto): Signal={res2['signal']:.3f}, Metadata={res2['metadata']}")
    assert res2['signal'] == 0.0, "High macro risk should trigger VETO"
    assert res2['metadata']['is_veto'] is True
    
    # scenario 3: Sentiment/OnChain Dissonance [V039]
    ctx3 = NexusGlobalContext(
        timestamp=time.time(),
        sentiment_bias=0.7, # Greed
        onchain_pressure=0.8, # Strong selling
        macro_risk=0.3,
        confidence=0.9,
        nexus_bias=0.0
    )
    res3 = await agent.process(snapshot, ctx3)
    logger.info(f"Scenario 3 (Dissonance): Signal={res3['signal']:.3f}, Phi={res3['phi']:.3f}")
    assert res3['metadata']['needs_hedge'] is True, "Euphoria + Dump should trigger HEDGE"

    logger.info("✅ NEXUS AGENT TEST SUCCESSFUL: The Oracle is calibrated.")

if __name__ == "__main__":
    asyncio.run(test_nexus_oracle())
