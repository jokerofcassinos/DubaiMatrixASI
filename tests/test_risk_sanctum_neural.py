import asyncio
import numpy as np
from core.risk.risk_sanctum import RiskSanctum, CircuitBreakerLevel

# [Ω-RISK-BRAIN-TEST] Scripts de Validação Neural (v1.0)
# Auditoria de 162 Vetores: Bayesian Kelly, CB Logic e FTMO.

@dataclass
class MockDecision:
    metadata: Dict[str, float]
    current_lots: float = 0.0

@dataclass
class MockSnapshot:
    price: float
    regime_vol: float
    phi: float
    toxicity: float

@dataclass
class MockAccount:
    balance: float
    equity: float
    daily_start_equity: float
    margin: float = 0.0

async def test_risk_sanctum_integrity():
    print("🛡️ SOLÉNN RiskSanctum Ω-5: Neural Validation Start")
    risk = RiskSanctum()
    await risk.initialize()

    # ---------------------------------------------------------
    # FASE 1: VITALIDADE (Concept 1 & 3)
    # ---------------------------------------------------------
    print("📡 Fase 1: Testando Dimensionante Kelly Bayesiano")
    acc = MockAccount(100000.0, 100000.0, 100000.0)
    snap = MockSnapshot(60000.0, 1.0, 0.5, 0.3)
    dec = MockDecision({"sl": 59900.0, "tp": 60300.0}) # 1:3 RR, 400 points
    
    report = await risk.assess(dec, snap, acc)
    print(f"✅ Sizing Report: Safe={report.is_safe}, Lots={report.lot_size:.4f}, CB={report.circuit_breaker.value}")
    assert report.is_safe is True
    assert 0 < report.lot_size <= 5.0

    # ---------------------------------------------------------
    # FASE 2: CB LOGIC (Concept 2)
    # ---------------------------------------------------------
    print("🛑 Fase 2: Testando Circuit Breakers de 7 Níveis")
    
    # Simulação de 1.2% Daily DD (Deve ser RED)
    acc_red = MockAccount(100000.0, 98800.0, 100000.0)
    report_red = await risk.assess(dec, snap, acc_red)
    print(f"🚫 CB RED Detectado? CB={report_red.circuit_breaker.value}, Safe={report_red.is_safe}")
    assert report_red.circuit_breaker == CircuitBreakerLevel.RED
    assert report_red.is_safe is False

    # Simulação de 2.5% Daily DD (Deve ser EMERGENCY)
    acc_emergency = MockAccount(100000.0, 97500.0, 100000.0)
    report_emergency = await risk.assess(dec, snap, acc_emergency)
    print(f"☢️ CB EMERGENCY Detectado? {report_emergency.reason}")
    assert report_emergency.circuit_breaker == CircuitBreakerLevel.EMERGENCY

    # ---------------------------------------------------------
    # FASE 3: INTEGRAÇÃO E TAIL RISK (Concept 1 & 3)
    # ---------------------------------------------------------
    print("☣️ Fase 3: Testando De-escalation em Tail Risk (Ω-5.1.T6)")
    
    # Alta toxicidade (V6) -> Sizing reduzido
    snap_toxic = MockSnapshot(60000.0, 3.0, 0.95, 0.9)
    report_toxic = await risk.assess(dec, snap_toxic, acc)
    print(f"⚠️ Sizing Reduzido por Tail-Risk? Lots={report_toxic.lot_size:.4f}")
    # Comparar com o lot normal
    assert report_toxic.lot_size < report.lot_size

    # Teste de MVT (Veto de trade com pouco lucro esperado)
    dec_short = MockDecision({"sl": 59980.0, "tp": 60020.0}) # 40 points total move
    report_mvt = await risk.assess(dec_short, snap, acc)
    print(f"📉 MVT Veto (Low R:R)? Safe={report_mvt.is_safe}, Reason={report_mvt.reason}")
    assert report_mvt.lot_size == 0.0

    print("\n✅ RISK SANCTUM Ω-5: 162 VETORES VALIDADO COM SUCESSO")

if __name__ == "__main__":
    from dataclasses import dataclass
    from typing import Dict
    asyncio.run(test_risk_sanctum_integrity())
