import os
from dotenv import load_dotenv

# [Ω-10.8] Sovereign Configuration - Loading Secrets
load_dotenv()

# [Ω-FTMO] Meta-Bridge Credentials
FTMO_LOGIN = int(os.getenv("FTMO_LOGIN", "0"))
FTMO_PASSWORD = os.getenv("FTMO_PASSWORD", "PWD")
FTMO_SERVER = os.getenv("FTMO_SERVER", "FTMO-Demo")

# [Ω-5] GESTÃO DE RISCO: CIRCUIT BREAKERS (THRESHOLD %)
CB_YELLOW_DD = 0.3
CB_ORANGE_DD = 0.5
CB_RED_DD = 1.0
CB_CRITICAL_DD = 1.5
CB_EMERGENCY_DD = 2.0
CB_BLACK_DD = 3.0

# [Ω-FTMO] HARD CAPS (SAFETY MARGINS)
MAX_DAILY_DRAWDOWN_PCT = 4.0   # FTMO é 5.0
MAX_TOTAL_DRAWDOWN_PCT = 8.0   # FTMO é 10.0
FTMO_COMMISSION_LOT = 4.0      # USD por lado (Total $8.0)

# [Ω-6] PERFORMANCE LIMITS
MAX_LATENCY_THRESHOLD_MS = 3.0
MAX_TRADES_PER_HOUR = 20

# Configurações Fundamentais da SOLÉNN Ω
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# [Ω-V1.1] State Management
TRADING_ACTIVE = False

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
