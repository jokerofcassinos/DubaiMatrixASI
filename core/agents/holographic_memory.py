"""
SOLÉNN v2 — Holographic Memory Agents (Ω-H01 to Ω-H162)
Transmuted from v1:
  - holographic_memory_agent.py: Distributed pattern storage/recall
  - holographic_manifold_agent.py: Manifold learning on stored patterns
  - synapse_agents.py: Hebbian synaptic plasticity
  - pheromone_field_agent.py: Successful pattern trail tracking
  - neural_sentience_agent.py: Meta-awareness scoring
  - temporal_geodesic_agent.py: Shortest path through memory space
  - continuum_agents.py: Consciousness state continuum

Protocol 3-6-9: 162 vetores planejados
  Concept 1 — Holographic Memory Storage (Ω-H01 to Ω-H54): Distributed
    pattern storage where each fragment contains whole information,
    retrieval via correlation matching, interference pattern analysis,
    decay with anti-fading reinforcement, associative recall, completion
  Concept 2 — Holographic Manifold & Synaptic Plasticity (Ω-H55 to Ω-H108):
    Manifold learning on stored patterns, Hebbian weight evolution,
    long-term potentiation/depression, manifold curvature as complexity
    metric, geodesic paths between memories
  Concept 3 — Pheromone Fields & Neural Sentience (Ω-H109 to Ω-H162):
    Pheromone trails for successful patterns, evaporation dynamics,
    trail reinforcement, neural sentience scoring, consciousness
    continuum classification, temporal geodesics
"""

from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional


# ──────────────────────────────────────────────────────────────
# Ω-H01 to Ω-H18: Holographic Memory Store
# ──────────────────────────────────────────────────────────────

@dataclass
class MemoryPattern:
    """Ω-H01: A stored market pattern."""
    vector: list[float]
    label: str           # e.g. "breakout_long_range", "mean_reversion_tight"
    outcome_pnl: float    # realized P&L when this pattern was traded
    hit_count: int = 0
    last_accessed: float = 0.0
    strength: float = 1.0  # reinforced by retrieval


