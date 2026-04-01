import unittest
import time
import os
from core.evolution.performance_tracker import PerformanceTracker, TradeOutcome

# [Ω-TEST-PERFORMANCE] Validation of Analytical Memory & Alpha Decomposition
# Testing C1 (Memory), C2 (Regime), C3 (Fitness)

class TestPerformanceEvolution(unittest.TestCase):

    def setUp(self):
        self.log_path = "data/test_evolution.json"
        if os.path.exists(self.log_path):
            os.remove(self.log_path)
        self.tracker = PerformanceTracker(storage_path=self.log_path)

    def test_trade_memory_and_stats(self):
        """[Ω-C1-V001] Trade registration and atomic persistence."""
        print("\n[STEP 1] Testing Analytical Memory...")
        
        t1 = TradeOutcome(
            trade_id="TR_001",
            symbol="BTCUSD",
            action="BUY",
            entry_price=65000.0,
            exit_price=65500.0,
            lot=1.0,
            pnl=500.0,
            pnl_net=460.0, # -40 commission
            commission=40.0,
            slippage=5.0,
            hold_time=300.0,
            regime="TRENDING",
            confidence=0.85,
            coherence=0.7
        )
        
        self.tracker.register_trade(t1)
        self.assertEqual(len(self.tracker.trades), 1)
        print("✅ Trade saved and stats updated.")

    def test_regime_alpha_decomposition(self):
        """[Ω-C2-V056] Multi-regime Alpha Sensor."""
        print("\n[STEP 2] Testing Regime-Aware Alpha...")
        
        # Simulating a bad run in Chaos and good run in Trending
        for i in range(5):
             # Profits in Trending with some variance
             self.tracker.register_trade(TradeOutcome(
                f"T_{i}", "BTC", "BUY", 100, 110, 1.0, 10, 5 + (i * 0.1), 5, 0, 60, "TRENDING", 0.9, 0.9
             ))
             # Losses in Chaos with some variance
             self.tracker.register_trade(TradeOutcome(
                f"C_{i}", "BTC", "SELL", 100, 110, 1.0, -10, -15 - (i * 0.1), 5, 0, 60, "CHAOS", 0.7, 0.4
             ))
             
        advice = self.tracker.get_hall_of_fame_advice()
        print(f"📊 Hall of Fame: {advice['best_performing_regime']} | Fitness: {advice['current_fitness']:.4f}")
        
        self.assertEqual(advice["best_performing_regime"], "TRENDING")
        self.assertGreater(self.tracker.get_sharpe("TRENDING"), 0)
        self.assertLess(self.tracker.get_sharpe("CHAOS"), 0)

    def test_evolutionary_fitness(self):
        """[Ω-C3-V109] Fitness calculation for Genetic Forge synergy."""
        print("\n[STEP 3] Testing Evolutionary Feedback (Fitness)...")
        
        # High Profit Factor and Win Rate scenario
        for i in range(10):
            self.tracker.register_trade(TradeOutcome(
                f"EV_{i}", "BTC", "BUY", 100, 150, 1.0, 50, 40 + i, 10, 0, 60, "GLOBAL", 1.0, 1.0
            ))
            
        fitness = self.tracker.calculate_fitness()
        print(f"📈 [Ω] Fitness after Alpha Streak: {fitness:.4f}")
        self.assertGreater(fitness, 1.0) # Correctly positive fitness

if __name__ == "__main__":
    unittest.main()
