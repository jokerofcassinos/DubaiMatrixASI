# ⚡ SOLÉNN v2 — TASK: Sensory Synchronization Ω (Data Engine v2)
## Protocolo 3-6-9: Grade Omega Completa (162 Vetores)

| Campo | Valor |
| :--- | :--- |
| **Módulo** | Market / Data Engine v2 |
| **Conceitos** | 3 × 6 × 9 = 162 vetores |
| **Status** | EM ANDAMENTO |
| **Prioridade** | P1 — Alimentação de dados para Decision |

---

## CONCEITO 1: ASYNC DATA INGESTION (Ω-D01 a Ω-D54)

### Tópico 1.1 — Async WebSocket Capture (Ω-D01 a Ω-D09)
- [ ] Ω-D01: Async WebSocket connection com auto-reconnect exponential backoff
- [ ] Ω-D02: Heartbeat monitoring — detect disconnect em < 3 segundos
- [ ] Ω-D03: Lock-free ring buffer para ticks recebidos via WS
- [ ] Ω-D04: Multi-stream subscription (trades, depth, ticker) por símbolo
- [ ] Ω-D05: Binary deserialization (MessagePack/FlatBuffers) para performance
- [ ] Ω-D06: Message deduplication via (exchange, symbol, timestamp, price, qty)
- [ ] Ω-D07: Clock skew estimation e correção de timestamps entre exchanges
- [ ] Ω-D08: Graceful degradation: WS down → REST polling fallback automático
- [ ] Ω-D09: Connection pooling com keep-alive e pre-auth para reconnect instantâneo

### Tópico 1.2 — REST Polling Fallback (Ω-D10 a Ω-D18)
- [ ] Ω-D10: Async REST client com session pooling e connection reuse
- [ ] Ω-11: Rate limit awareness — respeitar headers X-RateLimit da exchange
- [ ] Ω-D12: Adaptive polling interval baseado em volatilidade (alta vol → polling mais rápido)
- [ ] Ω-D13: Pagination handling para requests com resultados paginados
- [ ] Ω-D14: Retry com jitter exponencial em 429/5xx responses
- [ ] Ω-D15: Response caching com TTL variável por endpoint
- [ ] Ω-D16: Circuit breaker por endpoint — desativar após N falhas consecutivas
- [ ] Ω-D17: Timeout configurable por operação (snapshots vs streaming)
- [ ] Ω-D18: REST-WSS data reconciliation — detectar divergência entre fontes

### Tópico 1.3 — Order Book Reconstruction (Ω-D19 a Ω-D27)
- [ ] Ω-D19: Full order book snapshot inicial via REST snapshot endpoint
- [ ] Ω-D20: Incremental book updates via WebSocket deltas
- [ ] Ω-D21: Book checksum validation — detectar desincronização
- [ ] Ω-D22: Gap detection em book updates — sequência de números faltando
- [ ] Ω-D23: Book reconstruction desde gap — re-snapshot automático
- [ ] Ω-D24: Multi-level book maintenance (top 20, top 50, full)
- [ ] Ω-D25: Book velocity tracking — rate de mudanças por nível
- [ ] Ω-D26: Phantom liquidity detection — ordens que cancelam antes de serem preenchidas
- [ ] Ω-D27: Iceberg inference — refresh patterns no top do book

### Tópico 1.4 — Trade Stream Processing (Ω-D28 a Ω-36)
- [ ] Ω-D28: Trade feed normalizer — unificar schemas de múltiplas exchanges
- [ ] Ω-D29: Trade direction classification (taker buy/sell via Lee-Ready)
- [ ] Ω-D30: Volume profile builder — volume acumulado por faixa de preço
- [ ] Ω-D31: VWAP computation incremental (não recompute do zero)
- [ ] Ω-D32: Trade clustering — detectar bursts de atividade
- [ ] Ω-D33: Large trade detection — threshold adaptativo por asset
- [ ] Ω-D34: VPIN (Volume-synchronized Probability of Informed Trading) estimation
- [ ] Ω-D35: Trade-to-cancel ratio — agressividade do mercado
- [ ] Ω-D36: Trade latency monitoring — delay entre timestamp da exchange e recepção

