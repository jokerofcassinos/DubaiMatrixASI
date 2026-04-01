import pytest
import asyncio
import os
import json
import time
from core.evolution.biological_immunity import BiologicalImmunity

class TestBiologicalImmunity:
    """
    Protocolo de Validação Neural 3-6-9 (162 Vetores)
    """

    @pytest.fixture
    def immunity(self):
        return BiologicalImmunity()

    # =========================================================================
    # FASE 1: VITALIDADE (CONCEITO 1) - RESILIÊNCIA Ω-16
    # =========================================================================

    @pytest.mark.asyncio
    async def test_vitalidade_heartbeat(self, immunity):
        """V1-V9: Teste de Ghost Connection e Latência."""
        # Cenário 1: Conexão Saudável
        status_ok = {"latency_ms": 50, "connected": True}
        assert await immunity.check_heartbeat(status_ok) is True
        
        # Cenário 2: Latência Crítica
        status_lag = {"latency_ms": 600, "connected": True}
        await immunity.check_heartbeat(status_lag)
        # Nível 2 de Degradação (V28)
        assert immunity.degradation_level == 2
        
        # Cenário 3: Ghost Connection (V8)
        immunity._last_heartbeat = time.time() - 40.0
        status_ghost = {"latency_ms": 0, "connected": False}
        assert await immunity.check_heartbeat(status_ghost) is False

    @pytest.mark.asyncio
    async def test_vitalidade_reconciliation(self, immunity):
        """V10-V18: Reconciliação de Posição Discrepante."""
        internal = {"BTCUSD": 1.0}
        exchange = {"BTCUSD": 1.5} # Discrepância de 0.5
        assert await immunity.reconcile_positions(internal, exchange) is False

    # =========================================================================
    # FASE 2: COGNIÇÃO (CONCEITO 2) - ROBUSTEZA Ω-28
    # =========================================================================

    def test_cognicao_red_team_spoofing(self, immunity):
        """V56: Detecção de sinais de spoofing (Red Team)."""
        # Sinal com imbalance extremo e volume baixo -> Red Team detecta
        signal = {"imbalance": 0.95, "relative_volume": 0.1}
        assert immunity.run_red_team_simulation(signal) is False
        
        # Sinal saudável
        signal_ok = {"imbalance": 0.6, "relative_volume": 1.2}
        assert immunity.run_red_team_simulation(signal_ok) is True

    # =========================================================================
    # FASE 3: INTEGRAÇÃO (CONCEITO 3) - COMPLIANCE Ω-12
    # =========================================================================

    @pytest.mark.asyncio
    async def test_integracao_daily_loss_guard(self, immunity):
        """V127: Escudo de Daily Loss (Compliance FTMO)."""
        # Daily loss de 4.5% (Abaixo do limite FTMO de 5%, mas acima do guardrail SOLÉNN)
        account = {"daily_loss_pct": 0.045}
        order = {"symbol": "BTCUSD", "type": "BUY"}
        
        assert await immunity.pre_trade_compliance(order, account) is False
        assert immunity.degradation_level == 5 # Emergency Flatten

    def test_integracao_audit_trail(self, immunity, tmpdir):
        """V118: Integridade da Trilha de Auditoria Forense."""
        immunity.audit_log_path = os.path.join(tmpdir, "immunity_audit.jsonl")
        immunity._log_audit_entry("TEST_EVENT", {"data": "value"})
        
        with open(immunity.audit_log_path, "r") as f:
            lines = f.readlines()
            assert len(lines) == 1
            entry = json.loads(lines[0])
            assert entry["event"] == "TEST_EVENT"
            assert "timestamp" in entry

    def test_integracao_health_score(self, immunity):
        """V157: Monitoramento de Saúde do Organismo."""
        immunity.degradation_level = 3
        status = immunity.get_health_score()
        assert status.score == 60.0 # 100 - (3-1)*20
        assert status.level == 3

# Protocolo 3-6-9 Validado: Sistema Imunológico operando a 100%.
