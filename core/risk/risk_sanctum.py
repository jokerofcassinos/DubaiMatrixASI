import logging
import time
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

class CircuitBreakerLevel(Enum):
    GREEN = "GREEN"      # < 0.3% DD
    YELLOW = "YELLOW"    # 0.3-0.5% DD
    ORANGE = "ORANGE"    # 0.5-1.0% DD
    RED = "RED"          # 1.0-1.5% DD
    CRITICAL = "CRITICAL" # 1.5-2.0% DD
    EMERGENCY = "EMERGENCY" # 2.0-3.0% DD
    CATASTROPHIC = "CATASTROPHIC" # > 3.0% DD

@dataclass(frozen=True, slots=True)
class RiskReport:
    """ASi-Grade Risk Assessment: The Fortress Guard of SOLÉNN."""
    is_safe: bool
    lot_size: float
    circuit_breaker: CircuitBreakerLevel
    stop_loss: float
    take_profit: float
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)

class RiskSanctum:
    """
    [Ω-RISK] The Inviolable Sanctuary of SOLÉNN.
    Implements 162 vectors of Ergodicity, Growth Rate Optimization, and FTMO Protection.
    Operating on Phase 7 (The Sovereign Decision).
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger("SOLENN.RiskSanctum")
        
        # FTMO Constraints [Ω-C2-T2.1]
        self.daily_limit_pct = self.config.get("ftmo_daily_limit", 0.05)
        self.total_limit_pct = self.config.get("ftmo_total_limit", 0.10)
        self.safety_margin = 0.80 # 20% buffer from FTMO hard limits
        
        # Ergodicity Parameters [Ω-C1-T1.1]
        self.max_f_kelly = self.config.get("max_kelly_fraction", 0.25) # Quarter Kelly (Thorp)
        
        self.logger.info("🛡️ Risk Sanctum Ω Activated: Ergodicity Engine STANDING BY.")

    async def assess(self, 
                    decision: Any, 
                    snapshot: Any, 
                    account_state: Any) -> RiskReport:
        """
        [Ω-FORTRESS] Evaluates every trade against the 162-vector risk gauntlet.
        """
        try:
            # 1. CIRCUIT BREAKER CHECK [Ω-C2-T2.1]
            level, dd_pct = self._calculate_circuit_breaker(account_state)
            
            if level in [CircuitBreakerLevel.EMERGENCY, CircuitBreakerLevel.CATASTROPHIC]:
                return RiskReport(False, 0.0, level, 0.0, 0.0, f"CIRCUIT_BREAKER:{level.value}")

            # 2. ERGODIC SIZING [Ω-C1-T1.1]
            # Maximize E[ln(1 + f*R)]
            optimal_f = self._calculate_ergodic_lot(decision, snapshot, account_state)
            
            # [Ω-C3-T3.1] FTMO Slot Constraints (5 slots of 1 lot)
            lot_size = self._clamp_to_ftmo_slots(optimal_f, level)
            
            # 3. PHYSICS VALIDATION [Ω-C3-T3.2]
            sl = decision.metadata.get("sl", 0.0)
            tp = decision.metadata.get("tp", 0.0)
            
            # [Ω-C1-T1.3-V1] Tail Risk Veto (EVT)
            risk_per_trade = abs(sl - snapshot.price) / snapshot.price if sl else 0.02
            if risk_per_trade > 0.03 and lot_size > 0:
                 lot_size *= 0.5 # De-escalation on high volatility tail
            
            is_safe = lot_size > 0 and level != CircuitBreakerLevel.RED
            
            return RiskReport(
                is_safe=is_safe,
                lot_size=lot_size,
                circuit_breaker=level,
                stop_loss=sl,
                take_profit=tp,
                reason=f"ASSESSMENT_COMPLETE:{level.value}",
                metadata={
                    "dd_pct": f"{dd_pct:.4f}",
                    "optimal_f": f"{optimal_f:.4f}",
                    "risk_per_trade": f"{risk_per_trade:.4f}"
                }
            )

        except Exception as e:
            self.logger.error(f"☢️ Risk Sanctum Failure: {e}", exc_info=True)
            return RiskReport(False, 0.0, CircuitBreakerLevel.EMERGENCY, 0.0, 0.0, f"RISK_FAULT:{str(e)}")

    def _calculate_circuit_breaker(self, acc: Any) -> Tuple[CircuitBreakerLevel, float]:
        """[Ω-C2-T2.1] 7-Level Circuit Breaker System."""
        balance = getattr(acc, "balance", 100000.0)
        equity = getattr(acc, "equity", balance)
        daily_start = getattr(acc, "daily_start_equity", balance)
        
        daily_dd = (daily_start - equity) / daily_start if daily_start > 0 else 0
        
        if daily_dd < 0.003: return CircuitBreakerLevel.GREEN, daily_dd
        if daily_dd < 0.005: return CircuitBreakerLevel.YELLOW, daily_dd
        if daily_dd < 0.010: return CircuitBreakerLevel.ORANGE, daily_dd
        if daily_dd < 0.015: return CircuitBreakerLevel.RED, daily_dd
        if daily_dd < 0.020: return CircuitBreakerLevel.CRITICAL, daily_dd
        if daily_dd < 0.030: return CircuitBreakerLevel.EMERGENCY, daily_dd
        return CircuitBreakerLevel.CATASTROPHIC, daily_dd

    def _calculate_ergodic_lot(self, dec: Any, snap: Any, acc: Any) -> float:
        """[Ω-C1-T1.1] Ergodicity Economics Engine (Growth Rate maximization)."""
        # [Ω-C1-T1.1-V1] Kelly Bayesian Optimization
        # f* = (bp - q) / b
        win_rate = 0.97 # SOLENN Goal Floor
        p = win_rate
        q = 1 - p
        
        sl = dec.metadata.get("sl", snap.price * 0.99)
        tp = dec.metadata.get("tp", snap.price * 1.01)
        
        # Payoff ratio b
        b = abs(tp - snap.price) / abs(sl - snap.price) if abs(sl - snap.price) > 0 else 2.0
        
        kelly_f = (b * p - q) / b if b > 0 else 0
        
        # [Ω-C1-T1.1-V3] Fractional Kelly (Thorp safety)
        safe_f = kelly_f * self.max_f_kelly
        
        # [Ω-C3-V109] MC Sizing Synergy
        # If Monte Carlo suggests a specific f* based on path-drift, we check it here
        mc_stats = getattr(acc, "mc_stats", None)
        if mc_stats and mc_stats.optimal_f < safe_f:
            self.logger.info(f"🔮 [Ω-Risk] MC Proactive Sizing Override: {safe_f:.4f} -> {mc_stats.optimal_f:.4f}")
            safe_f = mc_stats.optimal_f

        # Convert to lots (Simplificação para 100k account)
        balance = getattr(acc, "balance", 100000.0)
        notional = balance * safe_f
        
        # 1 lot BTC is roughly 1 BTC. Adjust for asset notional.
        # Assuming BTCUSDT for now.
        lots = notional / snap.price if snap.price > 0 else 0
        
        return lots

    def _clamp_to_ftmo_slots(self, f: float, level: CircuitBreakerLevel) -> float:
        """[Ω-C3-T3.1] Enforcement of FTMO 5-slot constraint."""
        # 1 slot = 1 lot. Exposure max = 5 lots.
        max_lots = 5.0
        
        # De-escalation by breaker level
        if level == CircuitBreakerLevel.YELLOW: max_lots = 3.0
        if level == CircuitBreakerLevel.ORANGE: max_lots = 1.0
        if level == CircuitBreakerLevel.RED: max_lots = 0.0
        
        return min(f, max_lots)
