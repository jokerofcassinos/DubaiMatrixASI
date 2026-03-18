#include <vector>
#include <cmath>
#include <numeric>
#include <complex>

extern "C" {
    // 1. Topological Braiding Index
    // Calcula o "Winding Number" de um enxame de agentes em espaço de fase.
    // Strands: Sinais de N agentes ao longo do tempo.
    // Se o enxame está "trançado" (braided) em torno de um eixo direcional,
    // a tendência é topologicamente protegida contra ruído.
    __declspec(dllexport) double calculate_braid_index(double* strands, int n_agents, int lookback) {
        if (n_agents < 2 || lookback < 2) return 0.0;

        double total_winding = 0.0;
        
        // Strands é um array 2D linearizado [n_agents * lookback]
        for (int i = 0; i < n_agents - 1; ++i) {
            for (int t = 1; t < lookback; ++t) {
                double x1 = strands[i * lookback + (t - 1)];
                double y1 = strands[(i + 1) * lookback + (t - 1)];
                double x2 = strands[i * lookback + t];
                double y2 = strands[(i + 1) * lookback + t];

                // Calcula o ângulo da variação entre duas strands (fase complexa)
                std::complex<double> z1(x1, y1);
                std::complex<double> z2(x2, y2);
                
                if (std::abs(z1) > 1e-5 && std::abs(z2) > 1e-5) {
                    total_winding += std::arg(z2 / z1);
                }
            }
        }

        // Normalizado pelo número de interações
        return total_winding / (n_agents * lookback);
    }

    // 2. Kaldor-Hicks Market Efficiency
    // Avalia se uma ordem Taker é "socialmente eficiente" para o book da ASI.
    // Compara o ganho de utilidade (Alpha) vs o custo de impacto (Slippage + Spread).
    __declspec(dllexport) double calculate_kaldor_hicks_ratio(
        double expected_alpha, double slippage_est, double spread, double commission) {
        
        double individual_gain = expected_alpha;
        double societal_cost = slippage_est + (spread * 0.5) + commission;
        
        if (societal_cost <= 0) return 10.0; // Eficiência máxima

        // Ratio > 1.0 significa que o ganho compensa a destruição de liquidez local
        return individual_gain / societal_cost;
    }
}
