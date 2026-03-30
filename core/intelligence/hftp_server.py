"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              SOLÉNN — HFT-P SERVER Ω (SOVEREIGN PORTAL)                      ║
║     High-Frequency Trading Protocol: Python ↔ MQL5 (MT5)                     ║
║     Implementing: MessagePack Binary, Dual-Channel, AsyncIO                  ║
║     Framework 3-6-9: Phase 4(Ω-21) - Concept 1                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import msgpack
import time
import logging
import uuid
from typing import Dict, Any, Optional, Callable, List, Tuple
from dataclasses import dataclass, field, asdict

# ASI-Grade Constants (Law III.1)
DEFAULT_PORT = 5555
HEARTBEAT_INTERVAL = 1.0  # 1s [Ω-V1.1.5]
MAX_BUFFER_SIZE = 4096 * 4

@dataclass(frozen=True, slots=True)
class HFTMessage:
    """[Ω-V1.1.2] Immutable Binary Message Packet."""
    type: str # TICK, ORDER, RESP, PING
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    msg_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])

class HFTPServer:
    """
    [Ω-CORE] The HFT-P Sovereign Bridge.
    Sustains a low-latency binary tunnel between SOLÉNN and MetaTrader 5.
    """
    _instance: Optional['HFTPServer'] = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(HFTPServer, cls).__new__(cls)
        return cls._instance

    def __init__(self, host: str = "127.0.0.1", port: int = DEFAULT_PORT):
        if hasattr(self, '_initialized'): return
        self.host = host
        self.port = port
        self.logger = logging.getLogger("SOLENN.HFTP")
        
        # [Ω-V1.1.7] Multi-client state
        self._clients: Dict[str, Tuple[asyncio.StreamReader, asyncio.StreamWriter]] = {}
        self._handlers: Dict[str, Callable] = {}
        
        self.is_running = False
        self._initialized = True
        self.logger.info(f"⚡ HFT-P Server Ω Initialized on {host}:{port}")

    def register_handler(self, msg_type: str, handler: Callable):
        """[Ω-V1.2.6] Pub/Sub: Registers a function to handle incoming data."""
        self._handlers[msg_type] = handler

    async def start(self):
        """[Ω-V1.1.1] Launches the asyncio TCP server."""
        self.is_running = True
        server = await asyncio.start_server(self._handle_client, self.host, self.port)
        
        addr = server.sockets[0].getsockname()
        self.logger.info(f"🚀 HFT-P Sovereign Portal listening on {addr}")
        
        # [Ω-V1.1.5] Background Heartbeat Loop
        asyncio.create_task(self._heartbeat_loop())
        
        async with server:
            await server.serve_forever()

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """[Ω-V1.1.3] Manages client connection lifecycle (Dual-channel ready)."""
        client_id = f"CL-{uuid.uuid4().hex[:4]}"
        addr = writer.get_extra_info('peername')
        
        # [Ω-V1.6.3] Socket Tuning for HFT: TCP_NODELAY & Buffers
        sock = writer.get_extra_info('socket')
        if sock:
            import socket
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, MAX_BUFFER_SIZE)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, MAX_BUFFER_SIZE)
            
        self._clients[client_id] = (reader, writer)
        
        self.logger.info(f"🔗 EA Agent Connected: {client_id} from {addr}")
        
        try:
            while self.is_running:
                # [Ω-V1.1.8] Zero-copy buffer read pattern (simulated via reader)
                data = await reader.read(MAX_BUFFER_SIZE)
                if not data:
                    break
                
                # [Ω-V1.1.2] MessagePack Unpacking
                try:
                    raw_msg = msgpack.unpackb(data, raw=False)
                    msg_type = raw_msg.get("type", "UNKNOWN")
                    
                    if msg_type in self._handlers:
                        # [Ω-V1.1.9] Latency monitoring threshold
                        start = time.perf_counter()
                        await self._handlers[msg_type](raw_msg.get("payload"), client_id)
                        elapsed = (time.perf_counter() - start) * 1000
                        if elapsed > 1.0: # 1ms warning
                            self.logger.warning(f"🐢 Handler {msg_type} slow: {elapsed:.3f}ms")
                    
                except Exception as unpack_err:
                    # Fallback for old protocol if needed (optional)
                    self.logger.error(f"❌ Binary Decode Error: {unpack_err}")
                    
        except asyncio.CancelledError:
            pass
        finally:
            self.logger.warning(f"🔌 EA {client_id} Disconnected.")
            if client_id in self._clients:
                del self._clients[client_id]
            writer.close()
            await writer.wait_closed()

    async def send_message(self, client_id: str, msg_type: str, payload: Dict[str, Any]) -> bool:
        """[Ω-V1.3.1] Dispatcher: Sends a MessagePack binary packet to a specific EA."""
        if client_id not in self._clients:
            return False
        
        _, writer = self._clients[client_id]
        msg = {
            "type": msg_type,
            "payload": payload,
            "ts": time.time(),
            "id": uuid.uuid4().hex[:8]
        }
        
        try:
            # [Ω-V1.6.3] Async socket tuning (TCP_NODELAY) logic
            packed = msgpack.packb(msg, use_bin_type=True)
            writer.write(packed)
            await writer.drain()
            return True
        except Exception as e:
            self.logger.error(f"❌ Send Failure to {client_id}: {e}")
            return False

    async def broadcast(self, msg_type: str, payload: Dict[str, Any]):
        """[Ω-V1.1.7] Sends to all active agents (Hydra distribution)."""
        tasks = [self.send_message(cid, msg_type, payload) for cid in self._clients]
        if tasks:
            await asyncio.gather(*tasks)

    async def _heartbeat_loop(self):
        """[Ω-V1.1.5] Constant presence check to maintain tunnel warmth."""
        while self.is_running:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            if self._clients:
                await self.broadcast("PING", {"pulse": time.time()})

    async def stop(self):
        """Graceful shutdown of the sovereign portal."""
        self.is_running = False
        for cid, (reader, writer) in list(self._clients.items()):
            writer.close()
            await writer.wait_closed()
        self._clients.clear()
        self.logger.info("🛑 HFT-P Server Shutdown Complete.")

# --- VAL-Ω: TEST SCRIPT ---
if __name__ == "__main__":
    import threading
    
    async def run_server():
        server = HFTPServer()
        async def on_tick(payload, cid):
            print(f"📈 TICK RECEIVED from {cid}: {payload}")
        
        server.register_handler("TICK", on_tick)
        await server.start()

    async def mock_mql5_client():
        """Simulates an MQL5 Expert Advisor connecting via HFT-P."""
        await asyncio.sleep(1) # Wait for server
        reader, writer = await asyncio.open_connection('127.0.0.1', DEFAULT_PORT)
        print("🔗 MQL5 Simulator Connected.")
        
        # Send a Tick
        tick = {"type": "TICK", "payload": {"symbol": "BTCUSD", "bid": 69000, "ask": 69050}}
        writer.write(msgpack.packb(tick))
        await writer.drain()
        
        # Read PING
        data = await reader.read(1024)
        if data:
            msg = msgpack.unpackb(data)
            print(f"💓 Heartbeat from SOLENN: {msg['type']}")
        
        writer.close()
        await writer.wait_closed()

    # Run both locally for verification
    async def main():
        server_task = asyncio.create_task(run_server())
        client_task = asyncio.create_task(mock_mql5_client())
        await asyncio.gather(client_task)
        # Server keeps running in real app
        
    asyncio.get_event_loop().run_until_complete(main())
