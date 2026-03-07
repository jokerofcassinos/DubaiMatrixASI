#include "asi_core.h"
#include <vector>
#include <random>
#include <cmath>
#include <algorithm>

/*
    DUBAI MATRIX ASI — LIQUID STATE ENGINE (C++)
    Implementação de Reservoir Computing para HFT.
    Alta performance, latência sub-milissegundo.
*/

static std::vector<double> reservoir_state;
static std::vector<std::vector<double>> w_internal;
static std::vector<std::vector<double>> w_input;
static int reservoir_size = 0;

ASI_API void asi_init_reservoir(int n_neurons, double spectral_radius, double connectivity) {
    reservoir_size = n_neurons;
    reservoir_state.assign(n_neurons, 0.0);
    
    std::mt19937 gen(42);
    std::uniform_real_distribution<> dis(-1.0, 1.0);
    
    w_internal.assign(n_neurons, std::vector<double>(n_neurons, 0.0));
    for (int i = 0; i < n_neurons; i++) {
        for (int j = 0; j < n_neurons; j++) {
            if ((double)rand() / RAND_MAX < connectivity) {
                w_internal[i][j] = dis(gen);
            }
        }
    }
    
    // Simplificação: Scaling do raio espectral (aproximado)
    for (int i = 0; i < n_neurons; i++) {
        for (int j = 0; j < n_neurons; j++) {
            w_internal[i][j] *= (spectral_radius / std::sqrt(n_neurons * connectivity));
        }
    }
    
    // Pesos de entrada (fixos, aleatórios)
    w_input.assign(n_neurons, std::vector<double>(10, 0.0)); // Supondo até 10 inputs
    for (int i = 0; i < n_neurons; i++) {
        for (int j = 0; j < 10; j++) {
            w_input[i][j] = dis(gen);
        }
    }
}

ASI_API void asi_perturb_reservoir(const double* inputs, int n_inputs) {
    if (reservoir_size <= 0) return;
    
    std::vector<double> next_state(reservoir_size, 0.0);
    
    for (int i = 0; i < reservoir_size; i++) {
        double activation = 0.0;
        
        // Contribuição interna (recorrência)
        for (int j = 0; j < reservoir_size; j++) {
            activation += w_internal[i][j] * reservoir_state[j];
        }
        
        // Contribuição externa (ticks/book)
        for (int j = 0; j < std::min(n_inputs, 10); j++) {
            activation += w_input[i][j] * inputs[j];
        }
        
        next_state[i] = std::tanh(activation);
    }
    
    reservoir_state = next_state;
}

ASI_API void asi_read_reservoir_output(double* out_waves, int n_outputs) {
    if (reservoir_size <= 0) return;
    
    // Retorna as primeiras N ativações do reservatório como "ondas" de sinal
    for (int i = 0; i < std::min(n_outputs, reservoir_size); i++) {
        out_waves[i] = reservoir_state[i];
    }
}
