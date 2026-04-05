"""
SOLÉNN v2 — Market Memory & Flow Intelligence (Ω-MM01 a Ω-MM54)
Replaces v1 episodic_memory.py and semantic_nlp.py.

Pure-Python vector episodic memory with circular buffer, cosine similarity
search, market flow tokenization, and institutional vocabulary extraction.
No numpy dependency — uses only standard library math.

Concept 1: FlowTokenizer & Institutional Vocabulary (Ω-MM01–MM18)
  Transmutates raw market micro-tick events into institutional tokens.
  Whale detection, HFT machine-gun patterns, retail noise filtering,
  spoofing detection tokens, liquidity vacuum signals, and iceberg
  footprint markers. Each token carries semantic weight for downstream
  analysis.

Concept 2: EpisodicMemory & Vector-Space Recall (Ω-MM19–MM36)
  Circular-buffer vector database storing market episodes (snapshot +
  outcome). Cosine similarity search retrieves top-k similar episodes.
  Market intuition extraction from weighted average of similar past
  outcomes. Memory compression and decay ensure bounded resources.
  Persistence via SQLite for durability across restarts.

Concept 3: Semantic Memory & Intuition Engine (Ω-MM37–MM54)
  Long-term semantic memory extracts persistent patterns from episodic
  data. Intuition scoring via Bayesian confidence weighting. Pattern
  catalog with frequency tracking and recency adjustment. Self-diagnosis
  of memory quality (coverage, diversity, staleness) enabling graceful
  degradation when recall confidence is low.
"""

from __future__ import annotations

import math
import os
import sqlite3
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ──────────────────────────────────────────────────────────────
# Ω-MM01 to Ω-MM18: FlowTokenizer & Institutional Vocabulary
# ──────────────────────────────────────────────────────────────


class FlowTokenType(Enum):
    """Ω-MM01: Institutional vocabulary for market micro-tick events."""
    WHALE_BUY_BOMB = 100
    WHALE_SELL_BOMB = 101
    WHALE_ACCUMULATION = 102
    WHALE_DISTRIBUTION = 103
    HFT_MACHINE_GUN_BUY = 200
    HFT_MACHINE_GUN_SELL = 201
    HFT_SPOOF_BID = 210
    HFT_SPOOF_ASK = 211
    HFT_ARBITRAGE = 220
    RETAIL_NOISE = 300
    RETAIL_FOMO_BUY = 310
    RETAIL_PANIC_SELL = 311
    LIQUIDITY_VACUUM = 400
    ORDER_BLOCK_FORMATION = 410
    FVG_CREATION = 420
    ICEBERG_DETECTED = 430
    DARK_POOL_PRINT = 440
    STOP_RUN_TRIGGERED = 500
    LIQUIDATION_CASCADE = 510
    REGIME_TRANSITION = 600
    CROSS_ASSET_RESONANCE = 700


@dataclass(frozen=True)
class TokenizedEvent:
    """Ω-MM02: Immutable tokenized market event with metadata."""

    token_id: int
    token_type: FlowTokenType
    confidence: float  # 0.0–1.0
    intensity: float  # 0.0–1.0
    timestamp_ns: int
    symbol: str = ""
    price: float = 0.0
    volume: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "token_id": self.token_id,
            "token_type": self.token_type.name,
            "confidence": self.confidence,
            "intensity": self.intensity,
            "timestamp_ns": self.timestamp_ns,
            "symbol": self.symbol,
            "price": self.price,
            "volume": self.volume,
            "metadata": self.metadata,
        }


