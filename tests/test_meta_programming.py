import pytest
import ast
from core.evolution.meta_programming import MetaProgrammingEngine, ThresholdOptimizer

class MockAgent:
    """Mock Agent p/ teste de evolução AST."""
    THRESHOLD = 10.0
    
    def validate(self, val: float) -> bool:
        return val > self.THRESHOLD

class WildAgent:
    """Agente com loop proposital p/ teste de segurança."""
    def run(self):
        while True:
            pass

class TestMetaProgramming:
    """
    Protocolo de Validação Neural 3-6-9 (162 Vetores)
    """

    @pytest.fixture
    def engine(self):
        return MetaProgrammingEngine()

    # =========================================================================
    # FASE 1: TRANSFORMAÇÃO AST (CONCEITO 1) - Ω-34
    # =========================================================================

    def test_threshold_optimization(self, engine):
        """V1: Teste de otimização de limite (Threshold)."""
        optimizer = ThresholdOptimizer("THRESHOLD", 20.0)
        
        # Evoluir a lógica do MockAgent
        EvolvedAgent = engine.rewrite_logic(MockAgent, optimizer)
        
        assert EvolvedAgent is not None
        assert EvolvedAgent.__name__ == "MockAgent_Evolved"
        
        # Instanciar e testar comportamento alterado
        agent = EvolvedAgent()
        
        # 15.0 era True no original (10.0), deve ser False no evoluído (20.0)
        assert agent.validate(15.0) is False
        assert agent.validate(25.0) is True
        
        # O original deve permanecer inalterado
        original = MockAgent()
        assert original.validate(15.0) is True

    def test_logic_halting_detection(self, caplog, engine):
        """V73: Detecção de loops 'While' perigosos."""
        optimizer = ThresholdOptimizer("UNUSED", 0) # Apenas p/ disparar o visitor
        
        with caplog.at_level("WARNING"):
            engine.rewrite_logic(WildAgent, optimizer)
            assert "Loop 'While' detectado" in caplog.text

    def test_broken_ast_error_handling(self, engine):
        """V17: Verificação de erros de compilação."""
        # Tentar evoluir um objeto que não suporta inspect.getsource
        result = engine.rewrite_logic(lambda x: x+1, ThresholdOptimizer("X", 0))
        assert result is None

# Protocolo 3-6-9 Validado: A SOLÉNN agora reescreve sua própria arquitetura.
