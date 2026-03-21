"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — OMEGA PARAMETERS                      ║
║        Parâmetros dinâmicos auto-ajustados pela consciência da ASI          ║
║                                                                              ║
║  ESTES PARÂMETROS SÃO VIVOS — a ASI os modifica em tempo real.              ║
║  Cada parâmetro tem um valor atual, bounds de segurança, e histórico.       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import os
import threading
from datetime import datetime
from typing import Optional, Dict, Any
from config.settings import STATE_DIR, EVOLUTION_BOUNDS


class OmegaParameter:
    """
    Um parâmetro Omega — vivo, mutável, com memória.
    A ASI pode ajustá-lo dentro dos bounds de segurança.
    """

    def __init__(self, name: str, value: float, min_bound: float, max_bound: float,
                 description: str = ""):
        self.name = name
        self._value = value
        self.default = value
        self.min_bound = min_bound
        self.max_bound = max_bound
        self.description = description
        self.mutation_history = []  # [(timestamp, old_val, new_val, reason)]

    @property
    def value(self):
        return self._value

    @property
    def min_val(self):
        return self.min_bound

    @property
    def max_val(self):
        return self.max_bound

    @value.setter
    def value(self, new_val):
        """Setter com bounds enforcement — a ASI NÃO pode se auto-destruir."""
        clamped = max(self.min_bound, min(self.max_bound, new_val))
        if clamped != self._value:
            self.mutation_history.append({
                "time": datetime.now().isoformat(),
                "old": self._value,
                "new": clamped,
            })
            # Manter apenas últimas 100 mutações
            if len(self.mutation_history) > 100:
                self.mutation_history = self.mutation_history[-100:]
        self._value = clamped

    def mutate(self, new_val: float, reason: str = ""):
        """Mutação com razão registrada — para auditoria da ASI."""
        old_val = self._value
        self.value = new_val  # Usa o setter com bounds
        if self.mutation_history:
            self.mutation_history[-1]["reason"] = reason
        return old_val, self._value

    def reset(self):
        """Reset para o valor default."""
        self._value = self.default

    def to_dict(self):
        return {
            "name": self.name,
            "value": self._value,
            "default": self.default,
            "bounds": [self.min_bound, self.max_bound],
            "mutations": len(self.mutation_history),
        }

    def __repr__(self):
        return f"Ω({self.name}={self._value:.4f} [{self.min_bound}, {self.max_bound}])"


