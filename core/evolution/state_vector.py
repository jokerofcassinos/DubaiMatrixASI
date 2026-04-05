"""
SOLÉNN v2 — State Vector Engine: Market Context Discretization (Ω-SV01 a Ω-SV54)
Replaces v1 StateVectorData with full multi-dimensional state discretization
system. Market's continuous state is quantized into a topological DNA hash
that enables genetic agent profiling — agents are tracked per-state to know
WHERE they perform (not just globally).

Concept 1: State Dimension Extraction & Classification (Ω-SV01–SV18)
  Discretizes market into orthogonal dimensions: session, regime, velocity,
  entropy, volatility, order flow imbalance, spread quality, and trend
  structure. Each dimension maps to a discrete bin. Dimensions are designed
  to be near-orthogonal (minimal mutual information).

Concept 2: Topological Hashing & State Similarity (Ω-SV19–SV36)
  Creates deterministic hash from discretized dimensions. Computes state
  similarity via weighted Hamming distance. States are clustered dynamically
  to avoid hyperfragmentation (too many unique states = no signal per state).

Concept 3: Agent-State Performance Profiling (Ω-SV37–SV54)
  Tracks each agent's performance per state vector. Identifies state-specific
  specialists and generalists. Provides state-aware routing — weight agents
  higher in states where they have proven track records.
"""

from __future__ import annotations

import hashlib
import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ──────────────────────────────────────────────────────────────
# Ω-SV01 to Ω-SV18: State Dimension Extraction & Classification
# ──────────────────────────────────────────────────────────────


class SessionType(Enum):
    """Ω-SV01: Market session classification by liquidity profile."""

    ASIAN = "asian"
    LONDON = "london"
    NY_OPEN = "ny_open"
    NY_CLOSE = "ny_close"
    DEAD = "dead"
    UNKNOWN = "unknown"


class RegimeType(Enum):
    """Ω-SV02: Regime type simplified for state vector."""

    TREND_UP = "trend_up"
    TREND_DOWN = "trend_down"
    IGNITION = "ignition"
    REVERSAL = "reversal"
    RANGE_TIGHT = "range_tight"
    RANGE_WIDE = "range_wide"
    CHOPPY = "choppy"
    UNKNOWN = "unknown"


class VelocityBand(Enum):
    """Ω-SV03: Tick velocity classification — raw speed of tape."""

    HFT_BURST = "hft_burst"  # > 20 ticks/s
    HIGH = "high"  # 10–20 ticks/s
    MEDIUM = "medium"  # 3–10 ticks/s
    LOW = "low"  # < 3 ticks/s
    FROZEN = "frozen"  # no ticks


class EntropyState(Enum):
    """Ω-SV04: Shannon entropy — informational disorder."""

    CHAOTIC = "chaotic"  # > 6.5 bits — near random walk
    COMPLEX = "complex"  # 3.0–6.5 bits — normal dynamics
    ORDERED = "ordered"  # < 3.0 bits — clean trend or pattern


class VolatilityState(Enum):
    """Ω-SV05: ATR-based volatility classification."""

    EXTREME = "extreme"  # ATR > 150
    HIGH = "high"  # ATR 80–150
    NORMAL = "normal"  # ATR 30–80
    COMPRESSED = "compressed"  # ATR < 30
    UNKNOWN = "unknown"


class FlowImbalance(Enum):
    """Ω-SV06: Order flow net imbalance direction and strength."""

    STRONG_BUY = "strong_buy"  # > 70% buy
    MODERATE_BUY = "moderate_buy"  # 55–70% buy
    NEUTRAL = "neutral"  # 45–55%
    MODERATE_SELL = "moderate_sell"  # 55–70% sell
    STRONG_SELL = "strong_sell"  # > 70% sell
    UNKNOWN = "unknown"


class SpreadQuality(Enum):
    """Ω-SV07: Bid-ask spread quality relative to historical norm."""

    TIGHT = "tight"  # < 50% of median spread
    NORMAL = "normal"  # 50–150% of median spread
    WIDE = "wide"  # 150–300% of median spread
    BLOWN = "blown"  # > 300% — liquidity dried up
    UNKNOWN = "unknown"


