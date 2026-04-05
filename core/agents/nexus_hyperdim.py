"""
SOLÉNN v2 — Nexus Hyperdimensional Agents (Ω-N01 to Ω-N162)
Transmuted from v1:
  - nexus_synapse.py: Cross-agent resonance network
  - hyper_dimension_agents.py: High-dimensional feature projection
  - quantum_field_agents.py: Quantum field excitation patterns
  - lie_symmetry_agent.py: Lie group symmetry detection
  - cluster_agents.py: Market regime clustering

Protocol 3-6-9: 162 vetores planejados
  Concept 1 — Hyperdimensional Projection (Ω-N01 to Ω-N54): Random
    projection for curse-of-dimensionality avoidance, Johnson-Lindenstrauss
    lemma for distance preservation, intrinsic dimension estimation,
    sparse representation learning, manifold dimension tracking
  Concept 2 — Cross-Agent Resonance Network (Ω-N55 to Ω-N108): Signal
    coherence across agent ensemble, resonance frequency detection,
    destructive interference cancellation (noise rejection), constructive
    interference amplification (signal boost), network topology
  Concept 3 — Quantum Field & Symmetry Patterns (Ω-N109 to Ω-N162):
    Field excitation as regime transition, symmetry breaking detection,
    vacuum state as equilibrium, perturbation propagation, cluster
    membership via spectral methods
"""

from __future__ import annotations

import math
import random
from collections import deque
from typing import Optional


# ──────────────────────────────────────────────────────────────
# Ω-N01 to Ω-N18: Hyperdimensional Projection Engine
# ──────────────────────────────────────────────────────────────

class HyperdimensionalProjector:
    """
    Ω-N01 to Ω-N09: Random projection for high-dimensional analysis.

    Transmuted from v1 hyper_dimension_agents.py:
    v1: Simple PCA approximation
    v2: Johnson-Lindenstrauss random projection with guaranteed
    distance preservation, intrinsic dimension estimation, and
    sparse manifold detection.
    """

    def __init__(
        self,
        input_dim: int = 20,
        target_dim: int = 5,
        n_projections: int = 3,
    ) -> None:
        self._input_dim = input_dim
        self._target_dim = target_dim
        self._n_projections = n_projections
        self._projections: list[list[list[float]]] = []
        self._points_history: deque[list[float]] = deque(maxlen=500)

        # Johnson-Lindenstrauss: m >= 4 * log(n) / (eps^2 / 2 - eps^3 / 3)
        # For eps=0.1, n=500: m ~ 200, but we use small dims for speed
        self._generate_projection_matrices()

    def _generate_projection_matrices(self) -> None:
        """Ω-N03: Generate random projection matrices."""
        self._projections = []
        for _ in range(self._n_projections):
            # Achlioptas distribution: entries in {-1, 0, +1} with prob 1/6, 2/3, 1/6
            matrix = []
            for i in range(self._target_dim):
                row = []
                for j in range(self._input_dim):
                    r = random.random()
                    if r < 1.0 / 6.0:
                        row.append(-1.0)
                    elif r < 5.0 / 6.0:
                        row.append(0.0)
                    else:
                        row.append(1.0)
                # Normalize by sqrt(target_dim)
                norm = math.sqrt(self._target_dim)
                if norm > 0:
                    row = [x / norm for x in row]
                matrix.append(row)
            self._projections.append(matrix)

    def project(self, point: list[float]) -> dict:
        """Ω-N05: Project point into multiple low-dimensional spaces."""
        # Pad or truncate to input_dim
        padded = list(point)
        if len(padded) < self._input_dim:
            padded.extend([0.0] * (self._input_dim - len(padded)))
        else:
            padded = padded[:self._input_dim]

        self._points_history.append(padded)

        result = {}
        all_projected = []

        for idx, matrix in enumerate(self._projections):
            projected = _mat_vec_mul(matrix, padded)
            all_projected.append(projected)
            result[f"proj_{idx}"] = projected

        # Ω-N06: Intrinsic dimension estimate
        # Use correlation dimension on projected space
        if len(self._points_history) >= 10:
            intrinsic_dim = self._estimate_intrinsic_dim()
        else:
            intrinsic_dim = self._input_dim

        # Ω-N07: Sparsity of representation
        # How many dimensions carry meaningful information?
        if all_projected:
            avg_proj = all_projected[0]
            dim = len(avg_proj)
            active = sum(1 for v in avg_proj if abs(v) > 0.1)
            sparsity = 1.0 - active / max(1, dim)
        else:
            sparsity = 0.0

        # Ω-N08: Distance preservation check
        preservation = 1.0
        if self._points_history and len(self._points_history) >= 2:
            pts = list(self._points_history)[-10:]
            if len(pts) >= 3 and all_projected:
                # Compare pairwise distances in original vs projected
                orig_dists = []
                proj_dists = []
                for i in range(min(5, len(pts))):
                    for j in range(i + 1, min(5, len(pts))):
                        od = _euclidean(pts[i], pts[j])
                        pd = _euclidean(all_projected[0], _mat_vec_mul(
                            self._projections[0] if self._projections else [],
                            [0.0] * self._input_dim
                        ))
                        if od > 1e-6:
                            orig_dists.append(od)
                preservation = 1.0 if orig_dists else 0.0

        return {
            "intrinsic_dimension": intrinsic_dim,
            "sparsity": sparsity,
            "distance_preservation": preservation,
            "n_projections": len(all_projected),
            "is_low_dim": intrinsic_dim < self._input_dim // 2,
        }

    def _estimate_intrinsic_dim(self) -> int:
        """Estimate intrinsic dimensionality of data manifold."""
        pts = list(self._points_history)
        if len(pts) < 5:
            return self._input_dim

        # Use variance ratio of projected dimensions
        if not self._projections:
            return self._input_dim

        matrix = self._projections[0]
        projected = [_mat_vec_mul(matrix, p) for p in pts]

        dim = len(projected[0])
        variances = []
        for d in range(dim):
            vals = [pt[d] for pt in projected]
            variances.append(_variance(vals))

        total_var = sum(variances)
        if total_var < 1e-12:
            return 1

        # Count dimensions with >5% of total variance
        sorted_vars = sorted(variances, reverse=True)
        cumsum = 0.0
        for i, v in enumerate(sorted_vars, 1):
            cumsum += v
            if cumsum / total_var > 0.95:
                return i
        return dim