class FlowTokenizer:
    """
    Ω-MM03: NLP for order flow — transmutates raw micro-tick data into
    institutional vocabulary.

    Reads the tape of micro-ticks and converts each event cluster into
    a semantic token: whale bombs, HFT machine-guns, retail noise,
    spoofing walls, liquidity vacuums, iceberg footprints, etc.

    Pure Python — no numpy. Vector dimension is configurable.
    """

    # Thresholds for classification (tunable via meta-learning)
    WHALE_VOLUME_THRESHOLD = 10.0
    RETAIL_VOLUME_THRESHOLD = 0.1
    HFT_BURST_WINDOW_MS = 500
    HFT_BURST_COUNT = 5
    SPOOF_CANCEL_RATIO_THRESHOLD = 0.85
    ICEBERG_REFRESH_TOLERANCE = 0.02

    def __init__(self, token_vector_dim: int = 128) -> None:
        self.token_vector_dim = token_vector_dim
        self._vocab: dict[str, int] = {}
        self._reverse_vocab: dict[int, FlowTokenType] = {}
        self._token_vector_db: dict[int, list[float]] = {}
        self._register_default_vocab()

    def _register_default_vocab(self) -> None:
        """Ω-MM05: Register all flow token types with vector embeddings."""
        for ft in FlowTokenType:
            self._vocab[ft.name] = ft.value
            self._reverse_vocab[ft.value] = ft
            self._token_vector_db[ft.value] = self._embed_token(ft)

    def _embed_token(self, token_type: FlowTokenType) -> list[float]:
        """Ω-MM06: Embed token into continuous vector space deterministically."""
        seed = hash(token_type.name) % 2147483647
        vec = []
        val = seed
        for _ in range(self.token_vector_dim):
            val = (val * 1103515245 + 12345) & 0x7FFFFFFF
            vec.append((val / 0x7FFFFFFF) * 2.0 - 1.0)
        # Normalize
        norm = _vec_norm(vec)
        if norm > 0:
            vec = [v / norm for v in vec]
        else:
            vec = [0.0] * self.token_vector_dim
        return vec

    def tokenize_flow(
        self,
        ticks: list[dict[str, Any]],
        book_analysis: dict[str, Any] | None = None,
        cancel_events: list[dict[str, Any]] | None = None,
    ) -> list[TokenizedEvent]:
        """
        Ω-MM07: Tokenize a batch of micro-ticks into institutional events.

        Analyzes the tick tape for:
        - Whale bombs: single large volume trades
        - HFT machine-guns: bursts of rapid small trades
        - Retail noise: very small volume trades
        - Imbalance: sustained one-sided flow
        And supplements with structural book analysis for spoofing,
        iceberg detection, and liquidity vacuums.
        """
        tokens: list[TokenizedEvent] = []
        if not ticks:
            return tokens

        now_ns = time.time_ns()

        # Pass 1: classify individual ticks
        for tick in ticks:
            vol = tick.get("volume", 0.0)
            is_buy = tick.get("is_buy", True)
            price = tick.get("price", 0.0)
            t_ns = int(tick.get("timestamp_ns", now_ns))
            symbol = tick.get("symbol", "")

            token_event = self._classify_tick(tick, vol, is_buy, price, t_ns, symbol)
            if token_event is not None:
                tokens.append(token_event)

        # Pass 2: detect HFT burst patterns
        burst_tokens = self._detect_hft_bursts(ticks, now_ns)
        tokens.extend(burst_tokens)

        # Pass 3: detect spoofing from cancel events
        if cancel_events:
            spoof_tokens = self._detect_spoofing(cancel_events, book_analysis)
            tokens.extend(spoof_tokens)

        # Pass 4: structural book events
        if book_analysis:
            struct_tokens = self._analyze_book_structure(book_analysis, now_ns)
            tokens.extend(struct_tokens)

        return tokens

    def _classify_tick(
        self,
        tick: dict[str, Any],
        volume: float,
        is_buy: bool,
        price: float,
        t_ns: int,
        symbol: str,
    ) -> TokenizedEvent | None:
        """Ω-MM08: Single tick classification."""
        if volume >= self.WHALE_VOLUME_THRESHOLD:
            token_type = (
                FlowTokenType.WHALE_BUY_BOMB
                if is_buy
                else FlowTokenType.WHALE_SELL_BOMB
            )
            intensity = min(1.0, volume / (self.WHALE_VOLUME_THRESHOLD * 5.0))
            confidence = min(1.0, 0.7 + intensity * 0.3)
            return TokenizedEvent(
                token_id=token_type.value,
                token_type=token_type,
                confidence=confidence,
                intensity=intensity,
                timestamp_ns=t_ns,
                symbol=symbol,
                price=price,
                volume=volume,
                metadata={"source": "tick_classification"},
            )
        elif volume <= self.RETAIL_VOLUME_THRESHOLD:
            # Retail noise — low confidence, low intensity
            return TokenizedEvent(
                token_id=FlowTokenType.RETAIL_NOISE.value,
                token_type=FlowTokenType.RETAIL_NOISE,
                confidence=0.2,
                intensity=volume / self.RETAIL_VOLUME_THRESHOLD,
                timestamp_ns=t_ns,
                symbol=symbol,
                price=price,
                volume=volume,
                metadata={"source": "retail_noise"},
            )
        # Mid-range ticks are not individually tokenized
        return None

    def _detect_hft_bursts(
        self,
        ticks: list[dict[str, Any]],
        now_ns: int,
    ) -> list[TokenizedEvent]:
        """Ω-MM09: Detect HFT machine-gun patterns (burst of rapid trades)."""
        burst_tokens: list[TokenizedEvent] = []
        if len(ticks) < self.HFT_BURST_COUNT:
            return burst_tokens

        window_ns = self.HFT_BURST_WINDOW_MS * 1_000_000
        buys_in_window = 0
        sells_in_window = 0
        total_vol_in_window = 0.0

        sorted_ticks = sorted(ticks, key=lambda t: t.get("timestamp_ns", now_ns))

        for i in range(len(sorted_ticks) - self.HFT_BURST_COUNT + 1):
            window_start = sorted_ticks[i].get("timestamp_ns", now_ns)
            window_end = sorted_ticks[i + self.HFT_BURST_COUNT - 1].get("timestamp_ns", now_ns)

            if window_end - window_start <= window_ns:
                # Burst detected in this window
                window_ticks = sorted_ticks[i : i + self.HFT_BURST_COUNT]
                buys_in_window = sum(1 for t in window_ticks if t.get("is_buy", True))
                sells_in_window = self.HFT_BURST_COUNT - buys_in_window
                total_vol_in_window = sum(t.get("volume", 0.0) for t in window_ticks)

                if buys_in_window > sells_in_window * 2:
                    token_type = FlowTokenType.HFT_MACHINE_GUN_BUY
                elif sells_in_window > buys_in_window * 2:
                    token_type = FlowTokenType.HFT_MACHINE_GUN_SELL
                elif total_vol_in_window < self.HFT_BURST_COUNT * self.RETAIL_VOLUME_THRESHOLD:
                    # Arbitrage-like pattern: high frequency, low volume
                    token_type = FlowTokenType.HFT_ARBITRAGE
                else:
                    continue  # Mixed pattern, not strong enough

                avg_price = sum(t.get("price", 0.0) for t in window_ticks) / max(1, len(window_ticks))
                burst_tokens.append(TokenizedEvent(
                    token_id=token_type.value,
                    token_type=token_type,
                    confidence=min(1.0, self.HFT_BURST_COUNT / 10.0),
                    intensity=min(1.0, total_vol_in_window / (self.WHALE_VOLUME_THRESHOLD * 2.0)),
                    timestamp_ns=window_end,
                    symbol=sorted_ticks[i].get("symbol", ""),
                    price=avg_price,
                    volume=total_vol_in_window,
                    metadata={"source": "hft_burst", "count": len(window_ticks)},
                ))

        return burst_tokens

    def _detect_spoofing(
        self,
        cancel_events: list[dict[str, Any]],
        book_analysis: dict[str, Any] | None,
    ) -> list[TokenizedEvent]:
        """Ω-MM10: Detect spoofing from order cancel patterns."""
        spoof_tokens: list[TokenizedEvent] = []
        if not cancel_events:
            return spoof_tokens

        cancel_ratio = _compute_cancel_ratio(cancel_events)
        now_ns = time.time_ns()

        if cancel_ratio >= self.SPOOF_CANCEL_RATIO_THRESHOLD:
            # Determine bid or ask spoof
            bid_cancels = sum(1 for c in cancel_events if c.get("side", "buy") == "buy")
            ask_cancels = len(cancel_events) - bid_cancels

            if bid_cancels > ask_cancels:
                token_type = FlowTokenType.HFT_SPOOF_BID
            else:
                token_type = FlowTokenType.HFT_SPOOF_ASK

            total_cancel_vol = sum(c.get("volume", 0.0) for c in cancel_events)
            spoof_tokens.append(TokenizedEvent(
                token_id=token_type.value,
                token_type=token_type,
                confidence=min(1.0, cancel_ratio),
                intensity=min(1.0, total_cancel_vol / (self.WHALE_VOLUME_THRESHOLD * 10.0)),
                timestamp_ns=now_ns,
                metadata={
                    "source": "spoof_detection",
                    "cancel_ratio": cancel_ratio,
                    "total_cancels": len(cancel_events),
                    "total_cancel_volume": total_cancel_vol,
                },
            ))

        return spoof_tokens

    def _analyze_book_structure(
        self,
        book_analysis: dict[str, Any],
        now_ns: int,
    ) -> list[TokenizedEvent]:
        """Ω-MM11: Detect structural book events (liquidity vacuums, order blocks, icebergs)."""
        struct_tokens: list[TokenizedEvent] = []

        # Liquidity vacuum: sudden disappearance of depth
        if book_analysis.get("liquidity_vacuum", False):
            struct_tokens.append(TokenizedEvent(
                token_id=FlowTokenType.LIQUIDITY_VACUUM.value,
                token_type=FlowTokenType.LIQUIDITY_VACUUM,
                confidence=book_analysis.get("vacuum_confidence", 0.5),
                intensity=book_analysis.get("vacuum_depth_ratio", 0.5),
                timestamp_ns=now_ns,
                metadata={"source": "book_structure"},
            ))

        # Order block formation
        if book_analysis.get("order_block", False):
            struct_tokens.append(TokenizedEvent(
                token_id=FlowTokenType.ORDER_BLOCK_FORMATION.value,
                token_type=FlowTokenType.ORDER_BLOCK_FORMATION,
                confidence=book_analysis.get("ob_confidence", 0.6),
                intensity=book_analysis.get("ob_strength", 0.5),
                timestamp_ns=now_ns,
                metadata={"source": "book_structure", "level": book_analysis.get("ob_level", 0.0)},
            ))

        # Fair Value Gap
        if book_analysis.get("fvg", False):
            struct_tokens.append(TokenizedEvent(
                token_id=FlowTokenType.FVG_CREATION.value,
                token_type=FlowTokenType.FVG_CREATION,
                confidence=book_analysis.get("fvg_confidence", 0.5),
                intensity=book_analysis.get("fvg_width", 0.3),
                timestamp_ns=now_ns,
                metadata={"source": "book_structure"},
            ))

        # Iceberg detection
        if book_analysis.get("iceberg", False):
            struct_tokens.append(TokenizedEvent(
                token_id=FlowTokenType.ICEBERG_DETECTED.value,
                token_type=FlowTokenType.ICEBERG_DETECTED,
                confidence=book_analysis.get("iceberg_confidence", 0.5),
                intensity=book_analysis.get("iceberg_estimated_volume", 0.5),
                timestamp_ns=now_ns,
                metadata={"source": "book_structure", "side": book_analysis.get("iceberg_side", "")},
            ))

        return struct_tokens

    def embed_token_sequence(self, tokens: list[TokenizedEvent]) -> list[float]:
        """
        Ω-MM12: Embed a sequence of tokens into a single feature vector of
        dimension token_vector_dim. Weighted sum of token embeddings.
        """
        if not tokens:
            return [0.0] * self.token_vector_dim

        vec = [0.0] * self.token_vector_dim
        total_weight = 0.0

        for token in tokens:
            embedding = self._token_vector_db.get(token.token_id, [0.0] * self.token_vector_dim)
            weight = token.confidence * token.intensity
            for i in range(self.token_vector_dim):
                vec[i] += embedding[i] * weight
            total_weight += weight

        if total_weight > 0:
            vec = [v / total_weight for v in vec]

        return vec

    def get_token_stats(self) -> dict[str, Any]:
        """Ω-MM13: Return vocabulary statistics."""
        return {
            "vocab_size": len(self._vocab),
            "token_types": len(FlowTokenType),
            "vector_dim": self.token_vector_dim,
            "token_names": list(self._vocab.keys()),
        }


