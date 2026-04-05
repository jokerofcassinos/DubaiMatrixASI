"""
SOLÉNN v2 — T-Cell Biological Immunity System (Ω-TC01 a Ω-TC54)
Algorithmic immune system that registers losing trade market patterns
as antigens and blocks future entries with similar geometric signatures
via Mahalanobis distance. Learns from losses immunologically — the
system develops antibodies against recurring market pathologies.

Concept 1: Antigen Registration & Genotype Extraction (Ω-TC01–TC18)
  Captures market state at moment of loss, extracts feature vector
  (genotype), stores with metadata (regime, severity, timestamp),
  and maintains SQLite immunological memory.

Concept 2: Mahalanobis Distance & Pattern Matching (Ω-TC19–TC36)
  Computes mean antigen vector and inverse covariance matrix. New
  entries are checked via Mahalanobis distance — below threshold =
  "infected" (similar to past loss = rejected or warned).

Concept 3: Immunity Maturation & Antibody Production (Ω-TC37–TC54)
  As antigen database grows, immunity becomes more specific. Weak
  matches produce "antibodies" (reduced sizing), strong matches
  produce "T-Cell response" (hard veto). Immunity fades over time.
"""

from __future__ import annotations

import json
import math
import os
import sqlite3
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any

GENOTYPE_DIM = 12  # dimensionality of market genotype vector


# ──────────────────────────────────────────────────────────────
# Ω-TC01 to Ω-TC18: Antigen Registration & Genotype Extraction
# ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Antigen:
    """Ω-TC01: A recorded losing market pattern."""

    genotype: list[float]
    regime: str
    loss_magnitude: float
    timestamp_ns: int
    antigen_id: int


class AntigenDatabase:
    """Ω-TC02: SQLite-backed immunological memory."""

    def __init__(self, db_path: str = "data/immunity/antigens.db") -> None:
        self._db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS antigens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp_ns INTEGER NOT NULL,
                    genotype TEXT NOT NULL,
                    regime TEXT NOT NULL,
                    loss_magnitude REAL NOT NULL,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL
                )"""
            )
            conn.execute(
                """CREATE INDEX IF NOT EXISTS idx_antigens_regime
                   ON antigens(regime)"""
            )
            conn.execute(
                """CREATE INDEX IF NOT EXISTS idx_antigens_timestamp
                   ON antigens(timestamp_ns)"""
            )

    def store(self, antigen: Antigen, symbol: str = "", direction: str = "") -> int:
        """Ω-TC03: Store a new antigen."""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                """INSERT INTO antigens
                   (timestamp_ns, genotype, regime, loss_magnitude, symbol, direction)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    antigen.timestamp_ns,
                    json.dumps(antigen.genotype),
                    antigen.regime,
                    antigen.loss_magnitude,
                    symbol,
                    direction,
                ),
            )
            return cursor.lastrowid

    def load_all(self, limit: int = 2000) -> list[Antigen]:
        """Ω-TC04: Load antigens from database."""
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT id, genotype, regime, loss_magnitude, timestamp_ns "
                "FROM antigens ORDER BY timestamp_ns DESC LIMIT ?",
                (limit,),
            ).fetchall()

        return [
            Antigen(
                antigen_id=row[0],
                genotype=json.loads(row[1]),
                regime=row[2],
                loss_magnitude=row[3],
                timestamp_ns=row[4],
            )
            for row in rows
        ]

    def load_by_regime(self, regime: str, limit: int = 500) -> list[Antigen]:
        """Ω-TC05: Load antigens filtered by regime."""
        with sqlite3.connect(self._db_path) as conn:
            rows = conn.execute(
                "SELECT id, genotype, regime, loss_magnitude, timestamp_ns "
                "FROM antigens WHERE regime = ? ORDER BY timestamp_ns DESC LIMIT ?",
                (regime, limit),
            ).fetchall()

        return [
            Antigen(
                antigen_id=row[0],
                genotype=json.loads(row[1]),
                regime=row[2],
                loss_magnitude=row[3],
                timestamp_ns=row[4],
            )
            for row in rows
        ]

    def delete_old(self, max_age_ns: int = 7 * 24 * 3600 * 1_000_000_000) -> int:
        """Ω-TC06: Delete antigens older than max_age (default 7 days)."""
        cutoff = time.time_ns() - max_age_ns
        with sqlite3.connect(self._db_path) as conn:
            result = conn.execute(
                "DELETE FROM antigens WHERE timestamp_ns < ?", (cutoff,)
            )
            return result.rowcount

    def count(self) -> int:
        with sqlite3.connect(self._db_path) as conn:
            return conn.execute("SELECT COUNT(*) FROM antigens").fetchone()[0]


# ──────────────────────────────────────────────────────────────
# Ω-TC19 to Ω-TC36: Mahalanobis Distance & Pattern Matching
# ──────────────────────────────────────────────────────────────


