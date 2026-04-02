"""
[TESTE NEURAL: CONEXÃO NATIVA BROKERS V2]
Autenticidade Cross-Exchange Wss & MT5 ThreadPool
"""
import sys
import logging
import asyncio

from market.exchanges.mt5_connector import MetaBridge
from market.exchanges.binance_hftp import BinanceHFTP

# Fake credentials for MT5 local check
MT5_LOGIN = 1512930277
MT5_PASS = "w31?MRh*M@y"
MT5_SERVER = "FTMO-Demo"

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(name)s | %(message)s')
log = logging.getLogger("TestBrokerIntegrity")

async def run_brokers_test():
    log.info("--- STARTING NEURAL TEST FOR BROKER BRIDGES ---")

    # 1. MT5 BRIDGE INSTANTIATION
    mt5_bridge = MetaBridge(MT5_LOGIN, MT5_PASS, MT5_SERVER)
    log.info("1. MetaTrader5 Bridge Instantiated (ThreadPool Activated).")
    
    # Tentativa de inicialização asincrona
    mt5_status = await mt5_bridge.initialize()
    if mt5_status:
        log.info(f"-> MT5 Initialized successfully! Sync loop running in background.")
    else:
        log.warning(f"-> MT5 could not connect (Terminal may be closed or wrong credentials). Controlled Failure expected.")

    # 2. BINANCE WSS INSTANTIATION
    binance = BinanceHFTP(symbol="btcusdt")
    
    # Dummy Callback function
    ticks_received = []
    def on_tick(tick_data):
        ticks_received.append(tick_data)

    binance.register_callback(on_tick)
    await binance.connect()

    log.info("2. Binance Websocket Poller Fired.")
    log.info("-> Waiting 4 seconds for Ticks to Arrive from Binance WSS...")
    
    await asyncio.sleep(4.0)

    # 3. VERIFICATION
    if len(ticks_received) > 0:
        log.info(f"✅ SUCCESS: Recieved {len(ticks_received)} frames from Binance on btcusdt@ticker.")
        log.info(f"Sample Frame: {ticks_received[-1]}")
    else:
        log.error("☢️ FAILURE: No frames received from Binance!")

    # 4. TEARDOWN
    log.info("Shutting down bridges...")
    await binance.disconnect()
    await mt5_bridge.stop()
    log.info("Done.")

if __name__ == "__main__":
    asyncio.run(run_brokers_test())
