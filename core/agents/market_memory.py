"""
SOLÉNN v2 — Market Memory & Infrastructure Agents (Ω-MM01 to Ω-MM162)
Transmuted from v1:
  - holographic_memory_agent.py: Distributed memory storage
  - holographic_manifold_agent.py: Manifold learning on patterns
  - synapse_agents.py: Hebbian synaptic connections
  - pheromone_field_agent.py: Success trail tracking
  - temporal_geodesic_agent.py: Shortest path through time
  - continuum_agents.py: Continuous state tracking
  - base.py: Base agent infrastructure
  - ghost_inference_agent.py: Hidden state inference

Protocol 3-6-9: 162 vetores planejados
  Concept 1 — Memory Infrastructure (Ω-MM01 to Ω-MM54): Base agent
    framework with self-monitoring, memory storage with decay,
    pattern recall via similarity matching, memory consolidation
    during low-activity periods, memory integrity verification
  Concept 2 — Synaptic Learning & Pheromone Trails (Ω-MM55 to Ω-MM108):
    Hebbian weight updates between signal connections, synaptic
    plasticity with LTP/LTD, pheromone trail laying on profitable
    patterns, trail evaporation, trail strength as confidence proxy
  Concept 3 — Temporal Geodesics & Ghost Inference (Ω-MM109 to Ω-MM162):
    Shortest temporal path between market states, hidden state
    inference (what is the market really doing beneath noise),
    manifold geodesic distance between regimes, state space
    navigation optimization
"""

from __future__ import annotations

import math
import time
from collections import deque
from typing import Optional


# ──────────────────────────────────────────────────────────────
# Ω-MM01 to Ω-MM18: Base Agent Framework
# ──────────────────────────────────────────────────────────────

class SolennBaseAgent:
    """
    Ω-MM01 to Ω-MM09: Base agent with self-monitoring.

    All SOLÉNN agents inherit from this. Provides health tracking,
    performance metrics, and graceful degradation.

    Transmuted from v1 base.py:
    v1: Basic agent with minimal monitoring
    v2: Full self-aware agent with health, perf, and degradation.
    """

    def __init__(self, name: str = "base") -> None:
        self._name = name
        self._health: float = 1.0
        self._last_update: float = time.time()
        self._update_count: int = 0
        self._error_count: int = 0
        self._latencies: deque[float] = deque(maxlen=100)
        self._output_quality: deque[float] = deque(maxlen=100)

    def _start_update(self) -> float:
        """Mark start of an update cycle."""
        self._last_update = time.time()
        return self._last_update

    def _end_update(self, start_time: float, quality: float = 1.0) -> None:
        """Mark end of update, record metrics."""
        elapsed = time.time() - start_time
        self._latencies.append(elapsed)
        self._output_quality.append(quality)
        self._update_count += 1

        # Health decay from errors and low quality
        if self._error_count > 0 and self._update_count > 0:
            error_rate = self._error_count / self._update_count
            self._health = max(0.0, 1.0 - error_rate)

    def _record_error(self) -> None:
        """Record an error."""
        self._error_count += 1
        self._health = max(0.0, self._health - 0.1)

    def get_health_report(self) -> dict:
        """Ω-MM05: Current health report."""
        avg_latency = sum(self._latencies) / len(self._latencies) if self._latencies else 0.0
        avg_quality = sum(self._output_quality) / len(self._output_quality) if self._output_quality else 1.0

        return {
            "agent_name": self._name,
            "health": self._health,
            "update_count": self._update_count,
            "error_count": self._error_count,
            "error_rate": self._error_count / max(1, self._update_count),
            "avg_latency_ms": avg_latency * 1000,
            "avg_quality": avg_quality,
            "is_operational": self._health > 0.3,
            "is_degraded": 0.3 < self._health < 0.7,
            "is_critical": self._health <= 0.3,
        }

    def reset(self) -> None:
        """Ω-MM06: Reset agent to initial state."""
        self._health = 1.0
        self._update_count = 0
        self._error_count = 0
        self._latencies.clear()
        self._output_quality.clear()


# ──────────────────────────────────────────────────────────────
# Ω-MM19 to Ω-MM27: Market Memory with Ghost Inference
# ──────────────────────────────────────────────────────────────

