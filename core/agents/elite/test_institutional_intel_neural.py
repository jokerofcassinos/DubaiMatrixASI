"""
    TESTE NEURAL OMEGA (Lei VI.3 & VI.5)
    Avaliação de Vitalidade, Cognição e Integração para:
    - SOLÉNN INSTITUTIONAL STRUCTURE Ω
    - SOLÉNN SPOOF HUNTER Ω
    - SOLÉNN GAME THEORY Ω
"""
import time
import numpy as np
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from core.agents.elite.solenn_institutional_structure import SolennInstitutionalStructure
from core.agents.elite.solenn_spoof_hunter import SolennSpoofHunter
from core.agents.elite.solenn_game_theory import SolennGameTheory

async def test_vitality(inst, spoof, game):
    print("\n[ETAPA 1] VITALIDADE PLENA (7+ Verificações de Base)")
    
    assert isinstance(inst, SolennInstitutionalStructure)
    assert isinstance(spoof, SolennSpoofHunter)
    assert isinstance(game, SolennGameTheory)
    print("✅ Instanciação dos 3 Agentes de Caça e Estrutura Institucional = OK")
    
    assert inst.bullish_ob_array.shape == (50,)
    print("✅ Institutional: Depth Array Vectorizado (Float32)")
    
    assert spoof.limit_book_bid.shape == (20,)
    assert spoof.short_term_spoof_memory.shape == (300,)
    print("✅ SpoofHunter: Arrays LDOM e Ring Buffers Purgativos alocados.")
    
    assert game.class_probabilities.shape == (4,)
    print("✅ GameTheory: Array Class Probabilities (HFT, MM, Sardinhas) ativo.")

async def test_cognition(inst, spoof, game):
    print("\n[ETAPA 2] COGNIÇÃO: INSTITUCIONAL & CONTRA-INTELIGÊNCIA")
    
    # 1. Inst Structure
    t0 = time.perf_counter()
    vec_inst = await inst.compute_structural_bias(60000.0, 0.05)
    t1 = time.perf_counter()
    print(f"✅ Institutional SMC: FVG Gravitacional computado em {(t1-t0)*1000:.4f}ms. Is Mitigated? {vec_inst.is_mitigated}")
    
    # 2. Spoof Hunter
    dom = np.array([1200, 50, 10, 10, 5], dtype=np.float32)
    trades = np.array([1.0, 0.5, 0.1, 15.0], dtype=np.float32) # Injeção de 15 lots de repente
    t0 = time.perf_counter()
    vec_spoof = await spoof.scan_dark_pools_and_spoof(dom, trades)
    t1 = time.perf_counter()
    print(f"✅ Spoof Hunter LDOM: Executado em {(t1-t0)*1000:.4f}ms. Spoof detectado? {vec_spoof.is_spoofed}. Predator Injected? {bool(vec_spoof.predator_bias)}")
    
    # 3. Game Theory
    pain = np.array([0.1, 0.5, 0.9, 0.95], dtype=np.float32) # Dor aumentando até topo do array
    t0 = time.perf_counter()
    vec_game = await game.compute_nash_equilibrium(pain)
    t1 = time.perf_counter()
    print(f"✅ Game Theory HJB: Resolvido em {(t1-t0)*1000:.4f}ms. Optimal Action: {vec_game.optimal_reaction} (Pain>0.8=Fade Retail)")


async def test_integration(inst, spoof, game):
    print("\n[ETAPA 3] INTEGRAÇÃO PARALELA E BYPASS (Teoria dos Jogos)")
    
    results = await asyncio.gather(
        inst.compute_structural_bias(61000.0, 0.5),
        spoof.scan_dark_pools_and_spoof(np.array([2000, 10], dtype=np.float32), np.array([0.1, 0.1, 25.0], dtype=np.float32)),
        game.compute_nash_equilibrium(np.array([0.4, 0.45, 0.88], dtype=np.float32))
    )
    
    print("✅ Reação Conjunta Async = SUCESSO")
    print(f"   ↳ [SMC] FVG Pull: {results[0].fvg_gravitational_pull:.3f}")
    print(f"   ↳ [Spoof] Fake Wall? {results[1].is_spoofed}")
    print(f"   ↳ [Game Theory] Pooling Equilibrium: {results[2].is_pooling_equilibrium}")

async def main():
    print("=" * 60)
    print(" SOLÉNN v2 - BOOTING NEURAL TESTS (INSTITUTIONAL + COUNTER-INTEL CLUSTER)")
    print("=" * 60)
    
    inst = SolennInstitutionalStructure()
    spoof = SolennSpoofHunter()
    game = SolennGameTheory()
    
    await test_vitality(inst, spoof, game)
    await test_cognition(inst, spoof, game)
    await test_integration(inst, spoof, game)

if __name__ == "__main__":
    asyncio.run(main())
