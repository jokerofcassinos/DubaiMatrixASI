import asyncio
import logging
import msgpack
import time
from typing import Dict, Any, Optional, Deque, List

# [Ω-SOLÉNN] High-Frequency Trading Protocol (HFT-P) Bridge Server
# Protocolo 3-6-9: INFRAESTRUTURA HFT-P (Ω-6.1) — Modo Servidor Soberano

class HFTPBridge:
    """
    [Ω-HFT-P] Institutional Binary Bridge Server (Python <-> MQL5/MetaTrader).
    Operates as the Central Sovereign Server to accept connections from EA Agents.
    Optimized for < 1ms decision-to-wire latency via Proactor I/O.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 9999):
        self.host = host
        self.port = port
        self.logger = logging.getLogger("SOLENN.HFTP")
        
        self._server: Optional[asyncio.AbstractServer] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._reader: Optional[asyncio.StreamReader] = None
        self._is_connected = False
        self._loop_task: Optional[asyncio.Task] = None
        
        # [Ω-BUF] Queues for Asynchronous Messaging
        self._outbound_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._inbound_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        
        # [Ω-MET] Health & Latency Metrics
        self._last_heartbeat = 0.0
        self._reconnect_attempts = 0

    async def connect(self, timeout: float = 600.0) -> bool:
        """
        [Ω-HYPERLISTEN] Actually starts the server and waits for the first connection.
        We keep the 'connect' name for backward compatibility with SolennOmega.
        """
        try:
            self.logger.info(f"📡 [Ω-HFT] Starting HFT-P Sovereign Server on {self.host}:{self.port}...")
            
            self._server = await asyncio.start_server(
                self._handle_client, 
                self.host, 
                self.port
            )
            
            # Start background task to keep server running
            # We wrap the server start in an wait condition for the first connection if we want synchronous boot
            self.logger.info("⏳ [Ω-HFT] Server active. Waiting for MetaTrader 5 Agent to connect...")
            
            # Wait for connection or timeout
            start_time = time.time()
            while not self._is_connected and (time.time() - start_time) < timeout:
                await asyncio.sleep(0.5)
                
            if self._is_connected:
                self.logger.info("✅ [Ω-HFT] Connection established with MT5 Agent.")
                return True
            else:
                self.logger.warning("🕒 [Ω-HFT] Connection TIMEOUT. MetaTrader 5 Agent did not connect.")
                # We return True anyway if server is up? No, return False to signal isolation mode.
                return False
                
        except Exception as e:
            self.logger.error(f"☢️ [Ω-HFT] Server Start FAIL: {e}")
            return False

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Processes incoming connection and handles handshake [Ω-V5.5.9]."""
        if self._is_connected:
            self.logger.warning("🚫 [Ω-HFT] Rejecting second connection attempt. Only 1 Agent supported.")
            writer.close()
            await writer.wait_closed()
            return

        addr = writer.get_extra_info('peername')
        self.logger.info(f"🤝 [Ω-HFT] Incoming connection from {addr}. Handshaking...")

        try:
            # [Ω-HANDSHAKE] Using Unpacker for stream resilience
            unpacker = msgpack.Unpacker()
            data = await asyncio.wait_for(reader.read(4096), timeout=5.0)
            if not data:
                writer.close()
                return

            unpacker.feed(data)
            try:
                # Get first message from stream
                msg = next(unpacker)
                self.logger.info(f"📩 Received Handshake: {msg}")
                
                # Check HELLO or AUTH token
                if msg.get("type") == "HELLO" or msg.get("type") == "HANDSHAKE":
                    # 2. Send AUTHORIZED ack
                    ack = msgpack.packb({"status": "AUTHORIZED", "ts": time.time_ns(), "role": "MASTER"})
                    writer.write(ack)
                    await writer.drain()
                    
                    # 3. Establish Connection
                    self._reader = reader
                    self._writer = writer
                    self._is_connected = True
                    self._loop_task = asyncio.create_task(self._process_loop())
                    self.logger.info("⚡ [Ω-SYNC] HFTP-P Matrix Active & Authorized.")
                else:
                    self.logger.error("🚫 Handshake rejected: Invalid protocol message.")
                    writer.close()
            except Exception as e:
                self.logger.error(f"☢️ [Ω-HFT] Handshake Parse FAIL: {e}")
                writer.close()

        except asyncio.TimeoutError:
            self.logger.error("🚫 Handshake TIMEOUT from client.")
            writer.close()
        except Exception as e:
            self.logger.error(f"☢️ [Ω-HFT] Handle Client fault: {e}")
            writer.close()

    async def submit_order(self, order_packet: Dict[str, Any]):
        """[V1.1.12] Fast-path order submission via async queue."""
        if not self._is_connected:
            self.logger.warning("⚠️ HFTP-P Offline. Order rejected.")
            return False
            
        try:
            payload = msgpack.packb(order_packet)
            await self._outbound_queue.put(payload)
            return True
        except asyncio.QueueFull:
            return False

    async def submit_raw_order(self, data: bytes):
        """[Ω-RAW] Atomic byte submission (Test Mode)."""
        if not self._is_connected: return False
        try:
            await self._outbound_queue.put(data)
            return True
        except: return False

    async def _process_loop(self):
        """[Ω-PROACTOR] Parallel Bi-directional I/O logic (Ω-HFT-P v2.1)."""
        self.logger.info("📡 HFTP-P Dual-Loop: Initializing...")
        try:
            await asyncio.gather(
                self._read_loop(),
                self._write_loop(),
                return_exceptions=True
            )
        except Exception as e:
            self.logger.error(f"☢️ HFTP-P Bridge Global Error: {e}")
        finally:
            self._is_connected = False
            self.logger.warning("⚠️ HFTP-P Proactor Loop: Terminated.")

    async def _read_loop(self):
        """[Ω-INPUT] Dedicated Reader (MT5 -> Master)."""
        unpacker = msgpack.Unpacker()
        pkt_count = 0
        last_report = time.time()
        
        while self._is_connected:
            try:
                data = await self._reader.read(4096)
                if not data:
                    self.logger.warning("⚠️ MT5 Agent closed connection.")
                    break
                
                # Telemetry reporting
                now = time.time()
                if now - last_report > 5.0:
                    if pkt_count > 0:
                        self.logger.info(f"📊 [Ω-TELEMETRY] Incoming traffic: {pkt_count} packets in last 5s.")
                    pkt_count = 0
                    last_report = now
                
                unpacker.feed(data)
                for msg in unpacker:
                    pkt_count += 1
                    if msg.get("type") == "ORDER_ACK":
                        self.logger.info(f"✅ [Ω-OMS] Order ACK Received: {msg}")
                    await self._inbound_queue.put(msg)
                    
            except Exception as e:
                self.logger.error(f"☢️ [Ω-INPUT] Read Fail: {e}")
                break
        self._is_connected = False

    async def _write_loop(self):
        """[Ω-OUTPUT] Dedicated High-Speed Writer (Master -> MT5)."""
        while self._is_connected:
            try:
                # [Ω-1] Get from queue (non-blocking if available)
                payload = await self._outbound_queue.get()
                
                # [Ω-2] Direct Send (Atomic)
                self._writer.write(payload)
                await self._writer.drain()
                
                # [Ω-3] Mark task done
                self._outbound_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"☢️ [Ω-OUTPUT] Write Fail: {e}")
                break
        self._is_connected = False

    async def get_next_response(self) -> Optional[Dict[str, Any]]:
        try:
            return self._inbound_queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

    async def close(self):
        self._is_connected = False
        if self._loop_task:
            self._loop_task.cancel()
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        if self._writer:
            self._writer.close()
        self.logger.info("🌑 HFTP-P Bridge Hibernated.")
