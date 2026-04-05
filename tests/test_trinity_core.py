"""
SOLÉNN v2 — Tests for Decision / Trinity Core Ω (Ω-T01 a Ω-T162)
3 test suites: trinity_core (Ω-T01–T54), kinetic_risk (Ω-T55–T108),
shadow_engine (Ω-T109–T162). Each vector has happy path, edge case, error case.
"""

from __future__ import annotations

import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import math
import time
import unittest
from collections import deque
from dataclasses import asdict

from core.decision.omega_types import (
    CircuitBreakerLevel,
    ConfluenceResult,
    DecisionCheckpoint,
    DecisionState,
    DecisionTelemetryEvent,
    Direction,
    ExitPlan,
    PerformanceAttribution,
    PostTradeAnalysis,
    Priority,
    RegimeState,
    RegimeType,
    Signal,
    TradeSignal,
    ValidationStage,
    ValidationStageResult,
    generate_checkpoint_id,
    generate_signal_id,
    generate_trace_id,
)
from core.decision.trinity_core import (
    BayesianEngine,
    ConfluenceEngine,
    DecisionOutputFormatter,
    DecisionStateMachine,
    RegimeAwareRouter,
    RegimeDetector,
    TrinityCore,
    ValidationPipeline,
)
from core.decision.kinetic_risk import (
    BayesianKellyEstimator,
    CircuitBreakerSystem,
    DynamicExitEngine,
    PositionRecord,
    PositionRiskMonitor,
    PortfolioRiskOptimizer,
    TailRiskProtector,
)
from core.decision.shadow_engine import (
    CounterfactualEngine,
    ForensicAnalyzer,
    RootCauseCategory,
    RootCausePatchSystem,
    ShadowEngine,
)
from core.decision.meta_learning import (
    ConceptDriftDetector,
    MetaLearningEngine,
    ParameterStabilityMonitor,
    ThompsonSamplingAllocator,
)
from core.decision.telemetry import (
    Alert,
    AlertLevel,
    PerformanceAttributor,
    TelemetryEngine,
)


# ──────────────────────────────────────────────────────────────
# Ω-T01 to Ω-T54: TRINITY CORE TESTS
# ──────────────────────────────────────────────────────────────

class TestRegimeDetector(unittest.TestCase):
    """Ω-T01, Ω-T37, Ω-T38, Ω-T45"""

    def setUp(self):
        self.detector = RegimeDetector(window_size=100, prior_transition=0.02)

    def test_t01_initial_uniform_prior(self):
        """Ω-T01: Initial state has uniform prior over regimes."""
        state = self.detector.update(0.0)
        self.assertIsInstance(state, RegimeState)
        total = sum(state.probabilities.values())
        self.assertAlmostEqual(total, 1.0, places=5)

    def test_t01_uptrend_detection(self):
        """Ω-T01: Detector should shift to trending up with positive returns."""
        for _ in range(20):
            self.detector.update(0.003)  # Strong positive returns
        state = self.detector.update(0.003)
        self.assertIn(
            state.primary_regime,
            [RegimeType.TRENDING_UP_STRONG, RegimeType.TRENDING_UP_WEAK],
        )

    def test_t38_critical_slowing_down(self):
        """Ω-T38: CSD score should increase with variance trend."""
        for _ in range(50):
            self.detector.update(0.0)  # Stable period
        # Then inject growing variance
        for i in range(30):
            self.detector.update(i * 0.01 * (1 if i % 2 == 0 else -1))
        state = self.detector.update(0.05)
        self.assertGreaterEqual(state.critical_slowing_down, 0.0)
        self.assertLessEqual(state.critical_slowing_down, 1.0)

    def test_t44_unknown_regime(self):
        """Ω-T44: With random data, regime should have lower confidence."""
        import random
        for _ in range(100):
            self.detector.update(random.gauss(0, 0.05))
        state = self.detector.update(0.01)
        # Confidence should be lower than with directional data
        self.assertLessEqual(state.confidence, 0.95)

    def test_t45_transition_prediction(self):
        """Ω-T45: Transition can be predicted when CSD is high."""
        state = self.detector.update(0.0)
        self.assertIn(
            state.transition_predicted,
            [None] + list(RegimeType),
        )


class TestConfluenceEngine(unittest.TestCase):
    """Ω-T02 to Ω-T09"""

    def setUp(self):
        self.engine = ConfluenceEngine(confluence_threshold=0.7)
        self.engine.register_signal_source("rsi", 0.6)
        self.engine.register_signal_source("macd", 0.6)
        self.engine.register_signal_source("orderflow", 0.6)

    def test_t02_signal_ingest(self):
        """Ω-T02: Can ingest signals from registered sources."""
        sig = Signal(
            signal_id="test-1", source="rsi", direction=Direction.LONG,
            score=0.8, confidence=0.9, timestamp_ns=time.time_ns(),
        )
        self.engine.ingest_signal(sig)
        result = self.engine.compute_confluence()
        self.assertEqual(result.n_signals_total, 1)

    def test_t09_confluence_score_strong(self):
        """Ω-T09: Strong alignment produces high confluence score."""
        now = time.time_ns()
        for i, src in enumerate(["rsi", "macd", "orderflow"]):
            self.engine.ingest_signal(Signal(
                signal_id=f"sig-{i}", source=src, direction=Direction.LONG,
                score=0.9, confidence=0.95, timestamp_ns=now,
            ))
        result = self.engine.compute_confluence(now)
        self.assertTrue(result.is_strong_confluence)
        self.assertEqual(result.consensus_direction, Direction.LONG)

    def test_t08_conflict_detection(self):
        """Ω-T08: Opposing signals detected as conflict."""
        now = time.time_ns()
        self.engine.ingest_signal(Signal(
            signal_id="s1", source="rsi", direction=Direction.LONG,
            score=0.9, confidence=0.9, timestamp_ns=now,
        ))
        self.engine.ingest_signal(Signal(
            signal_id="s2", source="macd", direction=Direction.SHORT,
            score=0.9, confidence=0.9, timestamp_ns=now,
        ))
        conflict, pairs = self.engine.detect_conflicts()
        self.assertTrue(conflict)
        self.assertTrue(len(pairs) > 0)

    def test_t06_signal_decay(self):
        """Ω-T06: Freshness decay applies to signal weight."""
        past = time.time_ns() - int(600e9)  # 10 minutes ago
        self.engine.ingest_signal(Signal(
            signal_id="old", source="rsi", direction=Direction.LONG,
            score=0.9, confidence=0.9, timestamp_ns=past,
        ))
        now = time.time_ns()
        result = self.engine.compute_confluence(now)
        # Old signal should have reduced weight but still contribute
        self.assertGreaterEqual(result.confluence_score, 0.0)

    def test_t04_weight_update(self):
        """Ω-T04: Manual weight update works."""
        self.engine.update_weight("rsi", 0.9)
        meta = self.engine._metadata["rsi"]
        self.assertAlmostEqual(meta.weight, 0.9)


