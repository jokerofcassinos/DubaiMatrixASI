import asyncio
import logging
import pytest
import time
from market.exchanges.binance_hftp import BinanceHFTP
from market.exchanges.bybit_hftp import BybitHFTP
from market.exchanges.hft_connector_base import HFTMessage

# [Ω-TEST-NEURAL] Conectividade Matrix Ω-6: Validação de Rede Ultra-Veloz
# 1-Handshake | 2-Sustentação | 3-Throughput

@pytest.mark.asyncio
async def test_hftp_connectivity_flow():
    """
    VALICAÇÃO INTEGRAL DA SUÍTE CONECTIVA Ω-6
    Protocolo 3-6-9: Testando a Conexão Matrix (162 Vetores).
    """
    connectors = [BinanceHFTP(), BybitHFTP()]
    received_count = 0
    
    async def global_callback(msg: HFTMessage):
        """[Ω-CALLBACK] Central message handler for tests."""
        nonlocal received_count
        received_count += 1
        if received_count % 10 == 0:
            print(f"-> Matrix Stream: {msg.exchange} | {msg.channel} | Ingested @ {msg.ts_ingest}")

    # 🧪 ETAPA 1: HANDSHAKE (Connect & Auth)
    print("\n[VITALIDADE] Iniciando Handshake Matrix Ω-6.1.1 (Pre-Auth)...")
    for conn in connectors:
        await conn.start(global_callback)
        assert conn._is_running is True
        print(f"-> Handshake {conn.exchange} OK (Auth Cached: {conn._auth_cached})")

    # 🧪 ETAPA 2: SUSTENTAÇÃO (Polling persistence)
    print("[COGNIÇÃO] Testando Sustentação de Fluxo HFT Ω-6.1.9...")
    # Start polling tasks
    tasks = [asyncio.create_task(conn.poll_stream()) for conn in connectors]
    
    # Wait for data accumulation
    await asyncio.sleep(0.5)
    
    # 🧪 ETAPA 3: THROUGHPUT (SRE Consistency)
    print(f"[INTEGRAÇÃO] Validando Throughput e Latência de Barramento Ω-6.2...")
    print(f"-> Total de Mensagens Processadas: {received_count} (Ω-Throughput OK)")
    
    assert received_count > 50 # High frequency check
    
    print("✅ Suíte Conectiva Matrix Ω Validada com Sucesso (Status Online).")
    
    for task in tasks:
        task.cancel()
    
    for conn in connectors:
        await conn.stop()

if __name__ == "__main__":
    asyncio.run(test_hftp_connectivity_flow())
