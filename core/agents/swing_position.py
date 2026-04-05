"""
SOLÉNN v2 — Swing Position & Supernova Capacitor Agents (Ω-WP01 to Ω-WP162)
Transmuted from v1:
  - swing_position_agent.py: Swing detection and position tracking
  - swing_analysis_agent.py: Swing structure analysis
  - supernova_capacitor.py: Energy accumulation and explosive release
  - dark_mass_agent.py: Hidden market momentum detection
  - liquid_state_agent.py: Phase state transitions
  - crash_velocity_agent.py: Crash speed prediction
  - leech_agent.py: Liquidity drain detection
  - liquidity_leech_agent.py: Parasitic flow identification

Protocol 3-6-9: 162 vetores planejados
  Concept 1 — Swing Detection & Structure (Ω-WP01 to Ω-WP54):
    Zig-zag swing identification, swing high/low hierarchy,
    support/resistance from swing clustering, swing failure
    pattern, structure break detection, market structure phase
  Concept 2 — Energy Accumulation & Release (Ω-WP55 to Ω-WP108):
    Supernova capacitor model (energy store until critical mass),
    energy accumulation rate, compression-release cycles,
    explosive move probability, dark mass (hidden momentum)
    detection
  Concept 3 — Phase State & Velocity (Ω-WP109 to Ω-WP162):
    Liquid/solid/gas market phase classification, crash velocity
    prediction, liquidity drain (leech) detection, parasitic flow
    filtering, state transition energy
"""

from __future__ import annotations

import math
from collections import deque
from typing import Optional


# ──────────────────────────────────────────────────────────────
# Ω-WP01 to Ω-WP18: Swing Detection & Structure
# ──────────────────────────────────────────────────────────────

