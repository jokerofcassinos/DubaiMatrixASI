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
        self._register("buy_threshold", 0.20, 0.05, 0.95,
                        "Score mínimo para decisão BUY")
        self._register("sell_threshold", -0.20, -0.95, -0.05,
                        "Score mínimo para decisão SELL (negativo)")
        self._register("confidence_min", 0.70, 0.10, 0.95,
                        "Confiança mínima para executar trade")
        self._register("convergence_threshold", 0.40, 0.20, 0.95,
                        "% de agentes que devem concordar")
        self._register("trinity_min_rr_ratio", 1.1, 0.5, 5.0,
                        "RR Ratio mínimo no TrinityCore")
        self._register("mc_min_score", -0.35, -0.80, 0.50,
                        "Score mínimo do Monte Carlo para aprovar trade")
        self._register("mc_min_win_prob", 0.40, 0.25, 0.70,
                        "Win Probability mínima do Monte Carlo")

        # ═══ RISK PARAMETERS ═══
        self._register("position_size_pct", 50.0, 0.5, 75.0,
                        "% do saldo por posição")
        self._register("kelly_fraction", 1.0, 0.10, 1.00,
                        "Fração do Kelly Criterion")
        self._register("stop_loss_atr_mult", 2.0, 1.0, 5.0,
                        "Multiplicador ATR para stop loss")
        self._register("take_profit_atr_mult", 3.0, 1.5, 8.0,
                        "Multiplicador ATR para take profit")
        self._register("trailing_stop_atr_mult", 1.5, 0.5, 3.0,
                        "Multiplicador ATR para trailing stop")

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
        self._register("trend_regime_aggression", 1.2, 0.5, 2.0,
                        "Multiplicador de agressividade em regime trending")
        self._register("range_regime_aggression", 0.7, 0.3, 1.5,
                        "Multiplicador de agressividade em regime ranging")
        self._register("chaos_regime_aggression", 0.3, 0.1, 0.8,
                        "Multiplicador de agressividade em regime caótico")

        # ═══ PHASE 22 & 23: CONVICTION & SMART TP PARAMETERS ═══
        self._register("high_conviction_multiplier", 15.0, 1.0, 30.0,
                        "Multiplicador do Lot Size quando Coerência > 0.8 e Confiança > 0.8")
        self._register("smart_tp_micro_reversal_buffer", 15.0, 5.0, 50.0,
                        "Buffer de lucro ($) onde ignoramos exaustões de baixo impacto (limpa traps)")


        # ═══ AGENT WEIGHT DEFAULTS ═══
        self._register("weight_trend", 1.0, 0.1, 3.0,
                        "Peso do agente de tendência")
        self._register("weight_momentum", 1.0, 0.1, 3.0,
                        "Peso do agente de momentum")
        self._register("weight_volume", 0.8, 0.1, 3.0,
                        "Peso do agente de volume")
        self._register("weight_pattern", 0.7, 0.1, 3.0,
                        "Peso do agente de padrões")
        self._register("weight_volatility", 0.9, 0.1, 3.0,
                        "Peso do agente de volatilidade")
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
        self._register("min_entry_distance_atr", 0.3, 0.1, 3.0,
                        "Distância mínima da última entrada em múltiplos de ATR")
        self._register("duplicate_position_distance_atr", 1.0, 0.3, 5.0,
                        "Distância mínima de posição existente na mesma direção em ATR")
        self._register("max_order_splits", 20.0, 1.0, 100.0,
                        "Máximo de slots por execução")
        self._register("kinematic_exhaustion_atr_mult", 1.8, 1.0, 3.5,
                        "Distância máxima de estiramento em 5 velas antes da reversão")

        # ═══ PHASE 40: ZERO-DRAWDOWN CITADEL ═══
        self._register("exposure_ceiling_balance_ratio", 500.0, 100.0, 5000.0,
                        "Ratio de balanço por lote (ex: 500 = 1 lot a cada $500).")
        self._register("v_reversal_atr_multiplier", 3.0, 2.0, 6.0,
                        "Multiplicador de ATR para detectar Climax e asfixiar risco.")

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
