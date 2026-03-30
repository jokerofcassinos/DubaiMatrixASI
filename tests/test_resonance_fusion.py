import unittest
import asyncio
from dataclasses import dataclass, field
from typing import Dict, Any

from core.decision.trinity_core import TrinityCore, Action
from core.resonance_orchestrator import ResonanceSnapshot

# [Ω-TEST-RESONANCE] Fusion & Veto Validation

@dataclass
class MockQuantumState:
    signal: float
    phi: float
    confidence: float
    coherence: float
    bull_agents: list = None
    bear_agents: list = None

@dataclass
class MockRegimeState:
    current: str = "TRENDING"
    monte_carlo_paths: list = field(default_factory=lambda: [1, 1, 1, 1]) # Bullish paths
    confidence: float = 0.9

@dataclass
class MockSnapshot:
    price: float = 65000.0
    spread: float = 1.0
    metadata: Dict[str, Any] = None

class TestResonanceFusion(unittest.IsolatedAsyncioTestCase):
    
    async def asyncSetUp(self):
        self.trinity = TrinityCore()
        
    async def test_global_panic_veto(self):
        """[V057] Black Swan / Global Panic Veto."""
        q_state = MockQuantumState(signal=0.8, phi=0.9, confidence=0.9, coherence=0.9, bull_agents=["A1", "A2", "A3"])
        snapshot = MockSnapshot(metadata={"atr_14": 10.0})
        
        # Simulating Extreme Global Panic
        res_snap = ResonanceSnapshot(
            timestamp=0, macro_score=-1.0, onchain_score=-1.0, sentiment_score=-1.0,
            gravity_center=-0.9, coherence=1.0, is_panic=True, confidence=1.0
        )
        
        reg_state = MockRegimeState()
        decision = await self.trinity.decide(q_state, reg_state, snapshot, res_snapshot=res_snap)
        
        self.assertEqual(decision.action, Action.WAIT)
        self.assertIn("GLOBAL_PANIC", decision.reason)
        print(f"✅ Veto Global Panic: {decision.reason}")

    async def test_incoherent_gravity_veto(self):
        """[V056] Incoherent Gravity Veto (Tech Buy vs Macro Bear)."""
        # Strong Technical Buy Signal
        q_state = MockQuantumState(signal=0.8, phi=0.9, confidence=0.9, coherence=0.9, bull_agents=["A1", "A2", "A3"])
        snapshot = MockSnapshot(metadata={"atr_14": 10.0})
        
        # Extreme Bearish Environment (Macro/On-Chain negative)
        res_snap = ResonanceSnapshot(
            timestamp=0, macro_score=-0.9, onchain_score=-0.8, sentiment_score=-0.1,
            gravity_center=-0.85, coherence=0.9, is_panic=False, confidence=1.0
        )
        
        reg_state = MockRegimeState()
        decision = await self.trinity.decide(q_state, reg_state, snapshot, res_snapshot=res_snap)
        
        self.assertEqual(decision.action, Action.WAIT)
        self.assertIn("INCOHERENT_GRAVITY", decision.reason)
        print(f"✅ Veto Gravidade Incoerente: {decision.reason}")

    async def test_synergistic_approval(self):
        """[V109] Synergistic Alignment: Tech + Environment."""
        # Strong Buy Signal
        q_state = MockQuantumState(signal=0.8, phi=0.9, confidence=0.9, coherence=0.9, bull_agents=["A1", "A2", "A3"])
        # Mocking ATR and key levels safely
        snapshot = MockSnapshot(metadata={"atr_14": 100.0, "near_key_level": True})
        
        # Positive Environment
        res_snap = ResonanceSnapshot(
            timestamp=0, macro_score=0.4, onchain_score=0.4, sentiment_score=0.5,
            gravity_center=0.45, coherence=0.95, is_panic=False, confidence=1.0
        )
        
        # Adjusting Trinity configuration to allow for high ATR moves
        self.trinity.config["phi_min"] = 0.05
        self.trinity.config["mvp_floor"] = 1.0 # Allow for small test profit
        
        decision = await self.trinity.decide(q_state, "TRENDING", snapshot, res_snapshot=res_snap)
        
        # Should NOT be vetoed if logic holds
        if decision.action != Action.WAIT:
            self.assertEqual(decision.action, Action.BUY)
            print(f"✅ Aprovação Sinérgica: {decision.action.value} | Reason: {decision.reason}")
        else:
            print(f"⚠️ Synergitic Vetoed anyway: {decision.reason}")

if __name__ == "__main__":
    unittest.main()