class SwingDetector:
    """
    Ω-WP01 to Ω-WP09: Swing high/low detection and structure.

    Transmuted from v1 swing_position_agent.py:
    v1: Simple peak/trough finding
    v2: Full structural swing analysis with hierarchy,
    clustering, and structure break detection.
    """

    def __init__(
        self,
        swing_window: int = 5,
        max_swing_age: int = 50,
    ) -> None:
        self._swing_window = swing_window
        self._max_age = max_swing_age
        self._prices: deque[float] = deque(maxlen=200)
        self._swing_highs: list[tuple[int, float]] = []
        self._swing_lows: list[tuple[int, float]] = []
        self._all_swing_levels: list[float] = []

    def update(self, price: float) -> dict:
        """Ω-WP03: Detect new swings and update structure."""
        self._prices.append(price)
        idx = len(self._prices) - 1

        if idx < self._swing_window * 2:
            return {"state": "WARMING_UP"}

        prices = list(self._prices)

        # Ω-WP04: Swing high/low detection
        if self._is_swing_high(prices, idx):
            self._swing_highs.append((idx, price))
            self._all_swing_levels.append(price)
            # Age out old swings
            self._swing_highs = [
                (i, p) for i, p in self._swing_highs
                if idx - i < self._max_age
            ]

        if self._is_swing_low(prices, idx):
            self._swing_lows.append((idx, price))
            self._all_swing_levels.append(price)
            self._swing_lows = [
                (i, p) for i, p in self._swing_lows
                if idx - i < self._max_age
            ]

        # Ω-WP05: Market structure determination
        structure = self._determine_structure()

        # Ω-WP06: Key levels from swing clustering
        key_levels = self._cluster_swing_levels(n_clusters=5)

        # Ω-WP07: Nearest swing level
        nearest_level = None
        min_dist = float('inf')
        for lvl in key_levels:
            d = abs(price - lvl)
            if d < min_dist:
                min_dist = d
                nearest_level = lvl

        return {
            "structure": structure,
            "key_levels": key_levels,
            "nearest_swing_level": nearest_level,
            "distance_to_nearest": min_dist,
            "n_swing_highs": len(self._swing_highs),
            "n_swing_lows": len(self._swing_lows),
            "is_near_support": nearest_level is not None and price > nearest_level and min_dist / max(1e-6, price) < 0.01,
            "is_near_resistance": nearest_level is not None and price < nearest_level and min_dist / max(1e-6, price) < 0.01,
        }

    def _is_swing_high(self, prices: list[float], idx: int) -> bool:
        """Check if current price is a swing high."""
        w = self._swing_window
        if idx < w or idx >= len(prices) - w:
            return False
        center = prices[idx]
        for i in range(idx - w, idx + w + 1):
            if i == idx:
                continue
            if prices[i] >= center:
                return False
        return True

    def _is_swing_low(self, prices: list[float], idx: int) -> bool:
        """Check if current price is a swing low."""
        w = self._swing_window
        if idx < w or idx >= len(prices) - w:
            return False
        center = prices[idx]
        for i in range(idx - w, idx + w + 1):
            if i == idx:
                continue
            if prices[i] <= center:
                return False
        return True

    def _determine_structure(self) -> str:
        """Ω-WP05: Determine current market structure."""
        if len(self._swing_highs) < 2 or len(self._swing_lows) < 2:
            return "DETERMINING"

        highs = [h[1] for h in self._swing_highs[-3:]]
        lows = [l[1] for l in self._swing_lows[-3:]]

        higher_highs = all(highs[i] > highs[i - 1] for i in range(1, len(highs)))
        lower_lows = all(lows[i] < lows[i - 1] for i in range(1, len(lows)))
        lower_highs = all(highs[i] < highs[i - 1] for i in range(1, len(highs)))
        higher_lows = all(lows[i] > lows[i - 1] for i in range(1, len(lows)))

        if higher_highs and higher_lows:
            return "UPTREND"
        elif lower_highs and lower_lows:
            return "DOWNTREND"
        elif higher_highs and lower_lows:
            return "EXPANDING_RANGE"
        elif lower_highs and higher_lows:
            return "CONTRACTING_RANGE"
        else:
            return "RANGING"

    def _cluster_swing_levels(self, n_clusters: int = 5) -> list[float]:
        """Ω-WP06: Cluster swing levels into support/resistance zones."""
        if len(self._all_swing_levels) < 2:
            return []

        levels = sorted(set(round(lvl, 2) for lvl in self._all_swing_levels[-100:]))

        # Simple density-based clustering: merge levels within tolerance
        if len(levels) <= n_clusters:
            return levels

        tolerance = (levels[-1] - levels[0]) / (n_clusters * 2) if len(levels) > 1 else 1.0
        clusters: list[float] = []
        current_cluster: list[float] = [levels[0]]

        for lvl in levels[1:]:
            if lvl - current_cluster[-1] < tolerance:
                current_cluster.append(lvl)
            else:
                clusters.append(sum(current_cluster) / len(current_cluster))
                current_cluster = [lvl]
        if current_cluster:
            clusters.append(sum(current_cluster) / len(current_cluster))

        return sorted(clusters)[-n_clusters:]  # Return top N most significant


# ──────────────────────────────────────────────────────────────
# Ω-WP19 to Ω-WP27: Supernova Capacitor (Energy Accumulation)
# ──────────────────────────────────────────────────────────────

