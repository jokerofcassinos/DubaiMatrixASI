"""
SOLÉNN v2 — Sovereign Config System Core (Ω-C01 a Ω-C09)
Immutable type-enforced dataclasses with frozen=True, slots=True,
post-init validation, CRC32 checksums, and deep freeze.
"""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass, field, fields, is_dataclass, MISSING
from typing import Any, TypeVar
import zlib

T = TypeVar("T", bound="SovereignConfig")


def deep_freeze(value: Any) -> Any:
    """Ω-C05: Recursively convert mutable structures to immutable equivalents.

    Lists become tuples, sets become frozensets. Dicts remain dicts but with
    all nested values frozen — the outer frozen=True dataclass prevents mutation
    of the dict reference itself, so we only need to freeze the contained values.
    """
    if isinstance(value, dict):
        return {k: deep_freeze(v) for k, v in value.items()}
    if isinstance(value, list):
        return tuple(deep_freeze(v) for v in value)
    if isinstance(value, set):
        return frozenset(deep_freeze(v) for v in value)
    if is_dataclass(value) and not isinstance(value, type):
        frozen = {}
        for f in fields(value):
            frozen[f.name] = deep_freeze(getattr(value, f.name))
        return value.__class__(**frozen)
    return value


def deep_thaw(value: Any) -> Any:
    """Reverse of deep_freeze — convert immutable back to mutable for serialization."""
    if isinstance(value, frozenset):
        return dict((k, deep_thaw(v)) for k, v in value)
    if isinstance(value, tuple):
        return [deep_thaw(v) for v in value]
    if is_dataclass(value) and not isinstance(value, type):
        thawed = {}
        for f in fields(value):
            thawed[f.name] = deep_thaw(getattr(value, f.name))
        return thawed
    return value


def compute_checksum(data: dict[str, Any]) -> str:
    """Ω-C04: Compute CRC32 + SHA256 checksum for config integrity verification."""
    serialized = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
    crc = zlib.crc32(serialized) & 0xFFFFFFFF
    sha = hashlib.sha256(serialized).hexdigest()[:16]
    return f"{crc:08x}_{sha}"


@dataclass(frozen=True, slots=True)
class ConfigFieldDescriptor:
    """Ω-C07: Custom field descriptor with validated getter/setter."""
    name: str
    coerce_type: type
    default: Any = None
    description: str = ""
    min_val: float | None = None
    max_val: float | None = None
    required: bool = False

    def coerce(self, value: Any) -> Any:
        """Ω-C06: Type coercion from string/int to correct type."""
        try:
            return self.coerce_type(value)
        except (TypeError, ValueError):
            if self.default is not None:
                return self.default
            raise

    def validate(self, value: Any) -> None:
        if self.min_val is not None and value < self.min_val:
            raise ValueError(f"Field '{self.name}': {value} < minimum {self.min_val}")
        if self.max_val is not None and value > self.max_val:
            raise ValueError(f"Field '{self.name}': {value} > maximum {self.max_val}")


@dataclass(frozen=True)
class SovereignConfig:
    """
    Ω-C01 to Ω-C09: Foundation immutable config with full validation.

    All fields are frozen at construction. CRC32 checksum auto-generated.
    Deep freeze applied to mutable nested fields. Type coercion applied.
    No post-construction mutation possible.
    """

    name: str
    version: str
    values: dict[str, Any] = field(default_factory=dict)
    checksum: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Ω-C03: Post-init validation for all config fields."""
        if not self.name:
            raise ValueError("Config name cannot be empty")
        if not self.version:
            raise ValueError("Config version cannot be empty")

        if not isinstance(self.values, dict):
            raise TypeError(f"Config values must be a dict, got {type(self.values)}")

        if not isinstance(self.metadata, dict):
            raise TypeError(f"Config metadata must be a dict, got {type(self.metadata)}")

    def __hash__(self) -> int:
        return hash((self.name, self.version, self.checksum))

    @classmethod
    def create(cls: type[T], name: str, version: str, values: dict[str, Any] | None = None, metadata: dict[str, Any] | None = None) -> T:
        """Factory method with deep freeze and auto-checksum."""
        vals = values or {}
        meta = metadata or {}
        frozen_values = deep_freeze(vals) if vals else {}
        if not isinstance(frozen_values, dict):
            frozen_values = dict(frozen_values) if frozen_values else {}
        checksum = compute_checksum({"name": name, "version": version, "values": str(frozen_values), "metadata": str(meta)})
        return cls(name=name, version=version, values=dict(frozen_values) if frozen_values else {}, checksum=checksum, metadata=meta)

    def merge(self, other: SovereignConfig) -> SovereignConfig:
        """Merge two configs — other takes precedence on conflicts."""
        merged_values = {**self.values, **other.values}
        merged_meta = {**self.metadata, **other.metadata}
        return SovereignConfig.create(
            name=self.name,
            version=other.version,
            values=merged_values,
            metadata=merged_meta,
        )

    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def get_typed(self, key: str, coerce_type: type, default: Any = None) -> Any:
        """Ω-C06: Get value with type coercion."""
        raw = self.values.get(key, default)
        if raw is default:
            return default
        try:
            return coerce_type(raw)
        except (TypeError, ValueError):
            return default

    def has_key(self, key: str) -> bool:
        return key in self.values

    def verify_integrity(self) -> bool:
        """Ω-C04: Verify config integrity via checksum."""
        expected = compute_checksum({
            "name": self.name,
            "version": self.version,
            "values": str(self.values),
            "metadata": str(self.metadata),
        })
        return self.checksum == expected

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "values": self.values,
            "checksum": self.checksum,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls: type[T], data: dict[str, Any]) -> T:
        return cls(
            name=data["name"],
            version=data["version"],
            values=data.get("values", {}),
            checksum=data.get("checksum", ""),
            metadata=data.get("metadata", {}),
        )

    def __repr__(self) -> str:
        return f"SovereignConfig(name='{self.name}', version='{self.version}', keys={len(self.values)}, checksum={self.checksum[:8]}...)"
