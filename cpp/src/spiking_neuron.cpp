#include "asi_core.h"
#include <cmath>
#include <algorithm>

/**
 * Motor de Neurônio Leaky Integrate-and-Fire (LIF).
 * Resolve: dv/dt = (V_rest - V + R*I) / (R*C)
 * 
 * @param input_current Corrente de entrada (ex: pressão de orderflow)
 * @param dt Delta tempo (ms)
 * @param v_rest Potencial de repouso
 * @param v_threshold Limiar de disparo
 * @param resistance Resistência de membrana
 * @param capacitance Capacitância de membrana (determina inércia)
 * @param in_out_v_potential [In/Out] Potencial de membrana
 * @param out_fired [Out] 1 se disparou
 */
ASI_API void asi_update_lif_neuron(double input_current, double dt, 
                                   double v_rest, double v_threshold, 
                                   double resistance, double capacitance, 
                                   double* in_out_v_potential, int* out_fired) {
    if (!in_out_v_potential || !out_fired) return;

    double v = *in_out_v_potential;
    double rc = resistance * capacitance;
    
    // Euler integration para a EDO do neurônio LIF
    // dv = dt * ( (V_rest - V) + R*I ) / RC
    // dt em ms, rc costuma ser ms também (time constant tau = RC)
    double step_dt = (dt > 0.0) ? dt : 1.0; 
    double dv = step_dt * ((v_rest - v) + (resistance * input_current)) / rc;
    v += dv;

    *out_fired = 0;
    if (v >= v_threshold) {
        *out_fired = 1;
        v = v_rest; // Reset após disparo (paradigma simples)
    } else if (v < v_rest - 10.0) {
        // Lower bound para evitar potenciais negativos absurdos em pressões contrárias
        v = v_rest - 10.0;
    }

    *in_out_v_potential = v;
}
