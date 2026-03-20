"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — SENTIMENT SCRAPER                          ║
║     Rastreador de Sentimento de Mercado via Web Scraping (Zero-Cost)       ║
║                                                                              ║
║  Captura Fear & Greed Index, tendências de busca, e sentimento social      ║
║  sem nenhuma API paga — pura engenharia de extração de dados.              ║
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

# Headers para simular navegador real
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class SentimentSnapshot:
    """Snapshot de sentimento do mercado."""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    fear_greed_index: float = 50.0          # 0=Extreme Fear, 100=Extreme Greed
    fear_greed_label: str = "Neutral"
    btc_dominance: float = 0.0              # % dominância BTC
    total_market_cap: float = 0.0           # Market cap total crypto
    btc_24h_change: float = 0.0             # Variação 24h
    btc_7d_change: float = 0.0              # Variação 7d
    trending_sentiment: float = 0.0         # -1 (bearish) a +1 (bullish)
    social_volume: float = 0.0              # Volume de menções sociais
    data_quality: float = 0.0               # 0-1, qualidade dos dados coletados
    sources_active: int = 0                 # Quantas fontes responderam


class SentimentScraper:
    """
    Scraper de Sentimento — coleta dados de múltiplas fontes gratuitas.

    Fontes:
    1. Alternative.me Fear & Greed Index API (gratuita)
    2. CoinGecko (dados gerais de mercado, gratuita)
    3. Blockchain.com (dados on-chain básicos)
    """

    def __init__(self):
        self._running = False
        self._thread = None
        self._current_sentiment = SentimentSnapshot()
        self._history = deque(maxlen=1000)
        self._update_interval = 120  # Atualizar a cada 2 minutos
        self._session = requests.Session()
        self._session.headers.update(HEADERS)
        self._last_update = 0.0

    def start(self):
        """Inicia o scraper em background."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        log.omega("📡 Sentiment Scraper: ONLINE")

    def stop(self):
        """Para o scraper."""
        self._running = False

    @property
    def sentiment(self) -> SentimentSnapshot:
        """Retorna o snapshot de sentimento mais recente."""
        return self._current_sentiment

    @property
    def sentiment_score(self) -> float:
        """Score consolidado de sentimento [-1.0 a +1.0]."""
        s = self._current_sentiment
        # Normalizar Fear & Greed para [-1, 1]
        fg_normalized = (s.fear_greed_index - 50) / 50.0
        # Combinar com trending sentiment
        combined = fg_normalized * 0.6 + s.trending_sentiment * 0.4
        return max(-1.0, min(1.0, combined))

    def _worker(self):
        """Thread principal de scraping."""
        while self._running:
            try:
                now = time.time()
                if now - self._last_update >= self._update_interval:
                    self._scrape_all()
                    self._last_update = now
            except Exception as e:
                log.error(f"❌ Sentiment Scraper erro: {e}")

            time.sleep(10)  # Check a cada 10s

    @catch_and_log(default_return=None)
    def _scrape_all(self):
        """Executa todos os scrapers."""
        snap = SentimentSnapshot()
        sources = 0

        # 1. Fear & Greed Index
        fg = self._scrape_fear_greed()
        if fg:
            snap.fear_greed_index = fg.get("value", 50)
            snap.fear_greed_label = fg.get("label", "Neutral")
            sources += 1

        # 2. CoinGecko Market Data
        market = self._scrape_coingecko_market()
        if market:
            snap.btc_dominance = market.get("btc_dominance", 0)
            snap.total_market_cap = market.get("total_market_cap", 0)
            snap.btc_24h_change = market.get("btc_24h_change", 0)
            snap.btc_7d_change = market.get("btc_7d_change", 0)
            sources += 1

        # 3. Derivar sentiment trending
        snap.trending_sentiment = self._derive_trending_sentiment(snap)
        snap.sources_active = sources
        snap.data_quality = min(1.0, sources / 2.0)

        self._current_sentiment = snap
        self._history.append(snap)

        log.info(
            f"📊 Sentiment Update: F&G={snap.fear_greed_index:.0f} ({snap.fear_greed_label}) | "
            f"BTC Dom={snap.btc_dominance:.1f}% | 24h={snap.btc_24h_change:+.2f}% | "
            f"Score={self.sentiment_score:+.3f} | Sources={sources}"
        )

    @catch_and_log(default_return=None)
    def _scrape_fear_greed(self) -> Optional[dict]:
        """Scrape Fear & Greed Index de alternative.me (API pública gratuita)."""
        url = "https://api.alternative.me/fng/?limit=1&format=json"
        try:
            resp = self._session.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if "data" in data and len(data["data"]) > 0:
                    entry = data["data"][0]
                    return {
                        "value": float(entry.get("value", 50)),
                        "label": entry.get("value_classification", "Neutral"),
                    }
        except requests.exceptions.RequestException as e:
            log.warning(f"📡 Fear&Greed API timeout/error: {e}")
        return None

    @catch_and_log(default_return=None)
    def _scrape_coingecko_market(self) -> Optional[dict]:
        """Scrape dados de mercado do CoinGecko (API pública gratuita)."""
        # Global data
        url_global = "https://api.coingecko.com/api/v3/global"
        resp = self._session.get(url_global, timeout=10)
        result = {}

        if resp.status_code == 200:
            data = resp.json().get("data", {})
            result["btc_dominance"] = data.get("market_cap_percentage", {}).get("btc", 0)
            result["total_market_cap"] = data.get("total_market_cap", {}).get("usd", 0)

        # BTC price data
        url_btc = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true&include_7d_change=true"
        resp2 = self._session.get(url_btc, timeout=10)
        if resp2.status_code == 200:
            btc = resp2.json().get("bitcoin", {})
            result["btc_24h_change"] = btc.get("usd_24h_change", 0)
            result["btc_7d_change"] = btc.get("usd_7d_change", 0) if "usd_7d_change" in btc else 0

        return result if result else None

    def _derive_trending_sentiment(self, snap: SentimentSnapshot) -> float:
        """Calcula um score de tendência de sentimento baseado em múltiplos fatores."""
        score = 0.0
        factors = 0

        # Fear & Greed contribuição
        if snap.fear_greed_index > 0:
            fg_score = (snap.fear_greed_index - 50) / 50.0
            score += fg_score
            factors += 1

        # 24h change contribuição
        if snap.btc_24h_change != 0:
            change_score = max(-1.0, min(1.0, snap.btc_24h_change / 10.0))
            score += change_score
            factors += 1

        # BTC dominance (alta dominância = flight to safety = levemente bearish para alts)
        if snap.btc_dominance > 60:
            score += 0.1  # Bullish para BTC
            factors += 1
        elif snap.btc_dominance < 40:
            score -= 0.1  # Bearish para BTC
            factors += 1

        return max(-1.0, min(1.0, score / max(1, factors)))

    def get_history(self, count: int = 10) -> List[SentimentSnapshot]:
        """Retorna os últimos N snapshots de sentimento."""
        history = list(self._history)
        return history[-count:] if len(history) >= count else history

    @property
    def metrics(self) -> dict:
        """Métricas do scraper."""
        return {
            "running": self._running,
            "last_update": datetime.fromtimestamp(self._last_update).isoformat() if self._last_update > 0 else "never",
            "history_size": len(self._history),
            "current_score": self.sentiment_score,
            "fear_greed": self._current_sentiment.fear_greed_index,
            "sources_active": self._current_sentiment.sources_active,
        }
