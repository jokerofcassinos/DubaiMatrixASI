"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — PERFORMANCE TRACKER                        ║
║     Rastreador de Performance Multi-Dimensional                            ║
║                                                                              ║
║  Registra cada trade, calcula métricas de performance em tempo real,       ║
║  e alimenta o Self Optimizer com dados para auto-evolução.                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import time
import json
import os
import numpy as np
from datetime import datetime, timezone
from collections import deque
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List

from utils.logger import log
from config.settings import DATA_DIR
from config.omega_params import OMEGA


@dataclass
class TradeRecord:
    """Registro completo de um trade."""
    ticket: int = 0
    position_id: int = 0             # ID da posição no MT5
    symbol: str = ""
    action: str = ""                 # BUY / SELL
    lot_size: float = 0.0
    entry_price: float = 0.0
    exit_price: float = 0.0
    sl: float = 0.0
    tp: float = 0.0
    profit: float = 0.0              # Lucro líquido (PnL + Comm + Swap)
    pips: float = 0.0
    commission: float = 0.0
    swap: float = 0.0
    fee: float = 0.0
    duration_seconds: float = 0.0
    regime_at_entry: str = ""
    coherence_at_entry: float = 0.0
    signal_strength: float = 0.0
    entry_time: str = ""
    exit_time: str = ""
    session: str = ""                # LONDON / NY / ASIA / OVERLAP
    is_winner: bool = False
    comment: str = ""                # Comentário persistido


