import time
import sys
import os
import datetime

# Adicionar root ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.consciousness.neural_swarm import NeuralSwarm
from core.consciousness.regime_detector import RegimeState, MarketRegime
from core.decision.trinity_core import TrinityCore, Action
from core.consciousness.quantum_thought import QuantumState

class MockSnapshot:
    def __init__(self, price=100000.0):
        self.price = price
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)
        self.symbol_info = {"point": 0.01, "spread": 100}
        self.candles = {
            "M1": {
                "open": [price] * 64,
                "high": [price] * 64,
                "low": [price] * 64,
                "close": [price] * 64,
                "tick_volume": [100] * 64
            },
            "M5": {
                "open": [price] * 64,
                "high": [price] * 64,
                "low": [price] * 64,
                "close": [price] * 64,
                "tick_volume": [100] * 64
            }
        }
        # Shadow attributes
        self.m1_closes = self.candles["M1"]["close"]
        self.m5_closes = self.candles["M5"]["close"]
        self.book = {
            "bids": [{"price": price-5, "volume": 1.0}], 
            "asks": [{"price": price+5, "volume": 1.0}]
        }
        self.spread = 10
        self.atr = 50.0
        self.recent_ticks = [{"last": price, "bid": price-10, "ask": price+10, "volume": 10}] * 100
        self.tick = self.recent_ticks[-1] 
        self.regime = "LOW_LIQUIDITY" # Para o HolographicMemoryAgent
        
        self.metadata = {
            "tick_velocity": 2.0,
            "shannon_entropy": 0.3,
            "v_pulse_detected": False,
            "v_pulse_capacitor": 0.1,
            "pnl_prediction": "STABLE",
            "kl_divergence": 0.1,
            "jounce": 0.0,
            "recent_ticks": self.recent_ticks
        }
        self.indicators = {
            "M1_entropy": [0.3] * 64,
            "M5_entropy": [0.3] * 64,
            "M5_hurst": 0.5,
            "M5_atr_14": [50.0] * 64,
            "M5_bb_width": [100.0] * 64,
            "M5_ema_9": [price] * 64,
            "M5_ema_21": [price] * 64,
            "M5_ema_50": [price] * 64,
            "M5_volume_ratio": [1.0] * 64,
            "M1_volatility_ratio": [1.0] * 64,
            "M1_atr_14": [50.0] * 64,
            "M5_rsi_14": [50.0] * 64,
            "M1_delta_vol": [0.0] * 64
        }

def test_swarm_and_veto():
    print("🧠 [DIAGNOSTICO] Testando Otimização de Agentes e Veto...")
    
    swarm = NeuralSwarm()
    core = TrinityCore()
    
    # BYPASS COOLDOWN (TrinityCore utiliza _startup_timestamp com time.time())
    core._startup_timestamp = time.time() - 200 # 200 segundos atrás
    
    snapshot = MockSnapshot()
    
    # 1. Testar latência e participação
    print(f"--- FASE 1: Latência e Participação ({len(swarm.agents)} agentes) ---")
    start = time.time()
    signals = swarm.analyze(snapshot)
    end = time.time()
    
    active_count = len([s for s in signals if abs(s.signal) > 0.01])
    print(f"✅ Agentes que retornaram sinal: {len(signals)}")
    print(f"✅ Agentes com sinal ativo (>0.01): {active_count}")
    print(f"⏱️ Tempo total de análise: {(end-start)*1000:.2f}ms")
    
    # 2. Testar Veto Bypass (Entropic Vacuum)
    print("\n--- FASE 2: Entropic Vacuum Bypass ---")
    # Configurar estado com alta coerência mas baixa volatilidade
    class FakeQuantum:
        def __init__(self):
            self.signal = 0.8
            self.raw_signal = 0.8
            self.collapsed_signal = 0.8
            self.confidence = 0.95
            self.coherence = 0.75  # ALTA COERENCIA (>0.60)
            self.phi = 0.45        # ALTA INTEGRACAO (>0.30)
            self.entropy = 0.30    # BAIXA ENTROPIA (Geralmente causa Veto)
            self.superposition = False
            self.metadata = {
                "bull_agents": ["Agent1", "Agent2", "Agent3"], 
                "bear_agents": [],
                "phi": 0.45,
                "coherence": 0.75,
                "entropy": 0.30
            }
            self.agent_signals = signals
            
    q_state = FakeQuantum()
    
    # Regime de Baixa Liquidez/Drifting
    from core.consciousness.regime_detector import MarketRegime, RegimeState
    regime = RegimeState(
        current=MarketRegime.LOW_LIQUIDITY,
        confidence=0.8,
        transition_prob=0.1,
        predicted_next=MarketRegime.LOW_LIQUIDITY,
        aggression_multiplier=0.4,
        reasoning="Testing Bypass",
        duration_bars=10
    )
    
    # Mocking asi_state com métricas avançadas
    class FakeState:
        def __init__(self):
            self.win_rate = 0.6
            self.avg_win = 100
            self.avg_loss = 50
            self.total_profit = 1000
            self.equity = 10000
            self.balance = 10000
            self.consecutive_wins = 5
            self.consecutive_losses = 0
            self.max_drawdown = 0.05
            self.recovery_factor = 2.0
            self.profit_factor = 2.5
            self.sharpe_ratio = 3.0
            self.kelly_criterion = 0.2
            self.risk_fraction = 0.01
            
    decision = core.decide(q_state, regime, snapshot, FakeState())
    
    if decision and decision.action != Action.WAIT:
        print(f"🔥 SUCESSO! Veto de Vácuo Ignorado via Coerência (Ação: {decision.action.value})")
        print(f"📝 Razão: {decision.reasoning}")
    elif decision:
        print(f"❌ FALHA: Veto ainda ativo. Razão: {decision.veto_reason}")
    else:
        print(f"❌ FALHA: Decisão retornou None.")

if __name__ == "__main__":
    test_swarm_and_veto()
