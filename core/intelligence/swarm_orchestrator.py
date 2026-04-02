import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
import numpy as np

from core.intelligence.base_synapse import BaseSynapse
from core.intelligence.byzantine_consensus import ByzantineConsensus
from core.consciousness.neural_swarm import NeuralSwarm
from market.data_engine import QuantumState


def _safe_float(val, default: float = 0.0) -> float:
    """
    [Ω-SHIELD] Universal numpy/array/bool → float converter.
    Handles: int, float, np.float64, np.int64, np.bool_,
    np.ndarray (takes .item() or mean()), str signals, bool, and any edge case.
    """
    if val is None:
        return default
    # Native Python scalar — fast path
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        return float(val)
    # Python bool (must check before int because bool is subclass of int)
    if isinstance(val, bool):
        return 1.0 if val else 0.0
    # NumPy scalar types (float64, int64, bool_, etc.)
    if isinstance(val, (np.floating, np.integer)):
        return float(val)
    if isinstance(val, np.bool_):
        return 1.0 if val else 0.0
    # NumPy array — collapse to scalar
    if isinstance(val, np.ndarray):
        if val.size == 1:
            return float(val.item())
        if val.size > 1:
            return float(np.mean(val))
        return default
    # String signal names
    if isinstance(val, str):
        upper = val.upper().strip()
        if upper in ("BUY", "LONG", "BULLISH"):
            return 1.0
        if upper in ("SELL", "SHORT", "BEARISH"):
            return -1.0
        # Try numeric string
        try:
            return float(upper)
        except (ValueError, TypeError):
            return default
    # Last resort
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


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

    def attach_genetic_swarm(self, swarm: NeuralSwarm):
        """[Ω-C1-T1.2] Attach the evolved neural swarm for collective voting."""
        self.neural_swarm = swarm
        self.logger.info("🐝 Genetic Neural Swarm Attached to Orchestrator.")

    async def get_quantum_state(self, snapshot: Any, nexus_context: Any = None) -> QuantumState:
        """
        [Ω-C2-T2.1] Consensus Synthesis: Collapsing the Swarm's wave function.
        Returns the unified QuantumState for Trinity Core.
        """
        _empty_state = QuantumState(
            timestamp=time.time(), symbol="",
            signal=0.0, confidence=0.0, coherence=0.0, phi=0.0
        )

        if not self.synapses:
            return _empty_state

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 1. Collect Votes from all active Synapses [Ω-C2-T2.1-V1]
        #    CRITICAL FIX: Track synapse names alongside tasks for correct
        #    index mapping after asyncio.gather returns.
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        tasks = []
        task_synapse_names: List[str] = []  # Parallel list: task[i] belongs to task_synapse_names[i]

        for name, synapse in self.synapses.items():
            if synapse.heartbeat():
                tasks.append(synapse.process(snapshot, nexus_context))
                task_synapse_names.append(name)

        if not tasks:
            return _empty_state

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2. Extract and Weighted Aggregation [Ω-C2-T2.1-V2]
        #    Uses task_synapse_names[i] for correct name mapping.
        #    Uses _safe_float for ALL numeric extractions (numpy shield).
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        raw_sigs: Dict[str, float] = {}
        valid_data: List[Dict[str, float]] = []  # [{name, sig, conf, phi, thompson_w}, ...]

        for i, res in enumerate(results):
            synapse_name = task_synapse_names[i]

            if isinstance(res, Exception):
                self.logger.warning(f"☢️ Synapse Fault [{synapse_name}]: {res}")
                continue

            if not isinstance(res, dict):
                self.logger.warning(f"☢️ Synapse [{synapse_name}] returned non-dict: {type(res)}")
                continue

            synapse = self.synapses[synapse_name]

            # Thompson Sampling weight [Ω-C1-T1.4-V1]
            w = synapse.get_sample_weight()

            sig = _safe_float(res.get("signal", 0.0))
            conf = _safe_float(res.get("confidence", 0.0))
            phi = _safe_float(res.get("phi", 0.0))

            # [Ω-C2-T2.1-V9] Store raw signal for Byzantine audit
            raw_sigs[synapse_name] = sig

            valid_data.append({
                "name": synapse_name,
                "signal": sig,
                "confidence": conf,
                "phi": phi,
                "thompson_w": w,
            })

        if not valid_data:
            return _empty_state

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 3. Byzantine Audit Layer [Ω-BYZANTINE]
        #    Filters and penalizes malicious/noisy agents (Concept 1 & 2)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        trust_weights = self.byzantine.filter_signals(raw_sigs)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 4. Final Synthesis (Mean Weighted) [Ω-C2-T2.5-V1]
        #    Combined Weight = Thompson Sampling × Byzantine Trust
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        sum_sig = 0.0
        sum_conf = 0.0
        sum_phi = 0.0
        sum_w = 0.0
        bull_agents: List[str] = []
        bear_agents: List[str] = []

        for entry in valid_data:
            name = entry["name"]
            w_total = entry["thompson_w"] * trust_weights.get(name, 1.0)

            sum_sig += entry["signal"] * w_total
            sum_conf += entry["confidence"] * w_total
            sum_phi += entry["phi"] * w_total
            sum_w += w_total

            if entry["signal"] > 0.1:
                bull_agents.append(name)
            elif entry["signal"] < -0.1:
                bear_agents.append(name)

        if sum_w == 0.0:
            return _empty_state

        avg_signal = sum_sig / sum_w
        avg_conf = sum_conf / sum_w
        avg_phi = sum_phi / sum_w

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 5. Genetic Consensus Overlays [Ω-GENETIC-SYNERGY]
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if self.neural_swarm:
            # Map snapshot to dict context for agents (safe getattr for optional fields)
            context = {
                "price": _safe_float(getattr(snapshot, 'price', 0.0)),
                "rsi": _safe_float(getattr(snapshot, 'rsi_14', 50.0)),
                "atr": _safe_float(getattr(snapshot, 'atr_14', 0.0)),
                "phi": _safe_float(getattr(snapshot, 'phi', 0.0)),
                "ema_fast": _safe_float(getattr(snapshot, 'ema_fast', 0.0)),
                "ema_slow": _safe_float(getattr(snapshot, 'ema_slow', 0.0)),
                "volume": _safe_float(getattr(snapshot, 'volume', 0.0)),
                "spread": _safe_float(getattr(snapshot, 'spread', 0.0)),
                "imbalance": _safe_float(getattr(snapshot, 'book_imbalance', 0.0))
            }
            try:
                genetic_res = await self.neural_swarm.get_consensus_signal(context)
                gen_sig = _safe_float(genetic_res.get("signal", 0.0))
                gen_conf = _safe_float(genetic_res.get("confidence", 0.0))

                # Blend Genetic Signal (Ω-C2-T2.6): Weight determined by active agents
                max_agents = getattr(self.neural_swarm, 'max_agents', 10)
                if max_agents > 0:
                    w_gen = 0.3 * (_safe_float(genetic_res.get("active_agents", 0)) / max_agents)
                else:
                    w_gen = 0.0

                avg_signal = (avg_signal * (1.0 - w_gen)) + (gen_sig * w_gen)
                avg_conf = (avg_conf * (1.0 - w_gen)) + (gen_conf * w_gen)

                if abs(gen_sig) > 0.1:
                    self.logger.debug(f"🐝 Genetic Swarm Vote: {gen_sig:.4f} (W: {w_gen:.2f})")
            except Exception as e:
                self.logger.warning(f"☢️ Genetic Swarm Fault: {e}")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 6. Calculation of Coherence [Ω-C2-T2.2-V1]
        #    (Inverse of signal variance among active agents + Byzantine check)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        names = list(raw_sigs.keys())
        raw_values = [raw_sigs[n] for n in names]
        filtered_values = [v * trust_weights.get(names[i], 1.0) for i, v in enumerate(raw_values)]

        coherence = self.byzantine.get_coherence_metrics(raw_values, filtered_values)

        # Extrair symbol do snapshot se disponível
        sym = getattr(snapshot, 'symbol', '') if snapshot else ''

        return QuantumState(
            timestamp=time.time(),
            symbol=sym,
            signal=float(avg_signal),
            phi=float(avg_phi),
            confidence=float(avg_conf),
            coherence=float(coherence),
        )

    async def shutdown(self):
        """[Ω-C1-T1.1-V9] Terminate all synaptic clusters."""
        for name, synapse in self.synapses.items():
            await synapse.shutdown()
        self.logger.info("🌑 Swarm Orchestrator Halted.")
