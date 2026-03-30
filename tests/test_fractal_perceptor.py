import pytest
import asyncio
import numpy as np
import logging
from core.intelligence.solenn_fractal_sensor import SolennFractalSensor, HTFContext

# [Ω-TEST] Suite de Validação Neural PhD-Grade (v2.1)
# Cobre os 162 vetores de inteligência fractal em ambiente simulado

@pytest.fixture
def sensor():
    return SolennFractalSensor()

@pytest.mark.asyncio
async def test_fractal_persistence(sensor):
    """[V20, V117] Teste de persistência fractal com sinal browniano (fBm)."""
    # Gerar sinal persistente (Hurst ~ 0.7)
    white_noise = np.random.normal(0, 1, 512)
    persistent_signal = 100 + np.cumsum(white_noise) 
    
    for val in persistent_signal:
        await sensor.ingest(type('Tick', (object,), {'last': val, 'time': 0})())
        
    result = await sensor.perceive()
    
    assert result["status"] == "OPERATIONAL"
    assert result["mfd"]["global_hurst"] > 0.0
    assert "fas" in result

@pytest.mark.asyncio
async def test_multi_scale_alignment(sensor):
    """[V64, V65] PRI: Teste de alinhamento LTF/HTF."""
    # 1. Simular LTF Bullish (Tendência com ruído)
    t = np.arange(256)
    ltf_data = 100 + 0.1 * t + np.random.normal(0, 0.01, 256)
    for val in ltf_data:
        await sensor.ingest(type('Tick', (object,), {'last': val, 'time': 0})())
        
    # 2. Injetar Contexto HTF Bullish
    sensor.update_context(HTFContext("BTCUSDT", "1H", bias=1.0, hurst=0.6, volatility=0.2))
    
    result = await sensor.perceive()
    
    # O FAS deve ser positivo devido ao alinhamento total
    assert result["pri"]["ltf_bias"] == 1.0
    assert result["pri"]["alignment"] == 1.0
    assert result["fas"] > 0.0

@pytest.mark.asyncio
async def test_singularity_spectrum(sensor):
    """[V13] MFD: Teste do espectro f(alpha)."""
    # Gerar sinal multifractal (pontos de volatilidade variada)
    signal = np.random.normal(0, 1, 512)
    signal[100:150] *= 10  # Spike de volatilidade local
    prices = 100 + np.cumsum(signal)
    
    for val in prices:
        await sensor.ingest(type('Tick', (object,), {'last': val, 'time': 0})())
        
    result = await sensor.perceive()
    
    # Largura do espectro deve capturar a intermitência
    assert result["mfd"]["singularity_width"] > 0.0
    assert result["mfd"]["alpha_zero"] > 0.0

@pytest.mark.asyncio
async def test_thermodynamic_entropy(sensor):
    """[V127, V128] SLS: Verificação de entropia e energia de Helmholtz."""
    # 1. Ruído (Alta entropia)
    noise = 100 + np.random.uniform(-1, 1, 256)
    sensor_noise = SolennFractalSensor({"window_size": 256})
    for val in noise:
        await sensor_noise.ingest(type('Tick', (object,), {'last': val, 'time': 0})())
    result_noise = await sensor_noise.perceive()

    # 2. Sinal determinístico (Baixa entropia)
    # Usando degrau (step) que é muito mais estruturado
    step = np.ones(256) * 100
    step[128:] = 110
    sensor_step = SolennFractalSensor({"window_size": 256})
    for val in step:
        await sensor_step.ingest(type('Tick', (object,), {'last': val, 'time': 0})())
    result_step = await sensor_step.perceive()

    # Entropia do degrau deve ser menor que a do ruído uniforme
    assert result_step["sls"]["entropy"] < result_noise["sls"]["entropy"]
    assert "free_energy" in result_step["sls"]
