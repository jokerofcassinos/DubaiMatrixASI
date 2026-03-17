import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import numpy as np

# Add project root to path
sys.path.append(os.getcwd())

from core.decision.trinity_core import TrinityCore, Action
from core.consciousness.regime_detector import MarketRegime
from config.omega_params import OMEGA

class TestKineticPhD(unittest.TestCase):
    def setUp(self):
        self.trinity = TrinityCore()
        # Mock para evitar Veto de Startup nos testes
        import time
        self.trinity._creation_time = time.time() - 1000
        OMEGA.load()

    def test_kinetic_exhaustion_veto(self):
        """Verifica se VETA sinal estável mas com velocidade cinetica morrendo."""
        snapshot = MagicMock()
        # Estabilidade perfeita (Var=0), mas velocidade baixíssima (5.0)
        snapshot.metadata = {"tick_velocity": 5.0, "pnl_prediction": "POSITIVE"}
        snapshot.price = 70000.0
        snapshot.atr = 50.0
        snapshot.indicators = {"M1_atr_14": [50.0], "M5_atr_14": [50.0], "M1_entropy": [0.3]}
        snapshot.candles = {"M1": {"low": [69990]*10, "high": [70010]*10, "close": [70000]*10, "open": [69995]*10}}
        snapshot.symbol_info = {"spread": 10, "point": 0.01, "trade_contract_size": 1}
        
        quantum_state = MagicMock()
        quantum_state.collapsed_signal = 0.19 
        quantum_state.phi = 0.05
        quantum_state.superposition = False
        quantum_state.entropy = 0.3
        quantum_state.confidence = 0.5
        quantum_state.coherence = 0.5 # Evitar TypeError
        quantum_state.agent_signals = []
        
        regime_state = MagicMock()
        regime_state.current = MarketRegime.CREEPING_BULL
        regime_state.duration_bars = 10
        regime_state.v_pulse_detected = False # Evitar TypeError
        
        # Injetar ASIState real para evitar erros de comparação de MagicMock
        from config.settings import ASIState
        asi_state = ASIState()
        asi_state.consecutive_losses = 0
        asi_state.circuit_breaker_active = False
        
        # Simular acúmulo de histórico para Entropy Bridge
        for _ in range(20):
            self.trinity.decide(quantum_state, regime_state, snapshot, asi_state)
            
        decision = self.trinity.decide(quantum_state, regime_state, snapshot, asi_state)
        self.assertEqual(decision.action, Action.WAIT)
        self.assertIn("KINETIC_EXHAUSTION", decision.reasoning)

    def test_creep_maturity_veto(self):
        """Verifica se VETA regime que durou demais sem ignição."""
        snapshot = MagicMock()
        snapshot.metadata = {"tick_velocity": 50.0} # Velocidade OK
        snapshot.price = 70000.0
        snapshot.atr = 50.0
        snapshot.indicators = {"M1_atr_14": [50.0], "M5_atr_14": [50.0], "M1_entropy": [0.3]}
        snapshot.candles = {"M1": {"low": [69990]*10, "high": [70010]*10, "close": [70000]*10, "open": [69995]*10}}
        snapshot.symbol_info = {"spread": 10, "point": 0.01, "trade_contract_size": 1}
        
        quantum_state = MagicMock()
        quantum_state.collapsed_signal = 0.30 
        quantum_state.phi = 0.10 
        quantum_state.superposition = False
        quantum_state.entropy = 0.3
        quantum_state.confidence = 0.5
        quantum_state.coherence = 0.5
        quantum_state.agent_signals = []
        
        regime_state = MagicMock()
        regime_state.current = MarketRegime.CREEPING_BULL
        regime_state.duration_bars = 150 # MUITO VELHO
        regime_state.v_pulse_detected = False
        
        # Injetar ASIState real
        from config.settings import ASIState
        asi_state = ASIState()
        asi_state.consecutive_losses = 0
        asi_state.circuit_breaker_active = False
        
        decision = self.trinity.decide(quantum_state, regime_state, snapshot, asi_state)
        self.assertEqual(decision.action, Action.WAIT)
        self.assertIn("CREEP_MATURITY", decision.reasoning)

    @patch('core.decision.trinity_core.QuantumMonteCarloEngine.simulate_trade')
    def test_mc_score_floor(self, mock_mc):
        """Verifica veto por MC-Score baixo mesmo com EV positivo."""
        mock_mc.return_value = MagicMock(
            monte_carlo_score=-0.35, # Abaixo do floor -0.25
            expected_return=5.5,    # EV Positivo (enganoso)
            win_probability=0.40,
            conditional_var_95=-80.0,
            optimal_sl_distance=50.0,
            optimal_tp_distance=150.0,
            optimal_rr_ratio=5.0
        )
        
        snapshot = MagicMock()
        snapshot.metadata = {"tick_velocity": 50.0, "agent_signals": [], "v_pulse_detected": False, "god_mode_active": False, "phi_resonance": False, "kl_divergence": 0.0}
        snapshot.price = 70000.0 
        snapshot.atr = 50.0
        snapshot.point_val = 0.01
        snapshot.fast_atr = 50.0
        snapshot.symbol_info = {"point": 0.01, "spread": 10, "trade_contract_size": 1}
        
        snapshot.m1_lows = np.array([69990.0]*10, dtype=float)
        snapshot.m1_highs = np.array([70010.0]*10, dtype=float)
        snapshot.indicators = {"M1_atr_14": [50.0], "M5_atr_14": [50.0], "M1_entropy": [0.3]}
        snapshot.candles = {"M1": {"low": snapshot.m1_lows, "high": snapshot.m1_highs, "close": np.array([70000.0]*10, dtype=float), "open": np.array([69995.0]*10, dtype=float)}}
        
        quantum_state = MagicMock()
        quantum_state.collapsed_signal = 0.35 
        quantum_state.phi = 0.50 
        quantum_state.superposition = False
        quantum_state.entropy = 0.3
        quantum_state.confidence = 1.0 
        quantum_state.coherence = 0.5 
        quantum_state.agent_signals = []
        
        regime_state = MagicMock()
        regime_state.current = MarketRegime.TRENDING_BULL
        regime_state.duration_bars = 5
        regime_state.v_pulse_detected = False
        
        # Injetar ASIState real para evitar erros de comparação de MagicMock
        from config.settings import ASIState
        asi_state = ASIState()
        asi_state.consecutive_losses = 0
        asi_state.circuit_breaker_active = False
        
        decision = self.trinity.decide(quantum_state, regime_state, snapshot, asi_state)
        self.assertEqual(decision.action, Action.WAIT)
        self.assertIn("MC_SCORE_FLOOR", decision.reasoning)

if __name__ == "__main__":
    unittest.main()
