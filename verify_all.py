
import subprocess
import sys
import os
import time
from datetime import datetime

# Root of the project
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
TESTS_DIR = os.path.join(ROOT_DIR, "tests")

# Critical tests that must pass for the ASI to be considered "LETHAL"
CRITICAL_TESTS = [
    # Infrastructure & Security
    "verify_config.py",
    "verify_bridge_stability.py",
    "verify_transcendence_dll.py",
    
    # Decision Heart (Trinity Core)
    "verify_omega_stability.py",
    "verify_sl_robustness.py",
    "test_stability_filters.py",
    
    # Consciousness & Swarm
    "verify_swarm_coherence.py",
    "verify_phi_symmetry.py",
    "reproduce_phi_error.py",
    
    # PhD & Alpha Edge
    "verify_phd_alpha.py",
    "verify_omega_extreme.py",
    "verify_top_fading.py",
    "verify_smart_tp_optimization.py",
    
    # Execution & Sync
    "verify_strike_sync.py",
    "verify_nro.py"
]

def run_test(test_name):
    test_path = os.path.join(TESTS_DIR, test_name)
    if not os.path.exists(test_path):
        # Fallback to root if not in tests/
        test_path = os.path.join(ROOT_DIR, test_name)
    
    print(f"🧪 Running {test_name}...", end="", flush=True)
    start_time = time.time()
    
    try:
        # Run process and capture output
        process = subprocess.Popen(
            [sys.executable, test_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=ROOT_DIR
        )
        stdout, stderr = process.communicate(timeout=60)
        
        duration = time.time() - start_time
        
        if process.returncode == 0:
            print(f" ✅ PASS ({duration:.2f}s)")
            return True, stdout
        else:
            print(f" ❌ FAIL ({duration:.2f}s)")
            return False, stderr or stdout
            
    except subprocess.TimeoutExpired:
        print(f" ⚠️ TIMEOUT")
        return False, "Timeout expired after 60s"
    except Exception as e:
        print(f" 💥 ERROR: {e}")
        return False, str(e)

def main():
    print("="*60)
    print(f"🚀 DUBAI MATRIX ASI — UNIFIED CROSS-VERIFICATION SUITE")
    print(f"📅 Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    results = []
    failed_logs = []
    
    for test in CRITICAL_TESTS:
        passed, log_output = run_test(test)
        results.append(passed)
        if not passed:
            failed_logs.append((test, log_output))
            
    print("="*60)
    total = len(results)
    passed_count = sum(results)
    pass_rate = (passed_count / total) * 100
    
    print(f"📊 SUMMARY: {passed_count}/{total} Passed ({pass_rate:.1f}%)")
    
    if all(results):
        print("\n🏆 STATUS: LETHAL (Ready for Production Strike)")
        sys.exit(0)
    else:
        print("\n⚠️ STATUS: NOT LETHAL (Infrastructure/Logic Errors Found)")
        print("\n--- FAILURE LOGS ---")
        for test, log in failed_logs:
            print(f"\n❌ {test}:")
            print("-" * 20)
            # Print last 10 lines of error
            lines = log.strip().split('\n')
            for line in lines[-10:]:
                print(f"  {line}")
        sys.exit(1)

if __name__ == "__main__":
    main()
