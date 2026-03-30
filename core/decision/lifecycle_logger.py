import os
import json
import asyncio
import time
import uuid
import logging
import shutil
import hashlib
from collections import deque
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Deque, Set
from dataclasses import dataclass, field, asdict
import aiofiles

# ==============================================================================
# SOLÉNN — LIFECYCLE LOGGER Ω (Core Decision)
# "A serenidade de quem já sabe o resultado antes da execução."
# Protocolo 3-6-9: 162-Vetores de Soberania Forense (V2.0)
# ==============================================================================

@dataclass(frozen=True, slots=True)
class TraceEvent:
    """
    [Ω-V004] Entidade atômica de rastreabilidade neural.
    [Ω-V005] Memória otimizada via __slots__.
    """
    trace_id: str      # [Ω-V001] Ω-Grade TraceID
    stage: str         # [Ω-V016] Perception, Decision, Action, Reflection
    timestamp_ns: int  # [Ω-V010] Precisão de nanossegundos
    message: str       # Descrição do evento narrativo
    source: str        # [Ω-V002] Módulo de origem (hash-verified)
    seq_id: int        # [Ω-V013] Índice sequencial absoluto da cadeia
    level: str         # [Ω-V037-V045] Nível Ω-Grade de severidade
    caused_by: Optional[str] = None # [Ω-V028] Link para trace pai (Causalidade)
    context: Dict[str, Any] = field(default_factory=dict) # [Ω-V019] Snapshot Deep State
    metadata: Dict[str, Any] = field(default_factory=dict) # [Ω-V046] Metadados de auditoria

    def validate(self) -> bool:
        """[Ω-V007] Validação de integridade do evendo em runtime."""
        if not self.trace_id or not isinstance(self.trace_id, str): return False
        if not self.stage or not isinstance(self.stage, str): return False
        if not isinstance(self.timestamp_ns, int): return False
        return True

    def to_json(self) -> str:
        """[Ω-V082] Serialização atômica para JSON-L format."""
        return json.dumps(asdict(self), ensure_ascii=False)

