"""
    TESTE NEURAL OMEGA (Lei VI.3 & VI.5)
    Avaliação de Vitalidade, Cognição e Integração para:
    - SOLÉNN BLACK SWAN Ω
    - SOLÉNN LIQUIDATOR Ω
    - SOLÉNN RICCI Ω
    - SOLÉNN FEYNMAN Ω
    - SOLÉNN KOLMOGOROV Ω
"""
import time
import numpy as np
import asyncio
from dataclasses import dataclass
import sys
import os

# Adicionar caminho para importar os módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from core.agents.elite.solenn_black_swan import SolennBlackSwan, SwanSignal
from core.agents.elite.solenn_liquidator import SolennLiquidator, LiquidatorPulse
from core.agents.elite.solenn_ricci import SolennRicci, RicciMetrics
from core.agents.elite.solenn_feynman import SolennFeynman, FeynmanWave
from core.agents.elite.solenn_kolmogorov import SolennKolmogorov, KolmogorovSignal

@dataclass
class MockSnapshot:
    price: float = 65000.0
    atr: float = 150.0
    volume: float = 12.5
    flags: int = 1

async def test_vitality(swan, liquidator, ricci, feynman, kolmogorov):
    print("\n[ETAPA 1] VITALIDADE PLENA (7+ Verificações)")
    
    assert isinstance(swan, SolennBlackSwan)
    assert isinstance(liquidator, SolennLiquidator)
    assert isinstance(ricci, SolennRicci)
    assert isinstance(feynman, SolennFeynman)
    assert isinstance(kolmogorov, SolennKolmogorov)
    print("✅ Instanciação dos 5 Hiper-Módulos Elite = OK")
    
    assert swan.h_buffer.shape == (1000,)
    print("✅ Black Swan: Buffers históricos pré-alocados O(1)")
    
    assert liquidator.hft_shadow_book.shape == (20,)
    print("✅ Liquidator: HFT Shadow Book Instanciado.")
    
    assert ricci.metric_tensor_g.shape == (4, 4)
    assert ricci.riemann_tensor_R.shape == (4, 4, 4, 4)
    print("✅ Ricci: Tensores Riemannianos P/V/Vol/T em Float32 dimensionados")
    
    assert feynman.superposition_matrix.shape == (100, 100)
    print("✅ Feynman: Matriz Quântica de Superposição (100x100) montada.")
    
    assert type(kolmogorov.shannon_entropy) == float
    print("✅ Kolmogorov: Vetores de Decaimento Entrópico carregados.")

async def test_cognition_physics(ricci, feynman, kolmogorov):
    print("\n[ETAPA 2] COGNIÇÃO: PHYSICS & TOPOLOGY CLUSTER")
    
    # Ricci TDA Test
    t0 = time.perf_counter()
    metrics_r = await ricci.compute_manifold_state(65000.0, 150.0)
    t1 = time.perf_counter()
    print(f"✅ Ricci: Topologia Betti calculada em {(t1-t0)*1000:.4f}ms (Curvatura: {metrics_r.scalar_curvature:.2f})")
    
    # Feynman Action test
    arr_prices = np.array([64900.0, 64950.0, 65000.0], dtype=np.float32)
    t0 = time.perf_counter()
    wave_f = await feynman.compute_quantum_paths(arr_prices, 65050.0) # Resistance at 65050
    t1 = time.perf_counter()
    print(f"✅ Feynman: Matriz de Integrais executada em {(t1-t0)*1000:.4f}ms. Probabilidade de Túnel: {wave_f.tunnel_probability:.4f}")
    
    # Kolmogorov Complexity Test
    arr_ticks = np.array([1, 1, 1, -1, 1, 1, -1, 1, 1, 1, -1, 1, 1, 1, -1], dtype=np.int8) 
    t0 = time.perf_counter()
    signal_k = await kolmogorov.calculate_entropic_state(arr_ticks)
    t1 = time.perf_counter()
    print(f"✅ Kolmogorov: Compressibilidade LZ calculada em {(t1-t0)*1000:.4f}ms. Entropia: {signal_k.entropy:.3f}")

async def test_integration(swan, liquidator, ricci, feynman, kolmogorov):
    print("\n[ETAPA 3] INTEGRAÇÃO PARALELA (5-Node Consensus Bypass)")
    
    snap = MockSnapshot(volume=0.0001, atr=1000.0, price=65000.0)
    
    # Rodar todos async em paralelo
    results = await asyncio.gather(
        liquidator.scan_phantom_vacuum(snap),
        swan.check_ruin_defenses(snap),
        ricci.compute_manifold_state(snap.price, snap.atr),
        feynman.compute_quantum_paths(np.array([64000.0, 65000.0]), 65500.0), # R> P
        kolmogorov.calculate_entropic_state(np.array([1, 1, -1])),
    )
    
    out_liq, out_swan, out_ricci, out_fey, out_kol = results
    
    print("✅ Execução Paralela Assíncrona via asyncio.gather = SUCESSO")
    print(f"   ↳ [Ricci] Gauge Anomaly: {out_ricci.gauge_anomaly}")
    print(f"   ↳ [Feynman] Túnel Probabilidade: {out_fey.tunnel_probability:.2f}")
    print(f"   ↳ [Kolmogorov] Morte Térmica da Entropia: {out_kol.is_entropy_dead}")
    if out_swan.trigger_active:
        print("✅ Byzantine Override Ativo pelo BlackSwan!")

async def main():
    print("=" * 60)
    print(" SOLÉNN v2 - BOOTING NEURAL TESTS (ELITE + PHYSICS CLUSTER)")
    print("=" * 60)
    
    swan = SolennBlackSwan()
    liq = SolennLiquidator()
    ricci = SolennRicci()
    fey = SolennFeynman()
    kol = SolennKolmogorov()
    
    await test_vitality(swan, liq, ricci, fey, kol)
    await test_cognition_physics(ricci, fey, kol)
    await test_integration(swan, liq, ricci, fey, kol)

if __name__ == "__main__":
    asyncio.run(main())
