"""
    🧪 TESTE DE RESSONÂNCIA: SOLENN REGIME Ω (v2.1)
    Verificação da Glândula Pineal sob estresse topológico.
"""

import pytest
import asyncio
import numpy as np
from core.solenn_regime import SolennRegime, MarketRegime

class MockSnapshot:
    def __init__(self, bid, ask, hurst=0.5, entropy=2.0):
        self.bid = bid
        self.ask = ask
        self.last_price = (bid + ask) / 2
        self.spread = ask - bid
        self.ema_fast = self.last_price
        self.ema_slow = self.last_price
        self.rsi_14 = 50.0
        self.atr_14 = 10.0
        self.hurst = hurst
        self.entropy = entropy
        self.vol_gk = 0.01
        self.v_pulse = 0.5
        self.jounce = 0.1
        self.lorentz_factor = 1.0
        self.book_imbalance = 0.0

@pytest.mark.asyncio
async def test_regime_stabilization():
    """Verifica se o regime estabiliza após a janela de calibração."""
    regime = SolennRegime()
    
    # Gerando 60 snapshots ruidosos (Ranging)
    for i in range(60):
        # Ruído muito pequeno para manter a entropia baixa
        snapshot = MockSnapshot(50000 + np.random.randn() * 0.1, 50000.1 + np.random.randn() * 0.1, hurst=0.45, entropy=1.2)
        snapshot.ema_fast = 50000.05
        snapshot.ema_slow = 50000.05
        state = await regime.identify(snapshot)
        
    print(f"\nFinal Stable State: {state.current.value}")
    assert state.current != MarketRegime.REGIME_UNKNOWN
    assert len(state.betti_vector) == 3
    assert state.confidence > 0  # HMM should have some certainty

@pytest.mark.asyncio
async def test_trending_detection():
    """Simula um trending forte para verificar a sensibilidade multifractal."""
    regime = SolennRegime()
    
    # Calibração
    for i in range(50):
        await regime.identify(MockSnapshot(50000, 50001))
        
    # Trending Bull (Hurst alto + Momentum)
    base_price = 50000
    for i in range(100):
        base_price += 10 # Strong move
        snapshot = MockSnapshot(base_price, base_price + 1, hurst=0.75, entropy=0.5)
        # Injetando momentum via fast/slow
        snapshot.ema_fast = base_price
        snapshot.ema_slow = base_price - 50
        state = await regime.identify(snapshot)
        
    print(f"Trending state identified: {state.current.value}")
    assert state.current == MarketRegime.TRENDING_UP_STRONG
    assert state.hurst > 0.6

@pytest.mark.asyncio
async def test_critical_slowing_down():
    """Verifica se o CSD aumenta durante transições induzidas."""
    regime = SolennRegime()
    
    # Calibração (Stable)
    for i in range(50):
        await regime.identify(MockSnapshot(50000, 50001))
        
    initial_csd = (await regime.identify(MockSnapshot(50000, 50001))).csd_score
    
    # Transição abrupta (Injeção de "Chaos")
    for i in range(20):
        price = 50000 + np.random.randn() * 100 # Volatilidade extrema
        await regime.identify(MockSnapshot(price, price + 1, hurst=0.5, entropy=4.5))
        
    final_csd = (await regime.identify(MockSnapshot(50000, 50001))).csd_score
    print(f"CSD Transition: {initial_csd} -> {final_csd}")
    assert final_csd > initial_csd # CSD must increase with volatility shock
