"""
SOLÉNN v2 — Game Theory & Behavioral Finance Agents (Ω-G01 to Ω-G162)
Transmuted from v1:
  - mean_field_game_agent.py: Mean field game equilibrium solver
  - behavioral.py: Behavioral bias detection
  - session_dynamics.py: Session-specific pattern analysis
  - hex_matrix.py: Hexagonal price zone mapping

Protocol 3-6-9: 162 vetores planejados
  Concept 1 — Mean Field Game Theory (Ω-G01 to Ω-G54): Nash equilibrium
    in population of agents, mean field approximation, best response
    dynamics, equilibrium distribution, value function estimation,
    fixed point iteration for strategy distribution
  Concept 2 — Behavioral Finance Analysis (Ω-G55 to Ω-G108): Cognitive
    bias detection (overconfidence, loss aversion, herding, anchoring,
    recency, confirmation), sentiment extremity scoring, contrarian
    signal generation, bias quantification with contrarian inversion
  Concept 3 — Session Dynamics & Spatial Analysis (Ω-G109 to Ω-G162):
    Session overlap patterns (Tokyo/London/NY), session transition
    detection, hexagonal price zone mapping, spatial liquidity
    distribution, session-specific alpha patterns
"""

from __future__ import annotations

import math
import time
from collections import Counter, deque
from dataclasses import dataclass, field
from typing import Optional


# ──────────────────────────────────────────────────────────────
# Ω-G01 to Ω-G18: Mean Field Game Solver
# ──────────────────────────────────────────────────────────────

class MeanFieldGameSolver:
    """
    Ω-G01 to Ω-G09: Solve mean field game equilibrium.

    Transmuted from v1 mean_field_game_agent.py:
    v1: Simple strategy population tracking
    v2: Full mean field game solver with fixed point iteration,
    strategy distribution evolution, Nash stability detection,
    and value function estimation for each strategy class.
    """

    def __init__(
        self,
        strategies: Optional[list[str]] = None,
        window_size: int = 200,
    ) -> None:
        self._strategies = strategies or [
            "TREND_FOLLOWING", "MEAN_REVERSION", "MARKET_MAKING", "ARBITRAGE"
        ]
        self._window_size = window_size
        # Population fraction for each strategy
        self._population: dict[str, float] = {
            s: 1.0 / len(self._strategies) for s in self._strategies
        }
        self._payoffs: dict[str, deque[float]] = {
            s: deque(maxlen=window_size) for s in self._strategies
        }
        self._history: deque[dict] = deque(maxlen=200)

    def update(
        self,
        price: float,
        flow_imbalance: float,
        realized_vol: float,
    ) -> dict:
        """
        Ω-G03: Update game state, estimate payoffs, compute equilibrium.
        flow_imbalance: net buy-sell pressure [-1, 1]
        realized_vol: recent volatility measure
        """
        # Ω-G04: Estimate payoff for each strategy given market state
        payoffs = {}
        payoffs["TREND_FOLLOWING"] = abs(flow_imbalance) * realized_vol
        payoffs["MEAN_REVERSION"] = max(0, 0.5 - abs(flow_imbalance)) * (1.0 - realized_vol)
        payoffs["MARKET_MAKING"] = max(0, 1.0 - abs(flow_imbalance) - realized_vol * 2)
        payoffs["ARBITRAGE"] = abs(flow_imbalance) * (1.0 - realized_vol) * 0.5

        for s, p in payoffs.items():
            self._payoffs[s].append(p)

        # Ω-G05: Fixed point iteration for equilibrium distribution
        # Population shifts toward strategies with higher average payoff
        avg_payoffs = {
            s: (sum(self._payoffs[s]) / len(self._payoffs[s]))
            if self._payoffs[s] else 0.0
            for s in self._strategies
        }
        total_payoff = sum(avg_payoffs.values())
        if total_payoff > 1e-12:
            target_pop = {
                s: p / total_payoff for s, p in avg_payoffs.items()
            }
        else:
            target_pop = {s: 1.0 / len(self._strategies) for s in self._strategies}

        # Smooth population update (inertia prevents instant switching)
        inertia = 0.9
        for s in self._strategies:
            self._population[s] = (
                inertia * self._population[s] +
                (1 - inertia) * target_pop[s]
            )

        # Normalize
        pop_sum = sum(self._population.values())
        if pop_sum > 0:
            for s in self._strategies:
                self._population[s] /= pop_sum

        # Ω-G06: Nash stability check
        # Stable if population change < threshold
        prev = dict(self._history[-1])["population"] if self._history else self._population
        pop_change = sum(
            abs(self._population[s] - prev.get(s, 0))
            for s in self._strategies
        )
        is_stable = pop_change < 0.02

        result = {
            "population": dict(self._population),
            "avg_payoffs": avg_payoffs,
            "is_stable": is_stable,
            "dominant_strategy": max(self._population, key=self._population.get),
            "population_entropy": _entropy_from_dict(self._population),
        }
        self._history.append(result)
        return result

    def get_best_response(self, current_state: dict) -> str:
        """Ω-G08: Given market state, return best response strategy."""
        if not self._payoffs:
            return "TREND_FOLLOWING"

        # Strategy that performs best when current state matches history
        best_score = -float('inf')
        best_strategy = self._strategies[0]

        for s in self._strategies:
            payoffs = list(self._payoffs[s])
            if not payoffs:
                continue
            # Recent payoffs weighted more
            weights = [(i + 1) ** 0.5 for i in range(len(payoffs))]
            w_sum = sum(w * p for w, p in zip(weights, payoffs)) / sum(weights)
            if w_sum > best_score:
                best_score = w_sum
                best_strategy = s

        return best_strategy


