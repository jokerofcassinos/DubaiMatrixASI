"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — TRINITY CORE                          ║
║           Núcleo de decisão: BUY / SELL / WAIT                              ║
║                                                                              ║
║  A decisão final emerge da convergência de todos os setores neurais.        ║
║  WAIT é o estado default — só entra quando TUDO converge.                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional
from enum import Enum

from core.consciousness.quantum_thought import QuantumState
from core.consciousness.regime_detector import RegimeState, MarketRegime
from core.consciousness.monte_carlo_engine import QuantumMonteCarloEngine
from config.omega_params import OMEGA
from config.settings import (
    EXECUTION_MAX_SPREAD_POINTS, RISK_MAX_CONSECUTIVE_LOSSES
)
from utils.logger import log
from utils.decorators import catch_and_log
from utils.time_tools import TimeEngine


class Action(Enum):
    BUY = "BUY"
    SELL = "SELL"
    WAIT = "WAIT"


@dataclass
class Decision:
    """Decisão final da ASI — payload para o executor."""
    action: Action
    confidence: float          # [0, 1]
    signal_strength: float     # [-1, +1]
    entry_price: float         # Preço de entrada sugerido
    stop_loss: float           # SL em preço
    take_profit: float         # TP em preço
    lot_size: float            # Tamanho do lote
    regime: str                # Regime de mercado
    reasoning: str             # Explicação completa
    veto_reason: str = ""      # Se vetado, razão
    risk_reward_ratio: float = 0.0