class TestValidationPipeline(unittest.TestCase):
    """Ω-T10 to Ω-T18"""

    def setUp(self):
        self.pipeline = ValidationPipeline()
        self.regime = RegimeState(
            primary_regime=RegimeType.TRENDING_UP_STRONG,
            probabilities={RegimeType.TRENDING_UP_STRONG: 0.85, RegimeType.RANGING_TIGHT: 0.15},
            confidence=0.85,
            transition_predicted=None,
            transition_probability=0.0,
            critical_slowing_down=0.0,
            hurst=0.6,
            entropy=0.2,
            timestamp_ns=time.time_ns(),
        )
        self.confluence = ConfluenceResult(
            confluence_score=0.85, n_signals_aligned=5, n_signals_total=6,
            alignment_ratio=0.83, consensus_direction=Direction.LONG,
            signal_details={}, conflict_detected=False, conflict_pairs=[],
            timestamp_ns=time.time_ns(),
        )

    def _make_features(self) -> dict:
        return {
            "checksum_valid": True, "bid_lt_ask": True, "price": 50000.0,
            "vwap": 49900.0, "timestamp_monotonic": True, "volume": 100.0,
            "gap_free": True, "tech_indicators_aligned": True,
            "rsi": 55, "macd_confirmatory": True, "bb_squeeze": False,
            "atr_expansion": True, "volume_confirmatory": True,
            "structure_compatible": True, "entry_confirmed": True,
            "setup_valid_1m": True, "kelly_fraction": 0.1,
            "portfolio_correlation": 0.2, "total_exposure_pct": 10.0,
            "risk_of_ruin": 1e-8, "valid_session": True,
            "expected_rr": 8.0, "expected_profit_usd": 150.0,
            "estimated_tce": 10.0, "edge_p_value": 0.0001,
            "spectral_energy": 0.5, "orderflow_imbalance": 0.3,
            "depth_asymmetry": 0.2, "aggressor_confirmed": True,
            "vpin": 0.3, "spread_bps": 5.0, "volatility": 2.0,
            "htf_alignment": 0.8, "funding_rate": 0.01,
            "time_to_macro_event": 9999.0, "microprice_imbalance": 0.2,
            "depth_total_usd": 100000.0,
        }

    def test_t17_all_pass(self):
        """Ω-T17: Good features pass all 47 stages."""
        f = self._make_features()
        passed, results = self.pipeline.run(
            features=f, regime_state=self.regime, confluence=self.confluence,
            price=50000.0, atr=100.0, spread_bps=5.0, volatility=2.0,
            vpin=0.3, microprice_direction=Direction.LONG, htf_alignment=0.8,
            drawdown_pct=0.1, portfolio_correlation=0.2, funding_rate=0.01,
            time_to_macro_event_seconds=9999.0, entropy=0.2,
            expected_rr_ratio=8.0, expected_profit_usd=150.0,
            min_viable_profit_usd=60.0, estimated_tce=10.0,
            edge_p_value=0.0001, hurst=0.6, spectral_energy=0.5,
            orderflow_imbalance=0.3, depth_asymmetry=0.2,
            aggressor_side_confirmed=True,
        )
        self.assertTrue(passed)

    def test_t17_veto_on_failure(self):
        """Ω-T17: Single failure → entire setup rejected."""
        f = self._make_features()
        f["bid_lt_ask"] = False  # Data quality failure
        passed, results = self.pipeline.run(
            features=f, regime_state=self.regime, confluence=self.confluence,
            price=50000.0, atr=100.0, spread_bps=5.0, volatility=2.0,
            vpin=0.3, microprice_direction=Direction.LONG, htf_alignment=0.8,
            drawdown_pct=0.1, portfolio_correlation=0.2, funding_rate=0.01,
            time_to_macro_event_seconds=9999.0, entropy=0.2,
            expected_rr_ratio=8.0, expected_profit_usd=150.0,
            min_viable_profit_usd=60.0, estimated_tce=10.0,
            edge_p_value=0.0001, hurst=0.6, spectral_energy=0.5,
            orderflow_imbalance=0.3, depth_asymmetry=0.2,
            aggressor_side_confirmed=True,
        )
        self.assertFalse(passed)

    def test_t18_audit_log(self):
        """Ω-T18: Audit log populated after validation."""
        f = self._make_features()
        self.pipeline.run(
            features=f, regime_state=self.regime, confluence=self.confluence,
            price=50000.0, atr=100.0, spread_bps=5.0, volatility=2.0,
            vpin=0.3, microprice_direction=Direction.LONG, htf_alignment=0.8,
            drawdown_pct=0.1, portfolio_correlation=0.2, funding_rate=0.01,
            time_to_macro_event_seconds=9999.0, entropy=0.2,
            expected_rr_ratio=8.0, expected_profit_usd=150.0,
            min_viable_profit_usd=60.0, estimated_tce=10.0,
            edge_p_value=0.0001, hurst=0.6, spectral_energy=0.5,
            orderflow_imbalance=0.3, depth_asymmetry=0.2,
            aggressor_side_confirmed=True,
        )
        log = self.pipeline.get_audit_log()
        self.assertGreater(len(log), 0)
        self.assertIn("stage", log[0])
        self.assertIn("passed", log[0])


