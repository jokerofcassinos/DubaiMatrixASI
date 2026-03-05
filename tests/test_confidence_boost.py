import numpy as np
from core.consciousness.neural_swarm import AgentSignal
from core.consciousness.quantum_thought import QuantumThoughtEngine

def test_confidence_logic():
    engine = QuantumThoughtEngine()
    
    # Simular sinais onde confiança individual é baixa (0.63 avg) mas coerência é alta
    signals = [
        AgentSignal("Trend", 0.8, 0.63, "Bullish", 1.0),
        AgentSignal("Momentum", 0.6, 0.63, "Bullish", 1.0),
        AgentSignal("Volume", 0.7, 0.63, "Bullish", 1.0)
    ]
    
    state = engine.process(signals, regime_weight=1.0)
    
    print(f"Test Result:")
    print(f"  Raw Signal: {state.raw_signal:.3f}")
    print(f"  Coherence: {state.coherence:.2f}")
    print(f"  Aggregated Confidence: {state.confidence:.2f}")
    print(f"  Should Collapse: {not state.superposition}")
    print(f"  Reasoning: {state.reasoning}")

    if state.confidence > 0.63 and not state.superposition:
        print("\n✅ SUCCESS: Confidence boost applied and state collapsed.")
    else:
        print("\n❌ FAILURE: Logic did not bridge the gap.")

if __name__ == "__main__":
    test_confidence_logic()
