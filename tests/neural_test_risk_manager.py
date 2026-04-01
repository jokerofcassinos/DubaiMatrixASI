import asyncio
import numpy as np
import pytest
from market.risk_manager import RiskManager, RiskLevel
from market.regime_detector import RegimeState

# [Ω-TEST] Neural Audit: Risk Manager Ω-5 (Shield Precision)
# "O escudo não deve apenas resistir; deve se auto-fortalecer na adversidade."

@pytest.mark.asyncio
async def test_circuit_breakers_and_kelly():
    """[AUDIT Ω-5.2] Testing Drawdown-based CB Levels and Bayesian Kelly."""
    
    rm = RiskManager(initial_balance=100000.0)
    await rm.initialize()
    
    # --- FASE 1: SIZING EM REGIME NORMAL (GREEN) ---
    print("\n[FASE 1] Auditando Sizing em Regime Normal (HODL_BULL)...")
    regime_bull = RegimeState("HODL_BULL", 0.9, 0.01, 0.2, 100, {})
    size_green = rm.calculate_optimal_sizing(regime_bull, matrix_confidence=0.9)
    print(f"📊 Sizing GREEN: {size_green:.4f} lots")
    assert size_green > 0
    assert rm.get_exposure_multiplier() == 1.0

    # --- FASE 2: GATILHO DE CIRCUIT BREAKER (RED) ---
    print("\n[FASE 2] Simulando Drawdown de 1.2% (Gatilho RED)...")
    await rm.update_equity(98800.0) # 1.2% loss
    assert rm.level == RiskLevel.RED
    assert rm.get_exposure_multiplier() == 0.1
    
    size_red = rm.calculate_optimal_sizing(regime_bull, matrix_confidence=0.9)
    print(f"📉 Sizing RED (Scaled 90% reduction): {size_red:.4f} lots")
    assert size_red < size_green

    # --- FASE 3: SHUTDOWN OPERACIONAL (EMERGENCY) ---
    print("\n[FASE 3] Simulando Drawdown de 2.5% (EMERGENCY LOCKDOWN)...")
    await rm.update_equity(97500.0) # 2.5% loss
    assert rm.level == RiskLevel.EMERGENCY
    assert rm._lockdown is True
    assert rm.validate_execution() is False
    
    size_emergency = rm.calculate_optimal_sizing(regime_bull, matrix_confidence=0.9)
    assert size_emergency == 0.0
    print(f"☢️ EMERGENCY Status: LOCKDOWN={rm._lockdown} | Sizing={size_emergency}")

    # --- FASE 4: MONTE CARLO RUIN PROJECTION (Ω-20) ---
    print("\n[FASE 4] Auditando Projeção de Ruína Ω-20...")
    await asyncio.sleep(2) # Give MC time to run at least once (short sleep in test)
    print(f"🌌 P(ruin) Estimada: {rm.p_ruin:.4%}")
    assert isinstance(rm.p_ruin, float)

    print("\n✅ AUDITORIA Ω-5 CONCLUÍDA: Escudo Soberano Operando com Precisão Quântica.")

if __name__ == "__main__":
    asyncio.run(test_circuit_breakers_and_kelly())
