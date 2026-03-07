"""
╔══════════════════════════════════════════════════════════════════════════════╗
║             DUBAI MATRIX ASI — LUCID DREAMING CLIENT (PHASE Ω-ONE)           ║
║     Interface para orquestrar auto-simulações aceleradas em Java.           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import socket
import threading
from utils.logger import log
from utils.decorators import catch_and_log

class LucidDreamClient:
    """
    Cliente Python para interagir com o LucidDreamingDaemon (Java).
    Permite que a ASI "sonhe" com cenários de mercado e valide mutações.
    """

    def __init__(self, host="127.0.0.1", port=5557):
        self.host = host
        self.port = port
        self._lock = threading.Lock()

    @catch_and_log(default_return=None)
    def dream_cycle(self, base_price: float, volatility: float, iterations: int = 5000) -> dict:
        """
        Solicita um ciclo de sonho (auto-simulação acelerada).
        Retorna as métricas de alpha descobertas por 'Shadow Agents'.
        """
        try:
            with self._lock:
                with socket.create_connection((self.host, self.port), timeout=5.0) as s:
                    payload = f"DREAM|{base_price}|{volatility}|{iterations}\n"
                    s.sendall(payload.encode())
                    
                    response = s.recv(1024).decode().strip()
                    if response.startswith("SUCCESS"):
                        parts = response.split("|")
                        return {
                            "alpha": float(parts[1].split(":")[1]),
                            "mutations": int(parts[2].split(":")[1]),
                            "time_ms": int(parts[3].split(":")[1].replace("ms", ""))
                        }
            return None
        except (ConnectionRefusedError, socket.timeout):
            # O daemon Java pode não estar rodando ainda
            return None

# Singleton
DREAM_ENGINE = LucidDreamClient()
