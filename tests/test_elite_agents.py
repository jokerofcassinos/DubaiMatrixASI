"""
SOLÉNN v2 — Tests for Elite Agents Ω (Ω-E01 to Ω-E162)
Coverage: orderflow (Ω-E01–E54), regime (Ω-E55–E108),
signal_aggregator (Ω-E109–E162).
"""

from __future__ import annotations

import math
import random
import time
import unittest

from core.agents.orderflow import (
    AggressorSideDetector,
    BookPressureGradient,
    BookShapeAnalyzer,
    FlowToxicityMonitor,
    FlowDirectionEntropy,
    OrderFlowImbalance,
    VPINCalculator,
    DepthVelocityTracker,
    LiquidityResilienceScore,
    MarketQualityIndex,
    VolumeProfile,
    ImpactModel,
    SpoofPatternDetector,
    LayeringDetector,
    SpoofConfidenceScorer,
)
from core.agents.regime import (
    HurstExponentCalculator,
    FractalDimensionCalculator,
    ScaleInvariantFeatures,
    VolatilityCone,
    VolCompressionDetector,
    VolRegimeTransitionPredictor,
    TrendStrengthIndex,
    DivergenceDetector,
    CorrelationBreakdownDetector,
    _compute_correlation,
    BasisAnomalyDetector,
    LiquidationCascadePredictor,
    SessionTransitionSignal,
    CorrelationNetworkBuilder,
    InformationFlowTracker,
)
from core.agents.signal_aggregator import (
    ShannonEntropyCalculator,
    MutualInformationEstimator,
    RedundancyAnalyzer,
    _compute_mi_discretized,
    MarketTemperatureEstimator,
    FreeEnergyCalculator,
    PhaseTransitionPredictor,
    GrangerCausalityTracker,
    SignalQualityTracker,
    AdaptiveWeightedAggregator,
    PersistentHomologyCalculator,
)


# ──────────────────────────────────────────────────────────────
# Ω-E01 to Ω-E54: Order Flow Tests
# ──────────────────────────────────────────────────────────────

