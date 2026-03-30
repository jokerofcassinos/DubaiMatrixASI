import asyncio
import unittest
import numpy as np
from core.consciousness.quantum_thought import QuantumThought

# [Ω-TEST-QUANTUM] Scenario Superposition & Wave Collapse Validation
# Testing the Quantum Gate's ability to differentiate Signal from Chaos.

class TestQuantumThought(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.quantum = QuantumThought()

    async def test_superposition_update(self):
        """[Ω-V001-V054] Verifies the Mapping of Amplitudes."""
        print("\n[STEP 1] Generating Superposition...")
        # Uniform Inputs (Maximum Entropy)
        swarm_sig = 0.0
        mc_paths = [0.0] * 100
        regime_conf = 0.5
        
        self.quantum.update_superposition(swarm_sig, mc_paths, regime_conf)
        
        probs = self.quantum.current_state.get_probabilities()
        print(f"🧬 Probabilities: {probs}")
        
        # Should be roughly balanced
        self.assertAlmostEqual(np.sum(probs), 1.0, places=5)
        self.assertGreater(probs[2], 0.1) # Static state should exist

    async def test_entropy_and_collapse(self):
        """[Ω-C2-V055] Verifies von Neumann Entropy and Information Gain."""
        print("\n[STEP 2] Testing Wave Collapse Logic...")
        
        # High Confidence Scenario (Low Entropy)
        swarm_sig = 0.95 # Bullish
        mc_paths = [1.0] * 100 # All Bullish
        regime_conf = 0.9 # High Trust
        
        self.quantum.update_superposition(swarm_sig, mc_paths, regime_conf)
        entropy = self.quantum.calculate_von_neumann_entropy()
        is_ready, direction, confidence = self.quantum.should_collapse()
        
        print(f"🛡️ Entropy: {entropy:.4f}")
        print(f"📊 Authorized: {is_ready} | Direction: {direction} | Conf: {confidence:.2%}")
        
        self.assertTrue(is_ready)
        self.assertEqual(direction, "bull")
        self.assertLess(entropy, 1.0) # Low entropy for high confidence

    async def test_noise_blocking(self):
        """[Ω-V005] Verifies the rejection of Decent/Noisy states."""
        print("\n[STEP 3] Testing Chaos Rejection...")
        
        # Chaos Scenario (High Entropy)
        swarm_sig = -0.1
        mc_paths = [0.0] * 100
        regime_conf = 0.1 # Low confidence, high chaos
        
        self.quantum.update_superposition(swarm_sig, mc_paths, regime_conf)
        is_ready, direction, _ = self.quantum.should_collapse()
        
        print(f"🚫 Authorization Result: {is_ready} (Expected False)")
        self.assertFalse(is_ready)

if __name__ == "__main__":
    unittest.main()
