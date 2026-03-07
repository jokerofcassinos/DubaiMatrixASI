import sys
import os
import time

# Adicionar o diretório raiz ao path
sys.path.append(os.getcwd())

from config.omega_params import OMEGA
from core.consciousness.quantum_thought import QuantumState, AgentSignal
from core.consciousness.regime_detector import RegimeState, MarketRegime
from core.decision.trinity_core import TrinityCore, Action
import numpy as np

def test_recalibration():
    print("--- 🔬 DUBAI MATRIX ASI — PHASE Ω-EXTREME VERIFICATION ---")
    
    # 1. Verificar Parâmetros Base
    mc_wp = OMEGA.get("mc_min_win_prob")
    phi_min = OMEGA.get("phi_min_threshold")
    print(f"Base MC_MIN_WIN_PROB: {mc_wp} (Target: 0.38)")
    print(f"Base PHI_MIN: {phi_min} (Target: 0.35)")
    
    # 2. Simular Snapshot em DRIFTING_BEAR
    class MockSnapshot:
        def __init__(self):
            self.tick = {"ask": 67000.1, "bid": 67000.0}
            self.symbol_info = {"spread": 10, "point": 0.01}
            self.indicators = {"M5_atr_14": [100.0]}
            self.indicators.update({"M5_atr_14": [100.0]})
            self.candles = {"M1": {"close": [67100, 67080, 67060, 67040, 67020]}} # Drifting Bear
            self.metadata = {"tick_velocity": 45.0, "pnl_prediction": "NEUTRAL"} # Burst detectado

    snapshot = MockSnapshot()
    
    # 3. Simular QuantumState com alta entropia e PHI no novo threshold
    q_state = QuantumState(
        raw_signal=-0.3, # Sinal fraco de venda
        collapsed_signal=-0.3,
        confidence=0.8,
        coherence=0.4,
        entropy=0.9, # Entropia alta
        superposition=False,
        decision_vector=np.array([-0.3]),
        agent_contributions={},
        agent_signals=[AgentSignal("WhaleTrackerAgent", -0.6, 0.9, 1.0, "Institucional")],
        phi=0.30, # Abaixo do base (0.35) mas deve ser aceito pelo dynamic_phi em DRIFTING
        reasoning="Test"
    )
    
    regime = RegimeState(
        current=MarketRegime.DRIFTING_BEAR,
        confidence=0.8,
        transition_prob=0.1,
        predicted_next=MarketRegime.DRIFTING_BEAR,
        aggression_multiplier=1.1,
        reasoning="Test",
        duration_bars=10
    )
    
    trinity = TrinityCore()
    # Bypass startup cooldown
    trinity._creation_time = time.time() - 300 
    
    # Mock para evitar simulação real Monte Carlo
    class MockMonteCarlo:
        def simulate_trade(self, **kwargs):
            from core.consciousness.monte_carlo_engine import MonteCarloResult
            return MonteCarloResult(
                win_probability=0.5, loss_probability=0.5, expected_return=10.0,
                median_return=10.0, best_case=20.0, worst_case=-5.0,
                value_at_risk_95=-10.0, conditional_var_95=-15.0, sharpe_ratio=1.5,
                skewness=0.0, kurtosis=3.0, optimal_sl_distance=50.0,
                optimal_tp_distance=100.0, optimal_rr_ratio=2.0,
                n_simulations=1000, n_steps=50, simulation_time_ms=1.5,
                regime_used="TEST", monte_carlo_score=0.5
            )
    trinity.monte_carlo = MockMonteCarlo()
    
    try:
        decision = trinity.decide(q_state, regime, snapshot, None)
        print(f"Decision Action: {decision.action}")
        print(f"Decision Reasoning: {decision.reasoning}")
        
        # Verificação de GOD-MODE REVERSAL via Velocity Divergence
        if "GOD-MODE REVERSAL" in decision.reasoning or "Velocity Burst" in decision.reasoning:
            print("✅ SUCCESS: Velocity Divergence Logic triggered!")
        else:
            print("❌ FAILED: Velocity logic not triggered.")
    except Exception as e:
        print(f"⚠️ Simulation Error: {e}")

if __name__ == "__main__":
    test_recalibration()
