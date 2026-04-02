import sys
import os
import shutil
import time
import math
import threading
from typing import Dict, Any, List

class SolennTerminalMatrix:
    """ 
    [Ω-TERMINAL] Motor Visual de Matriz Terminal.
    Renderizador O(1) de escapes ANSI resiliente a logs externos.
    """
    
    _lock = threading.Lock()
    _log_buffer = []
    _max_logs = 10
    _ui_active = False

    # Cores ANSI
    C_RESET = "\033[0m"
    C_GREEN = "\033[38;2;0;255;150m"
    C_DARK_GREEN = "\033[38;2;0;100;50m"
    C_CYAN = "\033[38;2;0;255;255m"
    C_BLUE = "\033[38;2;0;130;255m"
    C_RED = "\033[38;2;255;50;50m"
    C_ORANGE = "\033[38;2;255;150;0m"
    C_YELLOW = "\033[38;2;255;255;0m"
    C_GRAY = "\033[38;2;100;100;100m"
    C_LUMEN = "\033[38;2;200;255;220m"
    
    BG_DARK = "\033[48;2;5;10;15m"
    CLEAR_EOL = "\033[K"

    @classmethod
    def enable_ansi_windows(cls):
        """Habilita cores no Windows CMD / PowerShell."""
        if os.name == 'nt':
            os.system('color')
    
    @classmethod
    def clear_screen(cls):
        with cls._lock:
            sys.stdout.write("\033[2J\033[H" + cls.BG_DARK)
            sys.stdout.flush()

    @classmethod
    def hide_cursor(cls):
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()

    @classmethod
    def show_cursor(cls):
        sys.stdout.write("\033[?25h" + cls.C_RESET)
        sys.stdout.flush()

    @classmethod
    def move_xy(cls, x: int, y: int):
        sys.stdout.write(f"\033[{y};{x}H")

    @classmethod
    def print_at(cls, x: int, y: int, text: str, color: str = ""):
        with cls._lock:
            cls.move_xy(x, y)
            # Imprime com CLEAR_EOL para não deixar lixo de logs passados na mesma linha
            sys.stdout.write(color + text + cls.C_RESET + cls.BG_DARK + cls.CLEAR_EOL)
            sys.stdout.flush()

    @classmethod
    def add_log(cls, message: str):
        """ Adiciona mensagem ao buffer de logs rotativo. """
        timestamp = time.strftime("%H:%M:%S")
        cls._log_buffer.append(f"[{timestamp}] {message}")
        if len(cls._log_buffer) > cls._max_logs:
            cls._log_buffer.pop(0)

    @classmethod
    def boot_sequence(cls):
        """ Sequência Lenta de Inicialização Alien. """
        if not sys.stdout.isatty(): return
        
        cls._ui_active = True
        cls.enable_ansi_windows()
        cls.clear_screen()
        cls.hide_cursor()
        
        width = shutil.get_terminal_size().columns or 100
        
        lines = [
            f"{cls.C_CYAN}[OS: INITIALIZING NEURAL KERNEL]{cls.C_RESET}",
            f"{cls.C_DARK_GREEN}Mounting Holographic Memory Banks... OK{cls.C_RESET}",
            f"{cls.C_DARK_GREEN}Establishing HFTP Bridge via Zero-Copy IPC... OK{cls.C_RESET}",
            f"{cls.C_BLUE}Bypassing Standard Execution Paradigms... OK{cls.C_RESET}",
            f"{cls.C_ORANGE}Warning: Antifragile State Manager Hooked. {cls.C_RESET}"
        ]
        
        for i, line in enumerate(lines):
            cls.print_at(2, i + 2, line)
            time.sleep(0.1) # v2: Fast Boot
            
        time.sleep(0.3)
        cls.clear_screen()

        # Logo Render
        logo = [
            r"   _____ ____  _    ____NNN ",
            r"  / ___// __ \/ /  / ____/ | / / | / /",
            r"  \__ \/ / / / /  / __/ /  |/ /  |/ / ",
            r" ___/ / /_/ / /__/ /___/ /|  / /|  /  ",
            r"/____/\____/_____/_____/_/ |_/_/ |_/  "
        ]

        center_x = max(2, (width - 40) // 2)
        for i, l in enumerate(logo):
            cls.print_at(center_x, i + 4, l, cls.C_LUMEN)
            time.sleep(0.05)
            
        cls.print_at(center_x, 10, "ASIAN COGNITIVE NODE Ω - 100% AWAKE", cls.C_CYAN)
        time.sleep(0.5)
        cls.clear_screen()

    @classmethod
    def render_tactical_dashboard(cls, telemetry: Dict[str, Any]):
        """ Renderiza UI estática tática atualizada em loop O(1). """
        if not cls._ui_active: return
        
        # Grid lines
        width, height = shutil.get_terminal_size()
        if width < 95 or height < 20: 
            # Terminal muito pequeno, desativa UI para não bagunçar
            cls.restore()
            cls._ui_active = False
            print("⚠️ Terminal size too small for Matrix UI. Switching to raw logs.")
            return

        with cls._lock:
            # Header
            cls.print_at(2, 2, "┌" + "─"*90 + "┐", cls.C_CYAN)
            cls.print_at(2, 3, "│  S O L É N N   Ω   [ 100 %   C O G N I T I V E   A W A R E N E S S ]                │", cls.C_CYAN)
            cls.print_at(2, 4, "├" + "─"*30 + "┬" + "─"*29 + "┬" + "─"*29 + "┤", cls.C_CYAN)

            # Columns Headers
            cls.print_at(2, 5, "│ " + cls.C_LUMEN + "SENSORY NETWORKS" + cls.C_CYAN.rjust(15) + " │ ", cls.C_CYAN)
            cls.move_xy(34, 5)
            sys.stdout.write(cls.C_LUMEN + "RISK SANCTUM FTMO" + cls.C_CYAN.rjust(14) + "│ ")
            cls.move_xy(64, 5)
            sys.stdout.write(cls.C_LUMEN + "Ω CONSCIOUSNESS STATE" + cls.C_CYAN.rjust(10) + "│")

            # Content Sensory
            lag = telemetry.get('bridge_latency_ms', 0)
            c_lag = cls.C_GREEN if lag < 5 else (cls.C_YELLOW if lag < 20 else cls.C_RED)
            cls.print_at(2, 7, f"│ HFTP Lag  : {c_lag}{lag:<10.3f}{cls.C_CYAN} ms │", cls.C_CYAN)
            
            regime = telemetry.get('regime_label', 'BOOTING')
            cls.print_at(2, 8, f"│ Regime    : {cls.C_LUMEN}{regime:<14}{cls.C_CYAN} │", cls.C_CYAN)
            
            volatility = telemetry.get('volatility_tensile', 0.0)
            cls.print_at(2, 9, f"│ Vol Tens  : {cls.C_YELLOW}{volatility:<14.2f}{cls.C_CYAN} │", cls.C_CYAN)

            # Content Risk
            pnl = telemetry.get('live_pnl', 0.0)
            c_pnl = cls.C_GREEN if pnl >= 0 else cls.C_RED
            cls.print_at(34, 7, f"│ Live PnL  : {c_pnl}{pnl:<14.2f}{cls.C_CYAN} │", cls.C_CYAN)
            
            dd = telemetry.get('drawdown_pct', 0.0)
            c_dd = cls.C_GREEN if dd < 2.0 else cls.C_RED
            cls.print_at(34, 8, f"│ DD limit  : {c_dd}{dd:<14.3f}%{cls.C_CYAN}│", cls.C_CYAN)
            
            slots = telemetry.get('slots_active', 0)
            cls.print_at(34, 9, f"│ Exp Slots : {cls.C_LUMEN}{slots:<14}{cls.C_CYAN} │", cls.C_CYAN)

            # Content Consciousness
            reflexivity_r = telemetry.get('reflexivity_r', 0.0)
            c_r = cls.C_ORANGE if reflexivity_r > 0.8 else cls.C_LUMEN
            cls.print_at(64, 7, f"│ Reflex R  : {c_r}{reflexivity_r:<14.3f}{cls.C_CYAN} │", cls.C_CYAN)
            
            entropy_s = telemetry.get('quantum_entropy', 0.0)
            c_s = cls.C_CYAN if entropy_s < 0.5 else cls.C_GRAY
            cls.print_at(64, 8, f"│ Quant S   : {c_s}{entropy_s:<14.4f}{cls.C_CYAN} │", cls.C_CYAN)
            
            prob_success = telemetry.get('prob_success', 1.0)
            c_prob = cls.C_GREEN if prob_success > 0.7 else cls.C_YELLOW
            cls.print_at(64, 9, f"│ Prob Goal : {c_prob}{(prob_success*100):<12.1f}%{cls.C_CYAN} │", cls.C_CYAN)

            # Health & Metrics
            cls.print_at(2, 11, "├" + "─"*90 + "┤", cls.C_CYAN)
            sre_status = telemetry.get('sre_status', 'OPTIMAL')
            c_sre = cls.C_GREEN if sre_status == 'OPTIMAL' else (cls.C_YELLOW if sre_status == 'DEGRADED' else cls.C_RED)
            brier = telemetry.get('brier_score', 0.0)
            safe = telemetry.get('safe_mode', False)
            cls.print_at(2, 12, f"│ HEALTH: {c_sre}{sre_status:<10}{cls.C_CYAN} | BRIER_DRIFT: {cls.C_LUMEN}{brier:<8.4f}{cls.C_CYAN} | SAFE_MODE: {cls.C_RED}{str(safe):<5}{cls.C_CYAN} │", cls.C_CYAN)
            
            cls.print_at(2, 13, "├" + "─"*90 + "┤", cls.C_CYAN)

            # Log Area (Fixed 5 lines for rolling logs to prevent terminal jump)
            last_msg = telemetry.get('last_log', '...')
            if last_msg != '...':
                cls.add_log(last_msg)

            for i, log_line in enumerate(cls._log_buffer[-5:]):
                cls.print_at(2, 14 + i, f"│ {cls.C_GRAY}{log_line[:86]:<86}{cls.C_CYAN} │", cls.C_CYAN)

            cls.print_at(2, 19, "└" + "─"*90 + "┘", cls.C_CYAN)
            sys.stdout.flush()

    @classmethod
    def restore(cls):
        cls._ui_active = False
        cls.show_cursor()
        sys.stdout.write(cls.C_RESET + "\n")
        sys.stdout.flush()
