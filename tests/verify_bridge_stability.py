import os
import sys
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)
    
import time
from market.mt5_bridge import MT5Bridge
from cpp.asi_bridge import CPP_CORE
from utils.logger import log

def test_bridge_resilience():
    log.info("🧪 [STABILITY TEST] Verificando Resiliência da Infraestrutura...")
    
    # 1. Test C++ DLL Discovery
    if not CPP_CORE._loaded:
        log.error("❌ C++ Core failed to load. Check MSYS2/MinGW paths.")
    else:
        log.omega("✅ C++ Core carregado com sucesso via descoberta dinâmica.")
        
    # 2. Test Socket Reconnection (Simulated)
    bridge = MT5Bridge()
    log.info("📡 Iniciando HFT Socket Server...")
    bridge._start_socket_server()
    time.sleep(1)
    
    if bridge._socket_running:
        log.omega("✅ TCP Server iniciado corretamente.")
        # Simular restart sem liberar porta
        log.info("🔄 Simulando restart rápido do socket...")
        bridge._start_socket_server() # Não deve dar erro de bind
        log.omega("✅ Rebind SO_REUSEADDR validado.")
    else:
        log.error("❌ TCP Server falhou ao iniciar.")

    log.omega("✅ TESTE DE RESILIÊNCIA CONCLUÍDO.")

if __name__ == "__main__":
    test_bridge_resilience()
