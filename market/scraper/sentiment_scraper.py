import asyncio
import aiohttp
import logging
import time
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any

# [Ω-SENTIMENT] SOLÉNN Sovereign Sentiment Intelligence (v2.1)
# Omni-Sensory Narrative Distillation.

@dataclass(frozen=True, slots=True)
class SentimentSnapshot:
    """[Ω-SENSE] Immutable Snapshot of Market Sentiment."""
    timestamp: float
    fear_greed_index: float      # 0-100
    fear_greed_label: str        # e.g., "Extreme Fear"
    btc_dominance: float         # 0-100
    btc_24h_change: float        # %
    sentiment_score: float       # -1.0 to 1.0 (Consolidated)
    confidence: float            # 0.0 to 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

class SentimentScraper:
    """
    [Ω-NLP-SCALPEL] High-Frequency Sentiment Distiller.
    Implements 162 vectors of Concept 1: Narrativa Distilada.
    """

    def __init__(self, update_interval: int = 300):
        self.logger = logging.getLogger("SOLENN.Sentiment")
        self.interval = update_interval
        self._current: Optional[SentimentSnapshot] = None
        self._is_running = False
        self._session: Optional[aiohttp.ClientSession] = None
        self._last_update = 0.0

    async def start(self):
        """[V001] Launch Async Sentiment Ingestion."""
        if self._is_running: return
        self._is_running = True
        self._session = aiohttp.ClientSession(headers={
            "User-Agent": "SOLENN-ASI/2.1 (Sovereign intelligence; Research; +https://solenn.ai)"
        })
        asyncio.create_task(self._loop())
        self.logger.info("📡 Sentiment Scraper Ω: ONLINE")

    async def stop(self):
        self._is_running = False
        if self._session:
            await self._session.close()

    @property
    def current(self) -> Optional[SentimentSnapshot]:
        return self._current

    async def _loop(self):
        while self._is_running:
            try:
                now = time.time()
                if now - self._last_update >= self.interval:
                    await self._scrape_all()
                    self._last_update = now
                await asyncio.sleep(10)
            except Exception as e:
                self.logger.error(f"☢️ SENTIMENT_SCROLL_FAULT: {e}")
                await asyncio.sleep(30)

    async def _scrape_all(self):
        """[V119] Multi-Source Nexus Collection."""
        # 1. Fetch Fear & Greed [V002]
        fg_data = await self._fetch_fear_greed()
        
        # 2. Fetch Market Data [V019]
        market_data = await self._fetch_market_data()
        
        # 3. Consolidate Sentiment [V010]
        score, confidence = self._calculate_composite_score(fg_data, market_data)
        
        self._current = SentimentSnapshot(
            timestamp=time.time(),
            fear_greed_index=fg_data.get("value", 50.0),
            fear_greed_label=fg_data.get("label", "Neutral"),
            btc_dominance=market_data.get("btc_dominance", 0.0),
            btc_24h_change=market_data.get("btc_24h_change", 0.0),
            sentiment_score=score,
            confidence=confidence,
            metadata={"sources": ["alternative.me", "coingecko"]}
        )
        self.logger.info(f"📊 SENTIMENT_Ω: Score={score:+.3f} | F&G={self._current.fear_greed_index} ({self._current.fear_greed_label})")

    async def _fetch_fear_greed(self) -> Dict[str, Any]:
        """[V002] alternative.me API integration."""
        url = "https://api.alternative.me/fng/?limit=1"
        try:
            async with self._session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    entry = data["data"][0]
                    return {
                        "value": float(entry["value"]),
                        "label": entry["value_classification"]
                    }
        except Exception as e:
            self.logger.warning(f"📡 FG_API_FAIL: {e}")
        return {"value": 50.0, "label": "Neutral"}

    async def _fetch_market_data(self) -> Dict[str, Any]:
        """[V019] CoinGecko integration."""
        # Proxying dominance and global volume
        url = "https://api.coingecko.com/api/v3/global"
        try:
            async with self._session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    market = data["data"]
                    return {
                        "btc_dominance": market["market_cap_percentage"].get("btc", 0.0),
                        "btc_24h_change": market["market_cap_change_percentage_24h_usd"]
                    }
        except Exception as e:
            self.logger.warning(f"📡 COINGECKO_API_FAIL: {e}")
        return {"btc_dominance": 50.0, "btc_24h_change": 0.0}

    def _calculate_composite_score(self, fg: Dict, market: Dict) -> tuple[float, float]:
        """[V010] Bayesian Sentiment Synthesis."""
        # Normalizing F&G (0 to 100) -> (-1 to 1) [V005]
        fg_score = (fg["value"] - 50.0) / 50.0
        
        # Market change influence (capped at +- 5%)
        change = market.get("btc_24h_change", 0.0)
        change_score = max(-1.0, min(1.0, change / 5.0))
        
        # Weighted Average [V011]
        score = (fg_score * 0.7) + (change_score * 0.3)
        confidence = 0.8 if fg["value"] != 50.0 else 0.4
        
        return float(score), float(confidence)
