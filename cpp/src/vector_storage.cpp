#include "asi_core.h"
#include <cmath>
#include <vector>
#include <algorithm>

/*
    Vector Storage & Search (Phase Ω-Next)
    Implementação de busca vetorial (Cosine Similarity) acelerada.
*/

ASI_API int asi_vector_search(const double* query, const double* database, int query_dim, int db_size, double* out_similarities, int* out_indices, int top_k) {
    if (!query || !database || !out_similarities || !out_indices) return 0;

    std::vector<std::pair<double, int>> results;
    results.reserve(db_size);

    // 1. Calcular norma do query
    double query_norm = 0.0;
    for (int j = 0; j < query_dim; j++) query_norm += query[j] * query[j];
    query_norm = std::sqrt(query_norm);

    if (query_norm < 1e-10) return 0;

    // 2. Busca exaustiva (Brute Force Cosine Similarity)
    // Otimização: Em produção real usaríamos quantização ou HNSW, 
    // mas para "Market Intuition" regional, 10k-100k vetores cabem no L3/RAM.
    for (int i = 0; i < db_size; i++) {
        const double* entry = &database[i * query_dim];
        double dot_product = 0.0;
        double entry_norm = 0.0;
        
        for (int j = 0; j < query_dim; j++) {
            dot_product += query[j] * entry[j];
            entry_norm += entry[j] * entry[j];
        }
        
        entry_norm = std::sqrt(entry_norm);
        double similarity = (entry_norm > 1e-10) ? (dot_product / (query_norm * entry_norm)) : 0.0;
        
        results.push_back({similarity, i});
    }

    // 3. Sort por similaridade decrescente
    std::partial_sort(results.begin(), results.begin() + std::min(top_k, db_size), results.end(),
                      [](const std::pair<double, int>& a, const std::pair<double, int>& b) {
                          return a.first > b.first;
                      });

    // 4. Retornar top_k
    int actual_k = std::min(top_k, db_size);
    for (int i = 0; i < actual_k; i++) {
        out_similarities[i] = results[i].first;
        out_indices[i] = results[i].second;
    }

    return actual_k;
}