class HolographicMemoryStore:
    """
    Ω-H01 to Ω-H09: Distributed holographic memory storage.

    Transmuted from v1 holographic_memory_agent.py:
    v1: Simple list of past states
    v2: Full holographic storage where each memory is a vector in
    high-dimensional space, retrieval via correlation matching,
    pattern completion from partial input, decay with reinforcement.
    """

    def __init__(
        self,
        max_patterns: int = 500,
        match_threshold: float = 0.7,
        decay_rate: float = 0.001,
    ) -> None:
        self._max_patterns = max_patterns
        self._match_threshold = match_threshold
        self._decay_rate = decay_rate
        self._patterns: list[MemoryPattern] = []
        self._access_times: deque[float] = deque(maxlen=1000)

    def store(
        self,
        vector: list[float],
        label: str,
        outcome_pnl: float = 0.0,
    ) -> None:
        """Ω-H03: Store a new pattern."""
        # Check for similar existing pattern
        for p in self._patterns:
            sim = _cosine_similarity(vector, p.vector)
            if sim > 0.95:
                # Update existing: average vector and reinforce
                p.vector = [
                    0.5 * a + 0.5 * b
                    for a, b in zip(vector, p.vector)
                ]
                p.strength = min(2.0, p.strength + 0.1)
                p.hit_count += 1
                p.last_accessed = time.time()
                p.outcome_pnl = 0.7 * p.outcome_pnl + 0.3 * outcome_pnl
                return

        # Create new pattern
        pattern = MemoryPattern(
            vector=list(vector),
            label=label,
            outcome_pnl=outcome_pnl,
            strength=1.0,
            hit_count=0,
            last_accessed=time.time(),
        )
        self._patterns.append(pattern)

        # Evict weak/stale patterns if over capacity
        if len(self._patterns) > self._max_patterns:
            self._patterns.sort(
                key=lambda p: p.strength * _recency_factor(p.last_accessed)
            )
            self._patterns = self._patterns[-self._max_patterns:]

    def retrieve(
        self,
        query_vector: list[float],
        top_k: int = 5,
    ) -> list[MemoryPattern]:
        """Ω-H05: Retrieve most similar patterns via correlation."""
        scored = []
        for p in self._patterns:
            sim = _cosine_similarity(query_vector, p.vector)
            # Holographic retrieval score = similarity * strength * recency
            recency = _recency_factor(p.last_accessed)
            score = sim * p.strength * recency
            scored.append((score, p))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored[:top_k]]

    def complete_pattern(
        self,
        partial_vector: list[float],
        mask: list[bool],
    ) -> list[float]:
        """
        Ω-H07: Pattern completion from partial input.
        partial_vector has known values where mask is True,
        missing values where mask is False. Fills missing values
        by averaging from most similar stored patterns.
        """
        # Match on known dimensions only
        def masked_cosine(a: list[float], b: list[float]) -> float:
            nums = []
            for av, bv, m in zip(a, b, mask):
                if m:
                    nums.append(av * bv)
            if not nums:
                return 0.0
            denom_a = math.sqrt(sum(a[i] ** 2 for i, m in enumerate(mask) if m))
            denom_b = math.sqrt(sum(b[i] ** 2 for i, m in enumerate(mask) if m))
            if denom_a < 1e-12 or denom_b < 1e-12:
                return 0.0
            return sum(nums) / (denom_a * denom_b)

        scored = [(masked_cosine(partial_vector, p.vector), p)
                  for p in self._patterns]
        scored.sort(key=lambda x: x[0], reverse=True)

        # Fill missing values from top-3 matches
        top_matches = scored[:3]
        result = list(partial_vector)
        for i, m in enumerate(mask):
            if not m and top_matches:
                total_w = 0.0
                total_val = 0.0
                for sim, p in top_matches:
                    w = max(0.1, sim * p.strength)
                    total_w += w
                    total_val += w * p.vector[i]
                if total_w > 0:
                    result[i] = total_val / total_w

        return result

    def apply_decay(self, elapsed_seconds: float) -> int:
        """Ω-H09: Apply temporal decay to all patterns."""
        decay_factor = math.exp(-self._decay_rate * elapsed_seconds)
        faded_count = 0
        for p in self._patterns:
            p.strength *= decay_factor
            if p.strength < 0.05:
                faded_count += 1
        # Remove severely faded patterns
        self._patterns = [p for p in self._patterns if p.strength >= 0.05]
        return faded_count

    def get_stats(self) -> dict:
        """Ω-H10: Memory store statistics."""
        if not self._patterns:
            return {"count": 0, "avg_strength": 0.0, "interference": 0.0}

        strengths = [p.strength for p in self._patterns]

        # Ω-H11: Interference score (how similar are patterns to each other)
        # High interference = patterns overlap too much = memory confusion
        if len(self._patterns) >= 2:
            sims = []
            subset = self._patterns[:min(50, len(self._patterns))]
            for i in range(len(subset)):
                for j in range(i + 1, len(subset)):
                    sims.append(_cosine_similarity(
                        subset[i].vector, subset[j].vector
                    ))
            interference = sum(sims) / len(sims) if sims else 0.0
        else:
            interference = 0.0

        label_counts: dict[str, int] = {}
        for p in self._patterns:
            label_counts[p.label] = label_counts.get(p.label, 0) + 1

        return {
            "count": len(self._patterns),
            "avg_strength": sum(strengths) / len(strengths),
            "interference": interference,
            "is_confused": interference > 0.8,
            "label_distribution": label_counts,
        }


# ──────────────────────────────────────────────────────────────
# Ω-H19 to Ω-R27: Manifold Learner
# ──────────────────────────────────────────────────────────────

