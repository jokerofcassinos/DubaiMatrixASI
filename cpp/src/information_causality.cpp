#include <vector>
#include <cmath>
#include <numeric>
#include <algorithm>
#include <map>

extern "C" {
    // 1. Transfer Entropy (TE) - Shannon Information Flow
    // Calcula o fluxo de informação direcional de uma série X (ex: ETH) para Y (ex: BTC).
    // TE = H(Y_next | Y_past) - H(Y_next | Y_past, X_past)
    // Se TE(X->Y) > TE(Y->X), X é um leading indicator de Y.
    __declspec(dllexport) double calculate_transfer_entropy(double* x_data, double* y_data, int size, int bins) {
        if (size < 20) return 0.0;

        // Discretização (Binning) simples
        auto get_bins = [bins](double* data, int n) {
            std::vector<int> b(n);
            double min_val = data[0], max_val = data[0];
            for(int i=1; i<n; i++) {
                if(data[i] < min_val) min_val = data[i];
                if(data[i] > max_val) max_val = data[i];
            }
            double range = max_val - min_val + 1e-9;
            for(int i=0; i<n; i++) {
                b[i] = (int)((data[i] - min_val) / range * (bins - 1));
            }
            return b;
        };

        std::vector<int> bx = get_bins(x_data, size);
        std::vector<int> by = get_bins(y_data, size);

        // H(Y_next | Y_past)
        std::map<std::pair<int, int>, int> count_y_next_past;
        std::map<int, int> count_y_past;
        for(int i=1; i<size; i++) {
            count_y_next_past[{by[i], by[i-1]}]++;
            count_y_past[by[i-1]]++;
        }

        double h_y_cond_y = 0;
        for(auto const& [key, val] : count_y_next_past) {
            double p_joint = (double)val / (size - 1);
            double p_cond = (double)val / count_y_past[key.second];
            h_y_cond_y -= p_joint * std::log2(p_cond);
        }

        // H(Y_next | Y_past, X_past)
        struct Triple { int y_next, y_past, x_past; bool operator<(const Triple& o) const { if(y_next!=o.y_next) return y_next<o.y_next; if(y_past!=o.y_past) return y_past<o.y_past; return x_past<o.x_past; } };
        std::map<Triple, int> count_triple;
        std::map<std::pair<int, int>, int> count_yx_past;
        for(int i=1; i<size; i++) {
            count_triple[{by[i], by[i-1], bx[i-1]}]++;
            count_yx_past[{by[i-1], bx[i-1]}]++;
        }

        double h_y_cond_yx = 0;
        for(auto const& [key, val] : count_triple) {
            double p_joint = (double)val / (size - 1);
            double p_cond = (double)val / count_yx_past[{key.y_past, key.x_past}];
            h_y_cond_yx -= p_joint * std::log2(p_cond);
        }

        double transfer_entropy = h_y_cond_y - h_y_cond_yx;
        return (transfer_entropy > 0) ? transfer_entropy : 0.0;
    }

    // 2. Kramers-Kronig Causal Relation (Dispersive Sensor)
    // Calcula a "Suscetibilidade" do preço baseada na relação entre volatilidade (Imaginária) 
    // e o deslocamento real (Real). Detecta se o mercado está "super-aquecido" (dispersão anômala).
    __declspec(dllexport) double calculate_kramers_kronig_anomaly(double* returns, int size) {
        if (size < 10) return 0.0;

        double sum_real = 0.0;
        double sum_imag = 0.0; // Volatilidade como proxy de resposta imaginária

        for(int i=0; i<size; i++) {
            sum_real += returns[i];
            sum_imag += std::abs(returns[i]);
        }

        // Em equilíbrio, a relação real/imaginária é constante.
        // Se a dispersão (volatilidade) cresce sem deslocamento real correspondente, 
        // a causalidade está "esticada" (reversão iminente).
        double ratio = std::abs(sum_real) / (sum_imag + 1e-9);
        return ratio;
    }
}
