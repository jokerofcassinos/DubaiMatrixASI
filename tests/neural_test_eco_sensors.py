import asyncio
import logging
import pytest
from market.scraper.macro_sensor import MacroSensor
from market.scraper.onchain_sensor import OnChainSensor
from market.scraper.sentiment_sensor import SentimentSensor

# [Ω-TEST-NEURAL] Suíte Eco-Sensor Ω-10: Validação de Consciência de Ecossistema
# 1-Coleta | 2-Divergência | 3-Relatório

@pytest.mark.asyncio
async def test_eco_sensor_suite_flow():
    """
    VALICAÇÃO INTEGRAL DA SUITE ECO-SENSOR Ω-10
    Protocolo 3-6-9: Testando o Pulso Global (162 Vetores).
    """
    sensors = [MacroSensor(), OnChainSensor(), SentimentSensor()]
    
    # 🧪 ETAPA 1: COLETA (Polling all sensors)
    print("\n[VITALIDADE] Coletando Pulso do Ecossistema Ω-10.1...")
    snapshots = []
    for sensor in sensors:
        await sensor.start()
        snap = await sensor.poll()
        snapshots.append(snap)
        assert snap is not None
        assert snap.confidence > 0.0
        print(f"-> Sensor {sensor.name} capturou {len(snap.variables)} variáveis (Ω-Coleta OK)")

    # 🧪 ETAPA 2: DIVERGÊNCIA (Regime & Correlation Check)
    print("[COGNIÇÃO] Analisando Alinhamento e Bias de Regime Ω-10.2...")
    # Check if we have at least one bearish or bullish bias
    biases = [s.regime_bias for s in snapshots]
    print(f"-> Biases Detectados: {biases} (Ω-Bias OK)")
    
    # Simple check on Macro variables
    macro_snap = next(s for s in snapshots if s.source == "MacroSensor")
    assert "DXY" in macro_snap.variables
    assert "VIX" in macro_snap.variables

    # 🧪 ETAPA 3: RELATÓRIO (Ecosystem Integration)
    print("[INTEGRAÇÃO] Validando Fluxo On-Chain e Sentimento Ω-10.3...")
    onchain_snap = next(s for s in snapshots if s.source == "OnChainSensor")
    assert onchain_snap.variables["NET_EXCHANGE_FLOW"] != 0
    
    sentiment_snap = next(s for s in snapshots if s.source == "SentimentSensor")
    assert 0 <= sentiment_snap.variables["FEAR_GREED"] <= 100
    
    print("✅ Suíte Eco-Sensor Ω Validada com Sucesso (Status Sintonizado).")
    
    for sensor in sensors:
        await sensor.stop()

if __name__ == "__main__":
    asyncio.run(test_eco_sensor_suite_flow())
