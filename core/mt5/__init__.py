"""
SOLÉNN v2 — MT5 Integration Bridge
Connects MetaTrader5 terminal to SOLÉNN Ω Brain (Config→Data→Agents→Decision→Execution→Evolution)

Concept 1: MT5 Data Bridge (MT5-01 to MT5-54)
Concept 2: MT5 Order Execution (MT5-55 to MT5-108)
Concept 3: SOLÉNN MT5 Integration (MT5-109 to MT5-162)
"""

from core.mt5.bridge import MT5Bridge
from core.mt5.data_stream import MT5Connection, MT5Tick, MT5Candle, MT5DataStreamer
from core.mt5.executor import MT5OrderExecutor, OrderType, OrderRequest, PositionManager
from core.mt5.bridge import MT5Bridge as MT5DataBridge

__all__ = [
    "MT5Bridge", "MT5Connection", "MT5Tick", "MT5Candle",
    "MT5DataStreamer", "MT5OrderExecutor", "OrderType", "OrderRequest",
    "PositionManager", "MT5DataBridge",
]
