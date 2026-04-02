"""
[TESTE NEURAL: O CRUZAMENTO DO PORTÃO DE SINAIS]
Instanciar Confluência Suprema -> Validar Tolerâncias -> Executar Demo (0.01)
"""
import sys
import logging
import asyncio
import time

from market.exchanges.mt5_connector import MetaBridge
from market.data_engine import MarketData, QuantumState
from core.intelligence.signals_gate import SolennSignalGate

# Credenciais MT5 FTMO Validadas (Conta Demo)
MT5_LOGIN = 1512930277
MT5_PASS = "w31?MRh*M@y"
MT5_SERVER = "FTMO-Demo"

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(name)s | %(message)s')
log = logging.getLogger("TestGateCrossing")

async def run_crossing():
    log.info("--- STARTING NEURAL CROSSING (SIGNAL GATE -> MT5) ---")

    # 1. MT5 BRIDGE INSTANTIATION
    mt5_bridge = MetaBridge(MT5_LOGIN, MT5_PASS, MT5_SERVER)
    if not await mt5_bridge.initialize():
        log.error("☢️ MT5 Initialization failed. Missing Terminal or Credentials.")
        return
        
    log.info("1. MetaTrader5 Bridge Instantiated (ThreadPool Activated).")
    
    # 2. SIGNAL GATE INSTANTIATION
    gate = SolennSignalGate(config={"min_confidence": 0.80})
    log.info("2. Solenn Signal Gate Instantiated (162 vectors active).")

    # 3. FORJANDO O ESTADO MENTAL INCONTESTÁVEL
    # Simula um tick do BTCUSD com spread excelente e order_flow tóxico=0
    mock_snapshot = MarketData(
        symbol="BTCUSD",
        exchange="MT5",
        timestamp=int(time.time() * 1e9),
        price=68000.0,
        volume=1.0,
        side="TICK",
        book_imbalance=0.1,  # Não tóxico
        spread=0.5,
        vol_gk=0.0005,
        vwap_local=67980.0
    )
    
    # Simula que o Enxame convergiu com 99% de convicção em direção BUY (+1.0)
    mock_quantum = QuantumState(
        timestamp=time.time(),
        symbol="BTCUSD",
        signal=1.0,           # Forte BUY
        confidence=0.99,      # Alta Confiança Preditiva
        coherence=0.95,       # Harmonia multi-escala
        phi=1.618,            
        imbalance=0.1
    )
    
    regime = "TRENDING-UP-STRONG"
    bayes_score = 0.95 # Confiança Bayesiana pós-prior
    
    log.info(f"3. Enviando Tese de Operação -> Regime: {regime}")
    
    # 4. AVALIAÇÃO O(1) PELO PORTÃO
    sovereign_signal = await gate.evaluate(
        snapshot=mock_snapshot,
        quantum_state=mock_quantum,
        regime_state_identity=regime,
        bayes_conviction=bayes_score
    )
    
    log.info(f"-> Veredito do Portal: {sovereign_signal.action} | Conviction: {sovereign_signal.confidence} | Reason: {sovereign_signal.reasoning}")

    # 5. EXECUÇÃO FATAL
    if sovereign_signal.action in ["BUY", "SELL"]:
        volume = 0.01 # Lote minúsculo de Testdrive de Integração
        log.info(f"4. Enviando Solicitação Sub-milissegundo para MetaBridge: {sovereign_signal.action} {volume} Lot")
        
        ticket = await mt5_bridge.execute_order(
            symbol=mock_snapshot.symbol,
            side=sovereign_signal.action,
            volume=volume,
            max_slippage_pts=50 # Slack maior pela volatilidade do BTC
        )
        
        if ticket:
            log.info(f"✅✅✅ MATRIZ CRUZADA! ORDEM CONFIRMADA: Ticket #{ticket} ✅✅✅")
        else:
            log.error("☢️ Ordem Bloqueada pela MetaBridge (Circuit Breaker local, limite lotes, ou erro MQL5).")
    else:
        log.warning("O Portal rejeitou a operação matemática. Nenhuma ordem enviada.")

    log.info("Shutting down bridges...")
    await mt5_bridge.stop()
    log.info("Done.")

if __name__ == "__main__":
    asyncio.run(run_crossing())
