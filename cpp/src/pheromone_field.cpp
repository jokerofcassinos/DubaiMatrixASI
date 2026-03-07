#include "asi_core.h"
#include <vector>
#include <map>
#include <cmath>
#include <algorithm>
#include <mutex>

/*
    Neural Stigmergy Engine (Phase Ω-Zero)
    Implementação de Campo de Feromônios para comunicação indireta entre agentes.
    Agentes depositam 'sinais' no ambiente, influenciando o sistema de forma fluida.
*/

// Estrutura interna para gerenciar o campo (em produção real seria Shared Memory / mmap)
struct Pheromone {
    double intensity;
    double last_update;
};

static std::map<int, Pheromone> pheromone_field; // Preço mapeado para ticks (Price * 100)
static std::mutex field_mutex;

ASI_API void asi_deposit_pheromone(double price_level, double intensity, double decay_rate) {
    std::lock_guard<std::mutex> lock(field_mutex);
    int key = (int)(price_level * 100);
    
    if(pheromone_field.find(key) == pheromone_field.end()) {
        pheromone_field[key] = {intensity, 0.0};
    } else {
        // Acumulação estigmergica
        pheromone_field[key].intensity += intensity;
    }
}

ASI_API double asi_sense_pheromone(double price_level) {
    std::lock_guard<std::mutex> lock(field_mutex);
    int key = (int)(price_level * 100);
    
    if(pheromone_field.find(key) != pheromone_field.end()) {
        return pheromone_field[key].intensity;
    }
    return 0.0;
}

ASI_API void asi_update_pheromone_field(double dt) {
    std::lock_guard<std::mutex> lock(field_mutex);
    
    // Evaporar feromônios (decay)
    for(auto it = pheromone_field.begin(); it != pheromone_field.end(); ) {
        it->second.intensity *= (1.0 - 0.05 * dt); // 5% de evaporação por ciclo
        
        if(it->second.intensity < 0.001) {
            it = pheromone_field.erase(it);
        } else {
            ++it;
        }
    }
}
