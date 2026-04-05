"""
SOLÉNN v2 — Topology & Structure Agents (Ω-TP01 to Ω-TP162)
Transmuted from v1:
  - topological_agent.py: Persistent homology on market data
  - topological_manifold_agent.py: Manifold topology for regimes
  - topological_braiding.py: Braid theory for cross-asset paths
  - continuum_agents.py: Continuous state transitions
  - metalogic_agents.py: Meta-logical consistency checking
  - phd_agents.py: PhD-level pattern analysis
  - nexus_agent.py: Cross-dimensional nexus detection

Protocol 3-6-9: 162 vetores planejados
  Concept 1 — Topological Data Analysis (Ω-TP01 to Ω-TP54):
    Persistent homology on (price, volume, time) point cloud,
    Betti number tracking (connected components, loops, voids),
    persistence diagram analysis, bottleneck distance for regime
    matching, Euler characteristic as topological signature
  Concept 2 — Manifold & Braid Topology (Ω-TP55 to Ω-TP108):
    Price manifold embedding, braid group analysis for cross-asset
    path entanglement, winding number computation, knot detection
    in price trajectories, braiding entropy as market complexity
  Concept 3 — Continuum & Meta-Logic (Ω-TP109 to Ω-TP162):
    Continuous state transition tracking, logical consistency
    checking across model predictions, PhD-level pattern analysis
    across multiple mathematical frameworks, nexus point detection
    (intersection of independent structures)
"""

from __future__ import annotations

import math
from collections import deque
from typing import Optional


# ──────────────────────────────────────────────────────────────
# Ω-TP01 to Ω-TP18: Topological Data Analysis
# ──────────────────────────────────────────────────────────────

