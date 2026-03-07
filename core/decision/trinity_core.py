"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — TRINITY CORE                          ║
║           Núcleo de decisão: BUY / SELL / WAIT                              ║
║                                                                              ║
║  A decisão final emerge da convergência de todos os setores neurais.        ║
║  WAIT é o estado default — só entra quando TUDO converge.                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import time
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
    metadata: dict = None      # Metadados extras (Phase Ω-Extreme)


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
        self._creation_time = time.time()

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
        base_buy_threshold = OMEGA.get("buy_threshold")
        base_sell_threshold = OMEGA.get("sell_threshold")
        base_confidence_min = OMEGA.get("confidence_min")
        
        # Calibração Dinâmica de Limiares (Dynamic Threshold Calculus)
        # Em mercados com muito volume ou previsões altíssimas, a exigência do limiar se auto-calibra.
        dynamic_buy_thresh = base_buy_threshold
        dynamic_sell_thresh = base_sell_threshold
        dynamic_conf_min = base_confidence_min

        # 1. Ajuste pelo PnL Predictor
        pnl_pred = snapshot.metadata.get("pnl_prediction")
        if pnl_pred == "HIGH_PROBABILITY:POSITIVE_EXPECTANCY":
            # Facilita entradas promissoras
            dynamic_buy_thresh *= 0.6
            dynamic_sell_thresh *= 0.6
            dynamic_conf_min *= 0.8
        
        # 2. Ajuste por Regime
        if regime_state.current.value in ["TRENDING_BULL", "TRENDING_BEAR"]:
            # Tendências definidas precisam de menos confiança isolada, a maré já ajuda
            dynamic_conf_min *= 0.85
        elif regime_state.current.value in ["SQUEEZE_BUILDUP", "UNKNOWN", "LOW_LIQUIDITY"]:
            # Na compressão/baixa liquidez, sinais são menores por natureza, precisamos alargar a malha
            dynamic_buy_thresh *= 0.7
            dynamic_sell_thresh *= 0.7
            dynamic_conf_min *= 0.90
        elif regime_state.current.value in ["HIGH_VOL_CHAOS", "CHOPPY"]:
            # Em caos e chop, a exigência de sinal é muito mais estrita
            dynamic_buy_thresh *= 1.3
            dynamic_sell_thresh *= 1.3
            dynamic_conf_min = min(0.95, dynamic_conf_min * 1.1)

        # ═══ 3.5 DECOERÊNCIA SUPREMA (GOD-MODE REVERSAL) ═══
        # Se a entropia é máxima (todos os agentes discordam fortemente, pânico) e 
        # a volatilidade está explodindo, o ruído não é ruído: é uma "Liquidation Cascade"
        is_god_mode = False
        if quantum_state.entropy > 0.85 and regime_state.current.value in ["HIGH_VOL_CHAOS", "SQUEEZE_BUILDUP", "SQUEEZE"]:
            # Vamos absorver a liquidez com uma reversão tática.
            candles_m1 = snapshot.candles.get("M1")
            if candles_m1 and len(candles_m1.get("close", [])) >= 5:
                closes = np.array(candles_m1["close"], dtype=np.float64)
                delta_price = closes[-1] - closes[-5]
                atr_local = self._get_current_atr(snapshot)
                
                # Se o preço moveu mais que 2.5x o ATR local em 5 min e a entropia é máxima:
                if abs(delta_price) > atr_local * 2.5 and atr_local > 0:
                    log.omega(f"🌌 [GOD-MODE REVERSAL] Entropia Máxima ({quantum_state.entropy:.2f}) + Cascade. Absorvendo impacto topológico.")
                    action = Action.BUY if delta_price < 0 else Action.SELL
                    confidence = 0.99  # Certeza absoluta do rebote elástico
                    signal = 1.0 if action == Action.BUY else -1.0
                    is_god_mode = True

        # ═══ DECISÃO ═══
        if not is_god_mode:
            if signal >= dynamic_buy_thresh and confidence >= dynamic_conf_min:
                action = Action.BUY
            elif signal <= dynamic_sell_thresh and confidence >= dynamic_conf_min:
                action = Action.SELL
            else:
                reasons = []
                if abs(signal) < abs(dynamic_buy_thresh):
                    reasons.append(f"SIGNAL_WEAK({signal:+.3f} < req {abs(dynamic_buy_thresh):.3f})")
                if confidence < dynamic_conf_min:
                    reasons.append(f"LOW_CONFIDENCE({confidence:.2f} < req {dynamic_conf_min:.2f})")
                return self._wait(" | ".join(reasons))

        # ═══ PHASE Ω-EXTREME: CONSCIOUSNESS GATES (Φ) ═══
        phi_min = OMEGA.get("phi_min_threshold", 0.4)
        phi_hydra = OMEGA.get("phi_hydra_threshold", 4.5)

        # Calibração Dinâmica de Consciência (Dynamic Incoherence)
        # O valor de Φ natural varia com a energia do mercado. 
        # Exigir Φ=0.4 em mercados "Drifting" causa paralisia infinita.
        dynamic_phi_min = phi_min

        # 1. Ajuste por Regime
        if regime_state.current.value in ["DRIFTING_BEAR", "DRIFTING_BULL", "CHOPPY", "UNKNOWN", "LOW_LIQUIDITY"]:
            dynamic_phi_min *= 0.35  # Baixa volatilidade = menor necessidade de integração complexa
        elif regime_state.current.value in ["TRENDING_BULL", "TRENDING_BEAR"]:
            dynamic_phi_min *= 0.8   # Tendências claras são mais fáceis de ler

        # 2. Ajuste por Coerência do Enxame
        if quantum_state.coherence > 0.85:
            dynamic_phi_min *= 0.5   # Se há unanimidade entre agentes, toleramos menor Φ sistêmico

        # 3. Ajuste por Confiança Extrema
        if quantum_state.confidence > 0.90:
            dynamic_phi_min *= 0.7

        # 4. Ajuste por Previsão Java PnL Predictor
        pnl_pred = snapshot.metadata.get("pnl_prediction")
        if pnl_pred == "HIGH_PROBABILITY:POSITIVE_EXPECTANCY":
            dynamic_phi_min *= 0.5  # Expectância positiva atestada, facilita entrada

        dynamic_phi_min = max(0.05, min(phi_min, dynamic_phi_min))

        if quantum_state.phi < dynamic_phi_min:
            return self._wait(f"SYSTEM_INCOHERENCE (Φ={quantum_state.phi:.2f} < {dynamic_phi_min:.2f})")
            
        # ═══ VETO PREDITIVO (JAVA PNL PREDICTOR) ═══
        if pnl_pred == "IMPOSSIBLE:NEGATIVE_EXPECTANCY":
            if quantum_state.confidence < 0.95:  # Só ignora o veto se a certeza do enxame for quase absoluta
                return self._wait("JAVA_PNL_VETO (Negative Expectancy Detected)")

        is_hydra_mode = False
        if quantum_state.phi >= phi_hydra:
            log.omega(f"🔥 [HYDRA RESONANCE DETECTED] — Φ={quantum_state.phi:.2f}. Destravando agressão máxima.")
            is_hydra_mode = True

        # ═══ 4. PHASE 4: PREDATOR MODE OVERRIDE ═══
        # Se o agente ShadowPredator detectou manipulação institucional, entramos em modo de contra-ataque.
        shadow_signal = next((s for s in quantum_state.agent_signals if s.agent_name == "ShadowPredator"), None)
        if shadow_signal and shadow_signal.confidence > 0.85:
            log.omega("💀 [PREDATOR MODE ACTIVATED] — Detecção de manipulação institucional. Override direcional.")
            # No modo predador, seguimos estritamente o sinal do ShadowPredator ignorando o ruído
            action = Action.BUY if shadow_signal.signal > 0 else Action.SELL
            confidence = shadow_signal.confidence

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

        # ═══ ADAPTIVE SPREAD/FEE VALIDATION (Phase 28) ═══
        # A taxa real do trade (spread) não pode corroer o potencial de lucro nem dominar o ATR.
        sym_info = snapshot.symbol_info
        if sym_info:
            spread_points = sym_info.get("spread", 0)
            point_val = sym_info.get("point", 1.0)
            spread_cost_in_price = spread_points * point_val
            
            # Validação 1: Impacto no Reward Esperado
            if reward > 0:
                spread_impact = spread_cost_in_price / reward
                max_impact = OMEGA.get("max_spread_reward_impact", 0.25)
                
                if spread_impact > max_impact:
                    return self._wait(
                        f"SPREAD_TOO_EXPENSIVE_REWARD (Cost={spread_cost_in_price:.2f}, "
                        f"Reward={reward:.2f}, Impact={spread_impact:.1%}>{max_impact:.1%})"
                    )
                    
            # Validação 2: Impacto na Volatilidade/Liquidez (ATR)
            if atr > 0:
                spread_atr_impact = spread_cost_in_price / atr
                max_atr_impact = OMEGA.get("max_spread_atr_impact", 0.25)
                if spread_atr_impact > max_atr_impact:
                    return self._wait(
                        f"SPREAD_TOO_EXPENSIVE_ATR (Cost={spread_cost_in_price:.2f}, "
                        f"ATR={atr:.2f}, Impact={spread_atr_impact:.1%}>{max_atr_impact:.1%})"
                    )

        # ═══ KINEMATIC EXHAUSTION VETO (Phase 29 + 30) ═══
        # Proteção contra compra de topos (Liquidity Hunts) após esticada irracional
        candles_m1 = snapshot.candles.get("M1")
        if candles_m1 and len(candles_m1["close"]) >= 5:
            closures = np.array(candles_m1["close"], dtype=np.float64)
            last_close = closures[-1]
            
            kinematic_atr_mult = OMEGA.get("kinematic_exhaustion_atr_mult", 1.8)
            
            if action == Action.BUY:
                local_min = np.min(closures[-5:])
                distance = last_close - local_min
                if distance > atr * kinematic_atr_mult:  
                    return self._wait(f"KINEMATIC_EXHAUSTION_BUY (Spike={distance:.1f} > {kinematic_atr_mult}xATR={atr*kinematic_atr_mult:.1f}) | TOP_HUNT_RISK")
            elif action == Action.SELL:
                local_max = np.max(closures[-5:])
                distance = local_max - last_close
                if distance > atr * kinematic_atr_mult:
                    return self._wait(f"KINEMATIC_EXHAUSTION_SELL (Spike={distance:.1f} > {kinematic_atr_mult}xATR={atr*kinematic_atr_mult:.1f}) | BOTTOM_HUNT_RISK")

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
        lot_size = 0.01  # Placeholder
        if is_hydra_mode:
            # Sinalizamos para o risk_engine que estamos em Hydra
            lot_size = 0.02 # Apenas um sinal, risk_quantum aplicará mme

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
            metadata={}
        )
        
        if is_hydra_mode:
            decision.metadata["hydra_mode"] = True
        
        if is_hydra_mode:
            decision.metadata = decision.metadata if hasattr(decision, 'metadata') else {}
            decision.metadata["hydra_mode"] = True

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
        # 0. Startup Cooldown (Evita trades com sistema "frio")
        uptime = time.time() - self._creation_time
        startup_cooldown = OMEGA.get("startup_cooldown_seconds", 120)  # Default 2 minutos
        if uptime < startup_cooldown:
            return f"STARTUP_COOLDOWN({uptime:.0f}s/{startup_cooldown}s)"

        # 1. Spread excessivo absoluto
        if snapshot.tick:
            max_spread = OMEGA.get("max_spread_points", 5000)
            sym_info = snapshot.symbol_info
            if sym_info and sym_info.get("spread", 0) > max_spread:
                return f"SPREAD_HIGH_ABSOLUTE({sym_info['spread']}>{max_spread})"

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