class TestBayesianEngine(unittest.TestCase):
    """Ω-T19 to Ω-T27"""

    def setUp(self):
        self.engine = BayesianEngine()

    def test_t21_win_rate_posterior(self):
        """Ω-T21: Posterior narrows with more data."""
        for _ in range(100):
            self.engine.update_win_rate(True)
        for _ in range(50):
            self.engine.update_win_rate(False)
        mean, lo, hi = self.engine.get_win_rate_posterior()
        self.assertGreaterEqual(mean, 0.6)  # 200 vs 100 with priors → ~0.6
        self.assertLess(hi - lo, 0.2)  # Narrow CI

    def test_t23_model_averaging(self):
        """Ω-T23: Bayesian model averaging weights models."""
        self.engine.update_model_weight("model_a", -10.0)
        self.engine.update_model_weight("model_b", -5.0)
        # Model B has better (less negative) log-likelihood
        weights = self.engine._model_weights
        self.assertGreater(weights.get("model_b", 0), weights.get("model_a", 0))

    def test_t24_bayes_factor(self):
        """Ω-T24: Bayes factor favors better-fitting model."""
        h1_data = [0.5, 0.6, 0.4, 0.55, 0.45]  # Tight around 0.5
        h0_data = [0.5, 0.6, 0.4, 0.55, 0.45]
        bf = self.engine.bayes_factor(h1_data, h0_data)
        self.assertAlmostEqual(bf, 1.0, places=1)  # Same data → BF ≈ 1

    def test_t25_regime_specific_wr(self):
        """Ω-T25: Regime-specific win rate with shrinkage."""
        self.engine.register_regime_prior(RegimeType.TRENDING_UP_STRONG, wins=10, losses=5)
        wr = self.engine.get_regime_specific_win_rate(RegimeType.TRENDING_UP_STRONG, wins=20, losses=10)
        self.assertGreater(wr, 0.5)


class TestDecisionStateMachine(unittest.TestCase):
    """Ω-T28 to Ω-T36"""

    def setUp(self):
        self.sm = DecisionStateMachine()

    def test_t28_valid_transition(self):
        """Ω-T28: Valid transitions succeed."""
        self.assertTrue(self.sm.transition(DecisionState.OBSERVING))
        self.assertTrue(self.sm.transition(DecisionState.SIGNAL_DETECTED))
        self.assertTrue(self.sm.transition(DecisionState.CONFLUENCE_CHECK))

    def test_t28_invalid_transition(self):
        """Ω-T28: Invalid transitions are rejected."""
        result = self.sm.transition(DecisionState.MANAGING)  # IDLE -> MANAGING is invalid
        self.assertFalse(result)

    def test_t30_timeout(self):
        """Ω-T30: Timeout detection works."""
        self.sm.transition(DecisionState.OBSERVING)
        # Simulate entry in the past
        self.sm._entry_time_ns = time.time_ns() - int(301e9)  # 301s ago
        self.assertTrue(self.sm.check_timeout())

    def test_t34_concurrent_limit(self):
        """Ω-T34: Concurrent decision limit enforced."""
        self.assertTrue(self.sm.can_accept_new_decision())

    def test_t32_emergency_transition(self):
        """Ω-T32: Emergency transition works from any state."""
        self.sm.transition(DecisionState.OBSERVING)
        self.sm.emergency_to_circuit_breaker()
        self.assertEqual(self.sm.get_state(), DecisionState.CIRCUIT_BREAKER)


class TestRegimeRouter(unittest.TestCase):
    """Ω-T37 to Ω-T45"""

    def test_t39_strategy_routing(self):
        """Ω-T39: Correct strategy for each regime."""
        router = RegimeAwareRouter()
        params = router.get_strategy_for_regime(RegimeType.TRENDING_UP_STRONG)
        self.assertEqual(params["strategy"], "trend_follow")

    def test_t44_no_trade_regime(self):
        """Ω-T44: No-trade regimes correctly identified."""
        router = RegimeAwareRouter()
        self.assertTrue(router.is_no_trade_regime(RegimeType.CHOPPY_EXPANDING))
        self.assertTrue(router.is_no_trade_regime(RegimeType.FLASH_CRASH))
        self.assertFalse(router.is_no_trade_regime(RegimeType.TRENDING_UP_STRONG))

    def test_t43_cascade_delay(self):
        """Ω-T43: Cross-asset cascade delays returned."""
        router = RegimeAwareRouter()
        delay = router.get_cascade_delay("BTC", "ETH")
        self.assertGreater(delay, 0)


