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
        self._position_index: set = set()  # [Phase Ω-Darwin] Deduplication index (Position ID)
        self._ticket_index: set = set()    # Legacy support
        
        # [Phase Ω-Resilience] Daily Metrics
        self._daily_trades: List[TradeRecord] = []
        self._last_reset_day: int = datetime.now(timezone.utc).day

        # Métricas de Streaks (Calculadas dinamicamente)
        self._consecutive_wins: int = 0
        self._consecutive_losses: int = 0
        self._max_consecutive_wins: int = 0
        self._max_consecutive_losses: int = 0

        # Caminhos de persistência
        self._trades_file = os.path.join(DATA_DIR, "trade_history.json")
        self._load_history()

    def set_initial_balance(self, balance: float):
        """
        Ajusta o ponto de partida da curva de equidade. 
        """
        discrepancy = abs(self._initial_balance - balance)
        
        if discrepancy > 1.0:
            old_val = self._initial_balance
            self._initial_balance = balance
            
            # Reconstruir curva com o novo âncora
            self._rebuild_equity_curve()
            log.omega(f"📊 BALANCE ANCHOR SYNCHRONIZED: ${old_val:,.2f} -> ${balance:,.2f}")
    
    def has_trade(self, position_id: int) -> bool:
        """Verifica se um trade já foi registrado (O(1))."""
        return position_id in self._position_index or position_id in self._ticket_index


    def record_trade(self, trade: TradeRecord):
        """
        Adiciona ou atualiza um trade no histórico e recalcula métricas.
        """
        if not trade or (trade.position_id == 0 and trade.ticket == 0):
            return False

        pos_key = trade.position_id if trade.position_id > 0 else trade.ticket

        # [Phase 36] Commission Deduction
        if trade.commission == 0 and trade.profit != 0 and trade.lot_size > 0:
            # [Ω-PhD] FTMO Hard Alignment: BTCUSD Crypto cost is strictly $40/lot round-trip.
            comm_per_lot = 40.0 if "BTCUSD" in trade.symbol.upper() else OMEGA.get("commission_per_lot", 32.0)
            trade.commission = -(trade.lot_size * comm_per_lot)
            trade.profit += trade.commission 

        trade.is_winner = trade.profit > 0

        # Deduplication & Update Check
        for i, existing in enumerate(self._trades):
            existing_key = existing.position_id if existing.position_id > 0 else existing.ticket
            if existing_key == pos_key:
                profit_diff = trade.profit - existing.profit
                if abs(profit_diff) > 0.001:
                    self._trades[i] = trade
                    self._recalculate_all_metrics()
                    self._save_history()
                return False

        self._trades.append(trade)
        self._daily_trades.append(trade)
        self._position_index.add(pos_key)

        # Recalcular tudo para garantir integridade cronológica
        self._recalculate_all_metrics()
        self._save_history()

        log.debug(f"📊 Trade Recorded: Pos#{pos_key} | P&L=${trade.profit:+.2f} | {'✅ WIN' if trade.is_winner else '❌ LOSS'}")
        return True

    def _recalculate_all_metrics(self):
        """Recalcula equity, drawdown e streaks baseando-se na ordem cronológica real."""
        if not self._trades:
            return

        # [Phase 52.6] Purge Incomplete Trades (trades sem lucro/prejuízo real ou fantasmas de 0)
        self._trades = [t for t in self._trades if abs(t.profit) > 0.0001]

        # 1. Ordenar por tempo de entrada
        self._trades.sort(key=lambda x: x.entry_time)

        # 2. Resetar métricas
        self._equity_curve = [self._initial_balance]
        self._peak_equity = self._initial_balance
        self._max_drawdown = 0.0
        self._max_drawdown_pct = 0.0
        
        self._consecutive_wins = 0
        self._consecutive_losses = 0
        self._max_consecutive_wins = 0
        self._max_consecutive_losses = 0

        now_str = datetime.now(timezone.utc).isoformat()
        now = datetime.fromisoformat(now_str)

        # 3. Rebuild
        for t in self._trades:
            # Equity
            current = self._equity_curve[-1] + t.profit
            self._equity_curve.append(current)
            if current > self._peak_equity:
                self._peak_equity = current
            
            dd = self._peak_equity - current
            self._max_drawdown = max(self._max_drawdown, dd)
            if self._peak_equity > 0:
                self._max_drawdown_pct = max(self._max_drawdown_pct, (dd / self._peak_equity))

            # Streaks (Apenas se o trade for recente - últimas 24h - para evitar spam de alertas antigos)
            try:
                # Tratar tzinfo de forma segura para Python 3.11+
                if 'Z' in t.exit_time:
                    t_time = datetime.fromisoformat(t.exit_time.replace('Z', '+00:00'))
                else:
                    t_time = datetime.fromisoformat(t.exit_time)
                    if t_time.tzinfo is None:
                        t_time = t_time.replace(tzinfo=timezone.utc)
                
                # Se o "now" for naive, forçar UTC
                if now.tzinfo is None:
                    now = now.replace(tzinfo=timezone.utc)
                    
                if (now - t_time).total_seconds() < 86400:
                    if t.is_winner:
                        self._consecutive_wins += 1
                        self._consecutive_losses = 0
                    else:
                        self._consecutive_losses += 1
                        self._consecutive_wins = 0
            except:
                # Fallback se não conseguir parsear data
                if t.is_winner:
                    self._consecutive_wins += 1
                    self._consecutive_losses = 0
                else:
                    self._consecutive_losses += 1
                    self._consecutive_wins = 0

            self._max_consecutive_wins = max(self._max_consecutive_wins, self._consecutive_wins)
            self._max_consecutive_losses = max(self._max_consecutive_losses, self._consecutive_losses)

    def _rebuild_equity_curve(self):
        """Recalcula métricas (alias para _recalculate_all_metrics)."""
        self._recalculate_all_metrics()

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
    def check_ghost_positions(self, active_mt5_tickets: List[int]):
        """
        Detecta 'Ghost Positions' — posições que a ASI acha que existem mas o MT5 não.
        """
        registered_active = {t.ticket for t in self._trades if not t.exit_time}
        ghosts = registered_active - set(active_mt5_tickets)
        
        if ghosts:
            for g_ticket in ghosts:
                log.critical(f"👻 GHOST POSITION DETECTED: Ticket #{g_ticket} missing in MT5!")
                # [Phase Ω-Hardening] Marcar como fechado em erro para não poluir análise
                for t in self._trades:
                    if t.ticket == g_ticket:
                        t.exit_time = datetime.now(timezone.utc).isoformat()
                        t.comment += " | GHOST_SYNC_ERROR"
            self._recalculate_all_metrics()
            self._save_history()
            return list(ghosts)
        return []
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
