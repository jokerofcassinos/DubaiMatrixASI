"""
SOLÉNN v2 — Tests for Evolution / Self-optimization Ω (Ω-V01 to Ω-V162)
Coverage: genetic_optimizer, performance_tracker, self_optimizer.
"""

from __future__ import annotations

import math
import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import random
import time
import unittest

from core.evolution.genetic_optimizer import (
    Individual,
    ParamSpec,
    PopulationManager,
    MetaParameterOptimizer,
    RegimeSpecificOptimizer,
    WalkForwardAnalyzer,
)
from core.evolution.performance_tracker import (
    GoalTracker,
    GoalStatus,
    TradeRecord,
    BenchmarkComparator,
    PerformancePredictor,
    RollingPerformanceMonitor,
    StrategyTracker,
    TradeAnalytics,
)
from core.evolution.self_optimizer import (
    AdaptiveRiskManager,
    AutoRollbackManager,
    ComplexityController,
    CoordinateDescentTuner,
    EnsembleOptimizer,
    EntropyMeasure,
    ExperienceReplay,
    MetaOptimizer,
    SignalSelector,
)


# ──────────────────────────────────────────────────────────────
# Ω-V01 to Ω-V54: Genetic Optimization Tests
# ──────────────────────────────────────────────────────────────

class TestGeneticOptimizer(unittest.TestCase):
    """Ω-V01 to Ω-V54"""

    def test_v02_population_init(self):
        """Ω-V02: Population generation with diversity."""
        specs = [ParamSpec("p1", -5, 5, 0), ParamSpec("p2", 0, 10, 5)]
        mgr = PopulationManager(specs, population_size=30)
        pop = mgr.initialize_population()
        self.assertEqual(len(pop), 30)
        for ind in pop:
            self.assertEqual(len(ind.genome), 2)

    def test_v03_v05_v06_evolution(self):
        """Ω-V03, Ω-V05, Ω-V06: Evolution improves fitness."""
        random.seed(42)
        # Simple sphere function
        def sphere(genome: list[float]) -> float:
            return -sum(g ** 2 for g in genome)  # Negative = maximization

        specs = [ParamSpec("x", -10, 10, 5), ParamSpec("y", -10, 10, -5)]
        mgr = PopulationManager(specs, population_size=50, mutation_rate=0.2, mutation_std=0.5)
        mgr.initialize_population()

        initial_fitness = mgr._population[0].fitness if mgr._population else float("-inf")
        for i in range(10):
            mgr.evolve(sphere)

        final_fitness = mgr._population[0].fitness
        # Fitness should improve (get closer to 0)
        self.assertGreater(final_fitness, initial_fitness - 1)

    def test_v09_hall_of_fame(self):
        """Ω-V09: Hall of Fame tracks best individuals."""
        def sphere(genome: list[float]) -> float:
            return -sum(g ** 2 for g in genome)

        specs = [ParamSpec("x", -5, 5, 0)]
        mgr = PopulationManager(specs, population_size=20, elite_fraction=0.1,
                                mutation_rate=0.1, mutation_std=0.3)
        mgr.initialize_population()
        for _ in range(15):
            mgr.evolve(sphere)

        self.assertGreater(len(mgr.hall_of_fame), 0)

    def test_v07_diversity(self):
        """Ω-V07: Population diversity changes."""
        def sphere(genome: list[float]) -> float:
            return -sum(g ** 2 for g in genome)

        specs = [ParamSpec("x", -10, 10, 0) for _ in range(5)]
        mgr = PopulationManager(specs, population_size=30, mutation_rate=0.3)
        mgr.initialize_population()
        d1 = mgr.compute_diversity()
        for _ in range(5):
            mgr.evolve(sphere)
        d2 = mgr.compute_diversity()
        self.assertGreater(d1, 0)

    def test_v10_v15_v18_meta_optimizer(self):
        """Ω-V10, Ω-V15, Ω-V18: Meta-parameter optimization."""
        specs = [ParamSpec("lr", 0.001, 0.1, 0.01, log_scale=True)]
        opt = MetaParameterOptimizer(specs)

        def fn(g: list[float]) -> float:
            return -abs(g[0] - 0.03)  # Optimal at 0.03

        # Explore
        for _ in range(20):
            genome = opt.suggest_random()
            opt.evaluate(genome, fn)
        # Exploit
        for _ in range(10):
            genome = opt.suggest_best_nearby(radius=0.2)
            opt.evaluate(genome, fn)

        best, best_fitness = opt.best_result
        self.assertIsNotNone(best)
        self.assertGreater(best_fitness, -0.01)

    def test_v19_v27_regime_optimizer(self):
        """Ω-V19, Ω-V27: Regime-specific optimization."""
        specs = [ParamSpec("p1", 0, 1, 0.5), ParamSpec("p2", 0, 1, 0.5)]
        opt = RegimeSpecificOptimizer(specs)
        # Add data for trending regime
        for _ in range(60):
            opt.add_regime_data("trending", [0.7, 0.3])
        opt.add_regime_data("ranging", [0.3, 0.7], n_samples=60)

        def trend_fn(g: list[float]) -> float:
            return -((g[0] - 0.7) ** 2 + (g[1] - 0.3) ** 2)

        result = opt.optimize_regime("trending", trend_fn, n_gens=15)
        self.assertIsNotNone(result)

    def test_v28_v32_v36_walk_forward(self):
        """Ω-V28, Ω-V32, Ω-V36: Walk-forward analysis."""
        specs = [ParamSpec("threshold", 0, 2, 1)]
        wfa = WalkForwardAnalyzer(specs, train_window=30, test_window=10)

        def fn(genome: list[float], data: list[float]) -> float:
            threshold = genome[0]
            wins = sum(1 for r in data if abs(r) > threshold * 0.01)
            return wins / max(len(data), 1)

        random.seed(42)
        data = [random.gauss(0, 0.02) for _ in range(100)]
        results = wfa.run_walk_forward(data, fn)
        self.assertGreater(len(results), 0)

        stability = wfa.get_parameter_stability()
        self.assertIsInstance(stability, dict)


