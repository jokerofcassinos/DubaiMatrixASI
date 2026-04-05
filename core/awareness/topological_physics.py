"""
SOLÉNN v2 — Ω-TOPOLGY — Tensor Analysis, Persistent Homology,
            Ricci Curvature, Hyperdimensional Projection & Holographic Memory.
Pure Python, no numpy, frozen dataclasses.
"""

from __future__ import annotations

import math
import random
import time
from collections import deque, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ============================================================
# Types
# ============================================================

@dataclass(frozen=True, slots=True)
class TopologicalState:
    betti_0: int
    betti_1: int
    euler_characteristic: float
    persistence_entropy: float
    ricci_curvature: float
    dimension_estimate: int
    manifold_quality: float
    homology_stable: bool


# ============================================================
# 1. Hyperdimensional Projector (Johnson-Lindenstrauss)
# ============================================================

class HyperdimensionalProjector:
    def __init__(self, input_dim: int = 20, target_dim: int = 5,
                 epsilon: float = 0.1, seed: Optional[int] = None) -> None:
        self._input_dim = input_dim
        self._target_dim = target_dim
        self._epsilon = epsilon
        self._rng = random.Random(seed or 42)
        self._matrix: List[List[float]] = []
        scale = 1.0 / math.sqrt(target_dim)
        for i in range(input_dim):
            row = [scale if self._rng.random() > 0.5 else -scale
                   for _ in range(target_dim)]
            self._matrix.append(row)
        self._intrinsic_dim: float = float(input_dim)

    def project(self, vector: List[float]) -> List[float]:
        if len(vector) != self._input_dim:
            return [0.0] * self._target_dim
        result = [0.0] * self._target_dim
        for i in range(self._input_dim):
            for j in range(self._target_dim):
                result[j] += vector[i] * self._matrix[i][j]
        return result

    def estimate_intrinsic_dimension(self, projected: List[List[float]]) -> float:
        if len(projected) < 10:
            return float(self._target_dim)
        k = min(5, len(projected) - 1)
        dims = []
        for i in range(len(projected)):
            dists = sorted(
                _euclidean_seq(projected[i], projected[j])
                for j in range(len(projected)) if j != i
            )[:k]
            if dists and dists[0] > 1e-10 and len(dists) > 1:
                ratio = dists[-1] / max(1e-10, dists[0])
                d = math.log(max(1, len(projected))) / max(1e-10, math.log(ratio))
                dims.append(d)
        self._intrinsic_dim = sum(dims) / max(1, len(dims))
        return self._intrinsic_dim

    @property
    def intrinsic_dim(self) -> float:
        return self._intrinsic_dim


# ============================================================
# 2. Resonance Network
# ============================================================

class ResonanceNetwork:
    def __init__(self, n_agents: int = 5) -> None:
        self._n = n_agents
        self._signals: List[deque] = [deque(maxlen=50) for _ in range(n_agents)]

    def update(self, agent_id: int, signal: float) -> None:
        if 0 <= agent_id < self._n:
            self._signals[agent_id].append(signal)

    @property
    def consensus(self) -> float:
        means = []
        for i in range(self._n):
            s = list(self._signals[i])
            if s:
                means.append(sum(s) / len(s))
        if len(means) < 2:
            return 1.0
        return max(0.0, 1.0 - (max(means) - min(means)))

    @property
    def resonance_score(self) -> float:
        signs = []
        for i in range(self._n):
            s = list(self._signals[i])
            if s:
                signs.append(1 if sum(s) > 0 else -1)
        if not signs:
            return 0.0
        return sum(1 for s in signs if s == signs[0]) / len(signs)


# ============================================================
# 3. Tensor Market Analysis
# ============================================================

