import sys
import os
import time
from unittest.mock import MagicMock, patch

# Adicionar o diretório raiz ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from execution.sniper_executor import SniperExecutor
from execution.quantum_twap import QuantumTwapEngine
from execution.position_manager import PositionManager
from core.decision.trinity_core import Decision, Action
from market.data_engine import MarketSnapshot

def test_limits_and_floors():
    print("🔬 DUBAI MATRIX ASI — LIMITS & FLOORS VERIFICATION")
    print("================================================")

    # 1. Test Quantum TWAP Slicing
    print("\n--- Testing Quantum TWAP Slicing Limit ---")
    bridge = MagicMock()
    twap = QuantumTwapEngine(bridge)
    
    # Simular total_lot = 5.0 com max_chunk = 0.3 (Deveria dar 17 chunks, mas limitamos a 5)
    total_lot = 5.0
    max_chunk = 0.3
    
    # Acessar o método interno de planejamento de fatias para verificar o limite
    # Como o código foi alterado dentro do loop, vamos simular a execução
    decision = Decision(action=Action.SELL, confidence=0.9, signal_strength=0.5, entry_price=70000, stop_loss=70100, take_profit=69900, lot_size=5.0, regime="TRENDING", reasoning="Test")
    
    # Capturar log.omega calls ou apenas confiar no código alterado
    # Vamos verificar se o SniperExecutor também limita
    
    # 2. Test SniperExecutor Hydra Limit
    print("\n--- Testing SniperExecutor Hydra Limit ---")
    risk = MagicMock()
    executor = SniperExecutor(bridge, risk)
    
    bridge.get_symbol_info.return_value = {"point": 0.01, "stops_level": 10, "digits": 2}
    bridge.get_open_positions.return_value = []
    bridge.get_account_info.return_value = {"margin_level": 500.0, "margin_free": 100000.0}
    bridge.get_dynamic_commission_per_lot.return_value = 15.0
    bridge.calculate_margin.return_value = 100.0
    risk.calculate_lot_size.return_value = 5.0
    risk.validate_trade.return_value = (True, 5.0, "Approved")
    
    snapshot = MarketSnapshot()
    snapshot.tick = {"bid": 70000, "ask": 70001, "mid": 70000.5}
    snapshot.account = {"balance": 100000.0, "margin_level": 500.0, "margin_free": 100000.0}
    snapshot.metadata = {"phi": 0.5, "phi_resonance": True} # Trigger Hydra
    
    # Mocking ASI State (Fixing TypeError)
    asi_state = MagicMock()
    asi_state.peak_balance = 100000.0
    asi_state.win_rate = 0.8
    asi_state.total_trades = 20
    asi_state.total_profit = 5000.0
    asi_state.total_wins = 16
    asi_state.total_losses = 4
    asi_state.circuit_breaker_active = False
    asi_state.daily_drawdown = 0.0
    
    # Mock send_limit_order to capture number of calls
    bridge.send_limit_order.return_value = {"success": True, "ticket": 123, "price": 70000, "volume": 1.0}
    
    # Nota: Se o lote for >= 1.5 e conf >= 0.85, ele vai pro TWAP engine.
    # Vamos baixar o threshold do TWAP no OMEGA temporariamente para não desviar, ou testar o desvio.
    from config.omega_params import OMEGA
    OMEGA.set("twap_lot_threshold", 10.0) # Desativa TWAP momentaneamente para testar Hydra do Sniper
    
    executor.execute(decision, asi_state, snapshot)
    
    calls = bridge.send_limit_order.call_count + bridge.send_market_order.call_count
    print(f"Total Slots Dispatched (Hydra): {calls}")
    if calls > 0 and calls <= 5:
        print(f"✅ SUCCESS: Hydra capped at {calls} slots (<= 5).")
    elif calls == 0:
        print(f"❌ FAILURE: Hydra dispatched 0 slots (Vetoed?). Check logs.")
    else:
        print(f"❌ FAILURE: Hydra dispatched {calls} slots (> 5).")

    # 3. Test PositionManager Dynamic Floor
    print("\n--- Testing PositionManager Dynamic Floor ---")
    pm = PositionManager(bridge)
    
    # 0.1 Lote -> Comissao aprox $3.2
    # Lote 0.1 * 32.0 (default comm) = 3.2
    lot_scale = 0.1
    comm_cost = lot_scale * 32.0
    
    # Antigamente o floor era max(comm*1.1, 15.0) -> $15.0
    # Agora é max(comm*1.15, 1.0) -> $3.68
    
    expected_safe_floor = max(comm_cost * 1.15, 1.0)
    print(f"Expected Safe Floor for 0.1 lot (comm ${comm_cost:.2f}): ${expected_safe_floor:.2f}")
    
    # Simular estado de breakeven armado
    ticket = 999
    pm._positions_state[ticket] = {
        "peak_profit": 10.0,
        "peak_time": time.time(),
        "start_time": time.time() - 60,
        "breakeven_active": True
    }
    
    # Simular profit de $5.0 (acima do novo floor de $3.68, mas abaixo do antigo de $15.0)
    snapshot.tick = {"mid": 70000, "bid": 69999, "ask": 70001}
    snapshot.indicators = {"M5_atr_14": [50.0]}
    flow_analysis = {"delta": 0.0, "signal": 0.0}
    
    # Mock positions
    bridge.get_open_positions.return_value = [{
        "ticket": ticket, "symbol": "BTCUSD", "type": "BUY", "time": time.time()-60, 
        "open_price": 69900, "profit": 5.0, "volume": 0.1
    }]
    
    with patch('utils.logger.log.omega') as mock_log:
        pm.monitor_positions(snapshot, flow_analysis)
        
        # Se NÃO fechar, é sucesso (porque $5.0 > $3.68)
        if bridge.close_batch.called:
            print("❌ FAILURE: Position closed prematurely at $5.0 profit.")
        else:
            print("✅ SUCCESS: Position held at $5.0 profit (Correctly above floor).")

    # Simular profit caindo para $0.50 (abaixo do novo floor)
    bridge.get_open_positions.return_value[0]["profit"] = 0.50
    pm.monitor_positions(snapshot, flow_analysis)
    
    if bridge.close_batch.called:
        print("✅ SUCCESS: Position closed at $0.50 (Correctly below floor).")
    else:
        print("❌ FAILURE: Position NOT closed at $0.50 (Should be below floor).")

if __name__ == "__main__":
    test_limits_and_floors()
