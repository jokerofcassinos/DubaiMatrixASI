#include <vector>
#include <cmath>
#include <numeric>
#include <algorithm>

extern "C" {
    // 1. Dirac-Fermi Surface Pressure
    // Modela o Order Book como um Gás de Fermi.
    // Calcula a "Pressão de Fermi" que impede a compressão do preço contra paredes de liquidez.
    // Se a energia cinética do preço (Velocity) supera a Pressão de Fermi, o rompimento é iminente.
    __declspec(dllexport) double calculate_fermi_pressure(double* volumes, int size, double temperature) {
        if (size == 0) return 0.0;

        // Distribuição de Fermi-Dirac: f(E) = 1 / (exp((E - mu)/kT) + 1)
        // Aqui mu (Potencial Químico) é o volume médio.
        double mu = 0.0;
        for(int i=0; i<size; i++) mu += volumes[i];
        mu /= size;

        double total_pressure = 0.0;
        double kT = temperature + 1e-9;

        for(int i=0; i<size; i++) {
            double E = volumes[i];
            double occupation = 1.0 / (std::exp((E - mu) / kT) + 1.0);
            total_pressure += E * occupation;
        }

        return total_pressure / size;
    }

    // 2. Chern-Simons Topological Protection Index
    // Calcula a invariante topológica de 3-formas do enxame.
    // Mede a "robustez helicoidal" do sinal. Se o sinal gira no espaço de fase
    // mantendo a sua forma, ele está topologicamente protegido contra reversão.
    __declspec(dllexport) double calculate_chern_simons_index(double* x, double* y, double* z, int size) {
        if (size < 2) return 0.0;

        double helicity = 0.0;
        for (int i = 1; i < size; ++i) {
            // Produto escalar entre a velocidade e o rotacional (v . curl v)
            double vx = x[i] - x[i-1];
            double vy = y[i] - y[i-1];
            double vz = z[i] - z[i-1];

            // Aproximação de helicidade em 3D (Price, Volume, Entropy)
            helicity += (x[i] * vy - y[i] * vx) * vz; 
        }

        return helicity / size;
    }
}