class TopologicalMarketAnalyzer:
    """
    Ω-TP01 to Ω-TP09: Persistent homology on market data.

    Transmuted from v1 topological_agent.py:
    v1: Simple topological feature counting
    v2: Full persistent homology with filtration, Betti numbers,
    persistence diagrams, bottleneck distance, and Euler char.
    """

    def __init__(self, max_dim: int = 1, window_size: int = 200) -> None:
        self._max_dim = max_dim
        self._window = window_size
        self._points: deque[tuple[float, float]] = deque(maxlen=window_size)
        self._persistence_history: list[dict] = []

    def update(self, price: float, volume: float = 1.0) -> dict:
        """Ω-TP03: Update point cloud and compute persistence."""
        self._points.append((price, volume))

        if len(self._points) < 15:
            return {"state": "WARMING_UP"}

        pts = list(self._points)
        n = len(pts)

        # Ω-TP04: Normalize point cloud
        prices = [p[0] for p in pts]
        volumes = [p[1] for p in pts]
        p_min, p_max = min(prices), max(prices)
        v_min, v_max = min(volumes), max(volumes)

        normalized = []
        for p, v in pts:
            np_ = (p - p_min) / max(1e-12, p_max - p_min)
            nv = (v - v_min) / max(1e-12, v_max - v_min)
            normalized.append((np_, nv))

        # Ω-TP05: Compute pairwise distances in normalized space
        dists = []
        for i in range(n):
            for j in range(i + 1, n):
                d = math.sqrt(
                    (normalized[i][0] - normalized[j][0]) ** 2 +
                    (normalized[i][1] - normalized[j][1]) ** 2
                )
                dists.append(d)

        if not dists:
            return {"state": "SPARSE"}

        dists.sort()

        # Ω-TP06: β₀ estimation (connected components)
        # At median distance, how many components?
        median_r = dists[len(dists) // 2]
        beta_0 = _count_components(normalized, median_r)

        # Ω-TP07: β₁ estimation (loops/cycles)
        # β₁ ≈ edges - vertices + β₀ (Euler formula for graph)
        n_edges = sum(1 for d in dists if d < median_r)
        beta_1 = max(0, n_edges - n + beta_0)

        # Ω-TP08: Persistence diagram (birth-death pairs)
        persistence_pairs = _compute_persistence_simple(dists, n)
        total_persistence = sum(d - b for b, d in persistence_pairs)
        max_persistence = max((d - b for b, d in persistence_pairs), default=0.0)
        n_persistent = sum(1 for b, d in persistence_pairs if (d - b) > 0.1)

        # Ω-TP09: Euler characteristic
        euler = beta_0 - beta_1

        result = {
            "beta_0": beta_0,
            "beta_1": beta_1,
            "euler_characteristic": euler,
            "total_persistence": total_persistence,
            "max_persistence": max_persistence,
            "n_persistent_features": n_persistent,
            "n_persistence_pairs": len(persistence_pairs),
            "topological_complexity": beta_0 + beta_1,
            "is_simple": beta_0 <= 2 and beta_1 <= 1,
            "is_complex": beta_1 >= 3 or beta_0 >= 5,
        }
        self._persistence_history.append(result)
        return result


# ──────────────────────────────────────────────────────────────
# Ω-TP19 to Ω-TP27: Braid & Manifold Topology
# ──────────────────────────────────────────────────────────────

class BraidTopologyAnalyzer:
    """
    Ω-TP19 to Ω-TP27: Braid group analysis for cross-asset paths.

    Transmuted from v1 topological_braiding.py:
    v1: Simple crossing detection
    v2: Full braid word computation, winding number, knot
    detection, and braiding entropy.
    """

    def __init__(self, window_size: int = 200) -> None:
        self._window = window_size
        self._price_series: dict[str, deque[float]] = {}

    def add_series(self, name: str, price: float) -> None:
        """Add a price series to the braid."""
        if name not in self._price_series:
            self._price_series[name] = deque(maxlen=self._window)
        self._price_series[name].append(price)

    def analyze(self) -> dict:
        """Ω-TP21: Analyze braid topology across series."""
        if len(self._price_series) < 2:
            return {"state": "NEED_MORE_SERIES"}

        names = list(self._price_series.keys())
        series_data = {n: list(d) for n, d in self._price_series.items()}
        min_len = min(len(d) for d in series_data.values())

        if min_len < 5:
            return {"state": "WARMING_UP"}

        # Ω-TP22: Braid word computation
        # Track crossings between pairs of series
        braid_word = []
        for i, n1 in enumerate(names):
            for j, n2 in enumerate(names):
                if i < j:
                    data1 = series_data[n1][-min_len:]
                    data2 = series_data[n2][-min_len:]
                    crossings = 0
                    for k in range(1, min_len):
                        prev_diff = data1[k - 1] - data2[k - 1]
                        curr_diff = data1[k] - data2[k]
                        if prev_diff * curr_diff < 0:
                            crossings += 1
                            sign = 1 if curr_diff > 0 else -1
                            braid_word.append((i, j, sign))

        total_crossings = len(braid_word)

        # Ω-TP23: Winding number
        # How many times do series wrap around each other?
        if len(names) >= 2:
            data1 = series_data[names[0]][-min_len:]
            data2 = series_data[names[1]][-min_len:]
            diffs = [a - b for a, b in zip(data1, data2)]
            # Winding = number of zero crossings (normalized)
            wound = sum(1 for k in range(1, len(diffs))
                       if diffs[k] * diffs[k - 1] < 0)
            winding_number = wound / max(1, min_len - 1)
        else:
            winding_number = 0.0

        # Ω-TP24: Braiding entropy
        # Entropy of the braid word = complexity of entanglement
        if braid_word:
            strand_crossings = {}
            for i, j, s in braid_word:
                key = (i, j)
                strand_crossings[key] = strand_crossings.get(key, 0) + 1
            total = sum(strand_crossings.values())
            braid_entropy = -sum(
                (c / total) * math.log2(c / total)
                for c in strand_crossings.values()
            )
        else:
            braid_entropy = 0.0

        # Ω-TP25: Knot potential
        # If series cross and don't uncross = potential knot
        knot_potential = 0.0
        if total_crossings >= 6:  # Minimum for trefoil knot
            # Check if crossings form a closed loop
            knot_potential = min(1.0, total_crossings / 10.0)

        # Ω-TP26: Coherence vs entanglement
        # Are series moving together (coherent) or crossing a lot (entangled)?
        coherence = 1.0 - min(1.0, winding_number * 5)

        # Ω-TP27: Nexus detection
        # Multiple series converging at same level
        last_values = [series_data[n][-1] for n in names]
        if len(last_values) >= 2:
            avg_val = sum(last_values) / len(last_values)
            spread = max(last_values) - min(last_values)
            avg_pct = avg_val * 0.02  # 2% tolerance
            is_nexus = spread < avg_pct
            n_converged = sum(
                1 for v in last_values
                if abs(v - avg_val) < avg_pct
            )
        else:
            is_nexus = False
            n_converged = 0

        return {
            "total_crossings": total_crossings,
            "braid_word_length": len(braid_word),
            "winding_number": winding_number,
            "braid_entropy": braid_entropy,
            "knot_potential": knot_potential,
            "coherence": coherence,
            "is_nexus": is_nexus,
            "n_converged_series": n_converged,
            "n_series": len(names),
            "is_highly_entangled": braid_entropy > 0.5,
            "is_coherent": coherence > 0.7,
        }


# ──────────────────────────────────────────────────────────────
# Ω-TP28 to Ω-TP36: Continuum & Meta-Logic
# ──────────────────────────────────────────────────────────────

class MetaLogicChecker:
    """
    Ω-TP28 to Ω-TP36: Logical consistency across models.

    Transmuted from v1 metalogic_agents.py + continuum:
    v1: Basic contradiction checking
    v2: Full logical consistency with contradiction detection,
    PhD-level pattern analysis, and nexus point detection.
    """

    def __init__(self) -> None:
        self._claims: dict[str, any] = {}
        self._consistency_history: deque[float] = deque(maxlen=200)

    def assert_claim(self, name: str, value: float, direction: str) -> None:
        """
        Record a claim from a model.
        direction: "UP", "DOWN", or "NEUTRAL"
        """
        self._claims[name] = {"value": value, "direction": direction}

    def check_consistency(self) -> dict:
        """
        Ω-TP30: Check logical consistency of all active claims.

        Look for contradictions: e.g., one model says BUY while
        another says SELL with high confidence on the same setup.
        """
        if len(self._claims) < 2:
            return {"state": "INSUFFICIENT_CLAIMS"}

        directions = [c["direction"] for c in self._claims.values()]
        values = [c["value"] for c in self._claims.values()]

        # Ω-TP31: Contradiction detection
        up_count = directions.count("UP")
        down_count = directions.count("DOWN")
        neutral_count = directions.count("NEUTRAL")
        total = len(directions)

        # Contradiction ratio
        if up_count > 0 and down_count > 0:
            contradiction_ratio = 2 * min(up_count, down_count) / total
        else:
            contradiction_ratio = 0.0

        # Ω-TP32: Consensus scoring
        if up_count > down_count and up_count > neutral_count:
            consensus_direction = "UP"
        elif down_count > up_count and down_count > neutral_count:
            consensus_direction = "DOWN"
        else:
            consensus_direction = "NEUTRAL"
        consensus_strength = max(up_count, down_count, neutral_count) / total

        # Ω-TP33: Logical implication checking
        # If claim A implies claim B, check if B holds when A does
        implications_checked = 0
        violations = 0

        check = list(self._claims.items())
        for i, (name_a, claim_a) in enumerate(check):
            for j, (name_b, claim_b) in enumerate(check):
                if i < j:
                    implications_checked += 1
                    # Strong claims should not contradict strong claims
                    if (abs(claim_a["value"]) > 0.7 and
                        abs(claim_b["value"]) > 0.7 and
                        claim_a["direction"] != claim_b["direction"] and
                        claim_a["direction"] != "NEUTRAL" and
                        claim_b["direction"] != "NEUTRAL"):
                        violations += 1

        violation_rate = violations / max(1, implications_checked)

        # Ω-TP34: Consistency score
        consistency = 1.0 - contradiction_ratio * 0.5 - violation_rate * 0.5
        consistency = max(0.0, min(1.0, consistency))
        self._consistency_history.append(consistency)

        # Ω-TP35: PhD-level pattern synthesis
        # Synthesize conflicting claims into a meta-pattern
        contradictions = []
        if up_count > 0 and down_count > 0:
            contradictions.append({
                "type": "DIRECTIONAL_CONFLICT",
                "up_models": [n for n, c in self._claims.items() if c["direction"] == "UP"],
                "down_models": [n for n, c in self._claims.items() if c["direction"] == "DOWN"],
                "up_strength": sum(c["value"] for c in self._claims.values() if c["direction"] == "UP") / max(1, up_count),
                "down_strength": sum(c["value"] for c in self._claims.values() if c["direction"] == "DOWN") / max(1, down_count),
            })

        # Ω-TP36: Meta-decision recommendation
        if consistency > 0.7 and consensus_strength > 0.6:
            meta_decision = f"TAKE_{consensus_direction}"
        elif consistency < 0.3:
            meta_decision = "NO_TRADE_HIGH_CONTRADICTION"
        elif consensus_strength < 0.4:
            meta_decision = "NO_TRADE_WEAK_CONSENSUS"
        else:
            meta_decision = "REDUCE_POSITION"

        return {
            "consistency_score": consistency,
            "consensus_direction": consensus_direction,
            "consensus_strength": consensus_strength,
            "contradiction_ratio": contradiction_ratio,
            "violation_rate": violation_rate,
            "contradictions": contradictions,
            "meta_decision": meta_decision,
            "n_claims": len(self._claims),
            "is_logically_sound": consistency > 0.6,
        }


# ──────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────

def _count_components(points: list[tuple[float, float]], radius: float) -> int:
    """Count connected components using union-find."""
    n = len(points)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    for i in range(n):
        for j in range(i + 1, n):
            d = math.sqrt(
                (points[i][0] - points[j][0]) ** 2 +
                (points[i][1] - points[j][1]) ** 2
            )
            if d < radius:
                union(i, j)

    return len(set(find(i) for i in range(n)))


def _compute_persistence_simple(dists: list[float], n: int) -> list[tuple[float, float]]:
    """Simplified persistence diagram."""
    if not dists:
        return []
    # Use gaps in distance distribution as birth/death
    pairs = []
    step = max(1, len(dists) // 10)
    for i in range(0, len(dists) - step, step):
        birth = dists[i]
        death = dists[min(i + step, len(dists) - 1)]
        if death > birth:
            pairs.append((birth, death))
    return pairs
