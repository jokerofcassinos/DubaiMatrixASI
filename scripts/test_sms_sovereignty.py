import sys
import os
import time
import numpy as np
from datetime import datetime, timezone
from unittest.mock import MagicMock

# Adicionar o diretório raiz ao sys.path para importar os módulos do projeto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.decision.trinity_core import TrinityCore
from core.consciousness.regime_detector import MarketRegime, RegimeState
from core.consciousness.quantum_thought import QuantumState
from market.data_engine import MarketSnapshot
from config.omega_params import OMEGA

def test_tiered_sms():
    trinity = TrinityCore()
    
    # Mocking ASI State (Disable circuit breakers)
    asi_state = MagicMock()
    asi_state.circuit_breaker_active = False
    asi_state.consecutive_losses = 0
    asi_state.daily_drawdown = 0.0

    # Mocking Indicators (Avoid ATR blocks)
    indicators = {
        "M5_atr_14": [100.0],
        "M1_atr_14": [100.0],
        "M5_ema_9": [70000.0]
    }

def run_scenario(trinity, asi_state, indicators, name, curvature, velocity, coherence, phi, expected_unlocked=True):
    print(f"\n--- {name} ---")
    
    snapshot = MarketSnapshot()
    snapshot.timestamp = datetime.now(timezone.utc)
    mid_price = 70000.0
    snapshot.tick = {"ask": mid_price + 25.0, "bid": mid_price - 25.0, "mid": mid_price}
    snapshot.symbol = "BTCUSD"
    snapshot.symbol_info = {"point": 0.00001, "spread": 50, "trade_contract_size": 1.0}
    snapshot.regime = MarketRegime.UNKNOWN
    snapshot.indicators = indicators
    # snapshot.price is a property, derived from tick['mid']
    
    snapshot.metadata = {
        "manifold_curvature": curvature,
        "tick_velocity": velocity,
        "v_pulse_detected": False,
        "phi_resonance": False
    }

    # Quantum State
    # Note: TrinityCore extracts 'phi' and 'coherence' from quantum_state.phi/coherence
    q_state = MagicMock()
    q_state.phi = phi
    q_state.coherence = coherence
    q_state.collapsed_signal = 0.35 # BUY
    q_state.raw_signal = 0.35 # Equal to collapsed signal for testing
    q_state.confidence = 0.85
    q_state.entropy = 0.1
    q_state.superposition = False
    q_state.metadata = {"phi": phi, "coherence": coherence}
    q_state.agent_signals = []

    # Regime State
    r_state = RegimeState(
        current=MarketRegime.UNKNOWN,
        confidence=1.0,
        transition_prob=0.0,
        predicted_next=MarketRegime.UNKNOWN,
        aggression_multiplier=1.0,
        reasoning="Test Regime",
        duration_bars=10
    )
    r_state.v_pulse_detected = False

    # Bypass startup cooldown in TrinityCore
    trinity._startup_timestamp = time.time() - 1000 
    trinity._creation_time = time.time() - 1000 # Critical for uptime calculation in _check_vetos 
    
    decision = trinity.decide(q_state, r_state, snapshot, asi_state)
    
    print(f"Action: {decision.action}")
    print(f"Reasoning: {decision.reasoning}")
    
    from core.decision.trinity_core import Action
    if expected_unlocked:
        if decision.action != Action.WAIT:
            print(f"✅ SUCCESS: Trade UNLOCKED via SMS Sovereignty.")
        else:
            print(f"❌ FAILURE: Trade blocked. Reasoning: {decision.reasoning}")
    else:
        if decision.action == Action.WAIT:
            print(f"✅ SUCCESS: Logic correctly vetoed trade.")
        else:
            print(f"❌ FAILURE: Trade erroneously authorized.")

if __name__ == "__main__":
    trinity = TrinityCore()
    
    # Mocking ASI State (Disable circuit breakers)
    asi_state = MagicMock()
    asi_state.circuit_breaker_active = False
    asi_state.consecutive_losses = 0
    asi_state.daily_drawdown = 0.0

    # Mocking Indicators (Avoid ATR blocks)
    indicators = {
        "M5_atr_14": [100.0],
        "M1_atr_14": [100.0],
        "M5_ema_9": [70000.0]
    }

    # CASO 1: SMS Tier 1 (High Voltage)
    # Curvatura > 0.08, Velocidade > 10.0, Phi baixo (0.01), Coerência baixa (0.40)
    run_scenario(trinity, asi_state, indicators, 
                 "SCENARIO 1: Tier-1 SMS (High Voltage)", 
                 curvature=0.09, velocity=12.0, coherence=0.40, phi=0.01)
    
    # CASO 2: SMS Tier 2 (Structural Stability)
    # Curvatura > 0.15, Velocidade baixa (3.0), Phi baixo (0.01), Coerência ALTA (0.45)
    run_scenario(trinity, asi_state, indicators, 
                 "SCENARIO 2: Tier-2 SMS (Structural Stability)", 
                 curvature=0.20, velocity=3.0, coherence=0.45, phi=0.01)

    # CASO 3: Sem Cobertura SMS (Baixa Curvatura, Baixa Velocidade)
    run_scenario(trinity, asi_state, indicators, 
                 "SCENARIO 3: NO SMS COVERAGE", 
                 curvature=0.02, velocity=3.0, coherence=0.40, phi=0.01, expected_unlocked=False)