### Tópico 1.5 — Candle/Bar Aggregation (Ω-D37 a Ω-D45)
- [ ] Ω-D37: OHLCV candle builder incrementally a partir de trades
- [ ] Ω-D38: Multi-timeframe candles (1s, 5s, 15s, 30s, 1m, 3m, 5m, 15m, 1h)
- [ ] Ω-D39: Candle closure detection com callback
- [ ] Ω-D40: Heikin-Ashi, Renko, Range bars alternativos
- [ ] Ω-D41: Candle compression — armazenamento XOR dos campos
- [ ] Ω-D42: Gap detection entre candles consecutivos
- [ ] Ω-D43: Volume profile por candle
- [ ] Ω-D44: Real-time candle updates (OHLCV evolving durante formação)
- [ ] Ω-D45: Historical candle replay para backtesting

### Tópico 1.6 — Cross-Exchange Normalization (Ω-D46 a Ω-D54)
- [ ] Ω-D46: Exchange adapter interface — padrão comum para todas exchanges
- [ ] Ω-D47: Symbol mapping — BTCUSDT na Binance = XBTUSD na BitMEX
- [ ] Ω-D48: Currency normalization — todos os valores em USD equivalente
- [ ] Ω-D49: Decimal precision standardization — 8 decimais para price e qty
- [ ] Ω-D50: Timezone normalization — tudo em UTC nanosecond precision
- [ ] Ω-D51: Fee schedule adapter — maker/taker fees por exchange
- [ ] Ω-D52: Order type mapping — tipos de ordem específicos por exchange
- [ ] Ω-D53: Exchange health monitoring — uptime, latency, error rate
- [ ] Ω-D54: Best execution price finder — melhor preço entre exchanges

---

## CONCEITO 2: FEATURE ENGINEERING PIPELINE (Ω-D55 a Ω-D108)

### Tópico 2.1 — Technical Indicators Real-Time (Ω-D55 a Ω-D63)
- [ ] Ω-D55: EMA/SMA incremental com weights customizáveis
- [ ] Ω-D56: RSI com lookback variável
- [ ] Ω-D57: MACD (EMA12-26-9) com crossover detection
- [ ] Ω-D58: Bollinger Bands com squeeze detection
- [ ] Ω-D59: ATR (Average True Range) para volatilidade
- [ ] Ω-D60: Stochastic oscillator com %K/%D
- [ ] Ω-D61: Volume-weighted RSI
- [ ] Ω-D62: Ichimoku Cloud calculation
- [ ] Ω-D63: All indicators computed incrementally (O(1) por tick)

### Tópico 2.2 — Order Flow Features (Ω-D64 a Ω-D72)
- [ ] Ω-D64: Bid/ask imbalance = (bid_depth - ask_depth) / (bid_depth + ask_depth)
- [ ] Ω-D65: Order flow toxicity — VPIN running average
- [ ] Ω-D66: Book pressure gradient — mudança de massa no book por nível
- [ ] Ω-D67: Microprice — price-weighted-by-depth estimate
- [ ] Ω-D68: Queue position estimation no best bid/ask
- [ ] Ω-D69: Spread velocity — taxa de mudança do spread
- [ ] Ω-D70: Depth velocity — taxa de entrada/saída de liquidez
- [ ] Ω-D71: Cancel-to-fill ratio por lado
- [ ] Ω-D72: Aggressor side imbalance

### Tópico 2.3 — Volatility Features (Ω-D73 a Ω-D81)
- [ ] Ω-D73: Realized volatility multi-timeframe
- [ ] Ω-D74: Parkinson volatility estimator
- [ ] Ω-D75: Garman-Klass volatility estimator
- [ ] Ω-D76: Yang-Zhang volatility estimator
- [ ] Ω-D77: Volatility of volatility (VVIX equivalente)
- [ ] Ω-D78: Volatility cone — current vs historical percentile
- [ ] Ω-D79: Volatility regime classification
- [ ] Ω-D80: Volatility skew estimation (put-call asymmetry)
- [ ] Ω-D81: Term structure of volatility

