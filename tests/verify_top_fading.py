
import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import time
import sys
import os
from datetime import datetime, timezone

# Set encoding for stdout to handle Φ
import io
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')

# Add project root to path
sys.path.append(os.getcwd())

from core.decision.trinity_core import TrinityCore, Action
from core.consciousness.quantum_thought import QuantumState, AgentSignal
from core.consciousness.regime_detector import RegimeState, MarketRegime
from config.omega_params import OMEGA

class TestTopFading(unittest.TestCase):
    def setUp(self):
        self.trinity = TrinityCore()
        # Mock para evitar Veto de Startup nos testes
        self.trinity._startup_timestamp = time.time() - 3600
        self.trinity._creation_time = time.time() - 3600

    def test_exhaustion_sovereignty_bypass(self):
        """Verifica se o portão counter-trend relaxa com Soberania de Exaustão."""
        price = 72000.0
        fast_atr = 100.0
        
        snapshot = MagicMock()
        snapshot.price = price
        snapshot.atr = fast_atr
        snapshot.timestamp = datetime.now(timezone.utc)
        snapshot.tick = {"ask": price, "bid": price - 1}
        snapshot.symbol_info = {"point": 1.0, "spread": 10, "trade_contract_size": 1}
        snapshot.candles = {
            "M1": {
                "low": [71900]*10, "high": [72100]*10, 
                "close": [72050]*10, "open": [72000]*10
            }
        }
        
        snapshot.indicators = {
            "M1_atr_14": [fast_atr],
            "M5_atr_14": [fast_atr],
            "M1_entropy": [0.85] 
        }
        # Injeção via dicionário para evitar MagicMock.get default
        snapshot.metadata = {
            "v_pulse_detected": False, 
            "pnl_prediction": "NEUTRAL", 
            "tick_velocity": 0.0, 
            "v_pulse_capacitor": 0.0,
            "coherence": 0.90,
            "phi": 0.28,
            "entropy": 0.10
        }

        regime_state = MagicMock()
        regime_state.current = MarketRegime.CREEPING_BULL
        regime_state.v_pulse_detected = False

        quantum_state = MagicMock()
        quantum_state.phi = 0.28 
        quantum_state.confidence = 0.90
        quantum_state.collapsed_signal = -0.45 
        quantum_state.superposition = False
        quantum_state.coherence = 0.90
        quantum_state.entropy = 0.10
        quantum_state.signal_strength = 0.45
        
        quantum_state.metadata = {
            "bear_agents": ["TrendAgent", "VolumeAgent", "QuantumAgent"],
            "bull_agents": [],
            "entropy": 0.10,
            "is_god_candidate": False
        }
        
        exhaustion_signal = AgentSignal("PrigogineDissipative", -1.0, 0.92, "BIFURCATION_DETECTED", 5.0)
        quantum_state.agent_signals = [exhaustion_signal]

        asi_state = MagicMock()
        asi_state.circuit_breaker_active = False
        
        mc_result = MagicMock()
        mc_result.monte_carlo_score = 0.6
        mc_result.win_probability = 0.65
        mc_result.expected_return = 150.0
        mc_result.conditional_var_95 = -5.0
        mc_result.optimal_sl_distance = 150.0
        mc_result.optimal_tp_distance = 300.0
        mc_result.optimal_rr_ratio = 2.0

        with patch.object(self.trinity, '_check_vetos', return_value=None), \
             patch.object(self.trinity.monte_carlo, 'simulate_trade', return_value=mc_result):
            
            decision = self.trinity.decide(quantum_state, regime_state, snapshot, asi_state)
            self.assertEqual(decision.action, Action.SELL)

    def test_veto_without_exhaustion(self):
        """Verifica se o veto continua ativo se não houver exaustão clara."""
        price = 72000.0
        fast_atr = 100.0
        snapshot = MagicMock()
        snapshot.price = price
        snapshot.atr = fast_atr
        snapshot.timestamp = datetime.now(timezone.utc)
        snapshot.tick = {"ask": price, "bid": price - 1}
        snapshot.symbol_info = {"point": 1.0, "spread": 10}
        snapshot.candles = {"M1": {"open": [72000]*10, "close": [72050]*10, "high": [72100]*10, "low": [71900]*10}}
        snapshot.indicators = {
            "M1_atr_14": [fast_atr],
            "M5_atr_14": [fast_atr],
            "M1_entropy": [0.40] 
        }
        snapshot.metadata = {
            "v_pulse_detected": False, 
            "pnl_prediction": "NEUTRAL", 
            "tick_velocity": 0.0, 
            "v_pulse_capacitor": 0.0,
            "coherence": 0.28,
            "phi": 0.28
        }
        
        regime_state = MagicMock()
        regime_state.current = MarketRegime.CREEPING_BULL
        regime_state.v_pulse_detected = False
        
        quantum_state = MagicMock()
        quantum_state.phi = 0.28
        quantum_state.confidence = 0.90
        quantum_state.collapsed_signal = -0.45
        quantum_state.superposition = False
        quantum_state.entropy = 0.05
        quantum_state.coherence = 0.28
        quantum_state.agent_signals = [] 
        quantum_state.metadata = {
            "bear_agents": ["TrendAgent", "VolumeAgent", "QuantumAgent"],
            "bull_agents": [],
            "entropy": 0.05,
            "is_god_candidate": False
        }

        with patch.object(self.trinity, '_check_vetos', return_value=None):
            decision = self.trinity.decide(quantum_state, regime_state, snapshot, MagicMock())
            self.assertEqual(decision.action, Action.WAIT)
            self.assertIn("TREND_PROTECTION_VETO", decision.reasoning)

if __name__ == "__main__":
    unittest.main()
