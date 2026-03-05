/*
╔══════════════════════════════════════════════════════════════════════════════╗
║         DUBAI MATRIX ASI — QUANTUM INDICATOR ENGINE (C++)                  ║
║    Cálculos de indicadores técnicos em velocidade nativa                   ║
║                                                                              ║
║  Cada função opera diretamente sobre arrays de doubles sem overhead        ║
║  de interpretação Python — ~50-200x mais rápido que NumPy para arrays     ║
║  pequenos e ~10-30x mais rápido para arrays grandes.                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
*/

#include "asi_core.h"
#include <cmath>
#include <algorithm>
#include <vector>
#include <numeric>

// ═══════════════════════════════════════════════════════════
//  EMA — Exponential Moving Average
// ═══════════════════════════════════════════════════════════
ASI_API void asi_ema(const double* close, int len, int period, double* out) {
    if (len <= 0 || period <= 0) return;
    
    double multiplier = 2.0 / (period + 1.0);
    
    // SMA como seed
    double sum = 0.0;
    int seed_len = std::min(period, len);
    for (int i = 0; i < seed_len; i++) {
        sum += close[i];
        out[i] = sum / (i + 1);
    }
    
    // EMA a partir do período
    for (int i = period; i < len; i++) {
        out[i] = (close[i] - out[i - 1]) * multiplier + out[i - 1];
    }
}

// ═══════════════════════════════════════════════════════════
//  RSI — Relative Strength Index
// ═══════════════════════════════════════════════════════════
ASI_API void asi_rsi(const double* close, int len, int period, double* out) {
    if (len < period + 1) {
        for (int i = 0; i < len; i++) out[i] = 50.0;
        return;
    }

    // Calcular ganhos e perdas
    std::vector<double> gains(len, 0.0);
    std::vector<double> losses(len, 0.0);
    
    for (int i = 1; i < len; i++) {
        double delta = close[i] - close[i - 1];
        gains[i] = delta > 0 ? delta : 0.0;
        losses[i] = delta < 0 ? -delta : 0.0;
    }

    // Primeira média (SMA seed)
    double avg_gain = 0.0, avg_loss = 0.0;
    for (int i = 1; i <= period; i++) {
        avg_gain += gains[i];
        avg_loss += losses[i];
    }
    avg_gain /= period;
    avg_loss /= period;

    // RSI para os primeiros valores
    for (int i = 0; i < period; i++) out[i] = 50.0;
    
    // RSI no ponto seed
    if (avg_loss > 0.0) {
        double rs = avg_gain / avg_loss;
        out[period] = 100.0 - (100.0 / (1.0 + rs));
    } else if (avg_gain > 0.0) {
        out[period] = 100.0;
    } else {
        out[period] = 50.0;
    }

    // Smoothed RSI
    for (int i = period + 1; i < len; i++) {
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period;
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period;
        
        if (avg_loss > 0.0) {
            double rs = avg_gain / avg_loss;
            out[i] = 100.0 - (100.0 / (1.0 + rs));
        } else if (avg_gain > 0.0) {
            out[i] = 100.0;
        } else {
            out[i] = 50.0;
        }
    }
}

// ═══════════════════════════════════════════════════════════
//  ATR — Average True Range
// ═══════════════════════════════════════════════════════════
ASI_API void asi_atr(const double* high, const double* low, const double* close,
                     int len, int period, double* out) {
    if (len < 2 || period <= 0) return;
    
    // True Range
    std::vector<double> tr(len, 0.0);
    tr[0] = high[0] - low[0];
    
    for (int i = 1; i < len; i++) {
        double hl = high[i] - low[i];
        double hc = std::abs(high[i] - close[i - 1]);
        double lc = std::abs(low[i] - close[i - 1]);
        tr[i] = std::max({hl, hc, lc});
    }
    
    // ATR como SMA primeiro, depois RMA (Wilder's smoothing)
    double sum = 0.0;
    for (int i = 0; i < std::min(period, len); i++) {
        sum += tr[i];
        out[i] = sum / (i + 1);
    }
    
    for (int i = period; i < len; i++) {
        out[i] = (out[i - 1] * (period - 1) + tr[i]) / period;
    }
}

// ═══════════════════════════════════════════════════════════
//  BOLLINGER BANDS
// ═══════════════════════════════════════════════════════════
ASI_API void asi_bollinger(const double* close, int len, int period, double num_std,
                           double* upper, double* middle, double* lower, double* width) {
    if (len < period) return;
    
    for (int i = 0; i < len; i++) {
        int start = std::max(0, i - period + 1);
        int count = i - start + 1;
        
        // SMA
        double sum = 0.0;
        for (int j = start; j <= i; j++) sum += close[j];
        double sma = sum / count;
        middle[i] = sma;
        
        // Desvio padrão
        if (count >= period) {
            double sq_sum = 0.0;
            for (int j = start; j <= i; j++) {
                double diff = close[j] - sma;
                sq_sum += diff * diff;
            }
            double std_dev = std::sqrt(sq_sum / count);
            
            upper[i] = sma + num_std * std_dev;
            lower[i] = sma - num_std * std_dev;
            width[i] = sma > 0.0 ? (upper[i] - lower[i]) / sma : 0.0;
        } else {
            upper[i] = sma;
            lower[i] = sma;
            width[i] = 0.0;
        }
    }
}