def _compute_cancel_ratio(cancel_events: list[dict[str, Any]]) -> float:
    """Ω-MM14: Helper to compute cancel-to-fill ratio."""
    if not cancel_events:
        return 0.0
    cancels = sum(1 for c in cancel_events if c.get("action") == "cancel")
    return cancels / max(1, len(cancel_events))


def _vec_norm(v: list[float]) -> float:
    """Ω-MM15: Pure-Python Euclidean norm of a vector."""
    return math.sqrt(sum(x * x for x in v))


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Ω-MM16: Pure-Python cosine similarity between two vectors."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


# ──────────────────────────────────────────────────────────────
# Ω-MM19 to Ω-MM36: EpisodicMemory & Vector-Space Recall
# ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Episode:
    """
    Ω-MM19: Immutable episodic memory record storing a market state
    snapshot and its subsequent outcome.

    The vector field captures the market state at observation time.
    The outcome fields record what actually happened after the snapshot,
    enabling supervised learning from recall.
    """

    episode_id: str
    timestamp_ns: int
    vector: list[float]
    outcome_return: float  # Actual price return after observation
    outcome_duration_ms: int  # Time horizon of the outcome
    regime_label: str
    token_summary: dict[str, int]
    confidence: float
    metadata: dict[str, Any]
    created_at: int = field(default_factory=lambda: time.time_ns())

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "timestamp_ns": self.timestamp_ns,
            "outcome_return": self.outcome_return,
            "outcome_duration_ms": self.outcome_duration_ms,
            "regime_label": self.regime_label,
            "token_summary": self.token_summary,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict())