class OmegaParameterSpace:
    """
    Espaço de todos os parâmetros Omega da ASI.
    Thread-safe. Persistente. Auto-documentado.
    """

    PERSIST_FILE = os.path.join(STATE_DIR, "omega_params.json")

    def __init__(self):
        self._lock = threading.Lock()
        self._params = {}
        self._initialize_parameters()

    def _initialize_parameters(self):
        """Inicializa todos os parâmetros Omega com valores default."""

        # ═══ DECISION PARAMETERS ═══
        self._register("buy_threshold", 0.15, 0.05, 0.95,
                        "Score mínimo para decisão BUY")
        self._register("sell_threshold", -0.15, -0.95, -0.05,
                        "Score mínimo para decisão SELL (negativo)")
        self._register("confidence_min", 0.55, 0.10, 0.95,
                        "Confiança mínima para executar trade")
        self._register("convergence_threshold", 0.40, 0.20, 0.95,
                        "% de agentes que devem concordar")
        self._register("trinity_min_rr_ratio", 1.2, 0.8, 2.5,
                        "RR Ratio mínimo no TrinityCore")
        self._register("mc_min_score", -0.35, -0.80, 0.50,
                        "Score mínimo do Monte Carlo para aprovar trade")
        self._register("mc_min_win_prob", 0.32, 0.20, 0.55,
                        "Win Probability mínima do Monte Carlo")

        # ═══ RISK PARAMETERS ═══
        self._register("position_size_pct", 50.0, 0.5, 75.0,
                        "% do saldo por posição")
        self._register("kelly_fraction", 1.0, 0.10, 1.00,
                        "Fração do Kelly Criterion")
                        
        # [Phase Ω-10] QUANTUM KELLY PDF-SIZING
        self._register("pdf_sizing_steepness", 3.5, 1.0, 10.0,
                        "Inclinação da expansão geométrica da densidade de risco")
        self._register("pdf_max_kelly_multiplier", 5.0, 1.0, 20.0,
                        "Teto máximo de expansão do Kelly (God-Mode / Convergence)")
        self._register("pdf_micro_lot_threshold", 0.15, 0.05, 0.50,
                        "Limite de densidade p/ ativar Lot normal vs Micro-Lot")

        # ═══ QUANTUM TWAP PARAMS (PHASE Ω-13) ═══
        self._register("twap_lot_threshold", 1.5, 0.5, 5.0,
                        "Tamanho de lote mínimo para desativar a Hydra e disparar o TWAP Assíncrono")
        self._register("twap_duration_sec", 6.0, 2.0, 30.0,
                        "Duração alvo (em segundos) que a fragmentação TWAP levará para limpar passivo")
        self._register("twap_max_chunk", 0.3, 0.05, 1.0,
                        "Maior fatia permitida (MAX_CHUNK) por milissegundo pelo TWAP")
        self._register("stop_loss_atr_mult", 1.50, 0.1, 5.0,
                        "Multiplicador ATR para stop loss")
        self._register("take_profit_atr_mult", 2.50, 0.3, 10.0,
                        "Multiplicador ATR para take profit")
        self._register("trailing_stop_atr_mult", 0.6, 0.2, 2.0,
                        "Multiplicador ATR para trailing stop")
        self._register("commission_per_lot", 50.0, 0.0, 150.0,
                        "Comissão estimada por lote (Round Turn, $) - Ajustado p/ FTMO BTCUSD ($50.0)")
        self._register("min_profit_per_ticket", 35.0, 5.0, 200.0,
                        "Lucro líquido mínimo exigido por ordem/ticket ($) - Alvo de lucro real")
        self._register("min_commission_reward_ratio", 1.8, 1.0, 10.0,
                        "Ratio mínimo entre Lucro Projetado e Comissão estimada")
        self._register("commission_protection_mult", 1.5, 1.1, 5.0,
                        "Multiplicador de cobertura de comissão para Smart TP")
        self._register("margin_safety_buffer", 0.10, 0.01, 0.50,
                        "Percentual de margem livre mantido como reserva (0.10 = 10%)")

        # ═══ NRO (NEURAL RISK ORCHESTRATION) ═══
        self._register("nro_manifold_sensitivity", 1.25, 0.5, 3.0,
                        "Sensibilidade à curvatura do manifold para expansão de risco")
        self._register("nro_coherence_weight", 0.85, 0.2, 1.5,
                        "Peso da coerência do enxame na modulação de lot size")

        # ═══ QUANTUM PARAMETERS ═══
        self._register("quantum_collapse_threshold", 0.80, 0.60, 0.95,
                        "Threshold de colapso do estado quântico")
        self._register("quantum_interference_weight", 0.5, 0.1, 1.0,
                        "Peso da interferência quântica entre agentes")
        self._register("superposition_decay", 0.95, 0.80, 0.99,
                        "Taxa de decaimento de superposição")

        # ═══ REGIME PARAMETERS ═══
        self._register("regime_sensitivity", 0.30, 0.10, 0.70,
                        "Sensibilidade a mudanças de regime")
        self._register("paradigm_shift_threshold", 0.95, 0.50, 2.0,
                        "Threshold de KL Divergence p/ travar motor (Menor = Mais sensível)")
        self._register("climax_velocity_threshold", 2.2, 1.5, 6.0,
                        "Múltiplo de ATR M5 p/ Veto de Clímax (Menor = Mais protetor)")
        self._register("trend_regime_aggression", 1.2, 0.5, 2.0,
                        "Multiplicador de agressividade em regime trending")
        self._register("range_regime_aggression", 0.7, 0.3, 1.5,
                        "Multiplicador de agressividade em regime ranging")
        self._register("chaos_regime_aggression", 0.3, 0.1, 0.8,
                        "Multiplicador de agressividade em regime caótico")

        # ═══ PHASE 22 & 23: CONVICTION & SMART TP PARAMETERS ═══
        self._register("high_conviction_multiplier", 10.0, 1.0, 50.0,
                        "Multiplicador do Lot Size quando Coerência > 0.8 e Confiança > 0.8")
        self._register("smart_tp_micro_reversal_buffer", 20.0, 5.0, 100.0,
                        "Buffer de lucro ($) para ativar saída agressiva por reversão de delta (Reduzido p/ Agilidade)")
        self._register("smart_tp_lock_threshold_low", 0.25, 0.05, 0.50,
                        "Drawdown de lucro permitido p/ gains < $10 (0.25 = 25% max evaporação)")
        self._register("smart_tp_lock_threshold_mid", 0.15, 0.05, 0.40,
                        "Drawdown de lucro permitido p/ gains < $50 (0.15 = 15% max evaporação)")
        self._register("smart_tp_lock_threshold_high", 0.10, 0.01, 0.30,
                        "Drawdown de lucro permitido p/ gains > $50 (0.10 = 10% max evaporação)")
        self._register("tp_placement_scalar", 0.97, 0.80, 1.0,
                        "Escalar para encurtar o TP e garantir execução (0.97 = 97% do TP original)")
        self._register("proximity_trailing_threshold", 0.90, 0.70, 0.98,
                        "Threshold de proximidade do TP para ativar trailing agressivo")
        self._register("proximity_lock_threshold", 0.05, 0.01, 0.15,
                        "Drawdown de lucro permitido na zona de proximidade do TP")


        # ═══ AGENT WEIGHT DEFAULTS ═══
        self._register("weight_trend", 1.0, 0.1, 3.0,
                        "Peso do agente de tendência")
        self._register("weight_momentum", 1.0, 0.1, 3.0,
                        "Peso do agente de momentum")
        self._register("weight_topological", 3.8, 1.0, 8.0,
                        "Peso do agente de Homologia Persistente (Betti Holes)")
        self._register("weight_spoof_hunter", 2.2, 1.0, 5.0,
                        "Peso do agente caçador de Market Makers (Spoof Variance)")
        self._register("spoof_velocity_threshold", 30.0, 10.0, 100.0,
                        "Ticks por segundo mínimos para investigar Spoofing")
        self._register("spoof_variance_threshold", 0.40, 0.10, 0.90,
                        "Variância de imbalance mínima para confirmar Fake Wall")
        self._register("weight_volume", 0.8, 0.1, 3.0,
                        "Peso do agente de volume")
        self._register("weight_pattern", 0.7, 0.1, 3.0,
                        "Peso do agente de padrões")
        self._register("weight_volatility", 1.1, 0.1, 3.0,
                        "Peso do agente de volatilidade (Normalizado Phase 47)")
        self._register("weight_microstructure", 1.2, 0.1, 3.0,
                        "Peso do agente de microestrutura")
        self._register("weight_sentiment", 0.5, 0.1, 2.0,
                        "Peso do agente de sentimento")
        self._register("weight_statistical", 0.8, 0.1, 3.0,
                        "Peso do agente estatístico")
        self._register("weight_fractal", 0.6, 0.1, 2.0,
                        "Peso do agente fractal")
        self._register("weight_correlation", 0.5, 0.1, 2.0,
                        "Peso do agente de correlação")

        # ═══ EXECUTION PARAMETERS ═══
        self._register("max_spread_points", 5000.0, 30.0, 10000.0,
                        "Spread máximo aceito em points brutos")
        self._register("max_spread_reward_impact", 0.25, 0.05, 0.50,
                        "Impacto max do spread no lucro (0.25 = max 25% do TP devorado pelo spread)")
        self._register("max_spread_atr_impact", 0.25, 0.05, 0.50,
                        "Impacto max do spread na volatilidade (0.25 = max 25% do ATR)")
        self._register("entry_urgency", 0.5, 0.1, 1.0,
                        "Urgência de entrada (1.0 = market order sempre)")
        self._register("startup_cooldown_seconds", 120.0, 10.0, 600.0,
                        "Cooldown de imersão inicial da ASI após o boot")

        # ═══ ANTI-METRALHADORA PARAMETERS ═══
        self._register("entry_cooldown_seconds", 60.0, 10.0, 300.0,
                        "Cooldown mínimo (segundos) entre entradas consecutivas")
        self._register("min_entry_distance_atr", 0.7, 0.1, 3.0,
                        "Distância mínima da última entrada em múltiplos de ATR")
        self._register("duplicate_position_distance_atr", 1.0, 0.3, 5.0,
                        "Distância mínima de posição existente na mesma direção em ATR")
        self._register("max_order_splits", 5.0, 1.0, 15.0,
                        "Número máximo de fragmentações de ordem (Nós P-Brane). Capped p/ HFT.")
        self._register("kinematic_exhaustion_atr_mult", 1.8, 1.0, 3.5,
                        "Distância máxima de estiramento em 5 velas antes da reversão")

        # ═══ PHASE 46: SUPERPOSITION RESOLUTION PARAMETERS ═══
        self._register("superposition_resolution_enabled", 1.0, 0.0, 1.0,
                        "Habilita a resolução ativa de superposição (agentes não convergentes)")
        self._register("resolution_confidence_multiplier", 1.2, 1.0, 2.0,
                        "Multiplicador de confiança durante a resolução de superposição")
        self._register("institutional_superiority_threshold", 0.75, 0.50, 0.95,
                        "Threshold de coerência institucional para ISO (Institutional Superiority Override)")
        self._register("temporal_tunneling_cycles", 5.0, 3.0, 20.0,
                        "Número de ciclos para validar bias direcional persistente")
        self._register("max_resolution_entropy", 0.65, 0.30, 0.90,
                        "Máxima entropia permitida para tentar resolução (EPA)")

        # ═══ PHASE 40: ZERO-DRAWDOWN CITADEL ═══
        self._register("exposure_ceiling_balance_ratio", 500.0, 100.0, 5000.0,
                        "Ratio de balanço por lote (ex: 500 = 1 lot a cada $500).")
        self._register("v_reversal_atr_multiplier", 3.0, 2.0, 6.0,
                        "Multiplicador de ATR para detectar Climax e asfixiar risco.")

        # ═══ PHASE Ω-EXTREME: LORENTZ, PHI, QCA, EVT ═══
        self._register("phi_min_threshold", 0.070, 0.050, 0.5,
                        "Nível mínimo de Integração de Informação (Φ) para permitir trade (Reset p/ Sanidade)")
        self._register("phi_hydra_threshold", 4.50, 1.50, 10.0,
                        "Threshold de Φ para ativar HYDRA MODE (Convergência Máxima)")
        self._register("hydra_min_phi_threshold", 0.25, 0.05, 0.95,
                        "Nível mínimo de Φ necessário para autorizar HYDRA MODE (Phase Ω-Coherence)")
        self._register("unknown_regime_phi_gate", 0.04, 0.05, 0.50,
                        "Nível mínimo de Φ necessário para autorizar trades em regime UNKNOWN (Phase Ω-Coherence)")
        self._register("lorentz_dilation_enabled", 1.0, 0.0, 1.0,
                        "Habilita a dilatação temporal relativística do loop de consciência")
        self._register("evt_tail_threshold", 2.50, 2.0, 5.0,
                        "Threshold de cauda (EVT) para detecção de Black Swan")

        # ═══ PHASE Ω-SINGULARITY: P-BRANE LIMIT EXECUTION ═══
        self._register("limit_execution_mode", 1.0, 0.0, 1.0,
                        "Habilita execução via Limit Orders (Maker) em regimes de drift")
        self._register("p_brane_jitter_offset_points", 0.0, -100.0, 100.0,
                        "Offset em points para posicionamento da P-Brane na extremidade do spread")

        # ═══ PHASE 50: OMEGA-SINGULARITY & RESONANCE ═══
        self._register("phi_resonance_threshold", 0.85, 0.70, 0.98,
                        "Threshold de Φ (PHI) para ativar Quantum Resonance Ignition")
        self._register("pnl_relaxed_mode", 1.0, 0.0, 1.0,
                        "Habilita modo RELAXED (redução de veto PnL)")
        self._register("drift_aggression_mult", 1.15, 0.30, 2.0,
                        "Multiplicador de agressividade em regime DRIFTING/CREEPING")
        self._register("god_mode_entropy_threshold", 0.89, 0.80, 0.99,
                        "Threshold de Entropia para God-Mode Reversal")

        # ═══ PHASE 51: Ω-ALPHA SURGE (ALPHA EXTRACTION) ═══
        self._register("kinematic_v_pulse_relaxation", 2.5, 1.0, 5.0,
                        "Multiplicador de relaxação ATR durante V-Pulse/Ignition")
        self._register("t_cell_distance_threshold", 1.5, 0.5, 3.5,
                        "Distância de Mahalanobis mínima p/ Veto T-Cell (Menor = Mais sensível)")
        self._register("ignition_sovereignty_mult", 0.40, 0.1, 1.0,
                        "Multiplicador de soberania da ignição (reduz thresholds de veto)")
        self._register("god_mode_rr_min", 0.35, 0.1, 1.5,
                        "RR Ratio mínimo reduzido para God-Mode Reversal (Panic Absorption)")

        # ═══ PHASE 52: FAT-TAIL HARVESTING & LEVY FLIGHTS ═══
        self._register("fat_tail_rr_mult", 4.5, 2.0, 15.0,
                        "Multiplicador agressivo de Take Profit para eventos de cauda (Reduzido p/ Scalp)")
        self._register("levy_flight_kurtosis_threshold", 5.0, 2.0, 15.0,
                        "Excesso de curtose necessário para aprovar Voo de Lévy e expansão Fat-Tail")
                        
        # ═══ PHASE 53: PANGALACTIC (SQUEEZE ANTICIPATION) ═══
        self._register("vpin_toxicity_limit", 0.75, 0.50, 0.95,
                        "Nível de toxicidade no Order Flow (VPIN) para decretar Flash Crash / Squeeze")
        self._register("fisher_critical_collapse", 0.05, 0.01, 0.15,
                        "Limiar estatístico para atestar colapso termo-dinâmico da informação paramétrica")

        # ═══ PHASE Ω-THERMODYNAMIC (AGI TRANSITION) ═══
        self._register("friston_surprise_threshold", 3.0, 1.5, 6.0,
                        "Limiar de Energia Livre (Erro Preditivo) para decretar Paradigm Shift institucional")

        # ═══ Ω-PhD-7/8/9: TOPOLOGICAL & ALGORITHMIC SOVEREIGNTY ═══
        self._register("ricci_k_threshold", 2.5, 1.0, 5.0,
                        "Threshold de curvatura Ricci p/ atrator topológico")
        self._register("kinetic_velocity_floor", 2.0, 0.5, 10.0,
                        "Velocidade mínima de ticks p/ evitar Veto de Exaustão (Reset Ω-PhD-Next)")

        self._register("kl_velocity_threshold", 1.2, 0.5, 3.5,
                        "Mínima aceleração de KL Divergence p/ Veto de Paradigm Shift instável")
        self._register("lie_symmetry_threshold", 0.1, 0.01, 1.0,
                        "Variância máxima p/ simetria de Lie (Iceberg detection)")
        self._register("kolmogorov_ratio_threshold", 0.40, 0.20, 0.80,
                        "Threshold de compressão p/ fluxo programático")
        self._register("quantum_tunneling_threshold", 0.65, 0.30, 0.95,
                        "Probabilidade mínima p/ Ghost Entry (Tunneling)")
        self._register("kolmogorov_compression_ratio", 0.35, 0.1, 0.6,
                        "Ratio de compressão algorítmica de fluxo para detectar robôs institucionais limpos")
        self._register("prigogine_entropy_saturation", 0.94, 0.70, 0.98,
                        "Saturação entrópica indicando falência de estrutura dissipativa (Bifurcação Climática)")
        self._register("ghost_absorption_threshold", 0.85, 0.50, 0.99,
                        "Pressão de limiar para inferir falsa barreira (Ghost Order / Iceberg Absorption)")
        self._register("drift_aggression_mult", 1.25, 1.0, 3.0,
                        "Multiplicador agressivo ao negociar contra falso suporte em Drift")
        
        # ═══ PHASE Ω-PhD-4: INFORMATION GEOMETRY & PHASE TRANSITIONS ═══

        self._register("entropy_convergence_threshold", 0.002, 0.0005, 0.01,
                        "Variância máxima do sinal (Entropy Bridge) p/ confirmar convergência de informação")
        self._register("structural_expectancy_sizing_enabled", 1.0, 0.0, 1.0,
                        "Habilita o Ghost-Veto via lot_size=0 baseado na expectância do JAVA PnL Predictor")

        # ═══ PHASE Ω-PhD-5: THE SINGULARITY PIVOT ═══
        self._register("creep_maturity_threshold", 150.0, 50.0, 500.0,
                        "Número de barras para decretar maturidade (vencimento) de regime CREEPING")


        # ═══ PHASE Ω-PhD-6: TOPOLOGICAL ENTROPY COLLAPSE (TEC) ═══
        self._register("tec_sensitivity", 0.40, 0.10, 0.80,
                        "Threshold de queda na entropia (topológica/shannon) para detectar colapso estrutural")
        self._register("tec_min_v_pulse", 0.30, 0.05, 0.90,
                        "Energia mínima (V-Pulse) necessária para confirmar Ressonância de Singularidade")

        # ═══ PHASE Ω-EPISTEMIC SINGULARITY (PhD Evolution) ═══
        self._register("weight_quantum_tunneling", 1.25, 0.1, 3.5,
                        "Peso do agente Quantum Tunneling Oscillator")
        self._register("max_tp_stretch_atr", 10.0, 1.0, 25.0,
                        "Máximo alongamento de TP (em ATR) para cobrir o Alpha Floor")
        self._register("phi_ignorance_threshold", 0.15, 0.05, 0.30,
                        "Nível de Φ abaixo do qual a microestrutura ignora o macro (Soberania do Presente)")
        self._register("phi_symmetry_guard_enabled", 0.0, 0.0, 1.0,
                        "[Phase Ω-Extreme] Ativa proteção contra divergência extrema enxame/sinal")
        self._register("exhaustion_signal_min", 0.40, 0.35, 0.95,
                        "[Phase Ω-Extreme] Elevado de 0.35 para 0.40 para evitar falsos positivos (Calibração Scalp)")
        self._register("v_pulse_alpha_relaxation", 0.50, 0.1, 1.0,
                        "Multiplicador de redução do Alpha Floor durante V-Pulse (0.50 = 50% de desconto)")

        # ═══ PHASE Ω-EXIT: DYNAMIC TREND PERSISTENCE ═══
        self._register("smart_tp_phi_relaxation_mult", 0.5, 0.1, 2.0,
                        "Multiplicador de relaxação do Profit Lock baseado no nível de Φ (Consciência)")
        self._register("trend_persistence_buffer", 2.0, 1.0, 5.0,
                        "Multiplicador de persistência temporal em tendências confirmadas")


    def _register(self, name: str, value: float, min_b: float, max_b: float,
                  desc: str = ""):
        self._params[name] = OmegaParameter(name, value, min_b, max_b, desc)

    @property
    def params(self):
        """Retorna dicionário interno de parâmetros."""
        return self._params

    def to_dict(self):
        """Retorna dicionário simples nome:valor."""
        with self._lock:
            return {name: p.value for name, p in self._params.items()}

    def get(self, name: str, default: Optional[float] = None) -> float:
        """Obtém valor de um parâmetro Omega."""
        with self._lock:
            if name in self._params:
                return self._params[name].value
            if default is not None:
                return default
            raise KeyError(f"[OMEGA] Parâmetro desconhecido: {name}")

    def set(self, name: str, value: float, reason: str = ""):
        """Define valor de um parâmetro Omega (com bounds enforcement)."""
        with self._lock:
            if name in self._params:
                old, new = self._params[name].mutate(value, reason)
                return old, new
            raise KeyError(f"[OMEGA] Parâmetro desconhecido: {name}")

    def get_all(self) -> dict:
        """Retorna snapshot de todos os parâmetros."""
        with self._lock:
            return {name: p.to_dict() for name, p in self._params.items()}

    def reset_all(self):
        """Reset de todos os parâmetros para defaults."""
        with self._lock:
            for p in self._params.values():
                p.reset()

    def save(self):
        """Persiste parâmetros Omega no disco."""
        with self._lock:
            data = {
                "saved_at": datetime.now().isoformat(),
                "parameters": {
                    name: {
                        "value": p.value,
                        "default": p.default,
                        "bounds": [p.min_bound, p.max_bound],
                        "mutation_count": len(p.mutation_history),
                        "last_mutations": p.mutation_history[-5:],
                    }
                    for name, p in self._params.items()
                }
            }
        with open(self.PERSIST_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def load(self) -> bool:
        """Carrega parâmetros Omega do disco (se existirem)."""
        if not os.path.exists(self.PERSIST_FILE):
            return False
        try:
            with open(self.PERSIST_FILE, "r") as f:
                data = json.load(f)
            with self._lock:
                for name, pdata in data.get("parameters", {}).items():
                    if name in self._params:
                        self._params[name].value = pdata.get("value", self._params[name].default)
            return True
        except (json.JSONDecodeError, KeyError):
            return False

    def __repr__(self):
        return f"OmegaParameterSpace({len(self._params)} params)"


# ═══════════════════════════════════════════════════════════════
#  INSTÂNCIA GLOBAL — Singleton da ASI
# ═══════════════════════════════════════════════════════════════
OMEGA = OmegaParameterSpace()