class TrendStructure(Enum):
    """Ω-SV08: Market micro-structure via swing analysis."""

    UPTREND_HH_HL = "uptrend_hh_hl"
    DOWNTREND_LH_LL = "downtrend_lh_ll"
    RANGE = "range"
    EXPANSION = "expansion"  # breaking out
    CONTRACTION = "contraction"  # compressing
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class StateVector:
    """Ω-SV09: Immutable discretized market state vector.

    Each field is a discrete classification. The profile_hash is a
    deterministic topological hash of all dimensions.
    """

    timestamp_ns: int
    session: SessionType
    regime: RegimeType
    velocity: VelocityBand
    entropy: EntropyState
    volatility: VolatilityState
    flow_imbalance: FlowImbalance
    spread_quality: SpreadQuality
    trend_structure: TrendStructure

    @property
    def profile_hash(self) -> str:
        """Ω-SV10: Deterministic hash of all state dimensions."""
        raw = "|".join([
            self.session.value,
            self.regime.value,
            self.velocity.value,
            self.entropy.value,
            self.volatility.value,
            self.flow_imbalance.value,
            self.spread_quality.value,
            self.trend_structure.value,
        ])
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, str]:
        return {
            "timestamp_ns": str(self.timestamp_ns),
            "session": self.session.value,
            "regime": self.regime.value,
            "velocity": self.velocity.value,
            "entropy": self.entropy.value,
            "volatility": self.volatility.value,
            "flow_imbalance": self.flow_imbalance.value,
            "spread_quality": self.spread_quality.value,
            "trend_structure": self.trend_structure.value,
            "profile_hash": self.profile_hash,
        }

    @property
    def dimension_count(self) -> int:
        """Ω-SV11: Number of non-unknown dimensions."""
        dims = [
            self.session.value != "unknown",
            self.regime.value != "unknown",
            self.velocity.value != "frozen",
            self.entropy.value != "chaotic",
            self.volatility.value != "unknown",
            self.flow_imbalance.value != "unknown",
            self.spread_quality.value != "unknown",
            self.trend_structure.value != "unknown",
        ]
        return sum(dims)

    @property
    def quality_score(self) -> float:
        """Ω-SV12: Overall state quality [0, 1] — how reliable is this state?"""
        n_good = self.dimension_count
        return n_good / 8.0


