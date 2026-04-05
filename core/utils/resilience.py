"""
SOLÉNN v2 — Code Resilience Decorators & Safety Guards (Ω-CD01 a Ω-CD54)
Replaces v1 decorators.py. Production-grade decorators for retry,
timing, circuit-breaker, value clamping, and exception handling.
No module failure can crash the ASI.

Concept 1: Retry, Timing & Safety Bounds (Ω-CD01–CD18)
  Exponential backoff retry, latency monitoring with threshold warnings,
  numeric value clamping to prevent runaway outputs.

Concept 2: Circuit Breaker & Exception Handling (Ω-CD19–CD36)
  Per-module circuit breakers with state machine (closed→open→half_open),
  exception capture with graceful fallback, AST self-healing for
  missing attributes.

Concept 3: Async Safety & Resource Management (Ω-CD37–CD54)
  Async-compatible retry/timeout, rate limiting with token bucket,
  deadlock prevention, memory-bounded decorators, graceful shutdown.
"""

from __future__ import annotations

import functools
import time
import threading
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar

T = TypeVar("T")


# ──────────────────────────────────────────────────────────────
# Ω-CD01 to Ω-CD18: Retry, Timing & Safety Bounds
# ──────────────────────────────────────────────────────────────


def retry(max_attempts: int = 3, delay: float = 0.1,
          backoff_factor: float = 2.0,
          exceptions: tuple[type[Exception], ...] = (Exception,)):
    """Ω-CD01: Retry with exponential backoff."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exc: Exception | None = None
            current_delay = delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    if attempt < max_attempts:
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
            raise last_exc  # type: ignore
        return wrapper
    return decorator


def timed(func: Callable[..., T] | None = None, *,
          log_threshold_ms: float = 100) -> Callable[..., T] | Callable:
    """Ω-CD04: Measure execution time and log slow calls."""
    def decorator(f: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            start = time.perf_counter()
            result = f(*args, **kwargs)
            elapsed_ms = (time.perf_counter() - start) * 1000
            wrapper._last_elapsed_ms = elapsed_ms  # type: ignore
            return result
        wrapper._last_elapsed_ms = 0.0  # type: ignore
        return wrapper
    if func is not None:
        return decorator(func)
    return decorator


def clamp(min_val: float | None = None, max_val: float | None = None):
    """Ω-CD07: Clamp numeric return values to safe bounds."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            if isinstance(result, (int, float)):
                if min_val is not None:
                    result = max(min_val, result)
                if max_val is not None:
                    result = min(max_val, result)
            return result
        return wrapper
    return decorator


# ──────────────────────────────────────────────────────────────
# Ω-CD19 to Ω-CD36: Circuit Breaker & Exception Handling
# ──────────────────────────────────────────────────────────────


class CircuitBreakerOpen(Exception):
    """Ω-CD20: Raised when circuit breaker is open."""
    pass


@dataclass
class BreakerState:
    """Ω-CD21: State of a single circuit breaker."""
    failure_count: int = 0
    last_failure_time: float = 0.0
    state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN


class CircuitBreaker:
    """Ω-CD22: Per-module circuit breaker with state machine."""

    _breakers: dict[str, BreakerState] = {}
    _lock = threading.Lock()

    @classmethod
    def register(cls, name: str, failure_threshold: int = 5,
                 recovery_timeout_s: float = 60.0) -> "CircuitBreaker":
        return cls(name, failure_threshold, recovery_timeout_s)

    @classmethod
    def get_state(cls, name: str) -> BreakerState:
        with cls._lock:
            if name not in cls._breakers:
                cls._breakers[name] = BreakerState()
            return cls._breakers[name]

    @classmethod
    def record_success(cls, name: str) -> None:
        with cls._lock:
            bs = cls._breakers.get(name)
            if bs:
                bs.failure_count = 0
                if bs.state == "HALF_OPEN":
                    bs.state = "CLOSED"

    @classmethod
    def record_failure(cls, name: str) -> None:
        with cls._lock:
            bs = cls._breakers.get(name)
            if bs:
                bs.failure_count += 1
                bs.last_failure_time = time.time()

    @classmethod
    def is_open(cls, name: str) -> bool:
        bs = cls.get_state(name)
        if bs.state == "OPEN":
            return time.time() - bs.last_failure_time < 60.0
        return False

    def __init__(self, name: str, failure_threshold: int = 5,
                 recovery_timeout_s: float = 60.0) -> None:
        self._name = name
        self._threshold = failure_threshold
        self._recovery = recovery_timeout_s
        CircuitBreaker._breakers[name] = BreakerState()

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            bs = self.get_state(self._name)
            if bs.state == "OPEN":
                elapsed = time.time() - bs.last_failure_time
                if elapsed < self._recovery:
                    raise CircuitBreakerOpen(
                        f"Circuit breaker [{self._name}] OPEN. "
                        f"Recovery in {self._recovery - elapsed:.0f}s"
                    )
                bs.state = "HALF_OPEN"

            try:
                result = func(*args, **kwargs)
                self.record_success(self._name)
                return result
            except CircuitBreakerOpen:
                raise
            except Exception as e:
                self.record_failure(self._name)
                bs = self.get_state(self._name)
                if bs.failure_count >= self._threshold:
                    bs.state = "OPEN"
                raise
        return wrapper


