import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Adicionar root ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from execution.risk_quantum import RiskQuantumEngine
from config.settings import ASIState
import config.omega_params

class MockSnapshot:
    def __init__(self, price=100000.0, curvature=0.0, coherence=0.5, pnl="STABLE"):
        self.price = price
        self.symbol_info = {"point": 0.01, "trade_contract_size": 1}
        self.metadata = {
            "pnl_prediction": pnl,
            "phi_last": 0.5,
            "coherence_last": coherence,
            "manifold_curvature": curvature,
            "kl_divergence": 0.1,
            "v_pulse_detected": False,
            "raw_signal": 0.5
        }
        self.indicators = {
            "M1_atr_14": [50.0]
        }
        self.account = {"margin_level": 500.0, "margin": 1000.0}

def test_nro_logic():
    print("🧠 [VERIFICACAO] Testando Neural Risk Orchestration (NRO) - FINAL FIX...")
    
    # ═══ MOCK DATA ═══
    mock_params = {
        "nro_manifold_sensitivity": 1.25,
        "nro_coherence_weight": 0.85,
        "structural_expectancy_sizing_enabled": 1.0,
        "exposure_ceiling_balance_ratio": 1.0, 
        "position_size_pct": 1000.0,
        "paradigm_shift_threshold": 0.95,
        "stop_loss_atr_mult": 1.5,
        "take_profit_atr_mult": 2.5,
        "commission_per_lot": 32.0,
        "min_profit_per_ticket": 50.0,
        "min_commission_reward_ratio": 2.0,
        "margin_safety_buffer": 0.1,
        "kelly_fraction": 1.0,
        "non_ergodic_enabled": False
    }

    # Patch Global - Surgical and Targeted
    with patch('config.omega_params.OmegaParameterSpace.get', side_effect=lambda self, name, default=None: mock_params.get(name, default if default is not None else 1.0)), \
         patch('execution.risk_quantum.MIN_LOT_SIZE', 0.001), \
         patch('execution.risk_quantum.MAX_LOT_SIZE', 10000.0), \
         patch('execution.risk_quantum.RISK_MAX_POSITION_PCT', 1.0), \
         patch('execution.risk_quantum.RISK_MAX_DAILY_LOSS_PCT', 1.0), \
         patch('execution.risk_quantum.RISK_MAX_DRAWDOWN_PCT', 1.0):
        
        state = ASIState()
        risk = RiskQuantumEngine()
        risk.MAX_LOT = 10000.0
        
        balance = 100000.0 # $100k
        sl_dist = 50.0 # points
        tick_value = 0.01
        
        # CASO 1: Expectância Negativa mas com Coerência (Safe Exploration)
        print("\n--- CASO 1: Negative Expectancy + High Coherence ---")
        snap1 = MockSnapshot(coherence=0.85, pnl="NEGATIVE_EXPECTANCY")
        lot1 = risk.calculate_lot_size(balance, sl_dist, 0.7, 100, 100, {"point": 0.01}, 0.8, state, snap1)
        print(f"Lote resultante (Safe Exploration): {lot1:.3f}")
        assert lot1 > 0, f"Deveria permitir trade via Safe Exploration (lot={lot1})"

        # CASO 2: Expansão por Curvatura do Manifold
        print("\n--- CASO 2: Manifold Curvature Scaling ---")
        snap2 = MockSnapshot(curvature=0.2, coherence=0.5, pnl="STABLE") 
        snap0 = MockSnapshot(curvature=0.0, coherence=0.5, pnl="STABLE")
        
        # v_pulse desativado
        snap2.metadata["v_pulse_detected"] = False
        snap0.metadata["v_pulse_detected"] = False
        
        lot2_norm = risk.calculate_lot_size(balance, sl_dist, 0.7, 100, 100, {"point": 0.01}, 0.95, state, snap0)
        lot2_curv = risk.calculate_lot_size(balance, sl_dist, 0.7, 100, 100, {"point": 0.01}, 0.95, state, snap2)
        print(f"Lote Normal: {lot2_norm:.3f} | Lote com Curvatura: {lot2_curv:.3f}")
        assert lot2_curv > lot2_norm, f"Deveria expandir lote com curvatura positiva ({lot2_curv} <= {lot2_norm})"

        # CASO 3: Bypass Letal (V-Pulse)
        print("\n--- CASO 3: Lethal Bypass (V-Pulse) ---")
        snap3 = MockSnapshot(coherence=0.5, pnl="CRITICAL_NEGATIVE_EXPECTANCY")
        snap3.metadata["v_pulse_detected"] = True
        lot3 = risk.calculate_lot_size(balance, sl_dist, 0.7, 100, 100, {"point": 0.01}, 0.8, state, snap3)
        print(f"Lote resultante (Lethal Bypass): {lot3:.3f}")
        assert lot3 >= 0.01, f"Deveria permitir bypass (lot={lot3})"

    print("\n✅ [NRO] Todos os testes de orquestração passaram!")

if __name__ == "__main__":
    test_nro_logic()