class StateExtractor:
    """Ω-SV13: Extracts state vector from market data snapshot."""

    def __init__(
        self,
        median_spread: float = 10.0,
        atr_reference: float = 50.0,
    ) -> None:
        self._median_spread = median_spread
        self._atr_reference = atr_reference

    def extract(self, snapshot: dict[str, Any]) -> StateVector:
        """Ω-SV14: Full state extraction from snapshot."""
        ts = snapshot.get("timestamp_ns", time.time_ns())
        session = self._classify_session(snapshot.get("hour", 12))
        regime = self._classify_regime(snapshot.get("regime", {}))
        velocity = self._classify_velocity(snapshot.get("tick_velocity", 0.0))
        entropy = self._classify_entropy(snapshot.get("shannon_entropy", 4.0))
        vol = self._classify_volatility(snapshot.get("atr", self._atr_reference))
        flow = self._classify_flow_imbalance(snapshot.get("flow_imbalance_ratio", 0.5))
        spread = self._classify_spread(snapshot.get("spread", self._median_spread))
        trend = self._classify_trend(snapshot.get("trend_structure", {}))

        return StateVector(
            timestamp_ns=ts,
            session=session,
            regime=regime,
            velocity=velocity,
            entropy=entropy,
            volatility=vol,
            flow_imbalance=flow,
            spread_quality=spread,
            trend_structure=trend,
        )

    def _classify_session(self, hour: int) -> SessionType:
        """Ω-SV15: Hour → session via liquidity profile."""
        if 0 <= hour < 7:
            return SessionType.ASIAN
        elif 7 <= hour < 12:
            return SessionType.LONDON
        elif 12 <= hour < 14:
            return SessionType.NY_OPEN
        elif 14 <= hour < 21:
            return SessionType.NY_CLOSE
        else:
            return SessionType.DEAD

    def _classify_regime(self, regime_data: Any) -> RegimeType:
        """Ω-SV16: Regime object → discrete type."""
        if isinstance(regime_data, str):
            val = regime_data.upper()
        elif isinstance(regime_data, dict):
            val = regime_data.get("type", regime_data.get("label", "")).upper()
        else:
            val = str(regime_data).upper()

        if "UP" in val and "TREND" in val:
            return RegimeType.TREND_UP
        if "DOWN" in val and "TREND" in val:
            return RegimeType.TREND_DOWN
        if any(k in val for k in ["IGNITION", "BREAKOUT", "SQUEEZE"]):
            return RegimeType.IGNITION
        if "REVERS" in val:
            return RegimeType.REVERSAL
        if any(k in val for k in ["CHOP", "CHOPPY", "NOISE"]):
            return RegimeType.CHOPPY
        if "RANGE" in val or "SIDEWAYS" in val:
            return RegimeType.RANGE_TIGHT
        if "TREND" in val:
            return RegimeType.TREND_UP if "BULL" in val else RegimeType.TREND_DOWN

        return RegimeType.UNKNOWN

    def _classify_velocity(self, vel: float) -> VelocityBand:
        """Ω-SV17: Tick velocity → discrete band."""
        v = abs(vel)
        if v <= 0:
            return VelocityBand.FROZEN
        if v > 20:
            return VelocityBand.HFT_BURST
        if v > 10:
            return VelocityBand.HIGH
        if v > 3:
            return VelocityBand.MEDIUM
        return VelocityBand.LOW

    def _classify_entropy(self, ent: float) -> EntropyState:
        """Ω-SV18: Shannon entropy → discrete state."""
        if ent > 6.5:
            return EntropyState.CHAOTIC
        if ent > 3.0:
            return EntropyState.COMPLEX
        return EntropyState.ORDERED

    def _classify_volatility(self, atr: float) -> VolatilityState:
        if atr > 150:
            return VolatilityState.EXTREME
        if atr > 80:
            return VolatilityState.HIGH
        if atr > 30:
            return VolatilityState.NORMAL
        if atr > 0:
            return VolatilityState.COMPRESSED
        return VolatilityState.UNKNOWN

    def _classify_flow_imbalance(self, ratio: float) -> FlowImbalance:
        """ratio: 0 = all sell, 1 = all buy."""
        if ratio > 0.70:
            return FlowImbalance.STRONG_BUY
        if ratio > 0.55:
            return FlowImbalance.MODERATE_BUY
        if ratio < 0.30:
            return FlowImbalance.STRONG_SELL
        if ratio < 0.45:
            return FlowImbalance.MODERATE_SELL
        return FlowImbalance.NEUTRAL

    def _classify_spread(self, spread: float) -> SpreadQuality:
        ratio = spread / max(1e-9, self._median_spread)
        if ratio < 0.5:
            return SpreadQuality.TIGHT
        if ratio < 1.5:
            return SpreadQuality.NORMAL
        if ratio < 3.0:
            return SpreadQuality.WIDE
        return SpreadQuality.BLOWN

    def _classify_trend(self, trend_data: Any) -> TrendStructure:
        if isinstance(trend_data, dict):
            structure = trend_data.get("structure", trend_data.get("pattern", "")).upper()
        else:
            structure = str(trend_data).upper()

        if "HH" in structure and "HL" in structure:
            return TrendStructure.UPTREND_HH_HL
        if "LH" in structure and "LL" in structure:
            return TrendStructure.DOWNTREND_LH_LL
        if "EXPAND" in structure or "BREAKOUT" in structure:
            return TrendStructure.EXPANSION
        if "CONTRACT" in structure or "COMPRESS" in structure:
            return TrendStructure.CONTRACTION
        if "RANGE" in structure:
            return TrendStructure.RANGE

        # Default from direction
        if trend_data.get("direction", 0) > 0:
            return TrendStructure.UPTREND_HH_HL
        if trend_data.get("direction", 0) < 0:
            return TrendStructure.DOWNTREND_LH_LL
        return TrendStructure.UNKNOWN