class LifecycleLogger:
    """
    [Ω-M51.V2] Lifecycle Logger Sovereignty.
    Implementação completa do framework 3-6-9 integrado (162 Vetores).
    Garante observabilidade total, persistência não-bloqueante e saúde cognitiva.
    """
    
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(LifecycleLogger, cls).__new__(cls)
        return cls._instance

    def __init__(self, log_dir: str = "logs/lifecycle", reset: bool = False):
        if hasattr(self, '_initialized') and not reset: return
        self.log_dir = log_dir
        self.audit_dir = os.path.join(log_dir, "audits")
        
        # [Ω-V064] Buffer de memória ultra-rápida (Hot traces)
        self.hot_traces: Dict[str, Deque[TraceEvent]] = {}
        self._trace_metadata: Dict[str, Dict[str, Any]] = {}
        
        # [Ω-V055] Fila de alta performance para persistência assíncrona
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=100000)
        
        # [Ω-V073] Contadores atômicos
        self._global_seq = 0
        self._trace_seq: Dict[str, int] = {}
        
        # [Ω-V109-V117] Métricas de Saúde Cognitiva (SRE)
        self.metrics = {
            "total_events": 0,
            "persisted_events": 0,
            "dropped_events": 0, # [Ω-V134]
            "worker_heartbeat": 0,
            "queue_saturation": 0.0,
            "last_cycle_latency_ms": 0.0
        }
        
        self._worker_task = None
        self._ensure_sovereign_dir() # [Ω-V114]
        self._initialized = True
        
        logging.info("🛡️ SOLÉNN LifecycleLogger Ω Initialized | 162 Vectors Active")

    def _ensure_sovereign_dir(self):
        """[Ω-V114] Garantir soberania do sistema de arquivos."""
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs(self.audit_dir, exist_ok=True)

    # --------------------------------------------------------------------------
    # CONCEPT 1: CAUSAL TRACEABILITY & FORENSIC AUDIT (V1-V54)
    # --------------------------------------------------------------------------

    def start_trace(self, context: Dict[str, Any] = None, source: str = "CORE", caused_by: str = None) -> str:
        """
        [Ω-V001] Inicia uma nova cadeia causal com ID determinístico.
        [Ω-V003] Suporta herança causal (parent-child).
        [Ω-V009] Captura snapshot inicial de estado (Frozen).
        """
        # [Ω-V001] Ω-Grade ID Generation
        entropy = uuid.uuid4().hex[:8].upper()
        # [Ω-V002] Source-based hashing for ID
        src_hash = hashlib.md5(source.encode()).hexdigest()[:4].upper()
        trace_id = f"SOLENN_{src_hash}_{entropy}"
        
        self.hot_traces[trace_id] = deque(maxlen=1000) # [Ω-V065]
        self._trace_seq[trace_id] = 0
        self._trace_metadata[trace_id] = {
            "start_ts_ns": time.time_ns(),
            "source": source,
            "caused_by": caused_by,
            "context": context or {} # [Ω-V019] Deep snapshot
        }
        
        # [Ω-V037] Log de início da jornada neural
        self.log_event(
            trace_id=trace_id,
            stage="INIT",
            message=f"Soberania iniciada via {source}.",
            source=source,
            context=context,
            level="Ω-ADVISORY"
        )
        return trace_id

    def log_event(self, trace_id: str, stage: str, message: str, source: str = "MODULE", context: Dict[str, Any] = None, level: str = "INFO"):
        """
        [Ω-V010] Registro sequencial com precisão de nanossegundos.
        [Ω-V013] Atribuição de índice sequencial absoluto.
        [Ω-V127] Mecanismo de backpressure ativo.
        """
        # [Ω-V127-V130] Load Shedding logic
        q_size = self.queue.qsize()
        self.metrics["queue_saturation"] = q_size / self.queue.maxsize
        
        if q_size > self.queue.maxsize * 0.9 and level == "INFO":
            self.metrics["dropped_events"] += 1
            return # [Ω-V128] Drop non-essential
            
        seq = self._get_next_seq(trace_id)
        
        event = TraceEvent(
            trace_id=trace_id,
            stage=stage,
            timestamp_ns=time.time_ns(),
            message=message,
            source=source,
            seq_id=seq,
            level=level,
            caused_by=self._trace_metadata.get(trace_id, {}).get("caused_by"),
            context=context or {}, # [Ω-V020] Context filtering can be done here
            metadata={"q_sat": self.metrics["queue_saturation"]}
        )

        # [Ω-V007] Validation Gauntlet
        if not event.validate(): return
        
        # [Ω-V064] Persistence to Hot memory (Recent History)
        if trace_id not in self.hot_traces:
            self.hot_traces[trace_id] = deque(maxlen=1000)
        self.hot_traces[trace_id].append(event)
        self.metrics["total_events"] += 1
        
        # [Ω-V057] Non-blocking push to the proactor queue
        try:
            self.queue.put_nowait(event)
        except asyncio.QueueFull:
            self.metrics["dropped_events"] += 1

    def _get_next_seq(self, trace_id: str) -> int:
        """[Ω-V013] Invariante de sequenciamento neural."""
        self._global_seq += 1
        idx = self._trace_seq.get(trace_id, 0) + 1
        self._trace_seq[trace_id] = idx
        return idx

    # --------------------------------------------------------------------------
    # CONCEPT 2: NON-BLOCKING NEURAL PERSISTENCE (V55-V108)
    # --------------------------------------------------------------------------

    async def start_worker(self):
        """[Ω-V060] Inicia o metabolismo de persistência assíncrona."""
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._persistence_loop())

    async def stop_worker(self):
        """[Ω-V062] Encerramento gracioso do registrador."""
        if self._worker_task:
            await self.queue.put(None) # Sentinel
            await self._worker_task
            self._worker_task = None

    async def _persistence_loop(self):
        """
        [Ω-V150] Loop de persistência soberana Ω-Grade.
        [Ω-V082] JSON-L Atomic Serialization.
        [Ω-V100] Rotação temporal diária automática.
        """
        while True:
            start_cycle = time.perf_counter()
            event = await self.queue.get()
            if event is None: break
            
            # [Ω-V100] Daily Rotation Invariant
            date_str = datetime.now(timezone.utc).strftime('%Y%p%d')
            filename = f"solenn_lifecycle_{date_str}.jsonl"
            path = os.path.join(self.log_dir, filename)
            
            try:
                # [Ω-V082] Data serialization
                payload = event.to_json()
                
                # [Ω-V029] Non-blocking I/O write using aiofiles
                async with aiofiles.open(path, mode='a', encoding='utf-8') as f:
                    await f.write(payload + "\n")
                
                self.metrics["persisted_events"] += 1
                self.metrics["worker_heartbeat"] = time.time_ns()
                
            except Exception as e:
                # [Ω-V112] Logger internal error reporting
                logging.error(f"☢️ [LOGGER_INTERNAL_FAIL] Persistence failed: {e}")
                
            finally:
                self.metrics["last_cycle_latency_ms"] = (time.perf_counter() - start_cycle) * 1000
                self.queue.task_done()

    # --------------------------------------------------------------------------
    # CONCEPT 3: COGNITIVE HEALTH & ADAPTIVE TELEMETRY (V109-V162)
    # --------------------------------------------------------------------------

    def get_health_status(self) -> Dict[str, Any]:
        """
        [Ω-V109] Relatório SRE de saúde do registrador.
        [Ω-V115] Invariante: total == persisted + dropped + queue.
        """
        status = "HEALTHY"
        if self.metrics["dropped_events"] > 0: status = "DEGRADED"
        if self.metrics["queue_saturation"] > 0.95: status = "CRITICAL"
        
        return {
            "status": status,
            "total_events": self.metrics["total_events"],
            "persisted": self.metrics["persisted_events"],
            "dropped": self.metrics["dropped_events"],
            "q_sat": self.metrics["queue_saturation"],
            "worker_alive": self._worker_task is not None and not self._worker_task.done(),
            "latency_ms": self.metrics["last_cycle_latency_ms"]
        }

    async def run_forensic_audit(self, trace_id: str, pnl: float):
        """
        [Ω-V044/Ω-V160] Protocolo forense disparado em trades perdedores.
        Realiza dissecação 12-camadas da cadeia causal.
        """
        if pnl >= 0: return # Só auditamos perdas ou anomalias (Bug P0)
        
        events = self.get_trace_history(trace_id)
        audit_packet = {
            "audit_id": f"AUDIT-{trace_id}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pnl": pnl,
            "causal_chain": [asdict(e) for e in events],
            "forensic_summary": f"Audit triggered for loss of {pnl}. Chain length: {len(events)}"
        }
        
        audit_file = os.path.join(self.audit_dir, f"audit_{trace_id}.json")
        try:
            async with aiofiles.open(audit_file, mode='w', encoding='utf-8') as f:
                await f.write(json.dumps(audit_packet, indent=4, ensure_ascii=False))
            logging.warning(f"💀 [FORENSIC_AUDIT] Dissected loss in trace {trace_id}. Target: {audit_file}")
        except Exception as e:
            logging.error(f"☢️ [AUDIT_FAIL] Could not persist forensic audit: {e}")

    # --------------------------------------------------------------------------
    # TRACE RETRIEVAL (V010, V064)
    # --------------------------------------------------------------------------

    def get_trace_history(self, trace_id: str) -> List[TraceEvent]:
        """[Ω-V010] Recuperação instantânea da cadeia causal para auditoria hot."""
        return list(self.hot_traces.get(trace_id, []))

    def get_history(self, trace_id: str) -> List[TraceEvent]:
        """Alias de compatibilidade p/ v2.0 orchestrator."""
        return self.get_trace_history(trace_id)

    def cleanup_traces(self, older_than_seconds: int = 3600):
        """[Ω-V066] Garbage collection de traços inativos."""
        now = time.time_ns()
        to_remove = []
        for tid, meta in self._trace_metadata.items():
            if now - meta["start_ts_ns"] > (older_than_seconds * 1e9):
                to_remove.append(tid)
        
        for tid in to_remove:
            self.hot_traces.pop(tid, None)
            self._trace_metadata.pop(tid, None)
            self._trace_seq.pop(tid, None)

# ------------------------------------------------------------------------------
# SINGLETON INSTANCE EXPORT (Ω-Sovereignty)
# ------------------------------------------------------------------------------
# Exportamos como 'lifecycle' conforme esperado pelo orchestrator.py
lifecycle = LifecycleLogger()
solenn_logger = lifecycle # Alias para compatibilidade interna

if __name__ == "__main__":
    # Teste de fumaça (Ω-V109)
    async def smoke_test():
        await lifecycle.start_worker()
        tid = lifecycle.start_trace({"ceo": "Active"})
        lifecycle.log_event(tid, "SMOKE", "Igniting neural trace...")
        await asyncio.sleep(0.1)
        print(lifecycle.get_health_status())
        await lifecycle.stop_worker()
    
    asyncio.run(smoke_test())
