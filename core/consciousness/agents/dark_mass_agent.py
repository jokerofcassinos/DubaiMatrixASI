"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — DARK MASS AGENT (L3 LIQUIDITY)               ║
║     Matéria Escura: Inferência de Liquidez OTC e Icebergs Ocultos            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import numpy as np
from typing import Optional
from core.consciousness.agents.base import BaseAgent, AgentSignal
from utils.logger import log

class DarkMassAgent(BaseAgent):
    """
    Agente Astrofísico: Detecta "Matéria Escura" no mercado.
    Compara o deslocamento cinético do preço (ΔP) com a massa observada (Volume L2).
    Se o preço recusa a cair mesmo sob bombardeio de sell volume visível, 
    existe uma Galáxia Escura (Buy Iceberg) no L3 absorvendo o impacto.
    """
    def __init__(self, weight=2.4):
        super().__init__("DarkMass", weight=weight)
        self.needs_orderflow = True
        self.baseline_mass_per_point = 0.0

    def analyze(self, snapshot, orderflow_analysis=None, **kwargs) -> Optional[AgentSignal]:
        if not snapshot.candles or "M1" not in snapshot.candles:
            return None
            
        m1_closes = snapshot.candles["M1"].get("close", [])
        m1_vols = snapshot.candles["M1"].get("tick_volume", [])
        
        if len(m1_closes) < 10 or len(m1_vols) < 10:
            return None
            
        # 1. Calibrar a Inércia (Baseline Mass)
        # Quantos lotes (aprox) movem 1 ponto no M1 nas ultimas horas?
        recent_dp = np.abs(np.diff(m1_closes[-20:]))
        recent_dp[recent_dp == 0] = 0.0001 # Evitar div/0
        recent_mass = np.array(m1_vols[-19:]) / recent_dp
        
        self.baseline_mass_per_point = np.median(recent_mass)
        
        # 2. Analisar Anomalia Gravitacional (Últimos 3 minutos)
        delta_p = m1_closes[-1] - m1_closes[-4]
        total_vol = sum(m1_vols[-3:])
        
        # Qual deveria ter sido o movimento teórico dado o volume?
        expected_dp = total_vol / max(1.0, self.baseline_mass_per_point)
        
        # Anomalia: O preço moveu MENOS do que a física Newtoniana exigia?
        # Ex: Despejaram 5000 volume, preço devia cair 50 pontos, mas caiu 5.
        # Tem alguém (Dark Pool) segurando o mercado.
        
        signal = 0.0
        confidence = 0.0
        reasoning = "Normal Kinetic Mass"
        
        # Se movemos muito pouco para o volume empregado, houve absorção de L3.
        if abs(delta_p) < expected_dp * 0.2 and total_vol > np.mean(m1_vols[-20:]) * 1.5:
            # Volume gigante, deslocamento pífio.
            # Direcionalidade do Delta do Orderflow nos diz quem "bateu" na parede
            delta_flow = orderflow_analysis.get('delta', 0.0) if orderflow_analysis else 0.0
            
            if delta_flow < 0:
                # Bateram forte na venda, mas o preço não caiu. Matéria escura de COMPRA.
                signal = 1.0
                confidence = 0.90
                reasoning = f"L3 BUY DARK POOL (Absorbed {total_vol} vols, ΔP={delta_p:.1f})"
            elif delta_flow > 0:
                # Bateram forte na compra, mas o preço não subiu. Matéria escura de VENDA.
                signal = -1.0
                confidence = 0.90
                reasoning = f"L3 SELL DARK POOL (Absorbed {total_vol} vols, ΔP={delta_p:.1f})"
                
        return AgentSignal(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning
        )
