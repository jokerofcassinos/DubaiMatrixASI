"""
    TESTE NEURAL OMEGA (Lei VI.3 & VI.5)
    Avaliação de Vitalidade, Cognição e Integração para:
    - SOLÉNN FLUID DYNAMICS Ω
    - SOLÉNN CHAOS THERMODYNAMICS Ω
"""
import time
import numpy as np
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from core.agents.elite.solenn_fluid_dynamics import SolennFluidDynamics
from core.agents.elite.solenn_chaos_thermodynamics import SolennChaosThermodynamics

async def test_vitality(fluid, chaos):
    print("\n[ETAPA 1] VITALIDADE PLENA (Verificações Base)")
    
    assert isinstance(fluid, SolennFluidDynamics)
    assert isinstance(chaos, SolennChaosThermodynamics)
    print("✅ Instanciação dos Agentes Fluid e Chaos = OK")
    
    assert fluid.cylindrical_obstacle_size.shape == (50,)
    print("✅ FluidDynamics: Array de Obstrução Navier-Stokes Alocado.")
    
    assert chaos.tick_window_size == 120
    print("✅ ChaosThermodynamics: Janela Lyapunov configurada para 120 Ticks.")

async def test_cognition(fluid, chaos):
    print("\n[ETAPA 2] COGNIÇÃO: FÍSICA DOS FLUIDOS & CAOS TÉRMICO")
    
    # 1. Fluid Dynamics
    density = np.random.rand(50).astype(np.float32) * 10.0 # Livro de ofertas randômico
    velocity = 5.5 # Ticks per ms speed
    t0 = time.perf_counter()
    vec_fluid = await fluid.extract_fluid_tensors(density, velocity)
    t1 = time.perf_counter()
    print(f"✅ Fluid Navier-Stokes: Executado em {(t1-t0)*1000:.4f}ms.")
    print(f"   ↳ Reynolds Number: {vec_fluid.reynolds_number:.2f} | Turbulent? {vec_fluid.is_turbulent}")
    
    # 2. Chaos Thermodynamics
    returns = np.random.normal(0, 0.01, 120).astype(np.float32)
    volatility = 0.5
    t0 = time.perf_counter()
    vec_chaos = await chaos.compute_lyapunov_thermodynamics(returns, volatility)
    t1 = time.perf_counter()
    print(f"✅ Chaos Lyapunov: Executado em {(t1-t0)*1000:.4f}ms.")
    print(f"   ↳ Lyapunov Exp: {vec_chaos.max_lyapunov_exponent:.4f} | Chaotic? {vec_chaos.is_chaotic} | Helmholtz Free Energy: {vec_chaos.helmholtz_free_energy:.4f}")


async def test_integration(fluid, chaos):
    print("\n[ETAPA 3] INTEGRAÇÃO PARALELA (Bypass de Latência HFT)")
    
    results = await asyncio.gather(
        fluid.extract_fluid_tensors(np.ones(50, dtype=np.float32), 10.5),
        chaos.compute_lyapunov_thermodynamics(np.random.normal(0, 0.01, 120).astype(np.float32), 0.8)
    )
    
    print("✅ Reação Conjunta Async = SUCESSO")
    print(f"   ↳ [Fluid] Kinetic Energy: {results[0].kinetic_sweep_energy:.3f}")
    print(f"   ↳ [Chaos] Stochastic Resonance: {results[1].stochastic_resonance_ratio:.3f}")

async def main():
    print("=" * 60)
    print(" SOLÉNN v2 - BOOTING NEURAL TESTS (FLUID DYNAMICS + CHAOS THERMO CLUSTER)")
    print("=" * 60)
    
    fluid = SolennFluidDynamics()
    chaos = SolennChaosThermodynamics()
    
    await test_vitality(fluid, chaos)
    await test_cognition(fluid, chaos)
    await test_integration(fluid, chaos)

if __name__ == "__main__":
    asyncio.run(main())
