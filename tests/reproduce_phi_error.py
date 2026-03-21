import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import time
from datetime import datetime, timezone

# Add project root to path
sys.path.append(os.getcwd())

from core.decision.trinity_core import TrinityCore, Action
from core.consciousness.regime_detector import MarketRegime
from config.omega_params import OMEGA

class TestReproduction(unittest.TestCase):
    def setUp(self):
        self.trinity = TrinityCore()
        OMEGA.load()

    def test_reproduce_phi_error(self):
        """Reproduces the UnboundLocalError: phi."""
        snapshot = MagicMock()
        snapshot.timestamp = datetime.now(timezone.utc)
        snapshot.symbol_info = {"point": 0.00001}
        snapshot.metadata = {
            "v_pulse_detected": False,
            "v_pulse_capacitor": 0.0,
            "tick_velocity": 1.0  # Low velocity to trigger kinetic_exhaustion logic
        }
        
        quantum_state = MagicMock()
        quantum_state.phi = 0.5
        quantum_state.raw_signal = 0.8
        quantum_state.collapsed_signal = 0.8
        quantum_state.confidence = 0.9
        quantum_state.superposition = False
        quantum_state.agent_signals = []
        quantum_state.entropy = 0.5  # Fixed from MagicMock to float
        quantum_state.coherence = 0.8
        
        regime_state = MagicMock()
        regime_state.current = MarketRegime.TRENDING_BULL
        regime_state.v_pulse_detected = False
        
        asi_state = MagicMock()
        
        # We need to fill _signal_history to reach line 280
        for _ in range(20):
            self.trinity._signal_history.append(0.8)
            
        # Bypass cold start
        self.trinity._startup_timestamp = time.time() - 1000
        
        print("Attempting to call decide()...")
        try:
            decision = self.trinity.decide(quantum_state, regime_state, snapshot, asi_state)
            print("Decide call successful (Error NOT reproduced)")
        except UnboundLocalError as e:
            print(f"REPRODUCED: {e}")
            raise e
        except Exception as e:
            print(f"Other error: {e}")
            raise e

if __name__ == "__main__":
    unittest.main()
