import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import time

# Add project root to path
sys.path.append(os.getcwd())

from core.decision.trinity_core import TrinityCore, Action
from core.consciousness.regime_detector import MarketRegime
from config.omega_params import OMEGA
from execution.sniper_executor import SniperExecutor

class TestOmegaStability(unittest.TestCase):
    def setUp(self):
        self.trinity = TrinityCore()
        # Mock para evitar Veto de Startup nos testes
        self.trinity._is_startup_cooldown = MagicMock(return_value=False)
        
        # Ensure OMEGA is initialized with our new defaults
        OMEGA.load()

    def test_kl_paradigm_shift_veto(self):
        """Verifica se o Veto de Paradigm Shift (KL > 1.5) funciona."""
        snapshot = MagicMock()
        snapshot.metadata = {"kl_divergence": 4.5}
        snapshot.price = 70000.0
        
        quantum_state = MagicMock()
        regime_state = MagicMock()
        regime_state.current = MarketRegime.TRENDING_BULL
        regime_state.v_pulse_detected = False
        asi_state = MagicMock()
        asi_state.startTime = time.time() - 1000 
        asi_state.circuit_breaker_active = False

        # Mocking check_vetos to pass through to the KL check
        with patch.object(self.trinity, '_check_vetos', return_value=None):
            decision = self.trinity.decide(quantum_state, regime_state, snapshot, asi_state)
        
        self.assertEqual(decision.action, Action.WAIT)
        self.assertIn("PARADIGM_SHIFT VETO", decision.reasoning)
        self.assertEqual(decision.metadata.get("kl_div"), 4.5)

    def test_phi_gate_creeping_regime(self):
        """Verifica se regimes rasteiros exigem Φ mais alto (0.35)."""
        snapshot = MagicMock()
        snapshot.metadata = {"kl_divergence": 0.0}
        snapshot.price = 70000.0
        
        # Simular Φ=0.20 (acima do global 0.15, mas abaixo do específico 0.35 para CREEPING)
        quantum_state = MagicMock()
        quantum_state.phi = 0.20
        quantum_state.raw_signal = 0.8  # Signal forte
        quantum_state.confidence = 0.8
        
        regime_state = MagicMock()
        regime_state.current = MarketRegime.CREEPING_BULL
        
        asi_state = MagicMock()
        asi_state.startTime = time.time() - 1000
        asi_state.circuit_breaker_active = False

        # Mocking internal methods that precede the Phi Gate check
        with patch.object(self.trinity, '_check_vetos', return_value=None), \
             patch.object(self.trinity, '_wait', side_effect=lambda r: MagicMock(action=Action.WAIT, reasoning=f"WAIT: {r}")):
            
            # Here we hack the decide function to skip directly to the phi gate logic if possible, 
            # OR we ensure the preceding checks pass. Since we can't easily skip lines in Python,
            # we must ensure quantum_state has enough agents to pass superposition.
            
            # Setup Quantum State for "Convergence" but low PHI
            quantum_state.phi = 0.20
            q_meta = {"agent_signals": "BULL[10] BEAR[2]"} # Clear bias
            quantum_state.metadata = q_meta
            
            decision = self.trinity.decide(quantum_state, regime_state, snapshot, asi_state)
            
            self.assertEqual(decision.action, Action.WAIT)
            self.assertIn("SIGNAL_FRAGILE(Φ=0.20 < 0.35)", decision.reasoning)

    def test_latency_abort(self):
        """Verifica se o kill-switch de latência aborta a execução lenta."""
        bridge = MagicMock()
        risk = MagicMock()
        risk.validate_trade.return_value = (True, 1.0, "OK") # Auto-approve
        
        executor = SniperExecutor(bridge, risk)
        
        decision = MagicMock()
        decision.action = Action.BUY
        decision.confidence = 0.9
        decision.entry_price = 70000.0
        decision.stop_loss = 69000.0
        decision.take_profit = 72000.0
        decision.metadata = {}
        
        snapshot = MagicMock()
        snapshot.metadata = {}
        snapshot.account = {"balance": 100000.0, "margin_free": 50000.0}
        snapshot.indicators = {}
        
        asi_state = MagicMock()
        asi_state.win_rate = 0.6
        asi_state.total_trades = 50
        asi_state.total_profit = 5000.0
        
        # Simular atraso artificial de 500ms
        # Precisamos de 7 chamadas ao time.time()
        # 1. execution_intent_time
        # 2. now (sonar check)
        # 3. now (candle time)
        # 4. now_epoch (metralhadora timer)
        # 5. now (metralhadora log cooldown)
        # 6. now (post_close log cooldown)
        # 7. now_pre_dispatch (Kill-switch)
        with patch('time.time') as mock_time:
            start_time = 1000.0
            mock_time.side_effect = [
                start_time,          # execution_intent_time
                start_time + 0.01,   # sonar
                start_time + 0.02,   # candle
                start_time + 0.03,   # now_epoch
                start_time + 0.04,   # log cooldowns
                start_time + 0.05,   # log cooldowns
                start_time + 0.50    # now_pre_dispatch (ABORT!)
            ]
            
            result = executor.execute(decision, asi_state, snapshot)
            
            self.assertIsNone(result)
            # Verificar se bridge.send_market_order NUNCA foi chamado
            bridge.send_market_order.assert_not_called()

if __name__ == "__main__":
    unittest.main()
