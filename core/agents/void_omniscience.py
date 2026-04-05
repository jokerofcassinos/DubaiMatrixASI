"""
SOLÉNN v2 — Void Omniscience & Meta-Awareness Agents (Ω-W01 to Ω-W162)
Transmuted from v1:
  - omniscience_void.py: Multi-scale awareness field
  - neural_sentience_agent.py: Consciousness continuum monitoring
  - state_observer.py: State vector observation and anomaly detection
  - state_vector.py: State integrity tracking

Protocol 3-6-9: 162 vetores planejados
  Concept 1 — Omniscience Void Field (Ω-W01 to Ω-W54): Multi-scale
    awareness spanning all market data channels simultaneously,
    information density mapping, void regions (lack of information
    as signal), omniscience scoring (coverage completeness),
    entropy gradient tracking
  Concept 2 — Neural Sentience Monitoring (Ω-W55 to Ω-W108):
    Consciousness continuum classification (alert/drowsy/confused/
    unconscious), meta-cognitive quality assessment, Brier score
    calibration, prediction accuracy feedback loop
  Concept 3 — State Vector Observation (Ω-W109 to Ω-W162): Complete
    system state capture, state integrity verification, anomaly
    detection in state transitions, state drift quantification,
    recovery protocol on state corruption
"""

from __future__ import annotations

import math
import time
from collections import deque
from typing import Optional


# ──────────────────────────────────────────────────────────────
# Ω-W01 to Ω-W18: Omniscience Void Field
# ──────────────────────────────────────────────────────────────

class OmniscienceField:
    """
    Ω-W01 to Ω-W09: Multi-scale awareness field tracking.

    Transmuted from v1 omniscience_void.py:
    v1: Simple multi-indicator aggregation
    v2: Full omniscience field with channel coverage, information
    density mapping, void region detection, and completeness scoring.
    """

    def __init__(self, n_channels: int = 12) -> None:
        self._n_channels = n_channels
        self._channel_activity: dict[str, float] = {}
        self._channel_timestamps: dict[str, float] = {}
        self._coverage_history: deque[float] = deque(maxlen=200)
        self._density_history: deque[float] = deque(maxlen=200)

    def update_channel(self, channel: str, data_quality: float) -> dict:
        """Ω-W03: Update a data channel's activity."""
        self._channel_activity[channel] = data_quality
        self._channel_timestamps[channel] = time.time()

        n_active = len(self._channel_activity)
        now = time.time()

        # Ω-W04: Channel coverage
        # How many channels are currently active?
        active_recent = 0
        for ch, ts in self._channel_timestamps.items():
            if now - ts < 60.0:  # active in last 60 seconds
                active_recent += 1

        coverage = active_recent / max(1, max(n_active, self._n_channels))

        # Ω-W05: Information density
        avg_quality = (
            sum(v for v in self._channel_activity.values()) /
            max(1, len(self._channel_activity))
        )
        info_density = coverage * avg_quality

        # Ω-W06: Void regions
        # Channels with no recent data or low quality
        void_channels = []
        for ch, ts in self._channel_timestamps.items():
            is_stale = (now - ts > 30.0)
            is_low_quality = self._channel_activity.get(ch, 0) < 0.2
            if is_stale or is_low_quality:
                void_channels.append(ch)

        void_ratio = len(void_channels) / max(1, self._n_channels)

        # Ω-W07: Entropy gradient
        self._coverage_history.append(coverage)
        self._density_history.append(info_density)

        if len(self._coverage_history) >= 5:
            cov = list(self._coverage_history)[-5:]
            entropy_gradient = cov[-1] - cov[0]
        else:
            entropy_gradient = 0.0

        # Ω-W08: Omniscience score
        # Composite of coverage, density, inverse void, stability
        stability = 1.0 - min(1.0, abs(entropy_gradient) * 5)
        void_penalty = void_ratio * 0.5

        omniscience = (
            coverage * 0.3 +  # Am I seeing everything?
            info_density * 0.3 +  # Is the data good quality?
            (1.0 - void_ratio) * 0.2 +  # Are there blind spots?
            stability * 0.2  # Is coverage stable?
        )
        omniscience = max(0.0, min(1.0, omniscience - void_penalty))

        # Ω-W09: Awareness level classification
        if omniscience > 0.85 and void_ratio < 0.1:
            awareness = "OMNISCIENT"
        elif omniscience > 0.7:
            awareness = "HIGH_AWARENESS"
        elif omniscience > 0.5:
            awareness = "PARTIAL_AWARENESS"
        elif omniscience > 0.3:
            awareness = "LIMITED"
        else:
            awareness = "BLIND"

        return {
            "omniscience_score": omniscience,
            "coverage": coverage,
            "information_density": info_density,
            "void_channels": void_channels,
            "void_ratio": void_ratio,
            "entropy_gradient": entropy_gradient,
            "awareness_level": awareness,
            "is_actionable": omniscience > 0.6 and void_ratio < 0.4,
            "n_channels_active": active_recent,
        }


