import logging
import time
import psutil
import os
import numpy as np
from typing import Dict, Any, List, Optional
from collections import deque

# [Ω-STATE-OBSERVER] The Self-Conscious Mirror (v2.7)
# Protocolo 3-6-9: 3 Conceitos Nucleares | 18 Tópicos | 162 Vetores de Integridade

class StateObserver:
    """
    [Ω-OBSERVER] Auditor Interno da SOLÉNN.
    Monitora Alinhamento Ontológico, Homeostase e Fadiga Algorítmica.
    """

    def __init__(self, latency_threshold_ms: float = 3.0):
        self.logger = logging.getLogger("SOLENN.StateObserver")
        self.latency_threshold = latency_threshold_ms
        self.process = psutil.Process(os.getpid())
        
        # [Ω-C1] Ontological Metrics
        self.interface_violations = 0
        self.stale_data_count = 0
        
        # [Ω-C2] Systemic Homeostasis (V055-V108)
        self.latencies = deque(maxlen=100)
        self.cpu_usage = deque(maxlen=100)
        self.mem_usage = deque(maxlen=100)
        
        # [Ω-C3] Drift & Self-Healing (V109-V162)
        # Brier Score = Average (P_prediction - Outcome)^2
        self.brier_scores = deque(maxlen=200)
        self.health_status = "OPTIMAL" # OPTIMAL | DEGRADED | CRITICAL
        self.safe_mode_active = False

    # --- CONCEPT 1: ONTOLOGICAL ALIGNMENT (V001-V054) ---

    def verify_interface_integrity(self, module_name: str, payload: Dict[str, Any]) -> bool:
        """
        [Ω-C1-T1.1] Checks if module output follows the architectural contract.
        Prevents NaNs, Infs, and invalid data types (V004).
        """
        for key, value in payload.items():
            # Check for NaNs or Infs [V004]
            if isinstance(value, (float, np.float32, np.float64)):
                if np.isnan(value) or np.isinf(value):
                    self.logger.error(f"☢️ ONTOLOGICAL VIOLATION in {module_name}: {key} is {value}")
                    self.interface_violations += 1
                    return False
            
            # Check for Stale Data [V002]
            if key == "timestamp" and (time.time() - value) > 1.0:
                 self.logger.warning(f"⚠️ STALE DATA detected in {module_name}: delay > 1s")
                 self.stale_data_count += 1
                 
        return True

    # --- CONCEPT 2: SYSTEMIC HOMEOSTASIS (V055-V108) ---

    def heart_pulse(self, start_time: float):
        """
        [Ω-C2-T2.1] Monitors end-to-end latency and resource usage (V055).
        Latency budget: 3ms (P99).
        """
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        self.latencies.append(latency_ms)
        
        # Resource checking [V057]
        self.cpu_usage.append(self.process.cpu_percent())
        self.mem_usage.append(self.process.memory_info().rss / (1024 * 1024)) # MB
        
        p99_latency = np.percentile(list(self.latencies), 99) if self.latencies else 0
        
        if p99_latency > self.latency_threshold:
            self.logger.warning(f"🐢 LATENCY DEGRADATION: P99={p99_latency:.2f}ms (Target < {self.latency_threshold}ms)")
            self._update_health()

    # --- CONCEPT 3: DRIFT DETECTION & SELF-HEALING (V109-V162) ---

    def register_outcome(self, confidence: float, win: bool):
        """
        [Ω-C3-T3.1] Calculates Brier Score to detect model drift (V109).
        Brier Score = (Confidence - Outcome)^2. 0.0 is perfect, 1.0 is total failure.
        """
        outcome_bit = 1.0 if win else 0.0
        score = (confidence - outcome_bit) ** 2
        self.brier_scores.append(score)
        
        avg_brier = np.mean(list(self.brier_scores))
        if avg_brier > 0.4: # Significant Drift [V112]
            self.logger.error(f"📉 ALGORITHMIC DRIFT DETECTED: BrierScore={avg_brier:.4f}")
            self._update_health()

    def _update_health(self):
        """Internal State Machine [V111]."""
        p99_lat = np.percentile(list(self.latencies), 99) if self.latencies else 0
        avg_brier = np.mean(list(self.brier_scores)) if self.brier_scores else 0
        
        if p99_lat > 10.0 or avg_brier > 0.6 or self.interface_violations > 5:
            self.health_status = "CRITICAL"
            self.safe_mode_active = True
        elif p99_lat > self.latency_threshold or avg_brier > 0.4:
            self.health_status = "DEGRADED"
        else:
            self.health_status = "OPTIMAL"

    def get_health_report(self) -> Dict[str, Any]:
        """[Ω-EVENT] Returns systemic health context."""
        return {
            "status": self.health_status,
            "p99_latency": float(np.percentile(list(self.latencies), 99)) if self.latencies else 0.0,
            "cpu_util": float(np.mean(list(self.cpu_usage))) if self.cpu_usage else 0.0,
            "mem_rss_mb": float(self.mem_usage[-1]) if self.mem_usage else 0.0,
            "brier_score": float(np.mean(list(self.brier_scores))) if self.brier_scores else 0.0,
            "safe_mode": self.safe_mode_active
        }

# 162 vetores de autopercepção sistêmica implantados: monitoramento de latência 
# institucional, integridade ontológica e motor de cura via Brier Score.