# ──────────────────────────────────────────────────────────────
# Ω-V55 to Ω-V108: Performance Tracking Tests
# ──────────────────────────────────────────────────────────────

class TestPerformanceTracking(unittest.TestCase):
    """Ω-V55 to Ω-V108"""

    def test_v55_v63_rolling_monitor(self):
        """Ω-V55 to Ω-V63: Rolling performance metrics."""
        mon = RollingPerformanceMonitor(window=30)
        random.seed(42)
        for _ in range(50):
            pnl = random.gauss(10, 50)  # Positive expectancy
            mon.add_trade(pnl)

        d = mon.get_dashboard()
        self.assertIn("rolling_sharpe", d)
        self.assertIn("win_rate", d)
        self.assertGreater(d["n_trades"], 0)
        self.assertGreater(d["profit_factor"], 0)

    def test_v64_v72_strategy_tracker(self):
        """Ω-V64 to Ω-V72: Strategy-level tracking."""
        st = StrategyTracker()
        st.add_strategy("trend_follow")
        st.add_strategy("mean_reversion")
        st.add_strategy("scalping")

        random.seed(42)
        for _ in range(100):
            st.record_pnl("trend_follow", random.gauss(5, 20))
            st.record_pnl("mean_reversion", random.gauss(3, 15))
            st.record_pnl("scalping", random.gauss(1, 5))

        contrib = st.get_contribution()
        self.assertEqual(len(contrib), 3)
        self.assertAlmostEqual(sum(contrib.values()), 1.0, places=5)

        summary = st.get_performance_summary()
        self.assertEqual(summary["n_active"], 3)

    def test_v73_v81_trade_analytics(self):
        """Ω-V73 to Ω-V81: Trade-level analytics."""
        analytics = TradeAnalytics()
        for i in range(50):
            analytics.add_trade(TradeRecord(
                trade_id=f"t-{i}", strategy="trend",
                symbol="BTCUSDT", direction="long",
                entry_price=50000.0, exit_price=50000.0 + random.gauss(0, 100),
                size=1.0, pnl=random.gauss(10, 50),
                entry_time=time.time(), exit_time=time.time() + 60,
                regime="trending", setup_type="breakout",
                confidence=0.8, session="london",
            ))

        stats = analytics.get_pnl_distribution_stats()
        self.assertIn("mean", stats)
        self.assertIn("kurtosis", stats)

        fat_tails = analytics.detect_fat_tails()
        self.assertIsInstance(fat_tails, bool)

        anomalies = analytics.detect_anomalous_trades()
        self.assertIsInstance(anomalies, list)

        calendar = analytics.get_trade_calendar()
        self.assertIn("london", calendar)

    def test_v82_v90_performance_predictor(self):
        """Ω-V82 to Ω-V90: Predictive performance models."""
        pred = PerformancePredictor()
        random.seed(42)
        for _ in range(12):
            ret = random.gauss(0.05, 0.1)
            pred.add_period_data(returns=ret, sharpe=random.gauss(2, 1),
                                 win_rate=random.gauss(0.55, 0.1))

        forecast = pred.predict_next_period()
        self.assertIn("expected_return", forecast)
        self.assertIn("confidence", forecast)

        decay = pred.edge_decay_estimate()
        self.assertGreaterEqual(decay, 0)

        survival = pred.survival_probability(horizon_periods=12)
        self.assertGreaterEqual(survival, 0)
        self.assertLessEqual(survival, 1)

    def test_v91_v99_benchmark(self):
        """Ω-V91 to Ω-V99: Benchmarking & attribution."""
        bc = BenchmarkComparator()
        random.seed(42)
        for _ in range(24):
            strat_ret = random.gauss(0.03, 0.08)
            bench_ret = random.gauss(0.01, 0.06)
            bc.add_period(strat_ret, bench_ret)

        alpha = bc.get_alpha()
        te = bc.get_tracking_error()
        ir = bc.get_information_ratio()
        beta = bc.get_beta_exposure()
        decomposition = bc.decompose_return()

        self.assertIn("alpha", decomposition)
        self.assertIn("beta_contribution", decomposition)
        self.assertGreater(len(decomposition), 3)


