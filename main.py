"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    ██████╗ ██╗   ██╗██████╗  █████╗ ██╗                     ║
║                    ██╔══██╗██║   ██║██╔══██╗██╔══██╗██║                     ║
║                    ██║  ██║██║   ██║██████╔╝███████║██║                     ║
║                    ██║  ██║██║   ██║██╔══██╗██╔══██║██║                     ║
║                    ██████╔╝╚██████╔╝██████╔╝██║  ██║██║                     ║
║                    ╚═════╝  ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝                     ║
║                                                                              ║
║              ███╗   ███╗ █████╗ ████████╗██████╗ ██╗██╗  ██╗               ║
║              ████╗ ████║██╔══██╗╚══██╔══╝██╔══██╗██║╚██╗██╔╝               ║
║              ██╔████╔██║███████║   ██║   ██████╔╝██║ ╚███╔╝                ║
║              ██║╚██╔╝██║██╔══██║   ██║   ██╔══██╗██║ ██╔██╗                ║
║              ██║ ╚═╝ ██║██║  ██║   ██║   ██║  ██║██║██╔╝ ██╗               ║
║              ╚═╝     ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝               ║
║                                                                              ║
║                          █████╗ ███████╗██╗                                  ║
║                         ██╔══██╗██╔════╝██║                                  ║
║                         ███████║███████╗██║                                  ║
║                         ██╔══██║╚════██║██║                                  ║
║                         ██║  ██║███████║██║                                  ║
║                         ╚═╝  ╚═╝╚══════╝╚═╝                                  ║
║                                                                              ║
║         Superintelligência Financial Omega-Class — BTCUSD MT5               ║
║                         v1.0.0-omega                                         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

