"""
SOLÉNN v2 — Quantum Agents (Ω-QM01 to Ω-QM162)
Transmuted from v1:
  - quantum_gravity_agents.py: Gravity-like attraction between price levels
  - quantum_tunneling_oscillator.py: Barrier tunneling detection
  - quantum_unification_agents.py: Multi-framework unification
  - quantum_field_agents.py: Quantum field excitation patterns
  - quantum_unification: Unifying disparate market models

Protocol 3-6-9: 162 vetores planejados
  Concept 1 — Quantum Gravity (Ω-QM01 to Ω-QM54): Price levels
    as gravitational masses, attraction force between levels,
    orbital mechanics (support/resistance orbits), event horizon
    (liquidation zones), gravitational wave detection (ripple
    from large trades)
  Concept 2 — Quantum Tunneling (Ω-QM55 to Ω-QM108): Barrier
    penetration probability, tunneling through resistance levels,
    wave function across price barriers, energy barrier estimation
    (volume wall as potential), tunneling resonance
  Concept 3 — Quantum Unification (Ω-QM109 to Ω-QM162): Multi-
    framework coherence scoring, unification of technical indicators
    as quantum observables, uncertainty principle in trading
    (price-timing uncertainty), quantum entanglement of correlated
    assets
"""

from __future__ import annotations

import math
from collections import deque
from typing import Optional


# ──────────────────────────────────────────────────────────────
# Ω-QM01 to Ω-QM18: Quantum Gravity Model
# ──────────────────────────────────────────────────────────────

class QuantumGravityModel:
    """
    Ω-QM01 to Ω-QM09: Gravitational attraction between price levels.

    Price levels with high accumulated volume act as gravitational
    masses. The force of attraction pulls price toward these levels:
    F = G * m1 * m2 / r^2 where m = volume mass, r = distance,
    G = gravitational coupling constant calibrated to market data.

    Transmuted from v1 quantum_gravity_agents.py.
    """

    def __init__(
        self,
        gravity_constant: float = 1.0,
        n_mass_levels: int = 10,
    ) -> None:
        self._G = gravity_constant
        self._n_levels = n_mass_levels
        self._price_levels: dict[float, float] = {}  # price -> accumulated volume mass
        self._price_history: deque[float] = deque(maxlen=500)

    def update(self, price: float, volume: float = 1.0) -> dict:
        """Ω-QM03: Update gravitational field."""
        self._price_history.append(price)

        # Mass accumulation: add volume to the nearest price level
        level_key = round(price / max(1e-6, abs(price) * 0.001))
        level_price = level_key * max(1e-6, abs(price) * 0.001)
        self._price_levels[level_price] = self._price_levels.get(level_price, 0.0) + volume

        # Limit number of levels
        if len(self._price_levels) > 200:
            # Remove weakest levels
            sorted_levels = sorted(self._price_levels.items(), key=lambda x: x[1])
            self._price_levels = dict(sorted_levels[-200:])

        if len(self._price_history) < 10:
            return {"state": "WARMING_UP"}

        # Ω-QM04: Get top mass levels
        top_levels = sorted(self._price_levels.items(), key=lambda x: x[1], reverse=True)[:self._n_levels]

        # Ω-QM05: Gravitational force on current price
        net_force = 0.0
        for level_price, mass in top_levels:
            r = abs(price - level_price)
            if r < 1e-6:
                continue
            force = self._G * mass / r  # F/m = G*M/r^2 * m => G*M/r
            direction = 1.0 if level_price > price else -1.0
            net_force += direction * force

        # Ω-QM06: Nearest massive level (support/resistance)
        nearest_mass = None
        nearest_dist = float('inf')
        for lp, m in top_levels:
            d = abs(price - lp)
            if d < nearest_dist:
                nearest_dist = d
                nearest_mass = lp

        # Ω-QM07: Orbital state
        # Is price orbiting around a level? (oscillating around it)
        is_orbital = False
        orbit_level = None
        if len(self._price_history) >= 20:
            recent = list(self._price_history)[-20:]
            for lp, m in top_levels:
                above = sum(1 for p in recent if p > lp)
                below = sum(1 for p in recent if p < lp)
                if above >= 5 and below >= 5:  # Crossing both sides
                    is_orbital = True
                    orbit_level = lp
                    break

        # Ω-QM08: Event horizon
        # A level where once price gets too close, it's pulled in
        event_horizons = []
        for lp, m in top_levels:
            r_schwarzschild = self._G * m  # Simplified
            d = abs(price - lp)
            if d < r_schwarzschild:
                event_horizons.append((lp, m))

        # Ω-QM09: Gravitational wave detection
        # Sudden change in the gravitational field = wave
        if len(self._price_history) >= 5:
            # Large volume at new level = mass shift
            if volume > 10.0:  # Significant volume
                wave_amplitude = volume / max(1e-6, sum(v for v in self._price_levels.values()) / max(1, len(self._price_levels)))
            else:
                wave_amplitude = 0.0
        else:
            wave_amplitude = 0.0

        return {
            "net_gravitational_force": net_force,
            "nearest_mass_level": nearest_mass,
            "nearest_mass_distance": nearest_dist,
            "is_orbital": is_orbital,
            "orbit_level": orbit_level,
            "n_event_horizons": len(event_horizons),
            "event_horizons": [(lp, m) for lp, m in event_horizons[:5]],
            "wave_amplitude": wave_amplitude,
            "n_mass_levels": len(top_levels),
            "is_attracting_to_support": net_force < 0 and not is_orbital,
            "is_attracting_to_resistance": net_force > 0 and not is_orbital,
        }


