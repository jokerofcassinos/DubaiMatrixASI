"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — ON-CHAIN SCRAPER                           ║
║     Rastreador de Dados On-Chain via Web Scraping (Zero-Cost)              ║
║                                                                              ║
║  Captura métricas on-chain do Bitcoin: hashrate, fees, mempool,            ║
║  whale movements — dados que revelam a INTENÇÃO antes do preço.            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import time
import threading
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
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
class OnChainSnapshot:
    """Snapshot de dados on-chain do Bitcoin."""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    hashrate: float = 0.0                  # Hashrate total (TH/s)
    difficulty: float = 0.0                # Dificuldade de mineração
    mempool_size: int = 0                  # Transações na mempool
    mempool_bytes: int = 0                 # Tamanho da mempool em bytes
    avg_fee_sat: float = 0.0               # Fee média (sat/vB)
    blocks_last_24h: int = 0               # Blocos minerados em 24h
    avg_block_time: float = 600.0          # Tempo médio de bloco (s)
    exchange_inflow: float = 0.0           # BTC entrando em exchanges
    exchange_outflow: float = 0.0          # BTC saindo de exchanges
    net_exchange_flow: float = 0.0         # Net flow (+ = selling pressure)
    whale_alert_count: int = 0             # Movimentações whale recentes
    network_health: float = 0.5            # Score de saúde da rede [0-1]
    sources_active: int = 0