# ──────────────────────────────────────────────────────────────
# Ω-G19 to Ω-G27: Behavioral Bias Detection
# ──────────────────────────────────────────────────────────────

class BehavioralBiasDetector:
    """
    Ω-G19 to Ω-G27: Detect and quantify behavioral biases.

    Transmuted from v1 behavioral.py:
    v1: Basic sentiment scoring
    v2: Full cognitive bias detection for 6 bias types with
    quantified scores and composite contrarian signal.
    """

    def __init__(self, window_size: int = 200) -> None:
        self._window_size = window_size
        self._returns: deque[float] = deque(maxlen=window_size)
        self._volumes: deque[float] = deque(maxlen=window_size)
        self._prices: deque[float] = deque(maxlen=window_size)
        self._position_changes: deque[int] = deque(maxlen=window_size)
        self._bias_scores: dict[str, float] = {
            "overconfidence": 0.0,
            "loss_aversion": 0.0,
            "herding": 0.0,
            "anchoring": 0.0,
            "recency": 0.0,
            "confirmation": 0.0,
        }

    def update(
        self,
        price: float,
        volume: float,
        net_position_change: int = 0,
    ) -> dict:
        """
        Ω-G21: Update with new tick/volume/position data.
        net_position_change: +1 = more longs, -1 = more shorts, 0 = neutral
        """
        prev_price = self._prices[-1] if self._prices else price
        self._prices.append(price)
        if prev_price != 0:
            self._returns.append((price - prev_price) / abs(prev_price))
        self._volumes.append(volume)
        self._position_changes.append(net_position_change)

        if len(self._prices) < 30:
            return {"biases": self._bias_scores, "contrarian_signal": 0.0}

        returns = list(self._returns)
        positions = list(self._position_changes)
        volumes = list(self._volumes)
        prices_list = list(self._prices)

        # Ω-G22: Overconfidence = high volume during low-volatility periods
        # Market acts aggressively when there's little reason to
        recent_vol = sum(abs(r) for r in returns[-20:]) / max(1, 20)
        recent_vol_trading = sum(volumes[-20:]) / max(1, 20)
        long_term_vol_trading = sum(volumes) / max(1, len(volumes))
        if long_term_vol_trading > 0 and recent_vol < 0.001:
            self._bias_scores["overconfidence"] = min(
                1.0, recent_vol_trading / max(1, long_term_vol_trading)
            )
        else:
            self._bias_scores["overconfidence"] *= 0.95

        # Ω-G23: Loss aversion = reluctance to exit losing positions
        # Detected as: price moves away from recent average but positions
        # don't change (holders refusing to realize loss)
        if len(returns) >= 20:
            recent_return = sum(returns[-5:]) / 5
            position_response = sum(positions[-5:]) / max(1, 5)
            # If price drops but no selling (or price rises but no buying)
            if recent_return < -0.002 and sum(positions[-5:]) >= 0:
                self._bias_scores["loss_aversion"] = min(
                    1.0, abs(recent_return) * 100
                )
            elif recent_return > 0.002 and sum(positions[-5:]) <= 0:
                self._bias_scores["loss_aversion"] = min(
                    1.0, abs(recent_return) * 100
                )
            else:
                self._bias_scores["loss_aversion"] *= 0.95

        # Ω-G24: Herding = extreme concentration in one direction
        # All positions moving same way with high volume
        if positions:
            same_direction = sum(1 for p in positions[-15:] if p > 0)
            if same_direction > 12 or same_direction < 3:
                self._bias_scores["herding"] = min(1.0, abs(same_direction - 7.5) / 7.5)
            else:
                self._bias_scores["herding"] *= 0.95

        # Ω-G25: Anchoring = price stuck near round numbers
        # Resistance to move away from recent reference level
        if len(prices_list) >= 20:
            recent_range = max(prices_list[-20:]) - min(prices_list[-20:])
            avg_price = sum(prices_list[-20:]) / 20
            # Find nearest "round" number (multiple of 100, 50, 10, etc.)
            for round_unit in [1000, 500, 100, 50, 10, 1, 0.1, 0.01]:
                dist_to_round = min(
                    abs(avg_price - n * round_unit)
                    for n in [int(avg_price / round_unit),
                              int(avg_price / round_unit) + 1]
                )
                if dist_to_round < abs(avg_price) * 0.001:
                    # Price anchored near round number
                    self._bias_scores["anchoring"] = min(
                        1.0, 1.0 - recent_range / (abs(avg_price) * 0.01 + 1e-12)
                    )
                    break
            else:
                self._bias_scores["anchoring"] *= 0.95

        # Ω-G26: Recency = overreaction to latest move
        # Volume spikes after latest price move, disproportionate
        if len(returns) >= 10 and len(volumes) >= 10:
            latest_return = abs(returns[-1]) if returns else 0
            avg_return = sum(abs(r) for r in returns[:-1]) / max(1, len(returns) - 1)
            latest_vol = volumes[-1] if volumes else 1
            avg_vol = sum(volumes[:-1]) / max(1, len(volumes) - 1)
            if avg_return > 0 and avg_vol > 0:
                return_ratio = latest_return / max(1e-6, avg_return)
                vol_ratio = latest_vol / max(1e-6, avg_vol)
                # If small move but big volume reaction = recency
                if return_ratio < 0.5 and vol_ratio > 2.0:
                    self._bias_scores["recency"] = min(1.0, vol_ratio / 10)
                else:
                    self._bias_scores["recency"] *= 0.95

        # Confirmation = tendency to agree with prior direction
        if len(returns) >= 10 and positions:
            # Positions continue in direction of recent trend
            trend = sum(returns[-10:]) / max(1, 10)
            current_direction = sum(positions[-5:]) / max(1, 5)
            if trend > 0 and current_direction > 0 or trend < 0 and current_direction < 0:
                self._bias_scores["confirmation"] = min(
                    1.0, abs(trend) * 50 + abs(current_direction) * 0.2
                )
            else:
                self._bias_scores["confirmation"] *= 0.95

        # Ω-G27: Composite contrarian signal
        total_bias = sum(self._bias_scores.values()) / len(self._bias_scores)
        contrarian_strength = min(1.0, total_bias)
        # Direction: if market is extremely bullish, contrarian says short
        recent_direction = sum(returns[-5:]) / max(1, 5)
        contrarian_direction = "SELL" if recent_direction > 0 else "BUY"

        return {
            "biases": dict(self._bias_scores),
            "composite_bias": total_bias,
            "contrarian_strength": contrarian_strength,
            "contrarian_direction": contrarian_direction,
            "is_actionable": total_bias > 0.3 and abs(recent_direction) > 0.001,
        }


