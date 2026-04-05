"""
SOLÉNN v2 — Adaptive Parameter Tuning (Ω-C118 a Ω-C126)
Gradient-free optimization, sensitivity analysis, A/B testing, drift detection,
regime adaptation, cooling schedule, parameter ensemble, audit trail.
"""

from __future__ import annotations

import math
import random
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True, slots=True)
class TuningResult:
    param_name: str
    old_value: float
    new_value: float
    old_score: float
    new_score: float
    timestamp: float = field(default_factory=time.time)


@dataclass(frozen=True, slots=True)
class SensitivityResult:
    param_name: str
    sensitivity: float
    direction: str


@dataclass(frozen=True, slots=True)
class ABTestResult:
    param_a: float
    param_b: float
    score_a: float
    score_b: float
    winner: str


class ParameterOptimizer:
    """Ω-C119: Gradient-free parameter optimization using random hill climbing."""

    def __init__(self, score_fn: Callable[[dict[str, float]], float], param_bounds: dict[str, tuple[float, float]], cooling_rate: float = 0.999, initial_temp: float = 100.0) -> None:
        self._score_fn = score_fn
        self._bounds = param_bounds
        self._cooling_rate = cooling_rate
        self._temperature = initial_temp
        self._history: list[TuningResult] = []

    def optimize(self, current_params: dict[str, float], max_iterations: int = 100) -> dict[str, float]:
        best = dict(current_params)
        best_score = self._score_fn(best)
        current = dict(current_params)
        current_score = best_score

        for _ in range(max_iterations):
            neighbor = {}
            for param, (low, high) in self._bounds.items():
                rng = (high - low) * max(0.01, 0.1 * self._temperature / 100.0)
                neighbor[param] = max(low, min(high, current[param] + random.uniform(-rng, rng)))
            neighbor_score = self._score_fn(neighbor)

            if neighbor_score > current_score:
                current = dict(neighbor)
                current_score = neighbor_score
                if neighbor_score > best_score:
                    best = dict(neighbor)
                    best_score = neighbor_score
                    for param in self._bounds:
                        self._history.append(TuningResult(
                            param, current_params.get(param, 0), neighbor[param],
                            self._score_fn(current_params), neighbor_score,
                        ))
            else:
                current_score_val = current_score
                accept_prob = math.exp((neighbor_score - current_score_val) / max(self._temperature, 1e-10))
                if random.random() < accept_prob:
                    current = dict(neighbor)
                    current_score = neighbor_score
            self._temperature *= self._cooling_rate
        return best

    def get_history(self, last_n: int = 50) -> list[TuningResult]:
        return self._history[-last_n:]


class ParameterCoolingSchedule:
    """Ω-C124: Cooling schedule for adaptive tuning rate."""

    def __init__(self, initial_rate: float = 0.999, min_rate: float = 0.95, stability_threshold: float = 0.01) -> None:
        self._rate = initial_rate
        self._min_rate = min_rate
        self._stability_threshold = stability_threshold
        self._score_history: deque[float] = deque(maxlen=20)

    def update_adaptation_rate(self, current_score: float) -> float:
        self._score_history.append(current_score)
        if len(self._score_history) >= 20:
            scores = list(self._score_history)
            variance = sum((s - sum(scores) / len(scores)) ** 2 for s in scores) / len(scores)
            if variance < self._stability_threshold:
                self._rate = max(self._min_rate, self._rate * 0.99)
            else:
                self._rate = min(1.0, self._rate * 1.001)
        return self._rate

    def get_current_rate(self) -> float:
        return self._rate


class ParameterRegimeAdapter:
    """Ω-C123: Different optimal values per market regime."""

    def __init__(self) -> None:
        self._regime_params: dict[str, dict[str, float]] = {}
        self._current_regime: str = "unknown"

    def update_regime(self, regime: str) -> None:
        self._current_regime = regime

    def recommend_params(self, param_name: str, regime: str | None = None) -> float | None:
        target = regime or self._current_regime
        params = self._regime_params.get(target, {})
        return params.get(param_name)

    def store_regime_params(self, regime: str, params: dict[str, float]) -> None:
        self._regime_params[regime] = params

    def get_regime_map(self) -> dict[str, dict[str, float]]:
        return dict(self._regime_params)


class ParameterEnsemble:
    """Ω-C125: Multiple configs active simultaneously with weighting."""

    def __init__(self) -> None:
        self._configs: dict[str, tuple[dict[str, Any], float]] = {}

    def add_config(self, name: str, config: dict[str, Any], weight: float) -> None:
        self._configs[name] = (config, weight)

    def remove_config(self, name: str) -> None:
        self._configs.pop(name, None)

    def get_combined(self) -> dict[str, Any]:
        total_weight = sum(w for _, w in self._configs.values())
        if total_weight <= 0:
            return {}
        combined: dict[str, Any] = defaultdict(float)
        for config, weight in self._configs.values():
            for key, value in config.items():
                if isinstance(value, (int, float)):
                    combined[key] += value * weight / total_weight
                else:
                    combined[key] = value
        return dict(combined)

    def reweight(self, name: str, score: float) -> None:
        old = self._configs.get(name)
        if old:
            new_weight = max(0.01, old[1] * (1.0 + score))
            self._configs[name] = (old[0], new_weight)
