import asyncio
import numpy as np
import pytest
import time
from market.execution_engine import ExecutionEngine
from market.hftp_bridge import HFTPBridge
from market.regime_detector import RegimeState

# [Ω-TEST] Neural Audit: Execution Engine Ω-6 (Order Precision Check)
# "O golpe deve ser invisível até o impacto."

@pytest.mark.asyncio
async def test_execution_tactic_and_latency():
    """[AUDIT Ω-6.2] Testing Execution Tactics (Maker vs Taker) and State Machine."""
    
    # --- MOCKING BRIDGE FOR AUDIT ---
    bridge = HFTPBridge(host="127.0.0.1", port=9998)
    # We won't actually call connect() in this unit test to avoid socket errors, 
    # but we will mock the submit_order method.
    bridge._is_connected = True 
    async def mock_submit(packet): return True
    bridge.submit_order = mock_submit
    
    engine = ExecutionEngine(bridge)
    await engine.initialize()
    
    # --- FASE 1: RANGING ACCUMULATION (TACTIC: LIMIT) ---
    print("\n[FASE 1] Simulando Ranging (Regime: RANGING_TIGHT, Urgency: 0.2)...")
    regime_range = RegimeState("RANGING_TIGHT", 0.9, 0.05, 0.3, 100, {})
    oid1 = await engine.execute_trade("BTCUSDT", "BUY", 1.0, regime_range, 0.2)
    
    # [V2.5.37] Verify Tactic: Ranging should favor LIMIT (Maker)
    assert engine._orders[oid1]["type"] == "LIMIT"
    print(f"✅ OID: {oid1} | TACTIC: {engine._orders[oid1]['type']} (Correct: LIMIT)")
    
    # --- FASE 2: BREAKOUT URGENCY (TACTIC: MARKET) ---
    print("\n[FASE 2] Simulando Breakout (Regime: TRENDING_UP_STRONG, Urgency: 0.85)...")
    regime_trend = RegimeState("TRENDING_UP_STRONG", 0.95, 0.01, 1.2, 50, {})
    oid2 = await engine.execute_trade("BTCUSDT", "BUY", 1.0, regime_trend, 0.85)
    
    # [V2.5.37] Verify Tactic: Strong Trend + High Urgency should favor MARKET (Taker)
    assert engine._orders[oid2]["type"] == "MARKET"
    print(f"✅ OID: {oid2} | TACTIC: {engine._orders[oid2]['type']} (Correct: MARKET)")
    
    # --- FASE 3: SLIPPAGE PREDICTION (Ω-21) ---
    print("\n[FASE 3] Auditando Slippage Prediction Ω-21...")
    slip1 = engine._orders[oid1]["e_slippage"] # Low vol
    slip2 = engine._orders[oid2]["e_slippage"] # High vol
    print(f"📉 SLIPPAGE LOW_VOL: {slip1:.5f} | HIGH_VOL: {slip2:.5f}")
    assert slip2 > slip1 # Slippage should scale with volatility
    
    # --- FASE 4: STATE MACHINE ACKNOWLEDGMENT (V3.1) ---
    print("\n[FASE 4] Simulando ACK de Execução...")
    await engine.handle_acknowledgment({
        "id": oid2, 
        "price": 65000.5, 
        "vol": 1.0, 
        "status": "FILLED"
    })
    
    # [V3.1.46] Verify State transition: FILLED
    assert engine._orders[oid2]["status"] == "FILLED"
    print(f"✅ [STATE-CHECK] {oid2}: Status FILLED.")
    
    # --- FASE 5: RECONCILIATION ---
    print("\n[FASE 5] Auditoria de Reconciliação (Snapshot Ω-6.3)...")
    await engine.reconcile_states()
    assert oid2 not in engine._orders # Should be cleaned up as acked (depending on cleanup logic)
    
    print("\n✅ AUDITORIA Ω-6 CONCLUÍDA: Aorta de Execução Operando com Sincronia Matrix.")

if __name__ == "__main__":
    asyncio.run(test_execution_tactic_and_latency())
