
import sys
import os

# Add root to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

def test_config_load():
    print("[TEST] Testing Environment Configuration Load...")
    
    from config.exchange_config import MT5_LOGIN, MT5_SERVER, MT5_PASSWORD, MT5_PATH
    
    print(f"MT5_LOGIN: {MT5_LOGIN} ({type(MT5_LOGIN)})")
    print(f"MT5_SERVER: {MT5_SERVER}")
    print(f"MT5_PATH: {MT5_PATH}")
    
    # Check if values match .env (masking password)
    pass_masked = "*" * len(MT5_PASSWORD) if MT5_PASSWORD else "EMPTY"
    print(f"MT5_PASSWORD: {pass_masked}")

    if MT5_LOGIN != 0 and MT5_SERVER != "" and MT5_PATH != "":
        print("[OK] SUCCESS: Configuration loaded correctly from .env!")
    else:
        print("[FAIL] FAILURE: Configuration values are missing or default.")
        sys.exit(1)

if __name__ == "__main__":
    test_config_load()
