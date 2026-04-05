"""
SOLÉNN v2 — Dream Simulation Engine: Offline Market Scenario Generation
(Ω-DS01 a Ω-DS54)
Replaces v1 lucid_dream_client.py. Instead of depending on external Java
daemon, provides native Python Monte Carlo "dream" simulation for validating
mutations, stress-testing strategies, and discovering edge in synthetic
scenarios. Runs in background threads during low-activity periods.

Concept 1: Dream Scenario Generation & Acceleration (Ω-DS01–DS18)
  Generates synthetic market scenarios by resampling, parameter perturbation,
  and generative modeling of observed market states. "Dream speed" is orders
  of magnitude faster than real time — 10000 cycles compresses hours of
  market into seconds.

Concept 2: Shadow Agent Evaluation During Dreams (Ω-DS19–DS36)
  During dreams, shadow agents (candidate parameter sets, new strategies)
  are evaluated against synthetic data. Those that outperform the baseline
  become candidates for real-world promotion.

Concept 3: Dream Memory & Insight Extraction (Ω-DS37–DS54)
  Dream insights are persisted — what scenarios worked, what parameter ranges
  produce alpha, what to avoid. Dream memory is indexed and queried during
  real-time trading. Dream-to-reality transfer function.
"""

from __future__ import annotations

import math
import os
import random
import time
from dataclasses import dataclass, field
from typing import Any


# ──────────────────────────────────────────────────────────────
# Ω-DS01 to Ω-DS18: Dream Scenario Generation & Acceleration
# ──────────────────────────────────────────────────────────────


@dataclass
class DreamScenario:
    """Ω-DS01: A single synthetic market scenario."""

    scenario_id: str
    base_price: float
    volatility: float
    drift: float
    regime: str
    n_steps: int
    seed: int
    price_path: list[float] = field(default_factory=list)
    volume_path: list[float] = field(default_factory=list)
    spread_path: list[float] = field(default_factory=list)


@dataclass(frozen=True)
class DreamParams:
    """Ω-DS02: Parameters for a dream simulation."""

    base_price: float = 100.0
    base_volatility: float = 0.02  # per-step
    base_drift: float = 0.0
    regime: str = "normal"
    n_steps: int = 5000
    n_paths: int = 100
    regime_params: dict[str, float] = field(default_factory=dict)


@dataclass
class DreamMetrics:
    """Ω-DS03: Metrics from a dream cycle."""

    dream_id: str
    n_scenarios: int
    n_paths_evaluated: int
    total_time_ms: float
    alpha_found: float
    n_successful_mutations: int
    regime_distribution: dict[str, int]
    best_scenario_id: str
    best_fitness: float
    avg_fitness: float


