---
trigger: always_on
---

ANÁLISE & INTELIGÊNCIA (Ω-11 a Ω-20)
Ω-11 — INOVAÇÃO PROPRIETÁRIA RADICAL: CRIAÇÃO DE CONHECIMENTO NOVO

O SOLÉNN não apenas APLICA conhecimento existente — CRIA conhecimento novo. Framework de inovação proprietária em 4 estágios:

Estágio 1 — Observação de anomalias: identificar fenômenos no mercado que modelos existentes não explicam. Anomalia = resíduo inexplicado = oportunidade de novo conhecimento.

Estágio 2 — Formulação de hipótese generativa: "Qual mecanismo oculto produziria EXATAMENTE esta anomalia?" Raciocínio abdutivo (Ψ-8) gerando hipóteses candidatas.

Estágio 3 — Formalização matemática: hipótese traduzida em modelo matemático com predições quantitativas testáveis.

Estágio 4 — Validação experimental rigorosa: teste out-of-sample com protocolo pré-registrado, p-value corrigido, replicação em regime diferente.

Indicadores proprietários expandidos (além dos já definidos em Ω-1):

CFRI (Causal Flow Reversal Indicator): mede inversão na estrutura causal do mercado. Normalmente: macro → crypto (macro lidera). Em certas condições: crypto → macro (crypto lidera). CFRI detecta quando a direção de causalidade de Granger INVERTE → sinal de mudança de regime fundamental. Computação: transfer entropy T(macro→crypto) vs T(crypto→macro); CFRI = T(crypto→macro) / [T(macro→crypto) + ε]. CFRI > 1 = crypto liderando = regime atípico = tratar com cautela ou explorar a atipicidade.

EPDI (Emergent Pattern Density Index): contagem de padrões topológicos (β₀, β₁, β₂ de persistent homology) por unidade de tempo. EPDI crescente = mercado gerando mais estrutura = oportunidades crescendo. EPDI decrescente = mercado simplificando = movimentação forte iminente ou morte de atividade.

MFCS (Multi-Fractal Coherence Spectrum): para cada par de escalas (s₁, s₂), medir coerência espectral cruzada do espectro multifractal. MFCS alto em todas as escalas = mercado em harmonia multi-escala = setup de ultra-alta confiança. MFCS baixo = escalas discordantes = conflito = cautela.

LACI (Liquidity Absorption Capacity Index): volume necessário para mover preço 1bps / 5bps / 10bps / 25bps / 50bps, estimado por book depth real + histórico de execução + liquidity replenishment rate. LACI define o "tamanho máximo de posição" que o mercado suporta sem auto-impacto significativo.

RESI (Reflexive Equilibrium Stability Index): mede distância do mercado ao ponto de equilíbrio reflexivo de Soros. RESI alto = mercado perto de equilíbrio (estável, pouca oportunidade). RESI baixo = mercado longe de equilíbrio (instável, oportunidade alta). RESI ≈ 0 = ponto de bifurcação (máxima incerteza E máxima oportunidade).

TEDI (Temporal Entropy Differential Index): diferença de entropia entre janelas temporais adjacentes. TEDI = H(t, t-Δt) - H(t-Δt, t-2Δt). TEDI positivo = entropia crescente = mercado tornando-se mais imprevisível = reduzir. TEDI negativo = entropia decrescente = mercado tornando-se mais previsível = aumentar. TEDI ≈ 0 = estável.

QSMI (Quantum Superposition Market Index): inspirado em mecânica quântica — mercado em "superposição" de múltiplos estados possíveis antes do "colapso" (decisão). QSMI mede o número de estados de alta probabilidade (>10%) no ensemble de modelos. QSMI = 1 → mercado em estado quase-puro = alta confiança direcional. QSMI = 2 → superposição binária = bifurcação iminente, posicionar com straddle/strangle. QSMI > 3 → mercado em superposição complexa = NO TRADE.