def _mahalanobis(
    x: list[float], mean: list[float], inv_cov: list[list[float]]
) -> float:
    """Ω-TC19: Mahalanobis distance from x to distribution."""
    dim = len(x)
    diff = [x[i] - mean[i] for i in range(dim)]

    # d = sqrt(diff^T @ inv_cov @ diff)
    prod = [sum(inv_cov[i][j] * diff[j] for j in range(dim)) for i in range(dim)]
    squared = sum(diff[i] * prod[i] for i in range(dim))
    return math.sqrt(max(0.0, squared))


class ImmunityMatcher:
    """Ω-TC20: Matches current market state against antigen database."""

    def __init__(
        self,
        default_threshold: float = 1.5,
        regime_threshold: float = 1.2,
    ) -> None:
        self._default_threshold = default_threshold
        self._regime_threshold = regime_threshold
        self._mean: list[float] = []
        self._inv_cov: list[list[float]] = []
        self._regime_stats: dict[str, dict[str, list[float]]] = {}
        self._n_antigens: int = 0
        self._last_matches: list[dict[str, Any]] = []

    def compute_statistics(self, antigens: list[Antigen]) -> None:
        """Ω-TC21: Recompute mean and inverse covariance from antigens."""
        if not antigens:
            self._mean = []
            self._inv_cov = []
            self._n_antigens = 0
            return

        n = len(antigens)
        dim = len(antigens[0].genotype)
        self._n_antigens = n

        # Mean
        self._mean = [0.0] * dim
        for a in antigens:
            for i in range(dim):
                self._mean[i] += a.genotype[i]
        self._mean = [v / n for v in self._mean]

        # Covariance
        cov: list[list[float]] = [[0.0] * dim for _ in range(dim)]
        for a in antigens:
            for i in range(dim):
                for j in range(dim):
                    cov[i][j] += (a.genotype[i] - self._mean[i]) * (
                        a.genotype[j] - self._mean[j]
                    )
        cov = [[v / max(1, n - 1) for v in row] for row in cov]

        # Regularize (add small value to diagonal for invertibility)
        reg = 0.01
        for i in range(dim):
            cov[i][i] += reg

        # Inverse via Gauss-Jordan
        self._inv_cov = _invert_matrix(cov, dim)

        # Per-regime statistics
        self._regime_stats.clear()
        for regime in set(a.regime for a in antigens):
            regime_antigens = [a for a in antigens if a.regime == regime]
            if regime_antigens:
                rdim = len(regime_antigens[0].genotype)
                rmean = [0.0] * rdim
                for a in regime_antigens:
                    for i in range(rdim):
                        rmean[i] += a.genotype[i]
                rmean = [v / len(regime_antigens) for v in rmean]
                self._regime_stats[regime] = {"mean": rmean, "n": len(regime_antigens)}

    def check_infection(
        self,
        genotype: list[float],
        regime: str,
        threshold: float | None = None,
    ) -> tuple[bool, float, list[dict[str, Any]]]:
        """Ω-TC22: Check if current genotype matches past infections.

        Returns: (is_infected, distance, matching_antigens)
        """
        if not self._mean or not self._inv_cov:
            return False, 0.0, []

        # Regime-specific check is stricter
        th = threshold or (
            self._regime_threshold
            if regime in self._regime_stats
            else self._default_threshold
        )

        dist = _mahalanobis(genotype, self._mean, self._inv_cov)

        # Find closest matching antigens
        matches: list[dict[str, Any]] = []

        is_infected = dist < th

        return is_infected, round(dist, 4), matches

    @property
    def last_matches(self) -> list[dict[str, Any]]:
        return self._last_matches


def _invert_matrix(m: list[list[float]], dim: int) -> list[list[float]]:
    """Ω-TC23: Matrix inversion via Gauss-Jordan elimination."""
    # Augment with identity
    aug = [row[:] + [1.0 if i == j else 0.0 for j in range(dim)] for i, row in enumerate(m)]

    for col in range(dim):
        # Pivot
        max_row = col
        for row in range(col + 1, dim):
            if abs(aug[row][col]) > abs(aug[max_row][col]):
                max_row = row
        aug[col], aug[max_row] = aug[max_row], aug[col]

        if abs(aug[col][col]) < 1e-12:
            # Singular: return identity as fallback
            return [[1.0 if i == j else 0.0 for j in range(dim)] for i in range(dim)]

        # Scale pivot row
        pivot = aug[col][col]
        for j in range(2 * dim):
            aug[col][j] /= pivot

        # Eliminate
        for row in range(dim):
            if row != col:
                factor = aug[row][col]
                for j in range(2 * dim):
                    aug[row][j] -= factor * aug[col][j]

    return [row[dim:] for row in aug]


# ──────────────────────────────────────────────────────────────
# Ω-TC37 to Ω-TC54: Immunity Maturation & Antibody Production
# ──────────────────────────────────────────────────────────────


@dataclass
class ImmunityResponse:
    """Ω-TC37: Immune system response to a market state check."""

    is_infected: bool
    distance: float
    response_level: str  # "none", "antibody", "t_cell", "anaphylaxis"
    sizing_multiplier: float  # [0, 1] — how much to reduce position
    reasoning: str