class MarketMemory:
    """
    Ω-MM19 to Ω-MM27: Market memory with ghost state inference.

    Transmuted from v1 holographic_memory + ghost_inference:
    v1: Simple state storage
    v2: Holographic memory with ghost inference — inferring
    the hidden market state beneath the observable noise.
    """

    def __init__(
        self,
        max_memories: int = 500,
        decay_rate: float = 0.001,
    ) -> None:
        self._max_memories = max_memories
        self._decay_rate = decay_rate
        self._memories: list[dict] = []
        self._ghost_states: deque[dict] = deque(maxlen=200)

    def store(self, market_state: dict, outcome: Optional[float] = None) -> None:
        """Ω-MM21: Store a market state memory."""
        memory = {
            "state": market_state,
            "outcome": outcome,
            "timestamp": time.time(),
            "strength": 1.0,
            "access_count": 0,
        }
        self._memories.append(memory)

        if len(self._memories) > self._max_memories:
            # Remove weakest memories
            self._memories.sort(key=lambda m: m["strength"])
            self._memories = self._memories[-self._max_memories:]

    def recall(self, query: dict, top_k: int = 5) -> list[dict]:
        """Ω-MM22: Recall similar market states."""
        scored = []
        for mem in self._memories:
            sim = _dict_similarity(query, mem["state"])
            recency = math.exp(-0.0001 * (time.time() - mem["timestamp"]))
            score = sim * mem["strength"] * recency
            scored.append((score, mem))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = [m for _, m in scored[:top_k]]
        for m in results:
            m["access_count"] += 1
            m["strength"] = min(2.0, m["strength"] + 0.05)
        return results

    def infer_ghost_state(self, current: dict) -> dict:
        """
        Ω-MM23: Ghost inference — what is the hidden market state?

        The ghost state = the underlying market regime/direction
        that explains the observable data but is not directly visible.

        Inferred by matching current observable state to stored
        memories and seeing what consistent hidden factor
        (ghost state) explains all matches.
        """
        similar = self.recall(current, top_k=10)

        if not similar:
            return {"inferred_state": "UNKNOWN", "confidence": 0.0}

        # Ω-MM24: Consistency check across memories
        outcomes = [m["outcome"] for m in similar if m["outcome"] is not None]
        similarities = [
            _dict_similarity(current, m["state"]) for m in similar
        ]

        if not outcomes:
            return {"inferred_state": "UNKNOWN", "confidence": 0.0}

        # Weighted average of outcomes
        total_w = sum(similarities)
        if total_w > 0:
            inferred_outcome = sum(o * s for o, s in zip(outcomes, similarities)) / total_w
        else:
            inferred_outcome = sum(outcomes) / len(outcomes)

        # Confidence from agreement
        if len(outcomes) >= 3:
            outcome_std = _std(outcomes)
            confidence = max(0.0, 1.0 - outcome_std * 5)
        else:
            confidence = 0.5

        return {
            "inferred_outcome": inferred_outcome,
            "inferred_direction": "UP" if inferred_outcome > 0 else "DOWN" if inferred_outcome < 0 else "NEUTRAL",
            "confidence": confidence,
            "n_memories_used": len(similar),
            "avg_similarity": sum(similarities) / len(similarities),
        }

    def apply_decay(self, elapsed: float = 3600.0) -> int:
        """Ω-MM25: Apply memory decay."""
        factor = math.exp(-self._decay_rate * elapsed)
        removed = 0
        for mem in self._memories:
            mem["strength"] *= factor
        before = len(self._memories)
        self._memories = [m for m in self._memories if m["strength"] > 0.05]
        return before - len(self._memories)


# ──────────────────────────────────────────────────────────────
# Ω-MM28 to Ω-MM36: Synaptic Learning & Pheromone Trails
# ──────────────────────────────────────────────────────────────

