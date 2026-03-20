import time
import math
import random
import threading
import numpy as np
from typing import List

from market.mt5_bridge import MT5Bridge
from core.decision.trinity_core import Decision
from config.exchange_config import MIN_LOT_SIZE, MAX_LOT_SIZE
from utils.logger import log

class QuantumTwapEngine:
    """
    [Phase Ω-13] Quantum TWAP (Time-Weighted Average Price) Router.
    
    Fragmenta ordens massivas (Institucionais, God-Mode) em micro-frações pseudo-randômicas,
    e as distribui no mercado ao longo de N milissegundos seguindo uma distribuição de Poisson.
    
    Objetivo: Zero Slippage & Furtividade Absoluta (Anti-Front-running).
    """

    def __init__(self, bridge: MT5Bridge):
        self.bridge = bridge
        self.active_threads = []
        
    def execute_stealth(self, decision: Decision, total_lot: float, duration_seconds: float = 8.0, 
                        min_chunk: float = MIN_LOT_SIZE, max_chunk: float = 0.5):
        """
        Lança a execução TWAP em uma Thread separada (Fire-and-Forget).
        """
        thread = threading.Thread(
            target=self._twap_worker, 
            args=(decision, total_lot, duration_seconds, min_chunk, max_chunk),
            daemon=True
        )
        thread.start()
        self.active_threads.append(thread)
        
        # Ocasionalmente limpa threads mortas
        self.active_threads = [t for t in self.active_threads if t.is_alive()]
        
        return True

    def _twap_worker(self, decision: Decision, total_lot: float, duration_seconds: float, 
                     min_chunk: float, max_chunk: float):
        """
        Worker thread that slices the total_lot and dispatches sequentially with Poisson delays.
        """
        log.omega(
            f"👻 [QUANTUM TWAP] Iniciando roteamento furtivo para {total_lot:.2f} Lotes ({decision.action.value}). "
            f"Injeção projetada para {duration_seconds:.1f}s."
        )
        
        # 1. Planejamento das Fatias (Slices)
        # Queremos fatias aleatórias entre min_chunk e max_chunk
        remaining_lot = total_lot
        slices = []
        
        while remaining_lot > 0:
            if remaining_lot <= min_chunk:
                slices.append(remaining_lot)
                break
                
            # Tamanho pseudo-aleatório
            chunk = random.uniform(min_chunk, min(max_chunk, remaining_lot))
            
            # Arredondar para o Step size (MIN_LOT_SIZE)
            chunk = round(chunk / MIN_LOT_SIZE) * MIN_LOT_SIZE
            chunk = max(MIN_LOT_SIZE, chunk)
            
            if chunk >= remaining_lot:
                slices.append(remaining_lot)
                break
                
            slices.append(chunk)
            remaining_lot = round(remaining_lot - chunk, 2)
            
        num_slices = len(slices)
        
        if num_slices == 0:
            return
            
        # 2. Planejamento do Tempo (Poisson/Exponential deltas)
        # A média de atraso (lambda) é a duração total / número de fatias
        avg_delay = duration_seconds / num_slices
        
        # Se gerarmos deltas exponenciais cujo valor esperado é avg_delay
        deltas = np.random.exponential(scale=avg_delay, size=num_slices)
        
        # Ajustar para que a soma bata exatamente com duration_seconds
        scale_factor = duration_seconds / np.sum(deltas)
        deltas = deltas * scale_factor

        log.debug(f"👻 [TWAP PLANE] Executando {num_slices} micro-tiros variando de min={min(slices):.2f} a max={max(slices):.2f} lotes.")

        # 3. Execução Controlada M1/M2 (Mercado, Furtivo)
        # Assumindo que o TWAP quer garantir liquidez imediata com menor slippage, usamos MARKET.
        successful_lot = 0.0
        
        for i, chunk in enumerate(slices):
            delay = deltas[i]
            
            if delay > 0:
                time.sleep(delay)
                
            # Aciona a ponte MT5 silenciosamente
            res = self.bridge.send_market_order(
                action=decision.action.value,
                lot=chunk,
                sl=decision.stop_loss,
                tp=decision.take_profit,
                comment=f"TWAP_{i+1}/{num_slices}"
            )
            
            if res and res.get("success"):
                successful_lot += chunk
            else:
                log.warning(f"⚠️ [TWAP] Micro-tiro {i+1} falhou. Tentando prosseguir...")
                time.sleep(0.1) # Breve punição/espera para desafogar

        log.omega(
            f"👻 [QUANTUM TWAP] Roteamento Concluído. "
            f"Preenchido {successful_lot:.2f} de {total_lot:.2f} lotes alvo em ~{duration_seconds:.1f}s."
        )
