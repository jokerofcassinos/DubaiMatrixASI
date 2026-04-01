import asyncio
import numpy as np
import time
import pytest
from market.regime_detector import RegimeDetector

# [Ω-TEST] Neural Audit: Regime Detector Ω-4 (Matrix Precision Check)
# "A validade do estado é a âncora da verdade."

@pytest.mark.asyncio
async def test_regime_stability_and_transition():
    """[AUDIT Ω-4.1] Testing Regime Identification Stability and Transition Alerts."""
    detector = RegimeDetector()
    await detector.initialize()
    
    # --- FASE 1: RANGING (ESTÁVEL) ---
    print("\n[FASE 1] Simulando Ranging (Low Phi, Low VPIN)...")
    for _ in range(300):
        # Phi near 0.0 with noise. VPIN near 0.2.
        phi = np.random.normal(0.0, 0.05)
        vpin = np.random.normal(0.2, 0.02)
        state = await detector.process_matrix_signal(phi, vpin, 0.1, {})
        
    print(f"✅ STATE: {state.identity} | CONF: {state.confidence:.2f}")
    assert state.identity in ["RANGING_TIGHT", "RANGING_WIDE", "REGIME_UNKNOWN"]
    
    # --- FASE 2: PREPARANDO BREAKOUT (Instabilidade) ---
    print("\n[FASE 2] Simulando Critical Slowing Down (Pre-Breakout)...")
    phi_val = 0.0
    for _ in range(50):
        # Increasing oscillation and slight trend shift
        phi_val += 0.02
        phi = phi_val + np.random.normal(0.0, 0.1)
        vpin = 0.2 + np.random.uniform(0.0, 0.3)
        state = await detector.process_matrix_signal(phi, vpin, 0.4, {})
        
    print(f"⚠️ PROB TRANSIÇÃO (RTLI): {state.transition_prob:.2f}")
    assert state.transition_prob > 0.3 # RTLI alert should increase
    
    # --- FASE 3: TRENDING UP (BREAKOUT) ---
    print("\n[FASE 3] Simulando TRENDING_UP (High Phi, High VPIN)...")
    for _ in range(100):
        phi = 0.85 + np.random.normal(0.0, 0.05)
        vpin = 0.5 + np.random.normal(0.0, 0.03)
        state = await detector.process_matrix_signal(phi, vpin, 0.8, {})
        
    print(f"🚀 STATE: {state.identity} | CONF: {state.confidence:.2f}")
    assert "TRENDING_UP" in state.identity
    assert state.confidence > 0.6
    
    # --- FASE 4: PANIC LIQUIDATION ---
    print("\n[FASE 4] Simulando PANIC (Zero Phi, Extreme VPIN)...")
    for _ in range(50):
        phi = -0.9 + np.random.normal(0.0, 0.05)
        vpin = 0.95 # Extreme toxic flow
        state = await detector.process_matrix_signal(phi, vpin, 0.9, {})
        
    print(f"💀 STATE: {state.identity} | CONF: {state.confidence:.2f}")
    assert state.identity in ["PANIC_LIQUIDATION", "TRENDING_DOWN_STRONG"]
    
    print("\n✅ AUDITORIA Ω-4 CONCLUÍDA: Córtex de Regime Operando com Precisão Matrix.")

if __name__ == "__main__":
    asyncio.run(test_regime_stability_and_transition())
