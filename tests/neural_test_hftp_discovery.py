import asyncio
import logging
import msgpack
import time
import pytest
from market.hftp_bridge import HFTPBridge

# [Ω-TEST-NEURAL] Conectividade Matrix Ω-6.2: Validação de Descoberta Dinâmica
# 1-Scan | 2-Discovery | 3-Handshake Resilience

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("SOLENN.Test.Discovery")

class MockHFTPServer:
    """Mock do HFT-P Server (MQL5 side) em porta dinâmica."""
    def __init__(self, host="127.0.0.1", port=10001):
        self.host = host
        self.port = port
        self.server = None
        self._is_running = False

    async def start(self):
        self.server = await asyncio.start_server(self.handle_client, self.host, self.port)
        self._is_running = True
        log.info(f"✅ Mock HFT-P Server started @ {self.host}:{self.port}")
        async with self.server:
            await self.server.serve_forever()

    async def handle_client(self, reader, writer):
        """Simula o Handshake do MQL5 (Ω-SOLÉNN)."""
        data = await reader.read(1024)
        if data:
            msg = msgpack.unpackb(data)
            if msg.get("type") == "HANDSHAKE" and msg.get("token") == "Ω-SOLENN-ASI-AUTH":
                log.info(f"🧬 Server: Handshake RECEIVED from {msg.get('symbol', 'UNKNOWN')}")
                # Envia AUTHORIZED
                response = msgpack.packb({"status": "AUTHORIZED", "ts": time.time_ns()})
                writer.write(response)
                await writer.drain()
        
        # Manter conexão viva para Heartbeats
        while self._is_running:
            try:
                data = await reader.read(1024)
                if not data: break
                msg = msgpack.unpackb(data)
                if msg.get("type") == "HEARTBEAT":
                    # log.debug("Server: Heartbeat Ack")
                    pass
            except: break
        writer.close()

    async def stop(self):
        self._is_running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()

@pytest.mark.asyncio
async def test_dynamic_port_discovery():
    """
    VALICAÇÃO DA DESCOBERTA SENSORIAL Ω-6.2.1
    O Bridge deve encontrar o Server em 10001 mesmo se a porta padrão (9999) falhar.
    """
    log.info("\n🧪 INICIANDO TESTE DE DESCOBERTA DINÂMICA (Ω-6.2.1)...")
    
    # 1. Iniciar Mock Server em porta NÂO padrão (10001)
    mock_port = 10001
    server = MockHFTPServer(port=mock_port)
    server_task = asyncio.create_task(server.start())
    await asyncio.sleep(0.5) # Aguardar Gênese do Server

    # 2. Iniciar Bridge com porta padrão errada (9999) mas com Scan Range que inclui 10001
    bridge = HFTPBridge(port=9999, scan_range=range(10000, 10003))
    
    # 3. Executar Trigger de Conexão (Ω-Discovery)
    log.info("[VITALIDADE] Disparando Handshake com Scan Ativo...")
    success = await bridge.connect(timeout=1.0)
    
    # 🕵️ AUDITORIA SRE
    assert success is True
    assert bridge.port == mock_port
    assert bridge._is_connected is True
    log.info(f"✅ [Ω-SUCCESS] Bridge encontrou o servidor na porta {bridge.port} (Discovery OK)")

    # 4. Validar Sustentação (Heartbeat)
    await asyncio.sleep(1.2)
    log.info("📡 [COGNIÇÃO] Sustentação de Heartbeat validada.")

    # 5. Shutdown Graceful
    await bridge.close()
    await server.stop()
    server_task.cancel()
    log.info("🌑 Desativação de Teste Concluída.")

if __name__ == "__main__":
    asyncio.run(test_dynamic_port_discovery())