# ──────────────────────────────────────────────────────────────
# Ω-SV19 to Ω-SV36: Topological Hashing & State Similarity
# ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class StateSimilarity:
    """Ω-SV19: Similarity between two state vectors."""

    state_a_hash: str
    state_b_hash: str
    hamming_distance: int
    jaccard_similarity: float
    weighted_similarity: float
    matching_dimensions: list[str]
    differing_dimensions: list[str]
    is_effectively_same: bool  # Similarity above threshold


class StateSimilarityEngine:
    """Ω-SV20: Computes similarity between state vectors."""

    DIMENSION_WEIGHTS: dict[str, float] = {
        "regime": 1.5,
        "volatility": 1.3,
        "entropy": 1.2,
        "flow_imbalance": 1.2,
        "session": 1.0,
        "velocity": 1.0,
        "trend_structure": 0.8,
        "spread_quality": 0.8,
    }

    def __init__(self, similarity_threshold: float = 0.75) -> None:
        self._similarity_threshold = similarity_threshold

    def compute(
        self, state_a: StateVector, state_b: StateVector
    ) -> StateSimilarity:
        """Ω-SV21: Full similarity computation between two states."""
        dimensions = [
            "session",
            "regime",
            "velocity",
            "entropy",
            "volatility",
            "flow_imbalance",
            "spread_quality",
            "trend_structure",
        ]

        matching: list[str] = []
        differing: list[str] = []
        weighted_match = 0.0
        weight_sum = 0.0

        for dim in dimensions:
            val_a = getattr(state_a, dim).value if dim != "trend_structure" else getattr(state_a, dim).value
            val_b = getattr(state_b, dim).value if dim != "trend_structure" else getattr(state_b, dim).value

            w = self.DIMENSION_WEIGHTS.get(dim, 1.0)
            weight_sum += w

            if val_a == val_b:
                matching.append(dim)
                weighted_match += w
            else:
                differing.append(dim)

        hamming = len(differing)
        jaccard = len(matching) / len(dimensions) if dimensions else 0.0
        weighted_sim = weighted_match / weight_sum if weight_sum > 0 else 0.0

        return StateSimilarity(
            state_a_hash=state_a.profile_hash,
            state_b_hash=state_b.profile_hash,
            hamming_distance=hamming,
            jaccard_similarity=round(jaccard, 4),
            weighted_similarity=round(weighted_sim, 4),
            matching_dimensions=matching,
            differing_dimensions=differing,
            is_effectively_same=weighted_sim >= self._similarity_threshold,
        )

    def find_most_similar(
        self, state: StateVector, candidates: list[StateVector], top_k: int = 5
    ) -> list[tuple[StateVector, float]]:
        """Ω-SV22: Find top-k most similar states from candidates."""
        scored: list[tuple[StateVector, float]] = []
        for c in candidates:
            sim = self.compute(state, c)
            scored.append((c, sim.weighted_similarity))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def cluster_states(self, states: list[StateVector], min_similarity: float = 0.6) -> list[list[StateVector]]:
        """Ω-SV23: Cluster states by similarity to reduce fragmentation."""
        if not states:
            return []

        # Simple single-linkage agglomerative clustering
        clusters: list[list[StateVector]] = [[states[0]]]

        for state in states[1:]:
            assigned = False
            for cluster in clusters:
                max_sim = max(
                    self.compute(state, c).weighted_similarity for c in cluster
                )
                if max_sim >= min_similarity:
                    cluster.append(state)
                    assigned = True
                    break
            if not assigned:
                clusters.append([state])

        return clusters


