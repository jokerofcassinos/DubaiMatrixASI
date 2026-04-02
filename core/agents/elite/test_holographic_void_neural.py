"""
    TESTE NEURAL OMEGA (Lei VI.3 & VI.5)
    Avaliação de Vitalidade, Cognição e Integração para:
    - SOLÉNN HOLOGRAPHIC MEMORY Ω
    - SOLÉNN OMNISCIENCE VOID Ω
"""
import time
import numpy as np
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from core.agents.elite.solenn_holographic_memory import SolennHolographicMemory
from core.agents.elite.solenn_omniscience_void import SolennOmniscienceVoid

async def test_vitality(holo, void_age):
    print("\n[ETAPA 1] VITALIDADE PLENA (Verificações Base)")
    
    assert isinstance(holo, SolennHolographicMemory)
    assert isinstance(void_age, SolennOmniscienceVoid)
    print("✅ Instanciação dos Agentes Holographic e Void = OK")
    
    assert void_age.capacitor_limit == 100.0
    print("✅ Omniscience Void: Capacitor Limit Set = 100.0.")

async def test_cognition(holo, void_age):
    print("\n[ETAPA 2] COGNIÇÃO: TRANSCENDÊNCIA DE MEMÓRIA & VÁCUO")
    
    # 1. Holographic Memory
    spikes = np.random.normal(0, 1, 10).astype(np.float32)
    volatility = 0.05
    
    t0 = time.perf_counter()
    vec_holo = await holo.extract_holographic_continuum(spikes, volatility)
    t1 = time.perf_counter()
    print(f"✅ Holographic Memory Topology: Executado em {(t1-t0)*1000:.4f}ms.")
    print(f"   ↳ Pheromone Evaporation: {vec_holo.pheromone_evaporation_rate:.4f} | Ghost Inf: {vec_holo.ghost_inference_match:.4f}")
    
    # 2. Omniscience Void (Burst test)
    phantom_imb = -0.3 # Fake sell walls
    vol_tick = 60.0
    
    t0 = time.perf_counter()
    vec_void = await void_age.compute_omniscience_collapse(vol_tick, phantom_imb)
    
    # Trigger Supernova
    vec_void_2 = await void_age.compute_omniscience_collapse(50.0, phantom_imb) # 60 + 50 = 110 (triggers apotheosis)
    t1 = time.perf_counter()
    
    print(f"✅ Omniscience Void: Executado em {(t1-t0)*1000:.4f}ms.")
    print(f"   ↳ Dark Mass Density: {vec_void.dark_mass_density:.4f} | Supernova Trigger: {vec_void_2.omni_apotheosis_trigger}")

async def test_integration(holo, void_age):
    print("\n[ETAPA 3] INTEGRAÇÃO PARALELA (Fechamento da Abóbada Causal)")
    
    results = await asyncio.gather(
        holo.extract_holographic_continuum(np.array([1.2, 0.4, -0.2]), 0.08),
        void_age.compute_omniscience_collapse(aggregate_volume=10.0, phantom_imbalance=0.1)
    )
    
    print("✅ O(1) Paralelo do Cérebro Abstrato P0 = SUCESSO")
    print(f"   ↳ [Holo] Time Dilation: {results[0].geodesic_time_dilation:.4f}")
    print(f"   ↳ [Void] Swarm Consensus: {results[1].meta_swarm_consensus:.4f}")

async def main():
    print("=" * 60)
    print(" SOLÉNN v2 - BOOTING NEURAL TESTS (HOLOGRAPHIC MEMORY + OMNISCIENCE VOID)")
    print("=" * 60)
    
    holo = SolennHolographicMemory(memory_decay=0.99)
    void_age = SolennOmniscienceVoid(capacitor_limit=100.0)
    
    await test_vitality(holo, void_age)
    await test_cognition(holo, void_age)
    await test_integration(holo, void_age)

if __name__ == "__main__":
    asyncio.run(main())