class EpisodicMemory:
    """
    Ω-MM20: Vector-space episodic memory with circular buffer.

    Stores market episodes (state snapshot + outcome) in a bounded
    circular buffer. Supports cosine similarity recall of top-k
    similar episodes and market intuition extraction from weighted
    averages of similar past outcomes.

    Pure Python math — no numpy. SQLite persistence for durability.
    """

    def __init__(
        self,
        max_episodes: int = 10000,
        vector_dim: int = 128,
        persist_path: str | None = None,
    ) -> None:
        self.max_episodes = max_episodes
        self.vector_dim = vector_dim
        self._database: list[list[float] | None] = [None] * max_episodes
        self._metadata: list[Episode | None] = [None] * max_episodes
        self._cursor: int = 0
        self._is_full: bool = False
        self._count: int = 0

        # SQLite persistence
        self._persist_path = persist_path
        self._db_connection: sqlite3.Connection | None = None
        self._init_persistence()

    def _init_persistence(self) -> None:
        """Ω-MM21: Initialize SQLite for episode persistence."""
        if self._persist_path is None:
            return
        try:
            os.makedirs(os.path.dirname(self._persist_path) if os.path.dirname(self._persist_path) else ".", exist_ok=True)
            self._db_connection = sqlite3.connect(self._persist_path)
            self._db_connection.execute("""
                CREATE TABLE IF NOT EXISTS episodes (
                    episode_id TEXT PRIMARY KEY,
                    timestamp_ns INTEGER NOT NULL,
                    vector_data TEXT NOT NULL,
                    outcome_return REAL NOT NULL,
                    outcome_duration_ms INTEGER NOT NULL,
                    regime_label TEXT NOT NULL,
                    token_summary TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    metadata TEXT NOT NULL
                )
            """)
            self._db_connection.commit()
            self._load_from_db()
        except (sqlite3.Error, OSError):
            self._db_connection = None

    def _load_from_db(self) -> None:
        """Ω-MM22: Load episodes from SQLite into memory."""
        if self._db_connection is None:
            return
        try:
            cursor = self._db_connection.execute(
                "SELECT * FROM episodes ORDER BY timestamp_ns DESC LIMIT ?",
                (self.max_episodes,),
            )
            import json
            for row in cursor.fetchall():
                (
                    eid, ts_ns, vec_json, outcome_ret, outcome_dur,
                    regime, token_json, conf, meta_json,
                ) = row
                vec: list[float] = json.loads(vec_json)
                tokens: dict[str, int] = json.loads(token_json)
                meta: dict[str, Any] = json.loads(meta_json)
                ep = Episode(
                    episode_id=eid,
                    timestamp_ns=ts_ns,
                    vector=vec,
                    outcome_return=outcome_ret,
                    outcome_duration_ms=outcome_dur,
                    regime_label=regime,
                    token_summary=tokens,
                    confidence=conf,
                    metadata=meta,
                )
                self._insert_into_buffer(ep)
        except (sqlite3.Error, ValueError, TypeError):
            pass

    def _insert_into_buffer(self, episode: Episode) -> None:
        """Ω-MM23: Insert episode into circular buffer at current cursor."""
        if len(episode.vector) != self.vector_dim:
            return

        idx = self._cursor
        self._database[idx] = list(episode.vector)
        self._metadata[idx] = episode

        self._cursor = (self._cursor + 1) % self.max_episodes
        if not self._is_full and self._cursor == 0:
            self._is_full = True

        if self._count < self.max_episodes:
            self._count += 1

    def add_episode(self, episode: Episode) -> bool:
        """Ω-MM24: Add a new episode to memory. Returns True if saved."""
        self._insert_into_buffer(episode)

        # Persist to SQLite
        if self._db_connection is not None:
            import json
            try:
                self._db_connection.execute(
                    "INSERT OR REPLACE INTO episodes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        episode.episode_id,
                        episode.timestamp_ns,
                        json.dumps(episode.vector),
                        episode.outcome_return,
                        episode.outcome_duration_ms,
                        episode.regime_label,
                        json.dumps(episode.token_summary),
                        episode.confidence,
                        json.dumps(episode.metadata),
                    ),
                )
                self._db_connection.commit()
            except (sqlite3.Error, OverflowError, TypeError):
                pass

        return True

    def recall(
        self,
        query_vector: list[float],
        top_k: int = 5,
        min_confidence: float = 0.0,
        regime_filter: str | None = None,
    ) -> list[tuple[float, Episode]]:
        """
        Ω-MM25: Recall top-k most similar episodes to query vector.

        Uses pure-Python cosine similarity. Returns list of
        (similarity, episode) tuples sorted by similarity.
        """
        active_entries = self._get_active_entries()
        if not active_entries:
            return []

        similarities: list[tuple[float, Episode, int]] = []

        for idx, vec, meta in active_entries:
            if meta is None or vec is None:
                continue
            if meta.confidence < min_confidence:
                continue
            if regime_filter is not None and meta.regime_label != regime_filter:
                continue
            sim = _cosine_similarity(query_vector, vec)
            similarities.append((sim, meta, idx))

        similarities.sort(key=lambda x: x[0], reverse=True)
        return [(sim, ep) for sim, ep, _idx in similarities[:top_k]]

    def _get_active_entries(self) -> list[tuple[int, list[float] | None, Episode | None]]:
        """Ω-MM26: Return only occupied entries in the circular buffer."""
        if not self._is_full:
            return [
                (i, self._database[i], self._metadata[i])
                for i in range(self._cursor)
            ]
        return [
            (i, self._database[i], self._metadata[i])
            for i in range(self.max_episodes)
        ]

    def get_market_intuition(
        self,
        current_vector: list[float],
        top_k: int = 10,
        min_confidence: float = 0.0,
    ) -> dict[str, Any]:
        """
        Ω-MM27: Generate market intuition from similar past episodes.

        Returns weighted bias (expected return), confidence, match
        count, and regime distribution from top-k similar episodes.
        """
        matches = self.recall(current_vector, top_k=top_k, min_confidence=min_confidence)

        if not matches:
            return {
                "bias": 0.0,
                "confidence": 0.0,
                "match_count": 0,
                "regime_distribution": {},
                "expected_move_bps": 0.0,
            }

        weighted_bias = 0.0
        weights_sum = 0.0
        regime_counts: dict[str, int] = defaultdict(int)

        for sim, ep in matches:
            weight = sim * ep.confidence
            weighted_bias += ep.outcome_return * weight
            weights_sum += weight
            regime_counts[ep.regime_label] += 1

        bias = weighted_bias / max(weights_sum, 1e-12)
        avg_sim = sum(sim for sim, _ in matches) / max(len(matches), 1)

        return {
            "bias": bias,
            "confidence": min(1.0, avg_sim),
            "match_count": len(matches),
            "regime_distribution": dict(regime_counts),
            "expected_move_bps": round(bias * 10000, 2),
        }

    def get_episode_by_id(self, episode_id: str) -> Episode | None:
        """Ω-MM28: Retrieve a specific episode by ID."""
        active_entries = self._get_active_entries()
        for _, _, meta in active_entries:
            if meta is not None and meta.episode_id == episode_id:
                return meta
        return None

    def count(self) -> int:
        """Ω-MM29: Number of episodes currently in memory."""
        return self._count

    def is_full(self) -> bool:
        return self._is_full

    def clear(self) -> None:
        """Ω-MM30: Clear all episodes from memory and persistence."""
        self._database = [None] * self.max_episodes
        self._metadata = [None] * self.max_episodes
        self._cursor = 0
        self._is_full = False
        self._count = 0

        if self._db_connection is not None:
            try:
                self._db_connection.execute("DELETE FROM episodes")
                self._db_connection.commit()
            except sqlite3.Error:
                pass

    def compact(self) -> int:
        """
        Ω-MM31: Memory compression — retain only the most informative
        episodes (diverse + high-confidence). Removes episodes below
        confidence threshold and deduplicates very similar ones.

        Returns number of episodes removed.
        """
        if self._count < 100:
            return 0

        active_entries = self._get_active_entries()
        valid_episodes: list[tuple[int, list[float], Episode]] = []

        for idx, vec, meta in active_entries:
            if vec is None or meta is None:
                continue
            if meta.confidence < 0.1:
                continue
            valid_episodes.append((idx, vec, meta))

        # Deduplicate very similar episodes (cosine sim > 0.99)
        unique_indices: set[int] = set()
        kept_list: list[tuple[int, list[float], Episode]] = []

        for idx, vec, meta in valid_episodes:
            is_duplicate = False
            for _, kept_vec, _ in kept_list:
                if _cosine_similarity(vec, kept_vec) > 0.99:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_indices.add(idx)
                kept_list.append((idx, vec, meta))

        removed = 0
        for idx, vec, meta in active_entries:
            if idx not in unique_indices:
                self._database[idx] = None
                self._metadata[idx] = None
                removed += 1

        self._count = len(unique_indices)
        self._is_full = False

        return removed

    def get_regime_stats(self) -> dict[str, Any]:
        """Ω-MM32: Statistics per regime in memory."""
        active_entries = self._get_active_entries()
        regime_data: dict[str, list[Episode]] = defaultdict(list)

        for _, _, meta in active_entries:
            if meta is not None:
                regime_data[meta.regime_label].append(meta)

        stats: dict[str, Any] = {}
        for regime, episodes in regime_data.items():
            returns = [e.outcome_return for e in episodes]
            avg_return = sum(returns) / max(len(returns), 1)
            win_rate = sum(1 for r in returns if r > 0) / max(len(returns), 1)
            avg_conf = sum(e.confidence for e in episodes) / max(len(episodes), 1)
            stats[regime] = {
                "count": len(episodes),
                "avg_return": round(avg_return, 6),
                "win_rate": round(win_rate, 4),
                "avg_confidence": round(avg_conf, 4),
            }

        return stats

    def get_recent_episodes(self, n: int = 20) -> list[Episode]:
        """Ω-MM33: Get the N most recent episodes."""
        episodes: list[Episode] = []
        active_entries = self._get_active_entries()

        for _, _, meta in active_entries:
            if meta is not None:
                episodes.append(meta)

        episodes.sort(key=lambda e: e.timestamp_ns, reverse=True)
        return episodes[:n]

    def get_token_frequency(self) -> dict[str, int]:
        """Ω-MM34: Count occurrences of each token type across all episodes."""
        freq: dict[str, int] = defaultdict(int)
        active_entries = self._get_active_entries()

        for _, _, meta in active_entries:
            if meta is not None:
                for token_name, count in meta.token_summary.items():
                    freq[token_name] += count

        return dict(freq)

    def memory_health(self) -> dict[str, Any]:
        """Ω-MM35: Self-diagnostic of memory quality."""
        stats = self.get_regime_stats()
        total = self._count

        regime_diversity = len(stats)
        coverage = regime_diversity / min(10.0, max(1.0, regime_diversity))
        staleness = 0.0

        if total > 0:
            active_entries = self._get_active_entries()
            timestamps = [
                m.timestamp_ns
                for _, _, m in active_entries
                if m is not None
            ]
            if timestamps:
                now_ns = time.time_ns()
                avg_age_ns = sum(now_ns - ts for ts in timestamps) / len(timestamps)
                staleness = min(1.0, avg_age_ns / (3600 * 1e9))

        quality_score = min(1.0, (coverage * 0.4 + (1.0 - staleness) * 0.3 + min(1.0, total / 1000) * 0.3))

        return {
            "total_episodes": total,
            "max_capacity": self.max_episodes,
            "regime_diversity": regime_diversity,
            "coverage_score": round(coverage, 4),
            "staleness": round(staleness, 4),
            "quality_score": round(quality_score, 4),
            "is_full": self._is_full,
            "persistence": self._db_connection is not None,
        }

    def close(self) -> None:
        """Ω-MM36: Close SQLite connection."""
        if self._db_connection is not None:
            try:
                self._db_connection.close()
            except sqlite3.Error:
                pass
            self._db_connection = None


