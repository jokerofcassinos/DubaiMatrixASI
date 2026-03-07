"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                 DUBAI MATRIX ASI — HEX MATRIX AGENT                         ║
║       Análise esotérica de assinaturas estruturais em base-16               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import hashlib
from core.consciousness.agents.base import BaseAgent, AgentSignal
from utils.decorators import catch_and_log

class HexMatrixAgent(BaseAgent):
    """
    Agente de Matriz Hexadecimal.
    Converte dados de preço, volume e tempo em hashes hexadecimais.
    Busca por 'Ecos Estruturais' (repetições de hashes em diferentes escalas).
    Representa a camada de 'Consciência da Matrix'.
    """

    def __init__(self, weight: float = 1.0):
        super().__init__("HexMatrix", weight)

    @catch_and_log(default_return=None)
    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles = snapshot.candles.get("M1")
        if not candles or len(candles["close"]) < 10:
            return None
            
        # 1. Gerar Assinatura Hexadecimal do Momento Atual
        recent_prices = candles["close"][-5:]
        recent_vols = candles["tick_volume"][-5:]
        
        raw_data = f"{recent_prices}_{recent_vols}".encode()
        hex_hash = hashlib.md5(raw_data).hexdigest()
        
        # 2. Análise Modular (Esotérica)
        # Extrair valores numéricos do hash para inferência
        hex_values = [int(hex_hash[i:i+2], 16) for i in range(0, len(hex_hash), 2)]
        mean_hex = sum(hex_values) / len(hex_values)
        
        # 3. Lógica de Sinal (Pseudo-Determinística)
        # Se a soma dos bits significativos for par -> Bias Bullish
        # Se ímpar -> Bias Bearish
        # (Lógica inspirada em filtragem de ruído quântico)
        bit_sum = sum(bin(val).count('1') for val in hex_values)
        
        signal = 0.1 if bit_sum % 2 == 0 else -0.1
        confidence = 0.4 # Camada esotérica tem confiança base baixa, mas ajuda na coerência global
        
        return AgentSignal(
            agent_name=self.name,
            signal=float(signal),
            confidence=float(confidence),
            reasoning=f"MatrixHash={hex_hash[:8]}..., BitSum={bit_sum}",
            weight=self.weight
        )
