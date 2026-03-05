/*
╔══════════════════════════════════════════════════════════════════════════════╗
║         DUBAI MATRIX ASI — ORDER FLOW PROCESSOR (C++)                      ║
║    Análise de microestrutura tick-by-tick em velocidade nativa             ║
║                                                                              ║
║  Processa arrays de ticks para extrair delta, imbalance, absorção,        ║
║  exaustão e volume climax com zero overhead de interpretação.              ║
╚══════════════════════════════════════════════════════════════════════════════╝
*/

#include "asi_core.h"
#include <cmath>
#include <algorithm>
#include <vector>

ASI_API void asi_process_orderflow(const TickData* ticks, int count, OrderFlowResult* result) {
    if (count <= 0 || !result) return;
    
    // Reset result
    result->cumulative_delta = 0.0;
    result->buy_volume = 0.0;
    result->sell_volume = 0.0;
    result->order_imbalance = 0.0;
    result->tick_velocity = 0.0;
    result->is_absorption = 0;
    result->is_exhaustion = 0;
    result->volume_climax_score = 0.0;
    
    if (count < 2) return;
    
    double total_volume = 0.0;
    double price_change_sum = 0.0;
    double max_volume = 0.0;
    double avg_volume = 0.0;
    
    // ═══ PASS 1: Classificar cada tick como Buy ou Sell ═══
    // Método: Lee-Ready tick rule (comparar last com mid)
    for (int i = 0; i < count; i++) {
        double mid = (ticks[i].bid + ticks[i].ask) / 2.0;
        double vol = ticks[i].volume;
        
        if (vol <= 0.0) vol = 1.0; // Fallback
        
        total_volume += vol;
        if (vol > max_volume) max_volume = vol;
        
        if (ticks[i].last >= mid) {
            // Agressão compradora (buy at ask)
            result->buy_volume += vol;
            result->cumulative_delta += vol;
        } else {
            // Agressão vendedora (sell at bid)
            result->sell_volume += vol;
            result->cumulative_delta -= vol;
        }
        
        if (i > 0) {
            price_change_sum += std::abs(ticks[i].last - ticks[i - 1].last);
        }
    }
    
    avg_volume = total_volume / count;
    
    // ═══ ORDER IMBALANCE ═══
    // [-1, +1] onde +1 = 100% compradores, -1 = 100% vendedores
    if (total_volume > 0.0) {
        result->order_imbalance = (result->buy_volume - result->sell_volume) / total_volume;
    }
    
    // ═══ TICK VELOCITY ═══
    // Velocidade de mudança de preço (proxy para momentum)
    if (count > 1) {
        double time_span_ms = (double)(ticks[count - 1].time_msc - ticks[0].time_msc);
        double price_range = ticks[count - 1].last - ticks[0].last;
        
        if (time_span_ms > 0.0) {
            result->tick_velocity = (price_range / time_span_ms) * 1000.0; // Por segundo
        }
    }
    
    // ═══ VOLUME CLIMAX DETECTION ═══
    // Volume climax = volume pico muito acima da média
    if (avg_volume > 0.0 && max_volume > 0.0) {
        result->volume_climax_score = max_volume / avg_volume;
    }
    
    // ═══ ABSORPTION DETECTION ═══
    // Alto volume + preço não se moveu = alguém absorveu
    if (count >= 5) {
        double first_price = ticks[0].last;
        double last_price = ticks[count - 1].last;
        double price_net_change = std::abs(last_price - first_price);
        double avg_tick_range = price_change_sum / (count - 1);
        
        // Se volume alto MAS preço quase não saiu do lugar = absorção
        bool high_volume = total_volume > avg_volume * count * 1.5;
        bool low_movement = price_net_change < avg_tick_range * 2.0;
        
        result->is_absorption = (high_volume && low_movement) ? 1 : 0;
    }
    
    // ═══ EXHAUSTION DETECTION ═══
    // Forte Delta em uma direção + preço desacelerando = exaustão
    if (count >= 10) {
        // Verificar se os últimos ticks estão desacelerando
        double first_half_delta = 0.0;
        double second_half_delta = 0.0;
        int half = count / 2;
        
        for (int i = 0; i < half; i++) {
            double mid = (ticks[i].bid + ticks[i].ask) / 2.0;
            double vol = std::max(ticks[i].volume, 1.0);
            first_half_delta += (ticks[i].last >= mid) ? vol : -vol;
        }
        for (int i = half; i < count; i++) {
            double mid = (ticks[i].bid + ticks[i].ask) / 2.0;
            double vol = std::max(ticks[i].volume, 1.0);
            second_half_delta += (ticks[i].last >= mid) ? vol : -vol;
        }
        
        // Exaustão: primeira metade forte numa direção, segunda metade fraca ou reversa
        bool strong_first = std::abs(first_half_delta) > avg_volume * half;
        bool weak_second = std::abs(second_half_delta) < std::abs(first_half_delta) * 0.3;
        bool reversed = (first_half_delta > 0 && second_half_delta < 0) ||
                       (first_half_delta < 0 && second_half_delta > 0);
        
        result->is_exhaustion = (strong_first && (weak_second || reversed)) ? 1 : 0;
    }
}
