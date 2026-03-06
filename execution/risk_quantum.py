"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — RISK QUANTUM ENGINE                   ║
║         Gestão de risco quântica: Kelly, CVaR, circuit breakers            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import Optional
from datetime import datetime, timezone

from config.omega_params import OMEGA
from config.settings import (
    RISK_MAX_DAILY_LOSS_PCT, RISK_MAX_DRAWDOWN_PCT,
    RISK_CIRCUIT_BREAKER_PAUSE_MIN, RISK_MAX_CONSECUTIVE_LOSSES,
    RISK_MAX_POSITION_PCT, ASIState
)
from config.exchange_config import MIN_LOT_SIZE, MAX_LOT_SIZE, LOT_STEP
from utils.math_tools import MathEngine
from utils.logger import log
from utils.decorators import catch_and_log
from cpp.asi_bridge import CPP_CORE


class RiskQuantumEngine:
    """
    Motor de risco quântico — protege o capital com precisão cirúrgica.

    NÃO usa stop loss fixo estúpido.
    Usa: Kelly Criterion + ATR dinâmico + drawdown monitors + circuit breakers.
    """

    def __init__(self):
        self.math = MathEngine()
        self._daily_pnl = 0.0
        self._daily_start_balance = 0.0
        self._daily_trades = 0
        self._circuit_breaker_until = None

    @catch_and_log(default_return=0.01)
    def calculate_lot_size(self, balance: float, stop_loss_distance: float,
                           win_rate: float, avg_win: float, avg_loss: float,
                           symbol_info: dict = None, confidence: float = 0.5,
                           asi_state: ASIState = None) -> float:
        """
        Calcula lot size ótimo usando Kelly Criterion modificado via C++.
        """
        if balance <= 0 or stop_loss_distance <= 0:
            return MIN_LOT_SIZE

        # Kelly Criterion (via C++)
        kelly = CPP_CORE.kelly_criterion(
            win_rate=max(0.3, min(0.9, win_rate)),
            avg_win=max(1.0, avg_win),
            avg_loss=max(1.0, avg_loss)
        )

        # Fração do Kelly (quarter-Kelly para segurança)
        kelly_fraction = OMEGA.get("kelly_fraction")
        safe_kelly = kelly * kelly_fraction

        # ═══ [OMEGA INJECTION] CONVICTION SIZING (Phase 22) ═══
        if confidence >= 0.80:
            mult = OMEGA.get("high_conviction_multiplier", 2.0)
            safe_kelly *= mult
            log.omega(f"🔥 HIGH CONVICTION DETECTED (Conf={confidence:.2f}). Sizing Multiplier = {mult}x")

        # Risco máximo por posição
        max_risk_pct = OMEGA.get("position_size_pct")
        if confidence >= 0.70:
            # PHASE 35.1: Em alta convicção, dobramos o teto (ex: 12% * 2.0 = 24%)
            max_risk_pct *= 2.0

        risk_fraction = min(safe_kelly, max_risk_pct / 100.0)
        
        # ═══ [OMEGA INJECTION] TOTAL WAR: TIERED AGGRESSION FLOOR (Phase 38) ═══
        if balance >= 5000.0:
            # PHASE 39: Capital Preservation Guard (Lock 70% of Peak)
            if asi_state and balance < asi_state.peak_balance * 0.70:
                risk_fraction *= 0.25 # Corta risco em 75%
                confidence *= 0.50    # Reduz percepção de convicção
                log.warning(f"⚠️ CAPITAL PRESERVATION ACTIVE: Balanço (${balance:.2f}) abaixo do reservado (${asi_state.peak_balance*0.7:.2f}). Reduzindo agressividade.")
            
            elif confidence >= 0.85:
                # ALL-IN TÁTICO: Forçar 95% da margem livre (via MME no executor)
                risk_fraction = max(risk_fraction, 0.95)
                log.omega(f"🔱 ALL-IN TÁTICO: Confidence {confidence:.2f} >= 0.85 | Forçando Risk = 95%")
            elif confidence >= 0.75:
                # AGRESSÃO EXTREMA: Mínimo 50% de risco
                risk_fraction = max(risk_fraction, 0.50)
                log.omega(f"⚔️ AGRESSÃO EXTREMA: Confidence {confidence:.2f} >= 0.75 | Forçando Risk = 50%")
            elif confidence >= 0.65:
                # BATTERING RAM: Mínimo 30% de risco
                risk_fraction = max(risk_fraction, 0.30)
                log.omega(f"🔥 BATTERING RAM: Confidence {confidence:.2f} >= 0.65 | Forçando Risk = 30%")

        risk_fraction = max(0.001, risk_fraction)  # Mínimo 0.1%

        # Calcular lot size final usando C++ Core
        point_value = 1.0  # Default para BTC
        if symbol_info:
            contract_size = symbol_info.get("trade_contract_size", 1)
            point = symbol_info.get("point", 0.01)
            if point > 0:
                point_value = contract_size * point

        lot_size = CPP_CORE.optimal_lot_size(
            balance=balance,
            risk_pct=risk_fraction,
            sl_distance=stop_loss_distance,
            point_value=point_value
        )

        # Arredondar para step e clamp (segurança extra local)
        lot_size = round(lot_size / LOT_STEP) * LOT_STEP
        lot_size = max(MIN_LOT_SIZE, min(MAX_LOT_SIZE, lot_size))

        return lot_size

    def check_daily_limits(self, balance: float) -> bool:
        """Verifica se os limites diários foram atingidos."""
        if self._daily_start_balance == 0:
            self._daily_start_balance = balance

        daily_loss_pct = (
            (self._daily_start_balance - balance) / self._daily_start_balance * 100
            if self._daily_start_balance > 0 else 0
        )

        if daily_loss_pct >= RISK_MAX_DAILY_LOSS_PCT:
            log.omega(f"🔴 DAILY LOSS LIMIT HIT: {daily_loss_pct:.2f}% >= {RISK_MAX_DAILY_LOSS_PCT}%")
            return False

        return True

    def check_circuit_breaker(self, asi_state) -> bool:
        """Verifica se o circuit breaker deve ativar."""
        # Verificar timeout do circuit breaker
        if self._circuit_breaker_until:
            if datetime.now(timezone.utc) < self._circuit_breaker_until:
                return False  # Ainda em pausa
            else:
                self._circuit_breaker_until = None
                asi_state.circuit_breaker_active = False
                log.omega("🟢 Circuit breaker DESATIVADO — resumindo operações")

        # Ativar se losses consecutivos
        if asi_state.consecutive_losses >= RISK_MAX_CONSECUTIVE_LOSSES:
            from datetime import timedelta
            self._circuit_breaker_until = (
                datetime.now(timezone.utc) +
                timedelta(minutes=RISK_CIRCUIT_BREAKER_PAUSE_MIN)
            )
            asi_state.circuit_breaker_active = True
            log.omega(
                f"🔴 CIRCUIT BREAKER ATIVADO! "
                f"{asi_state.consecutive_losses} losses consecutivos. "
                f"Pausa de {RISK_CIRCUIT_BREAKER_PAUSE_MIN} minutos."
            )
            return False

        return True

    def check_drawdown(self, balance: float, peak_balance: float) -> bool:
        """Verifica drawdown máximo."""
        if peak_balance <= 0:
            return True

        drawdown_pct = (peak_balance - balance) / peak_balance * 100

        if drawdown_pct >= RISK_MAX_DRAWDOWN_PCT:
            log.omega(
                f"🔴 MAX DRAWDOWN HIT: {drawdown_pct:.2f}% >= {RISK_MAX_DRAWDOWN_PCT}%"
            )
            return False

        return True

    def validate_trade(self, balance: float, asi_state,
                       lot_size: float) -> tuple:
        """
        Validação completa de risco antes de executar trade.
        Returns: (approved: bool, final_lot_size: float, reason: str)
        """
        # 1. Circuit breaker
        if not self.check_circuit_breaker(asi_state):
            return False, 0.0, "CIRCUIT_BREAKER"

        # 2. Daily limits
        if not self.check_daily_limits(balance):
            return False, 0.0, "DAILY_LOSS_LIMIT"

        # 3. Drawdown
        if not self.check_drawdown(balance, asi_state.peak_balance):
            return False, 0.0, "MAX_DRAWDOWN"

        # 4. Lot size sanity
        final_lot = max(MIN_LOT_SIZE, min(MAX_LOT_SIZE, lot_size))

        return True, final_lot, "APPROVED"

    def record_trade_result(self, profit: float, asi_state):
        """Registra resultado do trade para atualização de risco."""
        self._daily_pnl += profit
        self._daily_trades += 1
        asi_state.total_profit += profit

        if profit > 0:
            asi_state.total_wins += 1
            asi_state.consecutive_losses = 0
        else:
            asi_state.total_losses += 1
            asi_state.consecutive_losses += 1

        asi_state.total_trades += 1

    def reset_daily(self, balance: float):
        """Reset diário dos contadores."""
        self._daily_pnl = 0.0
        self._daily_start_balance = balance
        self._daily_trades = 0
        log.info(f"📊 Risk daily reset. Balance: ${balance:.2f}")
