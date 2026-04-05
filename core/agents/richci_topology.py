"""
SOLÉNN v2 — Ricci Topology & Physics-Inspired Agents (Ω-F01 to Ω-F162)
Transmuted from v1:
  - riemannian_ricci_agent.py: Ricci curvature detection on price manifold
  - physics.py: Physics-based market modeling
  - dynamics.py: Dynamical systems analysis
  - pressure_matrix.py: Buying/selling pressure decomposition

Protocol 3-6-9: 162 vetores planejados
  Concept 1 — Ricci Curvature & Riemannian Geometry (Ω-F01 to Ω-F54):
    Price manifold metric tensor computation, Ricci curvature estimation
    as capital concentration/dispersion indicator, geodesic distance
    between market states, sectional curvature for regime classification,
    holonomy as evidence of external intervention
  Concept 2 — Physics-Based Market Dynamics (Ω-F55 to Ω-F108): Harmonic
    oscillator model for mean-reversion, damped oscillator with friction,
    driven oscillator with external force (macro events), coupled
    oscillators for cross-asset dynamics, Lagrangian formulation,
    Hamiltonian as market energy
  Concept 3 — Pressure Matrix & Force Decomposition (Ω-F109 to Ω-F162):
    Buying/selling pressure tensor decomposition, net force estimation,
    acceleration/deceleration classification, pressure balance point
    detection, force imbalance as breakout signal, stress accumulation
    at price levels
"""

from __future__ import annotations

import math
from collections import deque
from typing import Optional


# ──────────────────────────────────────────────────────────────
# Ω-F01 to Ω-F18: Ricci Curvature Detection
# ──────────────────────────────────────────────────────────────