class StateClusterManager:
    """Ω-SV24: Manages state clusters to prevent hyperfragmnentation."""

    def __init__(
        self,
        min_samples_per_state: int = 20,
        max_unique_states: int = 100,
    ) -> None:
        self._min_samples = min_samples_per_state
        self._max_unique = max_unique_states
        self._state_counts: dict[str, int] = {}
        self._cluster_map: dict[str, str] = {}  # state_hash → canonical_hash

    def canonicalize(self, state_hash: str) -> str:
        """Ω-SV25: Map a state hash to its canonical cluster representative."""
        return self._cluster_map.get(state_hash, state_hash)

    def record_observation(self, state_hash: str) -> None:
        self._state_counts[state_hash] = self._state_counts.get(state_hash, 0) + 1

    def merge_underpopulated(
        self, similarity_engine: StateSimilarityEngine, all_states: dict[str, StateVector]
    ) -> int:
        """Ω-SV26: Merge states with < min_samples into similar well-populated states."""
        underpopulated = [
            h for h, c in self._state_counts.items() if c < self._min_samples
        ]

        merged = 0
        for weak_hash in underpopulated:
            if weak_hash not in all_states:
                continue

            weak_state = all_states[weak_hash]
            well_populated = [
                all_states[h]
                for h, c in self._state_counts.items()
                if c >= self._min_samples and h != weak_hash and h in all_states
            ]

            if not well_populated:
                continue

            similar_candidates = similarity_engine.find_most_similar(weak_state, well_populated, top_k=1)
            if similar_candidates and similar_candidates[0][1] >= 0.5:
                target = similar_candidates[0][0]
                self._cluster_map[weak_hash] = target.profile_hash
                self._state_counts[target.profile_hash] += self._state_counts[weak_hash]
                merged += 1

        # Enforce max unique states cap
        if len(self._state_counts) > self._max_unique:
            # Merge the least-populated states first
            sorted_states = sorted(self._state_counts.items(), key=lambda x: x[1])
            for excess_hash, _ in sorted_states[: len(self._state_counts) - self._max_unique]:
                if excess_hash in self._cluster_map:
                    continue
                # Find any cluster it could join
                for target_hash, count in sorted_states:
                    if (
                        target_hash != excess_hash
                        and target_hash in all_states
                        and excess_hash in all_states
                    ):
                        sim = similarity_engine.compute(
                            all_states[excess_hash], all_states[target_hash]
                        )
                        if sim.weighted_similarity >= 0.4:
                            self._cluster_map[excess_hash] = target_hash
                            merged += 1
                            break

        return merged

    def get_stats(self) -> dict[str, Any]:
        total_observed = sum(self._state_counts.values())
        return {
            "unique_states": len(self._state_counts),
            "total_observations": total_observed,
            "merged_count": len(self._cluster_map),
            "avg_samples_per_state": (
                round(total_observed / max(1, len(self._state_counts)), 1)
            ),
        }


# ──────────────────────────────────────────────────────────────
# Ω-SV37 to Ω-SV54: Agent-State Performance Profiling
# ──────────────────────────────────────────────────────────────


@dataclass
class AgentStateProfile:
    """Ω-SV37: Performance profile of one agent in one state cluster."""

    agent_name: str
    state_hash: str
    n_trades: int = 0
    n_wins: int = 0
    total_pnl: float = 0.0
    avg_pnl: float = 0.0
    win_rate: float = 0.5
    avg_win: float = 0.0
    avg_loss: float = 0.0
    sharpe_estimate: float = 0.0
    max_dd_in_state: float = 0.0
    last_trade_ns: int = 0


