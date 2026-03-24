"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                DUBAI MATRIX ASI — HNP PLASTICITY VERIFICATION                ║
║                                                                              ║
║  Verifica se a Genetic Forge atualiza os multiplicadores Bayesianos após     ║
║  os trades, e se o QuantumThought aplica esses roteamentos espaciais.        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import sys
import os
import shutil

# Ensure we can import the core modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.evolution.genetic_forge import GeneticForge
from core.consciousness.quantum_thought import QuantumThoughtEngine
from core.consciousness.agents.base import AgentSignal

def verify_genetic_plasticity():
    # Setup test file isolated from production
    test_path = "data/test_synaptic_weights.json"
    if os.path.exists(test_path):
        os.remove(test_path)
        
    forge = GeneticForge(data_path=test_path)
    
    # 1. Simulate 5 WINS for 'TesterAgent' in 'HASH_123' when voting BUY
    # 3 hits to bypass warmup -> total 5 hits, 0 misses = 1.0 WR = >0.70 = 2.0 multiplier
    print("🧠 [1] Injecting 5 consecutive WINS for 'TesterAgent' in 'HASH_123'...")
    sv_hash = "HASH_123"
    
    for _ in range(5):
        # Register BUY WIN -> bulls won 
        forge.register_trade_outcome(
            state_vector_hash=sv_hash,
            trade_action="BUY",
            is_win=True,
            bulls=["TesterAgent"],
            bears=[]
        )
        
    # Check weight
    weight = forge.get_synaptic_weight("TesterAgent", sv_hash)
    assert weight == 2.0, f"Plasticity Failed! Expected 2.0 multiplier for 100% WR, got {weight}"
    print(f"✅ Plasticity Success! TesterAgent multiplier in HASH_123 is {weight}")
    
    # 2. Simulate 5 LOSSES for 'BadAgent' in 'HASH_123'
    # 5 misses, 0 hits = 0.0 WR = <0.35 = 0.1 multiplier
    print("📉 [2] Injecting 5 consecutive ERRORS for 'BadAgent' in 'HASH_123'...")
    for _ in range(5):
        # Register BUY LOSS -> bears won, bulls lost
        forge.register_trade_outcome(
            state_vector_hash=sv_hash,
            trade_action="BUY",
            is_win=False,
            bulls=["BadAgent"],
            bears=[]
        )
        
    weight_bad = forge.get_synaptic_weight("BadAgent", sv_hash)
    assert weight_bad == 0.1, f"Crush Failed! Expected 0.1 multiplier for 0% WR, got {weight_bad}"
    print(f"✅ Anvil Success! BadAgent multiplier in HASH_123 was crushed to {weight_bad}")
    
    # 3. Verify QuantumThought routing injection
    # In order to do this we would need to mock GENETIC_FORGE global inside quantum_thought
    # Since we use global singleton in quantum_thought, let's swap it temporarily
    print("⚛️ [3] Verifying QuantumThought Synaptic Routing...")
    import core.evolution.genetic_forge
    original_forge = core.evolution.genetic_forge.GENETIC_FORGE
    core.evolution.genetic_forge.GENETIC_FORGE = forge 
    
    class MockSnapshot:
        metadata = {"state_vector_hash": sv_hash, "M1_entropy": 0.5, "M5_entropy": 0.5}
        candles = {}
        timestamp = 10000000
        price = 60000.0
        
    engine = QuantumThoughtEngine()
    
    signals = [
        AgentSignal("TesterAgent", signal=1.0, confidence=1.0, reasoning="Test"),
        AgentSignal("BadAgent", signal=1.0, confidence=1.0, reasoning="Test"),
    ]
    
    state = engine.process(signals, snapshot=MockSnapshot())
    
    # Check if the reasoning string was injected with multiplier
    for s in state.agent_signals:
        if s.agent_name == "TesterAgent":
            assert s.weight == 2.0, "Weight did not scale!"
            print(f"✅ TesterAgent signal properly routed with weight x{s.weight:.1f}")
        if s.agent_name == "BadAgent":
            assert s.weight == 0.1, "Weight did not crush!"
            print(f"✅ BadAgent signal properly routed with weight x{s.weight:.1f}")
            
    # Cleanup
    core.evolution.genetic_forge.GENETIC_FORGE = original_forge
    if os.path.exists(test_path):
        os.remove(test_path)
    print("\n🏁 ALL HNP PLASTICITY TESTS PASSED! LETHALITY RESTORED.")

if __name__ == "__main__":
    verify_genetic_plasticity()
