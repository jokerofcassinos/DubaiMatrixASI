"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — META-SWARM AGENTS                      ║
║           Agentes de Segunda Ordem: Analisam os próprios Agentes             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal
from utils.logger import log

class ConfidenceAggregatorAgent(BaseAgent):
    """
    Agente de Segunda Ordem (Phase 26).
    Seu trabalho não é olhar para o mercado, mas para a MENTE da ASI.
    Se múltiplos agentes primários estão gritando na mesma direção com +0.7, 
    ele consolida essa sinergia invisível e gera um meta-sinal de +0.85 ou mais.
    
    Isso quebra a barreira invisível onde 5 agentes têm quase-certeza, 
    mas a média diluída impede que a Confidence alcance o threshold de Lotes Grandes (0.8+).
    """
    
    def __init__(self):
        super().__init__(name="ConfidenceAggregator", weight=2.5) # Peso Massivo
        
    def analyze(self, snapshot, asi_state=None, **kwargs) -> AgentSignal:
        # Recupera o estado atual dos agentes (que roda no QuantumThoughtEngine)
        # Como o Quantum processa este agente junto com os outros, usamos os 
        # últimos vetores disponíveis (se injetados via asi_state).
        
        # Meta-Swarm: Por hora retornaremos neutro até o framework de injeção suportar agent_outputs puros,
        # ou podemos derivar a ressonância das próprias trends.
        
        # Fallback: Se o snapshot for muito limpo baseado em entropia baixa 
        # e alinhamento perfeito de EMAs, forçamos um boost de confiança independentemente.
        
        indicators = snapshot.indicators
        entropy = indicators.get("M5_entropy", [3.0])
        ent = entropy[-1] if isinstance(entropy, list) and entropy else 3.0
        
        ema_9 = indicators.get("M5_ema_9", [])
        ema_21 = indicators.get("M5_ema_21", [])
        ema_50 = indicators.get("M5_ema_50", [])
        
        if len(ema_9) > 0 and len(ema_21) > 0 and len(ema_50) > 0:
            bull_align = ema_9[-1] > ema_21[-1] > ema_50[-1]
            bear_align = ema_9[-1] < ema_21[-1] < ema_50[-1]
            
            # Se alinhamento é perfeito e entropia extremamente baixa (< 1.5), o caos está morto
            if ent < 1.5:
                if bull_align:
                    return AgentSignal(agent_name=self.name, signal=1.0, confidence=0.95, reasoning="Perfeito Alinhamento Bullish + Caos Morto", weight=self.weight)
                elif bear_align:
                    return AgentSignal(agent_name=self.name, signal=-1.0, confidence=0.95, reasoning="Perfeito Alinhamento Bearish + Caos Morto", weight=self.weight)
                    
        return AgentSignal(agent_name=self.name, signal=0.0, confidence=0.0, reasoning="Neutral/Fallback", weight=0.1)

class ExecutionScalerAgent(BaseAgent):
    """
    Agente que escala agressividade do número de "slots/Hydra splits" 
    para o SniperExecutor baseado em regime.
    """
    def __init__(self):
        super().__init__(name="ExecutionScaler", weight=1.0)
        
    def analyze(self, snapshot, asi_state=None, **kwargs) -> AgentSignal:
        return AgentSignal(agent_name=self.name, signal=0.0, confidence=0.0, reasoning="Placeholder para futuro", weight=0.0)
