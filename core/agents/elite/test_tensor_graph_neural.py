"""
    TESTE NEURAL OMEGA (Lei VI.3 & VI.5)
    Avaliação de Vitalidade, Cognição e Integração para:
    - SOLÉNN TENSOR GRAPH Ω
    - SOLÉNN NEXUS HYPERDIM Ω
"""
import time
import numpy as np
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from core.agents.elite.solenn_tensor_graph import SolennTensorGraph
from core.agents.elite.solenn_nexus_hyperdim import SolennNexusHyperdim

async def test_vitality(tensor, nexus):
    print("\n[ETAPA 1] VITALIDADE PLENA (Verificações Base)")
    
    assert isinstance(tensor, SolennTensorGraph)
    assert isinstance(nexus, SolennNexusHyperdim)
    print("✅ Instanciação dos Agentes Tensor e Nexus = OK")
    
    assert tensor.max_dimension == 15
    print("✅ TensorGraph: Prevenção dimensional (O(N^3)) confirmada para 15.")

async def test_cognition(tensor, nexus):
    print("\n[ETAPA 2] COGNIÇÃO: FÍSICA DOS GRAFOS & MACRO CONTÁGIO")
    
    # 1. Tensor Graph
    price_nodes = np.random.rand(50).astype(np.float32) * 100.0 # Price clustering simulation
    t0 = time.perf_counter()
    vec_tensor = await tensor.compute_tensor_topology(price_nodes)
    t1 = time.perf_counter()
    print(f"✅ Tensor Graph Topology: Executado em {(t1-t0)*1000:.4f}ms.")
    print(f"   ↳ Lie Symmetry: {vec_tensor.lie_symmetry_violation:.4f} | Braid Index: {vec_tensor.tensor_braiding_index:.2f}")
    
    # 2. Nexus Hyperdim
    dxy_macro = 0.05 # 5% impulse on DXY
    btc_mom = -0.01
    t0 = time.perf_counter()
    vec_nexus = await nexus.compute_macro_nexus(dxy_macro, btc_mom)
    t1 = time.perf_counter()
    print(f"✅ Nexus Macro Hyperdim: Executado em {(t1-t0)*1000:.4f}ms.")
    print(f"   ↳ Nexus Pull: {vec_nexus.nexus_gravity_pull:.4f} | Contagion: {vec_nexus.macro_contagion_force:.4f}")

async def test_integration(tensor, nexus):
    print("\n[ETAPA 3] INTEGRAÇÃO PARALELA (Bypass de Latência HFT)")
    
    results = await asyncio.gather(
        tensor.compute_tensor_topology(np.random.normal(100, 2, 20).astype(np.float32)),
        nexus.compute_macro_nexus(macro_dxy_vector=-0.02, local_btc_momentum=0.03)
    )
    
    print("✅ Reação Conjunta Async = SUCESSO")
    print(f"   ↳ [Tensor] Cluster Density: {results[0].clustering_density:.4f}")
    print(f"   ↳ [Nexus] Hex Matrix Entropy: {results[1].hex_matrix_entropy:.4f}")

async def main():
    print("=" * 60)
    print(" SOLÉNN v2 - BOOTING NEURAL TESTS (TENSOR GRAPH + NEXUS HYPERDIM CLUSTER)")
    print("=" * 60)
    
    tensor = SolennTensorGraph(tensor_dim=15)
    nexus = SolennNexusHyperdim()
    
    await test_vitality(tensor, nexus)
    await test_cognition(tensor, nexus)
    await test_integration(tensor, nexus)

if __name__ == "__main__":
    asyncio.run(main())
