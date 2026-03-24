"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — STATE VECTOR ENGINE (HNP)              ║
║                                                                              ║
║  Módulo responsável por discretizar as condições infinitas do mercado em     ║
║  um "DNA" topológico finito (Hash) para mapeamento genético de agentes.      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from typing import Dict, Any
from datetime import datetime
import numpy as np

class StateVectorData:
    """
    Representação unidimensional (Hash Discreto) do estado contínuo do mercado.
    Usado para mapear a performance dos agentes (Neural Profiling) contra contextos específicos.
    """
    
    def __init__(self, snapshot: Any):
        self.time_of_day = self._get_time_of_day(snapshot)
        self.regime = self._get_regime(snapshot)
        self.velocity_band = self._get_velocity_band(snapshot)
        self.entropy_state = self._get_entropy_state(snapshot)
        self.volatility_band = self._get_volatility_band(snapshot)
        
        # 🧬 O Hash Topológico Único
        self.profile_hash = f"{self.time_of_day}|{self.regime}|{self.velocity_band}|{self.entropy_state}|{self.volatility_band}"

    def _get_time_of_day(self, snapshot) -> str:
        """Classifica a sessão financeira de acordo com a liquidez macro."""
        # Se timestamp for int/float de ms
        try:
            dt = datetime.fromtimestamp(snapshot.timestamp / 1000.0) if hasattr(snapshot, 'timestamp') and snapshot.timestamp else datetime.utcnow()
            hour = dt.hour
            if 0 <= hour < 8: return "T_ASIAN"   # Sessão Asiática (Chop/Drift)
            if 8 <= hour < 14: return "T_LONDON" # Sessão Londres/Sobreposição NY (Alto Volume)
            if 14 <= hour < 20: return "T_NY"    # Sessão NY Tarde
            return "T_DEAD"                      # Fim do dia, baixa liquidez
        except Exception:
            return "T_UNKNOWN"

    def _get_regime(self, snapshot) -> str:
        """Extrai o regime consolidado do RegimeDetector."""
        if hasattr(snapshot, 'regime') and snapshot.regime:
            v_val = snapshot.regime.value if hasattr(snapshot.regime, 'value') else str(snapshot.regime)
            # Simplifica regimes para evitar hiperfragmentação do HNP
            if "TREND" in v_val: return "R_TREND"
            if "IGNITION" in v_val or "BREAKOUT" in v_val: return "R_IGNITION"
            if "REVERSAL" in v_val: return "R_REVERSAL"
            if "CHOPPY" in v_val: return "R_CHOPPY"
            return "R_DRIFT" # Drift Bear / Drift Bull caem como Drift macro para perfil genético
        return "R_UNKNOWN"

    def _get_velocity_band(self, snapshot) -> str:
        """Classifica a velocidade de fita (HFT Speed)."""
        vel = snapshot.metadata.get("tick_velocity", 0.0) if hasattr(snapshot, "metadata") else 0.0
        vel = abs(vel)
        if vel > 20.0: return "V_HFT_BURST"
        if vel > 10.0: return "V_HIGH"
        if vel > 3.0:  return "V_MED"
        return "V_LOW"

    def _get_entropy_state(self, snapshot) -> str:
        """Classifica a complexidade informacional do mercado (Grau de Caos)."""
        ent = snapshot.metadata.get("shannon_entropy", 0.0) if hasattr(snapshot, "metadata") else 0.0
        if ent > 6.5: return "E_CHAOTIC"     # Muito ruído/Random Walk
        if ent > 3.0: return "E_COMPLEX"     # Dinâmica normal
        return "E_ORDERED"                   # Mercado previsível / tendência limpa

    def _get_volatility_band(self, snapshot) -> str:
        """Classifica a expansão de ATR."""
        atr = getattr(snapshot, "atr", 0.0)
        if atr > 150.0: return "VOL_EXTREME"
        if atr > 80.0:  return "VOL_HIGH"
        if atr > 30.0:  return "VOL_NORMAL"
        return "VOL_COMPRESSED"

    def to_dict(self) -> Dict[str, str]:
        return {
            "time_of_day": self.time_of_day,
            "regime": self.regime,
            "velocity_band": self.velocity_band,
            "entropy_state": self.entropy_state,
            "volatility_band": self.volatility_band,
            "profile_hash": self.profile_hash
        }