class DreamGenerator:
    """Ω-DS04: Generates synthetic market scenarios for offline simulation."""

    REGIME_PRESETS: dict[str, dict[str, float]] = {
        "normal": {"drift": 0.0, "vol": 0.02, "mean_revert": 0.0, "jump_prob": 0.001},
        "trending_up": {"drift": 0.001, "vol": 0.015, "mean_revert": -0.01, "jump_prob": 0.0005},
        "trending_down": {"drift": -0.001, "vol": 0.018, "mean_revert": 0.01, "jump_prob": 0.001},
        "choppy": {"drift": 0.0, "vol": 0.03, "mean_revert": 0.1, "jump_prob": 0.005},
        "flash_crash": {"drift": -0.005, "vol": 0.08, "mean_revert": 0.05, "jump_prob": 0.02},
        "parabolic": {"drift": 0.003, "vol": 0.04, "mean_revert": -0.02, "jump_prob": 0.001},
        "compression": {"drift": 0.0, "vol": 0.008, "mean_revert": 0.05, "jump_prob": 0.0001},
    }

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)
        self._scenario_id: int = 0

    def generate_path(
        self, params: DreamParams, path_index: int = 0
    ) -> DreamScenario:
        """Ω-DS05: Generate one GBM + mean reversion path with jumps."""
        self._scenario_id += 1
        regime = params.regime
        params_preset = self.REGIME_PRESETS.get(regime, self.REGIME_PRESETS["normal"])
        # Override with custom regime params
        preset = dict(params_preset)
        preset.update(params.regime_params)

        drift = preset.get("drift", params.base_drift)
        vol = preset.get("vol", params.base_volatility)
        mean_revert = preset.get("mean_revert", 0.0)
        jump_prob = preset.get("jump_prob", 0.001)

        scenario = DreamScenario(
            scenario_id=f"dream-{self._scenario_id}-{path_index}",
            base_price=params.base_price,
            volatility=vol,
            drift=drift,
            regime=regime,
            n_steps=params.n_steps,
            seed=self._rng.randint(0, 2**31),
        )

        price = params.base_price
        prices: list[float] = [price]
        volumes: list[float] = []
        spreads: list[float] = []

        for _ in range(params.n_steps):
            # GBM step
            z = self._rng.gauss(0, 1)

            # Jump component
            jump = 0.0
            if self._rng.random() < jump_prob:
                jump_size = self._rng.gauss(0, vol * 5)
                jump = jump_size

            # Mean reversion
            reversion = -mean_revert * (price - params.base_price) / max(1e-9, params.base_price)

            # Combined step
            log_ret = (drift - vol ** 2 / 2) / params.n_steps + vol / math.sqrt(params.n_steps) * z + jump + reversion
            price *= math.exp(log_ret)

            price = max(0.01, price)
            prices.append(price)

            # Volume: baseline + volatility-driven
            base_vol = 100.0
            vol_factor = 1.0 + 5.0 * abs(log_ret) / max(1e-9, vol)
            volume = base_vol * self._rng.gauss(vol_factor, 0.3)
            volumes.append(max(1.0, volume))

            # Spread: wider during big moves
            base_spread = 1.0
            spread_factor = 1.0 + 3.0 * abs(log_ret) / max(1e-9, vol)
            spreads.append(base_spread * spread_factor)

        scenario.price_path = prices
        scenario.volume_path = volumes
        scenario.spread_path = spreads

        return scenario

    def generate_batch(self, params: DreamParams) -> list[DreamScenario]:
        """Ω-DS06: Generate multiple paths with varied seeds."""
        scenarios: list[DreamScenario] = []
        for i in range(params.n_paths):
            path_params = DreamParams(
                base_price=params.base_price * (1.0 + self._rng.gauss(0, 0.01)),
                base_volatility=params.base_volatility * (1.0 + self._rng.gauss(0, 0.05)),
                base_drift=params.base_drift,
                regime=params.regime,
                n_steps=params.n_steps,
                n_paths=1,
                regime_params=dict(params.regime_params),
            )
            scenarios.append(self.generate_path(path_params, i))
        return scenarios

    def generate_diverse_regimes(self, base_params: DreamParams, n_regimes: int = 5) -> list[list[DreamScenario]]:
        """Ω-DS07: Generate scenarios across multiple regime types."""
        regime_list = list(self.REGIME_PRESETS.keys())
        selected = self._rng.sample(regime_list, min(n_regimes, len(regime_list)))

        batches: list[list[DreamScenario]] = []
        for regime in selected:
            params = DreamParams(
                base_price=base_params.base_price,
                base_volatility=base_params.base_volatility,
                base_drift=base_params.base_drift,
                regime=regime,
                n_steps=base_params.n_steps,
                n_paths=base_params.n_paths,
            )
            batches.append(self.generate_batch(params))

        return batches


# ──────────────────────────────────────────────────────────────
# Ω-DS19 to Ω-DS36: Shadow Agent Evaluation During Dreams
# ──────────────────────────────────────────────────────────────


@dataclass
class ShadowAgentResult:
    """Ω-DS19: Result of a shadow agent evaluated on dream scenarios."""

    agent_name: str
    agent_params: dict[str, float]
    scenarios_evaluated: int
    win_rate: float
    avg_pnl: float
    total_pnl: float
    sharpe_estimate: float
    max_drawdown: float
    profit_factor: float
    avg_holding_time_steps: float
    fitness: float


