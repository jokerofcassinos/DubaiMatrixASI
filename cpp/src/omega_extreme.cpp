#include "asi_core.h"
#include <cmath>
#include <vector>
#include <numeric>
#include <algorithm>

// ═══════════════════════════════════════════════════════════
//  LORENTZ CLOCK: RELATIVISTIC TIME DILATION
// ═══════════════════════════════════════════════════════════

void asi_lorentz_clock_update(double volatility, double volume, double physical_dt, LorentzClockResult* out) {
    if (!out) return;

    // A "Energia Cinética" do mercado é o motor da dilatação
    // E = m * v^2 -> Massa (Volume) * Velocidade^2 (Volatilidade² aproximada por ATR ou Var)
    double kinetic_energy = volume * (volatility * volatility);
    out->kinetic_energy = kinetic_energy;

    // Constante 'c' do mercado (Velocidade limite de info)
    // Se a energia for muito alta, o tempo dilata.
    // Usamos um threshold adaptativo para 'c'
    const double MARKET_C = 1000.0; // Valor de calibração biomecânica
    
    double beta = kinetic_energy / MARKET_C;
    if (beta > 0.99) beta = 0.99; // Prevenir singularidade

    // Fator Gamma: γ = 1 / sqrt(1 - β²)
    double gamma = 1.0 / std::sqrt(1.0 - (beta * beta));
    out->dilation_factor = gamma;

    // Tempo Interno Percebido: t' = t * γ
    // Durante caos (alta energia), o tempo interno da ASI passa muito mais devagar para a realidade externa,
    // permitindo mais "processamento" por milissegundo real.
    out->internal_time_passed = physical_dt * gamma;
}

// ═══════════════════════════════════════════════════════════
//  CONSCIOUSNESS METRICS: INFORMATION INTEGRATION (Φ)
//  Simplificação algorítmica de Tononi para HFT
// ═══════════════════════════════════════════════════════════

void asi_calculate_phi(const AgentSignal* signals, int count, 
                               const double* network_weights, ConsciousnessResult* out) {
    if (!out || !signals || count < 2) return;

    double weighted_sum = 0.0;
    double variance = 0.0;
    
    // 1. Calcular Coerência (Média ponderada de sinais)
    for (int i = 0; i < count; ++i) {
        weighted_sum += signals[i].signal * signals[i].confidence * (network_weights ? network_weights[i] : 1.0);
    }
    double avg_signal = weighted_sum / count;
    out->coherence_score = std::abs(avg_signal);

    // 2. Calcular Integração (Sinergia vs Redundância)
    // Phi é alto quando os agentes convergem com alta confiança em direções complexas
    double entropy = 0.0;
    for (int i = 0; i < count; ++i) {
        double p = (signals[i].signal + 1.0) / 2.0; // Normalizar para [0, 1]
        if (p > 0 && p < 1) {
            entropy -= p * std::log2(p) + (1.0 - p) * std::log2(1.0 - p);
        }
    }
    out->integration_entropy = entropy / count;

    // Φ = Coerência * (1 / Entropia) -> Sincronia de alta informação
    if (out->integration_entropy > 0.01) {
        out->phi_value = out->coherence_score / out->integration_entropy;
    } else {
        out->phi_value = out->coherence_score * 100.0; 
    }
}

// ═══════════════════════════════════════════════════════════
//  QUANTUM CELLULAR AUTOMATA: LOB TRANSITION
// ═══════════════════════════════════════════════════════════

void asi_process_qca_grid(const double* bids, const double* asks, int levels, 
                                   double alpha, QCAResult* out) {
    if (!out || !bids || !asks) return;

    // Mapeamos o LOB para uma grade de 1D QCA
    // Cada célula é o volume relativo
    std::vector<int> grid(levels * 2);
    double total_vol = 0;
    
    for (int i = 0; i < levels; ++i) {
        grid[i] = (bids[i] > alpha) ? 1 : 0;
        grid[i + levels] = (asks[i] > alpha) ? 1 : 0;
        total_vol += bids[i] + asks[i];
    }

    // Regra de Wolfram (Simulada para entropia de grade)
    double transition_count = 0;
    for (int i = 1; i < (levels * 2) - 1; ++i) {
        if (grid[i-1] != grid[i+1]) transition_count++;
    }

    out->transition_speed = transition_count / (levels * 2);
    out->grid_entropy = total_vol > 0 ? (transition_count / total_vol) : 0;
    
    // Iminência de rompimento: Alta velocidade de transição em volumes baixos
    out->is_critical = (out->transition_speed > 0.7 && out->grid_entropy > 0.5) ? 1 : 0;
}

// ═══════════════════════════════════════════════════════════
//  LOTKA-VOLTERRA: PREDATOR-PREY (Ecological Liquidity)
// ═══════════════════════════════════════════════════════════

void asi_solve_lotka_volterra(double dt, double alpha, double beta, double delta, double gamma,
                                      double* in_out_prey, double* in_out_predator, PredatorPreyResult* out) {
    if (!out || !in_out_prey || !in_out_predator) return;

    double x = *in_out_prey;     // Presas (Varejo)
    double y = *in_out_predator; // Predadores (Institucional)

    // dx/dt = alpha*x - beta*x*y
    // dy/dt = delta*x*y - gamma*y
    double dx = (alpha * x - beta * x * y) * dt;
    double dy = (delta * x * y - gamma * y) * dt;

    *in_out_prey += dx;
    *in_out_predator += dy;

    out->prey_biomass = *in_out_prey;
    out->predator_biomass = *in_out_predator;
    
    // Risco de Extinção: Quando predadores saturam e presas somem (Liquidation Cascade)
    out->extinction_risk = (y > x * 2.0) ? 1.0 : (y / (x + 1e-9));
    out->hunt_efficiency = (dx < 0 && dy > 0) ? std::abs(dy / dx) : 0;
}

// ═══════════════════════════════════════════════════════════
//  BLACK SWAN HARVESTER: EVT (Extreme Value Theory)
// ═══════════════════════════════════════════════════════════

void asi_harvest_black_swan(const double* extreme_ticks, int len, double threshold, 
                                     ExtremeValueResult* out) {
    if (!out || !extreme_ticks || len < 5) return;

    double max_exceedance = 0;
    double sum_exceedance = 0;
    int count = 0;

    for (int i = 0; i < len; ++i) {
        if (std::abs(extreme_ticks[i]) > threshold) {
            double exc = std::abs(extreme_ticks[i]) - threshold;
            max_exceedance = std::max(max_exceedance, exc);
            sum_exceedance += exc;
            count++;
        }
    }

    if (count > 0) {
        out->threshold_exceedance = max_exceedance;
        double mean_excess = sum_exceedance / count;
        
        // GPD Shape approximation (simplificada)
        out->tail_risk = mean_excess / threshold; 
        out->is_black_swan = (out->tail_risk > 0.5) ? 1 : 0;
    } else {
        out->is_black_swan = 0;
    }
}