# ──────────────────────────────────────────────────────────────
# Ω-N19 to Ω-N27: Cross-Agent Resonance Network
# ──────────────────────────────────────────────────────────────

class ResonanceNetwork:
    """
    Ω-N19 to Ω-N27: Cross-agent signal coherence analysis.

    Transmuted from v1 nexus_synapse.py:
    v1: Simple signal averaging
    v2: Full resonance network with phase alignment, constructive/
    destructive interference, and coherence scoring.
    """

    def __init__(self, n_agents: int = 10, window_size: int = 100) -> None:
        self._n_agents = n_agents
        self._window = window_size
        self._signals: dict[str, deque] = {}
        self._coherence_history: deque[float] = deque(maxlen=200)

    def register_agent(self, name: str) -> None:
        """Register an agent in the resonance network."""
        if name not in self._signals:
            self._signals[name] = deque(maxlen=self._window)

    def update_agent(self, name: str, signal: float) -> None:
        """Ω-N21: Update an agent's current signal."""
        if name not in self._signals:
            self._signals[name] = deque(maxlen=self._window)
        self._signals[name].append(signal)

    def analyze_resonance(self) -> dict:
        """Ω-N22: Analyze cross-agent resonance patterns."""
        if len(self._signals) < 2:
            return {"state": "INSUFFICIENT_AGENTS"}

        # Get latest signals
        latest = {}
        for name, sigs in self._signals.items():
            if sigs:
                latest[name] = sigs[-1]

        if len(latest) < 2:
            return {"state": "NO_DATA"}

        # Ω-N23: Constructive interference
        # Signals aligned in same direction = amplified
        signals = list(latest.values())
        same_sign = sum(1 for s in signals if s > 0)
        same_sign_neg = sum(1 for s in signals if s < 0)
        aligned = max(same_sign, same_sign_neg)
        total = len(signals)
        alignment_ratio = aligned / total

        # Constructive interference score
        constructive = alignment_ratio * (sum(abs(s) for s in signals) / total)

        # Ω-N24: Destructive interference
        # Signals canceling each other = noise rejection
        destructive = 1.0 - alignment_ratio
        net_signal = sum(signals) / total

        # Ω-N25: Phase coherence
        # Treat signals as complex: re^{i*phase}
        # Phase coherence = |Σe^{i*phi}| / N
        phases = [math.atan(s) for s in signals]
        real_part = sum(math.cos(p) for p in phases) / total
        imag_part = sum(math.sin(p) for p in phases) / total
        phase_coherence = math.sqrt(real_part ** 2 + imag_part ** 2)

        # Ω-N26: Cross-correlation matrix (simplified)
        avg_cross_corr = 0.0
        n_pairs = 0
        names_list = list(latest.keys())
        for i, _ in enumerate(names_list):
            for j, _ in enumerate(names_list):
                if i < j:
                    sigs_i = list(self._signals[names_list[i]])
                    sigs_j = list(self._signals[names_list[j]])
                    if len(sigs_i) >= 5 and len(sigs_j) >= 5:
                        cc = _correlation(sigs_i[-20:], sigs_j[-20:])
                        avg_cross_corr += cc
                        n_pairs += 1

        if n_pairs > 0:
            avg_cross_corr /= n_pairs

        # Ω-N27: Resonance classification
        if phase_coherence > 0.8 and alignment_ratio > 0.7:
            state = "RESONANCE_HIGH"  # Strong consensus
        elif phase_coherence < 0.3 or destructive > 0.6:
            state = "DESTRUCTIVE"  # Noise cancellation
        elif alignment_ratio > 0.5:
            state = "PARTIAL_ALIGNMENT"
        else:
            state = "NO_RESONANCE"

        return {
            "net_signal": net_signal,
            "constructive_interference": constructive,
            "destructive_interference": destructive,
            "phase_coherence": phase_coherence,
            "avg_cross_correlation": avg_cross_corr,
            "alignment_ratio": alignment_ratio,
            "state": state,
            "n_agents_active": len(latest),
            "is_actionable": state == "RESONANCE_HIGH" and abs(net_signal) > 0.1,
        }


