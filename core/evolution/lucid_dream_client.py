import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from enum import Enum

from core.intelligence.base_synapse import BaseSynapse
from config.settings import DATA_DIR

log = logging.getLogger("SOLENN.LucidDream")

class DreamScenario(Enum):
    """V1-V9: Arquétipos de Mercado para Simulação (Ω-32)."""
    FLASH_CRASH = "FLASH_CRASH"
    SHORT_SQUEEZE = "SHORT_SQUEEZE"
    CHOPPY = "CHOPPY"
    TRENDING = "TRENDING"
    TOXIC_FLOW = "TOXIC_FLOW"
    LIQUIDITY_GAP = "LIQUIDITY_GAP"

class LucidDreamClient(BaseSynapse):
    """
    Ω-32, Ω-14 & Ψ-22: O Inconsciente Algorítmico da SOLÉNN.
    
    Orquestra auto-simulações aceleradas em backends Java/C++
    para validar genomas antes da exposição ao capital real.
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 5557):
        super().__init__("LucidDream")
        self.host = host
        self.port = port
        self.is_dreaming = False
        self.dream_history: List[Dict[str, Any]] = []

    async def dream_cycle(self, 
                          base_price: float, 
                          volatility: float, 
                          scenario: DreamScenario = DreamScenario.TRENDING,
                          iterations: int = 10000) -> Optional[Dict[str, Any]]:
        """
        V10-V18: Solicita um ciclo de sonho assíncrono (Ω-45).
        """
        if self.is_dreaming:
            log.warning("💤 [Ω-DREAM] O sistema já está em modo de sonho.")
            return None

        self.is_dreaming = True
        log.info(f"🌌 [Ω-DREAM] Iniciando ciclo de sonho: {scenario.value} ({iterations} iterações)")
        
        try:
            # V10: Asyncio open_connection
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=5.0
            )

            # V11: Payload format (V1-style mas evoluído)
            payload = f"DREAM|{scenario.value}|{base_price}|{volatility}|{iterations}\n"
            writer.write(payload.encode())
            await writer.drain()

            # V13: Wait for response with timeout
            response_data = await asyncio.wait_for(reader.readline(), timeout=15.0)
            response = response_data.decode().strip()
            
            writer.close()
            await writer.wait_closed()

            self.is_dreaming = False

            if response.startswith("DREAM_SUCCESS"):
                return self._parse_response(response, scenario)
            else:
                log.error(f"❌ [Ω-DREAM] Falha no sonho: {response}")
                return None

        except asyncio.TimeoutError:
            log.error("❌ [Ω-DREAM] Timeout de simulação. Daemon Java não responde.")
            self.is_dreaming = False
            return None
        except Exception as e:
            log.error(f"❌ [Ω-DREAM] Erro crítico na interface de simulação: {e}")
            self.is_dreaming = False
            return None

    def _parse_response(self, response: str, scenario: DreamScenario) -> Dict[str, Any]:
        """V19-V27: Decomposição de resultados de simulação."""
        # Formato esperado: DREAM_SUCCESS|ALPHA:0.87|MUTATIONS:142|TIME:45ms|SCORE:92.5
        try:
            parts = response.split("|")
            result = {
                "timestamp": time.time(),
                "scenario": scenario.value,
                "alpha": float(parts[1].split(":")[1]),
                "mutations": int(parts[2].split(":")[1]),
                "time_ms": int(parts[3].split(":")[1].replace("ms", "")),
                "score": float(parts[4].split(":")[1])
            }
            
            self.dream_history.append(result)
            log.info(f"🌟 [Ω-DREAM] Sonho Concluído: Alpha {result['alpha']:.2f}, Score {result['score']}")
            return result
        except (IndexError, ValueError) as e:
            log.error(f"❌ [Ω-DREAM] Erro de parsing no resultado: {e}")
            return None

    async def process(self, snapshot: Any, nexus_context: Any = None) -> Dict[str, Any]:
        """[Ω-EXEC] Gateway do inconsciente."""
        return {
            "node": self.name,
            "is_dreaming": self.is_dreaming,
            "episodes": len(self.dream_history)
        }

# Cliente Lucid Dream Ω (v2) inicializado.
# Validando cenários antes do colapso da função de onda.
