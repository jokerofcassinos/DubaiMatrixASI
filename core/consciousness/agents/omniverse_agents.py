"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — OMNIVERSE AGENTS (Phase Ω)                  ║
║     Inteligência Suprema (Nível 23): Efeito Zenão Quântico e Horizonte       ║
║     de Eventos (Buracos Negros de Liquidez).                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal

class QuantumZenoEffectAgent(BaseAgent):
    """
    [Phase Ω-Omniverse] Efeito Zenão Quântico.
    Na mecânica quântica, a observação contínua de um sistema instável atrasa seu decaimento
    (ou transição de estado). No HFT, quando milhares de algoritmos monitoram o mesmo
    nível de preço com ordens sub-tick, o preço "congela" (baixa volatilidade com alto volume).
    Quando a "observação" cessa (cancelamento das ordens/fim do spoofing), o sistema 
    colapsa violentamente. O agente detecta o congelamento Zenão para operar o breakout pós-colapso.
    """
    def __init__(self, weight=4.5):
        super().__init__("QuantumZenoEffect", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 10:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)
        highs = np.array(candles_m1["high"], dtype=np.float64)
        lows = np.array(candles_m1["low"], dtype=np.float64)
        volumes = np.array(candles_m1["tick_volume"], dtype=np.float64)
        
        recent_ranges = highs[-5:] - lows[-5:]
        recent_volumes = volumes[-5:]
        
        avg_range = np.mean(highs[-20:-5] - lows[-20:-5]) + 1e-6
        avg_vol = np.mean(volumes[-20:-5]) + 1e-6
        
        signal = 0.0
        conf = 0.0
        reason = "NO_ZENO_FREEZE"
        
        # O Efeito Zenão ocorre se o range (movimento) é asfixiado (< 30% da média)
        # MAS o volume de "observação" (troca de ticks) é extremo (> 200% da média)
        current_range = np.mean(recent_ranges)
        current_vol = np.mean(recent_volumes)
        
        if current_range < (avg_range * 0.3) and current_vol > (avg_vol * 2.0):
            # O preço está congelado sob observação algorítmica massiva.
            # Uma injeção de entropia (rompimento) está reprimida.
            # Procuramos o desequilíbrio na estrutura macro para prever o lado da ruptura.
            m5_candles = snapshot.candles.get("M5")
            if m5_candles and len(m5_candles["close"]) > 2:
                macro_trend = m5_candles["close"][-1] - m5_candles["open"][-2]
                signal = np.sign(macro_trend)
                conf = 0.95
                reason = f"ZENO_FREEZE_BREAKOUT_PENDING (Range={current_range/avg_range:.2f}x, Vol={current_vol/avg_vol:.2f}x)"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class BlackHoleEventHorizonAgent(BaseAgent):
    """
    [Phase Ω-Omniverse] Horizonte de Eventos (Buraco Negro de Liquidez).
    Diferente da Atração Magnética comum, o Horizonte de Eventos é o ponto 
    de não-retorno. Quando o preço entra a uma certa distância de um cluster 
    gigante de liquidação (Stop Losses do varejo), a gravidade se torna infinita.
    Qualquer tentativa de reversão antes de engolir a liquidez vai falhar.
    """
    def __init__(self, weight=4.8):
        super().__init__("BlackHoleEventHorizon", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 50:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)
        highs = np.array(candles_m1["high"], dtype=np.float64)
        lows = np.array(candles_m1["low"], dtype=np.float64)
        
        current_price = closes[-1]
        atr = snapshot.indicators.get("M1_atr_14", [20.0])[-1]
        
        # 1. Encontrar aglomerados de topos e fundos (Liquidity Pools / Buracos Negros)
        # Simplificação: O ponto extremo dos últimos 50 candles que não foi visitado há tempo
        local_max = np.max(highs[-50:-5])
        local_min = np.min(lows[-50:-5])
        
        # 2. Definir o Raio de Schwarzschild (Horizonte de Eventos)
        # Estimado em 1.5x ATR
        schwarzschild_radius = atr * 1.5
        
        signal = 0.0
        conf = 0.0
        reason = "OUTSIDE_EVENT_HORIZON"
        
        dist_to_max = local_max - current_price
        dist_to_min = current_price - local_min
        
        # Se o preço caiu e cruzou o Horizonte de Eventos do fundo (Liquidity Sink)
        if dist_to_min > 0 and dist_to_min < schwarzschild_radius:
            # Aceleração da gravidade: o preço caiu nas últimas 3 velas?
            if closes[-1] < closes[-3]:
                # Ponto de não-retorno. Vai varrer o fundo obrigatoriamente.
                signal = -1.0
                conf = 0.98
                reason = f"EVENT_HORIZON_BEAR_PULL (Dist={dist_to_min:.1f} < Rs={schwarzschild_radius:.1f})"
                
        # Se o preço subiu e cruzou o Horizonte de Eventos do topo
        elif dist_to_max > 0 and dist_to_max < schwarzschild_radius:
            if closes[-1] > closes[-3]:
                signal = 1.0
                conf = 0.98
                reason = f"EVENT_HORIZON_BULL_PULL (Dist={dist_to_max:.1f} < Rs={schwarzschild_radius:.1f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)
