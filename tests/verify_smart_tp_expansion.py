import sys
import os
import time
import numpy as np
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from execution.position_manager import PositionManager
from market.data_engine import MarketSnapshot
from config.omega_params import OMEGA

def test_smart_tp_relaxation():
    print("Testing Smart TP Relaxation Logic...")
    
    # Mock Bridge
    bridge = MagicMock()
    bridge.get_open_positions.return_value = [
        {
            'ticket': 12345,
            'type': 'BUY',
            'symbol': 'BTCUSD',
            'time': int(time.time()) - 100,
            'open_price': 60000.0,
            'price_open': 60000.0,
            'price_current': 61000.0,
            'profit': 1000.0,
            'volume': 1.0,
            'sl': 59000.0,
            'tp': 65000.0
        }
    ]
    
    mgr = PositionManager(bridge)
    
    # Mock Snapshot
    snapshot = MagicMock()
    snapshot.price = 61000.0
    snapshot.atr = 500.0
    snapshot.regime.value = "TRENDING_BULL"
    snapshot.metadata = {
        "phi_last": 0.8, # High PHI should relax thresholds
        "dynamic_commission_per_lot": 50.0
    }
    snapshot.symbol = "BTCUSD"
    
    # Mock Flow Analysis
    flow_analysis = {
        "delta": 0.5,
        "signal": 0.8,
        "exhaustion": {"detected": False},
        "absorption": {"detected": False},
        "volume_zscore": 1.0
    }
    
    # 1. First iteration to set peak
    mgr.monitor_positions(snapshot, flow_analysis)
    
    # Verify peak was set
    state = mgr._positions_state[12345]
    print(f"Initial Peak Profit: ${state['peak_profit']}")
    
    # 2. Simulate a pullback that would normally trigger exit
    # Peak was 1000. Let's drop to 800.
    # Normal lock_threshold might be 0.15-0.25 (150-250 drawdown).
    # With PHI=0.8 and relax_mult=0.5, phi_relax = 1 + 0.4 = 1.4.
    # lock_threshold = 0.15 * 1.4 = 0.21 (210 drawdown).
    # Pullback of 200 ($1000->$800) should NOT trigger exit now, but would have before.
    
    bridge.get_open_positions.return_value[0]['profit'] = 800.0
    snapshot.price = 60800.0
    
    # We need to mock bridge.close_position to see if it's called
    bridge.close_position = MagicMock(return_value={"success": True, "ticket": 12345})
    
    mgr.monitor_positions(snapshot, flow_analysis)
    
    if 12345 in mgr._closing_tickets:
        print("FAIL: Position closed prematurely even with high PHI!")
    else:
        print("SUCCESS: Position stayed open despite minor pullback due to PHI relaxation.")
        
    # 3. Increase pullback to exceed relaxed threshold
    # Pullback to 700 ($300 drop). 300 / 1000 = 30%. 30% > 21%. Should close.
    bridge.get_open_positions.return_value[0]['profit'] = 600.0
    snapshot.price = 60600.0
    
    mgr.monitor_positions(snapshot, flow_analysis)
    
    if 12345 in mgr._closing_tickets:
        print("SUCCESS: Position closed when pullback exceeded relaxed threshold.")
    else:
        # Check reasons in logs or state if possible
        print("FAIL: Position did NOT close when it should have.")

if __name__ == "__main__":
    test_smart_tp_relaxation()
