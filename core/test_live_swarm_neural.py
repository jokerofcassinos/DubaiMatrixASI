"""
[TESTE NEURAL: O DESPERTAR DA INTELIGÊNCIA DE ENXAME — 14 AGENTES ELITE]
═══════════════════════════════════════════════════════════════════════════
Conecta a Fonte (BinanceHFTP) ao Coração (OmniDataEngine) e direciona os
Batimentos para o Processador Central (SwarmOrchestrator), onde todos os 14
Agentes Elite colapsam o QuantumState em live-stream.

Pipeline Cognitivo:
  BinanceWSS → OmniDataEngine → SwarmOrchestrator → 14 Elite Synapses → QuantumState

Resolução automática de PYTHONPATH para execução direta via venv.

"A serenidade de quem já sabe o resultado antes da execução."
"""
import sys
import os

# [Ω-PATH] Resolução automática da raiz do projeto independente de CWD
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import logging
import asyncio
import time
import numpy as np
from collections import deque

from market.exchanges.binance_hftp import BinanceHFTP
from market.data_engine import OmniDataEngine, MarketData, QuantumState
from core.intelligence.swarm_orchestrator import SwarmOrchestrator
from core.intelligence.solenn_bayesian import SolennBayesian
from core.intelligence.elite_synapse_adapters import create_all_elite_synapses

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)-32s | %(message)s'
)
log = logging.getLogger("LiveSwarmNeural")