class TrinityCore:
    """
    Trinity Core — o cérebro decisório final da ASI.

    Recebe:
    - QuantumState (sinal convergente dos agentes)
    - RegimeState (contexto do regime de mercado)
    - Dados de risco e condições de trading

    Produz:
    - Decision (BUY, SELL ou WAIT)

    PRINCÍPIO: WAIT é o estado natural.
    A ASI só entra quando a probabilidade é avassaladora.
    """

    def __init__(self):
        self._decision_history = []
        self._veto_count = 0
        self._execute_count = 0
        self.monte_carlo = QuantumMonteCarloEngine()

    @catch_and_log(default_return=None)
    def decide(self, quantum_state: QuantumState,
               regime_state: RegimeState,
               snapshot,
               asi_state) -> Optional[Decision]:
        """
        Toma a decisão final: BUY, SELL ou WAIT.
        """
        if quantum_state is None or regime_state is None:
            return self._wait("NO_DATA")

        # ═══ VETO CHECKS (condições de perigo) ═══
        veto = self._check_vetos(snapshot, asi_state, regime_state)
        if veto:
            self._veto_count += 1
            return self._wait(f"VETO: {veto}")

        # ═══ QUANTUM STATE CHECK ═══
        if quantum_state.superposition:
            return self._wait("SUPERPOSITION (agentes não convergiram)")

        signal = quantum_state.collapsed_signal
        confidence = quantum_state.confidence
        coherence = quantum_state.coherence

        # ═══ THRESHOLDS ═══
        buy_threshold = OMEGA.get("buy_threshold")
        sell_threshold = OMEGA.get("sell_threshold")
        confidence_min = OMEGA.get("confidence_min")

        # ═══ DECISÃO ═══
        if signal >= buy_threshold and confidence >= confidence_min:
            action = Action.BUY
        elif signal <= sell_threshold and confidence >= confidence_min:
            action = Action.SELL
        else:
            reasons = []
            if abs(signal) < abs(buy_threshold):
                reasons.append(f"SIGNAL_WEAK({signal:+.3f})")
            if confidence < confidence_min:
                reasons.append(f"LOW_CONFIDENCE({confidence:.2f})")
            return self._wait(" | ".join(reasons))

        # ═══ CALCULAR SL/TP ═══
        tick = snapshot.tick
        if tick is None:
            return self._wait("NO_TICK_DATA")

        price = tick["ask"] if action == Action.BUY else tick["bid"]
        atr = self._get_current_atr(snapshot)

        if atr <= 0:
            return self._wait("ATR_ZERO")

        sl_mult = OMEGA.get("stop_loss_atr_mult")
        tp_mult = OMEGA.get("take_profit_atr_mult")

        if action == Action.BUY:
            stop_loss = price - atr * sl_mult
            take_profit = price + atr * tp_mult
        else:
            stop_loss = price + atr * sl_mult
            take_profit = price - atr * tp_mult

        # ═══ RISK/REWARD CHECK ═══
        risk = abs(price - stop_loss)
        reward = abs(take_profit - price)
        rr_ratio = reward / risk if risk > 0 else 0

        min_rr = OMEGA.get("trinity_min_rr_ratio", 1.5)
        if rr_ratio < min_rr:
            return self._wait(f"RR_RATIO_LOW({rr_ratio:.2f} < {min_rr})")

        # ═══ ADAPTIVE SPREAD/FEE VALIDATION (Phase 20) ═══
        # A taxa real do trade (spread) não pode corroer o potencial de lucro.
        sym_info = snapshot.symbol_info
        if sym_info:
            spread_points = sym_info.get("spread", 0)
            point_val = sym_info.get("point", 1.0)
            spread_cost_in_price = spread_points * point_val
            
            if reward > 0:
                spread_impact = spread_cost_in_price / reward
                max_impact = OMEGA.get("max_spread_reward_impact", 0.25)
                
                if spread_impact > max_impact:
                    return self._wait(
                        f"SPREAD_TOO_EXPENSIVE (Cost={spread_cost_in_price:.2f}, "
                        f"Reward={reward:.2f}, Impact={spread_impact:.1%}>{max_impact:.1%})"
                    )

        # ═══ MONTE CARLO VALIDATION ═══
        # Simula 5000 universos paralelos para validar o trade
        volatility_est = atr / max(price, 1) * np.sqrt(252)  # Anualizar
        mc_result = self.monte_carlo.simulate_trade(
            current_price=price,
            direction=action.value,
            stop_loss=stop_loss,
            take_profit=take_profit,
            volatility=max(volatility_est, 0.01),
            regime=regime_state.current.value,
            n_simulations=5000,
            n_steps=100,
        )

        mc_score = 0.0
        mc_win_prob = 0.5
        mc_ev = 0.0
        mc_cvar = 0.0
        mc_reasoning = ""

        if mc_result:
            mc_score = mc_result.monte_carlo_score
            mc_win_prob = mc_result.win_probability
            mc_ev = mc_result.expected_return
            mc_cvar = mc_result.conditional_var_95

            # Use optimal SL/TP from Monte Carlo if available
            if mc_result.optimal_sl_distance > 0 and mc_result.optimal_tp_distance > 0:
                opt_rr = mc_result.optimal_rr_ratio
                if opt_rr > rr_ratio * 1.1:  # MC found better RR
                    if action == Action.BUY:
                        stop_loss = price - mc_result.optimal_sl_distance
                        take_profit = price + mc_result.optimal_tp_distance
                    else:
                        stop_loss = price + mc_result.optimal_sl_distance
                        take_profit = price - mc_result.optimal_tp_distance
                    risk = abs(price - stop_loss)
                    reward = abs(take_profit - price)
                    rr_ratio = reward / risk if risk > 0 else 0

            mc_reasoning = (
                f"MC[score={mc_score:+.3f} WP={mc_win_prob:.1%} "
                f"EV={mc_ev:+.2f} CVaR={mc_cvar:+.2f} "
                f"sim={mc_result.simulation_time_ms:.1f}ms]"
            )

            # VETO se Monte Carlo score é muito negativo
            mc_min_score = OMEGA.get("mc_min_score", -0.1)
            if mc_score < mc_min_score:
                return self._wait(f"MC_SCORE_LOW({mc_score:+.3f}<{mc_min_score}) {mc_reasoning}")

            # VETO se win probability é muito baixa
            mc_min_wp = OMEGA.get("mc_min_win_prob", 0.45)
            if mc_win_prob < mc_min_wp:
                return self._wait(f"MC_WIN_PROB_LOW({mc_win_prob:.1%}<{mc_min_wp:.0%}) {mc_reasoning}")

        # ═══ LOT SIZE (será refinado pelo Risk Quantum Engine) ═══
        lot_size = 0.01  # Placeholder — risk_quantum calcula o real

        # ═══ CONSTRUIR DECISÃO ═══
        reasoning = (
            f"{action.value} signal={signal:+.3f} conf={confidence:.2f} "
            f"coherence={coherence:.2f} regime={regime_state.current.value} "
            f"ATR={atr:.2f} RR={rr_ratio:.2f} | "
            f"Quantum: {quantum_state.reasoning} | "
            f"{mc_reasoning}"
        )

        decision = Decision(
            action=action,
            confidence=confidence,
            signal_strength=signal,
            entry_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            lot_size=lot_size,
            regime=regime_state.current.value,
            reasoning=reasoning,
            risk_reward_ratio=rr_ratio,
        )

        self._execute_count += 1
        self._decision_history.append({
            "action": action.value,
            "signal": signal,
            "confidence": confidence,
            "mc_score": mc_score,
            "mc_win_prob": mc_win_prob,
        })

        log.signal(f"🎯 DECISION: {action.value} | {reasoning}")
        return decision

    def _check_vetos(self, snapshot, asi_state, regime_state) -> Optional[str]:
        """
        Sistema de veto — rejeita trades em condições de perigo.
        NÃO é paralisante: veta apenas em casos claros.
        """
        # 1. Spread excessivo
        if snapshot.tick:
            max_spread = OMEGA.get("max_spread_points")
            sym_info = snapshot.symbol_info
            if sym_info and sym_info.get("spread", 0) > max_spread:
                return f"SPREAD_HIGH({sym_info['spread']}>{max_spread})"

        # 2. Circuit breaker ativo
        if asi_state and asi_state.circuit_breaker_active:
            return "CIRCUIT_BREAKER_ACTIVE"

        # 3. Losses consecutivos
        if asi_state and asi_state.consecutive_losses >= RISK_MAX_CONSECUTIVE_LOSSES:
            return f"CONSECUTIVE_LOSSES({asi_state.consecutive_losses})"

        # 4. Regime de caos extremo
        if regime_state.current == MarketRegime.HIGH_VOL_CHAOS:
            if regime_state.confidence > 0.8:
                return "HIGH_VOL_CHAOS (confidence alta)"

        # 5. Sessão desfavorável (weekend com baixa liquidez)
        session = TimeEngine.session_info()
        if session.get("is_weekend") and session.get("trading_favorability", 0) < 0.3:
            return "WEEKEND_LOW_LIQUIDITY"

        return None  # Sem veto

    def _get_current_atr(self, snapshot) -> float:
        """Obtém ATR atual do snapshot."""
        atr = snapshot.indicators.get("M5_atr_14")
        if atr is not None and len(atr) > 0:
            return float(atr[-1])
        return 0.0

    def _wait(self, reason: str) -> Decision:
        """Retorna decisão WAIT."""
        return Decision(
            action=Action.WAIT,
            confidence=0.0,
            signal_strength=0.0,
            entry_price=0.0,
            stop_loss=0.0,
            take_profit=0.0,
            lot_size=0.0,
            regime="",
            reasoning=f"WAIT: {reason}",
        )

    @property
    def stats(self) -> dict:
        return {
            "total_decisions": len(self._decision_history),
            "executions": self._execute_count,
            "vetos": self._veto_count,
            "veto_rate": self._veto_count / max(1, len(self._decision_history)),
        }