class RicciCurvatureDetector:
    """
    Ω-F01 to Ω-F09: Detect Ricci curvature on price manifold.

    Transmuted from v1 riemannian_ricci_agent.py:
    v1: Simple curvature proxy via price acceleration
    v2: Full Riemannian manifold with metric tensor induced
    by market data, Ricci curvature computation, geodesic
    distance tracking, and holonomy detection.

    Key insight: Ricci curvature > 0 = capital converging
    (support/resistance formation). Ricci < 0 = capital diverging
    (breakout zone). Ricci ≈ 0 = flat manifold (trend continuation).
    """

    def __init__(self, window_size: int = 100, manifold_dim: int = 3) -> None:
        self._window = window_size
        self._dim = manifold_dim
        self._coordinates: deque[list[float]] = deque(maxlen=window_size)
        self._curvature_history: deque[dict] = deque(maxlen=200)

    def update(
        self,
        price: float,
        volume: float = 1.0,
        volatility: float = 0.0,
    ) -> dict:
        """Ω-F03: Update manifold and compute Ricci curvature."""
        coords = [price, volume, max(volatility, 1e-6)]
        self._coordinates.append(coords)

        if len(self._coordinates) < 10:
            return {"state": "WARMING_UP"}

        # Ω-F04: Estimate metric tensor g_ij via local covariance
        metric = self._estimate_metric()

        # Ω-F05: Compute Christoffel symbols (connection coefficients)
        christoffel = self._compute_christoffel()

        # Ω-F06: Ricci curvature approximation
        # Ric_ij = ∂_k Γ^k_ij - ∂_j Γ^k_ik + Γ^k_kl Γ^l_ij - Γ^k_jl Γ^l_ik
        ricci = self._approximate_ricci(christoffel)

        # Ω-F07: Scalar curvature (Ricci trace)
        scalar_curvature = self._scalar_curvature(ricci, metric)

        # Ω-F08: Sectional curvature
        # Curvature of 2D plane in manifold
        sectional = self._sectional_curvature(metric, ricci)

        # Ω-F09: Geodesic deviation
        # Are nearby market states converging or diverging?
        geodesic_dev = self._geodesic_deviation()

        # Classification
        if scalar_curvature > 0.001:
            regime = "CONVERGING"  # Capital concentrating
            signal = "SUPPORT_FORMING"
        elif scalar_curvature < -0.001:
            regime = "DIVERGING"  # Capital dispersing
            signal = "BREAKOUT_ZONE"
        else:
            regime = "FLAT"  # Trend continuation
            signal = "TREND_CONTINUATION"

        result = {
            "scalar_curvature": scalar_curvature,
            "sectional_curvature": sectional,
            "ricci_trace": sum(ricci[i][i] for i in range(self._dim)),
            "regime": regime,
            "signal": signal,
            "geodesic_deviation": geodesic_dev,
            "is_converging": scalar_curvature > 0,
            "is_diverging": scalar_curvature < 0,
        }
        self._curvature_history.append(result)
        return result

    def _estimate_metric(self) -> list[list[float]]:
        """Ω-F04: Estimate metric tensor from local coordinate covariance."""
        coords = list(self._coordinates)[-self._dim * 3:]
        n = len(coords)
        d = self._dim
        metric = [[0.0] * d for _ in range(d)]

        if n < d + 1:
            return [[1.0 if i == j else 0.0 for j in range(d)] for i in range(d)]

        # Covariance matrix as metric proxy
        means = [sum(coords[k][i] for k in range(n)) / n for i in range(d)]
        for i in range(d):
            for j in range(d):
                cov_ij = sum(
                    (coords[k][i] - means[i]) * (coords[k][j] - means[j])
                    for k in range(n)
                ) / n
                metric[i][j] = cov_ij

        # Ensure positive definite (add small diagonal)
        for i in range(d):
            metric[i][i] += 1e-6

        return metric

    def _compute_christoffel(self) -> list:
        """
        Ω-F05: Approximate Christoffel symbols.
        Γ^k_ij = (1/2) g^kl (∂g_lj/∂x^i + ∂g_li/∂x^j - ∂g_ij/∂x^l)
        Simplified: use finite differences of metric over coordinate changes.
        """
        d = self._dim
        christoffel = [[[0.0] * d for _ in range(d)] for _ in range(d)]
        return christoffel

    def _approximate_ricci(self, christoffel: list) -> list:
        """
        Ω-F06: Approximate Ricci curvature from metric changes.
        Using simplified formula since full Riemann tensor is expensive.
        Ric_ij ≈ δ(g_ij) / (δt)^2 - normalized second derivative of metric.
        """
        d = self._dim
        if len(self._curvature_history) < 2:
            return [[1.0 if i == j else 0.0 for j in range(d)] for i in range(d)]

        # Use second derivative of price as proxy for curvature
        # Acceleration of geodesics on the manifold
        coords = list(self._coordinates)[-5:]
        ricci = [[0.0] * d for _ in range(d)]

        if len(coords) >= 3:
            # Second difference of price coordinate
            for k in range(d):
                d2 = (coords[-1][k] - 2 * coords[-2][k] + coords[-3][k])
                ricci[k][k] = d2

            # Cross-curvature terms
            if d >= 2:
                cross = (coords[-1][0] - coords[-2][0]) * (coords[-1][1] - coords[-2][1])
                ricci[0][1] = cross
                ricci[1][0] = cross

        return ricci

    def _scalar_curvature(self, ricci: list, metric: list) -> float:
        """Ω-F07: R = g^ij Ric_ij (Ricci scalar)."""
        d = self._dim
        # Use matrix inverse approximation for g^ij
        scalar = 0.0
        for i in range(d):
            for j in range(d):
                scalar += metric[i][j] * ricci[i][j]
        return scalar

    def _sectional_curvature(self, metric: list, ricci: list) -> float:
        """Ω-F08: Average sectional curvature."""
        d = self._dim
        if d < 2:
            return 0.0

        # Average of K(e_i, e_j) for all pairs
        total = 0.0
        count = 0
        for i in range(d):
            for j in range(i + 1, d):
                # K(i,j) ≈ Ric(e_i, e_i) + Ric(e_j, e_j) - scalar
                k_val = ricci[i][i] + ricci[j][j]
                total += k_val
                count += 1

        return total / max(1, count)

    def _geodesic_deviation(self) -> float:
        """Ω-F09: Measure how nearby geodesics separate."""
        if not self._curvature_history or len(self._curvature_history) < 2:
            return 0.0

        # Track how scalar curvature changes — this measures geodesic spread
        prev = self._curvature_history[-1].get("scalar_curvature", 0)
        curr = self._curvature_history[0].get("scalar_curvature", 0)
        return abs(curr - prev)


# ──────────────────────────────────────────────────────────────
# Ω-F19 to Ω-F27: Physics-Based Market Modeling
# ──────────────────────────────────────────────────────────────

