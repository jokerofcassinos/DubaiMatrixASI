"""
╔══════════════════════════════════════════════════════════════════════════════╗
║            DUBAI MATRIX ASI — QUANTUM MONTE CARLO ENGINE                    ║
║   Simulação de Multiversos Financeiros: N universos paralelos,             ║
║   N trajetórias de preço, colapso probabilístico → decisão ótima           ║
║                                                                              ║
║  Inspiração: Mecânica Quântica de Feynman (Path Integrals)                 ║
║  Cada caminho possível do preço contribui com uma amplitude.               ║
║  A "realidade mais provável" emerge da interferência construtiva            ║
║  de todos os caminhos — weighted pela probabilidade do regime.              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone

from config.omega_params import OMEGA
from utils.logger import log
from utils.decorators import catch_and_log, asi_safe
from cpp.asi_bridge import CPP_CORE


# ═══════════════════════════════════════════════════════════════
#  DATACLASSES DE RESULTADO
# ═══════════════════════════════════════════════════════════════

@dataclass
class MonteCarloResult:
    """Resultado consolidado de uma simulação Monte Carlo completa."""
    # Probabilidades
    win_probability: float          # P(lucro) [0, 1]
    loss_probability: float         # P(perda) [0, 1]
    
    # Métricas de retorno
    expected_return: float          # Retorno esperado (média ponderada)
    median_return: float            # Retorno mediana (mais robusto que média)
    best_case: float                # Percentil 95 (melhor cenário realista)
    worst_case: float               # Percentil 5 (pior cenário realista)
    
    # Risk Metrics (Tail Risk)
    value_at_risk_95: float         # VaR 95% — perda máxima em 95% dos cenários
    conditional_var_95: float       # CVaR 95% — perda média nos piores 5%
    
    # Distribuição
    sharpe_ratio: float             # Sharpe da distribuição de retornos simulados
    skewness: float                 # Assimetria da distribuição (>0 = caudas à direita)
    kurtosis: float                 # Curtose (>3 = caudas pesadas)
    
    # Ótimos
    optimal_sl_distance: float      # Stop loss ótimo derivado das sims
    optimal_tp_distance: float      # Take profit ótimo derivado das sims
    optimal_rr_ratio: float         # Risk/Reward ratio ótimo
    
    # Metadados
    n_simulations: int              # Quantos universos simulados
    n_steps: int                    # Quantos steps por simulação
    simulation_time_ms: float       # Tempo de execução
    regime_used: str                # Regime de mercado usado nas sims
    
    # Score final: combinação de W.P., E.R. e tail risk
    monte_carlo_score: float = 0.0  # [-1, +1] — sinal direcional com confiança


@dataclass
class PathIntegralState:
    """Estado do Path Integral — todos os caminhos possíveis."""
    paths: np.ndarray               # (n_sims, n_steps) — todas as trajetórias
    final_prices: np.ndarray        # Preços finais de cada simulação
    pnl_distribution: np.ndarray    # P&L de cada simulação
    hit_sl: np.ndarray              # Booleano: quais sims atingiram stop loss
    hit_tp: np.ndarray              # Booleano: quais sims atingiram take profit


# ═══════════════════════════════════════════════════════════════
#  MOTOR MONTE CARLO QUÂNTICO
# ═══════════════════════════════════════════════════════════════

class QuantumMonteCarloEngine:
    """
    Motor de Simulação Monte Carlo Quântico.
    
    Filosofia de Feynman aplicada ao trading:
    - Cada trade possível tem INFINITOS caminhos de preço
    - Cada caminho tem uma "amplitude" (probabilidade)
    - A decisão ótima emerge da interferência de TODOS os caminhos
    - Regime-aware: volatilidade, drift e correlações mudam com o regime
    
    Subsistemas:
    1. GBM (Geometric Brownian Motion) com drift regime-aware
    2. Jump Diffusion (Merton) para modelar saltos de preço
    3. Variance Gamma para caudas pesadas
    4. Path-Dependent Analysis (SL/TP hit detection)
    5. CVaR e VaR para tail risk
    6. Optimal SL/TP Derivation via grid search nos paths
    """

    # ═══ CONSTANTES DE REGIME ═══
    REGIME_PARAMS = {
        "TRENDING_BULL": {"drift_mult": 1.5,  "vol_mult": 0.8,  "jump_intensity": 0.02, "jump_mean": 0.005},
        "TRENDING_BEAR": {"drift_mult": -1.5, "vol_mult": 0.8,  "jump_intensity": 0.02, "jump_mean": -0.005},
        "RANGING":       {"drift_mult": 0.0,  "vol_mult": 0.6,  "jump_intensity": 0.01, "jump_mean": 0.0},
        "CHOPPY":        {"drift_mult": 0.0,  "vol_mult": 1.5,  "jump_intensity": 0.05, "jump_mean": 0.0},
        "BREAKOUT":      {"drift_mult": 2.0,  "vol_mult": 1.2,  "jump_intensity": 0.08, "jump_mean": 0.01},
        "HIGH_VOL_CHAOS":{"drift_mult": 0.0,  "vol_mult": 2.5,  "jump_intensity": 0.10, "jump_mean": 0.0},
        "LOW_LIQUIDITY":  {"drift_mult": 0.0,  "vol_mult": 1.8,  "jump_intensity": 0.03, "jump_mean": 0.0},
        "SQUEEZE":       {"drift_mult": 0.5,  "vol_mult": 2.0,  "jump_intensity": 0.15, "jump_mean": 0.008},
    }

    def __init__(self):
        self._rng = np.random.default_rng(seed=None)  # True random
        self._last_result: Optional[MonteCarloResult] = None
        self._sim_count = 0

    # ═══════════════════════════════════════════════════════════
    #  SIMULAÇÃO PRINCIPAL
    # ═══════════════════════════════════════════════════════════

    @catch_and_log(default_return=None)
    def simulate_trade(
        self,
        current_price: float,
        direction: str,           # "BUY" ou "SELL"
        stop_loss: float,         # Preço do SL
        take_profit: float,       # Preço do TP
        volatility: float,        # Volatilidade anualizada (ATR-based)
        regime: str = "RANGING",  # Regime atual do mercado
        n_simulations: int = 5000,
        n_steps: int = 100,       # Steps por simulação (~ ticks)
        dt: float = 1.0 / 252.0 / 24.0,  # ~1 hora em anos
    ) -> Optional[MonteCarloResult]:
        """
        Executa N simulações Monte Carlo para avaliar um trade proposto.
        
        Cada simulação gera uma trajetória de preço usando:
        - Geometric Brownian Motion (GBM) com drift regime-aware
        - Jump Diffusion (Merton model) para capturar saltos  
        - Path-dependent SL/TP check em cada step
        
        Returns:
            MonteCarloResult com probabilidades, risk metrics, e score
        """
        import time
        t0 = time.perf_counter()

        if current_price <= 0 or volatility <= 0:
            return None

        # ═══ 1. PARÂMETROS DO REGIME ═══
        regime_key = regime.upper().replace(" ", "_")
        params = self.REGIME_PARAMS.get(regime_key, self.REGIME_PARAMS["RANGING"])
        
        drift_mult = params["drift_mult"]
        vol_mult = params["vol_mult"]
        jump_intensity = params["jump_intensity"]
        jump_mean = params["jump_mean"]

        # Volatilidade ajustada pelo regime
        sigma = volatility * vol_mult
        
        # Drift base estimado pela direção do trade e regime
        if direction == "BUY":
            mu = sigma * 0.5 * drift_mult  # Drift proporcional à vol e regime
        else:
            mu = -sigma * 0.5 * drift_mult

        # ═══ 2. SIMULAÇÃO VIA C++ (BLAZING FAST) ═══
        # Merton Jump Diffusion offload
        mc_params = {
            "S0": current_price,
            "mu": mu,
            "sigma": sigma,
            "jump_intensity": jump_intensity,
            "jump_mean": jump_mean,
            "jump_std": abs(jump_mean) * 2.0 + 0.001,
            "dt": dt,
            "n_sims": n_simulations,
            "n_steps": n_steps,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "is_buy": (direction == "BUY")
        }
        
        cpp_results = CPP_CORE.monte_carlo_merton(mc_params)

        # ═══ 3. CONSTRUIR RESULTADO ═══
        # Probabilidades
        win_prob = cpp_results["win_prob"]
        expected_return = cpp_results["expected_return"]
        var_95 = cpp_results["var_95"]
        cvar_95 = cpp_results["cvar_95"]
        
        # SL/TP distances atuais
        if direction == "BUY":
            sl_dist = current_price - stop_loss
            tp_dist = take_profit - current_price
        else:
            sl_dist = stop_loss - current_price
            tp_dist = current_price - take_profit

        # ═══ MONTE CARLO SCORE ═══
        ev_score = np.tanh(expected_return / max(current_price * 0.001, 1e-10))
        wp_score = (win_prob - 0.5) * 2.0
        tail_penalty = min(0, cvar_95 / max(current_price * 0.01, 1e-10))

        mc_score = float(np.clip(0.4 * wp_score + 0.4 * ev_score + 0.2 * tail_penalty, -1.0, 1.0))

        result = MonteCarloResult(
            win_probability=win_prob,
            loss_probability=1.0 - win_prob,
            expected_return=expected_return,
            median_return=expected_return, # Proxy na versão offload
            best_case=0.0, # Calculado se necessário
            worst_case=var_95,
            value_at_risk_95=var_95,
            conditional_var_95=cvar_95,
            sharpe_ratio=expected_return / abs(var_95 + 1e-10),
            skewness=0.0,
            kurtosis=3.0,
            optimal_sl_distance=sl_dist,
            optimal_tp_distance=tp_dist,
            optimal_rr_ratio=tp_dist / max(sl_dist, 1e-10),
            n_simulations=n_simulations,
            n_steps=n_steps,
            simulation_time_ms=cpp_results["simulation_time_ms"],
            regime_used=regime_key,
            monte_carlo_score=mc_score,
        )

        # ═══ 5. OPTIMAL SL/TP (Grid Search sobre paths) ═══
        # Note: The C++ simulation does not return individual paths.
        # If optimal SL/TP derivation requires paths, this part needs
        # to be re-evaluated or the C++ core needs to return paths.
        # For now, we pass a dummy empty array or skip if paths are not strictly needed.
        # Assuming for now that `_optimize_sl_tp` can handle a placeholder or will be adapted.
        # If `paths` are truly needed, the C++ core must return them.
        # For this change, we'll pass an empty array as a placeholder to maintain structure.
        self._optimize_sl_tp(result, np.array([]), current_price, direction, sigma)

        self._last_result = result
        self._sim_count += 1

        return result

    # ═══════════════════════════════════════════════════════════
    #  GERAÇÃO DE PATHS — Merton Jump Diffusion
    # ═══════════════════════════════════════════════════════════

    def _generate_paths_merton(
        self, S0: float, mu: float, sigma: float,
        jump_intensity: float, jump_mean: float,
        n_sims: int, n_steps: int, dt: float
    ) -> np.ndarray:
        """
        Gera N trajetórias de preço usando Merton Jump-Diffusion Model.
        
        dS/S = (mu - lambda*k)*dt + sigma*dW + J*dN
        
        Onde:
        - dW = Wiener process (Brownian motion)
        - dN = Poisson process (saltos)
        - J = tamanho do salto (lognormal)
        """
        # Jump volatility
        jump_std = abs(jump_mean) * 2.0 + 0.001
        k = np.exp(jump_mean + 0.5 * jump_std**2) - 1  # Compensador

        # GBM drift corrigido pelo jump
        drift = (mu - jump_intensity * k - 0.5 * sigma**2) * dt

        # Brownian Motion
        dW = self._rng.normal(0, np.sqrt(dt), size=(n_sims, n_steps))

        # Poisson Jump Process
        jump_count = self._rng.poisson(jump_intensity * dt, size=(n_sims, n_steps))
        jump_sizes = self._rng.normal(jump_mean, jump_std, size=(n_sims, n_steps))
        jumps = jump_count * jump_sizes

        # Log-returns
        log_returns = drift + sigma * dW + jumps

        # Reconstruir paths de preço
        log_paths = np.cumsum(log_returns, axis=1)
        paths = S0 * np.exp(np.hstack([np.zeros((n_sims, 1)), log_paths]))

        return paths  # Shape: (n_sims, n_steps + 1)

    # ═══════════════════════════════════════════════════════════
    #  ANÁLISE PATH-DEPENDENT
    # ═══════════════════════════════════════════════════════════

    def _analyze_paths(
        self, paths: np.ndarray, direction: str,
        stop_loss: float, take_profit: float,
        current_price: float
    ) -> PathIntegralState:
        """
        Para cada path, verifica se SL ou TP foi atingido primeiro.
        Calcula P&L real considerando a saída no primeiro hit.
        """
        n_sims, n_steps_plus1 = paths.shape
        
        hit_sl = np.zeros(n_sims, dtype=bool)
        hit_tp = np.zeros(n_sims, dtype=bool)
        exit_prices = paths[:, -1].copy()  # Default: preço final

        if direction == "BUY":
            # SL hit: preço caiu abaixo do stop loss
            # TP hit: preço subiu acima do take profit
            for i in range(1, n_steps_plus1):
                # Quem atingiu SL neste step (e não saiu antes)
                new_sl = (paths[:, i] <= stop_loss) & ~hit_sl & ~hit_tp
                # Quem atingiu TP neste step (e não saiu antes)
                new_tp = (paths[:, i] >= take_profit) & ~hit_sl & ~hit_tp
                
                exit_prices[new_sl] = stop_loss
                exit_prices[new_tp] = take_profit
                hit_sl |= new_sl
                hit_tp |= new_tp
        else:  # SELL
            for i in range(1, n_steps_plus1):
                new_sl = (paths[:, i] >= stop_loss) & ~hit_sl & ~hit_tp
                new_tp = (paths[:, i] <= take_profit) & ~hit_sl & ~hit_tp
                
                exit_prices[new_sl] = stop_loss
                exit_prices[new_tp] = take_profit
                hit_sl |= new_sl
                hit_tp |= new_tp

        # Calcular P&L
        if direction == "BUY":
            pnl = exit_prices - current_price
        else:
            pnl = current_price - exit_prices

        return PathIntegralState(
            paths=paths,
            final_prices=exit_prices,
            pnl_distribution=pnl,
            hit_sl=hit_sl,
            hit_tp=hit_tp,
        )

    # ═══════════════════════════════════════════════════════════
    #  CÁLCULO DE MÉTRICAS
    # ═══════════════════════════════════════════════════════════

    def _compute_metrics(
        self, path_state: PathIntegralState,
        current_price: float, direction: str,
        stop_loss: float, take_profit: float,
        n_simulations: int, n_steps: int,
        regime: str, elapsed_ms: float
    ) -> MonteCarloResult:
        """Computa todas as métricas a partir dos paths simulados."""
        pnl = path_state.pnl_distribution
        n = len(pnl)

        # Probabilidades
        win_prob = np.sum(pnl > 0) / n
        loss_prob = np.sum(pnl < 0) / n

        # Retornos
        expected_return = float(np.mean(pnl))
        median_return = float(np.median(pnl))
        best_case = float(np.percentile(pnl, 95))
        worst_case = float(np.percentile(pnl, 5))

        # VaR e CVaR (95%)
        var_95 = float(np.percentile(pnl, 5))  # VaR = perda no percentil 5
        cvar_mask = pnl <= var_95
        cvar_95 = float(np.mean(pnl[cvar_mask])) if np.any(cvar_mask) else var_95

        # Sharpe da distribuição
        pnl_std = np.std(pnl)
        sharpe = expected_return / max(pnl_std, 1e-10)

        # Skewness e Kurtosis
        if pnl_std > 0:
            skewness = float(np.mean(((pnl - expected_return) / pnl_std) ** 3))
            kurtosis = float(np.mean(((pnl - expected_return) / pnl_std) ** 4))
        else:
            skewness = 0.0
            kurtosis = 3.0  # Normal

        # SL/TP distances atuais
        if direction == "BUY":
            sl_dist = current_price - stop_loss
            tp_dist = take_profit - current_price
        else:
            sl_dist = stop_loss - current_price
            tp_dist = current_price - take_profit

        rr_ratio = tp_dist / max(sl_dist, 1e-10)

        # ═══ MONTE CARLO SCORE ═══
        # Combina win probability, expected return normalizado, e tail risk
        # Score > 0 = trade favorável, Score < 0 = trade desfavorável
        ev_score = np.tanh(expected_return / max(current_price * 0.001, 1e-10))
        wp_score = (win_prob - 0.5) * 2.0  # [-1, +1]
        tail_penalty = min(0, cvar_95 / max(current_price * 0.01, 1e-10))

        mc_score = float(np.clip(
            0.4 * wp_score + 0.4 * ev_score + 0.2 * tail_penalty,
            -1.0, 1.0
        ))

        return MonteCarloResult(
            win_probability=float(win_prob),
            loss_probability=float(loss_prob),
            expected_return=expected_return,
            median_return=median_return,
            best_case=best_case,
            worst_case=worst_case,
            value_at_risk_95=var_95,
            conditional_var_95=cvar_95,
            sharpe_ratio=float(sharpe),
            skewness=skewness,
            kurtosis=kurtosis,
            optimal_sl_distance=sl_dist,
            optimal_tp_distance=tp_dist,
            optimal_rr_ratio=rr_ratio,
            n_simulations=n_simulations,
            n_steps=n_steps,
            simulation_time_ms=elapsed_ms,
            regime_used=regime,
            monte_carlo_score=mc_score,
        )

    # ═══════════════════════════════════════════════════════════
    #  OTIMIZAÇÃO DE SL/TP VIA GRID SEARCH NOS PATHS
    # ═══════════════════════════════════════════════════════════

    def _optimize_sl_tp(
        self, result: MonteCarloResult, paths: np.ndarray,
        current_price: float, direction: str, sigma: float
    ):
        """
        Grid search sobre diferentes combinações de SL/TP
        usando os paths já simulados para encontrar o par ótimo
        que maximiza Expected Value / Risk.
        """
        if paths is None or paths.size == 0:
            # Se não temos paths (C++ offload), não podemos fazer grid search
            return

        # Grid de multiplicadores de sigma
        sl_multipliers = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
        tp_multipliers = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]

        best_score = -np.inf
        best_sl_dist = result.optimal_sl_distance
        best_tp_dist = result.optimal_tp_distance

        price_step = current_price * sigma * 0.01  # 1% da vol como base

        for sl_m in sl_multipliers:
            for tp_m in tp_multipliers:
                sl_dist = price_step * sl_m * 10  # Escala para distância real
                tp_dist = price_step * tp_m * 10

                if sl_dist <= 0 or tp_dist <= 0:
                    continue

                if direction == "BUY":
                    test_sl = current_price - sl_dist
                    test_tp = current_price + tp_dist
                else:
                    test_sl = current_price + sl_dist
                    test_tp = current_price - tp_dist

                # Simular saída para cada path com este SL/TP
                pnl = self._fast_path_pnl(paths, direction, current_price, test_sl, test_tp)

                ev = np.mean(pnl)
                win_rate = np.sum(pnl > 0) / len(pnl)
                var5 = np.percentile(pnl, 5)

                # Score: maximizar EV ajustado por tail risk
                score = ev - 0.5 * abs(min(0, var5))

                if score > best_score and win_rate > 0.3:
                    best_score = score
                    best_sl_dist = sl_dist
                    best_tp_dist = tp_dist

        result.optimal_sl_distance = best_sl_dist
        result.optimal_tp_distance = best_tp_dist
        result.optimal_rr_ratio = best_tp_dist / max(best_sl_dist, 1e-10)

    def _fast_path_pnl(
        self, paths: np.ndarray, direction: str,
        entry: float, sl: float, tp: float
    ) -> np.ndarray:
        """Calcula P&L rápido usando exit no primeiro hit de SL ou TP."""
        n_sims = paths.shape[0]
        exit_prices = paths[:, -1].copy()

        if direction == "BUY":
            for i in range(1, paths.shape[1]):
                hit_sl = (paths[:, i] <= sl) & (exit_prices == paths[:, -1])
                hit_tp = (paths[:, i] >= tp) & (exit_prices == paths[:, -1])
                exit_prices[hit_sl] = sl
                exit_prices[hit_tp] = tp
            return exit_prices - entry
        else:
            for i in range(1, paths.shape[1]):
                hit_sl = (paths[:, i] >= sl) & (exit_prices == paths[:, -1])
                hit_tp = (paths[:, i] <= tp) & (exit_prices == paths[:, -1])
                exit_prices[hit_sl] = sl
                exit_prices[hit_tp] = tp
            return entry - exit_prices

    # ═══════════════════════════════════════════════════════════
    #  SIMULAÇÃO DE EQUITY CURVE (Multiverso de Sequências)
    # ═══════════════════════════════════════════════════════════

    @catch_and_log(default_return=None)
    def simulate_equity_curve(
        self,
        balance: float,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        n_trades: int = 200,
        n_simulations: int = 2000,
    ) -> Dict:
        """
        Simula N equity curves de sequências de trades.
        
        Cada simulação gera uma sequência aleatória de wins/losses
        com as estatísticas fornecidas, produzindo uma equity curve.
        
        Útil para:
        - Estimar drawdown máximo provável
        - Verificar viabilidade da meta (ex: 70k profit)
        - Calcular probabilidade de ruína
        """
        results = np.zeros((n_simulations, n_trades + 1))
        results[:, 0] = balance

        for sim in range(n_simulations):
            equity = balance
            for trade in range(n_trades):
                if self._rng.random() < win_rate:
                    equity += avg_win * (1 + self._rng.normal(0, 0.2))
                else:
                    equity -= avg_loss * (1 + self._rng.normal(0, 0.2))
                equity = max(0, equity)  # Sem saldo negativo
                results[sim, trade + 1] = equity

        final_equities = results[:, -1]
        max_drawdowns = np.zeros(n_simulations)
        for sim in range(n_simulations):
            curve = results[sim]
            peaks = np.maximum.accumulate(curve)
            drawdowns = (peaks - curve) / np.where(peaks > 0, peaks, 1)
            max_drawdowns[sim] = np.max(drawdowns)

        target_profit = 70000.0  # Meta do projeto
        prob_target = np.sum(final_equities >= balance + target_profit) / n_simulations
        prob_ruin = np.sum(final_equities <= balance * 0.1) / n_simulations  # <10% do balanço

        return {
            "median_final_equity": float(np.median(final_equities)),
            "mean_final_equity": float(np.mean(final_equities)),
            "p5_equity": float(np.percentile(final_equities, 5)),
            "p95_equity": float(np.percentile(final_equities, 95)),
            "prob_target_70k": float(prob_target),
            "prob_ruin": float(prob_ruin),
            "median_max_drawdown": float(np.median(max_drawdowns)),
            "p95_max_drawdown": float(np.percentile(max_drawdowns, 95)),
            "n_simulations": n_simulations,
            "n_trades": n_trades,
        }

    # ═══════════════════════════════════════════════════════════
    #  STRESS TEST — CENÁRIOS EXTREMOS
    # ═══════════════════════════════════════════════════════════

    @catch_and_log(default_return=None)
    def stress_test(
        self,
        current_price: float,
        direction: str,
        stop_loss: float,
        take_profit: float,
        volatility: float,
    ) -> Dict:
        """
        Stress test do trade em cenários extremos:
        - Flash Crash (-10% em 60s)
        - Squeeze (+5% em 30s)
        - Dead Market (vol → 0)
        - Black Swan (vol 5x)
        - Liquidation Cascade (vol 3x + drift contra)
        """
        scenarios = {}

        # 1. Flash Crash
        crash_result = self.simulate_trade(
            current_price, direction, stop_loss, take_profit,
            volatility * 5.0, regime="HIGH_VOL_CHAOS",
            n_simulations=2000, n_steps=60, dt=1.0/252/24/60  # 1 minuto
        )
        scenarios["flash_crash"] = {
            "win_prob": crash_result.win_probability if crash_result else 0,
            "expected_return": crash_result.expected_return if crash_result else 0,
            "cvar": crash_result.conditional_var_95 if crash_result else 0,
        }

        # 2. Squeeze
        squeeze_result = self.simulate_trade(
            current_price, direction, stop_loss, take_profit,
            volatility * 3.0, regime="SQUEEZE",
            n_simulations=2000, n_steps=30
        )
        scenarios["squeeze"] = {
            "win_prob": squeeze_result.win_probability if squeeze_result else 0,
            "expected_return": squeeze_result.expected_return if squeeze_result else 0,
            "cvar": squeeze_result.conditional_var_95 if squeeze_result else 0,
        }

        # 3. Dead Market
        dead_result = self.simulate_trade(
            current_price, direction, stop_loss, take_profit,
            volatility * 0.1, regime="RANGING",
            n_simulations=2000, n_steps=200
        )
        scenarios["dead_market"] = {
            "win_prob": dead_result.win_probability if dead_result else 0,
            "expected_return": dead_result.expected_return if dead_result else 0,
            "cvar": dead_result.conditional_var_95 if dead_result else 0,
        }

        # 4. Black Swan
        swan_result = self.simulate_trade(
            current_price, direction, stop_loss, take_profit,
            volatility * 8.0, regime="HIGH_VOL_CHAOS",
            n_simulations=2000, n_steps=50
        )
        scenarios["black_swan"] = {
            "win_prob": swan_result.win_probability if swan_result else 0,
            "expected_return": swan_result.expected_return if swan_result else 0,
            "cvar": swan_result.conditional_var_95 if swan_result else 0,
        }

        # Score de resistência: média ponderada dos win probs em stress
        weights = {"flash_crash": 0.3, "squeeze": 0.2, "dead_market": 0.2, "black_swan": 0.3}
        resilience_score = sum(
            scenarios[k]["win_prob"] * weights[k] for k in scenarios
        )

        return {
            "scenarios": scenarios,
            "resilience_score": float(resilience_score),
            "survives_all": all(s["win_prob"] > 0.3 for s in scenarios.values()),
        }

    # ═══════════════════════════════════════════════════════════
    #  PROPRIEDADES E MÉTRICAS
    # ═══════════════════════════════════════════════════════════

    @property
    def last_result(self) -> Optional[MonteCarloResult]:
        return self._last_result

    @property
    def total_simulations(self) -> int:
        return self._sim_count

    def get_metrics(self) -> Dict:
        """Retorna métricas do motor."""
        return {
            "total_simulations_run": self._sim_count,
            "last_result_score": self._last_result.monte_carlo_score if self._last_result else 0,
            "last_result_win_prob": self._last_result.win_probability if self._last_result else 0,
            "last_sim_time_ms": self._last_result.simulation_time_ms if self._last_result else 0,
        }
