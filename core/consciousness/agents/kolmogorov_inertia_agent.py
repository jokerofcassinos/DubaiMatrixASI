import numpy as np
import zlib
from core.consciousness.agents.base import BaseAgent, AgentSignal
from config.omega_params import OMEGA

class KolmogorovInertiaAgent(BaseAgent):
    """
    Ω-PhD-8 AGENT: KOLMOGOROV INERTIA AGENT
    
    Analiza a complexidade algorítmica do fluxo de ticks (Tape).
    Diferencia "Fitas Programadas" (bots institucionais) de "Ruído Orgânico" (retail).
    
    Se a fita é altamente compressível (baixa complexidade), a ASI entra com 
    o "Freight Train" (Institutional Convergence).
    """
    
    def __init__(self, weight=4.8):
        super().__init__("KolmogorovInertia", weight=weight)
        
    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        tick_buffer = snapshot.recent_ticks[-100:] if hasattr(snapshot, 'recent_ticks') else []
        if not tick_buffer:
            tick_buffer = snapshot.metadata.get("tick_buffer", [])[-100:]
            
        if len(tick_buffer) < 50:
            return AgentSignal(self.name, 0.0, 0.0, "INSUFFICIENT_TAPE_DATA", self.weight)

        # 1. Serializar o Fluxo de Ticks (Binarização Baseada em Sentido)
        # 1 = Tick de Alta, 0 = Tick de Baixa
        binary_tape = "".join(["1" if (tick_buffer[i].get("last", 0) > tick_buffer[i-1].get("last", 0)) 
                               else "0" for i in range(1, len(tick_buffer))])
        
        # 2. Calcular a Razão de Compressão (Proxy para Complexidade de Kolmogorov)
        # S0 = Comprimento da fita original
        # S1 = Comprimento da fita comprimida
        # D = S1 / S0 (Ratio)
        raw_size = len(binary_tape)
        compressed_size = len(zlib.compress(binary_tape.encode('utf-8')))
        
        # Como zlib tem overhead para strings curtas, normalizamos o ratio
        # Em sequências perfeitamente algorítmicas (ex: 101010), o ratio cai drasticamente.
        complexity_ratio = compressed_size / raw_size
        
        # 3. Decision Logic (Programmatic Momentum)
        # Threshold: < 0.35 (Altamente compressível / Repetitivo)
        kolmogorov_thresh = OMEGA.get("kolmogorov_ratio_threshold", 0.40)
        
        signal = 0.0
        conf = 0.0
        reason = "ORGANIC_RETAIL_CHAOS"
        
        if complexity_ratio < kolmogorov_thresh:
            # Fita Programática! Os bots estão gerando uma estrutura fractal 
            # de alta previsibilidade (Inércia Algorítmica).
            
            # Determinar a direção dominante na fita programada
            bull_ticks = binary_tape.count("1")
            bear_ticks = binary_tape.count("0")
            
            # Se a fita é compressível e tem um viés claro (> 60%)
            bias = (bull_ticks - bear_ticks) / raw_size
            
            if abs(bias) > 0.1:
                signal = np.sign(bias)
                # Confiança inversamente proporcional à complexidade
                conf = min(0.99, (1.0 - complexity_ratio) * 1.5)
                reason = f"ALGORITHMIC_FREIGHT_TRAIN (Complexity={complexity_ratio:.2f} < {kolmogorov_thresh:.1f})"
                
        return AgentSignal(self.name, signal, conf, reason, self.weight)