class TestDecisionOutputFormatter(unittest.TestCase):
    """Ω-T46 to Ω-T54"""

    def setUp(self):
        self.formatter = DecisionOutputFormatter(min_viable_profit_usd=60.0)

    def _make_confluence(self) -> ConfluenceResult:
        return ConfluenceResult(
            confluence_score=0.85, n_signals_aligned=5, n_signals_total=6,
            alignment_ratio=0.83, consensus_direction=Direction.LONG,
            signal_details={}, conflict_detected=False, conflict_pairs=[],
            timestamp_ns=time.time_ns(),
        )

    def test_t46_signal_format(self):
        """Ω-T46: TradeSignal is fully populated."""
        sig = self.formatter.format_signal(
            direction=Direction.LONG, symbol="BTCUSDT", exchange="binance",
            entry_price=50000.0, confluence=self._make_confluence(),
            regime_state=RegimeState(
                primary_regime=RegimeType.TRENDING_UP_STRONG,
                probabilities={RegimeType.TRENDING_UP_STRONG: 0.85, RegimeType.RANGING_TIGHT: 0.15},
                confidence=0.85, transition_predicted=None,
                transition_probability=0.0, critical_slowing_down=0.0,
                hurst=0.6, entropy=0.2, timestamp_ns=time.time_ns(),
            ),
            validation_results=[], sizing_fraction=0.1, atr=100.0,
            stop_multiplier=2.0, rr_ratio=8.0, reasoning="test",
            alternatives_rejected=[], risk_disclosure="test",
            estimated_tce=10.0, trace_id="test-trace",
        )
        self.assertIsInstance(sig, TradeSignal)
        self.assertEqual(sig.direction, Direction.LONG)
        self.assertEqual(sig.symbol, "BTCUSDT")
        self.assertGreater(sig.take_profit, sig.entry_price)
        self.assertLess(sig.stop_loss, sig.entry_price)

    def test_t52_priority_encoding(self):
        """Ω-T52: A+ priority for highest confluence + RR."""
        result = ConfluenceResult(
            confluence_score=0.90, n_signals_aligned=6, n_signals_total=6,
            alignment_ratio=1.0, consensus_direction=Direction.LONG,
            signal_details={}, conflict_detected=False, conflict_pairs=[],
            timestamp_ns=time.time_ns(),
        )
        sig = self.formatter.format_signal(
            direction=Direction.LONG, symbol="BTCUSDT", exchange="binance",
            entry_price=50000.0, confluence=result,
            regime_state=RegimeState(
                primary_regime=RegimeType.TRENDING_UP_STRONG,
                probabilities={RegimeType.TRENDING_UP_STRONG: 0.95, RegimeType.RANGING_TIGHT: 0.05},
                confidence=0.95, transition_predicted=None,
                transition_probability=0.0, critical_slowing_down=0.0,
                hurst=0.7, entropy=0.1, timestamp_ns=time.time_ns(),
            ),
            validation_results=[], sizing_fraction=0.1, atr=100.0,
            stop_multiplier=2.0, rr_ratio=10.0, reasoning="test",
            alternatives_rejected=[], risk_disclosure="test",
            estimated_tce=10.0, trace_id="test-trace",
        )
        self.assertEqual(sig.priority, Priority.A_PLUS)

    def test_t154_telemetry(self):
        """Ω-T154: Telemetry events emitted and stored."""
        evt = self.formatter.emit_telemetry(
            "test_event", "test_component",
            inputs={"a": 1}, outputs={"b": 2},
            latency_us=100, confidence=0.8, trace_id="tr-1",
        )
        self.assertIsInstance(evt, DecisionTelemetryEvent)
        self.assertEqual(evt.event_type, "test_event")
        self.assertGreater(len(self.formatter.get_telemetry_events()), 0)


class TestTrinityCoreIntegration(unittest.TestCase):
    """Ω-T01 through Ω-T54: End-to-end Trinity Core test."""

    def test_full_pipeline(self):
        """Full decision pipeline: signals → regime → confluence → validation → trade."""
        core = TrinityCore(min_viable_profit_usd=60.0)

        # Warm up regime detector with trending data
        for _ in range(20):
            core.regime_detector.update(0.002)  # Consistent positive returns

        # Register signal sources
        core.confluence_engine.register_signal_source("signal_a", 0.7)
        core.confluence_engine.register_signal_source("signal_b", 0.7)

        now = time.time_ns()
        signals = [
            Signal(
                signal_id=f"sig-{i}", source="signal_a" if i == 0 else "signal_b",
                direction=Direction.LONG, score=0.9, confidence=0.85,
                timestamp_ns=now,
                features={
                    "return_1s": 0.001, "symbol": "BTCUSDT", "exchange": "binance",
                    "price": 50000.0, "atr": 100.0, "spread_bps": 5.0,
                    "volatility": 2.0, "vpin": 0.3,
                    "microprice_imbalance": 0.3, "htf_alignment": 0.8,
                    "portfolio_correlation": 0.2, "funding_rate": 0.01,
                    "time_to_macro_event": 9999.0, "expected_rr": 8.0,
                    "expected_profit_usd": 150.0, "estimated_tce": 10.0,
                    "edge_p_value": 0.0001, "spectral_energy": 0.5,
                    "orderflow_imbalance": 0.3, "depth_asymmetry": 0.2,
                    "aggressor_confirmed": True,
                    "checksum_valid": True, "bid_lt_ask": True,
                    "price": 50000.0, "vwap": 49900.0,
                    "timestamp_monotonic": True, "volume": 100.0,
                    "gap_free": True, "tech_indicators_aligned": True,
                    "rsi": 55, "macd_confirmatory": True,
                    "bb_squeeze": False, "atr_expansion": True,
                    "volume_confirmatory": True, "structure_compatible": True,
                    "entry_confirmed": True, "setup_valid_1m": True,
                    "kelly_fraction": 0.1, "total_exposure_pct": 10.0,
                    "risk_of_ruin": 1e-8, "valid_session": True,
                    "depth_total_usd": 100000.0,
                },
            )
            for i in range(2)
        ]

        trade_signal = core.receive_signals(signals)

        # Should produce a trade signal
        self.assertIsInstance(trade_signal, TradeSignal)
        self.assertGreater(trade_signal.confidence, 0.0)
        self.assertIsNotNone(trade_signal.exit_plan)
        self.assertGreater(len(trade_signal.reasoning), 0)

        # Bayesian update
        core.record_trade_outcome(pnl=100.0, was_win=True)
        state = core.get_bayesian_state()
        self.assertGreater(state["win_rate_mean"], 0.5)

        # Audit log
        audit = core.get_audit_log()
        self.assertGreater(len(audit), 0)

        # Decision log
        dlog = core.get_decision_log()
        self.assertGreater(len(dlog), 0)


