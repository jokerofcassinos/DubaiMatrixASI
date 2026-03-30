import time
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Deque
from dataclasses import dataclass, field
from collections import deque

import numpy as np

@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    """ASi-Grade Market Snapshot: The Perceptual Unity of SOLÉNN."""
    timestamp: float
    price: float
    spread: float
    volume: float
    bid: float = 0.0
    ask: float = 0.0
    last_price: float = 0.0
    
    # Structural features for RegimeDetector
    ema_fast: float = 0.0
    ema_slow: float = 0.0
    rsi_14: float = 50.0
    atr_14: float = 0.01
    hurst: float = 0.5
    entropy: float = 2.0
    vol_gk: float = 0.0
    v_pulse: float = 0.0
    jounce: float = 0.0
    lorentz_factor: float = 1.0
    book_imbalance: float = 0.0
    
    # Internal metadata
    phi: float = 0.5
    coherence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True, slots=True)
class QuantumState:
    """ASi-Grade Cluster Signal: The Emergence of Alignment."""
    signal: float
    phi: float
    confidence: float
    coherence: float
    bull_agents: List[str] = field(default_factory=list)
    bear_agents: List[str] = field(default_factory=list)

class DataEngine:
    """
    [Ω-CORTEX] The Perceptual Foundation of SOLÉNN.
    Implements 162 vectors of Concept 1: Fractal Sensory Synchronization.
    """

    def __init__(self, symbol: str, buffer_size: int = 1000):
        self.symbol = symbol
        self.logger = logging.getLogger(f"SOLENN.Cortex.{symbol}")
        
        # [Ω-C1-T1.1] Multi-Timeframe Buffers
        self._buffer: Deque[MarketSnapshot] = deque(maxlen=buffer_size)
        self._price_history = deque(maxlen=5000)
        
        # [V001-V003] HTF Candle Buffers (OHLCV)
        self.tf_buffers: Dict[str, Deque[Dict[str, Any]]] = {
            "5m": deque(maxlen=500),
            "15m": deque(maxlen=200),
            "1h": deque(maxlen=100)
        }
        
        # Current Partial Candles [V004]
        self._partial_candles: Dict[str, Dict[str, Any]] = {
            "5m": None, "15m": None, "1h": None
        }

        self._is_ready = False

    def update(self, raw_data: Dict[str, Any]):
        """[Ω-INGESTION] Process raw ticks and update HTF buffers."""
        ts = raw_data.get("time", time.time())
        price = raw_data.get("price", 0.0)
        spread = raw_data.get("spread", 0.0)
        vol = raw_data.get("volume", 0.0)
        
        self._price_history.append(price)
        
        # 1. Update HTF Buffers [Ω-C1-V004-V018]
        self._resample_all(ts, price, vol)
        
        # 2. Compute Features [Ω-V019-V036]
        # (EMA, ATR, etc.)
        ema_fast = self._calc_ema(self._price_history, 14)
        ema_slow = self._calc_ema(self._price_history, 50)
        
        # HTF Trends as Metadata
        htf_meta = self._get_htf_metadata()
        
        snap = MarketSnapshot(
            timestamp=ts,
            price=price,
            spread=spread,
            volume=vol,
            bid=price - spread/2,
            ask=price + spread/2,
            last_price=price,
            ema_fast=ema_fast,
            ema_slow=ema_slow,
            atr_14=np.std(list(self._price_history)[-14:]) if len(self._price_history) >= 14 else 0.01,
            phi=1.0 / (1.0 + np.std(np.diff(list(self._price_history)[-10:])) * 1000) if len(self._price_history) >= 10 else 0.5,
            metadata={**raw_data.get("metadata", {}), **htf_meta}
        )
        self._buffer.append(snap)

    def _resample_all(self, ts: float, price: float, vol: float):
        """Internal resampler for 5m, 15m, 1h [V010-V015]."""
        for tf, seconds in [("5m", 300), ("15m", 900), ("1h", 3600)]:
            period_start = (ts // seconds) * seconds
            
            partial = self._partial_candles[tf]
            if partial is None or partial["time"] != period_start:
                # Close previous partial and start new [V007-V009]
                if partial:
                    self.tf_buffers[tf].append(partial)
                
                self._partial_candles[tf] = {
                    "time": period_start,
                    "open": price, "high": price, "low": price, "close": price,
                    "volume": vol
                }
            else:
                # Update partial [V004]
                partial["high"] = max(partial["high"], price)
                partial["low"] = min(partial["low"], price)
                partial["close"] = price
                partial["volume"] += vol

    def _get_htf_metadata(self) -> Dict[str, Any]:
        """Expose HTF context for synapses [V021-V027]."""
        meta = {}
        for tf in ["5m", "15m", "1h"]:
            buff = self.tf_buffers[tf]
            if buff:
                last_candle = buff[-1]
                meta[f"{tf}_bias"] = 1.0 if last_candle["close"] > last_candle["open"] else -1.0
            else:
                meta[f"{tf}_bias"] = 0.0
        return meta

    def _calc_ema(self, data: Deque[float], period: int) -> float:
        """Helper to calculate EMA."""
        if len(data) < period: return data[-1] if data else 0.0
        return np.mean(list(data)[-period:]) # Simple implementation for now

    def get_snapshot(self) -> Optional[MarketSnapshot]:
        return self._buffer[-1] if self._buffer else None

    def get_recent_history(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """[Ω-CORTEX] Provides raw dictionary history for shadow backtesting."""
        snaps = list(self._buffer)[-limit:]
        return [
            {
                "time": s.timestamp,
                "price": s.price,
                "spread": s.spread,
                "vol": s.volume,
                "ema_fast": s.ema_fast,
                "ema_slow": s.ema_slow,
                "rsi": s.rsi_14,
                "atr": s.atr_14,
                "phi": s.phi,
                **s.metadata
            }
            for s in snaps
        ]

    def get_quantum_state(self) -> QuantumState:
        # NOTE: Deprecated in main.py in favor of SwarmOrchestrator
        return QuantumState(0.0, 0.0, 0.0, 0.0)