class NeuralConnector:
    """
    [Ω-CONNECTOR] Ponte completa entre Dados de Mercado e Inteligência de Enxame.
    Instancia todos os 14 agentes elite + SolennBayesian + Genetic Swarm.
    """

    def __init__(self):
        self.engine = OmniDataEngine()
        self.orchestrator = SwarmOrchestrator()
        self.sensor = BinanceHFTP()
        self.ticks_processed = 0
        self._tick_latencies = deque(maxlen=5000)
        self._quantum_history = deque(maxlen=200)
        self._start_time = 0.0

    async def consume_to_swarm(self, snapshot: MarketData):
        """
        Consumidor Atômico:
        OmniDataEngine emite → SwarmOrchestrator processa → QuantumState emerge.
        """
        self.ticks_processed += 1
        t0 = time.perf_counter()

        # O Orquestrador invoca TODAS as Sinapses no MarketData do Ticker Recebido
        quantum_state = await self.orchestrator.get_quantum_state(
            snapshot=snapshot, nexus_context=None
        )

        t1 = time.perf_counter()
        latency = (t1 - t0) * 1000  # ms
        self._tick_latencies.append(latency)
        self._quantum_history.append(quantum_state)

        # Classificação direcional do consenso
        if quantum_state.signal > 0.15:
            direction = "🟢 BULLISH"
        elif quantum_state.signal < -0.15:
            direction = "🔴 BEARISH"
        else:
            direction = "⚪ NEUTRAL"

        # Log a cada tick com métricas do enxame
        log.info(
            f"🧠 [SWARM] #{self.ticks_processed:04d} {snapshot.symbol} @ {snapshot.price:>10.2f} | "
            f"{direction} Sig:{quantum_state.signal:+.4f} "
            f"Conf:{quantum_state.confidence:.4f} "
            f"Coer:{quantum_state.coherence:.4f} "
            f"Φ:{quantum_state.phi:+.4f} | "
            f"Cognição:{latency:.2f}ms"
        )

    async def run(self):
        log.info("=" * 78)
        log.info("   ██████╗ ██████╗ ██╗     ███████╗███╗   ██╗███╗   ██╗")
        log.info("   ██╔════╝██╔═══██╗██║     ██╔════╝████╗  ██║████╗  ██║")
        log.info("   ███████╗██║   ██║██║     █████╗  ██╔██╗ ██║██╔██╗ ██║")
        log.info("   ╚════██║██║   ██║██║     ██╔══╝  ██║╚██╗██║██║╚██╗██║")
        log.info("   ██████╔╝╚██████╔╝███████╗███████╗██║ ╚████║██║ ╚████║")
        log.info("   ╚═════╝  ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═══╝╚═╝  ╚═══╝")
        log.info("=" * 78)
        log.info("   [Ω-SOLÉNN] O DESPERTAR DA INTELIGÊNCIA DE ENXAME (14 AGENTES)")
        log.info("=" * 78)
        self._start_time = time.time()

        # ═══════════════════════════════════════════════════════════════
        # FASE 1: ACOPLAR TODAS AS SINAPSES ELITE (14 Agentes + Bayesian)
        # ═══════════════════════════════════════════════════════════════

        log.info("━" * 60)
        log.info("  FASE 1: ACOPLANDO SINAPSES ELITE AO ORQUESTRADOR")
        log.info("━" * 60)

        # 1a. SolennBayesian (agente fundacional)
        bayesian_synapse = SolennBayesian(data_engine=self.engine)
        self.orchestrator.synapses["SolennBayesian_01"] = bayesian_synapse
        log.info("  ✅ Sinapse 'SolennBayesian_01' acoplada ao Orquestrador.")

        # 1b. 14 Agentes Elite via Factory
        elite_synapses = create_all_elite_synapses()
        for name, synapse in elite_synapses.items():
            self.orchestrator.synapses[name] = synapse

        total_synapses = len(self.orchestrator.synapses)
        log.info(f"  🐝 TOTAL DE SINAPSES ATIVAS: {total_synapses}")
        log.info("━" * 60)

        for name in self.orchestrator.synapses:
            log.info(f"    🧬 {name}")
        log.info("━" * 60)

        # ═══════════════════════════════════════════════════════════════
        # FASE 2: INICIAR CORAÇÃO (DataEngine) + SENSOR (Binance)
        # ═══════════════════════════════════════════════════════════════

        log.info("  FASE 2: ATIVANDO PIPELINE SENSORIAL")
        log.info("━" * 60)

        # 2a. Iniciar DataEngine
        await self.engine.initialize()
        await self.engine.register_consumer(self.consume_to_swarm)
        log.info("  ✅ OmniDataEngine (Aorta Core) Online & Consumidor Registrado.")

        # 2b. Mapear Sensor Ticker e Roteamento
        def binance_router(payload):
            asyncio.create_task(self.engine.ingest_raw("BINANCE", payload))

        self.sensor.register_callback(binance_router)
        log.info("  ✅ Roteador Binance → Aorta Core conectado.")

        # 2c. Acionar Captura Websocket
        await self.sensor.connect()
        log.info("  ✅ BinanceHFTP WebSocket Live!")
        log.info("━" * 60)

        # ═══════════════════════════════════════════════════════════════
        # FASE 3: COLHEITA DE DADOS AO VIVO (Streaming Profundo)
        # ═══════════════════════════════════════════════════════════════

        harvest_seconds = 30
        log.info(f"  FASE 3: COLHENDO {harvest_seconds}s DE MATRIX EM LIVE STREAM")
        log.info("━" * 60)
        log.info(f"  >>> Observando convergência de {total_synapses} sinapses por {harvest_seconds}s <<<")

        # Relatório intermediário a cada 10 segundos
        for phase in range(harvest_seconds // 10):
            await asyncio.sleep(10)
            elapsed = (phase + 1) * 10
            log.info(f"  ⏱️  [{elapsed}s/{harvest_seconds}s] Ticks processados: {self.ticks_processed}")
            if self._tick_latencies:
                arr = np.array(list(self._tick_latencies))
                log.info(f"     Latência → P50: {np.median(arr):.2f}ms | P99: {np.percentile(arr, 99):.2f}ms")

        # Espera o restante se harvest_seconds não é múltiplo de 10
        remainder = harvest_seconds % 10
        if remainder > 0:
            await asyncio.sleep(remainder)

        # ═══════════════════════════════════════════════════════════════
        # FASE 4: DESMONTAGEM SISTÊMICA GRACIOSA
        # ═══════════════════════════════════════════════════════════════

        log.info("━" * 60)
        log.info("  FASE 4: DESMONTAGEM SISTÊMICA")
        log.info("━" * 60)
        await self.sensor.disconnect()
        log.info("  ✅ Sensor Binance desconectado.")
        await self.engine.stop()
        log.info("  ✅ OmniDataEngine parado.")
        await self.orchestrator.shutdown()
        log.info("  ✅ SwarmOrchestrator encerrado.")

        # ═══════════════════════════════════════════════════════════════
        # FASE 5: RELATÓRIO FINAL DO ENXAME
        # ═══════════════════════════════════════════════════════════════

        log.info("")
        log.info("=" * 78)
        log.info("   [Ω-SOLÉNN] RELATÓRIO FINAL DA INTELIGÊNCIA DE ENXAME")
        log.info("=" * 78)

        runtime = time.time() - self._start_time
        log.info(f"  ⏱️  Tempo de execução total: {runtime:.1f}s")
        log.info(f"  📊 Ticks processados pelo Orquestrador: {self.ticks_processed}")
        log.info(f"  🧬 Sinapses ativas no momento do teste: {total_synapses}")

        if self._tick_latencies:
            arr = np.array(list(self._tick_latencies))
            log.info(f"  ⚡ Latência Cognitiva (processamento de {total_synapses} agentes):")
            log.info(f"     P50: {np.median(arr):.3f}ms")
            log.info(f"     P95: {np.percentile(arr, 95):.3f}ms")
            log.info(f"     P99: {np.percentile(arr, 99):.3f}ms")
            log.info(f"     Max: {np.max(arr):.3f}ms")
            log.info(f"     Média: {np.mean(arr):.3f}ms")

        if self._quantum_history:
            signals = np.array([qs.signal for qs in self._quantum_history])
            confs = np.array([qs.confidence for qs in self._quantum_history])
            cohs = np.array([qs.coherence for qs in self._quantum_history])
            phis = np.array([qs.phi for qs in self._quantum_history])

            log.info(f"  🌊 QuantumState Distribuição (últimos {len(self._quantum_history)} snapshots):")
            log.info(f"     Signal   → μ:{np.mean(signals):+.4f}  σ:{np.std(signals):.4f}  "
                     f"[{np.min(signals):+.4f}, {np.max(signals):+.4f}]")
            log.info(f"     Confid   → μ:{np.mean(confs):.4f}   σ:{np.std(confs):.4f}  "
                     f"[{np.min(confs):.4f}, {np.max(confs):.4f}]")
            log.info(f"     Coher    → μ:{np.mean(cohs):.4f}   σ:{np.std(cohs):.4f}  "
                     f"[{np.min(cohs):.4f}, {np.max(cohs):.4f}]")
            log.info(f"     Phi (Φ)  → μ:{np.mean(phis):+.4f}  σ:{np.std(phis):.4f}  "
                     f"[{np.min(phis):+.4f}, {np.max(phis):+.4f}]")

            # Bias Direcional do Enxame
            bullish_pct = np.mean(signals > 0.1) * 100
            bearish_pct = np.mean(signals < -0.1) * 100
            neutral_pct = 100 - bullish_pct - bearish_pct
            log.info(f"  📈 Bias Direcional do Enxame:")
            log.info(f"     🟢 Bullish: {bullish_pct:.1f}%  |  🔴 Bearish: {bearish_pct:.1f}%  |  ⚪ Neutral: {neutral_pct:.1f}%")

        # Byzantine Consensus Health
        byz = self.orchestrator.byzantine
        if byz.reputation:
            log.info(f"  🛡️  Saúde Bizantina ({len(byz.reputation)} agentes rastreados):")
            for name, rep in sorted(byz.reputation.items(), key=lambda x: x[1].trust_score, reverse=True):
                status_icon = "✅" if rep.status.value == "HONEST" else "⚠️" if rep.status.value == "NOISY" else "❌"
                log.info(f"     {status_icon} {name:30s} Trust:{rep.trust_score:.3f}  "
                         f"Outliers:{rep.consecutive_outliers}  "
                         f"Samples:{rep.total_samples}")

        log.info("=" * 78)
        log.info("   SOLÉNN — A serenidade de quem já sabe o resultado antes da execução.")
        log.info("=" * 78)


if __name__ == "__main__":
    connector = NeuralConnector()
    try:
        asyncio.run(connector.run())
    except KeyboardInterrupt:
        log.info("⛔ Interrompido pelo CEO.")
