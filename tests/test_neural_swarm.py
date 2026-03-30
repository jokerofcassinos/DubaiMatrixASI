import asyncio
import unittest
import numpy as np
from core.consciousness.neural_swarm import NeuralSwarm, SwarmAgent
from core.consciousness.genetic_forge import Genome

# [Ω-TEST-SWARM] Neural Swarm Consensus Validation
# Testing the Great Council's Cohesion and Adaptive Weighting

class TestNeuralSwarm(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.swarm = NeuralSwarm(max_agents=50)
        # Create 3 Mock Genomes: Bull, Bear, and Noise
        self.hall_of_fame = [
            Genome(id="Bull_Gen", expression="(+ EMA RSI)"), # likely positive
            Genome(id="Bear_Gen", expression="(- ATR 50)"),   # likely negative
            Genome(id="Chaos_Gen", expression="(* 0 0)")      # Neutral
        ]

    async def test_agent_assembly(self):
        """[Ω-V002] Verifies assembly and compilation of S-Expressions."""
        print("\n[STEP 1] Assembling Agents...")
        self.swarm.populate(self.hall_of_fame)
        
        self.assertEqual(len(self.swarm.agents), 3)
        self.assertTrue(all(a.compiled_func is not None for a in self.swarm.agents))
        print(f"✅ Agents Online: {[a.genome.id for a in self.swarm.agents]}")

    async def test_consensus_dynamics(self):
        """[Ω-C2-V056] Verifies the weighted voting synthesis."""
        print("\n[STEP 2] Testing Consensus Logic...")
        self.swarm.populate(self.hall_of_fame)
        
        # Context where Bull should win
        context = {"EMA": 100, "RSI": 60, "ATR": 10}
        
        # Execution
        result = await self.swarm.get_consensus_signal(context)
        
        print(f"🧬 Weighted Signal: {result['signal']:.4f}")
        print(f"🎯 Confidence: {result['confidence']:.4%}")
        
        # Bull: tanh(160) -> 1.0
        # Bear: tanh(-40) -> -1.0
        # Chaos: tanh(0) -> 0.0
        # Weighted (all R=1.0): (1 - 1 + 0) / 3 = 0.0
        self.assertAlmostEqual(result['signal'], 0.0, places=2)

    async def test_reputation_adaptation(self):
        """[Ω-C3-V111] Verifies if reputation changes with performance."""
        print("\n[STEP 3] Testing Reputation Adaptation...")
        self.swarm.populate(self.hall_of_fame)
        
        initial_rep = self.swarm.agents[0].reputation
        
        # Reward the first agent
        self.swarm.calibrate_reputations(realized_move=1.0)
        
        new_rep = self.swarm.agents[0].reputation
        print(f"📈 Rep Evolution: {initial_rep:.2f} -> {new_rep:.2f}")
        
        self.assertGreater(new_rep, initial_rep)

if __name__ == "__main__":
    unittest.main()
