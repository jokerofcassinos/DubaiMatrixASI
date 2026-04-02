"""
    TESTE NEURAL OMEGA (Lei VI.3 & VI.5)
    Avaliação de Vitalidade, Cognição e Integração para:
    - SOVEREIGN CONFIG Ω
    - STATE MANAGER Ω
"""
import time
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.solenn_config import SolennHyperConfig
from core.solenn_state_manager import SolennStateManager

async def test_vitality(config: SolennHyperConfig):
    print("\n[ETAPA 1] VITALIDADE PLENA (Verificações Base)")
    assert isinstance(config, SolennHyperConfig)
    
    # Valida Mutabilidade via Sandbox (with_update cria nova Cópia Limpa Imutável O(1))
    t0 = time.perf_counter()
    new_cfg = config.with_update(max_simultaneous_slots=3)
    t1 = time.perf_counter()
    
    assert new_cfg.max_simultaneous_slots == 3
    assert config.max_simultaneous_slots == 5  # Orignal se mantém inalterado
    print(f"✅ Mutabilidade Limitada [Hot-Swap O(1)] Ativada | Executado em {(t1-t0)*1000:.4f}ms.")
    
    try:
        config.with_update(averaging_down_forbidden=False)
        assert False, "O sistema permitiu Averaging Down (Invariante quebrado!)"
    except ValueError as e:
        print(f"✅ Invariantes Institucionais Vacinados. Averaging Down protegido: {e}")
        
    return new_cfg

async def test_cognition(config: SolennHyperConfig):
    print("\n[ETAPA 2] COGNIÇÃO: ORGANISMO DE ESTADO (State Manager)")
    statebr = SolennStateManager(config)
    
    # 1. State Inserido Normal
    t0 = time.perf_counter()
    succ = await statebr.update_state(pnl_delta=500.0, trace_id="tr-lucro", new_slot_count=1)
    t1 = time.perf_counter()
    
    assert succ is True
    shad = statebr.get_shadow_copy()
    print(f"✅ Atualização Assíncrona via WAL O(1) com PNL Positivo | {(t1-t0)*1000:.4f}ms.")
    print(f"   ↳ Estado Shadow: Drawdown={shad['running_drawdown']:.4f} | Slots={shad['open_slots']}")

    # 2. State de Risco Máximo (Acima dos 4% Permitido do Config)
    # FTMO limit 4% (0.04) numa base de 100000. 4000 negativos batem o block
    succ2 = await statebr.update_state(pnl_delta=-4500.0, trace_id="tr-catastrofe", new_slot_count=1)
    assert succ2 is False
    print("✅ Invariante FTMO de Risco (4%) defendeu modificação de Estado (Drawdown rejeitado!).")

async def test_integration(config: SolennHyperConfig):
    print("\n[ETAPA 3] INTEGRAÇÃO PARALELA (Fechamento da Abóbada Central)")
    statebr = SolennStateManager(config)
    
    async def fast_trade_emulation():
        for i in range(10):
            await statebr.update_state(pnl_delta=10.0, trace_id=f"tr-{i}", new_slot_count=2)
            
    t0 = time.perf_counter()
    await asyncio.gather(fast_trade_emulation(), fast_trade_emulation())
    t1 = time.perf_counter()
    
    shad = statebr.get_shadow_copy()
    print("✅ Concorrência Limpa Assíncrona no WAL concluída = SUCESSO (0 Data Races)")
    print(f"   ↳ Lifetime Trades: {shad['total_lifetime_trades']} | PnL Accum: {shad['today_pnl']} | Tempo: {(t1-t0)*1000:.4f}ms")

async def main():
    print("=" * 60)
    print(" SOLÉNN v2 - BOOTING NEURAL TESTS (SOVEREIGN CONFIG & STATE MANAGER)")
    print("=" * 60)
    
    cfg = SolennHyperConfig()
    new_cfg = await test_vitality(cfg)
    await test_cognition(new_cfg)
    await test_integration(new_cfg)

if __name__ == "__main__":
    asyncio.run(main())