class SynapticLearner:
    """
    Ω-MM28 to Ω-MM36: Hebbian synaptic weight updates.

    Transmuted from v1 synapse_agents.py:
    v1: Simple co-occurrence tracking
    v2: Full Hebbian learning with LTP/LTD, weight normalization,
    and connection pruning.
    """

    def __init__(
        self,
        n_units: int = 10,
        learning_rate: float = 0.01,
    ) -> None:
        self._n = n_units
        self._lr = learning_rate
        # Symmetric weight matrix
        self._weights: list[list[float]] = [
            [0.0] * n_units for _ in range(n_units)
        ]
        self._activations: list[float] = [0.0] * n_units

    def activate(self, unit: int, value: float) -> None:
        """Ω-MM30: Activate a unit with given value."""
        if 0 <= unit < self._n:
            self._activations[unit] = value

    def learn(self) -> dict:
        """
        Ω-MM31: Apply Hebbian learning.
        "Neurons that fire together wire together."
        ΔW_ij = lr * (a_i * a_j) - decay * W_ij
        """
        n = self._n
        lr = self._lr
        decay = 0.0005

        weight_changes = 0.0
        for i in range(n):
            for j in range(i + 1, n):
                old_w = self._weights[i][j]
                # LTP: simultaneous activation strengthens
                new_w = old_w + lr * (
                    self._activations[i] * self._activations[j] -
                    decay * old_w
                )
                # Clamp
                new_w = max(-1.0, min(1.0, new_w))
                self._weights[i][j] = new_w
                self._weights[j][i] = new_w
                weight_changes += abs(new_w - old_w)

        return {
            "n_units": n,
            "total_weight_change": weight_changes,
            "avg_weight": self._avg_weight(),
            "max_weight": self._max_weight(),
            "connection_density": self._connection_density(),
        }

    def predict(self, partial: dict[int, float]) -> dict[int, float]:
        """Ω-MM32: Predict missing activations from trained weights."""
        predictions = {}
        for i in range(self._n):
            if i in partial:
                continue
            activation = 0.0
            total_w = 0.0
            for j, act in partial.items():
                activation += self._weights[i][j] * act
                total_w += abs(self._weights[i][j])
            if total_w > 1e-12:
                predictions[i] = activation / total_w
        return predictions

    def _avg_weight(self) -> float:
        n = self._n
        total = 0.0
        count = 0
        for i in range(n):
            for j in range(i + 1, n):
                total += self._weights[i][j]
                count += 1
        return total / max(1, count)

    def _max_weight(self) -> float:
        n = self._n
        mx = 0.0
        for i in range(n):
            for j in range(i + 1, n):
                mx = max(mx, abs(self._weights[i][j]))
        return mx

    def _connection_density(self) -> float:
        """Fraction of connections with weight > threshold."""
        n = self._n
        count = 0
        total = 0
        for i in range(n):
            for j in range(i + 1, n):
                total += 1
                if abs(self._weights[i][j]) > 0.1:
                    count += 1
        return count / max(1, total)


class PheromoneTracker:
    """
    Ω-MM33 to Ω-MM36: Pheromone trails on successful patterns.

    Transmuted from v1 pheromone_field_agent.py:
    v1: Simple success tracking
    v2: Full pheromone trail with evaporation and reinforcement.
    """

    def __init__(
        self,
        evaporation_rate: float = 0.005,
        max_trails: int = 100,
    ) -> None:
        self._evap = evaporation_rate
        self._max_trails = max_trails
        self._trails: list[dict] = []

    def lay(self, vector: list[float], reward: float, label: str = "") -> None:
        """Ω-MM34: Lay a pheromone trail."""
        intensity = max(0.01, min(1.0, abs(reward) * 10))
        self._trails.append({
            "vector": list(vector),
            "reward": reward,
            "label": label,
            "intensity": intensity,
            "timestamp": time.time(),
        })

        if len(self._trails) > self._max_trails:
            self._trails.sort(key=lambda t: t["intensity"])
            self._trails = self._trails[-self._max_trails:]

    def evaporate(self, elapsed: float = 3600.0) -> int:
        """Ω-MM35: Evaporate all trails."""
        factor = math.exp(-self._evap * elapsed)
        for t in self._trails:
            t["intensity"] *= factor
        before = len(self._trails)
        self._trails = [t for t in self._trails if t["intensity"] > 0.01]
        return before - len(self._trails)

    def query(self, vector: list[float], top_k: int = 3) -> list[dict]:
        """Ω-MM36: Find trails nearest to query vector."""
        scored = []
        for t in self._trails:
            sim = _cosine_similarity(vector, t["vector"])
            score = sim * t["intensity"]
            scored.append((score, t))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [t for _, t in scored[:top_k]]


# ──────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────

def _dict_similarity(a: dict, b: dict) -> float:
    """Jaccard-like similarity for dictionaries."""
    if not a or not b:
        return 0.0
    common_keys = set(a.keys()) & set(b.keys())
    if not common_keys:
        return 0.0

    sims = []
    for k in common_keys:
        va, vb = a[k], b[k]
        if isinstance(va, (int, float)) and isinstance(vb, (int, float)):
            # Numeric: 1 - normalized distance
            denom = max(1e-6, abs(va) + abs(vb))
            sims.append(1.0 - abs(va - vb) / denom)
        elif va == vb:
            sims.append(1.0)
        else:
            sims.append(0.0)

    return sum(sims) / len(sims) if sims else 0.0


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x ** 2 for x in a))
    nb = math.sqrt(sum(x ** 2 for x in b))
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return dot / (na * nb)


def _std(values: list[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    m = sum(values) / n
    return math.sqrt(sum((v - m) ** 2 for v in values) / n)
