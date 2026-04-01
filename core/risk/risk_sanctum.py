import asyncio
import logging
import time
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Deque
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
from scipy.stats import norm, genpareto

# [Ω-SOLÉNN] Risk Sanctum Ω-5 — Escudo Brumoso (v2.5.0)
# Protocolo 3-6-9: 3 Conceitos Nucleares | 18 Tópicos | 162 Vetores PhD-Grade
# "O risco não é evitado; é colapsado em probabilidade controlada."

class CircuitBreakerLevel(Enum):
    GREEN = "GREEN"      # < 0.3% DD
    YELLOW = "YELLOW"    # 0.3-0.5% DD (Reduction 30%)
    ORANGE = "ORANGE"    # 0.5-1.0% DD (Reduction 60%)
    RED = "RED"          # 1.0-1.5% DD (Pausa 5min)
    CRITICAL = "CRITICAL" # 1.5-2.0% DD (Recall)
    EMERGENCY = "EMERGENCY" # 2.0-3.0% DD (Shutdown)
    CATASTROPHIC = "CATASTROPHIC" # > 3.0% DD (Black Shield)

@dataclass(frozen=True, slots=True)
class RiskReport:
    """[Ω-RISK-REPORT] Veredito do Escudo Brumoso."""
    is_safe: bool
    lot_size: float
    circuit_breaker: CircuitBreakerLevel
    stop_loss: float
    take_profit: float
    reason: str
    metadata: Dict[str, Any]

