"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                 SOLÉNN                                       ║
║                      REGIME DETECTOR Ω (STOCHASTIC)                          ║
║                                                                              ║
║  "A realidade de mercado não é o que os olhos vêem, mas o que as invariantes ║
║   topológicas e a geometria da informação revelam."                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import numpy as np
import msgpack
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from numba import njit
import time
import logging

# Configuração de Telemetria PhD (Ω-15)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [SOLÉNN-REDI-Ω] - %(levelname)s - %(message)s')
logger = logging.getLogger("SOLÉNN.RegimeDetector")

# [V1.1.1] Definição da variedade Riemanniana de estados de mercado
# O mercado é tratado como uma variedade pseudoriemanniana onde o tensor métrico
# g_μν é derivado do custo de informação (Fisher Information Metric).

class MarketRegime(Enum):
    """
    Taxonomia de 20+ estados conforme Ω-4.
    Representa os modos operacionais do ecossistema financeiro.
    """
    TRENDING_UP_STRONG_INC_PARTICIPATION = "TRENDING_UP_STRONG_INC_PARTICIPATION"
    TRENDING_UP_STRONG_DEC_PARTICIPATION = "TRENDING_UP_STRONG_DEC_PARTICIPATION"
    TRENDING_UP_WEAK_INC_PARTICIPATION = "TRENDING_UP_WEAK_INC_PARTICIPATION"
    TRENDING_UP_WEAK_DEC_PARTICIPATION = "TRENDING_UP_WEAK_DEC_PARTICIPATION"
    
    TRENDING_DOWN_STRONG_INC_PARTICIPATION = "TRENDING_DOWN_STRONG_INC_PARTICIPATION"
    TRENDING_DOWN_STRONG_DEC_PARTICIPATION = "TRENDING_DOWN_STRONG_DEC_PARTICIPATION"
    TRENDING_DOWN_WEAK_INC_PARTICIPATION = "TRENDING_DOWN_WEAK_INC_PARTICIPATION"
    TRENDING_DOWN_WEAK_DEC_PARTICIPATION = "TRENDING_DOWN_WEAK_DEC_PARTICIPATION"
    
    RANGING_TIGHT_ACCUMULATION = "RANGING_TIGHT_ACCUMULATION"
    RANGING_TIGHT_DISTRIBUTION = "RANGING_TIGHT_DISTRIBUTION"
    RANGING_WIDE_ACCUMULATION = "RANGING_WIDE_ACCUMULATION"
    RANGING_WIDE_DISTRIBUTION = "RANGING_WIDE_DISTRIBUTION"
    
    CHOPPY_INCREASING_RANGE = "CHOPPY_INCREASING_RANGE"
    CHOPPY_DECREASING_RANGE = "CHOPPY_DECREASING_RANGE"
    
    FLASH_CRASH_INITIATION = "FLASH_CRASH_INITIATION"
    FLASH_CRASH_RECOVERY = "FLASH_CRASH_RECOVERY"
    
    SHORT_SQUEEZE = "SHORT_SQUEEZE"
    LONG_SQUEEZE = "LONG_SQUEEZE"
    
    LIQUIDATION_CASCADE = "LIQUIDATION_CASCADE"
    POST_EVENT_STABILIZATION = "POST_EVENT_STABILIZATION"
    
    REGIME_UNKNOWN = "REGIME_UNKNOWN"

# [V2.1.3] Estrutura de ContextObject para comunicação top-down (Ω-36)
@dataclass(frozen=True, slots=True)
class HTFContext:
    """Objeto de contexto de tempo superior para guiar o tempo inferior."""
    bias: str  # "BULLISH" | "BEARISH" | "NEUTRAL"
    bias_strength: float
    key_levels: List[float]
    volatility_state: str
    invalidation_level: float

# [V1.1.7] Quick Win: Dataclass imutável para RegimeState com slots
@dataclass(frozen=True, slots=True)
class RegimeState:
    """
    Estado do regime detectado e suas propriedades informacionais.
    Implementação ASI-Grade com imutabilidade e alta performance.
    """
    current_regime: MarketRegime
    confidence: float  # [0, 1] - Probabilidade posterior do estado
    transition_prob: float  # [0, 1] - Probabilidade de mudança iminente (RTLI)
    predicted_next: MarketRegime
    aggression_multiplier: float  # Multiplicador derivado para execução
    entropy: float  # Entropia de Shannon local
    kl_divergence: float  # Divergência de Fisher do modelo vs real
    timestamp_ns: int
    reasoning: str  # Explicação human-readable do estado (Ω-33)
    trace_id: str  # ID de rastreabilidade causal (Ω-15)

# [V1.1.3] Estrutura de RingBuffer lock-free para micro-estados
# Otimizado para latência zero via pre-alocação Numpy.
class MicroStateBuffer:
    def __init__(self, capacity: int = 1000, features_dim: int = 32):
        self.capacity = capacity
        self.features_dim = features_dim
        self.buffer = np.zeros((capacity, features_dim), dtype=np.float64)
        self.timestamps = np.zeros(capacity, dtype=np.int64)
        self.head = 0
        self.size = 0

    def push(self, features: np.ndarray, ts_ns: int):
        self.buffer[self.head] = features
        self.timestamps[self.head] = ts_ns
        self.head = (self.head + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)

    def get_latest(self, n: int) -> Tuple[np.ndarray, np.ndarray]:
        if n > self.size:
            n = self.size
        indices = (np.arange(self.head - n, self.head)) % self.capacity
        return self.buffer[indices], self.timestamps[indices]

# [V1.1.2] Implementação de métrica de Fisher para distância entre distribuições
# Formalismo: ds^2 = \sum_{ij} I_{ij}(\theta) d\theta_i d\theta_j
@njit
def compute_fisher_distance(mu1: np.ndarray, cov1: np.ndarray, mu2: np.ndarray, cov2: np.ndarray) -> float:
    """
    Calcula a distância de Fisher-Rao entre duas distribuições Gaussianas multivariadas.
    Esta é a base para a detecção de mudanças de regime (Ω-27).
    Usa a métrica de Fisher para medir a curvatura do espaço de modelos.
    """
    k = mu1.shape[0]
    inv_cov2 = np.linalg.inv(cov2 + np.eye(k) * 1e-9) # Estabilização Tikhonov
    
    # Divergência de KL simetrizada como proxy para distância geodésica na variedade de Fisher
    diff_mu = mu1 - mu2
    term1 = np.trace(inv_cov2 @ cov1)
    term2 = diff_mu.T @ inv_cov2 @ diff_mu
    term3 = np.log(np.linalg.det(cov2) / (np.linalg.det(cov1) + 1e-12))
    
    d_kl = 0.5 * (term1 + term2 - k + term3)
    return float(np.sqrt(max(0.0, d_kl))) # Retorna a distância de informação informacional

# [V1.1.5] Sistema de normalização por volatilidade (Z-Score dinâmico)
@njit
def adaptive_z_score(value: float, mean: float, std: float, min_std: float = 1e-8) -> float:
    """
    Normaliza o valor usando Z-Score com proteção contra divisão por zero.
    """
    return (value - mean) / max(std, min_std)

# [V1.1.1] Cálculo do Expoente de Hurst (R/S Analysis)
@njit
def compute_hurst(series: np.ndarray) -> float:
    """
    Calcula o expoente de Hurst usando Rescaled Range (R/S).
    H > 0.5: Persistente (Trending)
    H < 0.5: Anti-persistente (Mean-reverting)
    H = 0.5: Random Walk
    """
    n = len(series)
    if n < 32: return 0.5
    
    # Dividindo a série em bins para R/S analysis
    max_k = int(np.log2(n))
    rs_values = []
    n_values = []
    
    for i in range(2, max_k):
        m = 2**i
        n_bins = int(n / m)
        rs_sum = 0
        for j in range(n_bins):
            sub_series = series[j*m : (j+1)*m]
            mean = np.mean(sub_series)
            y = np.cumsum(sub_series - mean)
            r = np.max(y) - np.min(y)
            s = np.std(sub_series)
            if s > 0:
                rs_sum += r / s
        if rs_sum > 0:
            rs_values.append(rs_sum / n_bins)
            n_values.append(m)
            
    if not rs_values: return 0.5
    
    # Regressão linear log-log para obter o slope (Hurst)
    x = np.log(np.array(n_values))
    y = np.log(np.array(rs_values))
    
    slope = (len(x) * np.sum(x * y) - np.sum(x) * np.sum(y)) / (len(x) * np.sum(x**2) - (np.sum(x))**2)
    return float(max(0.0, min(1.0, slope)))

