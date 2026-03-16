import sys
import os
import unittest
import time
from unittest.mock import MagicMock

# Ajustar path para importar módulos do projeto
sys.path.append(os.getcwd())

from execution.position_manager import PositionManager
from config.omega_params import OMEGA

class TestSmartTPOptimization(unittest.TestCase):
    def setUp(self):
        self.bridge = MagicMock()
        # Mock para evitar erros de salvamento de arquivos durante o teste
        self.bridge.close_position.return_value = {"success": True, "ticket": 123}
        self.bridge.get_pending_orders.return_value = []
        self.pm = PositionManager(self.bridge)
        
    def test_proximity_trailing_trigger(self):
        """Testa se o trailing stop fica mais agressivo na zona de proximidade."""
        # target_profit = (70100 - 70000) * 5.0 = 500.0
        tickets = [{"ticket": 123, "type": "BUY", "volume": 5.0, "price_open": 70000.0, "tp": 70100.0, "profit": 0.0, "time": 1000, "symbol": "BTCUSD"}]
        self.bridge.get_open_positions.return_value = tickets
        
        snapshot = MagicMock()
        snapshot.price = 70095.0
        snapshot.atr = 50.0
        snapshot.metadata = {"phi_last": 0.2, "dynamic_commission_per_lot": 32.0}
        snapshot.regime.value = "TRENDING_BULL"
        
        flow_analysis = {
            "delta": 0.1,
            "signal": 0.1,
            "exhaustion": {"detected": False},
            "absorption": {"detected": False},
            "volume_zscore": 1.0,
            "velocity_score": 0.5
        }
        
        # 1. ATINGIR PICO NA PROXIMITY ZONE (95% do TP)
        tickets[0]["profit"] = 476.0 # Peak
        self.pm.monitor_positions(snapshot, flow_analysis)
        
        # lock_threshold = 0.05 * 1.1 = 0.055
        # peak = 476. trailing_stop = 476 * 0.945 = 449.82
        
        # 2. PULLBACK (Profit cai para 455.0) -> NÃO deve fechar pelo HALF-WAY (que fecha em $5)
        # mas DEVE fechar pelo PROXIMITY_STRIKE se o profit cair abaixo da trava agressiva.
        # Vamos usar um pullback que fique acima do 0x0 para não disparar half-way.
        tickets[0]["profit"] = 440.0 # Pullback abaixo de 449.82
        self.pm.monitor_positions(snapshot, flow_analysis)
        
        time.sleep(0.5)
        
        # Verificamos se close_position foi chamado
        # O self.bridge.close_position deve ter sido chamado com 123
        calls = self.bridge.close_position.call_args_list
        found = any(call.args[0] == 123 for call in calls)
        self.assertTrue(found, "close_position(123) was not called")
        print("✅ Proximity Trailing Strike Verified.")

    def test_kds_trigger(self):
        """Testa o Kinematic Deceleration Sensor."""
        tickets = [{"ticket": 456, "type": "BUY", "volume": 1.0, "price_open": 70000.0, "tp": 70100.0, "profit": 95.0, "time": 1000, "symbol": "BTCUSD"}]
        self.bridge.get_open_positions.return_value = tickets
        self.pm._positions_state = {}
        
        snapshot = MagicMock()
        snapshot.price = 70095.0
        snapshot.atr = 50.0
        snapshot.metadata = {"phi_last": 0.1, "dynamic_commission_per_lot": 32.0}
        snapshot.regime.value = "UNKNOWN"
        
        # Velocity zero na zona de TP (95% do TP = 95.0 profit)
        flow_analysis = {
            "delta": 0.0,
            "signal": 0.0,
            "exhaustion": {"detected": False},
            "absorption": {"detected": False},
            "volume_zscore": 0.5,
            "velocity_score": 0.05 # < 0.2 Trigger KDS
        }
        
        self.pm.monitor_positions(snapshot, flow_analysis)
        
        time.sleep(0.5)
        
        calls = self.bridge.close_position.call_args_list
        found = any(call.args[0] == 456 for call in calls)
        self.assertTrue(found, "close_position(456) was not called")
        print("✅ KDS Velocity Burn Verified.")

if __name__ == "__main__":
    unittest.main()
