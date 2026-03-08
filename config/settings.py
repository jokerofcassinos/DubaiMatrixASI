"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — GLOBAL SETTINGS                       ║
║         Superintelligência Financial Omega-Class Configuration              ║
║                                                                              ║
║  Parâmetros globais auto-ajustáveis pela ASI.                               ║
║  Cada parâmetro tem bounds de segurança — a ASI pode mutar dentro deles.    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import os
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
#  DIRETÓRIOS BASE
# ═══════════════════════════════════════════════════════════════
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(DATA_DIR, "logs")
STATE_DIR = os.path.join(DATA_DIR, "state")
METRICS_DIR = os.path.join(DATA_DIR, "metrics")

# Garantir que diretórios existam
for _dir in [DATA_DIR, LOG_DIR, STATE_DIR, METRICS_DIR]:
    os.makedirs(_dir, exist_ok=True)

# ═══════════════════════════════════════════════════════════════
#  IDENTIDADE DA ASI
# ═══════════════════════════════════════════════════════════════
ASI_NAME = "DubaiMatrixASI"
ASI_VERSION = "1.0.0-omega"
ASI_CODENAME = "OMEGA CONVERGENCE"

# ═══════════════════════════════════════════════════════════════
#  LOOP PRINCIPAL
# ═══════════════════════════════════════════════════════════════
MAIN_LOOP_INTERVAL_MS = 100       # Intervalo do loop principal (ms)
CONSCIOUSNESS_CYCLE_MS = 250      # Ciclo de consciência neural (ms)
DECISION_CYCLE_MS = 500           # Ciclo de decisão (ms)
EVOLUTION_CYCLE_SECONDS = 60      # Ciclo de auto-evolução (s)

# ═══════════════════════════════════════════════════════════════
#  NEURAL SWARM
# ═══════════════════════════════════════════════════════════════
SWARM_AGENT_COUNT = 1000          # Número de micro-agentes analíticos
SWARM_MIN_CONFIDENCE = 0.65       # Confiança mínima para um agente emitir sinal
SWARM_CONVERGENCE_THRESHOLD = 0.75  # % mínimo de agentes concordando para trigger
SWARM_UNANIMITY_BOOST = 1.5      # Multiplicador quando há unanimidade

# ═══════════════════════════════════════════════════════════════
#  QUANTUM THOUGHT
# ═══════════════════════════════════════════════════════════════
QUANTUM_DIMENSIONS = 256          # Dimensões do espaço quântico de análise
QUANTUM_SUPERPOSITION_DECAY = 0.95  # Fator de decaimento de superposição
QUANTUM_COLLAPSE_THRESHOLD = 0.80   # Threshold para colapso do estado quântico
QUANTUM_ENTANGLEMENT_DEPTH = 5   # Profundidade de entrelaçamento entre agentes

# ═══════════════════════════════════════════════════════════════
#  REGIME DETECTION
# ═══════════════════════════════════════════════════════════════
REGIME_HMM_STATES = 7            # Número de estados ocultos do HMM
REGIME_LOOKBACK_BARS = 500       # Barras de lookback para treinamento do HMM
REGIME_TRANSITION_SENSITIVITY = 0.3  # Sensibilidade a transições de regime
REGIME_PREDICTION_HORIZON = 10   # Barras à frente para previsão de transição

# ═══════════════════════════════════════════════════════════════
#  DECISION — TRINITY CORE
# ═══════════════════════════════════════════════════════════════
TRINITY_BUY_THRESHOLD = 0.70     # Score mínimo para BUY
TRINITY_SELL_THRESHOLD = -0.70   # Score mínimo para SELL (negativo)
TRINITY_WAIT_ZONE = (-0.70, 0.70)  # Zona de WAIT — sem ação
TRINITY_CONFIDENCE_MIN = 0.80    # Confiança mínima para executar qualquer trade

# ═══════════════════════════════════════════════════════════════
#  RISK MANAGEMENT
# ═══════════════════════════════════════════════════════════════
RISK_MAX_POSITION_PCT = 25.0     # % máximo do saldo por posição (Antes 0.5% - Destravado para Overload)
RISK_MAX_DAILY_LOSS_PCT = 50.0   # % máximo de perda diária antes de circuit breaker
RISK_MAX_DRAWDOWN_PCT = 50.0     # % máximo de drawdown total
RISK_KELLY_FRACTION = 0.25       # Fração do Kelly Criterion (quarter-Kelly para segurança)
RISK_MAX_CONSECUTIVE_LOSSES = 5  # Losses consecutivos para ativar circuit breaker
RISK_CIRCUIT_BREAKER_PAUSE_MIN = 30  # Minutos de pausa após circuit breaker

