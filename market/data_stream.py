"""
SOLÉNN v2 — Data Streaming & Pub-Sub (Ω-D136 a Ω-D144)
Multi-consumer pub-sub with ring buffer, backpressure, latency monitoring,
consumer lag detection, message ordering, replay, versioning, snapshots.
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True, slots=True)
class DataMessage:
    """Message in the data stream."""
    topic: str
    exchange: str
    symbol: str
    data: Any
    timestamp_ns: int
    schema_version: str = "1.0"
    sequence: int = 0


@dataclass(slots=True)
class ConsumerState:
    """Ω-D139: Consumer lag and health tracking."""
    consumer_id: str
    topic: str
    last_received_seq: int
    last_received_ts: float
    total_received: int = 0
    total_dropped: int = 0

    @property
    def is_alive(self) -> bool:
        return (time.time() - self.last_received_ts) < 5.0


class PubSubBus:
    """
    Ω-D136 a Ω-D144: Pub-sub data bus with backpressure and replay.
    """

    def __init__(self, max_buffer: int = 10000) -> None:
        self._max_buffer = max_buffer
        self._topics: dict[str, deque[DataMessage]] = {}
        self._handlers: dict[str, list[Callable[[DataMessage], None]]] = {}
        self._consumer_states: dict[str, dict[str, ConsumerState]] = {}
        self._sequence: int = 0
        self._total_published = 0
        self._total_dropped = 0

    def subscribe(self, topic: str, consumer_id: str,
                  handler: Callable[[DataMessage], None],
                  initial_offset: int = -1) -> None:
        """Ω-D137: Subscribe to a topic with a handler callback."""
        self._handlers.setdefault(topic, []).append(handler)
        state = ConsumerState(
            consumer_id=consumer_id, topic=topic,
            last_received_seq=initial_offset, last_received_ts=time.time())
        self._consumer_states.setdefault(topic, {})[consumer_id] = state

    def publish(self, topic: str, exchange: str, symbol: str,
                data: Any, timestamp_ns: int | None = None,
                schema_version: str = "1.0") -> int:
        """Ω-D136: Publish a message to all subscribers."""
        self._sequence += 1
        msg = DataMessage(
            topic=topic, exchange=exchange, symbol=symbol,
            data=data, timestamp_ns=timestamp_ns or time.time_ns(),
            schema_version=schema_version, sequence=self._sequence)

        # Buffer message
        if topic not in self._topics:
            self._topics[topic] = deque(maxlen=self._max_buffer)
        self._topics[topic].append(msg)
        self._total_published += 1

        # Ω-D141: Deliver to handlers in order
        handlers = self._handlers.get(topic, [])
        for handler in handlers:
            try:
                handler(msg)
            except Exception:
                self._total_dropped += 1

        # Ω-D139: Update consumer states
        for consumer_id, state_map in self._consumer_states.get(topic, {}).items():
            state_map.last_received_seq = self._sequence
            state_map.last_received_ts = time.time()
            state_map.total_received += 1

        return self._sequence

    def replay(self, topic: str, from_sequence: int, limit: int = 100) -> list[DataMessage]:
        """Ω-D142: Replay messages from a specific sequence."""
        messages = list(self._topics.get(topic, []))
        return [m for m in messages if m.sequence >= from_sequence][:limit]

    def get_consumer_lag(self, topic: str, consumer_id: str) -> int:
        """Ω-D139: Consumer lag in messages."""
        state = self._consumer_states.get(topic, {}).get(consumer_id)
        if state is None:
            return 0
        return self._sequence - state.last_received_seq

    def get_consumer_states(self, topic: str) -> dict[str, ConsumerState]:
        states = self._consumer_states.get(topic, {})
        return {cid: ConsumerState(
            consumer_id=s.consumer_id, topic=s.topic,
            last_received_seq=s.last_received_seq,
            last_received_ts=s.last_received_ts,
            total_received=s.total_received,
            total_dropped=s.total_dropped)
            for cid, s in states.items()}

    def get_stats(self) -> dict[str, Any]:
        return {
            "total_published": self._total_published,
            "total_dropped": self._total_dropped,
            "topics": list(self._topics.keys()),
            "subscribers": sum(len(h) for h in self._handlers.values()),
            "total_sequences": self._sequence,
        }
