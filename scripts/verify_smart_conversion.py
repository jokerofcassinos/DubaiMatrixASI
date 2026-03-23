import sys
import os
import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

# Adicionar o diretório raiz ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from execution.sniper_executor import SniperExecutor
from core.decision.trinity_core import Decision, Action
from market.data_engine import MarketSnapshot

def test_smart_conversion():
    print("🔬 DUBAI MATRIX ASI — SMART LIMIT CONVERSION VERIFICATION")
    print("==========================================================")

    # 1. Setup Mocks
    bridge = MagicMock()
    risk = MagicMock()
    executor = SniperExecutor(bridge, risk)
    
    # Configurações de símbolo simuladas
    point = 0.01
    stops_level = 10
    bridge.get_symbol_info.return_value = {
        "point": point,
        "stops_level": stops_level,
        "digits": 2
    }
    bridge.get_open_positions.return_value = []
    bridge.get_account_info.return_value = {"margin_level": 500.0, "margin_free": 100000.0}
    bridge.get_dynamic_commission_per_lot.return_value = 15.0
    bridge.calculate_margin.return_value = 100.0
    
    # Mock Risk Engine para sempre aprovar 1.0 lote
    risk.calculate_lot_size.return_value = 1.0
    risk.validate_trade.return_value = (True, 1.0, "Approved")

    def run_case(name, action, limit_price, bid, ask, expected_type):
        print(f"\n--- CASE: {name} ---")
        bridge.get_tick.return_value = {"bid": bid, "ask": ask, "time": time.time()}
        
        decision = Decision(
            action=action,
            confidence=0.9,
            signal_strength=0.5,
            entry_price=limit_price,
            stop_loss=limit_price - 100 if action == Action.BUY else limit_price + 100,
            take_profit=limit_price + 100 if action == Action.BUY else limit_price - 100,
            lot_size=1.0,
            regime="UNKNOWN",
            reasoning="Test Reasoning",
            limit_order=True
        )
        decision.metadata = {"phi": 0.5}
        
        snapshot = MarketSnapshot()
        snapshot.tick = {"bid": bid, "ask": ask, "mid": (bid+ask)/2}
        snapshot.account = {"balance": 100000.0, "margin_level": 500.0, "margin_free": 100000.0}
        snapshot.symbol_info = bridge.get_symbol_info()
        
        asi_state = MagicMock()
        asi_state.peak_balance = 100000.0
        
        # Reset bridge calls
        bridge.send_limit_order.reset_mock()
        bridge.send_market_order.reset_mock()
        
        # Simular resposta de sucesso para o bridge
        success_res = {"success": True, "ticket": 12345, "price": limit_price, "volume": 1.0}
        bridge.send_limit_order.return_value = success_res
        bridge.send_market_order.return_value = success_res

        executor.execute(decision, asi_state, snapshot)
        
        if expected_type == "LIMIT":
            if bridge.send_limit_order.called:
                print(f"✅ SUCCESS: Correctly sent LIMIT order @ {limit_price}")
            else:
                print(f"❌ FAILURE: Expected LIMIT but sent MARKET or nothing.")
        else:
            if bridge.send_market_order.called:
                print(f"✅ SUCCESS: Correctly converted to MARKET order.")
            else:
                print(f"❌ FAILURE: Expected MARKET conversion but sent LIMIT or nothing.")

    # safety_buffer = (10 + 20) * 0.01 = 0.30
    
    # SELL LIMIT cases
    # Valid: Limit (68005.0) > Bid (68000.0) + 0.30
    run_case("Valid SELL LIMIT", Action.SELL, 68005.0, 68000.0, 68001.0, "LIMIT")
    
    # Invalid (Too close): Limit (68000.20) < Bid (68000.0) + 0.30
    run_case("Too Close SELL LIMIT (Below Bid+Buffer)", Action.SELL, 68000.20, 68000.0, 68001.0, "MARKET")

    # BUY LIMIT cases
    # Valid: Limit (67995.0) < Ask (68001.0) - 0.30
    run_case("Valid BUY LIMIT", Action.BUY, 67995.0, 68000.0, 68001.0, "LIMIT")
    
    # Invalid (Too close): Limit (68000.90) > Ask (68001.0) - 0.30
    run_case("Too Close BUY LIMIT (Above Ask-Buffer)", Action.BUY, 68000.90, 68000.0, 68001.0, "MARKET")

if __name__ == "__main__":
    test_smart_conversion()
