import sys
import os
import json
import time

# Add base path
sys.path.append(os.path.abspath("d:/DubaiMatrixASI"))

from market.mt5_bridge import MT5Bridge
from market.data_engine import DataEngine
from core.consciousness.neural_swarm import NeuralSwarm
from core.consciousness.quantum_thought import QuantumThoughtEngine

def debug_swarm():
    print("Initializing components...")
    bridge = MT5Bridge()
    if not bridge.connect():
        print("Failed to connect to MT5")
        return

    print("Waiting for data flow...")
    while bridge.get_tick() is None:
        time.sleep(0.5)
        
    engine = DataEngine(bridge)
    swarm = NeuralSwarm()
    quantum = QuantumThoughtEngine()
    
    print("Warming up DataEngine...")
    time.sleep(3) # allow background worker to fetch candles and calculate indicators
    
    snapshot = engine.update()
    if not snapshot:
        print("Failed to get snapshot")
        return
        
    print(f"Snapshot indicators available: {len(snapshot.indicators)}")
    
    signals = swarm.analyze(snapshot, {})
    print(f"\nSwarm generated {len(signals)} signals:")
    for s in signals:
        print(f"  {s.agent_name}: val={s.signal:+.3f} conf={s.confidence:.2f} w={s.weight:.1f} | {s.reasoning}")
        
    q_state = quantum.process(signals, 1.0)
    print(f"\nQuantum State: {q_state.reasoning}")

    bridge.disconnect()
    engine.shutdown()

if __name__ == "__main__":
    debug_swarm()
