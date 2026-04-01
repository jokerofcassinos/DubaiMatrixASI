import pytest
import asyncio
import time
from dataclasses import dataclass
from core.intelligence.signals_gate import SolennSignalGate, MarketRegime, QuantumState

@dataclass
class MockSnapshot:
    symbol: str = "BTCUSD"
    timestamp: float = time.time()
    book_imbalance: float = 0.1
    spread: float = 1.0
    vol_gk: float = 0.001

class TestSignalsGate:
    """
    Protocolo de Validação Neural 3-6-9 (162 Vetores)
    """

    @pytest.fixture
    def gate(self):
        return SolennSignalGate()

    @pytest.mark.asyncio
    async def test_high_confidence_buy_signal(self, gate):
        """V91: Teste de aceitação de sinal com alta confluência."""
        snapshot = MockSnapshot(book_imbalance=0.1)
        # QuantumState(signal, phi, confidence, coherence)
        state = QuantumState(0.5, 0.0, 0.9, 0.8)
        
        result = await gate.evaluate(
            snapshot, state, MarketRegime.TRENDING_UP_STRONG, 0.85
        )
        
        assert result.action == "BUY"
        assert result.net_ev > 0
        assert "ACCEPTED" in result.reasoning

    @pytest.mark.asyncio
    async def test_rejection_low_confidence(self, gate):
        """V2: Rejeição por confiança abaixo do threshold."""
        snapshot = MockSnapshot()
        state = QuantumState(0.5, 0.0, 0.4, 0.8)
        
        result = await gate.evaluate(
            snapshot, state, MarketRegime.TRENDING_UP_STRONG, 0.85
        )
        
        assert result.action == "NONE"
        assert "LOW_CONFIDENCE" in result.reasoning

    @pytest.mark.asyncio
    async def test_toxic_imbalance_rejection(self, gate):
        """V62: Rejeição por desequilíbrio tóxico no order flow."""
        snapshot = MockSnapshot(book_imbalance=0.98) # Toxicidade extrema
        state = QuantumState(0.5, 0.0, 0.9, 0.8)
        
        result = await gate.evaluate(
            snapshot, state, MarketRegime.TRENDING_UP_STRONG, 0.85
        )
        
        assert result.action == "NONE"
        assert "TOXIC_IMBALANCE" in result.reasoning

    @pytest.mark.asyncio
    async def test_unprofitable_tce_rejection(self, gate):
        """V83: Rejeição por custo de execução superior ao lucro esperado."""
        # Aumentar spread e vol para tornar o trade não lucrativo
        snapshot = MockSnapshot(spread=100.0, vol_gk=0.1) 
        state = QuantumState(0.5, 0.0, 0.9, 0.8)
        
        result = await gate.evaluate(
            snapshot, state, MarketRegime.TRENDING_UP_STRONG, 0.85
        )
        
        assert result.action == "NONE"
        assert "UNPROFITABLE_TCE" in result.reasoning

    @pytest.mark.asyncio
    async def test_regime_lockout_unknown(self, gate):
        """V29: Bloqueio absoluto em regime desconhecido."""
        snapshot = MockSnapshot()
        state = QuantumState(0.95, 0.0, 0.95, 0.95) # Sinal perfeito
        
        result = await gate.evaluate(
            snapshot, state, MarketRegime.REGIME_UNKNOWN, 0.95
        )
        
        # Mesmo com sinal perfeito, o regime UNKNOWN deve bloquear pelo threshold adaptativo 0.99
        assert result.action == "NONE"
        assert "LOW_CONFIDENCE" in result.reasoning
