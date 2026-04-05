"""
SOLÉNN v2 — Anti-Duplication & Knowledge Graph Query Integration (Ω-C145 a Ω-C153)
Functionality uniqueness check, semantic similarity search, parameter redundancy
detection, config dependency analysis, orphan/conflict detection, consolidation
suggestions, and impact analysis.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class KGFunctionalityNode:
    """Represents a functionality registered in the Knowledge Graph."""
    name: str
    description: str
    config_fields: tuple[str, ...]
    module: str
    checksum: str


@dataclass(frozen=True, slots=True)
class RedundancyReport:
    found: bool
    similar_configs: list[str]
    similarity_score: float
    recommendation: str


@dataclass(frozen=True, slots=True)
class ConflictReport:
    config_a: str
    config_b: str
    conflicting_fields: list[str]
    details: str


class KnowledgeGraphFunctionalityIndex:
    """Ω-C145 a Ω-C153: Lightweight in-memory KG for config functionality."""

    def __init__(self) -> None:
        self._nodes: dict[str, KGFunctionalityNode] = {}
        self._field_usage: dict[str, list[str]] = defaultdict(list)
        self._config_deps: dict[str, set[str]] = defaultdict(set)

    def register(self, node: KGFunctionalityNode) -> None:
        self._nodes[node.name] = node
        for f in node.config_fields:
            self._field_usage[f].append(node.name)

    def check_uniqueness(self, description: str, config_fields: list[str]) -> tuple[bool, list[str]]:
        """Ω-C145: Check if functionality is truly unique."""
        suggestions: list[str] = []
        desc_words = set(description.lower().split())
        for node_name, node in self._nodes.items():
            node_words = set(node.description.lower().split())
            common = desc_words & node_words
            if len(common) >= 3:
                suggestions.append(node_name)
        return len(suggestions) == 0, suggestions

    def check_parameter_redundancy(self, params_a: dict[str, Any], params_b: dict[str, Any], name_a: str, name_b: str) -> RedundancyReport:
        """Ω-C147: Detect redundant parameters between two configs."""
        common_keys = set(params_a.keys()) & set(params_b.keys())
        if not common_keys:
            return RedundancyReport(False, [], 0.0, "No overlap")
        diffs = sum(1 for k in common_keys if params_a[k] != params_b[k])
        similarity = 1.0 - (diffs / len(common_keys)) if common_keys else 0.0
        if similarity > 0.8:
            return RedundancyReport(True, [name_a, name_b], similarity, f"High redundancy ({similarity:.2f}) — consider merging")
        return RedundancyReport(False, [], similarity, "No redundancy")

    def check_conflicts(self, configs: dict[str, dict[str, Any]]) -> list[ConflictReport]:
        """Ω-C150: Detect conflicting config values."""
        conflicts: list[ConflictReport] = []
        config_names = list(configs.keys())
        for i in range(len(config_names)):
            for j in range(i + 1, len(config_names)):
                a, b = config_names[i], config_names[j]
                common = set(configs[a].keys()) & set(configs[b].keys())
                conflicting = [k for k in common if configs[a][k] != configs[b][k]]
                if conflicting:
                    conflicts.append(ConflictReport(config_a=a, config_b=b, conflicting_fields=conflicting, details=f"{a} and {b} disagree on {conflicting}"))
        return conflicts

    def find_orphans(self, all_configs: set[str], accessed_configs: set[str]) -> set[str]:
        """Ω-C149: Detect configs that no module reads or uses."""
        return all_configs - accessed_configs

    def get_dependency_graph(self) -> dict[str, list[str]]:
        return {k: list(v) for k, v in self._config_deps.items()}

    def get_consolidation_suggestions(self) -> list[dict[str, Any]]:
        """Ω-C151: Suggest groups of configs to consolidate."""
        field_groups: dict[str, list[str]] = defaultdict(list)
        for field, configs in self._field_usage.items():
            if len(configs) > 1:
                group_key = frozenset(configs)
                for gk in [group_key]:
                    field_groups[hk_hash(gk)].append(field)
        suggestions = []
        for key, fields in field_groups.items():
            configs = list(self._field_usage[fields[0]])
            suggestions.append({"configs": configs, "shared_fields": fields, "recommendation": "Consider grouping into single config"})
        return suggestions

    def impact_analysis(self, config_name: str, field_name: str) -> list[str]:
        """Ω-C152: What modules depend on this config field."""
        return list(self._field_usage.get(field_name, []))


def _hash(x: frozenset) -> str:
    data = json.dumps(sorted(x), sort_keys=True, default=str)
    return hashlib.md5(data.encode()).hexdigest()[:8]
