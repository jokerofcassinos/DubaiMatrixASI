#include "asi_core.h"
#include <vector>
#include <cmath>
#include <algorithm>

/*
    Information Geometry Engine (Phase Ω-Zero)
    Implementação da Métrica de Fisher e Divergência KL.
    Otimiza a auto-evolução via Gradiente Natural no manifold paramétrico.
*/

ASI_API void asi_calculate_fisher_metric(const double* prev_p, const double* curr_p, int n_bins,
                                        FisherResult* out) {
    if (!prev_p || !curr_p || n_bins < 5) return;

    double kl_div = 0;
    double fisher_info = 0;
    
    for(int i=0; i<n_bins; i++) {
        double p = prev_p[i] + 1e-10;
        double q = curr_p[i] + 1e-10;
        
        // KL Divergence: D_KL(P || Q) = sum(P * log(P/Q))
        kl_div += p * std::log(p / q);
        
        // Fisher Information (Aproximação via derivada discreta do log-likelihood)
        double score = (q - p) / p;
        fisher_info += q * (score * score);
    }

    out->information_distance = std::max(0.0, kl_div);
    out->fisher_information = fisher_info;
    
    // Natural Gradient Step: Proporcional à inversa da Informação de Fisher
    // g_nat = F^-1 * grad
    // Se fisher_info for gigante, 1.0/fisher vira 0. Então usamos log scale invertida e re-escalada
    double fisher_damped = std::log10(fisher_info + 2.0);
    out->natural_gradient_x = 1.0 / fisher_damped;
    
    // Optimal Step Size: Se a distância KL é alta, a mudança de regime é drástica.
    // Reduzimos o step para evitar overshooting no novo manifold.
    out->optimal_step_size = 0.1 / (1.0 + kl_div * 10.0);
}
