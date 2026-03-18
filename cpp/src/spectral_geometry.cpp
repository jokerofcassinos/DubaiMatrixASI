#include <vector>
#include <cmath>
#include <numeric>
#include <algorithm>
#include <complex>

extern "C" {
    // 1. Spectral Information Flux (SIF)
    // Calcula o fluxo de energia entre bandas de frequência (Teoria de Turbulência de Kolmogorov)
    // Se a energia está cascateando das frequências baixas para as altas, a tendência é autossustentada.
    __declspec(dllexport) double calculate_spectral_flux(double* data, int size) {
        if (size < 32) return 0.0;

        // Implementação simplificada de Fluxo de Energia Espectral
        // Comparamos a variância de janelas curtas (Alta freq) vs janelas longas (Baixa freq)
        double energy_low = 0.0;
        double energy_high = 0.0;

        // Baixa frequência: Variação da média móvel longa
        std::vector<double> long_ma(size - 20);
        for(int i = 20; i < size; ++i) {
            double sum = 0;
            for(int j=0; j<20; j++) sum += data[i-j];
            long_ma[i-20] = sum / 20.0;
        }
        for(size_t i=1; i<long_ma.size(); i++) energy_low += std::pow(long_ma[i] - long_ma[i-1], 2);

        // Alta frequência: Variação residual (ruído)
        for(int i=1; i<size; i++) {
            double ma_local = 0;
            int count = 0;
            for(int j=0; j<5 && (i-j)>=0; j++) { ma_local += data[i-j]; count++; }
            ma_local /= count;
            energy_high += std::pow(data[i] - ma_local, 2);
        }

        if (energy_low < 1e-9) return 0.0;
        
        // Fluxo > 1.0: Energia descendo para o micro-scalp (Trend Ignition)
        // Fluxo < 1.0: Energia subindo (Exaustão/Dissipação)
        return energy_high / (energy_low + 1e-9);
    }

    // 2. Quantum Geometric Tensor (QGT) Curvature
    // Calcula a métrica quântica do espaço de Hilbert dos sinais.
    // A curvatura de Berry (imaginária) detecta singularidades de preço.
    __declspec(dllexport) double calculate_berry_curvature(double* signals, int n_agents, int n_steps) {
        if (n_agents < 2 || n_steps < 2) return 0.0;

        double total_curvature = 0.0;
        // Aproximação discreta da fase de Berry acumulada no enxame
        for (int t = 1; t < n_steps; ++t) {
            for (int i = 0; i < n_agents - 1; ++i) {
                double s1 = signals[i * n_steps + (t - 1)];
                double s2 = signals[(i + 1) * n_steps + (t - 1)];
                double s3 = signals[i * n_steps + t];
                double s4 = signals[(i + 1) * n_steps + t];

                // Produto cruzado em espaço de fase 2D
                double area = (s1 * s4 - s2 * s3);
                total_curvature += area;
            }
        }

        return total_curvature / (n_agents * n_steps);
    }
}