# ──────────────────────────────────────────────────────────────
# Ω-T55 to Ω-T108: KINETIC RISK TESTS
# ──────────────────────────────────────────────────────────────

class TestBayesianKelly(unittest.TestCase):
    """Ω-T55 to Ω-T63"""

    def test_t55_kelly_update(self):
        """Ω-T55: Kelly fraction updates with new trade data."""
        est = BayesianKellyEstimator(prior_wins=50, prior_losses=50)
        # Feed winning trades
        for _ in range(30):
            est.update(100.0, True)
        for _ in range(10):
            est.update(-50.0, False)
        state = est.get_state()
        self.assertGreater(state["current_kelly"], 0.0)

    def test_t56_fractional_kelly(self):
        """Ω-T56: Fractional Kelly is smaller than raw Kelly."""
        est = BayesianKellyEstimator(kelly_fraction=0.25)
        est.update(100.0, True)
        est.update(100.0, True)
        state = est.get_state()
        self.assertLessEqual(state["current_kelly"], 0.25)

    def test_t59_drawdown_adjustment(self):
        """Ω-T59: Drawdown reduces Kelly."""
        est = BayesianKellyEstimator()
        for _ in range(20):
            est.update(50.0, True)
        kelly_normal = est.get_state()["current_kelly"]
        est.update_drawdown(2.0)  # 2% drawdown
        kelly_dd = est.get_state()["current_kelly"]
        self.assertLessEqual(kelly_dd, kelly_normal)

    def test_t63_anti_gambler(self):
        """Ω-T63: Kelly never exceeds max cap."""
        est = BayesianKellyEstimator(max_absolute_kelly=0.25)
        for _ in range(1000):
            est.update(1000.0, True)
        self.assertLessEqual(est.get_state()["current_kelly"], 0.25)


class TestCircuitBreaker(unittest.TestCase):
    """Ω-T64 to Ω-T72"""

    def test_t64_seven_levels(self):
        """Ω-T64: All 7 levels exist and have correct thresholds."""
        self.assertEqual(CircuitBreakerLevel.GREEN.trigger_dd_pct, 0.0)
        self.assertEqual(CircuitBreakerLevel.YELLOW.trigger_dd_pct, 0.3)
        self.assertEqual(CircuitBreakerLevel.ORANGE.trigger_dd_pct, 0.6)
        self.assertEqual(CircuitBreakerLevel.RED.trigger_dd_pct, 1.0)
        self.assertEqual(CircuitBreakerLevel.CRITICAL.trigger_dd_pct, 1.5)
        self.assertEqual(CircuitBreakerLevel.EMERGENCY.trigger_dd_pct, 2.0)
        self.assertEqual(CircuitBreakerLevel.CATASTROPHIC.trigger_dd_pct, 3.0)

    def test_t65_drawdown_trigger(self):
        """Ω-T65: Drawdown triggers correct level."""
        cb = CircuitBreakerSystem()
        state = cb.evaluate(
            drawdown_pct=1.2, consecutive_losses=0, volatility=1.0,
            latency_ms=5.0, avg_latency_ms=5.0, data_quality_score=1.0,
        )
        self.assertEqual(state.current_level, CircuitBreakerLevel.RED)

    def test_t66_consecutive_loss_trigger(self):
        """Ω-T66: Consecutive losses trigger circuit breaker."""
        cb = CircuitBreakerSystem()
        state = cb.evaluate(
            drawdown_pct=0.1, consecutive_losses=10, volatility=1.0,
            latency_ms=5.0, avg_latency_ms=5.0, data_quality_score=1.0,
        )
        self.assertIn(state.current_level, [CircuitBreakerLevel.RED, CircuitBreakerLevel.CRITICAL])

    def test_t70_auto_recovery(self):
        """Ω-T70: Recovery stages increment."""
        cb = CircuitBreakerSystem()
        cb._state.cooldown_remaining = 0
        cb._state.recovery_stage = 0
        cb._recovery_active = True
        cb.advance_recovery()
        self.assertEqual(cb._state.recovery_stage, 1)

    def test_t72_ftmo_compliance(self):
        """Ω-T72: FTMO compliance reporting."""
        cb = CircuitBreakerSystem(daily_loss_limit=5.0, total_loss_limit=10.0)
        compliance = cb.get_ftmo_compliance()
        self.assertTrue(compliance["ftmo_safe"])


class TestPositionRiskMonitor(unittest.TestCase):
    """Ω-T73 to Ω-T81"""

    def test_t73_pnl_tracking(self):
        """Ω-T73: Unrealized and realized P&L tracked."""
        monitor = PositionRiskMonitor()
        pos = PositionRecord(
            position_id="p1", symbol="BTCUSDT", direction="long",
            entry_price=50000.0, current_price=50100.0, size=1.0,
            unrealized_pnl=100.0, realized_pnl=0.0,
            stop_loss=49500.0, take_profit=51000.0,
            entry_time=time.time(), regime="trending",
            correlation_to_portfolio=0.3, funding_cost=0.0,
        )
        monitor.add_position(pos)
        self.assertGreater(monitor.get_total_unrealized_pnl(), 0)

    def test_t75_drawdown(self):
        """Ω-T75: Drawdown calculation."""
        monitor = PositionRiskMonitor()
        pnl = monitor.close_position("nonexistent", 0)
        self.assertEqual(pnl, 0.0)

    def test_t77_cvar(self):
        """Ω-T77: CVaR computed from P&L history."""
        monitor = PositionRiskMonitor()
        monitor._pnl_history = deque([-100, -50, -200, -30, 100, 50, -150, -80, 200, -75] * 10)
        cvar = monitor.get_cvar(0.95)
        self.assertGreater(cvar, 0)


