"""
SOLÉNN v2 — Fluid Dynamics & Karman Vortex Agents (Ω-V01 to Ω-V162)
Transmuted from v1:
  - karman_vortex_agent.py: Vortex shedding in price flow
  - fluid_dynamics.py: Navier-Stokes inspired market flow
  - kinetics_agents.py: Molecular kinetics of order flow
  - emanation_agents.py: Order flow emanation patterns

Protocol 3-6-9: 162 vetores planejados
  Concept 1 — Fluid Flow Modeling (Ω-V01 to Ω-V54): Navier-Stokes
    analogy for order flow (velocity field, pressure gradient,
    viscosity as market friction), Reynolds number estimation,
    laminar vs turbulent flow classification, Bernoulli principle
    for price/volume energy conservation
  Concept 2 — Vortex Detection & Shedding (Ω-V55 to Ω-V108): Karman
    vortex street detection in price oscillations, vortex shedding
    frequency (Strouhal number), coherent structure identification,
    wake analysis behind large orders, vortex-merger events as
    regime transition
  Concept 3 — Molecular Kinetics & Emanation (Ω-V109 to Ω-V162):
    Order flow as gas of interacting particles, Maxwell-Boltzmann
    distribution of order sizes, collision rate as activity
    indicator, emanation patterns from institutional zones,
    diffusion coefficient estimation
"""

from __future__ import annotations

import math
from collections import deque
from typing import Optional


# ──────────────────────────────────────────────────────────────
# Ω-V01 to Ω-V18: Fluid Flow Modeling
# ──────────────────────────────────────────────────────────────

class MarketFluidModel:
    """
    Ω-V01 to Ω-V09: Navier-Stokes inspired market flow model.

    Transmuted from v1 fluid_dynamics.py:
    v1: Simple price velocity tracking
    v2: Full fluid analogy with velocity field, pressure gradient,
    Reynolds number computation, viscosity estimation, and
    Bernoulli energy conservation.
    """

    def __init__(self, window_size: int = 200) -> None:
        self._window = window_size
        self._prices: deque[float] = deque(maxlen=window_size)
        self._volumes: deque[float] = deque(maxlen=window_size)
        self._velocity_history: deque[float] = deque(maxlen=500)

    def update(self, price: float, volume: float = 1.0) -> dict:
        """Ω-V03: Update fluid model with new tick."""
        self._prices.append(price)
        self._volumes.append(volume)

        if len(self._prices) < 5:
            return {"state": "WARMING_UP"}

        # Ω-V04: Velocity field (price change rate)
        velocity = self._prices[-1] - self._prices[-2]
        self._velocity_history.append(velocity)

        # Ω-V05: Acceleration (material derivative)
        if len(self._velocity_history) >= 2:
            accel = self._velocity_history[-1] - self._velocity_history[-2]
        else:
            accel = 0.0

        # Ω-V06: Pressure gradient
        # In fluid: -∇P drives flow. In market: price imbalance drives
        # order flow. Pressure ~ deviation from local average.
        local_avg = (
            sum(list(self._prices)[-20:]) / min(20, len(self._prices))
        )
        pressure_grad = price - local_avg

        # Ω-V07: Viscosity estimation (market friction)
        # High viscosity = price responds slowly to flow
        # Low viscosity = price moves freely
        if len(self._velocity_history) >= 10:
            vels = list(self._velocity_history)[-10:]
            avg_vol = sum(list(self._volumes)[-10:]) / 10
            velocity_var = _variance(vels)
            # Viscosity ~ velocity variance / volume rate
            viscosity = velocity_var / max(1e-6, avg_vol ** 2)
        else:
            viscosity = 1.0

        # Ω-V08: Reynolds number
        # Re = ρUL/μ — inertial forces / viscous forces
        # High Re = turbulent (chaotic price action)
        # Low Re = laminar (smooth trends)
        characteristic_length = _std(list(self._prices)[-20:]) if len(self._prices) >= 20 else abs(price) * 0.01
        characteristic_vel = _std(list(self._velocity_history)[-20:]) if len(self._velocity_history) >= 20 else abs(velocity)
        density = sum(list(self._volumes)[-20:]) / max(1, 20)

        reynolds = (
            density * characteristic_vel * characteristic_length /
            max(1e-6, viscosity)
        )

        # Ω-V09: Bernoulli energy
        # P + ½ρv² + ρgh = constant
        # Kinetic: ½ × volume × velocity²
        # Potential: volume × |pressure_grad| (stored energy)
        kinetic_energy = 0.5 * density * velocity ** 2
        potential_energy = density * abs(pressure_grad)
        total_energy = kinetic_energy + potential_energy

        # Flow classification
        if reynolds < 500:
            flow_regime = "LAMINAR"
        elif reynolds < 2000:
            flow_regime = "TRANSITIONAL"
        elif reynolds < 5000:
            flow_regime = "TURBULENT"
        else:
            flow_regime = "HIGHLY_TURBULENT"

        return {
            "velocity": velocity,
            "acceleration": accel,
            "pressure_gradient": pressure_grad,
            "viscosity": viscosity,
            "reynolds_number": reynolds,
            "flow_regime": flow_regime,
            "kinetic_energy": kinetic_energy,
            "potential_energy": potential_energy,
            "total_energy": total_energy,
            "is_turbulent": reynolds > 2000,
            "is_laminar": reynolds < 500,
            "is_trending": abs(velocity) > abs(pressure_grad) * 0.1,
        }


