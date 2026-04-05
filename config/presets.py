"""
SOLÉNN v2 — Parameter Presets & Portability (Ω-C136 a Ω-C144)
Persistence with schema versioning, export/import, diff/patch, presets,
blueprint sharing, migration scripts, validation on import, rollback, tagging.
"""

from __future__ import annotations

import json
import time
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class ParameterPreset:
    """Ω-C139: Pre-defined parameter collection."""
    name: str
    description: str
    parameters: dict[str, Any]
    created_at: float = field(default_factory=time.time)
    tags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ParameterSnapshot:
    """Ω-C144: Tagged parameter snapshot for future reference."""
    tag: str
    parameters: dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


def compute_params_diff(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    """Ω-C138: Compute compact diff between two parameter sets."""
    diff = {}
    all_keys = set(old.keys()) | set(new.keys())
    for key in all_keys:
        if key not in old:
            diff[key] = {"action": "added", "value": new[key]}
        elif key not in new:
            diff[key] = {"action": "removed", "old_value": old[key]}
        elif old[key] != new[key]:
            diff[key] = {"action": "changed", "old_value": old[key], "new_value": new[key]}
    return diff


def apply_params_patch(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    """Apply a parameter patch to a base configuration."""
    result = dict(base)
    for key, change in patch.items():
        if isinstance(change, dict) and "action" in change:
            if change["action"] == "added" or change["action"] == "changed":
                result[key] = change["new_value"] if "new_value" in change else change.get("value")
            elif change["action"] == "removed":
                result.pop(key, None)
        else:
            result[key] = change
    return result


class ParameterPresetManager:
    """Ω-C139 to Ω-C144: Manages presets, migration, snapshots, and portability."""

    def __init__(self) -> None:
        self._presets: dict[str, ParameterPreset] = {}
        self._snapshots: dict[str, ParameterSnapshot] = {}
        self._migration_scripts: dict[tuple[str, str], Callable[[dict[str, Any]], dict[str, Any]]] = {}

    def create_preset(self, name: str, description: str, parameters: dict[str, Any], tags: list[str] | None = None) -> ParameterPreset:
        preset = ParameterPreset(name=name, description=description, parameters=deepcopy(parameters), tags=tuple(tags or []))
        self._presets[name] = preset
        return preset

    def get_preset(self, name: str) -> ParameterPreset | None:
        return self._presets.get(name)

    def list_presets(self, tag: str | None = None) -> list[ParameterPreset]:
        if tag:
            return [p for p in self._presets.values() if tag in p.tags]
        return list(self._presets.values())

    def export_preset(self, name: str, file_path: str) -> bool:
        preset = self._presets.get(name)
        if preset is None:
            return False
        data = {"name": preset.name, "description": preset.description, "parameters": preset.parameters, "tags": list(preset.tags)}
        Path(file_path).write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        return True

    def import_preset(self, file_path: str, validate_fn: Callable[[dict], list[str]] | None = None) -> tuple[bool, list[str]]:
        """Ω-C142: Import preset with schema validation."""
        try:
            data = json.loads(Path(file_path).read_text(encoding="utf-8"))
            errors: list[str] = []
            if validate_fn:
                errors = validate_fn(data.get("parameters", {}))
            if errors:
                return False, errors
            preset = ParameterPreset(name=data.get("name", Path(file_path).stem), description=data.get("description", ""), parameters=data.get("parameters", {}), tags=tuple(data.get("tags", [])))
            self._presets[preset.name] = preset
            return True, []
        except Exception as e:
            return False, [str(e)]

    def take_snapshot(self, tag: str, parameters: dict[str, Any], metadata: dict[str, Any] | None = None) -> ParameterSnapshot:
        snapshot = ParameterSnapshot(tag=tag, parameters=deepcopy(parameters), metadata=metadata or {})
        self._snapshots[tag] = snapshot
        return snapshot

    def rollback_to_snapshot(self, tag: str) -> dict[str, Any] | None:
        """Ω-C143: Rollback parameters to a tagged snapshot."""
        snapshot = self._snapshots.get(tag)
        return deepcopy(snapshot.parameters) if snapshot else None

    def list_snapshots(self) -> dict[str, ParameterSnapshot]:
        return dict(self._snapshots)

    def register_migration_script(self, from_version: str, to_version: str, script: Callable) -> None:
        self._migration_scripts[(from_version, to_version)] = script

    def migrate(self, params: dict[str, Any], from_version: str, to_version: str) -> tuple[dict[str, Any], list[str]]:
        """Ω-C141: Execute migration scripts between versions."""
        warnings: list[str] = []
        key = (from_version, to_version)
        script = self._migration_scripts.get(key)
        if script is None:
            return params, [f"No migration script from {from_version} to {to_version}"]
        try:
            result = script(params)
            return result, warnings
        except Exception as e:
            return params, [f"Migration failed: {str(e)}"]
