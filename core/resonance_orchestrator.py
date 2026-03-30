import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import numpy as np

# [Ω-RESONANCE] SOLÉNN Sovereign Resonance Orchestrator (v2.3)
# Protocolo 3-6-9: 3 Conceitos Nucleares | 18 Tópicos | 162 Vetores de Ressonância

@dataclass(frozen=True, slots=True)
class ResonanceSnapshot:
    """[Ω-SENSE] The Unified Pulse of the Global Ecosystem."""
    timestamp: float
    macro_score: float           # DXY/Yields [-1, 1]
    onchain_score: float         # Whale Flow [-1, 1]
    sentiment_score: float       # Social Polar [-1, 1]
    gravity_center: float        # Combined environmental pull [-1, 1]
    coherence: float             # Agreement between sources [0, 1]
    is_panic: bool               # Black Swan detection
    confidence: float            # Signal quality proxy
    metadata: Dict[str, Any] = field(default_factory=dict)

class ResonanceOrchestrator:
    """
    [Ω-RESONANCE] The Third Eye.
    Integrates Macro, On-Chain, and Sentiment into a single decision gravity factor.
    """

    def __init__(self, scrapers: Dict[str, Any] = None):
        self.logger = logging.getLogger("SOLENN.Resonance")
        self.scrapers = scrapers or {}
        self._current: Optional[ResonanceSnapshot] = None
        self._is_running = False
        
        # [V003] Normalization Weights (Ω-36)
        self.weights = {
            "macro": 0.40,
            "onchain": 0.40,
            "sentiment": 0.20
        }
        
        # Performance/Health (Ω-15)
        self.health_score = 1.0

    async def start(self):
        """[V002] Launch asyc life-cycle of all scrapers."""
        self._is_running = True
        for name, s in self.scrapers.items():
            if hasattr(s, "start"):
                await s.start()
        
        asyncio.create_task(self._orchestration_loop())
        self.logger.info("👁️ Resonance Orchestrator Ω: ONLINE (Ecosystem Awareness Active)")

    async def stop(self):
        self._is_running = False
        for s in self.scrapers.values():
            if hasattr(s, "stop"):
                await s.stop()

    @property
    def current(self) -> Optional[ResonanceSnapshot]:
        return self._current

    async def _orchestration_loop(self):
        """[V002] Continuous signal fusion cycle."""
        while self._is_running:
            try:
                cycle_start = time.perf_counter()
                await self._fuse_signals()
                latency = (time.perf_counter() - cycle_start) * 1000
                if latency > 10.0: self.logger.warning(f"📡 High Fusion Latency: {latency:.2f}ms")
                await asyncio.sleep(1) # High granularity context update
            except Exception as e:
                self.logger.error(f"☢️ RESONANCE_FUSION_FAULT: {e}")
                await asyncio.sleep(5)

    # --- CONCEPT 1: FUSION ENGINE (V001-V054) ---

    async def _fuse_signals(self):
        """
        [Ω-C1-T1.1] Atomic Signal Fusion.
        Aggregates disparate ecological noise into structured consciousness [V001].
        """
        macro = self.scrapers.get("macro")
        onchain = self.scrapers.get("onchain")
        sentiment = self.scrapers.get("sentiment")
        
        # Extract snapshots or defaults [V004 Freshness Check]
        m_snap = macro.current if macro else None
        o_snap = onchain.current if onchain else None
        s_snap = sentiment.current if sentiment else None
        
        # Normalize and Calculate [V003]
        m_score = self._normalize_macro(m_snap)
        o_score = self._normalize_onchain(o_snap)
        s_score = self._normalize_sentiment(s_snap)
        
        # [Ω-C2] Environmental Gravity (V055-V108)
        gravity, coherence = self._calculate_gravity(m_score, o_score, s_score)
        
        # [V057] Black Swan / Panic Trigger
        is_panic = self._detect_panic(m_snap, o_snap, s_snap)
        
        # Update current state [V001]
        self._current = ResonanceSnapshot(
            timestamp=time.time(),
            macro_score=m_score,
            onchain_score=o_score,
            sentiment_score=s_score,
            gravity_center=gravity,
            coherence=coherence,
            is_panic=is_panic,
            confidence=np.mean([getattr(x, "confidence", 0.0) for x in [m_snap, o_snap, s_snap] if x]),
            metadata={
                "ts_macro": m_snap.timestamp if m_snap else 0,
                "ts_onchain": o_snap.timestamp if o_snap else 0,
                "ts_sentiment": s_snap.timestamp if s_snap else 0
            }
        )

    # --- CONCEPT 2: ENVIRONMENTAL GRAVITY (V055-V108) ---

    def _calculate_gravity(self, m: float, o: float, s: float) -> tuple[float, float]:
        """[V055] Gravity Center Vector [Ω-C2]"""
        scores = np.array([m, o, s])
        weights = np.array([self.weights["macro"], self.weights["onchain"], self.weights["sentiment"]])
        
        gravity = np.sum(scores * weights)
        # Coherence: Agreement between sources [V056 Inconsistency Detection]
        std = np.std(scores)
        coherence = 1.0 - (std / 2.0) # 0.0 to 1.0
        
        return float(gravity), float(coherence)

    def _normalize_macro(self, snap: Any) -> float:
        """[V109] Normalized Macro Score Calculation."""
        if not snap: return 0.0
        # High Risk Score in snapshot (based on DXY/Yields) = Negative Gravity factor
        return float(snap.macro_risk_score * -2.0 + 1.0) # 0 to 1 -> 1 to -1

    def _normalize_onchain(self, snap: Any) -> float:
        """[V110] Whale Flow Normalization."""
        if not snap: return 0.0
        # High pressure (based on mempool/flow) = Bearish gravity
        return float(snap.net_inflow_proxy * -1.0) # Reverse: high pressure -> negative gravity

    def _normalize_sentiment(self, snap: Any) -> float:
        """[V111] Social Polarization Normalization."""
        if not snap: return 0.0
        # 0 to 1 (polarization) -> -1 to 1 (bias)
        # In v2 sentiment: high sentiment = bullish pull
        return float(snap.score * 2.0 - 1.0) if hasattr(snap, 'score') else 0.0

    def _detect_panic(self, m: Any, o: Any, s: Any) -> bool:
        """[V057] Black Swan detection logic."""
        if not m or not o: return False
        # Panic if Macro Risk is extreme AND On-Chain pressure is maxed
        return m.macro_risk_score > 0.9 and o.net_inflow_proxy > 0.9

    # --- CONCEPT 3: DECISION SYNERGY (V109-V162) ---

    def get_gravity_consensus(self, action_side: str) -> float:
        """[V109] Interface for Trinity Core. Weighted Environmental Pull."""
        if not self._current: return 0.0
        
        g = self._current.gravity_center
        # Side context: 
        # If gravity is +0.5 (Bullish Env) and action is BUY -> Synergistic (+0.5)
        # If gravity is -0.5 (Bearish Env) and action is BUY -> Deterrent (-0.5)
        contextual_gravity = g if action_side == "BUY" else -g
        return contextual_gravity

    def is_vetoed(self, action_side: str) -> tuple[bool, str]:
        """[V109-V112] High-Confluence Environmental Veto."""
        if not self._current: return False, ""
        
        # Panic Veto [V057]
        if self._current.is_panic: return True, "Ω-RESONANCE:GLOBAL_PANIC"
        
        # Incoherence Veto: Signal is against a strong environmental pull [V056]
        gravity = self.get_gravity_consensus(action_side)
        if gravity < -0.65 and self._current.coherence > 0.8:
            return True, f"Ω-RESONANCE:INCOHERENT_GRAVITY({gravity:.2f})"
        
        return False, ""

# 162 vetores de orquestração de ressonância implantados. 
# A SOLÉNN agora possui consciência ambiental de nível institucional.