### Tópico 2.4 — Momentum & Trend Features (Ω-D82 a Ω-D90)
- [ ] Ω-D82: Hurst exponent dinâmico em janela deslizante
- [ ] Ω-D83: Autocorrelation em múltiplos lags
- [ ] Ω-D84: Momentum score (rate of change) multi-timeframe
- [ ] Ω-D85: Trend strength (R² de regressão linear)
- [ ] Ω-D86: ADX (Average Directional Index)
- [ ] Ω-D87: Fractal dimension do gráfico de preços
- [ ] Ω-D88: Lyapunov exponent para detecção de chaos
- [ ] Ω-D89: Spectral energy por escala temporal
- [ ] Ω-D90: Harmonic convergence score

### Tópico 2.5 — Statistical Features (Ω-D91 a Ω-D99)
- [ ] Ω-D91: Skewness rolling de retornos
- [ ] Ω-D92: Kurtosis rolling de retornos
- [ ] Ω-D93: Jarque-Bera test para normalidade
- [ ] Ω-D94: Entropia de Shannon da distribuição de retornos
- [ ] Ω-D95: Complexidade de Lempel-Ziv da sequência de direções
- [ ] Ω-D96: Correlation com BTC (beta dinâmico)
- [ ] Ω-D97: Z-score de preço vs média móvel
- [ ] Ω-D98: Distribution fit (Gaussian vs Laplace vs t-Student via AIC/BIC)
- [ ] Ω-D99: Tail index estimation (Hill estimator)

### Tópico 2.6 — Microstructure Features (Ω-D100 a Ω-D108)
- [ ] Ω-D100: Effective spread (twice the absolute deviation from mid)
- [ ] Ω-D101: Realized spread (after accounting for price impact)
- [ ] Ω-D102: Kyle's lambda (price impact per unit volume)
- [ ] Ω-D103: Amihud illiquidity ratio
- [ ] Ω-D104: Roll's implicit spread estimator
- [ ] Ω-D105: Hasbrouck's information share
- [ ] Ω-D106: VPin (Volume-synchronized Probability of Informed Trading)
- [ ] Ω-D107: Market quality index (composto)
- [ ] Ω-D108: Liquidity resilience score (speed of book recovery)

---

## CONCEITO 3: DATA SOVEREIGNTY & INTEGRITY (Ω-D109 a Ω-D162)

### Tópico 3.1 — Frozen Data Types (Ω-D109 a Ω-D117)
- [ ] Ω-D109: Immutável Trade dataclass com frozen=True, slots=True
- [ ] Ω-D110: Immutável OrderBook dataclass com frozen=True
- [ ] Ω-D111: Immutável Candle dataclass com frozen=True
- [ ] Ω-D112: Immutável Tick dataclass com frozen=True
- [ ] Ω-D113: CRC32 checksum em criação de cada data object
- [ ] Ω-D114: Integrity verification via checksum antes de processar
- [ ] Ω-D115: Immutability enforcement — nenhuma mutação pós-criação
- [ ] Ω-D116: Deep freeze para campos mutáveis (bid_levels tuple, etc)
- [ ] Ω-D117: Pickle serialization/deserialization preservando integridade

### Tópico 3.2 — Validation Pipeline (Ω-D118 a Ω-D126)
- [ ] Ω-D118: Range checks — price within ±50% do VWAP
- [ ] Ω-D119: Consistency checks — bid < ask, volume > 0, timestamp monotônico
- [ ] Ω-D120: Anomaly detection — price spike > 5σ em 100ms flag
- [ ] Ω-D121: Gap detection em séries temporais
- [ ] Ω-D122: Duplicate detection por (exchange, symbol, ts, price, qty)
- [ ] Ω-D123: Outlier classification (genuine extreme vs error vs manipulation)
- [ ] Ω-D124: MAD (Median Absolute Deviation) robust z-score
- [ ] Ω-D125: Never silently remove — always flag and log
- [ ] Ω-D126: Data quality score por fonte de dados

