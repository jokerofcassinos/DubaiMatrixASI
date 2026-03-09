"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — TRANSCENDENCE AGENTS (Phase Ω)              ║
║     Sistemas analíticos baseados em Geometria Diferencial, Teoria da         ║
║     Informação Quântica e Topologia Riemanniana.                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal

class RiemannianManifoldAgent(BaseAgent):
    """
    [Phase Ω-Transcendence] Geometria Riemanniana aplicada ao Fluxo de Preço.
    Mapeia a trajetória de preço e volume como uma curva em uma variedade de Riemann.
    Detecta "curvatura extrema" indicando exaustão (Blow-off Tops / Bottoms) ou 
    "geodésicas retas" indicando tendências inerciais sólidas.
    """
    def __init__(self, weight=2.5):
        super().__init__("RiemannianManifold", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles = snapshot.candles.get("M1")
        if not candles or len(candles["close"]) < 20:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles["close"], dtype=np.float64)
        volumes = np.array(candles["tick_volume"], dtype=np.float64)
        
        # Primeira derivada (Velocidade)
        dp = np.diff(closes[-15:])
        dv = np.diff(volumes[-15:])
        
        # Segunda derivada (Aceleração / Curvatura)
        ddp = np.diff(dp)
        
        if len(ddp) < 5:
            return AgentSignal(self.name, 0.0, 0.0, "NOT_ENOUGH_CURVATURE_DATA", self.weight)
            
        current_acceleration = ddp[-1]
        mean_acceleration = np.mean(np.abs(ddp))
        
        # Curvatura Riemanniana simplificada K = |y''| / (1 + y'^2)^(3/2)
        # Normalizando as escalas
        norm_dp = dp[-1] / (np.std(closes[-15:]) + 1e-6)
        norm_ddp = ddp[-1] / (np.std(closes[-15:]) + 1e-6)
        
        curvature = abs(norm_ddp) / ((1 + norm_dp**2)**1.5)
        
        signal = 0.0
        conf = 0.0
        reason = "GEODESIC_FLAT"
        
        if curvature > 2.0:
            # Curvatura extrema = Colapso iminente da estrutura atual (Exaustão)
            # Reverte a direção da primeira derivada
            direction = -np.sign(dp[-1])
            signal = float(direction)
            conf = min(0.95, curvature / 5.0)
            reason = f"RIEMANNIAN_CURVATURE_SNAP (K={curvature:.2f})"
        elif curvature < 0.2 and abs(norm_dp) > 1.0:
            # Geodésica reta com alta velocidade = Inércia Pura
            direction = np.sign(dp[-1])
            signal = float(direction)
            conf = 0.85
            reason = f"INERTIAL_GEODESIC (Vel={norm_dp:.2f}, K={curvature:.2f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class InformationGeometryAgent(BaseAgent):
    """
    [Phase Ω-Transcendence] Geometria da Informação (Kullback-Leibler Divergence).
    Avalia a distância estatística entre a distribuição de retornos atual (últimos 15 min)
    e a distribuição histórica (últimas 2 horas).
    Detecta "Paradigm Shifts" micro-estruturais antes dos indicadores técnicos.
    """
    def __init__(self, weight=2.2):
        super().__init__("InfoGeometry", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles = snapshot.candles.get("M1")
        if not candles or len(candles["close"]) < 120:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles["close"], dtype=np.float64)
        returns = np.diff(closes) / closes[:-1]
        
        recent_returns = returns[-15:]
        historical_returns = returns[-120:-15]
        
        if np.std(recent_returns) == 0 or np.std(historical_returns) == 0:
            return AgentSignal(self.name, 0.0, 0.0, "ZERO_VARIANCE", self.weight)

        # Histograma para aproximar PDF (Probability Density Function)
        bins = np.linspace(-0.005, 0.005, 20)
        p_recent, _ = np.histogram(recent_returns, bins=bins, density=True)
        q_hist, _ = np.histogram(historical_returns, bins=bins, density=True)
        
        # Evitar divisão por zero
        p_recent = p_recent + 1e-6
        q_hist = q_hist + 1e-6
        
        # Normalizar
        p_recent /= np.sum(p_recent)
        q_hist /= np.sum(q_hist)
        
        # KL Divergence (Distância de p para q)
        kl_div = np.sum(p_recent * np.log(p_recent / q_hist))
        
        signal = 0.0
        conf = 0.0
        reason = f"KL_DIVERGENCE_NORMAL ({kl_div:.4f})"
        
        # Se a divergência for extrema, houve um paradigm shift.
        if kl_div > 1.5:
            # O regime mudou. A direção favorece o desvio da média histórica.
            mean_recent = np.mean(recent_returns)
            mean_hist = np.mean(historical_returns)
            direction = np.sign(mean_recent - mean_hist)
            
            signal = float(direction)
            conf = min(0.99, kl_div / 4.0)
            reason = f"PARADIGM_SHIFT_DETECTED (KL={kl_div:.2f})"
        
        return AgentSignal(self.name, signal, conf, reason, self.weight)


class QuantumSuperpositionAgent(BaseAgent):
    """
    [Phase Ω-Transcendence] Detecção de Superposição de Estados.
    Mede a coerência de fase entre múltiplos timeframes (M1, M5, M15).
    Se os timeframes estão em superposição destrutiva (conflito), emite alerta.
    Se estão em interferência construtiva (harmonia), emite sinal de colapso de onda.
    """
    def __init__(self, weight=2.4):
        super().__init__("QuantumSuperposition", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        phases = []
        for tf in ["M1", "M5", "M15"]:
            candles = snapshot.candles.get(tf)
            if candles and len(candles["close"]) >= 3:
                closes = np.array(candles["close"], dtype=np.float64)
                roc = (closes[-1] - closes[-3]) / closes[-3]
                phases.append(np.sign(roc) * min(abs(roc) * 1000, 1.0))
                
        if len(phases) < 3:
            return AgentSignal(self.name, 0.0, 0.0, "LACK_OF_DIMENSIONS", self.weight)
            
        # Calcula interferência
        interference = sum(phases)
        
        signal = 0.0
        conf = 0.0
        reason = "WAVE_SUPERPOSITION_CHAOTIC"
        
        if abs(interference) > 2.2:
            # Interferência construtiva (M1, M5, M15 alinhados)
            signal = np.sign(interference)
            conf = 0.90
            reason = f"CONSTRUCTIVE_WAVE_COLLAPSE (Int={interference:.2f})"
        elif abs(interference) < 0.5:
            # Destrutiva - reverter para a tendência do M15 (Timeframe pai)
            tf_father = phases[-1]
            if abs(tf_father) > 0.5:
                signal = np.sign(tf_father)
                conf = 0.65
                reason = f"DESTRUCTIVE_SUPERPOSITION_FALLBACK_TO_M15"
                
        return AgentSignal(self.name, signal, conf, reason, self.weight)
