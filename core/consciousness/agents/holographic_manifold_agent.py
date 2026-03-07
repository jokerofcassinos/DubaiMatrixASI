import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal
from cpp.asi_bridge import CPP_CORE
from utils.logger import log

class HolographicManifoldAgent(BaseAgent):
    """
    Agente Ω-Class: Holographic Manifold (AdS/CFT).
    Utiliza o Princípio Holográfico para inferir a tensão do bulk (profundidade do book)
    a partir da curvatura da boundary (fluxo de ticks).
    """
    
    def __init__(self, weight=1.5):
        super().__init__(name="HolographicManifold", weight=weight)
        self.description = "Infers deep market pressure via AdS/CFT holographic mapping"
        self.needs_orderflow = True # O agente usa Book data

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        # Puxar dados da fronteira (últimos 100 ticks)
        ticks = np.array([t["mid"] for t in snapshot.recent_ticks][-100:], dtype=np.float64)
        
        # Puxar dados de desequilíbrio (Book)
        # Usamos o delta de volume por nível como vetor de 'bulk'
        book = snapshot.book
        if not book or len(ticks) < 10:
            return AgentSignal(agent_name=self.name, signal=0.0, confidence=0.0, reasoning="Insufficent data", weight=1.0)
            
        bids = [b["volume"] for b in book.get("bids", [])]
        asks = [a["volume"] for a in book.get("asks", [])]
        
        levels = min(len(bids), len(asks))
        imbalance_vec = np.array([bids[i] - asks[i] for i in range(levels)], dtype=np.float64)
        
        # Invocação C++ (Princípio Holográfico)
        holo = CPP_CORE.infer_holographic_pressure(ticks, imbalance_vec)
        
        if not holo:
            return AgentSignal(agent_name=self.name, signal=0.0, confidence=0.0, reasoning="Holographic Engine Failed", weight=1.0)
            
        # O sinal é a pressão do Bulk (AdS) normalizada
        # Bulk Pressure > 0 -> Pressão de compra no hiperespaço
        signal = holo["pressure"]
        
        # A confiança é dada pela Coerência Holográfica (Sincronia Ticks vs Book)
        # Se a fronteira e o volume estão em fase, a projeção é confiável.
        confidence = abs(holo["coherence"])
        
        # Posição geodésica: Distância até a reversão
        # Se a geodésica é curta, o manifold está prestes a colapsar (reversão iminente)
        if holo["geodesic"] < 0.1 and abs(signal) > 0.5:
             log.omega(f"🌀 HOLOGRAPHIC COLLAPSE IMMINENT: Geodesic Dist={holo['geodesic']:.4f}")
             # Inverte o sinal se o manifold estiver instável
             if not holo["stable"]:
                 signal *= -1.0
                 confidence *= 1.2 # Aumenta peso na reversão
        
        return AgentSignal(
            agent_name=self.name,
            signal=float(np.clip(signal, -1.0, 1.0)),
            confidence=float(np.clip(confidence, 0.0, 1.0)),
            reasoning=f"Bulk Pressure: {holo['pressure']:.4f}, Coherence: {holo['coherence']:.4f}",
            weight=1.5 # Agente de Ordem Superior
        )
