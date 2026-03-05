"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — EXCHANGE CONFIG                        ║
║              Configuração MT5 — BTCUSD Exclusive Warfare                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ═══════════════════════════════════════════════════════════════
#  MT5 CONNECTION
# ═══════════════════════════════════════════════════════════════
MT5_LOGIN = None           # Será configurado pelo CEO
MT5_PASSWORD = None        # Será configurado pelo CEO
MT5_SERVER = None          # Será configurado pelo CEO
MT5_PATH = None            # Caminho do terminal MT5 (ex: "C:/Program Files/MetaTrader 5/terminal64.exe")
MT5_TIMEOUT_MS = 10000     # Timeout de conexão em ms

# ═══════════════════════════════════════════════════════════════
#  SÍMBOLO — BTCUSD EXCLUSIVO
# ═══════════════════════════════════════════════════════════════
SYMBOL = "BTCUSD"
SYMBOL_ALIASES = ["BTCUSD", "BTCUSD.a", "BTCUSDm", "Bitcoin"]  # Variações possíveis entre brokers

# ═══════════════════════════════════════════════════════════════
#  TIMEFRAMES OPERACIONAIS
# ═══════════════════════════════════════════════════════════════
# Multi-escala temporal para análise simultânea
# MT5 timeframe constants serão usados em runtime
TIMEFRAMES = {
    "tick":  None,   # Tick-by-tick (stream direto)
    "M1":    1,      # mt5.TIMEFRAME_M1
    "M5":    5,      # mt5.TIMEFRAME_M5
    "M15":   15,     # mt5.TIMEFRAME_M15
    "M30":   30,     # mt5.TIMEFRAME_M30
    "H1":    16385,  # mt5.TIMEFRAME_H1
    "H4":    16388,  # mt5.TIMEFRAME_H4
    "D1":    16408,  # mt5.TIMEFRAME_D1
}

# Timeframes primários para decisão (análise rápida — scalp/HFT)
PRIMARY_TIMEFRAMES = ["M1", "M5", "M15"]

# Timeframes de contexto (macro direction)
CONTEXT_TIMEFRAMES = ["M30", "H1", "H4", "D1"]

# ═══════════════════════════════════════════════════════════════
#  CANDLES / BARRAS
# ═══════════════════════════════════════════════════════════════
BARS_TO_LOAD = {
    "M1":  1000,     # Últimas 1000 velas de 1 min
    "M5":  500,      # Últimas 500 velas de 5 min
    "M15": 300,      # Últimas 300 velas de 15 min
    "M30": 200,
    "H1":  200,
    "H4":  100,
    "D1":  100,
}

# ═══════════════════════════════════════════════════════════════
#  ORDER EXECUTION
# ═══════════════════════════════════════════════════════════════
MAGIC_NUMBER = 777777          # Número mágico para identificar ordens da ASI
ORDER_DEVIATION = 20           # Desvio máximo do preço em points
ORDER_FILLING_TYPE = "IOC"     # IOC = Immediate or Cancel (mais rápido)
ORDER_TYPE_FILLING_MAP = {
    "IOC": 1,     # ORDER_FILLING_IOC
    "FOK": 0,     # ORDER_FILLING_FOK
    "RETURN": 2,  # ORDER_FILLING_RETURN
}

# ═══════════════════════════════════════════════════════════════
#  POSITION LIMITS
# ═══════════════════════════════════════════════════════════════
MAX_OPEN_POSITIONS = 20         # Aumentado para suportar HFT Multi-slot (antes 3)
MAX_LOT_SIZE = 10.0            # Lot size máximo por posição ($13k + 1:1000 leverage)
MIN_LOT_SIZE = 0.01            # Lot size mínimo
LOT_STEP = 0.01                # Incremento de lote

# ═══════════════════════════════════════════════════════════════
#  MARKET SESSIONS (UTC)
# ═══════════════════════════════════════════════════════════════
SESSIONS = {
    "ASIA":    {"start": "00:00", "end": "08:00"},
    "EUROPE":  {"start": "07:00", "end": "16:00"},
    "US":      {"start": "13:00", "end": "22:00"},
    "OVERLAP_EU_US": {"start": "13:00", "end": "16:00"},  # Maior liquidez
}

# Sessões preferidas para trading (maior liquidez para BTC)
PREFERRED_SESSIONS = ["US", "OVERLAP_EU_US", "EUROPE"]