class TensorMarketAnalyzer:
    @staticmethod
    def construct_3d(prices: List[float], times: List[float],
                     volumes: List[float], grid: int = 5) -> List[List[List[float]]]:
        tensor = [[[0.0]*grid for _ in range(grid)] for __ in range(grid)]
        if not prices:
            return tensor
        ps = (min(prices), max(prices))
        ts = (min(times), max(times))
        vs = (min(volumes), max(volumes))
        pr = (max(1e-10, ps[1] - ps[0]),
              max(1e-10, ts[1] - ts[0]),
              max(1e-10, vs[1] - vs[0]))
        gs = max(1, grid - 1)
        for i in range(len(prices)):
            pi = min(gs, max(0, int((prices[i] - ps[0]) / pr[0] * gs)))
            ti = min(gs, max(0, int((times[i] - ts[0]) / pr[1] * gs)))
            vi = min(gs, max(0, int((volumes[i] - vs[0]) / pr[2] * gs)))
            tensor[pi][ti][vi] += 1.0
        return tensor

    @staticmethod
    def tensor_energy(tensor: List[List[List[float]]]) -> float:
        total = 0.0
        for i in tensor:
            for j in i:
                for v in j:
                    total += v * v
        return math.sqrt(total)

    @staticmethod
    def rank1_approximation(tensor: List[List[List[float]]],
                            dims: Tuple[int, int, int]) -> Tuple[List[float], List[float], List[float]]:
        d1, d2, d3 = dims
        a = [1.0] * d1
        b = [1.0] * d2
        c = [1.0] * d3
        for _ in range(10):
            na = [0.0] * d1
            for i in range(d1):
                for j in range(d2):
                    for k in range(d3):
                        na[i] += tensor[i % len(tensor)][j % len(tensor[0])][k % len(tensor[0][0])] * b[j] * c[k]
            nb = [0.0] * d2
            for j in range(d2):
                for i in range(d1):
                    for k in range(d3):
                        nb[j] += tensor[i % len(tensor)][j % len(tensor[0])][k % len(tensor[0][0])] * a[i] * c[k]
            nc = [0.0] * d3
            for k in range(d3):
                for i in range(d1):
                    for j in range(d2):
                        nc[k] += tensor[i % len(tensor)][j % len(tensor[0])][k % len(tensor[0][0])] * a[i] * b[j]
            for vec in (na, nb, nc):
                norm = math.sqrt(sum(v * v for v in vec))
                if norm > 0:
                    for ii in range(len(vec)):
                        vec[ii] /= norm
            a, b, c = na, nb, nc
        return a, b, c

    @staticmethod
    def reconstruction_error(tensor: List[List[List[float]]],
                             a: List[float], b: List[float], c: List[float]) -> float:
        error = 0.0
        for i in range(len(tensor)):
            for j in range(len(tensor[0])):
                for k in range(len(tensor[0][0])):
                    approx = a[i % len(a)] * b[j % len(b)] * c[k % len(c)]
                    error += (tensor[i][j][k] - approx) ** 2
        return math.sqrt(error)


# ============================================================
# 4. Graph Topology Analysis
# ============================================================

class GraphTopologyAnalyzer:
    @staticmethod
    def clustering_coefficient(adj: Dict[str, List[str]]) -> Dict[str, float]:
        result = {}
        for node in adj:
            nb = adj[node]
            k = len(nb)
            if k < 2:
                result[node] = 0.0
                continue
            links = 0
            for i in range(k):
                for j in range(i + 1, k):
                    if nb[j] in adj.get(nb[i], []):
                        links += 1
            result[node] = 2.0 * links / (k * (k - 1))
        return result

    @staticmethod
    def pagerank(adj: Dict[str, List[str]], damping: float = 0.85,
                 iterations: int = 20) -> Dict[str, float]:
        nodes = list(adj.keys())
        n = len(nodes)
        if n == 0:
            return {}
        pr = {node: 1.0 / n for node in nodes}
        for _ in range(iterations):
            new_pr = {node: (1 - damping) / n for node in nodes}
            for node in nodes:
                out_deg = len(adj.get(node, []))
                if out_deg > 0:
                    for nb in adj[node]:
                        if nb in new_pr:
                            new_pr[nb] += damping * pr[node] / out_deg
            total = sum(new_pr.values())
            if total > 0:
                for node in new_pr:
                    new_pr[node] /= total
            pr = new_pr
        return pr

    @staticmethod
    def connected_components(adj: Dict[str, List[str]]) -> List[set]:
        visited = set()
        components = []
        all_nodes = set(adj.keys())
        for nl in adj.values():
            all_nodes.update(nl)
        for node in all_nodes:
            if node not in visited:
                comp = set()
                queue = [node]
                while queue:
                    curr = queue.pop(0)
                    if curr in visited:
                        continue
                    visited.add(curr)
                    comp.add(curr)
                    for nb in adj.get(curr, []):
                        if nb not in visited:
                            queue.append(nb)
                if comp:
                    components.append(comp)
        return components


# ============================================================
# 5. Persistent Homology (Union-Find)
# ============================================================

