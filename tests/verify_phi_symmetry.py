
import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock OMEGA before imports
import config.omega_params as omega_params
# OMEGA does not support item assignment, use set() if available or mock directly
# In this environment, we just need to satisfy the import

import time
from core.decision.trinity_core import TrinityCore, Action
from core.consciousness.quantum_thought import QuantumState, AgentSignal

class TestPhiSymmetryGuard(unittest.TestCase):
    def setUp(self):
        self.trinity = TrinityCore()
        # Bypass startup cooldown
        self.trinity._start_time = time.time() - 3600 
        self.snapshot = MagicMock()
        self.snapshot.metadata = {"pnl_prediction": "STABLE", "entropy": 0.9}
        self.snapshot.tick = {"ask": 65000, "bid": 64995}
        self.regime = MagicMock()
        self.regime.current.value = "HIGH_VOL_CHAOS"
        self.state = MagicMock()

    def test_symmetry_guard_blocks_gaslit_buy(self):
        """Testa se o Guard bloqueia um sinal de compra quando o enxame é massivamente bear."""
        # Simula o cenário do trade de 20:07:58
        q_state = QuantumState(
            raw_signal=0.75,      # Sinal de compra forte (gaslit)
            collapsed_signal=0.75,
            confidence=0.85,
            coherence=0.40,
            entropy=0.85,
            superposition=False,
            decision_vector=None,
            agent_contributions={},
            agent_signals=[],
            phi=0.02,             # PHI extremamente baixo
            metadata={
                "bull_agents": ["A"] * 15,
                "bear_agents": ["B"] * 22, # Maioria Bear
                "is_god_candidate": True
            },
            reasoning="Simulation"
        )
        
        # Metadata must match what TrinityCore expects
        q_state.metadata = {
            "bull_agents": ["BullAgent"] * 10,
            "bear_agents": ["BearAgent"] * 30,
            "is_god_candidate": True,
            "phi": 0.02,
            "entropy": 0.85
        }
        
        decision = self.trinity.decide(q_state, self.regime, self.snapshot, self.state)
        
        # O motivo deve conter PHI_SYMMETRY_GUARD
        reasoning = decision.reasoning if hasattr(decision, 'reasoning') else ""
        print(f"DEBUG REASON: {reasoning}")
        self.assertEqual(decision.action, Action.WAIT)
        self.assertTrue("PHI_SYMMETRY_GUARD" in reasoning)

if __name__ == "__main__":
    unittest.main()
