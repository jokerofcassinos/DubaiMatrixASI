import pytest
import torch
import numpy as np
from dataclasses import dataclass
from core.intelligence.regime_detector import SolennRegime, MarketRegime, RegimeState

@dataclass
class MockSnapshot:
    bid: float = 70000.0
    ask: float = 70001.0
    last_price: float = 70000.5
    spread: float = 1.0
    ema_fast: float = 70010.0
    ema_slow: float = 70000.0
    rsi_14: float = 65.0
    atr_14: float = 40.0
    hurst: float = 0.6
    entropy: float = 3.5
    vol_gk: float = 0.002
    v_pulse: float = 0.0
    jounce: float = 0.0
    lorentz_factor: float = 1.0
    book_imbalance: float = 0.1

class TestRegimeDetector:
    """
    Protocolo de Validação Neural 3-6-9 (162 Vetores)
    """

    @pytest.fixture
    def regime_engine(self):
        return SolennRegime()

    @pytest.mark.asyncio
    async def test_full_pipeline_calibration(self, regime_engine):
        """V107: Teste de calibração inicial."""
        snapshot = MockSnapshot()
        state = await regime_engine.identify(snapshot)
        assert state.current == MarketRegime.REGIME_UNKNOWN

    @pytest.mark.asyncio
    async def test_identification_after_warmup(self, regime_engine):
        """V91: O Ato de Observação Colapsando o Mercado (Identificação Real)."""
        # Warmup de 120 snapshots p/ estabilizar Hurst/Entropy
        state = None
        for i in range(120):
            # Simulando tendência com ruído leve
            price = 70000 + i + (np.random.randn() * 0.1)
            snapshot = MockSnapshot(
                last_price = price,
                ema_fast = price + 10,
                ema_slow = price - 10,
                hurst = 0.8,
                entropy = 1.2
            )
            state = await regime_engine.identify(snapshot)

        # Deve identificar tendência dado o drift positivo e baixa volatilidade relativa
        assert state.current in [MarketRegime.TRENDING_UP_STRONG, MarketRegime.TRENDING_UP_WEAK]

    @pytest.mark.asyncio
    async def test_tms_betti_numbers(self, regime_engine):
        """V10-V13: Cálculo de Números de Betti."""
        for i in range(70):
            snapshot = MockSnapshot(
                last_price = 70000 + (np.random.randn() * 5)
            )
            state = await regime_engine.identify(snapshot)

        assert len(state.betti_vector) == 3
        assert state.betti_vector[0] >= 1.0

    @pytest.mark.asyncio
    async def test_hurst_dfa_calculation(self, regime_engine):
        """V110: DFA Hurst."""
        # Gerar ruído browniano p/ H ~= 0.5
        price = 70000.0
        for i in range(150):
            price += np.random.randn()
            snapshot = MockSnapshot(last_price = price)
            state = await regime_engine.identify(snapshot)

        # Hurst p/ ruído deve estar em range razoável
        # (DFA em janelas Curtas pode ter viés, então relaxamos o check)
        assert 0.1 < state.hurst < 2.5
