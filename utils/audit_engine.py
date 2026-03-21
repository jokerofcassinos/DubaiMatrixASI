import os
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from utils.logger import log
from utils.log_buffer import LOG_BUFFER
from utils.visual_capture import capture_mt5_window
from concurrent.futures import ThreadPoolExecutor

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
        
        # [Ω-FIX] Executor paralelo para capturas de tela e logs (Não trava o loop HFT)
        self._audit_pool = ThreadPoolExecutor(max_workers=5, thread_name_prefix="AuditPool")

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

    def get_active_audit_path(self, ticket: int) -> Optional[str]:
        """Retorna o caminho do diretório da auditoria ativa para um ticket."""
        if not ticket:
            return None
        # Buscar nos ativos
        for sid, data in self._active_audits.items():
            if ticket in data.get("tickets", set()):
                return data.get("dir")
        return None

    def end_audit(self, ticket: int, result: Dict[str, Any], strike_id: Optional[str] = None):
        """
        Finaliza a auditoria quando a ordem é fechada.
        Executa em background para não travar o loop HFT.
        """
        self._audit_pool.submit(self._end_audit_core, ticket, result, strike_id)

    def _end_audit_core(self, ticket: int, result: Dict[str, Any], strike_id: Optional[str] = None):
        """
        O coração da finalização da auditoria (executado em background).
        """
        # [Ω-FIX] Pequeno delay para permitir que o MT5 renderize o marcador de saída no chart
        time.sleep(1.0)
        
        s_id = strike_id
        
        # Se não temos strike_id, tentamos encontrar pelo ticket no mapa ativo
        if not s_id:
            for sid, data in self._active_audits.items():
                if ticket in data["tickets"]:
                    s_id = sid
                    break
        
        if not s_id or s_id not in self._active_audits:
            # [Ω-PERSISTENCE] Fallback: Tentar recuperar o diretório da auditoria no disco
            # Se o bot reiniciou, o mapa em memória está vazio, mas as pastas Trade_0 existem.
            if not s_id:
                # Se não temos s_id, o rastro foi perdido totalmente (restart pesado)
                return

            # Procurar se existe uma pasta com o strike_id para hoje
            today = datetime.now().strftime("%Y-%m-%d")
            base_audit_dir = os.path.join("audits", today)
            
            if not os.path.exists(base_audit_dir):
                return
                
            match_dir = None
            for folder in os.listdir(base_audit_dir):
                if folder.startswith(f"Strike_{s_id}"):
                    match_dir = os.path.join(base_audit_dir, folder)
                    break
            
            if match_dir and os.path.exists(os.path.join(match_dir, "lifecycle_context.json")):
                log.omega(f"📂 [AUDIT RECOVERY] Recuperando auditoria persistente para {s_id}...")
                try:
                    with open(os.path.join(match_dir, "lifecycle_context.json"), "r") as f:
                        recovered_context = json.load(f)
                    self._active_audits[s_id] = {
                        "dir": match_dir,
                        "context": recovered_context,
                        "tickets": recovered_context.get("tickets", [])
                    }
                except Exception as e:
                    log.error(f"Erro ao recuperar auditoria de {match_dir}: {e}")
                    return
            else:
                return

        try:
            audit_data = self._active_audits.pop(s_id)
            audit_dir = audit_data["dir"]
            
            # 1. Atualizar context com o resultado final
            context = audit_data["context"]
            context["timestamp_exit"] = time.time()
            context["duration"] = context["timestamp_exit"] - context.get("timestamp_entry", time.time())
            
            # [Ω-FIX] Acumular lucro para Strike Hydra
            new_pnl = result.get("profit", 0.0)
            if "result" in context and isinstance(context["result"], dict):
                old_pnl = context["result"].get("profit", 0.0)
                context["result"]["profit"] = old_pnl + new_pnl
            else:
                context["result"] = result
            
            # Marcar se foi LOSS ou PROFIT global do strike
            total_pnl = context["result"].get("profit", 0.0)
            status = "PROFIT" if total_pnl >= 0 else "LOSS"
            
            # [Ω-FIX] Renomear pasta de forma idempotente (sem concatenar infinitamente)
            base_folder = os.path.basename(audit_dir)
            # Limpar sufixos anteriores de PROFIT/LOSS se existirem (para Hydra slots subsequentes)
            import re
            clean_base = re.sub(r'_(PROFIT|LOSS)_-?\d+$', '', base_folder)
            
            new_folder_name = clean_base + f"_{status}_{int(abs(total_pnl))}"
            new_audit_dir = os.path.join(os.path.dirname(audit_dir), new_folder_name)
            
            # [Ω-FIX] Se o diretório alvo já existe (Hydra collision), usamos um sufixo de ticket
            if os.path.exists(new_audit_dir) and audit_dir != new_audit_dir:
                 new_folder_name += f"_T{ticket}"
                 new_audit_dir = os.path.join(os.path.dirname(audit_dir), new_folder_name)
            
            # 2. Salvar logs capturados no buffer
            all_logs = LOG_BUFFER.get_logs()
            filtered_logs = []
            
            # [PHASE Ω-AUDIT CLEANUP] 
            # Mantemos apenas o que importa para a análise PhD:
            # - Eventos de execução (Action != WAIT)
            # - Mudanças de regime
            # - Alertas OMEGA e SIGNAL
            # - Motivos de WAIT apenas se forem VETO ou SOVEREIGNTY
            # - Pulamos o "ruído" de ciclos de 1s repetitivos
            
            interesting_keywords = [
                "Action=BUY", "Action=SELL", "Action=CLOSE", "DECISION", "EXECUTADO", 
                "SINALIZADO", "FECHADO", "Auditoria", "REGIME CHANGE", "VETO", 
                "GEOMETRY ALERT", "SOVEREIGNTY", "NRO:", "SIGNAL │", "EQUITY_GUARD",
                "PREVIEW", "Strike=", "ERROR", "WARNING", "PNL", "Profit", "IGNITION"
            ]

            skip_until_next_interesting = False
            for line in all_logs:
                # Se a linha anterior nos mandou pular tudo até o próximo ciclo ou evento
                if skip_until_next_interesting:
                    if any(k in line for k in interesting_keywords):
                        skip_until_next_interesting = False
                    else:
                        continue

                # Identificar ciclos de WAIT silenciosos
                if "Action=WAIT" in line:
                    if not any(k in line for k in interesting_keywords):
                        # Se é um WAIT genérico, pulamos ele e as linhas de metadados dele
                        skip_until_next_interesting = True
                        continue
                
                # Se chegamos aqui, a linha é interessante ou metadado de algo interessante
                filtered_logs.append(line)

            with open(os.path.join(audit_dir, "terminal_logs.txt"), "w", encoding="utf-8") as f:
                f.write("\n".join(filtered_logs))
            
            # 3. Captura de Tela (Exit)
            # Salvamos na pasta ATUAL (seja a nova ou a recuperada)
            screenshot_path = os.path.join(audit_dir, "exit_screenshot.png")
            capture_mt5_window(screenshot_path)
            
            # 4. Salvar contexto finalizado
            with open(os.path.join(audit_dir, "lifecycle_context.json"), "w") as f:
                json.dump(context, f, indent=4)
                
            # Renomear diretório final para o novo estado de P&L acumulado
            if os.path.exists(audit_dir) and audit_dir != new_audit_dir:
                try:
                    os.rename(audit_dir, new_audit_dir)
                    audit_dir = new_audit_dir # Atualizar para logs
                except Exception as rename_err:
                    log.warning(f"⚠️ Falha ao renomear auditoria (talvez outro slot travou): {rename_err}")
            
            log.omega(f"🏁 Auditoria Quantum FINALIZADA: {new_folder_name} (P&L: ${total_pnl:.2f})")
            
        except Exception as e:
            log.error(f"❌ Falha ao finalizar auditoria para ticket {ticket}: {e}")

# Singleton
AUDIT_ENGINE = QuantumAuditEngine()
