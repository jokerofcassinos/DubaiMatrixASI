import asyncio
import logging
import time
import pytest
import msgpack
from market.data_engine import OmniDataEngine, MarketData
from market.hftp_bridge import HFTPBridge

logging.basicConfig(level=logging.INFO)

# Script Neural OBRIGATÓRIO de Validação - Sensory Synchronization Ω
# FASE 1: Vitalidade
# FASE 2: Cognição
# FASE 3: Integração

@pytest.mark.asyncio
async def test_data_engine_vitality():
    """[FASE 1] Vitalidade do Omni-Data Engine."""
    engine = OmniDataEngine()
    await engine.initialize()
    
    # Simulate routing consumer
    test_data = []
    async def dummy_consumer(data):
        test_data.append(data)
        
    await engine.register_consumer(dummy_consumer)
    
    # Ingest multiple MT5 and Virtual exchange ticks
    await engine.ingest_raw("MT5", {"type": "TICK", "symbol": "BTCUSD", "bid": 60000.0, "vol": 2.0})
    await engine.ingest_raw("MT5", {"type": "TICK", "symbol": "ETHUSD", "bid": 3000.0, "vol": 1.5, "maker": True})
    
    # Wait for queue to process
    await asyncio.sleep(0.1)
    
    assert len(test_data) == 2, "Data Engine não roteou os ticks corretamente."
    assert test_data[0].price == 60000.0
    assert test_data[1].is_maker is True
    
    await engine.stop()

@pytest.mark.asyncio
async def test_hftp_bridge_handshake():
    """[FASE 2] Cognição HFTP-P Handshake e Roteamento."""
    bridge = HFTPBridge(port=19999, order_port=20000, auth_token="TEST_TOKEN")
    
    # Start server
    asyncio.create_task(bridge.connect())
    await asyncio.sleep(0.1)
    
    # Simulate MT5 Client
    reader, writer = await asyncio.open_connection("127.0.0.1", 19999)
    handshake = msgpack.packb({"type": "HELLO", "ver": "MQL5_AGENT_V2", "token": "TEST_TOKEN"})
    writer.write(handshake)
    await writer.drain()
    
    response = await asyncio.wait_for(reader.read(1024), 2.0)
    welcome = msgpack.unpackb(response)
    
    assert welcome.get("type") == "WELCOME", "Handshake falhou ou token rejeitado."
    assert bridge._is_connected is True
    
    writer.close()
    await bridge.close()

@pytest.mark.asyncio
async def test_omni_data_integrity_validation():
    """[FASE 3] Check-Gate Neural Validation."""
    engine = OmniDataEngine()
    await engine.initialize()
    
    # Ingest negative volume (Corrupted Data) -> Should be rejected
    await engine.ingest_raw("MT5", {"type": "TICK", "symbol": "BTCUSD", "bid": 60000.0, "vol": -1.0})
    
    # Ingest duplicate tick -> Should be deduplicated
    await engine.ingest_raw("MT5", {"type": "TICK", "symbol": "BTCUSD", "bid": 60000.0, "vol": 1.0})
    await engine.ingest_raw("MT5", {"type": "TICK", "symbol": "BTCUSD", "bid": 60000.0, "vol": 1.0})
    
    await asyncio.sleep(0.1)
    
    # Metrics check
    assert len(engine._last_processed_ids) == 1, "Deduplicação falhou."
    
    await engine.stop()

if __name__ == "__main__":
    asyncio.run(test_data_engine_vitality())
    asyncio.run(test_hftp_bridge_handshake())
    asyncio.run(test_omni_data_integrity_validation())
    print("✅ TESTE NEURAL SENSORY SYNCHRONIZATION: PASSOU")
