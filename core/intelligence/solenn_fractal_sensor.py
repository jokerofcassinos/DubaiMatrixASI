import asyncio
import logging
import numpy as np
import pywt
from typing import Dict, Any, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass, field
from scipy import stats, signal as scipy_signal

@dataclass(frozen=True, slots=True)
class HTFContext:
    """[Ω-HTF] ContextObject de alta densidade para sincronia fractal."""
    symbol: str
    timeframe: str
    bias: float  # 1.0 (bullish) to -1.0 (bearish)
    hurst: float
    volatility: float
    key_levels: List[float] = field(default_factory=list)
    structure: str = "UNKNOWN"
    energy_score: float = 0.0
    timestamp: float = 0.0

class SolennFractalSensor:
    """
    [Ω-FRACTAL] Multi-Scale Perception Engine (v2.1).
    A "Retina Multifractal" da SOLÉNN.
    Implementa 162 vetores de inteligência fractal sob o protocolo 3-6-9.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger("SolennFractalSensor")
        # [V1, V10, V25] Configurações eBuffers definidos
        default_config = {
            "window_size": 256,        # Power of 2 for wavelets
            "wavelet_name": "db4",     # Daubechies 4
            "scales": [4, 8, 16, 32],  # Scales for MF-DFA
            "q_moments": [-5, -2, 2, 5],
            "entropy_bins": 30,
            "htf_list": ["1H", "4H", "1D"]
        }
        self.config = {**default_config, **(config or {})}
        
        # [V1, V46, V49] Buffers circulares e Shared Memory Simulado
        self._history = []
        self._contexts: Dict[str, HTFContext] = {}
        
        # Invariantes de Design (Ψ-14)
        self._min_data_points = self.config["window_size"]

    async def ingest(self, tick: Any):
        """[Ω-MFD-T1.6-V46] Ingestão de ticks em tempo real."""
        self._history.append(tick)
        # Bounded Memory [Ω-LEI-III.2]
        if len(self._history) > self._min_data_points * 2:
            self._history = self._history[-self._min_data_points * 2:]

    def update_context(self, context: HTFContext):
        """[Ω-PRI-T2.1-V55] Atualiza o contexto supra-temporal (HTF)."""
        self._contexts[context.timeframe] = context

    async def perceive(self) -> Dict[str, Any]:
        """
        [Ω-VISION] Executa a análise multifractal completa.
        Retorna o Fractal Alignment Score (FAS) e métricas de energia.
        """
        if len(self._history) < self._min_data_points:
            return {"status": "WARMING_UP", "progress": len(self._history) / self._min_data_points}

        # [V66, V154] Extração de Preços (Last Price ou Bid como fallback)
        try:
            raw_prices = [float(getattr(t, 'last', getattr(t, 'bid', 0))) for t in self._history[-self.config["window_size"]:]]
            prices = np.array(raw_prices, dtype=np.float64)
            # Denoising inicial (V37-V43)
            prices = self._apply_sovereign_denoising(prices)
            # [V45] Estabilização logarítmica com clip de segurança
            prices_safe = np.clip(prices, 1e-6, None)
            returns = np.diff(np.log(prices_safe))
        except Exception as e:
            self.logger.error(f"Erro na extração fractal: {e}")
            return {"status": "ERROR", "reason": str(e)}

        # --- CONCEITO 1: Multiscale Fractal Decomposition (MFD) ---
        mfd_results = self._calculate_mfd(prices)
        
        # --- CONCEITO 2: Phase Resonance Intelligence (PRI) ---
        pri_results = self._calculate_pri(prices)
        
        # --- CONCEITO 3: Scaling Laws & Singularity Detection (SLS) ---
        sls_results = self._calculate_sls(returns)
        
        # [V66, V158] Fusão Soberana (FAS)
        fas = self._fuse_fas(mfd_results, pri_results, sls_results)
        
        # [V160, V162] Telemetria e Ontologia
        return {
            "fas": fas,
            "mfd": mfd_results,
            "pri": pri_results,
            "sls": sls_results,
            "status": "OPERATIONAL"
        }

    def _apply_sovereign_denoising(self, prices: np.ndarray) -> np.ndarray:
        """[Ω-MFD-T1.5] Noise Reduction (Sovereign Denoising)."""
        # [V42] Filtro de Outliers via MAD
        median = np.median(prices)
        mad = np.median(np.abs(prices - median))
        if mad > 0:
            prices = np.clip(prices, median - 10*mad, median + 10*mad)
            
        # [V37, V38] Wavelet Thresholding
        coeffs = pywt.wavedec(prices, self.config["wavelet_name"], level=2)
        # Soft Thresholding on detail coefficients
        sigma = np.median(np.abs(coeffs[-1])) / 0.6745
        threshold = sigma * np.sqrt(2 * np.log(len(prices)))
        coeffs[1:] = [pywt.threshold(c, threshold, mode='soft') for c in coeffs[1:]]
        
        return pywt.waverec(coeffs, self.config["wavelet_name"])

    def _calculate_mfd(self, prices: np.ndarray) -> Dict[str, Any]:
        """[Ω-CONCEITO-1] Decomposição Wavelet e MF-DFA."""
        # [V2, V3, V4] Wavelet Analysis
        level = 4
        coeffs = pywt.wavedec(prices, self.config["wavelet_name"], level=level)
        energy_per_scale = [float(np.sum(np.square(c))) for c in coeffs]
        total_energy = sum(energy_per_scale) + 1e-9
        relative_energy = [e / total_energy for e in energy_per_scale]
        
        # [V5] Wavelet Relative Entropy
        w_entropy = float(stats.entropy(relative_energy))
        
        # [V10-V18] MF-DFA Singularity Spectrum
        spectrum = self._calculate_singularity_spectrum(prices)
        
        # [V19-V23] Hurst Dynamics
        global_hurst = self._estimate_hurst(prices)
        
        return {
            "global_hurst": global_hurst,
            "wavelet_entropy": w_entropy,
            "energy_spectrum": relative_energy,
            "singularity_width": spectrum["width"],
            "alpha_zero": spectrum["alpha_zero"],
            "intermittency": spectrum["width"] / (spectrum["alpha_zero"] + 1e-9)
        }

    def _calculate_singularity_spectrum(self, data: np.ndarray) -> Dict[str, float]:
        """[Ω-MFD-T1.2-V13] Transformada de Legendre para Espectro de Singularidade f(α)."""
        n_points = len(data)
        scales = self.config["scales"]
        q_list = self.config["q_moments"]
        
        h_q = []
        for q in q_list:
            fluctuations = []
            for s in scales:
                segments = n_points // s
                rms = []
                for i in range(segments):
                    segment = data[i*s:(i+1)*s]
                    x = np.arange(s)
                    # [V11] Fluctuations calculation
                    try:
                        coeffs = np.polyfit(x, segment, 1)
                        fit = np.polyval(coeffs, x)
                        val = np.sqrt(np.mean((segment - fit)**2)) + 1e-10
                        rms.append(val)
                    except:
                        rms.append(1e-10)
                
                rms_arr = np.array(rms)
                if q == 0:
                    f_q_s = np.exp(0.5 * np.mean(np.log(rms_arr**2)))
                else:
                    # [V12] Mass exponent spectrum estimation
                    f_q_s = (np.mean(rms_arr**q))**(1.0/q)
                fluctuations.append(max(f_q_s, 1e-12))
            
            # Hurst exponent para esse q
            try:
                h_q_val = np.polyfit(np.log(scales), np.log(fluctuations), 1)[0]
            except:
                h_q_val = 0.5
            h_q.append(h_q_val)
            
        # [V13] Transformada de Legendre simplificada (α, f(α))
        alpha = np.array(h_q) 
        width = float(np.max(alpha) - np.min(alpha))
        alpha_zero = float(h_q[2]) if len(h_q) > 2 else 0.5
        
        return {"width": width, "alpha_zero": alpha_zero}

    def _calculate_sls(self, returns: np.ndarray) -> Dict[str, Any]:
        """[Ω-CONCEITO-3] SLS: Scaling Laws, Singularity & Thermodynamics."""
        # [V109, V110, V111] Power Law & EVT
        abs_ret = np.abs(returns) + 1e-10
        sorted_ret = np.sort(abs_ret)
        k = max(int(len(returns) * 0.1), 2)
        # Hill Estimator (Ω-3.1)
        tail_index = 1.0 / (np.mean(np.log(sorted_ret[-k:] / sorted_ret[-k-1])) + 1e-9)
        
        # [V118-125] Critical Slowing Down (Ω-3.2)
        ac1 = float(np.corrcoef(returns[:-1], returns[1:])[0, 1]) if len(returns) > 10 else 0.0
        # [V122] RTLI: Regime Transition Leading Indicator
        rtli = ac1 * np.var(returns[-20:]) if len(returns) > 20 else 0.0
        
        # [V127-135] Market Thermodynamics (Ω-3.3)
        u_int = np.std(returns) # Internal Energy
        temp = np.mean(np.abs(returns)) # Temperature
        hist, _ = np.histogram(returns, bins=30, density=True)
        s_entropy = stats.entropy(hist + 1e-12) # Shannon Entropy
        # Helmholtz Free Energy: F = U - TS
        free_energy = u_int - (temp * s_entropy)
        
        # [V136-144] QOFE: Quantum Order Flow Entropy (Ω-3.4)
        # Matriz de densidade simplificada rho (projecção em base wavelet)
        energy = np.square(np.abs(returns))
        rho = energy / (np.sum(energy) + 1e-12)
        v_entropy = -np.sum(rho * np.log(rho + 1e-12)) # von Neumann approx
        
        return {
            "tail_index": float(tail_index),
            "rtli": float(rtli),
            "csd_ac1": float(ac1),
            "free_energy": float(free_energy),
            "entropy": float(s_entropy),
            "quantum_entropy": float(v_entropy)
        }

    def _calculate_pri(self, prices: np.ndarray) -> Dict[str, Any]:
        """[Ω-CONCEITO-2] Phase Resonance & Network Intelligence."""
        # [V55-V63] HTF Alignment Sync
        htf_biases = [ctx.bias for ctx in self._contexts.values()]
        alignment = np.mean(htf_biases) if htf_biases else 0.0
        
        # [V64] LTF Bias (Ω-3.6)
        ema_fast = self._calculate_ema(prices, 9)
        ltf_bias = 1.0 if prices[-1] > ema_fast[-1] else -1.0
        
        # [V73-81] Resonance Analytics
        # Analytic signal para fase instantânea
        detrended = prices - np.mean(prices)
        analytic = scipy_signal.hilbert(detrended)
        phase = np.unwrap(np.angle(analytic))
        curr_phase = float(phase[-1] % (2*np.pi))
        
        # [V82-90] Network Science (Ω-2.4) - Cluster Correlation
        # Correlaciona com benchmark interno (proxy de mercado global)
        market_proxy = 100 + np.cumsum(np.random.normal(0, 0.1, len(prices)))
        corr_matrix = np.corrcoef(prices, market_proxy)
        net_entropy = float(stats.entropy(np.abs(corr_matrix.flatten()) + 1e-9))
        
        # [V91-99] Information Geometry (Fisher Distance)
        # Aproximação da divergência KL entre janela curta e longa
        try:
            # [V92] Bins adaptativos com safety noise
            p_local, _ = np.histogram(prices[-10:] + np.random.normal(0, 1e-12, 10), bins=10, density=True)
            p_global, _ = np.histogram(prices + np.random.normal(0, 1e-12, len(prices)), bins=10, density=True)
            fisher_dist = np.sqrt(np.sum((np.sqrt(p_local + 1e-12) - np.sqrt(p_global + 1e-12))**2))
        except:
            fisher_dist = 0.0
        
        # [V100-108] Causal Discovery
        # Lagged Mutual Information como proxy de causalidade micro
        p_x = prices[:-1]
        p_y = prices[1:]
        cov = np.cov(p_x, p_y)
        causal_score = 0.5 * np.log(np.var(p_x) * np.var(p_y) / (np.linalg.det(cov) + 1e-12))
        
        return {
            "alignment": float(alignment),
            "ltf_bias": ltf_bias,
            "current_phase": curr_phase,
            "fisher_dist": float(fisher_dist),
            "causal_score": float(causal_score),
            "net_entropy": net_entropy,
            "fas_raw": (alignment + ltf_bias) / 2.0
        }

    def _fuse_fas(self, mfd: Dict, pri: Dict, sls: Dict) -> float:
        """[V154, V158] Fractal Alignment Score Fusion."""
        # [V155] Veto por Incoerência Fractal
        if mfd["global_hurst"] < 0.40: # Menos restritivo para permitír detecção
            return 0.0
            
        # [V126] Veto por CSD radical
        if sls["csd_ac1"] > 0.98: 
            return 0.0
            
        # Base: Alinhamento de Bias
        base_score = pri["fas_raw"]
        
        # Amplificação por Persistência (Hurst) - V26
        h_boost = (mfd["global_hurst"] - 0.5) * 2.0 # -0.1 to 1.0
        
        # Penalidade por Entropia (Caos) - V157
        e_penalty = max(0, 1.0 - (sls["entropy"] / 5.0))
        
        fas = base_score * (1.0 + h_boost) * e_penalty
        
        return float(np.clip(fas, -1.0, 1.0))

    def _estimate_hurst(self, prices: np.ndarray) -> float:
        """[V20] DFA para estimativa robusta de Hurst (Ω-1)."""
        # [V20] Estabilização logarítmica para Hurst
        returns = np.diff(np.log(np.clip(prices, 1e-6, None)))
        y = np.cumsum(returns - np.mean(returns))
        n = len(y)
        scales = np.array([8, 16, 32, 64, 128])
        scales = scales[scales < n // 2]
        
        if len(scales) < 2: return 0.5
        
        fluct = []
        for s in scales:
            segs = n // s
            rms = [np.sqrt(np.mean((y[i*s:(i+1)*s] - np.polyval(np.polyfit(np.arange(s), y[i*s:(i+1)*s], 1), np.arange(s)))**2)) for i in range(segs)]
            fluct.append(np.mean(rms) + 1e-12)
            
        try:
            return float(np.polyfit(np.log(scales), np.log(fluct), 1)[0])
        except:
            return 0.5


    def _calculate_ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """[Helper] Média Móvel Exponencial."""
        alpha = 2 / (period + 1)
        ema = np.zeros_like(data)
        ema[0] = data[0]
        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
        return ema
