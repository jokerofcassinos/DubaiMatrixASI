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
from datetime import datetime, timezone, timedelta
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
from config.omega_params import OMEGA
from utils.logger import log
from execution.trade_registry import registry as trade_registry
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
            if self.server_socket:
                try:
                    self.server_socket.close()
                except:
                    pass
            
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Reusar endereço para evitar erro de 'port in use' após restart rápido
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(("127.0.0.1", self.socket_port))
            self.server_socket.listen(1)
            self.server_socket.settimeout(2.0)
            
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
                        log.debug(f"Aguardando conexão socket: {e}")
                    time.sleep(1) # Backoff
                    continue

            try:
                if not self.client_socket or not self._socket_running:
                    continue
                    
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
            except (OSError, ConnectionResetError) as e:
                # [Phase Ω-Shutdown Shield] Se o sistema está desligando, ignoramos erros de socket fechado
                if not self._socket_running:
                    break
                    
                log.warning(f"⚠️ Socket Error: {e}")
                self._ea_connected = False
                # [Phase 50] HFT Heartbeat: Reconnect ultra-veloz para minimizar tempo cego
                if self._socket_running:
                    log.warning("🔄 HFT BRIDGE: Tentando reconexão ultra-veloz...")
                time.sleep(0.1) # Pequeno backoff antes de re-tentar

    def _handle_socket_data(self, data: str):
        """Processa ticks e resultados vindos do EA via socket."""
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
            
            # [Phase 50] EA Presence Confirmed
            self._ea_connected = True

        elif msg_type == "RESULT":
            # Formato: RESULT|ACTION|STATUS|TICKET|PRICE|STRIKE_ID
            if len(parts) < 3:
                log.warning(f"⚠️ Resposta EA Socket malformada: {line}")
                return

            action = parts[1]
            status = parts[2]
            strike_id = parts[5] if len(parts) > 5 else None
            
            log.info(f"📩 Resposta EA Socket: {action} -> {status} | Strike: {strike_id}")
            
            if status == "SUCCESS":
                if len(parts) >= 5:
                    ticket = int(parts[3])
                    price = float(parts[4])
                    
                    if action in ["BUY", "SELL", "LIMIT"]:
                        log.omega(f"🎯 {action} EXECUTADO: Ticket {ticket} @ {price} | Strike: {strike_id}")
                        # [PHASE Ω-SYNC] Sync socket ticket with intent using unique strike_id
                        if strike_id:
                            trade_registry.update_ticket_by_strike(strike_id, ticket)
                        else:
                            # Fallback for old protocol compatibility
                            trade_registry.update_ticket(0, ticket)
                else:
                    log.warning(f"⚠️ Resposta EA Socket SUCCESS sem ticket/preço: {line}")
            
            elif action == "CLOSE" or action == "CLOSE_ALL": # [Phase Ω] Explicit close confirmation
                log.omega(f"💀 SOCKET {action} CONFIRMED: {status}")

        elif msg_type == "PONG":
            self._ea_connected = True
            pass

    def send_socket_command(self, cmd: str, retry_count: int = 1):
        """Envia comando de trading diretamente para o EA via socket com auto-reparo."""
        if not self.client_socket or not self._ea_connected:
            # Tentar um warming rápido se estivermos tentando enviar um comando crítico
            if not self._ea_connected and "PING" not in cmd:
               log.debug("🔄 Socket EA offline. Tentando warming antes do comando.")
               self._start_socket_server() 
            
        for attempt in range(retry_count + 1):
            try:
                if not self.client_socket: return False
                msg = cmd + "\n"
                data = msg.encode('utf-8')
                self.client_socket.sendall(data) # sendall garante envio completo ou erro
                return True
            except (socket.error, BrokenPipeError) as se:
                if attempt < retry_count:
                    log.warning(f"🔄 HFT SOCKET RETRY ({attempt+1}): {se}. Tentando ressuscitar túnel...")
                    self.client_socket = None
                    self._ea_connected = False
                    time.sleep(0.01) # 10ms wait
                    continue
                else:
                    log.error(f"❌ HFT SOCKET FAIL: {se}. Falling back to Native API.")
                    self._ea_connected = False
                    self.client_socket = None
                    return False
            except Exception as e:
                log.error(f"❌ Erro inesperado ao enviar comando socket: {e}")
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

    def detect_broker_commission(self, symbol: str) -> float:
        """
        [Phase 49] Detecta a comissão real cobrada pela corretora.
        Analisa os últimos 50 deals para extrair a média por lote.
        """
        if not mt5.initialize():
            return OMEGA.get("commission_per_lot", 15.0)

        now = time.time()
        from_date = now - (86400 * 3) # Últimos 3 dias
        
        deals = mt5.history_deals_get(from_date, now)
        if deals is None or len(deals) == 0:
            return OMEGA.get("commission_per_lot", 15.0)

        commissions = []
        for d in deals:
            if d.symbol == symbol and d.commission != 0:
                # Comissão absoluta por volume unitário
                comm_per_unit = abs(d.commission) / d.volume
                commissions.append(comm_per_unit)

        if not commissions:
            return OMEGA.get("commission_per_lot", 32.0)

        # Usar a mediana para evitar outliers
        commissions.sort()
        detected_val = commissions[len(commissions) // 2]
        
        # [Phase 51] Round-Turn Logic Correction
        # Se a comissão detectada no deal for menor que $25, assumimos que é 'per leg'
        # (visto que BTC na FTMO/Prop chegam a $15-20 por perna, totalizando $30-40 RT)
        # Quase todas as corretoras MT5 registram a comissão por deal (leg).
        # Para o Smart TP, precisamos do custo ROUND TURN (in + out).
        detected_val *= 2.0 # Dobrar sempre para garantir cobertura de saída
            
        return round(float(detected_val), 2)

    def get_tick(self) -> Optional[dict]:
        """Obtém o tick mais recente (preferência para HFT Socket)."""
        if not self.connected:
            return None

        # [Phase 52.3] Tick Persistence: 
        # Não consumimos mais o socket tick instantaneamente para permitir que 
        # slots em paralelo (Hydra/Strike) compartilhem a mesma leitura ultra-veloz.
        now_ms = time.time() * 1000
        if self._last_socket_tick:
            # Consideramos o tick do socket "fresco" por 50ms
            tick_age = now_ms - self._last_socket_tick.get("time_msc", 0)
            if tick_age < 50:
                return self._last_socket_tick

        # Fallback para API oficial (Lenta)
        if mt5 is None: return None
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

        if mt5 is None: return None
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
            "stops_level": info.trade_stops_level,
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
                         price: float = None, strike_id: str = "") -> Optional[dict]:
        """
        [Phase Ω-Eternity] Envia ordem Limit para Market Making Quântico.
        Pega a liquidez do spread e evita slippage cobrando do Varejo.
        """
        if not self.connected or price is None:
            log.error("❌ MT5 não conectado ou Preço não fornecido para LIMIT")
            return None

        # [Phase 52.12] Pre-validation: Validar se o preço limite é válido para a corretora
        # Se o preço limite for muito perto do preço atual (viola stops_level), o MT5 rejeita com 10015.
        # Nesses casos, convertemos para MARKET imediatamente.
        tick = self.get_tick()
        info = self.get_symbol_info()
        if tick and info:
            point = info.get("point", 0.01)
            stops_level = (info.get("stops_level", 50) + 50) * point # Buffer de +50 pts extra p/ segurança 10015
            bid, ask = tick['bid'], tick['ask']

            is_invalid = False
            if action.upper() == "BUY":
                if price >= (bid - stops_level):
                    is_invalid = True
            else: # SELL
                if price <= (ask + stops_level):
                    is_invalid = True

            if is_invalid:
                log.warning(f"⚠️ [PRE-LIMIT-VETO] Preço {price:.2f} muito perto do spread (Stops={stops_level/point:.0f} pts). Fallback p/ MARKET.")
                return self.send_market_order(action, lot, sl, tp, comment)

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
        # Command format: "LIMIT|ACTION|SYMBOL|LOT|PRICE|SL|TP|STRIKE_ID"
        cmd = f"LIMIT|{action.upper()}|{self.symbol}|{lot:.2f}|{price:.5f}|{sl:.5f}|{tp:.5f}|{strike_id}"
        
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
            "price": result.price if result.price > 0 else price,
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
                          price: float = None, force_check_positions: bool = True,
                          strike_id: str = "" # [PHASE Ω-SYNC]
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
        # Formato: "ACTION|SYMBOL|LOT|SL|TP|STRIKE_ID" (O MQL5 espera exatamente isso em ProcessSingleCommand)
        # Notas: sl e tp podem ser 0.
        cmd = f"{action.upper()}|{self.symbol}|{lot:.2f}|{sl:.2f}|{tp:.2f}|{strike_id}"
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
        # ═══ Phase 50: Omega Close Resilience ═══
        cmd = f"CLOSE|{ticket}"
        if self.send_socket_command(cmd):
            # OMEGA: Se o socket enviou, confiamos, mas monitoramos o retorno
            return {"success": True, "ticket": ticket, "action": "CLOSE_SIGNALED_HFT"}
            
        # Fallback MT5 API (Ultra-Fast Force Close)
        # Se chegamos aqui, o socket está morto ou falhou. Não podemos hesitar.
        log.warning(f"⚠️ Socket HFT indisponível para ticket {ticket}. Iniciando FORCE CLOSE via API MT5.")
        
        # Obter tick mais fresco possível, sem travar
        tick = mt5.symbol_info_tick(self.symbol)
        if not tick:
            # Desespero: tentar pegar o último tick do buffer ou da conta
            tick = self._last_socket_tick or mt5.account_info()
            if not tick:
                log.critical(f"💀 FALHA TOTAL SENSORIAL: Impossível fechar ticket {ticket} — sem dados de preço.")
                return None
            
        # Determinar preço de fechamento com slippage agressivo para garantir strike
        is_buy = (pos.type == mt5.ORDER_TYPE_BUY)
        price_close = tick.bid if is_buy else tick.ask if hasattr(tick, "bid") else pos.price_current
        
        # [Phase 50] Aumento do deviation para 100 pontos para garantir preenchimento no pânico
        force_deviation = max(ORDER_DEVIATION * 2, 50) 
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": pos.volume,
            "type": mt5.ORDER_TYPE_SELL if is_buy else mt5.ORDER_TYPE_BUY,
            "position": ticket,
            "price": price_close,
            "deviation": force_deviation,
            "magic": pos.magic,
            "comment": "ASI OMEGA FORCE CLOSE",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        if result is None:
            log.critical(f"💀 ERRO CRÍTICO API MT5: order_send faliu totalmente para {ticket}")
            return None
            
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            log.error(f"❌ Force Close Rejeitado: code={result.retcode} ({result.comment})")
            return None
            
        profit = pos.profit
        # [Phase 52] Return direction for anti-metralhadora logic
        p_direction = "BUY" if is_buy else "SELL"
        
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
            "direction": p_direction,
            "symbol": self.symbol
        }

    def close_batch(self, symbol: str, direction: str) -> bool:
        """
        [Phase Ω-FastNuke] Fecha todas as posições de um símbolo e direção em um único comando.
        Usa o Socket CLOSE_ALL para agilizar em 1000%.
        """
        if not self.connected:
            return False

        # Converte direção para tipo MT5 (0=BUY, 1=SELL)
        p_type = 0 if direction.upper() == "BUY" else 1
        
        # Tenta via Socket (Caminho Ultra-Rápido)
        cmd = f"CLOSE_ALL|{symbol}|{p_type}"
        if self._ea_connected and self.send_socket_command(cmd):
            log.omega(f"⚡ FAST BATCH CLOSE SINALIZADO: {symbol} {direction} (via socket)")
            return True
        
        # Fallback via API Python (Loop manual - Lento)
        log.warning(f"⚠️ Socket indisponível para BATCH CLOSE. Usando fallback manual.")
        positions = self.get_open_positions()
        if not positions: return True
        
        success = True
        for pos in positions:
            if pos['symbol'] == symbol and pos['type'] == direction.upper():
                res = self.close_position(pos['ticket'])
                if not res or not res.get("success"):
                    success = False
        return success

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

    def get_pending_orders(self) -> Optional[List[dict]]:
        """Lista de ordens pendentes (Limit/Stop)."""
        if not self.connected:
            return None

        orders = mt5.orders_get(symbol=self.symbol)
        if orders is None:
            err = mt5.last_error()
            if err[0] == mt5.RES_S_OK:
                return []
            return None

        return [
            {
                "ticket": o.ticket,
                "symbol": o.symbol,
                "type": "BUY_LIMIT" if o.type == mt5.ORDER_TYPE_BUY_LIMIT else "SELL_LIMIT",
                "volume": o.volume_initial,
                "price": o.price_open,
                "sl": o.sl,
                "tp": o.tp,
                "time": o.time_setup,
                "magic": o.magic,
                "comment": o.comment,
            }
            for o in orders
        ]

    # ═══════════════════════════════════════════════════════════
    #  HISTÓRICO & AUDITORIA
    # ═══════════════════════════════════════════════════════════

    def get_closed_deals(self, from_time: int, to_time: int = None) -> List[dict]:
        """Recupera deals do histórico no período solicitado usando timestamps unix converted to naive datetime."""
        if not self.connected:
            return []
        
        # [Phase Ω-Resilience] MT5 Python API prefers NAIVE datetimes (local terminal time)
        # We convert the unix timestamp to a naive datetime object.
        from_dt = datetime.fromtimestamp(from_time)
        
        if to_time:
            to_dt = datetime.fromtimestamp(to_time)
        else:
            # Look 2 days into the future to ensure we catch everything regardless of server offset
            to_dt = datetime.now() + timedelta(days=2)
        
        deals = mt5.history_deals_get(from_dt, to_dt)
        if deals is None:
            err = mt5.last_error()
            if err[0] != mt5.RES_S_OK:
                log.debug(f"⚠️ history_deals_get returned None (Code: {err[0]})")
            return []
        
        result = []
        target_symbol = self.symbol.upper()
        
        for d in deals:
            deal_symbol = d.symbol.upper()
            # Filtrar por símbolo (case-insensitive e partial match para prefixos/sufixos de corretora)
            if target_symbol not in deal_symbol and deal_symbol not in target_symbol:
                continue
                
            result.append({
                "ticket": d.ticket,
                "order": d.order,
                "time": d.time,
                "time_msc": d.time_msc,
                "type": "BUY" if d.type == mt5.DEAL_TYPE_BUY else "SELL",
                "entry": d.entry, # 0=IN, 1=OUT, 2=INOUT, 3=OUT_BY
                "magic": d.magic,
                "position_id": d.position_id,
                "volume": d.volume,
                "price": d.price,
                "commission": d.commission,
                "swap": d.swap,
                "profit": d.profit,
                "fee": d.fee,
                "symbol": d.symbol,
                "comment": d.comment
            })
        return result

    def get_deals_by_position(self, position_id: int) -> List[dict]:
        """Recupera todos os deals associados a uma posição específica."""
        if not self.connected:
            return []
        
        deals = mt5.history_deals_get(position=position_id)
        if deals is None:
            return []
            
        result = []
        for d in deals:
            result.append({
                "ticket": d.ticket,
                "order": d.order,
                "time": d.time,
                "type": "BUY" if d.type == mt5.DEAL_TYPE_BUY else "SELL",
                "entry": d.entry,
                "magic": d.magic,
                "position_id": d.position_id,
                "volume": d.volume,
                "price": d.price,
                "commission": d.commission,
                "swap": d.swap,
                "profit": d.profit,
                "comment": d.comment
            })
        return result

    @catch_and_log(default_return=40.0)
    def get_dynamic_commission_per_lot(self) -> float:
        """
        [Phase Ω-Resilience] Calcula a comissão média por lote baseada no histórico real.
        Evita valores hardcoded e se adapta a diferentes corretoras/contas.
        Prioriza $40/lot para FTMO Crypto se o símbolo for BTCUSD.
        """
        # [Ω-PhD] FTMO Hard Alignment: BTCUSD Crypto cost is strictly $40/lot round-trip.
        # Muitos servidores demo do MT5 reportam commission=0 nos deals, enganando a ASI.
        target_symbol = self.symbol.upper()
        if "BTCUSD" in target_symbol:
            return 40.0

        if not self.connected:
            return 40.0 # Default safety

        # Pegar deals das últimas 24h
        to_date = datetime.now() + timedelta(days=1)
        from_date = datetime.now() - timedelta(days=30) # Scan deeper for stats
        
        deals = mt5.history_deals_get(from_date, to_date)
        if deals is None or len(deals) == 0:
            return 40.0

        total_commission = 0.0
        total_volume = 0.0
        
        for d in deals:
            # Filtrar por símbolo manualmente
            if target_symbol not in d.symbol.upper() and d.symbol.upper() not in target_symbol:
                continue
                
            # Comissões costumam ser negativas no MT5
            if abs(d.commission) > 0:
                total_commission += abs(d.commission)
                total_volume += d.volume
        
        if total_volume > 0:
            comm_per_lot_single_leg = total_commission / total_volume
            # [Phase Ω-Fix] MT5 Deals usually record half the round-trip commission (per deal).
            comm_per_lot = comm_per_lot_single_leg * 2.0
            
            # [Phase Ω-Resilience] Commission Sanity:
            is_index = any(idx in target_symbol for idx in ["NAS100", "US30", "GER40", "HK50", "SP500", "DE40"])
            min_comm = 0.0 if (is_index and total_commission == 0) else 1.0
            
            return max(min_comm, min(100.0, comm_per_lot))
            
        return 40.0 # Fallback safety for FTMO Crypto

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
