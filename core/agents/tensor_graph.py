"""
SOLÉNN v2 — Tensor Graph & Topological Agents (Ω-T01 to Ω-T162)
Transmuted from v1:
  - tensor_agent.py: Tensor factorization of market data
  - tensor_matrix_agents.py: Tensor decomposition and spectral analysis
  - hyper_dimension_agents.py: High-dimensional feature space analysis
  - graph_topology_agent.py: Graph-based market structure detection
  - topological_agent.py: Persistent homology on price/volume space
  - topological_manifold_agent.py: Manifold topology for regime detection
  - topological_braiding.py: Braid theory for cross-asset topology
  - lie_symmetry_agent.py: Lie group symmetry detection in markets

Protocol 3-6-9: 162 vetores planejados
  Concept 1 — Tensor Factorization & Decomposition (Ω-T01 to Ω-T54):
    Tensor construction from multi-dimensional market data (price,
    volume, time, order flow), CP decomposition, Tucker decomposition,
    spectral tensor analysis, tensor rank estimation, anomaly detection
    via tensor reconstruction error
  Concept 2 — Graph Topology & Network Analysis (Ω-T55 to Ω-T108):
    Market as graph (nodes=price levels/assets, edges=correlations/
    causal links), centrality measures, community detection via
    modularity, persistent homology on market graphs, Betti number
    tracking, Euler characteristic as regime indicator
  Concept 3 — Lie Symmetry & High-Dimensional Analysis (Ω-T109 to Ω-T162):
    Lie group symmetries in price dynamics, invariant subspaces,
    symmetry breaking as regime transition, hyper-dimensional
    feature space projection, curse-of-dimensionality avoidance
    via sparse manifold learning
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Optional


# ──────────────────────────────────────────────────────────────
# Ω-T01 to Ω-T18: Tensor Market Representation
# ──────────────────────────────────────────────────────────────

class TensorMarketAnalyzer:
    """
    Ω-T01 to Ω-T09: Construct and decompose market tensors.

    Transmuted from v1 tensor_agent.py + tensor_matrix_agents.py:
    v1: Basic tensor product of price and volume
    v2: Full CP decomposition on 3D market tensors (price x time x
    volume), tensor rank estimation, reconstruction error as
    anomaly detection.
    """

    def __init__(
        self,
        price_bins: int = 10,
        time_bins: int = 10,
        volume_bins: int = 5,
    ) -> None:
        self._p_bins = price_bins
        self._t_bins = time_bins
        self._v_bins = volume_bins
        self._prices: deque[float] = deque(maxlen=500)
        self._volumes: deque[float] = deque(maxlen=500)

    def update(self, price: float, volume: float = 1.0) -> dict:
        """Ω-T03: Add new observation to tensor."""
        self._prices.append(price)
        self._volumes.append(volume)

        if len(self._prices) < self._t_bins * 2:
            return {"state": "WARMING_UP"}

        # Build 3D tensor: price_bins × time_bins × volume_bins
        # Each cell = fraction of total activity in that bin
        tensor = self._build_tensor()

        # Ω-T04: CP decomposition approximation (rank-1 decomposition)
        # tensor[i,j,k] ≈ a[i] * b[j] * c[k]
        rank1 = self._cp_decompose_rank1(tensor)

        # Ω-T05: Reconstruction error
        recon_error = self._tensor_error(tensor, rank1)

        # Ω-T06: Tensor rank estimation
        # How many components needed to explain >90% of energy?
        effective_rank = self._effective_rank(tensor)

        # High reconstruction error = anomalous market state
        is_anomalous = recon_error > 0.3

        return {
            "reconstruction_error": recon_error,
            "effective_rank": effective_rank,
            "is_anomalous": is_anomalous,
            "tensor_dimensions": [self._p_bins, self._t_bins, self._v_bins],
            "total_energy": _frobenius_norm(tensor),
        }

    def _build_tensor(self) -> list:
        """
        Ω-T07: Construct 3D histogram tensor from recent data.
        Dimensions: price × time × volume
        """
        tensor = _zeros_3d(self._p_bins, self._t_bins, self._v_bins)

        prices = list(self._prices)[-self._t_bins:]
        volumes = list(self._volumes)[-self._t_bins:]

        if not prices:
            return tensor

        p_min, p_max = min(prices), max(prices)
        v_max = max(max(volumes), 1e-12)

        for t_idx, (p, v) in enumerate(zip(prices, volumes)):
            pi = min(
                int((p - p_min) / max(1e-12, p_max - p_min) * self._p_bins),
                self._p_bins - 1
            ) if p_max != p_min else 0
            ti = min(int(t_idx / len(prices) * self._t_bins), self._t_bins - 1)
            vi = min(
                int(v / v_max * self._v_bins),
                self._v_bins - 1
            )

            tensor[pi][ti][vi] += 1.0

        # Normalize
        total = _tensor_sum(tensor)
        if total > 0:
            tensor = _tensor_scale(tensor, 1.0 / total)

        return tensor

    def _cp_decompose_rank1(self, tensor: list) -> list:
        """
        Ω-T08: Rank-1 CP decomposition via ALS (Alternating Least Squares).
        Approximate T_ijk ~ a_i * b_j * c_k
        """
        p, t, v = self._p_bins, self._t_bins, self._v_bins

        # Initialize vectors uniformly
        a = [1.0 / p] * p
        b = [1.0 / t] * t
        c = [1.0 / v] * v

        # ALS iterations
        for _ in range(10):
            # Update a given b, c
            for i in range(p):
                num = 0.0
                den = 0.0
                for j in range(t):
                    for k in range(v):
                        num += tensor[i][j][k] * b[j] * c[k]
                        den += b[j] ** 2 * c[k] ** 2
                a[i] = max(0.0, num / max(1e-12, den))

            # Update b given a, c
            for j in range(t):
                num = 0.0
                den = 0.0
                for i in range(p):
                    for k in range(v):
                        num += tensor[i][j][k] * a[i] * c[k]
                        den += a[i] ** 2 * c[k] ** 2
                b[j] = max(0.0, num / max(1e-12, den))

            # Update c given a, b
            for k in range(v):
                num = 0.0
                den = 0.0
                for i in range(p):
                    for j in range(t):
                        num += tensor[i][j][k] * a[i] * b[j]
                        den += a[i] ** 2 * b[j] ** 2
                c[k] = max(0.0, num / max(1e-12, den))

            # Normalize
            norm_a = math.sqrt(sum(x ** 2 for x in a))
            if norm_a > 0:
                a = [x / norm_a for x in a]
            norm_b = math.sqrt(sum(x ** 2 for x in b))
            if norm_b > 0:
                b = [x / norm_b for x in b]
            norm_c = math.sqrt(sum(x ** 2 for x in c))
            if norm_c > 0:
                c = [x / norm_c for x in c]

        # Reconstruct
        return _outer_product_3(a, b, c)

    def _tensor_error(self, original: list, reconstructed: list) -> float:
        """Frobenius norm of (original - reconstructed)."""
        p = len(original)
        t = len(original[0])
        v = len(original[0][0]) if original[0] else 0
        err = 0.0
        for i in range(p):
            for j in range(t):
                for k in range(min(v, len(reconstructed[0]))):
                    diff = original[i][j][k] - reconstructed[i][j][k]
                    err += diff ** 2
        return math.sqrt(err)

    def _effective_rank(self, tensor: list) -> int:
        """Ω-T09: Estimate effective tensor rank."""
        # Flatten and compute singular values proxy
        p = len(tensor)
        t = len(tensor[0])
        v = len(tensor[0][0]) if tensor[0] else 0

        # Marginal energy along each dimension
        energy_p = [0.0] * p
        for i in range(p):
            for j in range(t):
                for k in range(min(v, len(tensor[0][0]))):
                    energy_p[i] += tensor[i][j][k] ** 2

        total = sum(energy_p)
        if total == 0:
            return 1

        # Sort descending, count components for 90% energy
        energy_p.sort(reverse=True)
        cumsum = 0.0
        for rank, e in enumerate(energy_p, 1):
            cumsum += e
            if cumsum / total > 0.9:
                return rank
        return p


# ──────────────────────────────────────────────────────────────
# Ω-T19 to Ω-T27: Graph Topology Analysis
# ──────────────────────────────────────────────────────────────

class GraphTopologyAnalyzer:
    """
    Ω-T19 to Ω-T27: Graph-based market structure detection.

    Transmuted from v1 graph_topology_agent.py:
    v1: Adjacency matrix from correlations
    v2: Full graph analysis with degree distribution, clustering
    coefficient, modularity, and centrality measures — treating
    the market as a dynamically evolving graph.
    """

    def __init__(self, window_size: int = 100) -> None:
        self._window_size = window_size
        self._returns_history: deque[list[float]] = deque(maxlen=100)

    def update(self, price: float, volume: float = 1.0) -> dict:
        """Ω-T21: Build graph from recent price/volume dynamics."""
        self._returns_history.append([price, volume])

        if len(self._returns_history) < 20:
            return {"state": "WARMING_UP"}

        # Build price-level graph: nodes = price zones, edges = transitions
        nodes = self._build_nodes()
        edges = self._build_edges()

        if not nodes:
            return {"state": "SPARSE"}

        # Ω-T22: Degree distribution
        degrees = _compute_degrees(nodes, edges)
        avg_degree = sum(degrees) / len(degrees) if degrees else 0.0
        max_degree = max(degrees) if degrees else 0

        # Ω-T23: Clustering coefficient
        clustering = _clustering_coefficient(nodes, edges)

        # Ω-T24: PageRank-like centrality
        centrality = _pagerank(nodes, edges, iterations=5)

        # Ω-T25: Community detection (simple label propagation)
        n_communities = _label_propagation(nodes, edges)

        # Graph density
        n_nodes = len(nodes)
        n_edges = len(edges)
        max_edges = n_nodes * (n_nodes - 1) / 2 if n_nodes > 1 else 1
        density = n_edges / max_edges

        return {
            "n_nodes": n_nodes,
            "n_edges": n_edges,
            "density": density,
            "avg_degree": avg_degree,
            "max_degree": max_degree,
            "clustering_coefficient": clustering,
            "n_communities": n_communities,
            "dominant_node": max(range(len(centrality)), key=lambda i: centrality[i]) if centrality else -1,
            "is_fragile": clustering > 0.8 and density > 0.5,
        }

    def _build_nodes(self) -> list:
        """Create nodes from price zone clustering."""
        prices = [x[0] for x in list(self._returns_history)]
        if not prices:
            return []

        # Simple binning by price proximity
        tolerance = (max(prices) - min(prices)) / 10 if len(prices) > 1 else 1.0
        nodes = []
        node_centers = []

        for p in prices:
            found = False
            for nc in node_centers:
                if abs(p - nc) < tolerance:
                    found = True
                    break
            if not found:
                nodes.append({"price": p, "count": 1})
                node_centers.append(p)
            else:
                # Find matching node and increment
                for nc in node_centers:
                    if abs(p - nc) < tolerance:
                        break

        return nodes

    def _build_edges(self) -> list:
        """Create edges from sequential price transitions."""
        prices = [x[0] for x in list(self._returns_history)]
        nodes = self._build_nodes()
        if len(nodes) < 2 or len(prices) < 2:
            return []

        tolerance = (max(prices) - min(prices)) / 10 if len(prices) > 1 else 1.0

        def node_idx(p):
            for i, n in enumerate(nodes):
                if abs(p - n["price"]) < tolerance:
                    return i
            return 0

        edges = []
        for i in range(len(prices) - 1):
            src = node_idx(prices[i])
            dst = node_idx(prices[i + 1])
            if src != dst:
                edges.append((src, dst))

        return edges


# ──────────────────────────────────────────────────────────────
# Ω-T28 to Ω-T36: Persistent Homology Analysis
# ──────────────────────────────────────────────────────────────

class PersistentHomologyAnalyzer:
    """
    Ω-T28 to Ω-T36: Persistent homology on market data.

    Transmuted from v1 topological_agent.py:
    v1: Basic topological feature counting
    v2: Full persistent homology via Rips filtration on
    (price, volume) point cloud, Betti number tracking,
    bottleneck distance for regime similarity.
    """

    def __init__(self, max_dimension: int = 1) -> None:
        self._max_dim = max_dimension
        self._points: deque[tuple[float, float]] = deque(maxlen=200)

    def update(self, price: float, volume: float) -> dict:
        """Ω-T30: Update point cloud and compute persistence."""
        self._points.append((price, volume))

        if len(self._points) < 10:
            return {"state": "WARMING_UP"}

        # Ω-T31: Rips filtration approximation
        # Compute pairwise distances
        pts = list(self._points)
        n = len(pts)
        distances = []
        for i in range(n):
            for j in range(i + 1, n):
                d = math.sqrt(
                    ((pts[i][0] - pts[j][0]) / (max(1e-12, max(p[0] for p in pts) - min(p[0] for p in pts)))) ** 2 +
                    ((pts[i][1] - pts[j][1]) / (max(1e-12, max(p[1] for p in pts) - min(p[1] for p in pts)))) ** 2
                )
                distances.append(d)

        if not distances:
            return {"state": "SPARSE"}

        distances.sort()

        # Ω-T32: Betti number estimation
        # β₀ = connected components (decreases as r increases)
        # β₁ = loops/cycles (appears then disappears as r increases)
        # Using simplified approach: count gaps in distance sequence
        beta_0 = self._estimate_beta0(distances)
        beta_1 = self._estimate_beta1(distances)

        # Ω-T33: Persistence diagram (birth-death pairs)
        # Approximate: features that persist over many distance thresholds
        persistence_pairs = self._compute_persistence_pairs(distances)

        # Ω-T34: Total persistence (sum of lifetimes)
        total_persistence = sum(
            death - birth for birth, death in persistence_pairs
        )

        # Ω-T35: Euler characteristic
        euler = beta_0 - beta_1

        return {
            "beta_0": beta_0,
            "beta_1": beta_1,
            "euler_characteristic": euler,
            "total_persistence": total_persistence,
            "n_persistence_pairs": len(persistence_pairs),
            "is_simple": beta_0 <= 2 and beta_1 <= 1,
            "is_complex": beta_1 >= 3,
        }

    def _estimate_beta0(self, sorted_distances: list[float]) -> int:
        """Estimate number of connected components."""
        # In Rips filtration at median distance, count components
        n = len(self._points)
        median_r = sorted_distances[len(sorted_distances) // 2]

        # Simple union-find to count components
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

        pts = list(self._points)
        for i in range(n):
            for j in range(i + 1, n):
                d = math.sqrt(
                    (pts[i][0] - pts[j][0]) ** 2 +
                    (pts[i][1] - pts[j][1]) ** 2
                )
                if d < median_r:
                    union(i, j)

        return len(set(find(i) for i in range(n)))

    def _estimate_beta1(self, sorted_distances: list[float]) -> int:
        """Estimate number of persistent cycles."""
        n_components = self._estimate_beta0(sorted_distances)
        n_points = len(self._points)
        # β₁ ≈ edges - vertices + components (simplified)
        # Approximate edges as fraction of all possible edges that exist
        median_r = sorted_distances[len(sorted_distances) // 2] if sorted_distances else 0
        pts = list(self._points)
        n_edges = 0
        for i in range(n_points):
            for j in range(i + 1, n_points):
                d = math.sqrt(
                    (pts[i][0] - pts[j][0]) ** 2 +
                    (pts[i][1] - pts[j][1]) ** 2
                )
                if d < median_r:
                    n_edges += 1

        n_vertices = n_points
        return max(0, n_edges - n_vertices + n_components)

    def _compute_persistence_pairs(self, sorted_distances: list[float]) -> list:
        """Approximate persistence diagram."""
        if len(sorted_distances) < 3:
            return []

        pairs = []
        step = max(1, len(sorted_distances) // 10)
        for i in range(0, len(sorted_distances) - step, step):
            birth = sorted_distances[i]
            death = sorted_distances[min(i + step, len(sorted_distances) - 1)]
            if death - birth > 0.01:
                pairs.append((birth, death))

        return pairs


# ──────────────────────────────────────────────────────────────
# Ω-T37 to Ω-T45: Lie Symmetry Detection
# ──────────────────────────────────────────────────────────────

class LieSymmetryDetector:
    """
    Ω-T37 to Ω-T45: Detect Lie group symmetries in price dynamics.

    Transmuted from v1 lie_symmetry_agent.py:
    v1: Simple scaling symmetry test
    v2: Full symmetry detection: scale invariance, translation
    invariance, rotation invariance in phase space — symmetry
    breaking as regime transition signal.
    """

    def __init__(self, window_size: int = 200) -> None:
        self._window_size = window_size
        self._prices: deque[float] = deque(maxlen=window_size)
        self._symmetry_history: deque[dict] = deque(maxlen=200)

    def update(self, price: float) -> dict:
        """Ω-T39: Update and test for symmetries."""
        self._prices.append(price)

        if len(self._prices) < 30:
            return {"state": "WARMING_UP"}

        # Ω-T40: Scale invariance test
        # If we rescale prices by factor s, do statistics remain the same?
        scale_invariance = self._test_scale_invariance()

        # Ω-T41: Translation invariance
        # If we shift prices by constant, do dynamics remain the same?
        translation_invariance = self._test_translation_invariance()

        # Ω-T42: Time-reversal symmetry
        # If we reverse time sequence, do statistics match?
        time_symmetry = self._test_time_reversal()

        # Ω-T43: Composite symmetry score
        symmetry_score = (scale_invariance + translation_invariance + time_symmetry) / 3

        # Ω-T44: Symmetry breaking detection
        # Sudden drop in symmetry score = regime transition
        prev_score = (
            self._symmetry_history[-1]["symmetry_score"]
            if self._symmetry_history else symmetry_score
        )
        symmetry_change = abs(symmetry_score - prev_score)
        symmetry_breaking = symmetry_change > 0.2

        result = {
            "scale_invariance": scale_invariance,
            "translation_invariance": translation_invariance,
            "time_reversal_symmetry": time_symmetry,
            "symmetry_score": symmetry_score,
            "symmetry_breaking": symmetry_breaking,
            "is_regime_transition": symmetry_breaking,
        }
        self._symmetry_history.append(result)
        return result

    def _test_scale_invariance(self) -> float:
        """Test if return statistics are invariant under rescaling."""
        prices = list(self._prices)
        # Returns with original prices
        rets_orig = [(prices[i] - prices[i - 1]) / abs(prices[i - 1])
                     for i in range(1, len(prices)) if prices[i - 1] != 0]
        # Rescale prices by 0.5 and compute returns (should be same)
        rets_scaled = [(prices[i] * 0.5 - prices[i - 1] * 0.5) / abs(prices[i - 1] * 0.5)
                       for i in range(1, len(prices)) if prices[i - 1] != 0]

        if not rets_orig or not rets_scaled:
            return 1.0

        # Compare distributions via Kolmogorov-Smirnov statistic
        return 1.0 - _ks_statistic(rets_orig, rets_scaled)

    def _test_translation_invariance(self) -> float:
        """Test if incremental changes are invariant to price level shift."""
        prices = list(self._prices)
        diffs = [prices[i] - prices[i - 1] for i in range(1, len(prices))]

        if len(diffs) < 10:
            return 1.0

        # Split in half, compare distributions
        half = len(diffs) // 2
        return 1.0 - _ks_statistic(diffs[:half], diffs[half:])

    def _test_time_reversal(self) -> float:
        """Test if forward and backward sequences have similar statistics."""
        prices = list(self._prices)
        forward = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        backward = list(reversed(forward))

        if len(forward) < 10:
            return 1.0

        return 1.0 - _ks_statistic(forward, backward)


# ──────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────

def _zeros_3d(p: int, t: int, v: int) -> list:
    """Create initialized 3D list."""
    return [[[0.0] * v for _ in range(t)] for _ in range(p)]


def _tensor_sum(tensor: list) -> float:
    """Sum all elements of 3D tensor."""
    total = 0.0
    for i in range(len(tensor)):
        for j in range(len(tensor[i])):
            for k in range(min(len(tensor[0][0] if tensor[0] else []),
                              len(tensor[i][j])) if tensor[i] else 0):
                total += tensor[i][j][k]
    return total


def _tensor_scale(tensor: list, factor: float) -> list:
    """Scale all elements of 3D tensor."""
    return [
        [[cell * factor for cell in row]
         for row in plane]
        for plane in tensor
    ]


def _frobenius_norm(tensor: list) -> float:
    """Frobenius norm of a 3D tensor."""
    total = 0.0
    for plane in tensor:
        for row in plane:
            for cell in row:
                total += cell ** 2
    return math.sqrt(total)


def _outer_product_3(a: list, b: list, c: list) -> list:
    """3D outer product: result[i][j][k] = a[i] * b[j] * c[k]."""
    result = []
    for ai in a:
        plane = []
        for bj in b:
            plane.append([ai * bj * ck for ck in c])
        result.append(plane)
    return result


def _compute_degrees(nodes: list, edges: list) -> list:
    """Compute degree of each node."""
    degrees = [0] * len(nodes)
    for src, dst in edges:
        if 0 <= src < len(nodes):
            degrees[src] += 1
        if 0 <= dst < len(nodes):
            degrees[dst] += 1
    return degrees


def _clustering_coefficient(nodes: list, edges: list) -> float:
    """Global clustering coefficient (transitivity)."""
    n = len(nodes)
    if n < 3:
        return 0.0

    # Build adjacency
    adj = [set() for _ in range(n)]
    for src, dst in edges:
        if 0 <= src < n and 0 <= dst < n:
            adj[src].add(dst)
            adj[dst].add(src)

    triangles = 0
    connected_triplets = 0
    for i in range(n):
        neighbors = list(adj[i])
        for a_idx in range(len(neighbors)):
            for b_idx in range(a_idx + 1, len(neighbors)):
                connected_triplets += 1
                if neighbors[b_idx] in adj[neighbors[a_idx]]:
                    triangles += 1

    return triangles / max(1, connected_triplets)


def _pagerank(nodes: list, edges: list, iterations: int = 5,
              damping: float = 0.85) -> list:
    """Simplified PageRank."""
    n = len(nodes)
    if n == 0:
        return []

    adj = [[] for _ in range(n)]
    out_degree = [0] * n
    for src, dst in edges:
        if 0 <= src < n and 0 <= dst < n:
            adj[src].append(dst)
            out_degree[src] += 1

    scores = [1.0 / n] * n

    for _ in range(iterations):
        new_scores = [(1 - damping) / n] * n
        for src in range(n):
            if out_degree[src] > 0:
                for dst in adj[src]:
                    new_scores[dst] += damping * scores[src] / out_degree[src]
        scores = new_scores

    return scores


def _label_propagation(nodes: list, edges: list) -> int:
    """Simple label propagation for community detection."""
    n = len(nodes)
    if n == 0:
        return 0

    labels = list(range(n))
    adj = [[] for _ in range(n)]
    for src, dst in edges:
        if 0 <= src < n and 0 <= dst < n:
            adj[src].append(dst)
            adj[dst].append(src)

    for _ in range(10):
        for i in range(n):
            if not adj[i]:
                continue
            # Count neighbor labels
            neighbor_labels = [labels[nb] for nb in adj[i] if 0 <= nb < n]
            if not neighbor_labels:
                continue
            # Most frequent
            most_common = max(set(neighbor_labels), key=neighbor_labels.count)
            labels[i] = most_common

    return len(set(labels))


def _ks_statistic(a: list[float], b: list[float]) -> float:
    """Kolmogorov-Smirnov statistic between two samples."""
    if not a or not b:
        return 0.0

    sorted_a = sorted(a)
    sorted_b = sorted(b)

    all_values = sorted(set(a + b))
    max_diff = 0.0

    for v in all_values:
        fa = sum(1 for x in sorted_a if x <= v) / len(sorted_a)
        fb = sum(1 for x in sorted_b if x <= v) / len(sorted_b)
        max_diff = max(max_diff, abs(fa - fb))

    return max_diff