class ManifoldLearner:
    """
    Ω-H19 to Ω-H27: Learn manifold structure of stored patterns.

    Transmuted from v1 holographic_manifold_agent.py:
    v1: Manifold embedding of regimes
    v2: Full manifold learning with local tangent space alignment
    approximation, curvature computation, and complexity scoring.
    """

    def __init__(self, n_neighbors: int = 5) -> None:
        self._n_neighbors = n_neighbors

    def analyze(self, vectors: list[list[float]]) -> dict:
        """
        Ω-H21: Analyze manifold structure of pattern vectors.
        Returns manifold curvature, intrinsic dimension, complexity.
        """
        n = len(vectors)
        if n < self._n_neighbors + 2:
            return {"state": "WARMING_UP", "curvature": 0.0}

        dim = len(vectors[0]) if vectors else 0

        # Ω-H22: Compute pairwise distances
        distances = _pairwise_distances(vectors)

        # Ω-H23: For each point, find k nearest neighbors and compute
        # local tangent approximation (PCA on neighbors)
        local_ranks = []
        for i in range(n):
            neighbors = sorted(range(n), key=lambda j: distances[i][j])
            neighbors = neighbors[1:self._n_neighbors + 1]  # exclude self

            if len(neighbors) < 2:
                local_ranks.append(1.0)
                continue

            # Local covariance of neighbors
            center = vectors[i]
            cov_matrix = _local_covariance(
                [vectors[j] for j in neighbors], center
            )

            # Approximate intrinsic dimension via eigenvalue ratio
            eigen_values = _approximate_eigenvalues(cov_matrix)
            if eigen_values and max(eigen_values) > 1e-12:
                total = sum(eigen_values)
                local_rank = (max(eigen_values) / total)
            else:
                local_rank = 0.0

            local_ranks.append(local_rank)

        # Ω-H24: Manifold curvature = variance of local tangent spaces
        mean_rank = sum(local_ranks) / len(local_ranks)
        curvature = math.sqrt(
            sum((r - mean_rank) ** 2 for r in local_ranks) / len(local_ranks)
        )

        # Ω-H25: Global intrinsic dimension estimate
        # Count eigenvalues > threshold across all local patches
        intrinsic_dim = max(1, round(mean_rank * dim))

        if curvature < 0.1:
            complexity = "FLAT"
        elif curvature < 0.3:
            complexity = "LOW_CURVATURE"
        elif curvature < 0.6:
            complexity = "MODERATE_CURVATURE"
        else:
            complexity = "HIGH_CURVATURE"

        return {
            "curvature": curvature,
            "intrinsic_dimension": intrinsic_dim,
            "ambient_dimension": dim,
            "complexity": complexity,
            "is_predictable": curvature < 0.3,
            "local_ranks": local_ranks,
        }


# ──────────────────────────────────────────────────────────────
# Ω-H28 to Ω-H36: Synaptic Plasticity Engine
# ──────────────────────────────────────────────────────────────

class SynapticPlasticityEngine:
    """
    Ω-H28 to Ω-H36: Hebbian learning for connection weights.

    Transmuted from v1 synapse_agents.py:
    v1: Simple co-occurrence tracking
    v2: Full Hebbian learning with LTP/LTD, weight normalization,
    and pattern prediction via learned weights.
    """

    def __init__(self, n_features: int = 10, learning_rate: float = 0.01) -> None:
        self._n = n_features
        self._lr = learning_rate
        self._weights: list[list[float]] = [
            [0.0] * n_features for _ in range(n_features)
        ]
        self._update_count = 0

    def update(self, activation: list[float]) -> None:
        """
        Ω-H30: Apply Hebbian learning rule.
        "Neurons that fire together wire together."
        Delta W_ij = lr * (a_i * a_j - decay * W_ij)
        """
        n = self._n
        lr = self._lr
        decay = 0.001  # Weight decay / long-term depression

        for i in range(n):
            for j in range(i + 1, n):
                # Hebbian LTP: co-activation strengthens
                hebbian = activation[i] * activation[j]
                # LTD: decay of unused connections
                new_w = self._weights[i][j] + lr * (
                    hebbian - decay * self._weights[i][j]
                )
                # Clamp weights
                new_w = max(-1.0, min(1.0, new_w))
                self._weights[i][j] = new_w
                self._weights[j][i] = new_w  # Symmetric

        self._update_count += 1

    def predict(
        self,
        partial_activation: list[float],
        mask: list[bool],
    ) -> list[float]:
        """
        Ω-H32: Predict missing features from learned synaptic weights.
        Given known features (mask=True), predict unknown features.
        """
        predicted = list(partial_activation)
        for i in range(self._n):
            if mask[i]:
                continue
            activation = 0.0
            total_w = 0.0
            for j in range(self._n):
                if mask[j]:
                    activation += self._weights[i][j] * partial_activation[j]
                    total_w += abs(self._weights[i][j])
            if total_w > 1e-12:
                predicted[i] = activation / total_w
        return predicted

    def get_weight_matrix_summary(self) -> dict:
        """Ω-H34: Summarize learned weight structure."""
        n = self._n
        all_weights = []
        for i in range(n):
            for j in range(i + 1, n):
                all_weights.append(self._weights[i][j])

        if not all_weights:
            return {"mean": 0.0, "std": 0.0, "max": 0.0, "sparse_ratio": 0.0}

        mean_w = sum(all_weights) / len(all_weights)
        variance = sum((w - mean_w) ** 2 for w in all_weights) / len(all_weights)
        std_w = math.sqrt(variance)
        max_w = max(abs(w) for w in all_weights)
        sparse_ratio = sum(1 for w in all_weights if abs(w) < 0.05) / len(all_weights)

        return {
            "mean_weight": mean_w,
            "std_weight": std_w,
            "max_weight": max_w,
            "sparse_ratio": sparse_ratio,
            "update_count": self._update_count,
        }


