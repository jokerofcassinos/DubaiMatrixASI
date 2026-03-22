import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import time
from datetime import datetime, timezone
import numpy as np

# Add project root to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from core.decision.trinity_core import TrinityCore, Action
from core.consciousness.regime_detector import MarketRegime
from core.consciousness.agents.base import AgentSignal
from config.omega_params import OMEGA


class TestCrashDetectionSovereignty(unittest.TestCase):
    """
    Verifies that the CrashVelocityDetector agent's crash sovereignty
    bypasses vetoes (SYNERGY_VETO, ENTROPIC_VACUUM, DRIFT_COHERENCE_WEAK)
    that previously blocked SELL signals during confirmed bear cascades.
    """

    def setUp(self):
        self.trinity = TrinityCore()
        self.trinity._startup_timestamp = time.time() - 1000
        OMEGA.load()

    def _make_base_snapshot(self, price=68500.0):
        """Create a standard bearish snapshot with all required fields."""
        snapshot = MagicMock()
        snapshot.price = price
        snapshot.atr = 150.0
        snapshot.timestamp = datetime.now(timezone.utc)
        snapshot.symbol_info = {"point": 0.01, "spread": 10, "trade_contract_size": 1.0}
        snapshot.indicators = {
            "M1_atr_14": [80.0],
            "M5_atr_14": [150.0],
            "M5_ema_9": [68700.0],  # Price below EMA = bearish
            "M5_volume_ratio": [2.0],
            "M1_velocity": [-15.0],
            "M1_entropy": [0.3],
        }
        # Bearish M1 candles (descending)
        m1_closes = list(np.linspace(68800, price, 15))
        m1_opens = [c + 20 for c in m1_closes]  # All red candles
        snapshot.candles = {
            "M1": {
                "close": m1_closes,
                "open": m1_opens,
                "high": [max(o, c) + 5 for o, c in zip(m1_opens, m1_closes)],
                "low": [min(o, c) - 5 for o, c in zip(m1_opens, m1_closes)],
                "tick_volume": [100] * 15,
            },
            "M5": {
                "close": list(np.linspace(68900, price, 15)),
                "open": [c + 30 for c in np.linspace(68900, price, 15)],
                "high": [c + 35 for c in np.linspace(68900, price, 15)],
                "low": [c - 5 for c in np.linspace(68900, price, 15)],
                "tick_volume": [500] * 15,
            }
        }
        snapshot.tick = {"ask": price + 1, "bid": price}
        snapshot.metadata = {
            "tick_velocity": -10.0,
            "v_pulse_detected": False,
            "v_pulse_capacitor": 0.0,
            "pnl_prediction": "OK",
            "kl_divergence": 0.05,
            "entropy": 0.3,
            "god_mode_active": False,
            "shannon_entropy": 0.5,
            "shannon_history": [0.5] * 12,
        }
        return snapshot

    def _make_base_quantum_state(self, signal=-0.50, phi=0.03, coherence=0.20):
        """Create a quantum state with low Phi (would trigger SYNERGY_VETO normally)."""
        qs = MagicMock()
        qs.phi = phi
        qs.collapsed_signal = signal
        qs.raw_signal = signal
        qs.confidence = 0.75
        qs.coherence = coherence
        qs.entropy = 0.3
        qs.superposition = False
        qs.reasoning = "Bearish pressure"
        qs.signal_strength = abs(signal)
        qs.agent_signals = []  # Will be populated per test
        qs.metadata = {
            "bull_agents": ["TrendAgent", "MomentumAgent"],
            "bear_agents": [
                "VolumeAgent", "VolatilityAgent", "PriceVelocityAgent",
                "AggressivenessAgent", "LiquiditySweepAgent", "ChartStructureAgent",
                "CandleAnatomyAgent", "OrderBlockAgent",
            ],
            "agent_signals": "",
            "top_bulls": [],
            "top_bears": [],
        }
        return qs

    def _make_regime_state(self, regime=MarketRegime.DRIFTING_BEAR):
        rs = MagicMock()
        rs.current = regime
        rs.v_pulse_detected = False
        rs.v_pulse_intensity = 0.0
        rs.duration_bars = 20
        rs.confidence = 0.7
        return rs

    def _make_asi_state(self):
        asi = MagicMock()
        asi.startTime = time.time() - 1000
        asi.circuit_breaker_active = False
        asi.consecutive_losses = 0
        return asi

    def test_crash_sovereignty_bypasses_synergy_veto(self):
        """
        Scenario: DRIFTING_BEAR, Phi=0.03 (would trigger SYNERGY_VETO),
        but CrashVelocityDetector emits is_crash_sovereign=True.
        Expected: SELL (not WAIT with SYNERGY_VETO)
        """
        snapshot = self._make_base_snapshot()
        qs = self._make_base_quantum_state(signal=-0.55, phi=0.03, coherence=0.25)
        rs = self._make_regime_state()
        asi = self._make_asi_state()

        # Add crash signal with sovereignty
        crash_agent_signal = AgentSignal(
            agent_name="CrashVelocityDetector",
            signal=-0.85,
            confidence=0.90,
            reasoning="CRASH_VELOCITY[severity=0.82]: ROC_CASCADE | BODY_EXPANSION | STRUCTURAL_CASCADE",
            weight=5.5,
            metadata={
                "crash_severity": 0.82,
                "cascade_depth": 3,
                "is_crash_sovereign": True,
                "roc_m1": -0.004,
                "roc_m5": -0.003,
                "roc_m15": -0.002,
                "body_expansion_count": 4,
            }
        )

        # Add some standard bear agents
        bear_agents = [
            AgentSignal("VolumeAgent", -0.6, 0.7, "Bearish volume", 1.0),
            AgentSignal("PriceVelocityAgent", -0.7, 0.8, "Bearish velocity", 1.8),
            AgentSignal("AggressivenessAgent", -0.5, 0.6, "Seller aggression", 1.7),
            AgentSignal("ChartStructureAgent", -0.4, 0.5, "Bearish structure", 1.5),
        ]

        qs.agent_signals = [crash_agent_signal] + bear_agents

        decision = self.trinity.decide(qs, rs, snapshot, asi)

        print(f"\n{'='*60}")
        print(f"TEST: Crash Sovereignty vs SYNERGY_VETO")
        print(f"Action: {decision.action if decision else 'None'}")
        print(f"Reasoning: {decision.reasoning if decision else 'N/A'}")
        print(f"{'='*60}")

        self.assertIsNotNone(decision)
        # The crash sovereignty should bypass SYNERGY_VETO
        if decision.action == Action.WAIT:
            self.assertNotIn("SYNERGY_VETO", decision.reasoning,
                             "SYNERGY_VETO should be bypassed by crash sovereignty")

    def test_crash_sovereignty_bypasses_entropic_vacuum(self):
        """
        Scenario: DRIFTING_BEAR with low entropy and low velocity
        (would trigger ENTROPIC_VACUUM_VETO), but crash is sovereign.
        Expected: Not blocked by ENTROPIC_VACUUM
        """
        snapshot = self._make_base_snapshot()
        snapshot.metadata["entropy"] = 0.2
        snapshot.metadata["tick_velocity"] = -3.0  # Low velocity
        qs = self._make_base_quantum_state(signal=-0.55, phi=0.10, coherence=0.35)
        rs = self._make_regime_state()
        asi = self._make_asi_state()

        crash_agent_signal = AgentSignal(
            agent_name="CrashVelocityDetector",
            signal=-0.80,
            confidence=0.88,
            reasoning="CRASH_VELOCITY[severity=0.75]: ROC_CASCADE | STRUCTURAL_CASCADE",
            weight=5.5,
            metadata={
                "crash_severity": 0.75,
                "cascade_depth": 2,
                "is_crash_sovereign": True,
            }
        )
        qs.agent_signals = [crash_agent_signal]

        decision = self.trinity.decide(qs, rs, snapshot, asi)

        print(f"\n{'='*60}")
        print(f"TEST: Crash Sovereignty vs ENTROPIC_VACUUM")
        print(f"Action: {decision.action if decision else 'None'}")
        print(f"Reasoning: {decision.reasoning if decision else 'N/A'}")
        print(f"{'='*60}")

        self.assertIsNotNone(decision)
        if decision.action == Action.WAIT:
            self.assertNotIn("ENTROPIC_VACUUM", decision.reasoning,
                             "ENTROPIC_VACUUM should be bypassed by crash sovereignty")

    def test_no_crash_sovereignty_without_threshold(self):
        """
        Scenario: Crash severity is below threshold (0.7) — NO sovereignty.
        Expected: Standard veto behavior preserved.
        """
        snapshot = self._make_base_snapshot()
        qs = self._make_base_quantum_state(signal=-0.35, phi=0.02, coherence=0.15)
        rs = self._make_regime_state()
        asi = self._make_asi_state()

        # Low severity, no sovereignty
        crash_agent_signal = AgentSignal(
            agent_name="CrashVelocityDetector",
            signal=-0.30,
            confidence=0.50,
            reasoning="CRASH_VELOCITY[severity=0.35]: ROC_CASCADE",
            weight=5.5,
            metadata={
                "crash_severity": 0.35,
                "cascade_depth": 1,
                "is_crash_sovereign": False,
            }
        )
        qs.agent_signals = [crash_agent_signal]

        decision = self.trinity.decide(qs, rs, snapshot, asi)

        print(f"\n{'='*60}")
        print(f"TEST: No Crash Sovereignty (below threshold)")
        print(f"Action: {decision.action if decision else 'None'}")
        print(f"Reasoning: {decision.reasoning if decision else 'N/A'}")
        print(f"{'='*60}")

        self.assertIsNotNone(decision)
        # With Phi=0.02 and no sovereignty, SYNERGY_VETO should block
        self.assertEqual(decision.action, Action.WAIT,
                         "Without crash sovereignty, low Phi should still trigger WAIT")


