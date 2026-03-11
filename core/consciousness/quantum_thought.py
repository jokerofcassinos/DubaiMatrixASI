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
    coherence: float            # Coerência inter-agent [0, 1]
    entropy: float              # Entropia do sistema de agentes
    superposition: bool         # Ainda em superposição?
    decision_vector: np.ndarray # Vetor de decisão n-dimensional
    agent_contributions: dict   # Contribuição de cada agente
    agent_signals: List[AgentSignal] # Sinais originais dos agentes (Phase 46 Fix)
    phi: float                  # Métrica de Consciência Sistêmica (Phase Ω-Extreme)
    metadata: dict              # Metadados adicionais para logs e diagnóstico (Phase 51 Fix)
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
                snapshot=None,
                regime_weight: float = 1.0,
                v_pulse_detected: bool = False) -> Optional[QuantumState]:
        """
        Processa sinais de todos os agentes e colapsa o estado quântico.

        Args:
            signals: Lista de AgentSignals do NeuralSwarm
            snapshot: Snapshot atual do mercado (Phase 51 Fix)
            regime_weight: Multiplicador do regime (agressividade)
            v_pulse_detected: [PHASE 48] V-Pulse detectado pelo RegimeDetector

        Returns:
            QuantumState com a decisão emergente
        """
        if not signals:
            return self._empty_state("NO_SIGNALS")

        # [Phase 51] Initialize reasoning append string
        v_pulse_reasoning_append = ""

        # Extrair sentimento se o snapshot estiver disponível
        sentiment_score = 0.0
        if snapshot:
            sentiment_score = snapshot.metadata.get("sentiment_score", 0.0)

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
                    s.weight *= 2.5  # Boost Phase Ω-Extreme
                    s.reasoning += " [!INSTITUTIONAL_CLARITY_BOOST!]"
                
            # [PHASE Ω-EXTREME] Entropic Resonance Filter
            # Se a entropia sistêmica é alta (>0.8) mas os institucionais estão convergindo (>0.8),
            # nós filtramos o ruído matemático e confiamos no Smart Money.
            if len(inst_signals) >= 2 and inst_coherence > 0.80:
                for s in math_signals:
                    if (s.signal > 0 and inst_bull < inst_bear) or (s.signal < 0 and inst_bull > inst_bear):
                         s.weight *= 0.1 # Esmaga ruído contrário aos institucionais no caos
                         s.reasoning += " [!ENTROPIC_FILTER: NOISE CRUSHED!]"

        # ═══ [OMEGA INJECTION] PHASE 30: FREIGHT TRAIN OVERRIDE ═══
        # Se a velocidade cinética e a agressividade formam um "Trem-Bala",
        # a barreira do Smart Money e o suporte/resistência viram vidro (Glass Support).
        freight_train_bull = any(s.agent_name in ["PriceVelocityAgent", "AggressivenessAgent", "MomentumAgent"] and s.signal > 0.85 for s in valid_signals)
        freight_train_bear = any(s.agent_name in ["PriceVelocityAgent", "AggressivenessAgent", "MomentumAgent"] and s.signal < -0.85 for s in valid_signals)
        
        if freight_train_bull:
            # PHASE 40: Elasticity Sovereignty (Trem-Bala não atropela Elástico Esticado)
            extreme_tension_bear = any(s.agent_name in ["PremiumDiscountAgent", "PriceGravityAgent"] and s.signal < -0.8 for s in valid_signals)
            
            # PHASE 45: Liquidity Hunt Detection (Bullish Expansion in Bear Regime)
            # Se estamos subindo forte para limpar liquidez (Vacuum/Explosion), esmagamos qualquer sinal Bear local.
            liquidity_hunt_bull = any(s.agent_name in ["LiquidationVacuumAgent", "ExplosionDetectorAgent"] and s.signal > 0.7 for s in valid_signals)

            for s in valid_signals:
                if s.agent_name in ["SRAgent", "PremiumDiscountAgent", "OrderBlockAgent", "LiquidityHeatmapAgent"] and s.signal < -0.3:
                    if extreme_tension_bear:
                        s.weight *= 2.0  # Boost: A estrutura é a última linha de defesa
                        s.reasoning += " [!SOVEREIGN_IMMUNITY: ELASTICITY OVERRIDES FREIGHT TRAIN!]"
                    else:
                        s.weight *= 0.05 # Esmagado: Em caça à liquidez, a resistência vira papel.
                        s.reasoning += " [!WEIGHT_CRUSHED: FREIGHT TRAIN PIERCING RESISTANCE!]"
                
                # VETO TOTAL sobre agentes Bear durante Trem-Bala de Alta
                if s.signal < -0.2:
                    if liquidity_hunt_bull:
                        s.weight *= 0.01  # Aniquilação total do sinal oposto
                        s.reasoning += " [!TRAP_VETO: LIQUIDITY HUNT UNSTOPPABLE BULL MOMENTUM!]"
                    else:
                        s.weight *= 0.1
                        s.reasoning += " [!WEIGHT_DAMPENED: AGAINST FREIGHT TRAIN!]"
                    
        if freight_train_bear:
            # PHASE 40: Elasticity Sovereignty
            extreme_tension_bull = any(s.agent_name in ["PremiumDiscountAgent", "PriceGravityAgent"] and s.signal > 0.8 for s in valid_signals)
            
            # PHASE 45: Liquidity Hunt Detection (Bearish Expansion)
            liquidity_hunt_bear = any(s.agent_name in ["LiquidationVacuumAgent", "ExplosionDetectorAgent"] and s.signal < -0.7 for s in valid_signals)

            for s in valid_signals:
                if s.agent_name in ["SRAgent", "PremiumDiscountAgent", "OrderBlockAgent", "LiquidityHeatmapAgent"] and s.signal > 0.3:
                    if extreme_tension_bull:
                        s.weight *= 2.0  # Boost
                        s.reasoning += " [!SOVEREIGN_IMMUNITY: ELASTICITY OVERRIDES FREIGHT TRAIN!]"
                    else:
                        s.weight *= 0.05
                        s.reasoning += " [!WEIGHT_CRUSHED: FREIGHT TRAIN SHATTERING SUPPORT!]"

                # VETO TOTAL sobre agentes Bull durante Trem-Bala de Baixa
                if s.signal > 0.2:
                    if liquidity_hunt_bear:
                        s.weight *= 0.01
                        s.reasoning += " [!TRAP_VETO: LIQUIDITY HUNT UNSTOPPABLE BEAR MOMENTUM!]"
                    else:
                        s.weight *= 0.1
                        s.reasoning += " [!WEIGHT_DAMPENED: AGAINST FREIGHT TRAIN!]"


        # ═══ [OMEGA INJECTION] SMART MONEY TRAP VETO / INVERSION (Phase 27) ═══
        # Retail Vende Suporte. Smart Money Compra Suporte.
        # Se agentes do Smart Money convergirem para forte rejeição (Trap), esmagar inércia de Varejo.
        # EXCEÇÃO: Se um Trem-Bala (Freight Train) estiver em curso na direção oposta, o Smart Money Trap
        #          é ignorado pois o suporte NÃO VAI SEGURAR.
        smc_trap_bull = sum(1 for s in valid_signals if s.agent_name in ["OrderBlockAgent", "PremiumDiscountAgent", "LiquidationVacuumAgent", "SRAgent", "LiquidationSweepAgent"] and s.signal > 0.5)
        smc_trap_bear = sum(1 for s in valid_signals if s.agent_name in ["OrderBlockAgent", "PremiumDiscountAgent", "LiquidationVacuumAgent", "SRAgent", "LiquidationSweepAgent"] and s.signal < -0.5)

        if smc_trap_bull >= 2 and not freight_train_bear:
            for s in valid_signals:
                if s.agent_name in ["TrendAgent", "MomentumAgent", "PriceVelocityAgent", "SentimentFearGreedAgent", "ChartStructureAgent", "MicrostructureAgent"]:
                    if s.signal < -0.1:
                        s.weight *= 0.05  # Esmaga em 95% a força (Morte da heurística burra)
                        s.reasoning += " [!TRAP_VETO: SMART MONEY BUYING SUPPORT!]"
                        
        if smc_trap_bear >= 2 and not freight_train_bull:
            for s in valid_signals:
                if s.agent_name in ["TrendAgent", "MomentumAgent", "PriceVelocityAgent", "SentimentFearGreedAgent", "ChartStructureAgent", "MicrostructureAgent"]:
                    if s.signal > 0.1:
                        s.weight *= 0.05  # Esmaga em 95% a força 
                        s.reasoning += " [!TRAP_VETO: SMART MONEY SELLING RESISTANCE!]"


        # ═══ [OMEGA INJECTION] PHASE 48: V-PULSE_LOCK / IGNITION SOVEREIGNTY ═══
        # Se o RegimeDetector detectou um V-Pulse (Ignition), o ruído é proscrito.
        # Os agentes de ignição (Explosion, Velocity, Aggressiveness) ganham soberania absoluta.
        if v_pulse_detected:
            ignition_agents = ["ExplosionDetectorAgent", "PriceVelocityAgent", "AggressivenessAgent", "LiquidationVacuumAgent"]
            dominant_dir = 1.0 if any(s.agent_name in ignition_agents and s.signal > 0.7 for s in valid_signals) else -1.0
            
            for s in valid_signals:
                if s.agent_name in ignition_agents and s.signal * dominant_dir > 0.5:
                    s.weight *= 5.0 # Boost massivo de autoridade
                    s.reasoning += " [!V-PULSE_LOCK: IGNITION SOVEREIGNTY!]"
                elif s.signal * dominant_dir < -0.1:
                    s.weight *= 0.001 # Aniquilação total de sinal contrário
                    s.reasoning += " [!V-PULSE_LOCK: CONTRARY NOISE ANNIHILATED!]"


        # ═══ [OMEGA INJECTION] KINEMATIC & STRUCTURAL DIVERGENCE (Phase 29/48) ═══
        # [PHASE 48 REFINEMENT]: Soberania de Ignição. 
        # Se houver uma explosão real confirmada por V-Pulse no regime, 
        # o dampening estrutural é relaxado para permitir breakouts.
        ignition_sovereign = any(s.agent_name in ["ExplosionDetectorAgent", "PriceVelocityAgent"] and abs(s.signal) > 0.9 for s in valid_signals)
        
        aggr_bull = any(s.agent_name in ["AggressivenessAgent", "PriceVelocityAgent", "ExplosionDetectorAgent"] and s.signal > 0.8 for s in valid_signals)
        aggr_bear = any(s.agent_name in ["AggressivenessAgent", "PriceVelocityAgent", "ExplosionDetectorAgent"] and s.signal < -0.8 for s in valid_signals)
        
        struct_bear = any(s.agent_name in ["ChartStructureAgent", "MarketStructureShiftAgent", "OrderBlockAgent", "LiquidityHeatmapAgent"] and s.signal < -0.3 for s in valid_signals)
        struct_bull = any(s.agent_name in ["ChartStructureAgent", "MarketStructureShiftAgent", "OrderBlockAgent", "LiquidityHeatmapAgent"] and s.signal > 0.3 for s in valid_signals)
        
        if aggr_bull and not struct_bull:
            damp_factor = 0.5 if ignition_sovereign else 0.1 # Suavizado se houver ignição
            for s in valid_signals:
                if s.agent_name in ["MomentumAgent", "PriceVelocityAgent", "AggressivenessAgent", "ExplosionDetectorAgent"]:
                    if s.signal > 0.4:
                        s.weight *= damp_factor
                        s.reasoning += f" [!STRUCTURAL DIVERGENCE DAMPENED ({damp_factor})!]"
                        
        if aggr_bear and not struct_bear:
            damp_factor = 0.5 if ignition_sovereign else 0.1
            for s in valid_signals:
                if s.agent_name in ["MomentumAgent", "PriceVelocityAgent", "AggressivenessAgent", "ExplosionDetectorAgent"]:
                    if s.signal < -0.4:
                        s.weight *= damp_factor
                        s.reasoning += f" [!STRUCTURAL DIVERGENCE DAMPENED ({damp_factor})!]"

        # ═══ [OMEGA INJECTION] PHASE 33: ADAPTIVE ELASTIC SNAPBACK VETO (Multi-Agent Strain) ═══
        # Proteção contra vender no fundo absoluto da corda esticada ou comprar no topo exausto.
        # Mede a tensão elástica combinada de agentes de anomalia, reversão e estrutura.
        # Se pelo menos 2 agentes do núcleo de estrutura/reversão acendem o alarme (Mesmo que fraco > 0.3),
        # a tensão do elástico é massiva e o Momentum será asfixiado.
        snap_bull_agents = sum(1 for s in valid_signals if s.agent_name in ["StatisticalAgent", "PriceGravityAgent", "CandleAnatomyAgent", "PremiumDiscountAgent"] and s.signal > 0.3)
        snap_bear_agents = sum(1 for s in valid_signals if s.agent_name in ["StatisticalAgent", "PriceGravityAgent", "CandleAnatomyAgent", "PremiumDiscountAgent"] and s.signal < -0.3)

        if snap_bull_agents >= 2:
            for s in valid_signals:
                if s.agent_name in ["TrendAgent", "MomentumAgent", "PriceVelocityAgent", "MicrostructureAgent", "OscillationWaveAgent"]:
                    if s.signal < -0.3:  # Tentativa de vender na inércia com o elástico trincando
                        s.weight *= 0.1  # Esmagamento de 90% da autoridade do momentum
                        s.reasoning += " [!TRAP_VETO: ELASTIC SNAPBACK (Multi-Agent Strain Up)!]"

        if snap_bear_agents >= 2:
            for s in valid_signals:
                if s.agent_name in ["TrendAgent", "MomentumAgent", "PriceVelocityAgent", "MicrostructureAgent", "OscillationWaveAgent"]:
                    if s.signal > 0.3:   # Tentativa de comprar na inércia com o elástico trincando
                        s.weight *= 0.1  # Esmagamento de 90% da autoridade do momentum
                        s.reasoning += " [!TRAP_VETO: ELASTIC SNAPBACK (Multi-Agent Strain Down)!]"

        # ═══ [OMEGA INJECTION] PHASE 32: DEAD CAT BOUNCE / COUNTER-TREND VETO ═══
        # Impede a ASI de comprar o repique em uma tendência de baixa (Dead Cat Bounce)
        # ou vender o recuo em uma tendência de alta (Bull Trap Pullback).
        # A Macro Tendência (Trend + Momentum base) aniquila a excitação microscópica oposta.
        macro_trend_bear = any(s.agent_name in ["TrendAgent", "MomentumAgent"] and s.signal < -0.3 for s in valid_signals)
        macro_trend_bull = any(s.agent_name in ["TrendAgent", "MomentumAgent"] and s.signal > 0.3 for s in valid_signals)

        if macro_trend_bear:
            for s in valid_signals:
                if s.agent_name in ["ChartStructureAgent", "PriceVelocityAgent", "PriceGravityAgent", "InformationEntropyAgent", "LiquidationVacuumAgent", "OrderBlockAgent"]:
                    if s.signal > 0.4: # Tentativa de comprar o repique na tendência de baixa
                        s.weight *= 0.1
                        s.reasoning += " [!TRAP_VETO: DEAD CAT BOUNCE (Counter-Trend Peak)!]"

        if macro_trend_bull:
            for s in valid_signals:
                if s.agent_name in ["ChartStructureAgent", "PriceVelocityAgent", "PriceGravityAgent", "InformationEntropyAgent", "LiquidationVacuumAgent", "OrderBlockAgent"]:
                    if s.signal < -0.4: # Tentativa de vender o recuo na tendência de alta
                        s.weight *= 0.1
                        s.reasoning += " [!TRAP_VETO: COUNTER-TREND DIP (Bull Trap Pullback)!]"

        # ═══════════════════════════════════════════════════
        #  PHASE 51: SENTIMENT-DRIVEN REBALANCING (Trap Protection)
        # ═══════════════════════════════════════════════════
        sentiment_score = snapshot.metadata.get("sentiment_score", 0.0)
        
        # Se estamos em Extreme Fear (< -0.8) ou Extreme Greed (> 0.8)
        if abs(sentiment_score) > 0.8:
            is_extreme_fear = sentiment_score < -0.8
            for s in valid_signals:
                # Enfraquece agentes que seguem a multidão (Trend/BOS) em extremos
                if s.agent_name in ["TrendAgent", "BOSAgent", "ChartStructureAgent", "MomentumAgent"]:
                    s.weight *= 0.4
                    s.reasoning += f" [!REBALANCED: EXTREME_{'FEAR' if is_extreme_fear else 'GREED'} SENTIMENT]"
                
                # Fortalece agentes de reversão e inteligência superior
                if s.agent_name in ["LiquidStateAgent", "PriceGravityAgent", "LiquidationVacuumAgent", "DarkMassAgent"]:
                    s.weight *= 2.5
                    s.reasoning += " [*BOOSTED: REVERSAL_CONVICTION]"

        # ═══ [OMEGA INJECTION] PHASE 52: ANTI-BEAR TRAP PROTECTION ═══
        # Proteção contra vender o 'fundo' ou 'sweep' (O que ocorreu no Cycle #3).
        # Se agentes de estrutura/gravidade estão FORTEMENTE BULLISH, ignoramos sinais de venda de inércia.
        rev_agents = ["OrderBlockAgent", "PriceGravityAgent", "LiquidStateAgent", "LiquidationVacuumAgent"]
        bullish_reversal_intensity = np.mean([s.signal for s in valid_signals if s.agent_name in rev_agents])
        
        if bullish_reversal_intensity > 0.4:
            for s in valid_signals:
                if s.agent_name in ["TrendAgent", "BOSAgent", "PressureMatrix", "MomentumAgent"]:
                    if s.signal < -0.1:
                        s.weight *= 0.02 # Esmagamento de 98%
                        s.reasoning += " [!BEAR_TRAP_VETO: INSTITUTIONAL REVERSAL DETECTED!]"

        # ═══ [OMEGA INJECTION] PHASE 52: LEADING-LAGGING DIVERGENCE BOOST ═══
        # Se os agentes 'Leading' (LiquidState, NavierStokes, PriceGravity) convergem contra
        # os agentes 'Lagging' (Trend, Momentum), damos soberania aos Leading.
        leading_signals = [s for s in valid_signals if s.agent_name in ["LiquidStateAgent", "NavierStokesFluidAgent", "PriceGravityAgent", "LiquidationVacuumAgent"]]
        lagging_signals = [s for s in valid_signals if s.agent_name in ["TrendAgent", "MomentumAgent", "BOSAgent"]]
        
        if leading_signals and lagging_signals:
            l_vals = [ls.signal for ls in leading_signals]
            lag_vals = [lgs.signal for lgs in lagging_signals]
            leading_dir = np.sign(np.mean(l_vals))
            lagging_dir = np.sign(np.mean(lag_vals))
            
            if leading_dir != lagging_dir and abs(np.mean(l_vals)) > 0.4:
                for s in leading_signals:
                    s.weight *= 3.0 # Triplica autoridade
                    s.reasoning += " [*LEADING_SOVEREIGNTY: DIVERGENCE DETECTED]"
                for s in lagging_signals:
                    s.weight *= 0.2 # Reduz lagging
                    s.reasoning += " [!LAGGING_DAMPENED: DIVERGENCE!]"

        # ═══ [OMEGA INJECTION] PHASE 34: TREND-STRUCTURE ALIGNMENT VETO ═══
        # Defesa contra Bull Traps (Comprar repique em resistência).
        # Se a Tendência Macro E a Estrutura (OrderBlocks/SR) estão Alinhadas em Baixa,
        # qualquer tentativa de compra baseada em impulso local é asfixiada.
        macro_bear_alignment = any(s.agent_name == "TrendAgent" and s.signal < -0.3 for s in valid_signals) and \
                               any(s.agent_name in ["ChartStructureAgent", "OrderBlockAgent"] and s.signal < -0.2 for s in valid_signals)
        
        macro_bull_alignment = any(s.agent_name == "TrendAgent" and s.signal > 0.3 for s in valid_signals) and \
                               any(s.agent_name in ["ChartStructureAgent", "OrderBlockAgent"] and s.signal > 0.2 for s in valid_signals)

        if macro_bear_alignment:
            for s in valid_signals:
                if s.agent_name in ["MomentumAgent", "PriceVelocityAgent", "AggressivenessAgent", "ExplosionDetectorAgent"]:
                    if s.signal > 0.1:  # Tentativa de comprar contra Trend+Structure
                        s.weight *= 0.1
                        s.reasoning += " [!TRAP_VETO: TREND-STRUCTURE MISALIGNMENT (Pullback at Resistance)!]"

        if macro_bull_alignment:
            for s in valid_signals:
                if s.agent_name in ["MomentumAgent", "PriceVelocityAgent", "AggressivenessAgent", "ExplosionDetectorAgent"]:
                    if s.signal < -0.1: # Tentativa de vender contra Trend+Structure
                        s.weight *= 0.1
                        s.reasoning += " [!TRAP_VETO: TREND-STRUCTURE MISALIGNMENT (Pullback at Support)!]"

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
            
        # ═══ 3. AGREGANDO VIA C++ (BLAZING FAST — Phase 41) ═══
        # Coletamos os parâmetros dinâmicos do OMEGA
        buy_threshold = OMEGA.get("buy_threshold", 0.7)
        convergence_threshold = OMEGA.get("convergence_threshold", 0.75)
        interference_weight = OMEGA.get("quantum_interference_weight", 0.5)
        decay_factor = OMEGA.get("quantum_decay_factor", 1.0)
        
        cpp_result = CPP_CORE.converge_signals(
            valid_signals, 
            interference_weight=interference_weight,
            decay=decay_factor
        )
        
        if not cpp_result:
            return self._empty_state("CPP_CONVERGENCE_FAILED")

        raw_signal = cpp_result["signal"]
        coherence = cpp_result["coherence"]
        system_entropy = cpp_result["entropy"]
        comp_time_cpp = cpp_result["time_ms"]
        
        # ═══════════════════════════════════════════════════
        #  PHASE 52: STRICT COHERENCE FILTER (After Convergence)
        # ═══════════════════════════════════════════════════
        # Se a coerência é baixa (< 0.40), o enxame está em 'guerra civil'.
        # Com 110 agentes, uma coerência de 0.45 já indica um consenso direcional forte.
        # Nesses casos de caos total (<0.40), aplicamos um redutor global no sinal bruto.
        if coherence < 0.40 and not v_pulse_detected:
            raw_signal *= 0.5 # Asfixia a força da decisão se não há harmonia
            v_pulse_reasoning_append += " [!LOW_COHERENCE_DAMPENING!]"
        
        # ═══ 4. CONSCIOUSNESS METRICS (Φ) — Phase Ω-Extreme ═══
        phi_metrics = CPP_CORE.calculate_phi(valid_signals)
        phi_val = phi_metrics["phi"] if phi_metrics else 0.0
        
        # ═══ 5. COHERENCE BOOST & COLLAPSE POLICY ═══
        # Se a coerência é alta (>0.7), damos um boost na confiança (Efeito Enxame)
        if coherence > 0.70:
            boost = (coherence - 0.70) * 0.5  # Max boost de +0.15 para coerência 1.0
            avg_confidence = min(1.0, avg_confidence + boost)
            
        # Override de segurança adicional (Python layer policy)
        confidence_min_val = OMEGA.get("confidence_min", 0.70) # Usar 0.70 como base
        
        # Se coerência > 0.85 (unanimidade), somos mais permissivos no threshold
        if coherence > 0.85:
            confidence_min_val *= 0.9
            
        # [OMEGA REFINEMENT] Natural Collapse Check
        # O estado colapsa naturalmente se tiver confiança E sinal suficientes.
        # [PHASE 48]: Se v_pulse_detected, o colapso é forçado com thresholds relaxados.
        natural_collapse = (avg_confidence >= (confidence_min_val * 0.8 if v_pulse_detected else confidence_min_val)) and \
                           (abs(raw_signal) >= (buy_threshold * 0.7 if v_pulse_detected else buy_threshold))

        if natural_collapse:
            collapsed_signal = raw_signal
            superposition = False
            if v_pulse_detected:
                v_pulse_reasoning_append = " [V-PULSE FORCED COLLAPSE]"
        elif OMEGA.get("superposition_resolution_enabled", 0.0) > 0.5:
            # ═══ PHASE 46: SUPERPOSITION RESOLUTION MOTOR ═══
            # Se não colapsou naturalmente, as mentes "brigaram". 
            # Mas se houver uma coerência institucional ou bias de regime, nós resolvemos.
            resolution = self.solve_superposition(
                valid_signals, raw_signal, avg_confidence, coherence, system_entropy
            )
            
            if resolution and resolution["resolved"]:
                collapsed_signal = resolution["signal"]
                avg_confidence = resolution["confidence"]
                superposition = False
            else:
                collapsed_signal = 0.0
                superposition = True
        else:
            collapsed_signal = 0.0  # WAIT
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

        # ═══ [PHASE 52] METADATA COLLECTION ═══
        # Capturamos os contribuidores de elite (peso * sinal)
        sorted_bull = sorted(
            [s for s in valid_signals if s.signal > 0], 
            key=lambda x: x.weight * x.signal, 
            reverse=True
        )
        sorted_bear = sorted(
            [s for s in valid_signals if s.signal < 0], 
            key=lambda x: x.weight * abs(x.signal), 
            reverse=True
        )

        top_bulls = [s.agent_name for s in sorted_bull[:3]]
        top_bears = [s.agent_name for s in sorted_bear[:3]]

        # Reasoning compacto e cirúrgico
        reasoning = (
            f"SIGNAL={raw_signal:+.3f} | CONF={avg_confidence:.2f} | Φ={phi_val:.2f} | "
            f"COH={coherence:.2%}"
            + (f" | BULL: {', '.join(top_bulls)}" if raw_signal > 0 else "")
            + (f" | BEAR: {', '.join(top_bears)}" if raw_signal < -0.1 else "")
            + v_pulse_reasoning_append
        )

        # ═══ [PHASE 50] GOD-MODE SANCTUARY SYNC ═══
        # Se detectamos um vácuo de liquidação com alta confiança e a entropia é alta,
        # sinalizamos para o TrinityCore que este é um candidato a God-Mode Reversal.
        is_vacuum_gate = any(s.agent_name == "LiquidationVacuumAgent" and s.confidence > 0.85 for s in valid_signals)
        is_god_candidate = (system_entropy > 0.80 or v_pulse_detected) and is_vacuum_gate

        state = QuantumState(
            raw_signal=raw_signal,
            collapsed_signal=collapsed_signal,
            confidence=avg_confidence,
            coherence=coherence,
            entropy=system_entropy,
            superposition=superposition,
            decision_vector=decision_vector,
            agent_contributions=agent_contributions,
            agent_signals=valid_signals,
            phi=phi_val,
            metadata={
                "bull_agents": [s.agent_name for s in sorted_bull],
                "bear_agents": [s.agent_name for s in sorted_bear],
                "top_bulls": top_bulls,
                "top_bears": top_bears,
                "phi": phi_val,
                "coherence": coherence,
                "entropy": system_entropy,
                "is_god_candidate": is_god_candidate
            },
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

    @catch_and_log(default_return=None)
    def solve_superposition(self, signals: List[AgentSignal], raw_signal: float, 
                           confidence: float, coherence: float, entropy: float) -> dict:
        """
        Tenta resolver o estado de superposição (discordância) entre agentes.
        Aplica 5 lógicas ASI para forçar a decoerência se houver um bias oculto.
        """
        resolution = {"resolved": False, "signal": 0.0, "confidence": confidence, "method": ""}
        
        # Thresholds de resolução
        conf_mult = OMEGA.get("resolution_confidence_multiplier", 1.2)
        inst_thresh = OMEGA.get("institutional_superiority_threshold", 0.75)
        max_entropy = OMEGA.get("max_resolution_entropy", 0.65)
        
        # ═══ 1. ISO: INSTITUTIONAL SUPERIORITY OVERRIDE ═══
        # Se os agentes institucionais estão muito coerentes e com peso forte, 
        # eles vencem a discordância matemática.
        inst_agents = {
            "WhaleTrackerAgent", "IcebergHunterAgent", "StopHunterAgent", 
            "InstitutionalFootprintAgent", "LiquidityHeatmapAgent", "OrderBlockAgent",
            "LiquidationVacuumAgent", "AggressivenessAgent"
        }
        inst_sigs = [s for s in signals if s.agent_name in inst_agents and abs(s.signal) > 0.2]
        
        if len(inst_sigs) >= 3:
            # Cálculo ponderado pelo peso do agente (autoridade)
            total_weight = sum(s.weight for s in inst_sigs)
            if total_weight > 0:
                weighted_avg_inst = sum(s.signal * s.weight for s in inst_sigs) / total_weight
                inst_bull = sum(1 for s in inst_sigs if s.signal > 0)
                inst_bear = sum(1 for s in inst_sigs if s.signal < 0)
                inst_coh = max(inst_bull, inst_bear) / len(inst_sigs)
                
                # Critério de Superioridade: Coerência > 75% E sinal ponderado > 0.65
                if inst_coh >= inst_thresh and abs(weighted_avg_inst) > 0.65:
                    resolution["resolved"] = True
                    resolution["signal"] = 1.0 if weighted_avg_inst > 0 else -1.0
                    resolution["confidence"] = min(0.95, confidence * conf_mult)
                    resolution["method"] = f"INSTITUTIONAL_WEIGHTED({weighted_avg_inst:.2f})"
                    return resolution

        # ═══ 2. RAD: REGIME-ANCHORED DECOHERENCE ═══
        # Se o sinal bruto está alinhado com o momentum do regime, resolvemos a favor do regime.
        # (Nota: O regime_weight já foi aplicado aos sinais, aqui verificamos a direção dominante)
        if abs(raw_signal) > 0.15 and entropy < max_entropy:
            resolution["resolved"] = True
            resolution["signal"] = raw_signal
            resolution["confidence"] = min(0.95, confidence * conf_mult * 0.9)
            resolution["method"] = "REGIME_ANCHORED"
            return resolution

        # ═══ 3. TTC: TEMPORAL TUNNELING (Persistence Check) ═══
        # Se as últimas 5 superposições tiveram o mesmo sinal bruto, colapsamos por persistência.
        if len(self._state_history) >= 5:
            last_signals = [h["signal"] for h in self._state_history[-5:]]
            if all(s > 0 for s in last_signals) or all(s < 0 for s in last_signals):
                resolution["resolved"] = True
                resolution["signal"] = raw_signal
                resolution["confidence"] = min(0.90, confidence * conf_mult * 0.8)
                resolution["method"] = "TEMPORAL_TUNNELING"
                return resolution

        return resolution

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
            agent_signals=[],
            phi=0.0,
            metadata={"bull_agents": [], "bear_agents": []},
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
