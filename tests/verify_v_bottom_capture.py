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
from config.omega_params import OMEGA

class TestVBottomCapture20(unittest.TestCase):
    def setUp(self):
        self.trinity = TrinityCore()
        # Bypass startup cooldown
        self.trinity._startup_timestamp = time.time() - 1000
        OMEGA.load()

    def test_chaos_ignition_capture(self):
        """
        Scenario (Phoenix Strike 2.0):
        - Regime: DRIFTING_BEAR
        - Phi: 0.05 (Would have failed SYNERGY_VETO 0.08)
        - Coherence: 0.22 (Would have failed DRIFT_COHERENCE_WEAK 0.25)
        - Velocity: Extreme HFT (45.0) -> Triggers Velocity Ignition
        - Signal: Strong BUY (0.75)
        - V-Pulse intensity: 0.85
        
        Expected: Action.BUY (Sovereignty 2.0)
        """
        snapshot = MagicMock()
        snapshot.metadata = {
            "v_pulse_detected": True,
            "v_pulse_capacitor": 0.85,
            "tick_velocity": 45.0, # Extreme velocity
            "pnl_prediction": "OK",
            "kl_divergence": 0.05,
            "entropy": 0.5,
            "god_mode_active": False,
        }
        snapshot.price = 70000.0
        snapshot.atr = 200.0
        snapshot.timestamp = datetime.now(timezone.utc)
        snapshot.symbol_info = {"point": 0.01, "spread": 10, "trade_contract_size": 1.0}
        snapshot.indicators = {
            "M1_atr_14": [100.0], 
            "M5_atr_14": [200.0],
            "M5_ema_9": [69800.0],
            "M5_volume_ratio": [1.5],
            "M1_velocity": [45.0]
        }
        snapshot.candles = {
            "M1": {
                "close": [70000.0] * 10,
                "open": [70000.0] * 10,
                "high": [70010.0] * 10,
                "low": [69990.0] * 10
            }
        }
        snapshot.tick = {"ask": 70000.0, "bid": 69999.0}
        
        quantum_state = MagicMock()
        quantum_state.phi = 0.05  # Chaos level
        quantum_state.collapsed_signal = 0.75
        quantum_state.raw_signal = 0.75
        quantum_state.confidence = 0.85
        quantum_state.coherence = 0.22 # Low coherence
        quantum_state.entropy = 0.5
        quantum_state.superposition = False 
        quantum_state.reasoning = "Test Reasoning"
        quantum_state.agent_signals = []
        quantum_state.metadata = {"bull_agents": [], "bear_agents": [], "agent_signals": ""}
        
        regime_state = MagicMock()
        regime_state.current = MarketRegime.DRIFTING_BEAR
        regime_state.v_pulse_detected = True
        regime_state.v_pulse_intensity = 0.85
        regime_state.duration_bars = 5
        
        asi_state = MagicMock()
        asi_state.startTime = time.time() - 1000
        asi_state.circuit_breaker_active = False
        asi_state.consecutive_losses = 0

        decision = self.trinity.decide(quantum_state, regime_state, snapshot, asi_state)
        
        print(f"DEBUG: Action: {decision.action if decision else 'None'}, Reasoning: {decision.reasoning if decision else 'N/A'}")
        
        self.assertIsNotNone(decision)
        # Check if the decision is BUY (expected due to sovereignty 2.0)
        self.assertEqual(decision.action, Action.BUY)
        # Check for Phoenix flag
        self.assertIn("Ω-PHOENIX_PULSE: SOVEREIGN", decision.reasoning)

if __name__ == "__main__":
    unittest.main()