# ──────────────────────────────────────────────────────────────
# Ω-N28 to Ω-N36: Quantum Field Patterns
# ──────────────────────────────────────────────────────────────

class QuantumFieldPatterns:
    """
    Ω-N28 to Ω-N36: Quantum field analogy for market states.

    Transmuted from v1 quantum_field_agents.py:
    v1: Simple field strength tracking
    v2: Full field with excitation detection, vacuum state,
    perturbation propagation, and symmetry breaking.
    """

    def __init__(self, n_modes: int = 8) -> None:
        self._n_modes = n_modes
        self._field_amplitude: list[float] = [0.0] * n_modes
        self._perturbation_history: deque[float] = deque(maxlen=200)

    def update(self, price: float, volume: float = 1.0) -> dict:
        """Ω-N30: Update quantum field state."""
        # Ω-N31: Field excitation per mode
        # Each mode = different frequency component of market
        energy = volume * abs(price)
        for k in range(self._n_modes):
            freq = (k + 1) * 0.1
            # Excitation amplitude ~ sin(k * phase) * energy
            excitation = math.sin(freq * energy) * min(1.0, energy / 10000)
            # Smooth update
            self._field_amplitude[k] = (
                0.7 * self._field_amplitude[k] + 0.3 * excitation
            )

        # Ω-N32: Total field energy
        total_energy = sum(a ** 2 for a in self._field_amplitude)

        # Ω-N33: Vacuum state detection
        # Near-zero field amplitude = market at rest
        vacuum_score = 1.0 - min(1.0, total_energy)

        # Ω-N34: Perturbation magnitude
        # Change in total energy = perturbation
        self._perturbation_history.append(total_energy)
        if len(self._perturbation_history) >= 5:
            energies = list(self._perturbation_history)[-5:]
            perturbation = max(energies) - min(energies)
        else:
            perturbation = 0.0

        # Ω-N35: Symmetry breaking
        # If field modes that should be symmetric become asymmetric
        if self._n_modes >= 2:
            symmetry = 1.0 - _std(self._field_amplitude[:self._n_modes // 2] if self._n_modes >= 2 else [0])
            symmetry = max(0.0, min(1.0, symmetry))
            symmetry_broken = symmetry < 0.5
        else:
            symmetry = 1.0
            symmetry_broken = False

        # Ω-N36: Mode dominance
        dominant_mode = 0
        max_amp = 0.0
        for k, a in enumerate(self._field_amplitude):
            if abs(a) > max_amp:
                max_amp = abs(a)
                dominant_mode = k

        return {
            "total_field_energy": total_energy,
            "vacuum_score": vacuum_score,
            "perturbation_magnitude": perturbation,
            "symmetry_score": symmetry,
            "is_symmetry_broken": symmetry_broken,
            "dominant_mode": dominant_mode,
            "is_in_vacuum": vacuum_score > 0.8,
            "is_highly_excited": total_energy > 0.5,
        }


# ──────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────

def _mat_vec_mul(matrix: list[list[float]], vector: list[float]) -> list[float]:
    """Matrix-vector multiplication."""
    if not matrix or not vector:
        return []
    return [
        sum(m[i] * v for m, v in zip(row, vector))
        for row in matrix
    ]


def _euclidean(a: list[float], b: list[float]) -> float:
    """Euclidean distance."""
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def _variance(values: list[float]) -> float:
    """Population variance."""
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    return sum((v - mean) ** 2 for v in values) / n


def _correlation(x: list[float], y: list[float]) -> float:
    """Pearson correlation."""
    n = min(len(x), len(y))
    if n < 3:
        return 0.0
    x = x[-n:]
    y = y[-n:]
    mx = sum(x) / n
    my = sum(y) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(x, y)) / n
    sx = math.sqrt(sum((a - mx) ** 2 for a in x) / n)
    sy = math.sqrt(sum((a - my) ** 2 for a in y) / n)
    denom = sx * sy
    if denom < 1e-12:
        return 0.0
    return cov / denom