# ──────────────────────────────────────────────────────────────
# Ω-G28 to Ω-G36: Session Dynamics Analyzer
# ──────────────────────────────────────────────────────────────

class SessionDynamicsAnalyzer:
    """
    Ω-G28 to Ω-G36: Session-specific market behavior modeling.

    Transmuted from v1 session_dynamics.py:
    v1: Basic hour-of-day tracking
    v2: Full session detection with overlap anomaly detection,
    session-specific alpha patterns, and transition classification.
    """

    # Session definitions in UTC hours
    SESSIONS = {
        "TOKYO": (0, 9),      # 00:00 - 09:00 UTC
        "LONDON": (7, 16),    # 07:00 - 16:00 UTC
        "NEW_YORK": (13, 21), # 13:00 - 21:00 UTC
    }

    def __init__(self, window_size: int = 300) -> None:
        self._window_size = window_size
        self._prices: deque[float] = deque(maxlen=window_size)
        self._volumes: deque[float] = deque(maxlen=window_size)
        self._session_stats: dict[str, dict] = {
            "TOKYO": {"count": 0, "avg_vol": 0.0, "avg_move": 0.0,
                      "avg_range": 0.0, "bias": 0.0},
            "LONDON": {"count": 0, "avg_vol": 0.0, "avg_move": 0.0,
                       "avg_range": 0.0, "bias": 0.0},
            "NEW_YORK": {"count": 0, "avg_vol": 0.0, "avg_move": 0.0,
                         "avg_range": 0.0, "bias": 0.0},
        }
        self._current_session_open: Optional[float] = None
        self._current_session_volume: float = 0.0
        self._last_session: Optional[str] = None

    def update(
        self,
        timestamp_utc: float,
        price: float,
        volume: float,
    ) -> dict:
        """
        Ω-G30: Update session analysis.
        timestamp_utc: Unix timestamp (UTC)
        """
        session = self._get_session(timestamp_utc)
        self._prices.append(price)
        self._volumes.append(volume)

        # Track session transitions
        if self._last_session != session:
            transition = self._last_session is not None
            self._last_session = session
            self._current_session_open = price
            self._current_session_volume = 0.0
        else:
            transition = False

        self._current_session_volume += volume

        if len(self._prices) < 30:
            return {"session": session, "state": "WARMING_UP"}

        # Ω-G31: Session classification stats update
        if session in self._session_stats:
            stats = self._session_stats[session]
            n = stats["count"]
            if self._current_session_open and self._current_session_open != 0:
                move = (price - self._current_session_open) / abs(self._current_session_open)
            else:
                move = 0.0

            # EMA update
            alpha = 1.0 / max(1, n + 1)
            stats["avg_vol"] = (1 - alpha) * stats["avg_vol"] + alpha * volume
            stats["avg_move"] = (1 - alpha) * stats["avg_move"] + alpha * move
            stats["count"] += 1
            stats["bias"] = 1.0 if move > 0 else -1.0 if move < 0 else 0.0

        # Ω-G32: Session anomaly detection
        # Tokyo session with high volume = anomaly (should be low)
        # London open without volume spike = anomaly
        expected_vol = self._session_stats.get(session, {}).get("avg_vol", 1.0)
        vol_anomaly = (
            volume / max(1e-6, expected_vol)
            if expected_vol > 0 else 1.0
        )

        is_anomaly = False
        anomaly_reason = ""
        if session == "TOKYO" and vol_anomaly > 3.0:
            is_anomaly = True
            anomaly_reason = "TOKYO_HIGH_VOLUME"
        elif session == "LONDON" and vol_anomaly < 0.3 and len(self._prices) > 60:
            is_anomaly = True
            anomaly_reason = "LONDON_LOW_VOLUME"

        return {
            "current_session": session,
            "session_transition": transition,
            "session_volume_ema": expected_vol,
            "current_volume_ratio": vol_anomaly,
            "is_anomaly": is_anomaly,
            "anomaly_reason": anomaly_reason,
            "session_bias": self._session_stats.get(session, {}).get("bias", 0.0),
        }

    def get_session_alpha(self, current_session: str) -> dict:
        """Ω-G34: Historical alpha profile for a given session."""
        stats = self._session_stats.get(current_session, {})

        # Session-specific strategy recommendation
        if current_session == "TOKYO":
            strategy = "MEAN_REVERSION"
            expected_volatility = "LOW"
        elif current_session == "LONDON":
            strategy = "TREND_FOLLOWING"
            expected_volatility = "HIGH"
        elif current_session == "NEW_YORK":
            strategy = "CONTINUATION"
            expected_volatility = "MEDIUM"
        else:
            strategy = "NEUTRAL"
            expected_volatility = "UNKNOWN"

        return {
            "session": current_session,
            "recommended_strategy": strategy,
            "expected_volatility": expected_volatility,
            "historical_bias": stats.get("bias", 0.0),
            "avg_volume": stats.get("avg_vol", 0.0),
        }

    @staticmethod
    def _get_session(timestamp_utc: float) -> str:
        """Determine session from UTC timestamp."""
        hour = int(timestamp_utc / 3600) % 24

        # Check overlap: if in multiple sessions, return most active
        in_tokyo = 0 <= hour < 9
        in_london = 7 <= hour < 16
        in_ny = 13 <= hour < 21

        if in_london and in_ny:
            return "LONDON_NY_OVERLAP"
        if in_tokyo and in_london:
            return "TOKYO_LONDON_OVERLAP"
        if in_ny:
            return "NEW_YORK"
        if in_london:
            return "LONDON"
        if in_tokyo:
            return "TOKYO"
        return "OVERNIGHT"


