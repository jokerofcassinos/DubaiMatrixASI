"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — C++ FFI BRIDGE                             ║
║     Interface Python ↔ C++ via ctypes para módulos de alta performance    ║
║                                                                              ║
║  Carrega asi_core.dll e expõe todas as funções C++ como métodos Python    ║
║  com conversão automática numpy ↔ C arrays.                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import ctypes
import ctypes.util
import numpy as np
import os
import sys
from typing import Optional, Tuple

from utils.logger import log

# ═══ STRUCT DEFINITIONS (espelhando asi_core.h) ═══

class TickData(ctypes.Structure):
    _fields_ = [
        ("bid", ctypes.c_double),
        ("ask", ctypes.c_double),
        ("last", ctypes.c_double),
        ("volume", ctypes.c_double),
        ("time_msc", ctypes.c_int64),
    ]

class OrderFlowResult(ctypes.Structure):
    _fields_ = [
        ("cumulative_delta", ctypes.c_double),
        ("buy_volume", ctypes.c_double),
        ("sell_volume", ctypes.c_double),
        ("order_imbalance", ctypes.c_double),
        ("tick_velocity", ctypes.c_double),
        ("is_absorption", ctypes.c_int),
        ("is_exhaustion", ctypes.c_int),
        ("volume_climax_score", ctypes.c_double),
    ]

class AgentSignal(ctypes.Structure):
    _fields_ = [
        ("signal", ctypes.c_double),
        ("confidence", ctypes.c_double),
        ("weight", ctypes.c_double),
    ]

class QuantumState(ctypes.Structure):
    _fields_ = [
        ("raw_signal", ctypes.c_double),
        ("coherence", ctypes.c_double),
        ("weighted_signal", ctypes.c_double),
        ("energy", ctypes.c_double),
        ("should_collapse", ctypes.c_int),
    ]

class PhaseSpaceResultC(ctypes.Structure):
    _fields_ = [
        ("orbit_radius", ctypes.c_double),
        ("global_orbit", ctypes.c_double),
        ("compression_ratio", ctypes.c_double),
        ("is_compressed", ctypes.c_int),
    ]

class SwingResultC(ctypes.Structure):
    _fields_ = [
        ("index", ctypes.c_int),
        ("price", ctypes.c_double),
    ]

class MonteCarloInputC(ctypes.Structure):
    _fields_ = [
        ("S0", ctypes.c_double),
        ("mu", ctypes.c_double),
        ("sigma", ctypes.c_double),
        ("jump_intensity", ctypes.c_double),
        ("jump_mean", ctypes.c_double),
        ("jump_std", ctypes.c_double),
        ("dt", ctypes.c_double),
        ("n_sims", ctypes.c_int),
        ("n_steps", ctypes.c_int),
        ("stop_loss", ctypes.c_double),
        ("take_profit", ctypes.c_double),
        ("is_buy", ctypes.c_bool),
    ]

class MonteCarloOutputC(ctypes.Structure):
    _fields_ = [
        ("win_prob", ctypes.c_double),
        ("expected_return", ctypes.c_double),
        ("var_95", ctypes.c_double),
        ("cvar_95", ctypes.c_double),
        ("simulation_time_ms", ctypes.c_double),
    ]


