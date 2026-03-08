# CAPABILITY INVENTORY (CI)
## PLMA LAYER 3 — DUBAI MATRIX ASI

> "O que a ASI faz não é 'trade'. A ASI extrai Alpha."

### 1. AQUISIÇÃO SENSORIAL E MICROESTRUTURA
- **HFT Socket Tick Streaming**: Capacidade de ingerir dados por Sockets TCP via porta 5555 ligados em um Expert Advisor MT5.
- **Order Flow Delta Calculation**: Acumulação contínua do volume baseando-se agressões sub-tick (Buy/Sell Imbalance).
- **Deep Absorption Detection**: Capta eventos onde Player A enche a mão agredindo enquanto Player B absorve o soco (preço em estado inercial), validando o timing exato para entrar a favor de Player B.
- **Regime Detection**: Identifica se estamos rodando num regime Trending, Choppy, Liquidation Cascade, Squeeze. E baseia a agressão do bot nestes status. (Phase 24: SQUEEZE_BUILDUP, CREEPING_BULL, DRIFTING_BEAR, LIQUIDITY_HUNT, MEAN_REVERTING eliminando pontos cegos do tipo UNKNOWN).
- **Phase 17 Structural Filtering**: Agentes dedicados a detectar topos e fundos macro (`ChartStructure`) e micro (`CandleAnatomy`) via fractais e body/wick ratios, vetando compras em "highs" e vendas em "lows".
- **Hyperbolic Power Clusters**: Detecção de centros de gravidade institucional via Geometria Hiperbólica (Poincaré Ball).
- **Holographic Bulk Inference**: Projeção da profundidade do book (Bulk) a partir do fluxo de ticks (Boundary) via AdS/CFT.

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
- **Adaptive Kinematic Veto (Phase 30)**: Bloqueia entradas quando a variação em 5 candles excede o limite elástico (Default 1.8 ATR).
- **Freight Train Override (Phase 30)**: Detecta momentum parabólico e desarma vetores de "Smart Money Trap" para não lutar contra a avalanche.
- **Elastic Snapback Veto (Phase 33)**: Sensor de tensão multivariável que asfixia Trend/Momentum no fim do elástico estatístico, evitando bottom-selling.
- **Dead Cat Bounce Protection (Phase 32)**: Filtro de divergência Macro vs Micro que impede compra de repiques em tendências de baixa dominantes.
- **Phase 40 Multi-Threaded Strike**: SniperExecutor capaz de disparar 25 slots simultâneos em <500ms através de `ThreadPoolExecutor`.
- **Phase 41 Omega-Convergence (C++)**: Agregação instantânea de 52 sinais neurais.
- **Phase Ω-One: Spiking Neural Networks**: Cognição assíncrona baseada em eventos (ticks) via neurônios LIF nativos.
- **Phase Ω-One: Mean Field Games (MFG)**: Modelagem de densidade de traders e geodésicas ótimas de saída via HJB/FP em C++.
- **Phase Ω-One: Feynman Path Propagator**: Previsão de interferência quântica de preço baseada em trajetórias integrais.
- **Phase Ω-One: Lucid Dreaming (Java Shadow)**: Simulação paralela massiva de orderflow para evolução rápida de parâmetros.
- **Phase Ω-One: Lyapunov Horizon**: Detecção de caos determinístico e limites de previsibilidade temporal.
- **Maximum Margin Extraction (MME - Phase 37)**: Auto-scaling de lotes para máxima utilização da margem disponível sem rejeição de ordens.
- **Equity Curve Simulator**: Simula equity curves de 200+ trades para estimar drawdown máximo e probabilidade de atingir meta.
- **Stress Test Multi-Cenário**: Flash Crash, Squeeze, Dead Market, Black Swan testados em cada trade.
- **Resultado**: O bot agora mantém posições em pullbacks saudáveis, permitindo a captura de breakouts macro no BTCUSD. ### FASE 36: ERA DA CALIBRAÇÃO DARWINIANA (Paradox of Profit Fix) - **Contexto:** Identificação do 'Paradoxo do Lucro' (Vitórias brutas ocultando perdas líquidas por comissões de ~$7/lote) e 'Amnésia de Histórico' no Brain. - **Evolução:** - **Consciousness Feedback Loop**: Implementação de auditoria periódica (60s) via `history_deals_get` que sincroniza o Brain com o terminal real. - **Speed Optimization**: Portabilidade de `send_limit_order` para Socket Bridge, eliminando o lag de 780ms do Python nativo. - **Commission-Aware Fitness**: Injeção mandatória de deduções de taxas no `PerformanceTracker`, realinhando a auto-evolução darwiniana para a riqueza líquida. - **Resultado**: O sistema agora evolui focado no **Alpha Líquido**, matando mutações 'Fake Fitness' e otimizando o preenchimento de ordens via HFT Socket. ### FASE 48: ERA DA SIMETRIA E IGNIÇÃO (V-Pulse & God-Mode) - **Contexto:** Detecção de inversão de sinal em V-reversals e lag de percepção em breakouts. - **Evolução:** - **Supernova Capacitor v2**: Rastreio sub-segundo de densidade de ticks bruta. - **Ignition Sovereignty**: O motor quântico agora silencia o ruído contrário durante o V-Pulse. - **God-Mode Reversal**: TrinityCore calibrado para absorver reversões violentas via decoerência forçada. - **Resultado**: A ASI atinge um novo patamar de acuidade cinemática, blindando o capital contra armadilhas de "falsa exaustão".

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

- [x] **Lorentz Clock (Relativistic Pacing)**: Adaptação do loop de consciência à energia cinética do mercado.
- [x] **Integrated Information (Φ)**: Gate de consciência sistêmica para evitar disparos incoerentes.
- [x] **QCA Grid Mapping**: Detecção de suporte/resistência via autômatos celulares de sub-tick.
- [x] **Lotka-Volterra Predator-Prey**: Modelagem de tensão comprador/vendedor como ecossistema.
- [x] **EVT Black Swan Harvester**: Captura de reversões extremas via Distribuição de Pareto Generalizada.
- [x] **P-Brane Maker Execution (Phase Ω-Singularity)**: Transição automática para Limit Orders em regimes de baixa liquidez/drift, capturando spread.
- [x] **Consciousness Feedback Loop (Phase Ω-Darwin)**: Auditoria periódica de deals reais no MT5 para sincronização do P&L líquido na consciência da ASI.
- [x] **Net-Wealth Mutation Alignment**: Garantia de que a auto-evolução darwiniana opera estritamente sobre Alpha Líquido, expurgando 'Fake Fitness'.
- [x] **Anti-Amnesia Intent Persistence**: Persistência de contexto perceptual (Regime, Sinais, PHI) no momento da entrada via `TradeRegistry`, erradicando a dissociação informativa no fechamento de posições.

*(Atualizado: 2026-03-08. Versão: 13.0.0-omega+integrity)*
