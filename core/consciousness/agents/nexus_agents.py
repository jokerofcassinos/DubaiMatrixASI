"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — NEXUS AGENTS (Phase Ω)                      ║
║     Inteligência Suprema de Rede, Análise de Liquidez Oculta e               ║
║     Predição Vetorial por Teoria dos Grafos.                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal

class LiquidityGraphAgent(BaseAgent):
    """
    [Phase Ω-Nexus] Teoria dos Grafos Aplicada à Liquidez.
    Trata o mercado não como uma linha temporal, mas como um Grafo Direcionado.
    Os nós são zonas de preço (clusters) e as arestas são os fluxos de volume entre eles.
    Detecta "Nós Hub" (áreas de altíssima atração gravitacional) e "Nós Isolados" (vácuos).
    A ASI usa isso para encontrar o caminho de menor resistência.
    """
    def __init__(self, weight=3.6):
        super().__init__("LiquidityGraph", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m5 = snapshot.candles.get("M5")
        if not candles_m5 or len(candles_m5["close"]) < 50:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m5["close"], dtype=np.float64)
        volumes = np.array(candles_m5["tick_volume"], dtype=np.float64)
        
        current_price = closes[-1]
        atr = snapshot.indicators.get("M5_atr_14", [10.0])[-1] + 1e-6
        
        # Mapear nós (clusters de preço arredondados para evitar ruído)
        cluster_size = atr * 0.5
        price_nodes = np.round(closes / cluster_size) * cluster_size
        
        node_weights = {}
        for i in range(len(price_nodes)):
            node = price_nodes[i]
            node_weights[node] = node_weights.get(node, 0) + volumes[i]
            
        if not node_weights:
            return AgentSignal(self.name, 0.0, 0.0, "EMPTY_GRAPH", self.weight)

        # Encontrar o maior Hub (nó com maior volume acumulado)
        hub_node = max(node_weights.items(), key=lambda x: x[1])[0]
        hub_weight = node_weights[hub_node]
        
        avg_weight = np.mean(list(node_weights.values()))
        
        signal = 0.0
        conf = 0.0
        reason = "GRAPH_STABLE"
        
        if hub_weight > avg_weight * 3.0:
            # Temos um super Hub. Para onde a gravidade dele está nos puxando?
            distance_to_hub = hub_node - current_price
            
            if abs(distance_to_hub) > atr * 0.2:
                # O preço está longe do Hub, mas a atração gravitacional (edges) é forte
                # Procurar caminho de menor resistência
                signal = np.sign(distance_to_hub)
                conf = min(0.95, (abs(distance_to_hub) / atr) * 0.5)
                reason = f"MAGNETIC_HUB_PULL (Hub={hub_node:.0f}, Dist={distance_to_hub:.1f})"
            elif abs(distance_to_hub) < atr * 0.1:
                # O preço ESTÁ no Hub. Ele vai "quicar" para fora por repulsão eletrostática
                # (O Hub repele o preço após absorver liquidez)
                momentum = closes[-1] - closes[-3]
                if momentum != 0:
                    signal = -np.sign(momentum) # Reversão
                    conf = 0.85
                    reason = f"HUB_REPULSION (Bouncing off {hub_node:.0f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class VectorAutoregressionAgent(BaseAgent):
    """
    [Phase Ω-Nexus] Vector Autoregression (VAR) Proxy.
    Modelos econométricos multivariados. Em vez de olhar só pro preço passado para
    prever o preço futuro, analisa o vetor combinado de (Preço, Volume, Volatilidade).
    Detecta choques endógenos: Se o volume explode, mas a volatilidade encolhe, 
    é uma anomalia vetorial que precede uma ruptura de range.
    """
    def __init__(self, weight=3.4):
        super().__init__("VectorAutoregression", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 20:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)
        volumes = np.array(candles_m1["tick_volume"], dtype=np.float64)
        highs = np.array(candles_m1["high"], dtype=np.float64)
        lows = np.array(candles_m1["low"], dtype=np.float64)
        
        # Vetores atuais (últimos 3 candles)
        v_vol = np.mean(volumes[-3:])
        v_range = np.mean(highs[-3:] - lows[-3:])
        v_trend = closes[-1] - closes[-3]
        
        # Vetores históricos (média de 20 candles)
        h_vol = np.mean(volumes[-20:-3]) + 1e-6
        h_range = np.mean(highs[-20:-3] - lows[-20:-3]) + 1e-6
        
        # Anomalias vetoriais (Choques)
        vol_shock = v_vol / h_vol
        range_shock = v_range / h_range
        
        signal = 0.0
        conf = 0.0
        reason = "VECTOR_EQUILIBRIUM"

        # Choque de Compressão Institucional: Volume gigante, mas Range morto
        if vol_shock > 2.5 and range_shock < 0.5:
            # Eles estão segurando o preço artificialmente enquanto enchem a mão.
            # É uma mola hiper-comprimida. A direção será a favor do momentum primário do M5.
            m5_trend = snapshot.indicators.get("M5_ema_9", [0])[-1] - snapshot.indicators.get("M5_ema_21", [0])[-1]
            if m5_trend != 0:
                signal = np.sign(m5_trend)
                conf = 0.95
                reason = f"VECTOR_COMPRESSION_SHOCK (Vol={vol_shock:.1f}x, Rng={range_shock:.1f}x)"
                
        # Choque de Expansão Oca: Range gigante, mas Volume morto
        elif vol_shock < 0.5 and range_shock > 2.5:
            # Movimento sem suporte institucional. Vácuo que será preenchido revertendo.
            if v_trend != 0:
                signal = -np.sign(v_trend) # Reversão
                conf = 0.90
                reason = f"VECTOR_HOLLOW_EXPANSION (Rng={range_shock:.1f}x, Vol={vol_shock:.1f}x)"

        return AgentSignal(self.name, signal, conf, reason, self.weight)