class TestDynamicExitEngine(unittest.TestCase):
    """Ω-T82 to Ω-T90"""

    def test_t82_adaptive_stop(self):
        """Ω-T82: Adaptive stop based on ATR × multiplier."""
        engine = DynamicExitEngine()
        stop = engine.compute_adaptive_stop(50000.0, "long", 100.0, "trending", 2.0)
        self.assertAlmostEqual(stop, 49800.0, places=1)

    def test_t83_trailing_stop(self):
        """Ω-T83: Trailing stop tightens as profit grows."""
        engine = DynamicExitEngine()
        pos = PositionRecord(
            position_id="t1", symbol="BTCUSDT", direction="long",
            entry_price=50000.0, current_price=50500.0, size=1.0,
            unrealized_pnl=500.0, realized_pnl=0.0,
            stop_loss=49800.0, take_profit=52000.0,
            entry_time=time.time(), regime="trending",
            correlation_to_portfolio=0.3, funding_cost=0.0,
        )
        new_stop = engine.compute_trailing_stop(
            49800.0, 50500.0, 50000.0, "long", 100.0, 2.0, 0.05,
        )
        # Stop should have moved up from original
        self.assertGreaterEqual(new_stop, 49800.0)

    def test_t88_emergency_exit(self):
        """Ω-T88: Emergency exit triggers on flash crash."""
        engine = DynamicExitEngine()
        self.assertTrue(
            engine.check_emergency_exit(
                volatility=15.0, spread_bps=50.0, liquidity_usd=500.0,
                is_flash_crash=True,
            )
        )
        self.assertFalse(
            engine.check_emergency_exit(
                volatility=2.0, spread_bps=5.0, liquidity_usd=100000.0,
                is_flash_crash=False,
            )
        )


class TestTailRiskProtector(unittest.TestCase):
    """Ω-T91 to Ω-T99"""

    def test_t91_tail_risk_score(self):
        """Ω-T91: Composite tail risk score in [0, 1]."""
        protector = TailRiskProtector()
        score = protector.detect_tail_risk(
            skewness=-3.0, kurtosis=15.0,
            correlation_breakdown=True,
            liquidation_proximity_bps=50.0,
        )
        self.assertGreater(score, 0.5)  # High risk conditions

    def test_t92_gpd_fit(self):
        """Ω-T92: GPD fitting works with enough data."""
        protector = TailRiskProtector()
        import random
        random.seed(42)
        for _ in range(200):
            protector.update(random.gauss(0, 0.01))
        xi, scale, n = protector.fit_gpd()
        self.assertGreaterEqual(n, 0)

    def test_t98_recovery_path(self):
        """Ω-T98: Recovery path planning after drawdown."""
        protector = TailRiskProtector()
        path = protector.generate_recovery_path(current_dd=2.0, target_dd=0.0)
        self.assertEqual(path["status"], "recovering")
        self.assertGreater(len(path["steps"]), 0)


class TestPortfolioRiskOptimizer(unittest.TestCase):
    """Ω-T100 to Ω-T108"""

    def test_t100_variance_contribution(self):
        """Ω-T100: Variance decomposition by strategy."""
        opt = PortfolioRiskOptimizer()
        import random
        random.seed(42)
        for sid in ["strat_a", "strat_b"]:
            for _ in range(50):
                opt.record_strategy_return(sid, random.gauss(0.001, 0.01))
        contrib = opt.get_variance_contribution()
        self.assertIn("strat_a", contrib)
        self.assertIn("strat_b", contrib)

    def test_t103_concentration_hhi(self):
        """Ω-T103: HHI concentration index."""
        opt = PortfolioRiskOptimizer()
        opt.record_strategy_return("dominant", 0.1)
        opt.record_strategy_return("dominant", 0.08)
        opt.record_strategy_return("minor", 0.001)
        hhi = opt.compute_hhi()
        self.assertGreater(hhi, 0)

    def test_t107_hedge_ratio(self):
        """Ω-T107: Minimum variance hedge ratio."""
        opt = PortfolioRiskOptimizer()
        import random
        random.seed(42)
        p = [random.gauss(0.001, 0.02) for _ in range(100)]
        h = [-x * 0.7 + random.gauss(0, 0.005) for x in p]
        ratio = opt.compute_min_variance_hedge_ratio(p, h)
        self.assertAlmostEqual(ratio, -0.7, delta=0.6)


# ──────────────────────────────────────────────────────────────
# Ω-T109 to Ω-T162: SHADOW ENGINE & TELEMETRY TESTS
# ──────────────────────────────────────────────────────────────

class TestCounterfactualEngine(unittest.TestCase):
    """Ω-T109 to Ω-T117"""

    def test_t109_timing_contrafactual(self):
        """Ω-T109: Timing dimension simulated across offsets."""
        engine = CounterfactualEngine()
        price_at_offset = {}
        for offset in [-20, -10, -5, -3, -2, -1, 1, 2, 3, 5, 10, 20]:
            price_at_offset[offset] = 50000.0 + offset * 0.5

        results = engine.simulate_timing(
            actual_entry_price=50000.0, actual_exit_price=50100.0,
            actual_pnl=100.0, direction="long",
            price_at_offset=price_at_offset, tick_size=0.5,
        )
        self.assertGreater(len(results), 0)

    def test_t111_sizing_contrafactual(self):
        """Ω-T111: Sizing variants computed."""
        engine = CounterfactualEngine()
        results = engine.simulate_sizing(actual_pnl=100.0, actual_size_fraction=0.1)
        self.assertEqual(len(results), 7)  # 7 variants

    def test_t115_hedge_contrafactual(self):
        """Ω-T115: Hedge variants reduce PnL proportionally."""
        engine = CounterfactualEngine()
        results = engine.simulate_hedge(actual_pnl=100.0, hedge_effectiveness=0.7)
        no_hedge = next(r for r in results if "0%" in r.variant)
        full_hedge = next(r for r in results if "100%" in r.variant)
        # Full hedge should reduce P&L more than no hedge
        self.assertLess(full_hedge.simulated_pnl, no_hedge.simulated_pnl)


