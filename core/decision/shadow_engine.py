import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any
from core.decision.trinity_core import Action
from core.consciousness.quantum_thought import QuantumState
from market.data_engine import MarketSnapshot
from utils.logger import log

class ShadowCounterfactualEngine:
    """
    [Phase Ω-9] Shadow Counterfactual Engine
    
    Este motor rastreia Oportunidades Desperdiçadas (Vetoes).
    Sempre que a TrinityCore barra uma execução que possuía sinal direcional forte,
    registramos um Trade Fantasma (Shadow Trade) e acompanhamos seu PnL virtual.
    - Se bater no TP virtual: FALSE_NEGATIVE (O Veto nos tirou dinheiro).
    - Se bater no SL virtual: TRUE_NEGATIVE (O Veto nos salvou).
    
    As métricas geradas podem ser usadas pelo CEO ou pela ASI para endurecer 
    ou relaxar os thresholds de Veto.
    """
    def __init__(self, file_path: str = "data/audits/shadow_trades.json"):
        self.file_path = file_path
        self._ensure_dir()
        self.shadow_trades: List[Dict[str, Any]] = self._load()
        # Keep only open trades or recent trades in memory to avoid bloat
        self.open_shadows: List[Dict[str, Any]] = [t for t in self.shadow_trades if t.get("status") == "OPEN"]
        self.last_save = time.time()
        log.omega(f"👻 [SHADOW ENGINE] Inicializado. {len(self.open_shadows)} shadow trades abertos na memória.")

    def _ensure_dir(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    def _load(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.file_path):
            try:
                # [Phase Ω-9 Fix] Handle empty or corrupted JSON files
                if os.path.getsize(self.file_path) == 0:
                    return []
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                log.error(f"Failed to load shadow trades: {e}")
        return []

    def _save(self):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.shadow_trades, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log.error(f"Failed to save shadow trades: {e}")

    def register_shadow_trade(self, veto_reason: str, snapshot: MarketSnapshot, quantum_state: QuantumState, action: Action, atr: float = 0.0):
        """
        Registra um novo VETO como uma oportunidade em observação.
        """
        if action == Action.WAIT:
            return

        direction = "BUY" if action == Action.BUY else "SELL"

        # --- ANTI-SPAM GUARD ---
        # Agrupa pelo motivo base do veto para evitar spam temporal (ex: "WAIT: COLD_START_SYNC_VETO (96s left)")
        base_veto = veto_reason.split("(")[0].strip() if "(" in veto_reason else veto_reason
        spam_key = f"{base_veto}_{direction}"
        now = time.time()
        
        # Cooldown de 60 segundos por assinatura de Veto + Direção
        if not hasattr(self, '_last_registry_time'):
            self._last_registry_time = {}
            
        if now - self._last_registry_time.get(spam_key, 0.0) < 60.0:
            return
            
        self._last_registry_time[spam_key] = now

        # Para criar o TP e SL teórico, usamos a ATR local:
        sl_points = atr * 1.5 if atr > 0 else 500.0
        tp_points = atr * 3.0 if atr > 0 else 1000.0

        entry_price = snapshot.price
        
        sl_price = entry_price - sl_points if direction == "BUY" else entry_price + sl_points
        tp_price = entry_price + tp_points if direction == "BUY" else entry_price - tp_points

        shadow_id = f"GST_{int(time.time()*1000)}"
        signal_val = quantum_state.collapsed_signal
        
        # [Phase Ω-9] Tentar extrair MC metadata da veto_reason
        import re
        mc_match = re.search(r'MC\[(.*?)\]', veto_reason)
        mc_data = f"MC[{mc_match.group(1)}]" if mc_match else ""

        # [Phase Ω-9] PhD-level metadata extraction
        bull_agents_list = [s.agent_name for s in quantum_state.agent_signals if s.signal > 0.05]
        bear_agents_list = [s.agent_name for s in quantum_state.agent_signals if s.signal < -0.05]
        neutral_agents_list = [s.agent_name for s in quantum_state.agent_signals if -0.05 <= s.signal <= 0.05]
        
        avg_conf = sum(s.confidence for s in quantum_state.agent_signals) / max(1, len(quantum_state.agent_signals))
        confidence = avg_conf * (0.8 + 0.2 * quantum_state.coherence)
        
        trade = {
            "id": shadow_id,
            "status": "OPEN",
            "entry_time": datetime.utcnow().isoformat() + "Z",
            "entry_price": entry_price,
            "direction": direction,
            "veto_reason": veto_reason,
            "signal_strength": signal_val,
            "confidence": confidence,
            "coherence": quantum_state.coherence,
            "phi": quantum_state.phi,
            "mc_data": mc_data,
            "sl_price": sl_price,
            "tp_price": tp_price,
            "close_time": None,
            "close_price": None,
            "result": None, # "FALSE_NEGATIVE" (Missed Profit), "TRUE_NEGATIVE" (Avoided Loss)
            "swarm_intelligence": {
                "bull_agents": bull_agents_list,
                "bear_agents": bear_agents_list,
                "neutral_agents": neutral_agents_list
            },
            "snapshot": {
                "regime": snapshot.regime.value if hasattr(snapshot.regime, 'value') else str(snapshot.regime),
                "atr": atr
            }
        }

        self.shadow_trades.append(trade)
        self.open_shadows.append(trade)
        self._save()
        log.omega(f"👻 [SHADOW REGISTRY] Fantasma {shadow_id} criado para VETO [{veto_reason}]. Dir: {direction} (Sig: {signal_val:.2f}).")

    def update_shadow_matrix(self, current_price: float):
        """
        Itera sobre os shadow trades abertos verificando se bateram em TP/SL teóricos.
        """
        if not self.open_shadows:
            return

        closed_count = 0
        now = datetime.utcnow().isoformat() + "Z"
        
        for trade in list(self.open_shadows):
            closed = False
            result = None
            
            if trade["direction"] == "BUY":
                if current_price >= trade["tp_price"]:
                    closed = True
                    result = "FALSE_NEGATIVE" # Price went up! Veto was wrong (Missed profit)
                elif current_price <= trade["sl_price"]:
                    closed = True
                    result = "TRUE_NEGATIVE" # Price went down. Veto was right (Avoided loss)
            
            elif trade["direction"] == "SELL":
                if current_price <= trade["tp_price"]:
                    closed = True
                    result = "FALSE_NEGATIVE" # Price went down! Veto was wrong (Missed profit)
                elif current_price >= trade["sl_price"]:
                    closed = True
                    result = "TRUE_NEGATIVE" # Price went up. Veto was right (Avoided loss)
                    
            if closed:
                trade["status"] = "CLOSED"
                trade["close_time"] = now
                trade["close_price"] = current_price
                trade["result"] = result
                
                self.open_shadows.remove(trade)
                closed_count += 1
                
                icon = "🔥" if result == "FALSE_NEGATIVE" else "🛡️"
                msg_type = "CUSTOU DINHEIRO" if result == "FALSE_NEGATIVE" else "SALVOU A CONTA"
                log.omega(f"👻 [SHADOW AUDIT] {icon} Veto [{trade['veto_reason']}] {msg_type}! "
                          f"Fantasma {trade['id']} de {trade['direction']} atingiu alvo simulado em {current_price:.2f}.")

        if closed_count > 0 or (time.time() - self.last_save > 60):
            self._save()
            self.last_save = time.time()
