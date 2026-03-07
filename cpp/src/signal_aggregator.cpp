#include "asi_core.h"
#include <cmath>
#include <algorithm>
#include <chrono>
#include <vector>
#include <numeric>

ASI_API void asi_converge_signals(const AgentRawSignal* signals, int count, 
                                 double interference_weight, double decay,
                                 ConvergenceResult* out) {
    auto t_start = std::chrono::high_resolution_clock::now();

    if (count <= 0 || !signals || !out) return;

    double weighted_signal_sum = 0.0;
    double weighted_conf_sum = 0.0;
    double total_weight = 0.0;
    double active_weight = 0.0;
    
    int bull = 0, bear = 0, neutral = 0;
    
    // Vetor para cálculo de entropia (distribuição de sinais)
    std::vector<double> signal_values;
    signal_values.reserve(count);

    for (int i = 0; i < count; i++) {
        const auto& s = signals[i];
        double effective_weight = s.weight;
        
        weighted_signal_sum += s.signal * effective_weight;
        weighted_conf_sum += s.confidence * effective_weight;
        total_weight += effective_weight;
        
        if (std::abs(s.signal) > 0.01) {
            active_weight += effective_weight;
        }

        // Histogramagem rápida
        if (s.signal > 0.1) bull++;
        else if (s.signal < -0.1) bear++;
        else neutral++;

        signal_values.push_back(s.signal);
    }

    // Médias balanceadas: Evita diluição massiva por agentes passivos (SIGNAL_WEAK fix)
    double focused_signal = (active_weight > 0) ? (weighted_signal_sum / active_weight) : 0.0;
    double focused_conf = (active_weight > 0) ? (weighted_conf_sum / active_weight) : 0.0;
    
    // Calcula participação apenas contando AGENTES ATIVOS e ignorando pesos fixos para o ratio.
    int active_agents = bull + bear;
    double agent_ratio = (double)active_agents / count;

    // Redução da Punição (Se 10% do enxame agir com firmeza, já é sinal de oportunidade)
    double participation_penalty = std::min(1.0, agent_ratio * 6.0); // Só penaliza se < 16% falarem
    
    double raw_signal = focused_signal * participation_penalty;
    double raw_conf = focused_conf * std::min(1.0, agent_ratio * 3.0);

    // Coerência: Desvio padrão inverso dos sinais (quão "alinhados" estão os agentes)
    double mean_sig = raw_signal;
    double var_sig = 0.0;
    for(double val : signal_values) {
        double diff = val - mean_sig;
        var_sig += diff * diff;
    }
    double std_sig = std::sqrt(var_sig / count);
    double coherence = 1.0 / (1.0 + std_sig * 2.0); // Normalizado [0, 1]

    // Entropia de Shannon simplificada (binning)
    double entropy = 0.0;
    const int bins = 10;
    int counts[bins] = {0};
    for(double val : signal_values) {
        int b = (int)((val + 1.0) / 2.0 * (bins - 1));
        b = std::max(0, std::min(bins - 1, b));
        counts[b]++;
    }
    for(int b=0; b<bins; b++) {
        if(counts[b] > 0) {
            double p = (double)counts[b] / count;
            entropy -= p * std::log2(p);
        }
    }
    entropy /= 3.32; // Normalizar pela entropia máxima log2(10)

    // Colapso Quântico: Reforço por interferência construtiva
    // Se coerência é alta, sinal é amplificado. Se baixa (caos), sinal é asfixiado.
    double interference_factor = 1.0 + (interference_weight * (coherence - 0.5));
    out->final_signal = std::clamp(raw_signal * interference_factor * decay, -1.0, 1.0);
    out->final_confidence = std::clamp(raw_conf * (0.5 + 0.5 * coherence), 0.0, 1.0);
    out->final_coherence = coherence;
    out->entropy = entropy;
    out->bull_count = bull;
    out->bear_count = bear;
    out->neutral_count = neutral;

    auto t_end = std::chrono::high_resolution_clock::now();
    out->computation_time_ms = std::chrono::duration<double, std::milli>(t_end - t_start).count();
}

// ═══════════════════════════════════════════════════════════
//  LEGACY WRAPPER (Phase 41 Compatibility)
// ═══════════════════════════════════════════════════════════
ASI_API void asi_aggregate_signals(const AgentSignal* signals, int count,
                                    double regime_weight, double signal_threshold,
                                    double coherence_threshold, QuantumState* state) {
    if (count <= 0 || !signals || !state) return;

    // Converter para o novo formato e chamar a lógica de convergência Phase 41
    std::vector<AgentRawSignal> raw_signals(count);
    for (int i = 0; i < count; i++) {
        raw_signals[i].signal = signals[i].signal;
        raw_signals[i].confidence = signals[i].confidence;
        raw_signals[i].weight = signals[i].weight;
        raw_signals[i].is_hybrid = 0;
    }

    ConvergenceResult res;
    asi_converge_signals(raw_signals.data(), count, 0.5, regime_weight, &res);

    // Mapear de volta para o struct QuantumState legado
    state->raw_signal = res.final_signal;
    state->coherence = res.final_coherence;
    state->weighted_signal = res.final_signal; 
    state->energy = res.entropy;
    state->should_collapse = (res.final_confidence >= 0.65 && std::abs(res.final_signal) >= signal_threshold) ? 1 : 0;
}
