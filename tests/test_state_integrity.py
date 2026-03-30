import unittest
import time
import numpy as np
from core.consciousness.state_observer import StateObserver

# [Ω-TEST-INTEGRITY] Full System Mirror Validation
# Testing Ontological Alignment, Homeostasis and Algorithmic Drift.

class TestStateObserver(unittest.TestCase):

    def setUp(self):
        self.observer = StateObserver(latency_threshold_ms=1.5)

    def test_ontological_integrity(self):
        """[Ω-C1-V004] Verifies NaN and Inf detection."""
        print("\n[STEP 1] Testing Ontological Invariants...")
        
        valid_payload = {"price": 65000.0, "timestamp": time.time()}
        self.assertTrue(self.observer.verify_interface_integrity("TestMod", valid_payload))
        
        invalid_payload = {"price": float('nan'), "timestamp": time.time()}
        self.assertFalse(self.observer.verify_interface_integrity("TestMod", invalid_payload))
        print("✅ NaN rejection verified.")

    def test_latency_homeostasis(self):
        """[Ω-C2-V055] Verifies heart pulse and P99 monitoring."""
        print("\n[STEP 2] Testing Systemic Homeostasis (Latency)...")
        
        # Fast cycles
        for _ in range(10):
            start = time.time()
            # Simulation 0.5ms
            self.observer.heart_pulse(start)
            
        report = self.observer.get_health_report()
        print(f"💓 Health: {report['status']} | Latency: {report['p99_latency']:.4f}ms")
        self.assertEqual(report["status"], "OPTIMAL")
        
        # Slow cycle trigger
        start = time.time() - 0.005 # Simulated 5ms latency
        self.observer.heart_pulse(start)
        
        report = self.observer.get_health_report()
        print(f"💓 Health after lag: {report['status']} | Latency: {report['p99_latency']:.4f}ms")
        self.assertEqual(report["status"], "DEGRADED")

    def test_drift_and_safe_mode(self):
        """[Ω-C3-V109] Verifies Brier Score and Safe Mode activation."""
        print("\n[STEP 3] Testing Algorithmic Drift & Safe Mode...")
        
        # Perfect predictions
        for _ in range(5):
            self.observer.register_outcome(confidence=0.9, win=True)
            
        report = self.observer.get_health_report()
        print(f"📊 Brier Score: {report['brier_score']:.4f}")
        self.assertLess(report["brier_score"], 0.1)
        
        # Total model collapse (High confidence, wrong outcomes)
        for _ in range(10):
            self.observer.register_outcome(confidence=0.99, win=False)
            
        report = self.observer.get_health_report()
        print(f"📉 Brier Score after drift: {report['brier_score']:.4f}")
        print(f"🔒 Safe Mode Active: {report['safe_mode']}")
        
        self.assertGreater(report["brier_score"], 0.5)
        self.assertTrue(report["safe_mode"])

if __name__ == "__main__":
    unittest.main()
