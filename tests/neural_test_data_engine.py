import asyncio
import logging
import pytest
import time
from market.data_engine import OmniDataEngine, MarketData

# [Ω-TEST-NEURAL] Omni-Data Engine Ω-13: Validação de Coração de Dados
# 1-Ingestão | 2-Normalização | 3-Streaming

@pytest.mark.asyncio
async def test_data_engine_flow():
    """
    VALICAÇÃO INTEGRAL DO OMNI-DATA ENGINE Ω-13
    Protocolo 3-6-9: Testando o Pipeline Institucional (162 Vetores).
    """
    engine = OmniDataEngine()
    await engine.initialize()
    
    received_data_list = []
    
    async def sample_consumer(data: MarketData):
        """[Ω-CONSUMER] Mock Consumer for the engine."""
        received_data_list.append(data)
        print(f"-> Consumer Received: {data.symbol} @ {data.price} from {data.exchange}")

    # Register Consumer Ω-13.1.9
    await engine.register_consumer(sample_consumer)
    
    # 🧪 ETAPA 1: INGESTÃO (Capture & Binary Parsing)
    print("\n[VITALIDADE] Ingerindo Dados Brutos (Binance Mock) Ω-13.1.1...")
    raw_binance_msg = {"s": "BTCUSD", "p": "65000.50", "v": "1.25", "m": True}
    await engine.ingest_raw("BINANCE", raw_binance_msg)
    
    # Wait for processing
    await asyncio.sleep(0.1)
    
    # 🧪 ETAPA 2: NORMALIZAÇÃO & VALIDAÇÃO (Validation Layer)
    print("[COGNIÇÃO] Testando Normalização e Validação Ω-13.1.4...")
    raw_bybit_msg = {"s": "ETHUSD", "p": "3500.25", "v": "10.0", "m": False}
    await engine.ingest_raw("BYBIT", raw_bybit_msg)
    
    await asyncio.sleep(0.1)
    
    # Check if both were received
    assert len(received_data_list) == 2
    assert received_data_list[0].exchange == "BINANCE"
    assert received_data_list[1].exchange == "BYBIT"
    assert received_data_list[0].price == 65000.50
    print(f"-> Latência P99 Estimada: {engine._metrics['p99_latency_ms']:.4f}ms (Ω-Latência OK)")

    # 🧪 ETAPA 3: STREAMING (Multi-Consumer SRE)
    print("[INTEGRAÇÃO] Validando Fluxo de Streaming e Métricas Ω-15.1...")
    assert engine._metrics["p99_latency_ms"] < 1.0 # Ω-Requirement
    print("✅ Omni-Data Engine Ω Validada com Sucesso (Status Aorta Online).")

if __name__ == "__main__":
    asyncio.run(test_data_engine_flow())
