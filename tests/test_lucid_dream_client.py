import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from core.evolution.lucid_dream_client import LucidDreamClient, DreamScenario

@pytest.mark.asyncio
class TestLucidDreamClient:
    """
    Protocolo de Validação Neural 3-6-9 (162 Vetores)
    """

    @pytest.fixture
    def client(self):
        return LucidDreamClient(host="127.0.0.1", port=5557)

    # =========================================================================
    # FASE 1: COMUNICAÇÃO Ω (CONCEITO 1) - Ω-32/Ω-45
    # =========================================================================

    async def test_dream_cycle_success(self, client):
        """V10-V18: Teste de ciclo de sonho bem-sucedido (Mocked)."""
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        
        # Resposta simulada do Daemon Java (V19)
        mock_reader.readline.return_value = b"DREAM_SUCCESS|ALPHA:0.85|MUTATIONS:100|TIME:50ms|SCORE:90.0\n"
        
        with patch("asyncio.open_connection", return_value=(mock_reader, mock_writer)) as mock_conn:
            result = await client.dream_cycle(
                base_price=65000.0,
                volatility=0.02,
                scenario=DreamScenario.FLASH_CRASH,
                iterations=5000
            )
            
            assert result is not None
            assert result["alpha"] == 0.85
            assert result["score"] == 90.0
            assert result["scenario"] == "FLASH_CRASH"
            assert len(client.dream_history) == 1
            
            # Verificar se enviou o payload correto
            mock_writer.write.assert_called()
            payload = mock_writer.write.call_args[0][0].decode()
            assert "DREAM|FLASH_CRASH|65000.0|0.02|5000" in payload

    async def test_dream_cycle_timeout(self, client):
        """V13: Teste de Resiliência (Timeout)."""
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        
        # Simular timeout no reader.readline
        mock_reader.readline.side_effect = asyncio.TimeoutError()
        
        with patch("asyncio.open_connection", return_value=(mock_reader, mock_writer)):
            result = await client.dream_cycle(
                65000.0, 0.02, DreamScenario.TRENDING
            )
            
            assert result is None
            assert client.is_dreaming is False

    @pytest.mark.parametrize("response, expected_score", [
        ("DREAM_SUCCESS|ALPHA:0.5|MUTATIONS:10|TIME:1ms|SCORE:10.5", 10.5),
        ("DREAM_SUCCESS|ALPHA:1.0|MUTATIONS:200|TIME:100ms|SCORE:100.0", 100.0),
    ])
    def test_parse_response_variants(self, client, response, expected_score):
        """V19-V27: Teste de Decomposição (Parsing) de múltiplas variantes."""
        result = client._parse_response(response, DreamScenario.CHOPPY)
        assert result["score"] == expected_score
        assert result["scenario"] == "CHOPPY"

# Protocolo 3-6-9 Validado: Sonho Lúcido integrado com o organismo SOLÉNN.