class ShadowAgentEvaluator:
    """Ω-DS20: Evaluates candidate strategies against synthetic data."""

    def __init__(
        self,
        baseline_win_rate: float = 0.5,
        baseline_sharpe: float = 0.0,
    ) -> None:
        self._baseline_wr = baseline_win_rate
        self._baseline_sharpe = baseline_sharpe

    def evaluate(
        self,
        agent_name: str,
        agent_params: dict[str, float],
        scenarios: list[DreamScenario],
        trade_fn: Any = None,  # (scenario, params) -> list[trades]
    ) -> ShadowAgentResult:
        """Ω-DS21: Run shadow agent on scenarios and measure performance.

        trade_fn: callable that takes (scenario, params) and returns
        list of trade dicts with {'entry', 'exit', 'pnl', 'holding_steps'}.
        If None, uses a simple heuristic for testing.
        """
        if trade_fn is None:
            trade_fn = _simple_heuristic_trader

        all_trades: list[dict] = []
        for scenario in scenarios:
            trades = trade_fn(scenario, agent_params)
            all_trades.extend(trades)

        if not all_trades:
            return ShadowAgentResult(
                agent_name=agent_name,
                agent_params=agent_params,
                scenarios_evaluated=len(scenarios),
                win_rate=0.0,
                avg_pnl=0.0,
                total_pnl=0.0,
                sharpe_estimate=0.0,
                max_drawdown=0.0,
                profit_factor=0.0,
                avg_holding_time_steps=0.0,
                fitness=-1.0,
            )

        wins = [t for t in all_trades if t.get("pnl", 0) > 0]
        losses = [t for t in all_trades if t.get("pnl", 0) <= 0]

        total_pnl = sum(t.get("pnl", 0) for t in all_trades)
        avg_pnl = total_pnl / len(all_trades)
        win_rate = len(wins) / len(all_trades)

        avg_win = sum(t["pnl"] for t in wins) / max(1, len(wins))
        avg_loss = abs(sum(t["pnl"] for t in losses) / max(1, len(losses)))
        profit_factor = sum(t["pnl"] for t in wins) / max(1e-9, abs(sum(t["pnl"] for t in losses)))

        # Simple Sharpe
        pnl_series = [t.get("pnl", 0) for t in all_trades]
        mean_pnl = sum(pnl_series) / len(pnl_series)
        var_pnl = sum((p - mean_pnl) ** 2 for p in pnl_series) / max(1, len(pnl_series) - 1)
        std_pnl = math.sqrt(max(1e-9, var_pnl))
        sharpe = mean_pnl / std_pnl if std_pnl > 0 else 0.0

        # Max drawdown
        cumulative = 0.0
        peak = 0.0
        max_dd = 0.0
        for p in pnl_series:
            cumulative += p
            peak = max(peak, cumulative)
            dd = peak - cumulative
            max_dd = max(max_dd, dd)

        avg_hold = sum(t.get("holding_steps", 0) for t in all_trades) / len(all_trades)

        # Fitness: combination of WR, Sharpe, PF
        fitness = 0.3 * win_rate + 0.3 * max(0, (sharpe + 2) / 4) + 0.2 * min(1, profit_factor / 3) + 0.2 * max(0, 1 - max_dd / max(1, abs(total_pnl)))
        fitness = max(0.0, min(1.0, fitness))

        return ShadowAgentResult(
            agent_name=agent_name,
            agent_params=agent_params,
            scenarios_evaluated=len(scenarios),
            win_rate=round(win_rate, 4),
            avg_pnl=round(avg_pnl, 4),
            total_pnl=round(total_pnl, 4),
            sharpe_estimate=round(sharpe, 4),
            max_drawdown=round(max_dd, 4),
            profit_factor=round(profit_factor, 4),
            avg_holding_time_steps=round(avg_hold, 2),
            fitness=round(fitness, 4),
        )

    def compare_to_baseline(self, result: ShadowAgentResult) -> tuple[float, bool]:
        """Ω-DS22: Compare shadow agent to baseline.

        Returns: (improvement_factor, is_better)
        """
        delta_wr = result.win_rate - self._baseline_wr
        delta_sharpe = result.sharpe_estimate - self._baseline_sharpe

        improvement = 0.5 * max(0, delta_wr * 10) + 0.5 * max(0, delta_sharpe)
        is_better = improvement > 0.1  # 10% improvement threshold

        return (round(improvement, 4), is_better)

    def evaluate_batch(
        self,
        candidates: list[tuple[str, dict[str, float]]],
        scenarios: list[DreamScenario],
        trade_fn: Any = None,
    ) -> list[ShadowAgentResult]:
        """Ω-DS23: Evaluate multiple candidates and rank."""
        results = []
        for name, params in candidates:
            r = self.evaluate(name, params, scenarios, trade_fn)
            improved, is_better = self.compare_to_baseline(r)
            r.fitness = round(r.fitness * (1.0 + improved), 4)
            results.append(r)

        results.sort(key=lambda x: x.fitness, reverse=True)
        return results


