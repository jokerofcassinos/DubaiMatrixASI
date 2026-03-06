/*
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — C++ CORE HEADER                            ║
║     API de Exportação para todos os módulos C++ de alta performance        ║
╚══════════════════════════════════════════════════════════════════════════════╝
*/

#pragma once

#include <cstdint>
#include <cstddef>

// ═══ EXPORT MACRO ═══
#ifdef _WIN32
    #ifdef ASI_EXPORTS
        #define ASI_API extern "C" __declspec(dllexport)
    #else
        // Durante a compilação local da DLL, queremos exportar, não importar.
        #define ASI_API extern "C" __declspec(dllexport)
    #endif
#else
    #define ASI_API extern "C" __attribute__((visibility("default")))
#endif

// ═══════════════════════════════════════════════════════════
//  QUANTUM INDICATOR ENGINE
//  Cálculos de indicadores em velocidade nativa C++
// ═══════════════════════════════════════════════════════════
//  OMEGA SIGNAL CONVERGENCE (Phase 41)
// ═══════════════════════════════════════════════════════════

struct AgentRawSignal {
    double signal;
    double confidence;
    double weight;
    int is_hybrid;
};

struct ConvergenceResult {
    double final_signal;
    double final_confidence;
    double final_coherence;
    double entropy;
    int bull_count;
    int bear_count;
    int neutral_count;
    double computation_time_ms;
};

ASI_API void asi_converge_signals(const AgentRawSignal* signals, int count,
                                     double interference_weight, double decay,
                                     ConvergenceResult* out);

ASI_API void asi_ema(const double* close, int len, int period, double* out);
ASI_API void asi_rsi(const double* close, int len, int period, double* out);
ASI_API void asi_atr(const double* high, const double* low, const double* close, int len, int period, double* out);
ASI_API void asi_bollinger(const double* close, int len, int period, double num_std,
                           double* upper, double* middle, double* lower, double* width);
ASI_API void asi_macd(const double* close, int len, int fast, int slow, int signal_period,
                      double* macd_line, double* signal_line, double* histogram);
ASI_API double asi_vwap(const double* close, const double* volume, int len);
ASI_API double asi_shannon_entropy(const double* data, int len, int bins);
ASI_API double asi_hurst_exponent(const double* data, int len);
ASI_API void asi_zscore(const double* data, int len, int window, double* out);

// ═══════════════════════════════════════════════════════════
//  ORDER FLOW PROCESSOR
//  Análise de microestrutura em velocidade de tick
// ═══════════════════════════════════════════════════════════

struct TickData {
    double bid;
    double ask;
    double last;
    double volume;
    int64_t time_msc;
    double time; // Adicionado para compatibilidade com Monte Carlo se necessário
};

struct OrderFlowResult {
    double cumulative_delta;
    double buy_volume;
    double sell_volume;
    double order_imbalance;
    double tick_velocity;
    int    is_absorption;
    int    is_exhaustion;
    double volume_climax_score;
};

ASI_API void asi_process_orderflow(const TickData* ticks, int count, OrderFlowResult* result);

// ═══════════════════════════════════════════════════════════
//  SIGNAL AGGREGATOR
//  Fusão de sinais neurais em velocidade nativa
// ═══════════════════════════════════════════════════════════

struct AgentSignal {
    double signal;     // [-1, +1]
    double confidence; // [0, 1]
    double weight;     // Peso do agente
};

struct QuantumState {
    double raw_signal;
    double coherence;
    double weighted_signal;
    double energy;         // "Energia" total dos sinais
    int    should_collapse; // 1 = colapsar, 0 = superpor
};

ASI_API void asi_aggregate_signals(const AgentSignal* signals, int count,
                                    double regime_weight, double signal_threshold,
                                    double coherence_threshold, QuantumState* state);
ASI_API double asi_kelly_criterion(double win_rate, double avg_win, double avg_loss);
ASI_API double asi_optimal_lot_size(double balance, double risk_pct, double sl_distance, double point_value);

// ═══════════════════════════════════════════════════════════
//  AGENT CLUSTER ENGINE
//  Funções matemáticas pesadas offloaded dos agentes Python
// ═══════════════════════════════════════════════════════════

struct PhaseSpaceResult {
    double orbit_radius;
    double global_orbit;
    double compression_ratio;
    int    is_compressed;
};

ASI_API double asi_fractal_dimension(const double* data, int len, int max_box);
ASI_API double asi_vpin_proxy(const double* open, const double* close,
                               const double* volume, int len, int lookback);
ASI_API void asi_phase_space(const double* closes, int len, int lookback,
                              PhaseSpaceResult* result);
ASI_API double asi_kurtosis(const double* data, int len);
ASI_API double asi_cross_scale_correlation(const double* series_a, int len_a,
                                            const double* series_b, int len_b);
ASI_API double asi_tick_entropy(const double* bids, int len, int bins);

// ═══════════════════════════════════════════════════════════
//  LATENCY OPTIMIZATION MODULE (Phase 18)
// ═══════════════════════════════════════════════════════════

struct SwingResult {
    int index;
    double price;
};

struct MonteCarloInput {
    double S0;
    double mu;
    double sigma;
    double jump_intensity;
    double jump_mean;
    double jump_std;
    double dt;
    int n_sims;
    int n_steps;
    double stop_loss;
    double take_profit;
    bool is_buy;
};

struct MonteCarloOutput {
    double win_prob;
    double expected_return;
    double var_95;
    double cvar_95;
    double simulation_time_ms;
};

// TickData já definido acima

ASI_API int asi_find_swings(const double* highs, const double* lows, int len, int lookback, 
                            SwingResult* out_highs, int* high_count, 
                            SwingResult* out_lows, int* low_count);

ASI_API void asi_navier_stokes_pressure(const double* bid_vols, const double* ask_vols, int levels, 
                                        double* out_ratio, double* out_pressure);

ASI_API double asi_calc_micro_variance(const double* data, int len);

ASI_API void asi_monte_carlo_merton(const MonteCarloInput* input, MonteCarloOutput* output);

ASI_API void asi_process_raw_ticks(const TickData* ticks, int len, 
                                  double* out_cumulative_delta, double* out_vpin, double* out_entropy);

// ═══════════════════════════════════════════════════════════
//  HYPERSPACE 4096D ENGINE (Phase 25)
// ═══════════════════════════════════════════════════════════

struct HyperspaceOutput {
    double confidence_boost;
    double expected_max_excursion;
    double probability_density;
    double hyperspace_time_ms;
};

// Vórtice multidimensional: simula 4096 instâncias de caminhos e concentrações.
ASI_API void asi_simulate_4096_hyperspace(const double* closes, int len, double current_volatility, HyperspaceOutput* output);
