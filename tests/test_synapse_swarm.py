import asyncio
import unittest
import logging
import sys
import os
from dataclasses import dataclass

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.intelligence.swarm_orchestrator import SwarmOrchestrator
from core.intelligence.base_synapse import BaseSynapse
from core.intelligence.elite.trend_synapse import TrendSynapse
from core.intelligence.elite.fractal_synapse import FractalSynapse

@dataclass
class MockSnapshot:
    price: float = 60000.0
    ema_fast: float = 59900.0
    ema_slow: float = 59800.0
    atr_14: float = 50.0
    hurst: float = 0.6
    v_pulse: float = 10.0

class TestSynapseSwarm(unittest.IsolatedAsyncioTestCase):
    
    async def asyncSetUp(self):
        self.orchestrator = SwarmOrchestrator()
        self.trend = TrendSynapse()
        self.fractal = FractalSynapse()
        
        self.orchestrator.register_synapse(self.trend)
        self.orchestrator.register_synapse(self.fractal)

    async def test_1_consciousness_aggregation(self):
        """[Ω-TEST-1] Verify the Swarm Orchestrator can collapse the wave function."""
        print("\n🧪 STAGE 1: Cognitive Alignment Check...")
        snapshot = MockSnapshot()
        
        quantum_state = await self.orchestrator.get_quantum_state(snapshot)
        
        print(f"   - Signal: {quantum_state.signal:.4f}")
        print(f"   - Phi: {quantum_state.phi:.4f}")
        print(f"   - Confidence: {quantum_state.confidence:.4f}")
        print(f"   - Coherence: {quantum_state.coherence:.4f}")
        print(f"   - Bull Agents: {quantum_state.bull_agents}")
        
        self.assertGreater(quantum_state.phi, 0.0)
        self.assertGreater(quantum_state.confidence, 0.0)
        self.assertIn("TREND_Ω", quantum_state.bull_agents)
        self.assertIn("FRACTAL_Ω", quantum_state.bull_agents)
        print("✅ STAGE 1 SUCCESS: Collective Intelligence Aligned.")

    async def test_2_bayesian_performance_update(self):
        """[Ω-TEST-2] Verify Thompson Sampling and Bayesian Learning."""
        print("\n🧪 STAGE 2: Bayesian Weight Adaptation...")
        
        # Initial priors (1.0, 1.0)
        initial_alpha = self.trend.alpha
        initial_beta = self.trend.beta
        print(f"   - Initial Prior Alpha/Beta: {initial_alpha}/{initial_beta}")

        # Simulate 5 wins
        for _ in range(5):
            await self.trend.update_performance(success=True)
        
        # Simulate 2 losses
        for _ in range(2):
            await self.trend.update_performance(success=False)
            
        print(f"   - Post-Performance Alpha/Beta: {self.trend.alpha}/{self.trend.beta}")
        
        # Sampling should favor higher values now
        samples = [self.trend.get_sample_weight() for _ in range(100)]
        avg_sample = sum(samples) / len(samples)
        
        print(f"   - Average Thompson Sample: {avg_sample:.4f}")
        self.assertGreater(self.trend.alpha, initial_alpha)
        self.assertGreater(avg_sample, 0.5)
        print("✅ STAGE 2 SUCCESS: Synaptic Weights Evolved.")

    async def test_3_fractal_eagle_vision(self):
        """[Ω-TEST-3] Verify HTF context integration."""
        print("\n🧪 STAGE 3: Fractal Eagle-Vision Integration...")
        snapshot = MockSnapshot()
        
        # Case: HTF is Bearish, but LTF is Bullish (Contramaré)
        self.fractal.update_htf_context({"1h_bias": -1.0, "4h_bias": -1.0})
        
        q_state = await self.orchestrator.get_quantum_state(snapshot)
        
        print(f"   - Contramaré Signal: {q_state.signal:.4f}")
        print(f"   - Contramaré Coherence: {q_state.coherence:.4f}")
        
        # Signal should be low/zero because of fractal conflict
        self.assertLess(abs(q_state.signal), 0.5)
        
        # Case: Resonant Alignment (All Bullish)
        self.fractal.update_htf_context({"1h_bias": 1.0, "4h_bias": 1.0})
        q_state_resonant = await self.orchestrator.get_quantum_state(snapshot)
        
        print(f"   - Resonant Signal: {q_state_resonant.signal:.4f}")
        self.assertGreater(q_state_resonant.signal, 0.5)
        print("✅ STAGE 3 SUCCESS: Fractal Consciousness Unified.")

if __name__ == "__main__":
    unittest.main()