# ═══════════════════════════════════════════════════════════════
#  EXECUTION
# ═══════════════════════════════════════════════════════════════
EXECUTION_MAX_SLIPPAGE_POINTS = 50  # Slippage máximo aceito (em points)
EXECUTION_MAX_SPREAD_POINTS = 100   # Spread máximo para aceitar trade
EXECUTION_RETRY_ATTEMPTS = 3       # Tentativas de retry em caso de falha
EXECUTION_RETRY_DELAY_MS = 100     # Delay entre retries
EXECUTION_ORDER_TIMEOUT_SEC = 10   # Timeout para execução de ordem
MAX_SLOTS_PER_CANDLE = 5           # Máximo de ordens enviadas no mesmo candle (HFT Throttling)
EXECUTION_COOLDOWN_MS = 500        # Cooldown mínimo entre disparos de ordens

# ═══════════════════════════════════════════════════════════════
#  WEB SCRAPING
# ═══════════════════════════════════════════════════════════════
SCRAPER_SENTIMENT_INTERVAL_SEC = 300   # Intervalo de scraping de sentimento (5 min)
SCRAPER_ONCHAIN_INTERVAL_SEC = 600     # Intervalo de scraping on-chain (10 min)
SCRAPER_MACRO_INTERVAL_SEC = 1800      # Intervalo de scraping macro (30 min)
SCRAPER_REQUEST_TIMEOUT_SEC = 10       # Timeout de requests HTTP
SCRAPER_MAX_RETRIES = 3               # Retries para scraping

# ═══════════════════════════════════════════════════════════════
#  AUTO-EVOLUTION BOUNDS (limites de segurança)
# ═══════════════════════════════════════════════════════════════
EVOLUTION_BOUNDS = {
    "TRINITY_BUY_THRESHOLD":       (0.50, 0.95),
    "TRINITY_SELL_THRESHOLD":      (-0.95, -0.50),
    "TRINITY_CONFIDENCE_MIN":      (0.60, 0.95),
    "RISK_MAX_POSITION_PCT":       (0.5, 50.0),
    "RISK_KELLY_FRACTION":         (0.10, 1.00),
    "SWARM_CONVERGENCE_THRESHOLD": (0.50, 0.95),
    "QUANTUM_COLLAPSE_THRESHOLD":  (0.60, 0.95),
    "EXECUTION_MAX_SPREAD_POINTS": (30, 200),
}


class ASIState:
    """
    Estado persistente da ASI — salva e carrega entre reinicializações.
    A ASI nunca "esquece" o que aprendeu.
    """

    STATE_FILE = os.path.join(STATE_DIR, "asi_state.json")

    def __init__(self):
        self.total_trades = 0
        self.total_wins = 0
        self.total_losses = 0
        self.total_profit = 0.0
        self.max_drawdown = 0.0
        self.peak_balance = 0.0
        self.agent_weights = {}          # Pesos dinâmicos de cada agente neural
        self.regime_history = []         # Histórico de regimes detectados
        self.parameter_mutations = []    # Histórico de mutações de parâmetros
        self.session_start = None
        self.last_trade_time = None
        self.circuit_breaker_active = False
        self.consecutive_losses = 0

    def save(self):
        """Persiste estado da ASI no disco."""
        state_data = {
            "asi_version": ASI_VERSION,
            "saved_at": datetime.now().isoformat(),
            "total_trades": self.total_trades,
            "total_wins": self.total_wins,
            "total_losses": self.total_losses,
            "total_profit": self.total_profit,
            "max_drawdown": self.max_drawdown,
            "peak_balance": self.peak_balance,
            "agent_weights": self.agent_weights,
            "regime_history": self.regime_history[-100:],  # Últimos 100 regimes
            "parameter_mutations": self.parameter_mutations[-50:],
            "consecutive_losses": self.consecutive_losses,
        }
        with open(self.STATE_FILE, "w") as f:
            json.dump(state_data, f, indent=2)

    def load(self):
        """Carrega estado anterior da ASI (se existir)."""
        if os.path.exists(self.STATE_FILE):
            try:
                with open(self.STATE_FILE, "r") as f:
                    data = json.load(f)
                self.total_trades = data.get("total_trades", 0)
                self.total_wins = data.get("total_wins", 0)
                self.total_losses = data.get("total_losses", 0)
                self.total_profit = data.get("total_profit", 0.0)
                self.max_drawdown = data.get("max_drawdown", 0.0)
                self.peak_balance = data.get("peak_balance", 0.0)
                self.agent_weights = data.get("agent_weights", {})
                self.regime_history = data.get("regime_history", [])
                self.parameter_mutations = data.get("parameter_mutations", [])
                self.consecutive_losses = data.get("consecutive_losses", 0)
                return True
            except (json.JSONDecodeError, KeyError) as e:
                print(f"[ASI STATE] Erro ao carregar estado: {e}")
                return False
        return False

    @property
    def win_rate(self):
        if self.total_trades == 0:
            return 0.0
        return self.total_wins / self.total_trades

    @property
    def profit_factor(self):
        if self.total_losses == 0:
            return float("inf") if self.total_wins > 0 else 0.0
        return self.total_wins / self.total_losses
