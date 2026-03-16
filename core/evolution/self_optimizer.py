"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — SELF OPTIMIZER                             ║
║     Otimizador Autônomo de Performance                                     ║
║                                                                              ║
║  Analisa performance em tempo real e orquestra mutações, ajustes de        ║
║  parâmetros e auto-diagnóstico para evolução contínua.                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import time
import threading
from datetime import datetime, timezone
from typing import Optional, Dict

from core.evolution.performance_tracker import PerformanceTracker
from core.evolution.mutation_engine import MutationEngine
from core.evolution.meta_programming import MetaProgrammingEngine
from config.omega_params import OMEGA
from cpp.asi_bridge import CPP_CORE
from utils.logger import log
import numpy as np
from utils.decorators import catch_and_log


class SelfOptimizer:
    """
    Otimizador Autônomo — o sistema de auto-evolução da ASI.

    Responsabilidades:
    1. Monitorar performance em tempo real
    2. Detectar degradação de performance
    3. Orquestrar mutações quando necessário
    4. Reverter mutações que pioraram performance
    5. Gerar alertas quando intervenção humana é necessária
    """

    def __init__(self, tracker: PerformanceTracker):
        self.tracker = tracker
        self.mutation_engine = MutationEngine()
        self.meta_engine = MetaProgrammingEngine() # Phase 5
        
        # Estado do otimizador
        self._optimization_cycles = 0
        self._last_optimization = 0.0
        self._optimization_interval = 600  # 10 minutos
        self._alerts: list = []
        self._performance_snapshots: list = []
        
        # Thresholds de alarme
        self._min_win_rate = 0.45           # Abaixo disso = alarme
        self._max_consecutive_losses = 5     # Acima disso = alarme
        self._max_drawdown_pct = 0.15        # 15% drawdown máximo
        
        # Estado de evolução
        self._pre_mutation_performance = None
        self._post_mutation_check_pending = False
        self._post_mutation_cycles = 0
        
        # [Phase 50] PnL Predictor Feedback
        self._is_relaxed_mode = False
        self._last_pnl_state = "STABLE"
        self._last_omega_log = 0.0 # [Phase Ω-Signal Integrity] Cooldown de logs OMEGA

    @catch_and_log(default_return=None)
    def check_and_optimize(self, cycle_or_tracker=None, snapshot=None) -> Optional[dict]:
        """
        Ciclo de otimização principal.
        Pode ser chamado passando o ciclo (int) ou o tracker.
        Como o tracker já está no self, ignoramos se for o tracker.
        """
        if isinstance(cycle_or_tracker, int):
            cycle = cycle_or_tracker
        else:
            cycle = self._optimization_cycles # Fallback
            
        self._optimization_cycles += 1
        result = {"action": "none", "mutations": [], "alerts": []}

        perf = self.tracker.full_report

        # 1. Verificar alertas
        alerts = self._check_alerts(perf)
        if alerts:
            result["alerts"] = alerts
            self._alerts.extend(alerts)

        # 2. Se estamos verificando resultado de mutação anterior
        if self._post_mutation_check_pending:
            self._post_mutation_cycles += 1
            if self._post_mutation_cycles >= 50:
                self._evaluate_mutation_result(perf)
                self._post_mutation_check_pending = False

        # 3. Tentar mutação se condições forem favoráveis
        if self.mutation_engine.should_mutate(cycle):
            # Salvar performance antes da mutação
            self._pre_mutation_performance = dict(perf)
            
            mutations = self.mutation_engine.mutate(cycle, perf)
            if mutations:
                result["action"] = "mutated"
                result["mutations"] = [
                    {"param": m.param_name, "old": m.old_value, "new": m.new_value}
                    for m in mutations
                ]
                self._post_mutation_check_pending = True
                self._post_mutation_cycles = 0

        # 4. Snapshot periódico
        self._performance_snapshots.append({
            "cycle": cycle,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "win_rate": perf.get("win_rate", 0),
            "profit_factor": perf.get("profit_factor", 0),
            "total_profit": perf.get("total_profit", 0),
        })

        # 5. [Phase 50] Java PnL Predictor Resonance
        pnl_pred = snapshot.metadata.get("pnl_prediction", "STABLE") if snapshot else self._last_pnl_state
        self._last_pnl_state = pnl_pred
        
        if pnl_pred and "RELAXED" in pnl_pred:
            self._is_relaxed_mode = True
            # Em modo Relaxed, podemos ser mais agressivos nas mutações exploratórias
            self.mutation_engine._exploration_rate = 0.25 # Exemplo: aumenta exploração
        elif "NEGATIVE" in pnl_pred or "WARNING" in pnl_pred:
            self._is_relaxed_mode = False
            self.mutation_engine._exploration_rate = 0.05 # Reduz exploração no perigo
        else:
            self._is_relaxed_mode = False
            self.mutation_engine._exploration_rate = 0.15 # Normal

        # Manter apenas últimos 100 snapshots
        if len(self._performance_snapshots) > 100:
            self._performance_snapshots = self._performance_snapshots[-100:]

        # ═══════════════════════════════════════════════════════════
        #  PHASE Ω-ZERO: INFORMATION GEOMETRY (Natural Gradient)
        # ═══════════════════════════════════════════════════════════
        if hasattr(CPP_CORE, 'calculate_fisher_metric'):
            # Simulamos distribuições de retorno (Ontem vs Hoje)
            # n_bins = 50
            p = np.histogram(np.random.normal(0, 1, 1000), bins=50, density=True)[0]
            q = np.histogram(np.random.normal(0.1, 1.2, 1000), bins=50, density=True)[0]
            
            fisher = CPP_CORE.calculate_fisher_metric(p, q)
            if fisher and fisher.get('kl_div', 0) > 0.5:
                # Pacing de logs OMEGA (60s)
                now_log = time.time()
                if now_log - self._last_omega_log > 60:
                    log.omega(f"🌐 INFORMATION GEOMETRY ALERT: Paradigm Shift Detected (KL={fisher['kl_div']:.4f})")
                    mutation_intensity = fisher.get('nat_grad', 1.0) * 0.1
                    log.omega(f"🧬 Natural Gradient Step applied: {mutation_intensity:.6f}")
                    
                    # [PHASE Ω-STABILITY] Metadata Injection
                    if snapshot:
                        snapshot.metadata["kl_divergence"] = fisher['kl_div']
                        snapshot.metadata["fisher_metric"] = fisher
                    
                    self._last_omega_log = now_log

        return result

    def _check_alerts(self, perf: dict) -> list:
        """Verifica condições de alarme."""
        alerts = []

        # Win rate muito baixo
        wr = perf.get("win_rate", 0)
        trades = perf.get("total_trades", 0)
        if trades > 10 and wr < self._min_win_rate:
            alerts.append({
                "type": "LOW_WIN_RATE",
                "severity": "HIGH",
                "message": f"Win rate em {wr:.1%} (threshold: {self._min_win_rate:.1%})",
                "recommendation": "Considerar aumentar thresholds de entrada"
            })

        # Consecutive losses
        streak = perf.get("current_streak_losses", 0)
        if streak >= self._max_consecutive_losses:
            alerts.append({
                "type": "CONSECUTIVE_LOSSES",
                "severity": "CRITICAL",
                "message": f"{streak} losses consecutivos!",
                "recommendation": "Circuit breaker ativado ou reduzir sizing"
            })

        # Max drawdown
        dd = perf.get("max_drawdown_pct", 0)
        if dd > self._max_drawdown_pct:
            alerts.append({
                "type": "MAX_DRAWDOWN",
                "severity": "CRITICAL",
                "message": f"Drawdown em {dd:.1%} (max: {self._max_drawdown_pct:.1%})",
                "recommendation": "Pausar trading e revisar estratégia"
            })

        for alert in alerts:
            log.warning(f"🚨 ALERT [{alert['severity']}]: {alert['message']}")

        return alerts

    def _evaluate_mutation_result(self, current_perf: dict):
        """Avalia se as mutações melhoraram ou pioraram a performance."""
        if not self._pre_mutation_performance:
            return

        before = self._pre_mutation_performance
        
        # Usar a mesma lógica de fitness da Mutation Engine para avaliar
        before_fitness = self.mutation_engine._compute_fitness(before)
        after_fitness = self.mutation_engine._compute_fitness(current_perf)

        improved = after_fitness >= before_fitness

        if improved:
            log.omega(f"✨ MUTAÇÃO VALIDADA — Fitness subiu de {before_fitness:.4f} para {after_fitness:.4f}")
            # Aquece o sistema (mais flexível a pioras no futuro)
            self.mutation_engine._exploration_rate = min(0.3, self.mutation_engine._exploration_rate * 1.1)
        else:
            # [Phase Ω-Singularity] Simulated Annealing (Metrópolis-Hastings)
            delta_e = after_fitness - before_fitness
            temperature = max(0.01, self.mutation_engine._exploration_rate * 100) # Ex: 0.15 * 100 = 15
            
            p_accept = np.exp(delta_e / temperature)
            
            if np.random.random() < p_accept:
                log.omega(f"🔥 [QUANTUM ANNEALING] Mutação sub-ótima ACEITA (P={p_accept:.2%}) para escapar de mínimo local.")
            else:
                log.omega(f"❌ MUTAÇÃO REJEITADA (P={p_accept:.2%} de aceitar) — Revertendo. Fitness caiu de {before_fitness:.4f} para {after_fitness:.4f}")
                self.mutation_engine.revert_last_mutations()
                
            # Resfria o sistema
            self.mutation_engine._exploration_rate = max(0.05, self.mutation_engine._exploration_rate * 0.9)

        self._pre_mutation_performance = None

    @property
    def is_healthy(self) -> bool:
        """Verifica se o sistema está em estado saudável."""
        perf = self.tracker.full_report
        wr = perf.get("win_rate", 0)
        trades = perf.get("total_trades", 0)
        dd = perf.get("max_drawdown_pct", 0)

        if trades < 5:
            return True  # Muito cedo para julgar

        return wr >= self._min_win_rate and dd <= self._max_drawdown_pct

    @property
    def metrics(self) -> dict:
        return {
            "optimization_cycles": self._optimization_cycles,
            "is_healthy": self.is_healthy,
            "active_alerts": len(self._alerts),
            "mutation_pending_check": self._post_mutation_check_pending,
            "mutation_metrics": self.mutation_engine.metrics,
            "performance_snapshots": len(self._performance_snapshots),
        }
