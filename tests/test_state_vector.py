import pytest
from dataclasses import dataclass
from core.evolution.state_vector import StateVectorEngine, StateVectorData

@dataclass
class MockSnapshot:
    """Mock do snapshot de mercado p/ teste de discretização."""
    timestamp: float = 0.0
    regime: str = "TREND_UP"
    atr: float = 40.0
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {
                "tick_velocity": 5.0,
                "shannon_entropy": 4.0
            }

class TestStateVector:
    """
    Protocolo de Validação Neural 3-6-9 (162 Vetores)
    """

    @pytest.fixture
    def engine(self):
        return StateVectorEngine()

    # =========================================================================
    # FASE 1: DISCRETIZAÇÃO (CONCEITO 1) - Ω-10
    # =========================================================================

    def test_basic_discretization_normal(self, engine):
        """V1: Teste de discretização básica (Condições Normais)."""
        # Base: 2024-03-31 02:00:00 UTC = 1711850400
        snapshot = MockSnapshot(timestamp=1711850400 * 1000)
        state = engine.discretize(snapshot)
        
        assert isinstance(state, StateVectorData)
        assert state.session == "T_ASIAN"
        assert state.regime == "R_TREND"
        assert state.velocity == "V_MED"
        assert state.entropy == "E_COMPLEX"
        assert state.volatility == "VOL_NORMAL"
        assert "|" in state.profile_hash

    def test_session_london_ny(self, engine):
        """V3-V4: Teste de transição de sessões Londres/NY."""
        # Base: 2024-03-31 00:00:00 UTC = 1711843200
        base_ts = 1711843200 * 1000 # ms
        
        # 10:00 UTC -> Londres
        s_london = MockSnapshot(timestamp=base_ts + (10 * 3600 * 1000))
        state_l = engine.discretize(s_london)
        assert state_l.session == "T_LONDON"
        
        # 16:00 UTC -> NY
        s_ny = MockSnapshot(timestamp=base_ts + (16 * 3600 * 1000))
        state_ny = engine.discretize(s_ny)
        assert state_ny.session == "T_NY"

    def test_entropy_ordered_chaotic(self, engine):
        """V29-V31: Filtro de entropia Shannon."""
        s_low = MockSnapshot(metadata={"shannon_entropy": 1.5, "tick_velocity": 1.0})
        state_l = engine.discretize(s_low)
        assert state_l.entropy == "E_ORDERED"
        
        s_high = MockSnapshot(metadata={"shannon_entropy": 7.5, "tick_velocity": 1.0})
        state_h = engine.discretize(s_high)
        assert state_h.entropy == "E_CHAOTIC"

    def test_hft_burst_velocity(self, engine):
        """V20: Detecção de Burst de velocidade HFT."""
        s_burst = MockSnapshot(metadata={"tick_velocity": 25.0, "shannon_entropy": 3.0})
        state = engine.discretize(s_burst)
        assert state.velocity == "V_HFT_BURST"

    # =========================================================================
    # FASE 2: HASHING TOPOLÓGICO (CONCEITO 2) - Ω-43
    # =========================================================================

    def test_deterministic_hash(self, engine):
        """V60: Garantia da imutabilidade e determinismo do Hash."""
        # 02:00 UTC -> T_ASIAN
        base_ts = 1711843200 * 1000 # 2024-03-31 00:00:00
        snapshot = MockSnapshot(timestamp=base_ts + (2 * 3600 * 1000))
        
        state1 = engine.discretize(snapshot)
        state2 = engine.discretize(snapshot)
        
        # Snapshots idênticos DEVEM produzir hashes idênticos
        assert state1.profile_hash == state2.profile_hash
        assert state1.profile_hash == "T_ASIAN|R_TREND|V_MED|E_COMPLEX|VOL_NORMAL"
