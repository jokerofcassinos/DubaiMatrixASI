import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

@dataclass
class SynapseStats:
    """[Ω-MVT] Internal performance metrics for each agent."""
    wins: int = 0
    losses: int = 0
    total_trades: int = 0
    avg_confidence: float = 0.0
    last_signal_time: float = 0.0
    uptime_start: float = field(default_factory=time.time)

    @property
    def win_rate(self) -> float:
        return self.wins / self.total_trades if self.total_trades > 0 else 0.5

class BaseSynapse(ABC):
    """
    [Ω-SYNAPSE] Base Class for SOLÉNN Specialized Agents.
    Supports asynchronous lifecycle, shared memory, and Thompson Sampling weightage.
    """

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"SOLENN.Synapse.{name}")
        self.stats = SynapseStats()
        self._is_active = True
        self.weight = 1.0 # Dynamic weight calibrated by Orchestrator
        
        # Bayesian Priors for Thompson Sampling (Alpha, Beta)
        self.alpha = 1.0
        self.beta = 1.0

    @abstractmethod
    async def process(self, snapshot: Any, nexus_context: Any = None) -> Dict[str, Any]:
        """
        [Ω-EXEC] Primary processing loop for the agent.
        Must return a dict with 'signal', 'confidence', and 'phi'.
        """
        pass

    async def update_performance(self, success: bool):
        """[Ω-EVOLVE] Update Bayesian priors based on trade outcome."""
        self.stats.total_trades += 1
        if success:
            self.stats.wins += 1
            self.alpha += 1.0
        else:
            self.stats.losses += 1
            self.beta += 1.0
            
    def get_sample_weight(self) -> float:
        """[Ω-QUANTUM] Thompson Sampling: returns a sample from Beta distribution."""
        import numpy as np
        return np.random.beta(self.alpha, self.beta)

    def heartbeat(self) -> bool:
        """[Ω-SRE] Health Check."""
        return self._is_active

    async def shutdown(self):
        """Graceful termination."""
        self._is_active = False
        self.logger.info(f"🌑 Synapse {self.name} going dark.")
