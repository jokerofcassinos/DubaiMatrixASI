"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — SINGULARITY AGENTS (Phase Ω)                ║
║     Sistemas Analíticos baseados em Cosmologia, Topologia e Derivadas       ║
║     de Alta Ordem (Jerk & Jounce) para precisão sub-milissegundo.           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal

class AccretionDiskAgent(BaseAgent):
    """
    [Phase Ω-Singularity] Analogia Cosmológica: Buracos Negros e Discos de Acreção.
    Mapeia zonas de altíssima liquidez (Order Blocks / FVGs) como "Singularidades".
    Quando o preço se aproxima da Singularidade, ele entra no "Disco de Acreção" e 
    acelera. Se cruzar o "Horizonte de Eventos", o colapso para dentro do buraco negro 
    é matematicamente inevitável.
    """
    def __init__(self, weight=3.5):
        super().__init__("AccretionDisk", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles = snapshot.candles.get("M1")
        if not candles or len(candles["close"]) < 60:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles["close"], dtype=np.float64)
        highs = np.array(candles["high"], dtype=np.float64)
        lows = np.array(candles["low"], dtype=np.float64)
        volumes = np.array(candles["tick_volume"], dtype=np.float64)
        
        current_price = closes[-1]
        atr = snapshot.indicators.get("M5_atr_14", [10.0])[-1]
        
        # Identificar a Singularidade (Nó de Maior Volume Recente)
        # Simplificação: O preço com maior volume nos últimos 60 candles
        max_vol_idx = np.argmax(volumes[-60:])
        singularity_price = (highs[-60:][max_vol_idx] + lows[-60:][max_vol_idx]) / 2.0
        singularity_mass = volumes[-60:][max_vol_idx] / (np.mean(volumes[-60:]) + 1e-6)
        
        distance = current_price - singularity_price
        dist_atr = abs(distance) / (atr + 1e-6)
        
        # Raio de Schwarzschild (Horizonte de Eventos) - dinâmico baseado na massa do volume
        schwarzschild_radius = 0.5 * singularity_mass # Em ATRs
        
        signal = 0.0
        conf = 0.0
        reason = "FREE_SPACE"
        
        if singularity_mass < 3.0: # Buraco negro muito fraco, sem gravidade suficiente
            return AgentSignal(self.name, signal, conf, "WEAK_SINGULARITY", self.weight)

        if dist_atr < schwarzschild_radius:
            # Preço cruzou o Horizonte de Eventos. Colapso direcional inevitável para a Singularidade.
            direction = -1.0 if distance > 0 else 1.0 # Puxado em direção à Singularidade
            signal = direction
            conf = 0.95
            reason = f"EVENT_HORIZON_BREACH (Mass={singularity_mass:.1f}x, Dist={dist_atr:.2f} ATR)"
        elif dist_atr < schwarzschild_radius * 2.0:
            # No Disco de Acreção: Aceleração extrema (fricção), alta volatilidade direcional
            # Pode gerar "spitting" (ejeção polar) se a velocidade for muito alta
            velocity = closes[-1] - closes[-3]
            if abs(velocity) > atr * 0.5:
                # Ejeção polar (Spike forte para FORA do buraco negro)
                direction = np.sign(velocity)
                signal = direction
                conf = 0.85
                reason = f"ACCRETION_DISK_EJECTION (Vel={velocity:.1f})"
            else:
                # Sendo sugado lentamente
                direction = -1.0 if distance > 0 else 1.0
                signal = direction * 0.6
                conf = 0.70
                reason = f"ACCRETION_DISK_PULL"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class KinematicDerivativesAgent(BaseAgent):
    """
    [Phase Ω-Singularity] Derivadas de 3ª e 4ª Ordem (Jerk & Jounce).
    Velocidade = dP/dt. Aceleração = dV/dt. Jerk = dA/dt. Jounce = dJ/dt.
    Uma inversão no Jounce precede a inversão da aceleração, que precede a inversão do preço.
    Isto detecta o exato milissegundo em que a força institucional acaba.
    """
    def __init__(self, weight=3.8):
        super().__init__("KinematicJounce", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        # Precisamos da mais alta resolução disponível.
        closes = snapshot.m1_closes if hasattr(snapshot, 'm1_closes') else []
        if len(closes) < 10:
            candles = snapshot.candles.get("M1")
            if not candles: return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)
            closes = np.array(candles["close"], dtype=np.float64)
            
        if len(closes) < 10:
            return AgentSignal(self.name, 0.0, 0.0, "NOT_ENOUGH_POINTS", self.weight)
            
        # Calcula derivadas usando diferenças finitas (ticks/velas)
        # P = closes[-6:]
        # V (Velocity) = diff(P) -> 5 pontos
        # A (Acceleration) = diff(V) -> 4 pontos
        # J (Jerk) = diff(A) -> 3 pontos
        # S (Snap/Jounce) = diff(J) -> 2 pontos
        
        p_recent = np.array(closes[-6:])
        v = np.diff(p_recent)
        a = np.diff(v)
        j = np.diff(a)
        s = np.diff(j)
        
        if len(s) < 1:
            return AgentSignal(self.name, 0.0, 0.0, "MATH_ERROR", self.weight)
            
        jounce = s[-1]
        jerk = j[-1]
        accel = a[-1]
        vel = v[-1]
        
        # Normalização aproximada para BTC M1
        atr = snapshot.indicators.get("M1_atr_14", [10.0])[-1] + 1e-6
        norm_jounce = jounce / atr
        
        signal = 0.0
        conf = 0.0
        reason = "KINEMATIC_STABLE"
        
        # Se a velocidade é positiva, mas a "força da força da força" (Jounce) inverteu brutalmente para baixo
        # O preço ainda está subindo, mas a inércia colapsou no nível quântico. O topo JÁ aconteceu.
        if vel > 0 and accel > 0 and norm_jounce < -2.0:
            signal = -1.0 # Reversão Bearish Antecipada
            conf = 0.95
            reason = f"JOUNCE_COLLAPSE_BEAR (Vel>0, Jounce={norm_jounce:.2f})"
            
        # Se o preço está caindo, mas a derivada de 4ª ordem inverteu positivamente
        elif vel < 0 and accel < 0 and norm_jounce > 2.0:
            signal = 1.0 # Reversão Bullish Antecipada
            conf = 0.95
            reason = f"JOUNCE_IGNITION_BULL (Vel<0, Jounce={norm_jounce:.2f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class TopologicalDataAgent(BaseAgent):
    """
    [Phase Ω-Singularity] Topologia Algébrica Aplicada (TDA).
    Calcula aproximações de "Betti Numbers" para detectar buracos (vacuums) na 
    variedade (manifold) de dados de preço x volume.
    Um "buraco" topológico indica um desfiladeiro de liquidez onde o preço vai despencar (ou explodir)
    sem resistência.
    """
    def __init__(self, weight=2.8):
        super().__init__("TopologyBetti", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles = snapshot.candles.get("M1")
        if not candles or len(candles["close"]) < 30:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles["close"], dtype=np.float64)[-30:]
        volumes = np.array(candles["tick_volume"], dtype=np.float64)[-30:]
        
        # Construção de Point Cloud 2D (Preço Normalizado, Volume Normalizado)
        p_norm = (closes - np.min(closes)) / (np.ptp(closes) + 1e-6)
        v_norm = (volumes - np.min(volumes)) / (np.ptp(volumes) + 1e-6)
        
        # Heurística rápida para detectar buraco (Hole in 2D space)
        # Se existe um cluster de alta volatilidade no passado, e o volume recente secou 
        # mas o preço continua movendo... existe um vácuo topológico.
        
        recent_p = p_norm[-5:]
        recent_v = v_norm[-5:]
        
        hist_p = p_norm[:-5]
        hist_v = v_norm[:-5]
        
        # Densidade Histórica vs Recente
        # Se estamos em uma área de preço (recent_p) que historicamente teve ALTO volume,
        # mas agora tem BAIXO volume, a topologia abriu um "furo". O preço vai rasgar essa área.
        
        signal = 0.0
        conf = 0.0
        reason = "TOPOLOGY_COMPACT"
        
        current_price_lvl = np.mean(recent_p)
        
        # Encontrar se essa área de preço já foi visitada antes
        matches = np.where(np.abs(hist_p - current_price_lvl) < 0.1)[0]
        if len(matches) > 0:
            historical_vol_in_this_area = np.mean(hist_v[matches])
            current_vol = np.mean(recent_v)
            
            # Se o volume histórico era gigante e o atual é inexistente = Vacuum Hole
            if historical_vol_in_this_area > 0.6 and current_vol < 0.2:
                # O preço vai continuar o movimento atual violentamente porque não há defesa
                trend_dir = np.sign(closes[-1] - closes[-5])
                if trend_dir != 0:
                    signal = float(trend_dir)
                    conf = 0.90
                    reason = f"TOPOLOGICAL_HOLE_DETECTED (HistVol={historical_vol_in_this_area:.2f}, CurVol={current_vol:.2f})"

        return AgentSignal(self.name, signal, conf, reason, self.weight)
