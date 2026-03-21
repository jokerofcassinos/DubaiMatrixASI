import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import time
from datetime import datetime, timezone

# Add project root to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from core.decision.trinity_core import TrinityCore, Action, Decision
from core.consciousness.regime_detector import MarketRegime, RegimeState
from market.data_engine import MarketSnapshot

class TestStabilityImprovements(unittest.TestCase):
    def setUp(self):
        self.trinity = TrinityCore()
    def setUp(self):
        self.trinity = TrinityCore()
        # Bypassing cold start
        self.trinity._startup_timestamp = time.time() - 3600
        
    def test_mc_persistence_filter(self):
        """Verifica se o filtro de persistência do MC veta oscilações estocásticas."""
        quantum_state = MagicMock()
        quantum_state.phi = 0.20
        quantum_state.collapsed_signal = 0.8
        quantum_state.confidence = 0.9
        quantum_state.coherence = 0.8
        quantum_state.entropy = 0.5
        quantum_state.superposition = False
        quantum_state.metadata = {"entropy": 0.5, "phi_last": 0.2, "kl_divergence": 0.1, "tick_velocity": 5.0}
        
        regime_state = MagicMock()
        regime_state.current = MarketRegime.CREEPING_BULL
        regime_state.v_pulse_detected = False
        regime_state.current_intensity = 0.5
        
        snapshot = MagicMock()
        snapshot.timestamp = datetime.now(timezone.utc)
        snapshot.price = 70000.0
        snapshot.atr = 100.0
        snapshot.metadata = {
            "v_pulse_detected": False, 
            "kl_divergence": 0.1,
            "v_pulse_capacitor": 0.1,
            "shannon_entropy": 0.9,
            "tick_velocity": 5.0
        }
        snapshot.symbol_info = {"point": 0.01}
        snapshot.indicators = {"M1_atr_14": [100.0], "M5_atr_14": [100.0], "m1_closes": [70000.0]*50}
        snapshot.candles = {"M1": {
            "high": [70005.0]*20, 
            "low": [69995.0]*20,
            "open": [70000.0]*20,
            "close": [70000.0]*20
        }}
        snapshot.tick = {"ask": 70000.0, "bid": 69995.0}
        
        # Patch internally to avoid complex mock chains
        self.trinity._get_current_atr = MagicMock(return_value=100.0)
        
        # Simular MC instável: Cycle 1 Negativo
        mc_result_neg = MagicMock()
        mc_result_neg.monte_carlo_score = 0.1
        mc_result_neg.win_probability = 0.5
        mc_result_neg.expected_return = -1.5
        mc_result_neg.conditional_var_95 = -2.0
        mc_result_neg.simulation_time_ms = 10.0
        mc_result_neg.optimal_sl_distance = 0
        mc_result_neg.optimal_tp_distance = 0
        
        with patch.object(self.trinity.monte_carlo, 'simulate_trade', return_value=mc_result_neg):
            decision = self.trinity.decide(quantum_state, regime_state, snapshot, MagicMock())
            self.assertEqual(decision.action, Action.WAIT)
            self.assertIn("MC_NEGATIVE_EV", decision.reasoning)
            
        # Simular MC instável: Cycle 2 Positivo (Mas média ainda negativa ou instável)
        mc_result_pos = MagicMock()
        mc_result_pos.monte_carlo_score = 0.1
        mc_result_pos.win_probability = 0.5
        mc_result_pos.expected_return = 0.5
        mc_result_pos.conditional_var_95 = -1.0
        mc_result_pos.simulation_time_ms = 10.0
        mc_result_pos.optimal_sl_distance = 0
        mc_result_pos.optimal_tp_distance = 0
        
        with patch.object(self.trinity.monte_carlo, 'simulate_trade', return_value=mc_result_pos):
            decision = self.trinity.decide(quantum_state, regime_state, snapshot, MagicMock())
            # Média de (-1.5 + 0.5) / 2 = -0.5. Deve vetar por instabilidade.
            self.assertEqual(decision.action, Action.WAIT)
            self.assertIn("MC_STABILITY_VETO", decision.reasoning)

        # Simular Cycle 3 Positivo -> Média (-1.5 + 0.5 + 1.2) / 3 = 0.06. Deve liberar.
        mc_result_pos_2 = MagicMock()
        mc_result_pos_2.monte_carlo_score = 0.5
        mc_result_pos_2.win_probability = 0.6
        mc_result_pos_2.expected_return = 1.2
        mc_result_pos_2.conditional_var_95 = -0.5
        mc_result_pos_2.simulation_time_ms = 10.0
        mc_result_pos_2.optimal_sl_distance = 100.0
        mc_result_pos_2.optimal_tp_distance = 200.0
        mc_result_pos_2.optimal_rr_ratio = 2.0
        
        with patch.object(self.trinity.monte_carlo, 'simulate_trade', return_value=mc_result_pos_2):
            decision = self.trinity.decide(quantum_state, regime_state, snapshot, MagicMock())
            self.assertEqual(decision.action, Action.BUY)

if __name__ == "__main__":
    unittest.main()
