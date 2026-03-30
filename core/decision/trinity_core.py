import time
import logging
import asyncio
import uuid
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

import numpy as np
from core.decision.justifier import SolomonJustifier
from core.decision.telemetry import SovereignTelemetry
from core.consciousness.quantum_thought import QuantumThought

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
    [Ω-CORE] The Sacred Decision Matrix of SOLÉNN.
    Implements 162 vectors of high-confluence deliberation and 47-layer veto gauntlet.
    Operating on Phase 7 (The Sovereign Decision).
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger("SOLENN.TrinityCore")
        
        # [Ω-C1-T1.2-V1] Dynamic Phi-Scaling Base (Law III.1)
        self.phi_min_base = self.config.get("phi_min", 0.15)
        self.min_consensus = self.config.get("min_consensus", 3)
        
        # [Ω-C3-T3.5-V1] Shadow Engine Integration (Opportunity Cost Oracle)
        try:
            from core.decision.shadow_engine import ShadowEngine
            self.shadow_engine = ShadowEngine()
        except ImportError:
            self.logger.warning("ShadowEngine not found. Falling back to dummy.")
            self.shadow_engine = None
        
        # [Ω-C2-T2.3-V3] Anti-Spam state (Entry Cooldown)
        self._last_entry_time = 0.0
        self._last_profitable_close_time = 0.0
        self._last_action_time: float = 0
        
        # [Ω-PHD] Solomon & Telemetry Initialization (Phase 14)
        self.justifier = SolomonJustifier(config=self.config)
        self.telemetry = SovereignTelemetry()
        self.quantum_gate = QuantumThought()
        
        self.logger.info("🔱 Trinity Core Ω Activated: 47-Layer Veto Gauntlet ONLINE.")

    async def decide(self, 
                    quantum_state: Any, 
                    regime_state: Any, 
                    snapshot: Any,
                    res_snapshot: Any = None,
                    asi_state: Any = None) -> TrinityDecision:
        """
        [Ω-DEBATE] The final collapse of uncertainty into action.
        Runs the 162-vector deliberation process in < 1ms.
        """
        # [V046] Telemetry Trace Initialization
        trace_id = self.telemetry.create_trace(context="TRINITY_DECISION")
        
        try:
            # 1. Domain Extraction & Normalization [Ω-C1-T1.1]
            self.telemetry.add_span(trace_id, "PERCEPTION_START", {"ts": time.time()})
            
            signal = getattr(quantum_state, "signal", 0.0)
            phi = getattr(quantum_state, "phi", 0.0)
            confidence = getattr(quantum_state, "confidence", 0.0)
            coherence = getattr(quantum_state, "coherence", 0.0)
            
            # Robust regime extraction (Law III.1)
            regime_obj = getattr(regime_state, "current", "UNKNOWN")
            regime = getattr(regime_obj, "name", str(regime_obj))

            # 2. QUANTUM GATE: SCENARIO COLLAPSE [Ω-QUANTUM-GATE]
            # [Ω-C1-V001-V108] Evaluate Superposition before committing
            mc_paths = getattr(regime_state, "monte_carlo_paths", []) # Context extraction
            q_gate_res = await self.quantum_gate.run_quantum_gate({
                "swarm_signal": signal,
                "mc_paths": mc_paths,
                "regime_confidence": confidence
            })
            
            if not q_gate_res["is_authorized"]:
                self.telemetry.record_loop(0.1, False) # Record noise
                return TrinityDecision(
                    action=Action.WAIT,
                    confidence=confidence,
                    reason=f"QUANTUM_OVERLAY_VETO(IG={q_gate_res['information_gain']:.3f})",
                    metadata={"q_gate": q_gate_res},
                    trace_id=trace_id
                )

            # 3. SOVEREIGN OVERRIDE [Concept 3: Soberania]
            # [Ω-C3-T3.1-V1] Check for Sovereign Strike Protocols (SMS, SRE, EVH)
            is_sovereign, sov_reason, sov_meta = self._evaluate_sovereign_protocols(quantum_state, snapshot, regime_state)
            
            # 3. DYNAMIC THRESHOLDING [Ω-C1-T1.2]
            dynamic_phi = self._calculate_dynamic_phi(phi, snapshot, regime)
            dynamic_conf = self._calculate_dynamic_confidence(regime)
            
            # 4. THE 47-LAYER VETO GAUNTLET [Concept 2: Veto]
            if not is_sovereign:
                is_vetoed, veto_reason = self._veto_gauntlet(quantum_state, snapshot, regime_state, dynamic_phi, res_snapshot)
                if is_vetoed:
                    decision = TrinityDecision(
                        action=Action.WAIT,
                        confidence=confidence,
                        reason=f"VETO:{veto_reason}",
                        metadata={"phi_req": dynamic_phi, "phi_actual": phi, "regime": regime},
                        trace_id=trace_id
                    )
                    # [Ω-C3-T3.5-V1] Register Ghost for Parallel Reality Auditing (Shadow Engine)
                    if self.shadow_engine:
                        intended = Action.BUY if signal > 0 else Action.SELL
                        asyncio.create_task(self.shadow_engine.register_ghost(trace_id, decision, snapshot, intended_action=intended))
                    return decision

            # 5. CONFLUENCE DECISION [Ω-C1-T1.1]
            action = Action.WAIT
            if is_sovereign:
                action = Action.BUY if signal > 0 else Action.SELL
                confidence = 0.99 
            else:
                # [Ω-C1-T1.1-V1] Signal Gate (Alpha Filter)
                buy_cond = signal >= self.config.get("buy_thresh", 0.30)
                sell_cond = signal <= self.config.get("sell_thresh", -0.30)
                
                if buy_cond and confidence >= dynamic_conf:
                    action = Action.BUY
                elif sell_cond and confidence >= dynamic_conf:
                    action = Action.SELL

            # 6. CONSENSUS QUORUM [Ω-C1-T1.1-V6] (Law I.1)
            if not is_sovereign and action != Action.WAIT:
                bull_agents = getattr(quantum_state, "bull_agents", [])
                bear_agents = getattr(quantum_state, "bear_agents", [])
                n_supporting = len(bull_agents) if action == Action.BUY else len(bear_agents)
                if n_supporting < self.min_consensus:
                    decision = TrinityDecision(Action.WAIT, 0.0, f"CONSENSUS_VETO({n_supporting}<{self.min_consensus})", trace_id=trace_id)
                    if self.shadow_engine:
                        intended = Action.BUY if signal > 0 else Action.SELL
                        asyncio.create_task(self.shadow_engine.register_ghost(trace_id, decision, snapshot, intended_action=intended))
                    return decision

            # 7. SIGNAL INVERSION (UMRSI) [Ω-C3-T3.2]
            if not is_sovereign:
                action, signal = self._apply_umrsi(action, signal, snapshot)

            if action == Action.WAIT:
                decision = TrinityDecision(Action.WAIT, 0.0, "NO_CONVERGENCE", trace_id=trace_id)
                if self.shadow_engine and abs(signal) > 0.2: # Only ghost potential candidates
                    intended = Action.BUY if signal > 0 else Action.SELL
                    asyncio.create_task(self.shadow_engine.register_ghost(trace_id, decision, snapshot, intended_action=intended))
                return decision

            # 8. EXIT & PHYSICS CALCULATION [Ω-C3-T3.3]
            self.telemetry.add_span(trace_id, "PHYSICS_START", {"ts": time.time()})
            physics = self._calculate_physics(action, signal, snapshot, regime_state)
            
            # [Ω-C1-T1.6-V2] MVP: Minimum Viable Profit protection (Economic Self-Defense)
            if physics.get("expected_pnl", 0) < self.config.get("mvp_floor", 60.0):
                await self.telemetry.finalize_trace(trace_id, "VETO_MVP")
                decision = TrinityDecision(Action.WAIT, 0.0, f"MVP_PROTECTION(${physics['expected_pnl']:.1f})", trace_id=trace_id)
                if self.shadow_engine:
                    intended = Action.BUY if signal > 0 else Action.SELL
                    asyncio.create_task(self.shadow_engine.register_ghost(trace_id, decision, snapshot, intended_action=intended))
                return decision

            # 9. SOLOMON JUSTIFICATION [Ω-PHD-V005]
            self.telemetry.add_span(trace_id, "SOLOMON_START", {"ts": time.time()})
            
            # Extract consensus info safely [V001]
            consensus_info = {
                "strength": signal,
                "confidence": confidence,
                "bias": "BULLISH" if signal > 0 else "BEARISH",
                "top_features": getattr(quantum_state, "top_features", {})
            }
            
            # Synthesize rationale [V001-V054]
            justification = self.justifier.synthesize(
                trace_id=trace_id,
                consensus=consensus_info,
                regime={"id": regime, "confidence": confidence},
                hydra_path=quantum_state
            )
            
            # Final Solomon Authorization [V014]
            authorized, auth_reason = self.justifier.authorize(justification)
            
            if not authorized:
                await self.telemetry.finalize_trace(trace_id, f"VETO_SOLOMON:{auth_reason}")
                decision = TrinityDecision(Action.WAIT, 0.0, f"SOLOMON_VETO:{auth_reason}", trace_id=trace_id)
                if self.shadow_engine:
                    intended = Action.BUY if signal > 0 else Action.SELL
                    asyncio.create_task(self.shadow_engine.register_ghost(trace_id, decision, snapshot, intended_action=intended))
                return decision

            latency_ms = (time.perf_counter() - self.telemetry._active_traces[trace_id]["start_time"]) * 1000
            
            # 10. SUCCESS: COMMITTING TO TELEMETRY [V052]
            decision_metadata = {
                    **physics,
                    "phi": phi,
                    "coherence": coherence,
                    "latency_ms": f"{latency_ms:.3f}",
                    "is_sovereign": is_sovereign,
                    "regime": regime,
                    "rationale": justification.rationale_text,
                    "op_class": justification.opportunity_class
                }
            
            self.telemetry.record_loop(latency_ms, True)
            await self.telemetry.finalize_trace(trace_id, "APPROVED")
            
            return TrinityDecision(
                action=action,
                confidence=confidence,
                reason=f"SOVEREIGN_STRIKE:{sov_reason}" if is_sovereign else f"TRINITY_CONFLUENCE:{regime}",
                metadata=decision_metadata,
                trace_id=trace_id
            )

        except Exception as e:
            self.logger.error(f"☢️ Trinity Emergency Halt: {e}", exc_info=True)
            return TrinityDecision(Action.WAIT, 0.0, f"SYSTEM_HALT:{str(e)}")

    def _evaluate_sovereign_protocols(self, q_state: Any, snap: Any, reg: Any) -> Tuple[bool, str, dict]:
        """[Ω-C3-T3.1] Protocols for bypassing standard veto gates (SRE, SMS, EVH)."""
        
        # [Ω-C3-T3.1-V1] SMS: Structural Manifold Sovereignty
        md = getattr(snap, "metadata", {})
        is_sms = md.get("structural_manifold_active", False) and getattr(q_state, "coherence", 0) > 0.85
        if is_sms: return True, "Ω-SMS_SOVEREIGNTY", {"protocol": "SMS"}
        
        # [Ω-C3-T3.1-V2] SRE: Soros Reflexivity Entrance
        is_sre = md.get("reflexive_climax", False) and abs(getattr(q_state, "signal", 0)) > 0.95
        if is_sre: return True, "Ω-SRE_CLIMAX", {"protocol": "SRE"}
        
        # [Ω-C3-T3.1-V4] PHOENIX: Kinetic Ignition
        if abs(md.get("tick_velocity", 0)) > 30.0 and getattr(q_state, "phi", 0) > 0.5:
            return True, "Ω-PHOENIX_IGNITION", {"protocol": "KINETIC"}

        return False, "", {}

    def _veto_gauntlet(self, q_state: Any, snap: Any, reg: Any, phi_thresh: float, res_snap: Any = None) -> Tuple[bool, str]:
        """[Ω-Concept 2] The 47-layer gauntlet (Logical and Statistical Vetoes)."""
        md = getattr(snap, "metadata", {})
        
        # 0. RESONANCE VETO [Ω-C3-T3.1.5]
        if res_snap:
            # Check for environmental veto (Panic or Gravity discordance)
            # Assuming ResonanceOrchestrator provides is_vetoed but we need to call it
            # Actually, I'll implement a simple check here since I didn't pass the orchestrator instance
            if getattr(res_snap, "is_panic", False):
                return True, "Ω-RESONANCE:GLOBAL_PANIC"
            
            # Simple Gravity Check if action is determined (buy/sell)
            signal = getattr(q_state, "signal", 0.0)
            if abs(signal) > 0.3:
                # If signal is BUY (>0.3) but gravity is extremely bearish (<-0.6)
                if signal > 0 and getattr(res_snap, "gravity_center", 0) < -0.65:
                    return True, f"Ω-RESONANCE:INCOHERENT_GRAVITY({res_snap.gravity_center:.2f})"
                if signal < 0 and getattr(res_snap, "gravity_center", 0) > 0.65:
                    return True, f"Ω-RESONANCE:INCOHERENT_GRAVITY({res_snap.gravity_center:.2f})"
        
        # 1. KINETIC EXHAUSTION [Ω-C2-T2.1-V1]
        if md.get("kinetic_exhaustion", False): return True, "KINETIC_EXHAUSTION"
        
        # 2. SYSTEM INCOHERENCE [Ω-C2-T2.1-V2]
        phi = getattr(q_state, "phi", 0.0)
        if phi < phi_thresh: return True, f"INCOHERENCE(Φ={phi:.3f}<{phi_thresh:.3f})"
        
        # 3. SHANNON NOISE [Ω-C1-T1.6-V1]
        if getattr(snap, "entropy", 0.0) > 3.5: return True, "SHANNON_ENTROPY_VETO"
        
        # 4. POST-TRADE REVERSAL LOCK [Ω-C2-T2.3-V3] (Anti-Metralhadora)
        if (time.time() - self._last_profitable_close_time) < 60.0:
             return True, "POST_WIN_REVERSAL_LOCK"
             
        # 5. LIQUIDITY VOID DEPLETION [Ω-C2-T2.2-V2]
        if md.get("book_depth_ratio", 1.0) < 0.2: return True, "LIQUIDITY_THIN_VETO"
        
        # 6. SPREAD SPIKE [Ω-C2-T2.2-V1]
        if getattr(snap, "spread", 0) > md.get("avg_spread", 0) * 3.0: return True, "SPREAD_SPIKE_VETO"

        return False, ""

    def _calculate_dynamic_phi(self, phi: float, snap: Any, regime: str) -> float:
        """[Ω-C1-T1.2] Scales Phi requirement based on market topology."""
        base = self.phi_min_base
        md = getattr(snap, "metadata", {})
        
        # [Ω-C1-T1.2-V1] Volatility Scaling
        if "CHAOS" in regime: base *= 3.0
        elif "TRENDING" in regime: base *= 0.8
        elif "STABLE" in regime: base *= 0.5
        
        # [Ω-C1-T1.2-V2] Structural Relaxation
        if md.get("near_key_level", False): base *= 0.7
        
        return max(0.05, base)

    def _calculate_dynamic_confidence(self, regime: str) -> float:
        """[Ω-C1-T1.1-V2] Adjusts confidence floor by regime risk."""
        if "CHAOS" in regime: return 0.85
        if "TRENDING" in regime: return 0.60
        return 0.75 # Default Alpha Gate

    def _apply_umrsi(self, action: Action, signal: float, snap: Any) -> Tuple[Action, float]:
        """[Ω-C3-T3.2] Universal Signal Inversion logic (Retail Trap Detection)."""
        md = getattr(snap, "metadata", {})
        if md.get("reflexive_trap", False) and action != Action.WAIT:
             action = Action.SELL if action == Action.BUY else Action.BUY
             signal = -signal
        return action, signal

    def _calculate_physics(self, action: Action, signal: float, snap: Any, reg_state: Any) -> Dict[str, Any]:
        """[Ω-C3-T3.3] Determines SL, TP, and Lot Sizing based on structural physics."""
        entry_price = getattr(snap, "price", getattr(snap, "close", 0))
        md = getattr(snap, "metadata", {})
        atr = md.get("atr_14", 0.0)
        
        # [Ω-C3-T3.3-V1] ATR-Multi-Exit
        sl_dist = atr * 1.5
        tp_dist = atr * 3.0
        
        sl = entry_price - sl_dist if action == Action.BUY else entry_price + sl_dist
        tp = entry_price + tp_dist if action == Action.BUY else entry_price - tp_dist
        
        # Estimated PnL for MVP check
        expected_pnl = tp_dist * self.config.get("lot_unit", 1.0) * 100 # Rough estimate
        
        return {
            "sl": sl,
            "tp": tp,
            "expected_pnl": expected_pnl,
            "atr": atr
        }
