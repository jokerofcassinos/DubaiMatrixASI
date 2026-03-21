import unittest
from unittest.mock import MagicMock
import numpy as np
from core.decision.trinity_core import TrinityCore, Action
from core.consciousness.regime_detector import RegimeState, MarketRegime
from core.consciousness.quantum_thought import QuantumState
from config.omega_params import OMEGA

class TestSorosReflexivityEngine(unittest.TestCase):
    def setUp(self):
        self.trinity = TrinityCore()
        self.trinity._creation_time = 0
        self.trinity._startup_timestamp = 0
        mock_mc = MagicMock()
        mock_mc.monte_carlo_score = 0.5
        mock_mc.win_probability = 0.6
        mock_mc.expected_return = 50.0
        mock_mc.conditional_var_95 = -10.0
        mock_mc.optimal_sl_distance = 0
        mock_mc.optimal_tp_distance = 0
        mock_mc.simulation_time_ms = 1.0
        self.trinity.monte_carlo.simulate_trade = MagicMock(return_value=mock_mc)
        
    def test_soros_squeeze_bull_inversion(self):
        """
        Verifica se a SRE inverte o sinal de Venda (-0.5) para Compra
        quando a velocidade (tick_vel) for abissalmente positiva (> 45.0).
        """
        # Mock QuantumState (Bearish consensus)
        q_state = MagicMock(spec=QuantumState)
        q_state.collapsed_signal = -0.50
        q_state.raw_signal = -0.50
        q_state.reasoning = "Mock"
        q_state.confidence = 0.85
        q_state.coherence = 0.60
        q_state.phi = 0.15 # Low coherence
        q_state.entropy = 0.0
        q_state.superposition = False
        q_state.metadata = {"is_god_candidate": False, "phi": 0.15}
        q_state.agent_signals = []
        
        # Mock RegimeState
        regime = RegimeState(
            current=MarketRegime.UNKNOWN, # Choppy regime
            confidence=0.8,
            transition_prob=0.1,
            predicted_next=MarketRegime.UNKNOWN,
            aggression_multiplier=1.0,
            reasoning="Mock",
            duration_bars=5,
            v_pulse_detected=False
        )
        
        # Mock Snapshot with KINETIC CONFLICT (Tick Vel +55.0 vs Signal -0.5)
        snap = MagicMock()
        snap.price = 70000.0
        snap.timestamp = MagicMock() # Will fail datetime math if not handled, so give it a valid datetime
        from datetime import datetime, timezone
        snap.timestamp = datetime.now(timezone.utc)
        snap.metadata = {
            "tick_velocity": 55.0, # Massive Bullish Squeeze
            "atr": 100.0,
            "fast_atr": 100.0,
            "v_pulse_capacitor": 0.0,
            "kl_divergence": 0.0,
            "commission_per_lot": 0.0
        }
        snap.candles = {
            "M1": {"close": [70000]*10, "open": [70000]*10, "high": [70000]*10, "low": [70000]*10}
        }
        snap.atr = 100.0
        snap.indicators = {"M5_atr_14": [100.0]}
        snap.symbol_info = {"point": 0.00001, "spread": 10, "trade_contract_size": 1.0}
        snap.tick = {"ask": 70000.0, "bid": 69999.0, "last": 70000.0}
        asi_state = MagicMock()
        asi_state.circuit_breaker_active = False
        asi_state.consecutive_losses = 0
        
        # Run decision
        # A SRE deve capturar tick_vel=55.0 > 45.0 + signal=-0.5 < -0.3
        decision = self.trinity.decide(q_state, regime, snap, asi_state)
        
        self.assertIsNotNone(decision)
        print(f"\\n[DEBUG] SRE Reasoning: {decision.reasoning}\\n")
        self.assertEqual(decision.action, Action.BUY)   # Inverted from SELL to BUY
        self.assertEqual(decision.confidence, 0.99)     # Forced to 0.99
        
    def test_entropic_vacuum_harvester(self):
        """
        Verifica se o modo EVH ativa para micro-scalp sem veto de incoerência em regime UNKNOWN
        onde phi < 0.04 e signal bruto é alto.
        """
        q_state = MagicMock(spec=QuantumState)
        q_state.collapsed_signal = 0.55 # Forte anomalia
        q_state.raw_signal = 0.55
        q_state.reasoning = "Mock"
        q_state.confidence = 0.85
        q_state.coherence = 0.30
        q_state.phi = 0.01  # Abaixo do unknown gate de 0.04
        q_state.entropy = 0.0
        q_state.superposition = False
        q_state.metadata = {"is_god_candidate": False, "phi": 0.01}
        q_state.agent_signals = []
        
        regime = RegimeState(
            current=MarketRegime.LOW_LIQUIDITY,
            confidence=0.8,
            transition_prob=0.1,
            predicted_next=MarketRegime.LOW_LIQUIDITY,
            aggression_multiplier=1.0,
            reasoning="Mock",
            duration_bars=10,
            v_pulse_detected=False
        )
        
        snap = MagicMock()
        snap.price = 70000.0
        from datetime import datetime, timezone
        snap.timestamp = datetime.now(timezone.utc)
        snap.metadata = {
            "tick_velocity": 10.0,
            "atr": 50.0,
            "fast_atr": 50.0,
            "kl_divergence": 0.0,
            "commission_per_lot": 0.0
        }
        snap.candles = {
            "M1": {"close": [70000]*10, "open": [70000]*10, "high": [70000]*10, "low": [70000]*10}
        }
        snap.atr = 50.0
        snap.indicators = {"M5_atr_14": [50.0]}
        snap.symbol_info = {"point": 0.00001, "spread": 10, "trade_contract_size": 1.0}
        snap.tick = {"ask": 70000.0, "bid": 69999.0, "last": 70000.0}
        asi_state = MagicMock()
        asi_state.circuit_breaker_active = False
        asi_state.consecutive_losses = 0
        
        decision = self.trinity.decide(q_state, regime, snap, asi_state)
        
        self.assertIsNotNone(decision)
        print(f"\\n[DEBUG] EVH Reasoning: {decision.reasoning}\\n")
        self.assertEqual(decision.action, Action.BUY)
        print("EVH Passed")


if __name__ == '__main__':
    unittest.main()
