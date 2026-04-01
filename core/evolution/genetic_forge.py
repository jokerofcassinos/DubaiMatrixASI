import asyncio
import time
import logging
import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

from core.intelligence.base_synapse import BaseSynapse
from config.settings import DATA_DIR

# Configuração de Logger ASI-Grade
log = logging.getLogger("SOLENN.GeneticForge")

@dataclass
class AgentDNA:
    """Perfil de Performance Genética de um Agente (Ω-7)."""
    name: str
    hits: int = 0
    misses: int = 0
    consecutive_losses: int = 0
    last_trade_time: float = 0.0
    tier: int = 2 # 1: Live Dominant, 2: Shadow/Standard
    regime_performance: Dict[str, Dict[str, int]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def win_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.5

class GeneticForge(BaseSynapse):
    """
    Ω-7, Ω-31, Ω-39 & Ω-40: O Coração Darwiniano da SOLÉNN.
    
    Gerencia a evolução de agentes, calcula pesos sinápticos via Holographic Routing
    e promove agentes baseados em performance real.
    """
    
    def __init__(self):
        super().__init__("GeneticForge")
        self.dna_path = os.path.join(DATA_DIR, "evolution", "agent_dna.json")
        self.profiles: Dict[str, AgentDNA] = {}
        self._ensure_dirs()
        self._load_dna()
        
    def _ensure_dirs(self):
        os.makedirs(os.path.dirname(self.dna_path), exist_ok=True)

    def _load_dna(self):
        """V18: Recuperação pós-reboot."""
        try:
            if os.path.exists(self.dna_path):
                with open(self.dna_path, "r") as f:
                    data = json.load(f)
                    for name, profile_data in data.items():
                        self.profiles[name] = AgentDNA(**profile_data)
                log.info(f"🧬 [Ω-FORGE] {len(self.profiles)} Perfis de DNA carregados.")
        except Exception as e:
            log.error(f"❌ Erro ao carregar DNA: {e}")

    def _save_dna(self):
        """Persistência imutável do progresso evolutivo."""
        try:
            data = {name: asdict(dna) for name, dna in self.profiles.items()}
            with open(self.dna_path, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            log.error(f"❌ Erro ao salvar DNA: {e}")

    # =========================================================================
    # CONCEITO 1: SYNAPTIC WEIGHTING (Ω-7, Ω-31)
    # =========================================================================

    def register_outcome(self, agent_name: str, is_win: bool, regime: str = "UNKNOWN"):
        """
        V1-V9: Atribuição de crédito por trade e aprendizado online.
        """
        if agent_name not in self.profiles:
            self.profiles[agent_name] = AgentDNA(name=agent_name)
            
        dna = self.profiles[agent_name]
        
        # 1. Update Global
        if is_win:
            dna.hits += 1
            dna.consecutive_losses = 0
        else:
            dna.misses += 1
            dna.consecutive_losses += 1
            
        # 2. Update por Regime (V10)
        if regime not in dna.regime_performance:
            dna.regime_performance[regime] = {"hits": 0, "misses": 0}
        
        if is_win:
            dna.regime_performance[regime]["hits"] += 1
        else:
            dna.regime_performance[regime]["misses"] += 1
            
        dna.last_trade_time = time.time()
        
        # 3. Verificação de Promoção/De-escalação (V55-V81)
        self._check_evolution_stage(dna)
        self._save_dna()

    def get_synaptic_weight(self, agent_name: str, current_regime: str = "UNKNOWN") -> float:
        """
        V19-V27: Holographic Routing - Cálculo do Multiplicador de Atenção.
        """
        if agent_name not in self.profiles:
            return 1.0 # Peso padrão para novos agentes
            
        dna = self.profiles[agent_name]
        total = dna.hits + dna.misses
        
        # Warmup phase (V6)
        if total < 5: return 1.0
        
        # Peso Base por Win Rate Global
        wr = dna.win_rate
        weight = 1.0
        
        # V20: Silenciamento de agentes ruidosos
        if wr < 0.45 or dna.consecutive_losses >= 3:
            weight = 0.1
        # V21: Amplificação de Dominância
        elif wr > 0.65:
            weight = 1.5 if dna.tier == 2 else 2.0
            
        # V10: Ajuste por Regime Específico
        regime_data = dna.regime_performance.get(current_regime, {"hits": 0, "misses": 0})
        regime_total = regime_data["hits"] + regime_data["misses"]
        
        if regime_total >= 3:
            regime_wr = regime_data["hits"] / regime_total
            if regime_wr > 0.7: weight *= 1.2
            if regime_wr < 0.4: weight *= 0.5
            
        return round(max(0.1, min(2.5, weight)), 2)

    # =========================================================================
    # CONCEITO 2: EVOLUTIONARY PROMOTION (Ω-39, Ω-40)
    # =========================================================================

    def _check_evolution_stage(self, dna: AgentDNA):
        """
        V55-V81: Lógica de Promoção e De-escalação automática.
        """
        total = dna.hits + dna.misses
        wr = dna.win_rate
        
        # Promoção para Tier 1 (V58)
        if dna.tier == 2 and total >= 30 and wr >= 0.70:
            dna.tier = 1
            log.info(f"🔥 [Ω-FORGE] PROMOÇÃO: Agente {dna.name} promovido ao TIER 1 (Live Dominant).")
            
        # De-escalação por fadiga (V75)
        if dna.tier == 1 and (wr < 0.55 or dna.consecutive_losses >= 5):
            dna.tier = 2
            log.warning(f"❄️ [Ω-FORGE] DE-ESCALAÇÃO: Agente {dna.name} rebaixado ao Tier 2 por Fadiga/Performance.")

    async def process(self, snapshot: Any, nexus_context: Any = None) -> Dict[str, Any]:
        """
        [Ω-EXEC] Sync evolutivo.
        """
        return {
            "node": self.name,
            "active_profiles": len(self.profiles),
            "tier_1_agents": [dna.name for dna in self.profiles.values() if dna.tier == 1],
            "status": "DYNAMICAL"
        }

# Módulo Solenn Genetic Forge Ω (v2) inicializado.
# Forjando a inteligência através da seleção natural financeira.
