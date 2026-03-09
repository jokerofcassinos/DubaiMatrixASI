"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — HOLOGRAPHIC MEMORY AGENT                    ║
║     Memória Epistêmica — Aprende com perdas recentes e veta repetições.      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import time
import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal
from execution.trade_registry import registry as trade_registry
from utils.logger import log

class HolographicMemoryAgent(BaseAgent):
    """
    [Phase Ω-Transcendence] Memória Holográfica de Curto Prazo.
    Analisa os últimos trades perdedores registrados no TradeRegistry.
    Se a "assinatura" (Regime + Força do Sinal + Coerência) do mercado atual for 
    muito similar à assinatura de um Loss recente, ele emite um VETO direcional forte.
    """
    def __init__(self, weight=3.0):
        super().__init__("HolographicMemory", weight)
        self.last_sync_time = 0
        self.loss_signatures = []

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        now = time.time()
        
        # Sincronizar assinaturas de perdas a cada 60 segundos
        if now - self.last_sync_time > 60:
            self._sync_loss_signatures()
            self.last_sync_time = now

        if not self.loss_signatures:
            return AgentSignal(self.name, 0.0, 0.0, "NO_LOSS_MEMORY", self.weight)

        current_regime = snapshot.regime.value if hasattr(snapshot.regime, 'value') else str(snapshot.regime)
        
        # O agente analisa se a condição atual de mercado é "tóxica" baseada em erros passados
        # No nível de agente não temos o "quantum_state" final, então avaliamos a similaridade de regime e volatilidade.
        current_atr = snapshot.atr if snapshot.atr else 0.1
        
        danger_score = 0.0
        match_count = 0
        
        for sig in self.loss_signatures:
            if sig['regime'] == current_regime:
                # Verificar se a volatilidade é similar (± 20%)
                if abs(sig['atr'] - current_atr) / current_atr < 0.20:
                    match_count += 1
                    danger_score += 1.0
                    
        signal = 0.0
        conf = 0.0
        reason = "MEMORY_CLEAR"
        
        if match_count >= 2:
            # Se erramos 2 vezes ou mais nessa mesma condição recentemente, alertamos contra agir
            # Emitimos um sinal de neutralidade extrema (Zero) com alta confiança para "puxar" o sinal pra baixo
            # No entanto, a forma mais efetiva de veto é emitir um sinal contrário à tendência
            trend_dir = snapshot.indicators.get("M5_ema_9", [0])[-1] - snapshot.indicators.get("M5_ema_50", [0])[-1]
            direction = -1.0 if trend_dir > 0 else 1.0 # Contrário à tendência aparente
            
            signal = direction
            conf = min(0.95, match_count * 0.3)
            reason = f"TOXIC_MEMORY_MATCH (Hits={match_count} in {current_regime})"
            log.debug(f"🧠 [EPISTEMIC MEMORY] Condição Tóxica detectada. Veto Sugerido.")
            
        return AgentSignal(self.name, signal, conf, reason, self.weight)

    def _sync_loss_signatures(self):
        """Extrai a assinatura dos últimos trades perdedores para evitar repeti-los."""
        try:
            from core.evolution.performance_tracker import PerformanceTracker
            # Como instanciar ou acessar o singleton do tracker?
            # A forma mais segura por hora é ler o JSON de trades ou usar o trade_registry
            # O trade_registry tem intent (que é salvo no strike). Se tivermos o resultado...
            
            # Vamos ler diretamente o histórico consolidado do arquivo
            import os, json
            from config.settings import DATA_DIR
            history_file = os.path.join(DATA_DIR, "trade_history.json")
            if not os.path.exists(history_file):
                return
                
            with open(history_file, 'r') as f:
                trades = json.load(f)
                
            # Filtrar perdas das últimas 24 horas
            recent_losses = []
            for t in trades[-50:]: # Últimos 50
                if t.get('profit', 0) < 0:
                    recent_losses.append(t)
            
            new_signatures = []
            for loss in recent_losses[-10:]: # Últimos 10 losses
                pos_id = loss.get('position_id')
                intent = trade_registry.get_intent(pos_id)
                if intent:
                    new_signatures.append({
                        'regime': intent.get('regime', 'UNKNOWN'),
                        'confidence': intent.get('confidence', 0),
                        'atr': intent.get('atr', 100.0) # Assumindo fallback
                    })
                else:
                    # Falback para dados do log
                    new_signatures.append({
                        'regime': loss.get('regime_at_entry', 'UNKNOWN'),
                        'atr': 100.0
                    })
            self.loss_signatures = new_signatures
        except Exception as e:
            log.error(f"Erro ao sincronizar Memória Epistêmica: {e}")
