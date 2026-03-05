"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — QUANTUM THOUGHT ENGINE                ║
║     Pensamento em milhões de dimensões — superposição → colapso            ║
║                                                                              ║
║  Cada agente gera um vetor. Os vetores interferem entre si como             ║
║  ondas quânticas. O resultado é um estado coletivo que colapsa              ║
║  na decisão ótima quando a convergência atinge o threshold.                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass

from core.consciousness.neural_swarm import AgentSignal
from config.omega_params import OMEGA
from utils.math_tools import MathEngine
from utils.decorators import catch_and_log, asi_safe
from utils.logger import log
from cpp.asi_bridge import CPP_CORE


@dataclass
class QuantumState:
    """Estado quântico do pensamento coletivo da ASI."""
    raw_signal: float           # Sinal bruto [-1, +1]
    collapsed_signal: float     # Sinal após colapso
    confidence: float           # Confiança [0, 1]
    coherence: float            # Coerência inter-agente [0, 1]
    entropy: float              # Entropia do sistema de agentes
    superposition: bool         # Ainda em superposição?
    decision_vector: np.ndarray # Vetor de decisão n-dimensional
    agent_contributions: dict   # Contribuição de cada agente
    reasoning: str              # Explicação completa


class QuantumThoughtEngine:
    """
    Motor de Pensamento Quântico — transforma sinais de agentes em decisão.

    Paradigma:
    1. Cada agente = uma dimensão de análise
    2. Sinais coexistem em SUPERPOSIÇÃO
    3. Interferência construtiva: sinais alinhados se AMPLIFICAM
    4. Interferência destrutiva: sinais opostos se CANCELAM
    5. COLAPSO: quando coerência > threshold → decisão emerge
    6. Se coerência < threshold → PERMANECE em superposição (WAIT)
    """

    def __init__(self):
        self.math = MathEngine()
        self._last_state = None
        self._state_history = []

    @catch_and_log(default_return=None)
    def process(self, signals: List[AgentSignal],
                regime_weight: float = 1.0) -> Optional[QuantumState]:
        """
        Processa sinais de todos os agentes e colapsa o estado quântico.

        Args:
            signals: Lista de AgentSignals do NeuralSwarm
            regime_weight: Multiplicador do regime (agressividade)

        Returns:
            QuantumState com a decisão emergente
        """
        if not signals:
            return self._empty_state("NO_SIGNALS")

        # ═══ 1. SUPERPOSIÇÃO — todos os sinais coexistem ═══
        valid_signals = [s for s in signals if s.confidence > 0.01]
        if not valid_signals:
            return self._empty_state("NO_VALID_SIGNALS")

        # ═══ [OMEGA INJECTION] QUANTUM STRUCTURAL ENTANGLEMENT (Phase 20) ═══
        # A inércia (Momentum) é cega para a topologia (Estrutura).
        # A Estrutura modula a inércia, asfixiando falsos rompimentos (Smart Money Traps).
        structure_bear = any(s.agent_name in ["ChartStructureAgent", "MicrostructureAgent", "FairValueGapAgent", "LiquidityHeatmapAgent"] and s.signal < -0.5 for s in valid_signals)
        structure_bull = any(s.agent_name in ["ChartStructureAgent", "MicrostructureAgent", "FairValueGapAgent", "LiquidityHeatmapAgent"] and s.signal > 0.5 for s in valid_signals)
        
        for s in valid_signals:
            if s.agent_name in ["MomentumAgent", "PriceVelocityAgent", "BreakOfStructureAgent", "LiquidationVacuumAgent", "ExplosionDetectorAgent"]:
                if structure_bear and s.signal > 0.4:
                    s.weight *= 0.25  # Crush: 75% da autoridade eliminada
                    s.reasoning += " [!WEIGHT_CRUSHED by Overhead Resistance!]"
                elif structure_bull and s.signal < -0.4:
                    s.weight *= 0.25  # Crush: 75% da autoridade eliminada
                    s.reasoning += " [!WEIGHT_CRUSHED by Underlying Support!]"

        # ═══ [OMEGA INJECTION] CLUSTER ENTROPY MAPPING (Phase 21) ═══
        # Diferenciamos a entropia dos Institucionais da entropia dos Reativos Matemáticos
        institutional_agents = {
            "StopHunterAgent", "LiquidityHeatmapAgent", "CrossScaleConvergenceAgent",
            "LiquidationVacuumAgent", "AggressivenessAgent", "WhaleTrackerAgent",
            "IcebergHunterAgent", "FairValueGapAgent", "MarketStructureShiftAgent"
        }
        
        inst_signals = [s for s in valid_signals if s.agent_name in institutional_agents and abs(s.signal) > 0.1]
        math_signals = [s for s in valid_signals if s.agent_name not in institutional_agents and abs(s.signal) > 0.1]
        
        if len(inst_signals) >= 3 and len(math_signals) >= 5:
            inst_bull = sum(1 for s in inst_signals if s.signal > 0)
            inst_bear = sum(1 for s in inst_signals if s.signal < 0)
            inst_coherence = max(inst_bull, inst_bear) / len(inst_signals)
            
            math_bull = sum(1 for s in math_signals if s.signal > 0)
            math_bear = sum(1 for s in math_signals if s.signal < 0)
            math_coherence = max(math_bull, math_bear) / len(math_signals)
            
            if inst_coherence > 0.75 and math_coherence < 0.60:
                for s in inst_signals:
                    s.weight *= 2.0  # Boost
                    s.reasoning += " [!INSTITUTIONAL_CLARITY_BOOST!]"

        # ═══ [OMEGA INJECTION] SMART MONEY TRAP VETO / INVERSION (Phase 27) ═══
        # Retail Vende Suporte. Smart Money Compra Suporte.
        # Se agentes do Smart Money convergirem para forte rejeição (Trap), esmagar inércia de Varejo.
        smc_trap_bull = sum(1 for s in valid_signals if s.agent_name in ["OrderBlockAgent", "PremiumDiscountAgent", "LiquidationVacuumAgent", "SRAgent", "LiquidationSweepAgent"] and s.signal > 0.5)
        smc_trap_bear = sum(1 for s in valid_signals if s.agent_name in ["OrderBlockAgent", "PremiumDiscountAgent", "LiquidationVacuumAgent", "SRAgent", "LiquidationSweepAgent"] and s.signal < -0.5)

        if smc_trap_bull >= 2:
            for s in valid_signals:
                if s.agent_name in ["TrendAgent", "MomentumAgent", "PriceVelocityAgent", "SentimentFearGreedAgent", "ChartStructureAgent", "MicrostructureAgent"]:
                    if s.signal < -0.1:
                        s.weight *= 0.05  # Esmaga em 95% a força (Morte da heurística burra)
                        s.reasoning += " [!TRAP_VETO: SMART MONEY BUYING SUPPORT!]"
                        
        if smc_trap_bear >= 2:
            for s in valid_signals:
                if s.agent_name in ["TrendAgent", "MomentumAgent", "PriceVelocityAgent", "SentimentFearGreedAgent", "ChartStructureAgent", "MicrostructureAgent"]:
                    if s.signal > 0.1:
                        s.weight *= 0.05  # Esmaga em 95% a força 
                        s.reasoning += " [!TRAP_VETO: SMART MONEY SELLING RESISTANCE!]"

        # ═══ [OMEGA INJECTION] KINEMATIC & STRUCTURAL DIVERGENCE (Phase 29) ═══
        # Se os agentes cinéticos apontam ignição parabólica, MAS a estrutura global diverge ou é neutra.
        aggr_bull = any(s.agent_name in ["AggressivenessAgent", "PriceVelocityAgent", "ExplosionDetectorAgent"] and s.signal > 0.8 for s in valid_signals)
        aggr_bear = any(s.agent_name in ["AggressivenessAgent", "PriceVelocityAgent", "ExplosionDetectorAgent"] and s.signal < -0.8 for s in valid_signals)
        
        struct_bear = any(s.agent_name in ["ChartStructureAgent", "MarketStructureShiftAgent", "OrderBlockAgent", "LiquidityHeatmapAgent"] and s.signal < -0.3 for s in valid_signals)
        struct_bull = any(s.agent_name in ["ChartStructureAgent", "MarketStructureShiftAgent", "OrderBlockAgent", "LiquidityHeatmapAgent"] and s.signal > 0.3 for s in valid_signals)
        
        if aggr_bull and not struct_bull:
            for s in valid_signals:
                if s.agent_name in ["MomentumAgent", "PriceVelocityAgent", "AggressivenessAgent", "ExplosionDetectorAgent"]:
                    if s.signal > 0.4:
                        s.weight *= 0.1
                        s.reasoning += " [!TRAP: STRUCTURAL DIVERGENCE (Bull Burst vs Flat/Bear Structure)!]"
                        
        if aggr_bear and not struct_bear:
            for s in valid_signals:
                if s.agent_name in ["MomentumAgent", "PriceVelocityAgent", "AggressivenessAgent", "ExplosionDetectorAgent"]:
                    if s.signal < -0.4:
                        s.weight *= 0.1
                        s.reasoning += " [!TRAP: STRUCTURAL DIVERGENCE (Bear Burst vs Flat/Bull Structure)!]"

        # ═══ 2. CONVICTION-WEIGHTED CONFIDENCE (Phase 19) ═══
        # Ignora agentes neutros (signal=0) para evitar diluição da confiança média.
        active_signals = [s for s in valid_signals if abs(s.signal) > 0.1]
        
        if active_signals:
            # Pesos baseados na magnitude do sinal (mais convicção = mais peso na confiança)
            conviction_weights = [abs(s.signal) * s.weight for s in active_signals]
            avg_confidence = float(np.average([s.confidence for s in active_signals], 
                                             weights=conviction_weights))
        else:
            # Se ninguém tem convicção, a confiança é o piso dos neutros (geralmente baixa)
            avg_confidence = float(np.mean([s.confidence for s in valid_signals])) * 0.5
            
        # ═══ 3. AGREGANDO VIA C++ (BLAZING FAST) ═══
        cpp_signals = [{"signal": s.signal, "confidence": s.confidence, "weight": s.weight} for s in valid_signals]
        buy_threshold = OMEGA.get("buy_threshold", 0.7)
        convergence_threshold = OMEGA.get("convergence_threshold", 0.75)
        
        cpp_result = CPP_CORE.aggregate_signals(
            cpp_signals, regime_weight, 
            signal_threshold=buy_threshold,
            coherence_threshold=convergence_threshold
        )
        
        raw_signal = cpp_result["raw_signal"]
        coherence = cpp_result["coherence"]
        system_entropy = cpp_result["energy"]  # Energy no C++ funciona como proxy de entropia/força
        should_collapse = cpp_result["should_collapse"]
        
        # ═══ 5. COHERENCE BOOST & COLLAPSE POLICY ═══
        # Se a coerência é alta (>0.7), damos um boost na confiança (Efeito Enxame)
        if coherence > 0.70:
            boost = (coherence - 0.70) * 0.5  # Max boost de +0.15 para coerência 1.0
            avg_confidence = min(1.0, avg_confidence + boost)
            
        # Override de segurança adicional (Python layer policy)
        confidence_min_val = OMEGA.get("confidence_min", 0.65)
        
        # Se coerência > 0.85 (unanimidade), somos mais permissivos no threshold
        if coherence > 0.85:
            confidence_min_val *= 0.9
            
        if avg_confidence < confidence_min_val:
            should_collapse = False

        if should_collapse:
            collapsed_signal = raw_signal
            superposition = False
        else:
            collapsed_signal = 0.0  # WAIT — manter superposição
            superposition = True

        # ═══ 6. CONSTRUIR ESTADO ═══
        agent_contributions = {}
        for s in valid_signals:
            agent_contributions[s.agent_name] = {
                "signal": s.signal,
                "confidence": s.confidence,
                "weight": s.weight,
                "weighted": s.weighted_signal,
                "reasoning": s.reasoning,
            }

        # Decision vector (para análise multidimensional)
        decision_vector = np.array([s.weighted_signal for s in valid_signals])

        # Reasoning completo
        bull_agents = [s.agent_name for s in valid_signals if s.signal > 0.1]
        bear_agents = [s.agent_name for s in valid_signals if s.signal < -0.1]
        neutral_agents = [s.agent_name for s in valid_signals if abs(s.signal) <= 0.1]

        reasoning = (
            f"SIGNAL={raw_signal:+.3f} "
            f"COHERENCE={coherence:.2f} "
            f"CONFIDENCE={avg_confidence:.2f} "
            f"ENTROPY={system_entropy:.2f} "
            f"{'COLLAPSED' if not superposition else 'SUPERPOSITION'} | "
            f"BULL[{','.join(bull_agents)}] "
            f"BEAR[{','.join(bear_agents)}] "
            f"NEUTRAL[{','.join(neutral_agents)}]"
        )

        state = QuantumState(
            raw_signal=raw_signal,
            collapsed_signal=collapsed_signal,
            confidence=avg_confidence,
            coherence=coherence,
            entropy=system_entropy,
            superposition=superposition,
            decision_vector=decision_vector,
            agent_contributions=agent_contributions,
            reasoning=reasoning,
        )

        self._last_state = state
        self._state_history.append({
            "signal": raw_signal,
            "collapsed": collapsed_signal,
            "coherence": coherence,
            "superposition": superposition,
        })

        # Trim history
        if len(self._state_history) > 1000:
            self._state_history = self._state_history[-1000:]

        return state

    def _empty_state(self, reason: str) -> QuantumState:
        return QuantumState(
            raw_signal=0.0,
            collapsed_signal=0.0,
            confidence=0.0,
            coherence=0.0,
            entropy=0.0,
            superposition=True,
            decision_vector=np.array([0.0]),
            agent_contributions={},
            reasoning=reason,
        )

    @property
    def last_state(self) -> Optional[QuantumState]:
        return self._last_state

    def get_collapse_rate(self, lookback: int = 100) -> float:
        """% de estados que colapsaram nos últimos N ciclos."""
        history = self._state_history[-lookback:]
        if not history:
            return 0.0
        collapsed = sum(1 for h in history if not h["superposition"])
        return collapsed / len(history)
