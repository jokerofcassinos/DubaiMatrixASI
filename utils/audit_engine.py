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

    def start_audit(self, ticket: int, decision: Any, snapshot: Any):
        """
        Inicia a auditoria de uma nova ordem.
        ticket: Ticket da ordem no MT5 (ou 0 se for pendente/agrupada)
        decision: O objeto Decision da TrinityCore
        snapshot: O MarketSnapshot do momento da entrada
        """
        try:
            date_str = datetime.now().strftime("%Y-%m-%d")
            folder_name = f"Trade_{ticket}_{decision.action.value}_{int(time.time())}"
            audit_dir = os.path.join(self.base_path, date_str, folder_name)
            
            if not os.path.exists(audit_dir):
                os.makedirs(audit_dir)
            
            # 1. Salvar Metadados Iniciais (Contexto do Pensamento)
            context = {
                "ticket": ticket,
                "timestamp_entry": time.time(),
                "action": decision.action.value,
                "signal": decision.signal_strength,
                "confidence": decision.confidence,
                "reasoning": decision.reasoning,
                "regime": decision.regime,
                "lot_size": decision.lot_size,
                "entry_price": decision.entry_price,
                "stop_loss": decision.stop_loss,
                "take_profit": decision.take_profit,
                "snapshot": {
                    "price": snapshot.price,
                    "atr": snapshot.atr,
                    "phi": snapshot.metadata.get("phi_last", 0.0),
                    "kl_div": snapshot.metadata.get("kl_divergence", 0.0)
                }
            }
            
            with open(os.path.join(audit_dir, "lifecycle_context.json"), "w") as f:
                json.dump(context, f, indent=4)
            
            # 2. Captura de Tela (Entry)
            screenshot_path = os.path.join(audit_dir, "entry_screenshot.png")
            capture_mt5_window(screenshot_path)
            
            # 3. Armazenar o audit_dir p/ fechar depois
            self._active_audits[ticket] = {
                "dir": audit_dir,
                "context": context
            }
            
            log.info(f"📂 Auditoria Quantum iniciada: {folder_name}")
            
        except Exception as e:
            log.error(f"❌ Falha ao iniciar auditoria para ticket {ticket}: {e}")

    def end_audit(self, ticket: int, result: Dict[str, Any]):
        """
        Finaliza a auditoria quando a ordem é fechada.
        result: Dados do fechamento (P&L final, tempo, motivo)
        """
        if ticket not in self._active_audits:
            # Fallback p/ tickers agrupados ou perda de memória
            return

        try:
            audit_data = self._active_audits.pop(ticket)
            audit_dir = audit_data["dir"]
            
            # 1. Atualizar context com o resultado final
            context = audit_data["context"]
            context["timestamp_exit"] = time.time()
            context["duration"] = context["timestamp_exit"] - context["timestamp_entry"]
            context["result"] = result
            
            # Marcar se foi LOSS ou PROFIT p/ facilitar análise futura do CEO
            pnl = result.get("profit", 0.0)
            status = "PROFIT" if pnl >= 0 else "LOSS"
            
            # Renomear pasta para incluir o resultado
            new_folder_name = os.path.basename(audit_dir) + f"_{status}_{int(pnl)}"
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
            os.rename(audit_dir, new_audit_dir)
            
            log.omega(f"🏁 Auditoria Quantum FINALIZADA: {new_folder_name} (P&L: ${pnl:.2f})")
            
        except Exception as e:
            log.error(f"❌ Falha ao finalizar auditoria para ticket {ticket}: {e}")

# Singleton
AUDIT_ENGINE = QuantumAuditEngine()
