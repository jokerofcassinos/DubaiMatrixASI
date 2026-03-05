/*
╔══════════════════════════════════════════════════════════════════════════════╗
║         DUBAI MATRIX ASI — SIGNAL AGGREGATOR (C++)                         ║
║    Fusão de sinais neurais e utilidades de risco em velocidade nativa      ║
║                                                                              ║
║  Colapso de quantum state, cálculo de coerência, Kelly Criterion          ║
║  e sizing ótimo sem overhead de interpretação Python.                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
*/

#include "asi_core.h"
#include <cmath>
#include <algorithm>
#include <vector>

// ═══════════════════════════════════════════════════════════
//  SIGNAL AGGREGATION — Fusão de Agentes Neurais
// ═══════════════════════════════════════════════════════════
ASI_API void asi_aggregate_signals(const AgentSignal* signals, int count,
                                    double regime_weight, double signal_threshold,
                                    double coherence_threshold, QuantumState* state) {
    if (count <= 0 || !state) return;
    
    state->raw_signal = 0.0;
    state->coherence = 0.0;
    state->weighted_signal = 0.0;
    state->energy = 0.0;
    state->should_collapse = 0;
    
    if (count == 0) return;
    
    double total_weight = 0.0;
    double weighted_sum = 0.0;
    double energy_sum = 0.0;
    
    // ═══ Pass 1: Weighted average signal ═══
    for (int i = 0; i < count; i++) {
        double effective_weight = signals[i].weight * signals[i].confidence;
        weighted_sum += signals[i].signal * effective_weight;
        total_weight += effective_weight;
        energy_sum += std::abs(signals[i].signal) * signals[i].confidence;
    }
    
    if (total_weight > 0.0) {
        state->raw_signal = weighted_sum / total_weight;
    }
    
    state->energy = energy_sum / count;
    
    // ═══ Pass 2: Coherence — agreement between agents ═══
    // Medida de quão alinhados estão os agentes (apenas agentes com opinião)
    double direction_agreement = 0.0;
    int positive_count = 0;
    int negative_count = 0;
    int active_agents = 0;
    
    for (int i = 0; i < count; i++) {
        if (signals[i].signal > 0.05) { positive_count++; active_agents++; }
        else if (signals[i].signal < -0.05) { negative_count++; active_agents++; }
    }
    
    int dominant = std::max(positive_count, negative_count);
    
    if (active_agents > 0) {
        direction_agreement = (double)dominant / (double)active_agents;
    } else {
        direction_agreement = 0.5; // Mercado neutro
    }
    
    // Magnitude agreement
    if (active_agents > 0) {
        double mean_mag = 0.0;
        for (int i = 0; i < count; i++) {
            if (std::abs(signals[i].signal) > 0.05) {
                mean_mag += std::abs(signals[i].signal);
            }
        }
        mean_mag /= active_agents;
        
        double variance = 0.0;
        for (int i = 0; i < count; i++) {
            if (std::abs(signals[i].signal) > 0.05) {
                double diff = std::abs(signals[i].signal) - mean_mag;
                variance += diff * diff;
            }
        }
        variance /= active_agents;
        double mag_coherence = 1.0 / (1.0 + std::sqrt(variance));
        
        // Coherence final foca mais na direção do que na magnitude exata
        state->coherence = direction_agreement * 0.8 + mag_coherence * 0.2;
    } else {
        state->coherence = 0.5;
    }
    
    // ═══ Weighted signal with regime adjustment ═══
    state->weighted_signal = state->raw_signal * regime_weight;
    
    // ═══ Should Collapse Decision ═══
    // Colapsar se: coherence alta E signal forte E energia alta
    bool high_coherence = state->coherence >= coherence_threshold;
    bool strong_signal = std::abs(state->raw_signal) >= signal_threshold;
    bool high_energy = state->energy >= (signal_threshold * 0.8); // Escala com o threshold
    
    state->should_collapse = (high_coherence && strong_signal && high_energy) ? 1 : 0;
}

// ═══════════════════════════════════════════════════════════
//  KELLY CRITERION
// ═══════════════════════════════════════════════════════════
ASI_API double asi_kelly_criterion(double win_rate, double avg_win, double avg_loss) {
    if (win_rate <= 0.0 || win_rate >= 1.0 || avg_win <= 0.0 || avg_loss <= 0.0)
        return 0.0;
    
    // f* = (p * b - q) / b
    // onde p = win_rate, q = 1-p, b = avg_win/avg_loss
    double p = win_rate;
    double q = 1.0 - p;
    double b = avg_win / avg_loss;
    
    double kelly = (p * b - q) / b;
    
    // Clamp entre 0 e 0.25 (nunca arriscar mais que 25%)
    return std::clamp(kelly, 0.0, 0.25);
}

// ═══════════════════════════════════════════════════════════
//  OPTIMAL LOT SIZE
// ═══════════════════════════════════════════════════════════
ASI_API double asi_optimal_lot_size(double balance, double risk_pct, 
                                     double sl_distance, double point_value) {
    if (balance <= 0.0 || risk_pct <= 0.0 || sl_distance <= 0.0 || point_value <= 0.0)
        return 0.01;
    
    double risk_amount = balance * risk_pct;
    double lot = risk_amount / (sl_distance * point_value);
    
    // Clamp entre o mínimo (0.01) e máximo razoável
    return std::clamp(lot, 0.01, 100.0);
}
