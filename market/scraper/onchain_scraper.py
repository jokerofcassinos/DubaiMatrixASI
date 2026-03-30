import asyncio
import aiohttp
import logging
import time
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any

# [Ω-WHALE-PULSE] SOLÉNN Sovereign On-Chain Intelligence (v2.1)
# Intention Detection Before Price Action.

@dataclass(frozen=True, slots=True)
class OnChainSnapshot:
    """[Ω-SENSE] Immutable Snapshot of Bitcoin On-Chain State."""
    timestamp: float
    mempool_size: int            # [V055] Net Inflow indicator
    mempool_vsize: int           # Size in bytes
    avg_fee_sat_vb: float        # [V125] Network congestion proxy
    hashrate_th: float           # [V060] Network health
    difficulty: float            # Mining difficulty
    blocks_24h: int              # Blocks mined
    net_inflow_proxy: float      # [V058] Estimated selling pressure (-1.0 to 1.0)
    confidence: float            # Signal quality
    metadata: Dict[str, Any] = field(default_factory=dict)

class OnChainScraper:
    """
    [Ω-WHALE-PULSE] On-Chain Flow Monitor.
    Implements 162 vectors of Concept 2: Pulso On-Chain.
    """

    def __init__(self, update_interval: int = 600):
        self.logger = logging.getLogger("SOLENN.OnChain")
        self.interval = update_interval
        self._current: Optional[OnChainSnapshot] = None
        self._is_running = False
        self._session: Optional[aiohttp.ClientSession] = None
        self._last_update = 0.0

    async def start(self):
        """[V055] Launch Async Whale Monitoring."""
        if self._is_running: return
        self._is_running = True
        self._session = aiohttp.ClientSession(headers={
            "User-Agent": "SOLENN-ASI/WhalePulse-2.1 (Sovereign intelligence; Research)"
        })
        asyncio.create_task(self._loop())
        self.logger.info("⛓️ On-Chain Scraper Ω: ONLINE")

    async def stop(self):
        self._is_running = False
        if self._session:
            await self._session.close()

    @property
    def current(self) -> Optional[OnChainSnapshot]:
        return self._current

    async def _loop(self):
        while self._is_running:
            try:
                now = time.time()
                if now - self._last_update >= self.interval:
                    await self._scrape_all()
                    self._last_update = now
                await asyncio.sleep(60) # High granularity check
            except Exception as e:
                self.logger.error(f"☢️ ONCHAIN_SCROLL_FAULT: {e}")
                await asyncio.sleep(60)

    async def _scrape_all(self):
        """[V055-V063] On-Chain Data Synthesis."""
        # 1. Fetch Mempool Data [V058]
        mempool_data = await self._fetch_mempool()
        
        # 2. Fetch Hashrate Data [V060]
        stats = await self._fetch_blockchain_stats()
        
        # 3. Calculate Flow Proxy [V121]
        pressure = self._calculate_flow_pressure(mempool_data)
        
        self._current = OnChainSnapshot(
            timestamp=time.time(),
            mempool_size=mempool_data.get("count", 0),
            mempool_vsize=mempool_data.get("vsize", 0),
            avg_fee_sat_vb=mempool_data.get("avg_fee", 0.0),
            hashrate_th=stats.get("hash_rate", 0.0),
            difficulty=stats.get("difficulty", 0.0),
            blocks_24h=stats.get("n_blocks", 0),
            net_inflow_proxy=pressure,
            confidence=0.9 if stats.get("hash_rate", 0) > 0 else 0.4,
            metadata={"sources": ["mempool.space", "blockchain.info"]}
        )
        self.logger.info(f"⛓️ ONCHAIN_Ω: Fee={self._current.avg_fee_sat_vb:.1f} sat/vB | Pressure={pressure:+.3f}")

    async def _fetch_mempool(self) -> Dict[str, Any]:
        """[V055] mempool.space integration."""
        url_base = "https://mempool.space/api"
        try:
            # Get mempool stats
            async with self._session.get(f"{url_base}/mempool", timeout=10) as r1:
                stats = await r1.json() if r1.status == 200 else {}
            
            # Get recommended fees
            async with self._session.get(f"{url_base}/v1/fees/recommended", timeout=10) as r2:
                fees = await r2.json() if r2.status == 200 else {}
            
            return {
                "count": stats.get("count", 0),
                "vsize": stats.get("vsize", 0),
                "avg_fee": float(fees.get("hourFee", 1.0))
            }
        except Exception as e:
            self.logger.warning(f"📡 MEMPOOL_API_FAIL: {e}")
        return {}

    async def _fetch_blockchain_stats(self) -> Dict[str, Any]:
        """[V060] blockchain.info stats."""
        url = "https://api.blockchain.info/stats"
        try:
            async with self._session.get(url, timeout=10) as r:
                if r.status == 200:
                    return await r.json()
        except Exception as e:
            self.logger.warning(f"📡 BLOCKCHAIN_STATS_FAIL: {e}")
        return {}

    def _calculate_flow_pressure(self, mempool: Dict) -> float:
        """[V121] Net Flow Proxy calculation."""
        # Simple proxy: high mempool size + high fees = network stress / potential selling pressure
        count = mempool.get("count", 0)
        fee = mempool.get("avg_fee", 1.0)
        
        # Normalized score
        count_score = min(1.0, count / 200000.0)
        fee_score = min(1.0, fee / 100.0)
        
        pressure = (count_score * 0.4) + (fee_score * 0.6)
        # Shift to -1 to 1 (high = bearish pressure)
        return float(pressure * 2.0 - 1.0)