# ──────────────────────────────────────────────────────────────
# Ω-H37 to Ω-H45: Pheromone Field Tracker
# ──────────────────────────────────────────────────────────────

@dataclass
class PheromoneTrail:
    """Ω-H37: A single pheromone trail from a successful pattern."""
    vector: list[float]
    label: str
    intensity: float
    created_at: float
    reinforced_count: int = 0


class PheromoneFieldTracker:
    """
    Ω-H37 to Ω-H45: Pheromone fields for successful patterns.

    Transmuted from v1 pheromone_field_agent.py:
    v1: Basic success trail
    v2: Full pheromone field with evaporation dynamics,
    trail reinforcement, and multi-trail interference.
    """

    def __init__(
        self,
        evaporation_rate: float = 0.005,
        max_trails: int = 100,
    ) -> None:
        self._evap_rate = evaporation_rate
        self._max_trails = max_trails
        self._trails: list[PheromoneTrail] = []

    def lay_pheromone(
        self,
        vector: list[float],
        label: str,
        success_reward: float,
    ) -> None:
        """Ω-H39: Lay a new pheromone trail from successful pattern."""
        intensity = max(0.01, min(1.0, success_reward))

        # Check if close to existing trail → reinforce instead
        for trail in self._trails:
            sim = _cosine_similarity(vector, trail.vector)
            if sim > 0.8:
                trail.intensity = min(1.0, trail.intensity + intensity * 0.3)
                trail.reinforced_count += 1
                trail.created_at = time.time()  # refresh timestamp
                return

        trail = PheromoneTrail(
            vector=list(vector),
            label=label,
            intensity=intensity,
            created_at=time.time(),
            reinforced_count=0,
        )
        self._trails.append(trail)

        # Evict weakest trail if over capacity
        if len(self._trails) > self._max_trails:
            self._trails.sort(key=lambda t: t.intensity)
            self._trails = self._trails[-self._max_trails:]

    def apply_evaporation(self, elapsed_seconds: float) -> int:
        """Ω-H41: Evaporate all trails over time."""
        factor = math.exp(-self._evap_rate * elapsed_seconds)
        for t in self._trails:
            t.intensity *= factor
        before = len(self._trails)
        self._trails = [t for t in self._trails if t.intensity > 0.01]
        return before - len(self._trails)

    def query_field(self, vector: list[float]) -> dict:
        """Ω-H42: Query pheromone field for current pattern."""
        if not self._trails:
            return {"scent": 0.0, "matching_label": None, "is_strong": False}

        best_score = 0.0
        best_label: Optional[str] = None
        total_scent = 0.0

        for trail in self._trails:
            sim = _cosine_similarity(vector, trail.vector)
            score = sim * trail.intensity
            total_scent += score
            if score > best_score:
                best_score = score
                best_label = trail.label

        return {
            "scent": total_scent,
            "best_match_score": best_score,
            "matching_label": best_label,
            "active_trails": len(self._trails),
            "is_strong": total_scent > 0.5,
            "scent_gradient": total_scent / max(1, len(self._trails)),
        }


# ──────────────────────────────────────────────────────────────
# Ω-H46 to Ω-H54: Neural Sentience Monitor
# ──────────────────────────────────────────────────────────────