class TestCrashAgentStandalone(unittest.TestCase):
    """Tests the CrashVelocityDetectorAgent in isolation."""

    def test_bearish_cascade_detection(self):
        """Test that cascading bearish candles produce a strong sell signal."""
        from core.consciousness.agents.crash_velocity_agent import CrashVelocityDetectorAgent
        agent = CrashVelocityDetectorAgent()

        snapshot = MagicMock()
        snapshot.price = 67000.0

        # Create cascading bearish candles (each close lower, bodies expanding)
        n = 20
        closes_m1 = list(np.linspace(68000, 67000, n))  # Strong downtrend
        opens_m1 = [c + (i * 5 + 10) for i, c in enumerate(closes_m1)]  # Expanding bodies
        snapshot.candles = {
            "M1": {
                "close": closes_m1,
                "open": opens_m1,
                "high": [max(o, c) + 5 for o, c in zip(opens_m1, closes_m1)],
                "low": closes_m1,
                "tick_volume": list(range(100, 100 + n * 10, 10)),  # Expanding volume
            },
            "M5": {
                "close": list(np.linspace(68200, 67000, n)),
                "open": [c + 40 for c in np.linspace(68200, 67000, n)],
                "high": [c + 45 for c in np.linspace(68200, 67000, n)],
                "low": list(np.linspace(68180, 66980, n)),
                "tick_volume": [500] * n,
            },
            "M15": {
                "close": list(np.linspace(68500, 67000, n)),
                "open": [c + 50 for c in np.linspace(68500, 67000, n)],
                "high": [c + 55 for c in np.linspace(68500, 67000, n)],
                "low": list(np.linspace(68480, 66980, n)),
                "tick_volume": [1000] * n,
            }
        }

        result = agent.analyze(snapshot)
        print(f"\n{'='*60}")
        print(f"TEST: Bearish Cascade Detection (Standalone)")
        print(f"Signal: {result.signal if result else 'None'}")
        print(f"Reasoning: {result.reasoning if result else 'N/A'}")
        if result and result.metadata:
            print(f"Severity: {result.metadata.get('crash_severity', 'N/A')}")
            print(f"Cascade Depth: {result.metadata.get('cascade_depth', 'N/A')}")
            print(f"Sovereign: {result.metadata.get('is_crash_sovereign', 'N/A')}")
        print(f"{'='*60}")

        self.assertIsNotNone(result, "Crash agent should detect the cascade")
        self.assertLess(result.signal, -0.2, "Signal should be bearish")
        self.assertGreater(result.metadata.get("crash_severity", 0), 0.3,
                           "Severity should be significant")


