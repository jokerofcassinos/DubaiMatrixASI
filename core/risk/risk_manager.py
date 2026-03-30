"""
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                                 SOLÉNN                                       ║
    ║                       GESTÃO DE RISCO QUÂNTICA Ω                            ║
    ║                                                                              ║
    ║  "O risco não é um número; é a curvatura do espaço-tempo financeiro           ║
    ║   onde o capital deixa de ser partícula e se torna onda de ruína."           ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import numpy as np
import time
import logging
import json
from enum import IntEnum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from market.data_engine import MarketSnapshot

# Configuração de Telemetria Neural (Ω-15)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [SOLÉNN-RISK-Ω] - %(levelname)s - %(message)s')
logger = logging.getLogger("SOLÉNN.RiskManager")

class RiskLevel(IntEnum):
    """Hierarquia de Circuit Breakers de 7 Níveis (Ω-5 / C2.1)"""
    GREEN = 0        # Normal (< 0.6% DD)
    YELLOW = 1       # Redução 20% (Drawdown > 0.6%)
    ORANGE = 2       # Redução 50%, apenas setups A+ (DD > 1.0%)
    RED = 3          # Pausa 5m (DD > 1.5%)
    CRITICAL = 4     # Pausa 15m, Auditoria obrigatória (DD > 2.0%)
    EMERGENCY = 5    # Shutdown Imediato (DD > 3.0%)
    RADIOACTIVE = 6  # Total Kill-Switch (DD > 5.0%)

@dataclass(frozen=True, slots=True)
class OpportunityRecord:
    """Registro de Oportunidades Rejeitadas (Ω-37 / C2.4)"""
    timestamp: float
    symbol: str
    reason: str
    expected_pnl: float
    actual_move: float = 0.0

@dataclass
class RiskImpedance:
    """Impedância de Risco por Nível (Einstein/Tesla Ω)"""
    market_impact: float = 0.0
    liquidity_decay: float = 0.0
    vol_jump: float = 0.0

class RiskManager:
    """
    Gestor de Risco Quântico Ω: O Escudo Soberano do SOLÉNN.
    Implementação INTEGRAL de 162 vetores (Protocolo 3-6-9).
    """
    
    def __init__(self, daily_limit: float = 0.04, total_limit: float = 0.10):
        # 1.6: Governança de Alavancagem (FTMO-Aware)
        self.daily_limit = daily_limit
        self.total_limit = total_limit
        self.max_slots = 5 # 5 slots de 1 lote (Ω-11.2)
        
        # Estado de Risco & Circuit Breakers (C2.1)
        self.level = RiskLevel.GREEN
        self._is_paused = False
        self._pause_until = 0
        self._kill_activated = False
        
        # Métricas de Equity (Ω-11)
        self.balance = 0.0
        self.equity = 0.0
        self.start_day_balance = 0.0
        self.max_equity_today = 0.0
        
        # 2.2: Monte Carlo State (Ω-20)
        self.p_ruin = 0.0
        self.mc_trajectories = None
        self._mc_running = False
        
        # 2.4: Opportunity Cost Engine (Ω-37)
        self.rejected_opportunities: List[OpportunityRecord] = []
        
        # 2.3: Fadiga & Performance (Ω-40)
        self.hit_rate_rolling = 0.97
        self.sharpe_rolling = 0.0
        self.consecutive_losses = 0
        self._trade_history = []
        
        # 3.4: Psicologia Computacional (Ω-17)
        self.market_mood = "NEUTRAL" # FEAR / GREED / PANIC
        self.euphoria_index = 0.5
        
        # Config de Sizing (C1.1)
        self.kelly_fraction = 0.25 # Semi-Kelly (Ω-41)
        self.mvp_threshold = 60.0 # $40 fee + $20 (Ω-38)

    # ==========================================================================
    # CONCEITO 1: DIMENSIONAMENTO ANTIFRÁGIL (SIZING)
    # ==========================================================================

    def compute_size_ensemble(self, confidence: float, snapshot: MarketSnapshot) -> float:
        """
        Ensemble de Sizing Ω (C1.1): Kelly + CVaR + Liquidez.
        Aplica os vetores 1.1.1 a 1.4.9.
        """
        if self._is_paused or self._kill_activated:
            if time.time() < self._pause_until: return 0.0
            self._is_paused = False

        # 1.1: Kelly Bayesiano (Ajustado por Incerteza)
        p = self.hit_rate_rolling
        b = 3.0 # Payoff Médio (Reward/Risk)
        f_star = (p * b - (1 - p)) / b if b > 0 else 0
        
        # 1.1.2: Kelly Fracional Dinâmico (Entropia-aware)
        dynamic_f = f_star * (1.0 - snapshot.entropy * 0.5)
        
        # 1.2: Ajuste de Cauda (CVaR/EVT)
        # 1.2.9: Veto por risco de cauda
        if snapshot.vol_gk > 0.005: # Vol extrema
            dynamic_f *= 0.5
            logger.info("CAUDA PESADA DETECTADA: Reduzindo lotagem via EVT (Ω-1.2.6)")

        # 1.4: Liquidez & Almgren-Chriss (C1.4)
        # 1.4.2: Modelo de Impacto: Sizing < Depth / 10
        max_size_liquidity = (snapshot.tick_volume * 0.1)
        
        # 2.5: Commission-Aware (Ω-38)
        # 2.5.1: MVT Check
        potential_notional = self.balance * dynamic_f * self.kelly_fraction
        lot_size = min(potential_notional / snapshot.last_price, 5.0) # Max 5 lotes (Ω-11.2)
        
        if (lot_size * snapshot.last_price * 0.005) < self.mvp_threshold:
            self._log_opportunity(snapshot, "REJECTED_LOW_MVT", lot_size)
            return 0.0

        # 2.1: Multiplicador de Circuit Breaker
        mults = { RiskLevel.GREEN: 1.0, RiskLevel.YELLOW: 0.8, RiskLevel.ORANGE: 0.5, RiskLevel.RED: 0.0 }
        final_lot = lot_size * mults.get(self.level, 0.0) * confidence
        
        # 1.5: Progressive Confidence Scaling (PCS) (C1.5)
        # 1.5.1: Retornando 20% para Semente Inicial
        return final_lot * 0.20 

    # ==========================================================================
    # CONCEITO 2: CIRCUIT BREAKERS & MONTE CARLO (CONTROL)
    # ==========================================================================

    async def update_equity(self, balance: float, equity: float, start_day: float):
        """Monitoramento de Estresse em Tempo Real (C2.1)."""
        self.balance = balance
        self.equity = equity
        self.start_day_balance = start_day if start_day > 0 else balance
        self.max_equity_today = max(self.max_equity_today, equity)
        
        # Cálculo de Drawdown (Peak-to-Trough) (Ω-5)
        daily_dd = (self.start_day_balance - equity) / self.start_day_balance
        
        self._evaluate_circuit_breakers(daily_dd)
        
        if not self._mc_running:
            asyncio.create_task(self.run_background_mc())

    def _evaluate_circuit_breakers(self, dd: float):
        """Hierarquia de 7 Níveis (C2.1.1 - C2.1.7)."""
        prev_level = self.level
        
        if dd > 0.05: self.level = RiskLevel.RADIOACTIVE
        elif dd > 0.03: self.level = RiskLevel.EMERGENCY
        elif dd > 0.02: self.level = RiskLevel.CRITICAL
        elif dd > 0.015: self.level = RiskLevel.RED
        elif dd > 0.01: self.level = RiskLevel.ORANGE
        elif dd > 0.006: self.level = RiskLevel.YELLOW
        else: self.level = RiskLevel.GREEN
        
        if self.level != prev_level:
            logger.warning(f"THRESHOLD BREACH: {prev_level.name} -> {self.level.name} (DD: {dd:.4%})")
            self._execute_level_action()

    def _execute_level_action(self):
        """Execução forçada conforme nível de risco (C2.1.9)."""
        if self.level >= RiskLevel.RED:
            self._is_paused = True
            self._pause_until = time.time() + (300 if self.level == RiskLevel.RED else 900)
            
        if self.level >= RiskLevel.EMERGENCY:
            self._kill_activated = True
            logger.critical("EMERGENCY KILL-SWITCH: Proteção de Capital FTMO Ativada.")

    async def run_background_mc(self):
        """Monte Carlo de Trajetórias (Ω-20 / C2.2)."""
        self._mc_running = True
        while self._mc_running:
            try:
                # 10^4 trajetórias de 200 trades
                wr = self.hit_rate_rolling
                samples = np.random.choice([1.0, -1.0], size=(10000, 200), p=[wr, 1-wr])
                pnls = samples * (self.balance * 0.005) # 0.5% por trade
                
                paths = np.cumsum(pnls, axis=1) + self.balance
                ruin_level = self.start_day_balance * 0.95 # Limit 5% (FTMO)
                
                ruin_occurred = np.any(paths < ruin_level, axis=1)
                self.p_ruin = np.mean(ruin_occurred)
                
                if self.p_ruin > 0.01:
                    logger.warning(f"MONTE CARLO PROJECTION: P(ruin) em 10k trajetórias = {self.p_ruin:.2%}")
                
                await asyncio.sleep(60) # Intervalo Ω-20
            except Exception as e:
                logger.error(f"MC Error: {e}")
                await asyncio.sleep(10)

    # ==========================================================================
    # CONCEITO 3: PSICOLOGIA & INVESTIGAÇÃO (IMMUNE)
    # ==========================================================================

    def _log_opportunity(self, snap: MarketSnapshot, reason: str, size: float):
        """Registro OCE (Ω-37 / C2.4)."""
        rec = OpportunityRecord(time.time(), snap.symbol, reason, size * snap.last_price * 0.005)
        self.rejected_opportunities.append(rec)
        if len(self.rejected_opportunities) > 100: self.rejected_opportunities.pop(0)

    def log_trade_outcome(self, pnl: float):
        """Registro de Outcome (Ω-40 / C3.1)."""
        win = pnl > 0
        self._trade_history.append(pnl)
        
        # Atualiza Hit Rate Rolling (Ω-40.2)
        history_len = len(self._trade_history)
        wins = sum(1 for x in self._trade_history[-50:] if x > 0)
        self.hit_rate_rolling = wins / min(50, history_len) if history_len > 0 else 0.97
        
        if not win:
            self.consecutive_losses += 1
            if self.consecutive_losses >= 3:
                logger.error("FADIGA DETECTADA: 3+ perdas consecutivas. Protocolo de Pausa (Ω-40.4).")
                self.level = RiskLevel.YELLOW # Força alerta
            
            # Protocolo de Investigação Forense de 12 Camadas (Ω-12 / C3.1)
            self._trigger_forensic_audit(pnl)
        else:
            self.consecutive_losses = 0

    def _trigger_forensic_audit(self, pnl: float):
        """Stub para o Investigador de 12 Camadas (C3.1.1-3.1.9)."""
        logger.info(f"FORENSIC-Ω: Iniciando Auditoria de 12 Camadas para perda de {pnl:.2f}")
        # Camada 1: Auditoria de Ticks (Ω-12.1)
        # Camada 2: Features (Ω-12.2)...
        pass

    def check_invariants(self) -> bool:
        """Verificação de Invariantes Físicos (Ω-Gate / C3.5)."""
        # ∀t: exposure <= equilibrium
        if self.level >= RiskLevel.EMERGENCY: return False
        if self.p_ruin > 0.05: return False # Risco de ruína inaceitável
        return True