class OnChainScraper:
    """
    Scraper On-Chain — coleta dados da blockchain do Bitcoin.

    Fontes gratuitas:
    1. Blockchain.com API (hashrate, dificuldade, mempool)
    2. Mempool.space API (fees, mempool, blocos)
    3. Blockchair API (métricas gerais)
    """

    def __init__(self):
        self._running = False
        self._thread = None
        self._current = OnChainSnapshot()
        self._history = deque(maxlen=500)
        self._update_interval = 300  # 5 minutos (dados on-chain mudam devagar)
        self._session = self._create_resilient_session()
        self._last_update = 0.0

    def _create_resilient_session(self) -> requests.Session:
        """Cria uma sessão com retries e tratamento de erros de rede."""
        session = requests.Session()
        session.headers.update(HEADERS)
        
        # Configurar Retry exponencial
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def start(self):
        """Inicia o scraper em background."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        log.omega("⛓️ On-Chain Scraper: ONLINE")

    def stop(self):
        self._running = False

    @property
    def data(self) -> OnChainSnapshot:
        return self._current

    @property
    def network_pressure(self) -> float:
        """
        Score de pressão da rede [-1.0 a +1.0].
        Positivo = pressão vendedora (BTC entrando em exchanges).
        Negativo = pressão compradora (BTC saindo de exchanges / HODLing).
        """
        snap = self._current
        pressure = 0.0

        # Mempool congestionada = pressão de transações
        if snap.mempool_size > 100000:
            pressure += 0.2
        elif snap.mempool_size < 10000:
            pressure -= 0.1

        # Net exchange flow
        if snap.net_exchange_flow > 0:
            pressure += min(0.5, snap.net_exchange_flow / 1000.0)
        elif snap.net_exchange_flow < 0:
            pressure -= min(0.5, abs(snap.net_exchange_flow) / 1000.0)

        # Fees altas = congestionamento = bearish de curto prazo
        if snap.avg_fee_sat > 100:
            pressure += 0.15
        elif snap.avg_fee_sat < 10:
            pressure -= 0.1

        return max(-1.0, min(1.0, pressure))

    def _worker(self):
        """Thread principal."""
        while self._running:
            try:
                now = time.time()
                if now - self._last_update >= self._update_interval:
                    self._scrape_all()
                    self._last_update = now
            except (requests.exceptions.RequestException, ConnectionResetError) as e:
                log.warning(f"⚠️ On-Chain Scraper: Network glitch detected ({e}). Retrying next cycle.")
            except Exception as e:
                log.error(f"❌ On-Chain Scraper erro crítico: {e}")
            time.sleep(15)

    @catch_and_log(default_return=None)
    def _scrape_all(self):
        """Executa todos os scrapers on-chain."""
        snap = OnChainSnapshot()
        sources = 0

        # 1. Mempool.space
        mempool = self._scrape_mempool_space()
        if mempool:
            snap.mempool_size = mempool.get("count", 0)
            snap.mempool_bytes = mempool.get("vsize", 0)
            snap.avg_fee_sat = mempool.get("avg_fee", 0)
            sources += 1

        # 2. Blockchain.com
        blockchain = self._scrape_blockchain_com()
        if blockchain:
            snap.hashrate = blockchain.get("hashrate", 0)
            snap.difficulty = blockchain.get("difficulty", 0)
            snap.blocks_last_24h = blockchain.get("blocks_24h", 0)
            sources += 1

        # 3. Calcular saúde da rede
        snap.network_health = self._compute_network_health(snap)
        snap.sources_active = sources

        self._current = snap
        self._history.append(snap)

        log.info(
            f"⛓️ On-Chain Update: Mempool={snap.mempool_size:,} txs | "
            f"Fee={snap.avg_fee_sat:.1f} sat/vB | "
            f"Health={snap.network_health:.2f} | Sources={sources}"
        )

    @catch_and_log(default_return=None)
    def _scrape_mempool_space(self) -> Optional[dict]:
        """Scrape dados do mempool.space (API pública)."""
        result = {}

        # Mempool stats
        url = "https://mempool.space/api/mempool"
        resp = self._session.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            result["count"] = data.get("count", 0)
            result["vsize"] = data.get("vsize", 0)

        # Fee recommendations
        url_fees = "https://mempool.space/api/v1/fees/recommended"
        resp2 = self._session.get(url_fees, timeout=10)
        if resp2.status_code == 200:
            fees = resp2.json()
            # Média ponderada entre fastest e economy
            fastest = fees.get("fastestFee", 0)
            half_hour = fees.get("halfHourFee", 0)
            hour = fees.get("hourFee", 0)
            economy = fees.get("economyFee", 0)
            result["avg_fee"] = (fastest * 0.1 + half_hour * 0.3 + hour * 0.3 + economy * 0.3)

        return result if result else None

    @catch_and_log(default_return=None)
    def _scrape_blockchain_com(self) -> Optional[dict]:
        """Scrape dados do blockchain.com (API pública)."""
        result = {}

        # Stats gerais
        url = "https://api.blockchain.info/stats"
        resp = self._session.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            result["hashrate"] = data.get("hash_rate", 0) / 1e9  # Convert to TH/s
            result["difficulty"] = data.get("difficulty", 0)
            result["blocks_24h"] = data.get("n_blocks_total", 0)

        return result if result else None

    def _compute_network_health(self, snap: OnChainSnapshot) -> float:
        """Calcula score de saúde da rede Bitcoin [0-1]."""
        health = 0.5  # Base

        # Hashrate alto = rede saudável
        if snap.hashrate > 0:
            health += 0.15

        # Mempool não congestionada = fluxo normal
        if snap.mempool_size < 50000:
            health += 0.15
        elif snap.mempool_size > 200000:
            health -= 0.15

        # Fees razoáveis
        if 5 < snap.avg_fee_sat < 50:
            health += 0.1
        elif snap.avg_fee_sat > 200:
            health -= 0.2

        return max(0.0, min(1.0, health))

    @property
    def metrics(self) -> dict:
        return {
            "running": self._running,
            "last_update": datetime.fromtimestamp(self._last_update).isoformat() if self._last_update > 0 else "never",
            "history_size": len(self._history),
            "network_pressure": self.network_pressure,
            "network_health": self._current.network_health,
            "mempool_size": self._current.mempool_size,
        }
