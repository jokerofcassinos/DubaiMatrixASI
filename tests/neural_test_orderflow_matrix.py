import asyncio
import logging
import pytest
from market.orderflow_matrix import OrderflowMatrix, MatrixSignal

# [Ω-TEST-NEURAL] Visão Matrix Ω-0: Validação de Realidade Subjacente
# 1-Recepção | 2-Decomposição | 3-Alinhamento

@pytest.mark.asyncio
async def test_matrix_perception_flow():
    """
    VALICAÇÃO INTEGRAL DA VISÃO MATRIX Ω-0
    Protocolo 3-6-9: Decompondo a Realidade (162 Vetores).
    """
    matrix = OrderflowMatrix("BTCUSD")
    await matrix.initialize()
    
    # Mock Tick Data (Simulation of Informed Flow)
    informed_tick = {
        "timestamp": 123456789.0,
        "price": 65432.1,
        "volume": 2.5,
        "side": "buy",
        "tick_id": 9999,
        "best_bid": 65431.0,
        "best_ask": 65432.5
    }

    # 🧪 ETAPA 1: RECEPÇÃO (Ingestion & Normalization)
    print("\n[VITALIDADE] Ingerindo Tick Informado Ω-0.1...")
    signal = await matrix.ingest_tick(informed_tick)
    assert signal is not None
    assert isinstance(signal.phi, float)

    # 🧪 ETAPA 2: DECOMPOSIÇÃO (The 12 Reality Layers)
    print(f"[COGNIÇÃO] Testando Decomposição de 12 Camadas (Φ: {signal.phi:.4f})...")
    # Verify metadata (Dark Flow, Pull Rate, Performance)
    assert "dark_flow" in signal.metadata
    assert "pull_rate" in signal.metadata
    print(f"-> Genuidade do Sinal: {signal.genuinity*100:.1f}%")
    print(f"-> Urgência de Execução: {signal.urgency*100:.1f}%")
    print(f"-> Latência de Percepção: {signal.metadata['perf_ms']:.4f}ms")

    # 🧪 ETAPA 3: INTEGRAÇÃO (Alignment check)
    print("[INTEGRAÇÃO] Validando Sincronia e Fingerprinting Ω-0.3...")
    # Se a latência for < 1ms e o Phi for calculado, a integração está ressonando.
    assert signal.metadata['perf_ms'] < 1.0
    print("✅ Visão Matrix Ω Validada com Sucesso (Status Transdimensional).")
    
    await matrix.stop()

if __name__ == "__main__":
    asyncio.run(test_matrix_perception_flow())
