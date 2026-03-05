"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — MATH ENGINE                           ║
║        Ferramentas matemáticas de fronteira — wavelets, fractais,           ║
║               entropia, estatísticas avançadas, geometria                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import Optional, Tuple, List


class MathEngine:
    """
    Motor matemático da ASI — funções que nenhum indicador convencional oferece.
    Cada função é uma arma de análise que penetra camadas invisíveis do mercado.
    """

    # ═══════════════════════════════════════════════════════════
    #  ESTATÍSTICAS AVANÇADAS
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def zscore(data: np.ndarray, window: int = 20) -> np.ndarray:
        """
        Z-score rolling — detecta desvios extremos da média.
        Útil para identificar condições de sobre-compra/sobre-venda.
        """
        if len(data) < window:
            return np.zeros_like(data)
        mean = np.convolve(data, np.ones(window) / window, mode='same')
        # Rolling std manual para evitar edge effects
        std = np.array([
            np.std(data[max(0, i - window):i + 1]) if i >= window - 1 else 1.0
            for i in range(len(data))
        ])
        std[std == 0] = 1e-10  # Evitar divisão por zero
        return (data - mean) / std

    @staticmethod
    def rolling_correlation(x: np.ndarray, y: np.ndarray,
                            window: int = 20) -> np.ndarray:
        """Correlação rolling entre duas séries."""
        n = len(x)
        if n < window or len(y) < window:
            return np.zeros(n)

        result = np.zeros(n)
        for i in range(window - 1, n):
            x_win = x[i - window + 1:i + 1]
            y_win = y[i - window + 1:i + 1]
            if np.std(x_win) > 1e-10 and np.std(y_win) > 1e-10:
                result[i] = np.corrcoef(x_win, y_win)[0, 1]
        return result

    @staticmethod
    def exponential_moving_average(data: np.ndarray, period: int) -> np.ndarray:
        """EMA otimizada com numpy."""
        if len(data) == 0:
            return np.array([])
        alpha = 2.0 / (period + 1)
        ema = np.zeros_like(data, dtype=np.float64)
        ema[0] = data[0]
        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i - 1]
        return ema

    @staticmethod
    def weighted_moving_average(data: np.ndarray, period: int) -> np.ndarray:
        """WMA — dá mais peso aos dados recentes."""
        if len(data) < period:
            return np.full_like(data, np.nan, dtype=np.float64)
        weights = np.arange(1, period + 1, dtype=np.float64)
        weights /= weights.sum()
        result = np.full_like(data, np.nan, dtype=np.float64)
        for i in range(period - 1, len(data)):
            result[i] = np.dot(data[i - period + 1:i + 1], weights)
        return result

    # ═══════════════════════════════════════════════════════════
    #  ENTROPIA & TEORIA DA INFORMAÇÃO
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def shannon_entropy(data: np.ndarray, bins: int = 50) -> float:
        """
        Entropia de Shannon — mede a imprevisibilidade do preço.
        Alta entropia = mercado caótico = WAIT.
        Baixa entropia = mercado previsível = oportunidade.
        """
        if len(data) < 2:
            return 0.0
        hist, _ = np.histogram(data, bins=bins, density=True)
        hist = hist[hist > 0]  # Remove zeros
        hist = hist / hist.sum()  # Normaliza para probabilidade
        return -np.sum(hist * np.log2(hist))

    @staticmethod
    def rolling_entropy(data: np.ndarray, window: int = 50,
                        bins: int = 20) -> np.ndarray:
        """Entropia rolling — detecta transições de previsibilidade."""
        n = len(data)
        result = np.zeros(n)
        for i in range(window - 1, n):
            window_data = data[i - window + 1:i + 1]
            result[i] = MathEngine.shannon_entropy(window_data, bins)
        return result

    @staticmethod
    def mutual_information(x: np.ndarray, y: np.ndarray,
                           bins: int = 20) -> float:
        """
        Informação mútua entre duas séries — captura relações não-lineares
        que correlação linear não consegue ver.
        """
        if len(x) < 2 or len(y) < 2:
            return 0.0
        hist_2d, _, _ = np.histogram2d(x, y, bins=bins, density=True)
        hist_2d = hist_2d / hist_2d.sum()

        hist_x = hist_2d.sum(axis=1)
        hist_y = hist_2d.sum(axis=0)

        mi = 0.0
        for i in range(bins):
            for j in range(bins):
                if hist_2d[i, j] > 0 and hist_x[i] > 0 and hist_y[j] > 0:
                    mi += hist_2d[i, j] * np.log2(
                        hist_2d[i, j] / (hist_x[i] * hist_y[j])
                    )
        return max(0.0, mi)

    # ═══════════════════════════════════════════════════════════
    #  ANÁLISE FRACTAL
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def hurst_exponent(data: np.ndarray, max_lag: int = 100) -> float:
        """
        Expoente de Hurst — classifica o regime do mercado:
          H > 0.5 → trending (tendência persiste)
          H = 0.5 → random walk
          H < 0.5 → mean reverting (reversão à média)
        """
        if len(data) < max_lag:
            return 0.5  # Indeterminado

        lags = range(2, min(max_lag, len(data) // 2))
        tau = []
        lag_list = []

        for lag in lags:
            diffs = data[lag:] - data[:-lag]
            std_diff = np.std(diffs)
            if std_diff > 0:
                tau.append(std_diff)
                lag_list.append(lag)

        if len(tau) < 2:
            return 0.5

        log_lags = np.log(lag_list)
        log_tau = np.log(tau)

        # Regressão linear em log-log
        coeffs = np.polyfit(log_lags, log_tau, 1)
        return coeffs[0]  # O slope é o expoente de Hurst

    @staticmethod
    def fractal_dimension(data: np.ndarray, window: int = 50) -> float:
        """
        Dimensão fractal — mede a complexidade da série de preço.
        D ≈ 1.0 → série suave (trending forte)
        D ≈ 1.5 → série aleatória
        D ≈ 2.0 → série extremamente ruidosa
        """
        if len(data) < window:
            return 1.5

        data_win = data[-window:]
        n = len(data_win)

        # Método box-counting simplificado
        diffs = np.abs(np.diff(data_win))
        if np.max(diffs) == 0:
            return 1.0

        # Normalizar
        data_norm = (data_win - np.min(data_win))
        data_range = np.max(data_win) - np.min(data_win)
        if data_range > 0:
            data_norm = data_norm / data_range

        # Calcular comprimento da curva
        length = np.sum(np.sqrt(1 + (diffs / (data_range / n)) ** 2))
        if length <= 0:
            return 1.0

        return 1.0 + np.log(length) / np.log(n)

    # ═══════════════════════════════════════════════════════════
    #  VOLATILIDADE & RISCO
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def rsi(data: np.ndarray, period: int = 14) -> np.ndarray:
        """Relative Strength Index — mede a velocidade e mudança dos movimentos de preço."""
        if len(data) < period + 1:
            return np.zeros_like(data)

        deltas = np.diff(data)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down if down != 0 else 0
        rsi = np.zeros_like(data)
        rsi[:period] = 100. - 100. / (1. + rs)

        for i in range(period, len(data)):
            delta = deltas[i - 1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta

            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period

            rs = up / down if down != 0 else 0
            rsi[i] = 100. - 100. / (1. + rs)

        return rsi

    @staticmethod
    def atr(high: np.ndarray, low: np.ndarray, close: np.ndarray,
            period: int = 14) -> np.ndarray:
        """Average True Range — medida de volatilidade."""
        n = len(close)
        if n < 2:
            return np.zeros(n)

        tr = np.zeros(n)
        tr[0] = high[0] - low[0]
        for i in range(1, n):
            tr[i] = max(
                high[i] - low[i],
                abs(high[i] - close[i - 1]),
                abs(low[i] - close[i - 1])
            )

        atr_vals = np.zeros(n)
        if n >= period:
            atr_vals[period - 1] = np.mean(tr[:period])
            for i in range(period, n):
                atr_vals[i] = (atr_vals[i - 1] * (period - 1) + tr[i]) / period

        return atr_vals

    @staticmethod
    def realized_volatility(returns: np.ndarray, window: int = 20) -> np.ndarray:
        """Volatilidade realizada rolling."""
        n = len(returns)
        result = np.zeros(n)
        for i in range(window - 1, n):
            result[i] = np.std(returns[i - window + 1:i + 1]) * np.sqrt(252)
        return result

    @staticmethod
    def garman_klass_volatility(open_: np.ndarray, high: np.ndarray,
                                 low: np.ndarray, close: np.ndarray,
                                 window: int = 20) -> np.ndarray:
        """
        Volatilidade Garman-Klass — mais eficiente que close-to-close.
        Usa OHLC completo para estimativa superior.
        """
        n = len(close)
        if n < 2:
            return np.zeros(n)

        log_hl = np.log(high / low) ** 2
        log_co = np.log(close / open_) ** 2

        gk = 0.5 * log_hl - (2 * np.log(2) - 1) * log_co

        result = np.zeros(n)
        for i in range(window - 1, n):
            result[i] = np.sqrt(np.mean(gk[i - window + 1:i + 1]) * 252)

        return result

    # ═══════════════════════════════════════════════════════════
    #  MICROESTRUTURA
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def order_imbalance(buy_volume: np.ndarray,
                        sell_volume: np.ndarray) -> np.ndarray:
        """
        Desbalanceamento de ordens — indica pressão líquida.
        +1.0 = só compradores
        -1.0 = só vendedores
         0.0 = equilibrado
        """
        total = buy_volume + sell_volume
        total[total == 0] = 1e-10
        return (buy_volume - sell_volume) / total

    @staticmethod
    def tick_velocity(prices: np.ndarray,
                      timestamps: np.ndarray) -> np.ndarray:
        """
        Velocidade de tick — rapidez de mudança de preço.
        Alta velocidade = momentum forte.
        """
        if len(prices) < 2:
            return np.zeros(len(prices))

        dp = np.diff(prices)
        dt = np.diff(timestamps)
        dt[dt == 0] = 1e-10  # Evitar div/0

        velocity = np.zeros(len(prices))
        velocity[1:] = dp / dt
        return velocity

    @staticmethod
    def vwap(prices: np.ndarray, volumes: np.ndarray) -> np.ndarray:
        """Volume Weighted Average Price — preço médio ponderado por volume."""
        cumulative_pv = np.cumsum(prices * volumes)
        cumulative_vol = np.cumsum(volumes)
        cumulative_vol[cumulative_vol == 0] = 1e-10
        return cumulative_pv / cumulative_vol

    # ═══════════════════════════════════════════════════════════
    #  DETECÇÃO DE PADRÕES
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def detect_divergence(price: np.ndarray, indicator: np.ndarray,
                          window: int = 20) -> Tuple[bool, bool]:
        """
        Detecta divergência entre preço e indicador.
        Returns: (bullish_divergence, bearish_divergence)
        """
        if len(price) < window or len(indicator) < window:
            return False, False

        price_recent = price[-window:]
        ind_recent = indicator[-window:]

        # Encontrar últimos 2 pivôs
        price_lows = []
        price_highs = []
        ind_lows = []
        ind_highs = []

        for i in range(2, window - 2):
            # Pivô de baixa
            if (price_recent[i] < price_recent[i - 1] and
                price_recent[i] < price_recent[i - 2] and
                price_recent[i] < price_recent[i + 1] and
                price_recent[i] < price_recent[i + 2]):
                price_lows.append((i, price_recent[i]))
                ind_lows.append((i, ind_recent[i]))

            # Pivô de alta
            if (price_recent[i] > price_recent[i - 1] and
                price_recent[i] > price_recent[i - 2] and
                price_recent[i] > price_recent[i + 1] and
                price_recent[i] > price_recent[i + 2]):
                price_highs.append((i, price_recent[i]))
                ind_highs.append((i, ind_recent[i]))

        bullish_div = False
        bearish_div = False

        # Divergência bullish: preço faz lower low, indicador faz higher low
        if len(price_lows) >= 2 and len(ind_lows) >= 2:
            if (price_lows[-1][1] < price_lows[-2][1] and
                ind_lows[-1][1] > ind_lows[-2][1]):
                bullish_div = True

        # Divergência bearish: preço faz higher high, indicador faz lower high
        if len(price_highs) >= 2 and len(ind_highs) >= 2:
            if (price_highs[-1][1] > price_highs[-2][1] and
                ind_highs[-1][1] < ind_highs[-2][1]):
                bearish_div = True

        return bullish_div, bearish_div

    @staticmethod
    def support_resistance_levels(high: np.ndarray, low: np.ndarray,
                                   close: np.ndarray,
                                   sensitivity: float = 0.02) -> dict:
        """
        Detecta níveis de suporte e resistência usando clustering de pivôs.
        """
        pivots = []

        for i in range(2, len(close) - 2):
            # Pivô de alta (resistência)
            if (high[i] > high[i - 1] and high[i] > high[i - 2] and
                high[i] > high[i + 1] and high[i] > high[i + 2]):
                pivots.append(("R", high[i], i))

            # Pivô de baixa (suporte)
            if (low[i] < low[i - 1] and low[i] < low[i - 2] and
                low[i] < low[i + 1] and low[i] < low[i + 2]):
                pivots.append(("S", low[i], i))

        if not pivots:
            return {"support": [], "resistance": []}

        # Clusterizar níveis próximos
        prices = [p[1] for p in pivots]
        current_price = close[-1]
        threshold = current_price * sensitivity

        supports = []
        resistances = []

        for ptype, price, idx in pivots:
            if ptype == "S" and price < current_price:
                # Verificar se já existe um suporte similar
                merged = False
                for i, (s_price, s_count, s_last) in enumerate(supports):
                    if abs(price - s_price) < threshold:
                        # Merge: média ponderada
                        new_price = (s_price * s_count + price) / (s_count + 1)
                        supports[i] = (new_price, s_count + 1, max(s_last, idx))
                        merged = True
                        break
                if not merged:
                    supports.append((price, 1, idx))

            elif ptype == "R" and price > current_price:
                merged = False
                for i, (r_price, r_count, r_last) in enumerate(resistances):
                    if abs(price - r_price) < threshold:
                        new_price = (r_price * r_count + price) / (r_count + 1)
                        resistances[i] = (new_price, r_count + 1, max(r_last, idx))
                        merged = True
                        break
                if not merged:
                    resistances.append((price, 1, idx))

        # Ordenar por relevância (mais toques = mais forte)
        supports.sort(key=lambda x: x[1], reverse=True)
        resistances.sort(key=lambda x: x[1], reverse=True)

        return {
            "support": [(p, c) for p, c, _ in supports[:5]],
            "resistance": [(p, c) for p, c, _ in resistances[:5]],
        }

    # ═══════════════════════════════════════════════════════════
    #  KELLY CRITERION & POSITION SIZING
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def kelly_criterion(win_rate: float, avg_win: float,
                        avg_loss: float) -> float:
        """
        Kelly Criterion — sizing ótimo matematicamente.
        Retorna fração do capital a arriscar.
        """
        if avg_loss == 0 or win_rate <= 0 or win_rate >= 1:
            return 0.0

        b = avg_win / abs(avg_loss)  # Razão win/loss
        q = 1.0 - win_rate

        kelly = (win_rate * b - q) / b
        return max(0.0, kelly)

    @staticmethod
    def optimal_lot_size(balance: float, risk_pct: float,
                         stop_loss_points: float,
                         point_value: float) -> float:
        """
        Calcula lot size ótimo baseado em risco por trade.
        """
        if stop_loss_points <= 0 or point_value <= 0:
            return 0.01  # Mínimo

        risk_amount = balance * (risk_pct / 100.0)
        lot_size = risk_amount / (stop_loss_points * point_value)

        # Arredondar para step de 0.01
        lot_size = round(lot_size, 2)
        return max(0.01, lot_size)

    # ═══════════════════════════════════════════════════════════
    #  WAVELET DECOMPOSITION
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def haar_wavelet_decompose(data: np.ndarray,
                                levels: int = 3) -> List[np.ndarray]:
        """
        Decomposição wavelet Haar simplificada.
        Separa o sinal em componentes de diferentes frequências.
        Nível 0 = tendência de longo prazo
        Último nível = ruído de alta frequência
        """
        coeffs = []
        signal = data.copy().astype(np.float64)

        for _ in range(levels):
            n = len(signal)
            if n < 2:
                break
            half = n // 2
            approx = np.zeros(half)
            detail = np.zeros(half)

            for i in range(half):
                approx[i] = (signal[2 * i] + signal[2 * i + 1]) / np.sqrt(2)
                detail[i] = (signal[2 * i] - signal[2 * i + 1]) / np.sqrt(2)

            coeffs.append(detail)
            signal = approx

        coeffs.insert(0, signal)  # Aproximação final = tendência
        return coeffs

    # ═══════════════════════════════════════════════════════════
    #  UTILIDADES
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def normalize(data: np.ndarray, min_val: float = 0.0,
                  max_val: float = 1.0) -> np.ndarray:
        """Normaliza dados para range [min_val, max_val]."""
        d_min = np.min(data)
        d_max = np.max(data)
        if d_max - d_min == 0:
            return np.full_like(data, (min_val + max_val) / 2)
        return min_val + (data - d_min) / (d_max - d_min) * (max_val - min_val)

    @staticmethod
    def sigmoid(x: float) -> float:
        """Sigmoid — mapeia qualquer valor para [0, 1]."""
        return 1.0 / (1.0 + np.exp(-x))

    @staticmethod
    def tanh_scaled(x: float, scale: float = 1.0) -> float:
        """Tanh escalado — mapeia para [-1, 1]."""
        return np.tanh(x * scale)

    @staticmethod
    def softmax(x: np.ndarray) -> np.ndarray:
        """Softmax — transforma scores em probabilidades."""
        exp_x = np.exp(x - np.max(x))  # Estabilidade numérica
        return exp_x / exp_x.sum()

    @staticmethod
    def returns(prices: np.ndarray) -> np.ndarray:
        """Retornos logarítmicos."""
        if len(prices) < 2:
            return np.array([0.0])
        return np.diff(np.log(prices))