class AgentStateProfiler:
    """Ω-SV38: Tracks agent performance per state vector."""

    def __init__(self, min_trades_for_reliability: int = 5) -> None:
        self._profiles: dict[tuple[str, str], AgentStateProfile] = {}
        self._min_reliable = min_trades_for_reliability

    def record_trade(
        self,
        agent_name: str,
        state_hash: str,
        pnl: float,
        win: bool,
    ) -> None:
        """Ω-SV39: Record a trade outcome for an agent in a state."""
        key = (agent_name, state_hash)

        if key not in self._profiles:
            self._profiles[key] = AgentStateProfile(
                agent_name=agent_name, state_hash=state_hash
            )

        p = self._profiles[key]
        p.n_trades += 1
        if win:
            p.n_wins += 1
            p.avg_win = ((p.avg_win * (p.n_wins - 1)) + pnl) / p.n_wins
        else:
            losses = p.n_trades - p.n_wins
            p.avg_loss = ((p.avg_loss * (losses - 1)) - pnl) / losses

        p.total_pnl += pnl
        p.avg_pnl = p.total_pnl / p.n_trades
        p.win_rate = p.n_wins / p.n_trades
        p.last_trade_ns = time.time_ns()

        # Simple Sharpe estimate from state-specific PnL
        if p.n_trades >= 2:
            # EMA-ish standard deviation
            std = max(1e-9, abs(p.avg_pnl) + abs(p.total_pnl) / (p.n_trades + 1))
            p.sharpe_estimate = p.avg_pnl / std

    def get_profile(
        self, agent_name: str, state_hash: str
    ) -> AgentStateProfile:
        key = (agent_name, state_hash)
        if key in self._profiles:
            return self._profiles[key]
        return AgentStateProfile(agent_name=agent_name, state_hash=state_hash)

    def get_state_weights(
        self,
        agent_names: list[str],
        state_hash: str,
        default_weight: float = 1.0,
    ) -> dict[str, float]:
        """Ω-SV40: Get agent weights for a specific state.

        Returns dict of {agent_name: weight_multiplier} based on
        historical performance in this state.
        """
        weights: dict[str, float] = {}
        for name in agent_names:
            profile = self.get_profile(name, state_hash)

            if profile.n_trades < self._min_reliable:
                # Not enough data: use prior (default weight with slight decay)
                prior = 0.5 + 0.5 * (profile.n_trades / self._min_reliable)
                weights[name] = round(default_weight * prior, 4)
                continue

            # Base weight from win rate and Sharpe
            wr_score = profile.win_rate
            sharpe_score = max(0, min(1, (profile.sharpe_estimate + 2) / 4))
            pnl_score = max(0, min(1, (1 + math.tanh(profile.avg_pnl / 50))))

            composite = 0.4 * wr_score + 0.3 * sharpe_score + 0.3 * pnl_score

            # Scale to [0.5, 2.0]
            weight = 0.5 + 1.5 * composite

            # Bonus for large sample size
            sample_bonus = min(0.2, (profile.n_trades - self._min_reliable) * 0.01)
            weight += sample_bonus

            weights[name] = round(weight, 4)

        return weights

    def get_specialists(
        self, state_hash: str, top_k: int = 3
    ) -> list[tuple[str, float]]:
        """Ω-SV41: Identify agents that specialize in this state."""
        specialists: list[tuple[str, float]] = []

        for (name, s_hash), profile in self._profiles.items():
            if s_hash != state_hash:
                continue
            if profile.n_trades < self._min_reliable:
                continue

            quality = profile.win_rate * 0.5 + min(1, profile.sharpe_estimate / 2) * 0.5
            specialists.append((name, quality))

        specialists.sort(key=lambda x: x[1], reverse=True)
        return specialists[:top_k]

    def get_generalists(
        self, min_states: int = 10, min_total_trades: int = 50
    ) -> list[tuple[str, float]]:
        """Ω-SV42: Find agents with consistent performance across many states."""
        agent_stats: dict[str, list[tuple[float, int]]] = {}

        for (name, s_hash), profile in self._profiles.items():
            if profile.n_trades < 3:
                continue
            if name not in agent_stats:
                agent_stats[name] = []
            agent_stats[name].append((profile.win_rate, profile.n_trades))

        generalists: list[tuple[str, float]] = []
        for name, stats in agent_stats.items():
            total_trades = sum(n for _, n in stats)
            n_states = len(stats)

            if n_states < min_states or total_trades < min_total_trades:
                continue

            # Average WR across states, weighted by trade count
            avg_wr = sum(wr * n for wr, n in stats) / total_trades
            consistency = 1.0 - max(0, 0.5 - min(0.5, avg_wr - 0.5))
            generalists.append((name, round(consistency, 4)))

        generalists.sort(key=lambda x: x[1], reverse=True)
        return generalists

    def forget_state(
        self, agent_name: str, state_hash: str, max_age_ns: int = 30 * 24 * 3600 * 1_000_000_000
    ) -> bool:
        """Ω-SV43: Remove stale state profile (default 30 days)."""
        key = (agent_name, state_hash)
        if key in self._profiles:
            if time.time_ns() - self._profiles[key].last_trade_ns > max_age_ns:
                del self._profiles[key]
                return True
        return False

    def get_stats(self) -> dict[str, Any]:
        if not self._profiles:
            return {"total_profiles": 0}

        agents = set(k[0] for k in self._profiles.keys())
        states = set(k[1] for k in self._profiles.keys())
        total_trades = sum(p.n_trades for p in self._profiles.values())

        return {
            "total_profiles": len(self._profiles),
            "unique_agents": len(agents),
            "unique_states": len(states),
            "total_trades_recorded": total_trades,
        }


