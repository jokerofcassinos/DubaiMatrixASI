import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import time
import numpy as np

# Add project root to path
sys.path.append(os.getcwd())

from core.decision.trinity_core import TrinityCore, Action
from core.consciousness.regime_detector import MarketRegime
from config.omega_params import OMEGA
from execution.risk_quantum import RiskQuantumEngine

class TestPhDAlpha(unittest.TestCase):
    def setUp(self):
        self.trinity = TrinityCore()
        self.risk = RiskQuantumEngine()
        # Mock para evitar Veto de Startup nos testes
        self.trinity._creation_time = time.time() - 1000
        OMEGA.load()
        OMEGA.set("buy_threshold", 0.20)
        OMEGA.set("sell_threshold", -0.20)
        print(f"DEBUG: OMEGA buy_threshold = {OMEGA.get('buy_threshold')}")

    def test_entropy_bridge_buy(self):
        """Verifica se o Ω-Entropy Bridge autoriza sinal estável abaixo do threshold."""
        # Threshold base: 0.18 (novo calibrado)
        # Sinal: 0.17 (abaixo de 0.18, mas acima de 0.9 * 0.18 = 0.162)
        
        snapshot = MagicMock()
        snapshot.metadata = {"kl_divergence": 0.0, "tick_velocity": 2.0, "pnl_prediction": "IMPOSSIBLE:NEGATIVE_EXPECTANCY"}
        snapshot.tick = {"ask": 70000.0, "bid": 69990.0, "last": 70000.0}
        snapshot.price = 70000.0
        snapshot.symbol_info = {"spread": 10, "point": 0.01, "trade_contract_size": 1}
        snapshot.atr = 50.0
        snapshot.indicators = {"M5_atr_14": [50.0], "M1_atr_14": [50.0], "M1_entropy": [0.5]}
        snapshot.candles = {
            "M1": {
                "low": np.array([69990.0]*10),
                "high": np.array([70010.0]*10),
                "close": np.array([70000.0]*10),
                "open": np.array([69995.0]*10)
            }
        }
        
        quantum_state = MagicMock()
        quantum_state.phi = 0.05 # LATE IGNITION (Previously would fail Φ-Gate 0.15)
        quantum_state.coherence = 0.5
        quantum_state.collapsed_signal = 0.19 # Sinal estável (95% do threshold 0.20)
        quantum_state.confidence = 0.85
        quantum_state.entropy = 0.3
        quantum_state.superposition = False
        quantum_state.metadata = {"bull_agents": ["A1","A2","A3"], "bear_agents": []}
        
        regime_state = MagicMock()
        regime_state.current = MarketRegime.CREEPING_BULL
        regime_state.v_pulse_detected = False
        
        asi_state = MagicMock()
        asi_state.circuit_breaker_active = False
        asi_state.consecutive_losses = 0
        
        # Simular 20 ciclos de sinal 0.19 (Variância 0)
        # Note: trinity_core updates _signal_history internally if implementation is correct
        for _ in range(19):
            self.trinity.decide(quantum_state, regime_state, snapshot, asi_state)
            
        # O 20º ciclo deve disparar mesmo com Φ baixo e PnL negativo
        decision = self.trinity.decide(quantum_state, regime_state, snapshot, asi_state)
        
        if decision.action != Action.BUY:
            print(f"DEBUG: Action was {decision.action}, Reasoning: {decision.reasoning}")
            
        self.assertEqual(decision.action, Action.BUY)
        self.assertTrue(self.trinity.entropy_bridge_active)

    def test_soft_kl_scaling(self):
        """Verifica se o lote reduz via decaimento gaussiano com KL alto."""
        balance = 100000.0
        stop_loss_distance = 1000.0
        win_rate = 0.5
        avg_win = 1500.0
        avg_loss = 1000.0
        
        snapshot = MagicMock()
        snapshot.price = 70000.0
        snapshot.indicators = {"M1_atr_14": [100.0]}
        # symbol_info: point_value calc: balance * risk / (sl * point_value)
        snapshot.symbol_info = {"trade_contract_size": 1, "point": 1.0}
        snapshot.account = {"margin_level": 500.0}
        snapshot.digits_mult = 1.0
        
        # Caso 1: KL baixo (0.1) -> Lote normal
        snapshot.metadata = {"kl_divergence": 0.1}
        # Balance e SL que resultem em lote médio (~0.5) para evitar MIN/MAX
        balance = 50000.0 
        stop_loss_distance = 1000.0
        lot_normal = self.risk.calculate_lot_size(balance, stop_loss_distance, win_rate, avg_win, avg_loss, snapshot=snapshot)
        
        # Caso 2: KL médio (1.5 > base 0.95) -> Lote reduzido
        snapshot.metadata = {"kl_divergence": 1.5}
        lot_reduced = self.risk.calculate_lot_size(balance, stop_loss_distance, win_rate, avg_win, avg_loss, snapshot=snapshot)
        
        # Gaussian decay: exp(-(1.5/0.95)**2) = exp(-2.49) = 0.082
        print(f"DEBUG: Lot Normal {lot_normal}, Lot Reduced {lot_reduced}")
        self.assertLess(lot_reduced, lot_normal * 0.5) # Scaling confirmed (reduced from 0.5 to ~0.04)

if __name__ == "__main__":
    unittest.main()