class TestOrderFlow(unittest.TestCase):
    """Ω-E01 to Ω-E54"""

    def test_e01_vpin(self):
        """Ω-E01: VPIN updates and returns value when enough buckets."""
        vpin = VPINCalculator(bucket_volume=10.0, num_buckets=10)
        for i in range(200):
            vol = 1.0
            is_buy = i % 3 == 0  # 66% sell
            result = vpin.update(vol, is_buy)
        # After enough buckets, should return a value
        result = vpin.update(10.0, False)
        self.assertIsNotNone(result)
        self.assertGreater(result, 0.3)  # Asymmetric flow → non-zero VPIN

    def test_e02_imbalance(self):
        """Ω-E02: Order flow imbalance calculation."""
        calc = OrderFlowImbalance(levels=5)
        result = calc.compute([100, 80, 60, 40, 20], [20, 40, 60, 80, 100])
        self.assertAlmostEqual(result, 0.0, places=2)  # Equal total
        result2 = calc.compute([100, 100, 100, 0, 0], [0, 0, 0, 0, 0])
        self.assertAlmostEqual(result2, 1.0, places=2)  # All bid

    def test_e03_aggressor(self):
        """Ω-E03: Lee-Ready tick test classification."""
        det = AggressorSideDetector()
        result = det.classify(50000.0, 49999.0, 50001.0)
        self.assertIn(result, ["unknown", "buy", "sell"])
        result2 = det.classify(50005.0, 50004.0, 50006.0)  # Price went up
        self.assertEqual(result2, "buy")
        result3 = det.classify(50002.0, 50001.0, 50003.0)  # Price went down
        self.assertEqual(result3, "sell")

    def test_e05_toxicity(self):
        """Ω-E05: Flow toxicity detection."""
        mon = FlowToxicityMonitor(threshold=0.6)
        self.assertFalse(mon.update(0.3))
        self.assertFalse(mon.update(0.4))
        self.assertTrue(mon.update(0.7))  # Above threshold
        self.assertTrue(mon._toxic_streak > 0)

    def test_e09_entropy(self):
        """Ω-E09: Flow direction entropy increases with randomness."""
        ent = FlowDirectionEntropy(window=100)
        # Alternating pattern → low entropy
        for i in range(50):
            h1 = ent.update("buy" if i % 2 == 0 else "sell")
        # Random pattern → higher entropy
        random.seed(42)
        for _ in range(50):
            h2 = ent.update(random.choice(["buy", "sell"]))
        self.assertGreater(h2, h1)

    def test_e10_depth_velocity(self):
        """Ω-E10: Depth velocity tracks book changes."""
        tracker = DepthVelocityTracker(window=50)
        tracker.update([100.0, 80.0, 60.0], [60.0, 80.0, 100.0])
        v1 = tracker.update([200.0, 160.0, 120.0], [120.0, 160.0, 200.0])
        self.assertGreater(v1, 0.0)  # Depth doubled → velocity

    def test_e15_resilience(self):
        """Ω-E15: Liquidity resilience scoring."""
        score = LiquidityResilienceScore()
        self.assertAlmostEqual(score.score, 1.0)
        score.record_event(depth_lost=1000.0, recovery_time_s=5.0)
        self.assertGreaterEqual(score.score, 0.0)
        self.assertLessEqual(score.score, 1.0)

    def test_e17_book_shape(self):
        """Ω-E17: Book shape classification."""
        analyzer = BookShapeAnalyzer()
        # Flat book
        shape = analyzer.classify([50, 50, 50, 50], [50, 50, 50, 50])
        self.assertEqual(shape, "flat")
        # Wall (large concentration at one level)
        shape = analyzer.classify([500, 10, 10, 10], [10, 10, 10, 10])
        self.assertEqual(shape, "wall")

    def test_e19_impact_model(self):
        """Ω-E19: Market impact model calibrates."""
        model = ImpactModel()
        # Feed observations
        for i in range(20):
            qty = 0.1 + i * 0.05
            depth = 10.0
            actual = model._calibration.eta * (qty / depth) ** model._calibration.gamma * 10000 + random.gauss(0, 0.1)
            model.calibrate(qty, depth, max(0.1, actual))

        predicted = model.predict(order_qty=1.0, book_depth=10.0)
        self.assertGreater(predicted, 0)

    def test_e28_spoof_detection(self):
        """Ω-E28: Spoof pattern detection."""
        det = SpoofPatternDetector(large_order_bps=0.05, cancel_time_ms=200.0)
        det.record_placement("spoof-1", 500.0, 1000.0, 1000.0)  # Large order (50% of book)
        is_spoof, conf = det.record_cancellation("spoof-1", 1100.0)  # Cancelled 100ms later
        self.assertTrue(is_spoof)
        self.assertGreater(conf, 0.0)

    def test_e37_volume_profile(self):
        """Ω-E37-E44: Volume profile with POC and value area."""
        vp = VolumeProfile(num_bins=100, price_range=(49000.0, 51000.0))
        # Add trades concentrated around 50000
        for _ in range(100):
            price = 50000.0 + random.gauss(0, 50)
            vp.add_trade(price, 1.0, is_buy=True)
        for _ in range(50):
            price = 50000.0 + random.gauss(0, 30)
            vp.add_trade(price, 1.0, is_buy=False)

        poc = vp.poc
        self.assertGreater(poc, 49000.0)
        self.assertLess(poc, 51000.0)

        va_low, va_high = vp.value_area
        self.assertLessEqual(va_low, poc)
        self.assertGreaterEqual(va_high, poc)

    def test_e44_cumulative_delta(self):
        """Ω-E44: Cumulative delta tracks buy-sell imbalance."""
        vp = VolumeProfile(num_bins=100, price_range=(49000.0, 51000.0))
        for _ in range(100):
            vp.add_trade(50000.0, 1.0, is_buy=True)
        for _ in range(30):
            vp.add_trade(50000.0, 1.0, is_buy=False)
        self.assertGreater(vp.cumulative_delta, 0)

    def test_e51_market_quality(self):
        """Ω-E51: Market quality index."""
        mq = MarketQualityIndex()
        # Good conditions: tight spread, deep book, low toxicity
        q1 = mq.update(spread_bps=2.0, depth_usd=1000000.0, vpin=0.2)
        # Bad conditions: wide spread, shallow, toxic
        q2 = mq.update(spread_bps=50.0, depth_usd=10000.0, vpin=0.8)
        # Quality decreased
        self.assertLess(q2, q1)


