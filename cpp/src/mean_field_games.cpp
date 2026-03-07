#include "asi_core.h"
#include <cmath>
#include <vector>
#include <algorithm>

/**
 * Solucionador de Mean Field Games (MFG) para Trajetória de Capital.
 * Acopla HJB (Estratégia ASI) e Fokker-Planck (Dinâmica de Massa).
 * 
 * @param density_profile Histograma de densidade (Volume Profile)
 * @param len Tamanho do array
 * @param price_min Preço base do perfil
 * @param price_step Incremento de preço por bin
 * @param current_price Preço spot atual
 * @param volatility Volatilidade (difusão)
 * @param reward_function Mapa de potencial de recompensa (Alpha Surface)
 * @param out [Out] Veredicto geodésico
 */
ASI_API void asi_solve_mfg(const double* density_profile, int len, 
                           double price_min, double price_step,
                           double current_price, double volatility, 
                           const double* reward_function, MFGResult* out) {
    if (!density_profile || !reward_function || !out || len < 3 || price_step <= 0) return;

    // 1. Localizar índice do preço
    int idx = static_cast<int>((current_price - price_min) / price_step);
    if (idx < 1) idx = 1;
    if (idx >= len - 1) idx = len - 2;

    // 2. Fokker-Planck (Massa de Traders)
    // rho_t + div(rho * v) = D * laplacian(rho)
    // Estimamos o drift da multidão baseado no gradiente de densidade e difusão
    double rho = density_profile[idx];
    double drho = (density_profile[idx + 1] - density_profile[idx - 1]) / (2.0 * price_step);
    double d2rho = (density_profile[idx + 1] - 2.0 * rho + density_profile[idx - 1]) / (price_step * price_step);
    
    // Drift da massa (em direção à liquidez)
    double mass_drift = -drho * (volatility * volatility * 0.5);

    // 3. HJB (Hamilton-Jacobi-Bellman - Nosso Valor)
    // V_t + H(x, grad V) = f(x, rho)
    // f(x, rho) é a recompensa ajustada pela densidade (custo de congestionamento)
    double val = reward_function[idx];
    double dval = (reward_function[idx + 1] - reward_function[idx - 1]) / (2.0 * price_step);
    
    // 4. Acoplamento Ótimo
    // A nossa "velocidade" (agressividade) deve se opor à fricção da massa 
    // e seguir o gradiente de valor máximo.
    double congestion_cost = 1.0 + (rho * 0.1); // Custo proporcional à densidade local
    
    out->crowd_density = rho;
    out->optimal_velocity = dval / congestion_cost;
    out->expected_drift = mass_drift;
    
    // Medida de coerência entre nosso alvo e o fluxo da massa
    double alignment = (out->optimal_velocity * mass_drift > 0) ? 1.0 : -0.5;
    out->stability_score = std::tanh(alignment + 1.0 / (1.0 + std::abs(d2rho)));
}
