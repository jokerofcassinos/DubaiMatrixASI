"""
SOLÉNN v2 — Config Loading Pipeline (Ω-C28 a Ω-C36)
Multi-source config loader, template substitution, schema validation,
hot-reload, lazy loading, inheritance, encryption, versioning.
"""

from __future__ import annotations

import json
import os
import re
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .sovereign_config import SovereignConfig, compute_checksum


@dataclass(frozen=True, slots=True)
class LoadResult:
    """Result of a config load operation."""
    config: SovereignConfig
    source: str
    load_time_ms: float
    warnings: tuple[str, ...] = ()
    schema_errors: tuple[str, ...] = ()


class ConfigMergeStrategy:
    """Ω-C29: Multi-source config merge with precedence ordering."""

    @staticmethod
    @staticmethod
    def merge(
        configs: list[tuple[str, dict[str, Any]]],
    ) -> dict[str, Any]:
        """Merge configs in descending precedence order.

        Args:
            configs: list of (source_name, config_dict) tuples.
                     LAST entry has highest precedence.

        Returns:
            Merged dictionary.
        """
        merged: dict[str, Any] = {}
        for source_name, cfg in configs:
            ConfigMergeStrategy._deep_merge(merged, cfg)
        return merged

    @staticmethod
    def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> None:
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                ConfigMergeStrategy._deep_merge(base[key], value)
            else:
                base[key] = deepcopy(value)


