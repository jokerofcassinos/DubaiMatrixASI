import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal
from config.omega_params import OMEGA

class GhostOrderInferenceAgent(BaseAgent):
    """
    Ω-PhD-8 AGENT: GHOST ORDER INFERENCE (PREDATORY SWEEP DETECTOR)
    
    Analisa a densidade de "rebatida" em níveis-chave para detectar Ordens Livres Passivas (Icebergs/Ghosts).
    Se o preço atinge um nível técnico de suporte, o varejo espera um salto (rebound largo).
    Mas se os "bounces" subsequentes são curtíssimos e imediatamente consumidos, 
    uma instituição está absorvendo ordens LIMIT de forma furtiva para induzir quebra (Sweep).
    
    Nesses casos, a ASI deve vender CONTRA o suporte (Antecipar o Rompimento Predatório).
    """
    
    def __init__(self, weight=4.8):
        super().__init__("GhostOrderInference", weight=weight)
        
    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        tick_buffer = snapshot.metadata.get("tick_buffer", [])
        if len(tick_buffer) < 50:
            return AgentSignal(self.name, 0.0, 0.0, "INSUFFICIENT_TAPE_DATA", self.weight)

        prices = np.array([t.get("last", 0) for t in tick_buffer], dtype=np.float64)
        
        # 1. Definir o range recente (Micro-Estrutura de curto prazo)
        p_max = np.max(prices)
        p_min = np.min(prices)
        current = prices[-1]
        
        if p_max == p_min:
            return AgentSignal(self.name, 0.0, 0.0, "ZERO_VOLATILITY", self.weight)
            
        range_size = p_max - p_min
        
        # 2. Estamos próximos a um extremo? (Testando Suporte ou Resistência)
        # Próximo a 10% do range
        dist_to_min = current - p_min
        dist_to_max = p_max - current
        
        is_at_support = dist_to_min <= (range_size * 0.15)
        is_at_resistance = dist_to_max <= (range_size * 0.15)
        
        signal = 0.0
        conf = 0.0
        reason = "NO_GHOST_ACTIVITY"
        
        threshold = OMEGA.get("ghost_absorption_threshold", 0.85)

        if is_at_support:
            # Testando densidade de rebound
            # Medimos os retornos positivos após o mínimo ter sido atingido
            min_index = np.argmin(prices)
            if min_index < len(prices) - 5: # Há vida após a mínima?
                post_min_prices = prices[min_index:]
                rebound = np.max(post_min_prices) - p_min
                
                # Se o preço não subiu nem 15% do range original, está sendo sugado (Absorvido no chão)
                if rebound < (range_size * 0.15):
                    # Absorção Perigosa (Suporte Falso!)
                    signal = -1.0 # VENDA (Antecipa Rompimento)
                    conf = min(0.98, threshold * 1.05)
                    reason = f"GHOST_SWEEP_DETECTED (Passive Absorption at Support, Rebound={rebound:.1f})"

        elif is_at_resistance:
            # Inverso para topo
            max_index = np.argmax(prices)
            if max_index < len(prices) - 5:
                post_max_prices = prices[max_index:]
                retrace = p_max - np.min(post_max_prices)
                
                if retrace < (range_size * 0.15):
                    # Absorção em topo (Vai romper pra cima)
                    signal = 1.0 # COMPRA
                    conf = min(0.98, threshold * 1.05)
                    reason = f"GHOST_SWEEP_DETECTED (Passive Absorption at Resistance, Retrace={retrace:.1f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)
