"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              SOLÉNN — TEST: BYZANTINE RESILIENCE Ω                           ║
║     Validation of Swarm Robustness against Noisy/Malicious Agents            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import logging
from core.intelligence.swarm_orchestrator import SwarmOrchestrator
from core.intelligence.base_synapse import BaseSynapse

class MockSynapse(BaseSynapse):
    def __init__(self, name: str, behavior: str = "honest"):
        super().__init__(name)
        self.behavior = behavior
        if behavior == "honest":
            self.alpha = 100.0 # Clear winner
            self.beta = 1.0
        else:
            self.alpha = 1.0
            self.beta = 1.0
        
    async def process(self, snapshot, context=None):
        if self.behavior == "honest":
            return {"signal": 0.8, "confidence": 0.9, "phi": 0.8}
        elif self.behavior == "malicious":
            # Lie: say the trend is down when everyone says up
            return {"signal": -0.9, "confidence": 0.95, "phi": 0.9}
        elif self.behavior == "noisy":
            return {"signal": 0.1, "confidence": 0.3, "phi": 0.2}
        return {"signal": 0.0, "confidence": 0.0, "phi": 0.0}

async def run_byzantine_validation():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("SOLENN.TestByzantine")
    
    orchestrator = SwarmOrchestrator()
    
    # Register 3 Honest Agents and 1 Malicious Agent
    orchestrator.register_synapse(MockSynapse("Honest_Alpha", "honest"))
    orchestrator.register_synapse(MockSynapse("Honest_Beta", "honest"))
    orchestrator.register_synapse(MockSynapse("Honest_Gamma", "honest"))
    orchestrator.register_synapse(MockSynapse("Liar_Agent", "malicious"))
    
    print("\n[STEP 1] Generating Initial Quantum State with Liar present...")
    state = await orchestrator.get_quantum_state(None)
    
    print(f"Aggregated Signal: {state.signal:.4f}")
    print(f"Coherence Score: {state.coherence:.4f}")
    print(f"Bull Agents: {state.bull_agents}")
    print(f"Bear Agents: {state.bear_agents}")
    
    # [Ω-CHECK] Without Byzantine, the signal would be pulled down significantly.
    # Honest (0.8+0.8+0.8) + Liar (-0.9) = 1.5 / 4 = 0.375 (if same weights)
    # With Byzantine filtering the outlier -0.9, it should stay near 0.8.
    
    if state.signal > 0.5:
        print("\n✅ Verification Success: Byzantine Filter blocked the Liar's signal.")
    else:
        print("\n❌ Verification Failure: Liar's signal corrupted the consensus.")

    print("\n[STEP 2] Simulating Repetitive Attacks (Bayesian Trust Decay)...")
    for i in range(5):
        await orchestrator.get_quantum_state(None)
        liar_rep = orchestrator.byzantine.reputation["Liar_Agent"]
        print(f"Iteration {i+1} | Liar Trust Score: {liar_rep.trust_score:.4f} | Status: {liar_rep.status}")

    final_liar_rep = orchestrator.byzantine.reputation["Liar_Agent"]
    if final_liar_rep.trust_score < 0.3:
        print(f"\n✅ Reputation Success: Liar's Trust Score decayed to {final_liar_rep.trust_score:.4f}")
    else:
        print(f"\n❌ Reputation Failure: Liar's Trust Score remains high.")

if __name__ == "__main__":
    asyncio.run(run_byzantine_validation())
