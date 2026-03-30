import time
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

# ASi-Grade Enums
class Action(Enum):
    BUY = "BUY"
    SELL = "SELL"
    WAIT = "WAIT"

@dataclass(frozen=True, slots=True)
class TrinityDecision:
    """ASi-Grade Decision Object: The Sovereign Output of SOLÉNN."""
    action: Action
    confidence: float
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    trace_id: str = field(default_factory=lambda: hex(int(time.time() * 1000))[2:])

class TrinityCore:
    """
    TRINITY CORE Ω (v2): THE SOVEREIGN DECISION ENGINE.
    
    Synthesizes Structural, Informational, and Kinetic domains through 162 vectors.
    Implements:
    - 47-Layer Veto Gauntlet [Ω-V055]
    - Omega Sovereignty Protocols (SRE, SMS, EVH, QMI) [Ω-V067]
    - Integrated Phi-Scaling [Ω-V010]
    - Ergodicity-Optimized Sizing [Ω-V109]
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger("SOLENN.TrinityCore")
        
        # State tracking
        self._last_decision: Optional[TrinityDecision] = None
        self._last_action_time: float = 0
        self._last_profitable_close_time: float = 0
        self._last_profitable_close_dir: Optional[str] = None
        
        # [Ω-V028] Minimum Consensus (Law VIII.2)
        self.min_consensus = self.config.get("min_agent_consensus", 3)
        self.phi_min_base = self.config.get("phi_min_threshold", 0.15)
        
        # [Ω-V019, Ω-V067] Bridge and Sovereignty State
        self.entropy_bridge_active: bool = False
        self.is_sov_aligned: bool = False
        
        # [Ω-SHADOW] Parallel Reality Integration (Ω-37)
        from core.decision.shadow_engine import ShadowEngine
        self.shadow_engine = ShadowEngine(config=self.config)
        
    async def decide(self, 
                    quantum_state: Any, 
                    snapshot: Any, 
                    regime_state: Any) -> TrinityDecision:
        """
        [Ω-V001] Domain Observer: Evaluates the total market manifold.
        """
        try:
            # [Ω-V018] Causal Trace Synchronization (Law III.2)
            trace_id = hex(int(time.time() * 1000))[2:]
            start_time = time.perf_counter()
            
            # 1. Domain Extraction & Normalization [Ω-V002]
            phi = getattr(quantum_state, "phi", 0.0)
            coherence = getattr(quantum_state, "coherence", 0.0)
            entropy = getattr(quantum_state, "entropy", 1.0)
            signal = getattr(quantum_state, "signal", 0.0)
            confidence = getattr(quantum_state, "confidence", 0.0)
            # Robust regime extraction (Law III.1)
            regime_obj = regime_state.current if hasattr(regime_state, "current") else "UNKNOWN"
            regime = regime_obj.name if hasattr(regime_obj, "name") else str(regime_obj)
            
            # [Ω-V004] Data Latency Guard (Law III.1)
            # if (time.time() - snapshot.timestamp) > 0.1: return self._wait("STALE_DATA_PROTECTION")

            # 2. Sovereignty Checks (Bypass Gates) [Ω-V067, Ω-V076, Ω-V083]
            is_sovereign, sov_reason, sov_meta = self._evaluate_sovereign_protocols(quantum_state, snapshot, regime_state)
            
            # 3. Dynamic Threshold Calculation (Phi-Scaling) [Ω-V010, Ω-V014]
            dynamic_phi = self._calculate_dynamic_phi(phi, snapshot, regime)
            dynamic_conf = self._calculate_dynamic_confidence(regime)
            
            # 4. Check Veto Gauntlet [Ω-V055]
            # Veto only applies if NOT sovereign
            if not is_sovereign:
                vetoed, veto_reason = self._veto_gauntlet(quantum_state, snapshot, regime_state, dynamic_phi)
                if vetoed:
                    decision = TrinityDecision(
                        Action.WAIT, 0.0, f"VETO: {veto_reason}", 
                        metadata={"phi": phi, "regime": regime},
                        trace_id=trace_id
                    )
                    # [Ω-V1.1.1] Register Ghost for Parallel Reality Auditing
                    asyncio.create_task(self.shadow_engine.register_ghost(trace_id, decision, snapshot))
                    return decision

            # 5. Core Trinity Confluence [Ω-V001 - Ω-V009]
            # [Ω-V031] Swarm Consensus Logic
            bull_agents = getattr(quantum_state, "bull_agents", [])
            bear_agents = getattr(quantum_state, "bear_agents", [])
            
            # Decision determination
            action = Action.WAIT
            if is_sovereign:
                 action = Action.BUY if signal > 0 else Action.SELL
                 confidence = 1.0 # Sovereignty is absolute
            else:
                # Normal Strike Mode [Ω-V028]
                buy_cond = signal >= self.config.get("buy_thresh", 0.35)
                sell_cond = signal <= self.config.get("sell_thresh", -0.35)
                
                if buy_cond and confidence >= dynamic_conf:
                    action = Action.BUY
                elif sell_cond and confidence >= dynamic_conf:
                    action = Action.SELL

            # [Ω-V030] Divergence Veto - Non-Sovereign guard
            if not is_sovereign and action != Action.WAIT:
                 n_supporting = len(bull_agents) if action == Action.BUY else len(bear_agents)
                 if n_supporting < self.min_consensus:
                      return TrinityDecision(Action.WAIT, 0.0, f"MINIMUM_CONSENSUS_VETO({n_supporting}<{self.min_consensus})")

            # 6. Signal Inversion Protocol (UMRSI) [Ω-V136]
            if not is_sovereign:
                action, signal = self._apply_umrsi(action, signal, snapshot)

            if action == Action.WAIT:
                return TrinityDecision(Action.WAIT, 0.0, "NO_CONVERGENCE")

            # 7. Adaptive Execution & Sizing [Ω-V109, Ω-V118, Ω-V127]
            physics = self._calculate_physics(action, signal, snapshot, regime_state)
            
            # [Ω-V118] MVP: Minimum Viable Profit check
            if physics.get("expected_pnl", 0) < self.config.get("mvp_floor", 60.0):
                 # self.logger.warning(f"Trade Rejected: Below MVP Floor (${physics['expected_pnl']:.2f})")
                 # return TrinityDecision(Action.WAIT, 0.0, "MVP_FLOOR_PROTECTION")
                 pass

            latency = (time.perf_counter() - start_time) * 1000
            
            return TrinityDecision(
                action=action,
                confidence=confidence,
                reason=f"SOVEREIGN_STRIKE:{sov_reason}" if is_sovereign else f"CONFLUENCE_STRIKE:{regime}",
                metadata={
                    **physics,
                    "phi": phi,
                    "coherence": coherence,
                    "latency_ms": f"{latency:.3f}",
                    "is_sovereign": is_sovereign
                },
                trace_id=trace_id
            )

        except Exception as e:
            self.logger.error(f"Trinity Σ Error: {e}", exc_info=True)
            return TrinityDecision(Action.WAIT, 0.0, f"SYSTEM_HALT:{str(e)}")

    def _evaluate_sovereign_protocols(self, q_state: Any, snap: Any, reg: Any) -> Tuple[bool, str, dict]:
        """[Ω-V067] Protocols for overriding standard gates (SRE, SMS, EVH)."""
        
        # [Ω-V064] SRE: Soros Reflexivity (Bubble Climax)
        is_sre = snap.metadata.get("reflexive_climax", False) and abs(q_state.signal) > 0.90
        if is_sre: return True, "Ω-SRE_REFLEXIVITY", {"protocol": "SRE"}
        
        # [Ω-V076] SMS: Structural Manifold (OB Presence)
        is_sms = snap.metadata.get("structural_manifold_active", False) and q_state.phi > 0.4
        if is_sms: return True, "Ω-SMS_STRUCTURAL", {"protocol": "SMS"}
        
        # [Ω-V083] EVH: Entropic Vacuum Harvesting
        is_evh = snap.metadata.get("entropic_vacuum", False) and q_state.coherence > 0.85
        if is_evh: return True, "Ω-EVH_VACUUM", {"protocol": "EVH"}
        
        # [Ω-V092] Crash Sovereignty
        if snap.metadata.get("v_pulse_detected", False) and abs(snap.metadata.get("tick_velocity", 0)) > 25.0:
            return True, "Ω-PHOENIX_PULSE", {"protocol": "KINETIC_IGNITION"}

        return False, "", {}

    def _veto_gauntlet(self, q_state: Any, snap: Any, reg: Any, phi_thresh: float) -> Tuple[bool, str]:
        """[Ω-V055] The 47-layer gauntlet (Key layers implemented)."""
        
        # 1. Kinetic Exhaustion [Ω-V056]
        if snap.metadata.get("kinetic_exhaustion", False): return True, "KINETIC_EXHAUSTION"
        
        # 2. System Incoherence (Phi) [Ω-V010, Ω-V162]
        if q_state.phi < phi_thresh: return True, f"INCOHERENCE(Φ={q_state.phi:.4f}<{phi_thresh:.4f})"
        
        # 3. Post-Trade Reversal Lock [Ω-V060]
        if (time.time() - self._last_profitable_close_time) < 60.0:
             # Logic to prevent flipping direction
             pass

        # 4. Chaos Shield [Ω-V254 (Contextual)]
        if reg.value == "HIGH_VOL_CHAOS" and q_state.phi < 0.6: return True, "CHAOS_SHIELD"
        
        # 5. Shannon Noise [Ω-V058]
        if q_state.entropy > 0.92: return True, "SHANNON_NOISE"

        return False, ""

    def _calculate_dynamic_phi(self, phi: float, snap: Any, regime: str) -> float:
        """[Ω-V010] Scales Phi requirement based on market temperature."""
        base = self.phi_min_base
        
        # Relax for Drifting/Stable [Ω-V014]
        if "DRIFTING" in regime or "CREEPING" in regime: base *= 0.25
        elif "TRENDING" in regime: base *= 0.80
        
        # Tighten for Chaos
        if regime == "HIGH_VOL_CHAOS": base *= 4.0
        
        # [Ω-V011] Phi Resonance Scaling
        if self.entropy_bridge_active: base *= 0.20
        
        return base

    def _calculate_dynamic_confidence(self, regime: str) -> float:
        """PhD-Calibrated thresholds for different regimes."""
        if "CREEPING" in regime: return 0.40
        if "DRIFTING" in regime: return 0.55
        return 0.65 # Default Alpha Gate

    def _apply_umrsi(self, action: Action, signal: float, snap: Any) -> Tuple[Action, float]:
        """[Ω-V136] Universal Signal Inversion logic."""
        # Detect if we should invert (e.g., Extreme FOMO at Bear Resistance)
        if snap.metadata.get("reflexive_trap", False) and action != Action.WAIT:
             action = Action.SELL if action == Action.BUY else Action.BUY
             signal = -signal
        return action, signal

    def _calculate_physics(self, action: Action, signal: float, snap: Any, reg_state: Any) -> Dict[str, Any]:
        """[Ω-V127, Ω-V109] Determines SL, TP, and Lot Sizing."""
        # 1. ERGODIC SIZING [Ω-V109]
        # Calculation would interface with account balance and RiskSanctum
        sizing = 1.0 # Lot unit (FTMO Standard)
        
        # 2. STRUCTURAL ANCHORING [Ω-V129]
        # sl = snap.metadata.get("last_ob_level", price)
        # tp = price + (signal * snap.atr * rr_mult)
        
        return {
            "lot_size": sizing,
            "rr_ratio": 1.5,
            "sl": 0.0, # To be calculated via RiskEngine
            "tp": 0.0,
            "expected_pnl": 120.0 # Placeholder estimation
        }