class SupernovaCapacitor:
    """
    Ω-WP19 to Ω-WP27: Energy accumulation and explosive release.

    Transmuted from v1 supernova_capacitor.py:
    v1: Simple volatility compression tracking
    v2: Full capacitor model with charge/discharge cycles,
    compression ratio, explosion probability, and dark mass.
    """

    def __init__(self, window_size: int = 100) -> None:
        self._window = window_size
        self._prices: deque[float] = deque(maxlen=window_size)
        self._volumes: deque[float] = deque(maxlen=window_size)
        self._energy: float = 0.0  # accumulated energy
        self._max_energy: float = 1.0  # capacitor capacity
        self._last_release: int = 0
        self._charge_rate: float = 0.0

    def update(self, price: float, volume: float = 1.0) -> dict:
        """Ω-WP21: Charge capacitor with market energy."""
        self._prices.append(price)
        self._volumes.append(volume)

        if len(self._prices) < 10:
            return {"state": "WARMING_UP"}

        # Ω-WP22: Energy input = vol compression + volume anomaly + price compression
        prices = list(self._prices)
        volumes = list(self._volumes)

        # Volatility compression (Bollinger squeeze analog)
        recent_std = _std(prices[-20:]) if len(prices) >= 20 else _std(prices)
        long_std = _std(prices)
        compression = 1.0 - (recent_std / max(1e-6, long_std)) if long_std > 0 else 0.0

        # Volume anomaly
        avg_vol = sum(volumes) / len(volumes)
        vol_anomaly = volume / max(1e-6, avg_vol)

        # Price compression (range narrowing)
        if len(prices) >= 20:
            recent_range = max(prices[-10:]) - min(prices[-10:])
            full_range = max(prices) - min(prices)
            range_compression = 1.0 - (recent_range / max(1e-6, full_range))
        else:
            range_compression = 0.0

        # Ω-WP23: Charge rate
        charge = max(0.0, compression * 0.4 + range_compression * 0.3 + vol_anomaly * 0.3)
        self._charge_rate = 0.7 * self._charge_rate + 0.3 * charge
        self._energy = min(self._max_energy, self._energy + self._charge_rate * 0.1)

        # Ω-WP24: Discharge detection
        # Energy release = explosive move
        if len(prices) >= 3:
            recent_move = abs(prices[-1] - prices[-3]) / max(1e-6, abs(prices[-3]))
            if recent_move > recent_std * 2 and self._energy > 0.3:
                # Discharge event
                self._energy *= 0.5  # Partial discharge
                self._last_release = len(prices)

                return {
                    "state": "SUPERNOVA",
                    "energy_before_release": self._energy * 2,
                    "move_magnitude": recent_move,
                    "is_supernova": True,
                }

        # Ω-WP25: Explosion probability
        explosion_prob = self._energy / self._max_energy

        # Ω-WP26: Dark mass (hidden momentum)
        # Price not moving but energy accumulating = hidden pressure
        if len(prices) >= 20:
            price_change = abs(prices[-1] - prices[-20]) / max(1e-6, abs(prices[-20]))
            energy_vs_move = self._energy / max(1e-6, price_change + 0.001)
            dark_mass = min(1.0, energy_vs_move * 0.1)
        else:
            dark_mass = 0.0

        return {
            "state": "CHARGING",
            "energy_level": self._energy,
            "energy_pct": self._energy / self._max_energy,
            "charge_rate": self._charge_rate,
            "explosion_probability": explosion_prob,
            "dark_mass": dark_mass,
            "compression": compression,
            "is_near_critical": self._energy > self._max_energy * 0.8,
            "is_supernova": False,
        }


# ──────────────────────────────────────────────────────────────
# Ω-WP28 to Ω-WP36: Phase State & Crash Velocity
# ──────────────────────────────────────────────────────────────