ICDI (Institutional Camouflage Detection Index): mede a probabilidade de que o fluxo visível esteja sendo deliberadamente mascarado. Baseado em: discrepância volume executado/volume visível, anomalia de timing (regularidade suspeita), cross-exchange coordination (mesmo padrão em múltiplas exchanges com delays consistentes), size masking (ordens grandes fragmentadas em ordens de tamanho "round-number" diferente para parecerem varejo). ICDI alto = alguém grande está tentando esconder algo = oportunidade para quem detecta.

Ω-12 — ÉTICA, COMPLIANCE & GUARDRAILS INVIOLÁVEIS

Guardrails absolutos contra manipulação ilegal:

Zero spoofing (NUNCA colocar ordem com intenção de cancelar antes de fill)
Zero layering (NUNCA construir profundidade artificial)
Zero wash trading (NUNCA negociar consigo mesmo)
Zero front-running de clientes (N/A em trading proprietário, mas princípio mantido)
Zero market manipulation (NUNCA agir com intenção de distorcer preço)
Audit trails: cada decisão do SOLÉNN é logada com: timestamp (microsecond precision), input data snapshot, modelo usado, parâmetros ativos, score de confiança, decisão tomada, razão da decisão (human-readable), alternativas consideradas e por que foram rejeitadas. Trail é imutável (append-only), criptograficamente assinado, e retido por mínimo 7 anos.

Compliance-aware alpha: quando existe conflito entre compliance e alpha, compliance vence SEMPRE com zero exceções. Mas: soluções criativas que satisfazem compliance E maximizam alpha são ativamente buscadas. Compliance não é constraint a ser contornada — é constraint a ser satisfeita com máxima elegância.

Ω-13 — INFRAESTRUTURA DE DADOS INSTITUCIONAL

Pipeline de dados ultra-baixa latência em 12 estágios:

Estágio 1 — Captura: conexão direta via WebSocket (primário) + REST polling (fallback) com heartbeat monitoring, reconnection automática com exponential backoff + jitter, e multi-source redundancy (2+ exchanges para mesmo dado).

Estágio 2 — Deserialização: parsing binário (MessagePack/FlatBuffers) com zero-copy quando possível, custom allocators sem GC, buffer pool pré-alocado.

Estágio 3 — Normalização: unificação de schemas entre exchanges (field naming, unit conversion, timezone normalization to UTC-ns, precision standardization to 8 decimals).

Estágio 4 — Validação: range checks (price within ±50% of VWAP), consistency checks (bid < ask, volume > 0, timestamp monotonically increasing), anomaly detection (price spike > 5σ in 100ms → flag for manual review, proceed with caution).

Estágio 5 — Deduplicação: dedup por (exchange, symbol, timestamp, price, quantity, side) com tolerance de ±1ms no timestamp para compensar clock skew.

Estágio 6 — Timestamp Normalization: conversão de todos os timestamps para UTC nanoseconds com estimação e correção de clock offset entre exchanges via NTP-like cross-reference.

Estágio 7 — Gap Detection & Filling: detectar gaps em séries temporais (missing ticks, missing candles), classificar (exchange downtime → gap genuíno, packet loss → preencher por interpolação/repetição, filtering → preencher por modelo), preencher com método apropriado, flagar dados preenchidos para tratamento downstream diferenciado.

Estágio 8 — Outlier Handling: classificar outliers em (genuine extreme event → preservar, data error → corrigir ou excluir, manipulation artifact → flagar). Método: MAD (Median Absolute Deviation) robust z-score > 10 → investigar, > 20 → quase certamente erro. Never silently remove — always flag and log.

Estágio 9 — Feature Engineering: computação de features derivadas (returns, log-returns, volatility, momentum, imbalance ratios, etc.) com pipeline de cálculo incremental (não recomputar do zero a cada tick, atualizar incrementalmente).

Estágio 10 — Compressão: armazenamento comprimido (Gorilla compression para timestamps, XOR para doubles, dictionary encoding para categoricals, run-length para flags) com ratio de compressão típico 10-20x sem perda.

Estágio 11 — Indexação: indexação por (timestamp, symbol, exchange) com B-tree para range queries temporais, hash para point lookups, inverted index para event search.

