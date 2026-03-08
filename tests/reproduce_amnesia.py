
import sys
import os
from datetime import datetime, timezone
import time

# Adicionar o diretório raiz ao path
sys.path.append(os.getcwd())

from market.data_engine import MarketSnapshot
from core.consciousness.regime_detector import MarketRegime
from core.decision.trinity_core import Action, Decision
from core.evolution.performance_tracker import PerformanceTracker, TradeRecord
from execution.sniper_executor import SniperExecutor
from execution.trade_registry import registry as trade_registry

def test_amnesia_fix():
    print("🧪 Testing Financial Amnesia Fix...")
    
    # 1. Setup - Mock objects
    snapshot = MarketSnapshot()
    snapshot.symbol = "BTCUSD"
    snapshot.regime = MarketRegime.TRENDING_BULL # O regime ORIGINAL
    snapshot.timestamp = datetime.now(timezone.utc)
    
    decision = Decision(
        action=Action.BUY,
        confidence=0.85,
        signal_strength=0.75,
        entry_price=68000.0,
        stop_loss=67000.0,
        take_profit=70000.0,
        lot_size=0.1,
        regime="TRENDING_BULL",
        reasoning="Test breakout"
    )
    
    # 2. Simulate Execution (Registers Intent)
    print("🚀 Simulating Trade Execution...")
    ticket = 12345
    # Simular o que o SniperExecutor faz agora
    trade_registry.register_intent(ticket=ticket, intent=decision, snapshot=snapshot)
    
    # 3. Simulate "Financial Amnesia" Scenario
    future_snapshot = MarketSnapshot()
    future_snapshot.symbol = "BTCUSD"
    future_snapshot.regime = MarketRegime.HIGH_VOL_CHAOS # O regime ATUAL (no futuro)
    future_snapshot.timestamp = datetime.now(timezone.utc)
    
    # 4. Simulate Reflection Phase
    print("🧠 Simulating Reflection Phase...")
    # Mock de um 'deal' vindo do MT5
    deal = {
        'ticket': ticket,
        'position_id': 555,
        'symbol': 'BTCUSD',
        'type': 'SELL', # Fechamento de um BUY
        'price': 69500.0,
        'volume': 0.1,
        'profit': 150.0,
        'time': time.time(),
        'entry': 1 # OUT
    }
    
    # O que o ASIBrain faz agora:
    intent = trade_registry.get_intent(position_id=555, ticket=ticket)
    
    if intent:
        regime_label = intent.get("regime", "UNKNOWN")
        coherence = intent.get("coherence", 0.0)
        print(f"✅ SUCCESS: Original regime '{regime_label}' recovered from TradeRegistry!")
    else:
        regime_label = future_snapshot.regime.value
        print(f"❌ FAILURE: Intent not found, fallback to current regime '{regime_label}' (Amnesia!)")
    
    # Validar
    assert regime_label == "TRENDING_BULL", f"Expected TRENDING_BULL, got {regime_label}"
    print("✨ VERIFICATION COMPLETE: TradeRegistry effectively prevents Financial Amnesia.")

if __name__ == "__main__":
    test_amnesia_fix()
