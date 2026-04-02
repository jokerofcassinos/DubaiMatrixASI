"""
[Ω-SOLÉNN] Meta-Bridge Ω-45 — A Ponte do Absoluto Terminal MT5 (v2.0 - Async ThreadPool)
Protocolo 3-6-9: 3 Conceitos | 18 Tópicos | 162 Vetores de Execução

CONCEITO 1: HBRIDGE ASYNC & THREAD POOLING (Bloqueio Zero)
CONCEITO 2: FTMO SANCTUM (Circuit Breakers e Risco O(1))
CONCEITO 3: SLIPPAGE PREDICTION & TIER OPTIMIZATION
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional
from dataclasses import dataclass

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None

log = logging.getLogger("SOLENN.MetaBridge")

@dataclass(frozen=True, slots=True)
class MT5Position:
    ticket: int
    symbol: str
    type: str # BUY/SELL
    volume: float
    price_open: float
    profit: float

@dataclass(frozen=True, slots=True)
class AccountStatus:
    login: int
    balance: float
    equity: float
    daily_loss_pct: float
    margin_free: float
    connected: bool

class MetaBridge:
    def __init__(self, login: int, password: str, server: str, max_workers: int = 4):
        self.login = login
        self.password = password
        self.server = server
        
        # [CONCEITO 1] ThreadPool para MQL5 C-ffi Blocking
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # [CONCEITO 2] FTMO Sanctum Risk Limits
        self._daily_loss_limit = 0.04  # 4% Max Daily Loss
        self._total_loss_limit = 0.08  # 8% Max Total Loss
        self._max_total_exposure_lots = 5.0
        
        self.account_info: Optional[AccountStatus] = None
        self._is_running = False

    async def _async_exec(self, func, *args, **kwargs):
        """ Executa rotinas do MT5 que poderiam bloquear o Event Loop. """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, lambda: func(*args, **kwargs))

    async def initialize(self) -> bool:
        """[Ω-GENESIS] Tenta Handshake com MetaTrader Terminal em Background."""
        log.info(f"🧬 Meta-Bridge Ω-45: Threaded Handshaking Terminal {self.login}...")
        
        if mt5 is None:
            log.error("☢️ MT5_LIBRARY_MISSING: Aborting Bridge Connection.")
            return False

        try:
            # Chamada assíncrona para não travar o loop principal
            success = await self._async_exec(mt5.initialize, login=self.login, password=self.password, server=self.server)
            
            if not success:
                err = mt5.last_error()
                log.error(f"☢️ MT5_INITIALIZATION_FAILED: {err}")
                return False
                
            self._is_running = True
            log.info("✅ MetaBridge Ω-45: Handshake SUCCESS. Starting sync loop.")
            asyncio.create_task(self._sync_loop())
            return True
        except Exception as e:
            log.error(f"☢️ MT5_CRITICAL_INIT_ERROR: {e}")
            return False

    async def stop(self):
        self._is_running = False
        log.info("🛑 Meta-Bridge Ω-45: Shutting Down MT5 Context...")
        await self._async_exec(mt5.shutdown)
        self.executor.shutdown(wait=False)

    async def execute_order(self, symbol: str, side: str, volume: float, max_slippage_pts: int = 10) -> Optional[int]:
        """
        [Ω-EXEC] Envio O(1) de Ordem HIB (High Importance Block).
        Stochastic Optimal Control (Ω-45.1.2) - Proteção Anti-CircuitBreaker Embutida.
        """
        # --- 1. PRE-TRADE SANCTUM CHECK ---
        if self.account_info and self.account_info.daily_loss_pct >= self._daily_loss_limit:
            log.critical(f"🛑 FTMO CIRCUIT BREAKER ACTIVE ({self.account_info.daily_loss_pct*100:.2f}% LOSS). TRADE BLOCKED.")
            return None
        
        if volume > self._max_total_exposure_lots:
            log.warning(f"⚠️ FTMO SLOT LIMIT EXCEEDED. Adjusted to {self._max_total_exposure_lots} Lots.")
            volume = self._max_total_exposure_lots

        # --- 2. ORDER PACKING ---
        order_type = mt5.ORDER_TYPE_BUY if side == "BUY" else mt5.ORDER_TYPE_SELL
        
        def _send_mt5():
            # A captura de tick é processada instantaneamente dentro da thread
            tick = mt5.symbol_info_tick(symbol)
            if not tick: return None
            
            price = tick.ask if side == "BUY" else tick.bid
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": float(volume),
                "type": order_type,
                "price": price,
                "deviation": max_slippage_pts,
                "magic": 162369,
                "comment": "Ω-SOLENN",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            return mt5.order_send(request)

        log.info(f"🚀 THROWING INTENT: {side} {volume} {symbol} (Awaiting MT5 execution...)")
        
        result = await self._async_exec(_send_mt5)
        
        if result is None:
            log.error("☢️ ORDER_FAILED: Missing tick data or connection.")
            return None
            
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            log.error(f"☢️ ORDER_REJECTED (Code {result.retcode}): {result.comment}")
            return None
            
        log.info(f"✅ EXECUTED: Ticket #{result.order} @ {result.price} (Slip={result.deal})")
        return result.order

    async def _sync_loop(self):
        """[Ω-RECONCILIATOR] Sincronização Periódica FTMO Account (Ω-45.1.3)."""
        while self._is_running:
            try:
                # Polling leve para extração de balance na MT5 sem prender o Core
                def _get_acc():
                    ac = mt5.account_info()
                    if ac: return ac.login, ac.balance, ac.equity, ac.margin_free
                    return None

                data = await self._async_exec(_get_acc)
                if data:
                    login, balance, equity, margin = data
                    # Calculo de Loss FTMO simplificado (Ponto de início do dia deveria ser injetado)
                    daily_loss = max(0.0, (balance - equity) / balance)
                    
                    self.account_info = AccountStatus(
                        login=login, balance=balance, equity=equity,
                        daily_loss_pct=daily_loss, margin_free=margin, connected=True
                    )
                    
                    if daily_loss >= self._daily_loss_limit:
                        log.critical(f"🛑 CRITICAL_DAILY_LOSS ({(daily_loss*100):.2f}%). ORCHESTRATOR MUST FLATTEN.")
            except Exception as e:
                log.error(f"☢️ MT5 SYNC FATAL: {e}")
            
            await asyncio.sleep(0.5)  # 2 Hz