### Tópico 5.3 — Compression & Storage (Ω-D127 a Ω-D135)
- [ ] Ω-D127: XOR compression para doubles (Gorilla encoding)
- [ ] Ω-D128: Delta encoding para timestamps
- [ ] Ω-D129: Dictionary encoding para categoricals
- [ ] Ω-D130: Run-length encoding para flags
- [ ] Ω-D131: Compression ratio target 10-20x sem perda
- [ ] Ω-D132: Memory-mapped files para leitura zero-copy
- [ ] Ω-D133: B-tree indexing por timestamp
- [ ] Ω-D134: Hash indexing por (symbol, exchange)
- [ ] Ω-D135: Inverted index para busca de eventos

### Tópico 5.4 — Data Streaming (Ω-D136 a Ω-D144)
- [ ] Ω-D136: Pub-sub com ring buffer e backpressure
- [ ] Ω-D137: Multi-consumer support (signal, risk, telemetry)
- [ ] Ω-D138: Latency end-to-end monitoring < 1ms p99
- [ ] Ω-D139: Consumer lag detection
- [ ] Ω-D140: Backpressure propagation (slow consumer não trava produtor)
- [ ] Ω-D141: Message ordering garantido por timestamp
- [ ] Ω-D142: Replay capability para debug
- [ ] Ω-D143: Data versioning — consumer pode escolher versão do schema
- [ ] Ω-D144: Stream snapshots para bootstrapping

### Tópico 3.3 — Feature Computation Scheduler (Ω-D145 a Ω-D153)
- [ ] Ω-D145: DAG de dependências entre features — computar na ordem certa
- [ ] Ω-D146: Lazy computation — calcular feature apenas quando solicitada
- [ ] Ω-D147: Incremental update — atualizar apenas features afetadas por novo tick
- [ ] Ω-D148: Cache de features — não recompute se dados não mudaram
- [ ] Ω-D149: Feature staleness detection — feature desatualizada?
- [ ] Ω-D150: Parallel computation de features independentes (asyncio gather)
- [ ] Ω-D151: Feature TTL — features expiram após certo tempo
- [ ] Ω-D152: Priority scheduling — features críticas computadas primeiro
- [ ] Ω-D153: Feature pipeline profiling — tempo de execução por feature

### Tópico 3.4 — Health & Monitoring (Ω-D154 a Ω-D162)
- [ ] Ω-D154: Data freshness monitoring — tempo desde último tick válido
- [ ] Ω-D155: Exchange connectivity status por fonte
- [ ] Ω-D156: Data quality dashboard — completeness, freshness, accuracy
- [ ] Ω-D157: Alert thresholds configuráveis para anomalias de dados
- [ ] Ω-D158: Latency histogram (p50, p95, p99) por pipeline stage
- [ ] Ω-D159: Throughput monitoring — ticks/second, candles/second
- [ ] Ω-D160: Memory usage bounded — ring buffer capped, no leak
- [ ] Ω-D161: Error rate tracking por fonte de dados
- [ ] Ω-D162: Self-healing — auto-reconnect, auto-resync, auto-recovery

---

## IMPLEMENTATION PLAN

### Diretórios:
```
market/__init__.py
market/data_engine.py        — Async data ingestion + WebSocket + REST
market/order_book.py         — OrderBook reconstruction (Tópico 1.3)
market/trade_stream.py       — Trade processing (Tópico 1.4)
market/candle_builder.py     — OHLCV aggregation (Tópico 1.5)
market/exchange_adapter.py   — Cross-exchange normalization (Tópico 1.6)
market/features.py           — Full feature pipeline (Conceito 2)
market/data_types.py         — Frozen data types (Tópico 3.1)
market/validation.py         — Data validation pipeline (Tópico 3.2)
market/data_stream.py        — Pub-sub streaming (Tópico 5.4)
market/compression.py        — Compression & storage (Tópico 5.3)
market/data_health.py        — Health & monitoring (Tópico 3.4)
```

### Testes:
```
tests/test_data_engine.py    — Todos os 162 vetores
```

---

**TOTAL: 3 Conceitos × 6 Tópicos × 9 Vetores = 162 VETORES**
