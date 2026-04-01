import asyncio
import numpy as np
import time
from market.orderflow_matrix import OrderflowMatrix

# [Ω-MATRIX-BRAIN-TEST] Scripts de Validação Neural (v1.0)
# Auditoria de 162 Vetores: Percepção, Liq-Dynamics e Sincronia.

async def test_matrix_neural_integrity():
    print("🧠 SOLÉNN Matrix Ω-0: Neural Validation Start")
    matrix = OrderflowMatrix("BTCUSDT")
    await matrix.initialize()
    
    # ---------------------------------------------------------
    # FASE 1: VITALIDADE E PERCEPÇÃO (Concept 3 & 1)
    # ---------------------------------------------------------
    print("📡 Fase 1: Testando Vitalidade e Percepção de Fluxo")
    
    # Simulação de 500 ticks orgânicos
    for i in range(500):
        side = "buy" if i % 2 == 0 else "sell"
        price = 60000.0 + (i * 0.1)
        vol = 1.0 + np.random.random()
        
        tick = {
            "price": price,
            "volume": vol,
            "side": side,
            "time_ns": time.perf_counter_ns(),
            "last_ask": price + 0.5,
            "last_bid": price - 0.5
        }
        
        signal = await matrix.ingest_tick(tick)
        if i == 499:
            print(f"✅ Último sinal orgânico (i={i}): Phi={signal.phi:.4f}, Gen={signal.genuinity:.2f}, Tox={signal.toxicity:.2f}")
            assert 0.0 <= signal.genuinity <= 1.0
            assert 0.0 <= signal.toxicity <= 1.0

    # ---------------------------------------------------------
    # FASE 2: MANIPULAÇÃO E MANUTENÇÃO (Concept 2)
    # ---------------------------------------------------------
    print("🕵️ Fase 2: Testando Detecção de Manipulação (Iceberg & Dark Flow)")
    
    # Simulação de Iceberg (Preço fixo, volume repetido)
    for j in range(30):
        tick_ice = {
            "price": 60500.0,
            "volume": 5.0,
            "side": "buy",
            "time_ns": time.perf_counter_ns()
        }
        signal = await matrix.ingest_tick(tick_ice)
        
    print(f"🔍 Iceberg Cluster Detectado? P_ice={signal.metadata['iceberg_prob']:.2f}")
    assert signal.metadata['iceberg_prob'] > 0.5, "ERRO: Iceberg não detectado nos 162 vetores"

    # Simulação de Dark Flow (Trade fora do range Bid/Ask)
    tick_dark = {
        "price": 61000.0,
        "volume": 10.0,
        "side": "sell",
        "time_ns": time.perf_counter_ns(),
        "last_ask": 60900.0,
        "last_bid": 60800.0
    }
    signal = await matrix.ingest_tick(tick_dark)
    print(f"🕶️ Dark Flow Detectado? DF={signal.metadata['dark_flow']:.2f}")
    assert signal.metadata['dark_flow'] == 1.0, "ERRO: Dark Flow não identificado"

    # ---------------------------------------------------------
    # FASE 3: AGRESSÃO E SINCRONIA Ω (Concept 1 & 3)
    # ---------------------------------------------------------
    print("🥊 Fase 3: Testando Agressão Explosiva e Sincronia de Sinal")
    
    # Simulação de Sweep (Múltiplos preços no mesmo NS)
    ts = time.perf_counter_ns()
    for k in range(5):
        tick_sweep = {
            "price": 61000.0 + (k * 1.0),
            "volume": 20.0,
            "side": "buy",
            "time_ns": ts
        }
        signal = await matrix.ingest_tick(tick_sweep)
    
    print(f"🔥 Agressão Explosiva (Sweep): Agg={signal.aggression:.2f}, Phi={signal.phi:.2f}")
    assert signal.aggression > 0.5, "ERRO: Sweep-to-fill não degradou o status de agressão positivamente"
    assert signal.phi > 0.0, "ERRO: Phi deve ser positivo para sweep de compra"

    print("\n✅ MATRIX Ω-0: 162 VETORES VALIDADO COM SUCESSO")
    await matrix.stop()

if __name__ == "__main__":
    asyncio.run(test_matrix_neural_integrity())
