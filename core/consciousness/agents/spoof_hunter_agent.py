import numpy as np
import time
from typing import Dict, Any, List
from core.consciousness.agents.base import BaseAgent, AgentSignal
from market.data_engine import MarketSnapshot
from utils.logger import log

class SpoofHunterAgent(BaseAgent):
    """
    [Phase Ω-12] Predador de Liquidez (Spoof Hunter)
    
    Analisa a correlação não-linear entre a Velocidade Extrema da Fita (Tick Velocity)
    e a Volatilidade de Cancelamentos no Livro de Ofertas (Imbalance Variance).
    
    Se o mercado acelera, mas o Book está tremendo (cancelamentos massivos de limites),
    o movimento direcional é uma ilusão induzida por Market Makers.
    """
    
    def __init__(self, weight: float = 1.0, memory_size: int = 150):
        super().__init__("SpoofHunterAgent", weight)
        self.memory_size = memory_size
        self._history_time: List[float] = []
        self._history_imbalance: List[float] = []
        self._history_price: List[float] = []
        
    def analyze(self, snapshot: MarketSnapshot, **kwargs) -> AgentSignal:
        now = time.time()
        
        # Calcular imbalance instantâneo do L1/L2
        bids = snapshot.book.get("bids", [])
        asks = snapshot.book.get("asks", [])
        
        bid_vol = sum(b.get("volume", 0) for b in bids) if bids and isinstance(bids[0], dict) else sum(bids) if bids else 0
        ask_vol = sum(a.get("volume", 0) for a in asks) if asks and isinstance(asks[0], dict) else sum(asks) if asks else 0
        
        total_vol = bid_vol + ask_vol
        imbalance = (bid_vol - ask_vol) / total_vol if total_vol > 0 else 0.0
        
        # Memória circular
        self._history_time.append(now)
        self._history_imbalance.append(imbalance)
        self._history_price.append(snapshot.price)
        
        if len(self._history_time) > self.memory_size:
            self._history_time.pop(0)
            self._history_imbalance.pop(0)
            self._history_price.pop(0)
            
        if len(self._history_time) < 30:
            return AgentSignal(self.name, 0.0, 0.0, "INITIALIZING", self.weight)
            
        # 1. Velocidade Cinética (Ticks por segundo real)
        dt = self._history_time[-1] - self._history_time[0]
        if dt <= 0: return AgentSignal(self.name, 0.0, 0.0, "DT_ZERO", self.weight)
        tick_velocity = len(self._history_time) / dt
        
        # 2. Volatilidade do Imbalance (Flash Spoofing)
        imb_array = np.array(self._history_imbalance)
        imb_volatility = np.std(imb_array)
        
        # 3. Deltas de preço
        price_delta = self._history_price[-1] - self._history_price[0]
        
        # Importar OMEGA dinamicamente para evitar circular dependence
        from config.omega_params import OMEGA

        # Thresholds
        velocity_threshold = OMEGA.get("spoof_velocity_threshold", 30.0)
        spoof_variance_threshold = OMEGA.get("spoof_variance_threshold", 0.40)
        
        if tick_velocity < velocity_threshold:
            return AgentSignal(self.name, 0.0, 0.0, "LOW_VELOCITY", self.weight)
            
        if imb_volatility < spoof_variance_threshold:
            return AgentSignal(self.name, 0.0, 0.0, "STABLE_BOOK", self.weight)
            
        # DETECÇÃO: Velocidade Alta + Book Piscando (Spoofing Variance)
        signal = 0.0
        conf = 0.0
        reason = "NORMAL_ORDERFLOW"
        
        if price_delta > 0:
            signal = -0.95
            conf = 0.90
            reason = f"FAKE_PUMP_SPOOF (Vel={tick_velocity:.1f}, Var={imb_volatility:.3f})"
        elif price_delta < 0:
            signal = 0.95
            conf = 0.90
            reason = f"FAKE_DUMP_SPOOF (Vel={tick_velocity:.1f}, Var={imb_volatility:.3f})"
            
        return AgentSignal(self.name, signal, conf, reason, self.weight)
