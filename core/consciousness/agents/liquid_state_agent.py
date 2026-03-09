"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — LIQUID STATE AGENT                    ║
║     Leitura de padrões não-lineares via Reservoir Computing (C++)           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import numpy as np
from typing import Optional
from core.consciousness.agents.base import BaseAgent, AgentSignal

class LiquidStateAgent(BaseAgent):
    """
    Agente MCDF Conceito 2 (Liquid State Machine - Reservoir Computing).
    Analisa as ondulações (ripples) do reservatório C++ para extrair
    a intenção direcional oculta no ruído microestrutural.
    
    Ele mapeia o estado n-dimensional do reservatório para uma predição direcional
    via regressão de memória curta em tempo real, sem lag de indicadores.
    """
    
    def __init__(self, weight=1.0):
        super().__init__("LiquidStateAgent", weight=weight)
        # Pesos de Readout (Readout Layer). Serão atualizados dinamicamente via Hebbian/RLS
        # Inicializando como zeros, mas assumindo 10 ondas de saída
        self.w_out = np.zeros(10)
        self.learning_rate = 0.01
        self.last_price = 0.0
        self.last_waves = np.zeros(10)
        
    def analyze(self, snapshot, **kwargs) -> Optional[AgentSignal]:
        waves = snapshot.metadata.get("reservoir_waves")
        if waves is None or len(waves) == 0:
            return None
            
        waves_arr = np.array(waves)
        if len(waves_arr) < 10:
            return None
            
        current_price = snapshot.price
        
        # 1. Atualização online do Readout Layer (RLS simplificado / Hebbian)
        if self.last_price > 0:
            # Qual foi a mudança de preço real (o target)
            delta_p = current_price - self.last_price
            # Normalizar target para o domínio [-1, 1]
            target = np.tanh(delta_p * 100.0) 
            
            # Predição que a matriz fez no tick anterior
            prediction = np.dot(self.w_out, self.last_waves)
            
            # Erro
            error = target - prediction
            
            # OMEGA Update (Delta Rule adaptada para estabilidade)
            self.w_out += self.learning_rate * error * self.last_waves
            
            # Decaimento de peso (Regularização L2)
            self.w_out *= 0.999
            
        # 2. Salva o estado para a próxima iteração
        self.last_price = current_price
        self.last_waves = waves_arr
        
        # 3. Predição Atual
        signal_raw = np.dot(self.w_out, waves_arr)
        
        # Normalização via sigmoid (esmagamento suave)
        signal = float(np.tanh(signal_raw))
        
        # Confiança baseada na amplitude do sinal vs ruído médio
        confidence = min(0.95, max(0.40, abs(signal_raw) / 2.0))
        
        # Zera se o sinal for minúsculo (ruído estagnado)
        if abs(signal) < 0.15:
            signal = 0.0
            confidence = 0.0
            
        reasoning = f"LiquidState(Pred={signal:+.2f} | Conf={confidence:.2f})"
        
        # Phase 51: God-Mode Alignment (Se V-Pulse for detectado)
        v_pulse = snapshot.metadata.get("v_pulse_detected", False)
        if v_pulse and abs(signal) > 0.4:
            confidence = 0.99
            reasoning += " [V-PULSE ALIGNMENT]"
            
        return AgentSignal(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            weight=self.weight
        )