# ──────────────────────────────────────────────────────────────
# Ω-W19 to Ω-W27: Neural Sentience Monitor
# ──────────────────────────────────────────────────────────────

class SentienceMonitor:
    """
    Ω-W19 to Ω-W27: System consciousness monitoring.

    Transmuted from v1 neural_sentience_agent.py:
    v1: Basic accuracy tracking
    v2: Full consciousness continuum with Brier score calibration,
    meta-cognitive assessment, and self-correction triggering.
    """

    def __init__(self, window_size: int = 100) -> None:
        self._window = window_size
        self._predictions: deque[tuple[float, bool]] = deque(maxlen=window_size)
        self._confidence_history: deque[float] = deque(maxlen=window_size)
        self._surprise_history: deque[float] = deque(maxlen=window_size)
        self._brier_window: deque[float] = deque(maxlen=100)

    def record_prediction(
        self,
        predicted_prob: float,
        actual_outcome: bool,
        confidence: float,
    ) -> dict:
        """Ω-W21: Record a prediction and its outcome."""
        self._predictions.append((predicted_prob, actual_outcome))
        self._confidence_history.append(confidence)

        # Surprise = |actual - predicted|
        surprise = abs(int(actual_outcome) - predicted_prob)
        self._surprise_history.append(surprise)

        # Brier score for this prediction
        brier = (predicted_prob - int(actual_outcome)) ** 2
        self._brier_window.append(brier)

        if len(self._predictions) < 10:
            return {"state": "WARMING_UP"}

        # Ω-W22: Prediction accuracy
        n_correct = sum(
            1 for p, o in self._predictions
            if (p >= 0.5 and o) or (p < 0.5 and not o)
        )
        accuracy = n_correct / len(self._predictions)

        # Ω-W23: Brier score (calibration)
        avg_brier = sum(self._brier_window) / len(self._brier_window)
        brier_max = 1.0  # worst case
        calibration = 1.0 - avg_brier / brier_max

        # Ω-W24: Meta-cognitive quality
        # Correlation between confidence and accuracy
        if len(self._confidence_history) >= 20:
            confs = list(self._confidence_history)[-30:]
            preds_list = [p for p, _ in self._predictions]
            # Are confident predictions more accurate?
            high_conf = sum(1 for i, c in enumerate(confs)
                           if c > 0.7 and preds_list[i] == (preds_list[i] >= 0.5))
            low_conf = sum(1 for i, c in enumerate(confs)
                          if c <= 0.7 and preds_list[i] == (preds_list[i] >= 0.5))
            high_n = sum(1 for c in confs if c > 0.7)
            low_n = sum(1 for c in confs if c <= 0.7)

            meta_quality = (
                (high_conf / max(1, high_n)) -
                (low_conf / max(1, low_n))
            )
        else:
            meta_quality = 0.0

        # Ω-W25: Surprise rate
        avg_surprise = (
            sum(self._surprise_history) / len(self._surprise_history)
            if self._surprise_history else 0.0
        )

        # Ω-W26: Confidence trend
        if len(self._confidence_history) >= 10:
            confs = list(self._confidence_history)[-10:]
            conf_trend = confs[-1] - confs[0]
        else:
            conf_trend = 0.0

        # Ω-W27: Consciousness state
        if accuracy > 0.7 and calibration > 0.7 and avg_surprise < 0.3:
            state = "ALERT"
        elif accuracy < 0.4 or avg_surprise > 0.7:
            state = "CONFUSED"
        elif calibration > 0.5:
            state = "DROWSY"
        else:
            state = "TRANSITIONAL"

        return {
            "accuracy": accuracy,
            "brier_score": avg_brier,
            "calibration": calibration,
            "meta_cognitive_quality": meta_quality,
            "avg_surprise": avg_surprise,
            "confidence_trend": conf_trend,
            "consciousness_state": state,
            "n_predictions": len(self._predictions),
            "is_operational": state in ("ALERT", "DROWSY"),
            "needs_recalibration": calibration < 0.3 and len(self._predictions) > 30,
        }


