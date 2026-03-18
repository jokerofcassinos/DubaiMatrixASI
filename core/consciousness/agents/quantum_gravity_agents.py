import numpy as np
import math
from typing import Dict, Any, List, Optional
from core.consciousness.agents.base import BaseAgent, AgentSignal
from cpp.asi_bridge import CPP_CORE
from utils.decorators import catch_and_log
from config.omega_params import OMEGA

class EventHorizonAgent(BaseAgent):
    """
    [Ω-GRAVITY] Liquidity Event Horizon (Schwarzschild Radius).
    In a Drifting Bear regime, old supports are not barriers, they are Black Holes.
    If price crosses the 'Radius of No Return' (e.g. < 2 ATRs from a tested support),
    the agent forces a SELL to capture the inevitable liquidation cascade.
    """
    def __init__(self, weight: float = 1.0):
        super().__init__("EventHorizonAgent", weight)
        
    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        regime = snapshot.regime.value if snapshot.regime else "UNKNOWN"
        is_drifting_down = regime in ["DRIFTING_BEAR", "LIQUIDATION_CASCADE"]
        
        if not is_drifting_down:
            return None # Agent only acts as a gravitational pull during down-drifts
            
        candles_m5 = snapshot.candles.get("M5")
        if not candles_m5 or len(candles_m5["low"]) < 50:
            return None
            
        lows = np.array(candles_m5["low"], dtype=np.float64)
        price = snapshot.price
        atr = getattr(snapshot, 'atr', 0)
        
        if atr == 0: return None
        
        # Find recent structural valleys
        valleys = []
        for i in range(2, len(lows) - 5):
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                valleys.append(lows[i])
                
        if not valleys: return None
        
        # Check proximity to the lowest recent valley
        for valley in valleys[-10:]:
            if price > valley: # Price is approaching from above
                distance_to_valley = price - valley
                distance_in_atr = distance_to_valley / atr
                
                # Schwarzschild Radius condition: 
                # If we are within 2.5 ATRs of a support that has been tested (Black Hole)
                # and drifting down, we will inevitably be sucked in.
                if distance_in_atr < 2.5 and distance_in_atr > 0.1:
                    matches = sum(1 for v in valleys if abs((v - valley)/valley*100) < 0.1)
                    if matches >= 2: # Massive gravity well
                        return AgentSignal(
                            self.name, -1.0, 0.95, 
                            f"Price crossed Event Horizon of Support {valley:.0f} (Dist: {distance_in_atr:.1f} ATR). Inevitable Tunneling.", 
                            self.weight
                        )
                        
        return None

class QuantumTunnelingDecayAgent(BaseAgent):
    """
    [Ω-DECAY] Quantum Tunneling Probability.
    A support level decays with each impact. If it's touched 4+ times, 
    the probability of the 5th impact breaking through approaches 1.0.
    """
    def __init__(self, weight: float = 1.0):
        super().__init__("QuantumTunnelingDecayAgent", weight)
        
    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        candles = snapshot.candles.get("M1")
        if not candles or len(candles["low"]) < 50: return None
        
        lows = np.array(candles["low"])
        price = snapshot.price
        
        valleys = []
        for i in range(2, len(lows) - 5):
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                valleys.append(lows[i])
                
        for valley in valleys[-20:]:
            dist = (price - valley) / price * 100
            if abs(dist) < 0.05: # Price is currently at the support
                # Count impacts in the last 100 bars
                impacts = sum(1 for v in lows[-100:] if abs((v - valley)/valley*100) < 0.05)
                if impacts >= 4:
                    return AgentSignal(
                        self.name, -1.0, 0.99, 
                        f"Barrier Fatigue: Support {valley:.0f} impacted {impacts} times. Quantum Tunneling imminent.", 
                        self.weight
                    )
                    
        return None

