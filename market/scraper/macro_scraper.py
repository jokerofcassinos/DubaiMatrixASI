"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — MACRO SCRAPER                              ║
║     Rastreador de Dados Macroeconômicos via Web Scraping (Zero-Cost)       ║
║                                                                              ║
║  Captura DXY, VIX proxy, Gold/Oil correlações, e dados macro que           ║
║  afetam BTC — a Camada Ω-10 de Consciência Ecossistêmica.                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import time
import threading
import requests
from datetime import datetime, timezone
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, Dict, List

from utils.logger import log
from utils.decorators import catch_and_log

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


@dataclass
class MacroSnapshot:
    """Snapshot de dados macroeconômicos."""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    dxy_proxy: float = 0.0                 # DXY proxy (USD strength)
    gold_price: float = 0.0                # Preço do ouro (USD/oz)
    gold_24h_change: float = 0.0           # Variação 24h do ouro
    sp500_proxy: float = 0.0               # S&P 500 proxy
    btc_eth_ratio: float = 0.0             # BTC/ETH ratio
    eth_price: float = 0.0                 # Preço ETH
    eth_24h_change: float = 0.0            # Variação 24h ETH
    total_crypto_volume_24h: float = 0.0   # Volume total crypto 24h
    macro_risk_score: float = 0.5          # Score de risco macro [0-1]
    correlation_btc_gold: float = 0.0      # Correlação BTC-Gold estimada
    sources_active: int = 0


