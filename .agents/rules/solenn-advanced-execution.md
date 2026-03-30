---
trigger: always_on
---

EXECUÇÃO AVANÇADA (Ω-21 a Ω-30)
Ω-21 — CUSTO TOTAL DE EXECUÇÃO (TCE)

TCE = ΣComponents onde cada componente é modelado e minimizado separadamente:

Componente	Modelo	Minimização
Comissão	Fee schedule × volume × tier	Maximizar maker fills, atingir próximo tier
Slippage de entrada	f(size, depth, vol, urgência)	Smart order splitting, limit orders quando possível
Slippage de saída	f(size, depth, vol, urgência)	Pre-computed exit levels, limit quando possível
Market impact	η(Q/D)^γ (Almgren-Chriss)	Fragmentação temporal, passividade quando possível
Funding cost	rate × notional × hold_time	Minimizar hold time, preferir funding-neutral hours
Opportunity cost	spread_missed × P(missed_fill)	Balance aggression vs cost
Latency cost	E[unfavorable_move_during_latency]	Minimize critical path latency
Information leakage	Custo de outros agentes inferindo intenção	Randomizar execution pattern
TCE budget: para cada trade, TCE estimado é subtraído do expected profit ANTES da decisão de execução. Se E[profit] - E[TCE] < min_profit_threshold, trade é REJEITADO — não vale a pena executar.

TCE optimization é tão importante quanto alpha discovery: um sistema com edge de 5bps mas TCE de 3bps tem alpha REAL de 2bps. Reduzir TCE de 3bps para 1bps DOBRA o alpha real. TCE optimization tem retorno certo (não estocástico como alpha).

Ω-22 — CROSS-EXCHANGE INTELLIGENCE

Visão consolidada multi-exchange: aggregated order book de 3+ exchanges com:

Depth normalizado (ajustado por fee tier para comparação justa)
Price discrepancy map (arbitrage gaps)
Flow direction analysis (capital migrando de exchange A para B = ação iminente em B)
Latency map (quem lidera, quem segue, com que delay)
Liquidity concentration (qual exchange tem mais liquidez REAL em cada nível)
Cross-exchange signals:

Basis divergence between exchanges → mean-reversion trade ou sinal direcional (se uma exchange lidera)
Volume surge em exchange X mas não em Y → informação assimétrica, exchange X é a fonte → follow
Funding divergence entre exchanges → carry trade entre exchanges ou sinal de posicionamento assimétrico
Exchange health scoring: score contínuo para cada exchange baseado em: uptime rolling, latency p99, order fill quality, data freshness, regulatory risk, withdrawal processing time. Score baixo → reduzir dependência, shift para exchange com score mais alto.

Ω-23 — TEMPORAL PATTERN MINING

Sequential pattern mining: algoritmos GSP/PrefixSpan/SPADE aplicados a sequências de (trade_direction, size_bucket, volatility_state, imbalance_state, regime_state) → descobrir padrões temporais tipo: "após sequência [large_buy, vol_spike, imbalance_bullish], há 94% de probabilidade de upmove > 5 ticks em 3-7 segundos".

Temporal association rules: {antecedent} →{Δt} {consequent} com suporte, confiança, lift. Exemplo: {funding_spike, OI_increase, vol_compression} →{5min} {breakout_up} com confidence 0.87, lift 4.2. Rules com lift > 3 e confidence > 0.8 são candidatas a setups.

Motif discovery: TimeSeries motifs (subsequências recorrentes) via Matrix Profile (STUMPY algorithm). Motifs frequentes = padrões recorrentes do mercado. Motifs seguidos consistentemente por certo outcome = padrões explorável.

Anomaly discovery: Matrix Profile discords = subsequências mais incomuns. Anomalias que precedem movimentos grandes = early warning signals. Catálogo de anomalias-precursoras mantido e monitorado em tempo real.

Ω-24 — NETWORK SCIENCE FINANCEIRA

