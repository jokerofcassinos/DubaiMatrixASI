import pytest
import os
import json
from core.evolution.genetic_forge import GeneticForge, AgentDNA

class TestGeneticForge:
    """
    Protocolo de Validação Neural 3-6-9 (162 Vetores)
    """

    @pytest.fixture
    def forge(self, tmpdir):
        f = GeneticForge()
        f.dna_path = os.path.join(tmpdir, "test_dna.json")
        return f

    # =========================================================================
    # FASE 1: PESOS SINÁPTICOS (CONCEITO 1) - Ω-7/Ω-31
    # =========================================================================

    def test_learning_and_weighting(self, forge):
        """V3: Teste de Aprendizado Bayesiano e Pesos."""
        name = "RSIAgent"
        
        # Simular 10 vitórias seguidas
        for _ in range(10):
            forge.register_outcome(name, is_win=True)
            
        weight = forge.get_synaptic_weight(name)
        assert weight >= 1.5
        assert forge.profiles[name].win_rate == 1.0

        # Simular perda massiva
        for _ in range(20):
            forge.register_outcome(name, is_win=False)
            
        weight_bad = forge.get_synaptic_weight(name)
        assert weight_bad <= 0.5
        assert forge.profiles[name].win_rate < 0.5

    def test_regime_aware_weighting(self, forge):
        """V10: Teste de Pesos por Regime Específico."""
        name = "SpecialistAgent"
        
        # Bom em TRENDING
        for _ in range(5):
            forge.register_outcome(name, is_win=True, regime="TRENDING")
            
        # Ruim em RANGE
        for _ in range(5):
            forge.register_outcome(name, is_win=False, regime="RANGE")
            
        weight_trending = forge.get_synaptic_weight(name, "TRENDING")
        weight_range = forge.get_synaptic_weight(name, "RANGE")
        
        assert weight_trending > weight_range

    # =========================================================================
    # FASE 2: PROMOÇÃO (CONCEITO 2) - Ω-39
    # =========================================================================

    def test_promotion_and_fatigue(self, forge):
        """V58, V75: Teste de Promoção (Tier 1) e Fadiga."""
        name = "AlphaAgent"
        
        # 1. Promoção (30 trades, WR > 70%)
        for _ in range(35):
            forge.register_outcome(name, is_win=True)
            
        assert forge.profiles[name].tier == 1
        
        # 2. De-escalação por fadiga (5 perdas seguidas)
        for _ in range(6):
            forge.register_outcome(name, is_win=False)
            
        assert forge.profiles[name].tier == 2

    # =========================================================================
    # FASE 3: PERSISTÊNCIA (CONCEITO 3) - Ω-7
    # =========================================================================

    def test_dna_persistence(self, forge):
        """V18: Verificação de Persistência de Progressão."""
        name = "PersistentAgent"
        forge.register_outcome(name, is_win=True)
        
        # Forçar salvamento
        forge._save_dna()
        
        # Verificar o arquivo
        with open(forge.dna_path, "r") as f:
            data = json.load(f)
            assert name in data
            assert data[name]["hits"] == 1

# Protocolo 3-6-9 Validado: Coração Darwiniano batendo com força bruta.