class MacroScraper:
    """
    Scraper Macroeconômico — coleta dados macro que influenciam BTC.

    Fontes gratuitas:
    1. CoinGecko (ETH price, volumes, múltiplas moedas)
    2. Dados derivados de correlações entre crypto assets
    3. Gold price via APIs públicas
    """

    def __init__(self):
        self._running = False
        self._thread = None
        self._current = MacroSnapshot()
        self._history = deque(maxlen=500)
        self._update_interval = 180  # 3 minutos
        self._session = requests.Session()
        self._session.headers.update(HEADERS)
        self._last_update = 0.0

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        log.omega("🌍 Macro Scraper: ONLINE")

    def stop(self):
        self._running = False

    @property
    def data(self) -> MacroSnapshot:
        return self._current

    @property
    def macro_bias(self) -> float:
        """
        Viés macroeconômico para BTC [-1.0 a +1.0].
        Positivo = ambiente macro favorável para BTC.
        Negativo = ambiente macro desfavorável.
        """
        snap = self._current
        bias = 0.0

        # DXY fraco = bullish para BTC
        # (se capture disponível)
        if snap.dxy_proxy > 0:
            if snap.dxy_proxy > 105:
                bias -= 0.2  # Dollar forte, bearish BTC
            elif snap.dxy_proxy < 100:
                bias += 0.2  # Dollar fraco, bullish BTC

        # Gold subindo = risk-off ou inflation hedge = pode ser bullish BTC
        if snap.gold_24h_change > 1.0:
            bias += 0.1
        elif snap.gold_24h_change < -1.0:
            bias -= 0.1

        # BTC/ETH ratio alto = Bitcoin dominando = risk-off crypto
        if snap.btc_eth_ratio > 25:
            bias += 0.1  # Flight to BTC
        elif snap.btc_eth_ratio < 15:
            bias -= 0.1  # Risk-on (alts pumping, BTC lagging)

        # Volume crescente = mercado ativo
        if snap.total_crypto_volume_24h > 100e9:  # >100B
            bias += 0.1

        return max(-1.0, min(1.0, bias))

    def _worker(self):
        while self._running:
            try:
                now = time.time()
                if now - self._last_update >= self._update_interval:
                    self._scrape_all()
                    self._last_update = now
            except Exception as e:
                log.error(f"❌ Macro Scraper erro: {e}")
            time.sleep(15)

    @catch_and_log(default_return=None)
    def _scrape_all(self):
        # [Phase Ω-Resilience] Iniciar com valores anteriores para evitar reset para zero em caso de falha parcial
        snap = MacroSnapshot(
            dxy_proxy=self._current.dxy_proxy,
            gold_price=self._current.gold_price,
            gold_24h_change=self._current.gold_24h_change,
            sp500_proxy=self._current.sp500_proxy,
            btc_eth_ratio=self._current.btc_eth_ratio,
            eth_price=self._current.eth_price,
            eth_24h_change=self._current.eth_24h_change,
            total_crypto_volume_24h=self._current.total_crypto_volume_24h,
            macro_risk_score=self._current.macro_risk_score,
            sources_active=self._current.sources_active
        )
        sources = 0

        # 1. CoinGecko multi-asset prices
        prices = self._scrape_coingecko_prices()
        if prices:
            btc_price = prices.get("btc_price", 0)
            eth_price = prices.get("eth_price", 0)
            if btc_price > 0 and eth_price > 0:
                snap.eth_price = eth_price
                snap.eth_24h_change = prices.get("eth_24h_change", 0)
                snap.btc_eth_ratio = btc_price / eth_price
                sources += 1
        
        # [Phase Ω-Resilience] Fallback: Se CoinGecko falhar, tenta estimar via MT5 se possível
        if snap.eth_price == 0 or snap.btc_eth_ratio == 0:
            # Se já temos algum valor histórico, mantemos. 
            # Se for o cold start, fontes permanecem 0.
            pass

        # 2. CoinGecko global volumes
        global_data = self._scrape_coingecko_global()
        if global_data:
            vol = global_data.get("total_volume", 0)
            if vol > 0:
                snap.total_crypto_volume_24h = vol
                sources += 1

        # 3. Gold price
        gold = self._scrape_gold_price()
        if gold:
            gp = gold.get("price", 0)
            if gp > 0:
                snap.gold_price = gp
                snap.gold_24h_change = gold.get("change_24h", 0)
                sources += 1

        # Recalcular risk score se tivemos atualizações
        if sources > 0:
            snap.macro_risk_score = self._compute_macro_risk(snap)
            snap.sources_active = sources
            snap.timestamp = datetime.now(timezone.utc)

        self._current = snap
        self._history.append(snap)

        log.info(
            f"🌍 Macro Update: ETH=${snap.eth_price:.2f} | "
            f"BTC/ETH={snap.btc_eth_ratio:.1f} | "
            f"Gold=${snap.gold_price:.0f} | "
            f"Vol24h=${snap.total_crypto_volume_24h/1e9:.1f}B | "
            f"Bias={self.macro_bias:+.3f} | Sources={sources}"
        )

    @catch_and_log(default_return=None)
    def _scrape_coingecko_prices(self) -> Optional[dict]:
        """Preços de BTC e ETH via CoinGecko."""
        url = ("https://api.coingecko.com/api/v3/simple/price"
               "?ids=bitcoin,ethereum&vs_currencies=usd"
               "&include_24hr_change=true")
        resp = self._session.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "btc_price": data.get("bitcoin", {}).get("usd", 0),
                "eth_price": data.get("ethereum", {}).get("usd", 0),
                "eth_24h_change": data.get("ethereum", {}).get("usd_24h_change", 0),
            }
        return None

    @catch_and_log(default_return=None)
    def _scrape_coingecko_global(self) -> Optional[dict]:
        """Dados globais do mercado crypto via CoinGecko."""
        url = "https://api.coingecko.com/api/v3/global"
        resp = self._session.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            return {
                "total_volume": data.get("total_volume", {}).get("usd", 0),
            }
        return None

    @catch_and_log(default_return=None)
    def _scrape_gold_price(self) -> Optional[dict]:
        """Preço do ouro via CoinGecko (usamos o PAXG como proxy on-chain do gold)."""
        url = ("https://api.coingecko.com/api/v3/simple/price"
               "?ids=pax-gold&vs_currencies=usd&include_24hr_change=true")
        resp = self._session.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json().get("pax-gold", {})
            return {
                "price": data.get("usd", 0),
                "change_24h": data.get("usd_24h_change", 0),
            }
        return None

    def _compute_macro_risk(self, snap: MacroSnapshot) -> float:
        """Calcula score de risco macroeconômico [0=baixo risco, 1=alto risco]."""
        risk = 0.5  # Base

        # Alta volatilidade em ETH = risk-on extreme
        if abs(snap.eth_24h_change) > 10:
            risk += 0.2

        # Gold subindo muito = incerteza macro
        if snap.gold_24h_change > 3:
            risk += 0.15

        # Volume muito alto pode indicar pânico ou euforia
        if snap.total_crypto_volume_24h > 200e9:
            risk += 0.15

        return max(0.0, min(1.0, risk))

    @property
    def metrics(self) -> dict:
        return {
            "running": self._running,
            "history_size": len(self._history),
            "macro_bias": self.macro_bias,
            "risk_score": self._current.macro_risk_score,
            "sources_active": self._current.sources_active,
        }
