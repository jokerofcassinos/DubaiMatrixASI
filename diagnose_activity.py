
import sys
import os
import json

# Add project root to path
sys.path.append(os.getcwd())

from config.omega_params import OMEGA
from types import SimpleNamespace

def run_advanced_diagnostics():
    print("\n--- DUBAI MATRIX ASI Ω-CORE DIAGNOSTICS ---")
    
    # [PHASE 13] 2026-03 MARKET REGIME MOCK
    # High volatility, extreme tick velocity
    snapshot = SimpleNamespace(
        metadata = {
            "tick_velocity": 45.2, # Extreme volatility
            "phi": 0.85,          # High integration
            "coherence": 0.92,    # High synergy
            "is_braided": False,
            "v_pulse_detected": True
        },
        regime = SimpleNamespace(value="VOLATILE_TRENDING"),
        candles = {"M1": {"close": [100, 105, 110, 115, 120]}}
    )

    print(f"Market Regime: {snapshot.regime.value}")
    print(f"Swarm Consciousness (Phi): {snapshot.metadata['phi']}")
    print(f"Swarm Coherence: {snapshot.metadata['coherence']}")
    
    # 1. KINETIC VETO Check
    floor = OMEGA.get("kinetic_velocity_floor", 2.0)
    tick_vel = snapshot.metadata["tick_velocity"]
    if tick_vel < floor:
        print(f"❌ VETO: KINETIC_EXHAUSTION (Velocity {tick_vel} < {floor})")
    else:
        print(f"✅ KINETIC PASS: Velocity {tick_vel} > {floor}")

    # 2. SYNERGY VETO Check
    min_phi = OMEGA.get("min_phi_threshold", 0.3)
    phi = snapshot.metadata["phi"]
    if phi < min_phi:
        print(f"❌ VETO: SYNERGY_VETO (Phi {phi} < {min_phi})")
    else:
        print(f"✅ SYNERGY PASS: Phi {phi} > {min_phi}")

    # 3. PHD IMMUNITY Check
    phd_active = snapshot.metadata.get("v_pulse_detected", False)
    if phd_active:
        print("🛡️ PHD IMMUNITY ACTIVE: Vetoes will be bypassed for Lethal Strike.")

if __name__ == "__main__":
    run_advanced_diagnostics()
