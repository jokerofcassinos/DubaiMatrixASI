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
from execution.sniper_executor import SniperExecutor

class TestOmegaStability(unittest.TestCase):
    def setUp(self):
        self.trinity = TrinityCore()
        # Bypassing cold start cooldown for tests
        self.trinity._startup_timestamp = time.time() - 1000
        
        # Ensure OMEGA is initialized
        OMEGA.load()

    def test_kl_paradigm_shift_veto(self):
        """Verifica se o Veto de Paradigm Shift (KL > 1.5) funciona."""
        snapshot = MagicMock()
        snapshot.metadata = {"kl_divergence": 4.5}
        snapshot.price = 70000.0
        snapshot.timestamp = datetime.now(timezone.utc)
        snapshot.symbol_info = {"point": 0.01}
        snapshot.indicators = {"M1_atr_14": [10.0]}
        # Mock empty candles to avoid attribute errors if accessed
        snapshot.candles = {"M1": {"close": []}}
        
        quantum_state = MagicMock()
        quantum_state.collapsed_signal = -0.8
        quantum_state.confidence = 0.95
        quantum_state.coherence = 0.9
        # Avoid agent_signals causing attribute errors
        quantum_state.agent_signals = []
        
        regime_state = MagicMock()
        regime_state.current = MarketRegime.TRENDING_BULL
        regime_state.v_pulse_detected = False
        
        asi_state = MagicMock()
        asi_state.startTime = time.time() - 1000 
        asi_state.circuit_breaker_active = False

        # Mocking check_vetos to pass through to the KL check
        with patch.object(self.trinity, '_check_vetos', return_value=None):
            decision = self.trinity.decide(quantum_state, regime_state, snapshot, asi_state)
        
        self.assertIsNotNone(decision)
        self.assertEqual(decision.action, Action.WAIT)
        # Fix string match
        self.assertIn("PARADIGM_SHIFT_CLOSE", decision.reasoning)
        self.assertEqual(decision.metadata.get("emergency_close"), True)

    def test_phi_gate_creeping_regime(self):
        """Verifica se regimes rasteiros exigem Φ mais alto (0.35)."""
        snapshot = MagicMock()
        snapshot.metadata = {"kl_divergence": 0.0}
        snapshot.price = 70000.0
        snapshot.timestamp = datetime.now(timezone.utc)
        snapshot.symbol_info = {"point": 0.01}
        snapshot.indicators = {"M1_atr_14": [10.0]}
        snapshot.candles = {"M1": {"close": []}}
        
        quantum_state = MagicMock()
        quantum_state.phi = 0.20
        quantum_state.collapsed_signal = 0.8
        quantum_state.raw_signal = 0.8
        quantum_state.confidence = 0.8
        quantum_state.coherence = 0.8
        quantum_state.agent_signals = []
        
        regime_state = MagicMock()
        regime_state.current = MarketRegime.CREEPING_BULL
        regime_state.v_pulse_detected = False
        
        asi_state = MagicMock()
        asi_state.startTime = time.time() - 1000
        asi_state.circuit_breaker_active = False

        # Mocking internal methods that precede the Phi Gate check
        with patch.object(self.trinity, '_check_vetos', return_value=None), \
             patch.object(self.trinity, '_wait', side_effect=lambda r: MagicMock(action=Action.WAIT, reasoning=f"WAIT: {r}")):
            
            # Setup Quantum State for "Convergence" but low PHI
            q_meta = {"agent_signals": "BULL[10] BEAR[2]"}
            quantum_state.metadata = q_meta
            
            decision = self.trinity.decide(quantum_state, regime_state, snapshot, asi_state)
            
            self.assertIsNotNone(decision)
            self.assertEqual(decision.action, Action.WAIT)
            found = "SIGNAL_FRAGILE" in decision.reasoning or "SUPERPOSITION" in decision.reasoning
            self.assertTrue(found, f"Expected Phi-related wait, got: {decision.reasoning}")

    def test_latency_abort(self):
        """Verifica se o kill-switch de latência aborta a execução lenta."""
        bridge = MagicMock()
        bridge.get_open_positions.return_value = []
        bridge.calculate_margin.return_value = 1000.0
        bridge.get_dynamic_commission_per_lot.return_value = 15.0
        bridge.get_symbol_info.return_value = {"stops_level": 10, "point": 0.01, "digits": 5}
        bridge.get_tick.return_value = {"bid": 70000.0, "ask": 70001.0}
        
        risk = MagicMock()
        risk.validate_trade.return_value = (True, 1.0, "OK")
        risk.calculate_lot_size.return_value = 1.0
        
        executor = SniperExecutor(bridge, risk)
        
        decision = MagicMock()
        decision.action = Action.BUY
        decision.confidence = 0.9
        decision.signal_strength = 0.8 # [PHASE 14 FIX] Concrete value for string formatting
        decision.entry_price = 70000.0
        decision.stop_loss = 69000.0
        decision.take_profit = 72000.0
        decision.metadata = {"phi": 0.5, "quantum_metadata": {}}
        
        snapshot = MagicMock()
        snapshot.metadata = {"v_pulse_detected": False, "non_ergodic_ruin": False}
        snapshot.account = {"balance": 100000.0, "margin_free": 50000.0, "margin_level": 500.0}
        snapshot.indicators = {"M5_atr_14": [100.0]}
        snapshot.timestamp = datetime.now(timezone.utc)
        snapshot.price = 70000.0
        snapshot.symbol_info = {"point": 0.01}
        
        asi_state = MagicMock()
        asi_state.win_rate = 0.6
        asi_state.total_trades = 50
        asi_state.total_profit = 5000.0
        asi_state.total_wins = 30
        asi_state.total_losses = 20
        
        with patch('time.time') as mock_time:
            start_time = 1000.0
            mock_time.side_effect = [start_time] + [start_time + 0.01] * 12 + [start_time + 0.50]
            
            result = executor.execute(decision, asi_state, snapshot)
            
            self.assertIsNone(result)
            bridge.send_market_order.assert_not_called()

if __name__ == "__main__":
    unittest.main()
