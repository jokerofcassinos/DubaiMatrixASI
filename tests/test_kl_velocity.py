
import unittest
from unittest.mock import MagicMock, patch
import numpy as np
import sys
import os

# Adicionar o diretório raiz ao sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.decision.trinity_core import TrinityCore, Action
from core.consciousness.quantum_thought import QuantumState
from core.consciousness.regime_detector import RegimeState, MarketRegime

class TestKLVelocity(unittest.TestCase):
    def setUp(self):
        self.core = TrinityCore()
        
    @patch('core.decision.trinity_core.OMEGA')
    def test_kl_velocity_veto(self, mock_omega):
        # Configurar mocks
        mock_omega.get.side_effect = lambda name, default=None: {
            "paradigm_shift_threshold": 0.95,
            "kl_velocity_threshold": 0.15,
            "buy_threshold": 0.7,
            "sell_threshold": -0.7,
            "confidence_min": 0.7,
            "startup_cooldown_seconds": 0,
            "max_spread_points": 5000
        }.get(name, default)

        # Mock do snapshot com KL pulando de 0.1 para 0.5 (Velocidade = 0.4 > 0.15)
        snapshot_1 = MagicMock()
        snapshot_1.metadata = {"kl_divergence": 0.1, "tick_velocity": 0.0}
        snapshot_1.price = 100.0
        snapshot_1.symbol_info = {"spread": 10, "point": 0.01}
        snapshot_1.atr = 1.0
        snapshot_1.indicators = {}
        
        snapshot_2 = MagicMock()
        snapshot_2.metadata = {"kl_divergence": 0.5, "tick_velocity": 0.0}
        snapshot_2.price = 101.0
        snapshot_2.symbol_info = {"spread": 10, "point": 0.01}
        snapshot_2.atr = 1.0
        snapshot_2.indicators = {}
        
        regime_state = MagicMock()
        regime_state.current = MagicMock()
        regime_state.current.value = "TRENDING_BULL"
        
        quantum_state = MagicMock()
        quantum_state.superposition = False
        quantum_state.collapsed_signal = 0.85
        quantum_state.confidence = 0.90
        quantum_state.phi = 0.5
        quantum_state.entropy = 0.1 # Adicionado
        quantum_state.metadata = {"is_god_candidate": False} # Adicionado
        
        asi_state = MagicMock()
        asi_state.circuit_breaker_active = False
        asi_state.consecutive_losses = 0
        
        # Primeiro ciclo: KL=0.1 (OK)
        decision_1 = self.core.decide(quantum_state, regime_state, snapshot_1, asi_state)
        
        # Segundo ciclo: KL=0.5 (Deve disparar VETO)
        decision_2 = self.core.decide(quantum_state, regime_state, snapshot_2, asi_state)
        
        if decision_2:
            print(f"Decision 2 Reasoning: {decision_2.reasoning}")
            self.assertIn("KL_VELOCITY_VETO", decision_2.reasoning)
        else:
            self.fail("Decision 2 is None - exception caught in trinity_core")

    @patch('core.decision.trinity_core.OMEGA')
    def test_entropy_convergence(self, mock_omega):
        # Configurar thresholds
        mock_omega.get.side_effect = lambda name, default=None: {
            "entropy_convergence_threshold": 0.002,
            "buy_threshold": 0.7,
            "sell_threshold": -0.7,
            "confidence_min": 0.7,
            "startup_cooldown_seconds": 0,
            "paradigm_shift_threshold": 0.95,
            "kl_velocity_threshold": 1.0, # Desativar vel veto,
            "max_spread_points": 5000
        }.get(name, default)

        # Simular 20 sinais com variância alta (0.01)
        # Sinais girando em torno de 0.65 (abaixo de 0.7)
        signals = [0.65 + (i % 2) * 0.1 for i in range(20)] # 0.65, 0.75, 0.65... Var ~ 0.0025
        
        snapshot = MagicMock()
        snapshot.metadata = {"kl_divergence": 0.1, "tick_velocity": 0.0}
        snapshot.price = 100.0
        snapshot.symbol_info = {"spread": 10, "point": 0.01}
        snapshot.atr = 1.0
        snapshot.indicators = {}
        
        regime_state = MagicMock()
        regime_state.current = MagicMock()
        regime_state.current.value = "CREEPING_BULL"
        regime_state.duration_bars = 10
        
        asi_state = MagicMock()
        asi_state.circuit_breaker_active = False
        asi_state.consecutive_losses = 0
        
        # Alimentar histórico
        for s in signals[:-1]:
            qs = MagicMock()
            qs.superposition = False
            qs.collapsed_signal = s
            qs.confidence = 0.9
            qs.phi = 0.5
            qs.entropy = 0.1
            qs.metadata = {"is_god_candidate": False}
            self.core.decide(qs, regime_state, snapshot, asi_state)
            
        # Último sinal: 0.65. Se não houver convergence, VETO pq 0.65 < 0.7
        qs_final = MagicMock()
        qs_final.superposition = False
        qs_final.collapsed_signal = 0.65
        qs_final.confidence = 0.9
        qs_final.phi = 0.5
        qs_final.entropy = 0.1
        qs_final.metadata = {"is_god_candidate": False}
        
        decision = self.core.decide(qs_final, regime_state, snapshot, asi_state)
        
        if decision:
            print(f"Decision Convergence Reasoning: {decision.reasoning}")
            self.assertIn("BUY_SIGNAL_WEAK", decision.reasoning)
            self.assertFalse(self.core.entropy_bridge_active)
        else:
            self.fail("Decision is None")

if __name__ == "__main__":
    unittest.main()
