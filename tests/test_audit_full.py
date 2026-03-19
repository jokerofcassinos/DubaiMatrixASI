
import os
import sys
import time
from datetime import datetime
from dataclasses import dataclass
from typing import Any

# Root path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.audit_engine import AUDIT_ENGINE
from utils.logger import log

@dataclass
class MockAction:
    value: str

@dataclass
class MockDecision:
    action: Any
    signal_strength: float = 0.85
    confidence: float = 0.92
    reasoning: str = "OMEGA TEST: High Prob Convergence"
    regime: str = "TRENDING_BULL"
    lot_size: float = 0.1
    entry_price: float = 65000.0
    stop_loss: float = 64800.0
    take_profit: float = 65500.0

@dataclass
class MockSnapshot:
    price: float = 65000.0
    atr: float = 150.0
    metadata: Any = None

def run_full_audit_test():
    """
    [Ω-TEST] Test complete Audit Lifecycle: Start -> Buffer -> End (Exit)
    """
    log.omega("🚀 INICIANDO TESTE DE AUDITORIA COMPLETA (Post-Mortem)...")
    
    # 1. Setup Mocks
    ticket = 999999
    decision = MockDecision(action=MockAction(value="BUY"))
    snapshot = MockSnapshot(metadata={"phi_last": 0.42, "kl_divergence": 0.15})
    
    # 2. Trigger Start Audit
    log.info("Step 1: Disparando START_AUDIT (Entry)...")
    AUDIT_ENGINE.start_audit(ticket, decision, snapshot)
    
    # 3. Simulate System Activity (Fill Log Buffer)
    log.info("Step 2: Simulando atividade para o Log Buffer...")
    for i in range(5):
        log.omega(f"🧬 [OMEGA-GENOME] Analisando sequência #{i+1}...")
        log.signal(f"💫 Sinal detectado: {0.8 + i/100:.3f}")
        time.sleep(0.5)
    
    # 4. Trigger End Audit
    log.info("Step 3: Disparando END_AUDIT (Exit)...")
    result = {
        "status": "SUCCESS",
        "profit": 150.0,
        "pnl_pct": 0.23,
        "exit_price": 65150.0,
        "reason": "TAKE_PROFIT HITS"
    }
    AUDIT_ENGINE.end_audit(ticket, result)
    
    # 5. Verify Results
    log.omega("📋 VERIFICANDO RESULTADOS...")
    date_folder = datetime.now().strftime("%Y-%m-%d")
    audit_base = os.path.join("audits", date_folder)
    
    if os.path.exists(audit_base):
        # List and sort by modification time to get the latest
        folders = [os.path.join(audit_base, f) for f in os.listdir(audit_base) if f"Trade_{ticket}" in f]
        folders.sort(key=os.path.getmtime, reverse=True)
        
        if folders:
            fpath = folders[0]
            log.omega(f"✅ Pasta de audit encontrada: {fpath}")
            
            files = os.listdir(fpath)
            expected = ["lifecycle_context.json", "terminal_logs.txt", "entry_screenshot.png", "exit_screenshot.png"]
            for exp in expected:
                if exp in files:
                    log.info(f"   - Arquivo ok: {exp}")
                else:
                    log.warning(f"   - ⚠️ Arquivo FALTANDO: {exp}")
            
            # Show absolute path for the user
            abs_path = os.path.abspath(fpath)
            print(f"\n[AUDIT_LINK]: {abs_path}")
        else:
            log.error("❌ Pasta de audit NÃO encontrada para o ticket 999999.")
    else:
        log.error("❌ Direitório de audits não existe.")

if __name__ == "__main__":
    run_full_audit_test()