class StateVectorEngine:
    """Ω-SV44: Master engine combining extraction, similarity, and profiling."""

    def __init__(
        self,
        median_spread: float = 10.0,
        atr_reference: float = 50.0,
        min_samples_per_state: int = 20,
        max_unique_states: int = 100,
    ) -> None:
        self.extractor = StateExtractor(median_spread, atr_reference)
        self.similarity = StateSimilarityEngine()
        self.clusters = StateClusterManager(min_samples_per_state, max_unique_states)
        self.profiler = AgentStateProfiler()
        self._state_cache: dict[str, StateVector] = {}

    def compute_state(self, snapshot: dict[str, Any]) -> StateVector:
        """Ω-SV45: Extract, canonicalize, and track state."""
        state = self.extractor.extract(snapshot)
        self._state_cache[state.profile_hash] = state
        self.clusters.record_observation(state.profile_hash)
        return state

    def get_canonical_hash(self, state_hash: str) -> str:
        """Ω-SV46: Get the canonical cluster hash for a state."""
        return self.clusters.canonicalize(state_hash)

    def agent_weights_for_state(
        self, agent_names: list[str], state_hash: str
    ) -> dict[str, float]:
        """Ω-SV47: Get state-aware agent weights."""
        canonical = self.get_canonical_hash(state_hash)
        return self.profiler.get_state_weights(agent_names, canonical)

    def record_agent_outcome(
        self,
        agent_name: str,
        state_hash: str,
        pnl: float,
        win: bool,
    ) -> None:
        """Ω-SV48: Record a trade outcome with state context."""
        canonical = self.get_canonical_hash(state_hash)
        self.profiler.record_trade(agent_name, canonical, pnl, win)

    def maintenance(self) -> dict[str, Any]:
        """Ω-SV49: Run maintenance — merge underpopulated states."""
        stats_before = self.clusters.get_stats()
        n_merged = self.clusters.merge_underpopulated(self.similarity, self._state_cache)
        stats_after = self.clusters.get_stats()

        # Clean up stale profiles
        n_cleaned = 0
        keys_to_check = list(self.profiler._profiles.keys())
        for key in keys_to_check:
            agent_name, state_hash = key
            self.profiler.forget_state(agent_name, state_hash)

        return {
            "states_before": stats_before["unique_states"],
            "states_after": stats_after["unique_states"],
            "merged": n_merged,
        }

    def get_full_stats(self) -> dict[str, Any]:
        """Ω-SV50: Comprehensive statistics."""
        return {
            "state_engine": self.clusters.get_stats(),
            "profiler": self.profiler.get_stats(),
            "cached_states": len(self._state_cache),
        }