# ──────────────────────────────────────────────────────────────
# Ω-W28 to Ω-W36: State Vector Observer
# ──────────────────────────────────────────────────────────────

class StateObserver:
    """
    Ω-W28 to Ω-W36: System state observation and integrity.

    Transmuted from v1 state_observer.py + state_vector.py:
    v1: Basic state snapshot
    v2: Full state integrity with anomaly detection, drift
    quantification, and recovery protocol.
    """

    def __init__(self, n_dimensions: int = 20) -> None:
        self._n_dim = n_dimensions
        self._states: deque[list[float]] = deque(maxlen=500)
        self._state_hash: int = 0
        self._anomaly_count: int = 0

    def observe(self, state_vector: list[float]) -> dict:
        """Ω-W30: Observe current system state."""
        if len(state_vector) < self._n_dim:
            state_vector = state_vector + [0.0] * (self._n_dim - len(state_vector))
        state_vector = state_vector[:self._n_dim]

        # Ω-W31: State integrity check
        # NaN/Inf detection
        has_invalid = any(math.isnan(v) or math.isinf(v) for v in state_vector)
        if has_invalid:
            self._anomaly_count += 1
            # Replace invalid values
            state_vector = [
                0.0 if (math.isnan(v) or math.isinf(v)) else v
                for v in state_vector
            ]

        self._states.append(state_vector)

        # Ω-W32: State drift quantification
        if len(self._states) >= 5:
            states_list = list(self._states)
            current = states_list[-1]
            baseline = states_list[max(0, len(states_list) - 50)]
            drift = _euclidean(current, baseline)
        else:
            drift = 0.0

        # Ω-W33: State anomaly via Mahalanobis-style distance
        if len(self._states) >= 10:
            states_list = list(self._states)
            n = len(states_list)
            dim = len(state_vector)
            means = [sum(s[d] for s in states_list) / n for d in range(dim)]
            stds = [
                max(1e-6, math.sqrt(
                    sum((s[d] - means[d]) ** 2 for s in states_list) / n
                ))
                for d in range(dim)
            ]

            # Normalized distance from mean
            mahal_approx = math.sqrt(
                sum(((state_vector[d] - means[d]) / stds[d]) ** 2
                    for d in range(dim)) / dim
            )

            is_state_anomaly = mahal_approx > 3.0
            if is_state_anomaly:
                self._anomaly_count += 1
        else:
            mahal_approx = 0.0
            is_state_anomaly = False

        # Ω-W34: State stability
        if len(self._states) >= 10:
            states_list = list(self._states)[-10:]
            avg_change = 0.0
            for i in range(1, len(states_list)):
                avg_change += _euclidean(states_list[i], states_list[i - 1])
            avg_change /= len(states_list) - 1
            stability = 1.0 / (1.0 + avg_change)
        else:
            stability = 1.0

        return {
            "state_valid": not has_invalid,
            "anomaly_count": self._anomaly_count,
            "state_drift": drift,
            "mahalanobis_distance": mahal_approx,
            "is_state_anomaly": is_state_anomaly,
            "stability": stability,
            "dimensionality": self._n_dim,
            "needs_recovery": has_invalid or self._anomaly_count > 5,
        }

    def get_full_state_snapshot(self) -> dict:
        """Ω-W35: Complete state snapshot for recovery."""
        if not self._states:
            return {"timestamp": time.time(), "state": []}

        return {
            "timestamp": time.time(),
            "state": list(self._states[-1]),
            "anomaly_count": self._anomaly_count,
            "n_observations": len(self._states),
        }


# ──────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────

def _euclidean(a: list[float], b: list[float]) -> float:
    """Euclidean distance between two vectors."""
    return math.sqrt(
        sum((x - y) ** 2 for x, y in zip(a, b))
    ) if len(a) == len(b) else float('inf')
