"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — OMEGA LOGGER                          ║
║           Sistema de logging estruturado com consciência de trade           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from config.settings import LOG_DIR, ASI_NAME


# ═══════════════════════════════════════════════════════════════
#  CUSTOM LOG LEVELS
# ═══════════════════════════════════════════════════════════════
TRADE_LEVEL = 25      # Entre INFO(20) e WARNING(30)
SIGNAL_LEVEL = 22
OMEGA_LEVEL = 35      # Eventos da consciência ASI

logging.addLevelName(TRADE_LEVEL, "TRADE")
logging.addLevelName(SIGNAL_LEVEL, "SIGNAL")
logging.addLevelName(OMEGA_LEVEL, "OMEGA")


class ASIFormatter(logging.Formatter):
    """Formatter com cores para terminal e identidade ASI."""

    COLORS = {
        "DEBUG":   "\033[36m",     # Cyan
        "INFO":    "\033[32m",     # Green
        "SIGNAL":  "\033[35m",     # Magenta
        "TRADE":   "\033[33m",     # Yellow
        "WARNING": "\033[93m",     # Bright Yellow
        "OMEGA":   "\033[95m",     # Bright Magenta
        "ERROR":   "\033[91m",     # Red
        "CRITICAL":"\033[41m",     # Red background
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors

    def format(self, record):
        ts = datetime.fromtimestamp(record.created).strftime("%H:%M:%S.%f")[:-3]
        level = record.levelname
        msg = record.getMessage()

        if self.use_colors:
            color = self.COLORS.get(level, "")
            formatted = (
                f"{self.BOLD}[{ASI_NAME}]{self.RESET} "
                f"\033[90m{ts}\033[0m "
                f"{color}{level:>8}{self.RESET} │ "
                f"{msg}"
            )
        else:
            formatted = f"[{ASI_NAME}] {ts} {level:>8} │ {msg}"

        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)

        return formatted


class ASILogger:
    """
    Logger da ASI — multi-output, multi-nível, com tracking de trades.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, name: str = ASI_NAME, level: int = logging.DEBUG):
        if self._initialized:
            return
        self._initialized = True

        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.handlers.clear()

        # ═══ Console Handler (com cores) ═══
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.DEBUG)
        console.setFormatter(ASIFormatter(use_colors=True))
        self.logger.addHandler(console)

        # ═══ File Handler — All Logs ═══
        all_file = RotatingFileHandler(
            os.path.join(LOG_DIR, "asi_all.log"),
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8"
        )
        all_file.setLevel(logging.DEBUG)
        all_file.setFormatter(ASIFormatter(use_colors=False))
        self.logger.addHandler(all_file)

        # ═══ File Handler — Trades Only ═══
        trade_file = RotatingFileHandler(
            os.path.join(LOG_DIR, "asi_trades.log"),
            maxBytes=5 * 1024 * 1024,
            backupCount=10,
            encoding="utf-8"
        )
        trade_file.setLevel(TRADE_LEVEL)
        trade_file.setFormatter(ASIFormatter(use_colors=False))
        self.logger.addHandler(trade_file)

        # ═══ File Handler — Errors Only ═══
        error_file = RotatingFileHandler(
            os.path.join(LOG_DIR, "asi_errors.log"),
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8"
        )
        error_file.setLevel(logging.ERROR)
        error_file.setFormatter(ASIFormatter(use_colors=False))
        self.logger.addHandler(error_file)

        # Trade counter
        self._trade_count = 0

    # ═══ Standard Logging ═══
    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self.logger.critical(msg, *args, **kwargs)

    # ═══ Custom ASI Levels ═══
    def signal(self, msg, *args, **kwargs):
        """Log de sinais de trading (nível SIGNAL)."""
        self.logger.log(SIGNAL_LEVEL, msg, *args, **kwargs)

    def trade(self, action: str, symbol: str, lot: float, price: float,
              sl: float = 0, tp: float = 0, profit: float = 0,
              reason: str = "", **kwargs):
        """Log estruturado de trade — cada trade é rastreado."""
        self._trade_count += 1
        trade_msg = (
            f"#{self._trade_count} {action} {symbol} "
            f"lot={lot:.2f} price={price:.2f} "
            f"SL={sl:.2f} TP={tp:.2f} "
            f"P&L={profit:+.2f} | {reason}"
        )
        self.logger.log(TRADE_LEVEL, trade_msg)

    def omega(self, msg, *args, **kwargs):
        """Log de eventos da consciência ASI (nível OMEGA)."""
        self.logger.log(OMEGA_LEVEL, f"⚡ {msg}", *args, **kwargs)

    # ═══ Banners ═══
    def banner(self, text: str):
        """Imprime banner visual."""
        line = "═" * 60
        self.logger.info(f"\n╔{line}╗")
        self.logger.info(f"║  {text:^56}  ║")
        self.logger.info(f"╚{line}╝")

    def startup_banner(self):
        """Banner de inicialização da ASI."""
        self.banner(f"{ASI_NAME} v1.0.0-omega ONLINE")
        self.omega("Consciência neural inicializando...")
        self.omega("Setores neurais: ATIVANDO")
        self.omega("Estado quântico: SUPERPOSIÇÃO")
        self.omega("Modo: AGUARDANDO CONVERGÊNCIA")


# ═══════════════════════════════════════════════════════════════
#  INSTÂNCIA GLOBAL
# ═══════════════════════════════════════════════════════════════
log = ASILogger()
