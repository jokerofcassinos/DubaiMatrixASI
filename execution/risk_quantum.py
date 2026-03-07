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
                           asi_state: ASIState = None, snapshot = None) -> float:
        """
        Calcula lot size ótimo usando Kelly Criterion modificado via C++.
        Transição OMEGA-CLASS: Otimização da Taxa de Crescimento Temporal (Non-Ergodic Growth).
        """
        if balance <= 0 or stop_loss_distance <= 0:
            return MIN_LOT_SIZE

        # 1. Obter métricas de performance base (Normalization)
        wr = max(0.3, min(0.9, win_rate))
        aw = max(1.0, avg_win)
        al = max(1.0, avg_loss)
        rr = aw / al

        # 2. ═══ [OMEGA-CLASS] NON-ERGODIC GROWTH OPTIMIZATION ═══
        # Em vez de Kelly estático, buscamos a alavancagem que maximiza g(f).
        # Simulamos 5 níveis de leverage para encontrar o pico da curva de crescimento.
        best_leverage = 0.0
        max_growth = -999.0
        
        # r_win_pct e r_loss_pct em termos de variação do preço
        price = snapshot.price if snapshot else 1.0
        avg_win_price_pct = aw / price if price > 0 else 0.01
        avg_loss_price_pct = al / price if price > 0 else 0.01

        for leverage in [0.5, 1.0, 2.0, 5.0, 10.0]:
            growth = CPP_CORE.non_ergodic_growth_rate(wr, avg_win_price_pct, avg_loss_price_pct, leverage)
            if growth > max_growth:
                max_growth = growth
                best_leverage = leverage

        # Se o crescimento máximo for negativo (Ruína Probabilística), reduzimos drasticamente.
        if max_growth < 0:
            log.warning(f"⚠️ NON-ERGODIC RUIN DETECTED: Growth Rate {max_growth:.6f} for best leverage {best_leverage}. Reducing exposure.")
            risk_fraction = 0.001 
        else:
            # f* ótimo baseado em crescimento temporal
            # Mapeamos a leverage ótima para uma fração de risco do balanço
            # Sizing = (Best Leverage * Distância do SL em %)
            sl_pct = stop_loss_distance / price if price > 0 else 0.01
            risk_fraction = best_leverage * sl_pct
            log.omega(f"📊 NON-ERGODIC OPTIMIZATION: Max Growth {max_growth:.6f} @ {best_leverage}x Leverage. Risk Fraction: {risk_fraction:.4f}")

        # 3. ═══ [OMEGA-CLASS] ITO CALCULUS REFINEMENT (Volatility Tax) ═══
        # Se tivermos volatilidade (ATR), ajustamos pela taxa de "imposto" estocástico.
        atr_m1 = snapshot.indicators.get("M1_atr_14") if hasattr(snapshot, 'indicators') else None
        if atr_m1 is not None and len(atr_m1) > 0:
            sigma_pct = (np.mean(atr_m1[-14:]) * np.sqrt(1440)) / price # Vol diaria estimada
            mu_pct = (wr * avg_win_price_pct - (1-wr) * avg_loss_price_pct)
            
            ito_sizing = CPP_CORE.ito_lot_sizing(balance, wr, mu_pct, sigma_pct, 1.0/1440.0)
            ito_fraction = ito_sizing / balance if balance > 0 else 0.01
            
            # Conservadorismo Quântico: Mínimo entre o crescimento não-ergódico e o limite de Ito
            risk_fraction = min(risk_fraction, ito_fraction)
            log.omega(f"📉 ITO REFINEMENT: Vol Taxed Risk Ceiling = {ito_fraction:.4f}")

        # 4. Conviction Sizing (Phase 22)
        kelly_fraction = OMEGA.get("kelly_fraction", 0.25)
        risk_fraction *= (kelly_fraction * 4.0) # Normaliza pelo multiplicador de agressividade do CEO

        if confidence >= 0.80:
            mult = OMEGA.get("high_conviction_multiplier", 2.0)
            risk_fraction *= mult
            log.omega(f"🔥 HIGH CONVICTION: Multiplier {mult}x applied. Final Risk: {risk_fraction:.4f}")

        # 5. Tiers de Agressão floor (Phase 38) e Circuit Breakers
        max_risk_pct = OMEGA.get("position_size_pct", 10.0) / 100.0
        if confidence >= 0.70:
            max_risk_pct *= 2.0

        risk_fraction = min(risk_fraction, max_risk_pct)
        
        # [TOTAL WAR OVERRIDES]
        if balance >= 5000.0:
            if asi_state and balance < asi_state.peak_balance * 0.70:
                risk_fraction *= 0.25 
            elif confidence >= 0.85: risk_fraction = max(risk_fraction, 0.95)
            elif confidence >= 0.75: risk_fraction = max(risk_fraction, 0.50)
            elif confidence >= 0.65: risk_fraction = max(risk_fraction, 0.30)

        # 6. Converter para Lote
        point_value = 1.0
        if symbol_info:
            contract_size = symbol_info.get("trade_contract_size", 1)
            point = symbol_info.get("point", 0.01)
            if point > 0:
                point_value = contract_size * point

        lot_size = balance * risk_fraction / (stop_loss_distance * point_value) if stop_loss_distance > 0 else MIN_LOT_SIZE

        # Ceiling de Exposição (Phase 40)
        exposure_ratio = OMEGA.get("exposure_ceiling_balance_ratio", 2000.0)
        max_safe_lots = balance / max(500.0, exposure_ratio) 
        if lot_size > max_safe_lots:
            lot_size = max_safe_lots

        lot_size = round(lot_size / LOT_STEP) * LOT_STEP
        lot_size = max(MIN_LOT_SIZE, min(MAX_LOT_SIZE, lot_size))

        return lot_size

        # 3. PHASE 40: Hard Exposure Ceiling
        # $30k account -> Max 15.0 lots (Safety ratio: 2000 units of balance per lot)
        # Isso garante que mesmo em Total War, não batemos 100 lotes que liquidam com 0.4% de variação.
        exposure_ratio = OMEGA.get("exposure_ceiling_balance_ratio", 2000.0)
        max_safe_lots = balance / max(500.0, exposure_ratio) 
        if lot_size > max_safe_lots:
            log.omega(f"🛡️ EXPOSURE CEILING: Lote {lot_size:.2f} excedeu teto de segurança {max_safe_lots:.2f}. Limitando.")
            lot_size = max_safe_lots

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
