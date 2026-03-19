import os
import time
import json
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, List

# Mocking parts of the system for standalone test
class Action(Enum):
    BUY = "BUY"
    SELL = "SELL"
    WAIT = "WAIT"

@dataclass
class Decision:
    action: Action
    confidence: float
    signal_strength: float
    entry_price: float
    stop_loss: float
    take_profit: float
    lot_size: float
    regime: str
    reasoning: str
    metadata: Dict[str, Any]

@dataclass
class MarketSnapshot:
    price: float
    atr: float
    metadata: Dict[str, Any]

def test_audit_fix():
    print("🧠 [DIAGNOSTICO] Testando Fix de Auditoria (Strike-ID & Metadata)...")
    
    from utils.audit_engine import AUDIT_ENGINE
    from execution.trade_registry import registry as trade_registry
    
    # 1. Simular Decisão com Metadados PhD
    decision = Decision(
        action=Action.BUY,
        confidence=0.95,
        signal_strength=0.8,
        entry_price=50000.0,
        stop_loss=49500.0,
        take_profit=51000.0,
        lot_size=0.1,
        regime="TRENDING_BULL",
        reasoning="Teste de Auditoria PhD",
        metadata={
            "quantum_metadata": {
                "bull_agents": ["RiemannianRicci", "NavierStokes", "BlackSwanEVT"],
                "bear_agents": [],
                "neutral_agents": ["MarketIntuition"]
            }
        }
    )
    
    snapshot = MarketSnapshot(
        price=50000.0,
        atr=250.0,
        metadata={"phi_last": 0.65, "kl_divergence": 0.12}
    )
    
    # 2. Simular Hydra Strike (3 slots)
    strike_id = f"TEST_STRIKE_{int(time.time())}"
    tickets = [123001, 123002, 123003]
    
    print(f"🚀 Iniciando Strike Hydra: {strike_id}...")
    for t in tickets:
        # Registrar intenção
        trade_registry.register_intent(
            ticket=t,
            intent=decision,
            snapshot=snapshot,
            position_id=t,
            strike_id=strike_id
        )
        # Iniciar Auditoria
        AUDIT_ENGINE.start_audit(ticket=t, decision=decision, snapshot=snapshot, strike_id=strike_id)
        
    # Verificar se apenas uma pasta foi criada
    date_str = time.strftime("%Y-%m-%d")
    audit_base = os.path.join("audits", date_str)
    
    folders = [f for f in os.listdir(audit_base) if strike_id in f]
    print(f"📁 Pastas encontradas com Strike ID: {len(folders)}")
    if len(folders) != 1:
        print(f"❌ ERRO: Esperava 1 pasta, encontrei {len(folders)}")
    else:
        print(f"✅ SUCESSO: Apenas 1 pasta criada para o strike.")
        
    # Verificar metadados JSON
    audit_dir = os.path.join(audit_base, folders[0])
    json_path = os.path.join(audit_dir, "lifecycle_context.json")
    
    with open(json_path, 'r') as f:
        data = json.load(f)
        swarm = data.get("swarm_intelligence", {})
        print(f"🔍 Swarm Metadata: Bull={len(swarm.get('bull_agents', []))}, Bear={len(swarm.get('bear_agents', []))}")
        
    # 3. Simular Fechamento (Exit)
    print("🏁 Simulando fechamento de um ticket do strike...")
    # Recuperar strike_id do registry (como o PositionManager faz)
    intent_data = trade_registry.get_intent(position_id=tickets[0])
    s_id_recovered = intent_data.get("strike_id")
    
    AUDIT_ENGINE.end_audit(
        ticket=tickets[0], 
        result={"ticket": tickets[0], "profit": 150.0, "success": True},
        strike_id=s_id_recovered
    )
    
    # Verificar se a pasta foi renomeada e contém logs/exit_screenshot
    final_folders = [f for f in os.listdir(audit_base) if strike_id in f and "PROFIT_150" in f]
    if final_folders:
        print(f"✅ SUCESSO: Pasta renomeada corretamente: {final_folders[0]}")
        final_dir = os.path.join(audit_base, final_folders[0])
        files = os.listdir(final_dir)
        print(f"📄 Arquivos na pasta final: {files}")
        if "terminal_logs.txt" in files and "exit_screenshot.png" in files:
            print("✅ SUCESSO: Logs e Screenshot de saída capturados.")
        else:
            print("❌ ERRO: Faltam logs ou screenshot de saída.")
    else:
        print("❌ ERRO: Pasta não foi renomeada ou não encontrada após end_audit.")

if __name__ == "__main__":
    test_audit_fix()