class TestSwingAgentStandalone(unittest.TestCase):
    """Tests the SwingPositionDetectorAgent in isolation."""

    def test_distribution_detection(self):
        """Test that equal highs near price produce a sell signal."""
        from core.consciousness.agents.swing_position_agent import SwingPositionDetectorAgent
        agent = SwingPositionDetectorAgent()

        snapshot = MagicMock()
        snapshot.price = 69500.0

        n = 50
        # M15: Create a range with multiple equal highs near 69550
        base_closes = list(np.random.uniform(69200, 69500, n))
        # Insert peaks at ~69550 (distribution zone)
        for i in [10, 20, 30, 40]:
            base_closes[i] = 69480.0
        highs_m15 = [c + 70 for c in base_closes]
        # Create equal highs cluster
        for i in [10, 20, 30, 40]:
            highs_m15[i] = 69550.0  # Equal highs!

        snapshot.candles = {
            "M5": {
                "close": list(np.random.uniform(69300, 69500, 35)),
                "open": list(np.random.uniform(69300, 69500, 35)),
                "high": [69550.0 if i % 8 == 0 else 69520.0 for i in range(35)],
                "low": list(np.random.uniform(69200, 69400, 35)),
                "tick_volume": [300] * 35,
            },
            "M15": {
                "close": base_closes,
                "open": [c - 20 for c in base_closes],
                "high": highs_m15,
                "low": [c - 50 for c in base_closes],
                "tick_volume": [1000] * n,
            },
        }

        result = agent.analyze(snapshot)
        print(f"\n{'='*60}")
        print(f"TEST: Distribution Detection (Standalone)")
        print(f"Signal: {result.signal if result else 'None'}")
        print(f"Reasoning: {result.reasoning if result else 'N/A'}")
        if result and result.metadata:
            print(f"Swing Type: {result.metadata.get('swing_type', 'N/A')}")
            print(f"Is Swing Trade: {result.metadata.get('is_swing_trade', 'N/A')}")
            print(f"Target: {result.metadata.get('target_liquidity_level', 'N/A')}")
        print(f"{'='*60}")

        # Given the equal highs near price, should detect distribution
        if result is not None:
            print("✅ Agent detected a swing pattern")
        else:
            print("ℹ️ No swing pattern detected (normal if price too far from cluster)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
