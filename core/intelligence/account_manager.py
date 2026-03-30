"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              SOLÉNN — ACCOUNT MANAGER Ω (SOVEREIGN CAPITAL)                  ║
║     Account Manager: Balance, Equity, Margin, Commissions                    ║
║     Implementing: Adaptive Commission Discovery, Auto-Reconciliation          ║
║     Framework 3-6-9: Phase 4(Ω-21) - Concept 1.4                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional

class AccountManager:
    """
    [Ω-CORE] Sovereign Capital Orchestrator.
    Synchronizes financial state with MT5 and optimizes cost-efficiency.
    """
    def __init__(self, hftp_server: Any):
        self.hftp = hftp_server
        self.logger = logging.getLogger("SOLENN.Account")
        
        # [Ω-V1.4.1] Financial State
        self.balance: float = 0.0
        self.equity: float = 0.0
        self.margin: float = 0.0
        self.free_margin: float = 0.0
        self.leverage: int = 100
        
        # [Ω-V1.4.3] Broker Commission Detection
        self.commission_per_lot_rt: float = 32.0 # Default FTMO
        
        self.is_synced = False
        self.hftp.register_handler("ACCOUNT", self._on_account_update)

    async def _on_account_update(self, payload: Dict[str, Any], client_id: str):
        """[Ω-V1.4.1] Real-time state synchronization."""
        self.balance = payload.get("bal", 0.0)
        self.equity = payload.get("eq", 0.0)
        self.margin = payload.get("mar", 0.0)
        self.free_margin = payload.get("fmar", 0.0)
        
        # [Ω-V1.4.4] Dynamic Leverage detection
        new_leverage = payload.get("lev", 100)
        if new_leverage != self.leverage:
            self.logger.warning(f"⚠️ [Ω-Acc] Leverage Change Detected: 1:{self.leverage} -> 1:{new_leverage}")
            self.leverage = new_leverage
            
        # [Ω-V1.4.3] Intelligent Commission Update
        comm = payload.get("comm", 0.0)
        if comm > 0 and abs(comm - self.commission_per_lot_rt) > 0.01:
            self.commission_per_lot_rt = comm
            self.logger.info(f"💰 [Ω-Acc] Commission Adjusted to ${comm:.2f}/lot (Round-Turn)")
            
        self.is_synced = True

    async def poll_account(self, client_id: str = "DEFAULT"):
        """Requests account snapshot from MT5."""
        await self.hftp.send_message(client_id, "POLL_ACCOUNT", {"ts": time.time()})

    def get_balance(self) -> float:
        """[Ω-V1.4.1] Sovereign Balance."""
        return self.balance if self.balance > 0 else 100000.0 # Default for bootstrap

    def get_equity(self) -> float:
        """[Ω-V1.4.1] Sovereign Equity."""
        return self.equity if self.equity > 0 else 100000.0

    def get_risk_snapshot(self) -> Dict[str, float]:
        """[Ω-V1.4.2] Provides margin usage metrics for the Brain."""
        return {
            "equity": self.equity,
            "margin_usage": (self.margin / self.equity) * 100 if self.equity > 0 else 0,
            "free_margin": self.free_margin,
            "comm_lot": self.commission_per_lot_rt
        }
