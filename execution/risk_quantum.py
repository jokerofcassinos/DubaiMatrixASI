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
                           asi_state: ASIState = None, snapshot = None,
                           commission_per_lot: float = 15.0) -> float:
        """
        Calcula lot size ótimo usando Kelly Criterion modificado via C++.
        Transição OMEGA-CLASS: Otimização da Taxa de Crescimento Temporal (Non-Ergodic Growth).
        """
        if balance <= 0 or stop_loss_distance <= 0:
            return MIN_LOT_SIZE

        # Use metrics from asi_state if they are more reliable/recent
        wr = win_rate
        aw = avg_win
        al = avg_loss

        if asi_state and asi_state.total_trades > 0:
            # We trust the synchronized state
            wr = max(0.3, min(0.9, asi_state.total_wins / asi_state.total_trades))
            aw = asi_state.avg_win
            al = asi_state.avg_loss
        
        # OMEGA-CLASS: Bayesian Priors for Cold Start (Resilience Phase)
        price = snapshot.price if snapshot else 67000.0
        atr = snapshot.indicators.get("M1_atr_14", [price * 0.001])[0] / (snapshot.digits_mult if hasattr(snapshot, 'digits_mult') else 1)
        
        # [Phase Ω-Resilience] Commission-Aware Math:
        comm_per_lot = OMEGA.get("commission_per_lot", 50.0)
        min_target_pts = OMEGA.get("min_profit_per_ticket", 80.0)
        point = (snapshot.symbol_info.get("point", 0.01) if snapshot and snapshot.symbol_info else 0.01)
        
        baseline_move = max(min_target_pts * point + comm_per_lot, atr * 0.75) 
        
        if aw <= 0: aw = baseline_move * 1.5
        if al <= 0: al = baseline_move
        
        # Limit aw to something reasonable to avoid absurd Kelly sizes
        aw = min(aw, balance * 0.05) 
        
        rr = aw / al if al > 0 else 1.0

        # 2. ═══ [OMEGA-CLASS] NON-ERGODIC GROWTH OPTIMIZATION ═══
        best_leverage = 0.0
        max_growth = -999.0
        
        avg_win_price_pct = aw / price if price > 0 else 0.01
        avg_loss_price_pct = al / price if price > 0 else 0.01

        for leverage in [0.5, 1.0, 2.0, 5.0, 10.0]:
            growth = CPP_CORE.non_ergodic_growth_rate(wr, avg_win_price_pct, avg_loss_price_pct, leverage)
            if growth > max_growth:
                max_growth = growth
                best_leverage = leverage

        if max_growth < -0.1: # [Phase Ω-Integrity] Aumentado threshold para reduzir falsos-negativos de ruína
            log.warning(f"⚠️ NON-ERGODIC RUIN DETECTED: Growth Rate {max_growth:.6f}. Reducing exposure.")
            if snapshot and hasattr(snapshot, 'metadata'):
                snapshot.metadata["non_ergodic_ruin"] = True
            risk_fraction = 0.005 # Aumentado de 0.001 para permitir strike mínimo
        else:
            if snapshot and hasattr(snapshot, 'metadata'):
                snapshot.metadata["non_ergodic_ruin"] = False
            sl_pct = stop_loss_distance / price if price > 0 else 0.01
            # [Phase Ω-Resilience] Min Growth Floor: Garantir exposição mínima em alta confiança
            effective_leverage = max(best_leverage, 1.0 if confidence > 0.8 else 0.0)
            risk_fraction = effective_leverage * sl_pct
            log.omega(f"📊 NON-ERGODIC OPTIMIZATION: Max Growth {max_growth:.6f} @ {best_leverage}x Leverage. Risk Fraction: {risk_fraction:.4f}")

        # 3. ═══ [OMEGA-CLASS] ITO CALCULUS REFINEMENT (Volatility Tax) ═══
        if snapshot and hasattr(snapshot, 'indicators'):
            atr_m1 = snapshot.indicators.get("M1_atr_14")
            if atr_m1 is not None and len(atr_m1) > 0:
                sigma_pct = (np.mean(atr_m1[-14:]) * np.sqrt(1440)) / price 
                mu_pct = (wr * avg_win_price_pct - (1-wr) * avg_loss_price_pct)
                
                ito_sizing = CPP_CORE.ito_lot_sizing(balance, wr, mu_pct, sigma_pct, 1.0/1440.0)
                ito_fraction = ito_sizing / balance if balance > 0 else 0.01
                risk_fraction = min(risk_fraction, ito_fraction)

        # 4. Conviction Sizing
        kelly_fraction = OMEGA.get("kelly_fraction", 0.25)
        risk_fraction *= (kelly_fraction * 4.0) 

        if confidence >= 0.80:
            mult = OMEGA.get("high_conviction_multiplier", 2.0)
            risk_fraction *= mult

        # [Phase Ω-Transcendence] Dynamic Order Flow Risk Modification
        # Se a pressão do livro de ofertas estiver contra a intenção do trade, reduzimos o risco.
        if snapshot and hasattr(snapshot, 'metadata'):
            # metadata tem os sinais dos agentes
            pressure = snapshot.metadata.get("orderbook_pressure", 0.0) # Assume extraction in flow
            action = snapshot.metadata.get("intended_action", "WAIT")
            
            # Se queremos comprar, mas a pressão é muito vendedora (< -0.4)
            if action == "BUY" and pressure < -0.4:
                risk_fraction *= 0.5
                log.debug("🛡️ [ORDER FLOW RISK] Pressão vendedora intensa detectada. Cortando lote pela metade.")
            # Se queremos vender, mas a pressão é muito compradora (> 0.4)
            elif action == "SELL" and pressure > 0.4:
                risk_fraction *= 0.5
                log.debug("🛡️ [ORDER FLOW RISK] Pressão compradora intensa detectada. Cortando lote pela metade.")

            # [Phase Ω-PhD] Soft-KL Risk Scaling (Information Geometry)
            kl_div = snapshot.metadata.get("kl_divergence", 0.0)
            kl_base = OMEGA.get("paradigm_shift_threshold", 0.95)
            if kl_div > kl_base:
                # Gaussian decay: Multiplier = exp(-(KL/base)^2)
                kl_mult = float(np.exp(-((kl_div / kl_base) ** 2)))
                risk_fraction *= kl_mult
                log.omega(f"🧬 [SOFT-KL SCALING] KL={kl_div:.2f} > {kl_base:.2f}. Reducing risk by {(1-kl_mult)*100:.1f}%.")

            # [Phase Ω-PhD-4] Ω-Structural Expectancy Sizing (Ghost Veto)
            if OMEGA.get("structural_expectancy_sizing_enabled", 1.0) > 0.5:
                pnl_pred = snapshot.metadata.get("pnl_prediction", "STABLE")
                # Se a expectância é negativa e NÃO é um disparo de alta energia (God-Mode/Pulse/KL/Drift), asfixiamos o lote.
                kl_div_current = snapshot.metadata.get("kl_divergence", 0.0)
                kl_shift = kl_div_current > OMEGA.get("paradigm_shift_threshold", 0.95)
                
                # [Phase Ω-Eternity] Drift Regime awareness
                regime_name = "UNKNOWN"
                if hasattr(snapshot, 'regime') and snapshot.regime:
                    if hasattr(snapshot.regime, 'current'):
                        regime_name = snapshot.regime.current.value
                    else:
                        regime_name = str(snapshot.regime)
                
                is_stable_drift = "DRIFTING" in regime_name or "LIQUIDATION" in regime_name
                
                # [Phase Ω-Inertia] Kinetic Inertia: Se o consenso do enxame é total, bypassamos o pessimismo do Java
                # No ASIBrain, salvamos Φ em phi_last
                phi = snapshot.metadata.get("phi_last", 0.0)
                raw_signal = snapshot.metadata.get("raw_signal", 0.0)
                is_consensus_absolute = phi > 0.35 and abs(raw_signal) > 0.50
                
                is_lethal = (snapshot.metadata.get("v_pulse_detected", False) or 
                             snapshot.metadata.get("god_mode_active", False) or 
                             is_stable_drift or
                             is_consensus_absolute or
                             kl_shift)
                             
                if "NEGATIVE_EXPECTANCY" in pnl_pred:
                    if not is_lethal:
                        log.omega(f"🛡️ [Ω-STRUCTURAL SIZING] Negative Expectancy ({pnl_pred}). Ghost Veto: lot_size=0.")
                        return 0.0 
                    else:
                        log.info(f"🦅 [EXPECTANCY BYPASS] Negative Expectancy bypassed. Reason: " + 
                                 f"{'Drift' if is_stable_drift else ('Consensus' if is_consensus_absolute else 'Ignition')}")
                        # Em caso letal com histórico ruim, forçamos exposição mínima.
                        risk_fraction = max(0.005, risk_fraction * 0.5)

         # 5. Tiers de Agressão floor e Circuit Breakers
        max_risk_pct = OMEGA.get("position_size_pct", 10.0) / 100.0
        if confidence >= 0.70:
            max_risk_pct *= 2.0

        risk_fraction = min(risk_fraction, max_risk_pct)
        risk_fraction = max(0.001, risk_fraction)

        # 6. Converter para Lote
        point_value = 1.0
        if symbol_info:
            contract_size = symbol_info.get("trade_contract_size", 1)
            point = symbol_info.get("point", 0.01)
            if point > 0:
                point_value = contract_size * point

        lot_size = balance * risk_fraction / (stop_loss_distance * point_value) if stop_loss_distance > 0 else MIN_LOT_SIZE

        # 7. [Phase Ω-Infrastructure] Margin Level Guard (Anti-Stop-Out)
        if snapshot and snapshot.account:
            margin_level = snapshot.account.get("margin_level", 0.0)
            margin = snapshot.account.get("margin", 0.0)
            
            # Se a margem é 0, o nível é tecnicamente infinito. MT5 retorna 0.0 neste caso.
            if margin == 0 or margin_level == 0:
                pass # Margem livre total
            elif margin_level < 150.0:
                log.warning(f"🚨 [MARGIN GUARD] Critical Level {margin_level:.2f}% < 150%. Locking lot to MIN_LOT.")
                lot_size = MIN_LOT_SIZE
            elif margin_level < 200.0:
                log.warning(f"⚠️ [MARGIN GUARD] Caution Level {margin_level:.2f}% < 200%. Reducing lot by 50%.")
                lot_size *= 0.5

        # Hard Exposure Ceiling
        exposure_ratio = OMEGA.get("exposure_ceiling_balance_ratio", 2000.0)
        max_safe_lots = balance / max(500.0, exposure_ratio) 
        if lot_size > max_safe_lots:
            log.omega(f"🛡️ EXPOSURE CEILING: Lote {lot_size:.2f} excedeu teto de segurança {max_safe_lots:.2f}. Limitando.")
            lot_size = max_safe_lots

        # [Phase Ω-PhD-5] Micro-Scaling: Redução de 50% em trades que bypassaram regime podre
        # [Phase Ω-PhD-6] Micro-Scaling: Redução de 25% em trades TEC (Singularidade)
        # Aplicado após todos os caps para garantir o efeito de exploração segura.
        if snapshot and hasattr(snapshot, "metadata"):
            if snapshot.metadata.get("bypassed_stale_regime", False):
                # Se for TEC, a redução é de 25% (0.75x), se for Stale Regime (PhD-5) é de 50% (0.5x)
                if snapshot.metadata.get("is_tec_active", False):
                    lot_size *= 0.75
                    log.info("🦅 [Ω-MICRO SCALING: TEC] Structural Singularity detected. Reducing lot size by 25% for safe exploration.")
                else:
                    lot_size *= 0.5
                    log.info("🦅 [Ω-MICRO SCALING: STALE] Stale regime bypass detected. Reducing lot size by 50% for safety.")

        lot_size = round(lot_size / LOT_STEP) * LOT_STEP
        lot_size = max(MIN_LOT_SIZE, min(MAX_LOT_SIZE, lot_size))

        return lot_size

    def validate_trade(self, balance: float, asi_state: ASIState, lot_size: float) -> tuple[bool, float, str]:
        """
        Executa validações finais de segurança antes do disparo.
        Retorna (approved, final_lot, reason).
        """
        try:
            # 1. Check Daily Limits (FTMO Safety)
            if not self.check_daily_limits(balance):
                return False, lot_size, "Limite diário atingido ou Hibernação ativa."

            # 2. Maximum Risk Concentration
            # [Phase 37] Previne exposição excessiva em um único trade
            if lot_size <= 0:
                return False, 0.0, "Ghost Veto: Lote nulo ou negativo não permitido."
            
            risk_pct = (lot_size * 100.0) / (balance / 100.0) if balance > 0 else 0
            max_pos_pct = OMEGA.get("position_size_pct", 10.0)
            
            if risk_pct > max_pos_pct:
                adjusted_lot = (max_pos_pct * balance) / 10000.0
                return True, adjusted_lot, f"Lote reduzido de {lot_size} para {adjusted_lot} (Risk Cap {max_pos_pct}%)"
            
            return True, lot_size, "Aprovado"
        except Exception as e:
            log.error(f"❌ [RiskQuantum] Erro em validate_trade: {e}")
            return False, lot_size, f"Erro interno: {str(e)}"

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
        safety_stop_loss_abs = -4800.00

        if daily_pnl <= safety_stop_loss_abs:
            log.critical(f"🛑 CIRCUIT BREAKER TRIPPED! Daily Loss ${daily_pnl:.2f} atingiu limite FTMO/Safety. Hibernando.")
            return False

        # Max Drawdown de Conta (ex: 10% do start balance histórico)
        # Implementar se necessário o histórico de balance inicial.
        
        return True

    def update_pnl(self, balance: float):
        """Atualiza estado interno do P&L."""
        if self._daily_start_balance > 0:
            self._daily_pnl = balance - self._daily_start_balance

    @catch_and_log(default_return=None)
    def evaluate_wormhole_trigger(self, pos: dict, snapshot) -> Optional[dict]:
        """
        [PHASE Ω-TRANSCENDENCE] Detecta se a posição está colapsando e ativa o Wormhole.
        O Wormhole abre um hedge gravitacional para neutralizar a perda do SL.
        """
        if not pos or not snapshot:
            return None

        # Filtro de símbolo
        symbol = pos.get("symbol", "")
        if symbol != snapshot.symbol:
            return None

        # Dados da posição
        pos_type = pos.get("type_name", pos.get("type", "")) 
        open_price = pos.get("price_open", pos.get("open_price", 0.0))
        sl_price = pos.get("sl", 0.0)
        current_price = snapshot.price
        ticket = pos.get("ticket", 0)

        if sl_price == 0:
            return None # Sem SL, sem Wormhole

        # Distância total até o SL
        total_sl_dist = abs(open_price - sl_price)
        if total_sl_dist <= 0:
            return None

        # Distância atual percorrida em direção ao SL
        # Se BUY, preço caindo = prejuízo
        # Se SELL, preço subindo = prejuízo
        if "BUY" in str(pos_type).upper():
            current_drawdown = open_price - current_price
        else: # SELL
            current_drawdown = current_price - open_price
        
        # Ratio de perigo (0.0 a 1.0+)
        danger_ratio = current_drawdown / total_sl_dist if total_sl_dist > 0 else 0
        
        # Gateway de ativação: 80% do caminho para o SL (Configurável via Omega)
        threshold = OMEGA.get("wormhole_trigger_threshold", 0.80)
        
        if danger_ratio >= threshold:
            # 🌀 WORMHOLE COLLAPSE DETECTED!
            action = "SELL" if "BUY" in str(pos_type).upper() else "BUY"
            
            # TP dinâmico para o micro-hedge (buscando neutralizar 50% do strike do SL)
            point = snapshot.symbol_info.get("point", 0.01)
            tp_points = int((total_sl_dist * 0.45) / point) if point > 0 else 1000
            
            log.critical(f"🌀 [WORMHOLE TRIGGER] Pos #{ticket} {pos_type} em colapso ({danger_ratio:.2%}). Iniciando Gamma Hedge {action}.")
            
            return {
                "action": action,
                "tp_points": tp_points,
                "reason": f"WORMHOLE_RECOVERY: Danger Ratio {danger_ratio:.2%}"
            }
            
        return None
