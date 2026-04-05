"""
SOLÉNN v2 — Bounded Allocation Ring Buffers (Ω-C10 a Ω-C18)
Lock-free SPSC ring buffer with configurable overflow strategies,
memory-bounded allocation, and config-driven sizing.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, TypeVar, Optional, Sequence, Iterator
from collections.abc import MutableSequence

T = TypeVar("T")


class OverflowStrategy(Enum):
    """Strategy for handling ring buffer overflow."""
    DROP_OLDEST = "drop_oldest"
    DROP_NEWEST = "drop_newest"
    RAISE_EXCEPTION = "raise_exception"


@dataclass(frozen=True, slots=True)
class RingBufferConfig:
    """Immutable configuration for a RingBuffer instance (Ω-C18)."""
    capacity: int
    overflow_strategy: OverflowStrategy = OverflowStrategy.DROP_OLDEST
    thread_safe: bool = True

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise ValueError(f"RingBuffer capacity must be > 0, got {self.capacity}")


@dataclass(frozen=True, slots=True)
class RingBufferSnapshot:
    """Immutable snapshot of ring buffer state at a point in time."""
    items: tuple
    head: int
    tail: int
    size: int
    capacity: int
    overflow_count: int

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RingBufferSnapshot):
            return NotImplemented
        return (self.items == other.items and
                self.head == other.head and
                self.tail == other.tail and
                self.size == other.size and
                self.capacity == other.capacity)


class RingBuffer(Generic[T]):
    """
    Thread-safe ring buffer with configurable overflow strategies.

    Supports SPSC (single-producer single-consumer) lock-free access
    when thread_safe=False, and full thread-safety when thread_safe=True.
    Memory is pre-allocated and bounded — no dynamic growth.
    """

    def __init__(self, config: RingBufferConfig) -> None:
        self._config = config
        self._buffer: list[Optional[T]] = [None] * config.capacity
        self._head = 0
        self._tail = 0
        self._size = 0
        self._overflow_count = 0
        self._lock = threading.Lock() if config.thread_safe else None
        self._not_empty = threading.Condition(self._lock) if config.thread_safe else None
        self._not_full = threading.Condition(self._lock) if config.thread_safe else None

    @property
    def config(self) -> RingBufferConfig:
        return self._config

    @property
    def capacity(self) -> int:
        return self._config.capacity

    @property
    def size(self) -> int:
        return self._size

    @property
    def is_empty(self) -> bool:
        return self._size == 0

    @property
    def is_full(self) -> bool:
        return self._size == self._config.capacity

    @property
    def overflow_count(self) -> int:
        return self._overflow_count

    @property
    def fill_ratio(self) -> float:
        return self._size / self._config.capacity if self._config.capacity > 0 else 0.0

    def push(self, item: T) -> None:
        """Push item to buffer. Behavior on overflow depends on strategy."""
        if self._lock is not None:
            with self._lock:
                self._push_unsafe(item)
        else:
            self._push_unsafe(item)

    def _push_unsafe(self, item: T) -> None:
        if self._size == self._config.capacity:
            strategy = self._config.overflow_strategy
            if strategy == OverflowStrategy.DROP_OLDEST:
                self._tail = (self._tail + 1) % self._config.capacity
                self._buffer[self._head] = item
                self._head = (self._head + 1) % self._config.capacity
                self._overflow_count += 1
            elif strategy == OverflowStrategy.DROP_NEWEST:
                self._overflow_count += 1
                return
            elif strategy == OverflowStrategy.RAISE_EXCEPTION:
                self._overflow_count += 1
                raise BufferError(
                    f"RingBuffer full (capacity={self._config.capacity}). "
                    f"Overflow strategy: RAISE_EXCEPTION"
                )
        else:
            self._buffer[self._head] = item
            self._head = (self._head + 1) % self._config.capacity
            self._size += 1

    def pop(self) -> Optional[T]:
        """Pop oldest item from buffer. Returns None if empty."""
        if self._lock is not None:
            with self._lock:
                return self._pop_unsafe()
        else:
            return self._pop_unsafe()

    def _pop_unsafe(self) -> Optional[T]:
        if self._size == 0:
            return None
        item = self._buffer[self._tail]
        self._buffer[self._tail] = None
        self._tail = (self._tail + 1) % self._config.capacity
        self._size -= 1
        return item

    def peek(self) -> Optional[T]:
        """Peek at oldest item without removing it."""
        if self._lock is not None:
            with self._lock:
                return self._peek_unsafe()
        else:
            return self._peek_unsafe()

    def _peek_unsafe(self) -> Optional[T]:
        if self._size == 0:
            return None
        return self._buffer[self._tail]

    def get_all(self) -> list[T]:
        """Return all items in order (oldest to newest)."""
        if self._lock is not None:
            with self._lock:
                return self._get_all_unsafe()
        else:
            return self._get_all_unsafe()

    def _get_all_unsafe(self) -> list[T]:
        result: list[T] = []
        idx = self._tail
        for _ in range(self._size):
            item = self._buffer[idx]
            if item is not None:
                result.append(item)
            idx = (idx + 1) % self._config.capacity
        return result

    def clear(self) -> None:
        """Clear all items from buffer."""
        if self._lock is not None:
            with self._lock:
                self._clear_unsafe()
        else:
            self._clear_unsafe()

    def _clear_unsafe(self) -> None:
        self._buffer = [None] * self._config.capacity
        self._head = 0
        self._tail = 0
        self._size = 0

    def snapshot(self) -> RingBufferSnapshot:
        """Take an immutable snapshot of current state."""
        if self._lock is not None:
            with self._lock:
                return self._snapshot_unsafe()
        else:
            return self._snapshot_unsafe()

    def _snapshot_unsafe(self) -> RingBufferSnapshot:
        items = tuple(self._get_all_unsafe())
        return RingBufferSnapshot(
            items=items,
            head=self._head,
            tail=self._tail,
            size=self._size,
            capacity=self._config.capacity,
            overflow_count=self._overflow_count,
        )

    def __len__(self) -> int:
        return self._size

    def __bool__(self) -> bool:
        return self._size > 0

    def __contains__(self, item: object) -> bool:
        if self._lock is not None:
            with self._lock:
                return item in self._buffer[:self._size]
        return item in self._buffer[:self._size]

    def __iter__(self) -> Iterator[T]:
        if self._lock is not None:
            with self._lock:
                return iter(self._get_all_unsafe())
        return iter(self._get_all_unsafe())

    def __repr__(self) -> str:
        return (
            f"RingBuffer(capacity={self._config.capacity}, "
            f"size={self._size}, "
            f"overflow_strategy={self._config.overflow_strategy.value}, "
            f"overflow_count={self._overflow_count})"
        )

    def __getstate__(self) -> dict:
        return {
            "config": self._config,
            "items": self.get_all(),
            "overflow_count": self._overflow_count,
        }

    def __setstate__(self, state: dict) -> None:
        self._config = state["config"]
        self._buffer = [None] * self._config.capacity
        self._head = 0
        self._tail = 0
        self._size = 0
        self._overflow_count = state["overflow_count"]
        for item in state["items"]:
            self._push_unsafe(item)
        self._lock = threading.Lock() if self._config.thread_safe else None
        self._not_empty = threading.Condition(self._lock) if self._config.thread_safe else None
        self._not_full = threading.Condition(self._lock) if self._config.thread_safe else None
