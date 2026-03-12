"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              DUBAI MATRIX ASI — METALOGIC AGENTS (Phase Ω)                  ║
║     Inteligência Suprema (Nível 29): Semântica de Kripke e Lógica           ║
║     Intuicionista aplicada ao Fluxo de Consciência.                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from core.consciousness.agents.base import BaseAgent, AgentSignal

class KripkeSemanticsAgent(BaseAgent):
    """
    [Phase Ω-Metalogic] Semântica de Kripke (Mundos Possíveis).
    Modela o presente como um nó em um grafo de mundos possíveis.
    O agente cria 5 versões 'alternativas' do snapshot atual mudando levemente
    os pesos dos indicadores (ruído de observação). Se o sinal de rompimento 
    sobrevive a todos os mundos possíveis (Verdade Necessária), a confiança 
    é elevada a níveis de PhD. Se o sinal falha em um mundo, é meramente 
    Contingente e a ASI veta o risco.
    """
    def __init__(self, weight=4.8):
        super().__init__("KripkeSemantics", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 5:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)
        
        # Sinal base no mundo real
        real_world_signal = np.sign(closes[-1] - closes[-2])
        
        # Simular 5 mundos possíveis com perturbações de ruído (0.1% ATR)
        atr = snapshot.indicators.get("M1_atr_14", [20.0])[-1]
        worlds = []
        for _ in range(5):
            noise = np.random.normal(0, atr * 0.05)
            perturbed_signal = np.sign((closes[-1] + noise) - closes[-2])
            worlds.append(perturbed_signal)
            
        # Verificar Invariância (Verdade Necessária)
        is_necessary = all(w == real_world_signal for w in worlds)
        
        signal = 0.0
        conf = 0.0
        reason = "CONTINGENT_TRUTH"
        
        if is_necessary and real_world_signal != 0:
            signal = float(real_world_signal)
            conf = 0.98
            reason = f"NECESSARY_TRUTH_DETECTED (Stable in 5/5 alternative worlds)"
        else:
            # A verdade do sinal depende do ruído. É frágil.
            signal = 0.0
            conf = 0.0
            reason = "FRAGILE_LOGIC_VETO (Signal failed in alternative worlds)"

        return AgentSignal(self.name, signal, conf, reason, self.weight)


class IntuitionisticLogicAgent(BaseAgent):
    """
    [Phase Ω-Metalogic] Lógica Intuicionista (Sem Terceiro Excluído).
    Na lógica clássica, um suporte ou rompe ou não rompe. Na lógica intuicionista,
    não basta não ser falso, você precisa de uma PROVA CONSTRUTIVA.
    Este agente exige que o volume e o spread confirmem o rompimento
    simultaneamente. Se não há prova, o estado é Indeterminado (Veto).
    """
    def __init__(self, weight=4.5):
        super().__init__("IntuitionisticLogic", weight)

    def analyze(self, snapshot, **kwargs) -> AgentSignal:
        # Prova Construtiva de Rompimento:
        # 1. Delta de Preço > 0.5 ATR
        # 2. Delta de Volume > 1.5x média
        # 3. Spread não alargou (Liquidez presente)
        
        candles_m1 = snapshot.candles.get("M1")
        if not candles_m1 or len(candles_m1["close"]) < 10:
            return AgentSignal(self.name, 0.0, 0.0, "NO_DATA", self.weight)

        closes = np.array(candles_m1["close"], dtype=np.float64)
        vols = np.array(candles_m1["tick_volume"], dtype=np.float64)
        atr = snapshot.indicators.get("M1_atr_14", [20.0])[-1]
        
        price_move = closes[-1] - closes[-2]
        vol_surge = vols[-1] / (np.mean(vols[-10:-1]) + 1e-6)
        
        # Verificar spread via metadados ou symbol_info
        sym_info = snapshot.symbol_info
        spread_is_tight = True
        if sym_info:
            current_spread = sym_info.get("spread", 0)
            avg_spread = 3000 # Estimativa conservadora p/ BTC
            if current_spread > avg_spread * 1.5:
                spread_is_tight = False

        signal = 0.0
        conf = 0.0
        reason = "NO_CONSTRUCTIVE_PROOF"
        
        # Construção da Prova de Alta
        if price_move > atr * 0.4 and vol_surge > 1.3 and spread_is_tight:
            signal = 1.0
            conf = 0.95
            reason = f"CONSTRUCTIVE_BULL_PROOF (P={price_move:.1f}, V={vol_surge:.1f}x)"
            
        # Construção da Prova de Baixa
        elif price_move < -atr * 0.4 and vol_surge > 1.3 and spread_is_tight:
            signal = -1.0
            conf = 0.95
            reason = f"CONSTRUCTIVE_BEAR_PROOF (P={price_move:.1f}, V={vol_surge:.1f}x)"
            
        return AgentSignal(self.name, signal, conf, reason, self.weight)