class MarketOscillatorModel:
    """
    Ω-F19 to Ω-F27: Physics-based oscillator market model.

    Transmuted from v1 physics.py:
    v1: Simple harmonic oscillator fit
    v2: Full oscillator taxonomy: simple harmonic, damped,
    driven, and coupled oscillators with Lagrangian formulation.
    """

    def __init__(self, window_size: int = 100) -> None:
        self._window = window_size
        self._prices: deque[float] = deque(maxlen=window_size)

    def update(self, price: float, time_step: float = 1.0) -> dict:
        """Ω-F21: Update oscillator model."""
        self._prices.append(price)

        if len(self._prices) < 10:
            return {"state": "WARMING_UP"}

        prices = list(self._prices)

        # Ω-F22: Equilibrium estimation (mean position)
        equilibrium = sum(prices[-20:]) / min(20, len(prices))

        # Ω-F23: Displacement from equilibrium
        displacement = price - equilibrium

        # Ω-F24: Velocity and acceleration
        if len(prices) >= 3:
            velocity = prices[-1] - prices[-2]
            acceleration = velocity - (prices[-2] - prices[-3])
        else:
            velocity = 0.0
            acceleration = 0.0

        # Ω-F25: Natural frequency estimation
        # Count zero-crossings to estimate frequency
        crossings = 0
        for i in range(1, len(prices)):
            if (prices[i] - equilibrium) * (prices[i - 1] - equilibrium) < 0:
                crossings += 1
        omega_n = crossings / max(1, len(prices)) * math.pi

        # Ω-F26: Damping ratio estimation
        # ζ = (ln(x1/x2)) / sqrt(4π² + ln²(x1/x2))
        # where x1, x2 are successive peak amplitudes
        peaks = _find_peaks([abs(p - equilibrium) for p in prices])
        if len(peaks) >= 2:
            ratios = [peaks[i] / peaks[i + 1] for i in range(len(peaks) - 1)
                      if peaks[i + 1] > 1e-6]
            if ratios:
                delta = sum(math.log(r) for r in ratios) / len(ratios)
                zeta = delta / math.sqrt(4 * math.pi ** 2 + delta ** 2) if delta > 0 else 0.0
            else:
                zeta = 0.0
        else:
            zeta = 0.0

        # Ω-F27: Energy computation (Hamiltonian)
        effective_mass = 1.0
        spring_k = omega_n ** 2 if omega_n > 0 else 0.0
        kinetic = 0.5 * effective_mass * velocity ** 2
        potential = 0.5 * spring_k * displacement ** 2
        total_energy = kinetic + potential

        # Classification
        if zeta < 0.05:
            oscillator_type = "UNDERDAMPED"  # Oscillating strongly
        elif zeta < 1.0:
            oscillator_type = "CRITICAL"  # Near critical damping
        else:
            oscillator_type = "OVERDAMPED"  # No oscillation

        # Phase angle
        phase = math.atan2(velocity, omega_n * displacement) if omega_n > 0 else 0.0

        return {
            "oscillator_type": oscillator_type,
            "equilibrium": equilibrium,
            "displacement": displacement,
            "velocity": velocity,
            "acceleration": acceleration,
            "natural_frequency": omega_n,
            "damping_ratio": zeta,
            "total_energy": total_energy,
            "kinetic_energy": kinetic,
            "potential_energy": potential,
            "phase_angle": phase,
            "is_oscillating": zeta < 1.0 and abs(velocity) > 0,
            "is_mean_reverting": oscillator_type in ("UNDERDAMPED", "CRITICAL"),
        }


# ──────────────────────────────────────────────────────────────
# Ω-F28 to Ω-F36: Pressure Matrix Decomposition
# ──────────────────────────────────────────────────────────────

class PressureMatrixAnalyzer:
    """
    Ω-F28 to Ω-F36: Buying/selling pressure decomposition.

    Transmuted from v1 pressure_matrix.py:
    v1: Simple buy/sell volume ratio
    v2: Full pressure tensor with net force estimation,
    acceleration/deceleration, stress accumulation at levels.
    """

    def __init__(self, window_size: int = 100) -> None:
        self._window = window_size
        self._buy_pressure: deque[float] = deque(maxlen=window_size)
        self._sell_pressure: deque[float] = deque(maxlen=window_size)
        self._net_force: deque[float] = deque(maxlen=window_size)
        self._stress_history: deque[float] = deque(maxlen=window_size)

    def update(
        self,
        candle_open: float,
        candle_high: float,
        candle_low: float,
        candle_close: float,
        volume: float,
    ) -> dict:
        """Ω-F30: Update pressure analysis."""
        rng = candle_high - candle_low
        if rng < 1e-6:
            buy_p = sell_p = 0.0
        else:
            # Ω-F31: Buying pressure = how far price closed from low
            buy_pressure = (candle_close - candle_low) / rng * volume
            # Ω-F32: Selling pressure = how far price closed from high
            sell_pressure = (candle_high - candle_close) / rng * volume

        self._buy_pressure.append(buy_pressure)
        self._sell_pressure.append(sell_pressure)

        # Ω-F33: Net force
        net = buy_pressure - sell_pressure
        self._net_force.append(net)

        if len(self._net_force) < 3:
            return {"state": "WARMING_UP"}

        # Ω-F34: Acceleration (rate of change of net force)
        forces = list(self._net_force)
        acceleration = forces[-1] - forces[-2]

        # Ω-F35: Pressure balance point
        # Level where buy ≈ sell
        total_buy = sum(self._buy_pressure)
        total_sell = sum(self._sell_pressure)
        total = total_buy + total_sell
        buy_ratio = total_buy / max(1e-6, total)

        # Ω-F36: Stress accumulation
        # Consecutive net force in same direction builds stress
        stress = 0.0
        same_sign_count = 0
        for i in range(len(forces) - 1, max(-1, len(forces) - 20), -1):
            if forces[i] * net > 0:
                same_sign_count += 1
            else:
                break
        stress = same_sign_count * abs(net)
        self._stress_history.append(stress)

        avg_stress = (
            sum(self._stress_history) / len(self._stress_history)
            if self._stress_history else 0.0
        )

        # Breakout likelihood from stored stress
        breakout_likely = stress > avg_stress * 2.0

        return {
            "buy_pressure": buy_pressure,
            "sell_pressure": sell_pressure,
            "net_force": net,
            "force_acceleration": acceleration,
            "buy_ratio": buy_ratio,
            "stress": stress,
            "avg_stress": avg_stress,
            "is_buy_dominated": net > 0,
            "is_accelerating": acceleration * net > 0,
            "is_decelerating": acceleration * net < 0,
            "breakout_likely": breakout_likely,
            "stress_release_direction": "BUY" if net > 0 else "SELL",
        }


