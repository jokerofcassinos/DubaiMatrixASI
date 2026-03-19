
import unittest
from unittest.mock import MagicMock, PropertyMock
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from execution.risk_quantum import RiskQuantumEngine
from config.settings import ASIState

class TestRiskGhostVeto(unittest.TestCase):
    def setUp(self):
        self.engine = RiskQuantumEngine()
        
        # Proper snapshot mocking to avoid TypeError in calculate_lot_size
        self.mock_snapshot = MagicMock()
        self.mock_snapshot.price = 60000.0
        self.mock_snapshot.digits_mult = 1.0
        self.mock_snapshot.metadata = {
            "pnl_prediction": "NEGATIVE_EXPECTANCY",
            "phi_last": 0.0,
            "raw_signal": 0.0,
            "kl_divergence": 0.0,
            "v_pulse_detected": False,
            "god_mode_active": False
        }
        
        # Account mock for margin checks
        self.mock_snapshot.account = {
            "balance": 100000.0,
            "margin_level": 500.0,
            "margin": 1000.0,
            "margin_free": 99000.0
        }
        
        # Mocking the regime object with a 'current' attribute that has a 'value'
        mock_regime = MagicMock()
        mock_regime.current.value = "CHOPPY"
        self.mock_snapshot.regime = mock_regime
        
        self.mock_snapshot.symbol_info = {"point": 0.01, "trade_contract_size": 1}
        self.mock_snapshot.indicators = {"M1_atr_14": [60.0]}
        
        # Mocking ASIState as it has read-only properties
        self.asi_state = MagicMock(spec=ASIState)
        self.asi_state.total_trades = 100
        self.asi_state.total_wins = 60
        self.asi_state.total_losses = 40
        self.asi_state.gross_profit = 12000.0
        self.asi_state.gross_loss = 4000.0
        
        # Mock the properties specifically using type() for PropertyMock
        type(self.asi_state).win_rate = PropertyMock(return_value=0.6)
        type(self.asi_state).avg_win = PropertyMock(return_value=200.0)
        type(self.asi_state).avg_loss = PropertyMock(return_value=100.0)
        type(self.asi_state).total_profit = PropertyMock(return_value=8000.0)

    def test_ghost_veto_active(self):
        """Should return 0.0 when negative expectancy is detected and no lethal bypass exists."""
        lot = self.engine.calculate_lot_size(
            balance=100000.0,
            stop_loss_distance=100.0,
            win_rate=0.6,
            avg_win=200.0,
            avg_loss=100.0,
            snapshot=self.mock_snapshot,
            asi_state=self.asi_state
        )
        self.assertEqual(lot, 0.0)

    def test_bypass_high_confidence(self):
        """Should bypass veto if confidence is extremely high (0.95 > 0.88)."""
        lot = self.engine.calculate_lot_size(
            balance=100000.0,
            stop_loss_distance=100.0,
            win_rate=0.6,
            avg_win=200.0,
            avg_loss=100.0,
            snapshot=self.mock_snapshot,
            asi_state=self.asi_state,
            confidence=0.95
        )
        self.assertGreater(lot, 0.0)

    def test_bypass_strong_consensus(self):
        """Should bypass veto if there is strong consensus (Phi > 0.30)."""
        self.mock_snapshot.metadata["phi_last"] = 0.4
        self.mock_snapshot.metadata["raw_signal"] = 0.5
        lot = self.engine.calculate_lot_size(
            balance=100000.0,
            stop_loss_distance=100.0,
            win_rate=0.6,
            avg_win=200.0,
            avg_loss=100.0,
            snapshot=self.mock_snapshot,
            asi_state=self.asi_state
        )
        self.assertGreater(lot, 0.0)

    def test_bypass_squeeze_regime(self):
        """Should bypass veto if in a Squeeze regime."""
        # Test as string
        self.mock_snapshot.regime = "SQUEEZE_BUILDUP"
        lot = self.engine.calculate_lot_size(
            balance=100000.0,
            stop_loss_distance=100.0,
            win_rate=0.6,
            avg_win=200.0,
            avg_loss=100.0,
            snapshot=self.mock_snapshot,
            asi_state=self.asi_state
        )
        self.assertGreater(lot, 0.0)

if __name__ == '__main__':
    import logging
    # Suppress all logs during test to see only unittest results
    logging.getLogger().setLevel(logging.CRITICAL)
    unittest.main()
