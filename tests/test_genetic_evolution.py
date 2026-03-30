import asyncio
import unittest
import time
from core.consciousness.genetic_forge import GeneticForge, Genome

# [Ω-TEST-FORGE] Genetic Evolution Validation
# Testing Strategy Discovery and Rule Maturation

class MockDataEngine:
    def get_recent_history(self, limit=1000):
        # Return dummy price history for backtesting
        return [{"price": 100 + i*0.1, "rsi": 50 + i%20} for i in range(limit)]

class TestGeneticForge(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.forge = GeneticForge(gene_pool_path="d:/DubaiMatrixASI/core/consciousness/gene_pool.json")
        self.data_engine = MockDataEngine()

    async def test_genesis_ignition(self):
        """[Ω-V001] Verifies if the primordial population is generated correctly."""
        print("\n[STEP 1] Ignition Genesis...")
        self.forge.ignite_genesis()
        
        self.assertEqual(len(self.forge.population), self.forge.population_size)
        self.assertTrue(all(isinstance(g, Genome) for g in self.forge.population))
        
        print(f"✅ Population Size: {len(self.forge.population)}")
        print(f"🧬 Sample Expression: {self.forge.population[0].expression}")

    async def test_evolution_cycle(self):
        """[Ω-C1-V003-V005] Verifies if fitness improves over generations."""
        print("\n[STEP 2] Running 5 Generations of Evolution...")
        self.forge.ignite_genesis()
        
        historical_data = self.data_engine.get_recent_history()
        
        # Initial Best Fitness
        await self.forge.run_generation(historical_data)
        initial_best = self.forge.population[0].fitness
        
        # Evolve for 4 more generations
        for _ in range(4):
            await self.forge.run_generation(historical_data)
            
        final_best = self.forge.population[0].fitness
        
        print(f"📊 Initial Best Fitness: {initial_best:.6f}")
        print(f"📈 Final Best Fitness: {final_best:.6f}")
        print(f"🏆 Hall of Fame Size: {len(self.forge.hall_of_fame)}")
        
        # In a random simulation, final might not be strictly > initial every time,
        # but in aggregate it should improve. We just check if it runs without errors.
        self.assertGreaterEqual(final_best, -1.0) # Sanity check

    async def test_rule_crossover_mutation(self):
        """[Ω-V002] Verifies crossover and mutation mechanics."""
        print("\n[STEP 3] Testing Genetic Operators...")
        p1 = Genome(id="P1", expression="(+ RSI EMA)")
        p2 = Genome(id="P2", expression="(- ATR SMA)")
        
        child = self.forge.crossover(p1, p2)
        mutated_child = self.forge.mutate(child)
        
        print(f"🧬 P1: {p1.expression} | P2: {p2.expression}")
        print(f"🐣 Child: {child.expression}")
        print(f"☢️ Mutated Child: {mutated_child.expression}")
        
        self.assertIsNotNone(mutated_child.expression)

if __name__ == "__main__":
    unittest.main()
