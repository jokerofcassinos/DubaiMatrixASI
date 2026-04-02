"""
[Ω-SOLÉNN] Binance HFT-P Connector Ω-6.1 — Matrix Connection (v2.0)
Protocolo 3-6-9: 3 Conceitos | 18 Tópicos | 162 Vetores de Execução

CONCEITO 1: CONNECTION POOLING PERSISTENTE (WebSocket Nativo)
CONCEITO 2: MESSAGE DESERIALIZATION O(1) (JSON Zero-Copy Simulation)
CONCEITO 3: QUEUE BACKPRESSURE & CROSS-EXCHANGE INTELLIGENCE
"""

import asyncio
import json
import logging
import time
from typing import Callable, Optional
from collections import deque
import websockets # O(1) Async WebSocket Library

log = logging.getLogger("SOLENN.BinanceWSS")

class BinanceHFTP:
    """
    [Ω-BINANCE] Conector WSS Assíncrono Nativo.
    Escuta Ticker de `symbol` via Stream Raw e despacha para Callbacks em O(1).
    """
    
    def __init__(self, symbol: str = "btcusdt"):
        self.symbol = symbol.lower()
        self.stream_url = f"wss://stream.binance.com:9443/ws/{self.symbol}@ticker"
        self._is_running = False
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._callbacks = []
        
        # [CONCEITO 3] Circular Ring Buffer Limitado contra Out of Memory
        self._raw_queue = deque(maxlen=5000)

    def register_callback(self, callback: Callable[[dict], None]):
        """ Conecta o Orquestrador ou Data Engine ao fluxo sanguíneo de Ticks. """
        self._callbacks.append(callback)

    async def connect(self):
        """[V1.1.1] Start the WSS Persistent Pool."""
        self._is_running = True
        log.info(f"🌐 [Ω-BINANCE] Arming Sensor Array -> {self.stream_url}")
        
        # Cria a Task independente para re-conexão e ingestão contínua
        asyncio.create_task(self._poll_stream())

    async def disconnect(self):
        self._is_running = False
        if self._ws:
            await self._ws.close()
        log.info("🛑 [Ω-BINANCE] Websocket Stream Severed.")

    async def _poll_stream(self):
        """[Ω-POLL] High Frequency Ingestion Loop com Backoff em falhas."""
        reconnect_delay = 1.0
        
        while self._is_running:
            try:
                log.info(f"🔌 [Ω-BINANCE] Handshaking wss://...")
                async with websockets.connect(self.stream_url) as ws:
                    self._ws = ws
                    log.info(f"✅ [Ω-BINANCE] Connected! Stream `{self.symbol}@ticker` Live.")
                    reconnect_delay = 1.0  # reset on success
                    
                    while self._is_running:
                        # [V1.1.7] Parsing Message O(1)
                        message = await ws.recv()
                        
                        try:
                            data = json.loads(message)
                            # Transformação Estrutural Simplificada da Binance para o Schema da ASI
                            normalized_tick = {
                                "source": "BINANCE",
                                "symbol": self.symbol.upper(),
                                "bid": float(data.get('b', 0.0)),
                                "ask": float(data.get('a', 0.0)),
                                "last": float(data.get('c', 0.0)),
                                "volume": float(data.get('v', 0.0)),
                                "timestamp_ms": data.get('E', int(time.time() * 1000))
                            }
                            
                            self._raw_queue.append(normalized_tick)
                            
                            # Dispara os callbacks cadastrados (O(1) execution path)
                            for cb in self._callbacks:
                                cb(normalized_tick)
                                
                        except json.JSONDecodeError:
                            log.error("☢️ [Ω-BINANCE] Failed Payload Parsing (Corrompido?).")
                            
            except Exception as e:
                log.error(f"☢️ [Ω-BINANCE] Websocket Crash: {e}. Reconnecting in {reconnect_delay}s...")
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, 30.0) # Exponential Backoff Max 30s