Estágio 12 — Streaming Real-Time: dados disponíveis para consumidores via pub-sub (ring buffer com backpressure) com latência end-to-end (captura → disponível para consumo) < 1ms no p99.

Ω-14 — BACKTESTING COM MICROESTRUTURA REALISTA

Simulação que captura TODAS as fontes de irrealismo do backtesting naïve:

Posição na fila: ordens limit não são filled instantaneamente — são filled quando chegam ao topo da fila. Modelar posição na fila via tempo de submissão + priority rules da exchange (price-time, pro-rata, etc.).

Partial fills: ordens grandes são filled parcialmente, com timing estocástico dos fills parciais modelado por processo de Poisson não-homogêneo com intensidade dependente de profundidade e volatilidade.

Market impact das próprias ordens: execução de tamanho Q em mercado de profundidade D causa impacto temporário Δp_temp = η × (Q/D)^γ (Almgren-Chriss com γ ≈ 0.5-0.7) + impacto permanente Δp_perm = λ × (Q/ADV)^δ. Impacto é tanto no preço de execução quanto na reação de outros participantes.

Latência realista: delay entre decisão e execução = [decision_latency + network_latency + exchange_matching_latency]. Cada componente é variável estocástica calibrada em dados reais. Durante esse delay, preço pode mover desfavoravelmente.

Slippage realista: diferença entre preço esperado e preço de execução = f(tamanho, profundidade, volatilidade instantânea, tipo de ordem, horário). Modelado como distribuição assimétrica (viés negativo — slippage tende a ser contra nós).

Fee modeling completo: maker/taker fees, tier discounts baseados em volume rolling, rebates, funding costs (para posições mantidas por múltiplos funding periods), withdrawal fees se cross-exchange.

Cenários adversariais: simular backtesting onde o mercado REAGE à nossa presença — outros participantes detectam nossos padrões e adaptam. "Backtesting with oracle adversary" — worst-case performance.

Overfitting detection: (i) Walk-forward analysis com janelas não-sobrepostas, (ii) Combinatorial purged cross-validation (CPCV) de Bailey & de Prado, (iii) Deflated Sharpe Ratio (DSR) que penaliza por número de trials, (iv) Minimum Backtest Length (MinBTL), (v) Probability of Backtest Overfitting (PBO) via combination of Sharpe across IS/OOS splits.

Ω-15 — MONITORAMENTO SRE (Site Reliability Engineering)

Dashboards em 3 camadas:

Camada Executive (CEO): P&L curve, drawdown, Sharpe rolling, win rate rolling, position status, circuit breaker status, regime. Atualização: 1s.
Camada Operacional: todas as métricas de trading + microestrutura + modelo + execução. Atualização: 100ms.
Camada Debug: logs brutos, state machine, order lifecycle, data pipeline health. Atualização: real-time streaming.
Alertas hierárquicos: INFO (log only) → WARNING (Slack notification) → ERROR (Slack + sound) → CRITICAL (Slack + sound + SMS) → FATAL (all channels + auto-shutdown + CEO phone call trigger).

Logs estruturados: JSON format com campos obrigatórios: {timestamp, level, component, event_type, message, context: {trade_id, regime, confidence, position, etc.}, trace_id, span_id}. Rotação diária, retenção 90 dias hot + cold storage indefinido.

Tracing distribuído: cada decisão de trading = trace com spans para: data_ingestion → feature_computation → regime_detection → signal_generation → confluence_evaluation → risk_check → order_creation → order_submission → order_fill → post_trade_analysis. Trace ID permite reconstruir toda a cadeia causal de qualquer decisão.

Anomaly detection pré-impacto: modelos de detecção de anomalia em métricas de sistema (latência, throughput, error rate) que detectam degradação ANTES de impacto financeiro: (i) ARIMA-based forecast vs actual, (ii) isolation forest para anomalias multivariadas, (iii) CUSUM para shifts de média, (iv) custom rules (ex: latência p99 > 2x média de 1h → alert).