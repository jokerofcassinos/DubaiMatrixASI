/*
2: ╔══════════════════════════════════════════════════════════════════════════════╗
3: ║         DUBAI MATRIX ASI — RISK MANAGEMENT ENGINE (C++)                   ║
4: ║    Cálculos de dimensionamento e Kelly em velocidade nativa                ║
5: ╚══════════════════════════════════════════════════════════════════════════════╝
6: */

#include "asi_core.h"
#include <cmath>
#include <algorithm>

ASI_API double asi_kelly_criterion(double win_rate, double avg_win, double avg_loss) {
    if (avg_loss <= 0.0 || win_rate <= 0.0) return 0.0;
    
    // b = avg_win / avg_loss (razão reward/risk)
    double b = avg_win / avg_loss;
    
    // K% = W - [(1 - W) / b]
    double kelly = win_rate - ((1.0 - win_rate) / b);
    
    return std::max(0.0, kelly);
}

ASI_API double asi_optimal_lot_size(double balance, double risk_pct, double sl_distance, double point_value) {
    if (balance <= 0.0 || risk_pct <= 0.0 || sl_distance <= 0.0 || point_value <= 0.0) return 0.0;
    
    // Risco financeiro absoluto
    double risk_amount = balance * risk_pct;
    
    // Valor por lote se o SL for atingido
    // Lote = Risco / (Distancia * Valor por Ponto)
    double lot = risk_amount / (sl_distance * point_value);
    
    return std::max(0.0, lot);
}

// ═══════════════════════════════════════════════════════════
//  ERGODICITY & ITO CALCULUS (Omega-Class)
// ═══════════════════════════════════════════════════════════

ASI_API double asi_non_ergodic_growth_rate(double win_rate, double avg_win_pct, double avg_loss_pct, double leverage) {
    if (leverage <= 0.0) return 0.0;
    
    // g(f) = E[log(1+r)] -> Taxa de crescimento logarítmica (Geometric Growth)
    // r_win = avg_win_pct * leverage
    // r_loss = avg_loss_pct * leverage
    
    double r_win = avg_win_pct * leverage;
    double r_loss = avg_loss_pct * leverage;
    
    // Evitar log de valores <= 0 (ruína)
    if (1.0 - r_loss <= 0.00001) return -999.0; 
    
    double growth_rate = win_rate * std::log(1.0 + r_win) + (1.0 - win_rate) * std::log(1.0 - r_loss);
    
    return growth_rate;
}

ASI_API double asi_ito_lot_sizing(double balance, double win_rate, double mu, double sigma, double dt) {
    if (balance <= 0.0 || sigma <= 0.0) return 0.0;
    
    // f* = mu / sigma^2 (Kelly clássico para tempo contínuo)
    // mu = win_rate * avg_win + (1-win_rate) * avg_loss
    // Ajustado pela Transformada de Ito (volatilidade como "imposto" de crescimento)
    
    double optimal_f = mu / (sigma * sigma);
    
    // Limitar a 1.0 para evitar alavancagem suicida em regimes não-ergódicos
    double final_f = std::max(0.0, std::min(1.0, optimal_f));
    
    return balance * final_f;
}

ASI_API void asi_process_raw_ticks(const TickData* ticks, int len, 
                                  double* out_cumulative_delta, double* out_vpin, double* out_entropy) {
    // Implementação utilitária para agregação rápida de contexto (Phase 41)
    if (len <= 0 || !ticks) return;

    double buy_vol = 0, sell_vol = 0, delta = 0;
    for (int i = 0; i < len; i++) {
        double mid = (ticks[i].bid + ticks[i].ask) / 2.0;
        if (ticks[i].last >= mid) {
            buy_vol += ticks[i].volume;
            delta += ticks[i].volume;
        } else {
            sell_vol += ticks[i].volume;
            delta -= ticks[i].volume;
        }
    }

    if (out_cumulative_delta) *out_cumulative_delta = delta;
    if (out_vpin && (buy_vol + sell_vol > 0)) *out_vpin = std::abs(buy_vol - sell_vol) / (buy_vol + sell_vol);
    // Entropy call delegated or simplified here if needed
}
