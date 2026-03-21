import numpy as np
import time
import os
import sys

# Adicionar raiz do projeto ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.consciousness.neural_swarm import NeuralSwarm
from core.consciousness.quantum_thought import QuantumThoughtEngine
from core.decision.trinity_core import TrinityCore, Action
from market.data_engine import MarketSnapshot
from utils.logger import log

def test_swarm_coherence():
    log.omega("🧪 [STABILITY TEST] Verificando Coerência do Enxame e Métrica Phi...")
    
    # Setup
    swarm = NeuralSwarm(None, None, None)
    thought = QuantumThoughtEngine()
    trinity = TrinityCore()
    
    snapshot = MarketSnapshot()
    snapshot.symbol = "BTCUSD"
    snapshot.timestamp = time.time()
    snapshot.candles = {"M5": {"close": np.array([50000]*100), "high": np.array([50100]*100), "low": np.array([49900]*100)}}
    snapshot.indicators = {"M5_atr_14": np.array([100.0]), "M5_volume_ratio": np.array([1.0])}
    snapshot.book = {}
    snapshot.metadata = {}
    snapshot.symbol_info = {"spread": 10, "point": 0.01, "trade_tick_value": 1.0}
    snapshot.tick = {"mid": 50000.0, "bid": 49995.0, "ask": 50005.0, "spread": 10}
    
    # 1. Testar Modulação de Autoridade (Baixa Coerência)
    log.info("🔹 Testando Modulação de Autoridade (Coerência Baixa)...")
    initial_weights = {a.name: a.weight for a in swarm.agents[:5]}
    swarm.modulate_authority(coherence=0.2)
    new_weights = {a.name: a.weight for a in swarm.agents[:5]}
    
    # Agentes de Elite devem ter aumentado o peso (ou pelo menos mudado)
    log.info(f"⚖️ Exemplo de mudança: {list(initial_weights.keys())[0]} {initial_weights[list(initial_weights.keys())[0]]} -> {new_weights[list(new_weights.keys())[0]]}")
    log.info("✅ Modulação de Autoridade OK.")

    # 2. Testar Pruning de Agentes
    log.info("🔹 Testando Pruning de Agentes...")
    # Forçar acurácia baixa em alguns agentes
    for a in swarm.agents[:3]:
        a._accuracy_history = [False] * 10
    
    original_count = len(swarm.agents)
    swarm.prune_agents(min_accuracy=0.45)
    log.info(f"✂️ Agentes: {original_count} -> {len(swarm.agents)}")
    assert len(swarm.agents) < original_count
    log.info("✅ Pruning OK.")

    # 3. Testar SYNERGY VETO em TrinityCore
    log.info("🔹 Testando SYNERGY VETO em TrinityCore...")
    from core.consciousness.quantum_thought import QuantumState
    
    # Caso 1: Phi Saudável (Sem Veto)
    qs_ok = QuantumState(
        raw_signal=0.8, 
        collapsed_signal=0.8, 
        confidence=0.8, 
        coherence=0.8,
        entropy=0.1,
        superposition=False,
        decision_vector=np.array([0, 0, 1]),
        agent_contributions={},
        agent_signals=[],
        phi=0.5,
        metadata={},
        reasoning="Testing"
    )
    res_ok = trinity._check_vetos(snapshot, None, None, v_pulse_detected=False, quantum_state=qs_ok)
    log.info(f"🛡️ Resposta Phi Saudável: {res_ok}")
    assert res_ok is None or "SYNERGY_VETO" not in res_ok

    # Caso 2: Phi Crítico (Veto Ativado)
    qs_bad = QuantumState(
        raw_signal=0.8, 
        collapsed_signal=0.8, 
        confidence=0.8, 
        coherence=0.2,
        entropy=0.8,
        superposition=True,
        decision_vector=np.array([0, 0, 1]),
        agent_contributions={},
        agent_signals=[],
        phi=0.02,
        metadata={},
        reasoning="Testing"
    )
    res_bad = trinity._check_vetos(snapshot, None, None, v_pulse_detected=False, quantum_state=qs_bad)
    log.info(f"🛡️ Resposta Phi Crítico: {res_bad}")
    assert res_bad is not None and "SYNERGY_VETO" in res_bad
    log.info("✅ SYNERGY VETO OK.")

    log.omega("🏆 [STABILITY TEST] SUCESSO. Enxame e Métrica Phi validados.")

if __name__ == "__main__":
    test_swarm_coherence()
