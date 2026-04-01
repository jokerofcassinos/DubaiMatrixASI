import logging
import time
import asyncio
from enum import Enum
from typing import Dict, Any, List, Optional
import numpy as np

from core.intelligence.base_synapse import BaseSynapse
from core.evolution.performance_tracker import PerformanceTracker
from core.evolution.mutation_engine import MutationEngine
from core.evolution.lucid_dream_client import LucidDreamClient

log = logging.getLogger("SOLENN.SelfOptimizer")

class CircuitBreakerLevel(Enum):
    GREEN = 0      # P0: Normal
    YELLOW = 1     # P1: Sizing -30%
    ORANGE = 2     # P2: Sizing -60%, A+ Only
    RED = 3        # P3: Pause 5min
    CRITICAL = 4   # P4: Pause 15min
    EMERGENCY = 5  # P5: Shutdown + Notify
    CATASTROPHIC = 6 # P6: Shutdown + Tail Hedge

class SelfOptimizer(BaseSynapse):
    """
    Ω-37, Ω-27 & Ω-16: O Orquestrador Autônomo de Performance da SOLÉNN.
    
    Monitora a saúde sistêmica, detecta desvios de paradigma via Geometria da Informação
    e aciona Circuit Breakers para proteção de capital.
    """
    
    def __init__(self, 
                 tracker: PerformanceTracker, 
                 mutation_engine: MutationEngine,
                 dream_client: Optional[LucidDreamClient] = None):
        super().__init__("SelfOptimizer")
        self.tracker = tracker
        self.mutation_engine = mutation_engine
        self.dream_client = dream_client
        
        self.current_level = CircuitBreakerLevel.GREEN
        self.last_pause_time = 0.0
        self.is_paused = False
        
        # Thresholds Ω-v2 (Calibrados p/ FTMO §11.1)
        self.FLOOR_WIN_RATE = 0.97
        self.CEIL_DRAWDOWN = 0.02
        self.MAX_CONSECUTIVE_LOSSES = 1
        
        self.optimization_cycles = 0

    async def process(self, snapshot: Any, nexus_context: Any = None) -> Dict[str, Any]:
        """[Ω-EXEC] Ciclo neural de orquestração de performance."""
        self.optimization_cycles += 1
        
        # 1. Ω-40: Análise de Saúde Sistêmica
        perf_report = self.tracker.full_report
        health_status = self._analyze_health(perf_report)
        
        # 2. Ω-5: Gestão de Circuit Breakers
        await self._manage_safety(health_status)
        
        # 3. Ω-27: Geometria da Informação (Simulado)
        kl_div = self._calculate_kl_divergence(snapshot)
        
        # 4. Ω-7: Orquestração de Mutações
        mutation_result = None
        # Permitir mutação se não estiver pausado e nível for preventivo (Green/Yellow/Orange)
        if not self.is_paused and self.current_level.value <= CircuitBreakerLevel.ORANGE.value:
            if kl_div > 0.5 or health_status["needs_fix"]:
                log.info(f"🧬 [Ω-OPT] Disparando ciclo de auto-evolução (Nível={self.current_level.name}, KL={kl_div:.4f})")
                mutation_result = self.mutation_engine.mutate(self.optimization_cycles, perf_report)
        
        return {
            "node": self.name,
            "level": self.current_level.name,
            "kl_div": kl_div,
            "is_paused": self.is_paused,
            "mutated": bool(mutation_result)
        }

    def _analyze_health(self, perf: Dict[str, Any]) -> Dict[str, Any]:
        """V1-V9: Decomposição de métricas de saúde."""
        wr = perf.get("win_rate", 1.0)
        dd = perf.get("max_drawdown_pct", 0.0)
        losses = perf.get("consecutive_losses", 0)
        
        needs_fix = (wr < self.FLOOR_WIN_RATE) or (losses >= self.MAX_CONSECUTIVE_LOSSES)
        is_critical = dd >= self.CEIL_DRAWDOWN
        
        return {
            "win_rate": wr,
            "drawdown": dd,
            "losses": losses,
            "needs_fix": needs_fix,
            "is_critical": is_critical
        }

    async def _manage_safety(self, health: Dict[str, Any]):
        """Ω-5: Escala de Circuit Breakers de 7 Níveis."""
        
        # Lógica simplificada de transição de níveis (V109-V115)
        if health["drawdown"] >= 0.03:
            self.current_level = CircuitBreakerLevel.CATASTROPHIC
        elif health["drawdown"] >= 0.02:
            self.current_level = CircuitBreakerLevel.EMERGENCY
        elif health["is_critical"]:
            self.current_level = CircuitBreakerLevel.CRITICAL
            await self._pause_system(900) # 15 min
        elif health["losses"] >= self.MAX_CONSECUTIVE_LOSSES:
            self.current_level = CircuitBreakerLevel.RED
            await self._pause_system(300) # 5 min
        elif health["needs_fix"]:
            self.current_level = CircuitBreakerLevel.ORANGE
        else:
            self.current_level = CircuitBreakerLevel.GREEN
            self.is_paused = False

    async def _pause_system(self, duration: int):
        """V112-V113: Pausa temporária p/ cool-off."""
        if not self.is_paused:
            log.warning(f"🛑 [Ω-SAFETY] Gateway Crítico: Pausando sistema por {duration}s. Nível: {self.current_level.name}")
            self.is_paused = True
            self.last_pause_time = time.time()
            # Em implementação real, aqui dispararíamos fechamento de ordens live.

    def _calculate_kl_divergence(self, snapshot: Any) -> float:
        """Ω-27: Detecção de Paradigm Shift via Divergência KL (Simulado)."""
        # Comparação entre distribuição de retornos preditos vs realizados
        return float(np.random.random() * 0.2) # Baseline normal baixo
        
# Auto-Otimizador Ω (v2) inicializado.
# A serenidade de quem já sabe o resultado antes da execução.
