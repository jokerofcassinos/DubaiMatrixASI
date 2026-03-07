"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DUBAI MATRIX ASI — RISK QUANTUM ENGINE                   ║
║         Gestão de risco quântica: Kelly, CVaR, circuit breakers            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import Optional
from datetime import datetime, timezone

from config.omega_params import OMEGA
from config.settings import (
    RISK_MAX_DAILY_LOSS_PCT, RISK_MAX_DRAWDOWN_PCT,
    RISK_CIRCUIT_BREAKER_PAUSE_MIN, RISK_MAX_CONSECUTIVE_LOSSES,
    RISK_MAX_POSITION_PCT, ASIState
)
from config.exchange_config import MIN_LOT_SIZE, MAX_LOT_SIZE, LOT_STEP
from utils.math_tools import MathEngine
from utils.logger import log
from utils.decorators import catch_and_log
from cpp.asi_bridge import CPP_CORE


class RiskQuantumEngine:
    """
    Motor de risco quântico — protege o capital com precisão cirúrgica.

    NÃO usa stop loss fixo estúpido.
    Usa: Kelly Criterion + ATR dinâmico + drawdown monitors + circuit breakers.
    """

    def __init__(self):
        self.math = MathEngine()
        self._daily_pnl = 0.0
        self._daily_start_balance = 0.0
        self._daily_trades = 0
        self._circuit_breaker_until = None

    @catch_and_log(default_return=0.01)
    def calculate_lot_size(self, balance: float, stop_loss_distance: float,
                           win_rate: float, avg_win: float, avg_loss: float,
                           symbol_info: dict = None, confidence: float = 0.5,
                           asi_state: ASIState = None, snapshot = None) -> float:
        """
        Calcula lot size ótimo usando Kelly Criterion modificado via C++.
        Transição OMEGA-CLASS: Otimização da Taxa de Crescimento Temporal (Non-Ergodic Growth).
        """
        if balance <= 0 or stop_loss_distance <= 0:
            return MIN_LOT_SIZE

        # 1. Obter métricas de performance base (Normalization)
        wr = max(0.3, min(0.9, win_rate))
        
        # OMEGA-CLASS: Bayesian Priors for Cold Start
        # Se avg_win/avg_loss vierem zerados ou muito pequenos ($1.0), 
        # usamos um prior estatístico de 0.2% do ATR ou do Preço.
        price = snapshot.price if snapshot else 67000.0
        atr = snapshot.indicators.get("M1_atr_14", [price * 0.001])[0]
        
        baseline_move = max(50.0, atr * 0.5) # No mínimo $50 de move ou 0.5 ATR
        
        aw = max(baseline_move, avg_win)
        al = max(baseline_move, avg_loss)
        rr = aw / al

        # 2. ═══ [OMEGA-CLASS] NON-ERGODIC GROWTH OPTIMIZATION ═══
        # Em vez de Kelly estático, buscamos a alavancagem que maximiza g(f).
        # Simulamos 5 níveis de leverage para encontrar o pico da curva de crescimento.
        best_leverage = 0.0
        max_growth = -999.0
        
        # r_win_pct e r_loss_pct em termos de variação do preço
        price = snapshot.price if snapshot else 1.0
        avg_win_price_pct = aw / price if price > 0 else 0.01
        avg_loss_price_pct = al / price if price > 0 else 0.01

        for leverage in [0.5, 1.0, 2.0, 5.0, 10.0]:
            growth = CPP_CORE.non_ergodic_growth_rate(wr, avg_win_price_pct, avg_loss_price_pct, leverage)
            if growth > max_growth:
                max_growth = growth
                best_leverage = leverage

        # Se o crescimento máximo for negativo (Ruína Probabilística), reduzimos drasticamente.
        if max_growth < 0:
            log.warning(f"⚠️ NON-ERGODIC RUIN DETECTED: Growth Rate {max_growth:.6f} for best leverage {best_leverage}. Reducing exposure.")
            risk_fraction = 0.001 
        else:
            # f* ótimo baseado em crescimento temporal
            # Mapeamos a leverage ótima para uma fração de risco do balanço
            # Sizing = (Best Leverage * Distância do SL em %)
            sl_pct = stop_loss_distance / price if price > 0 else 0.01
            risk_fraction = best_leverage * sl_pct
            log.omega(f"📊 NON-ERGODIC OPTIMIZATION: Max Growth {max_growth:.6f} @ {best_leverage}x Leverage. Risk Fraction: {risk_fraction:.4f}")

        # 3. ═══ [OMEGA-CLASS] ITO CALCULUS REFINEMENT (Volatility Tax) ═══
        # Se tivermos volatilidade (ATR), ajustamos pela taxa de "imposto" estocástico.
        atr_m1 = snapshot.indicators.get("M1_atr_14") if hasattr(snapshot, 'indicators') else None
        if atr_m1 is not None and len(atr_m1) > 0:
            sigma_pct = (np.mean(atr_m1[-14:]) * np.sqrt(1440)) / price # Vol diaria estimada
            mu_pct = (wr * avg_win_price_pct - (1-wr) * avg_loss_price_pct)
            
            log.debug(f"📐 RISK_MATH: wr={wr:.4f} mu_pct={mu_pct:.6f} sigma_pct={sigma_pct:.6f} aw_pct={avg_win_price_pct:.6f} al_pct={avg_loss_price_pct:.6f}")
            
            ito_sizing = CPP_CORE.ito_lot_sizing(balance, wr, mu_pct, sigma_pct, 1.0/1440.0)
            ito_fraction = ito_sizing / balance if balance > 0 else 0.01
            
            # Conservadorismo Quântico: Mínimo entre o crescimento não-ergódico e o limite de Ito
            risk_fraction = min(risk_fraction, ito_fraction)
            log.omega(f"📉 ITO REFINEMENT: Vol Taxed Risk Ceiling = {ito_fraction:.4f} (Ito_Sizing=${ito_sizing:.2f})")

        # 4. Conviction Sizing (Phase 22)
        kelly_fraction = OMEGA.get("kelly_fraction", 0.25)
        risk_fraction *= (kelly_fraction * 4.0) # Normaliza pelo multiplicador de agressividade do CEO

        if confidence >= 0.80:
            mult = OMEGA.get("high_conviction_multiplier", 2.0)
            risk_fraction *= mult
            log.omega(f"🔥 HIGH CONVICTION: Multiplier {mult}x applied. Final Risk: {risk_fraction:.4f}")

        # 5. Tiers de Agressão floor (Phase 38) e Circuit Breakers
        max_risk_pct = OMEGA.get("position_size_pct", 10.0) / 100.0
        if confidence >= 0.70:
            max_risk_pct *= 2.0

        risk_fraction = min(risk_fraction, max_risk_pct)
        
        # [TOTAL WAR OVERRIDES]
        if balance >= 5000.0:
            if asi_state and balance < asi_state.peak_balance * 0.70:
                risk_fraction *= 0.25 
            elif confidence >= 0.85: risk_fraction = max(risk_fraction, 0.95)
            elif confidence >= 0.75: risk_fraction = max(risk_fraction, 0.50)
            elif confidence >= 0.65: risk_fraction = max(risk_fraction, 0.30)

        # 6. Converter para Lote
        point_value = 1.0
        if symbol_info:
            contract_size = symbol_info.get("trade_contract_size", 1)
            point = symbol_info.get("point", 0.01)
            if point > 0:
                point_value = contract_size * point

        lot_size = balance * risk_fraction / (stop_loss_distance * point_value) if stop_loss_distance > 0 else MIN_LOT_SIZE

        # Ceiling de Exposição (Phase 40)
        exposure_ratio = OMEGA.get("exposure_ceiling_balance_ratio", 2000.0)
        max_safe_lots = balance / max(500.0, exposure_ratio) 
        if lot_size > max_safe_lots:
            lot_size = max_safe_lots

        lot_size = round(lot_size / LOT_STEP) * LOT_STEP
        lot_size = max(MIN_LOT_SIZE, min(MAX_LOT_SIZE, lot_size))

        return lot_size

        # 3. PHASE 40: Hard Exposure Ceiling
        # $30k account -> Max 15.0 lots (Safety ratio: 2000 units of balance per lot)
        # Isso garante que mesmo em Total War, não batemos 100 lotes que liquidam com 0.4% de variação.
        exposure_ratio = OMEGA.get("exposure_ceiling_balance_ratio", 2000.0)
        max_safe_lots = balance / max(500.0, exposure_ratio) 
        if lot_size > max_safe_lots:
            log.omega(f"🛡️ EXPOSURE CEILING: Lote {lot_size:.2f} excedeu teto de segurança {max_safe_lots:.2f}. Limitando.")
            lot_size = max_safe_lots

        # Arredondar para step e clamp (segurança extra local)
        lot_size = round(lot_size / LOT_STEP) * LOT_STEP
        lot_size = max(MIN_LOT_SIZE, min(MAX_LOT_SIZE, lot_size))

        return lot_size

    def check_daily_limits(self, balance: float) -> bool:
        """
        Verifica se os limites diários da FTMO foram atingidos.
        [PHASE Ω-ACCOUNT-SAFETY] Monitoramento em Dólar Absoluto.
        """
        if self._daily_start_balance <= 0:
            self._daily_start_balance = balance
            log.info(f"🏦 EQUITY_GUARD: Start Balance do dia definido em ${balance:.2f}")
            return True

        # P&L flutuante do dia (Equity - Start Balance)
        daily_pnl = balance - self._daily_start_balance
        
        # Limite Hard da FTMO: -$5000.00
        # Nosso Circuit Breaker de Segurança (Hibernação): -$4800.00
        ftmo_limit = -5000.00
        safety_limit = -4800.00
        
        if daily_pnl <= safety_limit:
            log.omega(f"🚨 [EMERGENCY HIBERNATION] P&L do dia ({daily_pnl:+.2f}) atingiu o limite de segurança de ${safety_limit:.2f}!")
            log.omega(f"🚨 [RISK] Faltam apenas ${abs(daily_pnl - ftmo_limit):.2f} para a eliminação da conta pela FTMO.")
            return False

        if daily_pnl < -500.00:
             log.warning(f"⚠️ [DANGER] Drawdown diário atingiu {daily_pnl:+.2f}. Restam ${abs(daily_pnl - safety_limit):.2f} para hibernação.")

        return True

    def check_circuit_breaker(self, asi_state, snapshot=None) -> bool:
        """Verifica se o circuit breaker deve ativar ou se manter ativo via Entropia Quântica."""
        # Se a trava foi ativada, ela só é solta se a entropia ceder e o caos estabilizar
        if self._circuit_breaker_until:
            # Em vez de olhar para o relógio, olhamos para a estrutura causal do mercado
            is_locked = True
            
            if snapshot and snapshot.indicators:
                entropy = snapshot.indicators.get("M5_entropy")
                chaos_lyapunov = snapshot.indicators.get("M5_lyapunov")
                
                ent_val = entropy[-1] if isinstance(entropy, (list, np.ndarray)) and len(entropy) > 0 else 3.0
                lya_val = chaos_lyapunov[-1] if isinstance(chaos_lyapunov, (list, np.ndarray)) and len(chaos_lyapunov) > 0 else 0.5
                
                # Se a entropia (desordem direcional) caiu abaixo de 1.8 e o lyapunov (previsibilidade) é < 0 (determinístico)
                if ent_val < 1.8 and lya_val < 0.0:
                    is_locked = False
                    log.omega(f"🟢 [ENTROPY LOCK RELEASED] Caos dissipado (Ent={ent_val:.2f}, Lya={lya_val:.2f}). Resumindo operações.")
                else:
                    # Trava mecânica de segurança de tempo infinito, apenas notifica a cada ciclo longo
                    if int(datetime.now(timezone.utc).timestamp()) % 60 == 0:
                        log.debug(f"🔒 [ENTROPY LOCK ACTIVE] Aguardando estabilização. Ent={ent_val:.2f} (Alvo <1.8), Lya={lya_val:.2f} (Alvo <0.0)")

            if is_locked:
                return False  # Continua em pausa termodinâmica
            else:
                self._circuit_breaker_until = None
                asi_state.circuit_breaker_active = False

        # Ativar se losses consecutivos (a ignição continua baseada no balanço destrutivo)
        if asi_state.consecutive_losses >= RISK_MAX_CONSECUTIVE_LOSSES:
            self._circuit_breaker_until = True # Flag booleana de estado de trava termodinâmica
            asi_state.circuit_breaker_active = True
            
            ent_val = 3.0
            if snapshot and snapshot.indicators:
                entropy = snapshot.indicators.get("M5_entropy")
                ent_val = entropy[-1] if isinstance(entropy, (list, np.ndarray)) and len(entropy) > 0 else 3.0

            log.omega(
                f"🔴 [QUANTUM CIRCUIT BREAKER ATIVADO] "
                f"{asi_state.consecutive_losses} losses consecutivos. "
                f"Trava ativada na Entropia={ent_val:.2f}. "
                f"Só religará quando o mercado resfriar termodinamicamente."
            )
            return False

        return True

    def check_drawdown(self, balance: float, peak_balance: float) -> bool:
        """Verifica drawdown máximo."""
        if peak_balance <= 0:
            return True

        drawdown_pct = (peak_balance - balance) / peak_balance * 100

        if drawdown_pct >= RISK_MAX_DRAWDOWN_PCT:
            log.omega(
                f"🔴 MAX DRAWDOWN HIT: {drawdown_pct:.2f}% >= {RISK_MAX_DRAWDOWN_PCT}%"
            )
            return False

        return True

    def validate_trade(self, balance: float, asi_state,
                       lot_size: float, snapshot=None) -> tuple:
        """
        Validação completa de risco antes de executar trade.
        Returns: (approved: bool, final_lot_size: float, reason: str)
        """
        # 1. Circuit breaker (Entropy-Locked)
        if not self.check_circuit_breaker(asi_state, snapshot=snapshot):
            return False, 0.0, "ENTROPY_CIRCUIT_BREAKER_ACTIVE"

        # 2. Daily limits
        if not self.check_daily_limits(balance):
            return False, 0.0, "DAILY_LOSS_LIMIT"

        # 3. Drawdown
        if not self.check_drawdown(balance, asi_state.peak_balance):
            return False, 0.0, "MAX_DRAWDOWN"

        # 4. Lot size sanity
        final_lot = max(MIN_LOT_SIZE, min(MAX_LOT_SIZE, lot_size))

        return True, final_lot, "APPROVED"

    def record_trade_result(self, profit: float, asi_state):
        """Registra resultado do trade para atualização de risco."""
        self._daily_pnl += profit
        self._daily_trades += 1
        asi_state.total_profit += profit

        if profit > 0:
            asi_state.total_wins += 1
            asi_state.consecutive_losses = 0
        else:
            asi_state.total_losses += 1
            asi_state.consecutive_losses += 1

        asi_state.total_trades += 1

    def evaluate_wormhole_trigger(self, position: dict, snapshot) -> Optional[dict]:
        """
        [PHASE Ω-TRANSCENDENCE] Wormhole Risk Recovery.
        Se uma posição atinge o 'Event Horizon' (-85% do SL), 
        abrimos um Gamma Hedge para congelar a perda.
        """
        p_profit = position.get("profit", 0.0)
        p_type = position.get("type", "")
        p_symbol = position.get("symbol") or position.get("symbol_name")
        
        # Só ativa se o prejuízo for significativo (> $50) e estiver perto do SL
        if p_profit < -50.0:
            # Pegar SL original ou delta do ATR
            # Simplificação: se o profit atual é 85% do ATR médio do SL
            atr = snapshot.indicators.get("M1_atr_14", [0.0])[0]
            sl_dist = OMEGA.get("stop_loss_atr_mult") * atr
            
            # Se o prejuízo em points ultrapassar 80% do SL esperado
            if abs(p_profit) > (sl_dist * 0.85 * 10): # Ajuste p/ valor do tick
                log.omega(f"🕳️ WORMHOLE TRIGGERED: Position {position['ticket']} near Event Horizon. Initiating Gamma Scalp.")
                return {
                    "action": "SELL" if p_type == "BUY" else "BUY",
                    "lot": position.get("volume", 0.01) * 1.5, # Hedge agressivo
                    "tp_points": 50, # Saída rápida
                    "reason": "Wormhole Recovery"
                }
        return None

    def reset_daily(self, balance: float):
        """Reset diário dos contadores."""
        self._daily_pnl = 0.0
        self._daily_start_balance = balance
        self._daily_trades = 0
        log.info(f"📊 Risk daily reset. Balance: ${balance:.2f}")