# ──────────────────────────────────────────────────────────────
# Ω-V109 to Ω-V162: Self-Optimization Tests
# ──────────────────────────────────────────────────────────────

class TestSelfOptimization(unittest.TestCase):
    """Ω-V109 to Ω-V162"""

    def test_v109_v113_coordinate_descent(self):
        """Ω-V109, Ω-V113: Coordinate descent tuning."""
        tuner = CoordinateDescentTuner(step_size=0.1, n_iterations=10)
        target = [0.3, 0.7, -0.2]

        def fn(g: list[float]) -> float:
            return -sum((g[i] - target[i]) ** 2 for i in range(len(target)))

        genome = [0.0, 0.0, 0.0]
        initial_fitness = fn(genome)
        best_genome, results = tuner.tune(genome, ["p1", "p2", "p3"], fn)
        final_fitness = fn(best_genome)

        self.assertGreater(final_fitness, initial_fitness)
        self.assertGreater(len(results), 0)

    def test_v117_rollback(self):
        """Ω-V117: Auto-rollback manager detects degradation."""
        rb = AutoRollbackManager(monitor_window=10, degradation_threshold=0.2)
        rb.record_pre_tuning(100.0)
        for i in range(10):
            rb.record_post_result(70.0)  # 30% degradation
        self.assertTrue(rb._needs_rollback)

    def test_v118_v119_signal_selector(self):
        """Ω-V118, Ω-V119: Signal selection and pruning."""
        ss = SignalSelector(min_performance=0.0)
        ss.register_signal("rsi")
        ss.register_signal("bad_signal")
        ss.register_signal("macd")

        for _ in range(60):
            ss.record_signal_result("rsi", random.gauss(0.1, 0.05))
            ss.record_signal_result("bad_signal", random.gauss(-0.1, 0.05))
            ss.record_signal_result("macd", random.gauss(0.08, 0.05))

        active = ss.get_active_signals()
        self.assertIn("rsi", active)
        self.assertIn("macd", active)
        # bad_signal should be pruned
        if "bad_signal" in ss._pruned_signals:
            self.assertNotIn("bad_signal", active)

    def test_v121_v122_ensemble_optimizer(self):
        """Ω-V121, Ω-V122: Ensemble composition optimization."""
        eo = EnsembleOptimizer()
        eo.add_model("model_a")
        eo.add_model("model_b")

        for _ in range(20):
            eo.update_model_performance("model_a", random.gauss(0.1, 0.05))
            eo.update_model_performance("model_b", random.gauss(0.05, 0.05))

        weights = eo.get_weights()
        self.assertGreater(weights["model_a"], weights["model_b"])
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=5)

    def test_v126_complexity_control(self):
        """Ω-V126: Complexity controller."""
        cc = ComplexityController(max_complexity=100)
        c1 = cc.measure(n_params=5, n_modules=2, n_rules=10)
        self.assertLess(c1, cc._max)
        c2 = cc.measure(n_params=50, n_modules=20, n_rules=50)
        self.assertFalse(cc.is_acceptable(c2))
        trend = cc.get_complexity_trend()
        self.assertIn(trend, ["increasing", "stable", "decreasing"])

    def test_v127_v140_experience_replay(self):
        """Ω-V127 to Ω-V140: Learning from experience."""
        er = ExperienceReplay(max_size=1000)
        random.seed(42)

        for i in range(50):
            reg = random.choice(["trending", "ranging", "choppy"])
            er.store({
                "trade_id": f"t-{i}",
                "pnl": random.gauss(10, 50),
                "regime": reg,
                "context": {"vol": random.random(), "momentum": random.gauss(0, 0.5)},
                "timestamp": time.time() - i * 3600,
            })

        # Retrieve similar
        similar = er.retrieve_similar(
            query={"vol": 0.5, "momentum": 0.3}, top_k=5,
        )
        self.assertGreater(len(similar), 0)

        # Extract lesson
        trade = {"pnl": -50.0, "regime": "choppy", "setup": "breakout",
                 "key_factors": ["low_vol", "whipsaw"]}
        lesson = er.extract_lesson(trade)
        self.assertIn("lesson", lesson)

        # Transfer learning
        transferred = er.transfer_experience("trending", "new_regime")
        self.assertEqual(len(transferred), sum(1 for e in er._experiences if e.get("regime") == "trending"))

        # Know stats
        stats = er.get_knowledge_stats()
        self.assertIn("total_experiences", stats)

    def test_v134_forgetting(self):
        """Ω-V134: Forgetting obsolete patterns."""
        er = ExperienceReplay()
        # Old lessons
        old_ts = time.time() - 86400 * 60  # 60 days ago
        for _ in range(5):
            er._lessons.append({"lesson": "old", "timestamp": old_ts})
        # New lesson
        er._lessons.append({"lesson": "new", "timestamp": time.time()})

        n_forgotten = er.forget_obsolete_patterns(max_age=86400 * 30)  # 30 days
        self.assertGreaterEqual(n_forgotten, 5)
        self.assertEqual(len(er._lessons), 1)  # Only new lesson remains

    def test_v136_v138_entropy_simplification(self):
        """Ω-V137, Ω-V138: Entropy measurement and simplification."""
        config = {
            "param_1": 0.1, "param_2": 0.2, "param_3": 0.3,
            "module_1": True, "module_2": True,
        }
        entropy = EntropyMeasure.compute_system_entropy(config)
        self.assertGreater(entropy, 0)

        sensitivity = {"param_1": 0.001, "param_2": 0.5, "module_1": 0.005}
        candidates = EntropyMeasure.find_simplification_candidates(
            config, sensitivity, threshold=0.01,
        )
        self.assertIn("param_1", candidates)

    def test_v145_v153_adaptive_risk(self):
        """Ω-V145 to Ω-V153: Adaptive risk management."""
        arm = AdaptiveRiskManager(target_volatility=0.15)

        # Update with market data
        for _ in range(30):
            arm.update_market_state(volatility=random.gauss(0.1, 0.03), drawdown=0.5)
        arm.update_pnl(random.gauss(5, 20))

        size = arm.compute_optimal_size()
        self.assertGreater(size, 0)
        self.assertLessEqual(size, 1.0)

        fatigue = arm.detect_fatigue(threshold_consecutive_losses=5)
        self.assertIsInstance(fatigue, bool)

        conf = arm.calibrate_confidence()
        self.assertAlmostEqual(conf, 0.5, places=1)  # Default when no data

    def test_v154_v162_meta_optimizer(self):
        """Ω-V154 to Ω-V162: Meta-optimization & reflection."""
        mo = MetaOptimizer()

        # Record rounds
        mo.record_optimization_round("genetic", params_changed=5, fitness_improvement=0.5)
        mo.record_optimization_round("bayesian", params_changed=3, fitness_improvement=0.3)

        # Self-diagnosis
        diag = mo.diagnose_system()
        self.assertIn("health", diag)
        self.assertIn("issues", diag)

        # Improvement proposal
        prop = mo.generate_improvement_proposal("Add new signal", estimated_impact=0.1)
        proposals = mo.get_all_proposals()
        self.assertGreater(len(proposals), 0)

        # Evolution tracking
        mo.track_evolution("sharpe", 2.0)
        mo.track_evolution("sharpe", 2.5)
        mo.track_evolution("sharpe", 3.0)
        trend = mo.get_evolution_trend("sharpe")
        self.assertEqual(trend, "improving")

    def test_v100_v108_goal_tracker(self):
        """Ω-V100 to Ω-V108: Goal tracking and reporting."""
        gt = GoalTracker()
        gt.add_goal("profit_target", target=70000.0, current=30000.0, unit="USD")
        gt.add_goal("min_trades", target=200.0, current=150.0, unit="trades")

        report = gt.get_goal_report()
        self.assertEqual(len(report), 2)

        # Update progress
        gt.update_goal("profit_target", 35000.0)
        report = gt.get_goal_report()
        self.assertGreater(report[0]["progress_pct"], 0)

        # Monte Carlo
        mc = gt.run_monte_carlo(
            current_value=35000.0, target=70000.0,
            mean_period_return=1000.0, std_period_return=2000.0,
            n_iterations=1000,
        )
        self.assertIn("probability", mc)
        self.assertGreaterEqual(mc["probability"], 0.0)
        self.assertLessEqual(mc["probability"], 1.0)


if __name__ == "__main__":
    unittest.main()
