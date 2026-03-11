"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — TENSOR MATRIX AGENTS (Phase Ω)              ║
║     Inteligência Suprema (Nível 21): Mecânica Quântica Relativística,       ║
║     Grupo de Renormalização e Quebra de Ergodicidade.                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal

class DiracEquationAgent(BaseAgent):
    """
    [Phase Ω-Tensor] Equação de Dirac (Mecânica Quântica Relativística).
    A equação de Schrödinger (usada em outras abordagens quantitativas) é não-relativística.
    Em HFT, a volatilidade extrema atua como a 'velocidade da luz'. A equação de Dirac
    prevê a existência de antimatéria. No mercado, isso significa 'Anti-Liquidez' 
    (Spoofing massivo que aniquila liquidez real em um choque violento, gerando whipsaws).
    O agente calcula o 'Spinor' do mercado.
    """
    def __init__(self, weight=4.7):
        super().__init__("DiracEquation", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 10:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)
        volumes = np.array(candles_m1["tick_volume"], dtype=np.float64)
        
        # Calcular 'Massa' (Volume relativo) e 'Momento' (Variação de preço)
        m = (volumes[-1] / (np.mean(volumes[-10:-1]) + 1e-6))
        p = closes[-1] - closes[-2]
        
        # 'Velocidade da Luz' c é análoga à Volatilidade Máxima local
        c = snapshot.indicators.get("M1_atr_14", [20.0])[-1] * 2.0
        
        signal = 0.0
        conf = 0.0
        reason = "DIRAC_STABLE_VACUUM"
        
        # Energia Relativística E^2 = (pc)^2 + (mc^2)^2
        # Se a energia ultrapassa o threshold de aniquilação, ocorre a "criação de pares" (whipsaw violento)
        E_squared = (p * c)**2 + (m * c**2)**2
        
        # Estado do Spinor (Acoplamento entre momento e antimatéria)
        # Se p é muito alto mas m (massa real) é baixa, a energia vem do vácuo (Fake Breakout de antimatéria)
        if abs(p) > c * 0.5: # Alta velocidade (relativística)
            if m < 0.5: # Baixa massa (Sem volume)
                # Partícula fantasma (Spoofing). Vai aniquilar. Invertemos a direção.
                signal = -np.sign(p)
                conf = 0.98
                reason = f"DIRAC_ANTIMATTER_ANNIHILATION (p={p:.1f}, m={m:.2f} -> Whipsaw Imminent)"
            elif m > 3.0: # Massa ultra densa em velocidade relativística
                # Partícula real massiva. Rompimento verdadeiro.
                signal = np.sign(p)
                conf = 0.95
                reason = f"DIRAC_REAL_PARTICLE_BREAKOUT (p={p:.1f}, m={m:.2f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class RenormalizationGroupAgent(BaseAgent):
    """
    [Phase Ω-Tensor] Grupo de Renormalização (Física Estatística).
    Lida com transições de fase e criticalidade. Um crash ou pump real é
    escala-invariante (ocorre identicamente no nível de ticks, M1 e M5 simultaneamente).
    Este agente usa 'Block Spin Transformation' para agrupar dados e ver se
    a estrutura magnética (direção) sobrevive às mudanças de escala. Se sim,
    estamos em um Ponto Crítico Global (Foguete/Mergulho imparável).
    """
    def __init__(self, weight=4.9):
        super().__init__("RenormalizationGroup", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        candles_m5 = snapshot.candles.get("M5")
        
        if not candles_m1 or not candles_m5 or len(candles_m1["close"]) < 5 or len(candles_m5["close"]) < 2:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        m1_closes = np.array(candles_m1["close"], dtype=np.float64)
        m5_closes = np.array(candles_m5["close"], dtype=np.float64)
        
        # 'Spins' (Direção do momento) nas diferentes escalas
        spin_m1 = np.sign(m1_closes[-1] - m1_closes[-3]) # Macro-tick level
        spin_m5 = np.sign(m5_closes[-1] - m5_closes[-2]) # Macro level
        
        # Adicionar o tick level se disponível via velocidade
        tick_velocity = snapshot.metadata.get("tick_velocity", 0.0)
        spin_tick = np.sign(tick_velocity) if abs(tick_velocity) > 10.0 else 0
        
        signal = 0.0
        conf = 0.0
        reason = "NO_SCALE_INVARIANCE"
        
        # Ponto Crítico (Invariância de Escala): Todas as escalas se alinham perfeitamente
        if spin_m1 == spin_m5 and spin_m5 == spin_tick and spin_tick != 0:
            # O sistema perdeu a "temperatura" que mantinha a desordem. O alinhamento é total.
            signal = float(spin_tick)
            conf = 0.99 # Certeza quase absoluta, o mercado está em transição de fase
            reason = f"RENORMALIZATION_CRITICAL_POINT (Scale Invariant Spin={spin_tick})"
            
        # Desacoplamento de Escala (Renormalização falha): O macro diz uma coisa, o micro grita outra
        elif spin_m5 != 0 and spin_tick != 0 and spin_m5 != spin_tick:
            # Geralmente, em HFT, o tick level é a 'Verdade Oculta' (A isca macro puxa, o micro vende)
            # Operamos a divergência a favor do fluxo HFT se a velocidade for insana
            if abs(tick_velocity) > 25.0:
                signal = float(spin_tick)
                conf = 0.85
                reason = f"RENORMALIZATION_SCALE_DECOUPLING (Macro {spin_m5} vs Micro {spin_tick})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class ErgodicHypothesisAgent(BaseAgent):
    """
    [Phase Ω-Tensor] Teste de Hipótese Ergódica.
    A ergodicidade assume que a média no tempo é igual à média no espaço (ensemble).
    No mercado, a ergodicidade é CONSTANTEMENTE quebrada pelas baleias.
    O agente mede o desvio padrão transversal (spread/profundidade) vs o temporal (volatilidade).
    Se o mercado não for ergódico, indicadores clássicos falham 100%. O agente inverte o sinal
    clássico nesses momentos.
    """
    def __init__(self, weight=4.3):
        super().__init__("ErgodicHypothesis", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 20:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)
        
        # Média Temporal (Time Average)
        time_variance = np.var(closes[-10:])
        
        # Média Espacial / Ensemble (Aproximada pelo volume no spread instantâneo)
        book = snapshot.book
        if not book or not book.get("bids") or not book.get("asks"):
            return AgentSignal(self.name, 0.0, 0.0, "NO_BOOK_DATA", self.weight)
            
        bids = np.array([[b["price"], b["volume"]] for b in book["bids"]], dtype=np.float64)
        asks = np.array([[a["price"], a["volume"]] for a in book["asks"]], dtype=np.float64)
        
        # Dispersão espacial da liquidez (Spatial Variance proxy)
        spatial_variance = np.std(bids[:10, 1]) + np.std(asks[:10, 1]) + 1e-6
        
        signal = 0.0
        conf = 0.0
        reason = "ERGODIC_STATE"
        
        # Razão de Quebra Ergódica
        # Se a variância de liquidez (espacial) for bizarramente divergente da variância de preço (temporal)
        # O sistema quebrou ergodicidade. (Ex: Preço parado, mas o book está fervendo com ordens massivas pulando).
        trend = closes[-1] - closes[-5]
        
        if spatial_variance > time_variance * 50.0 and time_variance < 50.0:
            # Preço congelado no tempo, mas o espaço está caótico. Uma explosão direcional está sendo represada.
            # Qual lado está empurrando a entropia espacial?
            bid_vol = np.sum(bids[:5, 1])
            ask_vol = np.sum(asks[:5, 1])
            if bid_vol > ask_vol * 2.0:
                signal = 1.0 # Pressão contida no Bid
                conf = 0.92
                reason = "NON_ERGODIC_BUILDUP_BULL (Time Frozen, Space Chaotic)"
            elif ask_vol > bid_vol * 2.0:
                signal = -1.0 # Pressão contida no Ask
                conf = 0.92
                reason = "NON_ERGODIC_BUILDUP_BEAR (Time Frozen, Space Chaotic)"
                
        return AgentSignal(self.name, signal, conf, reason, self.weight)
