
import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import sys
import os

# Adicionar o diretório raiz ao sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.decision.trinity_core import TrinityCore, Action
from execution.risk_quantum import RiskQuantumEngine

class TestSingularityPivot(unittest.TestCase):
    def setUp(self):
        self.core = TrinityCore()
        self.risk = RiskQuantumEngine()
        
    @patch('core.decision.trinity_core.OMEGA')
    def test_creep_maturity_and_ignition_bypass(self, mock_omega):
        # 1. Configurar OMEGA para TrinityCore
        mock_omega.get.side_effect = lambda name, default=None: {
            "creep_maturity_threshold": 150.0,
            "kinetic_velocity_floor": 8.0,
            "buy_threshold": 0.5,
            "sell_threshold": -0.5,
            "confidence_min": 0.5,
            "startup_cooldown_seconds": 0,
            "max_spread_points": 5000,
            "paradigm_shift_threshold": 0.95,
            "kl_velocity_threshold": 1.0, 
            "limit_execution_mode": 0,
            "min_profit_per_ticket": 0.0, 
            "commission_per_lot": 0.0, 
            "stop_loss_atr_mult": 0.5,
            "phi_min_threshold": 0.1,
            "min_atr_distance_mult": 0.0,
            "mc_min_score": -1.0,
            "phi_ignorance_threshold": 0.0,
            "trinity_min_rr_ratio": 0.1
        }.get(name, default)

        # Mock objects
        regime_state = MagicMock()
        regime_state.current = MagicMock()
        regime_state.current.value = "CREEPING_BULL"
        regime_state.v_pulse_detected = False
        
        snapshot = MagicMock()
        snapshot.price = 100.0
        snapshot.symbol_info = {"spread": 10, "point": 0.01}
        snapshot.atr = 1.0
        snapshot.digits_mult = 1.0
        snapshot.indicators = {"M5_atr_14": [1.0]} 
        snapshot.metadata = {"kl_divergence": 0.1, "tick_velocity": 10.0, "v_pulse_detected": False, "v_pulse_capacitor": 0.0}
        snapshot.candles = {"M1": {"close": [100]*10, "open": [100]*10, "high": [100]*10, "low": [100]*10}}
        snapshot.tick = {"ask": 100.05, "bid": 99.95} 
        snapshot.account = {"margin_level": 500.0}
        
        quantum_state = MagicMock()
        quantum_state.superposition = False
        quantum_state.collapsed_signal = 0.8
        quantum_state.raw_signal = 0.8 # [Phase Ω-PhD] Added for robustness
        quantum_state.confidence = 0.9
        quantum_state.phi = 0.5
        quantum_state.entropy = 0.1
        quantum_state.coherence = 0.5
        quantum_state.reasoning = "Test"
        quantum_state.agent_signals = []
        quantum_state.metadata = {"is_god_candidate": False, "bull_agents": ["TrendAgent", "MomentumAgent", "VolumeAgent"]}
        
        asi_state = MagicMock()
        asi_state.circuit_breaker_active = False
        asi_state.consecutive_losses = 0
        asi_state.margin_level = 500.0 
        asi_state.total_trades = 10
        asi_state.total_wins = 6
        asi_state.avg_win = 300
        asi_state.avg_loss = 200

        # --- CASE 1: STALE REGIME (160 bars) NO IGNITION -> VETO ---
        regime_state.duration_bars = 160
        decision_1 = self.core.decide(quantum_state, regime_state, snapshot, asi_state)
        self.assertEqual(decision_1.action, Action.WAIT)
        self.assertIn("CREEP_MATURITY_VETO", decision_1.reasoning)
        print(f"✓ Case 1 passed: Stale regime correctly vetoed.")

        # --- CASE 2: STALE REGIME (200 bars) + LETHAL IGNITION -> BYPASS ---
        regime_state.duration_bars = 200
        snapshot.metadata["v_pulse_detected"] = True
        snapshot.metadata["v_pulse_capacitor"] = 0.95 # Lethal
        
        # Mock Monte Carlo to pass hardcoded vetoes
        mc_mock = MagicMock()
        mc_mock.monte_carlo_score = 0.5
        mc_mock.expected_return = 2.0
        mc_mock.win_probability = 0.6
        mc_mock.conditional_var_95 = 0.1
        mc_mock.optimal_sl_distance = 0
        mc_mock.optimal_tp_distance = 0
        mc_mock.simulation_time_ms = 10.0
        self.core.monte_carlo.simulate_trade = MagicMock(return_value=mc_mock)
        
        decision_2 = self.core.decide(quantum_state, regime_state, snapshot, asi_state)
        if decision_2.action != Action.BUY:
            print(f"FAILED Case 2. Action: {decision_2.action}, Reason: {decision_2.reasoning}")
        
        self.assertEqual(decision_2.action, Action.BUY)
        self.assertTrue(decision_2.metadata.get("bypassed_stale_regime"))
        # Check if reflected in snapshot for risk engine
        self.assertTrue(snapshot.metadata.get("bypassed_stale_regime"))
        print(f"✓ Case 2 passed: Lethal ignition successfully bypassed stale regime.")

    @patch('execution.risk_quantum.OMEGA')
    @patch('execution.risk_quantum.CPP_CORE')
    @patch('execution.risk_quantum.MAX_LOT_SIZE', 100.0) # FIXED
    def test_micro_scaling(self, mock_cpp, mock_omega):
        # Mock OMEGA for RiskQuantum
        mock_omega.get.side_effect = lambda name, default=None: {
            "commission_per_lot": 0.0,
            "min_profit_per_ticket": 0.0,
            "position_size_pct": 10.0,
            "kelly_fraction": 1.0,
            "structural_expectancy_sizing_enabled": 0.0,
            "paradigm_shift_threshold": 0.95,
            "exposure_ceiling_balance_ratio": 1.0 # HUGE CAP to avoid interference
        }.get(name, default)
        
        # Mock non-ergodic growth and ito lot sizing
        mock_cpp.non_ergodic_growth_rate.return_value = 0.01
        mock_cpp.ito_lot_sizing.return_value = 1000.0 
        
        asi_state = MagicMock()
        asi_state.total_trades = 10
        asi_state.total_wins = 6
        asi_state.avg_win = 300
        asi_state.avg_loss = 200
        asi_state.margin_level = 500.0
        
        snapshot = MagicMock()
        snapshot.price = 60000.0
        snapshot.indicators = {"M1_atr_14": [100.0]}
        snapshot.symbol_info = {"point": 0.01, "spread": 20, "trade_contract_size": 1.0}
        snapshot.digits_mult = 1.0
        snapshot.account = {"margin_level": 500.0}
        snapshot.metadata = {"kl_divergence": 0.1, "bypassed_stale_regime": False}
        
        # Base lot size calculation
        lot_normal = self.risk.calculate_lot_size(
            balance=100000.0, stop_loss_distance=200.0,
            win_rate=0.5, avg_win=300.0, avg_loss=200.0,
            snapshot=snapshot, confidence=0.8, asi_state=asi_state
        )
        
        # Bypassed lot size calculation
        snapshot.metadata["bypassed_stale_regime"] = True
        lot_bypassed = self.risk.calculate_lot_size(
            balance=100000.0, stop_loss_distance=200.0,
            win_rate=0.5, avg_win=300.0, avg_loss=200.0,
            snapshot=snapshot, confidence=0.8, asi_state=asi_state
        )
        
        print(f"Lot Normal: {lot_normal}, Lot Bypassed: {lot_bypassed}")
        self.assertAlmostEqual(lot_bypassed, lot_normal * 0.5, places=1)
        print(f"✓ Case 3 passed: Micro-Scaling reduced lot size by 50%.")

if __name__ == "__main__":
    unittest.main()
