import pytest
import asyncio
import numpy as np
import time
from market.orderflow_matrix import OrderflowMatrix, MatrixSignal

# [Ω-SOLÉNN] Auditoria Neural: Percepção de Realidade (Matrix Ω-0)
# Validação de Convergência do Sinal Φ e Decomposição PhD

@pytest.fixture
def matrix():
    return OrderflowMatrix("BTCUSD")

@pytest.mark.asyncio
async def test_matrix_genesis_initialization(matrix):
    """Fase 1: Vitalidade (Gênese)."""
    await matrix.initialize()
    assert matrix._is_running is True
    await matrix.stop()
    assert matrix._is_running is False

@pytest.mark.asyncio
async def test_matrix_signal_phi_convergence(matrix):
    """Fase 2: Cognição (Convergência de Φ)."""
    await matrix.initialize()
    
    # Simulating organic bullish flow
    for i in range(250):
        tick = {
            "price": 60000 + (i * 0.1),
            "volume": 0.5 + (np.random.random() * 0.5),
            "side": "buy",
            "type": "market",
            "is_taker": True,
            "time_ns": time.time_ns(),
            "last_ask": 60000.5,
            "last_bid": 60000.4
        }
        signal = await matrix.ingest_tick(tick)
        
    print(f"\nFinal Phi: {signal.phi}, Urgency: {signal.urgency}, Genuinity: {signal.genuinity}, VPIN: {signal.toxicity}")
    # Phi should not be zero after consistent pressure
    assert signal.phi != 0.0
    assert signal.metadata['perf_ns'] < 100000000 # 100ms budget
    
    await matrix.stop()

@pytest.mark.asyncio
async def test_matrix_manipulation_detection(matrix):
    """Fase 3: Inteligência (Detecção de Manipulação)."""
    await matrix.initialize()
    
    # 1. Testing Iceberg Detection (Refresh pattern at same price)
    for i in range(50):
        tick = {
            "price": 50000.0, 
            "volume": 1.0,
            "side": "buy",
            "time_ns": time.time_ns()
        }
        signal = await matrix.ingest_tick(tick)
        
    print(f"\nManipulated: {signal.is_manipulated}, Intent: {signal.metadata['intent']}")
    assert signal.is_manipulated is True
    
    # 2. Testing Dark Flow (Outside spread print)
    tick = {
        "price": 55000.0,
        "volume": 10.0,
        "side": "sell",
        "last_ask": 54900.0, 
        "last_bid": 54890.0,
        "time_ns": time.time_ns()
    }
    signal = await matrix.ingest_tick(tick)
    assert signal.metadata['dark_flow'] == 1.0
    
    await matrix.stop()

@pytest.mark.asyncio
async def test_matrix_wash_trading_veto(matrix):
    """Fase 4: Antifragilidade (Veto de Ruído)."""
    await matrix.initialize()
    
    # Simulating artificial wash trading
    for i in range(200):
        tick = {
            "price": 50000.0,
            "volume": 0.1,
            "side": "buy" if i % 2 == 0 else "sell",
            "time_ns": time.time_ns()
        }
        signal = await matrix.ingest_tick(tick)
        
    print(f"\nWash-Trade Genuinity: {signal.genuinity}")
    # Genuinity should drop significantly due to predictable alternating side
    assert signal.genuinity <= 0.5 
    
    await matrix.stop()

if __name__ == "__main__":
    asyncio.run(test_matrix_signal_phi_convergence(OrderflowMatrix("BTCUSD")))
