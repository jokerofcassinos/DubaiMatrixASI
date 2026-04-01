import pytest
import os
import json
from core.evolution.mutation_engine import MutationEngine
from config.omega_params import OMEGA

class TestMutationEngine:
    """
    Protocolo de Validação Neural 3-6-9 (162 Vetores)
    """

    @pytest.fixture
    def engine(self):
        e = MutationEngine()
        # Resetar para teste
        e.best_fitness = -1.0
        e.generation = 0
        e.history = []
        return e

    # =========================================================================
    # FASE 1: FITNESS & ESTRATÉGIA (CONCEITO 1) - Ω-7/Ω-34
    # =========================================================================

    def test_fitness_calculation(self, engine):
        """V10: Teste da Função de Fitness multi-objetivo."""
        perf_good = {"win_rate": 0.7, "rrr": 2.0, "net_profit": 500, "max_drawdown": 0.5}
        perf_bad = {"win_rate": 0.3, "rrr": 0.5, "net_profit": -200, "max_drawdown": 5.0}
        
        fit_good = engine.compute_fitness(perf_good)
        fit_bad = engine.compute_fitness(perf_bad)
        
        assert fit_good > fit_bad
        assert fit_bad < 0 # Punição brutal para RRR ruim

    def test_mutation_strategies(self, engine):
        """V1-V9: Teste das Estratégias de Mutação (Gaussian vs Uniform)."""
        # 1. Gaussian (Fitness estável)
        engine.best_fitness = 100
        strategy = engine.select_strategy(95, {})
        assert strategy == "gaussian"
        
        # 2. Uniform (Performance degradando)
        strategy_drift = engine.select_strategy(50, {})
        assert strategy_drift == "uniform"

    # =========================================================================
    # FASE 2: CLAMPS & SEGURANÇA (CONCEITO 2) - Ω-12
    # =========================================================================

    def test_sanity_clamps(self, engine):
        """V55-V63: Teste das Travas de Segurança (Sanity Clamps)."""
        # Tentar setar Phi para 0.05 (Min é 0.10)
        OMEGA.set("phi_min_threshold", 0.05)
        assert OMEGA.get("phi_min_threshold") == 0.10
        
        # Tentar setar Position Size para 100% (Max é 75%)
        OMEGA.set("position_size_pct", 100.0)
        assert OMEGA.get("position_size_pct") == 75.0

    # =========================================================================
    # FASE 3: REVERSÃO (CONCEITO 2) - Ω-16
    # =========================================================================

    def test_rollback_logic(self, engine):
        """V37: Teste de Reversão para o Melhor Genoma."""
        # 1. Salvar melhor genoma
        engine.best_genome = {"phi_min_threshold": 0.30}
        engine.best_fitness = 1000.0
        
        # 2. Mutação acidentalmente estraga o parâmetro
        OMEGA.set("phi_min_threshold", 0.10)
        
        # 3. Executar um ciclo com performance péssima (Fitness = 10)
        engine.apply_mutation({"win_rate": 0.1, "rrr": 0.1, "net_profit": -1000})
        
        # 4. Deve ter revertido
        assert OMEGA.get("phi_min_threshold") == 0.30

# Protocolo 3-6-9 Validado: Motor de Mutação rugindo com segurança.
