import unittest
from unittest.mock import MagicMock, patch, call
import time
import sys
import os

# 1. Setup path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 2. Mock heavy dependencies BEFORE any other imports
mock_log_obj = MagicMock()
mock_audit = MagicMock()
mock_registry = MagicMock()

# Mock the logger module
# PositionManager does 'from utils.logger import log'
# So sys.modules['utils.logger'].log should be our mock_log_obj
sys.modules["utils.logger"] = MagicMock(log=mock_log_obj)
sys.modules["utils.decorators"] = MagicMock(catch_and_log=lambda **kwargs: (lambda f: f))
sys.modules["utils.audit_engine"] = MagicMock(AUDIT_ENGINE=mock_audit)
sys.modules["execution.trade_registry"] = MagicMock(registry=mock_registry)
sys.modules["market.mt5_bridge"] = MagicMock()
sys.modules["execution.wormhole_router"] = MagicMock()

# Now import the target
from execution.position_manager import PositionManager
from config.omega_params import OMEGA

class TestTrailingRelaxation(unittest.TestCase):
    def setUp(self):
        self.bridge = MagicMock()
        with patch('concurrent.futures.ThreadPoolExecutor') as mock_pool_class:
            mock_pool = MagicMock()
            mock_pool_class.return_value = mock_pool
            mock_pool.submit.side_effect = lambda f, *args, **kwargs: f(*args, **kwargs)
            self.pm = PositionManager(self.bridge)
        
        # Reset OMEGA
        OMEGA.set("swing_trailing_relaxation", 2.0)
        OMEGA.set("swing_min_profit_mult", 10.0)
        OMEGA.set("min_profit_per_ticket", 25.0)
        
        # Reset mocks
        mock_log_obj.reset_mock()
        self.bridge.reset_mock()

    def test_swing_relaxation_logic(self):
        """Verifica se o relaxamento de trailing é aplicado para Swing Trades."""
        snapshot = MagicMock()
        snapshot.price = 68000.0
        snapshot.atr = 50.0
        snapshot.regime.value = "TRENDING_BULL"
        snapshot.metadata = {"phi_last": 0.0, "dynamic_commission_per_lot": 0.0}
        
        ticket = 123
        pos = {
            'ticket': ticket, 'type': "BUY", 'symbol': 'BTC', 'time': 1000,
            'open_price': 67000.0, 'profit': 1000.0, 'volume': 1.0, 'tp': 72000.0
        }
        self.bridge.get_open_positions.return_value = [pos]
        mock_registry.get_intent.return_value = {"custom_metadata": {"is_swing_trade": True}}
        
        self.pm.monitor_positions(snapshot, {}) # Set peak
        pos['profit'] = 500.0 # Below locked 600
        self.pm.monitor_positions(snapshot, {})
        
        # Check logs via mock_log_obj.omega
        args = [c.args[0] for c in mock_log_obj.omega.call_args_list]
        self.assertTrue(any("T3" in a and "[RELAX]" in a for a in args), f"Log not found in: {args}")

    def test_standard_scalp(self):
        """Verifica scalp padrão sem relaxamento."""
        snapshot = MagicMock()
        snapshot.price = 68000.0
        snapshot.atr = 50.0
        snapshot.regime.value = "TRENDING_BULL"
        snapshot.metadata = {"phi_last": 0.0, "dynamic_commission_per_lot": 0.0}
        
        ticket = 456
        pos = {
            'ticket': ticket, 'type': "BUY", 'symbol': 'BTC', 'time': 2000,
            'open_price': 67000.0, 'profit': 1000.0, 'volume': 1.0, 'tp': 72000.0
        }
        self.bridge.get_open_positions.return_value = [pos]
        mock_registry.get_intent.return_value = {"custom_metadata": {"is_swing_trade": False}}
        
        self.pm.monitor_positions(snapshot, {}) # Set peak
        pos['profit'] = 750.0 # Below locked 800
        self.pm.monitor_positions(snapshot, {})
        
        # Check logs
        args = [c.args[0] for c in mock_log_obj.omega.call_args_list]
        self.assertTrue(any("T3" in a and "[RELAX]" not in a for a in args if "TRAILING_STOP" in a), f"Log not found in: {args}")

if __name__ == "__main__":
    unittest.main()
