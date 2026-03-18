import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal
from market.data_engine import MarketSnapshot

class KarmanVortexWakeAgent(BaseAgent):
    """
    [PHASE Ω-SINGULARITY] Karman Vortex Wake Detector
    Detecta a frequência de shedding de vórtices (micro-pumps/dumps alternados)
    após um colapso direcional (Liquidation Cascade / Blow-off Top).
    Baseado em Dinâmica de Fluidos e Número de Strouhal.
    """
    def __init__(self):
        super().__init__("KarmanVortexWakeAgent", weight=1.45)
        # Número de Strouhal médio para corpos rombudos em escoamento turbulento
        self.strouhal_number = 0.2 
        
    def calculate_vortex_shedding_frequency(self, velocity_array, obstacle_width_atr):
        if obstacle_width_atr <= 0 or len(velocity_array) == 0: 
            return 0.0
            
        # f = (St * V) / L -> Frequência = (Strouhal * Velocidade) / Largura (Range da Vela de Colapso)
        # Usamos abs() para pegar a inércia cinética independente da direção
        mean_velocity = float(np.mean(np.abs(velocity_array[-15:]))) 
        
        expected_freq = (self.strouhal_number * mean_velocity) / obstacle_width_atr
        return expected_freq
        
    def analyze(self, snapshot: MarketSnapshot, **kwargs) -> AgentSignal:
        try:
            # Requer histórico mínimo de ticks
            vel_hist = snapshot.tick_velocity_history if hasattr(snapshot, "tick_velocity_history") else []
            if len(vel_hist) < 15:
                vel_hist = [snapshot.metadata.get("tick_velocity", 0.0)] * 15

            # Precisamos de um indicador de "Tamanho do Obstáculo"
            # Vamos usar o ATR M5 ou a amplitude da última vela forte
            atr_m5 = snapshot.indicators.get("M5_atr_14", [0.0])[-1]
            atr_m1 = snapshot.indicators.get("M1_atr_14", [0.0])[-1]
            
            if atr_m5 <= 0:
                atr_m5 = atr_m1 if atr_m1 > 0 else 100.0

            # Verifica se houve um choque recente (obstáculo)
            # Aproximação: aceleração foi extrema recentemente, mas agora acalmou
            accel_hist = snapshot.tick_acceleration_history if hasattr(snapshot, "tick_acceleration_history") else [0.0]*15
            max_accel = max(np.abs(accel_hist[-15:])) if accel_hist else 0.0
            
            is_post_wake = max_accel > 15.0 and abs(snapshot.metadata.get("tick_velocity", 0.0)) < 10.0
            
            if not is_post_wake:
                return AgentSignal(self.name, 0.0, 0.0, "Aguardando wake.")

            # Calcula frequência do vórtice
            freq = self.calculate_vortex_shedding_frequency(vel_hist, atr_m5)
            
            if freq <= 0.001:
                return AgentSignal(self.name, 0.0, 0.0, "Frequência insignificante.")
                
            # O tempo desde o clímax (simplificado pelo tick atual)
            # Precisamos converter o timestamp datetime para float
            import time
            if hasattr(snapshot.timestamp, 'timestamp'):
                ts_val = snapshot.timestamp.timestamp()
            else:
                ts_val = float(snapshot.timestamp)
                
            time_step = ts_val % 60 # Posição no minuto atual
            
            # Sincroniza a entrada com a fase do vórtice (Sine Wave de alta frequência)
            current_phase = np.sin(2 * np.pi * freq * time_step)
            
            # Operamos a reversão do vórtice (Contra a fase atual para surfar a oscilação)
            signal_val = -float(current_phase)
            
            # Confiança é baseada na intensidade da amplitude da onda
            conf = min(0.95, abs(signal_val) * 1.5)
            
            return AgentSignal(
                agent_name=self.name,
                signal=np.sign(signal_val), 
                confidence=conf, 
                reasoning=f"Vortex Wake Detected: Freq={freq:.3f}, Phase={current_phase:.2f} (Freq: {freq:.4f}, Phase: {current_phase:.4f})"
            )
        except Exception as e:
            import traceback
            from utils.logger import log
            log.error(f"KarmanVortexWakeAgent Exception: {e}\n{traceback.format_exc()}")
            return AgentSignal(self.name, 0.0, 0.0, f"Error: {e}")
