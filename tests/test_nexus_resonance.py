import asyncio
import logging
import sys
import os

# Adjust path to import solaris modules
sys.path.append(os.getcwd())

from core.intelligence.nexus_resonance import NexusResonance

async def test_nexus_omniscience():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
    logger = logging.getLogger("TEST.Nexus")
    
    logger.info("🧪 Starting NEXUS OMNISCIENCE Test...")
    
    nexus = NexusResonance()
    
    try:
        # Start the gaze
        await nexus.start()
        
        logger.info("⏳ Waiting for sensory ingestion (10s)...")
        await asyncio.sleep(10)
        
        # Capture context
        context = nexus.get_context()
        
        logger.info("--- NEXUS REALITY REPORT ---")
        logger.info(f"Timestamp: {context.timestamp}")
        logger.info(f"Sentiment Bias: {context.sentiment_bias:+.3f}")
        logger.info(f"On-Chain Pressure: {context.onchain_pressure:+.3f}")
        logger.info(f"Macro Risk: {context.macro_risk:+.3f}")
        logger.info(f"Global Confidence: {context.confidence:+.3f}")
        logger.info(f"FINAL NEXUS BIAS: {context.nexus_bias:+.3f}")
        logger.info(f"Metadata: {context.metadata}")
        
        # Verify invariants
        assert -1.0 <= context.nexus_bias <= 1.0, "Nexus Bias out of bounds!"
        assert 0.0 <= context.confidence <= 1.0, "Confidence out of bounds!"
        
        logger.info("✅ NEXUS TEST SUCCESSFUL: Omniscience achieved.")
        
    except Exception as e:
        logger.error(f"❌ NEXUS TEST FAILED: {e}")
        raise
    finally:
        await nexus.stop()
        logger.info("🌑 Nexus sensory system halted.")

if __name__ == "__main__":
    asyncio.run(test_nexus_omniscience())