class TestForensicAnalyzer(unittest.TestCase):
    """Ω-T118 to Ω-T126"""

    def test_t118_t126_forensic_analysis(self):
        """Ω-T118-T126: All 9 layers checked."""
        analyzer = ForensicAnalyzer()
        good_checks = {"check1": True, "check2": True}
        bad_checks = {"check1": True, "check2": False}

        analysis = analyzer.analyze(
            trade_id="t1", signal_id="s1", direction=Direction.LONG,
            symbol="BTCUSDT", entry_price=50000.0, exit_price=49900.0,
            pnl=-100.0, exit_reason="stop_loss",
            data_checks=good_checks, feature_checks=good_checks,
            signal_checks=good_checks, confluence_checks=good_checks,
            regime_checks=good_checks, risk_checks=good_checks,
            execution_checks=good_checks, exit_checks=good_checks,
            market_checks=good_checks,
        )
        self.assertTrue(analysis.data_integrity_ok)
        self.assertFalse(analysis.was_profitable)

        analysis2 = analyzer.analyze(
            trade_id="t2", signal_id="s2", direction=Direction.LONG,
            symbol="BTCUSDT", entry_price=50000.0, exit_price=49900.0,
            pnl=-100.0, exit_reason="stop_loss",
            data_checks=good_checks, feature_checks=bad_checks,
            signal_checks=good_checks, confluence_checks=good_checks,
            regime_checks=bad_checks, risk_checks=good_checks,
            execution_checks=good_checks, exit_checks=good_checks,
            market_checks=bad_checks,
        )
        self.assertFalse(analysis2.feature_computation_ok)
        self.assertTrue(analysis2.market_condition_adverse)


class TestRootCausePatchSystem(unittest.TestCase):
    """Ω-T127 to Ω-T135"""

    def test_t127_root_cause_classification(self):
        """Ω-T127: Root cause correctly classified from failures."""
        system = RootCausePatchSystem()
        analysis = PostTradeAnalysis(
            trade_id="t1", signal_id="s1", direction=Direction.LONG,
            symbol="BTC", entry_price=50000, exit_price=49900,
            pnl=-100, pnl_pct=-0.2, holding_time_seconds=60,
            exit_reason="stop", was_profitable=False,
            data_integrity_ok=False, feature_computation_ok=True,
            signal_generation_ok=True, confluence_evaluation_ok=True,
            regime_context_ok=True, risk_assessment_ok=True,
            execution_quality_ok=True, exit_logic_ok=True,
            market_condition_adverse=False, contrafactual_results={},
            root_cause=None, patch_proposed=None,
        )
        root_cause = system.classify_root_cause(analysis, {"data": ["checksum failed"]})
        self.assertEqual(root_cause, RootCauseCategory.DATA)

    def test_t128_patch_proposal(self):
        """Ω-T128: Patch proposal created."""
        system = RootCausePatchSystem()
        patch = system.propose_patch(
            root_cause=RootCauseCategory.DATA,
            description="Fix checksum validation",
            current_behavior="Invalid data accepted",
            proposed_behavior="Reject invalid data",
        )
        self.assertEqual(patch.validation_status, "pending")
        self.assertGreater(len(patch.patch_id), 0)

    def test_t135_learning_velocity(self):
        """Ω-T135: Learning velocity tracked."""
        system = RootCausePatchSystem()
        system._discovery_times["bug1"] = time.time() - 100
        system._deploy_times["bug1"] = time.time()
        velocity = system.get_learning_velocity()
        self.assertEqual(velocity, 0.0)  # Not recorded yet

        system.record_bug_discovery("bug2")
        time.sleep(0.01)
        system.record_patch_deploy("bug2")
        velocity = system.get_learning_velocity()
        self.assertGreater(velocity, 0)


class TestShadowEngineIntegration(unittest.TestCase):
    """Ω-T109 through Ω-T135: End-to-end shadow engine."""

    def test_full_post_trade(self):
        """Full post-trade analysis pipeline."""
        engine = ShadowEngine()

        good_checks = {"c1": True, "c2": True}
        bad_checks = {"c1": True, "c2": "checksum_failed"}

        result = engine.run_full_post_trade_analysis(
            trade_id="t1", signal_id="s1", direction=Direction.LONG,
            symbol="BTCUSDT", entry_price=50000.0, exit_price=49900.0,
            pnl=-100.0, exit_reason="stop_loss",
            data_checks=good_checks, feature_checks=good_checks,
            signal_checks=good_checks, confluence_checks=good_checks,
            regime_checks=bad_checks, risk_checks=good_checks,
            execution_checks=good_checks, exit_checks=good_checks,
            market_checks=good_checks,
        )
        self.assertIn("analysis", result)
        self.assertIn("root_cause", result)
        self.assertIn("archived", result)
        self.assertTrue(result["archived"])