class PersistentHomologyCalculator:
    def __init__(self, max_epsilon: float = 0.5, steps: int = 10) -> None:
        self._max_eps = max_epsilon
        self._steps = steps
        self._points: List[Tuple[float, float]] = []

    def add_point(self, x: float, y: float) -> None:
        self._points.append((x, y))

    def compute(self) -> TopologicalState:
        n = len(self._points)
        if n < 3:
            return TopologicalState(
                betti_0=n, betti_1=0, euler_characteristic=float(n),
                persistence_entropy=0.0, ricci_curvature=0.0,
                dimension_estimate=max(1, n), manifold_quality=0.0, homology_stable=True
            )
        dists = []
        for i in range(n):
            for j in range(i + 1, n):
                d = _euclidean_seq(self._points[i], self._points[j])
                dists.append((d, i, j))
        dists.sort(key=lambda x: x[0])

        betti_0_h = [0] * self._steps
        betti_1_h = [0] * self._steps
        for step in range(self._steps):
            eps = self._max_eps * (step + 1) / self._steps
            uf = _UnionFind(n)
            edges = 0
            for d, i, j in dists:
                if d > eps:
                    break
                uf.union(i, j)
                edges += 1
            comps = len(set(uf.find(i) for i in range(n)))
            betti_0_h[step] = comps
            betti_1_h[step] = max(0, edges - n + comps)

        b0 = betti_0_h[-1]
        b1 = betti_1_h[-1]
        pe = _persistence_entropy(betti_1_h)
        stable = len(set(betti_0_h[-3:])) == 1 if len(betti_0_h) >= 3 else True
        return TopologicalState(
            betti_0=b0, betti_1=b1, euler_characteristic=b0 - b1,
            persistence_entropy=pe, ricci_curvature=0.0,
            dimension_estimate=max(1, int(math.log(n) / math.log(2))),
            manifold_quality=max(0.0, 1.0 - pe), homology_stable=stable,
        )


class _UnionFind:
    def __init__(self, n: int) -> None:
        self._p = list(range(n))

    def find(self, x: int) -> int:
        while self._p[x] != x:
            self._p[x] = self._p[self._p[x]]
            x = self._p[x]
        return x

    def union(self, x: int, y: int) -> None:
        rx, ry = self.find(x), self.find(y)
        if rx != ry:
            self._p[ry] = rx


def _persistence_entropy(history: List[int]) -> float:
    if not history or max(history) == 0:
        return 0.0
    total = sum(history)
    if total == 0:
        return 0.0
    return -sum((h / total) * math.log2(h / total) for h in history if h > 0)


# ============================================================
# 6. Ricci Curvature Detector
# ============================================================

class RicciCurvatureDetector:
    def __init__(self, window: int = 100) -> None:
        self._states: deque[List[float]] = deque(maxlen=window)

    def update(self, sv: List[float]) -> float:
        self._states.append(sv)
        if len(self._states) < 10:
            return 0.0
        states = list(self._states)
        n = len(states)
        k = min(5, n - 1)
        adj = defaultdict(list)
        for i in range(n):
            dists = sorted(((j, _euclidean_seq(states[i], states[j]))
                          for j in range(n) if j != i), key=lambda x: x[1])
            for j, _ in dists[:k]:
                adj[i].append(j)
        curvs = []
        for i in adj:
            if len(adj[i]) < 2:
                continue
            overlap = 0
            for ii in range(len(adj[i])):
                for jj in range(ii + 1, len(adj[i])):
                    if adj[i][jj] in adj.get(adj[i][ii], []):
                        overlap += 1
            tp = len(adj[i]) * (len(adj[i]) - 1) / 2
            curvs.append((overlap / max(1, tp)) - 0.5)
        return sum(curvs) / len(curvs) if curvs else 0.0


# ============================================================
# 7. Dynamical Systems Analyzer
# ============================================================

