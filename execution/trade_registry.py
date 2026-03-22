"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                DUBAI MATRIX ASI — TRADE INTENT REGISTRY                      ║
║     Persistência de Intenção e Metadados de Entrada (Anti-Amnésia)           ║
║                                                                              ║
║  Armazena o que a ASI estava pensando (regime, confiança, PHI) no momento    ║
║  exato da execução, eliminando o viés de antecipação na sincronização.       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import os
import threading
from datetime import datetime, timezone
from typing import Dict, Optional, Any

from utils.logger import log
from config.settings import DATA_DIR

class TradeRegistry:
    """
    Registro persistente de intenções de trade.
    Mapeia ticket/position_id para os metadados contextuais da entrada.
    """
    
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(TradeRegistry, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.registry_file = os.path.join(DATA_DIR, "trade_intent_registry.json")
        self.intents: Dict[str, Any] = {}
        self._load()
        self._initialized = True

    def _load(self):
        """Carrega o registro do disco."""
        try:
            if os.path.exists(self.registry_file):
                with open(self.registry_file, "r") as f:
                    self.intents = json.load(f)
                log.info(f"📂 Trade Registry carregado: {len(self.intents)} intenções mapeadas.")
            else:
                self.intents = {}
        except Exception as e:
            log.error(f"❌ Erro ao carregar Trade Registry: {e}")
            self.intents = {}

    def _save(self):
        """Salva o registro no disco."""
        try:
            os.makedirs(os.path.dirname(self.registry_file), exist_ok=True)
            with open(self.registry_file, "w") as f:
                json.dump(self.intents, f, indent=2)
        except Exception as e:
            log.error(f"❌ Erro ao salvar Trade Registry: {e}")

    def register_intent(self, ticket: int, intent: Any, snapshot: Any, position_id: int = 0, strike_id: Optional[str] = None):
        """
        Registra os metadados de intenção para um novo trade.
        Extrai regime, confiança e PHI dos objetos originais.
        """
        try:
            # Extrair metadados da intenção (objeto Decision)
            metadata = {
                "regime": getattr(intent, 'regime', 'UNKNOWN'),
                "confidence": getattr(intent, 'confidence', 0.0),
                "signal_strength": getattr(intent, 'signal_strength', 0.0),
                "coherence": getattr(intent, 'coherence', 0.0),
                "phi": getattr(snapshot, 'phi', 0.0) if snapshot else 0.0,
                "reasoning": getattr(intent, 'reasoning', ''),
                "symbol": getattr(snapshot, 'symbol', 'UNKNOWN') if snapshot else 'UNKNOWN',
                "strike_id": strike_id,
                "custom_metadata": getattr(intent, 'metadata', {})
            }
            
            with self._lock:
                intent_record = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "ticket": ticket,
                    "position_id": position_id,
                    **metadata
                }
                
                # Armazenar indexado por ticket
                self.intents[f"ticket_{ticket}"] = intent_record
                
                # Se temos position_id, indexar também por ele
                if position_id > 0:
                    self.intents[str(position_id)] = intent_record
                
                # Se temos um strike_id, permitimos busca por ele também
                if strike_id:
                    self.intents[f"strike_{strike_id}"] = intent_record

                # Limitar tamanho (últimos 5000)
                if len(self.intents) > 15000:
                    keys = list(self.intents.keys())[:500]
                    for k in keys:
                        self.intents.pop(k, None)

                self._save() # [PHASE 48 FIX] Corrigido self.save() -> self._save()
                log.info(f"💾 Intenção registrada Ticket#{ticket} | Strike={strike_id} | Conf={metadata.get('confidence'):.2f}")
        except Exception as e:
            log.error(f"❌ Erro ao registrar intenção: {e}")

    def get_intent(self, position_id: int, ticket: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Recupera os metadados de entrada salvos."""
        # 1. Tentar por position_id
        intent = self.intents.get(str(position_id))
        
        # 2. Tentar por ticket se não achou ou se fornecido
        if not intent and ticket:
            intent = self.intents.get(f"ticket_{ticket}")
            
        return intent

    def update_ticket_by_strike(self, strike_id: str, new_ticket: int):
        """Atualiza o ticket de um registro de intenção usando o strike_id como chave."""
        with self._lock:
            strike_key = f"strike_{strike_id}"
            if strike_key in self.intents:
                intent_record = self.intents[strike_key]
                old_ticket = intent_record.get("ticket", 0)
                
                # Atualizar o registro
                intent_record["ticket"] = new_ticket
                intent_record["position_id"] = new_ticket
                
                # Re-indexar por novo ticket
                self.intents[f"ticket_{new_ticket}"] = intent_record
                self.intents[str(new_ticket)] = intent_record
                
                # Remover indexação antiga pelo ticket 0 se existir
                if old_ticket == 0:
                    self.intents.pop("ticket_0", None)
                
                self._save()
                log.omega(f"🔄 SYNC: Strike {strike_id} mapeado para Ticket#{new_ticket}")

    def update_ticket(self, old_ticket: int, new_ticket: int):
        """Atualiza o ticket de um registro de intenção pendente."""
        with self._lock:
            old_key = f"ticket_{old_ticket}"
            if old_key in self.intents:
                intent_record = self.intents.pop(old_key)
                intent_record["ticket"] = new_ticket
                self.intents[f"ticket_{new_ticket}"] = intent_record
                # Se for o ticket final, ele também se torna o position_id inicial
                self.intents[str(new_ticket)] = intent_record
                self._save()

# Singleton Global
registry = TradeRegistry()