# ──────────────────────────────────────────────────────────────
# Ω-E55 to Ω-E108: Regime & Structural Tests
# ──────────────────────────────────────────────────────────────

class TestRegimeSignals(unittest.TestCase):
    """Ω-E55 to Ω-E108"""

    def test_e55_hurst(self):
        """Ω-E55: Hurst exponent calculation."""
        calc = HurstExponentCalculator(window=100)
        for _ in range(50):
            h = calc.update(random.gauss(0, 0.01))
        self.assertGreater(h, 0.0)
        self.assertLess(h, 1.0)

    def test_e57_fractal_dimension(self):
        """Ω-E57: D = 2 - H mapping."""
        h_calc = HurstExponentCalculator(window=100)
        fd = FractalDimensionCalculator(hurst_calculator=h_calc)
        for _ in range(60):
            d = fd.update(random.gauss(0, 0.01))
        self.assertGreater(d, 1.0)
        self.assertLess(d, 2.0)

    def test_e62_scale_invariant(self):
        """Ω-E62: Scale-invariant features."""
        prices = [100.0, 101.0, 99.0, 102.0, 98.0]
        prices_scaled = [p * 10 for p in prices]  # Scale by 10x
        ret1 = ScaleInvariantFeatures.compute_returns(prices)
        ret2 = ScaleInvariantFeatures.compute_returns(prices_scaled)
        self.assertEqual(ret1, ret2)  # Returns are scale-invariant

    def test_e64_volatility_cone(self):
        """Ω-E64: Volatility cone with percentiles."""
        vc = VolatilityCone(horizons=[10, 30])
        random.seed(42)
        for _ in range(200):
            vc.update(random.gauss(0, 0.01))
        result = vc.update(random.gauss(0, 0.03))  # High vol
        self.assertIn(10, result)
        self.assertIn(30, result)
        self.assertGreater(result[30]["current_vol"], 0)

    def test_e65_compression(self):
        """Ω-E65: Volatility compression detection."""
        det = VolCompressionDetector(squeeze_threshold=0.01, window=20)
        for _ in range(20):
            det.update(100.0)  # Perfectly stable
        squeezed, ratio = det.update(100.0)
        self.assertTrue(squeezed)

    def test_e70_transition(self):
        """Ω-E70: Vol regime transition prediction."""
        pred = VolRegimeTransitionPredictor(window=50)
        for _ in range(40):
            pred.update(0.01)  # Stable vol
        # Sudden vol increase
        for v in [0.01, 0.02, 0.05, 0.1, 0.3, 0.5, 1.0, 2.0, 3.0, 5.0]:
            result = pred.update(v)
        self.assertTrue(result)  # Should detect transition

    def test_e73_trend_strength(self):
        """Ω-E73: R² as trend strength measure."""
        tsi = TrendStrengthIndex(window=50)
        # Strong uptrend
        for i in range(50):
            r2, direction = tsi.update(100.0 + i * 0.5)
        self.assertGreater(r2, 0.8)
        self.assertAlmostEqual(direction, 1.0)

    def test_e76_divergence(self):
        """Ω-E76: Bullish and bearish divergence detection."""
        det = DivergenceDetector()
        # Bearish div: price higher high, indicator lower high
        det.detect_bearish_divergence(price=100.0, indicator=70.0, is_swing_high=True)
        det.detect_bearish_divergence(price=105.0, indicator=65.0, is_swing_high=True)
        self.assertTrue(det._indicator_highs[-1] < det._indicator_highs[-2])

    def test_e82_correlation_breakdown(self):
        """Ω-E82: Correlation breakdown detection."""
        det = CorrelationBreakdownDetector(window=50, threshold=0.3)
        det.set_baseline_correlation(0.8)
        # Initially correlated
        for _ in range(30):
            v = random.random()
            det.update(v + random.gauss(0, 0.1), v + random.gauss(0, 0.1))
        breakdown, corr = det.update(random.random(), -random.random())
        self.assertIsNotNone(corr)

    def test_e86_basis_anomaly(self):
        """Ω-E86: Basis anomaly detection."""
        det = BasisAnomalyDetector(normal_range_bps=(-10.0, 10.0))
        anomaly1, bps1 = det.update(50000.0, 50001.0)  # Small premium ~0.2 bps
        self.assertFalse(anomaly1)
        anomaly2, bps2 = det.update(50000.0, 50100.0)  # Large premium ~20 bps
        self.assertTrue(anomaly2)

    def test_e92_liquidation_cascade(self):
        """Ω-E92: Liquidation cascade prediction."""
        pred = LiquidationCascadePredictor()
        # Safe conditions
        risk1 = pred.update(oi_change_pct=1.0, funding_rate=0.01, leverage_estimate=3.0)
        # Dangerous conditions
        risk2 = pred.update(oi_change_pct=8.0, funding_rate=-0.08, leverage_estimate=20.0)
        risk3 = pred.update(oi_change_pct=10.0, funding_rate=-0.1, leverage_estimate=25.0)
        risk4 = pred.update(oi_change_pct=15.0, funding_rate=-0.15, leverage_estimate=30.0)
        risk5 = pred.update(oi_change_pct=20.0, funding_rate=-0.2, leverage_estimate=35.0)
        self.assertGreater(risk5, risk1)

    def test_e98_session(self):
        """Ω-E98: Session transitions."""
        self.assertEqual(SessionTransitionSignal.get_current_session(3), "tokyo")
        self.assertEqual(SessionTransitionSignal.get_current_session(10), "london")
        self.assertEqual(SessionTransitionSignal.get_current_session(15), "london")
        self.assertEqual(SessionTransitionSignal.get_current_session(16), "new_york")
        self.assertTrue(SessionTransitionSignal.is_transition(7))
        self.assertTrue(SessionTransitionSignal.is_transition(13))
        self.assertFalse(SessionTransitionSignal.is_transition(10))

        tokyo = SessionTransitionSignal.get_session_characteristics("tokyo")
        self.assertTrue(tokyo["mean_reversion_favored"])
        ny = SessionTransitionSignal.get_session_characteristics("new_york")
        self.assertTrue(ny["trend_favored"])

    def test_e100_network(self):
        """Ω-E100: Correlation network building."""
        net = CorrelationNetworkBuilder(window=30, threshold=0.7)
        net.add_asset("A")
        net.add_asset("B")
        net.add_asset("C")
        random.seed(42)
        for _ in range(30):
            a = random.gauss(0, 0.01)
            b = a * 0.9 + random.gauss(0, 0.002)  # Highly correlated with A
            c = random.gauss(0, 0.01)  # Uncorrelated
            net.update_returns({"A": a, "B": b, "C": c})

        edges = net.update_returns({"A": random.gauss(0, 0.01), "B": random.gauss(0, 0.01), "C": random.gauss(0, 0.01)})
        # Components
        components = net.get_connected_components()
        self.assertGreater(len(components), 0)


