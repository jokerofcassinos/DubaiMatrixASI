import os
import time
from datetime import datetime
from typing import List, Dict, Any
from utils.log_buffer import LOG_BUFFER
from config.settings import LOG_DIR

class LifecycleLogger:
    """
    [Ω-LIFECYCLE] Captura a 'Verdade Completa' de cada ciclo de trading.
    Dumps formatados de sinal + formação + execução para asi_trades.log.
    """
    def __init__(self):
        self.trades_log_path = os.path.join(LOG_DIR, "asi_trades.log")
        self._start_pos = 0

    def start_cycle(self):
        """Marca o início da captura de logs para o ciclo atual."""
        self._start_pos = len(LOG_BUFFER.buffer)

    def end_cycle(self, cycle_id: int, decision: Any, quantum_state: Any, snapshot: Any):
        """
        Finaliza a captura, extrai logs do buffer e escreve no log de trades
        se a decisão for relevante (ou a cada N ciclos se for WAIT).
        """
        # Sempre logar se for BUY/SELL ou se o usuário quiser (para debug)
        from core.decision.trinity_core import Action
        is_trade = decision and decision.action in [Action.BUY, Action.SELL]
        
        # [Ω-STRICT] Logar APENAS ordens executadas, conforme ordem do CEO
        if not is_trade:
            return 

        logs = self._get_buffered_logs()
        self._write_lifecycle_block(cycle_id, decision, quantum_state, snapshot, logs)

    def _get_buffered_logs(self) -> List[str]:
        current_buffer = list(LOG_BUFFER.buffer)
        return current_buffer[self._start_pos:]

    def _write_lifecycle_block(self, cycle_id: int, decision: Any, quantum_state: Any, snapshot: Any, logs: List[str]):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        regime = snapshot.regime.value if hasattr(snapshot.regime, 'value') else "UNKNOWN"
        action = decision.action.value if decision else "NONE"
        phi = getattr(quantum_state, 'phi', 0)
        coherence = getattr(quantum_state, 'coherence', 0)
        signal = getattr(quantum_state, 'raw_signal', 0)

        header = f"\n{'═'*80}\n"
        header += f"🚀 [CYCLE LIFECYCLE] #{cycle_id} | {now} | Regime: {regime}\n"
        header += f"{'─'*80}\n"
        
        # Seção de Formação do Sinal
        formation = f"📊 [SIGNAL FORMATION]\n"
        formation += f"   Action: {action} | Signal: {signal:+.4f} | Φ: {phi:.4f} | Coherence: {coherence:.2%}\n"
        
        if quantum_state and hasattr(quantum_state, 'metadata'):
            bulls = len(quantum_state.metadata.get("bull_agents", []))
            bears = len(quantum_state.metadata.get("bear_agents", []))
            formation += f"   Swarm Intensity: BULL[{bulls}] vs BEAR[{bears}]\n"

        # Seção de Execução
        execution = f"\n🎯 [DECISION RATIONALE]\n"
        execution += f"   {decision.reasoning if decision else 'N/A'}\n"
        
        # Logs Originais (Processo de Pensamento)
        original_text = f"\n📜 [INTERNAL LOGS & THINKING PROCESS]\n"
        for line in logs:
            original_text += f"   {line}\n"

        footer = f"{'═'*80}\n"

        block = header + formation + execution + original_text + footer
        
        try:
            with open(self.trades_log_path, "a", encoding="utf-8") as f:
                f.write(block)
        except Exception:
            pass
