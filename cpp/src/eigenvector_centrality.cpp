#include <vector>
#include <cmath>
#include <iostream>

extern "C" {
    // Calcula a Centralidade de Autovetor (PageRank) para o Order Book.
    // O Book é modelado como um Grafo de transição Markoviana.
    // Reescrito para não depender de bibliotecas externas (Eigen)
    __declspec(dllexport) void calculate_eigenvector_centrality(
        double* price_levels, double* volumes, int size, double damping_factor, double* out_centralities) {
        
        if (size <= 1) return;
        
        std::vector<std::vector<double>> transition_matrix(size, std::vector<double>(size, 0.0));
        double total_volume = 0.0;
        
        for (int i = 0; i < size; ++i) {
            total_volume += volumes[i];
            out_centralities[i] = 1.0 / size; // Inicialização uniforme
        }
        
        if (total_volume <= 0.0) return;

        // Construir matriz de transição baseada na distância do preço e atração do volume
        for (int i = 0; i < size; ++i) {
            double row_sum = 0.0;
            for (int j = 0; j < size; ++j) {
                if (i != j) {
                    double dist = std::abs(price_levels[i] - price_levels[j]);
                    double attraction = volumes[j] / (dist * dist + 1e-5); // Gravidade inversa do quadrado
                    transition_matrix[i][j] = attraction;
                    row_sum += attraction;
                }
            }
            // Normalização estocástica da linha com damping factor (Google PageRank style)
            if (row_sum > 0) {
                for (int j = 0; j < size; ++j) {
                    transition_matrix[i][j] = (transition_matrix[i][j] / row_sum) * damping_factor + (1.0 - damping_factor) / size;
                }
            } else {
                for (int j = 0; j < size; ++j) {
                    transition_matrix[i][j] = 1.0 / size;
                }
            }
        }

        // Power Iteration para encontrar o Autovetor principal (estado estacionário)
        std::vector<double> v(size, 1.0 / size);
        std::vector<double> next_v(size, 0.0);
        
        for (int iter = 0; iter < 50; ++iter) {
            // next_v = v^T * M
            double norm_sq = 0.0;
            for (int j = 0; j < size; ++j) {
                next_v[j] = 0.0;
                for (int i = 0; i < size; ++i) {
                    next_v[j] += v[i] * transition_matrix[i][j];
                }
                norm_sq += next_v[j] * next_v[j];
            }
            
            // Normalize
            double norm = std::sqrt(norm_sq);
            if (norm > 0) {
                for (int j = 0; j < size; ++j) {
                    next_v[j] /= norm;
                }
            }
            
            // Check convergence
            double diff = 0.0;
            for (int j = 0; j < size; ++j) {
                diff += std::abs(next_v[j] - v[j]);
            }
            
            v = next_v;
            
            if (diff < 1e-6) {
                break;
            }
        }

        // Output results
        for (int i = 0; i < size; ++i) {
            out_centralities[i] = v[i];
        }
    }
}
