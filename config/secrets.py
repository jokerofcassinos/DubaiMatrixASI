"""
SOLÉNN v2 — Secrets & Security (Ω-C37 a Ω-C45)
Secret detection, masking, encrypted storage, in-memory zeroing,
access auditing, permission levels, rotation, tamper detection, secure defaults.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class PermissionLevel(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    RESTRICTED = "restricted"
    CLASSIFIED = "classified"


ACCESS_LEVELS = {PermissionLevel.PUBLIC: 0, PermissionLevel.INTERNAL: 1, PermissionLevel.RESTRICTED: 2, PermissionLevel.CLASSIFIED: 3}

SECRET_PATTERNS = [
    ("api_key", re.compile(r"api[_-]?key[:=\s]+\S{16,}", re.IGNORECASE)),
    ("password", re.compile(r"password[:=\s]+\S{4,}", re.IGNORECASE)),
    ("token", re.compile(r"token[:=\s]+[A-Za-z0-9_-]{16,}", re.IGNORECASE)),
    ("secret", re.compile(r"secret[:=\s]+\S{16,}", re.IGNORECASE)),
    ("aws_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private_key", re.compile(r"-----BEGIN (RSA |EC )?PRIVATE KEY-----")),
    ("bearer_token", re.compile(r"Bearer\s+[A-Za-z0-9_\-.]+")),
]


@dataclass(frozen=True, slots=True)
class SecretReference:
    name: str
    permission: PermissionLevel = PermissionLevel.RESTRICTED
    created_at: float = field(default_factory=time.time)
    expires_at: float | None = None
    rotation_count: int = 0


def detect_secrets_in_text(text: str) -> list[tuple[str, str]]:
    """Ω-C37: Detect secrets in text and return (type, masked_value)."""
    findings = []
    for secret_type, pattern in SECRET_PATTERNS:
        for match in pattern.finditer(text):
            value = match.group(0)
            masked = value[:6] + "*" * (len(value) - 8) + value[-2:]
            findings.append((secret_type, masked))
    return findings


def mask_secret(value: str) -> str:
    """Ω-C38: Mask a secret value for safe logging."""
    if len(value) <= 4:
        return "***"
    return value[:2] + "*" * (len(value) - 4) + value[-2:]


def zero_memory(bytearray_ref: bytearray) -> None:
    """Ω-C40: Overwrite bytearray with zeros for secure clearing."""
    for i in range(len(bytearray_ref)):
        bytearray_ref[i] = 0


class EncryptedConfigStorage:
    """
    Ω-C39: Encrypted config storage using XOR-based light obfuscation
    (production should use Fernet/AES — this is a placeholder pattern).
    """

    def __init__(self, key: bytes | None = None) -> None:
        self._key = key or secrets.token_bytes(32)
        self._encrypted: dict[str, bytes] = {}

    def _xor_encrypt(self, plaintext: bytes) -> bytes:
        key_len = len(self._key)
        return bytes(p ^ self._key[i % key_len] for i, p in enumerate(plaintext))

    def store(self, key_name: str, secret_value: str) -> None:
        self._encrypted[key_name] = self._xor_encrypt(secret_value.encode("utf-8"))

    def retrieve(self, key_name: str) -> str:
        encrypted = self._encrypted.get(key_name)
        if encrypted is None:
            raise KeyError(f"Secret not found: {key_name}")
        return self._xor_encrypt(encrypted).decode("utf-8")

    def rotate(self, key_name: str, new_value: str) -> None:
        self.store(key_name, new_value)

    def delete(self, key_name: str) -> None:
        self._encrypted.pop(key_name, None)


class SecretAccessAuditLog:
    """Ω-C41: Audit log for secret access tracking."""

    def __init__(self) -> None:
        self._entries: list[dict[str, Any]] = []

    def log_access(self, secret_name: str, accessor: str, action: str, success: bool = True) -> None:
        self._entries.append({
            "timestamp": time.time(),
            "secret": mask_secret(secret_name),
            "accessor": accessor,
            "action": action,
            "success": success,
        })

    def get_entries(self, since: float = 0) -> list[dict[str, Any]]:
        return [e for e in self._entries if e["timestamp"] >= since]

    def export(self) -> list[dict[str, Any]]:
        return list(self._entries)


class ConfigTamperDetector:
    """Ω-C44: Hash-based config tamper detection."""

    def __init__(self) -> None:
        self._hashes: dict[str, str] = {}

    def register(self, file_path: str) -> None:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        content = path.read_bytes()
        self._hashes[file_path] = hashlib.sha256(content).hexdigest()

    def check(self, file_path: str) -> bool:
        path = Path(file_path)
        if not path.exists():
            return False
        content = path.read_bytes()
        current_hash = hashlib.sha256(content).hexdigest()
        return self._hashes.get(file_path) == current_hash

    def register_content(self, name: str, content: str) -> None:
        self._hashes[name] = hashlib.sha256(content.encode("utf-8")).hexdigest()

    def check_content(self, name: str, content: str) -> bool:
        return self._hashes.get(name) == hashlib.sha256(content.encode("utf-8")).hexdigest()


class SecretManager:
    """
    Ω-C37 a Ω-C45: Unified secret management facade.
    """

    def __init__(self, storage: EncryptedConfigStorage | None = None) -> None:
        self._storage = storage or EncryptedConfigStorage()
        self._audit = SecretAccessAuditLog()
        self._tamper = ConfigTamperDetector()
        self._permissions: dict[str, PermissionLevel] = {}
        self._secret_refs: dict[str, SecretReference] = {}

    def store_secret(self, name: str, value: str, permission: PermissionLevel = PermissionLevel.RESTRICTED, access_level: PermissionLevel = PermissionLevel.CLASSIFIED) -> None:
        has_perm = ACCESS_LEVELS.get(access_level, 0) >= ACCESS_LEVELS.get(permission, 0)
        if not has_perm:
            raise PermissionError(f"Insufficient permissions to store secret: {name}")
        self._storage.store(name, value)
        self._permissions[name] = permission
        self._secret_refs[name] = SecretReference(name=name, permission=permission)
        self._audit.log_access(name, "system", "store", success=True)

    def get_secret(self, name: str, accessor: str, access_level: PermissionLevel = PermissionLevel.RESTRICTED) -> str:
        perm = self._permissions.get(name, PermissionLevel.PUBLIC)
        has_perm = ACCESS_LEVELS.get(access_level, 0) >= ACCESS_LEVELS.get(perm, 0)
        if not has_perm:
            self._audit.log_access(name, accessor, "get", success=False)
            raise PermissionError(f"Insufficient permissions to access secret: {name}")
        value = self._storage.retrieve(name)
        self._audit.log_access(name, accessor, "get", success=True)
        return value

    def rotate_secret(self, name: str, new_value: str, accessor: str, access_level: PermissionLevel = PermissionLevel.RESTRICTED) -> None:
        has_perm = ACCESS_LEVELS.get(access_level, 0) >= ACCESS_LEVELS.get(self._permissions.get(name, PermissionLevel.PUBLIC), 0)
        if not has_perm:
            raise PermissionError(f"Insufficient permissions to rotate secret: {name}")
        self._storage.rotate(name, new_value)
        ref = self._secret_refs.get(name)
        if ref:
            self._secret_refs[name] = SecretReference(
                name=name, permission=ref.permission, created_at=ref.created_at, expires_at=ref.expires_at, rotation_count=ref.rotation_count + 1
            )
        self._audit.log_access(name, accessor, "rotate", success=True)

    def get_audit_entries(self, since: float = 0) -> list[dict[str, Any]]:
        return self._audit.get_entries(since)

    def check_tampering(self, file_path: str) -> bool:
        return self._tamper.check(file_path)

    def register_file(self, file_path: str) -> None:
        self._tamper.register(file_path)


SAFE_DEFAULTS: dict[str, Any] = {
    "max_retries": 3,
    "timeout_ms": 5000,
    "log_level": "INFO",
    "max_connections": 10,
    "retry_delay_ms": 1000,
    "enable_tls": True,
}