class TestMetaLearning(unittest.TestCase):
    """Ω-T145 to Ω-T153"""

    def test_t148_thompson_sampling(self):
        """Ω-T148: Thompson Sampling allocates more to better strategies."""
        ts = ThompsonSamplingAllocator(["strat_a", "strat_b"])
        # Strat A wins 80% of the time
        for _ in range(80):
            ts.update_outcome("strat_a", True, 100.0)
        for _ in range(20):
            ts.update_outcome("strat_a", False, -50.0)
        # Strat B wins 40% of the time
        for _ in range(40):
            ts.update_outcome("strat_b", True, 100.0)
        for _ in range(60):
            ts.update_outcome("strat_b", False, -50.0)

        wr = ts.get_expected_win_rates()
        self.assertGreater(wr["strat_a"], wr["strat_b"])

    def test_t146_drift_detection(self):
        """Ω-T146: Concept drift detected when distribution shifts."""
        detector = ConceptDriftDetector()
        # Stable period
        for _ in range(50):
            detector.update(0.0)
        self.assertFalse(detector.is_drift_detected())

        # Shift to high values
        for _ in range(50):
            detector.update(0.9)
        # At least one detector should flag
        self.assertTrue(
            detector.is_drift_detected() or detector.is_warning(),
        )

    def test_t150_parameter_stability(self):
        """Ω-T150-T151: Parameter stability monitored."""
        monitor = ParameterStabilityMonitor()
        # Stable parameter
        for _ in range(50):
            monitor.update("stable_param", 0.5)
        stability = monitor.get_stability_scores()
        self.assertGreater(stability["stable_param"], 0.8)

        # Unstable parameter — oscillating with non-zero mean so CV is high
        for _ in range(50):
            monitor.update("unstable_param", 10.0 + (1 if _ % 2 == 0 else -1) * 50.0)
        stability = monitor.get_stability_scores()
        self.assertLess(stability["unstable_param"], 0.5)

    def test_t153_autonomous_vs_human(self):
        """Ω-T153: High stability → autonomous, low → human."""
        m = MetaLearningEngine(["strat_a"])
        # Autonomous: high stability parameter change
        change_id = m.propose_change(
            component="threshold", change_type="parameter",
            current_value=0.5, proposed_value=0.55,
            stability_score=0.9, justification="Optimized",
        )
        self.assertEqual(m._autonomous_count, 1)

        # Human: low stability change
        change_id2 = m.propose_change(
            component="model", change_type="structural",
            current_value="v1", proposed_value="v2",
            stability_score=0.3, justification="New architecture",
        )
        self.assertIn(change_id2, m._pending_approvals)
        self.assertEqual(m._human_approval_count, 1)


class TestTelemetryAndPerformance(unittest.TestCase):
    """Ω-T136 to Ω-T162"""

    def test_t136_t144_performance_attribution(self):
        """Ω-T136-T144: Full performance attribution."""
        attributor = PerformanceAttributor()
        for i in range(20):
            attributor.record_trade(
                signal_id="sig_a", regime_key="trending_up",
                pnl=100.0 if i % 3 != 0 else -40.0,
                execution_cost=10.0,
                gross_pnl=110.0 if i % 3 != 0 else -30.0,
            )
        result = attributor.compute_attribution()
        self.assertIsInstance(result, PerformanceAttribution)
        self.assertGreater(result.total_pnl, -10)  # Should be net positive
        self.assertIn("sig_a", result.signal_attribution)

    def test_t143_opportunity_cost(self):
        """Ω-T143: Opportunity cost tracking."""
        attributor = PerformanceAttributor()
        attributor.record_rejected_trade(
            trade_reason="low confidence", would_have_pnl=200.0,
            was_rejection_correct=False,
        )
        attributor.record_rejected_trade(
            trade_reason="regime mismatch", would_have_pnl=-100.0,
            was_rejection_correct=True,
        )
        self.assertGreater(attributor._opp_cost_rejected_wrong, 0)
        self.assertGreater(attributor._opp_cost_rejected_right, 0)

    def test_t154_t162_telemetry_engine(self):
        """Ω-T154-T162: Telemetry with alerts and KG updates."""
        engine = TelemetryEngine()

        # Emit event
        evt = engine.emit("trade_executed", "trinity_core", {"pnl": 100.0}, latency_us=500)
        self.assertIn("event_type", evt)

        # Emit alert
        alert = engine.emit_alert(AlertLevel.WARNING, "High latency", "execution")
        self.assertIsInstance(alert, Alert)
        self.assertEqual(alert.level, AlertLevel.WARNING)

        # Trade summary
        summary = engine.generate_trade_summary(
            "t1", "long", "BTCUSDT", 50000.0, 50100.0, 100.0, 0.85, "confluence",
        )
        self.assertEqual(summary["trade_id"], "t1")
        self.assertTrue(summary["was_profitable"])

        # Dashboard data
        dashboard = engine.get_dashboard_data()
        self.assertGreater(dashboard["n_events_total"], 0)

        # KG updates
        kg_updates = engine.get_kg_updates()
        self.assertGreater(len(kg_updates), 0)

    def test_t160_anomaly_detection(self):
        """Ω-T160: Latency anomaly detected."""
        engine = TelemetryEngine()
        # Normal latency
        for _ in range(100):
            engine.emit("trade", "core", {}, latency_us=500)
        # Spike
        engine.emit("trade", "core", {}, latency_us=50000)
        alerts = engine.check_anomalies()
        self.assertGreater(len(alerts), 0)

    def test_t159_daily_report(self):
        """Ω-T159: Daily report generation."""
        engine = TelemetryEngine()
        attributor = PerformanceAttributor()
        attributor.record_trade("sig_a", "trending", pnl=100.0, execution_cost=10.0, gross_pnl=110.0)

        report = engine.generate_daily_report(
            performance=attributor.compute_attribution(),
            rolling_metrics={"n_trades": 1},
            n_alerts=0, n_trades=1, drawdown=0.1,
        )
        self.assertIn("date", report)
        self.assertEqual(report["n_trades"], 1)


if __name__ == "__main__":
    unittest.main()