# ──────────────────────────────────────────────────────────────
# Ω-V19 to Ω-V27: Karman Vortex Street Detection
# ──────────────────────────────────────────────────────────────

class KarmanVortexDetector:
    """
    Ω-V19 to Ω-V27: Karman vortex street in price oscillations.

    Transmuted from v1 karman_vortex_agent.py:
    v1: Basic oscillation detection
    v2: Full vortex shedding analysis with Strouhal number,
    vortex frequency estimation, coherent structure detection,
    and wake analysis.

    In fluid dynamics, a Karman vortex street forms when flow
    past an obstacle creates alternating vortices. In markets,
    this corresponds to regular oscillations around a price level
    (support/resistance), with a characteristic frequency.
    """

    def __init__(self, window_size: int = 200) -> None:
        self._window = window_size
        self._prices: deque[float] = deque(maxlen=window_size)
        self._zero_crossings: deque[float] = deque(maxlen=500)

    def update(self, price: float) -> dict:
        """Ω-V21: Update vortex detection."""
        self._prices.append(price)

        if len(self._prices) < 30:
            return {"state": "WARMING_UP"}

        prices = list(self._prices)
        mean_price = sum(prices[-30:]) / 30

        # Ω-V22: Zero crossing detection (relative to mean)
        deviations = [p - mean_price for p in prices[-30:]]
        current_crossing = deviations[-1] * deviations[-2] < 0
        if current_crossing:
            self._zero_crossings.append(len(prices) - 1)

        # Ω-V23: Strouhal number
        # St = f × D / U where f = shedding frequency, D = obstacle size,
        # U = flow velocity
        # In market: f = oscillation frequency, D = range, U = price velocity
        crossings = list(self._zero_crossings)[-20:]
        if len(crossings) >= 4:
            intervals = [crossings[i + 1] - crossings[i]
                        for i in range(len(crossings) - 1)]
            avg_interval = sum(intervals) / len(intervals)
            frequency = 1.0 / max(1, avg_interval)
        else:
            avg_interval = 0
            frequency = 0.0

        price_range = max(prices[-30:]) - min(prices[-30:])
        velocity = abs(prices[-1] - prices[0]) / len(prices)

        strouhal = (
            frequency * price_range / max(1e-6, velocity)
            if velocity > 1e-6 and price_range > 0
            else 0.0
        )

        # Ω-V24: Coherent structure detection
        # Vortex street = regular oscillation with consistent amplitude
        peaks = _find_zero_crossing_intervals(deviations)
        if len(peaks) >= 3:
            peak_values = [deviations[p] for p in peaks if 0 <= p < len(deviations)]
            if peak_values:
                amplitude_regularity = 1.0 - (
                    _std(peak_values) / max(1e-6, sum(abs(v) for v in peak_values) / len(peak_values))
                )
            else:
                amplitude_regularity = 0.0
        else:
            amplitude_regularity = 0.0

        # Ω-V25: Wake analysis
        # After a "vortex shedding" event (break of support),
        # how does the price behave in the wake?
        wake_decay = 0.0
        if len(deviations) >= 10:
            first_half = sum(abs(d) for d in deviations[-20:-10])
            second_half = sum(abs(d) for d in deviations[-10:])
            if first_half > 0:
                wake_decay = 1.0 - second_half / first_half

        # Classification
        is_vortex_street = (
            amplitude_regularity > 0.5 and
            frequency > 0.05 and
            strouhal > 0.1
        )

        return {
            "frequency": frequency,
            "strouhal_number": strouhal,
            "amplitude_regularity": amplitude_regularity,
            "wake_decay": wake_decay,
            "is_vortex_street": is_vortex_street,
            "n_oscillations": len(crossings),
            "mean_deviation": sum(abs(d) for d in deviations[-10:]) / 10,
        }


