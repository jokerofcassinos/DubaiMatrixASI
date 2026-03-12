"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — KINETICS AGENTS (Phase Ω)                   ║
║     Inteligência Suprema (Nível 25): Coeficiente de Restituição Elástica     ║
║     e Monopolos Magnéticos de Liquidez.                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal

class ImpulseScatteringAgent(BaseAgent):
    """
    [Phase Ω-Kinetics] Coeficiente de Restituição (Espalhamento de Impulso).
    Baseado na física de colisões. Quando uma 'bola' (preço) bate no 'chão' (suporte),
    a velocidade de rebote depende do coeficiente de restituição (e).
    Se o mercado absorve o impacto (volume alto) sem romper (fechamento longe da mínima),
    o impacto foi perfeitamente "Elástico" (e = 1). O agente então opera o rebote
    exato no milissegundo pós-colisão, ignorando a inércia da queda.
    """
    def __init__(self, weight=4.7):
        super().__init__("ImpulseScattering", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 5:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)
        opens = np.array(candles_m1["open"], dtype=np.float64)
        highs = np.array(candles_m1["high"], dtype=np.float64)
        lows = np.array(candles_m1["low"], dtype=np.float64)
        volumes = np.array(candles_m1["tick_volume"], dtype=np.float64)
        
        # Calcular 'Velocidade de Impacto' (Queda antes da colisão)
        v_impact = opens[-1] - closes[-2] # Gap/Inércia
        body = closes[-1] - opens[-1]
        
        atr = snapshot.indicators.get("M1_atr_14", [20.0])[-1]
        avg_vol = np.mean(volumes[-5:-1]) + 1e-6
        current_vol = volumes[-1]
        
        signal = 0.0
        conf = 0.0
        reason = "INELASTIC_IMPACT"
        
        # Choque no Chão (Suporte)
        if body < 0 or closes[-1] < closes[-2]: 
            wick_down = min(closes[-1], opens[-1]) - lows[-1]
            total_size = highs[-1] - lows[-1] + 1e-6
            
            # Se a absorção da queda foi elástica (Pavio enorme relativo ao corpo, com alto volume)
            if wick_down > atr * 0.4 and (wick_down / total_size) > 0.5 and current_vol > avg_vol * 1.5:
                # O impacto não quebrou o chão. Vai quicar.
                signal = 1.0 # COMPRA REBOTE
                conf = min(0.99, 0.7 + (wick_down / atr) * 0.2)
                reason = f"ELASTIC_BOUNCE_FLOOR (Wick={wick_down:.1f}, Vol={current_vol/avg_vol:.1f}x)"
                
        # Choque no Teto (Resistência)
        elif body > 0 or closes[-1] > closes[-2]:
            wick_up = highs[-1] - max(closes[-1], opens[-1])
            total_size = highs[-1] - lows[-1] + 1e-6
            
            if wick_up > atr * 0.4 and (wick_up / total_size) > 0.5 and current_vol > avg_vol * 1.5:
                # O impacto bateu no teto de concreto. Vai cair.
                signal = -1.0 # VENDA REJEIÇÃO
                conf = min(0.99, 0.7 + (wick_up / atr) * 0.2)
                reason = f"ELASTIC_REBOUND_CEILING (Wick={wick_up:.1f}, Vol={current_vol/avg_vol:.1f}x)"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class MagneticMonopoleAgent(BaseAgent):
    """
    [Phase Ω-Kinetics] Monopolos Magnéticos de Liquidez.
    Na física, monopolos magnéticos são hipotéticos, mas no HFT eles existem como
    Bolsões Isolados de Liquidação (Massive Naked Stops). O agente calcula
    a "Carga Magnética" de pavios longos que não foram revisitados.
    Se o preço entra no campo magnético de um Monopolo (Pavio Isolado), ele será
    puxado brutalmente para preencher aquele pavio.
    """
    def __init__(self, weight=4.4):
        super().__init__("MagneticMonopole", weight)
        self.monopoles_bull = [] # Preços que atraem pra cima (Pavios superiores isolados)
        self.monopoles_bear = [] # Preços que atraem pra baixo (Pavios inferiores isolados)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 50:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)
        highs = np.array(candles_m1["high"], dtype=np.float64)
        lows = np.array(candles_m1["low"], dtype=np.float64)
        opens = np.array(candles_m1["open"], dtype=np.float64)
        
        current_price = closes[-1]
        atr = snapshot.indicators.get("M1_atr_14", [20.0])[-1]
        
        # Escaneamento de Monopolos (últimos 50 candles, excluindo os 3 mais recentes)
        # Procurar pavios isolados que são maiores que 1.5 ATR
        for i in range(len(closes)-50, len(closes)-3):
            wick_up = highs[i] - max(closes[i], opens[i])
            wick_down = min(closes[i], opens[i]) - lows[i]
            
            if wick_up > atr * 1.5:
                # Monopolo de Alta (Imã no teto)
                if highs[i] not in [m[0] for m in self.monopoles_bull]:
                    self.monopoles_bull.append((highs[i], wick_up))
            if wick_down > atr * 1.5:
                # Monopolo de Baixa (Imã no fundo)
                if lows[i] not in [m[0] for m in self.monopoles_bear]:
                    self.monopoles_bear.append((lows[i], wick_down))
                    
        # Limpar monopolos que já foram "preenchidos" (neutralizados)
        self.monopoles_bull = [m for m in self.monopoles_bull if np.max(highs[-3:]) < m[0]]
        self.monopoles_bear = [m for m in self.monopoles_bear if np.min(lows[-3:]) > m[0]]
        
        signal = 0.0
        conf = 0.0
        reason = "NO_MONOPOLE_FIELD"
        
        # Calcular atração magnética (Lei de Coulomb: Força inversamente proporcional ao quadrado da distância)
        max_force_bull = 0
        for m_price, m_charge in self.monopoles_bull:
            dist = m_price - current_price
            if 0 < dist < atr * 2.0: # Entrou no campo magnético
                force = m_charge / (dist**2 + 1e-6)
                if force > max_force_bull: max_force_bull = force
                
        max_force_bear = 0
        for m_price, m_charge in self.monopoles_bear:
            dist = current_price - m_price
            if 0 < dist < atr * 2.0:
                force = m_charge / (dist**2 + 1e-6)
                if force > max_force_bear: max_force_bear = force
                
        # Decisão baseada na força magnética dominante
        if max_force_bull > 1.0 and max_force_bull > max_force_bear:
            signal = 1.0
            conf = min(0.95, 0.7 + (max_force_bull * 0.1))
            reason = f"MONOPOLE_MAGNETIC_PULL_UP (Force={max_force_bull:.2f})"
        elif max_force_bear > 1.0 and max_force_bear > max_force_bull:
            signal = -1.0
            conf = min(0.95, 0.7 + (max_force_bear * 0.1))
            reason = f"MONOPOLE_MAGNETIC_PULL_DOWN (Force={max_force_bear:.2f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)
