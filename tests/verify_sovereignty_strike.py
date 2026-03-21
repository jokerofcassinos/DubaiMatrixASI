import unittest
from unittest.mock import MagicMock
import time
import numpy as np
from core.decision.trinity_core import TrinityCore, Action
from core.consciousness.quantum_thought import QuantumState
from core.consciousness.regime_detector import RegimeState, MarketRegime
from config.omega_params import OMEGA

class TestSovereigntyStrike(unittest.TestCase):
    def setUp(self):
        self.trinity = TrinityCore()
        # Bypassar bootstrap
        self.trinity._creation_time = time.time() - 3600
        self.trinity._startup_timestamp = time.time() - 3600

    def test_sre_horizontal_bypass(self):
        """Testa se o SRE ignora um suporte horizontal forte em queda livre."""
        q_state = MagicMock(spec=QuantumState)
        q_state.phi = 0.15
        q_state.collapsed_signal = 0.85
        q_state.raw_signal = 0.85
        q_state.confidence = 0.99
        q_state.coherence = 0.60
        q_state.superposition = False
        q_state.entropy = 0.5
        q_state.metadata = {"entropy": 0.4, "bull_agents": ["A","B"], "bear_agents": []}
        q_state.agent_signals = []
        q_state.reasoning = "Mock"
        
        regime = MagicMock(spec=RegimeState)
        regime.current = MarketRegime.DRIFTING_BEAR
        regime.v_pulse_detected = False
        regime.v_pulse_intensity = 0.0
        
        snapshot = MagicMock()
        snapshot.price = 50000.0
        snapshot.tick = {"ask": 50000.0, "bid": 50000.0, "last": 50000.0}
        snapshot.atr = 100.0
        from datetime import datetime, timezone
        snapshot.timestamp = datetime.now(timezone.utc)
        snapshot.metadata = {"tick_velocity": -55.0, "v_pulse_detected": False}
        snapshot.symbol_info = {"spread": 10, "point": 1.0}
        
        data = [50000.0]*100
        snapshot.candles = {
            "M1": {"low": data, "close": data, "high": [50010.0]*100, "open": data}, 
            "M5": {"low": data, "close": [50000.0]*100, "high": [50010.0]*100, "open": data}
        }
        snapshot.indicators = {
            "M5_atr_14": [100.0]*100,
            "M1_atr_14": [20.0]*100,
            "M5_hurst": 0.5,
            "M5_entropy": 3.0
        }
        
        asi_state = MagicMock()
        asi_state.circuit_breaker_active = False
        asi_state.consecutive_losses = 0
        
        decision = self.trinity.decide(q_state, regime, snapshot, asi_state)
        
        self.assertIsNotNone(decision)
        if decision:
            print(f"\n[DEBUG SRE] Decision: {decision.action.name} | Reason: {decision.reasoning}")
            self.assertEqual(decision.action, Action.SELL)
            self.assertIn("SOROS_REFLEXIVITY", decision.reasoning)


    def test_evh_phi_relaxation(self):
        """Testa se o EVH opera em Φ baixíssimo no regime UNKNOWN."""
        q_state = MagicMock(spec=QuantumState)
        q_state.phi = 0.012
        q_state.collapsed_signal = -0.55
        q_state.raw_signal = -0.55
        q_state.confidence = 0.85
        q_state.coherence = 0.35
        q_state.superposition = False
        q_state.entropy = 0.5
        q_state.metadata = {"entropy": 0.1, "bear_agents": ["A"], "bull_agents": []}
        q_state.agent_signals = []
        q_state.reasoning = "Mock"
        
        regime = MagicMock(spec=RegimeState)
        regime.current = MarketRegime.UNKNOWN
        regime.v_pulse_detected = False
        
        snapshot = MagicMock()
        snapshot.price = 50000.0
        snapshot.tick = {"ask": 50000.0, "bid": 50000.0, "last": 50000.0}
        snapshot.atr = 100.0
        from datetime import datetime, timezone
        snapshot.timestamp = datetime.now(timezone.utc)
        snapshot.metadata = {"tick_velocity": -6.0}
        snapshot.symbol_info = {"spread": 10, "point": 1.0}
        
        data = [50000.0]*100
        snapshot.candles = {
            "M1": {"low": data, "close": data, "high": data, "open": data}, 
            "M5": {"low": data, "close": data, "high": data, "open": data}
        }
        snapshot.indicators = {
            "M5_atr_14": [100.0]*100,
            "M1_atr_14": [20.0]*100
        }
        
        asi_state = MagicMock()
        asi_state.circuit_breaker_active = False
        asi_state.consecutive_losses = 0
        
        decision = self.trinity.decide(q_state, regime, snapshot, asi_state)
        
        self.assertIsNotNone(decision)
        if decision:
            print(f"\n[DEBUG EVH] Decision: {decision.action.name} | Reason: {decision.reasoning}")
            self.assertEqual(decision.action, Action.SELL)


if __name__ == "__main__":
    unittest.main()
