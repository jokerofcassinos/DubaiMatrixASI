#include "asi_core.h"
#include <cmath>
#include <vector>
#include <numeric>
#include <algorithm>

/*
    Shannon Thermodynamic Entropy processor.
    Trata o mercado como partículas em um sistema fechado.
*/

ASI_API void asi_calculate_thermodynamics(const double* bid_prices, const double* bid_vols,
                                           const double* ask_prices, const double* ask_vols,
                                           int levels, ThermodynamicResult* out) {
    if (!out) return;

    // 1. Cálculo de Entropia de Shannon (Distribuição de Volume)
    double total_vol = 0.0;
    std::vector<double> probs;
    
    for (int i = 0; i < levels; i++) {
        total_vol += bid_vols[i] + ask_vols[i];
    }

    double entropy = 0.0;
    if (total_vol > 0) {
        for (int i = 0; i < levels; i++) {
            double p_bid = bid_vols[i] / total_vol;
            double p_ask = ask_vols[i] / total_vol;
            
            if (p_bid > 0) entropy -= p_bid * std::log2(p_bid);
            if (p_ask > 0) entropy -= p_ask * std::log2(p_ask);
        }
    }

    out->shannon_entropy = entropy;

    // 2. Temperatura e Pressão (Microestrutura)
    double bid_sum = std::accumulate(bid_vols, bid_vols + levels, 0.0);
    double ask_sum = std::accumulate(ask_vols, ask_vols + levels, 0.0);
    
    // Pressão como Desequilíbrio de Volume Absoluto
    out->pressure = std::abs(bid_sum - ask_sum) / (bid_sum + ask_sum + 0.0001);
    
    // Temperatura como Dispersão de Preços (Volatilidade Intrínseca do Book)
    double avg_bid = std::accumulate(bid_prices, bid_prices + levels, 0.0) / levels;
    double var_sum = 0.0;
    for (int i = 0; i < levels; i++) {
        var_sum += std::pow(bid_prices[i] - avg_bid, 2);
    }
    out->temperature = std::sqrt(var_sum / levels);

    // 3. Razão de Compressão (Condensado de Bose-Einstein analogy)
    // Se o volume está altamente concentrado em poucos níveis, a compressão é alta.
    out->compression_ratio = 1.0 / (entropy + 0.0001);
    
    // Estado Crítico: Alta Compressão + Alta Pressão
    out->is_critical_state = (out->compression_ratio > 4.0 && out->pressure > 0.7) ? 1 : 0;
}
