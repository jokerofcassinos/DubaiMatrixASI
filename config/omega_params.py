import json
import os
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional

from config.settings import DATA_DIR

log = logging.getLogger("SOLENN.OmegaParams")

@dataclass
class OmegaParameter:
    """Representação de um Parâmetro Ômega (Ω-12)."""
    name: str
    value: float
    min_val: float
    max_val: float
    description: str = ""
    is_critical: bool = False

class OmegaParams:
    """
    Ω-12: Gerenciador de Parâmetros de Ordem Superior.
    
    Implementa travas de segurança (Sanity Clamps) e persistência imutável.
    """
    
    def __init__(self):
        self.params_path = os.path.join(DATA_DIR, "config", "omega_params.json")
        self.params: Dict[str, OmegaParameter] = {}
        self._initialize_defaults()
        self._load()

    def _initialize_defaults(self):
        """V1: Inicializa os parâmetros fundamentais (v2.3.1)."""
        defaults = [
            # Sensores e Thresholds (Ω-1.viii)
            OmegaParameter("phi_min_threshold", 0.25, 0.10, 0.60, "Threshold mínimo de Φ para ativação de sinal", True),
            OmegaParameter("confidence_min", 0.65, 0.40, 0.95, "Confiança mínima requerida para execução", True),
            OmegaParameter("hurst_momentum_threshold", 0.55, 0.45, 0.75, "Expoente de Hurst mínimo para Trend Following"),
            
            # Gestão de Risco (Ω-5)
            OmegaParameter("position_size_pct", 5.0, 0.1, 75.0, "Percentual de alocação por trade", True),
            OmegaParameter("max_drawdown_limit", 2.0, 0.5, 5.0, "Limite de Drawdown para Circuit Breaker", True),
            
            # Execução (Ω-6)
            OmegaParameter("max_order_splits", 3, 1, 15, "Fragmentação máxima de ordens", True),
            OmegaParameter("take_profit_points", 300, 50, 1500, "Alvo de lucro padrão (BTCUSD points)"),
            OmegaParameter("stop_loss_points", 150, 50, 800, "Limite de perda padrão (BTCUSD points)"),
        ]
        for p in defaults:
            self.params[p.name] = p

    def _load(self):
        try:
            if os.path.exists(self.params_path):
                with open(self.params_path, "r") as f:
                    data = json.load(f)
                    for name, val in data.items():
                        if name in self.params:
                            self.params[name].value = val
                log.info(f"⚙️ [Ω-PARAMS] {len(data)} Parâmetros carregados.")
        except Exception as e:
            log.error(f"❌ Erro ao carregar Parâmetros: {e}")

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.params_path), exist_ok=True)
            data = {name: p.value for name, p in self.params.items()}
            with open(self.params_path, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            log.error(f"❌ Erro ao salvar Parâmetros: {e}")

    def get(self, name: str) -> float:
        return self.params[name].value if name in self.params else 0.0

    def set(self, name: str, value: float):
        """V63: OMEGA.set Bounds Gateway (Sanity Clamp)."""
        if name not in self.params:
            log.warning(f"⚠️ Tentativa de setar parâmetro inexistente: {name}")
            return
            
        param = self.params[name]
        # Aplicação de Clamps (V55-V61)
        clamped_value = max(param.min_val, min(param.max_val, value))
        
        if clamped_value != value:
            log.debug(f"🛠️ [CLAMP] {name} ajustado de {value} para {clamped_value}")
            
        param.value = clamped_value

    def to_dict(self) -> Dict[str, float]:
        return {name: p.value for name, p in self.params.items()}

# Singleton Global OMEGA
OMEGA = OmegaParams()
