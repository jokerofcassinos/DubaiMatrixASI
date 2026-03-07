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
ASI_API double asi_optimal_lot_size(double balance, double risk_pct, double sl_distance, double point_value);
ASI_API double asi_non_ergodic_growth_rate(double win_rate, double avg_win_pct, double avg_loss_pct, double leverage);
ASI_API double asi_ito_lot_sizing(double balance, double win_rate, double mu, double sigma, double dt);

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

// ═══════════════════════════════════════════════════════════
//  LGNN & THERMODYNAMIC ENGINE (Phase Ω-Next)
// ═══════════════════════════════════════════════════════════

struct GraphNode {
    double price;
    double liquidity;
    double centrality;
    double velocity;
};

struct GraphResult {
    GraphNode clusters[50];
    int cluster_count;
    double avalanche_risk; // [0-1]
    double global_centrality;
};

struct ThermodynamicResult {
    double shannon_entropy;
    double temperature;
    double pressure;
    double compression_ratio;
    int    is_critical_state;
};

ASI_API void asi_calculate_lgnn(const TickData* ticks, int tick_count, 
                                 const double* book_prices, const double* book_vols, int levels,
                                 GraphResult* out);

ASI_API double asi_map_poincare_dist(double r1, double theta1, double r2, double theta2);

ASI_API void asi_calculate_thermodynamics(const double* bid_prices, const double* bid_vols,
                                           const double* ask_prices, const double* ask_vols,
                                           int levels, ThermodynamicResult* out);

// Phase Ω-Next: Vector Episodic Memory
ASI_API int asi_vector_search(const double* query, const double* database, int query_dim, int db_size, double* out_similarities, int* out_indices, int top_k);

// ═══════════════════════════════════════════════════════════
//  FRONTIER ABSOLUTE: CAUSAL INFERENCE (Phase Ω-Zero)
// ═══════════════════════════════════════════════════════════

struct CausalResult {
    double causal_effect;        // P(Y | do(X))
    double counterfactual_loss;  // Perda estimada em cenário alternativo
    double do_impact_score;      // Impacto estimado da nossa ordem no micro-preço
    double confidence;           // Confiança no DAG causal
};

ASI_API void asi_calculate_causal_impact(const double* feature_matrix, int rows, int cols,
                                        double our_order_size, int target_index,
                                        CausalResult* out);

// ═══════════════════════════════════════════════════════════
//  FRONTIER ABSOLUTE: TOPOLOGICAL DATA ANALYSIS (Phase Ω-Zero)
// ═══════════════════════════════════════════════════════════

struct TopologyResult {
    double betti_0;              // Número de componentes conectados
    double betti_1;              // Número de "buracos" topológicos
    double persistence_entropy;  // Entropia da persistência homológica
    double critical_hole_size;   // Tamanho do maior buraco detectado
    int is_geometrically_unstable; // Flag de colapso estrutural
};

ASI_API void asi_calculate_topology(const double* prices, const double* volumes, int levels,
                                   TopologyResult* out);

// ═══════════════════════════════════════════════════════════
//  FRONTIER ABSOLUTE: TENSOR NETWORKS (Phase Ω-Zero)
// ═══════════════════════════════════════════════════════════

struct TensorResult {
    double entanglement_entropy; // Mede a conexão entre spot/derivativos
    double compression_loss;     // Perda de informação na representação MPS
    double stability_index;      // Estabilidade da decomposição tensorial
    int dominant_mode;           // Modo físico dominante detectado
};

ASI_API void asi_calculate_tensor_swarm(const double* spot_data, const double* deriv_data, int len,
                                       int bond_dimension, TensorResult* out);

// ═══════════════════════════════════════════════════════════
//  FRONTIER ABSOLUTE: NEURAL STIGMERGY (Phase Ω-Zero)
// ═══════════════════════════════════════════════════════════

ASI_API void asi_deposit_pheromone(double price_level, double intensity, double decay_rate);
ASI_API double asi_sense_pheromone(double price_level);
ASI_API void asi_update_pheromone_field(double dt);

// ═══════════════════════════════════════════════════════════
//  FRONTIER ABSOLUTE: INFORMATION GEOMETRY (Phase Ω-Zero)
// ═══════════════════════════════════════════════════════════

struct FisherResult {
    double fisher_information;   // Valor da informação de Fisher (curvatura)
    double natural_gradient_x;   // Gradiente natural no espaço de fase
    double information_distance; // Distância de Kullback-Leibler (KL Divergence)
    double optimal_step_size;    // Passo de mutação otimizado pela métrica
};

ASI_API void asi_calculate_fisher_metric(const double* prev_distribution, const double* curr_distribution, int n_bins,
                                        FisherResult* out);

// Vórtice multidimensional: simula 4096 instâncias de caminhos e concentrações.
ASI_API void asi_simulate_4096_hyperspace(const double* closes, int len, double current_volatility, HyperspaceOutput* output);

// ═══════════════════════════════════════════════════════════
//  PHASE Ω-ONE: SPIKING NEURAL NETWORKS (SNN)
// ═══════════════════════════════════════════════════════════

struct SpikeResult {
    double potential;        // Potencial de membrana atual
    int    fired;            // 1 se o neurônio disparou, 0 caso contrário
    double last_spike_time;  // Timestamp do último disparo
};