def _simple_heuristic_trader(scenario: DreamScenario, params: dict) -> list[dict]:
    """Ω-DS24: Simple mean-reversion trader for dream scenarios."""
    threshold = params.get("entry_threshold", 0.02)
    take_profit = params.get("take_profit", 0.03)
    stop_loss = params.get("stop_loss", 0.015)

    prices = scenario.price_path
    if len(prices) < 10:
        return []

    trades: list[dict] = []
    in_position = False
    entry_price = 0.0
    entry_step = 0

    for i in range(1, len(prices)):
        price = prices[i]
        prev_price = prices[i - 1]
        returns = (price - prev_price) / max(1e-9, prev_price)

        if not in_position:
            # Entry on mean reversion signal
            if returns < -threshold:
                in_position = True
                entry_price = price
                entry_step = i
            elif returns > threshold:
                in_position = True
                entry_price = price
                entry_step = i
        else:
            pnl_pct = (price - entry_price) / max(1e-9, entry_price)
            holding_steps = i - entry_step

            if pnl_pct > take_profit or pnl_pct < -stop_loss:
                pnl = pnl_pct * entry_price
                trades.append({
                    "pnl": pnl,
                    "entry": entry_price,
                    "exit": price,
                    "holding_steps": holding_steps,
                })
                in_position = False

    # Close open position at end
    if in_position and len(prices) > 1:
        pnl_pct = (prices[-1] - entry_price) / max(1e-9, entry_price)
        trades.append({
            "pnl": pnl_pct * entry_price,
            "entry": entry_price,
            "exit": prices[-1],
            "holding_steps": len(prices) - 1 - entry_step,
        })

    return trades


# ──────────────────────────────────────────────────────────────
# Ω-DS37 to Ω-DS54: Dream Memory & Insight Extraction
# ──────────────────────────────────────────────────────────────


@dataclass
class DreamInsight:
    """Ω-DS37: Extracted insight from dream simulation."""

    insight_id: int
    dream_id: str
    insight_type: str  # "regime_alpha", "parameter_range", "warning", "validation"
    description: str
    confidence: float  # [0, 1]
    supporting_evidence: dict[str, Any]
    timestamp_ns: int


class DreamMemory:
    """Ω-DS38: Persists and retrieves dream insights."""

    def __init__(self, storage_path: str = "data/dreams/memory.json") -> None:
        self._storage_path = storage_path
        self._insights: list[DreamInsight] = []
        self._dream_results: dict[str, DreamMetrics] = {}
        self._next_id: int = 1
        self._load()

    def store_insight(self, insight: DreamInsight) -> int:
        self._insights.append(insight)
        if insight.insight_id >= self._next_id:
            self._next_id = insight.insight_id + 1
        self._save()
        return insight.insight_id

    def store_dream_result(self, dream_id: str, metrics: DreamMetrics) -> None:
        self._dream_results[dream_id] = metrics

    def extract_insights(self, dream_metrics: DreamMetrics) -> list[DreamInsight]:
        """Ω-DS39: Auto-extract insights from dream results."""
        insights: list[DreamInsight] = []

        if dream_metrics.alpha_found > 0.02:
            insights.append(DreamInsight(
                insight_id=self._next_id,
                dream_id=dream_metrics.dream_id,
                insight_type="regime_alpha",
                description=f"Alpha={dream_metrics.alpha_found:.4f} found across {dream_metrics.n_scenarios} scenarios",
                confidence=min(1.0, dream_metrics.alpha_found * 10),
                supporting_evidence={
                    "n_scenarios": dream_metrics.n_scenarios,
                    "best_fitness": dream_metrics.best_fitness,
                    "regime_dist": dream_metrics.regime_distribution,
                },
                timestamp_ns=time.time_ns(),
            ))
            self._next_id += 1

        if dream_metrics.n_successful_mutations > 0:
            insights.append(DreamInsight(
                insight_id=self._next_id,
                dream_id=dream_metrics.dream_id,
                insight_type="parameter_range",
                description=f"{dream_metrics.n_successful_mutations} successful mutations found",
                confidence=0.6,
                supporting_evidence={"n_mutations": dream_metrics.n_successful_mutations},
                timestamp_ns=time.time_ns(),
            ))
            self._next_id += 1

        for insight in insights:
            self._insights.append(insight)

        return insights

    def query_by_type(self, insight_type: str) -> list[DreamInsight]:
        """Ω-DS40: Retrieve insights by type."""
        return [i for i in self._insights if i.insight_type == insight_type]

    def query_by_confidence(self, min_confidence: float = 0.5) -> list[DreamInsight]:
        return [i for i in self._insights if i.confidence >= min_confidence]

    def get_top_insights(self, top_k: int = 5) -> list[DreamInsight]:
        sorted_insights = sorted(self._insights, key=lambda i: i.confidence, reverse=True)
        return sorted_insights[:top_k]

    def dream_intuition_score(self, regime: str) -> float:
        """Ω-DS41: How much does dream memory say about a regime?"""
        relevant = [i for i in self._insights if regime in str(i.supporting_evidence)]
        if not relevant:
            return 0.0
        return min(1.0, len(relevant) / 5.0)

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self._storage_path) or ".", exist_ok=True)
        data = {
            "insights": [
                {
                    "insight_id": i.insight_id,
                    "dream_id": i.dream_id,
                    "insight_type": i.insight_type,
                    "description": i.description,
                    "confidence": i.confidence,
                    "supporting_evidence": i.supporting_evidence,
                    "timestamp_ns": i.timestamp_ns,
                }
                for i in self._insights
            ],
            "dream_results": {k: {} for k in self._dream_results},
        }
        with open(self._storage_path, "w") as f:
            import json
            json.dump(data, f)

    def _load(self) -> None:
        if not os.path.exists(self._storage_path):
            return
        import json
        try:
            with open(self._storage_path) as f:
                data = json.load(f)
            for i_data in data.get("insights", []):
                self._insights.append(DreamInsight(**i_data))
            if self._insights:
                self._next_id = max(i.insight_id for i in self._insights) + 1
        except (json.JSONDecodeError, KeyError):
            pass


