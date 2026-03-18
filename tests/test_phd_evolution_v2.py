import unittest
from unittest.mock import MagicMock, patch
import numpy as np
from core.decision.trinity_core import TrinityCore, Action, Decision
from core.consciousness.quantum_thought import QuantumState, QuantumThoughtEngine
from core.consciousness.regime_detector import RegimeState, MarketRegime
from core.consciousness.neural_swarm import AgentSignal
from execution.quantum_tunneling_execution import QuantumTunnelingExecution

class TestPhDEvolutionV2(unittest.TestCase):
    def setUp(self):
        self.core = TrinityCore()
        self.engine = QuantumThoughtEngine()
        
    @patch('core.consciousness.monte_carlo_engine.QuantumMonteCarloEngine.simulate_trade')
    def test_phd7_riemannian_ricci_bypass(self, mock_mc):
        """Ω-PhD-7: Verifica se o Ricci Attractor bypassa o Φ-Gate."""
        # Configurar Mock do Monte Carlo
        mock_result = MagicMock()
        mock_result.monte_carlo_score = 0.5
        mock_result.win_probability = 0.6
        mock_result.expected_return = 2.0
        mock_result.conditional_var_95 = 0.1
        mock_result.optimal_sl_distance = 0
        mock_result.optimal_tp_distance = 0
        mock_result.simulation_time_ms = 10.0
        mock_mc.return_value = mock_result
        
        # Agente Ricci detecta atrator (alta curvatura)
        signals = [
            AgentSignal("RiemannianRicci", 0.9, 0.95, "RICCI_ATTRACTOR_DETECTED", 5.0),
            AgentSignal("TrendAgent", 0.8, 0.8, "Bull Trend", 1.0),
            AgentSignal("VolumeAgent", 0.8, 0.8, "High Volume", 1.0) # Diverse domains
        ]
        
        # Snapshot com baixa consciência (Φ < threshold)
        snapshot = MagicMock()
        snapshot.indicators = {
            "M5_atr_14": [500.0], # BTC-like ATR
            "M1_atr_14": [200.0],
            "M5_bb_width": [1000.0],
            "M5_volume_ratio": [1.5],
            "M1_high": [60100.0] * 50,
            "M1_low": [59900.0] * 50,
            "M5_high": [60100.0] * 50,
            "M5_low": [59900.0] * 50
        }
        snapshot.metadata = {
            "entropy": 0.82,
            "kl_divergence": 0.1,
            "v_pulse_capacitor": 0.1,
            "tick_buffer": [{"last": 60000 + i*10} for i in range(20)],
            "tick_velocity": 5.0,
            "momentum_delta": 0.2,
            "spread": 50,
            "avg_tick_volume": 100,
            "total_tick_volume": 1000,
            "sell_volume": 1000
        }
        snapshot.price = 60100.0
        snapshot.candles = {
            "M1": {"high": [60200]*100, "low": [59800]*100, "close": [60000]*100, "open": [60000]*100},
            "M5": {"high": [60200]*100, "low": [59800]*100, "close": [60000]*100, "open": [60000]*100}
        }
        snapshot.tick = {"ask": 60100.0, "bid": 60095.0}
        snapshot.symbol_info = {"point": 1.0, "spread": 50, "trade_tick_size": 1.0}
        
        regime = MagicMock()
        regime.current = MarketRegime.CREEPING_BULL
        regime.duration_bars = 10
        regime.v_pulse_detected = False
        
        # Processar no motor quântico
        q_state = self.engine.process(signals, snapshot=snapshot)
        
        # Forçar Φ baixo no estado injetado (Φ=0.05 < 0.40)
        q_state.phi = 0.05 
        
        # Decidir na TrinityCore
        decision = self.core.decide(q_state, regime, snapshot, None)
        
        print(f"Decision: {decision.action.name if decision else 'NONE'} | Reason: {decision.reasoning if decision else 'N/A'}")
        
        # Deve autorizar COMPRA mesmo com Φ baixo, devido ao Ricci Attractor
        self.assertIsNotNone(decision)
        self.assertEqual(decision.action, Action.BUY)
        self.assertTrue(q_state.metadata.get("ricci_attractor", False))
        
    @patch('core.consciousness.monte_carlo_engine.QuantumMonteCarloEngine.simulate_trade')
    def test_phd8_kolmogorov_sync(self, mock_mc):
        """Ω-PhD-8: Verifica se o Kolmogorov Sync reduz a exigência de Φ."""
        # Configurar Mock do Monte Carlo
        mock_result = MagicMock()
        mock_result.monte_carlo_score = 0.5
        mock_result.win_probability = 0.6
        mock_result.expected_return = 2.0
        mock_result.conditional_var_95 = 0.1
        mock_result.optimal_sl_distance = 0
        mock_result.optimal_tp_distance = 0
        mock_result.simulation_time_ms = 10.0
        mock_mc.return_value = mock_result

        # Agente Kolmogorov detecta fluxo programático (alta confiança)
        signals = [
            AgentSignal("KolmogorovInertia", 0.9, 0.95, "ALGORITHMIC_FREIGHT_TRAIN", 4.8),
            AgentSignal("TrendAgent", 0.8, 0.9, "Bull Trend", 1.0),
            AgentSignal("VolumeAgent", 0.8, 0.9, "High Volume", 1.0)
        ]
        
        snapshot = MagicMock()
        snapshot.indicators = {
            "M5_atr_14": [500.0],
            "M5_volume_ratio": [2.0],
            "M1_high": [60100.0] * 50,
            "M1_low": [59900.0] * 50,
            "M5_high": [60100.0] * 50,
            "M5_low": [59900.0] * 50
        }
        snapshot.metadata = {"entropy": 0.3}
        snapshot.price = 60000.0
        snapshot.tick = {"ask": 60010.0, "bid": 60000.0}
        snapshot.candles = {
            "M1": {"high": [60200]*100, "low": [59800]*100, "close": [60000]*100, "open": [60000]*100},
            "M5": {"high": [60200]*100, "low": [59800]*100, "close": [60000]*100, "open": [60000]*100}
        }
        snapshot.symbol_info = {"point": 1.0, "spread": 10, "trade_tick_size": 1.0}
        
        # Φ = 0.25 (Normalmente vetado [threshold 0.35], mas Kolmogorov reduz para 0.175)
        q_state = self.engine.process(signals, snapshot=snapshot)
        q_state.phi = 0.25 
        q_state.metadata["is_programmatic"] = True
        
        regime = MagicMock()
        regime.current = MarketRegime.CREEPING_BULL
        regime.duration_bars = 10
        regime.v_pulse_detected = False
        
        decision = self.core.decide(q_state, regime, snapshot, None)
        
        self.assertIsNotNone(decision)
        print(f"Decision: {decision.action.name} | Reason: {decision.reasoning}")
        self.assertEqual(decision.action, Action.BUY)
        self.assertTrue(q_state.metadata.get("is_programmatic", False))

    def test_phd9_ghost_entry(self):
        """Ω-PhD-9: Verifica a autorização de Ghost Entry via Quantum Tunneling."""
        snapshot = MagicMock()
        snapshot.metadata = {
            "tick_velocity": 10.0,
            "momentum_delta": 0.8,
            "spread": 0.1, # Estreito
            "sell_volume": 100, # Parede baixa
            "avg_tick_volume": 500,
            "total_tick_volume": 50
        }
        
        p_tunnel = QuantumTunnelingExecution.calculate_tunneling_probability(snapshot, 1.0)
        print(f"P(Tunneling): {p_tunnel:.4f}")
        self.assertGreater(p_tunnel, 0.65)
        
        decision = Decision(
            action=Action.BUY,
            confidence=0.9,
            signal_strength=0.8,
            entry_price=100.0,
            stop_loss=99.0,
            take_profit=102.0,
            lot_size=0.1,
            regime="BULL",
            reasoning="Normal Buy",
            metadata={}
        )
        
        is_ghost = QuantumTunnelingExecution.should_authorize_ghost_entry(snapshot, decision)
        self.assertTrue(is_ghost)

if __name__ == "__main__":
    unittest.main()

if __name__ == "__main__":
    unittest.main()
