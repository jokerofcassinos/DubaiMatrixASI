import os
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from utils.logger import log
from utils.log_buffer import LOG_BUFFER
from utils.visual_capture import capture_mt5_window

class QuantumAuditEngine:
    """
    [Ω-AUDIT] The high-fidelity post-mortem system for DubaiMatrixASI.
    Captures full context, logs, and screenshots for every trade.
    """
    def __init__(self, base_path: str = "audits"):
        self.base_path = base_path
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)
        
        # Cache de contextos de início p/ associar no fim (Exit)
        self._active_audits: Dict[int, Dict[str, Any]] = {}

    def start_audit(self, ticket: int, decision: Any, snapshot: Any, strike_id: Optional[str] = None):
        """
        Inicia a auditoria de uma nova ordem.
        ticket: Ticket da ordem no MT5
        decision: O objeto Decision da TrinityCore
        snapshot: O MarketSnapshot do momento da entrada
        strike_id: ID único do strike (agrupa todos os slots Hydra)
        """
        try:
            # Se não houver strike_id, usamos o ticket (compatibilidade)
            s_id = strike_id or f"SID_{ticket or int(time.time()*1000)}"
            
            # Se já existe auditoria para este strike (Hydra slot anterior), apenas associamos o novo ticket
            if s_id in self._active_audits:
                if ticket > 0:
                    self._active_audits[s_id]["tickets"].add(ticket)
                return

            date_str = datetime.now().strftime("%Y-%m-%d")
            # Pasta baseada no strike_id para evitar duplicatas Trade_0
            folder_name = f"Strike_{s_id}_{decision.action.value}_{int(time.time())}"
            audit_dir = os.path.join(self.base_path, date_str, folder_name)
            
            if not os.path.exists(audit_dir):
                os.makedirs(audit_dir)
            
            # 1. Salvar Metadados Iniciais (Contexto do Pensamento PhD)
            q_meta = getattr(decision, "metadata", {}).get("quantum_metadata", {})
            
            context = {
                "strike_id": s_id,
                "tickets": [ticket] if ticket > 0 else [],
                "timestamp_entry": time.time(),
                "action": decision.action.value,
                "signal": decision.signal_strength,
                "confidence": decision.confidence,
                "reasoning": decision.reasoning,
                "regime": getattr(decision, "regime", "UNKNOWN"),
                "lot_size": decision.lot_size,
                "entry_price": decision.entry_price,
                "stop_loss": decision.stop_loss,
                "take_profit": decision.take_profit,
                "swarm_intelligence": {
                    "phi": snapshot.metadata.get("phi_last", 0.0),
                    "kl_div": snapshot.metadata.get("kl_divergence", 0.0),
                    "bull_agents": q_meta.get("bull_agents", []),
                    "bear_agents": q_meta.get("bear_agents", []),
                    "neutral_agents": q_meta.get("neutral_agents", [])
                },
                "snapshot": {
                    "price": snapshot.price,
                    "atr": snapshot.atr
                }
            }
            
            with open(os.path.join(audit_dir, "lifecycle_context.json"), "w") as f:
                json.dump(context, f, indent=4)
            
            # 2. Captura de Tela (Entry)
            screenshot_path = os.path.join(audit_dir, "entry_screenshot.png")
            capture_mt5_window(screenshot_path)
            
            # 3. Armazenar o audit_dir p/ fechar depois
            self._active_audits[s_id] = {
                "dir": audit_dir,
                "context": context,
                "tickets": {ticket} if ticket > 0 else set()
            }
            
            log.info(f"📂 Auditoria Quantum iniciada: {folder_name} (Strike: {s_id})")
            
        except Exception as e:
            log.error(f"❌ Falha ao iniciar auditoria para ticket {ticket}: {e}")

    def end_audit(self, ticket: int, result: Dict[str, Any], strike_id: Optional[str] = None):
        """
        Finaliza a auditoria quando a ordem é fechada.
        """
        s_id = strike_id
        
        # Se não temos strike_id, tentamos encontrar pelo ticket no mapa ativo
        if not s_id:
            for sid, data in self._active_audits.items():
                if ticket in data["tickets"]:
                    s_id = sid
                    break
        
        if not s_id or s_id not in self._active_audits:
            # Fallback reverso: se o ticket for novo mas as pastas Trade_0 existirem, 
            # o PositionManager pode estar enviando o ticket real agora.
            return

        try:
            audit_data = self._active_audits.pop(s_id)
            audit_dir = audit_data["dir"]
            
            # 1. Atualizar context com o resultado final
            context = audit_data["context"]
            context["timestamp_exit"] = time.time()
            context["duration"] = context["timestamp_exit"] - context["timestamp_entry"]
            context["result"] = result
            
            # Marcar se foi LOSS ou PROFIT
            pnl = result.get("profit", 0.0)
            status = "PROFIT" if pnl >= 0 else "LOSS"
            
            # Renomear pasta para incluir o resultado
            base_folder = os.path.basename(audit_dir)
            new_folder_name = base_folder + f"_{status}_{int(abs(pnl))}"
            new_audit_dir = os.path.join(os.path.dirname(audit_dir), new_folder_name)
            
            # 2. Salvar logs capturados no buffer (A cereja do bolo PHD)
            logs = LOG_BUFFER.get_logs()
            with open(os.path.join(audit_dir, "terminal_logs.txt"), "w", encoding="utf-8") as f:
                f.write("\n".join(logs))
            
            # 3. Captura de Tela (Exit)
            screenshot_path = os.path.join(audit_dir, "exit_screenshot.png")
            capture_mt5_window(screenshot_path)
            
            # 4. Salvar contexto finalizado
            with open(os.path.join(audit_dir, "lifecycle_context.json"), "w") as f:
                json.dump(context, f, indent=4)
                
            # Renomear diretório final
            if os.path.exists(audit_dir):
                os.rename(audit_dir, new_audit_dir)
            
            log.omega(f"🏁 Auditoria Quantum FINALIZADA: {new_folder_name} (P&L: ${pnl:.2f})")
            
        except Exception as e:
            log.error(f"❌ Falha ao finalizar auditoria para ticket {ticket}: {e}")

# Singleton
AUDIT_ENGINE = QuantumAuditEngine()