ASI_API void asi_update_lif_neuron(double input_current, double dt, 
                                   double v_rest, double v_threshold, 
                                   double resistance, double capacitance, 
                                   double* in_out_v_potential, int* out_fired);

// ═══════════════════════════════════════════════════════════
//  PHASE Ω-ONE: MEAN FIELD GAMES (MFG)
// ═══════════════════════════════════════════════════════════

struct MFGResult {
    double optimal_velocity;    // Velocidade geodésica ótima para a ASI
    double crowd_density;       // Densidade local da massa (gás de traders)
    double expected_drift;      // Drift induzido pela massa sob a HJB
    double stability_score;     // Quão estável é o fluxo MFG
};

ASI_API void asi_solve_mfg(const double* density_profile, int len, 
                           double price_min, double price_step,
                           double current_price, double volatility, 
                           const double* reward_function, MFGResult* out);

// ═══════════════════════════════════════════════════════════
//  PHASE Ω-ONE: FEYNMAN PATH INTEGRALS
// ═══════════════════════════════════════════════════════════

struct PathIntegralResult {
    double probability_amplitude_real;
    double probability_amplitude_imag;
    double stationary_phase_price;
    double quantum_interference_score;
};

// Propagador Quântico que resolve a amplitude de transição P(xA, tA -> xB, tB)
ASI_API void asi_calculate_feynman_path(const double* history, int len, 
                                        double target_price, double time_horizon,
                                        double liquidity_friction, PathIntegralResult* out);

// ═══════════════════════════════════════════════════════════
//  PHASE Ω-ONE: CHAOS & LYAPUNOV HORIZON
// ═══════════════════════════════════════════════════════════

struct ChaosResult {
    double lyapunov_exponent;   // Lambda (Exp. Lyapunov)
    double predictability_limit; // Tempo de Lyapunov (1/Lambda)
    double entropy;             // Shannon Entropy do fluxo
    int    is_chaotic;          // 1 se Lambda > 0
};

ASI_API void asi_calculate_chaos(const double* ticks, int len, double sample_rate, ChaosResult* out);

// ═══════════════════════════════════════════════════════════
//  PHASE Ω-CLASS: RESERVOIR COMPUTING (Liquid State)
// ═══════════════════════════════════════════════════════════

ASI_API void asi_init_reservoir(int n_neurons, double spectral_radius, double connectivity);
ASI_API void asi_perturb_reservoir(const double* inputs, int n_inputs);
ASI_API void asi_read_reservoir_output(double* out_waves, int n_outputs);

// ═══════════════════════════════════════════════════════════
//  PHASE Ω-CLASS: HOLOGRAPHIC MATRIX (AdS/CFT)
// ═══════════════════════════════════════════════════════════

struct HolographicResult {
    double bulk_pressure;
    double entanglement_entropy;
    double geodesic_distance;
    double holographic_coherence;
    int is_manifold_stable;
};

// Holographic Matrix
ASI_API void asi_infer_holographic_pressure(const double* boundary_ticks, int n_ticks, 
                                           const double* book_imbalance, int levels,
                                           HolographicResult* out);

// ═══════════════════════════════════════════════════════════
//  PHASE Ω-EXTREME: THE ABSOLUTE RELATIVITY
// ═══════════════════════════════════════════════════════════

struct LorentzClockResult {
    double internal_time_passed; // "Segundos" internos processados
    double dilation_factor;      // Gamma (Fator de dilatação)
    double kinetic_energy;       // Volatilidade * Volume
};

struct ConsciousnessResult {
    double phi_value;            // Métrica de integração de informação (IIT)
    double coherence_score;      // Coerência sistêmica
    double integration_entropy;  // Entropia da integração
};

struct QCAResult {
    double grid_entropy;         // Entropia da grade QCA
    double transition_speed;     // Velocidade da transição de fase
    int    is_critical;          // Ativado em iminência de rompimento
};

struct PredatorPreyResult {
    double predator_biomass;     // Força institucional
    double prey_biomass;         // Força de varejo
    double extinction_risk;      // Probabilidade de liquidação em massa
    double hunt_efficiency;      // ROI esperado da caça
};

struct ExtremeValueResult {
    double threshold_exceedance; // Valor acima do threshold GPD
    double tail_risk;            // Risco de cauda (EVT)
    double copula_correlation;   // Correlação de cauda multi-variável
    int    is_black_swan;        // 1 se evento extremo detectado
};

// LorentzClock: Relativistic Time Dilation
ASI_API void asi_lorentz_clock_update(double volatility, double volume, double physical_dt, LorentzClockResult* out);

// ConsciousnessMetrics: Information Integration (Φ)
ASI_API void asi_calculate_phi(const AgentSignal* signals, int count, 
                               const double* network_weights, ConsciousnessResult* out);

// Quantum Cellular Automata: Ultra-Fast LOB Grid
ASI_API void asi_process_qca_grid(const double* bids, const double* asks, int levels, 
                                   double alpha, QCAResult* out);

// Lotka-Volterra Engine: Predator-Prey Dynamics
ASI_API void asi_solve_lotka_volterra(double dt, double alpha, double beta, double delta, double gamma,
                                      double* in_out_prey, double* in_out_predator, PredatorPreyResult* out);

// Black Swan Harvester: Extreme Value Theory (EVT)
ASI_API void asi_harvest_black_swan(const double* extreme_ticks, int len, double threshold, 
                                     ExtremeValueResult* out);
