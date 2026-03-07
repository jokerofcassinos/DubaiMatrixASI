#include "asi_core.h"
#include <cmath>
#include <vector>
#include <algorithm>

/**
 * Calculador de Caos Determinístico e Horizonte de Lyapunov.
 * Quantifica a taxa de divergência exponencial do mercado.
 * 
 * @param ticks Série temporal de ticks
 * @param len Tamanho da série
 * @param sample_rate Taxa de amostragem (ticks/segundo)
 * @param out [Out] Veredicto de caos
 */
ASI_API void asi_calculate_chaos(const double* ticks, int len, double sample_rate, ChaosResult* out) {
    if (!ticks || len < 50 || !out) {
        if(out) {
            out->lyapunov_exponent = 0.0;
            out->predictability_limit = 0.0;
            out->entropy = 0.0;
            out->is_chaotic = 0;
        }
        return;
    }

    // Estimativa robusta do Expoente Máximo de Lyapunov (MLE)
    // Baseado na divergência de trajetórias próximas no espaço de fase.
    
    double sum_le = 0.0;
    int count = 0;
    
    // Embedding dimension = 5, Delay = 1 (Micro-caos)
    const int delay = 1;
    const int embed = 5;
    
    for (int i = 0; i < len - (embed * delay) - 10; i += 2) {
        // Distância inicial entre dois pontos próximos
        double d0 = 0.0;
        for(int k=0; k<embed; ++k) {
            double diff = ticks[i + k*delay] - ticks[i + k*delay + 1];
            d0 += diff * diff;
        }
        d0 = std::sqrt(d0);
        
        // Distância evoluída após T passos
        double dt_dist = 0.0;
        int T = 10;
        for(int k=0; k<embed; ++k) {
            double diff = ticks[i + k*delay + T] - ticks[i + k*delay + T + 1];
            dt_dist += diff * diff;
        }
        dt_dist = std::sqrt(dt_dist);
        
        if (d0 > 1e-7 && dt_dist > 1e-7) {
            // MLE = 1/T * log(dn/d0)
            sum_le += std::log(dt_dist / d0) / static_cast<double>(T);
            count++;
        }
    }
    
    double lambda = (count > 0) ? (sum_le / count) : 0.0;
    lambda *= sample_rate; // Escala Hz

    out->lyapunov_exponent = lambda;
    
    // Tempo de Lyapunov = 1 / Lambda
    // Captura o tempo médio após o qual as previsões se tornam ruído
    if (lambda > 1e-5) {
        out->predictability_limit = 1.0 / lambda;
        out->is_chaotic = (lambda > 0.05) ? 1 : 0; // Threshold empírico de caos HFT
    } else {
        out->predictability_limit = 3600.0; // Estabilidade absoluta
        out->is_chaotic = 0;
    }
    
    // Shannon-like Entropy (Variabilidade local)
    double mean = 0.0;
    for(int i=0; i<len; ++i) mean += ticks[i];
    mean /= len;
    
    double var = 0.0;
    for(int i=0; i<len; ++i) var += (ticks[i]-mean)*(ticks[i]-mean);
    out->entropy = std::sqrt(var/len);
}
