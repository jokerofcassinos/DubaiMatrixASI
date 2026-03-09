# CAPABILITY INVENTORY (CI)
## PLMA LAYER 3 — DUBAI MATRIX ASI

> "O que a ASI faz não é 'trade'. A ASI extrai Alpha."

### 1. AQUISIÇÃO SENSORIAL E MICROESTRUTURA
- **HFT Socket Tick Streaming**: Capacidade de ingerir dados por Sockets TCP via porta 5555 ligados em um Expert Advisor MT5.
- **Order Flow Delta Calculation**: Acumulação contínua do volume baseando-se agressões sub-tick (Buy/Sell Imbalance).
- **Deep Absorption Detection**: Capta eventos onde Player A enche a mão agredindo enquanto Player B absorve o soco (preço em estado inercial), validando o timing exato para entrar a favor de Player B.
- **Regime Detection**: Identifica se estamos rodando num regime Trending, Choppy, Liquidation Cascade, Squeeze. E baseia a agressão do bot nestes status. (Phase 24: SQUEEZE_BUILDUP, CREEPING_BULL, DRIFTING_BEAR, LIQUIDITY_HUNT, MEAN_REVERTING).
- **V-Pulse Capacitor v3**: Acumulação inercial de ignição HFT para detecção de breakouts de alta convicção.
- **Phase 17 Structural Filtering**: Agentes dedicados a detectar topos e fundos macro (`ChartStructure`) e micro (`CandleAnatomy`).
- **Phase 51: Ignition Sovereignty**: Bypass de vetos em V-Pulse.
- **Hyperbolic Power Clusters**: Detecção de centros de gravidade institucional via Geometria Hiperbólica (Poincaré Ball).
- **Holographic Bulk Inference**: Projeção da profundidade do book (Bulk) a partir do fluxo de ticks (Boundary) via AdS/CFT.

### 2. EXECUÇÃO AVANÇADA (Phase 9 e 26)
- **Margin Pre-flight check**: O executor não "tenta", ele recalcula via order_calc_margin assegurando fundo na corretora antes da batida do Sniper evitando colapso em logs.
- **Dynamic Hydra Execution (Phase 26)**: Slots dinâmicos que multiplicam a agressividade de execução (up to 25 slots progressivos) quando o Meta-Swarm detecta super-confiança em regimes de tendência sólida, destravando a limitação arbitrária de ordens.
- **Sniper Slot Splitter**: A agressão principal é diluída em até N slots paralelos (ex 0.5 lot = 5 posições simultâneas de 0.1) viabilizando saídas parciais por orderflow e juros compostos da Kelly.
- **Smart TP (Flow-based)**: Position Manager monitora fluxo sobre posições ativas; se a ponta vendedora exaurir-se durante um gain antes de abater o Profit Final original, o bot deflagra "SMART TP" retendo o recurso de maneira predatória.
- **Emergency Abort**: `close_all_positions()` — encerramento letal e compulsório de todos os trades via loop acelerado.
- **Non-Ergodic Risk Management**: Substituição do Critério de Kelly clássico por Otimização da Taxa de Crescimento Temporal (Cálculo de Ito) com Bayesian Priors para Cold Start.
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
- [x] **Lorentz Clock (Relativistic Pacing)**: Adaptação do loop de consciência à energia cinética do mercado.
- [x] **Integrated Information (Φ)**: Gate de consciência sistêmica para evitar disparos incoerentes.
- [x] **QCA Grid Mapping**: Detecção de suporte/resistência via autômatos celulares de sub-tick.
- [x] **Lotka-Volterra Predator-Prey**: Modelagem de tensão comprador/vendedor como ecossistema.
- [x] **EVT Black Swan Harvester**: Captura de reversões extremas via Distribuição de Pareto Generalizada.
- [x] **P-Brane Maker Execution (Phase Ω-Singularity)**: Transição automática para Limit Orders em regimes de baixa liquidez/drift, capturando spread.
- [x] **Consciousness Feedback Loop (Phase Ω-Darwin)**: Auditoria periódica de deals reais no MT5 para sincronização do P&L líquido na consciência da ASI.
- [x] **Net-Wealth Mutation Alignment**: Garantia de que a auto-evolução darwiniana opera estritamente sobre Alpha Líquido, expurgando 'Fake Fitness'.
- [x] **Anti-Amnesia Intent Persistence**: Persistência de contexto perceptual (Regime, Sinais, PHI) no momento da entrada via `TradeRegistry`, erradicando a dissociação informativa no fechamento de posições.

*(Atualizado: 2026-03-09. Versão: 14.8.0-omega+signal_integrity)*
