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
from utils.decorators import timed, catch_and_log, ast_self_heal
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
        
        # [PHASE Ω-ANTI-FRAGILITY] Ping-Pong State
        self.last_decision = None
        self._log_cache = {}  # {key: timestamp}
        log.omega("🛡️ TrinityCore Integrated Information (Φ) GATE: ENABLED")
        
        # [PHASE Ω-RESILIENCE] Log Cooldowns (Avoid spam)
        self._last_phi_val = 0.0
        self._last_sl_mult = 0.0
        self._last_regime = ""
        self._last_loss_time = 0.0  # [PHASE Ω-ANTI-FRAGILITY] Initialization

    @ast_self_heal
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

        # [Phase 51] OMEGA-ALPHA: Ignition & God-Mode Status
        has_ignition = snapshot.metadata.get("v_pulse_detected", False) or regime_state.v_pulse_detected
        is_god_mode = snapshot.metadata.get("god_mode_active", False)
        is_phi_resonance = snapshot.metadata.get("phi_resonance", False)

        # [PHASE 50] Strike Flag
        strike_flag = ""

        # ═══ VETO CHECKS (condições de perigo) ═══
        v_pulse_detected = snapshot.metadata.get("v_pulse_detected", False)
        veto = self._check_vetos(snapshot, asi_state, regime_state, v_pulse_detected)
        if veto:
            self._veto_count += 1
            # [Phase 51] OMEGA EMERGENCY: Se houver posições mas houver VETO fatal, força fechamento
            if "SPREAD_ABUSE" in str(veto) or "CHAOS_SHIELD" in str(veto):
                 log.warning(f"🚨 VETO DETECTED ({veto}) -> TRIGGERING OMEGA CLOSE.")
            return self._wait(f"VETO: {veto}")
        
        # [Phase 51] PARADIGM SHIFT CLOSE (Omniscience Exit)
        # Se a geometria da informação (KL Divergence) mostrar que o movimento exauriu
        kl_div = snapshot.metadata.get("kl_divergence", 0.0)
        if kl_div > OMEGA.get("paradigm_shift_threshold", 0.85):
            log.omega(f"🔮 PARADIGM SHIFT DETECTED (KL={kl_div:.4f}). Exiting current positions preemptively.")
            return Decision(
                action=Action.WAIT, # No novo sinal, mas o PositionManager deve ler o sinal de CLOSE
                confidence=1.0,
                signal_strength=0.0,
                entry_price=snapshot.price,
                stop_loss=0,
                take_profit=0,
                lot_size=0,
                regime=regime_state.current.value,
                reasoning=f"PARADIGM SHIFT: KL Divergence {kl_div:.4f} > threshold. Kinetic exhaustion confirmed.",
                metadata={"emergency_close": True}
            )

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
        
        # 2. Ajuste por Regime e [Phase Ω-Singularity] MAKER_ADVANTAGE
        limit_mode = (regime_state.current.value in ["DRIFTING_BEAR", "DRIFTING_BULL", "LOW_LIQUIDITY", "SQUEEZE_BUILDUP"]) \
                     and OMEGA.get("limit_execution_mode", 0.0) > 0.5
        
        if regime_state.current.value in ["TRENDING_BULL", "TRENDING_BEAR"]:
            # Tendências definidas precisam de menos confiança isolada, a maré já ajuda
            dynamic_conf_min *= 0.85
        elif regime_state.current.value in ["SQUEEZE_BUILDUP", "UNKNOWN", "LOW_LIQUIDITY", "DRIFTING_BEAR", "DRIFTING_BULL"]:
            # [PHASE Ω-ANTI-FRAGILITY] Drifting/Compression regimes are noisy.
            # [EPA - Entropy Phase-Attractor]: If entropy is low and we have v-pulse/ignition, we relax thresholds.
            # In Phase 48, we reduce the 'mult' from 1.5x to 1.1x if ignition is confirmed.
            has_ignition = snapshot.metadata.get("v_pulse_detected", False) or regime_state.v_pulse_detected
            
            if quantum_state.entropy < 0.6 and (limit_mode or has_ignition):
                mult = 1.02 if has_ignition else 1.05  # Omega Attraction: Ignition sovereign
            else:
                mult = 1.10 if quantum_state.phi > 0.3 else 1.15 # Reduced from 1.25
                
            dynamic_buy_thresh *= mult
            dynamic_sell_thresh *= mult
            dynamic_conf_min = min(0.95, dynamic_conf_min * 1.05) # Relaxed from 1.1

        elif regime_state.current.value in ["HIGH_VOL_CHAOS", "CHOPPY"]:
            # Em caos e chop, a exigência de sinal é muito mais estrita
            dynamic_buy_thresh *= 1.5
            dynamic_sell_thresh *= 1.5
            dynamic_conf_min = min(0.95, dynamic_conf_min * 1.2)

        # [MAKER_ADVANTAGE] If using Limit Orders, we can afford lower entry confidence
        if limit_mode:
            dynamic_conf_min *= 0.90
            self._log_cooldown("maker_advantage", f"📈 MAKER_ADVANTAGE: Confidence requirement reduced by 10% (Floor: {dynamic_conf_min:.2f})", 120)


        # ═══ 3.5 DECOERÊRENCE SUPREMA (GOD-MODE REVERSAL — Phase 50) ═══
        # Se a entropia é máxima (todos os agentes discordam fortemente, pânico) e/ou
        # a volatilidade está explodindo, o ruído não é ruído: é uma "Liquidation Cascade".
        # [PHASE 51] V-Pulse Ignition Bypass
        v_pulse_detected = snapshot.metadata.get("v_pulse_detected", False)
        v_pulse_active = snapshot.metadata.get("v_pulse_capacitor", 0.0) >= 0.65

        # 1. Bypass Startup Cooldown (V-Pulse is self-validating and hot)
        uptime = time.time() - self._creation_time
        if v_pulse_detected and uptime < OMEGA.get("startup_cooldown_seconds", 120):
            log.omega("⚡ [V-PULSE] Bypassing Startup Cooldown for immediate strike.")
            # We don't modify self._creation_time as it's used for uptime, we just skip the check in _check_vetos
        is_god_mode = False
        
        tick_velocity = snapshot.metadata.get("tick_velocity", 0.0)
        has_v_pulse = snapshot.metadata.get("v_pulse_detected", False) or regime_state.v_pulse_detected
        is_velocity_burst = tick_velocity > 40.0 or has_v_pulse
        
        is_god_candidate = quantum_state.metadata.get("is_god_candidate", False)
        
        if (quantum_state.entropy > 0.85 or is_velocity_burst or is_god_candidate) and \
           regime_state.current.value in ["HIGH_VOL_CHAOS", "SQUEEZE_BUILDUP", "SQUEEZE", "DRIFTING_BEAR"]:
            
            candles_m1 = snapshot.candles.get("M1")
            if candles_m1 and len(candles_m1.get("close", [])) >= 5:
                closes = np.array(candles_m1["close"], dtype=np.float64)
                delta_price = closes[-1] - closes[-5]
                atr_local = self._get_current_atr(snapshot)
                
                # REVERSAL SYNC: Se o preço caiu forte (>3x ATR) ou v-pulse Bear, o God-Mode COMPRA.
                if (abs(delta_price) > atr_local * 3.0 or is_velocity_burst or has_v_pulse) and atr_local > 0:
                    is_god_mode = True
                    # Inversão cinemática
                    god_signal = -1.0 if delta_price > 0 else 1.0
                    
                    self._log_cooldown("GOD_MODE_REVERSAL", f"🌌 [GOD-MODE REVERSAL PHASE 50] Ent:{quantum_state.entropy:.2f} Pulse:{has_v_pulse} Delta:{delta_price:+.2f}. Absorção Ativada.", 30)
                    
                    action = Action.BUY if god_signal > 0 else Action.SELL
                    confidence = 0.99
                    signal = god_signal
                    # reasoning and other variables will be populated below as the function continues
        
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
                
                # OMEGA: Epsilon check (1e-6) to fix floating-point precision issues (e.g., 0.77 < 0.77)
                if confidence < (dynamic_conf_min - 1e-6):
                    reasons.append(f"LOW_CONFIDENCE({confidence:.2f} < req {dynamic_conf_min:.2f})")
                return self._wait(" | ".join(reasons))
        
        # If we reach here, we have an Action (either from God-Mode or Normal)
        strike_flag = f" | [PHASE_50_STRIKE: {action.name}]"
        
        # The rest of the function (calculating SL/TP, RR, MC) will continue using the 'action', 'signal', 'confidence'.
        # Since is_god_mode is True, some later VETOs (like MC expected return < 0) will be bypassed.

        # ═══ PHASE Ω-EXTREME: CONSCIOUSNESS GATES (Φ) ═══
        phi_min = OMEGA.get("phi_min_threshold", 0.4)
        phi_hydra = OMEGA.get("phi_hydra_threshold", 4.5)

        # Calibração Dinâmica de Consciência (Dynamic Incoherence)
        # O valor de Φ natural varia com a energia do mercado. 
        # Exigir Φ=0.4 em mercados "Drifting" causa paralisia infinita.
        dynamic_phi_min = phi_min

        # 1. Ajuste por Regime
        if regime_state.current.value in ["DRIFTING_BEAR", "DRIFTING_BULL"]:
            dynamic_phi_min *= 0.25  # Mais permissivo em drifting regimes para capturar reversões lentas
        elif regime_state.current.value in ["CHOPPY", "UNKNOWN", "LOW_LIQUIDITY"]:
            dynamic_phi_min *= 0.35  # Baixa volatilidade = menor necessidade de integração complexa
        elif regime_state.current.value in ["TRENDING_BULL", "TRENDING_BEAR"]:
            dynamic_phi_min *= 0.8   # Tendências claras são mais fáceis de ler

        # 2. Ajuste por Coerência do Enxame
        if quantum_state.coherence > 0.85:
            dynamic_phi_min *= 0.5   # Se há unanimidade entre agentes, toleramos menor Φ sistêmico

        # 3. Ajuste por Confiança Extrema
        if quantum_state.confidence > 0.90:
            dynamic_phi_min *= 0.7

        # [Phase 26] Integration with Java PnL Predictor
        pnl_prediction = snapshot.metadata.get("pnl_prediction", "STABLE")
        if "NEGATIVE_EXPECTANCY" in pnl_prediction or "DRAWDOWN_RISK" in pnl_prediction:
            risk_mult = 0.5  # Reduce aggression if math says we are losing edge
        elif "RELAXED" in pnl_prediction:
            risk_mult = 1.3  # Even higher conviction in relaxed mode
        elif pnl_prediction == "STABLE":
            risk_mult = 1.0
        # 4. Ajuste por Previsão Java PnL Predictor
        pnl_pred = snapshot.metadata.get("pnl_prediction")
        pnl_prediction = pnl_pred if pnl_pred else "STABLE"
        
        if pnl_pred == "HIGH_PROBABILITY:POSITIVE_EXPECTANCY":
            dynamic_phi_min *= 0.5  # Expectância positiva atestada, facilita entrada
            
        phi = quantum_state.phi

        # [Phase 50] Quantum Resonance Ignition Gate
        is_phi_resonance = False
        if phi >= 0.85 and (has_v_pulse or signal_strength > 0.8):
             is_phi_resonance = True
             
        # [Phase 50] God-Mode Reversal (Decoerência Suprema)
        # In highly incoherent but extremely high-entropy (panic) regimes, 
        # subvert the wait and provide liquidity during the vacuum.
        is_god_mode_phi = False # Renamed to avoid conflict with existing is_god_mode
        q_meta = quantum_state.metadata
        entropy = q_meta.get("entropy", 0)
        entropy_thresh = OMEGA.get("god_mode_entropy_threshold", 0.85)
        
        if (phi < 0.2 and entropy > entropy_thresh) or is_god_mode:
            is_god_mode_phi = True
            log.omega(f"👹 [GOD-MODE REVERSAL] — High Entropy Panic/God Candidate (Φ={phi:.2f}, E={entropy:.2f}). Bypassing Incoherence Veto.")

        # ═══ VETO 03: SYSTEM INCOHERENCE (PHI) ═══
        phi_threshold = dynamic_phi_min # Use the dynamically calculated phi_min
        
        # [Phase 50] Resonance Bypass
        if is_phi_resonance:
            phi_threshold = 0.01 # Near-zero threshold for resonance
            
        # [Phase 50] God-Mode Reversal & Resonance Bypass
        if phi < phi_threshold and not is_god_mode_phi: # God-Mode Reversal bypasses this veto
            self._log_cooldown("PHI_VETO", f"⚠️ VETO: SYSTEM_INCOHERENCE (Φ={phi:.4f} < {phi_threshold:.4f})", 60)
            return self._wait("INCOHERENCE_VETO")

        # ═══ VETO 04: CHAOS SHIELD ═══
        chaos_regime = regime_state.current.value == "HIGH_VOL_CHAOS"
        if chaos_regime:
            self._log_cooldown("CHAOS_VETO", "🛡️ VETO: CHAOS_SHIELD (Market dynamics is too unstable)", 30)
            return self._wait("CHAOS_VETO")
            
        # ═══ VETO PREDITIVO (JAVA PNL PREDICTOR) ═══
        if pnl_pred == "IMPOSSIBLE:NEGATIVE_EXPECTANCY":
            if quantum_state.confidence < 0.95:  # Só ignora o veto se a certeza do enxame for quase absoluta
                return self._wait("JAVA_PNL_VETO (Negative Expectancy Detected)")

        is_hydra_mode = False
        if quantum_state.phi >= phi_hydra:
            self._log_cooldown("HYDRA_RESONANCE", f"🔥 [HYDRA RESONANCE DETECTED] — Φ={quantum_state.phi:.2f}. Destravando agressão máxima.", 60)
            is_hydra_mode = True

        # ═══ 4. PHASE 4: PREDATOR MODE OVERRIDE ═══
        # Se o agente ShadowPredator detectou manipulação institucional, entramos em modo de contra-ataque.
        shadow_signal = next((s for s in quantum_state.agent_signals if s.agent_name == "ShadowPredator"), None)
        if shadow_signal and shadow_signal.confidence > 0.85:
            self._log_cooldown("PREDATOR_MODE", "💀 [PREDATOR MODE ACTIVATED] — Detecção de manipulação institucional. Override direcional.", 60)
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
        
        # [PHASE Ω-ANTI-FRAGILITY] Adaptive SL Scaling
        # Em regimes de ruído ou queda lenta (Drifting), alargamos o range para evitar stop-hunting.
        dynamic_sl_mult = sl_mult
        if regime_state.current.value in ["UNKNOWN", "LOW_LIQUIDITY", "CHOPPY", "HIGH_VOL_CHAOS", "DRIFTING_BEAR", "DRIFTING_BULL"]:
            # Reduzido de 2.5 para 1.8 para aproximar o SL e evitar perdas profundas
            dynamic_sl_mult *= 1.8 
            
            # [PHASE Ω-RESILIENCE] Log Cooldown (Avoid spam on every cycle)
            mult_delta = abs(dynamic_sl_mult - self._last_sl_mult)
            if regime_state.current.value != self._last_regime or \
               mult_delta > 0.1:
                self._log_cooldown("chaos_shield", f"🛡️ [CHAOS SHIELD] Regime {regime_state.current.value} detectado. Alargando SL para {dynamic_sl_mult:.2f} ATR.", 60)
                self._last_sl_mult = dynamic_sl_mult
                self._last_regime = regime_state.current.value
 
        # [PHASE Ω-SINGULARITY] Injection of P-Brane Limit Logic
        limit_mode_param = OMEGA.get("limit_execution_mode", 0.0)
        limit_mode = limit_mode_param > 0.5 and regime_state.current.value in ["DRIFTING_BEAR", "DRIFTING_BULL", "LOW_LIQUIDITY", "SQUEEZE_BUILDUP"]

        if action == Action.BUY:
            stop_loss = price - atr * dynamic_sl_mult
            take_profit = price + atr * tp_mult
        else:
            stop_loss = price + atr * dynamic_sl_mult
            take_profit = price - atr * tp_mult

        # ═══ RISK/REWARD CHECK ═══
        risk = abs(price - stop_loss)
        reward = abs(take_profit - price)
        rr_ratio = reward / risk if risk > 0 else 0

        # [Phase Ω-Resilience] Commission-Aware RR:
        # Check if reward covers commission + min profit target
        sym_info = snapshot.symbol_info
        point_val = sym_info.get("point", 1.0) if sym_info else 1.0
        contract_size = sym_info.get("trade_contract_size", 1.0) if sym_info else 1.0
        
        # Estimate dynamic commission per lot from bridge
        # We don't have direct access to bridge here, but we can use the value from OMEGA or assume a default
        # Ideally, we should have the dynamic_comm in snapshot metadata.
        comm_per_lot = snapshot.metadata.get("dynamic_commission_per_lot", 15.0)
        min_net_profit = OMEGA.get("min_profit_per_ticket", 60.0)
        
        # Profit in points needed to cover commission + target (assuming 1 lot for ratio check)
        min_points_needed = (comm_per_lot + min_net_profit) / (contract_size if contract_size > 0 else 1.0)
        
        if reward < min_points_needed:
            # Se for God-Mode, engolimos o trade mesmo assim, a explosão de reversão vai compensar.
            if is_god_mode:
                 log.omega(f"👹 [GOD-MODE] Bypassing REWARD_TOO_SMALL ({reward:.2f} < {min_points_needed:.2f})")
            else:
                # If the ATR-based TP is too small to cover fees, we must expand it or veto
                # We choose to expansion first if the regime allows, otherwise veto.
                if regime_state.current.value in ["TRENDING_BULL", "TRENDING_BEAR"]:
                    take_profit = price + (min_points_needed * 1.1) if action == Action.BUY else price - (min_points_needed * 1.1)
                    reward = abs(take_profit - price)
                    rr_ratio = reward / risk if risk > 0 else 0
                    log.debug(f"⚖️ RR ADJUST: Expanding TP to {reward:.4f} to cover commissions + target profit.")
                else:
                    return self._wait(f"REWARD_TOO_SMALL_FOR_ALPHA (Reward {reward:.4f} < Min {min_points_needed:.4f})")

        min_rr = OMEGA.get("trinity_min_rr_ratio", 1.15)
        
        # [Phase 50] Resonance RR Relaxation
        if is_phi_resonance:
            min_rr *= 0.7  # Relax RR for resonance ignition
            
        if regime_state.current.value in ["LOW_LIQUIDITY", "UNKNOWN", "CHOPPY", "SQUEEZE_BUILDUP", "DRIFTING_BEAR", "DRIFTING_BULL"]:
             # Maker execution (limit_mode) captures spread, making low RR trades profitable.
             min_rr = 0.4 if limit_mode else (min_rr * 0.8)

        # [Phase 51] God-Mode RR Rationale
        if is_god_mode:
            min_rr = OMEGA.get("god_mode_rr_min", 0.35)
            log.omega(f"👹 [GOD-MODE RR] Bypassing RR thresholds for panic absorption (Min RR: {min_rr:.2f})")

        # [Phase 52] Divergence-Aware RR Adjustment
        # Se agentes 'Leading' divergem da decisão final, aumentamos a exigência de RR.
        q_meta = quantum_state.metadata
        top_bulls = q_meta.get("top_bulls", [])
        top_bears = q_meta.get("top_bears", [])
        
        leading_against = False
        if action == Action.SELL:
            if "LiquidStateAgent" in top_bulls or "PriceGravityAgent" in top_bulls:
                leading_against = True
        elif action == Action.BUY:
            if "LiquidStateAgent" in top_bears or "PriceGravityAgent" in top_bears:
                leading_against = True
                
        if leading_against and not is_god_mode:
            # [Phase 52 Refinement] Cap at 2.5 to avoid paralysis
            min_rr = min(2.5, min_rr * 1.5) 
            self._log_cooldown("RR_DIVERGENCE", f"⚠️ RR_DIVERGENCE: Líderes desconfiados. Elevando Min RR para {min_rr:.2f}", 60)

        if rr_ratio < min_rr:
            return self._wait(f"RR_RATIO_LOW({rr_ratio:.2f} < {min_rr:.2f})")

        # [Phase 48] Alpha Integrity: Commission Reward Ratio Gate
        # Reward in $ / Estimated Commission must be > threshold
        if comm_per_lot > 0:
            # Actual reward in $ (for 1 lot)
            reward_in_dollars = reward * contract_size
            comm_reward_ratio = reward_in_dollars / comm_per_lot
            min_comm_ratio = OMEGA.get("min_commission_reward_ratio", 1.5)
            
            if comm_reward_ratio < min_comm_ratio:
                return self._wait(f"COMM_REWARD_RATIO_LOW({comm_reward_ratio:.2f} < {min_comm_ratio})")

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

            # [Phase 51] Kinematic V-Pulse Relaxation
            if is_god_mode or has_ignition:
                relaxation = OMEGA.get("kinematic_v_pulse_relaxation", 2.5)
                kinematic_atr_mult *= relaxation
                log.omega(f"🚀 [ALPHA SURGE] Relaxing kinematic threshold to {kinematic_atr_mult:.2f} (x{relaxation})")
            
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

        # [Phase 52] VETO 7: KINEMATIC DECOUPLING (Vácuo de Liquidez)
        # Se estamos comprando no topo de um spike parabólico longe da média
        ema_9 = snapshot.indicators.get("M5_ema_9")
        if ema_9 is not None and len(ema_9) > 0 and atr > 0:
            dist_from_mean = (snapshot.price - ema_9[-1]) / atr
            # Se preço > 2 ATRs da média E sinal é BUY -> Perigo de Blow-off
            if action == Action.BUY and dist_from_mean > 2.0:
                # Se não houver uma ignição genuína comprovada por volume institucional
                v_ratio_list = snapshot.indicators.get("M5_volume_ratio", [1.0])
                vol_ratio = v_ratio_list[-1] if v_ratio_list is not None and len(v_ratio_list) > 0 else 1.0
                if vol_ratio < 3.0: # Volume não justifica o estiramento
                    return self._wait(f"KINEMATIC_DECOUPLING_BUY (Price too far from mean: {dist_from_mean:.1f}xATR)")
            # Simétrico para SELL
            elif action == Action.SELL and dist_from_mean < -2.0:
                v_ratio_list = snapshot.indicators.get("M5_volume_ratio", [1.0])
                vol_ratio = v_ratio_list[-1] if v_ratio_list is not None and len(v_ratio_list) > 0 else 1.0
                if vol_ratio < 3.0:
                    return self._wait(f"KINEMATIC_DECOUPLING_SELL (Price too far from mean: {dist_from_mean:.1f}xATR)")

        # [Phase 52] VETO 8: BLOW-OFF CLIMAX (Proteção contra Exaustão)
        q_meta = quantum_state.metadata
        agent_reasons = str(q_meta.get("agent_signals", ""))
        if "BLOW_OFF_CLIMAX" in agent_reasons or "REDLINE_VETO" in agent_reasons:
            return self._wait("BLOW_OFF_EXHAUSTION_DETECTED (Reversal Imminent)")

        # [Phase 52] VETO 9: HORIZONTAL RESISTANCE (Double/Triple Top)
        if action == Action.BUY:
            # Buscar picos recentes no M1 e M5
            for tf in ["M1", "M5"]:
                candles = snapshot.candles.get(tf)
                if candles and len(candles["high"]) > 50:
                    highs = np.array(candles["high"], dtype=np.float64)
                    recent_peaks = []
                    # Detectar picos (fractal 5)
                    for i in range(2, len(highs) - 5):
                        if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
                           highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                            recent_peaks.append(highs[i])
                    
                    if recent_peaks:
                        # Se houver picos no mesmo nível (±0.1%)
                        for peak in recent_peaks[-10:]: # Olhar últimos 10 picos
                            dist_to_peak = (peak - snapshot.price) / snapshot.price * 100
                            # Se o preço está encostando em um topo anterior
                            if abs(dist_to_peak) < 0.08:
                                # Contar quantos picos existem nesse nível (alinhamento)
                                matches = sum(1 for p in recent_peaks if abs((p - peak)/peak*100) < 0.1)
                                if matches >= 2: # Topo Duplo ou Triplo
                                    return self._wait(f"HORIZONTAL_RESISTANCE_VETO (Level={peak:.0f}, Peaks={matches})")

        # ═══ 4. MONTE CARLO VALIDATION ═══
        # Simula 5000 universos paralelos para validar o trade
        volatility_est = atr / max(price, 1) * np.sqrt(252)  # Anualizar
        # [Phase 47] Drift Decoupling: Se houve ignição ou explosão de ticks, 
        # forçamos um drift agressivo para o Monte Carlo não ser pessimista.
        forced_drift = None
        tick_velocity = snapshot.metadata.get("tick_velocity", 0.0)
        has_ignition = snapshot.metadata.get("v_pulse_detected", False) or regime_state.v_pulse_detected
        
        if has_ignition or tick_velocity > 35.0:
            # Mu = sigma * 5.0 (Ito Acceleration)
            forced_drift = (atr / max(price, 1)) * 5.0 * (1.0 if action == Action.BUY else -1.0)
            self._log_cooldown("forced_drift", f"🚀 [IGNITION DRIFT] Applying forced drift of {forced_drift:+.4f} due to {'V-Pulse' if has_ignition else 'Velocity Burst'}", 60)

        mc_result = self.monte_carlo.simulate_trade(
            current_price=price,
            direction=action.value,
            stop_loss=stop_loss,
            take_profit=take_profit,
            volatility=max(volatility_est, 0.01),
            regime=regime_state.current.value,
            n_simulations=5000,
            n_steps=100,
            force_drift=forced_drift
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

            # [Phase Ω-Singularity] Monte Carlo Hard Veto: Expected Value (EV)
            if mc_result.expected_return < 0:
                # Se o retorno esperado é negativo, a estatística diz que vamos perder dinheiro no longo prazo.
                # Só permitimos se for um sinal de exaustão extrema (God-Mode)
                if not is_god_mode:
                    return self._wait(f"MC_NEGATIVE_EV({mc_result.expected_return:.2f}) - Estatística desfavorável")

            # [Phase Ω-Resilience] Counter-Trend Phi Gate
            # Se a ordem é BUY em regime BEAR, ou SELL em regime BULL, exigimos Φ muito maior.
            is_counter_trend = (action == Action.BUY and "BEAR" in regime_state.current.value) or \
                               (action == Action.SELL and "BULL" in regime_state.current.value)
            
            if is_counter_trend and phi < 0.18:
                return self._wait(f"COUNTER_TREND_LOW_PHI (Φ={phi:.2f} < 0.18) - Sem integração p/ reversão")

            mc_reasoning = (
                f"MC[score={mc_score:+.3f} WP={mc_win_prob:.1%} "
                f"EV={mc_ev:+.2f} CVaR={mc_cvar:+.2f} "
                f"sim={mc_result.simulation_time_ms:.1f}ms]"
            )

            # VETO se Monte Carlo score é muito negativo
            mc_min_score = OMEGA.get("mc_min_score", -0.1)
            if mc_score < mc_min_score:
                return self._wait(f"MC_SCORE_LOW({mc_score:+.3f}<{mc_min_score}) {mc_reasoning}")

            # [Phase Ω-Singularity] Relax win probability for Maker trades
            # Maker trades benefit from spread capture, allowing for ~40% Win Prob.
            mc_min_wp = OMEGA.get("mc_min_win_prob", 0.45)
            if limit_mode:
                mc_min_wp = 0.40
                
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
            f"ATR={atr:.2f} RR={rr_ratio:.2f}{strike_flag} | "
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
            metadata={
                "phi": quantum_state.phi if quantum_state else 0.0,
                "quantum_metadata": quantum_state.metadata if quantum_state else {}
            }
        )
        
        # [PHASE Ω-SINGULARITY] Injection of P-Brane Limit Logic
        limit_mode = OMEGA.get("limit_execution_mode", 0.0)
        if limit_mode > 0.5 and regime_state.current.value in ["DRIFTING_BEAR", "DRIFTING_BULL", "LOW_LIQUIDITY", "SQUEEZE_BUILDUP"]:
            decision.metadata["limit_execution"] = True
            decision.metadata["jitter_offset"] = OMEGA.get("p_brane_jitter_offset_points", 0.0)

        
        if is_hydra_mode:
            decision.metadata["hydra_mode"] = True
            
        if is_phi_resonance:
            decision.metadata["phi_resonance"] = True
            decision.metadata["relaxed_mode"] = True

        self._execute_count += 1
        self._decision_history.append({
            "action": action.value,
            "signal": signal,
            "confidence": confidence,
            "mc_score": mc_score,
            "mc_win_prob": mc_win_prob,
        })

        # 🎯 DECISION REALIZATION
        # (Log movido para SniperExecutor para evitar falsos positivos de 'ghost trading')
        self.last_decision = decision
        return decision

    def _check_vetos(self, snapshot, asi_state, regime_state, v_pulse_detected: bool = False) -> Optional[str]:
        """
        Sistema de veto — rejeita trades em condições de perigo.
        NÃO é paralisante: veta apenas em casos claros.
        """
        # 0. Startup Cooldown (Evita trades com sistema "frio")
        uptime = time.time() - self._creation_time
        startup_cooldown = OMEGA.get("startup_cooldown_seconds", 120)  # Default 2 minutos
        if uptime < startup_cooldown and not v_pulse_detected:
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

        # 5. Sessão desfavorável (Weekend Sniper Mode)
        session = TimeEngine.session_info()
        if session.get("is_weekend"):
            # No fim de semana, só permitimos o "tiro perfeito"
            # 1. Sinal deve ser muito forte (> 0.65)
            # 2. Spread não pode ser abusivo (< 15% do ATR)
            atr = snapshot.atr
            spread = snapshot.symbol_info.get("spread", 999) if snapshot.symbol_info else 999
            
            # Traduz spread de pontos para preço se necessário (simplificado: spread_rel)
            # Mas aqui usamos os thresholds de favorabilidade
            if session.get("trading_favorability", 0) < 0.20:
                 # Se a liquidez for nula (Phase 47 Floor: 0.20), bloqueio total
                 return "WEEKEND_ZERO_LIQUIDITY"
                 
            # Se estivermos tentando operar com sinal fraco no fds, bloqueia
            # Note: o 'decide' será chamado depois, aqui é apenas veto preventivo
            # Como não temos o 'signal' aqui no _check_vetos, usamos a favorabilidade
            if session.get("trading_favorability", 0) < 0.35:
                # Permitir apenas se a volatilidade (ATR) for saudável
                if atr < 15.0: # BTC relaxado para 15 (Phase 32)
                    return "WEEKEND_STAGNANT_MARKET"
            
        # 6. [PHASE Ω-ANTI-FRAGILITY] Ping-Pong Veto
        # Impede inversão de mão imediata em regimes instáveis após loss
        if regime_state.current.value in ["UNKNOWN", "LOW_LIQUIDITY", "CHOPPY"]:
            # Verificar se houve loss recente (via asi_state ou tracking interno)
            # Como asi_state.consecutive_losses reseta em win, usamos nosso log interno
            now = time.time()
            if self._last_loss_time > 0 and (now - self._last_loss_time) < 300: # 5 minutos de trava
                return f"ANTI_PING_PONG ({300 - (now - self._last_loss_time):.0f}s rem)"
 
        return None  # Sem veto

    def _get_current_atr(self, snapshot) -> float:
        """Obtém ATR atual do snapshot."""
        atr = snapshot.indicators.get("M5_atr_14")
        if atr is not None and len(atr) > 0:
            return float(atr[-1])
        return 0.0

    def _log_cooldown(self, key: str, message: str, cooldown_sec: int = 30, level: str = "info"):
        """Evita spam de logs repetitivos no terminal."""
        now = time.time()
        if now - self._log_cache.get(key, 0) > cooldown_sec:
            if level == "warning":
                log.warning(message)
            elif level == "omega":
                log.omega(message)
            else:
                log.info(message)
            self._log_cache[key] = now

    def _wait(self, reason: str) -> Decision:
        """Retorna decisão WAIT com log inteligente para evitar spam."""
        # [PHASE Ω-RESILIENCE] Log wait reasons with cooldown if they are spammy
        # (A maioria já é logada no ASIBrain, mas aqui filtramos redundâncias internas)
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

    def update_loss_event(self):
        """Notifica o TrinityCore de um evento de loss recente."""
        self._last_loss_time = time.time()
        # [PHASE Ω-RESILIENCE] Log Cooldown para evitar flood no terminal
        self._log_cooldown("LOSS_EVENT", "🛡️ TrinityCore: LOSS event notified. ANTI-PING-PONG gate armed.", 30, level="warning")

    @property
    def stats(self) -> dict:
        return {
            "total_decisions": len(self._decision_history),
            "executions": self._execute_count,
            "vetos": self._veto_count,
            "veto_rate": self._veto_count / max(1, len(self._decision_history)),
        }