class DarkMatterAbsorptionAgent(BaseAgent):
    """
    [Ω-DARK-MATTER] Compares price deceleration with visible order book mass.
    If price slows down but visible volume is thin, Dark Matter (Icebergs/Hidden Limit Orders)
    is absorbing the impact.
    """
    def __init__(self, weight: float = 1.0):
        super().__init__("DarkMatterAbsorptionAgent", weight)
        
    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        if not CPP_CORE.is_loaded: return None
        
        tick_vel = snapshot.metadata.get("tick_velocity", 0.0)
        book = snapshot.book
        if not book: return None
        
        # Calculate visible mass near the spread (MT5 book entries are dictionaries)
        visible_bid_mass = sum(item["volume"] for item in book.get("bids", [])[:5])
        visible_ask_mass = sum(item["volume"] for item in book.get("asks", [])[:5])
        
        # Acceleration proxy (change in velocity over last 5 ticks)
        # Simplified: using absolute velocity as kinetic energy proxy
        acceleration = abs(tick_vel) 
        
        try:
            # If going down (tick_vel < 0), check bid mass. If going up, check ask mass.
            if tick_vel < 0:
                dark_gravity = CPP_CORE.calculate_dark_matter_gravity(acceleration, visible_bid_mass)
                if dark_gravity > visible_bid_mass * 10:
                    # Huge unseen absorption at the bottom
                    return AgentSignal(self.name, 1.0, 0.85, f"Dark Matter Bid Absorption (Hidden Mass: {dark_gravity:.2f})", self.weight)
            elif tick_vel > 0:
                dark_gravity = CPP_CORE.calculate_dark_matter_gravity(acceleration, visible_ask_mass)
                if dark_gravity > visible_ask_mass * 10:
                    # Huge unseen absorption at the top
                    return AgentSignal(self.name, -1.0, 0.85, f"Dark Matter Ask Absorption (Hidden Mass: {dark_gravity:.2f})", self.weight)
                    
            return AgentSignal(self.name, 0.0, 0.1, "Newtonian mechanics hold", self.weight)
        except:
            return None

class EigenvectorCentralityAgent(BaseAgent):
    """
    [Ω-PAGERANK] Eigenvector Centrality of Liquidity.
    Maps the Order Book as a Markov Chain. Finds the true gravitational 
    hub of the market (the price level where the network converges).
    """
    def __init__(self, weight: float = 1.0):
        super().__init__("EigenvectorCentralityAgent", weight)
        
    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        if not CPP_CORE.is_loaded: return None
        
        book = snapshot.book
        if not book: return None
        
        prices = []
        volumes = []
        # MT5 book entries are dictionaries: {"price": float, "volume": float, ...}
        for item in book.get("bids", [])[:25]:
            prices.append(item["price"])
            volumes.append(item["volume"])
        for item in book.get("asks", [])[:25]:
            prices.append(item["price"])
            volumes.append(item["volume"])
            
        if len(prices) < 10: return None
        
        try:
            p_arr = np.array(prices, dtype=np.float64)
            v_arr = np.array(volumes, dtype=np.float64)
            
            centralities = CPP_CORE.calculate_eigenvector_centrality(p_arr, v_arr, 0.85)
            
            if centralities is None or len(centralities) == 0: return None
            
            max_idx = np.argmax(centralities)
            hub_price = prices[max_idx]
            hub_centrality = centralities[max_idx]
            
            current_price = snapshot.price
            
            # If the most central node is far away, the price will be pulled towards it.
            if hub_centrality > 0.15: # Highly dominant node
                bias = 1.0 if hub_price > current_price else -1.0
                dist = abs(hub_price - current_price)
                atr = getattr(snapshot, 'atr', current_price * 0.001)
                if dist > atr * 0.2:
                    return AgentSignal(self.name, bias, 0.88, f"Eigenvector Gravitational Pull towards {hub_price:.2f} (C={hub_centrality:.2f})", self.weight)
                    
            return AgentSignal(self.name, 0.0, 0.1, "Dispersed Liquidity Network", self.weight)
        except:
            return None
