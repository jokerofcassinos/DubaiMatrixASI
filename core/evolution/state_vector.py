import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, asdict

log = logging.getLogger("SOLENN.StateVector")

@dataclass(frozen=True, slots=True)
class StateVectorData:
    """[Ω-DNA] Representação discreta e imutável do estado de mercado."""
    session: str         # [Ω-10.T] Sessão Financeira (T_ASIAN, T_LONDON, T_NY, T_DEAD)
    regime: str          # [Ω-4] Regime Consolidado (R_TREND, R_REVERSAL, R_CHOPPY, etc.)
    velocity: str        # [Ω-10.M] Velocidade HFT (V_HFT_BURST, V_HIGH, V_MED, V_LOW)
    entropy: str         # [Ω-1.QOFE] Estado de Entropia (E_CHAOTIC, E_COMPLEX, E_ORDERED)
    volatility: str      # [Ω-10.V] Banda de ATR (VOL_EXTREME, VOL_HIGH, VOL_NORMAL, VOL_COMP)
    profile_hash: str    # [Ω-43] Hash Topológico Único (DNA de Contexto)

class StateVectorEngine:
    """
    Ω-4, Ω-43 & Ω-10: O Motor de Discretização Topológica da SOLÉNN.
    
    Converte a continuidade do mercado em um DNA finito p/ mapeamento genético.
    """
    
    def __init__(self):
        self.last_state: Optional[StateVectorData] = None

    def discretize(self, snapshot: Any) -> StateVectorData:
        """[Ω-EXEC] Transmuta snapshot contínuo em vetor discreto."""
        
        session = self._get_session(snapshot)
        regime = self._get_regime(snapshot)
        velocity = self._get_velocity(snapshot)
        entropy = self._get_entropy(snapshot)
        volatility = self._get_volatility(snapshot)
        
        # [Ω-43] Geração do Hash Determinístico (DNA)
        profile_hash = f"{session}|{regime}|{velocity}|{entropy}|{volatility}"
        
        state = StateVectorData(
            session=session,
            regime=regime,
            velocity=velocity,
            entropy=entropy,
            volatility=volatility,
            profile_hash=profile_hash
        )
        
        self.last_state = state
        return state

    def _get_session(self, snapshot: Any) -> str:
        """V2-V5: Classificação de Sessão UTC (Ω-10.T)."""
        try:
            # Assume snapshot.timestamp em ms
            ts = snapshot.timestamp / 1000.0 if hasattr(snapshot, "timestamp") else 0.0
            dt = datetime.fromtimestamp(ts, tz=timezone.utc) if ts > 0 else datetime.now(timezone.utc)
            hour = dt.hour
            
            if 0 <= hour < 8: return "T_ASIAN"    # Madrugada (Acúmulo)
            if 8 <= hour < 14: return "T_LONDON"  # Manhã (Volume)
            if 14 <= hour < 20: return "T_NY"     # Tarde (Reversão/Vol)
            return "T_DEAD"                       # Noite (Baixa Liquidez)
        except Exception:
            return "T_UNKNOWN"

    def _get_regime(self, snapshot: Any) -> str:
        """V10-V15: Compressão de Regimes (Ω-4)."""
        regime_val = str(getattr(snapshot, "regime", "UNKNOWN")).upper()
        
        if "TREND" in regime_val: return "R_TREND"
        if "IGNITION" in regime_val or "BREAKOUT" in regime_val: return "R_IGNITION"
        if "REVERSAL" in regime_val: return "R_REVERSAL"
        if "CHOPPY" in regime_val: return "R_CHOPPY"
        if "DRIFT" in regime_val: return "R_DRIFT"
        
        return "R_UNKNOWN"

    def _get_velocity(self, snapshot: Any) -> str:
        """V20-V23: Bandas de Velocidade HFT (Ω-10.M)."""
        vel = abs(float(snapshot.metadata.get("tick_velocity", 0.0))) if hasattr(snapshot, "metadata") else 0.0
        
        if vel > 20.0: return "V_HFT_BURST"
        if vel > 10.0: return "V_HIGH"
        if vel > 3.0:  return "V_MED"
        return "V_LOW"

    def _get_entropy(self, snapshot: Any) -> str:
        """V29-V31: Estados de Entropia Shannon (Ω-1.QOFE)."""
        ent = float(snapshot.metadata.get("shannon_entropy", 0.0)) if hasattr(snapshot, "metadata") else 0.0
        
        if ent > 6.5: return "E_CHAOTIC"
        if ent > 3.0: return "E_COMPLEX"
        return "E_ORDERED"

    def _get_volatility(self, snapshot: Any) -> str:
        """V38-V41: Bandas de ATR (Ω-10.V)."""
        atr = float(getattr(snapshot, "atr", 0.0))
        
        if atr > 150.0: return "VOL_EXTREME"
        if atr > 80.0:  return "VOL_HIGH"
        if atr > 30.0:  return "VOL_NORMAL"
        return "VOL_COMP"

# Motor de Vetor de Estado Ω (v2) inicializado.
# O DNA do mercado agora é legível pela SOLÉNN.
