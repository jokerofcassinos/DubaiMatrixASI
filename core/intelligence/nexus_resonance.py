import asyncio
import logging
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

# [Ω-NEXUS-RESONANCE] SOLÉNN Sovereign Information Fusion (v2.1)
# The Unified Gaze of Omniscience.

from market.scraper.sentiment_scraper import SentimentScraper, SentimentSnapshot
from market.scraper.onchain_scraper import OnChainScraper, OnChainSnapshot
from market.scraper.macro_scraper import MacroScraper, MacroSnapshot

@dataclass(frozen=True, slots=True)
class NexusGlobalContext:
    """[Ω-NEXUS] The Integrated Global Reality for the Swarm."""
    timestamp: float
    sentiment_bias: float        # -1 to 1 (Fear/Greed)
    onchain_pressure: float      # -1 to 1 (Selling/Accumulation)
    macro_risk: float            # 0 to 1
    confidence: float            # 0 to 1
    nexus_bias: float            # -1 to 1 (Fused global directive)
    metadata: Dict[str, Any] = field(default_factory=dict)

class NexusResonance:
    """
    [Ω-NEXUS-RESONANCE] The Information Fusion Core.
    Implements 162 vectors of Concept 3: Nexus Fusion.
    """

    def __init__(self):
        self.logger = logging.getLogger("SOLENN.Nexus")
        self.sentiment = SentimentScraper()
        self.onchain = OnChainScraper()
        self.macro = MacroScraper()
        self._is_active = False

    async def start(self):
        """[V118] Launch all sensory systems."""
        if self._is_active: return
        self._is_active = True
        
        # Parallel launch of sensors
        await asyncio.gather(
            self.sentiment.start(),
            self.onchain.start(),
            self.macro.start()
        )
        self.logger.info("📡 NEXUS RESONANCE: ONLINE (All sensors integrated)")

    async def stop(self):
        self._is_active = False
        await self.sentiment.stop()
        await self.onchain.stop()
        await self.macro.stop()

    def get_context(self) -> NexusGlobalContext:
        """[V119] Generate Integrated Global Reality."""
        sent_snap = self.sentiment.current
        oc_snap = self.onchain.current
        mac_snap = self.macro.current
        
        # 1. Extraction [V121]
        s_bias = sent_snap.sentiment_score if sent_snap else 0.0
        oc_press = oc_snap.net_inflow_proxy if oc_snap else 0.0
        m_risk = mac_snap.macro_risk_score if mac_snap else 0.5
        
        # 2. Weighted Fusion [V120]
        # Sentiment = 50%, On-Chain = 30%, Macro = 20%
        nexus_bias = (s_bias * 0.5) + (oc_press * 0.3) + ((0.5 - m_risk) * 0.4)
        
        # 3. Global Confidence [V117]
        avg_conf = sum([
            sent_snap.confidence if sent_snap else 0.0,
            oc_snap.confidence if oc_snap else 0.0,
            mac_snap.confidence if mac_snap else 0.0
        ]) / 3.0
        
        return NexusGlobalContext(
            timestamp=time.time(),
            sentiment_bias=float(s_bias),
            onchain_pressure=float(oc_press),
            macro_risk=float(m_risk),
            confidence=float(avg_conf),
            nexus_bias=float(max(-1.0, min(1.0, nexus_bias))),
            metadata={
                "sent_label": sent_snap.fear_greed_label if sent_snap else "Unknown",
                "onchain_flow": "Bearish" if oc_press > 0.3 else "Bullish" if oc_press < -0.3 else "Neutral"
            }
        )
