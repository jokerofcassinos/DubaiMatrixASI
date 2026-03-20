import numpy as np
import time
from typing import Dict, Any, List
from core.consciousness.agents.base import BaseAgent, AgentSignal
from market.data_engine import MarketSnapshot
from utils.logger import log

class PersistentHomologyAgent(BaseAgent):
    """
    [Phase Ω-11] Persistent Homology (Topological ML) Agent.
    
    Analisa a estrutura topológica da nuvem de pontos (Preço x Tempo) dos últimos Ticks.
    Procura por "Betti-1 Holes" (Buracos Topológicos) — regiões de vácuo onde o preço 
    saltou artificialmente (Spoofing) sem formação de densidade de volume em volta.
    
    Se o preço está furando um suporte, mas topologicamente existe um Buraco massivo 
    logicamente abaixo, é uma Armadilha Institucional.
    """
    
    def __init__(self, weight: float = 1.0, lookback_ticks: int = 200, grid_size: int = 10):
        super().__init__("PersistentHomologyAgent", weight)
        self.lookback_ticks = lookback_ticks
        self.grid_size = grid_size
        self.hole_threshold = 0.85 # Quão vazio o centro precisa ser em relação às bordas para ser um Buraco
        
    def analyze(self, snapshot: MarketSnapshot, **kwargs) -> AgentSignal:
        tick_buffer = snapshot.metadata.get("tick_buffer", [])
        if len(tick_buffer) < self.lookback_ticks:
            return AgentSignal(self.name, 0.0, 0.0, "INITIALIZING", self.weight)
            
        # Pega a nuvem de pontos (P, V) do buffer
        prices = np.array([t.get("last", 0) for t in tick_buffer[-self.lookback_ticks:]])
        volumes = np.array([t.get("volume", 0) for t in tick_buffer[-self.lookback_ticks:]])
        
        # Grid 2D Approximation for Topological Density
        min_p, max_p = np.min(prices), np.max(prices)
        if max_p - min_p < 1e-9:
            return AgentSignal(self.name, 0.0, 0.0, "FLAT_TAPE", self.weight)
            
        # Normalizando preços para um Grid
        grid_bins = np.linspace(min_p, max_p, self.grid_size + 1)
        density, _ = np.histogram(prices, bins=grid_bins, weights=volumes)
        
        max_density = np.max(density)
        if max_density < 1e-9:
            return AgentSignal(self.name, 0.0, 0.0, "NO_VOLUME_DENSITY", self.weight)
            
        norm_density = density / max_density
        hole_detected = False
        hole_index = -1
        
        # Precisamos de 1 borda alta, 1 centro vazio (buraco), 1 borda alta.
        left_peak, right_peak = 0.0, 0.0
        for i in range(1, len(norm_density) - 1):
            left_p = max(norm_density[:i]) if i > 0 else 0
            right_p = max(norm_density[i+1:]) if i < len(norm_density) - 1 else 0
            center_hollowness = norm_density[i]
            
            if center_hollowness < (1.0 - self.hole_threshold) and left_p > 0.5 and right_p > 0.5:
                hole_detected = True
                hole_index = i
                left_peak, right_peak = left_p, right_p
                break
                
        if not hole_detected:
            return AgentSignal(self.name, 0.0, 0.0, "CONTINUOUS_TOPOLOGY", self.weight)
            
        hole_price_center = (grid_bins[hole_index] + grid_bins[hole_index+1]) / 2.0
        current_price = snapshot.price
        
        signal = 0.85 if current_price < hole_price_center else -0.85
        betti_strength = (left_peak + right_peak) / 2.0 - norm_density[hole_index]
        
        final_signal = signal * betti_strength
        reason = f"BETTI1_HOLE_DETECTED (PriceCenter={hole_price_center:.2f}, Strength={betti_strength:.2f})"
        
        return AgentSignal(self.name, final_signal, 0.85, reason, self.weight)
