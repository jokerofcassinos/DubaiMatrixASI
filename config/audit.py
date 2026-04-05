"""
SOLÉNN v2 — Config-as-Code Audit System (Ω-C46 a Ω-C54)
Full config dump, diff generator, version tracking, dependency graph,
deprecation warnings, migration assistant, compliance checker.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ComplianceStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"


@dataclass(frozen=True, slots=True)
class ComplianceCheck:
    rule_id: str
    description: str
    status: ComplianceStatus
    details: str = ""


@dataclass(frozen=True, slots=True)
class ConfigDiff:
    added: dict[str, Any]
    removed: dict[str, Any]
    changed: dict[str, tuple[Any, Any]]
    timestamp: float = field(default_factory=time.time)


def deep_equal(a: dict[str, Any], b: dict[str, Any]) -> bool:
    if set(a.keys()) != set(b.keys()):
        return False
    for key in a:
        if isinstance(a[key], dict) and isinstance(b[key], dict):
            if not deep_equal(a[key], b[key]):
                return False
        elif a[key] != b[key]:
            return False
    return True


def compute_config_diff(old: dict[str, Any], new: dict[str, Any]) -> ConfigDiff:
    """Ω-C47: Compute diff between two config dictionaries."""
    old_keys = set(old.keys())
    new_keys = set(new.keys())
    added = {k: new[k] for k in new_keys - old_keys}
    removed = {k: old[k] for k in old_keys - new_keys}
    changed: dict[str, tuple[Any, Any]] = {}
    for key in old_keys & new_keys:
        if isinstance(old[key], dict) and isinstance(new[key], dict):
            sub_diff = compute_config_diff(old[key], new[key])
            if sub_diff.added or sub_diff.removed or sub_diff.changed:
                changed[key] = (old[key], new[key])
        elif old[key] != new[key]:
            changed[key] = (old[key], new[key])
    return ConfigDiff(added=added, removed=removed, changed=changed)


class ConfigAuditTrail:
    """Ω-C48: Ring buffer-based history of all config changes."""

    def __init__(self, max_entries: int = 1000) -> None:
        self._entries: list[dict[str, Any]] = []
        self._max = max_entries

    def record(self, action: str, config_name: str, details: dict[str, Any], actor: str = "system") -> None:
        entry = {
            "timestamp": time.time(),
            "action": action,
            "config": config_name,
            "details": details,
            "actor": actor,
        }
        self._entries.append(entry)
        if len(self._entries) > self._max:
            self._entries = self._entries[-self._max:]

    def get_entries(self, limit: int = 50) -> list[dict[str, Any]]:
        return list(self._entries[-limit:])


class ConfigDependencyGraph:
    """Ω-C50: Build and query config dependency relations."""

    def __init__(self) -> None:
        self._dependencies: dict[str, set[str]] = {}
        self._dependents: dict[str, set[str]] = {}

    def add_dependency(self, source: str, target: str) -> None:
        self._dependencies.setdefault(source, set()).add(target)
        self._dependents.setdefault(target, set()).add(source)

    def get_dependencies(self, config_name: str) -> set[str]:
        return set(self._dependencies.get(config_name, set()))

    def get_dependents(self, config_name: str) -> set[str]:
        return set(self._dependents.get(config_name, set()))

    def detect_cycles(self) -> list[list[str]]:
        visited: set[str] = set()
        cycles: list[list[str]] = []

        def dfs(node: str, path: list[str]) -> None:
            if node in path:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:])
                return
            if node in visited:
                return
            visited.add(node)
            path.append(node)
            for dep in self._dependencies.get(node, set()):
                dfs(dep, list(path))

        for node in self._dependencies:
            dfs(node, [])
        return cycles

    def to_dict(self) -> dict[str, list[str]]:
        return {k: list(v) for k, v in self._dependencies.items()}


class ConfigComplianceChecker:
    """Ω-C54: Validate config against 12 architectural commandments."""

    def __init__(self) -> None:
        self._rules: dict[str, ComplianceCheck] = {}

    def register_rule(self, rule_id: str, description: str, check_fn: Any) -> None:
        result = check_fn()
        self._rules[rule_id] = ComplianceCheck(
            rule_id=rule_id, description=description, status=result,
        )

    def run_all(self) -> dict[str, ComplianceCheck]:
        return dict(self._rules)

    def summary(self) -> dict[str, int]:
        counts = {s.value: 0 for s in ComplianceStatus}
        for check in self._rules.values():
            counts[check.status.value] += 1
        return counts


class ConfigOrphanDetector:
    """Ω-C49: Detect configs that no module reads or uses."""

    def __init__(self) -> None:
        self._access_counts: dict[str, int] = {}

    def record_access(self, config_name: str) -> None:
        self._access_counts[config_name] = self._access_counts.get(config_name, 0) + 1

    def find_orphans(self, all_configs: set[str]) -> set[str]:
        return all_configs - set(self._access_counts.keys())

    def get_usage_stats(self) -> dict[str, int]:
        return dict(self._access_counts)


class ConfigMigrationAssistant:
    """Ω-C53: Detect and suggest migration from old field names to new."""

    def __init__(self) -> None:
        self._field_mappings: dict[str, str] = {}
        self._deprecations: dict[str, str] = {}

    def register_mapping(self, old_name: str, new_name: str, deprecation_reason: str = "renamed") -> None:
        self._field_mappings[old_name] = new_name
        self._deprecations[old_name] = deprecation_reason

    def migrate(self, config: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
        warnings_list: list[str] = []
        migrated = {}
        for key, value in config.items():
            if key in self._field_mappings:
                new_key = self._field_mappings[key]
                migrated[new_key] = value
                warnings_list.append(f"Field '{key}' deprecated ({self._deprecations[key]}) — migrated to '{new_key}'")
            else:
                migrated[key] = value
        return migrated, warnings_list