# ──────────────────────────────────────────────────────────────
# Ω-V28 to Ω-V36: Molecular Kinetics of Order Flow
# ──────────────────────────────────────────────────────────────

class OrderFlowKinetics:
    """
    Ω-V28 to Ω-V36: Molecular kinetics analogy for order flow.

    Transmuted from v1 kinetics_agents.py:
    v1: Basic trade size distribution
    v2: Full Maxwell-Boltzmann distribution fit, collision rate
    estimation, diffusion coefficient, and temperature model.

    Orders = particles, trades = collisions, price = container
    volume, volume flow = temperature.
    """

    def __init__(self, window_size: int = 300) -> None:
        self._window = window_size
        self._trade_sizes: deque[float] = deque(maxlen=window_size)
        self._inter_trade_times: deque[float] = deque(maxlen=window_size)
        self._last_time: Optional[float] = None

    def update(
        self,
        trade_volume: float,
        timestamp: float,
    ) -> dict:
        """Ω-V30: Update kinetic model with trade data."""
        self._trade_sizes.append(trade_volume)

        if self._last_time is not None:
            dt = max(1e-6, timestamp - self._last_time)
            self._inter_trade_times.append(dt)
        self._last_time = timestamp

        if len(self._trade_sizes) < 20:
            return {"state": "WARMING_UP"}

        # Ω-V31: Maxwell-Boltzmann distribution fit
        sizes = list(self._trade_sizes)
        mean_size = sum(sizes) / len(sizes)
        # For MB: mean = sqrt(2kT/πm) → T = πm·mean²/(2k)
        # Using simplified: "temperature" proportional to mean squared
        temperature = mean_size ** 2

        # Ω-V32: Most probable size vs mean
        sorted_sizes = sorted(sizes)
        modal_size = sorted_sizes[len(sorted_sizes) // 3]  # MB peak at lower end
        ratio_mean_mode = mean_size / max(1e-6, modal_size)

        # Ω-V33: Collision rate
        # Rate of trades per unit time
        if self._inter_trade_times:
            avg_dt = sum(self._inter_trade_times) / len(self._inter_trade_times)
            collision_rate = 1.0 / avg_dt
        else:
            collision_rate = 1.0

        # Ω-V34: Diffusion coefficient
        # D ~ mean_free_path × collision_rate
        # Mean free path ~ std of trade sizes
        size_std = _std(sizes)
        diffusion = size_std * collision_rate

        # Ω-V35: High-energy tail (large orders)
        # Orders > 3× mean = "hot molecules" (institutional)
        threshold = mean_size * 3.0
        hot_orders = sum(1 for s in sizes if s > threshold)
        hot_fraction = hot_orders / max(1, len(sizes))

        # Ω-V36: Maxwell-Boltzmann goodness of fit
        # Compare empirical distribution to theoretical MB
        mb_fit = 1.0 - min(1.0, abs(ratio_mean_mode - 1.5) / 1.5)

        return {
            "temperature": temperature,
            "mean_size": mean_size,
            "modal_size": modal_size,
            "ratio_mean_mode": ratio_mean_mode,
            "collision_rate": collision_rate,
            "diffusion_coefficient": diffusion,
            "hot_fraction": hot_fraction,
            "mb_fit": mb_fit,
            "is_institutional_hot": hot_fraction > 0.05,
            "n_orders": len(sizes),
        }


# ──────────────────────────────────────────────────────────────
# Ω-V37 to Ω-V45: Order Flow Emanation Patterns
# ──────────────────────────────────────────────────────────────

class OrderFlowEmanation:
    """
    Ω-V37 to Ω-V45: Emanation patterns from key price zones.

    Transmuted from v1 emanation_agents.py:
    v1: Simple volume flow tracking
    v2: Full emanation analysis with source identification,
    flow direction mapping, emanation rate, and confluence
    zones detection.
    """

    def __init__(self, window_size: int = 200, zone_size: float = 500.0) -> None:
        self._window = window_size
        self._zone_size = zone_size
        self._trade_flow: deque[tuple[float, float, str]] = deque(maxlen=window_size)
        # (price, volume, direction)

    def update(
        self,
        price: float,
        volume: float,
        direction: str = "UNKNOWN",
    ) -> dict:
        """Ω-V39: Update emanation analysis."""
        self._trade_flow.append((price, volume, direction))

        if len(self._trade_flow) < 20:
            return {"state": "WARMING_UP"}

        # Ω-V40: Zone classification
        zone = round(price / self._zone_size) * self._zone_size
        zone_flow = [(p, v, d) for p, v, d in self._trade_flow
                     if abs(p - zone) < self._zone_size]

        if not zone_flow:
            return {"state": "SPARSE", "zone": zone}

        # Ω-V41: Emanation rate (volume flow per unit time)
        total_vol = sum(v for _, v, _ in zone_flow)
        emanation_rate = total_vol / max(1, len(zone_flow))

        # Ω-V42: Flow direction balance
        buy_vol = sum(v for _, v, d in zone_flow if d == "BUY")
        sell_vol = sum(v for _, v, d in zone_flow if d == "SELL")
        flow_balance = (buy_vol - sell_vol) / max(1e-6, buy_vol + sell_vol)

        # Ω-V43: Source identification
        # Zones with high emanation but low incoming flow = source
        # Zones with high incoming but low outgoing = sink
        all_vol = sum(v for _, v, _ in self._trade_flow)
        zone_fraction = total_vol / max(1e-6, all_vol)
        is_source = zone_fraction > 0.3  # zone generates >30% of flow
        is_sink = zone_fraction < 0.05  # zone absorbs but doesn't emit

        return {
            "zone": zone,
            "emanation_rate": emanation_rate,
            "flow_balance": flow_balance,
            "zone_volume": total_vol,
            "zone_fraction": zone_fraction,
            "is_source": is_source,
            "is_sink": is_sink,
            "is_neutral": not is_source and not is_sink,
            "n_trades_in_zone": len(zone_flow),
        }


# ──────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────

def _std(values: list[float]) -> float:
    """Standard deviation."""
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    return math.sqrt(sum((v - mean) ** 2 for v in values) / n)


def _variance(values: list[float]) -> float:
    """Population variance."""
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    return sum((v - mean) ** 2 for v in values) / n


def _find_zero_crossing_intervals(deviations: list[float]) -> list[int]:
    """Find indices where deviation crosses zero (sign change)."""
    crossings = []
    for i in range(1, len(deviations)):
        if deviations[i] * deviations[i - 1] < 0:
            crossings.append(i)
    return crossings
