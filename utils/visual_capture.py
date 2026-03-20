import mss
import mss.tools
from PIL import Image
import pygetwindow as gw
import os
import time
import ctypes
from ctypes import wintypes
try:
    import win32gui
    import win32con
except ImportError:
    win32gui = None
    win32con = None
import threading
from utils.logger import log

# [Ω-CAPTURE-LOCK] Previne capturas paralelas e conflitos de EnumWindows
CAPTURE_LOCK = threading.Lock()

# [Ω-DPI] Enable DPI awareness for accurate screenshot coordinates
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

def capture_mt5_window(output_path: str) -> bool:
    """
    [Ω-AUDIT] Captures the MetaTrader 5 window and saves it to output_path.
    Uses aggressive focus methods for Windows.
    """
    if not CAPTURE_LOCK.acquire(timeout=5.0):
        log.warning("⚠️ Capture Lock Timeout: ignorando screenshot para não travar o loop.")
        return False
        
    try:
        # 1. Encontrar a janela correta (Priorizando a classe do MT5)
        hwnd = 0
        def enum_windows_callback(h, l):
            nonlocal hwnd
            class_name = win32gui.GetClassName(h)
            title = win32gui.GetWindowText(h)
            # Reliable identification via Class Name or common Title fragments
            is_mt5_class = 'MetaQuotes' in class_name or 'Terminal' in class_name
            is_mt5_title = 'MetaTrader' in title or ('FTMO' in title and 'BTCUSD' in title)
            
            if is_mt5_class or is_mt5_title:
                # Filter out tooltips or small helper windows by height
                rect = win32gui.GetWindowRect(h)
                if (rect[3] - rect[1]) > 300: # Main terminal is usually > 300px
                    hwnd = h
                    return False 
            return True

        if win32gui:
            try:
                win32gui.EnumWindows(enum_windows_callback, None)
            except Exception as e:
                # [Ω-FIX] O erro 183 (Already exists) ocorre frequentemente quando o callback retorna False
                # para parar a enumeração. Se encontramos o HWND, podemos ignorar qualquer exceção do EnumWindows.
                if not hwnd:
                    # Somente loga se realmente não encontramos nada, para evitar ruído.
                    log.debug(f"EnumWindows completed with message: {e}")
        
        if not hwnd:
            # Fallback p/ pygetwindow se win32gui falhar em encontrar
            windows = [w for w in gw.getWindowsWithTitle('MetaTrader 5')]
            if windows:
                hwnd = windows[0]._hWnd
        
        if not hwnd:
            # Fallback final: Capture monitor if no window found
            log.warning("⚠️ MT5 Window not found. Capturing primary monitor.")
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                sct.shot(output=output_path)
                return True

        # 2. AGGRESSIVE FOCUS (Bypass Windows focus-stealing protection)
        if win32gui:
            # Restore if minimized
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            
            # THE TRICK: Simular ALT para 'dar permissão' de foco ao processo
            import pyautogui
            pyautogui.press('alt') 
            
            # Tentar múltiplos métodos de ativação
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            win32gui.SetForegroundWindow(hwnd)
            win32gui.BringWindowToTop(hwnd)
            
            # Aguardar renderização
            time.sleep(1.0)
            
            # [Ω-FIX] Obter retângulo VISÍVEL (ignorando sombras do Win10/11)
            # DWMWA_EXTENDED_FRAME_BOUNDS = 9
            rect = wintypes.RECT()
            DWMWA_EXTENDED_FRAME_BOUNDS = 9
            ctypes.windll.dwmapi.DwmGetWindowAttribute(
                wintypes.HWND(hwnd),
                DWMWA_EXTENDED_FRAME_BOUNDS,
                ctypes.byref(rect),
                ctypes.sizeof(rect)
            )
            
            region = {
                "top": rect.top,
                "left": rect.left,
                "width": rect.right - rect.left,
                "height": rect.bottom - rect.top
            }
        else:
            # Fallback
            window = gw.Window(hwnd)
            window.activate()
            time.sleep(0.5)
            region = {"top": window.top, "left": window.left, "width": window.width, "height": window.height}

        # 3. CAPTURE (Garantir que a região é válida)
        if region["width"] <= 0 or region["height"] <= 0:
            log.error("❌ Região de captura inválida (L=0 ou A=0).")
            return False

        # [Ω-FIX] Usar PyAutoGUI em vez de mss para evitar glitches de aceleração de hardware e DPI
        try:
            import pyautogui
            # pyautogui usa (left, top, width, height)
            py_region = (region["left"], region["top"], region["width"], region["height"])
            screenshot = pyautogui.screenshot(region=py_region)
            screenshot.save(output_path)
            return True
        except Exception as e:
            log.warning(f"⚠️ Falha no PyAutoGUI: {e}. Tentando fallback MSS...")
            with mss.mss() as sct:
                sct_img = sct.grab(region)
                mss.tools.to_png(sct_img.raw, sct_img.size, output=output_path)
                return True
            
    except Exception as e:
        log.error(f"❌ Erro na captura visual do MT5: {e}")
        return False
    finally:
        # Garantir liberação do Lock mesmo em caso de erro fatal
        if CAPTURE_LOCK.locked():
            try:
                CAPTURE_LOCK.release()
            except RuntimeError:
                pass
