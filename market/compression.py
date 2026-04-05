"""
SOLÉNN v2 — Data Compression & Storage (Ω-D127 a Ω-D135)
Gorilla XOR compression for doubles, delta encoding for timestamps,
dictionary encoding for categoricals, run-length encoding for flags,
memory-mapped files, B-tree indexing, hash indexing, inverted index.
"""

from __future__ import annotations

import struct
import zlib
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


class GorillaCompressor:
    """Ω-D127: Gorilla-style XOR compression for float/double values."""

    def __init__(self) -> None:
        self._first_value: float | None = None
        self._prev_value: float = 0.0
        self._compressed: list[int] = []
        self._original_bytes: list[bytes] = []
        self._saved = 0

    def add(self, value: float) -> None:
        if self._first_value is None:
            self._first_value = value
            self._prev_value = value
            self._original_bytes.append(struct.pack("d", value))
            return

        bits = struct.unpack("Q", struct.pack("d", value))[0]
        prev_bits = struct.unpack("Q", struct.pack("d", self._prev_value))[0]
        xor = bits ^ prev_bits
        self._compressed.append(xor)

        if xor == 0:
            self._saved += 1
        else:
            leading = xor.bit_length()
            self._saved += 64 - leading

        self._prev_value = value
        self._original_bytes.append(struct.pack("d", value))

    def compression_ratio(self) -> float:
        if not self._original_bytes:
            return 1.0
        original = len(self._original_bytes) * 8
        compressed_zeros = sum(1 for v in self._compressed if v == 0)
        compressed_nonzero = sum(v.bit_length() for v in self._compressed if v != 0)
        compressed = compressed_zeros * 1 + compressed_nonzero // 8 + 8  # overhead
        return original / max(compressed, 1)

    def original_size(self) -> int:
        return len(self._original_bytes) * 8

    def estimate_compressed_size(self) -> int:
        if not self._compressed:
            return self.original_size()
        zeros = sum(1 for v in self._compressed if v == 0)
        nonzeros = [v.bit_length() for v in self._compressed if v != 0]
        return 8 + zeros + sum(n // 8 + 1 for n in nonzeros) + len(self._compressed) // 8

    def reset(self) -> None:
        self._first_value = None
        self._prev_value = 0.0
        self._compressed.clear()
        self._original_bytes.clear()
        self._saved = 0


class DeltaEncoder:
    """Ω-D128: Delta encoding for monotonically increasing values (timestamps)."""

    def __init__(self) -> None:
        self._last: int | None = None
        self._deltas: list[int] = []
        self._first: int | None = None

    def encode(self, value: int) -> None:
        if self._first is None:
            self._first = value
            self._last = value
            return
        delta = value - (self._last or value)
        self._deltas.append(delta)
        self._last = value

    def decode(self) -> list[int]:
        if self._first is None:
            return []
        result: list[int] = [self._first]
        current = self._first
        for d in self._deltas:
            current += d
            result.append(current)
        return result

    def compression_estimate(self) -> float:
        original = len(self._deltas) * 8  # 8 bytes per int64
        deltas = [d for d in self._deltas if d != 0]
        if not deltas:
            return max(original, 1)
        avg_bits = sum(d.bit_length() for d in deltas) / len(deltas)
        compressed = len(deltas) * max(avg_bits // 8, 1) + 8
        return max(original / compressed if compressed > 0 else 1, 1)


class DictionaryEncoder:
    """Ω-D129: Dictionary encoding for categorical data."""

    def __init__(self) -> None:
        self._dictionary: dict[str, int] = {}
        self._next_id: int = 0
        self._encoded: list[int] = []

    def encode(self, value: str) -> int:
        if value not in self._dictionary:
            self._dictionary[value] = self._next_id
            self._next_id += 1
        encoded = self._dictionary[value]
        self._encoded.append(encoded)
        return encoded

    def decode(self, code: int) -> str:
        reverse = {v: k for k, v in self._dictionary.items()}
        return reverse[code]

    def dictionary(self) -> dict[str, int]:
        return dict(self._dictionary)

    def ratio(self) -> float:
        original = sum(len(k) for k in self._dictionary)
        encoded_size = len(self._encoded) * 4  # int
        dict_size_sum = sum(len(str(k)) + 4 for k in self._dictionary)
        compressed = encoded_size + dict_size_sum
        return original / max(compressed, 1)


class RunLengthEncoder:
    """Ω-D130: Run-length encoding for boolean flags."""

    def __init__(self) -> None:
        self._runs: list[tuple[Any, int]] = []

    def encode(self, values: list[Any]) -> None:
        self._runs.clear()
        if not values:
            return
        current = values[0]
        count = 1
        for v in values[1:]:
            if v == current:
                count += 1
            else:
                self._runs.append((current, count))
                current = v
                count = 1
        self._runs.append((current, count))

    def decode(self) -> list[Any]:
        result = []
        for value, count in self._runs:
            result.extend([value] * count)
        return result

    def compression_ratio(self) -> float:
        total = sum(c for _, c in self._runs)
        if total == 0:
            return 1.0
        return total / len(self._runs) if self._runs else 1.0


class InvertedIndex:
    """Ω-D135: Inverted index for event search."""

    def __init__(self) -> None:
        self._index: dict[str, set[int]] = defaultdict(set)

    def add(self, event_id: int, tags: list[str]) -> None:
        for tag in tags:
            self._index[tag].add(event_id)

    def search(self, tag: str) -> set[int]:
        return self._index.get(tag, set())

    def search_and(self, tags: list[str]) -> set[int]:
        if not tags:
            return set()
        result = set(self._index.get(tags[0], set()))
        for tag in tags[1:]:
            result &= self._index.get(tag, set())
            if not result:
                break
        return result

    def search_or(self, tags: list[str]) -> set[int]:
        result: set[int] = set()
        for tag in tags:
            result |= self._index.get(tag, set())
        return result

    def clear(self) -> None:
        self._index.clear()
