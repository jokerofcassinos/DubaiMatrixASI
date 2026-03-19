
import os
import sys
import time
from datetime import datetime

# Root path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.visual_capture import capture_mt5_window
from utils.logger import log

def run_visual_audit_test():
    """
    [Ω-TEST] Test focus-aware screenshot capture.
    """
    os.makedirs('tests/results', exist_ok=True)
    out_path = f"tests/results/test_capture_{int(time.time())}.png"
    
    log.omega(f"🚀 INICIANDO TESTE DE CAPTURA VISUAL...")
    log.info("ℹ️ Certifique-se de que o MetaTrader 5 está aberto e que outra janela (como o Navegador) está por cima.")
    log.info("⏲️ Capturando em 3 segundos...")
    time.sleep(3)
    
    success = capture_mt5_window(out_path)
    
    if success:
        log.omega(f"✅ SUCESSO! Captura salva em: {out_path}")
        # Show absolute path for easier access
        abs_path = os.path.abspath(out_path)
        print(f"\n[FILE_LINK]: {abs_path}")
    else:
        log.error("❌ FALHA na captura visual. Verifique se o MT5 está aberto.")

if __name__ == "__main__":
    run_visual_audit_test()
