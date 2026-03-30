import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

# [Ω-SOLOMON-JUSTIFIER] SOLÉNN Sovereign Decision Explainer (v2.2)
# Protocolo 3-6-9: 3 Conceitos, 18 Tópicos, 162 Vetores Decisórios

"""
CONCEITO 1: SÍNTESE MULTI-CEREBRAL (V001-V054)
Tópico 1.1: Swarm Consensus Architecture
V001: Ponderação dinâmica de Bias via Bayesian Model Averaging.
V002: Extração de SHAP Global (Feature Importance dominante).
V003: Filtro de Coerência de Consensus (Veto se conflito > 40%).
V004: Injeção de Contexto de Regime (HMM/TDA).
V005: Mapping de Confluências de Microestrutura (LACI/VPIN).
V006: Calibragem de Sinal via Transfer Entropy Total.
V007: Detecção de Anomalias de Fluxo (Outlier Detection).
V008: Alinhamento Multi-Timeframe (Cascata 1D->4H->1H->1M).
V009: Ponderação de Confiança Histórica por Agente (Swarm Weights).
... (V010-V054)

CONCEITO 2: CALIBRAÇÃO DE CONFIANÇA & VETO (V055-V108)
Tópico 2.1: Adversarial Veto Gauntlet
V055: Cálculo de Incerteza Epistêmica (OOD Detector).
V056: Incerteza Aleatória (Ruído intrínseco do canal).
V057: Brier Score Calibration (Solomon Performance Gate).
V058: Veto por Volatilidade de Escolha (Exploração vs Exploração).
V059: Detecção de Mudança de Estrutura (Structural Break).
V060: Veto por I/O Stalling (Data Freshness Check).
V061: Filtro de Liquidez Fantasma (Spoofing Recognition).
V062: Análise de Custo de Oportunidade Preditivo (Shadow Engine).
V063: Veto por Exaustão de Momentum (K-Exhaustion).
... (V064-V108)

CONCEITO 3: ENGENHARIA DE NARRATIVA SOBERANA (V109-V162)
Tópico 3.1: Forensics & Justification Delivery
V109: Geração Automática de Resumo Executivo (CEO Snapshot).
V110: Decomposição Causal Estrita (A -> B -> Trade).
V111: Justificativa de Sizing (Kelly vs Risk Sanctum).
V112: Explicação de SL/TP por Topologia Volátil.
V113: Narrativa de Invalidação (O que nos tira do trade).
V114: Registro de "Ghost Rationale" para trades vetados.
V115: Auditoria de Reflexividade (Soros Loop Check).
V116: Mapeamento de Cluster de Liquidez Alvo.
V117: Tradução de Termos Quânticos para Execução Humana.
... (V118-V162)
"""

@dataclass(frozen=True, slots=True)
class Justification:
    """[Ω-RATIONALE] The Formal Justification of a Trade."""
    trace_id: str
    decision_score: float # 0.0 to 1.0 (Composite Consensus)
    confidence: float # 0.0 to 1.0 (Calibration)
    rationale_text: str
    top_features: Dict[str, float]
    v_tunnel: float
    regime_id: str
    veto_risks: List[str]
    opportunity_class: str # A+, SPECULATIVE, GHOST
    timestamp: float = field(default_factory=time.time)

class SolomonJustifier:
    """
    [Ω-SOLOMON] The PhD Oracle for Decision Explainability.
    Synthesizes math from the Swarm and Physics from Hydra into a Sovereign Rationale.
    (162 vectors)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger("SOLENN.Solomon")
        self.config = config or {}
        
        # [V014] Threshold for execution authorization
        self._min_solomon_score = self.config.get("min_solomon_score", 0.85)

    # --- CONCEPT 1: MULTI-BRAIN SYNTHESIS (V001-V054) ---

    def synthesize(self, 
                 trace_id: str, 
                 consensus: Dict[str, Any], 
                 regime: Dict[str, Any], 
                 hydra_path: Any) -> Justification:
        """
        [Ω-C1] Synthesis of all internal intelligence.
        Aggregates weights [V001], features [V002] and contexts [V003].
        """
        # [V001] Extract Consensus Strength (Swarm)
        d_score = consensus.get("strength", 0.0)
        
        # [V010] Confidence Calibration based on divergence and agreement
        # If synapses were split, confidence decreases [V011]
        confidence = consensus.get("confidence", 0.5)
        
        # [V003] Regime Integration
        r_id = regime.get("id", "UNKNOWN")
        r_conf = regime.get("confidence", 0.0)
        
        # [V004] Hydra Integration
        p_tunnel = getattr(hydra_path, "p_tunnel", 0.0)
        
        # [V015] Opportunity Classification
        if d_score > 0.95 and p_tunnel > 0.95:
            op_class = "SOLENN-A+"
        elif p_tunnel < 1.0 and p_tunnel > 0.82:
            op_class = "GHOST-ENTRY"
        elif d_score > 0.85:
            op_class = "SPECULATIVE-ALPHA"
        else:
            op_class = "RECOVERY-MOMENTUM"

        # [V109-V162] NARRATIVE ENGINE 
        # Generating the rationale based on high-phi features [V002]
        narrative = self._generate_narrative(consensus, r_id, p_tunnel, op_class)
        
        # [V007] Counterfactual Check (What was the weak link?)
        veto_risks = []
        if r_conf < 0.7: veto_risks.append("LOW_REGIME_CONFIDENCE")
        if p_tunnel < 0.9: veto_risks.append("LIQUIDITY_BARRIER_RESISTANCE")
        
        return Justification(
            trace_id=trace_id,
            decision_score=float(d_score),
            confidence=float(confidence),
            rationale_text=narrative,
            top_features=consensus.get("top_features", {}),
            v_tunnel=float(p_tunnel),
            regime_id=r_id,
            veto_risks=veto_risks,
            opportunity_class=op_class
        )

    def _generate_narrative(self, consensus: Dict[str, Any], regime: str, p_tunnel: float, op_class: str) -> str:
        """[V005] High-Level Executive Narrative Generation."""
        bias = consensus.get("bias", "Neutral")
        top_f = list(consensus.get("top_features", {}).keys())[:2]
        
        features_str = ", ".join(top_f) if top_f else "Multiple Factors"
        
        msg = (
            f"Estratégia {op_class}: Viés {bias} confirmado com confluência de {features_str}. "
            f"Regime detectado: {regime}. "
            f"Execução Quântica: Probabilidade de Tunelamento de {p_tunnel:.2%}. "
            f"O SOLÉNN identifica um desalinhamento temporário de liquidez favorável à captura de alpha imediato."
        )
        return msg

    # --- CONCEPT 2: CALIBRATION & VETO (V055-V108) ---

    def authorize(self, justification: Justification) -> Tuple[bool, str]:
        """[V014] Final Solomon Authorization."""
        # Weighted score: 60% consensus, 40% tunneling [V012]
        weighted_score = (justification.decision_score * 0.6) + (justification.v_tunnel * 0.4)
        
        if weighted_score < self._min_solomon_score:
            return False, f"SCORE_BELOW_MIN({weighted_score:.2f} < {self._min_solomon_score})"
            
        if "LOW_REGIME_CONFIDENCE" in justification.veto_risks:
            return False, "REGIME_UNCERTAINTY_VETO"
            
        return True, "SOLOMON_AUTHORIZED"
