import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
import numpy as np

from core.intelligence.base_synapse import BaseSynapse
from core.intelligence.byzantine_consensus import ByzantineConsensus
from core.consciousness.neural_swarm import NeuralSwarm
from market.data_engine import QuantumState

class SwarmOrchestrator:
    """
    [Ω-SYNAPSE] The Maestro of SOLÉNN Agent Swarm.
    Implements Concept 1 (Elite Swarm) and Concept 2 (Quantum Consensus).
    Responsible for 162 vectors of Collective Intelligence.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger("SOLENN.SwarmOrchestrator")
        self.synapses: Dict[str, BaseSynapse] = {}
        self._is_active = False
        self.neural_swarm: Optional[NeuralSwarm] = None
        
        # [Ω-C2-T2.2-V1] Coherence Thresholds
        self.min_coherence = self.config.get("min_coherence", 0.4)
        self.min_confidence = self.config.get("min_confidence", 0.6)
        
        # [Ω-BYZANTINE-SHIELD]
        self.byzantine = ByzantineConsensus(self.config.get("byzantine", {}))

        self.synapses[synapse.name] = synapse
        self.logger.info(f"🧠 Synapse Registered: {synapse.name}")

    def attach_genetic_swarm(self, swarm: NeuralSwarm):
        """[Ω-C1-T1.2] Attach the evolved neural swarm for collective voting."""
        self.neural_swarm = swarm
        self.logger.info("🐝 Genetic Neural Swarm Attached to Orchestrator.")

    async def get_quantum_state(self, snapshot: Any, nexus_context: Any = None) -> QuantumState:
        """
        [Ω-C2-T2.1] Consensus Synthesis: Collapsing the Swarm's wave function.
        Returns the unified QuantumState for Trinity Core.
        """
        if not self.synapses:
            return QuantumState(0.0, 0.0, 0.0, 0.0)

        # 1. Collect Votes from all active Synapses [Ω-C2-T2.1-V1]
        tasks = []
        for name, synapse in self.synapses.items():
            if synapse.heartbeat():
                tasks.append(synapse.process(snapshot, nexus_context))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 2. Extract and Weighted Agregation [Ω-C2-T2.1-V2]
        signals = []
        confidences = []
        phis = []
        bull_agents = []
        bear_agents = []
        sampled_weights = []
        raw_sigs = {}
        
        valid_count = 0
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                self.logger.error(f"☢️ Synapse Fault: {res}")
                continue
            
            synapse_name = list(self.synapses.keys())[i]
            synapse = self.synapses[synapse_name]
            
            # Thompson Sampling weight [Ω-C1-T1.4-V1]
            w = synapse.get_sample_weight()
            sampled_weights.append(w)
            
            sig = res.get("signal", 0.0)
            conf = res.get("confidence", 0.0)
            phi = res.get("phi", 0.0)
            
            # [Ω-C2-T2.1-V9] Store raw signal for Byzantine audit
            raw_sigs[synapse_name] = sig
            
            signals.append(sig * w)
            confidences.append(conf * w)
            phis.append(phi * w)
            
            if sig > 0.1: bull_agents.append(synapse_name)
            elif sig < -0.1: bear_agents.append(synapse_name)
            
            valid_count += 1

        if valid_count == 0:
            return QuantumState(0.0, 0.0, 0.0, 0.0)

        # 3. Byzantine Audit Layer [Ω-BYZANTINE]
        # Filters and penalizes malicious/noisy agents (Concept 1 & 2)
        trust_weights = self.byzantine.filter_signals(raw_sigs)
        
        # 4. Final Synthesis (Mean Weighted) [Ω-C2-T2.5-V1]
        sum_sig = 0
        sum_conf = 0
        sum_phi = 0
        sum_w = 0
        
        for i, res in enumerate(results):
            if isinstance(res, Exception): continue
            
            name = list(self.synapses.keys())[i]
            # Combined Weight: Thompson * Byzantine Trust
            w_total = sampled_weights[i] * trust_weights.get(name, 1.0)
            
            sum_sig += res.get("signal", 0.0) * w_total
            sum_conf += res.get("confidence", 0.0) * w_total
            sum_phi += res.get("phi", 0.0) * w_total
            sum_w += w_total

        if sum_w == 0:
            return QuantumState(0.0, 0.0, 0.0, 0.0)

        avg_signal = sum_sig / sum_w
        avg_conf = sum_conf / sum_w
        avg_phi = sum_phi / sum_w
        
        # 5. Genetic Consensus Overlays [Ω-GENETIC-SYNERGY]
        if self.neural_swarm:
            # Map snapshot to dict context for agents
            context = {
                "price": snapshot.price,
                "rsi": snapshot.rsi_14,
                "atr": snapshot.atr_14,
                "phi": snapshot.phi,
                "ema_fast": snapshot.ema_fast,
                "ema_slow": snapshot.ema_slow,
                "volume": snapshot.volume,
                "spread": snapshot.spread,
                "imbalance": snapshot.book_imbalance
            }
            genetic_res = await self.neural_swarm.get_consensus_signal(context)
            gen_sig = genetic_res.get("signal", 0.0)
            gen_conf = genetic_res.get("confidence", 0.0)
            
            # Blend Genetic Signal (Ω-C2-T2.6): Weight determined by active agents
            w_gen = 0.3 * (genetic_res.get("active_agents", 0) / self.neural_swarm.max_agents)
            avg_signal = (avg_signal * (1 - w_gen)) + (gen_sig * w_gen)
            avg_conf = (avg_conf * (1 - w_gen)) + (gen_conf * w_gen)
            
            if abs(gen_sig) > 0.1:
                self.logger.debug(f"🐝 Genetic Swarm Vote: {gen_sig:.4f} (W: {w_gen:.2f})")

        # 6. Calculation of Coherence [Ω-C2-T2.2-V1]
        # (Inverse of signal variance among active agents + Byzantine check)
        names = list(raw_sigs.keys())
        raw_values = list(raw_sigs.values())
        # We simulate "filtered values" by applying trust weights for metrics
        filtered_values = [v * trust_weights.get(names[i], 1.0) for i, v in enumerate(raw_values)]
        
        coherence = self.byzantine.get_coherence_metrics(raw_values, filtered_values)
        
        return QuantumState(
            signal=float(avg_signal),
            phi=float(avg_phi),
            confidence=float(avg_conf),
            coherence=float(coherence),
            bull_agents=bull_agents,
            bear_agents=bear_agents
        )

    async def shutdown(self):
        """[Ω-C1-T1.1-V9] Terminate all synaptic clusters."""
        for name, synapse in self.synapses.items():
            await synapse.shutdown()
        self.logger.info("🌑 Swarm Orchestrator Halted.")
