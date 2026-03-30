import unittest
import numpy as np
from core.consciousness.reflexive_loop import ReflexiveLoop

# [Ω-TEST-SOROS] Reflexive Dynamics & Climax Validation
# Testing the feedback loop between Market Reality and Cognitive Bias.

class TestReflexiveLoop(unittest.TestCase):

    def setUp(self):
        self.reflex = ReflexiveLoop(window_size=20)

    def test_bias_calculation(self):
        """[Ω-C1-V001] Verifies Bias inference from volume flow."""
        print("\n[STEP 1] Testing Cognitive Bias calculation...")
        # Strong Buy Pressure
        bias = self.reflex.calculate_cognitive_bias(taker_buy=100.0, taker_sell=10.0, spread=0.001)
        print(f"📈 Buy Bias: {bias:.4f}")
        self.assertGreater(bias, 0.5)
        
        # Strong Sell Pressure
        bias = self.reflex.calculate_cognitive_bias(taker_buy=10.0, taker_sell=100.0, spread=0.001)
        print(f"📉 Sell Bias: {bias:.4f}")
        self.assertLess(bias, -0.5)

    def test_boom_to_climax_transition(self):
        """[Ω-C2-V056] Simulates a Boom followed by a Climax divergence."""
        print("\n[STEP 2] Simulating BOOM -> CLIMAX cycle...")
        
        # 1. Simulate BOOM: Price and Bias rise together
        price = 60000.0
        bias = 0.5
        for i in range(25):
            # Vincular a magnitude das variações para garantir correlação [V055]
            noise = 0.5 + np.random.rand()
            price += 100.0 * noise
            bias += 0.05 * noise
            self.reflex.update_dynamics(price, bias)
            
        print(f"🚀 Status after cycle: {self.reflex.status} | R={self.reflex.reflexivity_factor:.4f}")
        self.assertEqual(self.reflex.status, "BOOM")
        self.assertGreater(self.reflex.reflexivity_factor, 0.8)
        
        # 2. Simulate CLIMAX: Price continues up, but Bias collapses (Divergence)
        for i in range(5):
            price += 100.0
            bias -= 0.3 # Bias dropping while price rises
            self.reflex.update_dynamics(price, bias)
            
        is_climax, direction, confidence = self.reflex.detect_climax_inflection()
        print(f"⚠️ Climax Signal: {is_climax} | Direction: {direction} | R={confidence:.4f}")
        
        self.assertTrue(is_climax)
        self.assertEqual(direction, "short")
        self.assertEqual(self.reflex.status, "CLIMAX")

    def test_random_rejection(self):
        """[Ω-V055] Verifies non-correlation rejection."""
        print("\n[STEP 3] Testing Random Market Rejection...")
        
        # Random noise
        for _ in range(25):
            price = 60000.0 + np.random.normal(0, 50)
            bias = np.random.normal(0, 0.2)
            self.reflex.update_dynamics(price, bias)
            
        print(f"🎲 Status: {self.reflex.status} | R={self.reflex.reflexivity_factor:.4f}")
        self.assertNotEqual(self.reflex.status, "BOOM")

if __name__ == "__main__":
    unittest.main()
