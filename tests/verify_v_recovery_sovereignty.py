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

class TestVRecoverySovereignty(unittest.TestCase):
    def setUp(self):
        self.trinity = TrinityCore()
        # Bypass startup cooldown
        self.trinity._startup_timestamp = time.time() - 1000
        OMEGA.load()

    def test_v_pulse_sovereignty_bypass(self):
        """
        Scenario: 
        - Regime: DRIFTING_BEAR
        - Phi: 0.04 (Extremely low)
        - Coherence: 0.35
        - V-Pulse: Detected & High Intensity (0.85)
        - Signal: Strong BUY (0.75)
        - PnL Pred: IMPOSSIBLE:NEGATIVE_EXPECTANCY 
        
        Expected: Action.BUY (Sovereignty Bypass)
        """
        snapshot = MagicMock()
        snapshot.metadata = {
            "kl_divergence": 0.05, 
            "entropy": 0.5,
            "v_pulse_detected": True,
            "v_pulse_capacitor": 0.85,
            "pnl_prediction": "IMPOSSIBLE:NEGATIVE_EXPECTANCY",
            "tick_velocity": 5.0,
            "god_mode_active": False,
        }
        snapshot.price = 65000.0
        snapshot.atr = 200.0
        snapshot.timestamp = datetime.now(timezone.utc)
        snapshot.symbol_info = {"point": 0.01, "spread": 10, "trade_contract_size": 1.0}
        snapshot.indicators = {
            "M1_atr_14": [100.0], 
            "M5_atr_14": [200.0],
            "M5_ema_9": [64800.0],
            "M5_volume_ratio": [1.5]
        }
        # Fixed KeyError: 'open'
        snapshot.candles = {
            "M1": {
                "close": [65000.0] * 10,
                "open": [65000.0] * 10,
                "high": [65010.0] * 10,
                "low": [64990.0] * 10
            }
        }
        snapshot.tick = {"ask": 65000.0, "bid": 64999.0}
        
        quantum_state = MagicMock()
        quantum_state.phi = 0.04  # Use concrete float
        quantum_state.collapsed_signal = 0.75
        quantum_state.raw_signal = 0.75
        quantum_state.confidence = 0.85
        quantum_state.coherence = 0.35
        quantum_state.entropy = 0.5  # Fixed TypeError
        quantum_state.superposition = True 
        quantum_state.reasoning = "Test Reasoning"
        quantum_state.agent_signals = []
        quantum_state.metadata = {"bull_agents": [], "bear_agents": [], "agent_signals": ""}
        
        regime_state = MagicMock()
        regime_state.current = MarketRegime.DRIFTING_BEAR
        regime_state.v_pulse_detected = True
        regime_state.v_pulse_intensity = 0.85
        regime_state.duration_bars = 10
        
        asi_state = MagicMock()
        asi_state.startTime = time.time() - 1000
        asi_state.circuit_breaker_active = False
        asi_state.consecutive_losses = 0

        decision = self.trinity.decide(quantum_state, regime_state, snapshot, asi_state)
        
        print(f"DEBUG: Action: {decision.action if decision else 'None'}, Reasoning: {decision.reasoning if decision else 'N/A'}")
        
        self.assertIsNotNone(decision)
        self.assertEqual(decision.action, Action.BUY)
        # Verify specific bypasses active in reasoning
        self.assertTrue(any(x in decision.reasoning for x in ["PHASE_50_STRIKE", "PHOENIX_PULSE"]))

if __name__ == "__main__":
    unittest.main()
