#include "asi_core.h"
#include <vector>
#include <cmath>
#include <algorithm>

/*
    Topology Core (Phase Ω-Zero)
    Implementação de Homologia Persistente simplificada para Order Book.
    Detecta quando a estrutura de liquidez perde coesão.
*/

ASI_API void asi_calculate_topology(const double* prices, const double* volumes, int levels,
                                   TopologyResult* out) {
    if (!prices || !volumes || levels < 5) return;

    // 1. Point Cloud Construction
    // Mapeamos (Preço, Volume) como pontos no plano R2
    std::vector<std::pair<double, double>> points;
    double max_vol = 0;
    for(int i=0; i<levels; i++) if(volumes[i] > max_vol) max_vol = volumes[i];
    
    for(int i=0; i<levels; i++) {
        points.push_back({prices[i], volumes[i] / (max_vol + 1e-6)});
    }

    // 2. Vietoris-Rips Complex (Aproximação)
    // Calculamos distâncias entre níveis de preço/volume adjacentes
    std::vector<double> gaps;
    for(int i=0; i<levels-1; i++) {
        double d_price = std::abs(prices[i+1] - prices[i]);
        gaps.push_back(d_price);
    }

    // 3. Betti Numbers Estimation
    // Betti 0: Componentes conectados (baixa fragmentação)
    // Betti 1: Buracos de liquidez (zonas de gap onde o preço 'atravessa')
    double avg_gap = 0;
    for(double g : gaps) avg_gap += g;
    avg_gap /= (levels - 1);

    int holes = 0;
    double max_hole = 0;
    for(double g : gaps) {
        if(g > avg_gap * 3.5) { // Limiar de "buraco topológico"
            holes++;
            if(g > max_hole) max_hole = g;
        }
    }

    // 4. Persistence Entropy
    // Mede a complexidade da forma estrutural
    double entropy = 0;
    for(double g : gaps) {
        if(g > 0) {
            double p = g / (avg_gap * levels);
            entropy -= p * std::log(p + 1e-10);
        }
    }

    out->betti_0 = (double)levels - (double)holes;
    out->betti_1 = (double)holes;
    out->persistence_entropy = entropy;
    out->critical_hole_size = max_hole;
    
    // Se o maior buraco for muito grande em relação ao preço médio, 
    // a topologia indica instabilidade geométrica.
    out->is_geometrically_unstable = (max_hole > prices[0] * 0.001) ? 1 : 0;
}
