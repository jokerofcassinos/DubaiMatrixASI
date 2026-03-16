
import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import time
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from core.decision.trinity_core import TrinityCore, Action
from core.consciousness.quantum_thought import QuantumState
from core.consciousness.regime_detector import RegimeState, MarketRegime

class TestLiquidityShield(unittest.TestCase):
    def setUp(self):
        self.trinity = TrinityCore()

    def test_creeping_bull_sl_expansion(self):
        """Verifica se o SL é expandido em regime CREEPING_BULL."""
        # 1. Setup Mock Data
        price = 72000.0
        fast_atr = 100.0
        point_val = 1.0 # BTC typical
        
        snapshot = MagicMock()
        snapshot.price = price
        snapshot.tick = {"ask": price, "bid": price - 1}
        snapshot.symbol_info = {"point": point_val}
        
        # M1 Lows (últimos 10 mins) - Mínima em 71950
        m1_lows = [72000, 71980, 71970, 71990, 71950, 71960, 71975, 71985, 71995, 72005]
        m1_highs = [L+20 for L in m1_lows]
        m1_closes = [L+10 for L in m1_lows]
        m1_opens = [L+5 for L in m1_lows]
        snapshot.candles = {"M1": {"low": m1_lows, "high": m1_highs, "close": m1_closes, "open": m1_opens}}
        
        # Indicators
        snapshot.indicators = {
            "M1_atr_14": [fast_atr],
            "M5_atr_14": [fast_atr]
        }
        snapshot.metadata = {"v_pulse_detected": False}

        # Regime CREEPING_BULL
        regime_state = MagicMock()
        regime_state.current = MarketRegime.CREEPING_BULL
        regime_state.v_pulse_detected = False

        # Quantum State (Ignition)
        quantum_state = MagicMock()
        quantum_state.phi = 0.88 # High PHI to pass all gates
        quantum_state.confidence = 0.95
        quantum_state.collapsed_signal = 0.70 # Signal used by Trinity
        quantum_state.superposition = False # Disable veto
        quantum_state.coherence = 0.90
        quantum_state.entropy = 0.05 # Float for comparison
        quantum_state.signal_strength = 0.70 # Float for comparison
        quantum_state.metadata = {"entropy": 0.05}
        quantum_state.agent_signals = []
        quantum_state.reasoning = "Test Signal"

        asi_state = MagicMock()
        asi_state.startTime = time.time() - 3600
        asi_state.circuit_breaker_active = False
        
        # Monte Carlo Result
        mc_result = MagicMock()
        mc_result.monte_carlo_score = 0.5
        mc_result.win_probability = 0.7
        mc_result.expected_return = 100.0
        mc_result.conditional_var_95 = -10.0
        mc_result.simulation_time_ms = 10.0
        mc_result.optimal_sl_distance = 100.0
        mc_result.optimal_tp_distance = 200.0
        mc_result.optimal_rr_ratio = 2.0

        # Bypass internal checks
        with patch.object(self.trinity, '_check_vetos', return_value=None), \
             patch.object(self.trinity.monte_carlo, 'simulate_trade', return_value=mc_result):
            
            # Executar decisão
            decision = self.trinity.decide(quantum_state, regime_state, snapshot, asi_state)
            
            if decision.action == Action.WAIT:
                print(f"\n[DIAGNOSTIC] WAIT Reason: {decision.reasoning}")
            
            # Em regime de transição (is_transition_regime = True):
            # struct_buffer = max(25*1, 0.4*100) = 40.0
            # min_sl_dist = 0.8 * 100 = 80.0
            # m1_min = 71950
            # structural_sl = 71950 - 40 = 71910
            # safe_sl_floor = 72000 - 80 = 71920
            # stop_loss = min(71910, 71920) = 71910
            
            print(f"\n[TEST_RESULT] Action: {decision.action}")
            print(f"[TEST_RESULT] Entry Price: {decision.entry_price}")
            print(f"[TEST_RESULT] Stop Loss: {decision.stop_loss}")
            print(f"[TEST_RESULT] SL Distance: {abs(decision.entry_price - decision.stop_loss)}")
            
            self.assertEqual(decision.action, Action.BUY)
            
            # SL deve estar em no máximo 71910 (distância de 90 pontos do preço de entrada)
            self.assertLessEqual(decision.stop_loss, 71910)
            self.assertGreaterEqual(abs(decision.entry_price - decision.stop_loss), 80.0)

if __name__ == "__main__":
    unittest.main()