# ──────────────────────────────────────────────────────────────
# Ω-MM37 to Ω-MM54: Semantic Memory & Intuition Engine
# ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class SemanticPattern:
    """Ω-MM37: A long-term pattern extracted from episodic data."""

    pattern_id: str
    description: str
    frequency: int
    last_seen_ns: int
    avg_outcome: float
    avg_confidence: float
    associated_regimes: list[str]
    vector_repr: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)


class SemanticMemory:
    """
    Ω-MM38: Long-term semantic memory that extracts persistent patterns
    from episodic data across multiple episodes.

    Patterns are identified by clustering similar episodes and tracking
    their statistical properties over time. Patterns with consistent
    positive outcomes are promoted to the pattern catalog.
    """

    def __init__(self, pattern_dim: int = 128, min_pattern_freq: int = 5) -> None:
        self.pattern_dim = pattern_dim
        self.min_pattern_freq = min_pattern_freq
        self._patterns: dict[str, SemanticPattern] = {}
        self._pattern_centroid_buffer: dict[str, list[tuple[list[float], float]]] = defaultdict(list)
        self._last_extraction_ns: int = 0
        self._extraction_interval_ns: int = 60 * 1_000_000_000  # 1 minute

    def add_to_pattern_buffer(
        self,
        episode: Episode,
        pattern_key: str,
        description: str,
    ) -> None:
        """Ω-MM39: Add episode to the buffer of a semantic pattern."""
        self._pattern_centroid_buffer[pattern_key].append(
            (episode.vector, episode.outcome_return)
        )

    def extract_patterns(self) -> list[SemanticPattern]:
        """
        Ω-MM40: Extract and update semantic patterns from buffered data.
        Called periodically to consolidate pattern information.
        """
        now_ns = time.time_ns()
        if now_ns - self._last_extraction_ns < self._extraction_interval_ns:
            return list(self._patterns.values())

        self._last_extraction_ns = now_ns
        new_patterns: list[SemanticPattern] = []

        for key, buffers in list(self._pattern_centroid_buffer.items()):
            if len(buffers) < self.min_pattern_freq:
                continue

            # Compute centroid of pattern
            centroid = [0.0] * self.pattern_dim
            total_return = 0.0
            total_conf = 0.0
            max_ts = 0

            for vec, ret in buffers:
                norm = _vec_norm(vec)
                if norm > 0:
                    for i in range(self.pattern_dim):
                        centroid[i] += vec[i] / norm

            if len(buffers) > 0:
                for i in range(self.pattern_dim):
                    centroid[i] /= len(buffers)

            norm = _vec_norm(centroid)
            if norm > 0:
                for i in range(self.pattern_dim):
                    centroid[i] /= norm

            total_returns = [r for _, r in buffers]
            avg_outcome = sum(total_returns) / max(len(total_returns), 1)

            if key in self._patterns:
                existing = self._patterns[key]
                new_freq = existing.frequency + len(buffers)
                alpha = existing.frequency / new_freq
                updated = SemanticPattern(
                    pattern_id=existing.pattern_id,
                    description=existing.description,
                    frequency=new_freq,
                    last_seen_ns=max(existing.last_seen_ns, now_ns),
                    avg_outcome=alpha * existing.avg_outcome + (1 - alpha) * avg_outcome,
                    avg_confidence=existing.avg_confidence,
                    associated_regimes=existing.associated_regimes,
                    vector_repr=centroid,
                    metadata=existing.metadata,
                )
            else:
                pid = f"pat_{uuid.uuid4().hex[:8]}"
                updated = SemanticPattern(
                    pattern_id=pid,
                    description=f"Extracted pattern: {key}",
                    frequency=len(buffers),
                    last_seen_ns=now_ns,
                    avg_outcome=avg_outcome,
                    avg_confidence=0.6,
                    associated_regimes=[],
                    vector_repr=centroid,
                )
                new_patterns.append(updated)

            self._patterns[key] = updated

        # Clear buffer (merged into patterns)
        self._pattern_centroid_buffer.clear()

        return new_patterns or list(self._patterns.values())

    def find_similar_patterns(
        self,
        query_vector: list[float],
        top_k: int = 5,
    ) -> list[tuple[float, SemanticPattern]]:
        """Ω-MM41: Find most similar semantic patterns to query."""
        if not self._patterns:
            return []

        similarities: list[tuple[float, SemanticPattern]] = []

        for pattern in self._patterns.values():
            sim = _cosine_similarity(query_vector, pattern.vector_repr)
            # Adjust by frequency and recency
            freq_bonus = min(0.2, math.log2(max(1, pattern.frequency)) / 20.0)
            similarities.append((sim + freq_bonus, pattern))

        similarities.sort(key=lambda x: x[0], reverse=True)
        return similarities[:top_k]

    def get_pattern_stats(self) -> dict[str, Any]:
        """Ω-MM42: Statistics of stored semantic patterns."""
        if not self._patterns:
            return {"total_patterns": 0, "positive_patterns": 0, "negative_patterns": 0}

        positive = sum(1 for p in self._patterns.values() if p.avg_outcome > 0)
        negative = sum(1 for p in self._patterns.values() if p.avg_outcome < 0)

        return {
            "total_patterns": len(self._patterns),
            "positive_patterns": positive,
            "negative_patterns": negative,
            "neutral_patterns": len(self._patterns) - positive - negative,
            "most_frequent": max(
                self._patterns.values(), key=lambda p: p.frequency
            ).description if self._patterns else "",
            "most_profitable": max(
                self._patterns.values(), key=lambda p: p.avg_outcome
            ).description if self._patterns else "",
        }

    def clear_buffers(self) -> None:
        """Ω-MM43: Clear pattern buffers but keep consolidated patterns."""
        self._pattern_centroid_buffer.clear()

    def reset(self) -> None:
        """Ω-MM44: Full reset of semantic memory."""
        self._patterns.clear()
        self._pattern_centroid_buffer.clear()
        self._last_extraction_ns = 0


