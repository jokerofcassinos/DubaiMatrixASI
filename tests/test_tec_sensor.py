import unittest
from unittest.mock import MagicMock, patch
import numpy as np

# Importações Reais
from core.decision.trinity_core import TrinityCore, Action
from core.consciousness.regime_detector import MarketRegime
from execution.risk_quantum import RiskQuantumEngine

class SimpleSnapshot:
    def __init__(self, price=100000.0, meta=None):
        self.price = price
        self.tick = {"ask": price + 5, "bid": price - 5}
        self.indicators = {"M1_atr_14": [100.0], "M1_entropy": [0.8], "M1_shannon": [0.9]*20}
        self.digits_mult = 1.0
        self.symbol_info = {"point": 0.01, "spread": 10, "trade_contract_size": 1}
        self.metadata = meta or {}
        self.candles = {
            "M1": {
                "close": [price]*10, 
                "open": [price]*10, 
                "high": [price+10]*10, 
                "low": [price-10]*10
            }
        }
        self.account = {"margin_level": 2000.0}

class SimpleQuantumState:
    def __init__(self, phi=0.1, signal=0.6, confidence=0.75):
        self.phi = phi
        self.raw_signal = signal
        self.collapsed_signal = signal
        self.confidence = confidence
        self.coherence = 0.5
        self.entropy = 0.5
        self.superposition = False
        self.metadata = {"is_god_candidate": False, "bull_agents": ["A"]*15, "bear_agents": ["B"]*5}
        self.agent_signals = []
        self.reasoning = "PhD-6 Test"

class SimpleASIState:
    def __init__(self):
        self.total_trades = 10
        self.total_wins = 6
        self.avg_win = 300.0
        self.avg_loss = 200.0
        self.daily_profit = 0.0
        self.daily_loss = 0.0
        self.max_drawdown = 0.0
        self.account = MagicMock(margin_level=2000.0)

class TestTECSensorFinal(unittest.TestCase):
    def setUp(self):
        self.core = TrinityCore()
        self.risk = RiskQuantumEngine()

    @patch('core.decision.trinity_core.OMEGA')
    def test_tec_resonance_bypass_final(self, mock_omega):
        # 1. Configurar OMEGA
        mock_omega.get.side_effect = lambda name, default=None: {
            "tec_sensitivity": 0.30,
            "tec_min_v_pulse": 0.20,
            "phi_min_threshold": 0.40,
            "buy_threshold": 0.50,
            "sell_threshold": -0.50,
            "phi_ignorance_threshold": 0.15,
            "stop_loss_atr_mult": 0.55,
            "phi_symmetry_guard_enabled": 0.0,
            "paradigm_shift_threshold": 0.95,
            "kl_velocity_threshold": 0.15,
            "tp_placement_scalar": 0.97
        }.get(name, default)

        # 2. Snapshot com TEC (Colapso de Entropia)
        shannon_history = [1.0] * 20
        meta = {
            "shannon_entropy": 0.1,
            "shannon_history": shannon_history,
            "v_pulse_capacitor": 1.0,
            "tick_velocity": 20.0,
            "pnl_prediction": "STABLE",
            "kl_divergence": 0.1
        }
        snapshot = SimpleSnapshot(meta=meta)

        # 3. Quantum State (Baixo Phi para forçar bypass)
        q_state = SimpleQuantumState(phi=0.05, signal=0.8, confidence=0.85)

        regime_state = MagicMock()
        regime_state.current = MarketRegime.TRENDING_BULL
        regime_state.v_pulse_detected = False

        # 4. Decisão
        decision = self.core.decide(q_state, regime_state, snapshot, None)

        # 5. Assertions
        self.assertIsNotNone(decision, "Decision should not be None (AttributeError/KeyError fixed)")
        self.assertEqual(decision.action, Action.BUY)
        self.assertTrue(decision.metadata.get("is_tec_active"))
        print(f"✓ Case 1 (Bypass) Success: Action={decision.action.name}")

    @patch('execution.risk_quantum.OMEGA')
    @patch('execution.risk_quantum.MAX_LOT_SIZE', 100.0)
    @patch('execution.risk_quantum.CPP_CORE')
    def test_tec_micro_scaling_final(self, mock_cpp, mock_omega):
        # Mock OMEGA
        mock_omega.get.side_effect = lambda name, default=None: {
            "exposure_ceiling_balance_ratio": 20000.0,
            "limit_execution_mode": 0,
            "risk_growth_cap": 0.05,
            "commission_per_lot": 50.0,
            "min_profit_per_ticket": 80.0
        }.get(name, default)
        
        mock_cpp.non_ergodic_growth_rate.return_value = 0.01
        mock_cpp.ito_lot_sizing.return_value = 1.0

        # 1. Lot Normal
        snapshot_normal = SimpleSnapshot()
        asi_state = SimpleASIState()
        
        lot_normal = self.risk.calculate_lot_size(
            balance=100000.0, stop_loss_distance=200.0,
            win_rate=0.6, avg_win=300.0, avg_loss=200.0,
            snapshot=snapshot_normal, confidence=0.8, asi_state=asi_state
        )

        # 2. Lot TEC (Bypass + TEC Active)
        meta_tec = {"bypassed_stale_regime": True, "is_tec_active": True}
        snapshot_tec = SimpleSnapshot(meta=meta_tec)
        
        lot_tec = self.risk.calculate_lot_size(
            balance=100000.0, stop_loss_distance=200.0,
            win_rate=0.6, avg_win=300.0, avg_loss=200.0,
            snapshot=snapshot_tec, confidence=0.8, asi_state=asi_state
        )

        print(f"Lot Normal: {lot_normal:.4f}, Lot TEC: {lot_tec:.4f}")
        
        # TEC deve ser ~75% do Normal
        self.assertAlmostEqual(lot_tec, lot_normal * 0.75, delta=0.04)
        print("✓ Case 2 (Micro-Scaling) Success: TEC lot is ~75% of normal.")

if __name__ == "__main__":
    unittest.main()
