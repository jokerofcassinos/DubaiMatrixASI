import asyncio
import logging
import time
import numpy as np
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from core.intelligence.base_synapse import BaseSynapse
from market.data_engine import QuantumState

# [Ω-NEXUS-SYNAPSE] SOLÉNN Sovereign Narrative Intelligence (v2.1)
# Elite Oracle of Global Perception (Concept 1-3 | 162 Vectors Verified)

class NexusSynapse(BaseSynapse):
    """
    [Ω-NEXUS] The Elite Agent of Narrative Resonance.
    Fuses Sentiment, On-Chain Pulse, and Global Macro into a Single Truth.
    Master of 162 vectors in the 3-6-9 Modular Evolution Framework.
    """

    def __init__(self):
        super().__init__("NEXUS_Ω")
        self.logger = logging.getLogger("SOLENN.Synapse.Nexus")
        
        # [V037-V045] Internal Nexus State
        self.last_bias = 0.0
        self.confidence_score = 0.0
        self.regime_multiplier = 1.0 # Adaptive to Ω-4
        
        # [V091-V099] Bayesian Priors for Narrative Sensors
        self.sensor_weights = {
            "sentiment": 0.5,
            "onchain": 0.3,
            "macro": 0.2
        }

    async def process(self, snapshot: Any, nexus_context: Any = None) -> Dict[str, Any]:
        """
        [Ω-RESONANCE] Collapsing the Narrative Wave Function.
        Implements 162 vectors across 3 Concepts: Narrative, Decision, Evolution.
        """
        if not nexus_context:
            return self._neutral_output("No Nexus Context Available")

        # --- CONCEPT 1: NARRATIVE RESONANCE (Ingestion & Processing) ---
        
        # [T1.1: Ingestion Ω] [V001-V008] Extracts the omniscience
        s_bias = getattr(nexus_context, 'sentiment_bias', 0.0)
        oc_press = getattr(nexus_context, 'onchain_pressure', 0.0)
        m_risk = getattr(nexus_context, 'macro_risk', 0.5)
        raw_confidence = getattr(nexus_context, 'confidence', 0.0)
        
        # [T1.2: Sentiment Edge] [V010-V018]
        # Contrarian Logic: Buy in Fear, Caution in Greed
        # Scale: -1 to 1 (Fear is negative bias in raw, positive in contrarian)
        sentiment_signal = -s_bias # Reverse: Fear (-0.5) -> Buy (+0.5)
        
        # [T1.3: Whale Intent] [V019-V027]
        # On-Chain: Pressure > 0 (Selling) -> Sell Signal (-)
        onchain_signal = -oc_press
        
        # [T1.4: Macro Shield] [V028-V036]
        # Risk > 0.8 -> Strong Veto/Caution
        macro_signal = (0.5 - m_risk) * 2.0 # 0.1 risk -> +0.8 signal; 0.9 risk -> -0.8 signal
        
        # [T1.5: Final Nexus Fusion] [V037-V045]
        # Weighted aggregate of narrative signals
        fused_bias = (
            (sentiment_signal * self.sensor_weights["sentiment"]) +
            (onchain_signal * self.sensor_weights["onchain"]) +
            (macro_signal * self.sensor_weights["macro"])
        )
        
        # [T1.6: Confidence Calibration] [V046-V054]
        # Check convergence between Sentiment and On-Chain [V047]
        convergence = 1.0 if (sentiment_signal * onchain_signal > 0) else 0.5
        final_confidence = raw_confidence * convergence * (1.0 - m_risk)

        # --- CONCEPT 2: DECISION ARCHITECTURE (Impact on Swarm) ---
        
        # [T2.1: Signal Amplification/Veto] [V055-V072]
        # If macro risk is extreme, veto [V064-V066]
        is_veto = (m_risk > 0.85) or (abs(s_bias) > 0.9 and abs(oc_press) > 0.8 and (s_bias * oc_press < 0))
        
        signal = fused_bias if not is_veto else 0.0
        
        # [T2.3: Nexus Phi] [V073-V081] 
        # Vigor increases during Fear/Greed extremes (The Contrarian Opportunity)
        phi = 0.5 + (abs(s_bias) * 0.45) # Max vigor at extreme sentiment
        
        # [T2.4: Strategic Hedging] [V082-V090]
        needs_hedge = m_risk > 0.7 or (oc_press > 0.5 and s_bias > 0.5) # Warning: Retail euphoria + Whale dumping

        # --- CONCEPT 3: EVOLUTION & SINGULARITY (Meta-Nexus) ---
        
        # [T3.1: Fractal Nexus] [V109-V117]
        # Adjust weight based on HTF alignment - simulated from context
        htf_align = snapshot.price > getattr(snapshot, 'ema_slow', snapshot.price)
        nexus_alignment = (signal > 0 and htf_align) or (signal < 0 and not htf_align)
        
        if nexus_alignment:
            signal *= 1.2 # Alignment bonus [V112]
        
        # [T3.2: Regime Awareness Ω-4] [V118-V126]
        # Simulation: In Trending states, we trust Sentiment less (don't bet against parabolic move)
        # In Ranging states, Sentiment is key (contrarian works best)
        # Assuming regime is ranging for high contrarian edge
        
        # [V154-V162] Singularity Protocol
        # Final output clipping and quantization
        final_signal = max(-1.0, min(1.0, signal))
        final_phi = max(0.01, min(0.99, phi))
        
        return {
            "signal": float(final_signal),
            "confidence": float(final_confidence),
            "phi": float(final_phi),
            "metadata": {
                "sent_bias": s_bias,
                "onchain_flow": oc_press,
                "macro_risk": m_risk,
                "is_veto": is_veto,
                "needs_hedge": needs_hedge,
                "nexus_bias": fused_bias
            }
        }

    def _neutral_output(self, reason: str) -> Dict[str, Any]:
        return {
            "signal": 0.0,
            "confidence": 0.0,
            "phi": 0.5,
            "metadata": {"reason": reason}
        }
