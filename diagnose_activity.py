
import sys
import os
import json

# Add project root to path
sys.path.append(os.getcwd())

from config.omega_params import OMEGA
from types import SimpleNamespace

def test_kinetic_floor():
    print("--- ASI KINETIC FLOOR DIAGNOSTIC ---")
    
    # Check current parameter
    floor = OMEGA.get("kinetic_velocity_floor")
    print(f"Current kinetic_velocity_floor: {floor}")
    
    if floor > 10.0:
        print("FAIL: Floor is still critically high!")
    elif floor == 2.0:
        print("SUCCESS: Floor is at default 2.0.")
    else:
        print(f"INFO: Floor is {floor}")

    # Simulate Veto Logic from TrinityCore
    # Mocking snapshot.metadata
    snapshot = SimpleNamespace(
        metadata = {
            "tick_velocity": 5.4, # Above 2.0, below 21.94
            "v_pulse_detected": False
        },
        candles = {
            "M1": {"close": [100, 101, 102, 103, 104]}
        }
    )
    
    # Veto logic simulation
    tick_vel = abs(snapshot.metadata.get("tick_velocity", 0.0))
    is_braided = snapshot.metadata.get("is_braided", False)
    
    print(f"Simulating Tick Velocity: {tick_vel}")
    print(f"Is Braided Override: {is_braided}")
    
    if tick_vel < floor and not is_braided:
        print(f"VETO TRIGGERED: KINETIC_EXHAUSTION (Velocity {tick_vel} < {floor})")
    else:
        print("VETO PASSED: No Kinetic Exhaustion.")

if __name__ == "__main__":
    test_kinetic_floor()