Mercado como rede dinâmica:

Nós: ativos, participantes inferidos, níveis de preço
Edges: fluxos de capital, correlações, causalidade de Granger, transferência de entropia
Propriedades monitorizadas:
Centrality (betweenness, eigenvector, PageRank) por ativo → identificar ativo-chave cujo movimento propagará mais
Clustering coefficient → cliquishness = fragilidade sistêmica
Average shortest path → velocidade de propagação de choque
Community structure (Louvain/Infomap) → clusters de ativos que movem juntos
Percolation threshold → distância ao colapso sistêmico
Spectral gap → estabilidade da rede (gap grande = estável, gap pequeno = instável)
Aplicação operacional: quando network metrics indicam fragilidade sistêmica crescente (clustering ↑, spectral gap ↓, percolation proximity ↑), REDUZIR exposição total, AUMENTAR hedge, REDUZIR correlação entre posições.

Ω-25 — SYMBIOTIC LEARNING CEO-BOT

Feedback do CEO como prior bayesiano suave: quando CEO expressa opinião ("acho que BTC vai cair hoje"), não é tratada como dado duro (evidence) mas como prior bayesiano que LEVEMENTE desloca a distribuição posterior, com strength = f(track_record_CEO, confidence_expressed, consistency_with_data). CEO acertou 70% das previsões direcionais? Prior tem weight 0.7. CEO acertou 50%? Prior tem weight ≈ 0 (uninformative). CEO acertou 80%? Prior tem weight 0.8 (strong prior).

Bot ensina CEO: visualizações que revelam padrões não-óbvios, explicações de POR QUE tomou cada decisão, insights sobre microestrutura que humano não observaria, alertas sobre vieses cognitivos que o CEO pode estar exibindo ("CEO, sua sugestão é inconsistente com o que os dados mostram — confirmamos viés de recência?").

Vocabulário compartilhado evolui: jargão interno do projeto evolui organicamente — termos novos criados quando conceito novo emerge (QOFE, RTLI, etc.), definições mantidas em glossário vivo, ambiguidade eliminada progressivamente.

Ω-26 — DIMENSIONAL ANALYSIS & SCALING LAWS

Teorema de Buckingham Pi: qualquer lei física pode ser expressa como relação entre grupos adimensionais. Aplicação: identificar quais combinações adimensionais de variáveis de mercado (ex: return / volatility = Sharpe, volume / avg_volume = relative_volume, spread / price = relative_spread) são as quantidades verdadeiramente fundamentais — invariantes sob mudança de escala.

Scaling laws de física estatística: se return(τ) ~ τ^H (scaling com expoente H), esta lei define a relação fundamentalmente entre timeframes e é explorável para transporte de informação cross-timeframe. Se P(return > x) ~ x^{-α} (power law tail), α define o risco verdadeiro (não-gaussiano) e é o parâmetro mais importante para risk management.

Renormalization group flow: como parâmetros efetivos (volatilidade, correlação, edge) mudam quando observados em escalas diferentes? Se edge é "relevant" (no sentido de RG), ele sobrevive a mudanças de escala e é genuíno. Se é "irrelevant", desaparece em escalas maiores e é overfitting à microestrutura.

Ω-27 — INFORMATION GEOMETRY

Espaço de modelos como variedade Riemanniana: cada modelo M é um ponto em variedade Μ. Métrica de Fisher I(θ) define distância entre modelos: ds² = Σᵢⱼ I_ij(θ) dθᵢ dθⱼ onde I_ij = E[∂log p/∂θᵢ × ∂log p/∂θⱼ].

Aplicações operacionais:

