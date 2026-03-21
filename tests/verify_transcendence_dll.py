import os
import sys
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from cpp.asi_bridge import CPP_CORE
import numpy as np

def test_transcendence():
    print("Testing DLL Load...")
    if not CPP_CORE._loaded:
        print("FAILED: DLL not loaded.")
        return

    print("Testing Casimir Force...")
    cancels = np.random.rand(100)
    force = CPP_CORE.calculate_casimir_force(cancels, 0.5)
    print(f"Casimir Force: {force}")

    print("Testing NLSE Rogue Wave...")
    amps = np.random.rand(50)
    phs = np.random.rand(50)
    prob = CPP_CORE.solve_nlse_rogue_wave(amps, phs, 1.5)
    print(f"Rogue Wave Prob: {prob}")

    print("Testing PHD Math (Laser Compression)...")
    energy = np.random.rand(100)
    comp = CPP_CORE.calculate_laser_compression(energy)
    print(f"Laser Compression: {comp}")

    print("ALL TESTS PASSED!")

if __name__ == "__main__":
    test_transcendence()