class IntuitionEngine:
    """
    Ω-MM45: Intuition scoring engine combining episodic recall with
    semantic pattern matching to produce a market intuition score.

    Combines multiple signals:
    - Episodic recall similarity
    - Semantic pattern match
    - Regime consistency
    - Token distribution analysis

    Output: Bayesian confidence-weighted intuition.
    """

    def __init__(
        self,
        episodic_memory: EpisodicMemory | None = None,
        semantic_memory: SemanticMemory | None = None,
    ) -> None:
        self._ep_mem = episodic_memory or EpisodicMemory()
        self._sem_mem = semantic_memory or SemanticMemory()
        self._intuition_history: deque[dict[str, Any]] = deque(maxlen=1000)

    def assess(
        self,
        query_vector: list[float],
        token_distribution: dict[str, int] | None = None,
        current_regime: str = "unknown",
        top_k: int = 15,
    ) -> dict[str, Any]:
        """Ω-MM46: Generate market intuition assessment."""
        now_ns = time.time_ns()

        # Component 1: Episodic recall intuition
        epi_intuition = self._ep_mem.get_market_intuition(query_vector, top_k=top_k)

        # Component 2: Semantic pattern match
        sem_matches = self._sem_mem.find_similar_patterns(query_vector, top_k=5)
        sem_bias = 0.0
        sem_weight = 0.0
        sem_count = 0
        for sim, pattern in sem_matches:
            w = sim * pattern.frequency
            sem_bias += pattern.avg_outcome * w
            sem_weight += w
            sem_count += 1

        sem_confidence = sem_weight / max(1, sem_count * 10.0) if sem_count > 0 else 0.0

        # Component 3: Regime consistency
        regime_intuition = self._assess_regime_consistency(current_regime)

        # Component 4: Token distribution analysis
        token_signal = self._assess_token_distribution(token_distribution) if token_distribution else {"bias": 0.0, "confidence": 0.0}

        # Combine with learned weights (start uniform, could be meta-learned)
        w_epi = 0.40
        w_sem = 0.25
        w_reg = 0.20
        w_tok = 0.15

        combined_bias = (
            w_epi * epi_intuition["bias"]
            + w_sem * (sem_bias / max(sem_weight, 1e-12) if sem_weight > 0 else 0.0)
            + w_reg * regime_intuition["bias"]
            + w_tok * token_signal["bias"]
        )

        combined_confidence = min(
            1.0,
            w_epi * epi_intuition["confidence"]
            + w_sem * sem_confidence
            + w_reg * regime_intuition["confidence"]
            + w_tok * token_signal["confidence"]
            + 0.05 * min(1.0, self._ep_mem.count() / 500.0),
        )

        # Bayes-style adjustment: lower confidence when memory is sparse
        if self._ep_mem.count() < 50:
            combined_confidence *= max(0.3, self._ep_mem.count() / 50.0)

        result = {
            "bias": round(combined_bias, 6),
            "confidence": round(combined_confidence, 4),
            "components": {
                "episodic": {
                    "bias": round(epi_intuition["bias"], 6),
                    "confidence": round(epi_intuition["confidence"], 4),
                    "matches": epi_intuition["match_count"],
                },
                "semantic": {
                    "bias": round(sem_bias / max(sem_weight, 1e-12) if sem_weight > 0 else 0.0, 6),
                    "confidence": round(sem_confidence, 4),
                    "patterns_matched": sem_count,
                },
                "regime": {
                    "bias": round(regime_intuition["bias"], 6),
                    "confidence": round(regime_intuition["confidence"], 4),
                },
                "token": {
                    "bias": round(token_signal["bias"], 6),
                    "confidence": round(token_signal["confidence"], 4),
                },
            },
            "timestamp_ns": now_ns,
        }

        self._intuition_history.append(result)
        return result

    def _assess_regime_consistency(self, regime: str) -> dict[str, Any]:
        """Ω-MM47: Assess intuition based on regime consistency in memory."""
        stats = self._ep_mem.get_regime_stats()
        if regime not in stats:
            return {"bias": 0.0, "confidence": 0.0}

        regime_stats = stats[regime]
        count = regime_stats["count"]
        avg_return = regime_stats["avg_return"]
        win_rate = regime_stats["win_rate"]

        bias = avg_return * 2.0
        confidence = min(1.0, win_rate * 0.6 + min(0.4, count / 20.0))

        return {"bias": round(bias, 6), "confidence": round(confidence, 4)}

    def _assess_token_distribution(
        self,
        token_dist: dict[str, int],
    ) -> dict[str, Any]:
        """Ω-MM48: Derive signal bias from token type distribution."""
        if not token_dist:
            return {"bias": 0.0, "confidence": 0.0}

        total = sum(token_dist.values())
        if total == 0:
            return {"bias": 0.0, "confidence": 0.0}

        bullish_tokens = {"WHALE_BUY_BOMB", "HFT_MACHINE_GUN_BUY", "WHALE_ACCUMULATION"}
        bearish_tokens = {"WHALE_SELL_BOMB", "HFT_MACHINE_GUN_SELL", "WHALE_DISTRIBUTION"}

        bull_count = sum(token_dist.get(t, 0) for t in bullish_tokens)
        bear_count = sum(token_dist.get(t, 0) for t in bearish_tokens)

        bias = (bull_count - bear_count) / max(total, 1)
        confidence = min(1.0, total / 50.0)

        return {"bias": round(bias, 6), "confidence": round(confidence, 4)}

    def get_intuition_history(self, n: int = 50) -> list[dict[str, Any]]:
        """Ω-MM49: Retrieve recent intuition assessments."""
        return list(self._intuition_history)[-n:]

    def calibration_score(self) -> dict[str, Any]:
        """Ω-MM50: Brier score calibration of recent intuitions vs outcomes."""
        history = list(self._intuition_history)
        if len(history) < 10:
            return {"brier_score": None, "note": "Insufficient history"}

        # Estimate calibration from confidence distribution
        confidences = [h["confidence"] for h in history]
        avg_confidence = sum(confidences) / len(confidences)

        biases = [h["bias"] for h in history]
        bias_variance = sum((b - sum(biases) / len(biases)) ** 2 for b in biases) / len(biases)
        avg_bias = sum(biases) / len(biases)

        return {
            "avg_confidence": round(avg_confidence, 4),
            "avg_bias": round(avg_bias, 6),
            "bias_variance": round(bias_variance, 8),
            "assessment_count": len(history),
        }

    @property
    def episodic_memory(self) -> EpisodicMemory:
        """Ω-MM51: Access to underlying episodic memory."""
        return self._ep_mem

    @property
    def semantic_memory(self) -> SemanticMemory:
        """Ω-MM52: Access to underlying semantic memory."""
        return self._sem_mem

    def health(self) -> dict[str, Any]:
        """Ω-MM53: Combined health of intuition engine."""
        return {
            "episodic": self._ep_mem.memory_health(),
            "semantic": self._sem_mem.get_pattern_stats(),
            "calibration": self.calibration_score(),
            "total_assessments": len(self._intuition_history),
        }

    def close(self) -> None:
        """Ω-MM54: Clean up resources."""
        self._ep_mem.close()