class ConfigTemplateEngine:
    """Ω-C30: Template substitution with environment variables."""

    ENV_VAR_PATTERN = re.compile(r"\{\{(\w+)\}\}")
    ENV_VAR_DEFAULT_PATTERN = re.compile(r"\{\{(\w+):([^}]*)\}\}")

    @staticmethod
    def substitute(template: str, env_vars: dict[str, str] | None = None) -> str:
        if env_vars is None:
            env_vars = dict(os.environ)
        for match in ConfigTemplateEngine.ENV_VAR_DEFAULT_PATTERN.finditer(template):
            var_name, default_val = match.group(1), match.group(2)
            template = template.replace(match.group(0), env_vars.get(var_name, default_val))
        for match in ConfigTemplateEngine.ENV_VAR_PATTERN.finditer(template):
            var_name = match.group(1)
            template = template.replace(match.group(0), env_vars.get(var_name, ""))
        return template

    @staticmethod
    def substitute_dict(data: dict[str, Any], env_vars: dict[str, str] | None = None) -> dict[str, Any]:
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = ConfigTemplateEngine.substitute(value, env_vars)
            elif isinstance(value, dict):
                result[key] = ConfigTemplateEngine.substitute_dict(value, env_vars)
            elif isinstance(value, list):
                result[key] = [
                    ConfigTemplateEngine.substitute(item, env_vars) if isinstance(item, str)
                    else ConfigTemplateEngine.substitute_dict(item, env_vars) if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        return result


class ConfigSchemaValidator:
    """Ω-C31: Lightweight JSON Schema-like validation."""

    def __init__(self, schema: dict[str, dict[str, Any]]) -> None:
        self._schema = schema

    def validate(self, data: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        for field_name, field_schema in self._schema.items():
            if field_schema.get("required", False) and field_name not in data:
                errors.append(f"Missing required field: {field_name}")
                continue
            if field_name in data:
                expected_type = field_schema.get("type")
                if expected_type and not isinstance(data[field_name], expected_type):
                    errors.append(f"Field '{field_name}' expected type {expected_type.__name__}, got {type(data[field_name]).__name__}")
                min_val = field_schema.get("min")
                max_val = field_schema.get("max")
                if min_val is not None and data[field_name] < min_val:
                    errors.append(f"Field '{field_name}' value {data[field_name]} below minimum {min_val}")
                if max_val is not None and data[field_name] > max_val:
                    errors.append(f"Field '{field_name}' value {data[field_name]} above maximum {max_val}")
        return errors


class ConfigInheritanceResolver:
    """Ω-C34: Config inheritance — base config + per-environment overrides."""

    def resolve(self, config: dict[str, Any], extends: str | None = None, base_configs: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
        if extends and base_configs and extends in base_configs:
            base = deepcopy(base_configs[extends])
            ConfigMergeStrategy._deep_merge(base, config)
            return base
        return config


class ConfigLoader:
    """
    Ω-C28 to Ω-C36: Full config loading pipeline.

    Multi-source support, template substitution, schema validation,
    inheritance, hot-reload hooks, lazy loading, versioning.
    """

    def __init__(self) -> None:
        self._schema_validator: ConfigSchemaValidator | None = None
        self._hot_reload_hooks: list[Callable[[SovereignConfig], None]] = []
        self._loaded_configs: dict[str, SovereignConfig] = {}
        self._base_configs: dict[str, dict[str, Any]] = {}
        self._version_counter = 0

    def set_schema(self, schema: dict[str, dict[str, Any]]) -> None:
        self._schema_validator = ConfigSchemaValidator(schema)

    def register_hot_reload_hook(self, hook: Callable[[SovereignConfig], None]) -> None:
        self._hot_reload_hooks.append(hook)

    def register_base_config(self, name: str, config: dict[str, Any]) -> None:
        self._base_configs[name] = config

    def load_json_file(self, file_path: str, name: str = "file", extends: str | None = None) -> LoadResult:
        import time
        start = time.monotonic()
        warnings: list[str] = []
        schema_errors: list[str] = []

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        data = ConfigTemplateEngine.substitute_dict(raw_data)

        resolver = ConfigInheritanceResolver()
        data = resolver.resolve(data, extends, self._base_configs)

        if self._schema_validator:
            schema_errors = self._schema_validator.validate(data)

        self._version_counter += 1
        data["_load_source"] = file_path
        data["_version"] = self._version_counter

        config = SovereignConfig.create(name=name, version=str(self._version_counter), values=data)
        self._loaded_configs[name] = config

        for hook in self._hot_reload_hooks:
            hook(config)

        elapsed = (time.monotonic() - start) * 1000
        return LoadResult(
            config=config,
            source=file_path,
            load_time_ms=round(elapsed, 2),
            warnings=tuple(warnings),
            schema_errors=tuple(schema_errors),
        )

    def load_dict(self, data: dict[str, Any], name: str = "inline", env_vars: dict[str, str] | None = None) -> LoadResult:
        import time
        start = time.monotonic()

        data = ConfigTemplateEngine.substitute_dict(data, env_vars)

        schema_errors: list[str] = []
        if self._schema_validator:
            schema_errors = self._schema_validator.validate(data)

        self._version_counter += 1
        data["_load_source"] = "inline"
        data["_version"] = self._version_counter

        config = SovereignConfig.create(name=name, version=str(self._version_counter), values=data)
        self._loaded_configs[name] = config

        for hook in self._hot_reload_hooks:
            hook(config)

        elapsed = (time.monotonic() - start) * 1000
        return LoadResult(
            config=config,
            source="inline",
            load_time_ms=round(elapsed, 2),
            schema_errors=tuple(schema_errors),
        )

    def load_multi_source(self, sources: list[tuple[str, dict[str, Any]]], name: str = "multi", env_vars: dict[str, str] | None = None) -> LoadResult:
        import time
        start = time.monotonic()

        merged_data = ConfigMergeStrategy.merge(sources)
        merged_data = ConfigTemplateEngine.substitute_dict(merged_data, env_vars)

        schema_errors: list[str] = []
        if self._schema_validator:
            schema_errors = self._schema_validator.validate(merged_data)

        self._version_counter += 1
        merged_data["_load_source"] = "multi_source_merge"
        merged_data["_version"] = self._version_counter

        config = SovereignConfig.create(name=name, version=str(self._version_counter), values=merged_data)
        self._loaded_configs[name] = config

        for hook in self._hot_reload_hooks:
            hook(config)

        elapsed = (time.monotonic() - start) * 1000
        return LoadResult(
            config=config,
            source="multi_source",
            load_time_ms=round(elapsed, 2),
            schema_errors=tuple(schema_errors),
        )

    def get_loaded(self, name: str) -> SovereignConfig | None:
        return self._loaded_configs.get(name)

    def get_all_loaded(self) -> dict[str, SovereignConfig]:
        return dict(self._loaded_configs)

    def clear_cache(self) -> None:
        self._loaded_configs.clear()