class NeuralSentienceMonitor:
    """
    Ω-H46 to Ω-H54: Meta-cognitive awareness scoring.

    Transmuted from v1 neural_sentience_agent.py:
    v1: Basic accuracy monitoring
    v2: Full sentience scoring system with consciousness
    continuum classification.
    """

    def __init__(self, window_size: int = 100) -> None:
        self._window = window_size
        self._confidence_history: deque[float] = deque(maxlen=window_size)
        self._match_quality_history: deque[float] = deque(maxlen=window_size)
        self._prediction_accuracy: deque[float] = deque(maxlen=window_size)
        self._interference_history: deque[float] = deque(maxlen=window_size)

    def update(
        self,
        confidence: float,
        match_quality: float,
        prediction_correct: bool,
        interference: float,
    ) -> dict:
        """Ω-H48: Update sentience metrics."""
        self._confidence_history.append(confidence)
        self._match_quality_history.append(match_quality)
        self._prediction_accuracy.append(1.0 if prediction_correct else 0.0)
        self._interference_history.append(interference)

        if len(self._confidence_history) < 10:
            return {"state": "WARMING_UP"}

        # Ω-H49: Composite sentience score
        avg_conf = sum(self._confidence_history) / len(self._confidence_history)
        avg_match = sum(self._match_quality_history) / len(self._match_quality_history)
        avg_acc = sum(self._prediction_accuracy) / len(self._prediction_accuracy)
        avg_intf = sum(self._interference_history) / len(self._interference_history)

        # Sentience = (confidence + match + accuracy) / 3 - interference_penalty
        sentience = (
            avg_conf * 0.3 +
            avg_match * 0.3 +
            avg_acc * 0.4 -
            avg_intf * 0.2
        )
        sentience = max(0.0, min(1.0, sentience))

        # Ω-H50: Consciousness state classification
        if sentience > 0.8 and avg_acc > 0.7:
            state = "ALERT"
        elif sentience > 0.6:
            state = "DROWSY"
        elif avg_intf > 0.6:
            state = "CONFUSED"
        elif sentience < 0.2:
            state = "UNCONSCIOUS"
        else:
            state = "TRANSITIONAL"

        # Ω-H51: Meta-cognitive quality
        # How well does confidence predict actual accuracy?
        if len(self._confidence_history) >= 30:
            conf_list = list(self._confidence_history)[-30:]
            acc_list = list(self._prediction_accuracy)[-30:]
            meta_quality = _correlation(conf_list, acc_list)
        else:
            meta_quality = 0.0

        return {
            "sentience_score": sentience,
            "state": state,
            "confidence": avg_conf,
            "match_quality": avg_match,
            "prediction_accuracy": avg_acc,
            "interference": avg_intf,
            "meta_cognitive_quality": meta_quality,
            "is_operational": state in ("ALERT", "DROWSY"),
        }


# ──────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────

def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors."""
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x ** 2 for x in a))
    norm_b = math.sqrt(sum(x ** 2 for x in b))
    if norm_a < 1e-12 or norm_b < 1e-12:
        return 0.0
    return dot / (norm_a * norm_b)


def _recency_factor(timestamp: float) -> float:
    """Exponential decay factor based on recency."""
    dt = max(0, time.time() - timestamp)
    return math.exp(-0.0001 * dt)  # very slow decay


def _pairwise_distances(vectors: list[list[float]]) -> list[list[float]]:
    """Compute pairwise Euclidean distances."""
    n = len(vectors)
    dists = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = math.sqrt(
                sum((a - b) ** 2 for a, b in zip(vectors[i], vectors[j]))
            )
            dists[i][j] = d
            dists[j][i] = d
    return dists


def _local_covariance(neighbors: list[list[float]], center: list[float]) -> list[list[float]]:
    """Compute local covariance matrix of neighbor points."""
    dim = len(center)
    n = len(neighbors)
    cov = [[0.0] * dim for _ in range(dim)]
    for nb in neighbors:
        for i in range(dim):
            for j in range(dim):
                cov[i][j] += (nb[i] - center[i]) * (nb[j] - center[j])
    for i in range(dim):
        for j in range(dim):
            cov[i][j] /= max(1, n)
    return cov


def _approximate_eigenvalues(matrix: list[list[float]]) -> list[float]:
    """Approximate eigenvalues via Gershgorin circle theorem."""
    n = len(matrix)
    centers = []
    radii = []
    for i in range(n):
        center = matrix[i][i]
        radius = sum(abs(matrix[i][j]) for j in range(n) if j != i)
        centers.append(center)
        radii.append(radius)

    # Return center + radius as eigenvalue proxy
    return [max(0, c + r) for c, r in zip(centers, radii)]


def _correlation(x: list[float], y: list[float]) -> float:
    """Pearson correlation between two lists."""
    n = len(x)
    if n < 3 or len(y) != n:
        return 0.0
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    cov = sum((a - mean_x) * (b - mean_y) for a, b in zip(x, y)) / n
    std_x = math.sqrt(sum((a - mean_x) ** 2 for a in x) / n)
    std_y = math.sqrt(sum((a - mean_y) ** 2 for a in y) / n)
    denom = std_x * std_y
    if denom < 1e-12:
        return 0.0
    return cov / denom