class DynamicalSystemsAnalyzer:
    @staticmethod
    def phase_space_reconstruct(data: List[float], delay: int = 3,
                                dim: int = 2) -> List[Tuple[float, ...]]:
        pts = []
        for i in range(delay * (dim - 1), len(data)):
            pts.append(tuple(data[i - delay * d] for d in range(dim - 1, -1, -1)))
        return pts

    @staticmethod
    def lyapunov_exponent(data: List[float]) -> float:
        n = len(data)
        if n < 30:
            return 0.0
        pts = DynamicalSystemsAnalyzer.phase_space_reconstruct(data, 3, 2)
        m = len(pts)
        if m < 10:
            return 0.0
        rates = []
        for i in range(1, m - 1):
            d0 = _euclidean_seq(pts[i], pts[i - 1])
            if d0 < 1e-12:
                continue
            for k in range(1, min(10, m - i)):
                d1 = _euclidean_seq(pts[i + k], pts[i - 1 + k])
                if d1 > 1e-12:
                    rates.append(math.log(d1 / d0) / k)
                    break
        return sum(rates) / len(rates) if rates else 0.0

    @staticmethod
    def oscillator_params(data: List[float]) -> Dict[str, float]:
        dx = [data[i + 1] - data[i] for i in range(len(data) - 1)]
        ddx = [dx[i + 1] - dx[i] for i in range(len(dx) - 1)]
        if len(ddx) < 10:
            return {"damping": 0.0, "frequency": 0.0, "energy": 0.0}
        x_vals = data[2:len(ddx) + 2]
        dx_list = dx[1:len(ddx) + 1]
        xv_list = list(x_vals)
        res = _multiple_regression(ddx, [dx_list, xv_list])
        if res and len(res) >= 2:
            return {
                "damping": -0.5 * res[0],
                "frequency": math.sqrt(max(0, -res[1])),
                "energy": sum(d * d for d in ddx) / len(ddx),
            }
        return {"damping": 0.0, "frequency": 0.0, "energy": 0.0}


# ============================================================
# 8. Quantum Gravity Model
# ============================================================

class QuantumGravityModel:
    def __init__(self, G: float = 1e-6) -> None:
        self._G = G
        self._levels: Dict[float, float] = {}

    def update(self, price: float, volume: float) -> Dict[str, Any]:
        if price in self._levels:
            self._levels[price] = max(self._levels[price], volume)
        else:
            self._levels[price] = volume
        if len(self._levels) > 20:
            prices = sorted(self._levels.keys())
            min_d = min(prices[i + 1] - prices[i] for i in range(len(prices) - 1))
            mi = next(i for i in range(len(prices) - 1) if prices[i + 1] - prices[i] == min_d)
            p1, p2 = prices[mi], prices[mi + 1]
            merged = (p1 + p2) / 2
            self._levels[merged] = self._levels[p1] + self._levels[p2]
            del self._levels[p1]
            del self._levels[p2]
        return self._attraction()

    def _attraction(self) -> Dict[str, Any]:
        levels = list(self._levels.items())
        if len(levels) < 2:
            return {"gravity": 0.0, "potential": 0.0}
        cur = levels[-1][0]
        force = sum(self._G * v / max(1e-10, (cur - p) ** 2)
                    for p, v in levels[:-1] if abs(cur - p) > 1e-10)
        pot = -sum(self._G * v / max(1e-10, abs(cur - p))
                   for p, v in levels[:-1])
        return {"gravity": force, "potential": pot}


# ============================================================
# 9. Holographic Memory
# ============================================================

class HolographicMemoryStore:
    def __init__(self, max_patterns: int = 200) -> None:
        self._max = max_patterns
        self._patterns: List[Dict[str, float]] = []
        self._timestamps: List[float] = []

    def store(self, p: Dict[str, float], ts: Optional[float] = None) -> None:
        if len(self._patterns) >= self._max:
            self._patterns.pop(0)
            self._timestamps.pop(0)
        self._patterns.append(p)
        self._timestamps.append(ts or time.time())

    def retrieve(self, query: Dict[str, float], top_k: int = 5,
                 threshold: float = 0.7) -> List[Tuple[float, Dict[str, float], float]]:
        scores = []
        now = time.time()
        for i, pat in enumerate(self._patterns):
            sim = _cosine_dicts(query, pat)
            if sim >= threshold:
                recency = math.exp(-abs(self._timestamps[i] - now) / 3600)
                scores.append((sim * 0.7 + recency * 0.3, pat, self._timestamps[i]))
        scores.sort(key=lambda x: -x[0])
        return scores[:top_k]

    def complete(self, partial: Dict[str, float]) -> Optional[Dict[str, float]]:
        res = self.retrieve(partial, top_k=1, threshold=0.3)
        if not res:
            return None
        _, pat, _ = res[0]
        return {**partial, **{k: v for k, v in pat.items() if k not in partial}}


class SynapticPlasticityEngine:
    def __init__(self, n: int = 5, lr: float = 0.01) -> None:
        self._n = n
        self._lr = lr
        self._w = [1.0] * n

    def update(self, pre: List[float], post: float) -> List[float]:
        if len(pre) != self._n:
            return self._w
        error = post - sum(self._w[i] * pre[i] for i in range(self._n))
        for i in range(self._n):
            self._w[i] = max(0.0, min(2.0, self._w[i] + self._lr * pre[i] * error))
        return self._w

    @property
    def weights(self) -> List[float]:
        return self._w