Entry point principal da DubaiMatrixASI.
Inicializa todos os sistemas e entra no loop de consciência.
"""

import sys
import time
import signal
import traceback
from datetime import datetime, timezone

# Adicionar diretório ao path
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import (
    ASI_NAME, ASI_VERSION, CONSCIOUSNESS_CYCLE_MS
)
from config.exchange_config import MT5_LOGIN, MT5_PASSWORD, MT5_SERVER, MT5_PATH
from market.mt5_bridge import MT5Bridge
from core.asi_brain import ASIBrain
from config.omega_params import OMEGA
from utils.logger import log


class DubaiMatrixASI:
    """
    PONTO DE ENTRADA DA ASI.
    Inicializa, conecta ao MT5, e entra no loop infinito de consciência.
    """

    def __init__(self):
        self.bridge = MT5Bridge()
        self.brain = None
        self._running = False
        self._shutdown_requested = False

        # Registrar signal handlers para graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Captura Ctrl+C para shutdown graceful."""
        log.omega("🛑 Shutdown signal recebido (Ctrl+C)")
        self._shutdown_requested = True

    def start(self, login: int = None, password: str = None,
              server: str = None, path: str = None):
        """
        Inicializa e roda a ASI.

        Args:
            login: MT5 Login
            password: MT5 Password
            server: MT5 Server
            path: Caminho do terminal MT5
        """
        log.startup_banner()

        log.omega(f"🚀 {ASI_NAME} {ASI_VERSION}")
        log.omega(f"📅 {datetime.now(timezone.utc).isoformat()}")
        log.omega(f"🎯 Ativo: BTCUSD")
        log.omega(f"🏗️ Modo: DEMO (Validação em tempo real)")

        # ═══ 1. CONECTAR AO MT5 ═══
        log.info("🔗 Conectando ao MetaTrader 5...")

        while not self._shutdown_requested:
            connected = self.bridge.connect(
                login=login, password=password,
                server=server, path=path
            )

            if connected:
                # Verificar se há dados fluindo
                log.info("📡 Aguardando primeiro sinal de dados (tick) do MT5...")
                tick_received = False
                for _ in range(30):  # Esperar até 30 segundos pelos dados
                    if self._shutdown_requested:
                        break
                    tick = self.bridge.get_tick()
                    if tick is not None:
                        log.omega(f"✅ Dados fluindo! Primeiro tick: Ask={tick['ask']}, Bid={tick['bid']}")
                        tick_received = True
                        break
                    
                    time.sleep(1)
                
                if tick_received:
                    break
                else:
                    log.warning("⚠️ MT5 conectado, mas sem dados fluindo (mercado fechado ou sem ticks). Desconectando e tentando novamente...")
                    self.bridge.disconnect()
            
            else:
                log.critical("❌ FALHA NA CONEXÃO MT5 — Verifique credenciais e terminal MT5")
                log.info("  Dica: Certifique-se que o MT5 está aberto e logado")
                log.warning("⏳ Aguardando 5 segundos antes de tentar novamente...")
            
            time.sleep(5)

        if self._shutdown_requested:
            return

        # ═══ 2. INICIALIZAR CÉREBRO ═══
        log.info("🧠 Inicializando ASI Brain...")
        self.brain = ASIBrain(self.bridge)

        # ═══ 3. HEALTH CHECK ═══
        health = self.bridge.health_check()
        log.info(f"🏥 Health Check: {health}")

        # ═══ 4. ENTRAR NO LOOP DE CONSCIÊNCIA ═══
        log.omega("⚡ WARMUP INICIADO — O DataEngine rodará em background para puxar e pre-calcular todo o histórico...")
        log.omega("⚡ CONSCIÊNCIA ATIVA — Entrando no loop principal")
        self._run_consciousness_loop()

    def _run_consciousness_loop(self):
        """
        Loop infinito de consciência — o heartbeat da ASI.
        Cada ciclo é um pensamento completo.
        """
        self._running = True
        cycle_interval = CONSCIOUSNESS_CYCLE_MS / 1000.0  # Para seconds

        while self._running and not self._shutdown_requested:
            try:
                cycle_start = time.perf_counter()

                # ═══ PENSAR ═══
                result = self.brain.think()

                # ═══ TIMING — Respeitar o intervalo ═══
                elapsed = time.perf_counter() - cycle_start
                
                # PHASE Ω-EXTREME: Lorentz Dilation
                # Se dilation > 1, o mercado está "quente" (alta energia).
                # A ASI dilata o próprio tempo externo para processar mais (dorme menos).
                dilation = 1.0
                if OMEGA.get("lorentz_dilation_enabled", 1.0) > 0.5:
                    dilation = getattr(self.brain.data_engine, 'lorentz_dilation', 1.0)
                
                effective_cycle = cycle_interval / max(1.0, dilation)
                
                sleep_time = max(0, effective_cycle - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)

                # ═══ HEALTH CHECK periódico ═══
                if self.brain._cycle_count % 200 == 0:
                    if not self.bridge.is_alive():
                        log.warning("⚠️ MT5 Bridge perdeu conexão — tentando reconectar...")
                        self.bridge.connect()

            except KeyboardInterrupt:
                break
            except Exception as e:
                log.error(f"❌ Erro no loop de consciência: {e}")
                log.debug(traceback.format_exc())
                time.sleep(1)  # Pausa breve antes de retry

        # ═══ SHUTDOWN ═══
        self._shutdown()

    def _shutdown(self):
        """Desligamento ordenado de todos os sistemas."""
        log.omega("🔴 INICIANDO SHUTDOWN SEQUENCE...")

        if self.brain:
            self.brain.shutdown()

        self.bridge.disconnect()

        log.omega(f"🏁 {ASI_NAME} OFFLINE")
        log.omega(f"📊 Sessão finalizada às {datetime.now(timezone.utc).isoformat()}")

        if self.brain:
            diag = self.brain.diagnostics
            log.info(f"📈 Trades: {diag['state']['total_trades']}")
            log.info(f"📈 Win Rate: {diag['state']['win_rate']:.1%}")
            log.info(f"📈 P&L: ${diag['state']['total_profit']:+.2f}")


# ═══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    asi = DubaiMatrixASI()

    # ═══ CONFIGURAR AQUI AS CREDENCIAIS MT5 ═══
    asi.start(
        login=1521199394,       # Seu login MT5 (ex: 12345678)
        password="!6yST!HJ!*",    # Sua senha MT5
        server="FTMO-Demo2",      # Seu servidor MT5 (ex: "MetaQuotes-Demo")
        path='C:\\Program Files\\FTMO Global Markets MT5 Terminal\\terminal64.exe',              # A ASI hookará magicamente no MT5 que já está aberto!
    )
