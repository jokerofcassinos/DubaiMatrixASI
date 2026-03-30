"""
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                                 SOLÉNN                                       ║
    ║                       MOTOR DE DADOS v2 (CORTEX) Ω                           ║
    ║                                                                              ║
    ║  "Os dados não são números; são a forma do invisível se manifestando          ║
    ║   no domínio do tempo."                                                      ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
"""

from dataclasses import dataclass, field
import numpy as np

@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    """Snapshot Sincronizado do Mercado (Ω-Vision)."""
    timestamp: float
    symbol: str
    bid: float = 0.0
    ask: float = 0.0
    last_price: float = 0.0
    tick_volume: float = 0.0
    spread: float = 0.0
    
    # Indicadores Ω-1.1
    ema_fast: float = 0.0
    ema_slow: float = 0.0
    rsi_14: float = 50.0
    atr_14: float = 0.01
    
    # Métricas Físicas Ω-1.2
    hurst: float = 0.5
    entropy: float = 2.0
    vol_gk: float = 0.0
    v_pulse: float = 0.0
    jounce: float = 0.0
    lorentz_factor: float = 1.0
    book_imbalance: float = 0.0
    
    features: np.ndarray = field(default_factory=lambda: np.zeros(15))
