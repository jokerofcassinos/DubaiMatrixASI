import asyncio
import logging
import pytest
from unittest.mock import MagicMock
from core.decision.trinity_core import TrinityCore, Action

# [Ω-TEST] Solomon & Telemetry Integration Validation
# Validates the PhD Rationale generation and the Causal TraceID propagation.

@pytest.mark.asyncio
async def test_solomon_telemetry_flow():
    """
    Test the full cognitive path:
    1. Create decision in TrinityCore
    2. Check if Telemetry Trace is created
    3. Check if Solomon Justification is generated
    4. Validate Trace finalization
    """
    # 1. Setup TrinityCore
    config = {"lot_unit": 1.0, "phi_min": 0.1, "min_solomon_score": 0.5}
    trinity = TrinityCore(config=config)
    
    # 2. Mock Market States (BULLISH Convergence)
    mock_q_state = MagicMock()
    mock_q_state.signal = 0.99  # Level A+
    mock_q_state.phi = 0.8     # High Coherence
    mock_q_state.confidence = 0.85
    mock_q_state.p_tunnel = 0.99 # Quantum Tunneling
    mock_q_state.top_features = {"order_flow": 0.9, "momentum": 0.8}
    mock_q_state.bull_agents = ["TrendOmega", "FractalSynapse", "NexusSynapse"]
    mock_q_state.bear_agents = []
    
    mock_regime = MagicMock()
    mock_regime.current.name = "TRENDING_UP"
    
    mock_snapshot = MagicMock()
    mock_snapshot.price = 70000.0
    mock_snapshot.metadata = {"atr_14": 500.0, "avg_spread": 10.0}
    mock_snapshot.spread = 10.0
    mock_snapshot.entropy = 0.5
    
    # 3. Execute Decision
    print("\n[STEP 1] Running Trinity Decision Loop...")
    decision = await trinity.decide(mock_q_state, mock_regime, mock_snapshot)
    
    # 4. Assertions
    print(f"[STEP 2] Decision: {decision.action} | Reason: {decision.reason}")
    if decision.action != Action.BUY:
        print(f"DEBUG: Decision failed. Reason: {decision.reason} | Metadata: {decision.metadata}")
    
    assert decision.action == Action.BUY
    assert "rationale" in decision.metadata
    assert decision.metadata["op_class"] == "SOLENN-A+"
    assert decision.trace_id.startswith("Ω-")
    
    print(f"[STEP 3] Solomon Rationale: {decision.metadata['rationale']}")
    
    # 5. Check Telemetry Persistence (Shadow verification)
    # We check if the trace is cleared from memory (meaning finalized)
    assert decision.trace_id not in trinity.telemetry._active_traces
    
    print("✅ Solomon & Telemetry Flow: VALIDATED.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_solomon_telemetry_flow())
