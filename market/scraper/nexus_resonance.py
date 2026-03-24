"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     DUBAI MATRIX ASI — NEXUS RESONANCE                       ║
║        Radar Cross-Asset de Latência Zero para Arbitragem Macro            ║
║                                                                              ║
║  Mapeia XAUUSD, Índices e DXY para prever movimentos no BTCUSD.              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import time
import threading
from collections import deque
import numpy as np

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None

from utils.logger import log

class NexusScraper(threading.Thread):
    """
    Rastreador de Ressonância Cross-Asset.
    Obtém Ticks de ativos correlacionados no mesmo terminal MT5.
    Calcula Lead/Lag Momentum.
    """

    def __init__(self, interval_sec: float = 1.0):
        super().__init__(daemon=True)
        self.interval = interval_sec
        self.running = False
        
        # Símbolos Alvo (Tentará resolver alias disponíveis na corretora FTMO/Prop)
        self.target_symbols = [
            {"name": "GOLD", "aliases": ["XAUUSD", "GOLD", "XAUUSD.cash"]},
            {"name": "NASDAQ", "aliases": ["US100.cash", "USTEC", "NQ100", "NAS100"]},
            {"name": "SP500", "aliases": ["US500.cash", "US500", "SPX500"]},
            {"name": "ETH", "aliases": ["ETHUSD", "ETHUSD.cash", "Ethereum"]}
        ]
        
        self.resolved_symbols = {}
        self.history = {item["name"]: deque(maxlen=60) for item in self.target_symbols} # 60s memory
        
        # Output Metrics
        self.resonance_score = 0.0
        self.breakout_signals = []
        self._last_log_time = 0.0

    def _resolve_symbols(self):
        """Descobre o nome exato do ticker na corretora atual."""
        if not mt5 or not mt5.initialize():
            return
            
        for target in self.target_symbols:
            asset_name = target["name"]
            if asset_name in self.resolved_symbols:
                continue
                
            for alias in target["aliases"]:
                info = mt5.symbol_info(alias)
                if info is not None:
                    mt5.symbol_select(alias, True)
                    self.resolved_symbols[asset_name] = alias
                    log.info(f"🌍 [NEXUS] Ativo correlacionado resolvido: {asset_name} -> {alias}")
                    break

    def run(self):
        self.running = True
        log.omega("⚡ 🌍 [PROJECT NEXUS] Scraper Cross-Asset INICIADO.")
        
        # Aguarda a MT5Bridge conectar globalmente
        time.sleep(5)
        self._resolve_symbols()

        while self.running:
            try:
                self._update_ticks()
                self._calculate_resonance()
            except Exception as e:
                log.error(f"❌ Erro no Nexus Scraper: {e}")
            
            time.sleep(self.interval)

    def _update_ticks(self):
        """Puxa o último preço de cada símbolo resolvido."""
        if not mt5 or not mt5.terminal_info():
            return
            
        for asset_name, ticker in self.resolved_symbols.items():
            tick = mt5.symbol_info_tick(ticker)
            if tick and tick.last > 0:
                self.history[asset_name].append((time.time(), tick.last))
            elif tick and tick.bid > 0:
                mid = (tick.bid + tick.ask) / 2
                self.history[asset_name].append((time.time(), mid))

    def _calculate_resonance(self):
        """
        Matemática de Ressonância: 
        BTC é direcionalmente colinear com NASDAQ e SP500 (Risk ON/OFF).
        BTC e Ouro (XAU) reagem negativamente a DXY, tendo correlação positiva de longo prazo, 
        mas no sub-segundo, o Ouro lidera o breakdown de liquidez Fiat.
        """
        score = 0.0
        self.breakout_signals.clear()
        
        now = time.time()
        
        for asset, data in self.history.items():
            if len(data) < 10:
                continue
                
            prices = [p[1] for p in list(data)[-10:]] # Ultimos 10 segs
            p_current = prices[-1]
            p_old = prices[0]
            
            delta_pct = (p_current - p_old) / p_old
            
            # Normalizar score (Um pulo de 0.05% em 10s no SP500 é gigantesco)
            momentum = 0.0
            if asset == "NASDAQ" or asset == "SP500":
                momentum = (delta_pct / 0.0005) # Se mover 0.05%, momentum = 1.0
            elif asset == "GOLD":
                momentum = (delta_pct / 0.0003) # Ouro se move mais pesado
            elif asset == "ETH":
                momentum = (delta_pct / 0.0010) # ETH move mais fácil
                
            score += momentum / len(self.resolved_symbols)
            
            if abs(momentum) > 1.5:
                direction = "📈" if momentum > 0 else "📉"
                self.breakout_signals.append(f"{asset} {direction}")
                
        # Limite
        self.resonance_score = max(min(score, 1.0), -1.0)
        
        # OMEGA LOGGING DE MUTAÇÕES
        if abs(self.resonance_score) > 0.4 or len(self.breakout_signals) > 0:
            if now - getattr(self, '_last_log_time', 0) > 30.0:
                log.omega(f"🌍 [NEXUS RESONANCE] Força Macroeconômica Φ={self.resonance_score:+.2f} | Mutações Visíveis: {', '.join(self.breakout_signals)}")
                self._last_log_time = now

    def stop(self):
        self.running = False
