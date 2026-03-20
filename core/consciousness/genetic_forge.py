import time
import threading
import json
import os
import random
from typing import Dict, Any, List

from config.omega_params import OMEGA
from market.mt5_bridge import MT5Bridge
from config.settings import ASIState
from utils.logger import log

class GeneticForge:
    """
    [Phase Ω-14] Forja Genética (DNA Hot-Swap & Continuous RL)
    
    Uma thread assíncrona que avalia a dor e o prazer do bot (Losses reais vs Ganhos perdidos
    nos Shadow Trades) e muta ativamente os parâmetros OMEGA em tempo de execução, 
    sobrescrevendo o omega_params.json sem reiniciar o MT5.
    """
    
    def __init__(self, bridge: MT5Bridge, asi_state: ASIState, interval_minutes: int = 15):
        self.bridge = bridge
        self.asi_state = asi_state
        self.interval_minutes = interval_minutes
        self.running = False
        self._thread = None
        self.shadow_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "audits", "shadow_trades.json")
        
    def start(self):
        if self.running: return
        self.running = True
        self._thread = threading.Thread(target=self._forge_loop, daemon=True)
        self._thread.start()
        log.omega("🧬 [GENETIC FORGE] Motor de Mutações Iniciado. Avaliando DNA a cada 15m.")

    def stop(self):
        self.running = False
        
    def _forge_loop(self):
        # Aguarda 5 minutos antes do primeiro swap para o cache preencher
        time.sleep(300)
        
        while self.running:
            try:
                self._evaluate_and_mutate()
            except Exception as e:
                log.error(f"🧬 [GENETIC FORGE] Erro na mutação do DNA: {e}")
                
            # Dormir para a próxima geração
            time.sleep(self.interval_minutes * 60)
            
    def _evaluate_and_mutate(self):
        """Avalia performance recente e muta parâmetros."""
        
        # 1. Puxar Shadow Trades
        shadow_trades = []
        if os.path.exists(self.shadow_path):
            try:
                with open(self.shadow_path, "r", encoding="utf-8") as f:
                    shadow_trades = json.load(f).get("ghosts", [])
            except:
                pass
                
        # Filtrar shadows dos últimos 60 minutos
        now = time.time()
        recent_shadows = [s for s in shadow_trades if (now - s.get("timestamp", 0)) < 3600]
        
        # 2. Avaliar Winrate Real
        win_rate = self.asi_state.win_rate if self.asi_state.total_trades > 0 else 1.0
        trades_today = self.asi_state.total_trades
        
        mutated = False
        mutations = []
        
        # Lógica de Mutação Heurística
        current_buy_threshold = OMEGA.get("buy_threshold", 0.18)
        current_rr = OMEGA.get("trinity_min_rr_ratio", 1.8)
        
        # CENA A: O Bot está perdendo dinheiro (Winrate < 75%)
        if win_rate < 0.75 and trades_today >= 3:
            # Precisa ficar mais conservador. Muta pra cima o threshold.
            new_threshold = min(0.35, current_buy_threshold * 1.05) 
            new_rr = min(3.0, current_rr * 1.1)
            
            OMEGA.set("buy_threshold", new_threshold, "GeneticForge: conservadorismo por baixa performance")
            OMEGA.set("sell_threshold", -new_threshold, "GeneticForge: conservadorismo por baixa performance")
            OMEGA.set("trinity_min_rr_ratio", new_rr, "GeneticForge: conservadorismo por baixa performance")
            
            mutations.append(f"Threshold subiu p/ {new_threshold:.3f}")
            mutations.append(f"Min RR subiu p/ {new_rr:.2f}")
            mutated = True
            
        # CENA B: O Bot está muito covarde. Winrate de 100%, mas só operou 1 vez, e tem VÁRIOS Shadows VETADOS por Threshold.
        elif win_rate >= 0.90 and len(recent_shadows) > 10 and trades_today < 3 and current_buy_threshold > 0.08:
            # Abaixa o escudo para absorver mais Trades
            new_threshold = max(0.08, current_buy_threshold * 0.95)
            new_rr = max(1.1, current_rr * 0.95)
            
            OMEGA.set("buy_threshold", new_threshold, "GeneticForge: agressividade por sub-execução")
            OMEGA.set("sell_threshold", -new_threshold, "GeneticForge: agressividade por sub-execução")
            OMEGA.set("trinity_min_rr_ratio", new_rr, "GeneticForge: agressividade por sub-execução")
            
            mutations.append(f"Threshold desceu p/ {new_threshold:.3f}")
            mutations.append(f"Min RR desceu p/ {new_rr:.2f}")
            mutated = True
            
        # MUTAÇÕES ESPECÍFICAS DE OMEGA AGENTS baseadas em aleatoriedade guiada (Exploration)
        if random.random() < 0.25: # 25% de chance de micro-mutação aleatória no Spoof Hunter
            current_spoof_wt = OMEGA.get("weight_spoof_hunter", 2.2)
            delta = random.uniform(-0.3, +0.3)
            new_spoof = max(1.0, min(5.0, current_spoof_wt + delta))
            OMEGA.set("weight_spoof_hunter", round(new_spoof, 2), "GeneticForge: micro-mutação aleatória")
            mutations.append(f"Spoof_Weight mutou p/ {new_spoof:.2f}")
            mutated = True
            
        if mutated:
            # Salvar DNA no Disco (Hot-Swap) 
            OMEGA.save()
            mut_str = " | ".join(mutations)
            log.omega(f"🧬 [DNA HOT-SWAP] Forja aplicou Otimização Evolutiva em Tempo Real: {mut_str}")