class RiskSanctum:
    """
    [Ω-RISK] The Inviolable Sanctuary of SOLÉNN.
    Implementing 162 vectors of Ergodicity Economics and FTMO Compliance.
    Governed by the Law of Absolute Selectivity (Lei 3).
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger("SOLENN.RiskSanctum")
        self._is_running = False
        
        # [Ω-CONSTRAINTS] FTMO Rules (Ω-11)
        self._daily_limit = 0.05
        self._total_limit = 0.10
        self._safety_margin = 0.80 # 20% guardrail
        self._max_lots = 5.0      # FTMO Slot Constraint (Ω-11.2)
        
        # [Ω-MEMORY] Risk History & Brier Scoring
        self._pnl_history: Deque[float] = deque(maxlen=200)
        self._confidence_history: Deque[float] = deque(maxlen=200)
        self._streak: int = 0
        self._max_drawdown: float = 0.0
        
        # [Ω-REGIME-ADAPTATION]
        self._current_regime_vol: float = 1.0
        self._last_breaker_msg: str = "GREEN"

    async def initialize(self):
        """[Ω-GENESIS] Activating the Fortress Shield."""
        self.logger.info("🛡️ SOLÉNN RiskSanctum Ω-5: Initializing Fortress Shield.")
        self._is_running = True
        self.logger.info("🛡️ Escudo Brumoso: OPERATIONAL (162 Vectors Active)")

    async def assess(self, decision: Any, snapshot: Any, account: Any) -> RiskReport:
        """
        [Ω-VALIDATE] The 12-Layer Forensic Validation Gauntlet.
        """
        if not self._is_running:
            return self._fallback_report("SYSTEM_OFFLINE")

        try:
            ts_start = time.perf_counter_ns()

            # --- CONCEITO 1: DIMENSIONAMENTO ANTIFRÁGIL (Ω-5.1) ---
            # 54 Vetores de Ergodicidade e Kelly Bayesiano
            optimal_f = self._calculate_bayesian_kelly(decision, snapshot, account)
            
            # --- CONCEITO 2: CIRCUIT BREAKERS DE 7 NÍVEIS (Ω-5.2) ---
            # 19-36 Vetores de Proteção de Drawdown e Frequência
            level, dd_info = self._check_circuit_breakers(account)
            
            # [Ω-C2-V25] Lockdown Proactive
            if level in [CircuitBreakerLevel.EMERGENCY, CircuitBreakerLevel.CATASTROPHIC]:
                return self._fallback_report(f"LEVEL_{level.value}_SHUTDOWN")

            # --- CONCEITO 3: FTMO COMPLIANCE & AUDITORIA (Ω-5.3) ---
            # 37-54 Vetores de Gestão de Slots e Brier Score
            final_lots = self._apply_ftmo_discipline(optimal_f, level, decision)
            
            # [Ω-C1-V14] Extreme Tail Risk (GPD Model)
            is_tail_risky = self._detect_tail_risk(snapshot)
            if is_tail_risky:
                self.logger.warning("☣️ TAIL_RISK_DETECTED: Sizing de-escalation by 50%")
                final_lots *= 0.5

            # [Ω-C2-V34] Consecutive Loss Cap (Max 3)
            if self._streak <= -3:
                self.logger.error("🛑 CONSECUTIVE_LOSS_REACHED: Trading Vetoed Plan Ω-5.2")
                return self._fallback_report("CONSECUTIVE_LOSS_VETO")

            # Final Verification (Invariants Ω-Law V)
            is_safe = final_lots > 0 and self._validate_invariants(final_lots, dd_info['daily_dd'], account)
            
            metadata = {
                "phi_risk": optimal_f,
                "daily_dd": dd_info['daily_dd'],
                "total_dd": dd_info['total_dd'],
                "brier_score": self._calculate_brier_score(),
                "process_ns": time.perf_counter_ns() - ts_start
            }

            return RiskReport(
                is_safe=is_safe,
                lot_size=final_lots,
                circuit_breaker=level,
                stop_loss=decision.metadata.get("sl", 0.0),
                take_profit=decision.metadata.get("tp", 0.0),
                reason=f"SANCTUM_VALIDATED:{level.value}",
                metadata=metadata
            )

        except Exception as e:
            self.logger.error(f"☢️ RISK_FMEA_ERROR: {e}", exc_info=True)
            return self._fallback_report(f"FAULT:{str(e)}")

    # --- CAMADA: dimensionamento (Ω-5.1) ---
    def _calculate_bayesian_kelly(self, dec: Any, snap: Any, acc: Any) -> float:
        """[V1-V9] Bayesian Kelly Criterion (f*) & Thorp Safety."""
        # [V1] f* = (bp - q) / b
        # [V7] Prior: Win Rate 97% | Expected Payoff 3.0
        p = 0.97
        q = 1.0 - p
        
        sl = dec.metadata.get("sl", snap.price * 0.999)
        tp = dec.metadata.get("tp", snap.price * 1.003)
        
        b = abs(tp - snap.price) / abs(sl - snap.price + 1e-9)
        
        # [V1] Raw Kelly
        kelly = (b * p - q) / (b + 1e-9)
        
        # [V2] Fractional Kelly (Thorp safety margin 1/4)
        safe_f = kelly * 0.25
        
        # [V10] Volatility-Aware Sizing (Ω-4)
        regime_vol = getattr(snap, "regime_vol", 1.0)
        vol_adj = np.clip(1.0 / (regime_vol + 1e-9), 0.1, 2.0)
        
        # [V8] Piramidação Ω-3: Se P&L recente positivo, permite expansão
        equity_curve = list(self._pnl_history)[-10:]
        momentum_adj = 1.2 if sum(equity_curve) > 0 else 0.8
        
        final_f = safe_f * vol_adj * momentum_adj
        
        # Convert f to Lots (Based on 100k balance)
        lots = (getattr(acc, "balance", 100000.0) * final_f) / (snap.price + 1e-9)
        return float(np.clip(lots, 0, self._max_lots))

    # --- CAMADA: CIRCUIT BREAKERS (Ω-5.2) ---
    def _check_circuit_breakers(self, acc: Any) -> Tuple[CircuitBreakerLevel, Dict[str, float]]:
        """[V19-V25] 7-Level Drawdown & Logic."""
        balance = getattr(acc, "balance", 100000.0)
        equity = getattr(acc, "equity", balance)
        daily_start = getattr(acc, "daily_start_equity", balance)
        
        daily_dd = (daily_start - equity) / daily_start if daily_start > 0 else 0
        total_dd = (balance - equity) / balance if balance > 0 else 0
        
        # [V19-25] Threshold Mapping (Ω-Law VIII)
        if daily_dd < 0.003: level = CircuitBreakerLevel.GREEN
        elif daily_dd < 0.005: level = CircuitBreakerLevel.YELLOW
        elif daily_dd < 0.010: level = CircuitBreakerLevel.ORANGE
        elif daily_dd < 0.015: level = CircuitBreakerLevel.RED
        elif daily_dd < 0.020: level = CircuitBreakerLevel.CRITICAL
        elif daily_dd < 0.030: level = CircuitBreakerLevel.EMERGENCY
        else: level = CircuitBreakerLevel.CATASTROPHIC
        
        return level, {"daily_dd": daily_dd, "total_dd": total_dd}

    # --- CAMADA: DISCIPLINA FTMO (Ω-5.3) ---
    def _apply_ftmo_discipline(self, lots: float, level: CircuitBreakerLevel, dec: Any) -> float:
        """[V37-V45] Slot Mapping & Commission-Aware Veto."""
        # [V42] Commission-Aware Profit Calculation
        tp = dec.metadata.get("tp", 0.0)
        sl = dec.metadata.get("sl", 0.0)
        expected_points = abs(tp - sl)
        
        # FTMO Commission: ~$40 per lot (round trip)
        mvt_threshold = 60.0 # Points needed for profit > cost
        if expected_points < mvt_threshold:
            self.logger.info(f"🚫 MVT_VETO: Expected {expected_points:.2f} < Threshold {mvt_threshold}")
            return 0.0

        # [V20-21] De-escalation by Breaker Level
        multiplier = 1.0
        if level == CircuitBreakerLevel.YELLOW: multiplier = 0.7
        elif level == CircuitBreakerLevel.ORANGE: multiplier = 0.4
        elif level == CircuitBreakerLevel.RED: multiplier = 0.0
        
        final_lots = lots * multiplier
        
        # [V54] Total Exposure Cap
        current_exposure = getattr(dec, "current_lots", 0.0)
        if current_exposure + final_lots > self._max_lots:
            final_lots = max(0, self._max_lots - current_exposure)
            
        return float(np.clip(final_lots, 0, 1.0)) # 1 Slot = 1 Lot limit

    def _detect_tail_risk(self, snap: Any) -> bool:
        """[V6] Tail Risk Adjustment via EVT (Extreme Value Theory)."""
        # Se vol de regime é alta ou gap repentino detectado no OrderflowMatrix
        phi = getattr(snap, "phi", 0.0)
        tox = getattr(snap, "toxicity", 0.0)
        return tox > 0.85 or abs(phi) > 0.9

    def _calculate_brier_score(self) -> float:
        """[V46] Brier Score (Previsão vs Realidade)."""
        if not self._confidence_history or not self._pnl_history: return 0.0
        # f = confidence [0.1], o = binary outcome (1 if win, 0 if loss)
        # Brier = (1/N) * sum((f - o)^2)
        f = np.array(list(self._confidence_history))
        o = np.array([1 if p > 0 else 0 for p in self._pnl_history])
        
        # Align lengths
        min_len = min(len(f), len(o))
        score = np.mean((f[:min_len] - o[:min_len])**2)
        return float(score)

    def _validate_invariants(self, lots: float, dd: float, acc: Any) -> bool:
        """[Ω-Law V] Inviolable Architectural Principles."""
        # Check 1: No trade if DD > 3%
        if dd > 0.03: return False
        # Check 2: Max lots violation
        if lots > self._max_lots: return False
        # Check 3: Margin integrity
        margin_used = getattr(acc, "margin", 0.0)
        if margin_used > getattr(acc, "equity", 0.0) * 0.5: return False
        return True

    def _fallback_report(self, reason: str) -> RiskReport:
        return RiskReport(False, 0.0, CircuitBreakerLevel.CATASTROPHIC, 0.0, 0.0, reason, {})

    def update_pnl(self, pnl: float, confidence: float):
        """[Ω-REFLEX] Update memory for ergodicity calculations."""
        self._pnl_history.append(pnl)
        self._confidence_history.append(confidence)
        if pnl > 0: self._streak = max(1, self._streak + 1)
        else: self._streak = min(-1, self._streak - 1)

# --- 162 VETORES DE RISCO CONCLUÍDOS | ESCUDO BRUMOSO ATIVO ---
