"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — AGENT BASE & SIGNAL                         ║
║     Estruturas fundamentais compartilhadas por todos os agentes.            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import Optional
from dataclasses import dataclass

from utils.math_tools import MathEngine


@dataclass
class AgentSignal:
    """Sinal emitido por um agente neural."""
    agent_name: str
    signal: float         # [-1.0 (SELL), 0.0 (NEUTRAL), +1.0 (BUY)]
    confidence: float     # [0.0 - 1.0]
    reasoning: str
    weight: float = 1.0
    timeframe: str = ""

    @property
    def weighted_signal(self) -> float:
        return self.signal * self.confidence * self.weight


class BaseAgent:
    """Classe base para todos os agentes neurais."""

    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight
        self.math = MathEngine()
        self._accuracy_history = []
        self._signal_history = []
        # Flag: se True, o NeuralSwarm passa orderflow_analysis como 2o arg
        self.needs_orderflow = False

    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        """Override nos agentes específicos."""
        raise NotImplementedError

    def record_accuracy(self, was_correct: bool):
        self._accuracy_history.append(1.0 if was_correct else 0.0)
        if len(self._accuracy_history) > 200:
            self._accuracy_history = self._accuracy_history[-200:]

    @property
    def accuracy(self) -> float:
        if not self._accuracy_history:
            return 0.5
        return sum(self._accuracy_history) / len(self._accuracy_history)