// ═══════════════════════════════════════════════════════════
//  MACD — Moving Average Convergence Divergence
// ═══════════════════════════════════════════════════════════
ASI_API void asi_macd(const double* close, int len, int fast, int slow, int signal_period,
                      double* macd_line, double* signal_line, double* histogram) {
    if (len <= 0) return;
    
    std::vector<double> ema_fast(len), ema_slow(len);
    asi_ema(close, len, fast, ema_fast.data());
    asi_ema(close, len, slow, ema_slow.data());
    
    for (int i = 0; i < len; i++) {
        macd_line[i] = ema_fast[i] - ema_slow[i];
    }
    
    asi_ema(macd_line, len, signal_period, signal_line);
    
    for (int i = 0; i < len; i++) {
        histogram[i] = macd_line[i] - signal_line[i];
    }
}

// ═══════════════════════════════════════════════════════════
//  VWAP — Volume Weighted Average Price
// ═══════════════════════════════════════════════════════════
ASI_API double asi_vwap(const double* close, const double* volume, int len) {
    if (len <= 0) return 0.0;
    
    double tp_vol_sum = 0.0;
    double vol_sum = 0.0;
    
    for (int i = 0; i < len; i++) {
        tp_vol_sum += close[i] * volume[i];
        vol_sum += volume[i];
    }
    
    return vol_sum > 0.0 ? tp_vol_sum / vol_sum : close[len - 1];
}

// ═══════════════════════════════════════════════════════════
//  SHANNON ENTROPY
// ═══════════════════════════════════════════════════════════
ASI_API double asi_shannon_entropy(const double* data, int len, int bins) {
    if (len < 2 || bins <= 0) return 0.0;
    
    // Encontrar min/max
    double min_val = data[0], max_val = data[0];
    for (int i = 1; i < len; i++) {
        if (data[i] < min_val) min_val = data[i];
        if (data[i] > max_val) max_val = data[i];
    }
    
    double range = max_val - min_val;
    if (range <= 0.0) return 0.0;
    
    // Histogram
    std::vector<int> hist(bins, 0);
    for (int i = 0; i < len; i++) {
        int bin = (int)((data[i] - min_val) / range * (bins - 1));
        bin = std::clamp(bin, 0, bins - 1);
        hist[bin]++;
    }
    
    // Entropy
    double entropy = 0.0;
    double n = (double)len;
    for (int i = 0; i < bins; i++) {
        if (hist[i] > 0) {
            double p = hist[i] / n;
            entropy -= p * std::log2(p);
        }
    }
    
    return entropy;
}

// ═══════════════════════════════════════════════════════════
//  HURST EXPONENT (R/S Method)
// ═══════════════════════════════════════════════════════════
ASI_API double asi_hurst_exponent(const double* data, int len) {
    if (len < 20) return 0.5;
    
    // Método R/S simplificado
    std::vector<double> returns(len - 1);
    for (int i = 0; i < len - 1; i++) {
        returns[i] = data[i + 1] > 0 && data[i] > 0 ? 
                     std::log(data[i + 1] / data[i]) : 0.0;
    }
    
    int n = (int)returns.size();
    if (n < 10) return 0.5;
    
    // R/S para diferentes tamanhos de janela
    std::vector<double> log_n, log_rs;
    
    int sizes[] = {10, 20, 40, 80};
    for (int s : sizes) {
        if (s > n) break;
        
        int num_windows = n / s;
        double total_rs = 0.0;
        int valid = 0;
        
        for (int w = 0; w < num_windows; w++) {
            int offset = w * s;
            
            // Média
            double mean = 0.0;
            for (int i = 0; i < s; i++) mean += returns[offset + i];
            mean /= s;
            
            // Desvio dos cumulativos
            double max_dev = 0.0, min_dev = 0.0, cum = 0.0;
            double sq_sum = 0.0;
            for (int i = 0; i < s; i++) {
                double val = returns[offset + i] - mean;
                cum += val;
                if (cum > max_dev) max_dev = cum;
                if (cum < min_dev) min_dev = cum;
                sq_sum += val * val;
            }
            
            double R = max_dev - min_dev;
            double S = std::sqrt(sq_sum / s);
            
            if (S > 1e-10) {
                total_rs += R / S;
                valid++;
            }
        }
        
        if (valid > 0) {
            log_n.push_back(std::log((double)s));
            log_rs.push_back(std::log(total_rs / valid));
        }
    }
    
    // Regressão linear simples para estimar H
    if (log_n.size() < 2) return 0.5;
    
    int m = (int)log_n.size();
    double sum_x = 0, sum_y = 0, sum_xy = 0, sum_xx = 0;
    for (int i = 0; i < m; i++) {
        sum_x += log_n[i];
        sum_y += log_rs[i];
        sum_xy += log_n[i] * log_rs[i];
        sum_xx += log_n[i] * log_n[i];
    }
    
    double denom = m * sum_xx - sum_x * sum_x;
    if (std::abs(denom) < 1e-10) return 0.5;
    
    double H = (m * sum_xy - sum_x * sum_y) / denom;
    return std::clamp(H, 0.0, 1.0);
}

// ═══════════════════════════════════════════════════════════
//  Z-SCORE
// ═══════════════════════════════════════════════════════════
ASI_API void asi_zscore(const double* data, int len, int window, double* out) {
    for (int i = 0; i < len; i++) {
        int start = std::max(0, i - window + 1);
        int count = i - start + 1;
        
        double mean = 0.0;
        for (int j = start; j <= i; j++) mean += data[j];
        mean /= count;
        
        double sq_sum = 0.0;
        for (int j = start; j <= i; j++) {
            double d = data[j] - mean;
            sq_sum += d * d;
        }
        double std_dev = std::sqrt(sq_sum / count);
        
        out[i] = std_dev > 1e-10 ? (data[i] - mean) / std_dev : 0.0;
    }
}