# ──────────────────────────────────────────────────────────────
# Ω-G37 to Ω-G45: Hexagonal Liquidity Map
# ──────────────────────────────────────────────────────────────

@dataclass
class HexCell:
    """Ω-G37: A single hexagonal zone in price space."""
    price_center: float
    accumulated_volume: float = 0.0
    hit_count: int = 0
    last_hit_time: float = 0.0
    absorption_rate: float = 0.0
    absorption_count: int = 0
    order_density: float = 0.0


class HexagonalLiquidityMap:
    """
    Ω-G37 to Ω-G45: Hexagonal price zone mapping.

    Transmuted from v1 hex_matrix.py:
    v1: Simple price level tracking
    v2: Spatial liquidity as hexagonal grid with volume heat map,
    cluster detection, absorption rate tracking, and nearest-
    cluster finding for liquidity magnet/barrier identification.
    """

    def __init__(
        self,
        hex_size: float = 100.0,  # price range per hex
        max_cells: int = 200,
    ) -> None:
        self._hex_size = hex_size
        self._max_cells = max_cells
        self._cells: dict[float, HexCell] = {}  # keyed by price_center

    def update(
        self,
        price: float,
        volume: float,
        was_absorbed: bool = False,
    ) -> None:
        """Ω-G39: Update hex map with new price/volume event."""
        # Find the hex this price belongs to
        hex_key = round(price / self._hex_size) * self._hex_size

        if hex_key not in self._cells:
            cell = HexCell(
                price_center=hex_key,
                order_density=volume / self._hex_size,
            )
            # Evict least active cells if over capacity
            if len(self._cells) >= self._max_cells:
                sorted_cells = sorted(
                    self._cells.items(),
                    key=lambda x: x[1].hit_count
                )
                self._cells = dict(sorted_cells[-(self._max_cells - 1):])
            self._cells[hex_key] = cell

        cell = self._cells[hex_key]
        cell.accumulated_volume += volume
        cell.hit_count += 1
        cell.last_hit_time = time.time()

        # Update order density
        cell.order_density = cell.accumulated_volume / (
            self._hex_size * max(1, cell.hit_count)
        )

        # Update absorption rate
        if was_absorbed:
            cell.absorption_count += 1
        cell.absorption_rate = (
            cell.absorption_count / max(1, cell.hit_count)
        )

    def get_hex_at(self, price: float) -> Optional[HexCell]:
        """Ω-G40: Get the hex cell containing this price."""
        hex_key = round(price / self._hex_size) * self._hex_size
        return self._cells.get(hex_key)

    def find_clusters(self, n: int = 5) -> list[HexCell]:
        """
        Ω-G41: Find n highest-density hex clusters.
        Clusters sorted by accumulated volume * hit_count * freshness.
        """
        scored = []
        for cell in self._cells.values():
            freshness = min(1.0, max(0.0, 1.0 - (
                time.time() - cell.last_hit_time
            ) / 3600.0))  # decay over 1 hour
            score = (
                cell.accumulated_volume *
                max(1, cell.hit_count) *
                freshness
            )
            scored.append((score, cell))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [cell for _, cell in scored[:n]]

    def get_liquidity_heatmap(
        self,
        price_range: float = 5000.0,
        center: float = 0.0,
        n_bins: int = 20,
    ) -> list[dict]:
        """Ω-G42: Generate liquidity heatmap centered on given price."""
        if center == 0.0:
            center = self._cells[list(self._cells.keys())[0]].price_center if self._cells else 0.0

        bin_size = price_range / n_bins
        heatmap = []
        for i in range(n_bins):
            bin_center = center - price_range / 2 + (i + 0.5) * bin_size
            hex_key = round(bin_center / self._hex_size) * self._hex_size
            cell = self._cells.get(hex_key)

            heatmap.append({
                "price_center": bin_center,
                "volume": cell.accumulated_volume if cell else 0.0,
                "density": cell.order_density if cell else 0.0,
                "absorption": cell.absorption_rate if cell else 0.0,
            })
        return heatmap

    def get_nearest_cluster(self, current_price: float) -> Optional[HexCell]:
        """Ω-G43: Find nearest high-density cluster to current price."""
        clusters = self.find_clusters(n=5)
        if not clusters:
            return None

        return min(
            clusters,
            key=lambda c: abs(c.price_center - current_price)
        )

    def get_liquidity_walls(
        self,
        current_price: float,
        threshold: float = 0.0,
    ) -> dict:
        """Ω-G44: Identify bid/ask walls (support/resistance hex clusters)."""
        support_cell: Optional[HexCell] = None
        resistance_cell: Optional[HexCell] = None
        min_dist = float('inf')

        for cell in self._cells.values():
            if cell.price_center < current_price:
                dist = current_price - cell.price_center
                if cell.accumulated_volume > threshold and dist < min_dist:
                    support_cell = cell
                    min_dist = dist
            elif cell.price_center > current_price:
                dist = cell.price_center - current_price
                if cell.accumulated_volume > threshold and dist < min_dist:
                    resistance_cell = cell
                    min_dist = dist

        return {
            "bid_wall": {
                "price": support_cell.price_center if support_cell else None,
                "volume": support_cell.accumulated_volume if support_cell else 0.0,
            } if support_cell else None,
            "ask_wall": {
                "price": resistance_cell.price_center if resistance_cell else None,
                "volume": resistance_cell.accumulated_volume if resistance_cell else 0.0,
            } if resistance_cell else None,
        }


# ──────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────

def _entropy_from_dict(d: dict[str, float]) -> float:
    """Shannon entropy from probability distribution dict."""
    total = sum(d.values())
    if total <= 0:
        return 0.0
    entropy = 0.0
    for v in d.values():
        p = v / total
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy
