"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — DATA ENGINE                           ║
║      Agregador central de dados de mercado em tempo real                    ║
║                                                                              ║
║  Coleta, organiza e distribui dados para todos os agentes neurais.          ║
║  É o SISTEMA NERVOSO SENSORIAL da ASI.                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
import threading
import time
from datetime import datetime, timezone
from typing import Optional, Dict
from collections import deque

from market.mt5_bridge import MT5Bridge
from config.exchange_config import PRIMARY_TIMEFRAMES, CONTEXT_TIMEFRAMES, BARS_TO_LOAD
from config.settings import MAIN_LOOP_INTERVAL_MS
from utils.logger import log
from utils.math_tools import MathEngine
from utils.decorators import timed, catch_and_log
from cpp.asi_bridge import CPP_CORE


class MarketSnapshot:
    """
    Snapshot completo do mercado em um instante.
    Passado para os agentes neurais como a "percepção" do mundo.
    """

    def __init__(self):
        self.timestamp = datetime.now(timezone.utc)
        self.tick = None                 # Tick mais recente
        self.candles = {}                # {timeframe: dict com OHLCV arrays}
        self.book = None                 # Book de ofertas
        self.indicators = {}             # Indicadores calculados
        self.account = None              # Info da conta
        self.symbol_info = None          # Info do símbolo
        self.metadata = {}               # Metadados extras
        self.raw_timestamp = int(self.timestamp.timestamp() * 1000) # MS timestamp para executor
        self._price_history_ref = []     # Referência para histórico de preços (Phase Ω-Extreme)

    def get_recent_prices(self, count: int = 100) -> np.ndarray:
        """Retorna os últimos N preços do histórico fixado no snapshot."""
        if not self._price_history_ref:
            return np.array([], dtype=np.float64)
        prices = list(self._price_history_ref)
        if len(prices) < count:
            return np.array(prices, dtype=np.float64)
        return np.array(prices[-count:], dtype=np.float64)

    @property
    def price(self) -> float:
        """Preço mid atual."""
        if self.tick:
            return self.tick.get("mid", 0.0)
        return 0.0

    @property
    def bid(self) -> float:
        if self.tick:
            return self.tick.get("bid", 0.0)
        return 0.0

    @property
    def ask(self) -> float:
        if self.tick:
            return self.tick.get("ask", 0.0)
        return 0.0

    @property
    def spread(self) -> float:
        if self.tick:
            return self.tick.get("spread", 0.0)
        return 0.0

    @property
    def recent_ticks(self) -> list:
        """Retorna lista de ticks recentes salvos no metadata."""
        return self.metadata.get("recent_ticks", [])

    @property
    def m1_closes(self) -> np.ndarray:
        """Atalho para closes de M1."""
        return self.candles.get("M1", {}).get("close", np.array([]))

    @property
    def m5_closes(self) -> np.ndarray:
        """Atalho para closes de M5."""
        return self.candles.get("M5", {}).get("close", np.array([]))

    @property
    def close(self) -> np.ndarray:
        return self.candles.get("M1", {}).get("close", np.array([]))

    @property
    def high(self) -> np.ndarray:
        return self.candles.get("M1", {}).get("high", np.array([]))

    @property
    def low(self) -> np.ndarray:
        return self.candles.get("M1", {}).get("low", np.array([]))

    @property
    def open(self) -> np.ndarray:
        return self.candles.get("M1", {}).get("open", np.array([]))

    @property
    def volume(self) -> np.ndarray:
        return self.candles.get("M1", {}).get("tick_volume", np.array([]))

    @property
    def atr(self) -> float:
        atr_arr = self.indicators.get("M1_atr_14", np.array([0.0]))
        return float(atr_arr[-1]) if len(atr_arr) > 0 else 0.0


class DataEngine:
    """
    Motor de Dados da ASI — coleta, processa e distribui dados de mercado.

    Responsabilidades:
    1. Coletar ticks, candles multi-TF, book em tempo real
    2. Calcular indicadores base (EMAs, ATR, VWAP, RSI, etc.)
    3. Manter buffers circulares para análise histórica rápida
    4. Criar snapshots atômicos do mercado para os agentes
    """

    def __init__(self, bridge: MT5Bridge):
        self.bridge = bridge
        self.math = MathEngine()
        self._lock = threading.Lock()

        # Buffers de dados
        self._candle_cache = {}          # {timeframe: dict}
        self._indicator_cache = {}       # {nome: array}
        self._tick_history = deque(maxlen=50000)
        self._price_history = deque(maxlen=100000)

        # Timestamps de última atualização
        self._last_update = {}
        self._snapshot_count = 0

        # PHASE Ω-EXTREME: Lorentz Clock & Relativistic Dilation
        self.lorentz_dilation = 1.0
        self.internal_clock_total = 0.0
        self.market_kinetic_energy = 0.0
        
        # ═══ BACKGROUND WORKER (Zero-Latency Architecture) ═══
        self._worker_running = True
        self._worker_thread = threading.Thread(target=self._background_worker, daemon=True)
        
        # OMEGA-CLASS: Initialize Liquid State Reservoir
        CPP_CORE.init_reservoir(n_neurons=500, spectral_radius=0.95, connectivity=0.1)
        log.omega("🌊 Liquid State Reservoir (500 neurons) INITIALIZED")
        
        self._worker_thread.start()

    def shutdown(self):
        """Para o worker de background."""
        self._worker_running = False

    # ═══════════════════════════════════════════════════════════
    #  COLETA DE DADOS (LATÊNCIA ZERO MÁXIMA)
    # ═══════════════════════════════════════════════════════════

    @timed(log_threshold_ms=20)  # Threshold ultra-baixo: 20ms
    def update(self) -> Optional[MarketSnapshot]:
        """
        Ciclo de atualização principal (Instântaneo).
        Coleta apenas dados de sub-milissegundo (tick/book) e 
        constrói o snapshot com os dados pré-calculados em background.
        """
        if not self.bridge.is_alive():
            return None

        snapshot = MarketSnapshot()

        # 1. Tick atual (Via HFT Socket ou MT5 Memory, ultra-rápido)
        snapshot.tick = self.bridge.get_tick()
        if snapshot.tick:
            self._tick_history.append(snapshot.tick)
            self._price_history.append(snapshot.tick["mid"])
            
            # OMEGA-CLASS: Perturb Liquid State Reservoir with raw tick
            # Inputs: [bid, ask, last, volume, spread, velocity, ...]
            v_sum = list(self._price_history)[-5:] if len(self._price_history) >= 5 else [snapshot.tick["mid"]] * 5
            velocity = np.diff(v_sum).mean() if len(v_sum) > 1 else 0.0
            
            inputs = np.array([
                snapshot.tick["bid"], snapshot.tick["ask"], 
                snapshot.tick["last"], snapshot.tick["volume"],
                snapshot.tick["ask"] - snapshot.tick["bid"], # spread
                velocity,
                np.log(snapshot.tick["volume"] + 1.0)
            ], dtype=np.float64)
            
            CPP_CORE.perturb_reservoir(inputs)
            # Retira ondas residuais como indicadores sintéticos
            snapshot.metadata["reservoir_waves"] = CPP_CORE.read_reservoir_output(10)

            # PHASE Ω-EXTREME: Lorentz Clock Update
            # Usamos a volatilidade GK recente e o volume do tick
            gk_vol = 0.0
            if "M1_gk_vol" in self._indicator_cache:
                gk_vol = self._indicator_cache["M1_gk_vol"][-1]
            
            lorentz = CPP_CORE.lorentz_clock_update(
                volatility=gk_vol,
                volume=snapshot.tick["volume"],
                physical_dt=MAIN_LOOP_INTERVAL_MS / 1000.0
            )
            
            if lorentz:
                self.lorentz_dilation = lorentz["dilation"]
                self.internal_clock_total += lorentz["internal_dt"]
                self.market_kinetic_energy = lorentz["energy"]
                
                snapshot.metadata["lorentz_dilation"] = self.lorentz_dilation
                snapshot.metadata["internal_clock"] = self.internal_clock_total

        # 2. Book de ofertas (Rápido)
        snapshot.book = self.bridge.get_book()

        # 3. Account & Symbol info (Cache na bridge)
        snapshot.account = self.bridge.get_account_info()
        snapshot.symbol_info = self.bridge.get_symbol_info()

        # [CRITICAL SYNCHRONIZATION OMEGA]
        # Aguardar que o background worker tenha calculado o primeiro frame.
        # Sem isso, a ASI operaria às cegas com um cache {} (cego/inconsciente).
        while not self._indicator_cache and self._worker_running:
            time.sleep(0.1)

        # 4. Dados pesados (Candles e Indicadores) puxados do CACHE com lock zero-copy
        with self._lock:
            snapshot.candles = dict(self._candle_cache)
            snapshot.indicators = dict(self._indicator_cache)

        # Metadata
        self._snapshot_count += 1
        snapshot._price_history_ref = list(self._price_history) # Fixar histórico para o snapshot
        snapshot.metadata = {
            "snapshot_id": self._snapshot_count,
            "tick_buffer_size": len(self._tick_history),
            "price_buffer_size": len(self._price_history),
            "recent_ticks": list(self._tick_history)[-200:] if self._tick_history else []
        }

        return snapshot

    # ═══════════════════════════════════════════════════════════
    #  BACKGROUND WORKER (Carga Pesada Assíncrona)
    # ═══════════════════════════════════════════════════════════

    def _background_worker(self):
        """
        Thread assíncrona que puxa candles multi-timeframe e calcula
        todos os indicadores matemáticos complexos sem travar o loop principal.
        """
        log.omega("⚡ DataEngine Background Worker: ONLINE")
        
        while self._worker_running:
            try:
                if not self.bridge.is_alive():
                    time.sleep(1)
                    continue
                
                start_time = time.perf_counter()
                
                # Snapshot local para cálculo
                local_snapshot = MarketSnapshot()
                
                # 1. Atualizar Candles
                new_candles = {}
                for tf in PRIMARY_TIMEFRAMES + CONTEXT_TIMEFRAMES:
                    candles = self.bridge.get_candles_as_dict(tf)
                    if candles is not None:
                        new_candles[tf] = candles
                        local_snapshot.candles[tf] = candles
                
                # 2. Computar Indicadores Pesados
                new_indicators = self._compute_indicators(local_snapshot)
                
                # 3. Swap Atômico no Cache (Thread-Safe)
                with self._lock:
                    self._candle_cache.update(new_candles)
                    self._indicator_cache.update(new_indicators)
                
                # Dormir para evitar CPU 100%, calculando ~10x por segundo
                elapsed = time.perf_counter() - start_time
                time.sleep(max(0.01, 0.1 - elapsed))
                
            except Exception as e:
                log.error(f"❌ Erro no DataEngine Background Worker: {e}")
                time.sleep(1)

    # ═══════════════════════════════════════════════════════════
    #  CÁLCULO DE INDICADORES
    # ═══════════════════════════════════════════════════════════

    @catch_and_log(default_return={})
    def _compute_indicators(self, snapshot: MarketSnapshot) -> dict:
        """
        Calcula todos os indicadores base.
        Estes alimentam os agentes neurais.
        """
        indicators = {}

        for tf in PRIMARY_TIMEFRAMES:
            candles = snapshot.candles.get(tf)
            if candles is None:
                continue

            close = candles["close"]
            high = candles["high"]
            low = candles["low"]
            volume = candles["tick_volume"]
            open_ = candles["open"]

            if len(close) < 30:
                continue

            prefix = f"{tf}_"

            # ═══ EMAs ═══
            indicators[f"{prefix}ema_9"] = CPP_CORE.ema(close, 9)
            indicators[f"{prefix}ema_21"] = CPP_CORE.ema(close, 21)
            indicators[f"{prefix}ema_50"] = CPP_CORE.ema(close, 50)
            indicators[f"{prefix}ema_200"] = CPP_CORE.ema(close, 200)

            # ═══ ATR ═══
            indicators[f"{prefix}atr_14"] = CPP_CORE.atr(high, low, close, 14)

            # ═══ RSI (via C++) ═══
            indicators[f"{prefix}rsi_14"] = CPP_CORE.rsi(close, 14)

            # ═══ MACD ═══
            macd_line, signal_line, histogram = CPP_CORE.macd(close, fast=12, slow=26, signal=9)
            indicators[f"{prefix}macd"] = macd_line
            indicators[f"{prefix}macd_signal"] = signal_line
            indicators[f"{prefix}macd_histogram"] = histogram

            # ═══ Bollinger Bands ═══
            bb_upper, bb_middle, bb_lower, bb_width = CPP_CORE.bollinger(close, period=20, num_std=2.0)
            indicators[f"{prefix}bb_upper"] = bb_upper
            indicators[f"{prefix}bb_middle"] = bb_middle
            indicators[f"{prefix}bb_lower"] = bb_lower
            indicators[f"{prefix}bb_width"] = bb_width

            # ═══ VWAP ═══
            indicators[f"{prefix}vwap"] = CPP_CORE.vwap(close, volume)

            # ═══ Z-Score de preço ═══
            indicators[f"{prefix}price_zscore"] = CPP_CORE.zscore(close, 20)

            # ═══ Hurst Exponent (regime) ═══
            indicators[f"{prefix}hurst"] = CPP_CORE.hurst_exponent(close)

            # ═══ Shannon Entropy ═══
            indicators[f"{prefix}entropy"] = CPP_CORE.shannon_entropy(close, bins=50)

            # ═══ Volume Profile ═══
            indicators[f"{prefix}volume_sma_20"] = np.convolve(
                volume, np.ones(20)/20, mode='same'
            )
            indicators[f"{prefix}volume_ratio"] = np.where(
                indicators[f"{prefix}volume_sma_20"] > 0,
                volume / indicators[f"{prefix}volume_sma_20"],
                1.0
            )

            # ═══ Garman-Klass Volatility ═══
            indicators[f"{prefix}gk_vol"] = self.math.garman_klass_volatility(
                open_, high, low, close
            )

            # ═══ Support/Resistance ═══
            indicators[f"{prefix}sr_levels"] = self.math.support_resistance_levels(
                high, low, close
            )

        return indicators


    # ═══════════════════════════════════════════════════════════
    #  DADOS HISTÓRICOS RÁPIDOS
    # ═══════════════════════════════════════════════════════════

    def get_recent_prices(self, count: int = 100) -> np.ndarray:
        """Últimos N preços do buffer."""
        prices = list(self._price_history)
        if len(prices) < count:
            return np.array(prices, dtype=np.float64)
        return np.array(prices[-count:], dtype=np.float64)

    def get_recent_ticks(self, count: int = 100) -> list:
        """Últimos N ticks do buffer."""
        ticks = list(self._tick_history)
        return ticks[-count:] if len(ticks) >= count else ticks

    def get_candle_data(self, timeframe: str) -> Optional[dict]:
        """Dados de candle em cache para um timeframe."""
        return self._candle_cache.get(timeframe)
