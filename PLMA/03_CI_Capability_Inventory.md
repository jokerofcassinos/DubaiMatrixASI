# CAPABILITY INVENTORY (CI)
## PLMA LAYER 3 — DUBAI MATRIX ASI

> "O que a ASI faz não é 'trade'. A ASI extrai Alpha."

### 1. AQUISIÇÃO SENSORIAL E MICROESTRUTURA
- **HFT Socket Tick Streaming**: Capacidade de ingerir dados por Sockets TCP via porta 5555 ligados em um Expert Advisor MT5.
- **Order Flow Delta Calculation**: Acumulação contínua do volume baseando-se agressões sub-tick (Buy/Sell Imbalance).
- **Deep Absorption Detection**: Capta eventos onde Player A enche a mão agredindo enquanto Player B absorve o soco (preço em estado inercial), validando o timing exato para entrar a favor de Player B.
- **Regime Detection**: Identifica se estamos rodando num regime Trending, Choppy, Liquidation Cascade, Squeeze. E baseia a agressão do bot nestes status. (Phase 24: SQUEEZE_BUILDUP, CREEPING_BULL, DRIFTING_BEAR, LIQUIDITY_HUNT, MEAN_REVERTING eliminando pontos cegos do tipo UNKNOWN).
- **Phase 17 Structural Filtering**: Agentes dedicados a detectar topos e fundos macro (`ChartStructure`) e micro (`CandleAnatomy`) via fractais e body/wick ratios, vetando compras em "highs" e vendas em "lows".

### 2. EXECUÇÃO AVANÇADA (Phase 9 e 26)
- **Margin Pre-flight check**: O executor não "tenta", ele recalcula via order_calc_margin assegurando fundo na corretora antes da batida do Sniper evitando colapso em logs.
- **Dynamic Hydra Execution (Phase 26)**: Slots dinâmicos que multiplicam a agressividade de execução (up to 25 slots progressivos) quando o Meta-Swarm detecta super-confiança em regimes de tendência sólida, destravando a limitação arbitrária de ordens.
- **Sniper Slot Splitter**: A agressão principal é diluída em até N slots paralelos (ex 0.5 lot = 5 posições simultâneas de 0.1) viabilizando saídas parciais por orderflow e juros compostos da Kelly.
- **Smart TP (Flow-based)**: Position Manager monitora fluxo sobre posições ativas; se a ponta vendedora exaurir-se durante um gain antes de abater o Profit Final original, o bot deflagra "SMART TP" retendo o recurso de maneira predatória.
- **Emergency Abort**: `close_all_positions()` — encerramento letal e compulsório de todos os trades via loop acelerado.
- **Dynamic Lot Sizing (Kelly Compound)**: Aloca o sizing progressivo escalando como juros compostos a cada reavaliação quântica do Risco, impulsionado pela Conviction.
- **Circuit Breakers Dinâmicos**: Corta a exposição caso exceda limite de drawdowns.
- **Anti-Metralhadora Protocol**: Bloqueio de 3 camadas contra re-entradas irracionais no mesmo preço (Cooldown, Price Distance, Directional Conflict).
- **Zero-Latency Anti-Slippage**: Veto de fechamento via MQL5 se o lucro do Smart TP for consumido por slippage antes da execução.
- **Global Risk Cap**: Limite inquebrável de 10% de conta sob 20 posições (0.5% max/pos).

### 2B. SIMULAÇÃO QUANTUM MONTE CARLO & PNL PREDICTION (Phase 8 e 25)
- **Trade Simulation (Merton Jump-Diffusion)**: 5000 universos paralelos de trajetórias de preço com saltos estocásticos. 56ms para simulação completa.
- **4096D Hyperspace Engine (Phase 25)**: Motor nativo em C++ que simula a densidade probabilística vetorial em 4096 dimensões para extrair expected_excursion_max, injetando *confidence_boost* massivo no sinal.
- **Java PnL Predictor Daemon (Phase 25)**: Servidor assíncrono Enterprise Java rodando em background recebendo inputs (balance, win_rate, wins/losses) via socket TCP, prevendo caminhos até a meta de 1M através de simulação Kelly-Risk.
- **Path-Dependent SL/TP Analysis**: Cada path verifica hit de stop loss ou take profit tick-a-tick.
- **CVaR/VaR Tail Risk**: Mede risco de cauda nos piores 5% dos cenários.
- **Optimal SL/TP Grid Search**: Busca o par SL/TP ótimo sobre os paths já simulados.
- **Equity Curve Simulator**: Simula equity curves de 200+ trades para estimar drawdown máximo e probabilidade de atingir meta.
- **Stress Test Multi-Cenário**: Flash Crash, Squeeze, Dead Market, Black Swan testados em cada trade.

### 3. COGNITIVE SYNTHESIS
- **Consciousness Heartbeat**: Função multi-thread que roda e recomeça a verificação de toda a matrix `MAIN_LOOP_INTERVAL_MS`.
- **Parallel Swarm Execution**: `ThreadPoolExecutor` rodando os agentes concorrentemente num gap maximo de milissegundos, impedindo estrangulamento de performance sequencial.
- **Quantum State Convergence**: O processamento do `agent_signals` colapsando sob as regras das dimensões múltiplas pelo `QuantumThoughtEngine`.
- **Market Dynamics Physics (Phase 19)**: Leitura de mercado via vetores de velocidade, campos gravitacionais por perfil de volume, e índices de agressividade com divergência de esforço x resultado.

### 4. INTELIGÊNCIA EXTERNA (Zero-Cost Scrapers)
- **Sentiment Score**: Fear & Greed Index + dados CoinGecko consolidados em score [-1, +1]. Atualizado a cada 2 minutos.
- **Network Pressure**: Métricas on-chain (mempool, fees, hashrate) consolidadas em score [-1, +1]. Atualizado a cada 5 minutos.
- **Macro Bias**: Dados multi-asset (ETH, Gold proxy, volumes globais) em score [-1, +1]. Atualizado a cada 3 minutos.
- **Data Quality Tracking**: Cada scraper reporta quantas fontes responderam e qualidade dos dados.

### 5. AUTO-EVOLUÇÃO DARWINIANA
- **Performance Tracking Multi-Dimensional**: Win rate por regime, sessão de mercado e direção. Sharpe, Sortino, Profit Factor, equity curve com persistência JSON.
- **Mutation Engine**: Mutações gaussian (fine-tuning), uniform (exploration) e targeted (directed fix) nos OmegaParams. Mantém melhor genome e reverte mutações ruins.
- **Self Optimizer**: Monitoramento contínuo com alertas automáticos (low win rate, consecutive losses, max drawdown). Orquestra ciclos de mutação a cada 200 ciclos.
- **Automatic Reversion**: Se mutações degradam performance, o sistema auto-reverte para o melhor genome conhecido.

*(Atualizado: 2026-03-04. Versão: 2.2.0-omega+phase19 — Phase 19 Integration)*
