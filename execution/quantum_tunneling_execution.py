import numpy as np
from config.omega_params import OMEGA
from utils.logger import log

class QuantumTunnelingExecution:
    """
    Ω-PhD-9 EXECUTION LAYER: QUANTUM TUNNELING EXECUTION (LSE)
    
    Calcula a probabilidade de "Tunelamento" do preço através de barreiras 
    de liquidez (Paredes de Ordens / S&R).
    
    Diferente de um rompimento clássico (Momentum), o tunelamento ocorre quando 
    a densidade de ordens opostas é "vazada" por absorção microscópica, 
    permitindo uma entrada antecipada (Ghost Entry).
    """

    @staticmethod
    def calculate_tunneling_probability(snapshot, signal_direction: float) -> float:
        """
        P = exp(-2 * L * sqrt(2m(V - E)) / h_bar)
        
        Proxy:
        L = Distância até a barreira (S/R)
        V = Potencial da Barreira (Volume na Parede)
        E = Energia Cinética do Preço (Momentum * Tick Velocity)
        """
        try:
            # 1. Obter Barreiras (S/R mais próximas)
            # Simplificamos usando o Volume no Bid/Ask como barreira de potencial
            # e a distância ao preço atual.
            
            # Se sinal é BUY (1.0), barreira é o ASK (Potencial de Venda)
            # Se sinal é SELL (-1.0), barreira é o BID (Potencial de Compra)
            
            dist_to_wall = abs(snapshot.metadata.get("spread", 1.0)) # L
            wall_volume = snapshot.metadata.get("sell_volume", 1.0) if signal_direction > 0 else snapshot.metadata.get("buy_volume", 1.0)
            
            # 2. Energia Cinética (E)
            velocity = abs(snapshot.metadata.get("tick_velocity", 0.0))
            momentum = abs(snapshot.metadata.get("momentum_delta", 0.1))
            kinetic_energy = velocity * momentum
            
            # 3. Barreira de Potencial (V)
            # Normalizada pelo Volume Médio
            barrier_potential = wall_volume / (snapshot.metadata.get("avg_tick_volume", 1.0) + 1e-9)
            
            # 4. Cálculo de Tunelamento (Quantum Leakage)
            # Se E < V, o preço "tunela". Se E > V, o preço "rompe" classicamente.
            if kinetic_energy >= barrier_potential:
                return 1.0 # Rompimento Clássico (100% de passagem)
            
            # m = Masa inercial (Volume total do snapshot)
            mass = snapshot.metadata.get("total_tick_volume", 10.0)
            
            # Delta Energy: V - E
            delta_e = max(0.0001, barrier_potential - kinetic_energy)
            
            # Probabilidade Exponencial (Schrödinger Proxy)
            # h_bar = 1.0 (Constante reduzida da Matrix)
            barrier_width = dist_to_wall * 2.0
            p_tunneling = np.exp(-1.0 * barrier_width * np.sqrt(mass * delta_e))
            
            return float(p_tunneling)
            
        except Exception as e:
            log.warning(f"Quantum Tunneling Calculation Error: {e}")
            return 0.0

    @classmethod
    def should_authorize_ghost_entry(cls, snapshot, decision) -> bool:
        """
        Autoriza entrada mesmo sem rompimento formal se P(Tunneling) > threshold.
        """
        if decision.action.name == "WAIT":
            return False
            
        direction = 1.0 if decision.action.name == "BUY" else -1.0
        p_tunnel = cls.calculate_tunneling_probability(snapshot, direction)
        
        threshold = OMEGA.get("quantum_tunneling_threshold", 0.65)
        
        if p_tunnel > threshold:
            log.omega(f"👻 [Ω-GHOST ENTRY] Quantum Tunneling Detected (P={p_tunnel:.3f} > {threshold:.2f}). Authorizing immediate strike.")
            return True
            
        return False