class PerformanceTracker:
    """
    Tracker de Performance — registra e analisa todos os trades.

    Métricas calculadas:
    - Win Rate total e por regime / sessão / direção
    - Profit Factor, Sharpe, Sortino
    - Max Drawdown, Max Runup
    - Média de pips, duração, etc.
    - Expectância matemática
    """

    def __init__(self):
        self._trades: List[TradeRecord] = []
        self._initial_balance: float = OMEGA.get("initial_balance_safety", 100000.0)
        self._equity_curve: List[float] = [self._initial_balance]
        self._peak_equity: float = self._initial_balance
        self._max_drawdown: float = 0.0
        self._max_drawdown_pct: float = 0.0
        self._consecutive_wins: int = 0
        self._consecutive_losses: int = 0
        self._max_consecutive_wins: int = 0
        self._max_consecutive_losses: int = 0
        self._ticket_index: set = set()  # [Phase Ω-Darwin] Deduplication index
        
        # [Phase Ω-Resilience] Daily Metrics
        self._daily_trades: List[TradeRecord] = []
        self._last_reset_day: int = datetime.now(timezone.utc).day

        # Caminhos de persistência
        self._trades_file = os.path.join(DATA_DIR, "trade_history.json")
        self._load_history()

    def set_initial_balance(self, balance: float):
        """
        Ajusta o ponto de partida da curva de equidade. 
        Se a curva só tem o valor inicial default, ou se há uma discrepância massiva, nós a corrigimos.
        """
        # Se houve mudança de magnitude (ex: 100k para 1M), forçamos o re-ancoramento
        discrepancy = abs(self._initial_balance - balance)
        
        if discrepancy > 1.0:
            old_val = self._initial_balance
            self._initial_balance = balance
            
            # Reconstruir curva com o novo âncora
            self._rebuild_equity_curve()
            log.omega(f"📊 BALANCE ANCHOR SYNCHRONIZED: ${old_val:,.2f} -> ${balance:,.2f}")

    def record_trade(self, trade: TradeRecord):
        """
        Adiciona ou atualiza um trade no histórico e recalcula métricas.
        [Phase Ω-Darwin] Sincronização de Fidelidade Extrema.
        Retorna True se for um trade NOVO.
        """
        if not trade or trade.ticket == 0:
            return False

        # Reset diário se necessário
        current_day = datetime.now(timezone.utc).day
        if current_day != self._last_reset_day:
            self._daily_trades = []
            self._last_reset_day = current_day

        # [Phase 36] Commission Deduction (Fiscal Sovereignty)
        # Se o MT5 não reportou comissão ainda, usamos o prior do OMEGA
        if trade.commission == 0 and trade.profit != 0 and trade.lot_size > 0:
            comm_per_lot = OMEGA.get("commission_per_lot", 15.0)
            trade.commission = -(trade.lot_size * comm_per_lot)
            trade.profit += trade.commission 

        # [CRITICAL FIX] Win status must be based on net profit
        trade.is_winner = trade.profit > 0

        # [Phase Ω-Darwin] Deduplication & Update Check
        for i, existing in enumerate(self._trades):
            if existing.ticket == trade.ticket:
                # Se o profit mudou (ajuste de swap/comissão real do MT5), recalcular
                profit_diff = trade.profit - existing.profit
                if abs(profit_diff) > 0.001:
                    log.debug(f"🔄 TRADE UPDATE [{trade.ticket}]: PnL Diff ${profit_diff:+.4f}")
                    self._trades[i] = trade
                    self._rebuild_equity_curve()
                    self._save_history()
                return False

        self._trades.append(trade)
        self._daily_trades.append(trade)
        self._ticket_index.add(trade.ticket)

        # Atualizar equity curve (Saldo Absoluto)
        current_equity = self._equity_curve[-1] + trade.profit
        self._equity_curve.append(current_equity)

        # Atualizar peak e drawdown (Baseado no saldo total da conta)
        if current_equity > self._peak_equity:
            self._peak_equity = current_equity
        
        dd = self._peak_equity - current_equity
        if dd > self._max_drawdown:
            self._max_drawdown = dd
        
        if self._peak_equity > 0:
            # [Phase Ω-Resilience] Drawdown % real sobre o capital (Fração 0.0 - 1.0)
            dd_pct = (dd / self._peak_equity)
            if dd_pct > self._max_drawdown_pct:
                self._max_drawdown_pct = dd_pct

        # Consecutivos
        if trade.is_winner:
            self._consecutive_wins += 1
            self._consecutive_losses = 0
            self._max_consecutive_wins = max(self._max_consecutive_wins, self._consecutive_wins)
        else:
            self._consecutive_losses += 1
            self._consecutive_wins = 0
            self._max_consecutive_losses = max(self._max_consecutive_losses, self._consecutive_losses)

        # Persistir
        self._save_history()

        log.info(
            f"📊 Trade Recorded: {trade.action} #{trade.ticket} | "
            f"P&L=${trade.profit:+.2f} | "
            f"{'✅ WIN' if trade.is_winner else '❌ LOSS'} | "
            f"Regime={trade.regime_at_entry}"
        )
        return True

    def _rebuild_equity_curve(self):
        """Recalcula toda a curva de equidade e drawdown do zero."""
        self._equity_curve = [self._initial_balance]
        self._peak_equity = self._initial_balance
        self._max_drawdown = 0.0
        self._max_drawdown_pct = 0.0
        
        for t in self._trades:
            current = self._equity_curve[-1] + t.profit
            self._equity_curve.append(current)
            if current > self._peak_equity:
                self._peak_equity = current
            dd = self._peak_equity - current
            if dd > self._max_drawdown:
                self._max_drawdown = dd
            if self._peak_equity > 0:
                # [Phase Ω-Resilience] Fixed: Fraction 0-1
                self._max_drawdown_pct = max(self._max_drawdown_pct, (dd / self._peak_equity))

    def _load_history(self):
        """Carrega histórico de trades persistido."""
        try:
            if os.path.exists(self._trades_file):
                with open(self._trades_file, "r") as f:
                    data = json.load(f)
                
                temp_trades = []
                for item in data:
                    t = TradeRecord(**item)
                    t.is_winner = t.profit > 0
                    temp_trades.append(t)
                
                # Sort trades by time
                temp_trades.sort(key=lambda x: x.entry_time)

                for trade in temp_trades:
                    if trade.ticket in self._ticket_index:
                        continue
                    self._trades.append(trade)
                    self._ticket_index.add(trade.ticket)
                    
                    # Carregar no diário se for de hoje
                    try:
                        trade_dt = datetime.fromisoformat(trade.entry_time)
                        if trade_dt.date() == datetime.now(timezone.utc).date():
                            self._daily_trades.append(trade)
                    except ValueError:
                        pass

                self._rebuild_equity_curve()

                if self._trades:
                    log.info(f"📂 Carregados {len(self._trades)} trades do histórico. WR={self.win_rate:.1%}")
        except Exception as e:
            log.error(f"Erro ao carregar histórico: {e}")

    @property
    def total_trades(self) -> int:
        return len(self._trades)

    @property
    def win_rate(self) -> float:
        if not self._trades:
            return 0.0
        winners = sum(1 for t in self._trades if t.is_winner)
        return winners / len(self._trades)

    @property
    def total_profit(self) -> float:
        return sum(t.profit for t in self._trades)

    @property
    def profit_factor(self) -> float:
        """Gross Profit / Gross Loss."""
        gross_profit = sum(t.profit for t in self._trades if t.profit > 0)
        gross_loss = abs(sum(t.profit for t in self._trades if t.profit < 0))
        return gross_profit / gross_loss if gross_loss > 0 else float('inf')

    @property
    def expectancy(self) -> float:
        """Expectância matemática por trade."""
        if not self._trades:
            return 0.0
        return self.total_profit / len(self._trades)

    @property
    def sharpe_ratio(self) -> float:
        """Sharpe Ratio simplificado (sem risk-free rate)."""
        if len(self._trades) < 2:
            return 0.0
        profits = np.array([t.profit for t in self._trades])
        if np.std(profits) == 0:
            return 0.0
        return np.mean(profits) / np.std(profits) * np.sqrt(252)

    @property
    def sortino_ratio(self) -> float:
        """Sortino Ratio (penaliza apenas downside)."""
        if len(self._trades) < 2:
            return 0.0
        profits = np.array([t.profit for t in self._trades])
        downside = profits[profits < 0]
        if len(downside) == 0 or np.std(downside) == 0:
            return float('inf') if np.mean(profits) > 0 else 0.0
        return np.mean(profits) / np.std(downside) * np.sqrt(252)

    def win_rate_by_regime(self) -> Dict[str, float]:
        """Win rate segmentado por regime de mercado."""
        regimes = {}
        for t in self._trades:
            regime = t.regime_at_entry or "UNKNOWN"
            if regime not in regimes:
                regimes[regime] = {"wins": 0, "total": 0}
            regimes[regime]["total"] += 1
            if t.is_winner:
                regimes[regime]["wins"] += 1

        return {
            regime: data["wins"] / data["total"] if data["total"] > 0 else 0.0
            for regime, data in regimes.items()
        }

    def win_rate_by_session(self) -> Dict[str, float]:
        """Win rate segmentado por sessão de mercado."""
        sessions = {}
        for t in self._trades:
            session = t.session or "UNKNOWN"
            if session not in sessions:
                sessions[session] = {"wins": 0, "total": 0}
            sessions[session]["total"] += 1
            if t.is_winner:
                sessions[session]["wins"] += 1

        return {
            session: data["wins"] / data["total"] if data["total"] > 0 else 0.0
            for session, data in sessions.items()
        }

    def win_rate_by_direction(self) -> Dict[str, float]:
        """Win rate segmentado por BUY/SELL."""
        dirs = {"BUY": {"wins": 0, "total": 0}, "SELL": {"wins": 0, "total": 0}}
        for t in self._trades:
            d = t.action if t.action in dirs else "BUY"
            dirs[d]["total"] += 1
            if t.is_winner:
                dirs[d]["wins"] += 1

        return {
            d: data["wins"] / data["total"] if data["total"] > 0 else 0.0
            for d, data in dirs.items()
        }

    @property
    def recent_stats(self) -> dict:
        """Métricas dos últimos 50 trades para adaptação rápida."""
        recent = self._trades[-50:]
        if not recent:
            return {"win_rate": 0.0, "avg_win": 0.0, "avg_loss": 0.0, "expectancy": 0.0}
        
        wins = [t.profit for t in recent if t.is_winner]
        losses = [t.profit for t in recent if not t.is_winner]
        
        wr = len(wins) / len(recent)
        aw = np.mean(wins) if wins else 0.0
        al = abs(np.mean(losses)) if losses else 0.0
        exp = (wr * aw) - ((1 - wr) * al)
        
        return {
            "win_rate": wr,
            "avg_win": aw,
            "avg_loss": al,
            "expectancy": exp,
            "count": len(recent)
        }

    @property
    def full_report(self) -> dict:
        """Relatório completo de performance."""
        recent = self.recent_stats
        return {
            "total_trades": self.total_trades,
            "total_wins": sum(1 for t in self._trades if t.is_winner),
            "total_losses": sum(1 for t in self._trades if not t.is_winner),
            "win_rate": self.win_rate,
            "recent_win_rate": recent["win_rate"],
            "recent_expectancy": recent["expectancy"],
            "total_profit": self.total_profit,
            "gross_profit": sum(t.profit for t in self._trades if t.is_winner),
            "gross_loss": abs(sum(t.profit for t in self._trades if not t.is_winner)),
            "daily_profit": sum(t.profit for t in self._daily_trades if t.is_winner),
            "daily_loss": abs(sum(t.profit for t in self._daily_trades if not t.is_winner)),
            "daily_net": sum(t.profit for t in self._daily_trades),
            "profit_factor": self.profit_factor,
            "expectancy": self.expectancy,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "max_drawdown": self._max_drawdown,
            "max_drawdown_pct": self._max_drawdown_pct,
            "max_consecutive_wins": self._max_consecutive_wins,
            "max_consecutive_losses": self._max_consecutive_losses,
            "current_streak_wins": self._consecutive_wins,
            "current_streak_losses": self._consecutive_losses,
            "avg_profit": np.mean([t.profit for t in self._trades]) if self._trades else 0,
            "avg_win": np.mean([t.profit for t in self._trades if t.is_winner]) if any(t.is_winner for t in self._trades) else 0,
            "avg_loss": np.mean([t.profit for t in self._trades if not t.is_winner]) if any(not t.is_winner for t in self._trades) else 0,
            "by_regime": self.win_rate_by_regime(),
            "by_session": self.win_rate_by_session(),
            "by_direction": self.win_rate_by_direction(),
            "peak_equity": self._peak_equity,
        }

    def _save_history(self):
        """Persiste o histórico de trades em JSON."""
        try:
            os.makedirs(os.path.dirname(self._trades_file), exist_ok=True)
            data = [asdict(t) for t in self._trades[-1000:]]  # Últimos 1000
            with open(self._trades_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            log.error(f"Erro ao salvar histórico de trades: {e}")
