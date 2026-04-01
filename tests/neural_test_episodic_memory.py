import asyncio
import logging
import pytest
from market.memory.episodic_memory import EpisodicMemory, Episode

# [Ω-TEST-NEURAL] Memória Episódica Ω-35: Validação de Anti-Amnésia
# 1-Gravação | 2-Forense | 3-Recuperação

@pytest.mark.asyncio
async def test_episodic_memory_flow():
    """
    VALICAÇÃO INTEGRAL DA MEMÓRIA EPISÓDICA Ω-35
    Protocolo 3-6-9: Testando o Grafo de Experiência (162 Vetores).
    """
    memory = EpisodicMemory()
    await memory.initialize()
    
    # 🧪 ETAPA 1: GRAVAÇÃO (Recording Intent)
    print("\n[VITALIDADE] Gravando Intenção de Trade Ω-35.1...")
    context = {"regime": "TRENDING_UP", "vol": 0.05}
    intent = {"action": "BUY", "target": 66000.0}
    ep_id = await memory.record_intent(context, intent)
    assert ep_id.startswith("EP_")
    assert len(memory._short_term_buffer) == 1

    # 🧪 ETAPA 2: FORENSE (Post-Mortem of Loss)
    print("[COGNIÇÃO] Testando Análise Forense de Perda (Bug P0) Ω-35.2...")
    outcome = {"pnl": -0.005, "exit_price": 64900.0}
    await memory.record_outcome(ep_id, outcome)
    
    # Check if forensic was triggered (Importance should be > 1.0)
    episode = memory._short_term_buffer[0]
    assert episode.importance > 1.0*1.5 # Incremented by outcome AND forensic
    assert episode.lesson is not None
    print(f"-> Lição Extraída da Perda: {episode.lesson} (Ω-Forense OK)")

    # 🧪 ETAPA 3: RECUPERAÇÃO (Semantic Search)
    print("[INTEGRAÇÃO] Testando Recuperação por Analogia Ω-35.3...")
    current_context = {"regime": "TRENDING_UP"}
    analogous = await memory.find_analogous(current_context)
    assert len(analogous) >= 1
    assert "TRENDING_UP" in analogous[0].tags
    print(f"-> Episódios Análogos Encontrados: {len(analogous)} (Ω-Sincronia OK)")
    print("✅ Memória Episódica Ω Validada com Sucesso (Status Anti-Amnésia).")

if __name__ == "__main__":
    asyncio.run(test_episodic_memory_flow())
