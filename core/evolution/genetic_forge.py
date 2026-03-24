"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — GENETIC FORGE (HNP)                    ║
║                                                                              ║
║  O Forjador Genético. Calcula o Peso Sináptico de cada agente baseado no     ║
║  histórico Bayesiano do agente para o Vetor de Estado (Perfil) atual.        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
from typing import Dict, List
from utils.logger import log
from config.settings import DATA_DIR

class GeneticForge:
    def __init__(self, data_path=None):
        self.data_path = data_path or os.path.join(DATA_DIR, "evolution", "synaptic_weights.json")
        self.profiles = {}
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.data_path):
                with open(self.data_path, "r", encoding="utf-8") as f:
                    self.profiles = json.load(f)
                log.omega(f"🧬 [GENETIC FORGE] Carregado! Operando com {len(self.profiles)} Perfis de DNA.")
            else:
                self.profiles = {}
        except Exception as e:
            log.warning(f"⚠️ Erro ao carregar Genetic Forge: {e}")
            self.profiles = {}

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump(self.profiles, f, indent=4)
        except Exception as e:
            log.warning(f"⚠️ Erro ao salvar Genetic Forge: {e}")

    def register_trade_outcome(self, state_vector_hash: str, trade_action: str, is_win: bool, bulls: List[str], bears: List[str]):
        """
        Registra se o agente acertou ou errou na previsão, dentro do contexto do State Vector.
        """
        if state_vector_hash not in self.profiles:
            self.profiles[state_vector_hash] = {}

        profile = self.profiles[state_vector_hash]

        # Quem votou certo?
        correct_group = []
        incorrect_group = []

        if trade_action == "BUY":
            correct_group, incorrect_group = (bulls, bears) if is_win else (bears, bulls)
        elif trade_action == "SELL":
            correct_group, incorrect_group = (bears, bulls) if is_win else (bulls, bears)

        # Registra acertos
        for agent in correct_group:
            if agent not in profile:
                profile[agent] = {"hits": 0, "misses": 0, "is_pandemic": False}
            profile[agent]["hits"] += 1

        # Registra erros
        for agent in incorrect_group:
            if agent not in profile:
                profile[agent] = {"hits": 0, "misses": 0, "is_pandemic": False}
            profile[agent]["misses"] += 1

        self._save()

    def get_synaptic_weight(self, agent_name: str, state_vector_hash: str, default_weight=1.0) -> float:
        """
        Calcula o multiplicador de atenção Bayesiano (Holographic Routing).
        """
        if state_vector_hash not in self.profiles or agent_name not in self.profiles[state_vector_hash]:
            return default_weight

        data = self.profiles[state_vector_hash][agent_name]
        hits = data.get("hits", 0)
        misses = data.get("misses", 0)
        total = hits + misses

        # Warmup phase
        if total < 3:
            return default_weight

        wr_raw = hits / total
        
        # O Multiplicador será 0.1 (Silenciado) até 2.0 (Dominante)
        if wr_raw > 0.70:
            multiplier = 2.0
        elif wr_raw > 0.55:
            multiplier = 1.2
        elif wr_raw < 0.35:
            multiplier = 0.1
        elif wr_raw < 0.45:
            multiplier = 0.5
        else:
            multiplier = 1.0

        # Pandemic Autopromotion
        if data.get("is_pandemic", False) and total >= 15 and wr_raw > 0.65:
            data["is_pandemic"] = False
            log.omega(f"🔥 [PANDEMIC PROMOTION] Agente {agent_name} atingiu {wr_raw*100:.1f}% WinRate. Adicionado à Matrix Real Money!")
            self._save()

        return multiplier

# Singleton Global
GENETIC_FORGE = GeneticForge()