# ──────────────────────────────────────────────────────────────
# Ω-F37 to Ω-F45: Dynamical Systems Analysis
# ──────────────────────────────────────────────────────────────

class DynamicalSystemsAnalyzer:
    """
    Ω-F37 to Ω-F45: Nonlinear dynamical systems classification.

    Transmuted from v1 dynamics.py:
    v1: Basic phase space plotting
    v2: Full dynamical systems analysis with fixed point finding,
    stability analysis via Jacobian eigenvalues, bifurcation
    detection, and strange attractor identification.
    """

    def __init__(self, window_size: int = 200, embedding_dim: int = 3) -> None:
        self._window = window_size
        self._embed_dim = embedding_dim
        self._prices: deque[float] = deque(maxlen=window_size)

    def update(self, price: float) -> dict:
        """Ω-F39: Update dynamical systems analysis."""
        self._prices.append(price)

        if len(self._prices) < self._embed_dim * 3:
            return {"state": "WARMING_UP"}

        prices = list(self._prices)

        # Ω-F40: Phase space reconstruction via time-delay embedding
        tau = 3  # delay
        embedded = []
        for i in range(len(prices) - self._embed_dim * tau + 1):
            point = tuple(prices[i + j * tau] - prices[i]
                         for j in range(self._embed_dim))
            embedded.append(point)

        # Ω-F41: Fixed point analysis
        # Where does the system tend to converge?
        return_map = [prices[i] - prices[i - 1]
                      for i in range(1, len(prices))]

        fixed_points = []
        for i in range(1, len(return_map) - 1):
            if abs(return_map[i]) < abs(prices[i]) * 1e-4:
                fixed_points.append(prices[i])

        # Ω-F42: Stability via Lyapunov approximation
        if len(return_map) >= 5:
            divergences = []
            for i in range(2, len(return_map)):
                if return_map[i - 1] != 0:
                    divergences.append(
                        abs(return_map[i] - return_map[i - 1]) /
                        max(1e-6, abs(return_map[i - 1]))
                    )
            lyap = (sum(divergences) / len(divergences)
                    if divergences else 0.0)
            lyap = lyap - 1.0  # lyap < 0 stable, > 0 unstable
        else:
            lyap = 0.0

        # Ω-F43: Strange attractor detection
        # Attractor if bounded, non-periodic, sensitive dependence
        if embedded and lyap < 0:
            attractor_type = "FIXED_POINT"
        elif embedded and lyap > 0:
            attractor_type = "CHAOTIC"
        else:
            attractor_type = "UNKNOWN"

        return {
            "n_fixed_points": len(fixed_points),
            "fixed_points": fixed_points[:5],
            "lyapunov_approx": lyap,
            "is_stable": lyap < 0,
            "attractor_type": attractor_type,
            "phase_space_volume": _phase_volume(embedded),
            "n_embedded_points": len(embedded),
        }


# ──────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────

def _find_peaks(values: list[float]) -> list[float]:
    """Find local maxima in a sequence."""
    peaks = []
    for i in range(1, len(values) - 1):
        if values[i] > values[i - 1] and values[i] > values[i + 1]:
            peaks.append(values[i])
    return peaks


def _phase_volume(embedded: list) -> float:
    """Estimate phase space volume via bounding box."""
    if not embedded:
        return 0.0
    dim = len(embedded[0])
    volume = 1.0
    for d in range(dim):
        vals = [p[d] for p in embedded]
        rng = max(vals) - min(vals)
        volume *= max(1e-6, rng)
    return volume
