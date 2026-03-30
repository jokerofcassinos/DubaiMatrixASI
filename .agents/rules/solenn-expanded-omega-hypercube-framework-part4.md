---
trigger: always_on
---

§3 — FRAMEWORK OMEGA HYPERCUBE EXPANDIDO (50 CAMADAS Ω) part 4
Ω-10 — CONSCIÊNCIA DE ECOSSISTEMA (300+ VARIÁVEIS)

Modelo completo do ecossistema financeiro como organismo vivo com 300+ variáveis monitoradas continuamente, organizadas em 15 categorias:

Categoria 1 — Microestrutura (40+ vars): spread (bid-ask, effective, realized, quoted), depth (por nível, por lado, total, ratio), imbalance (por nível, agregado, rate of change), trade flow (volume, count, avg size, direction, toxicity/VPIN), order flow (submissions, cancellations, modifications, cancel-to-trade ratio), queue position dynamics, market maker inventory proxy, latência de API (p50/p95/p99).

Categoria 2 — Idiossincrasias de Exchange (20+ vars): matching engine latency, fee tiers (maker/taker, volume-based), order type support, rate limits, historical uptime, maintenance windows, user base composition (retail/institutional/bot), geographic distribution of users, regulatory jurisdiction.

Categoria 3 — Liquidez (25+ vars): liquidez total e por nível, liquidez real vs fantasma (estimada), liquidez prevista em 30s/1m/5m, liquidez disponível para absorção sem market impact de 1bps/5bps/10bps/25bps, resilience (velocidade de recuperação pós-trade grande), fragmentation (distribuição entre exchanges).

Categoria 4 — Funding & Carry (15+ vars): funding rate atual e previsto (próximas 3 janelas), funding rate por exchange, cross-exchange funding spread, funding velocity (taxa de mudança), cumulative funding, funding premium/discount vs historical distribution, estimated annualized carry.

Categoria 5 — Open Interest & Posicionamento (20+ vars): OI total, OI por exchange, OI por tipo (longs/shorts ratio), OI rate of change, OI concentration (Herfindahl index), estimated leveraged OI, delta-neutral OI vs directional OI, max pain (options), gamma exposure by strike, put-call ratio, skew (25-delta risk reversal), term structure of vol implícita.

Categoria 6 — Liquidation Intelligence (15+ vars): liquidation levels mapeados (long liquidation clusters, short liquidation clusters), estimated distance to nearest cluster, estimated dollar value at each cluster, historical liquidation cascade patterns, liquidation velocity (during cascade), liquidation-induced price impact model, cascading potential (how much OI is between current price and liquidation clusters).

Categoria 7 — Basis & Cross-Market (15+ vars): basis spot-perpetual, basis spot-quarterly, cross-exchange basis, basis term structure, basis velocity, basis mean-reversion speed (Ornstein-Uhlenbeck θ), basis vs historical percentile, funding-basis relationship, implied convenience yield.

Categoria 8 — Correlações Dinâmicas (20+ vars): correlação instantânea vs 1h/4h/24h/7d/30d para top 10 pares, taxa de mudança de correlação, correlation regime (stable/transitioning/broken), conditional correlation (correlation in up markets vs down markets), tail dependence coefficient (Clayton/Gumbel copula), DCC-GARCH estimates, correlation surprise (observed vs predicted).

Categoria 9 — On-Chain Intelligence (25+ vars): exchange inflows/outflows (BTC, ETH, stablecoins), whale movements (txns > $1M), miner outflows, stablecoin supply (USDT/USDC/DAI/BUSD), stablecoin velocity (on-chain transfer volume / supply), MVRV ratio, SOPR, NVT signal, realized cap, thermocap multiple, HODL waves, entity-adjusted UTXO age bands, exchange reserve trend, hash rate, difficulty adjustment, mempool size/fee rate.

Categoria 10 — Macro Intelligence (30+ vars): calendário macro completo (FOMC, CPI, NFP, PPI, PMI, GDP, retail sales, jobless claims, ISM, housing, consumer confidence, PCE deflator, JOLTS), DXY + rate of change, US yields (2Y, 5Y, 10Y, 30Y) + curve shape + rate of change, real yields (TIPS), credit spreads (IG, HY, TED, OAS), VIX + VVIX + term structure + skew, MOVE index, oil (WTI/Brent), gold, copper/gold ratio, financial conditions index (Goldman/Chicago Fed), bank reserves, RRP, TGA balance, global M2 aggregate.

Categoria 11 — Sentiment Intelligence (20+ vars): Fear & Greed Index (crypto + traditional), social media volume spike detection, social sentiment polarity (NLP-based), news flow intensity, funding sentiment index (funding × OI × leverage), long/short ratio (exchanges que publicam), professional vs retail sentiment divergence, contrarian signal strength.

Categoria 12 — Temporal Patterns (15+ vars): hora do dia effects (volatility profile, spread profile, volume profile), day of week effects, month effects, options expiry effects (weekly/monthly/quarterly), FOMC day patterns, first/last trading day effects, holiday effects, daylight saving transition effects, quarter-end rebalancing patterns.

Categoria 13 — Volatilidade Multi-Dimensional (20+ vars): vol realizada (1min, 5min, 1h, 4h, 1d, 1w), vol implícita (ATM, 25-delta put, 25-delta call), vol of vol (VVIX-equivalent), vol term structure (slope, curvature), vol cone (current vs historical percentile by horizon), vol regime (low/normal/high/extreme), Parkinson/Garman-Klass/Rogers-Satchell/Yang-Zhang estimators, vol smile parameters (SABR α,ρ,ν), vol surface dynamics (sticky strike vs sticky delta), vol compression index (proximity to historical minimum vol → explosion imminent).

Categoria 14 — Network Science (15+ vars): correlation network density, average path length, clustering coefficient, largest eigenvalue, participation ratio, network entropy, community structure (Louvain), centrality measures (betweenness, eigenvector, PageRank) for each asset, network resilience (percolation threshold proximity).

Categoria 15 — Meta-Variables (20+ vars): model confidence (ensemble agreement), prediction interval width, regime identification confidence, data quality score (completeness, freshness, consistency), system health (latency, CPU, memory, error rate), edge decay rate (Sharpe rolling 100 trades), information ratio, hit rate rolling, average win/loss ratio rolling, consecutive losses count, time since last trade, time since last regime change, portfolio heat (total exposure / max exposure).

Ponderação: cada variável é ponderada por information gain I(Vᵢ; R_future) onde R_future = retorno futuro. Variáveis com I ≈ 0 são monitoradas mas não influenciam decisões. Variáveis com I alto recebem peso proporcional. Curse of dimensionality evitada por: (i) information-theoretic feature selection (mRMR), (ii) random projection para redução de dimensionalidade preservando distâncias (Johnson-Lindenstrauss), (iii) hierarchical grouping para evitar redundância (variáveis correlacionadas representadas por líder do cluster).