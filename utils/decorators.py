"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — DECORATORS                            ║
║          Armadura de código — retry, timing, circuit-breaker, safety        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import time
import functools
import traceback
from datetime import datetime, timezone
from typing import Optional, Callable


def retry(max_attempts: int = 3, delay_ms: int = 100,
          backoff_factor: float = 2.0, exceptions: tuple = (Exception,)):
    """
    Decorator de retry com backoff exponencial.
    Nenhuma oportunidade de trade é perdida por falha técnica transitória.

    Args:
        max_attempts: Número máximo de tentativas
        delay_ms: Delay inicial entre retries em ms
        backoff_factor: Multiplicador do delay a cada retry
        exceptions: Tupla de exceções que trigam retry
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay_ms / 1000.0  # Converter para seconds

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        time.sleep(current_delay)
                        current_delay *= backoff_factor

            raise last_exception
        return wrapper
    return decorator


def timed(func: Optional[Callable] = None, *,
          log_threshold_ms: float = 100):
    """
    Decorator que mede tempo de execução.
    Loga warning se exceder threshold — latência é o inimigo.

    Usage:
        @timed
        def slow_function(): ...

        @timed(log_threshold_ms=50)
        def fast_function(): ...
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = f(*args, **kwargs)
            elapsed_ms = (time.perf_counter() - start) * 1000

            # Armazenar timing no resultado se possível
            wrapper._last_elapsed_ms = elapsed_ms

            if elapsed_ms > log_threshold_ms:
                # Import aqui para evitar circular
                try:
                    from utils.logger import log
                    log.warning(
                        f"⏱️ LATENCY [{f.__name__}] {elapsed_ms:.1f}ms "
                        f"(threshold: {log_threshold_ms}ms)"
                    )
                except ImportError:
                    pass

            return result

        wrapper._last_elapsed_ms = 0.0
        return wrapper

    if func is not None:
        return decorator(func)
    return decorator


class CircuitBreakerOpen(Exception):
    """Exceção quando o circuit breaker está aberto."""
    pass


class CircuitBreaker:
    """
    Circuit Breaker — protege módulos instáveis.
    Se um módulo falhar X vezes consecutivas, ele é "desligado"
    temporariamente para evitar cascade failure.
    """

    def __init__(self, failure_threshold: int = 5,
                 recovery_timeout_sec: float = 60.0,
                 name: str = "unnamed"):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout_sec
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED (normal), OPEN (bloqueado), HALF_OPEN (testando)

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Verificar se deve tentar recovery
            if self.state == "OPEN":
                if self.last_failure_time:
                    elapsed = (datetime.now(timezone.utc) -
                              self.last_failure_time).total_seconds()
                    if elapsed >= self.recovery_timeout_sec:
                        self.state = "HALF_OPEN"
                    else:
                        raise CircuitBreakerOpen(
                            f"Circuit breaker [{self.name}] OPEN. "
                            f"Recovery em {self.recovery_timeout_sec - elapsed:.0f}s"
                        )

            try:
                result = func(*args, **kwargs)
                # Sucesso — reset counter
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                self.failure_count = 0
                return result

            except CircuitBreakerOpen:
                raise  # Re-raise circuit breaker exceptions
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = datetime.now(timezone.utc)

                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    try:
                        from utils.logger import log
                        log.error(
                            f"🔴 CIRCUIT BREAKER [{self.name}] OPEN! "
                            f"{self.failure_count} falhas consecutivas. "
                            f"Pausa de {self.recovery_timeout_sec}s"
                        )
                    except ImportError:
                        pass

                raise
        return wrapper


def asi_safe(min_val: float = None, max_val: float = None,
             param_name: str = ""):
    """
    Decorator que garante que retornos numéricos estão dentro de bounds seguros.
    A ASI NUNCA pode produzir valores que destroem o sistema.

    Usage:
        @asi_safe(min_val=-1.0, max_val=1.0, param_name="signal")
        def compute_signal(): ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            if isinstance(result, (int, float)):
                original = result
                if min_val is not None:
                    result = max(min_val, result)
                if max_val is not None:
                    result = min(max_val, result)

                if result != original:
                    try:
                        from utils.logger import log
                        log.warning(
                            f"🛡️ ASI_SAFE [{param_name or func.__name__}] "
                            f"clamped {original:.4f} → {result:.4f} "
                            f"[{min_val}, {max_val}]"
                        )
                    except ImportError:
                        pass

            return result
        return wrapper
    return decorator


def catch_and_log(default_return=None, critical: bool = False):
    """
    Decorator que captura exceções, loga, e retorna valor default.
    Nenhum módulo isolado pode crashar a ASI inteira.

    Args:
        default_return: Valor a retornar em caso de exceção
        critical: Se True, loga como CRITICAL ao invés de ERROR
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                try:
                    from utils.logger import log
                    msg = (
                        f"💀 EXCEPTION in [{func.__name__}]: {type(e).__name__}: {e}"
                    )
                    if critical:
                        log.critical(msg)
                    else:
                        log.error(msg)
                    log.debug(traceback.format_exc())
                except ImportError:
                    print(f"EXCEPTION in {func.__name__}: {e}")

                return default_return
        return wrapper
    return decorator


def ast_self_heal(func):
    """
    Sistema Imunológico AST (Phase Ω-Ascension):
    Captura AttributeError em runtime. Ao invés de abortar o ciclo, 
    infere a classe e injeta um mock dinâmico no objeto afetado para que a ASI
    continue rodando sem intervenção humana.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AttributeError as e:
            try:
                import re
                from utils.logger import log
                
                # Extrai do erro padrão: "'BookInfo' object has no attribute 'volume_real'"
                match = re.search(r"'([^']+)' object has no attribute '([^']+)'", str(e))
                if match:
                    obj_type, attr_name = match.groups()
                    log.omega(f"🧬 [AST SELF-HEAL] Falha de atributo '{attr_name}' no objeto '{obj_type}'. Autocicatrizando...")
                    
                    healed = False
                    # Procura o objeto corrompido nos argumentos para curá-lo
                    for arg in args:
                        if type(arg).__name__ == obj_type:
                            # Injeta property fantasma
                            setattr(arg, attr_name, 0.0) 
                            log.omega(f"🧬 Atributo {attr_name} = 0.0 injetado dinamicamente em {obj_type}!")
                            healed = True
                            
                    if healed:
                        # Roda a função novamente com a matriz cicatrizada
                        return func(*args, **kwargs)
            except Exception:
                pass
            raise e # Se não conseguiu curar, devolve o erro pro catch_and_log
    return wrapper
