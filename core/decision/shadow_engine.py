import os
import json
import time
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional
from core.decision.trinity_core import Action
from core.consciousness.quantum_thought import QuantumState
from market.data_engine import MarketSnapshot
from utils.logger import log
from utils.visual_capture import capture_mt5_window

class ShadowCounterfactualEngine:
    """
    [Phase Ω-9] Shadow Counterfactual Engine (V3 - Visual Forensics)
    
    Este motor rastreia Oportunidades Desperdiçadas (Vetoes) em ciclos de 45 candles.
    Organiza ghosts em diretórios por data e ciclo, mapeando-os por posição no chart.
    """
    def __init__(self, base_dir: str = "data/audits/ghost_trade_audits"):
        self.base_dir = base_dir
        self.pendentes_dir = os.path.join(base_dir, "pendentes")
        self.corretos_dir = os.path.join(base_dir, "corretos")
        self.errados_dir = os.path.join(base_dir, "errados")
        
        self._ensure_dirs()
        self.open_shadows: List[Dict[str, Any]] = self._load_pendentes()
        self.last_save = time.time()
        
        log.omega(f"👻 [SHADOW ENGINE] V3 Ativo. {len(self.open_shadows)} ghosts pendentes carregados.")

    def _ensure_dirs(self):
        for d in [self.pendentes_dir, self.corretos_dir, self.errados_dir]:
            os.makedirs(d, exist_ok=True)

    def _load_pendentes(self) -> List[Dict[str, Any]]:
        """Varre o diretório de pendentes para reconstruir a lista em memória."""
        open_list = []
        if not os.path.exists(self.pendentes_dir):
            return []
            
        for date_dir in os.listdir(self.pendentes_dir):
            date_path = os.path.join(self.pendentes_dir, date_dir)
            if not os.path.isdir(date_path): continue
            
            for cycle_dir in os.listdir(date_path):
                cycle_path = os.path.join(date_path, cycle_dir)
                if not os.path.isdir(cycle_path): continue
                
                for ghost_file in os.listdir(cycle_path):
                    if ghost_file.endswith(".json") and ghost_file != "cycle_meta.json":
                        try:
                            with open(os.path.join(cycle_path, ghost_file), 'r', encoding='utf-8') as f:
                                trade = json.load(f)
                                # Adicionar path original para facilitar movimentação depois
                                trade["_internal_path"] = os.path.join(cycle_path, ghost_file)
                                open_list.append(trade)
                        except Exception as e:
                            log.error(f"Erro ao carregar ghost {ghost_file}: {e}")
        return open_list

    def _get_or_create_cycle(self, entry_time_dt: datetime) -> Dict[str, Any]:
        """Calcula o ciclo atual (45 min) ou cria um novo se necessário."""
        date_str = entry_time_dt.strftime("%Y-%m-%d")
        day_dir = os.path.join(self.pendentes_dir, date_str)
        os.makedirs(day_dir, exist_ok=True)
        
        # Procurar o ciclo mais recente do dia
        cycles = sorted([d for d in os.listdir(day_dir) if d.startswith("cycle_")], reverse=True)
        
        create_new = True
        cycle_id = "001"
        cycle_start_ts = entry_time_dt.timestamp()
        
        if cycles:
            latest_cycle = cycles[0]
            meta_path = os.path.join(day_dir, latest_cycle, "cycle_meta.json")
            if os.path.exists(meta_path):
                with open(meta_path, 'r') as f:
                    meta = json.load(f)
                    start_ts = meta.get("start_ts", 0)
                    # Se estamos dentro da janela de 45 minutos do ciclo atual
                    if entry_time_dt.timestamp() - start_ts < (45 * 60):
                        return {
                            "path": os.path.join(day_dir, latest_cycle),
                            "id": latest_cycle.split("_")[1],
                            "start_ts": start_ts,
                            "code": meta.get("code")
                        }
                    else:
                        # O CICLO ANTIGO TERMINOU. Capturar screenshot final dele por segurança antes de criar novo.
                        code = meta.get("code")
                        screenshot_path = os.path.join(day_dir, latest_cycle, f"chart_{code}.png")
                        if not meta.get("final_screenshot") and not os.path.exists(screenshot_path):
                            capture_mt5_window(screenshot_path)
                            meta["final_screenshot"] = True
                            with open(meta_path, 'w') as sf: json.dump(meta, sf, indent=2)
                            log.omega(f"📸 [SHADOW SYNC] Screenshot FINAL preventivo do ciclo {code} capturado.")
            # Se não entramos no anterior, incrementamos o ID
            last_idx = int(latest_cycle.split("_")[1])
            cycle_id = f"{last_idx + 1:03d}"

        # Criar novo ciclo
        cycle_name = f"cycle_{cycle_id}"
        cycle_path = os.path.join(day_dir, cycle_name)
        os.makedirs(cycle_path, exist_ok=True)
        
        cycle_code = f"CYC{cycle_id}_{entry_time_dt.strftime('%Y%m%d')}"
        meta = {
            "code": cycle_code,
            "start_ts": cycle_start_ts,
            "start_iso": entry_time_dt.isoformat() + "Z",
            "duration_min": 45,
            "final_screenshot": False
        }
        
        with open(os.path.join(cycle_path, "cycle_meta.json"), "w") as f:
            json.dump(meta, f, indent=2)
            
        log.omega(f"👻 [SHADOW CYCLE] Novo ciclo {cycle_code} iniciado (Aguardando fim p/ screenshot).")
        
        return {
            "path": cycle_path,
            "id": cycle_id,
            "start_ts": cycle_start_ts,
            "code": cycle_code
        }

    def _get_candle_pos(self, cycle_path: str, entry_ts: float, start_ts: float) -> str:
        """Calcula a posição do candle (1-45) e lida com duplicatas (X.json, X_1.json)."""
        # Candle base: 1 candle per minute (M1)
        pos = int((entry_ts - start_ts) // 60) + 1
        pos = max(1, min(45, pos)) # Bound to screen width roughly
        
        base_name = f"{pos}"
        final_name = base_name
        counter = 1
        
        while os.path.exists(os.path.join(cycle_path, f"{final_name}.json")):
            final_name = f"{base_name}_{counter}"
            counter += 1
            
        return final_name

    def register_shadow_trade(self, veto_reason: str, snapshot: MarketSnapshot, quantum_state: QuantumState, action: Action, atr: float = 0.0):
        if action == Action.WAIT:
            return

        direction = "BUY" if action == Action.BUY else "SELL"
        now_dt = datetime.utcnow()
        now_ts = now_dt.timestamp()

        # --- ANTI-SPAM GUARD ---
        base_veto = veto_reason.split("(")[0].strip() if "(" in veto_reason else veto_reason
        spam_key = f"{base_veto}_{direction}"
        if not hasattr(self, '_last_registry_time'): self._last_registry_time = {}
        if time.time() - self._last_registry_time.get(spam_key, 0.0) < 60.0: return
        self._last_registry_time[spam_key] = time.time()

        # Preço e Alvos
        sl_points = atr * 1.5 if atr > 0 else 500.0
        tp_points = atr * 3.0 if atr > 0 else 1000.0
        entry_price = snapshot.price
        sl_price = entry_price - sl_points if direction == "BUY" else entry_price + sl_points
        tp_price = entry_price + tp_points if direction == "BUY" else entry_price - tp_points

        # Ciclo e Posição
        cycle = self._get_or_create_cycle(now_dt)
        candle_pos = self._get_candle_pos(cycle["path"], now_ts, cycle["start_ts"])
        
        shadow_id = f"GST_{int(now_ts*1000)}"
        
        # Metadata Swarm
        bull_agents = [s.agent_name for s in quantum_state.agent_signals if s.signal > 0.05]
        bear_agents = [s.agent_name for s in quantum_state.agent_signals if s.signal < -0.05]
        neutral_agents = [s.agent_name for s in quantum_state.agent_signals if -0.05 <= s.signal <= 0.05]
        
        avg_conf = sum(s.confidence for s in quantum_state.agent_signals) / max(1, len(quantum_state.agent_signals))
        confidence = avg_conf * (0.8 + 0.2 * quantum_state.coherence)

        trade = {
            "id": shadow_id,
            "status": "OPEN",
            "entry_time": now_dt.isoformat() + "Z",
            "entry_timestamp": now_ts,
            "entry_price": entry_price,
            "direction": direction,
            "veto_reason": veto_reason,
            "signal_strength": quantum_state.collapsed_signal,
            "confidence": confidence,
            "coherence": quantum_state.coherence,
            "phi": quantum_state.phi,
            "sl_price": sl_price,
            "tp_price": tp_price,
            "close_time": None,
            "close_price": None,
            "result": None,
            "cycle_code": cycle["code"],
            "candle_pos": candle_pos,
            "swarm_intelligence": {
                "bull_agents": bull_agents,
                "bear_agents": bear_agents,
                "neutral_agents": neutral_agents
            },
            "snapshot": {
                "regime": str(snapshot.regime.value if hasattr(snapshot.regime, 'value') else (snapshot.regime or "UNKNOWN")),
                "atr": atr,
                "metadata": {
                    "tick_velocity": snapshot.metadata.get("tick_velocity", 0.0),
                    "v_pulse_detected": snapshot.metadata.get("v_pulse_detected", False),
                    "shannon_entropy": snapshot.metadata.get("shannon_entropy", 0.0),
                    "jounce": snapshot.metadata.get("jounce", 0.0)
                }
            }
        }

        # Salvar JSON individual
        file_path = os.path.join(cycle["path"], f"{candle_pos}.json")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(trade, f, indent=2, ensure_ascii=False)
            
            trade["_internal_path"] = file_path
            self.open_shadows.append(trade)
            log.omega(f"👻 [SHADOW REGISTRY] Ghost {candle_pos} (ID: {shadow_id}) criado no ciclo {cycle['code']}.")
        except Exception as e:
            log.error(f"Erro ao salvar ghost {candle_pos}: {e}")

    def update_shadow_matrix(self, current_price: float):
        """Atualiza alvos, move finalizados, deleta expirados e gerencia fechamento de ciclo."""
        self._check_cycle_closure()
        
        if not self.open_shadows: return

        closed_count = 0
        now_ts = time.time()
        now_iso = datetime.utcnow().isoformat() + "Z"
        
        for trade in list(self.open_shadows):
            # 1. Verificação de Expiração (5 minutos)
            entry_ts = trade.get("entry_timestamp", 0)
            if now_ts - entry_ts > (5 * 60):
                self._expire_ghost(trade)
                continue

            # 2. Verificação de Alvos (TP/SL)
            closed = False
            result = None
            
            if trade["direction"] == "BUY":
                if current_price >= trade["tp_price"]:
                    closed, result = True, "FALSE_NEGATIVE"
                elif current_price <= trade["sl_price"]:
                    closed, result = True, "TRUE_NEGATIVE"
            elif trade["direction"] == "SELL":
                if current_price <= trade["tp_price"]:
                    closed, result = True, "FALSE_NEGATIVE"
                elif current_price >= trade["sl_price"]:
                    closed, result = True, "TRUE_NEGATIVE"
                    
            if closed:
                trade["status"] = "CLOSED"
                trade["close_time"] = now_iso
                trade["close_price"] = current_price
                trade["result"] = result
                self._finalize_ghost(trade)
                closed_count += 1

    def _finalize_ghost(self, trade: Dict[str, Any]):
        """Move o ghost de pendentes para corretos/errados."""
        try:
            target_dir = self.corretos_dir if trade["result"] == "TRUE_NEGATIVE" else self.errados_dir
            new_path = os.path.join(target_dir, f"{trade['id']}.json")
            
            # Remover campo interno antes de salvar
            old_path = trade.pop("_internal_path", None)
            
            with open(new_path, "w", encoding="utf-8") as f:
                json.dump(trade, f, indent=2, ensure_ascii=False)
            
            # Deletar original
            if old_path and os.path.exists(old_path):
                os.remove(old_path)
                
            self.open_shadows.remove(trade)
            
            icon = "🛡️" if trade["result"] == "TRUE_NEGATIVE" else "🔥"
            log.omega(f"👻 [SHADOW AUDIT] {icon} Ghost {trade['id']} ({trade['candle_pos']}) movido para {trade['result']}.")
        except Exception as e:
            log.error(f"Erro ao finalizar ghost {trade['id']}: {e}")

    def _expire_ghost(self, trade: Dict[str, Any]):
        """Deleta silenciosamente ghosts > 5 min."""
        try:
            path = trade.get("_internal_path")
            if path and os.path.exists(path):
                os.remove(path)
            self.open_shadows.remove(trade)
            # log.debug(f"🧹 Ghost {trade['id']} ({trade['candle_pos']}) expirado.")
        except Exception as e:
            log.error(f"Erro ao expirar ghost {trade['id']}: {e}")
    def _check_cycle_closure(self):
        """Vigia o tempo do ciclo atual e tira o print FINAL quando fechar 45 min."""
        now = time.time()
        
        # Só checamos se passamos 30s da última verificação para economizar CPU
        if not hasattr(self, '_last_cycle_check'): self._last_cycle_check = 0
        if now - self._last_cycle_check < 30: return
        self._last_cycle_check = now
        
        # Localizar ciclo atual
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        day_dir = os.path.join(self.pendentes_dir, date_str)
        if not os.path.exists(day_dir): return
        
        cycles = sorted([d for d in os.listdir(day_dir) if d.startswith("cycle_")], reverse=True)
        if not cycles: return
        
        latest_cycle = cycles[0]
        cycle_path = os.path.join(day_dir, latest_cycle)
        meta_path = os.path.join(cycle_path, "cycle_meta.json")
        
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r') as f:
                    meta = json.load(f)
                
                if meta.get("final_screenshot"): return # Já capturado
                
                start_ts = meta.get("start_ts", 0)
                # Se completou 45 minutos (ou se estamos muito próximos do fim)
                if now - start_ts >= (45 * 60):
                    code = meta.get("code")
                    screenshot_path = os.path.join(cycle_path, f"chart_{code}.png")
                    capture_mt5_window(screenshot_path)
                    
                    # Marcar como capturado no meta
                    meta["final_screenshot"] = True
                    meta["end_ts"] = now
                    meta["end_iso"] = datetime.utcnow().isoformat() + "Z"
                    with open(meta_path, 'w') as f:
                        json.dump(meta, f, indent=2)
                        
                    log.omega(f"📸 [SHADOW SYNC] Screenshot FINAL do ciclo {code} capturado com perfeição.")
            except Exception as e:
                log.error(f"Erro ao checar fechamento de ciclo: {e}")