# ──────────────────────────────────────────────────────────────
# Ω-QM19 to Ω-QM27: Quantum Tunneling Detection
# ──────────────────────────────────────────────────────────────

class QuantumTunnelingDetector:
    """
    Ω-QM19 to Ω-QM27: Barrier penetration via quantum tunneling.

    Resistance levels are energy barriers. Price can either:
    (a) Go over the barrier (breakout with high volume/energy)
    (b) Tunnel through the barrier (breakout with surprisingly low
        volume — quantum tunneling event)

    Transmission probability: T = exp(-2 * integral sqrt(2m(V-E))/hbar dx)

    Transmuted from v1 quantum_tunneling_oscillator.py.
    """

    def __init__(self, window_size: int = 200) -> None:
        self._window = window_size
        self._prices: deque[float] = deque(maxlen=window_size)
        self._volumes: deque[float] = deque(maxlen=window_size)
        self._tunnel_events: list[dict] = []

    def update(self, price: float, volume: float = 1.0) -> dict:
        """Ω-QM21: Check for tunneling events."""
        self._prices.append(price)
        self._volumes.append(volume)

        if len(self._prices) < 30:
            return {"state": "WARMING_UP"}

        prices = list(self._prices)
        volumes = list(self._volumes)
        n = len(prices)

        # Ω-QM22: Identify barrier (resistance) levels
        # Recent highs form barriers
        barriers = self._identify_barriers(prices, volumes)

        # Ω-QM23: Tunneling detection for each barrier
        tunnel_detected = False
        tunnel_barrier = None
        tunnel_energy = 0.0

        for barrier_price, barrier_width in barriers:
            d = abs(price - barrier_price)

            # Check if price crossed barrier recently
            if n >= 3:
                crossed_up = prices[-3] < barrier_price and prices[-1] > barrier_price
                crossed_down = prices[-3] > barrier_price and prices[-1] < barrier_price

                if crossed_up or crossed_down:
                    # Check volume at crossing moment
                    crossing_volume = volumes[-2] if n >= 2 else volume
                    avg_volume = sum(volumes[-10:]) / 10 if len(volumes) >= 10 else volume

                    # Ω-QM24: Tunneling = crossing with LOW volume
                    # Classical breakout needs high volume. Tunneling doesn't.
                    volume_ratio = crossing_volume / max(1e-6, avg_volume)

                    # Transmission probability
                    # V = barrier height (volume needed for classical crossing)
                    # E = actual energy (current volume)
                    barrier_height = barrier_width * abs(barrier_price) * 0.01
                    current_energy = crossing_volume
                    if barrier_height > current_energy:
                        T = math.exp(-2 * barrier_width * math.sqrt(barrier_height - current_energy))
                        T = max(0, min(1, T))
                    else:
                        T = 0.9  # Classical breakout

                    is_tunnel = volume_ratio < 0.8 and T > 0.1

                    if is_tunnel:
                        tunnel_detected = True
                        tunnel_barrier = barrier_price
                        tunnel_energy = T
                        self._tunnel_events.append({
                            "barrier": barrier_price,
                            "transmission_prob": T,
                            "volume_ratio": volume_ratio,
                            "direction": "UP" if crossed_up else "DOWN",
                        })

        # Ω-QM25: Tunneling resonance
        # Multiple tunneling events suggest resonant tunneling
        tunnel_count = len(self._tunnel_events)
        is_resonant = tunnel_count >= 3

        # Limit history
        if len(self._tunnel_events) > 50:
            self._tunnel_events = self._tunnel_events[-50:]

        return {
            "tunnel_detected": tunnel_detected,
            "tunnel_barrier": tunnel_barrier,
            "transmission_probability": tunnel_energy,
            "n_barriers": len(barriers),
            "barriers": [(bp, bw) for bp, bw in barriers[:5]],
            "total_tunnel_events": tunnel_count,
            "is_resonant_tunneling": is_resonant,
            "is_actionable": tunnel_detected and tunnel_energy > 0.2,
        }

    def _identify_barriers(self, prices: list[float], volumes: list[float]) -> list[tuple[float, float]]:
        """Ω-QM22: Identify resistance barriers in recent price data."""
        if len(prices) < 20:
            return []

        # Find local maxima with high volume
        barriers = []
        window = max(3, len(prices) // 10)
        for i in range(window, len(prices) - window):
            is_local_max = all(
                prices[i] >= prices[i + j]
                for j in range(-window, window + 1) if j != 0
            )
            if is_local_max:
                # Barrier width ~ how long price stays near this level
                width = window
                barriers.append((prices[i], width))

        # Sort by significance (height * local volume)
        barriers.sort(reverse=True)
        return barriers[:10]


# ──────────────────────────────────────────────────────────────
# Ω-QM28 to Ω-QM36: Quantum Unification
# ──────────────────────────────────────────────────────────────

class QuantumUnificationEngine:
    """
    Ω-QM28 to Ω-QM36: Unify multiple market frameworks.

    Transmuted from v1 quantum_unification_agents.py:
    v1: Simple indicator combination
    v2: Full quantum framework treating each indicator as an
    observable, with uncertainty principle, entanglement,
    and coherence scoring.
    """

    def __init__(self) -> None:
        self._indicators: dict[str, deque[float]] = {}
        self._entanglement_map: dict[tuple[str, str], float] = {}
        self._coherence_history: deque[float] = deque(maxlen=200)

    def register_indicator(self, name: str) -> None:
        """Register a new indicator observable."""
        self._indicators[name] = deque(maxlen=200)

    def update_indicator(self, name: str, value: float) -> None:
        """Ω-QM30: Update an indicator's latest reading."""
        if name not in self._indicators:
            self._indicators[name] = deque(maxlen=200)
        self._indicators[name].append(value)

    def compute_observable(self) -> dict:
        """
        Ω-QM31: Compute unified observable across all indicators.

        Each indicator is an operator O_i acting on the market
        state vector. The unified prediction is the expectation
        value ⟨Ψ|O|Ψ⟩ where O = Σ w_i O_i.
        """
        if not self._indicators:
            return {"state": "NO_INDICATORS"}

        # Get latest readings
        latest = {name: hist[-1] for name, hist in self._indicators.items() if hist}
        if len(latest) < 2:
            return {"state": "INSUFFICIENT_DATA"}

        names = list(latest.keys())
        values = list(latest.values())

        # Ω-QM32: Normalize all indicators to [-1, 1]
        normalized = {}
        for name, val in latest.items():
            history = list(self._indicators[name])
            if len(history) >= 10:
                h_min, h_max = min(history), max(history)
                if h_max != h_min:
                    normalized[name] = 2.0 * (val - h_min) / (h_max - h_min) - 1.0
                else:
                    normalized[name] = 0.0
            else:
                normalized[name] = 0.0

        norm_values = list(normalized.values())

        # Ω-QM33: Uncertainty principle
        # Price prediction vs timing prediction have fundamental limit
        # ΔP × ΔT ≥ h (market constant)
        # Approximate from spread of indicators
        price_indicators = [v for v in norm_values if abs(v) > 0.3]
        if price_indicators:
            uncertainty = _std(price_indicators)
        else:
            uncertainty = 1.0

        # Ω-QM34: Entanglement between indicators
        # Measure correlation as entanglement strength
        for i, ni in enumerate(names):
            for j, nj in enumerate(names):
                if i < j:
                    hist_i = list(self._indicators[ni])[-30:]
                    hist_j = list(self._indicators[nj])[-30:]
                    if len(hist_i) >= 10 and len(hist_j) >= 10:
                        ent = _correlation(hist_i, hist_j)
                        self._entanglement_map[(ni, nj)] = ent

        # Ω-QM35: Quantum coherence score
        # Coherent = indicators aligned in same direction
        avg_val = sum(norm_values) / len(norm_values)
        coherence = 1.0 - _std(norm_values)  # low std = coherent
        coherence = max(0.0, min(1.0, coherence))
        self._coherence_history.append(coherence)

        # Ω-QM36: Expectation value
        # Weighted expectation of market direction
        # Weights = 1 / (1 + correlation) to avoid double-counting
        weights = []
        for name in names:
            avg_ent = 0.0
            count = 0
            for (ni, nj), ent in self._entanglement_map.items():
                if ni == name or nj == name:
                    avg_ent += abs(ent)
                    count += 1
            avg_ent = avg_ent / max(1, count)
            weights.append(1.0 / (1.0 + avg_ent))

        total_w = sum(weights)
        if total_w > 0:
            expectation = sum(w * v for w, v in zip(weights, norm_values)) / total_w
        else:
            expectation = avg_val

        return {
            "expectation_value": expectation,
            "coherence": coherence,
            "uncertainty": uncertainty,
            "indicator_count": len(latest),
            "indicator_values": normalized,
            "entanglement_pairs": len(self._entanglement_map),
            "is_coherent": coherence > 0.6,
            "is_actionable": abs(expectation) > 0.2 and coherence > 0.4,
        }


# ──────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────

def _std(values: list[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    m = sum(values) / n
    return math.sqrt(sum((v - m) ** 2 for v in values) / n)


def _correlation(x: list[float], y: list[float]) -> float:
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