Distância entre modelo atual e modelo calibrado = quão desatualizado está o modelo
Geodésica entre modelos = caminho ótimo de re-calibração (menor perturbação que alcança novo ótimo)
Curvatura no espaço de modelos = sensibilidade a re-calibração (curvatura alta = modelo sensível)
Volume do espaço de modelos consistentes com dados = diversidade de explicações plausíveis = incerteza do modelo
Detecção de redundância no ensemble: se dois modelos estão geodesicamente próximos, são redundantes → manter apenas um
Natural gradient: gradient descent no espaço de modelos usando métrica de Fisher é invariante a reparametrização e converge mais rápido que gradient descent euclidiano → usar para todos os processos de otimização de modelos.

Ω-28 — ADVERSARIAL ROBUSTNESS

Red Team contínuo: modelo adversarial (red team) treinado com um único objetivo — encontrar o input (market state) que MAXIMIZA a perda do SOLÉNN.

Protocolo:

Red team gera market state adversarial s* = argmax_s Loss(SOLÉNN(s))
SOLÉNN é exposto a s* e avaliado
Se Loss(s*) > threshold_acceptable, SOLÉNN é re-treinado/ajustado para ser robusto a s*
Red team é re-treinado para encontrar NOVO s** que maximize perda do SOLÉNN atualizado
Iteração até convergência (Nash equilibrium)
Tipos de adversários:

Market adversary: gera sequências de preço/volume adversariais
Execution adversary: gera cenários de latência/slippage adversariais
Data adversary: gera cenários de dados corrompidos/atrasados
Multi-failure adversary: gera combinações de falhas simultâneas
Adaptive adversary: adversário que aprende a se adaptar à defesa do SOLÉNN
Objetivo: após convergência, SOLÉNN é robusto contra o adversário mais inteligente que conseguimos construir. Não significa invulnerável — mas maximamente resiliente dado nosso nível de imaginação adversarial.

Ω-29 — CAUSAL DISCOVERY AUTOMATIZADA

Algoritmos de descoberta causal aplicados continuamente a dados de mercado:

PC algorithm: constraint-based, testa independência condicional, eficiente em redes sparse
FCI (Fast Causal Inference): extensão de PC para variáveis latentes e seleção amostral
GES (Greedy Equivalence Search): score-based, busca no espaço de DAGs, BIC score
NOTEARS: continuous optimization formulation, W = argmin_W F(W) s.t. h(W) = 0 (DAG constraint)
PCMCI+: específico para séries temporais, controla autocorrelação e lag
DAG-GNN: neural network-based causal discovery para relações não-lineares
Grafo causal atualizado continuamente: estrutura causal do mercado não é estática — edges aparecem/desaparecem, strengths mudam, lags mudam. Grafo é re-estimado a cada hora com dados das últimas 24h (sliding window). Mudanças no grafo = mudança de estrutura do mercado = sinal de regime transition.

Intervenção via do-calculus: dado grafo causal, calcular efeito de intervenções hipotéticas — "se funding rate FORÇADO a zero, qual o efeito no preço?" → identificar leverage points.

Ω-30 — COMPRESSED SENSING & SPARSE RECOVERY

Princípio: se o sinal de mercado é sparse em alguma base (Fourier, wavelet, aprendida), pode ser recuperado com MENOS observações que Shannon-Nyquist exige.

Aplicação:

Detecção mais rápida: detectar padrão emergente com menos dados (menos ticks) que métodos tradicionais, reduzindo latência de detecção.
Reconstrução de book incompleto: quando dados do book estão incompletos (exchange com poucos níveis públicos), reconstruir book completo via compressed sensing assumindo que o book real é sparse em alguma base.
Denoising: separar sinal de ruído via sparse recovery — L1 minimization (LASSO/Basis Pursuit) em base onde sinal é sparse mas ruído não é.
Anomaly detection: anomalias são, por definição, sparse (raras). L1 minimization decompõe dados em componente regular + componente sparse (anomalias) → detecção natural.
Base ótima: pode ser fixa (wavelet, Fourier) ou APRENDIDA (dictionary learning via K-SVD, convolutional sparse coding). Base aprendida adapta-se à estrutura específica do mercado → performance superior.

