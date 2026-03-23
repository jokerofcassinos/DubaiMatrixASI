
import sys
import os
import time

# Add root to path
sys.path.append(os.getcwd())

from execution.trade_registry import registry

def test_strike_sync():
    print("Testing Strike ID Synchronization...")
    
    # 1. Register an intent with a strike_id
    unique_id = int(time.time())
    strike_id = f"test_strike_{unique_id}"
    intent_data = {
        "symbol": "BTCUSD",
        "action": "BUY",
        "lot_size": 0.1,
        "entry_price": 60000.0,
        "regime": "TRENDING_BULL"
    }
    
    # Mimic SniperExecutor registration (it uses a dummy ticket 0 for pending socket orders)
    registry.register_intent(
        ticket=0, 
        intent=intent_data,
        snapshot=None,
        strike_id=strike_id
    )
    
    print(f"Registered intent with Strike ID: {strike_id}")
    
    # 2. Simulate MT5 Bridge receiving a RESULT message with the same strike_id
    ticket_from_mt5 = 99887700 + unique_id
    print(f"Simulating RESULT from MQL5 with Ticket: {ticket_from_mt5}")
    
    # We call the new registry update method
    registry.update_ticket_by_strike(strike_id, ticket_from_mt5)
    
    # 3. Verify the ticket was updated in the registry
    # The registry should now have the intent under the new ticket
    updated_intent = registry.get_intent(position_id=ticket_from_mt5, ticket=ticket_from_mt5)
    
    if updated_intent:
        print(f"✅ SUCCESS: Intent found for Ticket {ticket_from_mt5}")
        if updated_intent.get("strike_id") == strike_id:
            print(f"✅ SUCCESS: Strike ID matched: {updated_intent.get('strike_id')}")
        else:
            print(f"❌ FAILURE: Strike ID mismatch. Expected {strike_id}, got {updated_intent.get('strike_id')}")
            sys.exit(1)
    else:
        print(f"❌ FAILURE: Intent NOT found for Ticket {ticket_from_mt5}. Mapping failed.")
        sys.exit(1)

    print("✨ VERIFICATION COMPLETE: Strike-based synchronization is operational.")

if __name__ == "__main__":
    test_strike_sync()