class PheromoneFieldTracker:
    def __init__(self, evap: float = 0.05) -> None:
        self._evap = evap
        self._ph: Dict[str, float] = defaultdict(float)

    def deposit(self, key: str, amount: float = 1.0) -> None:
        self._ph[key] += amount

    def evaporate(self) -> None:
        for k in list(self._ph):
            self._ph[k] *= (1.0 - self._evap)
            if self._ph[k] < 0.01:
                del self._ph[k]

    def strongest(self, k: int = 5) -> List[Tuple[str, float]]:
        items = sorted(self._ph.items(), key=lambda x: -x[1])
        return items[:k]


# ============================================================
# 10. Lie Symmetry Detector
# ============================================================

class LieSymmetryDetector:
    @staticmethod
    def scale_invariance(data: List[float]) -> float:
        if len(data) < 10:
            return 0.0
        m = sum(data) / len(data)
        v = _variance_f(data)
        scaled = [x * 2.0 for x in data]
        m2 = sum(scaled) / len(scaled)
        v2 = _variance_f(scaled)
        if m == 0 or v == 0:
            return 0.0
        e1 = abs(m2 / m - 2.0) / 2.0
        e2 = abs(v2 / v - 4.0) / 4.0
        return max(0.0, 1.0 - (e1 + e2) / 2.0)

    @staticmethod
    def time_reversal_symmetry(data: List[float]) -> float:
        if len(data) < 2:
            return 0.0
        return max(0.0, 1.0 - abs(_first_ac(data) - _first_ac(list(reversed(data)))))


def _first_ac(data: List[float]) -> float:
    n = len(data)
    if n < 2:
        return 0.0
    m = sum(data) / n
    v = sum((x - m) ** 2 for x in data) / n
    if v < 1e-12:
        return 0.0
    c = sum((data[i] - m) * (data[i + 1] - m) for i in range(n - 1)) / (n - 1)
    return c / v


# ============================================================
# 11. Meta-Logical Checker
# ============================================================

class MetaLogicChecker:
    @staticmethod
    def check(claims: Dict[str, Tuple[str, float]]) -> Dict[str, Any]:
        bull = sum(c for _, (cl, c) in claims.items() if cl == 'bullish')
        bear = sum(c for _, (cl, c) in claims.items() if cl == 'bearish')
        total = bull + bear
        if total == 0:
            return {"consensus": 0.0, "contradiction": 0.0}
        contradiction = 2.0 * min(bull, bear) / max(total, 1e-10)
        return {
            "consensus": max(0.0, 1.0 - contradiction),
            "contradiction": min(1.0, contradiction),
            "bullish_count": sum(1 for _, (cl, _) in claims.items() if cl == 'bullish'),
            "bearish_count": sum(1 for _, (cl, _) in claims.items() if cl == 'bearish'),
        }


# ============================================================
# Helpers
# ============================================================

def _euclidean_seq(a: Tuple, b: Tuple) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def _variance_f(values: List[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    m = sum(values) / n
    return sum((x - m) ** 2 for x in values) / n


def _cosine_dicts(a: Dict[str, float], b: Dict[str, float]) -> float:
    keys = set(a.keys()) & set(b.keys())
    if not keys:
        return 0.0
    dot = sum(a[k] * b[k] for k in keys)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na < 1e-10 or nb < 1e-10:
        return 0.0
    return dot / (na * nb)


def _multiple_regression(y: List[float], X: List[List[float]]) -> Optional[List[float]]:
    n = len(y)
    p = len(X)
    if n < p + 1:
        return None
    my = sum(y) / n
    mx = [sum(x) / n for x in X]
    if p == 2:
        y_c = [yi - my for yi in y]
        x1_c = [xi - mx[0] for xi in X[0]]
        x2_c = [xi - mx[1] for xi in X[1]]
        ss1 = sum(xi ** 2 for xi in x1_c)
        ss2 = sum(xi ** 2 for xi in x2_c)
        if ss1 < 1e-12 or ss2 < 1e-12:
            return [0.0, 0.0]
        return [sum(y_c[i] * x1_c[i] for i in range(n)) / ss1,
                sum(y_c[i] * x2_c[i] for i in range(n)) / ss2]
    return [0.0] * p
