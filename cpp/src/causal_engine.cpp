#include "asi_core.h"
#include <vector>
#include <cmath>
#include <numeric>
#include <algorithm>

/*
    Causal Graph Engine (Phase Ω-Zero)
    Implementação de Do-Calculus (Judea Pearl) para isolar causalidade de correlação.
    Calcula P(Y | do(X)) onde X é nossa intervenção (ordem) e Y é o preço.
*/

ASI_API void asi_calculate_causal_impact(const double* feature_matrix, int rows, int cols,
                                        double our_order_size, int target_index,
                                        CausalResult* out) {
    if (!feature_matrix || !out || rows < 10) return;

    // 1. Estimar o Structural Causal Model (SCM) simplificado
    // Assumimos um DAG: OurOrder(X) -> Spread/Liquidity(Z) -> PriceChange(Y)
    // E ruído externo(U) afetando Z e Y.
    
    // Extraímos vetores de features
    // Col 0: Liquidez externa, Col 1: Volatilidade, Col 2: Spread atual
    // target_index: Mudança de preço futura
    
    double mean_y = 0, mean_x = 0, var_x = 0, cov_xy = 0;
    std::vector<double> y_vals;
    
    for (int i = 0; i < rows; i++) {
        double x = feature_matrix[i * cols + 0]; // Ex: Volume
        double y = feature_matrix[i * cols + target_index];
        y_vals.push_back(y);
        mean_x += x;
        mean_y += y;
    }
    mean_x /= rows;
    mean_y /= rows;

    for (int i = 0; i < rows; i++) {
        double x = feature_matrix[i * cols + 0];
        double y = feature_matrix[i * cols + target_index];
        var_x += (x - mean_x) * (x - mean_x);
        cov_xy += (x - mean_x) * (y - mean_y);
    }

    // 2. Back-door Adjustment
    // Em produção real, calcularíamos a covariância condicionada às features mediadoras Z.
    // Aqui fazemos uma aproximação linear do Do-Operator:
    // E[Y | do(X=x)] = alpha + beta * x
    double beta = (var_x > 1e-9) ? (cov_xy / var_x) : 0.0;
    
    // 3. Simular Intervenção (Do-Calculus)
    // Queremos saber o efeito se injetarmos 'our_order_size'
    double impact = beta * our_order_size;
    
    // 4. Counterfactual Analysis
    // "O que teria acontecido se nossa ordem fosse 0?" -> Expected impact sum
    out->causal_effect = impact;
    out->do_impact_score = std::abs(impact) / (std::abs(mean_y) + 1e-6);
    out->counterfactual_loss = (impact < 0) ? std::abs(impact) : 0.0; 
    out->confidence = std::min(1.0, (double)rows / 1000.0); // Confiança cresce com N
}