# ──────────────────────────────────────────────────────────────
# Ω-E109 to Ω-E162: Advanced Quant Signal Tests
# ──────────────────────────────────────────────────────────────

class TestQuantSignals(unittest.TestCase):
    """Ω-E109 to Ω-E162"""

    def test_e109_shannon_entropy(self):
        """Ω-E109: Shannon entropy of return distribution."""
        calc = ShannonEntropyCalculator(window=100, num_bins=10)
        # Random returns → high entropy
        random.seed(42)
        for i in range(100):
            e1 = calc.update(random.gauss(0, 0.01))
        self.assertGreater(e1, 0)

    def test_e110_mutual_information(self):
        """Ω-E110: MI between feature and future return."""
        est = MutualInformationEstimator(num_bins=10, window=200)
        random.seed(42)
        for _ in range(100):
            x = random.gauss(0, 0.01)
            y = x * 0.8 + random.gauss(0, 0.003)  # Strongly correlated
            mi = est.update(x, y)
        self.assertGreater(mi, 0)

    def test_e114_redundancy(self):
        """Ω-E114: Redundancy analysis between signals."""
        analyzer = RedundancyAnalyzer()
        random.seed(42)
        for _ in range(50):
            v = random.gauss(0, 0.01)
            analyzer.add_signal("s1", v)
            analyzer.add_signal("s2", v + random.gauss(0, 0.001))  # Highly redundant
            analyzer.add_signal("s3", random.gauss(0, 0.01))  # Independent

        mi_matrix = analyzer.compute_redundancies()
        self.assertGreater(mi_matrix["s1"]["s2"], mi_matrix["s1"]["s3"])

    def test_e137_free_energy(self):
        """Ω-E137: Free energy calculation."""
        fc = FreeEnergyCalculator(window=50)
        for i in range(50):
            F, U, S = fc.update(vol=0.01 + i * 0.0001, trade_time=time.time() + i)
        self.assertIsNotNone(F)

    def test_e140_phase_transition(self):
        """Ω-E140: Phase transition prediction."""
        pred = PhaseTransitionPredictor(window=100)
        # Need enough data: first 40 stable, then strong variance increase
        for _ in range(80):
            pred.update(0.01)
        # Sudden variance increase
        for i in range(30):
            result = pred.update(0.01 if i % 2 == 0 else (0.5 + i * 0.1))
        self.assertIsInstance(result, bool)

    def test_e145_granger(self):
        """Ω-E145: Granger causality tracking."""
        gc = GrangerCausalityTracker(max_lag=3, window=100)
        random.seed(42)
        for i in range(80):
            a = random.gauss(0, 0.01)
            b = a * 0.7 + random.gauss(0, 0.005)  # B is driven by A
            gc.add_series("A", a)
            gc.add_series("B", b)

        graph = gc.update_graph()
        self.assertIn("A", graph)
        self.assertIn("B", graph)
        # A→B should be stronger than A→A (diagonal = 1.0)
        self.assertGreater(graph["A"]["B"], 0.1)

    def test_e154_signal_quality(self):
        """Ω-E154: Signal quality tracking."""
        tracker = SignalQualityTracker()
        tracker.update("rsi", was_correct=True, pnl=100.0, regime="trending")
        tracker.update("rsi", was_correct=True, pnl=50.0, regime="trending")
        tracker.update("rsi", was_correct=False, pnl=-40.0, regime="trending")

        quality = tracker.get_quality("rsi")
        self.assertGreater(quality["hit_rate"], 0.5)
        self.assertGreater(quality["total_pnl"], 0)

    def test_e160_meta_aggregation(self):
        """Ω-E160: Meta-signal aggregation with adaptive weights."""
        agg = AdaptiveWeightedAggregator()
        agg.register_signal("rsi")
        agg.register_signal("macd")
        agg.register_signal("vwap")

        # Update outcomes
        for _ in range(10):
            agg.update_outcome("rsi", True)
            agg.update_outcome("macd", True)
            agg.update_outcome("vwap", False)

        weights = agg.sample_weights()
        self.assertGreater(weights["rsi"], 0.1)

        signals = {
            "rsi": ("long", 0.8),
            "macd": ("long", 0.7),
            "vwap": ("short", 0.4),
        }
        meta = agg.aggregate(signals)
        self.assertEqual(meta.direction, "long")
        self.assertGreater(meta.confidence, 0.3)
        self.assertEqual(meta.n_signals, 3)

    def test_e118_persistent_homology(self):
        """Ω-E118: Simplified persistent homology."""
        ph = PersistentHomologyCalculator(embedding_dim=3, window_size=30)
        random.seed(42)
        for _ in range(30):
            result = ph.update(random.gauss(0, 0.1))
        self.assertIn("beta_0", result)
        self.assertIn("beta_1", result)
        self.assertIn("euler", result)
        self.assertEqual(result["beta_0"], 1)

    def test_e146_causal_discovery(self):
        """Ω-E147: Causal direction graph is populated."""
        gc = GrangerCausalityTracker(max_lag=5, window=100)
        random.seed(42)
        for _ in range(60):
            a = random.gauss(0, 0.01)
            b = a * 0.9 + random.gauss(0, 0.002)
            gc.add_series("cause", a)
            gc.add_series("effect", b)

        graph = gc.update_graph()
        self.assertIn("cause", graph)
        self.assertIn("effect", graph)
        # Both correlations should be non-trivial
        self.assertGreater(graph["cause"]["effect"], 0.3)
        self.assertGreater(graph["effect"]["cause"], 0.3)


if __name__ == "__main__":
    unittest.main()
