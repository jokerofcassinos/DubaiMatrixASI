"""
SOLÉNN v2 — Parameter Validation & Constraints (Ω-C127 a Ω-C135)
Constraint solver, range enforcement, ratio/sum/mutual exclusion,
conditional activation, violation recovery, satisfiability check.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True, slots=True)
class ConstraintViolation:
    constraint_type: str
    details: str
    violating_params: list[str]
    suggested_fix: str = ""


class ConstraintSolver:
    """Ω-C127 a Ω-C135: Constraint satisfaction system for parameters."""

    def __init__(self, params: dict[str, float | int]) -> None:
        self._params = dict(params)
        self._violations: list[ConstraintViolation] = []

    def check_range(self, param: str, min_val: float | int, max_val: float | int, inclusive: bool = True) -> bool:
        value = self._params.get(param)
        if value is None:
            return True
        if inclusive and min_val <= value <= max_val:
            return True
        if not inclusive and min_val < value < max_val:
            return True
        self._violations.append(ConstraintViolation(
            "range", f"{param}={value} outside [{min_val}, {max_val}]", [param], f"Set {param} to value in [{min_val}, {max_val}]",
        ))
        return False

    def check_ratio(self, param_a: str, param_b: str, min_ratio: float, max_ratio: float) -> bool:
        a, b = self._params.get(param_a), self._params.get(param_b)
        if a is None or b is None or b == 0:
            return True
        ratio = a / b
        if min_ratio <= ratio <= max_ratio:
            return True
        self._violations.append(ConstraintViolation("ratio", f"{param_a}/{param_b}={ratio} outside [{min_ratio}, {max_ratio}]", [param_a, param_b]))
        return False

    def check_sum(self, params: list[str], target: float, tolerance: float = 0.001) -> bool:
        values = [self._params.get(p, 0) for p in params]
        total = sum(v for v in values if isinstance(v, (int, float)))
        if abs(total - target) <= tolerance:
            return True
        self._violations.append(ConstraintViolation("sum", f"Sum of {params}={total} != {target}", params))
        return False

    def check_mutual_exclusion(self, param_a: str, param_b: str) -> bool:
        a_active = self._params.get(param_a, 0) != 0
        b_active = self._params.get(param_b, 0) != 0
        if not (a_active and b_active):
            return True
        self._violations.append(ConstraintViolation("mutual_exclusion", f"{param_a} and {param_b} cannot both be active", [param_a, param_b]))
        return False

    def check_conditional(self, condition_param: str, threshold: float, target_param: str) -> bool:
        condition_value = self._params.get(condition_param, 0)
        target_value = self._params.get(target_param, 0)
        if condition_value <= threshold and target_value != 0:
            self._violations.append(ConstraintViolation("conditional", f"{target_param} must be 0 when {condition_param} <= {threshold}", [condition_param, target_param]))
            return False
        return True

    def check_all(self, constraints: list[Callable[[ConstraintSolver], bool]]) -> list[ConstraintViolation]:
        self._violations.clear()
        for constraint_fn in constraints:
            constraint_fn(self)

    def get_violations(self) -> list[ConstraintViolation]:
        return list(self._violations)

    def has_violations(self) -> bool:
        return len(self._violations) > 0

    def auto_correct(self) -> dict[str, float | int]:
        corrected = dict(self._params)
        for violation in self._violations:
            if violation.constraint_type == "sum":
                current_sum = sum(corrected.get(p, 0) for p in violation.violating_params)
                if current_sum != 0:
                    target = 1.0
                    factor = 1.0 / current_sum
                    for p in violation.violating_params:
                        corrected[p] = corrected.get(p, 0) * factor
            elif violation.constraint_type == "range":
                param = violation.violating_params[0]
                import re
                match = re.search(r"\[(.*?),\s*(.*?)\]", violation.details)
                if match:
                    corrected[param] = (float(match.group(1)) + float(match.group(2))) / 2.0
            elif violation.constraint_type == "mutual_exclusion":
                if len(violation.violating_params) >= 2:
                    corrected[violation.violating_params[1]] = 0
        return corrected

    def reset(self) -> None:
        self._violations.clear()