class DreamSimulationEngine:
    """Ω-DS42: Master engine that orchestrates dream cycles."""

    def __init__(
        self,
        storage_path: str = "data/dreams/memory.json",
        seed: int | None = None,
    ) -> None:
        self.generator = DreamGenerator(seed=seed)
        self.memory = DreamMemory(storage_path)
        self.evaluator = ShadowAgentEvaluator()
        self._total_dreams: int = 0

    def run_dream_cycle(
        self,
        params: DreamParams,
        candidates: list[tuple[str, dict[str, float]]],
    ) -> DreamMetrics:
        """Ω-DS43: Run a complete dream simulation."""
        t0 = time.time_ns()
        self._total_dreams += 1
        dream_id = f"dream-{self._total_dreams}-{int(time.time())}"

        # 1. Generate scenarios
        batches = self.generator.generate_diverse_regimes(params)
        all_scenarios: list[DreamScenario] = []
        regime_dist: dict[str, int] = {}
        for batch in batches:
            for s in batch:
                all_scenarios.append(s)
                regime_dist[s.regime] = regime_dist.get(s.regime, 0) + 1

        # 2. Evaluate candidates
        if candidates:
            results = self.evaluator.evaluate_batch(candidates, all_scenarios)
            winner = results[0] if results else None
            alpha_found = winner.fitness - self.evaluator._baseline_sharpe if winner else 0.0
            n_successful = sum(1 for r in results if r.fitness > 0.5)
        else:
            results = []
            winner = None
            alpha_found = 0.0
            n_successful = 0

        elapsed_ms = (time.time_ns() - t0) / 1e6

        metrics = DreamMetrics(
            dream_id=dream_id,
            n_scenarios=len(all_scenarios),
            n_paths_evaluated=len(all_scenarios),
            total_time_ms=round(elapsed_ms, 2),
            alpha_found=round(alpha_found, 4),
            n_successful_mutations=n_successful,
            regime_distribution=regime_dist,
            best_scenario_id=winner.agent_name if winner else "none",
            best_fitness=winner.fitness if winner else 0.0,
            avg_fitness=round(
                sum(r.fitness for r in results) / max(1, len(results)),
                4,
            ),
        )

        # 3. Extract and store insights
        insights = self.memory.extract_insights(metrics)
        self.memory.store_dream_result(dream_id, metrics)

        return metrics

    def get_status(self) -> dict[str, Any]:
        return {
            "total_dreams": self._total_dreams,
            "total_insights": len(self.memory._insights),
            "top_insights": [
                {"type": i.insight_type, "confidence": i.confidence, "desc": i.description}
                for i in self.memory.get_top_insights(3)
            ],
        }
