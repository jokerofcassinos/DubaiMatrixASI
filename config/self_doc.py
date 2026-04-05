"""
SOLÉNN v2 — Self-Documenting Parameter System (Ω-C154 a Ω-C162)
Auto-generated documentation, usage examples, provenance tracking, changelog,
relationship map, performance journal, recommendation engine, explainability,
self-test.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True, slots=True)
class ParameterProvenance:
    """Ω-C156: Tracking of parameter origin and modification history."""
    name: str
    created_by: str
    created_at: float
    reason: str = ""
    modification_history: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True, slots=True)
class PerformanceJournalEntry:
    """Ω-C159: Correlation between parameter value and outcome."""
    timestamp: float
    parameter: str
    value: Any
    outcome_metric: float
    outcome_description: str
    regime: str = "unknown"


class ParameterDocumentationGenerator:
    """Ω-C154 to Ω-C162: Self-documenting parameter system."""

    def __init__(self) -> None:
        self._docstrings: dict[str, str] = {}
        self._examples: dict[str, list[str]] = {}
        self._provenance: dict[str, ParameterProvenance] = {}
        self._changelog: dict[str, list[dict[str, Any]]] = {}
        self._relationships: dict[str, list[str]] = {}
        self._performance_journal: list[PerformanceJournalEntry] = []

    def set_docstring(self, param_name: str, docstring: str) -> None:
        self._docstrings[param_name] = docstring

    def add_example(self, param_name: str, example: str) -> None:
        self._examples.setdefault(param_name, []).append(example)

    def set_provenance(self, name: str, created_by: str, reason: str = "") -> None:
        self._provenance[name] = ParameterProvenance(
            name=name, created_by=created_by, created_at=time.time(), reason=reason,
        )

    def record_change(self, param_name: str, old_value: Any, new_value: Any, changed_by: str, reason: str = "") -> None:
        entry = {"timestamp": time.time(), "old_value": old_value, "new_value": new_value, "changed_by": changed_by, "reason": reason}
        self._changelog.setdefault(param_name, []).append(entry)
        if param_name in self._provenance:
            old = self._provenance[param_name]
            self._provenance[param_name] = ParameterProvenance(
                name=old.name, created_by=old.created_by, created_at=old.created_at, reason=old.reason,
                modification_history=old.modification_history + (entry,)
            )

    def record_performance(self, parameter: str, value: Any, outcome: float, description: str, regime: str = "unknown") -> None:
        self._performance_journal.append(PerformanceJournalEntry(
            timestamp=time.time(), parameter=parameter, value=value, outcome_metric=outcome,
            outcome_description=description, regime=regime
        ))

    def add_relationship(self, source: str, target: str, relation_type: str = "related") -> None:
        self._relationships.setdefault(source, []).append(f"{target}({relation_type})")

    def get_recommendations(self, param_name: str, target_direction: str = "maximize") -> list[str]:
        """Ω-C160: Recommend parameter values based on historical performance."""
        entries = [e for e in self._performance_journal if e.parameter == param_name]
        if not entries:
            return ["No historical data for recommendation"]
        if target_direction == "maximize":
            best = max(entries, key=lambda e: e.outcome_metric)
            return [f"Best value observed: {best.value} (outcome: {best.outcome_metric}, {best.outcome_description})"]
        else:
            worst = min(entries, key=lambda e: e.outcome_metric)
            return [f"Avoid value similar to: {worst.value} (outcome: {worst.outcome_metric}, {worst.outcome_description})"]

    def generate_markdown_doc(self) -> str:
        """Ω-C154: Auto-generate markdown documentation from metadata."""
        lines = ["# SOLÉNN v2 — Parameter Documentation\n"]
        all_params = set(self._docstrings.keys()) | set(self._examples.keys()) | set(self._provenance.keys())
        for param in sorted(all_params):
            lines.append(f"## `{param}`")
            if param in self._docstrings:
                lines.append(f"{self._docstrings[param]}\n")
            if param in self._provenance:
                prov = self._provenance[param]
                lines.append(f"- **Created by:** {prov.created_by}")
                lines.append(f"- **Created at:** {prov.created_at}")
                if prov.reason:
                    lines.append(f"- **Reason:** {prov.reason}")
                lines.append(f"- **Modifications:** {len(prov.modification_history)}")
                lines.append("")
            if param in self._examples:
                lines.append(f"**Examples:**\n")
                for ex in self._examples[param]:
                    lines.append(f"- {ex}")
                lines.append("")
            if param in self._changelog:
                changes = self._changelog[param]
                lines.append(f"**Changelog ({len(changes)} changes):**\n")
                for ch in changes[-5:]:
                    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ch["timestamp"]))
                    lines.append(f"- [{ts}] {ch['old_value']} → {ch['new_value']} (by {ch['changed_by']})")
                lines.append("")
        return "\n".join(lines)

    def explain_parameter(self, param_name: str) -> str:
        """Ω-C161: Explain why a parameter has its current value."""
        parts = []
        if param_name in self._docstrings:
            parts.append(f"Description: {self._docstrings[param_name]}")
        if param_name in self._provenance:
            prov = self._provenance[param_name]
            parts.append(f"Originally set by {prov.created_by} because: {prov.reason or 'N/A'}")
            if prov.modification_history:
                parts.append(f"Modified {len(prov.modification_history)} times since creation.")
        perf = [e for e in self._performance_journal if e.parameter == param_name]
        if perf:
            avg_outcome = sum(e.outcome_metric for e in perf) / len(perf)
            parts.append(f"Average outcome: {avg_outcome:.4f} across {len(perf)} observations.")
        return "\n".join(parts) if parts else "No information available."

    def run_self_test(self) -> list[str]:
        """Ω-C162: Verify integrity of the entire parameter documentation system."""
        issues: list[str] = []
        all_params = set(self._docstrings.keys()) | set(self._examples.keys()) | set(self._provenance.keys())
        for param in all_params:
            if param not in self._provenance:
                issues.append(f"Parameter '{param}' has no provenance information.")
        if not all_params and not self._docstrings:
            pass
        changelogs_without_provenance = set(self._changelog.keys()) - set(self._provenance.keys())
        for param in changelogs_without_provenance:
            issues.append(f"Parameter '{param}' has changelog entries but no provenance.")
        return issues

    def get_relationship_map(self) -> dict[str, list[str]]:
        """Ω-C158: Graph visualization data for parameter interdependencies."""
        return dict(self._relationships)

    def get_journal(self, param: str | None = None, limit: int = 50) -> list[PerformanceJournalEntry]:
        """Ω-C159: Retrieve performance journal entries."""
        if param:
            return [e for e in self._performance_journal if e.parameter == param][-limit:]
        return list(self._performance_journal)[-limit:]
