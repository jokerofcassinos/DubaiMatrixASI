"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — MT5 BRIDGE                            ║
║        Interface direta com MetaTrader 5 — Conexão, Dados, Ordens          ║
║                                                                              ║
║  Esta é a PONTE entre a ASI e o mercado real.                               ║
║  Cada milissegundo de latência aqui = dinheiro perdido.                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import time
import socket
import threading
import numpy as np
from datetime import datetime, timezone
from typing import Optional, Dict, List, Tuple
from collections import deque

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None

from config.exchange_config import (
    MT5_LOGIN, MT5_PASSWORD, MT5_SERVER, MT5_PATH, MT5_TIMEOUT_MS,
    SYMBOL, SYMBOL_ALIASES, TIMEFRAMES, BARS_TO_LOAD,
    MAGIC_NUMBER, ORDER_DEVIATION, ORDER_FILLING_TYPE,
    MAX_OPEN_POSITIONS, MAX_LOT_SIZE, MIN_LOT_SIZE
)
from utils.logger import log
from utils.decorators import retry, timed, CircuitBreaker, catch_and_log


class MT5Bridge:
    """
    Ponte ASI ↔ MetaTrader 5.
    Responsabilidades:
    - Conexão/desconexão com o terminal MT5
    - Streaming de ticks e candles em tempo real
    - Envio de ordens (market, limit, stop)
    - Consulta de posições, histórico, account info
    - Gestão de erros e retry automático
    """

    def __init__(self):
        self.connected = False
        self.symbol = SYMBOL
        self.symbol_info = None
        self.account_info = None
        self.tick_buffer = deque(maxlen=10000)  # Buffer circular de ticks
        self._last_tick_time = 0
        self._circuit = CircuitBreaker(
            failure_threshold=10,
            recovery_timeout_sec=30,
            name="MT5Bridge"
        )
        
        # ═══ HFT SOCKET BRIDGE ═══
        self.socket_port = 5555
        self.server_socket = None
        self.client_socket = None
        self.socket_thread = None
        self._socket_running = False
        self._last_socket_tick = None
        self._ea_connected = False

    # ═══════════════════════════════════════════════════════════
    #  CONEXÃO
    # ═══════════════════════════════════════════════════════════

    @retry(max_attempts=5, delay_ms=1000)
    def connect(self, login: int = None, password: str = None,
                server: str = None, path: str = None) -> bool:
        """
        Conecta ao terminal MT5.
        Tenta múltiplas vezes com backoff — a ASI NUNCA desiste.
        """
        if mt5 is None:
            log.critical("❌ MetaTrader5 package não instalado! pip install MetaTrader5")
            return False

        # Usar params ou config
        _login = login or MT5_LOGIN
        _password = password or MT5_PASSWORD
        _server = server or MT5_SERVER
        _path = path or MT5_PATH

        # Inicializar MT5
        init_kwargs = {}
        if _path:
            init_kwargs["path"] = _path
        if _login:
            init_kwargs["login"] = int(_login)
        if _password:
            init_kwargs["password"] = str(_password)
        if _server:
            init_kwargs["server"] = str(_server)
        if MT5_TIMEOUT_MS:
            init_kwargs["timeout"] = MT5_TIMEOUT_MS

        if not mt5.initialize(**init_kwargs):
            error = mt5.last_error()
            log.error(f"❌ MT5 initialize falhou: {error}")
            return False

        # Verificar conexão
        terminal_info = mt5.terminal_info()
        if terminal_info is None:
            log.error("❌ Não foi possível obter info do terminal MT5")
            return False

        # Verificar símbolo
        self.symbol_info = self._resolve_symbol()
        if self.symbol_info is None:
            log.error(f"❌ Símbolo {SYMBOL} não encontrado no broker!")
            return False

        # Habilitar símbolo para trading
        if not self.symbol_info.visible:
            if not mt5.symbol_select(self.symbol, True):
                log.error(f"❌ Não foi possível habilitar {self.symbol}")
                return False

        # Account info
        self.account_info = mt5.account_info()
        if self.account_info is None:
            log.error("❌ Não foi possível obter info da conta")
            return False

        self.connected = True

        log.omega(f"🔗 MT5 CONECTADO!")
        log.info(f"   Terminal: {terminal_info.name}")
        log.info(f"   Conta: {self.account_info.login}")
        log.info(f"   Servidor: {self.account_info.server}")
        log.info(f"   Saldo: ${self.account_info.balance:.2f}")
        log.info(f"   Leverage: 1:{self.account_info.leverage}")
        log.info(f"   Símbolo: {self.symbol}")
        log.info(f"   Spread: {self.symbol_info.spread} points")

        # Iniciar servidor Socket para o EA
        self._start_socket_server()

        return True

    def _start_socket_server(self):
        """Inicializa servidor TCP para comunicação com MQL5 EA."""
        if self._socket_running:
            return
            
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Reusar endereço para evitar erro de 'port in use' após restart rápido
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(("127.0.0.1", self.socket_port))
            self.server_socket.listen(1)
            self.server_socket.settimeout(1.0)
            
            self._socket_running = True
            self.socket_thread = threading.Thread(target=self._socket_worker, daemon=True)
            self.socket_thread.start()
            log.omega(f"✅ ASI TCP Server Online na porta {self.socket_port}")
        except Exception as e:
            log.error(f"❌ Falha ao iniciar Servidor TCP: {e}")

    def _socket_worker(self):
        """Worker thread que gerencia a conexão e dados do EA."""
        while self._socket_running:
            if not self.client_socket:
                try:
                    conn, addr = self.server_socket.accept()
                    self.client_socket = conn
                    self._ea_connected = True
                    self._socket_buffer = ""  # Limpa o buffer a cada nova conexão
                    log.omega(f"✅ Expert Advisor Conectado via Socket: {addr}")
                except socket.timeout:
                    continue
                except Exception as e:
                    if self._socket_running:
                        log.error(f"Erro ao aceitar conexão socket: {e}")
                    continue

            try:
                self.client_socket.settimeout(1.0)
                # Socket needs a small timeout so the while loop checks self._socket_running
                raw_data = self.client_socket.recv(4096)
                if not raw_data: # Conexão fechada pelo EA
                    log.warning("⚠️ Socket EA desconectado (Graceful Close).")
                    self.client_socket.close()
                    self.client_socket = None
                    self._ea_connected = False
                    continue
                
                data = raw_data.decode('utf-8')
                self._socket_buffer += data
                
                # TCP Streaming buffer parser
                while '\n' in self._socket_buffer:
                    line, self._socket_buffer = self._socket_buffer.split('\n', 1)
                    if line.strip():
                        self._handle_socket_data(line)
                
            except socket.timeout:
                continue
            except ConnectionResetError:
                log.warning("⚠️ Socket resetado pela contraparte (MT5/EA).")
                self._ea_connected = False
                self.client_socket = None
            except Exception as e:
                if self._socket_running:
                    log.error(f"❌ Erro no streaming do socket: {e}")
                    if self.client_socket:
                        self.client_socket.close()
                    self.client_socket = None
                    self._ea_connected = False
                # [Phase 49] Backoff reduzido para HFT Reconnect
                time.sleep(0.5) 

    def _handle_socket_data(self, data: str):
        """Processa ticks e resultados vindos do EA via socket. Assume 'data' como uma linha única sem '\n'."""
        line = data.strip()
        if not line: return
        
        parts = line.split('|')
        if not parts: return
        
        msg_type = parts[0]
        
        if msg_type == "TICK":
            # Formato: TICK|SYMBOL|BID|ASK|LAST|VOL|MSC
            if len(parts) < 7: return
            symbol = parts[1]
            if symbol != self.symbol: return
                
            tick_data = {
                "time": int(time.time()),
                "bid": float(parts[2]),
                "ask": float(parts[3]),
                "last": float(parts[4]),
                "volume": float(parts[5]),
                "spread": float(parts[3]) - float(parts[2]),
                "mid": (float(parts[2]) + float(parts[3])) / 2,
                "time_msc": int(parts[6]),
                "source": "hft_socket"
            }
            self._last_socket_tick = tick_data
            self.tick_buffer.append(tick_data)

        elif msg_type == "RESULT":
            # Formato: RESULT|ACTION|STATUS|TICKET|PRICE
            action = parts[1]
            status = parts[2]
            log.info(f"📩 Resposta EA Socket: {action} -> {status} | Data: {line}")
            
            if action == "LIMIT" and status == "SUCCESS":
                ticket = parts[3]
                price = parts[4]
                log.omega(f"🎯 LIMIT EXECUTADO: Ticket {ticket} @ {price}")
            elif action == "SONAR":
                log.info(f"📡 SONAR PROBE RESULT: {status}")

        elif msg_type == "PONG":
            pass

    def send_socket_command(self, cmd: str):
        """Envia comando de trading diretamente para o EA via socket."""
        if not self.client_socket or not self._ea_connected:
            return False
            
        try:
            msg = cmd + "\n"
            self.client_socket.sendall(msg.encode('utf-8'))
            return True
        except Exception as e:
            log.error(f"Erro ao enviar comando socket: {e}")
            self._ea_connected = False
            self.client_socket = None
            return False

    def disconnect(self):
        """Desconecta do MT5 gracefully."""
        self._socket_running = False
        if self.client_socket:
            self.client_socket.close()
        if self.server_socket:
            self.server_socket.close()
            
        if mt5 is not None:
            mt5.shutdown()
        self.connected = False
        log.omega("🔌 MT5 DESCONECTADO")

    def _resolve_symbol(self):
        """Tenta encontrar o símbolo correto (brokers usam nomes diferentes)."""
        for alias in SYMBOL_ALIASES:
            info = mt5.symbol_info(alias)
            if info is not None:
                self.symbol = alias
                log.info(f"   Símbolo resolvido: {alias}")
                return info
        return None

    # ═══════════════════════════════════════════════════════════
    #  DADOS DE MERCADO
    # ═══════════════════════════════════════════════════════════

    @timed(log_threshold_ms=50)
    def get_closed_deals(self, from_date: datetime) -> List[dict]:
        """
        Busca negócios (deals) fechados desde uma data específica.
        Essencial para o Consciousness Feedback Loop.
        """
        if not self.connected:
            return []

        # MT5 lida melhor com timestamps float (epoch)
        from_timestamp = int(from_date.timestamp())
        to_timestamp = int(time.time())

        deals = mt5.history_deals_get(from_timestamp, to_timestamp)
        if deals is None:
            err = mt5.last_error()
            log.error(f"❌ Erro ao buscar histórico MT5: {err}")
            return []

        if len(deals) == 0:
            return []

        results = []
        for d in deals:
            # Filtramos apenas deals que fecham posições (entry out) 
            # ou que são de lucro/perda real (excluindo balanço/créditos se houver)
            if d.entry in [1, 2, 3]: # 1=OUT, 2=INOUT, 3=OUT_BY
                results.append({
                    "ticket": d.order,
                    "position": d.position_id,
                    "symbol": d.symbol,
                    "type": "BUY" if d.type == 1 else "SELL", # Note: No deal, type 1=SELL(out of buy), 0=BUY
                    # No Deal: 1=Sell side (close buy), 0=Buy side (close sell)
                    "direction": "SELL" if d.type == 1 else "BUY",
                    "volume": d.volume,
                    "price": d.price,
                    "profit": d.profit,
                    "commission": d.commission,
                    "swap": d.swap,
                    "time": datetime.fromtimestamp(d.time, tz=timezone.utc).isoformat(),
                    "comment": d.comment
                })
        
        return results

    def get_tick(self) -> Optional[dict]:
        """Obtém o tick mais recente (preferência para HFT Socket)."""
        if not self.connected:
            return None

        # Tentar pegar o tick do socket primeiro (Latência menor)
        if self._last_socket_tick:
            tick = self._last_socket_tick
            self._last_socket_tick = None # Consumido
            return tick

        # Fallback para API oficial
        tick = mt5.symbol_info_tick(self.symbol)
        if tick is None:
            return None

        tick_data = {
            "time": tick.time,
            "bid": tick.bid,
            "ask": tick.ask,
            "last": tick.last,
            "volume": tick.volume,
            "spread": tick.ask - tick.bid,
            "mid": (tick.bid + tick.ask) / 2,
            "time_msc": tick.time_msc,
            "source": "mt5_api"
        }

        # Adicionar ao buffer
        self.tick_buffer.append(tick_data)
        self._last_tick_time = tick.time_msc

        return tick_data

    @timed(log_threshold_ms=100)
    def get_candles(self, timeframe: str = "M1",
                    count: int = None) -> Optional[np.ndarray]:
        """
        Obtém candles (OHLCV) do timeframe especificado.
        Retorna numpy structured array para performance.
        """
        if not self.connected:
            return None

        tf_code = TIMEFRAMES.get(timeframe)
        if tf_code is None:
            log.error(f"Timeframe desconhecido: {timeframe}")
            return None

        bars_count = count or BARS_TO_LOAD.get(timeframe, 500)

        rates = mt5.copy_rates_from_pos(self.symbol, tf_code, 0, bars_count)
        if rates is None or len(rates) == 0:
            log.warning(f"Sem dados para {self.symbol} {timeframe}")
            return None

        return rates

    def get_candles_as_dict(self, timeframe: str = "M1",
                            count: int = None) -> Optional[dict]:
        """
        Retorna candles como dicionário de arrays numpy.
        Formato amigável para os agentes neurais.
        """
        rates = self.get_candles(timeframe, count)
        if rates is None:
            return None

        return {
            "time":   np.array([r[0] for r in rates]),
            "open":   np.array([r[1] for r in rates], dtype=np.float64),
            "high":   np.array([r[2] for r in rates], dtype=np.float64),
            "low":    np.array([r[3] for r in rates], dtype=np.float64),
            "close":  np.array([r[4] for r in rates], dtype=np.float64),
            "tick_volume": np.array([r[5] for r in rates], dtype=np.float64),
            "spread": np.array([r[6] for r in rates]),
            "real_volume": np.array([r[7] for r in rates], dtype=np.float64),
        }

    @timed(log_threshold_ms=100)
    def get_book(self, depth: int = 20) -> Optional[dict]:
        """
        Obtém book de ofertas (DOM — Depth of Market).
        Essencial para microestrutura e order flow analysis.
        """
        if not self.connected:
            return None

        # Subscrever ao book (necessário no MT5)
        if not mt5.market_book_add(self.symbol):
            return None

        book = mt5.market_book_get(self.symbol)
        if book is None or len(book) == 0:
            return None

        bids = []
        asks = []

        for entry in book:
            item = {
                "price": entry.price,
                "volume": entry.volume,
                "volume_real": getattr(entry, 'volume_dbl', entry.volume), # MT5 BookInfo uses volume_dbl or volume
            }
            if entry.type == mt5.BOOK_TYPE_SELL:
                asks.append(item)
            elif entry.type == mt5.BOOK_TYPE_BUY:
                bids.append(item)

        return {
            "bids": bids[:depth],
            "asks": asks[:depth],
            "bid_total": sum(b["volume"] for b in bids),
            "ask_total": sum(a["volume"] for a in asks),
            "imbalance": 0.0,  # Calculado pelo OrderFlowMatrix
        }

    def get_ticks_range(self, seconds_back: int = 60) -> Optional[list]:
        """Obtém ticks dos últimos N segundos para análise tick-by-tick."""
        if not self.connected:
            return None

        from_time = datetime.now(timezone.utc)
        from_time = from_time.replace(
            second=from_time.second - seconds_back if from_time.second >= seconds_back
            else 0
        )

        ticks = mt5.copy_ticks_from(
            self.symbol, from_time,
            seconds_back * 100,  # Estimativa de ticks
            mt5.COPY_TICKS_ALL
        )

        if ticks is None or len(ticks) == 0:
            return None

        return [
            {
                "time": t[0], "bid": t[1], "ask": t[2],
                "last": t[3], "volume": t[4], "flags": t[6]
            }
            for t in ticks
        ]

    # ═══════════════════════════════════════════════════════════
    #  ACCOUNT INFO
    # ═══════════════════════════════════════════════════════════

    def get_account_info(self) -> Optional[dict]:
        """Informações da conta em tempo real."""
        if not self.connected:
            return None

        info = mt5.account_info()
        if info is None:
            return None

        return {
            "balance": info.balance,
            "equity": info.equity,
            "margin": info.margin,
            "free_margin": info.margin_free,
            "margin_level": info.margin_level,
            "profit": info.profit,
            "leverage": info.leverage,
            "currency": info.currency,
        }

    def get_symbol_info(self) -> Optional[dict]:
        """Info detalhada do símbolo."""
        if not self.connected:
            return None

        info = mt5.symbol_info(self.symbol)
        if info is None:
            return None

        return {
            "bid": info.bid,
            "ask": info.ask,
            "spread": info.spread,
            "point": info.point,
            "digits": info.digits,
            "volume_min": info.volume_min,
            "volume_max": info.volume_max,
            "volume_step": info.volume_step,
            "trade_contract_size": info.trade_contract_size,
            "swap_long": info.swap_long,
            "swap_short": info.swap_short,
        }

    @retry(max_attempts=3, delay_ms=500)
    def calculate_margin(self, action: str, lot: float, price: float) -> Optional[float]:
        """
        Calcula a margem exigida para uma ordem proposta.
        Útil para validação pré-trade.
        """
        if not self.connected:
            return None

        order_type = mt5.ORDER_TYPE_BUY if action.upper() == "BUY" else mt5.ORDER_TYPE_SELL
        margin = mt5.order_calc_margin(order_type, self.symbol, lot, price)
        
        if margin is None:
            err = mt5.last_error()
            log.error(f"❌ Falha ao calcular margem para {action} {lot} @ {price}: {err}")
            return None

        return margin

    # ═══════════════════════════════════════════════════════════
    #  ENVIO DE ORDENS
    # ═══════════════════════════════════════════════════════════

    @timed(log_threshold_ms=200)
    def send_limit_order(self, action: str, lot: float,
                          sl: float = 0.0, tp: float = 0.0,
                          comment: str = "ASI_LIMIT", magic: int = None,
                          price: float = None) -> Optional[dict]:
        """
        [Phase Ω-Eternity] Envia ordem Limit para Market Making Quântico.
        Pega a liquidez do spread e evita slippage cobrando do Varejo.
        """
        if not self.connected or price is None:
            log.error("❌ MT5 não conectado ou Preço não fornecido para LIMIT")
            return None

        # Validar lot size
        lot = max(MIN_LOT_SIZE, min(MAX_LOT_SIZE, round(lot, 2)))

        order_type = mt5.ORDER_TYPE_BUY_LIMIT if action.upper() == "BUY" else mt5.ORDER_TYPE_SELL_LIMIT

        request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": self.symbol,
            "volume": lot,
            "type": order_type,
            "price": price,
            "deviation": ORDER_DEVIATION,
            "magic": magic or MAGIC_NUMBER,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_RETURN,
        }

        if sl > 0:
            request["sl"] = sl
        if tp > 0:
            request["tp"] = tp

        # [Phase Ω-Speed] Port to HFT Socket Bridge
        # Command format: "LIMIT|ACTION|SYMBOL|LOT|PRICE|SL|TP"
        cmd = f"LIMIT|{action.upper()}|{self.symbol}|{lot:.2f}|{price:.5f}|{sl:.5f}|{tp:.5f}"
        
        if self._ea_connected and self.send_socket_command(cmd):
            log.omega(f"⚡ FAST LIMIT SINALIZADO: {action} {lot} @ {price:.2f} (via socket)")
            return {
                "success": True,
                "ticket": 0, # Async result
                "price": price,
                "volume": lot,
                "action": action,
                "status": "PENDING_LIMIT_SIGNALED"
            }

        # Fallback to slow Native API
        log.warning(f"⚠️ Socket indisponível para LIMIT. Usando fallback API Python (Lento).")
        result = mt5.order_send(request)

        if result is None:
            log.error(f"❌ Falha ao enviar limit order (None): {mt5.last_error()}")
            return None

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            log.error(f"❌ Falha ao executar limit order: {result.comment} (Code: {result.retcode})")
            return None

        return {
            "success": True,
            "ticket": result.order,
            "price": result.price,
            "volume": result.volume,
            "action": action,
            "status": "PENDING_LIMIT"
        }

    @timed(log_threshold_ms=200)
    def cancel_pending_order(self, ticket: int) -> bool:
        """Cancela uma Limit/Stop order pendente."""
        if not self.connected:
            return False

        request = {
            "action": mt5.TRADE_ACTION_REMOVE,
            "order": ticket
        }
        
        result = mt5.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            return True
        return False

    @timed(log_threshold_ms=200)
    def send_market_order(self, action: str, lot: float,
                          sl: float = 0.0, tp: float = 0.0,
                          comment: str = "ASI", magic: int = None,
                          price: float = None, force_check_positions: bool = True
                          ) -> Optional[dict]:
        """
        Envia ordem a mercado — a arma principal da ASI.

        Args:
            action: "BUY" ou "SELL"
            lot: Tamanho do lote
            sl: Stop Loss (preço)
            tp: Take Profit (preço)
            comment: Comentário da ordem
            magic: Magic number (default: MAGIC_NUMBER)
            price: Preço opcional (se None, usa o último tick)
            force_check_positions: Se True, consulta o MT5 para o limite de posições
        """
        if not self.connected:
            log.error("❌ MT5 não conectado — ordem rejeitada")
            return None

        # Validar lot size
        lot = max(MIN_LOT_SIZE, min(MAX_LOT_SIZE, round(lot, 2)))

        # Determinar preço (prioridade para cache HFT Socket)
        if price is None:
            tick = self._last_socket_tick or mt5.symbol_info_tick(self.symbol)
            if tick is None:
                log.error("❌ Sem tick disponível para ordem")
                return None
            
            # Formato do tick muda se vier do socket ou API
            if isinstance(tick, dict):
                current_price = tick["ask"] if action.upper() == "BUY" else tick["bid"]
            else:
                current_price = tick.ask if action.upper() == "BUY" else tick.bid
        else:
            current_price = price

        order_type = mt5.ORDER_TYPE_BUY if action.upper() == "BUY" else mt5.ORDER_TYPE_SELL

        # Verificar posições abertas (Opcional para HFT burst)
        if force_check_positions:
            positions = mt5.positions_get(symbol=self.symbol)
            if positions and len(positions) >= MAX_OPEN_POSITIONS:
                log.warning(f"⚠️ Máximo de posições atingido ({MAX_OPEN_POSITIONS})")
                return None

        # Construir request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": lot,
            "type": order_type,
            "price": current_price,
            "deviation": ORDER_DEVIATION,
            "magic": magic or MAGIC_NUMBER,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        if sl > 0:
            request["sl"] = sl
        if tp > 0:
            request["tp"] = tp

        # ═══ Phase 43: HFT Socket Open (Priority) ═══
        # Formato: "ACTION|SYMBOL|LOT|SL|TP" (O MQL5 espera exatamente isso em ProcessSingleCommand)
        # Notas: sl e tp podem ser 0.
        cmd = f"{action.upper()}|{self.symbol}|{lot:.2f}|{sl:.2f}|{tp:.2f}"
        if self.send_socket_command(cmd):
            # No HFT, não esperamos o ticket/preço real aqui para não travar o loop de disparo
            # O resultado real será processado pelo _handle_socket_data assincronamente
            return {
                "success": True,
                "ticket": 0, # Pending async
                "deal": 0,
                "price": current_price, # Preço estimado (para logs imediatos)
                "volume": lot,
                "action": action,
                "status": "OPEN_SIGNALED"
            }

        # ═══ Fallback: MT5 Native API (Slow) ═══
        log.warning(f"⚠️ Socket falhou para abertura. Usando fallback API Python (Lento).")
        result = mt5.order_send(request)

        if result is None:
            log.error(f"❌ order_send retornou None: {mt5.last_error()}")
            return None

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            log.error(
                f"❌ Ordem rejeitada! code={result.retcode} "
                f"comment={result.comment}"
            )
            return {
                "success": False,
                "retcode": result.retcode,
                "comment": result.comment,
            }

        # Sucesso!
        log.trade(
            action=action, symbol=self.symbol, lot=lot,
            price=result.price, sl=sl, tp=tp,
            reason=f"ticket={result.order} deal={result.deal}"
        )

        return {
            "success": True,
            "ticket": result.order,
            "deal": result.deal,
            "price": result.price,
            "volume": result.volume,
            "action": action,
            "sl": sl,
            "tp": tp,
        }

    def send_sonar_probe(self, side: str, lot: float, price: float, duration_ms: int = 50) -> bool:
        """
        Envia uma 'Sonda Sonar' — Ordem limite ultra-curta para detectar liquidez oculta.
        """
        if not self.connected: return False
        
        cmd = f"SONAR|{self.symbol}|{side.upper()}|{lot:.2f}|{price:.2f}|{duration_ms}"
        return self.send_socket_command(cmd)

    def close_position(self, ticket: int) -> Optional[dict]:
        """Fecha uma posição pelo ticket."""
        if not self.connected:
            return None

        position = mt5.positions_get(ticket=ticket)
        if not position or len(position) == 0:
            log.warning(f"Posição {ticket} não encontrada")
            return None

        pos = position[0]

        # Inverter a ordem para fechar
        # Phase 18 Modification: Envio via Socket (Latência Zeo) em vez do Python MT5 API
        cmd = f"CLOSE|{ticket}"
        if self.send_socket_command(cmd):
            log.omega(f"⚡ FAST CLOSE SINALIZADO: ticket={ticket} (via socket)")
            return {"success": True, "ticket": ticket, "action": "CLOSE_SIGNALED"}
            
        # Fallback MT5 API
        log.warning(f"⚠️ Socket falhou para {ticket}. Tentando fechamento pela API Python MT5.")
        tick = mt5.symbol_info_tick(self.symbol)
        if not tick:
            log.error(f"❌ Sem tick da API MT5 para fechar ticket {ticket}")
            return None
            
        type_close = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        price_close = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": pos.volume,
            "type": type_close,
            "position": ticket,
            "price": price_close,
            "deviation": ORDER_DEVIATION,
            "magic": pos.magic,
            "comment": "ASI Fallback Close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            log.error(f"❌ Falha no fallback MT5 API para fechar {ticket}")
            return None
            
        profit = pos.profit
        log.trade(
            action="CLOSE", symbol=self.symbol, lot=pos.volume,
            price=result.price, profit=profit,
            reason=f"ticket={ticket} closed via API"
        )

        return {
            "success": True,
            "ticket": ticket,
            "close_price": result.price,
            "profit": profit,
        }

    def modify_position(self, ticket: int, sl: float = None,
                        tp: float = None) -> bool:
        """Modifica SL/TP de uma posição aberta."""
        if not self.connected:
            return False

        position = mt5.positions_get(ticket=ticket)
        if not position:
            return False

        pos = position[0]

        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": self.symbol,
            "position": ticket,
            "sl": sl if sl is not None else pos.sl,
            "tp": tp if tp is not None else pos.tp,
        }

        result = mt5.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            log.info(f"📝 Posição {ticket} modificada: SL={sl} TP={tp}")
            return True

        log.error(f"❌ Falha ao modificar posição {ticket}")
        return False

    # ═══════════════════════════════════════════════════════════
    #  POSIÇÕES & HISTÓRICO
    # ═══════════════════════════════════════════════════════════

    def get_open_positions(self) -> Optional[List[dict]]:
        """
        Lista de posições abertas. 
        Retorna None se houver erro de conexão/API, ou [] se não houver posições.
        """
        if not self.connected:
            return None

        positions = mt5.positions_get(symbol=self.symbol)
        
        # OMEGA: Diferenciar erro total de lista vazia
        if positions is None:
            err = mt5.last_error()
            if err[0] == mt5.RES_S_OK:
                return [] # Sucesso, mas zero ordens
            log.debug(f"⚠️ MT5 positions_get returned None (Code: {err[0]}: {err[1]})")
            return None # Erro real (socket timeout, etc)

        return [
            {
                "ticket": pos.ticket,
                "symbol": pos.symbol,
                "type": "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL",
                "volume": pos.volume,
                "open_price": pos.price_open,
                "current_price": pos.price_current,
                "sl": pos.sl,
                "tp": pos.tp,
                "profit": pos.profit,
                "swap": pos.swap,
                "time": pos.time,
                "magic": pos.magic,
                "comment": pos.comment,
            }
            for pos in positions
        ]

    def close_all_positions(self) -> int:
        """Fecha todas as posições abertas da ASI (emergency)."""
        positions = self.get_open_positions()
        closed = 0
        for pos in positions:
            if pos.get("magic") == MAGIC_NUMBER:
                result = self.close_position(pos["ticket"])
                if result and result.get("success"):
                    closed += 1
        log.omega(f"🔴 EMERGENCY: {closed}/{len(positions)} posições fechadas")
        return closed

    # ═══════════════════════════════════════════════════════════
    #  HEALTH CHECK
    # ═══════════════════════════════════════════════════════════

    def is_alive(self) -> bool:
        """Verifica se a conexão MT5 está viva."""
        if not self.connected or mt5 is None:
            return False
        try:
            tick = mt5.symbol_info_tick(self.symbol)
            return tick is not None
        except Exception:
            return False

    def health_check(self) -> dict:
        """Diagnóstico completo de saúde da bridge."""
        alive = self.is_alive()
        account = self.get_account_info() if alive else None
        symbol = self.get_symbol_info() if alive else None

        return {
            "connected": self.connected,
            "alive": alive,
            "symbol": self.symbol,
            "spread": symbol.get("spread") if symbol else None,
            "balance": account.get("balance") if account else None,
            "equity": account.get("equity") if account else None,
            "tick_buffer_size": len(self.tick_buffer),
            "last_tick_ms": self._last_tick_time,
        }
