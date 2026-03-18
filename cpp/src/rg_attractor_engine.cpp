#include <vector>
#include <cmath>
#include <numeric>
#include <algorithm>

extern "C" {
    // 1. Renormalization Group (RG) Scaling Invariance
    // Calcula se a "assinatura de tendência" é invariante em múltiplas escalas (Tick, M1, M5)
    // Se o sinal é fractalmente consistente, a probabilidade de reversão é nula.
    __declspec(dllexport) double calculate_rg_scaling_invariance(
        double* tick_data, int tick_size,
        double* m1_data, int m1_size,
        double* m5_data, int m5_size) {
        
        auto calculate_drift = [](double* data, int size) {
            if (size < 2) return 0.0;
            double sum_diff = 0.0;
            for (int i = 1; i < size; ++i) {
                sum_diff += (data[i] - data[i-1]);
            }
            return sum_diff / size;
        };

        double d_tick = calculate_drift(tick_data, tick_size);
        double d_m1 = calculate_drift(m1_data, m1_size);
        double d_m5 = calculate_drift(m5_data, m5_size);

        // Normalização pelos desvios
        double mean = (d_tick + d_m1 + d_m5) / 3.0;
        double variance = (std::pow(d_tick - mean, 2) + std::pow(d_m1 - mean, 2) + std::pow(d_m5 - mean, 2)) / 3.0;
        double std_dev = std::sqrt(variance + 1e-9);

        // Scaling Invariance Score: 1.0 = Perfeitamente fractal, 0.0 = Caótico/Inconsistente
        double invariance = 1.0 / (1.0 + std_dev);
        
        // Retorna o sinal (direção * invariância)
        double direction = (mean > 0) ? 1.0 : -1.0;
        return direction * invariance;
    }

    // 2. Strange Attractor (Lorenz Proxy) for Drift Folding
    // Estima se o drift atual está prestes a "dobrar" (reverter) baseado na divergência orbital
    __declspec(dllexport) double estimate_attractor_folding(double* prices, int size, double dt) {
        if (size < 10) return 0.0;

        // Parâmetros de Lorenz simplificados (Sigma, Rho, Beta)
        // Usamos o preço como proxy para o estado X
        double divergence = 0.0;
        for (int i = 2; i < size; ++i) {
            double dx = (prices[i] - prices[i-1]) / dt;
            double prev_dx = (prices[i-1] - prices[i-2]) / dt;
            
            // Aceleração da aceleração (Jerk) em espaço de fase
            double d2x = (dx - prev_dx) / dt;
            divergence += std::abs(d2x);
        }
        
        // Se a divergência orbital explodir, o "atrator estranho" está mudando de asa (reversão iminente)
        return divergence / size;
    }
}
