import time
import unittest
from unittest.mock import MagicMock
from core.consciousness.neural_swarm import NeuralSwarm, AgentSignal

class SlowAgent:
    def __init__(self, name="SlowAgent", delay=0.8):
        self.name = name
        self.delay = delay
        self.weight = 1.0
        self.needs_orderflow = False

    def analyze(self, snapshot, **kwargs):
        time.sleep(self.delay)
        return AgentSignal(self.name, 1.0, 1.0, "Slow but steady", self.weight)

class TestSwarmLatency(unittest.TestCase):
    def test_timeout_resilience(self):
        swarm = NeuralSwarm()
        # Injetamos um agente propositalmente lento (0.8s)
        # O timeout antigo era 0.6s (falharia), o novo é 1.2s (deve passar)
        slow_agent = SlowAgent(delay=0.8)
        swarm.agents.append(slow_agent)
        
        # Mock do snapshot para evitar AttributeErrors nos outros agentes
        mock_snapshot = MagicMock()
        mock_snapshot.indicators = {}
        mock_snapshot.candles = {}
        mock_snapshot.m1_closes = []
        mock_snapshot.m5_closes = []
        mock_snapshot.recent_ticks = []
        
        print(f"--- Iniciando teste de latência com agente de {slow_agent.delay}s ---")
        start = time.monotonic()
        results = swarm.analyze(snapshot=mock_snapshot)
        elapsed = time.monotonic() - start
        
        print(f"Tempo total: {elapsed:.3f}s")
        self.assertLess(elapsed, 1.5)
        
        # Verifica se o agente lento foi processado
        found = any(r.agent_name == "SlowAgent" for r in results)
        self.assertTrue(found, "O agente lento deveria ter sido concluído dentro do novo prazo de 1.2s")
        
        swarm.shutdown()

if __name__ == "__main__":
    # Suprimir logs para o teste ficar limpo
    import logging
    logging.getLogger('DubaiMatrixASI').setLevel(logging.CRITICAL)
    unittest.main()