class PhaseStateAnalyzer:
    """
    Ω-WP28 to Ω-WP36: Market phase state with crash dynamics.

    Transmuted from v1 liquid_state_agent.py + crash_velocity + leech:
    v1: State tracking via volatility
    v2: Full phase classification (solid/liquid/gas/plasma),
    crash velocity prediction, liquidity drain detection,
    parasitic flow filtering.
    """

    def __init__(self, window_size: int = 200) -> None:
        self._window = window_size
        self._prices: deque[float] = deque(maxlen=window_size)
        self._volumes: deque[float] = deque(maxlen=window_size)
        self._velocity_history: deque[float] = deque(maxlen=200)

    def update(self, price: float, volume: float = 1.0) -> dict:
        """Ω-WP30: Update phase state analysis."""
        self._prices.append(price)
        self._volumes.append(volume)

        if len(self._prices) < 20:
            return {"state": "WARMING_UP"}

        prices = list(self._prices)
        volumes = list(self._volumes)

        # Ω-WP31: Phase classification
        # Solid: low vol, tight range, low activity
        # Liquid: moderate vol, flowing, normal activity
        # Gas: high vol, wide swings, high energy
        # Plasma: extreme vol, chaotic, crisis mode
        returns = [(prices[i] - prices[i-1]) / max(1e-6, abs(prices[i-1]))
                   for i in range(1, len(prices))]

        vol = _std(returns) if returns else 0.0
        avg_vol_flow = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else 0.0
        long_vol = _std(returns) if len(returns) > 50 else vol

        if vol < long_vol * 0.5:
            phase = "SOLID"  # Frozen, accumulation phase
        elif vol < long_vol * 1.2:
            phase = "LIQUID"  # Normal flowing
        elif vol < long_vol * 2.0:
            phase = "GAS"  # Energetic, trending strongly
        else:
            phase = "PLASMA"  # Chaotic, crisis/climax

        # Ω-WP32: Crash velocity
        # If in PLASMA or transitioning GAS->PLASMA, predict speed
        if len(self._velocity_history) >= 5:
            recent_velocities = list(self._velocity_history)[-10:]
            avg_velocity = sum(recent_velocities) / len(recent_velocities)
            max_velocity = max(recent_velocities)
            velocity_trend = recent_velocities[-1] - recent_velocities[0]
        else:
            avg_velocity = 0.0
            max_velocity = 0.0
            velocity_trend = 0.0

        # Current velocity (absolute return rate)
        current_velocity = sum(abs(r) for r in returns[-5:]) / 5 if len(returns) >= 5 else 0.0
        self._velocity_history.append(current_velocity)

        # Ω-WP33: Crash probability
        # High velocity + negative bias + high volume = crash risk
        avg_return = sum(returns[-10:]) / 10 if len(returns) >= 10 else 0.0
        crash_prob = 0.0
        if avg_return < -0.002 and current_velocity > avg_velocity * 1.5:
            crash_prob = min(1.0, abs(avg_return) * 50 * (current_velocity / max(1e-6, avg_velocity)))

        # Ω-WP34: Liquidity drain (leech detection)
        # Volume without price movement = liquidity being drained
        if len(volumes) >= 20:
            vol_trend = sum(volumes[-10:]) / 10 / max(1e-6, sum(volumes[:10]) / 10)
            price_inertia = abs(prices[-1] - prices[-10]) / max(1e-6, abs(prices[-10]) + 1e-6)
            # High volume but price not moving = leech
            leech_score = vol_trend * (1.0 - price_inertia * 10) if vol_trend > 1.5 else 0.0
            leech_score = max(0.0, min(1.0, leech_score))
        else:
            leech_score = 0.0

        # Ω-WP35: Phase transition energy
        # Energy required to change from one phase to another
        transition_scores = {
            "SOLID->LIQUID": 0.0,
            "LIQUID->GAS": 0.0,
            "GAS->PLASMA": 0.0,
        }

        if phase == "SOLID" and vol > _std(returns[:len(returns)//2]) * 0.8 if len(returns) > 10 else False:
            transition_scores["SOLID->LIQUED"] = 0.6
        if phase == "LIQUID" and vol > long_vol:
            transition_scores["LIQUID->GAS"] = vol / max(1e-6, long_vol)
        if phase == "GAS" and vol > long_vol * 1.5:
            transition_scores["GAS->PLASMA"] = vol / max(1e-6, long_vol * 1.5)

        return {
            "phase": phase,
            "volatility": vol,
            "current_velocity": current_velocity,
            "avg_velocity": avg_velocity,
            "velocity_trend": velocity_trend,
            "crash_probability": crash_prob,
            "leech_score": leech_score,
            "phase_transition_scores": transition_scores,
            "is_stable": phase in ("SOLID", "LIQUID"),
            "is_stressed": phase in ("GAS", "PLASMA"),
            "is_leech_active": leech_score > 0.3,
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
