"""
╔══════════════════════════════════════════════════════════════════════════════╗
║             DUBAI MATRIX ASI — MEAN FIELD GAME AGENT (MFG)                   ║
║     Agente que modela a multidão como fluido e otimiza trajetórias.          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import Optional
from core.consciousness.agents.base import BaseAgent, AgentSignal
from core.consciousness.regime_detector import MarketRegime
from cpp.asi_bridge import CPP_CORE

class MeanFieldGameAgent(BaseAgent):
    """
    Agente baseado em Teoria dos Jogos de Campo Médio (MFG).
    Resolve as equações acopladas HJB e Fokker-Planck para 'surfar' a massa.
    """

    def __init__(self, weight=2.5):
        super().__init__("MeanFieldGame", weight=weight)
        self.needs_orderflow = True

    def analyze(self, snapshot, orderflow_analysis=None, **kwargs) -> Optional[AgentSignal]:
        if not hasattr(snapshot, 'close') or snapshot.close is None or len(snapshot.close) < 20:
            return None

        closes = snapshot.close[-20:]
        volumes = snapshot.volume[-20:] if hasattr(snapshot, 'volume') else np.ones(len(closes))
        
        price_min = float(np.min(closes))
        price_max = float(np.max(closes))
        price_step = (price_max - price_min) / 10.0 if price_max > price_min else 1.0
        
        # Histograma de volume como proxy para densidade de massa
        density, _ = np.histogram(closes, bins=11, range=(price_min, price_max + price_step), weights=volumes)
        density = density.astype(np.float64)
        
        # 2. Definir Função de Recompensa
        regime = kwargs.get('regime_state')
        bias = 0.0
        if regime:
            if hasattr(regime, 'current'):
                curr = regime.current
                if curr in [MarketRegime.TRENDING_BULL, MarketRegime.CREEPING_BULL, MarketRegime.BREAKOUT_UP]:
                    bias = 1.0
                elif curr in [MarketRegime.TRENDING_BEAR, MarketRegime.DRIFTING_BEAR, MarketRegime.BREAKOUT_DOWN]:
                    bias = -1.0
            elif isinstance(regime, dict):
                bias = float(regime.get('bias', 0.0))

        rewards = np.linspace(-bias, bias, 11).astype(np.float64)
        
        # 3. Resolver MFG via C++
        volatility = float(snapshot.atr) if hasattr(snapshot, 'atr') and snapshot.atr > 0 else (price_max - price_min) * 0.1
        if volatility <= 0: volatility = 1e-6
        
        current_price = float(snapshot.close[-1])
        
        mfg = CPP_CORE.solve_mfg(
            density, price_min, price_step, current_price, volatility, rewards
        )
        
        if not mfg:
            return None

        # 4. Decisão baseada na Velocidade Ótima e Estabilidade
        velocity = mfg['optimal_velocity']
        stability = mfg['stability']
        
        signal = np.tanh(velocity)
        confidence = np.clip(stability * 0.8, 0.1, 0.9)
        
        reasoning = f"Massa: {mfg['crowd_density']:.1e} | OptVel: {velocity:.4f} | Stab: {stability:.2f}"
        
        return AgentSignal(
            agent_name=self.name,
            signal=float(signal),
            confidence=float(confidence),
            reasoning=reasoning
        )