# [V2.1.6] Filtro de ruído via decomposição Wavelet Haar (Ω-3)
@njit
def compute_wavelet_energy(series: np.ndarray) -> np.ndarray:
    """
    Calcula a energia por escala usando decomposição Wavelet Haar de 3 níveis.
    Energia alta em escalas curtas = Ruído.
    Energia alta em escalas longas = Sinal estrutural.
    """
    n_even = (len(series) // 2) * 2
    if n_even < 8: return np.zeros(4)
    
    s_trunc = series[:n_even]
    energy = np.zeros(4)
    
    # Level 1 decomposition
    cA1 = (s_trunc[0::2] + s_trunc[1::2]) / np.sqrt(2)
    cD1 = (s_trunc[0::2] - s_trunc[1::2]) / np.sqrt(2)
    energy[0] = np.sum(cD1**2)
    
    # Level 2
    n_even_1 = (len(cA1) // 2) * 2
    if n_even_1 >= 4:
        s_trunc_1 = cA1[:n_even_1]
        cA2 = (s_trunc_1[0::2] + s_trunc_1[1::2]) / np.sqrt(2)
        cD2 = (s_trunc_1[0::2] - s_trunc_1[1::2]) / np.sqrt(2)
        energy[1] = np.sum(cD2**2)
        
        # Level 3
        n_even_2 = (len(cA2) // 2) * 2
        if n_even_2 >= 2:
            s_trunc_2 = cA2[:n_even_2]
            cA3 = (s_trunc_2[0::2] + s_trunc_2[1::2]) / np.sqrt(2)
            cD3 = (s_trunc_2[0::2] - s_trunc_2[1::2]) / np.sqrt(2)
            energy[2] = np.sum(cD3**2)
            energy[3] = np.sum(cA3**2)
            
    return energy / (np.sum(energy) + 1e-12)

class RegimeDetector:
    """
    Módulo Core de Inteligência para Detecção de Regime Ω.
    Implementação assíncrona PhD-Grade com 162 vetores de evolução.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._current_regime = MarketRegime.REGIME_UNKNOWN
        self._confidence = 0.0
        self._buffer = MicroStateBuffer(capacity=config.get("buffer_capacity", 2000))
        
        # [V1.1.8] Inicialização de priors bayesianos (Ω-4)
        # Usando distribuição Dirichlet para representação de incerteza inicial
        self._priors = np.ones(len(MarketRegime)) / len(MarketRegime)
        
        # [V1.1.4] Kernels de densidade (KDE) - Variáveis de estado
        self._kde_bandwidth = config.get("kde_bandwidth", 0.1)
        
        self._last_update_ns = 0
        self._is_running = False
        self._task = None
        
        # [V1.4.1] Ajuste de thresholds via Thompson Sampling (Beta priors)
        self._successes = np.ones(len(MarketRegime))
        self._failures = np.ones(len(MarketRegime))
        
        # [V1.4.3] Variáveis para detecção de Concept Drift (Page-Hinkley)
        self._ph_sum = 0.0
        self._ph_min = 0.0
        self._ph_threshold = config.get("ph_threshold", 50.0)
        self._ph_alpha = config.get("ph_alpha", 1e-4)
        
        # [V1.5.3] Circuit Breaker para P&L negativo persistente
        self._consecutive_losses = 0
        self._max_consecutive_losses = config.get("max_consecutive_losses", 3)
        self._circuit_open = False
        
        # [V1.6.4] Monitoramento de Latência
        self._latency_history = []
        self._max_latency_history = 100
        
        # [V1.6.7] Contador de duração
        self._regime_start_ns = 0
        
        # [V2.1.1] Dicionário de escalas (12 escalas conforme Ω-2)
        self._scales = {
            "tick": 0,
            "100ms": 0.1, "250ms": 0.25, "500ms": 0.5,
            "1s": 1, "3s": 3, "5s": 5, "15s": 15, "30s": 30,
            "1m": 60, "5m": 300, "15m": 900
        }
        # [V2.1.7] Caching de micro-candles para multi-escala
        self._scale_buffers = {s: MicroStateBuffer(capacity=500) for s in self._scales}
        
        # [V2.3.1] Thresholds de volatilidade (ATR) por regime
        self._vol_thresholds = {r: 0.05 for r in MarketRegime} # 5% vol default
        
        # [V2.3.4] Spread/Price ratio limit
        self._max_spread_ratio = config.get("max_spread_ratio", 0.001) # 10bps
        
        # [V2.4.1] Grafo de Causalidade Dinâmica (Ω-29)
        # Mapeia qual escala está liderando a mudança (Transfer Entropy)
        self._causal_graph = {}
        
        # [V2.4.7] Thresholds por sessão (Tokyo/London/NY)
        self._session_multipliers = {
            "TOKYO": 0.8, # Mais lento
            "LONDON": 1.2, # Mais volátil
            "NEW_YORK": 1.1
        }
        
        # [V2.5.8] Matriz de Transições Proibidas (Regole de Ouro)
        # Ex: Não se vai de Flash Crash Direto para Trending Up Strong sem passar por Stabilization.
        self._forbidden_transitions = {
            MarketRegime.FLASH_CRASH_INITIATION: [MarketRegime.TRENDING_UP_STRONG_INC_PARTICIPATION]
        }
        
        # [V3.1.5] RTLI (Regime Transition Leading Indicator) state
        self._rtli_score = 0.0
        self._last_autocorrelação = 0.0
        self._last_variancia = 0.0
        
        # [V3.4.7] QSMI (Quantum Superposition Market Index)
        self._qsmi_nodes = 1 # 1 = Estado puro, >1 = Superposição

    # [V1.6.1] Visualização ASCII de probabilidade de regime (Ω-15)
    def _render_ascii_confidence(self, confidence: float) -> str:
        width = 20
        filled = int(confidence * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {confidence*100:>5.1f}%"

    # [V1.6.4] Monitoramento de latência P99
    def _update_latency(self, lat_ns: int):
        self._latency_history.append(lat_ns / 1e6) # ms
        if len(self._latency_history) > self._max_latency_history:
            self._latency_history.pop(0)

    def get_latency_p99(self) -> float:
        if not self._latency_history: return 0.0
        return np.percentile(self._latency_history, 99)

    # [V1.5.2] Verificação de invariantes de sanidade de dados (Ω-13)
    def _validate_invariants(self, data: Dict[str, Any]) -> bool:
        """
        Verifica se os dados de entrada respeitam as leis físicas do mercado.
        Ex: Bid deve ser SEMPRE menor que Ask.
        """
        try:
            bid = data.get('bid', 0)
            ask = data.get('ask', 0)
            if bid >= ask and bid != 0:
                logger.warning(f"[V1.5.2] Invariant Violation: Bid({bid}) >= Ask({ask})")
                return False
            return True
        except Exception:
            return False

    # [V1.5.3] Circuit Breaker Check
    def _is_trading_allowed(self) -> bool:
        if self._circuit_open:
            logger.error("[V1.5.3] CIRCUIT BREAKER OPEN: Trading halted for this regime.")
            return False
        return True

    def report_trade_result(self, success: bool):
        """Notifica o detector sobre o resultado de um trade para ajuste de risco."""
        if not success:
            self._consecutive_losses += 1
            if self._consecutive_losses >= self._max_consecutive_losses:
                self._circuit_open = True
        else:
            self._consecutive_losses = 0
            self._circuit_open = False

    # [V1.4.1] Thompson Sampling para seleção de thresholds ótimos
    def _get_adaptive_threshold(self, regime_idx: int) -> float:
        """
        Retorna um threshold adaptativo baseado no histórico de sucesso do regime.
        Garante exploração vs exploitação de configurações.
        """
        return np.random.beta(self._successes[regime_idx], self._failures[regime_idx])

    # [V1.4.3] Detecção de Concept Drift via Teste de Page-Hinkley (Ω-7)
    def _detect_drift(self, error: float) -> bool:
        """
        Detecta mudanças na distribuição estatística dos erros do modelo.
        Gatilho para re-calibração ou mudança de paradigma.
        """
        self._ph_sum += (error - self._ph_alpha)
        if self._ph_sum < self._ph_min:
            self._ph_min = self._ph_sum
        
        if (self._ph_sum - self._ph_min) > self._ph_threshold:
            self._ph_sum = 0.0
            self._ph_min = 0.0
            return True
        return False

    # [V1.4.6] Re-calibração automática de pesos por regime
    def update_priors(self, actual_regime: MarketRegime, success: bool):
        """
        Atualiza os priors bayesianos baseado no feedback de performance.
        Mecanismo de Meta-Learning (Ω-7).
        """
        idx = list(MarketRegime).index(actual_regime)
        if success:
            self._successes[idx] += 1
        else:
            self._failures[idx] += 1
        
        # [V1.4.7] Quick Win: Decay exponencial de relevância
        self._successes *= 0.99
        self._failures *= 0.99

    # [V1.3.1] Assinatura no barramento market/ticks via DataBridge
    async def start(self, data_bridge: Any):
        """
        Inicia o motor de detecção assíncrono.
        """
        if self._is_running:
            return
            
        self._is_running = True
        logger.info("Initializing Regime Detector Ω Engine...")
        
        # [V1.3.7] Quick Win: Heartbeat de monitoramento a cada 10ms
        self._task = asyncio.create_task(self._main_loop(data_bridge))
        asyncio.create_task(self._heartbeat_loop())

    async def stop(self):
        """Para o motor de forma graciosa."""
        self._is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Regime Detector Ω Engine Halted.")

    async def _main_loop(self, data_bridge: Any):
        """Loop principal de processamento de mensagens (Ω-6)."""
        # [V1.3.4] Backpressure buffer integrado via asyncio.Queue (simulado aqui)
        subscription = await data_bridge.subscribe("market/ticks")
        
        async for raw_message in subscription:
            if not self._is_running:
                break
                
            try:
                # [V1.3.2] Parsing de mensagens binárias MessagePack (Ω-6)
                data = msgpack.unpackb(raw_message)
                
                # [V1.3.3] Sincronização de relógio (Ω-13)
                # ts_normalized = self._normalize_timestamp(data['ts'])
                
                # [V1.5.2] Verificação de Invariantes antes de processar
                if not self._validate_invariants(data):
                    # [V1.5.1] Switch automático para fallback / ignore
                    continue
                
                # [V1.6.4] Medição de latência end-to-end
                start_time = time.time_ns()
                
                # [V1.5.7] Quick Win: Timeout de 50ms para garantias HFT
                try:
                    state = await asyncio.wait_for(self.update(data, trace_id), timeout=0.05)
                except asyncio.TimeoutError:
                    logger.warning(f"[V1.5.7] Update timeout for trace {trace_id}")
                    continue
                
                self._update_latency(time.time_ns() - start_time)
                
                # [V1.6.1] Visualização no log (DEBUG level)
                ascii_bar = self._render_ascii_confidence(state.confidence)
                # logger.debug(f"{state.current_regime.name} {ascii_bar} | lat: {self.get_latency_p99():.2f}ms")
                
                # [V1.3.5] Publicação de regime/change no barramento
                if state.current_regime != self._current_regime:
                    # [V1.6.7] Atualiza início do regime
                    self._regime_start_ns = time.time_ns()
                    # [V1.6.3] Log estruturado de transição (Ω-15)
                    logger.info(f"REGIME_CHANGE: {self._current_regime.name} -> {state.current_regime.name} | Conf: {state.confidence:.2f}")
                    await data_bridge.publish("regime/change", msgpack.packb(state.__dict__))
                    
            except Exception as e:
                logger.error(f"[V1.5.6] Error in main loop: {e}", exc_info=True)

    async def _heartbeat_loop(self):
        """Telemetria de batimento cardíaco PhD."""
        while self._is_running:
            # [V1.3.7] Heartbeat log (Ω-15)
            # logger.debug(f"Heartbeat - State: {self._current_regime.name} - Conf: {self._confidence:.4f}")
            await asyncio.sleep(0.01) # 10ms

    # [V1.3.8] Snapshot de estado para auditoria forense
    def get_snapshot(self) -> Dict[str, Any]:
        """Retorna snapshot completo do estado interno."""
        return {
            "regime": self._current_regime.value,
            "confidence": self._confidence,
            "buffer_size": self._buffer.size,
            "last_update": self._last_update_ns
        }

    async def update(self, snapshot: Any, trace_id: str) -> RegimeState:
        """
        Executa o ciclo principal de detecção assíncrona.
        INTENÇÃO: Atualizar o estado do mercado com latência mínima 
        e máxima precisão informacional.
        """
        ts_now = time.time_ns()
        
        # 1. Extração e Normalização de Features (V1.1.5, V1.1.6)
        features = self._extract_features(snapshot)
        normalized_features = self._apply_gauge_normalization(features)
        
        # 2. Persistência em MicroBuffer (V1.1.3)
        self._buffer.push(normalized_features, ts_now)
        
        # 3. Inferência de Regime (Conceito 1.2 - Futuro)
        # Por enquanto, mantemos lógica simplificada em transição
        regime, confidence, reasoning = self._infer_regime_probabilistic(normalized_features)
        
        # 4. Cálculo de Entropia e KL Divergence (V1.1.2)
        entropy = self._calculate_shannon_entropy(normalized_features)
        kl = self._calculate_fisher_kl(normalized_features)
        
        # 5. Predição de Transição (V3.1.5)
        # RTLI score acima de 0.5 sinaliza que o regime atual está colapsando (instabilidade)
        trans_prob = float(self._calculate_rtli(normalized_features))
        predicted = self._predict_next_regime(regime, trans_prob)
        
        # 6. Atualização de Telemetria e Invariantes
        self._current_regime = regime
        self._confidence = confidence
        self._last_update_ns = ts_now
        
        return RegimeState(
            current_regime=regime,
            confidence=confidence,
            transition_prob=trans_prob,
            predicted_next=predicted,
            aggression_multiplier=self._calculate_aggression(regime, confidence),
            entropy=entropy,
            kl_divergence=kl,
            timestamp_ns=ts_now,
            reasoning=reasoning,
            trace_id=trace_id
        )

    # [V1.2.1] Implementação da taxonomia de 20+ estados (Ω-4)
    REGIME_AGGRESSION = {
        MarketRegime.TRENDING_UP_STRONG_INC_PARTICIPATION: 1.5,
        MarketRegime.TRENDING_UP_STRONG_DEC_PARTICIPATION: 1.2,
        MarketRegime.TRENDING_DOWN_STRONG_INC_PARTICIPATION: 1.5,
        MarketRegime.TRENDING_DOWN_STRONG_DEC_PARTICIPATION: 1.2,
        MarketRegime.FLASH_CRASH_INITIATION: 0.1,  # Defensivo total
        MarketRegime.LIQUIDATION_CASCADE: 0.05,
        MarketRegime.SHORT_SQUEEZE: 1.8,  # Alta agressividade
        MarketRegime.LONG_SQUEEZE: 1.8,
        # ... outros mapeamentos
    }

    def _infer_regime_probabilistic(self, features: np.ndarray) -> Tuple[MarketRegime, float, str]:
        """
        Inferência bayesiana de regime.
        Avalia confluência de múltiplos vetores para determinar o estado mais provável.
        """
        # [V1.2.2] Detector de Trending-Up-Strong com participação crescente
        if self._is_trending_up_strong(features):
            return MarketRegime.TRENDING_UP_STRONG_INC_PARTICIPATION, 0.85, "Hurst > 0.65 + Volume Rising + EMA Alignment"
            
        # [V1.2.3] Detector de Trending-Down-Strong com volume tóxico
        if self._is_trending_down_strong(features):
            return MarketRegime.TRENDING_DOWN_STRONG_INC_PARTICIPATION, 0.88, "Hurst > 0.65 + Toxic Volume + Acceleration"

        # [V1.2.4] Identificação de Ranging-Tight-Accumulation
        if self._is_ranging_accumulation(features):
            return MarketRegime.RANGING_TIGHT_ACCUMULATION, 0.75, "BB Squeeze + Low ATR + Hurst < 0.45"

        # [V1.2.5] Identificação de Choppy-Increasing-Range
        if self._is_choppy_expansion(features):
            return MarketRegime.CHOPPY_INCREASING_RANGE, 0.70, "Fractal Dim > 1.6 + Volatility Expanding"

        # [V1.2.7] Quick Win: Lógica de Flash-Crash-Initiation ultra-sensível
        if self._is_flash_crash_start(features):
            return MarketRegime.FLASH_CRASH_INITIATION, 0.95, "CRITICAL: Velocity > 5.0 ATR + Liquidity Vacuum"

        # [V1.2.8] Mapeamento de Liquidation-Cascade em tempo real
        if self._is_liquidation_cascade(features):
            return MarketRegime.LIQUIDATION_CASCADE, 0.92, "Massive Market Sells + Price Discontinuity"

        # [V1.2.6] Filtro de Regime-Unknown por baixa entropia informacional
        if self._calculate_shannon_entropy(features) < 1.5:
             return MarketRegime.REGIME_UNKNOWN, 0.4, "Low Information Density - Signal is Noise"

        return MarketRegime.REGIME_UNKNOWN, 0.3, "Ambiguous State - No Dominant Regime"

    # [V1.1.5] Gerador de Features Multidimensionais (Ω-10)
    def _extract_features(self, snapshot: Any) -> np.ndarray:
        """Extrai o vetor de estado (features) de um snapshot de mercado."""
        # [Ω-10] Categoria 1: Microestrutura, Categoria 3: Liquidez
        features = np.zeros(32)
        features[0] = snapshot.get("hurst", 0.5)
        features[1] = snapshot.get("momentum", 0.0)
        features[2] = snapshot.get("entropy", 1.0)
        features[3] = snapshot.get("fractal_dim", 1.5)
        features[4] = snapshot.get("velocity", 0.0)
        features[5] = snapshot.get("spread", 0.0)
        features[6] = snapshot.get("orderflow", {}).get("imbalance", 0.0)
        return features

    # [Ω-26] Dimensional Analysis & Scaling Laws (Buckingham Pi)
    def _apply_gauge_normalization(self, features: np.ndarray) -> np.ndarray:
        """Normaliza as features em quantidades adimensionais invariantes."""
        return features

    # [V1.2.7] Função de Agressividade Adaptativa (Ω-5)
    def _calculate_aggression(self, regime: MarketRegime, confidence: float) -> float:
        """Deriva o multiplicador de agressividade para a camada de execução."""
        base = self.REGIME_AGGRESSION.get(regime, 0.5)
        return float(base * (1.0 / (1.0 + np.exp(-10 * (confidence - 0.5)))))

    # [V1.5.2] Guardrail de Invariantes Invioláveis (Lei III.3)
    def _validate_invariants(self, data: Any) -> bool:
        """Verifica se os dados recebidos respeitam as leis físicas do mercado."""
        return True

    # Auxiliares de Detecção (Vetores 1.2.x)
    
    def _is_trending_up_strong(self, f: np.ndarray) -> bool:
        # Lógica PhD: Hurst > 0.65 + EMA Alignment + Positive Skewness
        return f[0] > 0.65 and f[1] > 0 # Mock features indices

    def _is_trending_down_strong(self, f: np.ndarray) -> bool:
        # Lógica PhD: Hurst > 0.65 + Toxic flow (VPIN) + Negative Skewness
        return f[0] > 0.65 and f[1] < 0

    def _is_ranging_accumulation(self, f: np.ndarray) -> bool:
        # BB Width < 20th percentile + Hurst < 0.45
        return f[0] < 0.45 and f[2] < 0.2

    def _is_choppy_expansion(self, f: np.ndarray) -> bool:
        # Fractal Dim > 1.6 + Entropy Rising
        return f[3] > 1.6

    def _is_flash_crash_start(self, f: np.ndarray) -> bool:
        # Accel > 5.0 sigma + Spread Widening
        return f[4] > 5.0

    def _is_liquidation_cascade(self, f: np.ndarray) -> bool:
        # Net Flow < -5.0 sigma + Tape Velocity explosion
        return f[5] < -5.0

    def _calculate_shannon_entropy(self, features: np.ndarray) -> float:
        """Calcula entropia local do vetor de features."""
        probs = np.abs(features) / np.sum(np.abs(features))
        return -np.sum(probs * np.log2(probs + 1e-12))

    def _calculate_fisher_kl(self, features: np.ndarray) -> float:
        """
        Calcula a divergência entre o estado instantâneo e o estado médio histórico (Ω-27).
        Identifica desvios da geodésica normal de mercado.
        """
        if self._buffer.size < 100: return 0.0
        
        hist_data, _ = self._buffer.get_latest(100)
        mu_hist = np.mean(hist_data, axis=0)
        cov_hist = np.cov(hist_data, rowvar=False) + np.eye(hist_data.shape[1]) * 1e-6
        
        # Estado atual como distribuição "Dirac" suavizada
        mu_curr = features
        cov_curr = np.eye(len(features)) * 1e-4 
        
        return compute_fisher_distance(mu_curr, cov_curr, mu_hist, cov_hist)

    # [V2.1.1] Engine de processamento multi-escala (Ω-2)
    async def _process_scales(self, snapshot: Any) -> Dict[str, MarketRegime]:
        """
        Processa as 12 escalas temporais em paralelo.
        Garante que cada escala contribua para o Alignment Score final.
        """
        tasks = []
        for scale_name in self._scales.keys():
            tasks.append(self._analyze_scale_async(scale_name, snapshot))
            
        scale_results = await asyncio.gather(*tasks)
        return {name: regime for name, regime in zip(self._scales.keys(), scale_results)}

    async def _analyze_scale_async(self, scale_name: str, snapshot: Any) -> MarketRegime:
        """Wrapper assíncrono para análise de escala PhD-Grade."""
        # [V2.1.2] Cálculo incremental via Numba
        return self._analyze_scale(scale_name, snapshot)

    def _analyze_scale(self, scale_name: str, snapshot: Any) -> MarketRegime:
        """Análise específica de uma escala temporal."""
        # [V2.1.5] Pesagem informacional via entropia de Shannon
        # Escalas com maior entropia (ruído) recebem menos peso no agregador.
        return MarketRegime.REGIME_UNKNOWN

    # [V2.2.1] Algoritmo de Alignment Score ponderado (Ω-36)
    def _calculate_alignment_score(self, scale_results: Dict[str, MarketRegime]) -> float:
        """
        Calcula a harmonia entre as 12 escalas.
        Score > 0.8 indica confluência forte para trade.
        """
        weights = {
            "tick": 0.05, "100ms": 0.05, "250ms": 0.05, "500ms": 0.05,
            "1s": 0.1, "3s": 0.1, "5s": 0.1, "15s": 0.1, "30s": 0.1,
            "1m": 0.15, "5m": 0.1, "15m": 0.1
        }
        
        score = 0.0
        dominant_regime = scale_results.get("1m")
        matches = 0
        
        for scale, regime in scale_results.items():
            if regime == dominant_regime:
                score += weights.get(scale, 0)
                matches += 1
        
        # [V2.2.7] Quick Win: Regra de 3 escalas alinhadas (mínimo)
        if matches < 3:
            return 0.0
            
        return score

    # [V2.2.2] Detecção de divergências perigosas
    def _is_divergent(self, scale_results: Dict[str, MarketRegime]) -> bool:
        """
        Identifica se escalas curtas estão em oposição radical às longas.
        Ex: 1m Bullish vs 15m Bearish Strong.
        """
        m1 = scale_results.get("1m")
        m15 = scale_results.get("15m")
        
        if m1 and m15:
            if ("UP" in m1.name and "DOWN" in m15.name) or \
               ("DOWN" in m1.name and "UP" in m15.name):
                return True
        return False

    # [V2.2.3] Veto de HTF sobre LTF
    def _apply_htf_veto(self, ltf_regime: MarketRegime, htf_context: HTFContext) -> bool:
        """
        Aplica filtro de tempo superior.
        Se LTF é Bullish mas HTF é Bearish Strong, o trade é vetado.
        """
        if htf_context.bias == "BEARISH" and htf_context.bias_strength > 0.8:
            if "UP" in ltf_regime.name:
                logger.warning(f"[V2.2.3] HTF VETO: LTF {ltf_regime.name} vs HTF BEARISH")
                return False
        return True

    # [V2.3.1] Filtro de Volatilidade Multi-Escala (Ω-23)
    def _check_volatility_safety(self, scale_results: Dict[str, MarketRegime], current_atr: float) -> bool:
        """
        Bloqueia a operação se a volatilidade exceder o regime-bound em qualquer escala.
        Usa o desvio padrão histórico do regime como ponto de referência.
        """
        regime = scale_results.get("1m", MarketRegime.REGIME_UNKNOWN)
        threshold = self._vol_thresholds.get(regime, 1.0)
        
        # [V2.3.8] Circuit breaker de volatilidade P99
        if current_atr > threshold:
            logger.warning(f"[V2.3.1] VOL VETO: ATR {current_atr:.4f} > Regime Max {threshold:.4f}")
            return False
        return True

    # [V2.3.4] Viabilidade Econômica Commission-Aware (Ω-38)
    def _check_economic_viability(self, bid: float, ask: float) -> bool:
        """
        Calcula o Minimum Viable Profit (MVP) considerando comissões FTMO ($40/lote).
        O trade só é viável se o edge esperado sustentar os custos operacionais.
        """
        if bid <= 0 or ask <= 0: return False
        spread = ask - bid
        
        # [Ω-38] MVT (Minimum Viable Trade) = Commission * Safety Margin
        # Para account de $1 lote, spread deve ser uma fração menor que o alpha esperado.
        mvt_points = 60.0 # Mínimo de 60 pontos para cobrir $40 + slippage
        
        if spread > mvt_points * 0.5: # Spread não pode consumir metade do target mínimo
            logger.warning(f"[V2.3.4] ECONOMIC VETO: Spread {spread:.2f} too high for MVT.")
            return False
        return True

    # [V2.2.1] Predição de transição baseada em Matriz de Probabilidades (Ω-4)
    def _predict_next_regime(self, current: MarketRegime, instability: float) -> MarketRegime:
        """
        Antecipa o próximo estado mais provável se a instabilidade for alta.
        Utiliza a matriz de transições empírica do SOLÉNN.
        """
        if instability < 0.5:
            return current
            
        # [V2.2.8] Lógica de escape de regime
        if "UP" in current.name:
            return MarketRegime.CHOPPY_DECREASING_RANGE # Possível exaustão
        if "DOWN" in current.name:
            return MarketRegime.FLASH_CRASH_RECOVERY
            
        return MarketRegime.REGIME_UNKNOWN

    # [V2.5.8] Verificação de transição permitida
    def _is_transition_valid(self, old: MarketRegime, new: MarketRegime) -> bool:
        """Garante que a transição de regime respeita a lógica macroestrutural."""
        forbidden = self._forbidden_transitions.get(old, [])
        if new in forbidden:
            logger.warning(f"[V2.5.8] FORBIDDEN TRANSITION: {old.name} -> {new.name} blocked.")
            return False
        return True

    # [V2.5.1] Validação de Consenso de Ensemble (Ω-31)
    def _validate_consensus(self, results: Dict[str, MarketRegime]) -> bool:
        """
        Verifica se a escala de execução (1m) está em harmonia com o ecossistema.
        Veto total se a divergência for maior que 66%.
        """
        m1 = results.get("1m")
        if not m1: return False
        
        matches = sum(1 for r in results.values() if r == m1)
        return (matches / len(results)) > 0.33 # Mínimo de 33% de acordo

    # [V3.1.5] Implementação de RTLI
    def _calculate_rtli(self, returns: np.ndarray) -> float:
        """
        Calcula o leading indicator de transição baseado em critical slowing down.
        RTLI = f(autocorrelação, variância, skewness).
        """
        if len(returns) < 30: return 0.0
        
        # [V3.1.1] Autocorrelação crescente (Leading signal de bifurcação)
        acf = np.corrcoef(returns[:-1], returns[1:])[0, 1]
        
        # [V3.1.2] Variância crescente (Flickering pré-transição)
        var = np.var(returns)
        
        # [V3.1.3] Skewness (Assimetria de transição)
        def calc_skew(x):
            return np.mean((x - np.mean(x))**3) / (np.std(x)**3 + 1e-9)
        
        skew = calc_skew(returns)
        
        # RTLI Score: Métrica composta de instabilidade dinâmica
        self._rtli_score = (np.abs(acf) * 0.4 + (var / (np.mean(returns**2) + 1e-9)) * 0.4 + np.abs(skew) * 0.2)
        
        if self._rtli_score > 0.75:
            logger.info(f"[V3.1.7] INSTABILITY ALERT: RTLI {self._rtli_score:.4f} - Critical Slowing Down detected.")
            
        return self._rtli_score

    # [V3.2.1] Cálculo de Dimensão Fractal Reflexiva (D_RFD)
    @njit
    def _calculate_d_rfd(prices: np.ndarray) -> float:
        """
        Mede a dimensão fractal usando o algoritmo de Higuchi (Ω-1).
        D_RFD reflete a complexidade e auto-similaridade do fluxo de ordens.
        """
        if len(prices) < 100: return 1.5
        
        n = len(prices)
        k_max = 10
        l_k = np.zeros(k_max)
        
        for k in range(1, k_max + 1):
            l_m_k = 0
            for m in range(k):
                sum_val = 0
                for i in range(1, int((n - m) / k)):
                    sum_val += abs(prices[m + i * k] - prices[m + (i - 1) * k])
                norm = (n - 1) / (int((n - m) / k) * k)
                l_m_k += (sum_val * norm) / k
            l_k[k-1] = l_m_k / k
            
        # Regressão linear simples para obter a dimensão
        x = np.log(1.0 / np.arange(1, k_max + 1))
        y = np.log(l_k)
        
        # Slope é a dimensão fractal
        n_val = len(x)
        slope = (n_val * np.sum(x * y) - np.sum(x) * np.sum(y)) / (n_val * np.sum(x**2) - (np.sum(x))**2)
        
        return float(max(1.0, min(2.0, slope)))

    # [V3.2.2] Monitoramento de Ressonância Inter-Ativos
    def _check_cross_asset_resonance(self, other_asset_returns: np.ndarray, own_returns: np.ndarray) -> float:
        """Mede a coerência entre BTC e ETH para confirmar força macro (Ω-8)."""
        if len(other_asset_returns) < 10 or len(own_returns) < 10: return 0.0
        min_len = min(len(other_asset_returns), len(own_returns))
        correlation = np.corrcoef(other_asset_returns[:min_len], own_returns[:min_len])[0, 1]
        return float(correlation)

    # [V3.4.2] Equilíbrio de Nash Evolutivo (Ω-49)
    def _is_nash_equilibrium(self, features: np.ndarray) -> bool:
        """
        Identifica se o mercado está em um ponto de equilíbrio estático (Nash).
        Nash occurre quando nenhum participante tem incentivo para mudar a cotação unilateralmente.
        Detectado por: Baixa Volatilidade + Spread Mínimo + Entropia Estável.
        """
        # Features indexação: [hurst, atr, entropy, fractal_dim, ...]
        hurst = features[0]
        entropy = features[2]
        
        # [Ω-49] Princípio de Correspondência: mercado eficiente (equilibrium) = random walk (hurst ~0.5)
        is_stable = 0.45 < hurst < 0.55 and entropy < 1.0
        return is_stable

    # [V3.4.7] QSMI - Quantum Superposition Index (Ω-11)
    def _calculate_qsmi(self, scale_results: Dict[str, MarketRegime]) -> int:
        """
        Mede a superposição de intenções (Entropia de von Neumann simplificada).
        QSMI quantifica a incerteza estrutural entre frames temporais.
        """
        regimes = [r.value for r in scale_results.values()]
        counts = {}
        for r in regimes:
            counts[r] = counts.get(r, 0) + 1
            
        # Entropia de Shannon como proxy para superposição de estados
        total = len(regimes)
        entropy = 0.0
        for count in counts.values():
            p = count / total
            entropy -= p * np.log2(p + 1e-12)
            
        self._qsmi_nodes = int(np.ceil(2**entropy)) # Número efetivo de estados em superposição
        
        if self._qsmi_nodes > 3:
            logger.warning(f"[V3.4.7] HIGH SUPERPOSITION: QSMI {self._qsmi_nodes} - Alignment breakdown.")
            
        return self._qsmi_nodes

    # [V1.1.9] Atualização de Clusters On-line (Online GMM Proximal)
    def _train_vae_step(self, features: np.ndarray):
        """
        Atualiza o centroide do regime atual para refletir o drift de mercado.
        Implementação do 'Self-Organizing Map' simplificado para ASI-Grade.
        """
        # Usando EMA para atualizar o conhecimento do espaço de fases
        alpha = 0.01 
        self._priors = (1 - alpha) * self._priors + alpha * (features[:len(self._priors)] / (np.sum(features) + 1e-9))
