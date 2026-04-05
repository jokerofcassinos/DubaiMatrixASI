"""
SOLÉNN v2 — Configuration Validation & Guardrails (Ω-C19 a Ω-C27)
Validator registry with dispatch by field type, cross-field dependency
validation, semantic checks, and invariant enforcement.
"""

from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional
from pathlib import Path


class ValidationSeverity(Enum):
    FATAL = "fatal"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True, slots=True)
class ValidationError:
    field: str
    message: str
    severity: ValidationSeverity
    code: str = ""

    @property
    def is_fatal(self) -> bool:
        return self.severity is ValidationSeverity.FATAL


class Validator(ABC):
    """Base validator interface."""

    @abstractmethod
    def validate(self, field_name: str, value: Any, context: dict[str, Any] | None = None) -> list[ValidationError]:
        ...

    @abstractmethod
    def can_handle(self, field_name: str, value: Any) -> bool:
        ...


class NumericRangeValidator(Validator):
    """Ω-C19: Numeric range validation with min/max/inclusive-exclusive bounds."""

    def __init__(
        self,
        min_val: float | None = None,
        max_val: float | None = None,
        min_inclusive: bool = True,
        max_inclusive: bool = True,
    ) -> None:
        self._min_val = min_val
        self._max_val = max_val
        self._min_inclusive = min_inclusive
        self._max_inclusive = max_inclusive

    def can_handle(self, field_name: str, value: Any) -> bool:
        return isinstance(value, (int, float))

    def validate(self, field_name: str, value: Any, context: dict[str, Any] | None = None) -> list[ValidationError]:
        errors: list[ValidationError] = []
        if self._min_val is not None:
            if self._min_inclusive and value < self._min_val:
                errors.append(ValidationError(
                    field=field_name,
                    message=f"Value {value} is below minimum {self._min_val}",
                    severity=ValidationSeverity.FATAL,
                    code="NUM_BELOW_MIN",
                ))
            elif not self._min_inclusive and value <= self._min_val:
                errors.append(ValidationError(
                    field=field_name,
                    message=f"Value {value} must be strictly greater than {self._min_val}",
                    severity=ValidationSeverity.FATAL,
                    code="NUM_NOT_ABOVE_MIN",
                ))
        if self._max_val is not None:
            if self._max_inclusive and value > self._max_val:
                errors.append(ValidationError(
                    field=field_name,
                    message=f"Value {value} exceeds maximum {self._max_val}",
                    severity=ValidationSeverity.FATAL,
                    code="NUM_ABOVE_MAX",
                ))
            elif not self._max_inclusive and value >= self._max_val:
                errors.append(ValidationError(
                    field=field_name,
                    message=f"Value {value} must be strictly less than {self._max_val}",
                    severity=ValidationSeverity.FATAL,
                    code="NUM_NOT_BELOW_MAX",
                ))
        return errors


class EnumChoiceValidator(Validator):
    """Ω-C21: Enum/choice validation for discrete allowed values."""

    def __init__(self, allowed_values: set[Any]) -> None:
        self._allowed = allowed_values

    def can_handle(self, field_name: str, value: Any) -> bool:
        return True

    def validate(self, field_name: str, value: Any, context: dict[str, Any] | None = None) -> list[ValidationError]:
        if value not in self._allowed:
            return [ValidationError(
                field=field_name,
                message=f"Value '{value}' not in allowed values: {self._allowed}",
                severity=ValidationSeverity.FATAL,
                code="INVALID_CHOICE",
            )]
        return []


class CrossFieldDependencyValidator(Validator):
    """Ω-C22: Cross-field dependency validation (if A=X, then B must be Y)."""

    def __init__(
        self,
        dependencies: dict[str, Callable[[Any, dict[str, Any]], list[ValidationError]]],
    ) -> None:
        self._dependencies = dependencies

    def can_handle(self, field_name: str, value: Any) -> bool:
        return field_name in self._dependencies

    def validate(self, field_name: str, value: Any, context: dict[str, Any] | None = None) -> list[ValidationError]:
        if context is None:
            return []
        if field_name in self._dependencies:
            return self._dependencies[field_name](value, context)
        return []


class SemanticValidator(Validator):
    """Ω-C23: Semantic validation — API key format, valid URL, existing path."""

    URL_PATTERN = re.compile(r"^https?://[^\s/$.?#].[^\s]*$")
    API_KEY_PATTERN = re.compile(r"^[A-Za-z0-9_-]{16,128}$")

    def __init__(self, semantic_type: str) -> None:
        self._semantic_type = semantic_type

    def can_handle(self, field_name: str, value: Any) -> bool:
        return isinstance(value, str)

    def validate(self, field_name: str, value: Any, context: dict[str, Any] | None = None) -> list[ValidationError]:
        errors: list[ValidationError] = []
        if self._semantic_type == "url":
            if not self.URL_PATTERN.match(value):
                errors.append(ValidationError(
                    field=field_name, message="Invalid URL format", severity=ValidationSeverity.FATAL, code="INVALID_URL",
                ))
        elif self._semantic_type == "api_key":
            if not self.API_KEY_PATTERN.match(value):
                errors.append(ValidationError(
                    field=field_name, message="Invalid API key format", severity=ValidationSeverity.FATAL, code="INVALID_API_KEY",
                ))
        elif self._semantic_type == "path":
            if not Path(value).exists():
                errors.append(ValidationError(
                    field=field_name, message=f"Path does not exist: {value}", severity=ValidationSeverity.WARNING, code="PATH_NOT_FOUND",
                ))
        return errors


class InvariantEnforcer(Validator):
    """Ω-C24: Config invariant enforcement — properties that must ALWAYS hold."""

    def __init__(self, invariant_fn: Callable[[dict[str, Any]], tuple[bool, str]]) -> None:
        self._invariant_fn = invariant_fn

    def can_handle(self, field_name: str, value: Any) -> bool:
        return True

    def validate(self, field_name: str, value: Any, context: dict[str, Any] | None = None) -> list[ValidationError]:
        if context is None:
            return []
        holds, description = self._invariant_fn(context)
        if not holds:
            return [ValidationError(
                field=field_name,
                message=f"Invariant violated: {description}",
                severity=ValidationSeverity.FATAL,
                code="INVARIANT_VIOLATION",
            )]
        return []


class ValidatorRegistry:
    """Ω-C19: Validator registry with dispatch by field type."""

    def __init__(self) -> None:
        self._validators: dict[str, list[Validator]] = {}

    def register(self, field_name: str, validator: Validator) -> None:
        self._validators.setdefault(field_name, []).append(validator)
        self._validators[field_name].sort(key=lambda v: v.__class__.__name__)

    def validate(self, field_name: str, value: Any, context: dict[str, Any] | None = None) -> list[ValidationError]:
        validators = self._validators.get(field_name, [])
        all_errors: list[ValidationError] = []
        for validator in validators:
            if validator.can_handle(field_name, value):
                all_errors.extend(validator.validate(field_name, value, context))
        return all_errors

    def validate_all(self, data: dict[str, Any]) -> list[ValidationError]:
        all_errors: list[ValidationError] = []
        for field_name, value in data.items():
            all_errors.extend(self.validate(field_name, value, data))
        return all_errors

    def has_errors(self, data: dict[str, Any]) -> bool:
        return any(e.is_fatal for e in self.validate_all(data))

    def clear(self) -> None:
        self._validators.clear()