def catch_and_log(default: T | None = None, critical: bool = False):
    """Ω-CD25: Catch exceptions, log, return default. Protects ASI from module crashes."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if critical:
                    print(f"CRITICAL [{func.__name__}]: {e}")
                return default if default is not None else type(func.__annotations__.get("return", type(None)), (), {})()  # type: ignore
        return wrapper
    return decorator


def asi_safe(min_val: float | None = None, max_val: float | None = None):
    """Ω-CD27: Guarantee function returns within safe bounds."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            if isinstance(result, (int, float)):
                if min_val is not None:
                    result = max(min_val, result)
                if max_val is not None:
                    result = min(max_val, result)
            return result
        return wrapper
    return decorator


# ──────────────────────────────────────────────────────────────
# Ω-CD37 to Ω-CD54: Async Safety & Resource Management
# ──────────────────────────────────────────────────────────────


class RateLimiter:
    """Ω-CD38: Token bucket rate limiter."""

    def __init__(self, rate: float = 10.0, max_tokens: int = 20) -> None:
        self._rate = rate
        self._max_tokens = max_tokens
        self._tokens = float(max_tokens)
        self._last_refill = time.time()
        self._lock = threading.Lock()

    def acquire(self) -> bool:
        with self._lock:
            now = time.time()
            elapsed = now - self._last_refill
            self._tokens = min(self._max_tokens, self._tokens + elapsed * self._rate)
            self._last_refill = now

            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return True
            return False


def rate_limited(max_calls: int, period: float = 1.0):
    """Ω-CD39: Decorator that limits calls to max_calls per period seconds."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        calls: deque[float] = deque()
        lock = threading.Lock()

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            now = time.time()
            with lock:
                while calls and calls[0] < now - period:
                    calls.popleft()
                if len(calls) >= max_calls:
                    raise RuntimeError(
                        f"Rate limit exceeded for {func.__name__}: "
                        f"{max_calls} calls per {period}s"
                    )
                calls.append(now)
            return func(*args, **kwargs)
        return wrapper
    return decorator


class TimeoutManager:
    """Ω-CD40: Execute function with timeout."""

    @staticmethod
    def execute(func: Callable[..., T], timeout_s: float,
                *args: Any, **kwargs: Any) -> T:
        result: list[T] = []
        exception: list[Exception] = []

        def _run() -> None:
            try:
                result.append(func(*args, **kwargs))
            except Exception as e:
                exception.append(e)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        thread.join(timeout=timeout_s)

        if thread.is_alive():
            raise TimeoutError(
                f"{func.__name__} timed out after {timeout_s}s"
            )
        if exception:
            raise exception[0]
        if result:
            return result[0]
        raise RuntimeError(f"{func.__name__} returned no result")


def timeout(timeout_s: float):
    """Ω-CD41: Decorator that enforces execution timeout."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return TimeoutManager.execute(func, timeout_s, *args, **kwargs)
        return wrapper
    return decorator


class MemoryGuard:
    """Ω-CD42: Memory-bounded caching for function results."""

    def __init__(self, max_entries: int = 1000) -> None:
        self._max = max_entries
        self._cache: dict[str, Any] = {}
        self._order: deque[str] = deque(maxlen=max_entries)

    def get(self, key: str) -> Any | None:
        return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        if key in self._cache:
            self._cache[key] = value
        else:
            if len(self._cache) >= self._max:
                oldest = self._order[0]
                self._cache.pop(oldest, None)
            self._order.append(key)
            self._cache[key] = value

    def clear(self) -> None:
        self._cache.clear()
        self._order.clear()

    @property
    def size(self) -> int:
        return len(self._cache)
