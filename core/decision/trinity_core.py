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
from execution.quantum_tunneling_execution import QuantumTunnelingExecution
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
    limit_order: bool = False  # [PHASE Ω-SINGULARITY]
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
        self._startup_timestamp = time.time() # [PHASE Ω-RESILIENCE] Cold Start Guard
        
        # [PHASE Ω-ANTI-FRAGILITY] Ping-Pong State
        self.last_decision = None
        self._log_cache = {}  # {key: timestamp}
        log.omega("🛡️ TrinityCore Integrated Information (Φ) GATE: ENABLED")
        
        # [PHASE Ω-RESILIENCE] Log Cooldowns (Avoid spam)
        self._last_phi_val = 0.0
        self._last_sl_mult = 0.0
        self._last_regime = ""
        self._last_loss_time = 0.0  # [PHASE Ω-ANTI-FRAGILITY] Initialization
        
        # [PHASE Ω-PHD] Alpha Extraction (Entropy Bridge)
        self._signal_history = []  # List of last 20 signals
        self.entropy_bridge_active = False
        self._kl_history = []      # [Phase Ω-PhD-4] KL Velocity tracking
        self._mc_ev_history = []   # [Phase Ω-Stability] Store last 3 MC EV results
        self.last_decision_bypassed = False  # [Phase Ω-PhD-5] Track if stale regime was bypassed
        self._last_kl_shift_time = 0.0      # [Phase Ω-PhD-14] Track recent paradigm shifts

    @ast_self_heal
    @catch_and_log(default_return=None)
    @timed
    def decide(self, quantum_state: QuantumState,
               regime_state: RegimeState,
               snapshot,
               asi_state) -> Optional[Decision]:
        """
        Toma a decisão final: BUY, SELL ou WAIT.
        """
        # [PHASE 14 FIX] Canonical Initialization (Anti-UnboundLocalError)
        action = Action.WAIT
        signal = 0.0
        confidence = 0.0
        coherence = 0.0
        atr = 0.0
        rr_ratio = 1.0
        price = snapshot.price if snapshot else 0.0
        stop_loss = 0.0
        take_profit = 0.0
        lot_size = 0.01
        mc_score = 0.0
        mc_win_prob = 0.0
        mc_ev = 0.0
        mc_cvar = 0.0
        mc_reasoning = "N/A"
        is_god_mode = False
        is_phi_resonance = False
        is_tunneling = False
        is_hydra_mode = False
        pnl_prediction = "STABLE"
        entropy = 0.0
        tec_active = False
        tec_entropy = 0.0
        has_v_pulse = False
        strike_flag = ""
        phi = 0.0
        # [PHASE Ω-RESILIENCE] Cold Start Cooldown (120s)
        elapsed = time.time() - self._startup_timestamp
        cooldown_period = OMEGA.get("cold_start_cooldown_seconds", 120.0)
        
        # [PHASE Ω-STABILITY] Structural Veto Gauntlet
        has_v_pulse = snapshot.metadata.get("v_pulse_detected", False) or regime_state.v_pulse_detected
        veto_reason = self._check_vetos(snapshot, asi_state, regime_state, v_pulse_detected=has_v_pulse, quantum_state=quantum_state)
        if veto_reason:
            return self._wait(veto_reason)
        if elapsed < cooldown_period:
            if time.time() - self._log_cache.get("cold_start", 0) > 30:
                log.info(f"⏳ [COLD START COOLDOWN] Syncing conscience: {elapsed:.1f}s / {cooldown_period}s remaining.")
                self._log_cache["cold_start"] = time.time()
            return self._wait(f"COLD_START_SYNC_VETO ({int(cooldown_period - elapsed)}s left)")

        # [PHASE Ω-RESILIENCE] Stale Snapshot Veto (Latency Protection)
        # If the think cycle took too long (like the 28s startup delay), the snapshot is stale.
        from datetime import datetime, timezone
        snap_age = (datetime.now(timezone.utc) - snapshot.timestamp).total_seconds()
        if snap_age > 1.5:
             return self._wait(f"STALE_SNAPSHOT_VETO ({snap_age:.1f}s age > 1.5s limit)")

        if quantum_state is None or regime_state is None:
            return self._wait("NO_DATA")

        # [Phase Ω-Singularity] Core Indicator Extraction (Global Scope)
        phi = getattr(quantum_state, 'phi', 0.0)
        phi_score = phi
        signal = getattr(quantum_state, 'collapsed_signal', 0.0)
        confidence = getattr(quantum_state, 'confidence', 0.0)
        coherence = getattr(quantum_state, 'coherence', 0.0)

        # [Phase 48] Metadata Extraction & Initialization (Consistency Fix)
        sym_info = snapshot.symbol_info
        q_meta = quantum_state.metadata if quantum_state and hasattr(quantum_state, 'metadata') else {}
        point_val = sym_info.get("point", 0.00001) if sym_info else 0.00001
        atr_m5 = self._get_current_atr(snapshot)
        atr = atr_m5 # Backward compatibility for legacy code paths

        # [Phase 50] Evolution: Entropy & God-Mode Initialization
        entropy = q_meta.get("entropy", 0)
        entropy_thresh = OMEGA.get("god_mode_entropy_threshold", 0.85)
        is_god_mode_phi = False

        has_ignition = snapshot.metadata.get("v_pulse_detected", False) or regime_state.v_pulse_detected
        is_breakdown = regime_state.current == MarketRegime.HFT_BREAKDOWN
        is_god_mode = snapshot.metadata.get("god_mode_active", False)
        is_phi_resonance = snapshot.metadata.get("phi_resonance", False)
        is_lethal_ignition = has_ignition and snapshot.metadata.get("v_pulse_capacitor", 0.0) > 0.8
        is_lethal_strike = is_lethal_ignition and confidence > 0.85 # [Ω-PhD] Define lethal strike scope
        
        # [Phase 73] Navier-Stokes Ignition Logic
        v_pulse_intensity = snapshot.metadata.get("v_pulse_capacitor", 0.0)

        # [Phase Ω-Singularity] Initialize metadata variables to avoid NameError
        is_tunneling = snapshot.metadata.get("is_tunneling", False)
        is_phi_resonance = snapshot.metadata.get("phi_resonance", False)
        pnl_prediction = snapshot.metadata.get("pnl_prediction", "STABLE")
        entropy = snapshot.metadata.get("entropy", 0.0)
        # coherence already initialized at top
        is_low_phi_drift = False # Initialize for global scope
        # [Ω-PhD-OPTIM] V-Pulse Recovery Sovereignty Detection
        is_v_pulse_recovery = has_ignition and signal > 0 and ("BEAR" in regime_state.current.value or "CHOPPY" in regime_state.current.value or "UNKNOWN" in regime_state.current.value)

        # ═══ [Phase Ω-PhD-6] Topological Entropy Collapse (TEC) Sensor ═══
        # Detecta colapso estrutural (Singularidade) via decaimento de entropia.
        tec_active = False
        tec_entropy = 1.0
        # signal already initialized at top (collapsed_signal)
        # [Phase Ω-PhD-7] Geodesic Flow Extraction (NRM Sovereignty) - Moved to TOP to avoid UnboundLocalError
        agent_signals = getattr(quantum_state, 'agent_signals', []) if quantum_state else []
        riemannian_signal = next((s for s in agent_signals if s.agent_name == "RiemannianRicci"), None)
        is_geodesic_flow = riemannian_signal and "GEODESIC_FLOW" in (getattr(riemannian_signal, 'reasoning', "") or "")
        
        # [Phase Ω-PhD-8] Ghost-Order-InFERENCE (Predatory Sweep Bypass)
        ghost_signal = next((s for s in agent_signals if s.agent_name == "GhostOrderInference"), None)
        is_ghost_sweep = ghost_signal and "GHOST_SWEEP_DETECTED" in (getattr(ghost_signal, 'reasoning', "") or "")

        # [Phase Ω-PhD-14] Ricci Singularity (Structural Manifold Reversal)
        ricci_signal = next((s for s in agent_signals if s.agent_name == "RicciRegime"), None)
        is_ricci_singularity = ricci_signal and (getattr(ricci_signal, 'metadata', {}) or {}).get("ricci_singularity", False)

        # [Phase Ω-PhD-14] Non-Bonded Repulsion (Van der Waals Reversion)
        repulsion_signal = next((s for s in agent_signals if s.agent_name == "NonBondedRepulsion"), None)
        is_repulsion_sovereign = repulsion_signal and abs(getattr(repulsion_signal, 'signal', 0.0)) > 0.8

        try:
            shannon = snapshot.metadata.get("shannon_entropy", 0.9)
            v_pulse = snapshot.metadata.get("v_pulse_capacitor", 0.0)
            shannon_history = snapshot.metadata.get("shannon_history", [])
            if len(shannon_history) >= 10:
                avg_past = sum(shannon_history[-10:-1]) / 9
                shannon_drop = avg_past - shannon
                sensitivity = OMEGA.get("tec_sensitivity", 0.40)
                min_energy = OMEGA.get("tec_min_v_pulse", 0.30)
                if shannon_drop > sensitivity and v_pulse > min_energy:
                    tec_active = True
                    tec_entropy = shannon
                    self._log_cooldown("TEC_RESONANCE", f"⚡ [Ω-TEC RESONANCE] Structural collapse (Drop={shannon_drop:.3f}, Pulse={v_pulse:.2f})", 60, level="omega")
        except Exception as e:
            log.warning(f"TEC Sensor Error: {e}")

        # [PHASE Ω-STABILITY] ABSOLUTE KL-VETO: Information Geometry Paradigm Shift
        kl_div = snapshot.metadata.get("kl_divergence", 0.0)
        current_price = snapshot.price
        
        # [Phase Ω-Singularity] Sovereignty based on extreme paradigm shift
        kl_shift_thresh = OMEGA.get("paradigm_shift_threshold", 0.95)
        is_kl_shift_sovereign = kl_div > kl_shift_thresh

        # [PHASE Ω-PhD-11] Singularity Sovereignty: Unifica TEC, Lethal Ignition e KL Shift
        is_tec_sovereign = (tec_active or (is_lethal_ignition and abs(signal) > 0.50) or (is_kl_shift_sovereign and abs(signal) > 0.60)) and abs(signal) > 0.35
        
        # [Phase Ω-PhD-4] Ω-KL-Velocity Guard (Curvature of Information)
        self._kl_history.append(kl_div)
        if len(self._kl_history) > 10: self._kl_history.pop(0)
        
        kl_velocity = 0.0
        if len(self._kl_history) >= 2:
            kl_velocity = abs(self._kl_history[-1] - self._kl_history[-2])
            kl_vel_thresh = OMEGA.get("kl_velocity_threshold", 0.15)
            
            # Se a geometria da informação está mudando rápido demais (Shock), vetamos.
            # Isso evita entrar no "olho do furacão" de uma mudança de paradigma instável.
            # [Phase Ω-PhD-7] Geodesic override: Se o fluxo é laminar (geodésico), o choque é estável.
            if not is_tec_sovereign and not is_geodesic_flow and kl_velocity > kl_vel_thresh and not has_ignition:
                self._log_cooldown("KL_VELOCITY_VETO", f"🛡️ [Ω-KL-VELOCITY] Information Shock ({kl_velocity:.3f} > {kl_vel_thresh:.2f}). Waiting for geometry stability.", 60)
                return self._wait("KL_VELOCITY_VETO")
            elif is_geodesic_flow and kl_velocity > kl_vel_thresh:
                 self._log_cooldown("KL_GEODESIC", f"☄️ [Ω-GEODESIC SHOCK] Bypassing KL Shock via Geodesic Flow Sovereignty (KL_Vel={kl_velocity:.2f}).", 60, level="omega")

        # [PHASE Ω-SINGULARITY] Recalibration: 0.95 -> 2.5 (Evita saídas falsas até métrica real estável)
        kl_base_thresh = OMEGA.get("paradigm_shift_threshold", 2.5)
        kl_veto_thresh = kl_base_thresh * 2.0 
        
        # [Phase Ω-PhD] NEW: Soft-Veto Check. 
        # Hard Veto moved to extreme 5.0x threshold. In-between values reduce lot size via RiskEngine.
        kl_extreme_thresh = kl_base_thresh * 5.0
        if not is_tec_sovereign and kl_div > kl_extreme_thresh:
            return Decision(
                action=Action.WAIT,
                confidence=1.0,
                signal_strength=0.0,
                entry_price=snapshot.price,
                stop_loss=0,
                take_profit=0,
                lot_size=0,
                regime=regime_state.current.value,
                reasoning=f"WAIT: PARADIGM_SHIFT VETO (KL={kl_div:.2f} > {kl_extreme_thresh:.2f}) - Information Chaos",
                metadata={"kl_div": kl_div}
            )
        
        # [Phase 51] PARADIGM SHIFT CLOSE (Omniscience Exit)
        if kl_div > kl_base_thresh:
            self._last_kl_shift_time = time.time() # Store shift for sovereignty window
            if not is_tec_sovereign:
                log.omega(f"🔮 PARADIGM SHIFT DETECTED (KL={kl_div:.4f}). Exiting current positions preemptively.")
            return Decision(
                action=Action.WAIT,
                confidence=1.0,
                signal_strength=0.0,
                entry_price=snapshot.price,
                stop_loss=0,
                take_profit=0,
                lot_size=0,
                regime=regime_state.current.value,
                reasoning=f"PARADIGM_SHIFT_CLOSE: KL Divergence {kl_div:.4f} > threshold. Kinetic exhaustion confirmed.",
                metadata={"emergency_close": True, "paradigm_shift": True}
            )

        # ═══ QUANTUM STATE CHECK ═══
        if quantum_state.superposition and not is_v_pulse_recovery:
            return self._wait("SUPERPOSITION (agentes não convergiram)")

        # [Phase Ω-PhD-7] Geodesic Flow Extraction (NRM Sovereignty) - EXTRACTION MOVED TO TOP
        
        action = Action.WAIT # Default state

        # ═══ THRESHOLDS ═══
        base_buy_threshold = OMEGA.get("buy_threshold")
        base_sell_threshold = OMEGA.get("sell_threshold")
        base_confidence_min = OMEGA.get("confidence_min")
        
        # [Phase Ω-PhD] Ω-Entropy Bridge (Temporal Convergence)
        # Persistence as a substitute for Intensity
        self._signal_history.append(signal)
        if len(self._signal_history) > 20: self._signal_history.pop(0)
        
        is_convergent = False
        if len(self._signal_history) >= 20:
            variance = np.var(self._signal_history)
            # [Phase Ω-PhD-4] Ω-Entropy-Convergence Filter
            # Stable signals (low variance) are required for the Bridge to activate.
            convergence_thresh = OMEGA.get("entropy_convergence_threshold", 0.002)
            if variance < convergence_thresh:
                if (signal > 0 and signal > 0.9 * base_buy_threshold) or \
                   (signal < 0 and signal < 0.9 * base_sell_threshold):
                    is_convergent = True
                    self._log_cooldown("ENTROPY_BRIDGE", f"🧠 [Ω-ENTROPY BRIDGE] Authorizing stable signal (Var={variance:.5f}) below threshold.", 60)
            
            # [Phase Ω-PhD-2] Φ-Resonance Scaling: Stability as a substitute for Energy
            # If the signal is geometrically stable, we don't need a high-energy information collapse (Phi).
            self.entropy_bridge_active = is_convergent # Export flag for later use

            # [Phase Ω-PhD-3] Ω-Kinetic-Symmetry Gate (Exhaustion Detection)
            # Persistence (Time) must be matched by Kinetic Energy (Velocity/ATR Ratio)
            # If we are stable but the 'heartbeat' (tick velocity) is fading, it's a trap.
            self.kinetic_exhaustion = False
            if is_convergent:
                tick_vel = abs(snapshot.metadata.get("tick_velocity", 0.0))
                # [Phase Ω-PhD-5/8] Dynamic Kinetic Floor (Reset Ω-PhD-Next)
                # [Phase Ω-Hard-Lethality] Kinematic sanity cap (3.5): Prevents optimizer from deadlocking the bot.
                k_floor = min(float(OMEGA.get("kinetic_velocity_floor", 2.0)), 3.5)
                
                # [Ω-PhD-Dynamic] Alpha Scaling: Se houver ressonância ou ignição, relaxamos o floor
                if phi > 0.40 or is_lethal_ignition or is_tec_sovereign:
                    k_floor *= 0.5 # Relaxa 50% para capturar explosões iniciais
                    
                if tick_vel < k_floor:
                    # [Phase Ω-PhD-5] Ignition Sovereignty: Lethal V-Pulse, TEC or high Phi overrides kinetic floor
                    # [Phase Ω-PhD-7] Geodesic Sovereignty: Fluxo laminar ignora floor cinemático
                    # [Phase Ω-Extreme] Stable Convergence (Bridge) overrides floor with minimal Phi
                    # [Ω-PhD-Topological] TEC_SOVEREIGNTY ignore exaustão (Colapso de entropia é prova absoluta)
                    is_braided = any((getattr(s, 'metadata', {}) or {}).get("is_braided") for s in agent_signals if s.agent_name == "TopologicalBraiding")
                    phi_override = phi > 0.20 or is_tec_sovereign or is_geodesic_flow or is_braided or (is_convergent and phi > 0.04)
                    
                    if not is_lethal_ignition and not phi_override:
                        self.kinetic_exhaustion = True
                        self._log_cooldown("KINETIC_EXHAUSTION", f"⚠️ [Ω-KINETIC EXHAUSTION] Stability detected but Velocity ({tick_vel:.1f}) is below floor ({k_floor:.1f}).", 60)
                    elif phi_override:
                        ov_reason = "TEC" if is_tec_sovereign else ("BRAIDED" if is_braided else ("GEODESIC" if is_geodesic_flow else ("PHI" if phi > 0.20 else "BRIDGE")))
                        self._log_cooldown("KINETIC_OVERRIDE", f"🧠 [Ω-KINETIC OVERRIDE] Bypassing exhaustion via {ov_reason} Sovereignty (Φ={phi:.2f} | Floor_Adj={k_floor:.1f}).", 60, level="omega")
        else:
            self.entropy_bridge_active = False
            self.kinetic_exhaustion = False
        
        # Calibração Dinâmica de Limiares (Dynamic Threshold Calculus)
        # Em mercados com muito volume ou previsões altíssimas, a exigência do limiar se auto-calibra.
        dynamic_buy_thresh = base_buy_threshold if base_buy_threshold is not None else 0.50
        dynamic_sell_thresh = base_sell_threshold if base_sell_threshold is not None else -0.50
        dynamic_conf_min = base_confidence_min if base_confidence_min is not None else 0.85

        # [Phase Ω-PhD-10] Supportive Vacuums (SR Abolition)
        # Se agentes quânticos detectam colapso de onda através do nível de S/R, nós o "abolimos".
        is_vacuum_abolition = False
        quantum_dir = next((s for s in quantum_state.agent_signals if s.agent_name == "QuantumDirectionalInference"), None)
        sr_signal = next((s for s in quantum_state.agent_signals if s.agent_name == "SRAgent"), None)
        
        if quantum_dir and sr_signal and abs(quantum_dir.signal) > 0.8:
            # Se a direção quântica confronta a direção do SR (ex: SR diz Reverte, Quantum diz fura)
            if np.sign(quantum_dir.signal) != np.sign(sr_signal.signal):
                is_vacuum_abolition = True
                self._log_cooldown("SR_ABOLITION", f"🌌 [Ω-SR ABOLITION] Support/Resistance abolished by Quantum Wave Collapse (QDir={quantum_dir.signal:.2f}).", 60, level="omega")
                # Reduzimos a exigência de confiança para atravessar o nível
                dynamic_conf_min *= 0.9
                # Se o sinal era Seller contra um Support, e Quantum diz Sell, ignoramos o SR.
                if np.sign(signal) == np.sign(quantum_dir.signal):
                     dynamic_buy_thresh *= 0.8
                     dynamic_sell_thresh *= 0.8

        # 2. Ajuste por Regime e [Phase Ω-Singularity] MAKER_ADVANTAGE
        limit_mode = (regime_state.current.value in ["DRIFTING_BEAR", "DRIFTING_BULL", "LOW_LIQUIDITY", "SQUEEZE_BUILDUP"]) \
                     and OMEGA.get("limit_execution_mode", 0.0) > 0.5
        
        # 1. Ajuste pelo PnL Predictor
        pnl_pred = snapshot.metadata.get("pnl_prediction")
        if pnl_pred == "HIGH_PROBABILITY:POSITIVE_EXPECTANCY":
            # Facilita entradas promissoras
            dynamic_buy_thresh *= 0.6
            dynamic_sell_thresh *= 0.6
            dynamic_conf_min *= 0.8
        
        current_regime_val = str(getattr(regime_state.current, 'value', regime_state.current))
        
        # Indicators already extracted at top for Phase Ω Stability
        
        has_ignition = snapshot.metadata.get("v_pulse_detected", False) or regime_state.v_pulse_detected
        has_v_pulse = has_ignition
        is_lethal_ignition = snapshot.metadata.get("is_lethal_strike", False)
        is_ricci_attractor = "RIEMANNIAN_RICCI" in snapshot.metadata.get("active_attractors", [])
        
        if regime_state.current in [MarketRegime.TRENDING_BULL, MarketRegime.TRENDING_BEAR]:
            # Tendências definidas precisam de menos confiança isolada, a maré já ajuda
            dynamic_conf_min *= 0.85
        elif current_regime_val in ["SQUEEZE_BUILDUP", "DRIFTING_BEAR", "DRIFTING_BULL", "HFT_BREAKDOWN", "CREEPING_BULL", "CREEPING_BEAR"]:
            # [Phase Ω-NEXUS] Adaptabilidade Radical em Liquidez Baixa ou Breakdown
            c_thresh = OMEGA.get("creep_maturity_threshold", 300.0) # [SCALP] Increased from 150 to 300
            duration = int(getattr(regime_state, 'duration_bars', 0) or 0)
            
            if "CREEPING" in current_regime_val and duration > c_thresh:
                # [Phase Ω-Hard-Lethality] Unconditional Bypass for CREEPING: 
                # Persistent trends are our alpha source. We override age veto if signal is present.
                if is_lethal_ignition or abs(signal) > 0.12 or phi_score > 0.15: # [SCALP] Relaxed signal/phi req
                    self._log_cooldown("CREEP_BYPASS", f"⚡ [Ω-MATURITY BYPASS] Stale regime ({duration} bars) overridden by { 'Ignition' if is_lethal_ignition else 'Structural Integrity' }.", 60, level="omega")
                    self.last_decision_bypassed = True
                else:
                    self._log_cooldown("CREEP_MATURITY", f"🛡️ [Ω-CREEP MATURITY] Regime {current_regime_val} is too old ({duration} bars).", 60)
                    return self._wait("CREEP_MATURITY_VETO")

            # [Phase Ω-PhD-Next] Hardened Phi Guard for Drift/Creep
            # Se a integração (Φ) é baixa (< 0.35), NÃO relaxamos os filtros, pois o regime é instável.
            # [Phase Ω-Stability] Integridade Estrutural vs Ignição
            # Se Φ é muito baixo (<0.25), o 'is_low_phi_drift' permanece ativo MESMO com ignição,
            # forçando o swarm a ter coerência mínima para validar o momentum.
            is_low_phi_drift = phi_score < 0.35 and (not (has_ignition or is_lethal_ignition) or phi_score < 0.25)
            
            # [Ω-PhD-OPTIM] Sovereignty Override
            if is_v_pulse_recovery:
                is_low_phi_drift = False
                self._log_cooldown("V_PULSE_SOVEREIGNTY", f"⚡ [Ω-V-PULSE SOVEREIGNTY] Recovery strike authorized (Sig={signal:.2f}). Bypassing low-phi hardening.", 60, level="omega")
            
            if (has_ignition or phi_score > 0.35 or regime_state.current == MarketRegime.HFT_BREAKDOWN) and not is_low_phi_drift:
                 mult = 0.90 if regime_state.current == MarketRegime.HFT_BREAKDOWN else 0.95
                 
                 # [Phase Ω-PhD-Next] Restore Drift relaxation for healthy Phi
                 is_drift = "DRIFTING" in current_regime_val
                 if is_drift: mult *= 0.55 # [PHASE Ω-STRIKE] Relaxed from 0.65 to 0.55 to catch alpha early
                 
                 dynamic_buy_thresh *= mult
                 dynamic_sell_thresh *= mult
                 dynamic_conf_min *= 0.80 if regime_state.current == MarketRegime.HFT_BREAKDOWN else 0.85
                 self._log_cooldown("NEXUS_RELAXATION", f"🧠 [PHASE Ω-NEXUS] Relaxing thresholds due to { current_regime_val } (Mult: {mult:.2f}, Conf Min: {dynamic_conf_min:.2f})", 60)
            else:
                 # [Phase Ω-Extreme] Se Φ é baixo em Drift, endurecemos o filtro
                 # [Ω-RECALIBRATION-3.0] Reduced from 2.5x to 1.8x to avoid total SELL paralysis
                 mult = 1.8 if is_low_phi_drift else 1.10
                 dynamic_buy_thresh *= mult
                 dynamic_sell_thresh *= mult
                 if is_low_phi_drift:
                     dynamic_conf_min = min(0.98, dynamic_conf_min * 1.25)
                     
                     # ═══ [PHASE Ω-STRICT] DRIFT_COHERENCE_VETO ═══
                     # Se o regime é instável (Low Phi), NÃO aceitamos entrar com baixa coerência
                     # [Ω-RECOVERY] Se o sinal é forte (>0.40), relaxamos de 0.50 para 0.40
                     # [Ω-RECALIBRATION-3.0] Lowered base thresholds to unlock SELL in DRIFTING_BEAR
                     c_req = 0.22 if abs(signal) > 0.55 else 0.27 if abs(signal) > 0.35 else 0.32 if abs(signal) > 0.15 else 0.40
                     
                     # [Ω-STABILITY] Chão de Coerência Absoluto p/ Caos Extremo (Evitar Fakeouts em Φ < 0.10)
                     if phi_score < 0.10: c_req = max(c_req, 0.25)
                     
                     # [Ω-PGC] Phi-Coherence Gradient: Quanto menor o Φ, maior o consenso exigido.
                     # [Ω-RECALIBRATION-3.0] Penalty reduced from 0.2 to 0.12 to avoid marginal blocking
                     if phi_score < 0.45:
                         pgc_penalty = max(0, 0.45 - phi_score) * 0.12
                         c_req = min(0.50, c_req + pgc_penalty)
                         
                     # [Ω-PhD-OPTIM] Coherence Relaxation for Sovereignty
                     if is_v_pulse_recovery:
                         # Phoenix Strike 2.0: If V-Pulse is extremely high (>0.8), relax drift requirement significantly
                         c_req = 0.41 if phi < 0.25 else 0.35
                         if v_pulse_detected:
                             if regime_state.v_pulse_intensity > 0.8:
                                 c_req = 0.20
                             else:
                                 c_req = 0.25
                          
                     if coherence < c_req and not (is_tec_sovereign or is_god_mode or (phi_score > 0.18 and coherence > 0.25)):

                         self._log_cooldown("DRIFT_COHERENCE_VETO", f"🛡️ VETO: DRIFT_COHERENCE_WEAK (Coherence={coherence:.2f} < {c_req:.2f} requirement in Drift/Low-Phi)", 60)
                         return self._wait("DRIFT_COHERENCE_WEAK")
                         
                     self._log_cooldown("LOW_PHI_DRIFT_GUARD", f"🛡️ [LOW PHI DRIFT] Incoherence detected (Φ={phi_score:.2f}). Hardening filters (2.5x) and requiring high coherence.", 60)
                 elif not self.entropy_bridge_active:
                     dynamic_conf_min = min(0.95, dynamic_conf_min * 1.05)
        
        elif current_regime_val in ["UNKNOWN", "CHOPPY", "LOW_LIQUIDITY"]:
            # [Phase Ω-Extreme] UNKNOWN Lockdown: Exige confiança avassaladora em regimes nebulosos
            # [PHASE Ω-STRIKE] Relaxed UNKNOWN multiplier from 1.4 to 1.1 to facilitate faster entries
            lock_mult = 1.1 if current_regime_val == "UNKNOWN" else 1.2
            dynamic_conf_min = min(0.98, dynamic_conf_min * lock_mult)
            dynamic_buy_thresh *= 1.1
            dynamic_sell_thresh *= 1.1
            self._log_cooldown("UNKNOWN_LOCKDOWN", f"🕵️ [Ω-LOCKDOWN] Scaling confidence requirement for {current_regime_val} to {dynamic_conf_min:.2f}", 60)

        elif regime_state.current == MarketRegime.PARADIGM_SHIFT:
            # Em mudança de paradigma, somos ultra-conservadores
            dynamic_buy_thresh *= 1.8
            dynamic_sell_thresh *= 1.8
            dynamic_conf_min = min(0.98, dynamic_conf_min * 1.3)
            self._log_cooldown("paradigm_shift_gate", f"🛡️ [PARADIGM SHIFT] Extreme filters active (Conf Min: {dynamic_conf_min:.2f})", 60)

        # [Phase Ω-Coherence] UNKNOWN Regime Veto
        if regime_state.current.value == "UNKNOWN":
            unknown_phi_gate = OMEGA.get("unknown_regime_phi_gate", 0.04)
            if not is_tec_sovereign and phi < unknown_phi_gate and not (has_ignition or is_lethal_ignition or is_ricci_attractor):
                self._log_cooldown("UNKNOWN_PHI_VETO", f"⚠️ VETO: UNKNOWN_REGIME_INCOHERENCE (Φ={phi:.2f} < req {unknown_phi_gate:.2f}). Avoiding blind entries.", 60)
                return self._wait("UNKNOWN_REGIME_INCOHERENCE")
            elif phi >= unknown_phi_gate:
                 self._log_cooldown("UNKNOWN_UNLOCKED", f"🔓 [Ω-SCALP] UNKNOWN unblocked via structural pattern (Φ={phi:.2f}).", 60, level="omega")
        
        # [Phase Ω-Singularity] QUANTUM MOMENTUM IGNITION (QMI)
        # Treat Energy (Velocity) as a substitute for Coherence (PHI) during Breakouts
        is_breakout = "BREAKOUT" in regime_state.current.value or regime_state.current == MarketRegime.HFT_BREAKDOWN
        tick_vel_abs = abs(snapshot.metadata.get("tick_velocity", 0.0))
        is_qmi_active = is_breakout and tick_vel_abs > 25.0 and abs(signal) > 0.40
        phi_req = 0.20 if is_qmi_active else 0.30

        # [Phase Ω-Safety] Cheap Spike Filter (Anti-FOMO)
        is_creeping = "CREEPING" in regime_state.current.value
        if not is_tec_sovereign and (is_creeping or is_breakout) and tick_vel_abs > 12.0 and phi < phi_req and not (is_god_mode or is_v_pulse_recovery):
            reason = "QMI_INSUFFICIENT" if is_qmi_active else "CHEAP_SPIKE"
            self._log_cooldown(f"{reason}_VETO", f"🛡️ [{reason} VETO] Velocity surge ({tick_vel_abs:.1f}) without structural coherence (Φ={phi:.2f} < req {phi_req:.2f}).", 60)
            return self._wait(f"{reason}_VETO")

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
                    
                    # [Phase Ω-Coherence] God-Mode Coherence Verification
                    # Even in God-Mode, we need a TINY bit of coherence (0.05) to ensure it's not pure tick noise
                    if not (is_tec_sovereign or is_v_pulse_recovery) and phi < 0.05:
                        self._log_cooldown("GOD_MODE_NOISE_VETO", f"⚠️ VETO: GOD_MODE_NOISE (Φ={phi:.3f} is too low even for reversal).", 30)
                        return self._wait("GOD_MODE_NOISE")
                    # reasoning and other variables will be populated below as the function continues
        
        # ═══ 3.6 ORTHOGONAL CONVERGENCE (Echo Chamber Penalty) ═══
        # [Phase Ω-Transcendence] Verifica se o sinal é dominado por apenas um "tipo" de agente.
        bulls = q_meta.get("bull_agents", [])
        bears = q_meta.get("bear_agents", [])
        
        def _count_domains(agent_names):
            domains = set()
            for name in agent_names:
                if "Agent" in name:
                    # Categorização heurística baseada no nome
                    if any(x in name for x in ["Trend", "Momentum", "Velocity"]): domains.add("Kinematic")
                    elif any(x in name for x in ["Volume", "Liquidity", "OrderBook", "Vacuum"]): domains.add("OrderFlow")
                    elif any(x in name for x in ["Structure", "SRAgent", "Fractal", "FVG", "Block"]): domains.add("Structural")
                    elif any(x in name for x in ["Macro", "Sentiment", "Whale", "OnChain"]): domains.add("Macro")
                    elif any(x in name for x in ["Chaos", "Entropy", "Quantum", "Manifold"]): domains.add("Physics")
                    else: domains.add("Other")
            return len(domains)
            
        bull_domains = _count_domains(bulls)
        bear_domains = _count_domains(bears)
        
        # Penaliza a confiança se o sinal vem de menos de 3 domínios diferentes
        major_domains = bull_domains if signal > 0 else bear_domains
        if not is_tec_sovereign and major_domains < 3 and not is_god_mode:
            dynamic_conf_min *= 1.1 # Aumenta exigência (mais difícil passar)
            self._log_cooldown("ECHO_CHAMBER", f"⚠️ [ECHO CHAMBER] Signal supported by only {major_domains} domains. Raising conf threshold to {dynamic_conf_min:.2f}", 120)

        # [Phase Ω-Pleroma] TREND ALIGNMENT GUARDRAILS
        # In creeping regimes, the trend is the master. Fading is dangerous.
        is_creeping_bull = "BULL" in regime_state.current.value
        is_creeping_bear = "BEAR" in regime_state.current.value
        is_breakdown = regime_state.current == MarketRegime.HFT_BREAKDOWN
        
        # Test tentative directions
        tentative_is_counter = False
        if signal > 0 and is_creeping_bear: tentative_is_counter = True
        elif signal < 0 and is_creeping_bull: tentative_is_counter = True

        # [Phase Ω-Singularity] Exhaustion Sovereignty Check
        has_exhaustion_sovereignty = False
        entropy = 0.0
        if tentative_is_counter:
            exhaustion_agents = ["PrigogineDissipative", "NavierStokesTurbulence", "AntifragileExhaustionAgent", "VPINToxicity"]
            entropy_raw = snapshot.indicators.get("M1_entropy", 0.0)
            if isinstance(entropy_raw, (list, np.ndarray)) and len(entropy_raw) > 0:
                entropy = float(entropy_raw[-1])
            else:
                entropy = float(entropy_raw or 0)
            
            # Check for exhaustion agents in quantum_state signals
            found_exhaustion_agent = False
            if hasattr(quantum_state, 'agent_signals') and quantum_state.agent_signals:
                for s in quantum_state.agent_signals:
                    if s.agent_name in exhaustion_agents:
                        if s.confidence > 0.85 and np.sign(s.signal) == np.sign(signal):
                            found_exhaustion_agent = True
                            break
            
            has_exhaustion_sovereignty = found_exhaustion_agent and (entropy > 0.70)
            
            if has_exhaustion_sovereignty:
                # [Phase Ω-Singularity] Force thresholds to base-level for fading when bifurcation is clear
                # Using 0.35 as a safe ceiling for counter-trend entries
                # [Phase Ω-Extreme] Tightened exhaustion floor
                dynamic_buy_thresh = OMEGA.get("exhaustion_signal_min", 0.40)
                dynamic_sell_thresh = -dynamic_buy_thresh
                self._log_cooldown("EXHAUSTION_SOVEREIGNTY_LOG", f"⚡ [EXHAUSTION] Sovereignty ACTIVE (Entropy: {entropy:.2f}). Thresholds relaxed to {dynamic_buy_thresh:.2f} for fading.", 60)

            # ═══════════════════════════════════════════════════
            # [Phase Ω-Burst] BURST IGNITION SENSOR (BIS)
            # ═══════════════════════════════════════════════════
            # Se a velocidade é violenta na direção do sinal, relaxamos Φ
            # para capturar a singularidade antes que a estrutura se forme.
            tick_vel = snapshot.metadata.get("tick_velocity", 0.0)
            is_high_energy_surge = (signal > 0.35 and tick_vel > 15.0) or (signal < -0.35 and tick_vel < -15.0)
            
            if is_high_energy_surge:
                # [Phase Ω-Singularity] Capture the burst
                has_exhaustion_sovereignty = True # Reaproveita o bypass de Veto
                self._log_cooldown("BURST_IGNITION", f"🔥 [BURST IGNITION] High velocity detected ({tick_vel:.1f}). Bypassing structural gates.", 30, level="omega")

        # 1. Dynamic Signal Penalization for Counter-Trend
        if tentative_is_counter and not (is_breakdown or is_lethal_ignition or has_exhaustion_sovereignty or is_tec_sovereign):
            # Penaliza sinais contra a inércia do regime (Menos se houver Breakdown ou Ignição Letal ou Exaustão ou TEC)
            signal *= 0.5 # Redução moderada de força (Plano Ω-Pro)
            confidence *= 0.7 # Exige mais certeza but not overkill
            self._log_cooldown("TREND_PENALTY", f"⚠️ [TREND ALIGNMENT] Counter-Trend detected ({action.name} vs {regime_state.current.value}). Applying moderate suppression.", 60)

        # ═══ [Ω-KINETIC CONFLICT GUARD] ═══
        # Se a velocidade instantânea (tick_velocity) está forte no sentido oposto ao sinal,
        # vetamos a entrada para evitar "correr contra a locomotiva".
        tick_vel = snapshot.metadata.get("tick_velocity", 0.0)
        # Threshold de conflito cinemático (12.0)
        k_conflict_thresh = OMEGA.get("kinetic_conflict_threshold", 12.0)
        
        if not is_god_mode and not is_tec_sovereign:
            if (signal > 0 and tick_vel < -k_conflict_thresh) or (signal < 0 and tick_vel > k_conflict_thresh):
                self._log_cooldown("KINETIC_CONFLICT", f"🛡️ VETO: KINETIC_CONFLICT (Signal={np.sign(signal)} vs Vel={tick_vel:+.1f}).", 30)
                return self._wait("KINETIC_CONFLICT_VETO")

        # 2. Hard Veto for Weak Counter-Trend
        if tentative_is_counter:
            phi_min_counter = 0.30 if "CREEPING" in regime_state.current.value or "TRENDING" in regime_state.current.value else 0.20
            sig_min_counter = 0.45 if "CREEPING" in regime_state.current.value or "TRENDING" in regime_state.current.value else 0.40
            
            # [Phase Ω-PhD-14] Paradigm Sovereignty Bypass
            # Following a KL divergence shock, we allow faster counter-trend entries (Tunneling).
            is_paradigm_sovereign = (time.time() - self._last_kl_shift_time) < 300.0
            if is_paradigm_sovereign:
                phi_min_counter *= 0.25 # 0.20 -> 0.05
                sig_min_counter *= 0.5  # 0.40 -> 0.20
                self._log_cooldown("PARADIGM_SOVEREIGNTY", f"🌪️ [PARADIGM SOVEREIGNTY] Information Geometry shift detected recently. Relaxing counter-trend gates (Φ={phi_min_counter:.2f}).", 60, level="omega")
            
            # [Phase 73] Ignition Sovereignty
            ign_mult = OMEGA.get("ignition_sovereignty_mult", 0.4) if (has_ignition or is_breakdown) else 1.0
            
            if has_exhaustion_sovereignty:
                ign_mult *= 0.5 # Relaxamento adicional de exaustão
                self._log_cooldown("EXHAUSTION_SOVEREIGNTY", f"⚡ [EXHAUSTION SOVEREIGNTY] Bifurcation detected (Entropy={entropy:.2f}). Relaxing counter-trend gates.", 60)

            phi_min_counter *= ign_mult
            sig_min_counter *= ign_mult
            
            if not (is_tec_sovereign or is_ricci_singularity or is_repulsion_sovereign) and (phi < phi_min_counter or abs(signal) < sig_min_counter):
                return self._wait(f"TREND_PROTECTION_VETO (Requires Φ>{phi_min_counter:.2f} & Sig>{sig_min_counter:.2f} to fade {regime_state.current.value})")

            # [Phase Ω-Stochastic] MOMENTUM CONTINUITY CHECK
            # Se vamos contra a maré, a inércia imediata (tick_velocity) JÁ DEVE ter virado.
            # Não tentamos 'adivinhar' o topo; esperamos a primeira martelada de volta.
            tick_velocity = snapshot.metadata.get("tick_velocity", 0.0)
            
            # [Phase 73] Ignition Sovereignty: Se houver ignição letal, EXAUSTÃO, BREAKDOWN ou TEC, ignoramos o veto de continuidade
            if is_lethal_ignition or is_breakdown or has_exhaustion_sovereignty or is_tec_sovereign:
                pass
            elif (signal > 0 and tick_velocity < -12.0) or (signal < 0 and tick_velocity > 12.0):
                 return self._wait(f"MOMENTUM_CONTINUITY_VETO (Action direction contradicts immediate tick inertia)")

        # [Phase Ω-PhD-6] Singularity Resonance Bypass: Handled at start of decide()
        # is_tec_sovereign logic removed here to avoid duplication

        if pnl_prediction == "IMPOSSIBLE:NEGATIVE_EXPECTANCY":
            if is_lethal_ignition or is_lethal_strike or is_god_mode or is_tec_sovereign:
                self._log_cooldown("PNL_SOVEREIGNTY", f"🔥 [PNL SOVEREIGNTY] Bypassing JAVA_PNL_VETO due to { 'TEC' if is_tec_sovereign else 'LETHAL_STRIKE/IGNITION/GOD' } (Conf: {quantum_state.confidence:.2f})", 30)
                pass
            elif is_v_pulse_recovery and v_pulse_intensity > 0.65:
                self._log_cooldown("PNL_RECOVERY_BYPASS", f"🔥 [Ω-V-PULSE PNL BYPASS] High intensity recovery (Pulse={v_pulse_intensity:.2f}). Ignoring negative expectancy.", 60, level="omega")
                pass
            elif tentative_is_counter and has_exhaustion_sovereignty:
                pass
            elif self.entropy_bridge_active and pnl_pred == "IMPOSSIBLE:NEGATIVE_EXPECTANCY":
                # [Phase Ω-PhD-2] PnL Expectancy Smoothing for Creeping Alpha
                # We allow a small bypass if the signal was authorized by the Entropy Bridge
                # but the Java predictor (optimized for energy) doesn't see the expectancy yet.
                self._log_cooldown("PNL_SMOOTHING", "🧬 [Ω-PNL SMOOTHING] Overriding negative expectancy due to Entropy Bridge stability.", 60)
                pass
            else:
                return self._wait("JAVA_PNL_VETO (Negative Expectancy Detected)")
                
        if not is_god_mode:
            # [Phase Ω-Singularity] FINAL OVERRIDE for Exhaustion Sovereignty
            # Exhaustion (Bifurcation) is often a lone signal; we must not let ECHO CHAMBER or other filters block it.
            if tentative_is_counter and has_exhaustion_sovereignty:
                dynamic_buy_thresh = OMEGA.get("exhaustion_signal_min", 0.40)
                dynamic_sell_thresh = -dynamic_buy_thresh
                dynamic_conf_min = 0.70 # Relax confidence for bifurcation strikes
            
            # [Phase Ω-PhD] Ω-Entropy Bridge Check
            # Se Φ é baixo em Drift, desativamos o bypass de convergência (Bridge) para evitar noise-entry.
            allow_bridge = not is_low_phi_drift
            
            buy_cond = (signal >= dynamic_buy_thresh or (is_convergent and signal > 0 and allow_bridge)) and not self.kinetic_exhaustion
            sell_cond = (signal <= dynamic_sell_thresh or (is_convergent and signal < 0 and allow_bridge)) and not self.kinetic_exhaustion
            
            if self.kinetic_exhaustion:
                return self._wait("KINETIC_EXHAUSTION_VETO (Stable but Decelerating)")

            if (is_tec_sovereign or buy_cond) and (is_tec_sovereign or confidence >= (dynamic_conf_min - 1e-6)):
                action = Action.BUY
            elif (is_tec_sovereign or sell_cond) and (is_tec_sovereign or confidence >= (dynamic_conf_min - 1e-6)):
                action = Action.SELL
            else:
                reasons = []
                if signal > 0 and not buy_cond: reasons.append(f"BUY_SIGNAL_WEAK({signal:.3f}<{dynamic_buy_thresh:.3f})")
                if signal < 0 and not sell_cond: reasons.append(f"SELL_SIGNAL_WEAK({signal:.3f}>{dynamic_sell_thresh:.3f})")
                if confidence < (dynamic_conf_min - 1e-6): reasons.append(f"CONF_WEAK({confidence:.3f}<{dynamic_conf_min:.2f})")
                
                # [Phase Ω-PhD-6] TEC Sovereignty: Skip wait if singularity detected
                if not is_tec_sovereign:
                    return self._wait(f"NO_CONVERGENCE: {' | '.join(reasons)}")
        
        # [Phase Ω-PhD-6] Singularity Resonance Bypass: Force Action if TEC is active
        if is_tec_sovereign and not is_god_mode:
            if signal > 0: action = Action.BUY
            elif signal < 0: action = Action.SELL
            
        # If we reach here, we have an Action (either from God-Mode, normal flow, or TEC)
        strike_flag = f" | [PHASE_50_STRIKE: {action.name}]"
        if is_v_pulse_recovery:
            strike_flag += " | [Ω-PHOENIX_PULSE: SOVEREIGN]"
        
        # [Phase Ω-PhD-Next] Micro-Momentum Alignment Veto (Global)
        # Se os últimos 3 candles de M1 são fortemente BULL (para um sinal SELL) ou vice-versa, vetamos.
        candles_m1 = snapshot.candles.get("M1")
        momentum_rejection = False
        v_pulse_detected = False
        
        if candles_m1 and len(candles_m1["close"]) >= 3:
            closes = candles_m1["close"][-3:]
            opens = candles_m1["open"][-3:]
            
            # [Ω-PULSE] V-Pulse anti-entry (Single large candle rejection)
            last_candle_body = abs(closes[-1] - opens[-1])
            is_opposing = (action == Action.BUY and closes[-1] < opens[-1]) or (action == Action.SELL and closes[-1] > opens[-1])
            
            # Se o último candle foi um susto (corpo > 1.2x ATR) contra a posição, esperamos o próximo
            if is_opposing and last_candle_body > (snapshot.atr * 1.2) and not is_god_mode:
                v_pulse_detected = True
            
            # Momentum de 3 candles (Clássico)
            if action == Action.BUY: # Queremos ver pelo menos 1 candle verde ou não 3 de queda forte
                if all(c < o for c, o in zip(closes, opens)): momentum_rejection = True
            elif action == Action.SELL: # Queremos ver pelo menos 1 candle vermelho ou não 3 de alta forte
                if all(c > o for c, o in zip(closes, opens)): momentum_rejection = True

        if v_pulse_detected:
             return self._wait("V_PULSE_ANTI_ENTRY_VETO (Large counter-candle detected)")
             
        if momentum_rejection and not (is_lethal_ignition or is_breakout or is_tec_sovereign or is_god_mode):
             return self._wait("MICRO_MOMENTUM_VETO (Last 3 M1 candles strongly oppose signal)")

        # ═══ PHASE Ω-EXTREME: CONSCIOUSNESS GATES (Φ) ═══
        phi_min = OMEGA.get("phi_min_threshold", 0.25) # Normalized for 190 agents
        phi_hydra = OMEGA.get("phi_hydra_threshold", 4.5)

        # Calibração Dinâmica de Consciência (Dynamic Incoerência)
        # O valor de Φ natural varia com a energia do mercado. 
        # Exigir Φ=0.4 em mercados "Drifting" causa paralisia infinita.
        dynamic_phi_min = phi_min
        
        # [Phase Ω-PhD-2] Φ-Resonance Scaling
        if self.entropy_bridge_active:
            # Stability (Entropy Bridge) is a substitute for Energy (Phi)
            # We relax the Phi requirement by 80% (Resonance Mode)
            dynamic_phi_min *= 0.20
            self._log_cooldown("PHI_RESONANCE", f"🧠 [Ω-PHI RESONANCE] Scaling Phi-Gate to {dynamic_phi_min:.4f} for stable drift.", 60)

        # [Phase Ω-PhD-8] Kolmogorov Algorithmic Sync
        is_programmatic = quantum_state.metadata.get("is_programmatic", False)
        if is_programmatic:
            # Se o fluxo é programático, a confiança na estrutura é maior.
            # Reduzimos a exigência de Φ em 50%.
            dynamic_phi_min *= 0.50
            self._log_cooldown("KOLMOGOROV_SYNC", f"🤖 [Ω-KOLMOGOROV SYNC] Flow is programmatic. Scaling Phi-Gate to {dynamic_phi_min:.4f}.", 60)

        # [Phase Ω-PhD-6] TEC Resonance Gate
        # Se TEC está ativo, o sensor topológico precede o enxame.
        if tec_active:
            dynamic_phi_min = 0.01
            self.last_decision_bypassed = True 

        # 1. Ajuste por Regime
        if regime_state.current.value in ["DRIFTING_BEAR", "DRIFTING_BULL", "CREEPING_BULL", "CREEPING_BEAR"]:
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

        # 4. Ajuste por Previsão Java PnL Predictor
        pnl_pred = snapshot.metadata.get("pnl_prediction")
        pnl_prediction = pnl_pred if pnl_pred else "STABLE"
        
        if pnl_pred == "HIGH_PROBABILITY:POSITIVE_EXPECTANCY":
            dynamic_phi_min *= 0.5  # Expectância positiva atestada, facilita entrada
            
        phi = quantum_state.phi

        # [Phase 50] Quantum Resonance Ignition Gate
        is_phi_resonance = False
        has_v_pulse = snapshot.metadata.get("v_pulse_detected", False)
        signal_strength = quantum_state.signal_strength if hasattr(quantum_state, 'signal_strength') else abs(quantum_state.raw_signal)
        
        if phi >= 0.85 and (has_v_pulse or signal_strength > 0.8):
             is_phi_resonance = True
             
        # [Phase 50] God-Mode Reversal & Resonance Bypass
        is_god_mode_phi = False
        if (phi < 0.2 and entropy > entropy_thresh) or is_god_mode:
            # [Phase Ω-Extreme] PHI-Symmetry Guard
            # Se mais de 60% dos agentes estão na direção OPOSTA ao sinal, o God-Mode é bloqueado.
            # Isso evita que o God-Mode valide um sinal "gaslit" por pesos de ignição.
            bull_count = len(quantum_state.metadata.get("bull_agents", []))
            bear_count = len(quantum_state.metadata.get("bear_agents", []))
            total_active = bull_count + bear_count
            
            is_god_mode_phi = True
            if OMEGA.get("phi_symmetry_guard_enabled", 0.0) > 0.5 and total_active > 10:
                swarm_bias = (bull_count - bear_count) / total_active
                # Se o sinal é BUY (positive) mas o enxame é BEAR (bias < -0.3)
                if (signal > 0 and swarm_bias < -0.3) or (signal < 0 and swarm_bias > 0.3):
                    is_god_mode_phi = False
                    self._log_cooldown("PHI_SYMMETRY_GUARD", f"🛡️ [PHI SYMMETRY GUARD] God-Mode BLOCKED. Swarm Bias {swarm_bias:+.2f} contradicts Signal {signal:+.2f}.", 30)
            
            if is_god_mode_phi:
                self._log_cooldown("GOD_MODE_REVERSAL_GATE", f"👹 [GOD-MODE REVERSAL] — High Entropy Panic/God Candidate (Φ={phi:.2f}, E={entropy:.2f}). Bypassing Incoherence Veto.", 30, level="omega")

        # ═══ VETO 03: SYSTEM INCOHERENCE (PHI) ═══
        phi_threshold = dynamic_phi_min # Use the dynamically calculated phi_min
        
        # [Phase 50] Resonance Bypass
        if is_phi_resonance:
            phi_threshold = 0.01 # Near-zero threshold for resonance
        
        # [Phase Ω-Apocalypse] Hardened Ignition Floor
        # Se houver ignição mas a entropia for alta, exigimos Φ mais robusto
        if has_ignition:
            if entropy > 0.85:
                phi_threshold = max(phi_threshold, 0.15)
            else:
                phi_threshold = max(phi_threshold, 0.08)
            
        # [Phase 50] God-Mode Reversal & Resonance Bypass
        is_ricci_attractor = quantum_state.metadata.get("ricci_attractor", False)
        
        if phi < phi_threshold and not (is_god_mode_phi or has_exhaustion_sovereignty or is_tec_sovereign or is_ricci_attractor or is_v_pulse_recovery): # PhD-7: Ricci Attractor bypasses Φ-Gate
            self._log_cooldown("PHI_VETO", f"⚠️ VETO: SYSTEM_INCOHERENCE (Φ={phi:.4f} < {phi_threshold:.4f} | TEC={is_tec_sovereign} | RICCI={is_ricci_attractor})", 60)
            return self._wait("INCOHERENCE_VETO")

        # ═══ VETO 04: CHAOS SHIELD ═══
        chaos_regime = regime_state.current.value == "HIGH_VOL_CHAOS"
        if not is_tec_sovereign and chaos_regime:
            self._log_cooldown("CHAOS_VETO", "🛡️ VETO: CHAOS_SHIELD (Market dynamics is too unstable)", 30)
            return self._wait("CHAOS_VETO")
            
        # ═══ VETO 04.5: INFORMATION ENTROPIC VACUUM (Ph.D. Level) ═══
        # Se estamos em drift e a entropia é baixíssima com 0 inércia = Robôs negociando com robôs
        is_drifting = regime_state.current.value in ["DRIFTING_BEAR", "DRIFTING_BULL", "LOW_LIQUIDITY"]
        # [Phase Ω-PhD-7] Geodesic Flow bypasses Vacuum: Fluxo laminar programático é legítimo.
        # [Phase Ω-Aethel] Topological Protection Bypass
        is_topologically_protected = any(s.agent_name in ["ChernSimonsTopological", "BraidTopology"] and abs(s.signal) > 0.8 for s in agent_signals)
        
        # [Phase Ω-PhD-15] Coherence-Based Vacuum Bypass
        # Se o enxame está em harmonia (Coherence > 0.6) e bem integrado (Phi > 0.3), 
        # confiamos na entrada mesmo com baixa entropia/volatilidade.
        is_consensus_clear = coherence > 0.60 and phi > 0.30
        # [Ω-RECALIBRATION-3.0] Bypass VACUUM if bear/bull consensus is overwhelming (>65%)
        bear_ratio = len(quantum_state.metadata.get("bear_agents", [])) / max(1, len(quantum_state.metadata.get("bear_agents", [])) + len(quantum_state.metadata.get("bull_agents", [])))
        is_overwhelming_consensus = bear_ratio > 0.65 or bear_ratio < 0.35
        if is_drifting and entropy < 0.45 and abs(snapshot.metadata.get("tick_velocity", 0.0)) < 5.0 and not is_god_mode and not (is_geodesic_flow or is_topologically_protected or is_consensus_clear or is_overwhelming_consensus):
            self._log_cooldown("VACUUM_VETO", f"🌌 VETO: ENTROPIC_VACUUM (Drift + Low Entropy {entropy:.2f} + No Inertia + Φ={phi:.2f} < 0.25). Avoiding chop.", 60)
            return self._wait("ENTROPIC_VACUUM_VETO")
        elif is_overwhelming_consensus and is_drifting and entropy < 0.45:
            self._log_cooldown("VACUUM_CONSENSUS_BEAR", f"⚡ [Ω-BEAR GRIND BYPASS] Overwhelming consensus ({bear_ratio:.0%} bear). Low entropy = steady grind, not chop.", 60, level="omega")
        elif is_consensus_clear and is_drifting and entropy < 0.45:
             self._log_cooldown("VACUUM_CONSENSUS", f"☄️ [Ω-CONSCIOUSNESS BYPASS] Bypassing Entropic Vacuum via High Coherence ({coherence:.2%}).", 60, level="omega")
        elif (is_geodesic_flow or is_topologically_protected) and is_drifting and entropy < 0.45:
            reason = "Geodesic Flow" if is_geodesic_flow else "Topological Protection"
            self._log_cooldown("VACUUM_GEODESIC", f"☄️ [Ω-GEODESIC VACUUM] Bypassing Entropic Vacuum via {reason} (Ent={entropy:.2f}).", 60, level="omega")

        # ═══ VETO 04.6: PHI IGNORANCE (Soberania do Presente) ═══
        # Se Φ é baixíssimo
        # [PHASE Ω-STABILITY] Enhanced Phi Gates by Regime
        phi_gate = OMEGA.get("phi_min_threshold", 0.15)
        
        # Regimes de transição/rasteiros exigem Φ mais alto p/ evitar traps
        regime = regime_state.current
        phi_score = quantum_state.phi
        if regime in [MarketRegime.CREEPING_BULL, MarketRegime.DRIFTING_BEAR]:
            # [Phase Ω-PhD-2] Apply resonance scaling to the legacy gate as well
            phi_gate = max(phi_gate, 0.20)
            if self.entropy_bridge_active:
                phi_gate *= 0.10
                
        # [Phase Ω-PhD-8] Kolmogorov Sync for legacy gate
        if is_programmatic:
            phi_gate *= 0.50
            
        elif regime in [MarketRegime.HIGH_VOL_CHAOS, MarketRegime.LIQUIDITY_HUNT]:
            phi_gate = max(phi_gate, 0.50)
            
        if not (is_tec_sovereign or has_exhaustion_sovereignty or is_ricci_attractor or is_v_pulse_recovery) and phi_score < (phi_gate - 1e-6):
            return self._wait(f"SIGNAL_FRAGILE(Φ={phi_score:.2f} < {phi_gate:.2f})")
        
        phi_ignore = OMEGA.get("phi_ignorance_threshold", 0.15)
        if phi < phi_ignore and has_v_pulse and not is_phi_resonance:
             self._log_cooldown("PHI_IGNORANCE", f"⚡ [SOBERANIA DO PRESENTE] Φ={phi:.2f} is weak but V-Pulse is active. Bypassing PHI threshold for 3 candles.", 30, level="omega")
             phi_threshold = 0.01 # Bypassa o veto de PHI no TrinityCore
            
        # ═══ VETO PREDITIVO (JAVA PNL PREDICTOR) ═══
        if pnl_pred == "IMPOSSIBLE:NEGATIVE_EXPECTANCY":
            # [Phase Ω-PhD-2] Entropy Bridge bypasses PnL Expectancy check
            phi_sovereign = phi >= 0.20 or is_tec_sovereign
            if not (phi_sovereign or self.entropy_bridge_active) and quantum_state.confidence < 0.95:
                return self._wait("JAVA_PNL_VETO (Negative Expectancy Detected)")
            elif phi_sovereign:
                self._log_cooldown("PNL_OVERRIDE", f"🧬 [Ω-PNL OVERRIDE] Bypassing negative expectancy via Consciousness Sovereignty (Φ={phi:.2f}).", 60, level="omega")

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

        # ═══ CALCULAR SL/TP (Phase 52.7: Structural Anchoring) ═══
        tick = snapshot.tick
        if tick is None:
            return self._wait("NO_TICK_DATA")
 
        price = tick["ask"] if action == Action.BUY else tick["bid"]
        
        # [Phase 52.7] Usar ATR M1 para maior agilidade em Scalps
        atr_m1_list = snapshot.indicators.get("M1_atr_14", [0.0])
        atr_m1 = float(atr_m1_list[-1]) if len(atr_m1_list) > 0 else 0.0
        atr_m5 = self._get_current_atr(snapshot)
        
        # Referência de volatilidade rápida
        fast_atr = atr_m1 if atr_m1 > 0 else (atr_m5 * 0.5)
        if fast_atr <= 0:
            return self._wait("ATR_ZERO")
 
        sl_mult = OMEGA.get("stop_loss_atr_mult", 0.45)
        
        # Buscar extremos estruturais (Fractais de M1)
        candles_m1 = snapshot.candles.get("M1")
        m1_highs = np.array(candles_m1["high"], dtype=np.float64)[-10:] if candles_m1 else []
        m1_lows = np.array(candles_m1["low"], dtype=np.float64)[-10:] if candles_m1 else []
        
        # [Phase 52.8] Dynamic RR Scaling (The "Long Trade" Hunter)
        # Em tendências ou ignições, buscamos alvos muito mais longos
        rr_mult = 1.1 # Default Scalp
        if regime_state.current.value in ["TRENDING_BULL", "TRENDING_BEAR"]:
            rr_mult = 2.5 # Modo Trend
        elif regime_state.current.value in ["DRIFTING_BEAR", "DRIFTING_BULL", "CREEPING_BULL", "CREEPING_BEAR"]:
            rr_mult = 2.0 # Modo Drift/Creeping (Stretch TP for higher RRR)
        elif regime_state.current.value in ["SQUEEZE", "SQUEEZE_BUILDUP", "IGNITION_BULL", "IGNITION_BEAR"]:
            rr_mult = 3.0 # Modo Explosão (Breakout)
        
        # Ajuste extra por Consciência (Φ)
        if phi > 0.25:
            rr_mult += (phi * 0.5) # Mais integração = mais ambição
            
        # [Phase Ω-Omniscience] Quantum Entanglement TP Boost
        agent_reasons = str(q_meta.get("agent_signals", ""))
        if "ENTANGLEMENT" in agent_reasons:
            rr_mult += 1.5 # Macro alignment justifies huge targets
            self._log_cooldown("ENTANGLEMENT_BOOST", f"🌌 [OMNISCIENCE] Macro Entanglement Detected. TP Multiplier boosted to {rr_mult:.2f}x", 60)
            
        # [Phase 52: FAT-TAIL / LEVY FLIGHT]
        # Aqui abolimos o "scalp" e adotamos a assimetria brutal
        is_fat_tail = "LEVY_FLIGHT_DETECTED" in agent_reasons or "SINGULARITY_COLLAPSE" in agent_reasons
        if is_fat_tail or is_god_mode:
            # [SCALP] Reduced fat_tail_base from 10.0 to 4.5
            fat_tail_base = OMEGA.get("fat_tail_rr_mult", 4.5)
            # Aciona a multiplicacao extrema
            rr_mult = fat_tail_base + (phi * 1.5) # [SCALP] Reduced phi mult from 2.5 to 1.5
            self._log_cooldown("FAT_TAIL_HARVESTING", f"☄️ [FAT-TAIL HARVESTING] Levy Flight / Singularity Detectada. Expandindo TP Scale para {rr_mult:.2f}x", 60, level="omega")

        # [Phase 52.7] Liquidity-Shield: Regime-Aware Structural Buffers
        is_transition_regime = regime_state.current.value in ["CREEPING_BULL", "CREEPING_BEAR", "DRIFTING_BULL", "DRIFTING_BEAR", "HIGH_VOL_CHAOS", "LIQUIDATION_CASCADE"]
        
        # Buffer de liquidez: em regimes rasteiros/caóticos, precisamos de mais "respiro"
        struct_buffer = max(35 * point_val, 0.45 * fast_atr) if is_transition_regime else (15 * point_val)
        
        # SL Floor de segurança: não permite stop muito curto em regimes de "wick hunt"
        min_sl_dist = 0.9 * fast_atr if is_transition_regime else (0.5 * fast_atr)

        if action == Action.BUY:
            # SL: O maior entre (Mínima dos últimos 10 candles - buffer) e (Preço - sl_mult * Fast_ATR)
            # Nota: para BUY, subtraímos o buffer da mínima
            if isinstance(m1_lows, (np.ndarray, list)) and len(m1_lows) > 0:
                structural_sl = float(np.min(m1_lows)) - struct_buffer
            else:
                structural_sl = float(price - fast_atr * sl_mult)
            
            # Garantir distanciamento mínimo de segurança (Resilience Floor)
            safe_sl_floor = float(price - min_sl_dist)
            stop_loss = min(structural_sl, safe_sl_floor) 
            
            # [PhD-Log] Confirming Action again for final checks
            action = Action.BUY
            
            # TP Dinâmico (Phase 52.8)
            risk_dist = abs(price - stop_loss)
            
            # [PHASE Ω-SCALP] TP Stretch Protection:
            # Se o SL é largo demais (>2 ATR), limitamos o multiplicador de RR para o TP não ficar inalcançável.
            effective_rr = rr_mult
            if risk_dist > 2.0 * fast_atr:
                effective_rr = min(rr_mult, 1.25)
                self._log_cooldown("TP_STRETCH_PROTECT", f"🛡️ [TP STRETCH] SL is too wide ({risk_dist/fast_atr:.1f} ATR). Capping RR to {effective_rr}x", 60)

            tp_scalar = OMEGA.get("tp_placement_scalar", 0.97)
            take_profit = price + (risk_dist * effective_rr * tp_scalar)
        
        elif action == Action.SELL:
            # SL: O menor entre (Máxima dos últimos 10 candles + buffer) e (Preço + sl_mult * Fast_ATR)
            if isinstance(m1_highs, (np.ndarray, list)) and len(m1_highs) > 0:
                structural_sl = float(np.max(m1_highs)) + struct_buffer
            else:
                structural_sl = float(price + fast_atr * sl_mult)
                
            # Garantir distanciamento mínimo de segurança (Resilience Floor)
            safe_sl_floor = float(price + min_sl_dist)
            stop_loss = max(structural_sl, safe_sl_floor)
            
            # TP Dinâmico (Phase 52.8)
            risk_dist = abs(price - stop_loss)
            
            # [PHASE Ω-SCALP] TP Stretch Protection:
            # Se o SL é largo demais (>2 ATR), limitamos o multiplicador de RR para o TP não ficar inalcançável.
            effective_rr = rr_mult
            if risk_dist > 2.0 * fast_atr:
                effective_rr = min(rr_mult, 1.25)
                self._log_cooldown("TP_STRETCH_PROTECT", f"🛡️ [TP STRETCH] SL is too wide ({risk_dist/fast_atr:.1f} ATR). Capping RR to {effective_rr}x", 60)

            tp_scalar = OMEGA.get("tp_placement_scalar", 0.97)
            take_profit = price - (risk_dist * effective_rr * tp_scalar)
        
        else:
            # Se a ação não for BUY nem SELL (ex: WAIT), inicializamos com valores neutros para evitar UnboundLocalError
            # e retornamos o wait state se necessário, ou deixamos o RR check veta-lo
            stop_loss = price 
            take_profit = price
            if action != Action.WAIT:
                return self._wait("UNEXPECTED_ACTION_TYPE")

        # [Phase 52.8] BTC_STRIKE_CAP: Alargado massivamente para permitir corridas colossais
        max_dist_tp = 1500.0
        max_dist_sl = 280.0 # Stop encurtado p/ reduzir drawdown (Ω-Guard)

        if abs(float(price) - float(take_profit)) > float(max_dist_tp):
            take_profit = float(price) + (float(max_dist_tp) if action == Action.BUY else -float(max_dist_tp))
        if abs(float(price) - float(stop_loss)) > float(max_dist_sl):
            stop_loss = float(price) - (float(max_dist_sl) if action == Action.BUY else -float(max_dist_sl))
        # ═══ RISK/REWARD CHECK ═══
        risk = abs(float(price) - float(stop_loss))
        reward = abs(float(take_profit) - float(price))
        rr_ratio = reward / risk if float(risk) > 0 else 0

        # [Phase Ω-Resilience] Commission-Aware RR:
        # Check if reward covers commission + min profit target
        sym_info = snapshot.symbol_info
        point_val = sym_info.get("point", 1.0) if sym_info else 1.0
        contract_size = sym_info.get("trade_contract_size", 1.0) if sym_info else 1.0
        
        # [Phase 74] FTMO Alignment: Use safe baseline if metadata is missing
        comm_per_lot = snapshot.metadata.get("dynamic_commission_per_lot", snapshot.metadata.get("commission_per_lot", OMEGA.get("commission_per_lot", 50.0)))
        min_net_profit = OMEGA.get("min_profit_per_ticket", 80.0)
        
        # Profit in points needed to cover commission + target (assuming 1 lot for ratio check)
        # [Phase 52.6] Calibração de Alvo Realista:
        # Se Φ é alto (>0.3), relaxamos o piso de lucro p/ não perder movimentos rápidos.
        dynamic_min_profit = min_net_profit
        
        # [Phase Ω-EPISTEMIC SINGULARITY] Dynamic Alpha Floor
        # Discount based on Phi and V-Pulse
        if phi > 0.3:
            dynamic_min_profit *= 0.8 # 20% discount
            
        if has_v_pulse:
            alpha_relaxation = OMEGA.get("v_pulse_alpha_relaxation", 0.50)
            dynamic_min_profit *= alpha_relaxation
            self._log_cooldown("V_PULSE_ALPHA", f"⚡ [V-PULSE ALPHA] Reducing min net profit target by { (1-alpha_relaxation)*100:.0f}% due to ignition.", 30, level="omega")

        # [Phase PhD] Quantum Tunneling Alpha Sovereignty
        # Se o agente de tunelamento detectou fuga de liquidez, o lucro mínimo cai drasticamente
        is_tunneling = "TUNNELING" in agent_reasons
        if is_tunneling:
             dynamic_min_profit = 10.0 # Alpha Floor de sobrevivência apenas
             self._log_cooldown("TUNNELING_ALPHA", "🍩 [TUNNELING ALPHA] Liquidity leakage detected. Minimal profit floor enabled.", 30, level="omega")

        # O divisor era contract_size que na FTMO BTCUSD costuma vir zuado (ex: 1.0 ou 100.0)
        # Vamos assumir que 1 lote = 1 bitcoin de variação direta no PnL.
        min_points_needed = (comm_per_lot + dynamic_min_profit)
        
        if reward < min_points_needed:
            # Se for God-Mode ou Ressonância, engolimos o trade mesmo assim.
            if is_god_mode or is_phi_resonance or is_tunneling:
                 self._log_cooldown("REWARD_BYPASS", f"👹 [OMEGA IGNITION] Bypassing REWARD_TOO_SMALL ({reward:.2f} < {min_points_needed:.2f})", 30, level="omega")
            else:
                # [Phase Ω-Apocalypse] TP Elastic Expansion
                # If the ATR-based TP is too small to cover fees, we stretch it to meet the floor.
                expanded_tp_points = min_points_needed + (3.0 * point_val) # Tighter safety buffer
                
                # [Ω-ADAPTIVE] Stretch cap increases from 5x to 10x for HFT/Low-Vol scalping
                max_stretch_mult = OMEGA.get("max_tp_stretch_atr", 10.0)
                max_stretch = fast_atr * max_stretch_mult
                
                if expanded_tp_points < max_stretch:
                    reward = expanded_tp_points
                    if action == Action.BUY:
                        take_profit = price + reward
                    else:
                        take_profit = price - reward
                    
                    rr_ratio = reward / risk if risk > 0 else 0
                    self._log_cooldown("RR_ADJUST", f"⚖️ RR ADJUST: Expanding target to {reward:.2f} points p/ Alpha Floor (Stretch={max_stretch_mult}x ATR)", 60, level="info")
                else:
                    # [Phase PhD] Final Strike Bypass: Se temos colapso de entropia ou vácuo topológico, o lucro é secundário à certeza.
                    is_phd_strike = "TOPOLOGICAL" in agent_reasons or "ENTROPY_COLLAPSE" in agent_reasons
                    # [SCALP] Extreme Scaling Mode: Bypassa Alpha Floor se Phi é saudável ou há V-Pulse
                    # Relaxed Phi requirement from 0.25 to 0.15 for aggressive scalp
                    is_aggressive_scalp = (phi > 0.15 and coherence > 0.35) or has_v_pulse or is_tunneling
                    
                    # [Ω-MICRO-ALPHA] If Reward covers fees, we take it if Phi is high
                    is_micro_alpha = reward > (comm_per_lot * 1.1) and phi > 0.20
                    
                    if is_phd_strike or is_aggressive_scalp or is_micro_alpha:
                         reason = "PHD_STRIKE" if is_phd_strike else "AGGRESSIVE_SCALP" if is_aggressive_scalp else "MICRO_ALPHA"
                         self._log_cooldown(f"{reason}_BYPASS", f"🎯 [{reason}] Bypassing Alpha Floor (R={reward:.2f} < Min={min_points_needed:.2f} | Φ={phi:.2f})", 30, level="omega")
                    else:
                        return self._wait(f"REWARD_TOO_SMALL_FOR_ALPHA (Reward {reward:.2f} < Min {min_points_needed:.2f} & ATR Block {max_stretch:.2f})")

        min_rr = OMEGA.get("trinity_min_rr_ratio", 1.15)
        
        # [Phase 50] Resonance RR Relaxation
        if is_phi_resonance:
            min_rr *= 0.7  # Relax RR for resonance ignition
            
        if regime_state.current.value in ["LOW_LIQUIDITY", "UNKNOWN", "CHOPPY", "SQUEEZE_BUILDUP", "DRIFTING_BEAR", "DRIFTING_BULL"]:
             # Maker execution (limit_mode) captures spread, making low RR trades profitable.
             # In drifting regimes, we accept even lower RR if Phi is healthy
             phi_factor = 0.5 if phi > 0.20 else 0.8
             # [Phase Ω-PhD-7] Geodesic Flow accepts even lower RR (Scalp asimétrico)
             if is_geodesic_flow: phi_factor = 0.35
             min_rr = 0.35 if limit_mode else (min_rr * phi_factor)

        # [Phase 51] God-Mode RR Rationale
        if is_god_mode:
            min_rr = OMEGA.get("god_mode_rr_min", 0.35)
            self._log_cooldown("GOD_MODE_RR", f"👹 [GOD-MODE RR] Bypassing RR thresholds for panic absorption (Min RR: {min_rr:.2f})", 30, level="omega")

        # [Phase 52] Divergence-Aware RR Adjustment
        # Se agentes 'Leading' divergem da decisão final, aumentamos a exigência de RR.
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
            # [Phase 52 Refinement] Cap at 1.8 to avoid excessive paralysis
            # Divergence should demand better RRR, but not impossible targets.
            min_rr = min(1.8, min_rr * 1.25) 
            self._log_cooldown("RR_DIVERGENCE", f"⚠️ RR_DIVERGENCE: Líderes desconfiados. Elevando Min RR para {min_rr:.2f}", 60)

        if rr_ratio < (min_rr - 1e-6):
            return self._wait(f"RR_RATIO_LOW({rr_ratio:.2f} < {min_rr:.2f})")

        # [Phase 48] Alpha Integrity: Commission Reward Ratio Gate
        # Reward in $ / Estimated Commission must be > threshold
        if comm_per_lot > 0:
            # Actual reward in $ (for 1 lot)
            reward_in_dollars = reward * contract_size
            comm_reward_ratio = reward_in_dollars / comm_per_lot
            min_comm_ratio = OMEGA.get("min_commission_reward_ratio", 1.5)
            
            # [Phase 52.10] Maker Neutralization
            # Ordens limite não pagam o "spread cego" da corretora, elas embolsam o spread.
            # Portanto, o peso da comissão bruta sobre o alvo é mitigado.
            if limit_mode:
                min_comm_ratio = 0.0 # Desliga o veto de comissão para Maker
            
            if comm_reward_ratio < min_comm_ratio:
                return self._wait(f"COMM_REWARD_RATIO_LOW({comm_reward_ratio:.2f} < {min_comm_ratio:.2f})")

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
                self._log_cooldown("ALPHA_SURGE", f"🚀 [ALPHA SURGE] Relaxing kinematic threshold to {kinematic_atr_mult:.2f} (x{relaxation})", 30, level="omega")
            
            if action == Action.BUY:
                local_min = np.min(closures[-5:])
                distance = last_close - local_min
                if distance > atr_m5 * kinematic_atr_mult:  
                    return self._wait(f"KINEMATIC_EXHAUSTION_BUY (Spike={distance:.1f} > {kinematic_atr_mult}xATR={atr_m5*kinematic_atr_mult:.1f}) | TOP_HUNT_RISK")
            elif action == Action.SELL:
                local_max = np.max(closures[-5:])
                distance = local_max - last_close
                if distance > atr_m5 * kinematic_atr_mult:
                    return self._wait(f"KINEMATIC_EXHAUSTION_SELL (Spike={distance:.1f} > {kinematic_atr_mult}xATR={atr_m5*kinematic_atr_mult:.1f}) | BOTTOM_HUNT_RISK")

        # [Phase 52] VETO 7: KINEMATIC DECOUPLING (Vácuo de Liquidez)
        # Se estamos comprando no topo de um spike parabólico longe da média
        ema_9 = snapshot.indicators.get("M5_ema_9")
        if ema_9 is not None and len(ema_9) > 0 and atr > 0:
            dist_from_mean = (snapshot.price - ema_9[-1]) / atr
            
            # PhD Immunity: Se agentes de campo ou escala estão em ressonância, ignoramos o estiramento
            phd_protection = any(s.agent_name in ["RGScalingInvariance", "ChernSimonsTopological", "BraidTopology"] and abs(s.signal) > 0.85 for s in agent_signals)
            # Cascade Bypass: Em quedas verticais ou drifts estáveis, o estiramento é o motor do lucro
            is_cascade = regime_state.current.value in ["LIQUIDATION_CASCADE", "DRIFTING_BEAR", "DRIFTING_BULL"]
            
            # Se preço > 2 ATRs da média E sinal é BUY -> Perigo de Blow-off
            if action == Action.BUY and dist_from_mean > 2.0 and not (phd_protection or is_cascade):
                # Se não houver uma ignição genuína comprovada por volume institucional
                v_ratio_list = snapshot.indicators.get("M5_volume_ratio", [1.0])
                vol_ratio = v_ratio_list[-1] if v_ratio_list is not None and len(v_ratio_list) > 0 else 1.0
                if vol_ratio < 3.0: # Volume não justifica o estiramento
                    return self._wait(f"KINEMATIC_DECOUPLING_BUY (Price too far from mean: {dist_from_mean:.1f}xATR)")
            # Simétrico para SELL
            elif action == Action.SELL and dist_from_mean < -2.0 and not (phd_protection or is_cascade):
                v_ratio_list = snapshot.indicators.get("M5_volume_ratio", [1.0])
                vol_ratio = v_ratio_list[-1] if v_ratio_list is not None and len(v_ratio_list) > 0 else 1.0
                if vol_ratio < 3.0:
                    return self._wait(f"KINEMATIC_DECOUPLING_SELL (Price too far from mean: {dist_from_mean:.1f}xATR)")

        # [Phase 52] VETO 8: BLOW-OFF CLIMAX (Proteção contra Exaustão)
        q_meta = quantum_state.metadata
        agent_reasons = str(q_meta.get("agent_signals", ""))
        if "BLOW_OFF_CLIMAX" in agent_reasons or "REDLINE_VETO" in agent_reasons:
            return self._wait("BLOW_OFF_EXHAUSTION_DETECTED (Reversal Imminent)")

        # [Phase 52] VETO 9: HORIZONTAL RESISTANCE/SUPPORT (Double/Triple Top/Bottom)
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
                                    # [Phase Ω-Eschaton] Ignorar veto se sinal é avassalador ou tem ignição
                                    bypass_thresh = 0.15 if "CREEPING" in regime_state.current.value else 0.40
                                    # [Phase Ω-Thermodynamic] Ruin Velocity Bypass
                                    if abs(quantum_state.raw_signal) > 0.50:
                                        pass # Muro de contenção irrelevante perante a desintegração física
                                    elif not (has_ignition or is_god_mode or is_ghost_sweep or abs(quantum_state.raw_signal) > bypass_thresh):
                                        return self._wait(f"HORIZONTAL_RESISTANCE_VETO (Level={peak:.0f}, Peaks={matches})")
        
        # [Phase 52.11] Simétrico: Suporte Horizontal para SELL
        elif action == Action.SELL:
            for tf in ["M1", "M5"]:
                candles = snapshot.candles.get(tf)
                if candles and len(candles["low"]) > 50:
                    lows = np.array(candles["low"], dtype=np.float64)
                    recent_valleys = []
                    # Detectar fundos (fractal 5)
                    for i in range(2, len(lows) - 5):
                        if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
                           lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                            recent_valleys.append(lows[i])
                    
                    if recent_valleys:
                        for valley in recent_valleys[-10:]:
                            dist_to_valley = (snapshot.price - valley) / snapshot.price * 100
                            # Se o preço está caindo e encostando num fundo forte
                            if abs(dist_to_valley) < 0.08:
                                matches = sum(1 for v in recent_valleys if abs((v - valley)/valley*100) < 0.1)
                                if matches >= 2: # Fundo Duplo ou Triplo
                                     bypass_thresh = 0.15 if "CREEPING" in regime_state.current.value else 0.40

                                     # [PHASE Ω-SINGULARITY] Quantum Tunneling & Event Horizon Bypass
                                     is_drifting_bear = "DRIFTING_BEAR" in regime_state.current.value or "LIQUIDATION" in regime_state.current.value
                                     is_event_horizon = is_drifting_bear and matches >= 4

                                     # [Phase Ω-Thermodynamic] Ruin Velocity Bypass
                                     if abs(quantum_state.raw_signal) > 0.50:
                                         pass # A gravidade quântica engolirá o suporte
                                     elif is_event_horizon:
                                         pass # Bypass absoluto: A barreira fadigou e o horizonte de eventos atrai o preço (Tunneling)
                                     elif not (has_ignition or is_god_mode or is_ghost_sweep or abs(quantum_state.raw_signal) > bypass_thresh):
                                         return self._wait(f"HORIZONTAL_SUPPORT_VETO (Level={valley:.0f}, Valleys={matches})")
        # [Phase Ω-Apocalypse] VETO 9.5: LIQUIDITY SWEEP (V-Reversal Trap)
        # Prevents selling the exact bottom of a liquidity hunt (wick) or buying the exact top.
        candles_m1 = snapshot.candles.get("M1")
        if candles_m1 and len(candles_m1["close"]) >= 3:
            c0, c1 = candles_m1["close"][-1], candles_m1["close"][-2]
            o0, o1 = candles_m1["open"][-1], candles_m1["open"][-2]
            h0, l0 = candles_m1["high"][-1], candles_m1["low"][-1]
            
            # Condição de Venda na mínima (Bear Trap)
            if action == Action.SELL and not (has_exhaustion_sovereignty or is_tec_sovereign):
                # Se o preço caiu forte mas já formou um pavio enorme de absorção
                if c0 > l0 + (atr_m5 * 0.4): # Pavio inferior de 40% do ATR M5
                    return self._wait(f"LIQUIDITY_SWEEP_VETO (Bear Trap: Wick rejected {c0 - l0:.1f} points)")
            
            # Condição de Compra na máxima (Bull Trap)
            elif action == Action.BUY and not (has_exhaustion_sovereignty or is_tec_sovereign):
                # Se o preço subiu forte mas já formou um pavio superior enorme
                if c0 < h0 - (atr_m5 * 0.4):
                    return self._wait(f"LIQUIDITY_SWEEP_VETO (Bull Trap: Wick rejected {h0 - c0:.1f} points)")

        # [Phase 52.4] VETO 10: ELITE DIVERGENCE (Meritocracia de Ideias)
        # Identificamos os 5 agentes com maior peso (Elite), excluindo puros vetos (TCellImmunity)
        directional_elites = [a for a in quantum_state.agent_signals if a.agent_name not in ["TCellImmunity", "KripkeSemantics", "IntuitionisticLogic"]]
        elite_agents = sorted(directional_elites, key=lambda x: x.weight, reverse=True)[:5]
        if elite_agents and not (has_exhaustion_sovereignty or is_tec_sovereign):
            elite_direction_sum = float(sum(np.sign(a.signal) for a in elite_agents))
            swarm_direction = float(np.sign(signal)) # 'signal' is already defined as collapsed_signal
            
            # Se a elite está na direção oposta OU neutra (0), enquanto a manada grita para um lado
            if (swarm_direction > 0 and elite_direction_sum <= 0) or \
               (swarm_direction < 0 and elite_direction_sum >= 0):
                self._veto_count += 1
                return self._wait(f"ELITE_DIVERGENCE_VETO (Swarm={swarm_direction}, Elite_Sum={elite_direction_sum})")

        # [Phase Ω-Apocalypse] VETO 10.5: MOMENTUM EXHAUSTION DIVERGENCE
        # PhD Immunity: Se agentes Omega estão em consenso, ignoramos divergências visuais
        phd_names = ["RiemannianManifoldAgent", "InformationGeometryAgent", "QuantumSuperpositionAgent", "RGScalingInvariance", "BraidTopology"]
        phd_excited = any(s.agent_name in phd_names and abs(s.signal) > 0.7 for s in agent_signals)
        is_drifting = "DRIFTING" in regime_state.current.value
        
        if not (is_god_mode or is_tec_sovereign or phd_excited or is_drifting):
            momentum_bulls = [a for a in bulls if any(x in a for x in ["Velocity", "Momentum", "Aggressiveness", "Trend", "TemporalTrend"])]
            exhaustion_bears = [a for a in bears if any(x in a for x in ["Exhaustion", "BaitAndSwitch", "CandleAnatomy", "SRAgent", "ChartStructure", "LiquidityGraph", "IntentDecomposition", "BaitLayering", "StopHunter", "OrderBlock", "PremiumDiscount", "HarmonicResonance"])]
            
            # [Phase 52.13] Relaxed momentum condition to 2 agents to catch traps earlier
            if action == Action.BUY and len(momentum_bulls) >= 2 and len(exhaustion_bears) >= 2:
                bypass_thresh = 0.20 if "CREEPING" in regime_state.current.value else 0.50
                if abs(quantum_state.raw_signal) < bypass_thresh:
                    return self._wait(f"MOMENTUM_EXHAUSTION_VETO (Bullish velocity but structural rejection detected)")
            
            # Simétrico para SELL
            momentum_bears = [a for a in bears if any(x in a for x in ["Velocity", "Momentum", "Aggressiveness", "Trend", "TemporalTrend"])]
            exhaustion_bulls = [a for a in bulls if any(x in a for x in ["Exhaustion", "BaitAndSwitch", "CandleAnatomy", "SRAgent", "ChartStructure", "LiquidityGraph", "IntentDecomposition", "BaitLayering", "StopHunter", "OrderBlock", "PremiumDiscount", "HarmonicResonance"])]
            if action == Action.SELL and len(momentum_bears) >= 2 and len(exhaustion_bulls) >= 2:
                bypass_thresh = 0.20 if "CREEPING" in regime_state.current.value else 0.50
                if abs(quantum_state.raw_signal) < bypass_thresh:
                    return self._wait(f"MOMENTUM_EXHAUSTION_VETO (Bearish velocity but structural support detected)")

        # ═══ 4. MONTE CARLO VALIDATION ═══
        # Simula 5000 universos paralelos para validar o trade
        volatility_est = float(atr) / max(float(price), 1.0) * np.sqrt(252)  # Anualizar
        # [Phase 47] Drift Decoupling: Se houve ignição ou explosão de ticks, 
        # forçamos um drift agressivo para o Monte Carlo não ser pessimista.
        forced_drift = None
        tick_velocity = snapshot.metadata.get("tick_velocity", 0.0)
        has_ignition = snapshot.metadata.get("v_pulse_detected", False) or regime_state.v_pulse_detected
        
        if has_ignition or tick_velocity > 35.0:
            # Mu = sigma * 5.0 (Ito Acceleration)
            forced_drift = (float(atr) / max(float(price), 1.0)) * 5.0 * (1.0 if action == Action.BUY else -1.0)
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

            # [Phase Ω-Stability] Monte Carlo Persistence Filter
            # Stochastic noise in MC can cause flickering. We require the average EV of the last 3 cycles
            # to be positive, unless it's a lethal ignition or god mode.
            self._mc_ev_history.append(mc_result.expected_return)
            if len(self._mc_ev_history) > 3: self._mc_ev_history.pop(0)
            avg_mc_ev = sum(self._mc_ev_history) / len(self._mc_ev_history)

            is_drifting = "DRIFTING" in regime_state.current.value or "LIQUIDATION" in regime_state.current.value
            if mc_result.expected_return < 0 or (avg_mc_ev < 0 and len(self._mc_ev_history) >= 2):
                # Se o retorno esperado é negativo, a estatística diz que vamos perder dinheiro no longo prazo.
                # Só permitimos se for um sinal de exaustão extrema (God-Mode) ou Drift estável com consenso.
                if not is_god_mode and not (phi > 0.35 and abs(signal) > 0.50 and is_drifting):
                    if mc_result.expected_return < 0:
                        reason = f"MC_NEGATIVE_EV({mc_result.expected_return:.2f})"
                    else:
                        reason = f"MC_STABILITY_VETO(Avg_EV={avg_mc_ev:.2f})"
                    return self._wait(f"{reason} - Estatística desfavorável")

            # [Phase Ω-PhD-3] MC-Score Floor
            # O mc_score pondera WP, EV e CVaR. Um valor < -0.25 indica um trade intrinsecamente "sujo".
            if mc_score < -0.25 and not is_god_mode:
                if not (phi > 0.40 and abs(signal) > 0.60 and is_drifting):
                    return self._wait(f"MC_SCORE_FLOOR_VETO ({mc_score:.3f} < -0.25) - High Probability of Chaos")

            # [Phase Ω-Resilience] Counter-Trend Phi Gate
            # Se a ordem é BUY em regime BEAR, ou SELL em regime BULL, exigimos Φ muito maior.
            is_counter_trend = (action == Action.BUY and "BEAR" in regime_state.current.value) or \
                               (action == Action.SELL and "BULL" in regime_state.current.value)
            
            if is_counter_trend and phi < 0.18:
                # [Phase Ω-Pleroma] Regime Decoupling: Se a inércia do mercado quebrou violentamente, 
                # o Regime_Detector (que é atrasado) está mentindo. Bypassamos o veto.
                if is_velocity_burst or abs(signal) > 0.40:
                    self._log_cooldown("COUNTER_TREND_BYPASS", f"🌪️ [REGIME DECOUPLING] Bypassing Counter-Trend Veto due to extreme velocity/signal.", 60, level="omega")
                else:
                    return self._wait(f"COUNTER_TREND_LOW_PHI (Φ={phi:.2f} < 0.18) - Sem integração p/ reversão")

            mc_reasoning = (
                f"MC[score={mc_score:+.3f} WP={mc_win_prob:.1%} "
                f"EV={mc_ev:+.2f} CVaR={mc_cvar:+.2f} "
                f"sim={mc_result.simulation_time_ms:.1f}ms]"
            )

            # VETO se Monte Carlo score é muito negativo
            mc_min_score = OMEGA.get("mc_min_score", -0.1)
            # [Phase Ω-Continuum] Bypass MC if consensus is incredibly strong, EXCEPT in low liquidity/choppy OR Counter-Trend
            if mc_score < mc_min_score:
                if (phi > 0.45 and abs(signal) > 0.65 and regime_state.current.value not in ["LOW_LIQUIDITY", "CHOPPY", "UNKNOWN"] and not is_counter_trend) or is_v_pulse_recovery:
                     self._log_cooldown("MC_BYPASS", f"🛡️ [MC BYPASS] { 'V-Pulse Sovereignty' if is_v_pulse_recovery else 'Extreme consensus' } overriding pessimistic MC (Score={mc_score:+.3f}).", 60, level="omega")
                else:
                    return self._wait(f"MC_SCORE_LOW({mc_score:+.3f}<{mc_min_score}) {mc_reasoning}")

            # [Phase Ω-Singularity] Relax win probability for Maker trades
            # Maker trades benefit from spread capture, allowing for ~40% Win Prob.
            mc_min_wp = OMEGA.get("mc_min_win_prob", 0.45)
            if limit_mode:
                mc_min_wp = 0.40
                
            if mc_win_prob < mc_min_wp:
                # FIX: mc_result.expected_return instead of expected_value
                mc_ev_val = getattr(mc_result, "expected_return", 0.0)
                # [Phase Ω-Thermodynamic] EV Asymmetry Bypass
                # [Phase Ω-Lockdown] Enforce requirements in UNKNOWN/CHOPPY
                is_safe_regime = regime_state.current.value not in ["LOW_LIQUIDITY", "CHOPPY", "UNKNOWN"]
                
                if mc_ev_val > 1.5 and mc_win_prob >= 0.32 and is_safe_regime:
                     pass # Fat-Tail Asymmetry: Assume WR<40% if Expected Value is massive.
                elif phi > 0.45 and abs(signal) > 0.65 and is_safe_regime and not is_counter_trend:
                     pass # Bypass
                else:
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
                "phi": phi,
                "is_god_mode": is_god_mode,
                "is_phi_resonance": is_phi_resonance,
                "is_tunneling": is_tunneling,
                "is_hydra": is_hydra_mode,
                "pnl_prediction": pnl_prediction,
                "entropy": entropy,
                "coherence": coherence,
                "rr_ratio": rr_ratio,
                "is_tec_active": tec_active,
                "tec_entropy": tec_entropy,
                "v_pulse_detected": has_v_pulse,
                "quantum_metadata": quantum_state.metadata if quantum_state else {},
                "bypassed_stale_regime": self.last_decision_bypassed
            }
        )
        
        # [Phase Ω-PhD-5] Transmit bypass flag to Risk Engine via snapshot
        if snapshot and hasattr(snapshot, 'metadata'):
            snapshot.metadata["bypassed_stale_regime"] = self.last_decision_bypassed

        self.last_decision_bypassed = False # Reset p/ próximo ciclo
        
        # [PHASE Ω-SINGULARITY] Injection of P-Brane Limit Logic
        limit_mode = OMEGA.get("limit_execution_mode", 0.0)
        is_limit_regime = regime_state.current.value in ["DRIFTING_BEAR", "DRIFTING_BULL", "LOW_LIQUIDITY", "SQUEEZE_BUILDUP"]
        
        if limit_mode > 0.5 and is_limit_regime:
            decision.limit_order = True
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
        # [Phase Ω-PhD-9] Quantum Tunneling Ghost Entry
        if decision.action != Action.WAIT:
            is_ghost_entry = QuantumTunnelingExecution.should_authorize_ghost_entry(snapshot, decision)
            if is_ghost_entry:
                decision.reasoning += " | [Ω-GHOST_ENTRY: TUNNELING AUTHORIZED]"
                decision.metadata["quantum_tunneling"] = True
                
        return decision

    def _check_vetos(self, snapshot, asi_state, regime_state, v_pulse_detected: bool = False, quantum_state: QuantumState = None) -> Optional[str]:
        """
        Sistema de veto — rejeita trades em condições de perigo.
        NÃO é paralisante: veta apenas em casos claros.
        """
        # [PHASE Ω-STRICT] SYNERGY VETO: Integrated Information Theory (Phi)
        if quantum_state and hasattr(quantum_state, 'phi'):
            phi_min = OMEGA.get("min_phi_threshold", 0.08)
            if quantum_state.phi < phi_min and not v_pulse_detected:
                if time.time() - self._log_cache.get("phi_veto", 0) > 60:
                    log.warning(f"🛡️ [SYNERGY VETO] Swarm Consciousness below threshold: Φ={quantum_state.phi:.3f} < {phi_min}")
                    self._log_cache["phi_veto"] = time.time()
                return f"SYNERGY_VETO (Φ={quantum_state.phi:.3f})"
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

        # 2. T-CELL IMMUNITY SYSTEM (Antigen Detection)
        if hasattr(self, 't_cell') and self.t_cell.is_infected(snapshot):
            # [Phase Ω-Burst] T-Cell Singularity Bypass
            # Se houver ignição letal, God-Mode ou Burst confirmado, ignoramos o veto imunitário
            # pois movimentos de alta energia frequentemente mimetizam padrões de falha.
            # Nota: O sinal/action são calculados no decide(), mas aqui temos acesso ao snapshot (velocity)
            tick_vel = snapshot.metadata.get("tick_velocity", 0.0)
            is_burst_vel = abs(tick_vel) > 15.0
            
            # Recalcular is_lethal_ignition localmente para o veto
            v_intensity = snapshot.metadata.get("v_pulse_capacitor", 0.0)
            lethal = (snapshot.metadata.get("v_pulse_detected", False) or regime_state.v_pulse_detected) and v_intensity > 0.8
            
            if lethal or snapshot.metadata.get("god_mode_active", False) or is_burst_vel:
                self._log_cooldown("TCELL_BYPASS", f"⚡ [T-CELL BYPASS] Ignoring pathogen match due to High-Energy Singularity (Vel={tick_vel:.1f})", 60)
                pass
            else:
                return "T-CELL_VETO (Pathogen detected)"

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
 
        # [Phase Ω-Apocalypse] Climax Velocity Guard
        candles_m1 = snapshot.candles.get("M1")
        if candles_m1 and len(candles_m1["close"]) >= 2:
            last_delta = abs(snapshot.price - candles_m1.get("close")[-2])
            atr_m5 = self._get_current_atr(snapshot)
            if atr_m5 > 0:
                climax_velocity = last_delta / atr_m5
                climax_thresh = OMEGA.get("climax_velocity_threshold", 2.2)
                if climax_velocity > climax_thresh and \
                   regime_state.current.value not in ["LIQUIDATION_CASCADE", "HIGH_VOL_CHAOS"]:
                    return f"CLIMAX_VELOCITY_VETO (Vel={climax_velocity:.2f} > {climax_thresh:.2f} ATR)"

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
            elif level == "debug":
                log.debug(message)
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