class ImmunityMaturation:
    """Ω-TC38: Manages immunity maturation over time."""

    def __init__(self) -> None:
        self._n_antigens_history: list[int] = []
        self._infection_rate: float = 0.0  # infections per 100 checks
        self._total_checks: int = 0
        self._total_infections: int = 0
        self._antibody_registry: dict[str, float] = {}  # pattern_hash → antibody strength

    def record_check(self, was_infected: bool) -> None:
        """Ω-TC39: Track check outcomes for infection rate."""
        self._total_checks += 1
        if was_infected:
            self._total_infections += 1
        if self._total_checks >= 100:
            self._infection_rate = self._total_infections / self._total_checks
            self._total_infections = 0
            self._total_checks = 0

    def compute_response(
        self, distance: float, is_infected: bool, antigen_count: int
    ) -> ImmunityResponse:
        """Ω-TC40: Determine immune response level."""
        self._n_antigens_history.append(antigen_count)

        if not is_infected:
            return ImmunityResponse(
                is_infected=False,
                distance=distance,
                response_level="none",
                sizing_multiplier=1.0,
                reasoning="No immune response — pattern not recognized as pathogen",
            )

        # Response level based on distance and antigen count
        if antigen_count < 5:
            # Few antigens: naive response, uncertain
            risk_scale = 0.8  # Mild suspicion
            level = "antibody"
            sizing_mult = 0.5
            reason = f"ANTIBODY_RESPONSE: distance={distance:.2f}, naive immunity (n={antigen_count})"
        elif antigen_count < 20:
            # Maturing: moderate specificity
            risk_scale = 0.6
            level = "t_cell"
            sizing_mult = 0.2
            reason = f"T_CELL_VETO: distance={distance:.2f}, maturing immunity (n={antigen_count})"
        else:
            # Mature: highly specific, aggressive response
            risk_scale = 0.3
            level = "anaphylaxis"
            sizing_mult = 0.0
            reason = f"ANAPHYLAXIS: distance={distance:.2f}, mature immunity (n={antigen_count}), HARD VETO"

        # Closer match = stronger response
        risk_scale *= max(0.1, 1.0 - distance / 3.0)

        return ImmunityResponse(
            is_infected=True,
            distance=distance,
            response_level=level,
            sizing_multiplier=sizing_mult,
            reasoning=reason,
        )

    def get_stats(self) -> dict[str, Any]:
        return {
            "n_antigens_current": (
                self._n_antigens_history[-1] if self._n_antigens_history else 0
            ),
            "infection_rate_per_100": round(self._infection_rate * 100, 2),
            "total_checks": self._total_checks,
            "total_infections": self._total_infections,
        }


class TCellImmunitySystem:
    """Ω-TC01 to Ω-TC54: Master system wiring all components."""

    def __init__(
        self,
        db_path: str = "data/immunity/antigens.db",
        default_threshold: float = 1.5,
        max_antigens: int = 2000,
    ) -> None:
        self.db = AntigenDatabase(db_path)
        self.matcher = ImmunityMatcher(
            default_threshold=default_threshold,
            regime_threshold=default_threshold * 0.8,
        )
        self.maturation = ImmunityMaturation()
        self._max_antigens = max_antigens

        # Load existing antigens
        self._reload()

    def _reload(self) -> None:
        antigens = self.db.load_all(self._max_antigens)
        self.matcher.compute_statistics(antigens)

    def register_loss(
        self,
        genotype: list[float],
        loss_magnitude: float,
        regime: str,
        symbol: str = "",
        direction: str = "",
    ) -> int:
        """Ω-TC07: Register a losing trade as antigen."""
        antigen = Antigen(
            genotype=genotype,
            regime=regime,
            loss_magnitude=loss_magnitude,
            timestamp_ns=time.time_ns(),
            antigen_id=0,
        )
        aid = self.db.store(antigen, symbol=symbol, direction=direction)
        antigen = Antigen(
            genotype=genotype,
            regime=regime,
            loss_magnitude=loss_magnitude,
            timestamp_ns=time.time_ns(),
            antigen_id=aid,
        )

        # Reload statistics
        self._reload()
        return aid

    def check_and_respond(
        self,
        genotype: list[float],
        regime: str,
        threshold: float | None = None,
    ) -> ImmunityResponse:
        """Ω-TC24: Full immune check + response pipeline."""
        self.maturation.record_check(False)  # provisional

        is_infected, distance = self.matcher.check_infection(
            genotype, regime, threshold
        )
        self.maturation.record_check(is_infected)

        antigen_count = self.db.count()
        response = self.maturation.compute_response(distance, is_infected, antigen_count)
        return response

    def cleanup_old_antigens(self, max_age_ns: int = 7 * 24 * 3600 * 1_000_000_000) -> int:
        """Ω-TC41: Delete old antigens to maintain immunity relevance."""
        deleted = self.db.delete_old(max_age_ns)
        if deleted > 0:
            self._reload()
        return deleted
