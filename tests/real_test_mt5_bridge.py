import asyncio
import logging
from market.exchanges.mt5_connector import MetaBridge, AccountStatus
from config.settings import FTMO_LOGIN, FTMO_PASSWORD, FTMO_SERVER

# [Ω-TEST-NEURAL] Ponte do Absoluto Ω-45: Validação REAL de Execução e Compliance
# 1-Genese | 2-Execução | 3-Guardrais FTMO

async def test_meta_bridge_real():
    """
    VALIDAÇÃO REAL DO META-BRIDGE Ω-45
    Protocolo 3-6-9: Testando o Controle Ótimo com TERMINAL REAL.
    """
    print(f"\n[VITALIDADE] Iniciando Meta-Bridge Ω-45 (REAL CONNECT) -> {FTMO_SERVER}...")
    
    bridge = MetaBridge(login=FTMO_LOGIN, password=FTMO_PASSWORD, server=FTMO_SERVER)
    
    # 🧪 ETAPA 1: GENESE (Handshake Real)
    try:
        # Timeout de 15 segundos para inicialização do terminal
        success = await asyncio.wait_for(bridge.initialize(), timeout=15.0)
    except asyncio.TimeoutError:
        print("☢️ [ERROR] Timeout na Inicialização do MT5. Verifique se o terminal está aberto.")
        return

    if not success:
         print("-> [FAIL] Falha na Conexão Real com o Terminal MT5.")
         print("-> Verifique as credenciais no .env e se o servidor está correto.")
         return

    print(f"-> Handshake Meta-Bridge OK (Login: {FTMO_LOGIN})")
    
    # Aguardar sincronização inicial
    await asyncio.sleep(2) 
    
    if bridge.account_info:
        print(f"-> [VITAL] Account Balance: {bridge.account_info.balance}")
        print(f"-> [VITAL] Account Equity: {bridge.account_info.equity}")
        print(f"-> [VITAL] Daily Loss: {bridge.account_info.daily_loss*100:.2f}%")
    else:
        print("☢️ [WARNING] Account Info não sincronizado.")

    # 🧪 ETAPA 2: EXECUÇÃO (Order HIB Logic)
    # CUIDADO: Isso enviará uma ordem real se a conta for real.
    # Usaremos um volume mínimo e um par volátil para teste de execução.
    print("[COGNIÇÃO] Testando Envio de Ordem REAL HIB Ω-45.1.2...")
    
    # Escolha de símbolo: BTCUSD ou similar disponível no MT5 da FTMO
    symbol = "BTCUSD" # Ajustar se necessário (BTCUSD vs BTCUSD)
    
    ticket = await bridge.execute_order(symbol, "BUY", 0.01, 0.0) # Market Order 0.01
    
    if ticket:
        print(f"-> ✅ Ordem Real Enviada com Sucesso | Ticket: {ticket} (Ω-Execution OK)")
    else:
        print("-> ❌ Falha no Envio da Ordem Real.")

    # 🧪 ETAPA 3: GUARDRAILS FTMO (Risk Enforcement)
    # Apenas log de status, pois não queremos forçar um drawdown real.
    print("[INTEGRAÇÃO] Verificando Guardrail FTMO Ω-11.1...")
    if bridge.account_info:
        status = "🟢 SEGURO" if bridge.account_info.daily_loss < 0.04 else "🔴 BLOQUEADO"
        print(f"-> Status de Risco: {status} (Loss: {bridge.account_info.daily_loss*100:.2f}%)")

    print("\n✅ Teste Real Finalizado (Ponte do Absoluto Validada).")
    await bridge.stop()

if __name__ == "__main__":
    asyncio.run(test_meta_bridge_real())
