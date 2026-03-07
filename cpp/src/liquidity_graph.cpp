#include "asi_core.h"
#include <vector>
#include <cmath>
#include <algorithm>
#include <map>

/*
    LGNN - Liquidity Graph Neural Networks (Implementation)
    Mapeia o livro e fita como um Grafo Direcionado Dinâmico.
*/

ASI_API void asi_calculate_lgnn(const TickData* ticks, int tick_count, 
                                 const double* book_prices, const double* book_vols, int levels,
                                 GraphResult* out) {
    if (!out) return;

    // 1. Identificar Clusters de Liquidez (Nós)
    std::map<double, double> nodes;
    for (int i = 0; i < levels; i++) {
        nodes[book_prices[i]] += book_vols[i];
    }

    // 2. Mapear Aceleração de Agressões (Arestas)
    double total_imbalance = 0.0;
    double velocity_sum = 0.0;
    
    for (int i = 0; i < tick_count; i++) {
        total_imbalance += (ticks[i].ask - ticks[i].bid) * ticks[i].volume;
        if (i > 0) {
            velocity_sum += std::abs(ticks[i].last - ticks[i-1].last);
        }
    }

    // 3. Cálculo Simplificado de Centralidade de Autovetor (Proxy via Liquidez Relativa e Pressão)
    int count = 0;
    double max_liq = 0.0;
    for (auto const& [price, liq] : nodes) {
        if (liq > max_liq) max_liq = liq;
    }

    for (auto const& [price, liq] : nodes) {
        if (count >= 50) break;
        
        out->clusters[count].price = price;
        out->clusters[count].liquidity = liq;
        
        // Centralidade como função de Liquidez vs Distância do Preço Atual
        double dist = std::abs(price - (tick_count > 0 ? ticks[tick_count-1].last : price));
        double proximity_factor = 1.0 / (1.0 + dist);
        
        out->clusters[count].centrality = (liq / (max_liq + 0.0001)) * proximity_factor;
        out->clusters[count].velocity = velocity_sum / (tick_count + 1);
        
        count++;
    }

    out->cluster_count = count;

    // 4. Probabilidade de Avalanche (Distorção de Centralidade + Desequilíbrio)
    out->avalanche_risk = std::tanh(std::abs(total_imbalance) * 0.001 * (velocity_sum + 1.0));
    out->global_centrality = max_liq > 0 ? (total_imbalance / max_liq) : 0.0;
}

// ═══════════════════════════════════════════════════════════
//  HYPERBOLIC GEOMETRY (Poincaré Ball)
// ═══════════════════════════════════════════════════════════

ASI_API double asi_map_poincare_dist(double r1, double theta1, double r2, double theta2) {
    // r e theta representam coordenadas polares na "bola de Poincaré"
    // Distância hiperbólica d(u, v) = arcosh(1 + 2 * ||u-v||^2 / ((1-||u||^2)(1-||v||^2)))
    
    // Converter para cartesianas
    double x1 = r1 * std::cos(theta1);
    double y1 = r1 * std::sin(theta1);
    double x2 = r2 * std::cos(theta2);
    double y2 = r2 * std::sin(theta2);
    
    double norm_u_sq = x1*x1 + y1*y1;
    double norm_v_sq = x2*x2 + y2*y2;
    double dist_sq = (x1-x2)*(x1-x2) + (y1-y2)*(y1-y2);
    
    // Normalização para garantir que estamos dentro da bola aberta (r < 1)
    if (norm_u_sq >= 1.0) norm_u_sq = 0.999;
    if (norm_v_sq >= 1.0) norm_v_sq = 0.999;
    
    double val = 1.0 + 2.0 * dist_sq / ((1.0 - norm_u_sq) * (1.0 - norm_v_sq));
    return std::acosh(val);
}