class CppASICore:
    """
    Interface Python para o módulo C++ de alta performance.
    Carrega a DLL compilada e expõe as funções como métodos Python.
    """

    def __init__(self):
        self._lib = None
        self._loaded = False
        self._load_library()

    def _load_library(self):
        """Tenta carregar a DLL compilada."""
        dll_name = "asi_core.dll" if sys.platform == "win32" else "libasi_core.so"
        
        # Adicionar runtime paths do MSYS2 para resolver dependências (libstdc++, libgcc, etc.)
        msys2_paths = [
            r"D:\msys64\ucrt64\bin",
            r"D:\msys64\mingw64\bin",
            r"C:\msys64\ucrt64\bin",
            r"C:\msys64\mingw64\bin",
        ]
        for mpath in msys2_paths:
            if os.path.isdir(mpath):
                try:
                    os.add_dll_directory(mpath)
                except (OSError, AttributeError):
                    os.environ["PATH"] = mpath + ";" + os.environ.get("PATH", "")
        
        # Possíveis locais da DLL
        search_paths = [
            os.path.join(os.path.dirname(__file__), "..", dll_name),        # raiz do projeto
            os.path.join(os.path.dirname(__file__), "..", "cpp", "build", "Release", dll_name),
            os.path.join(os.path.dirname(__file__), "..", "cpp", "build", dll_name),
            os.path.join(os.path.dirname(__file__), "..", "cpp", "build", "Debug", dll_name),
        ]

        for path in search_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                try:
                    self._lib = ctypes.CDLL(abs_path)
                    self._setup_signatures()
                    self._loaded = True
                    log.omega(f"⚡ C++ ASI Core carregado: {abs_path}")
                    return
                except Exception as e:
                    log.warning(f"Falha ao carregar C++ DLL de {abs_path}: {e}")
        
        log.warning("⚠️ C++ ASI Core não encontrado — usando fallback Python (NumPy)")

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def _setup_signatures(self):
        """Configura as assinaturas de tipos das funções C."""
        lib = self._lib
        
        # EMA
        lib.asi_ema.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_double)]
        lib.asi_ema.restype = None
        
        # RSI
        lib.asi_rsi.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_double)]
        lib.asi_rsi.restype = None
        
        # ATR
        lib.asi_atr.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_double)]
        lib.asi_atr.restype = None

        # Bollinger
        lib.asi_bollinger.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int, ctypes.c_double,
                                      ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]
        lib.asi_bollinger.restype = None

        # MACD
        lib.asi_macd.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                  ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]
        lib.asi_macd.restype = None

        # VWAP
        lib.asi_vwap.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_int]
        lib.asi_vwap.restype = ctypes.c_double
        
        # Shannon Entropy
        lib.asi_shannon_entropy.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int]
        lib.asi_shannon_entropy.restype = ctypes.c_double
        
        # Hurst
        lib.asi_hurst_exponent.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
        lib.asi_hurst_exponent.restype = ctypes.c_double
        
        # Z-Score
        lib.asi_zscore.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_double)]
        lib.asi_zscore.restype = None

        # OrderFlow
        lib.asi_process_orderflow.argtypes = [ctypes.POINTER(TickData), ctypes.c_int, ctypes.POINTER(OrderFlowResult)]
        lib.asi_process_orderflow.restype = None

        # Signals
        lib.asi_aggregate_signals.argtypes = [ctypes.POINTER(AgentSignal), ctypes.c_int, ctypes.c_double, 
                                              ctypes.c_double, ctypes.c_double, ctypes.POINTER(QuantumState)]
        lib.asi_aggregate_signals.restype = None

        # Kelly
        lib.asi_kelly_criterion.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double]
        lib.asi_kelly_criterion.restype = ctypes.c_double

        # Lot Size
        lib.asi_optimal_lot_size.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double]
        lib.asi_optimal_lot_size.restype = ctypes.c_double

        # ═══ AGENT CLUSTER ENGINE ═══
        lib.asi_fractal_dimension.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int]
        lib.asi_fractal_dimension.restype = ctypes.c_double

        lib.asi_vpin_proxy.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double),
                                        ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int]
        lib.asi_vpin_proxy.restype = ctypes.c_double

        lib.asi_phase_space.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int,
                                         ctypes.POINTER(PhaseSpaceResultC)]
        lib.asi_phase_space.restype = None

        lib.asi_kurtosis.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
        lib.asi_kurtosis.restype = ctypes.c_double

        lib.asi_cross_scale_correlation.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int,
                                                     ctypes.POINTER(ctypes.c_double), ctypes.c_int]
        lib.asi_cross_scale_correlation.restype = ctypes.c_double

        lib.asi_tick_entropy.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int]
        lib.asi_tick_entropy.restype = ctypes.c_double

        # Latency Optimization (Phase 18)
        lib.asi_find_swings.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), 
                                        ctypes.c_int, ctypes.c_int, 
                                        ctypes.POINTER(SwingResultC), ctypes.POINTER(ctypes.c_int), 
                                        ctypes.POINTER(SwingResultC), ctypes.POINTER(ctypes.c_int)]
        lib.asi_find_swings.restype = ctypes.c_int

        lib.asi_navier_stokes_pressure.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), 
                                                ctypes.c_int, ctypes.POINTER(ctypes.c_double), 
                                                ctypes.POINTER(ctypes.c_double)]
        lib.asi_navier_stokes_pressure.restype = None

        lib.asi_calc_micro_variance.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
        lib.asi_calc_micro_variance.restype = ctypes.c_double

        lib.asi_monte_carlo_merton.argtypes = [ctypes.POINTER(MonteCarloInputC), ctypes.POINTER(MonteCarloOutputC)]
        lib.asi_monte_carlo_merton.restype = None

    # ═══ HELPER: numpy array → C pointer ═══
    @staticmethod
    def _ptr(arr: np.ndarray):
        """Converte numpy array para ponteiro ctypes."""
        return arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double))

    @staticmethod
    def _ensure_f64(arr) -> np.ndarray:
        """Garante que o array é float64 contíguo."""
        return np.ascontiguousarray(arr, dtype=np.float64)

    # ═══════════════════════════════════════════════════════════
    #  INDICADORES
    # ═══════════════════════════════════════════════════════════

    def ema(self, close: np.ndarray, period: int) -> np.ndarray:
        close = self._ensure_f64(close)
        out = np.zeros(len(close), dtype=np.float64)
        self._lib.asi_ema(self._ptr(close), len(close), period, self._ptr(out))
        return out

    def rsi(self, close: np.ndarray, period: int = 14) -> np.ndarray:
        close = self._ensure_f64(close)
        out = np.zeros(len(close), dtype=np.float64)
        self._lib.asi_rsi(self._ptr(close), len(close), period, self._ptr(out))
        return out

    def atr(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        high, low, close = self._ensure_f64(high), self._ensure_f64(low), self._ensure_f64(close)
        out = np.zeros(len(close), dtype=np.float64)
        self._lib.asi_atr(self._ptr(high), self._ptr(low), self._ptr(close), len(close), period, self._ptr(out))
        return out

    def bollinger(self, close: np.ndarray, period: int = 20, num_std: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        close = self._ensure_f64(close)
        n = len(close)
        upper = np.zeros(n, dtype=np.float64)
        middle = np.zeros(n, dtype=np.float64)
        lower = np.zeros(n, dtype=np.float64)
        width = np.zeros(n, dtype=np.float64)
        self._lib.asi_bollinger(self._ptr(close), n, period, num_std,
                                 self._ptr(upper), self._ptr(middle), self._ptr(lower), self._ptr(width))
        return upper, middle, lower, width

    def macd(self, close: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        close = self._ensure_f64(close)
        n = len(close)
        macd_line = np.zeros(n, dtype=np.float64)
        signal_line = np.zeros(n, dtype=np.float64)
        histogram = np.zeros(n, dtype=np.float64)
        self._lib.asi_macd(self._ptr(close), n, fast, slow, signal,
                            self._ptr(macd_line), self._ptr(signal_line), self._ptr(histogram))
        return macd_line, signal_line, histogram

    def vwap(self, close: np.ndarray, volume: np.ndarray) -> float:
        close, volume = self._ensure_f64(close), self._ensure_f64(volume)
        return self._lib.asi_vwap(self._ptr(close), self._ptr(volume), len(close))

    def shannon_entropy(self, data: np.ndarray, bins: int = 50) -> float:
        data = self._ensure_f64(data)
        return self._lib.asi_shannon_entropy(self._ptr(data), len(data), bins)

    def hurst_exponent(self, data: np.ndarray) -> float:
        data = self._ensure_f64(data)
        return self._lib.asi_hurst_exponent(self._ptr(data), len(data))

    def zscore(self, data: np.ndarray, window: int = 20) -> np.ndarray:
        data = self._ensure_f64(data)
        out = np.zeros(len(data), dtype=np.float64)
        self._lib.asi_zscore(self._ptr(data), len(data), window, self._ptr(out))
        return out

    # ═══════════════════════════════════════════════════════════
    #  ORDER FLOW
    # ═══════════════════════════════════════════════════════════

    def process_orderflow(self, ticks: list) -> dict:
        """Processa lista de dicts de ticks em C++."""
        count = len(ticks)
        if count == 0:
            return {}
        
        tick_array = (TickData * count)()
        for i, t in enumerate(ticks):
            tick_array[i].bid = t.get("bid", 0.0)
            tick_array[i].ask = t.get("ask", 0.0)
            tick_array[i].last = t.get("last", 0.0)
            tick_array[i].volume = t.get("volume", 0.0)
            tick_array[i].time_msc = t.get("time_msc", 0)

        result = OrderFlowResult()
        self._lib.asi_process_orderflow(tick_array, count, ctypes.byref(result))

        return {
            "cumulative_delta": result.cumulative_delta,
            "buy_volume": result.buy_volume,
            "sell_volume": result.sell_volume,
            "order_imbalance": result.order_imbalance,
            "tick_velocity": result.tick_velocity,
            "is_absorption": bool(result.is_absorption),
            "is_exhaustion": bool(result.is_exhaustion),
            "volume_climax_score": result.volume_climax_score,
        }

    # ═══════════════════════════════════════════════════════════
    #  SIGNAL AGGREGATION
    # ═══════════════════════════════════════════════════════════

    def aggregate_signals(self, signals: list, regime_weight: float = 1.0, 
                          signal_threshold: float = 0.3, coherence_threshold: float = 0.6) -> dict:
        """Agrega sinais de agentes neurais em C++."""
        count = len(signals)
        if count == 0:
            return {}

        sig_array = (AgentSignal * count)()
        for i, s in enumerate(signals):
            sig_array[i].signal = s.get("signal", 0.0)
            sig_array[i].confidence = s.get("confidence", 0.0)
            sig_array[i].weight = s.get("weight", 1.0)

        state = QuantumState()
        self._lib.asi_aggregate_signals(sig_array, count, regime_weight, 
                                         signal_threshold, coherence_threshold, 
                                         ctypes.byref(state))

        return {
            "raw_signal": state.raw_signal,
            "coherence": state.coherence,
            "weighted_signal": state.weighted_signal,
            "energy": state.energy,
            "should_collapse": bool(state.should_collapse),
        }

    # ═══════════════════════════════════════════════════════════
    #  RISK UTILITIES
    # ═══════════════════════════════════════════════════════════

    def kelly_criterion(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        return self._lib.asi_kelly_criterion(win_rate, avg_win, avg_loss)

    def optimal_lot_size(self, balance: float, risk_pct: float,
                          sl_distance: float, point_value: float) -> float:
        return self._lib.asi_optimal_lot_size(balance, risk_pct, sl_distance, point_value)

    # ═══════════════════════════════════════════════════════════
    #  AGENT CLUSTER ENGINE (C++ Accelerated)
    # ═══════════════════════════════════════════════════════════

    def fractal_dimension(self, data: np.ndarray, max_box: int = 64) -> float:
        data = self._ensure_f64(data)
        return self._lib.asi_fractal_dimension(self._ptr(data), len(data), max_box)

    def vpin_proxy(self, open_p: np.ndarray, close: np.ndarray, volume: np.ndarray, lookback: int = 5) -> float:
        open_p, close, volume = self._ensure_f64(open_p), self._ensure_f64(close), self._ensure_f64(volume)
        return self._lib.asi_vpin_proxy(self._ptr(open_p), self._ptr(close), self._ptr(volume), len(close), lookback)

    def phase_space(self, closes: np.ndarray, lookback: int = 10) -> dict:
        closes = self._ensure_f64(closes)
        result = PhaseSpaceResultC()
        self._lib.asi_phase_space(self._ptr(closes), len(closes), lookback, ctypes.byref(result))
        return {
            "orbit_radius": result.orbit_radius,
            "global_orbit": result.global_orbit,
            "compression_ratio": result.compression_ratio,
            "is_compressed": bool(result.is_compressed),
        }

    def kurtosis(self, data: np.ndarray) -> float:
        data = self._ensure_f64(data)
        return self._lib.asi_kurtosis(self._ptr(data), len(data))

    def cross_scale_correlation(self, series_a: np.ndarray, series_b: np.ndarray) -> float:
        series_a, series_b = self._ensure_f64(series_a), self._ensure_f64(series_b)
        return self._lib.asi_cross_scale_correlation(self._ptr(series_a), len(series_a), self._ptr(series_b), len(series_b))

    def tick_entropy(self, bids: np.ndarray, bins: int = 10) -> float:
        bids = self._ensure_f64(bids)
        return self._lib.asi_tick_entropy(self._ptr(bids), len(bids), bins)

    def find_swings(self, highs: np.ndarray, lows: np.ndarray, lookback: int = 5) -> Tuple[list, list]:
        highs = self._ensure_f64(highs)
        lows = self._ensure_f64(lows)
        n = len(highs)
        
        out_highs = (SwingResultC * 100)()
        out_lows = (SwingResultC * 100)()
        h_count = ctypes.c_int(0)
        l_count = ctypes.c_int(0)
        
        self._lib.asi_find_swings(self._ptr(highs), self._ptr(lows), n, lookback,
                                   out_highs, ctypes.byref(h_count),
                                   out_lows, ctypes.byref(l_count))
        
        sw_highs = [(out_highs[i].index, out_highs[i].price) for i in range(h_count.value)]
        sw_lows = [(out_lows[i].index, out_lows[i].price) for i in range(l_count.value)]
        return sw_highs, sw_lows

    def navier_stokes_pressure(self, bid_vols: np.ndarray, ask_vols: np.ndarray) -> Tuple[float, float]:
        bid_vols = self._ensure_f64(bid_vols)
        ask_vols = self._ensure_f64(ask_vols)
        ratio = ctypes.c_double(0.0)
        pressure = ctypes.c_double(0.0)
        self._lib.asi_navier_stokes_pressure(self._ptr(bid_vols), self._ptr(ask_vols), 
                                              len(bid_vols), ctypes.byref(ratio), 
                                              ctypes.byref(pressure))
        return ratio.value, pressure.value

    def calc_micro_variance(self, data: np.ndarray) -> float:
        data = self._ensure_f64(data)
        return self._lib.asi_calc_micro_variance(self._ptr(data), len(data))

    def monte_carlo_merton(self, params: dict) -> dict:
        inp = MonteCarloInputC()
        inp.S0 = params["S0"]
        inp.mu = params["mu"]
        inp.sigma = params["sigma"]
        inp.jump_intensity = params["jump_intensity"]
        inp.jump_mean = params["jump_mean"]
        inp.jump_std = params["jump_std"]
        inp.dt = params["dt"]
        inp.n_sims = params["n_sims"]
        inp.n_steps = params["n_steps"]
        inp.stop_loss = params["stop_loss"]
        inp.take_profit = params["take_profit"]
        inp.is_buy = params["is_buy"]
        
        out = MonteCarloOutputC()
        self._lib.asi_monte_carlo_merton(ctypes.byref(inp), ctypes.byref(out))
        
        return {
            "win_prob": out.win_prob,
            "expected_return": out.expected_return,
            "var_95": out.var_95,
            "cvar_95": out.cvar_95,
            "simulation_time_ms": out.simulation_time_ms
        }


# ═══ SINGLETON ═══
CPP_CORE = CppASICore()
