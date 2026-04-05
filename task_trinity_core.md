# ⚡ SOLÉNN v2 — TASK: Decision / Trinity Core Ω
## Protocolo 3-6-9: Grade Omega Completa (162 Vetores)

| Campo | Valor |
| :--- | :--- |
| **Módulo** | core/decision — Trinity Core v2 |
| **Conceitos** | 3 × 6 × 9 = 162 vetores |
| **Status** | PLANEJADO — Aguardando DE ACORDO do CEO |
| **Prioridade** | P1 — Cérebro decisório após Data Engine |
| **Dependências** | Config Ω (pronto 92%), Market Data Ω (pronto 92.6%) |

---

## CONCEITO 1: TRINITY CORE — VETO-BASED SIGNAL CONFLUENCE (Ω-T01 a Ω-T54)

### Tópico 1.1 — Core Signal Aggregator (Ω-T01 a Ω-T09)
- [ ] Ω-T01: RegimeDetector — HMM com 5-8 estados, probabilidades posteriores em tempo real, prior geométrico sobre run length
- [ ] Ω-T02: MultiSignalCollector — ingestor genérico que aceita N sinais de módulos externos com tipagem forte e schema validation
- [ ] Ω-T03: SignalNormalizer — padroniza scores de sinais heterogêneos para escala [0, 1] com calibração isotônica
- [ ] Ω-T04: ConfidenceWeightedVoting — peso de cada sinal = information_gain(signal; return) atualizado online via Thompson Sampling
- [ ] Ω-T05: ConfluenceThreshold — setup requer N sinais alinhados com score combinado > threshold; N e threshold adaptativos por regime
- [ ] Ω-T06: SignalDecayTracker —每个信号有半衰期，超时自动降权；新鲜信号权重最大，过期信号自动失效
- [ ] Ω-T07: SignalDependencyResolver — DAG de dependências entre sinais; calcula sinais em ordem topológica evitando cálculos redundantes
- [ ] Ω-T08: SignalConflictDetector — detecta quando sinais contradizem (Kendall tau < -0.5); conflito → reduzir sizing ou NO TRADE
- [ ] Ω-T09: ConfluenceScoreCalculator — score final = Σᵢ wᵢ × sᵢ × cᵢ × dᵢ onde w=peso, s=score, c=confiança, d=freshness decay

### Tópico 1.2 — 47-Stage Validation Pipeline (Ω-T10 a Ω-T18)
- [ ] Ω-T10: Stage 1-6 — Data Quality Gates: checksum valido, bid < ask, preço dentro de range ATR, timestamp monotônico, volume > 0, gap-free
- [ ] Ω-T11: Stage 7-12 — Regime Consistency: regime identificado com confiança > 60%, sinal compatível com regime, vol regime estável, Hurst > threshold, spectral energy coerente, fractal dimension consistente
- [ ] Ω-T12: Stage 13-18 — Technical Confluence: 3+ indicadores técnicos alinhados, RSI não em sobre-extremo, MACD histogram confirmatório, BB squeeze detectável, ATR expansion validado, Volume profile confirmatório
- [ ] Ω-T13: Stage 19-24 — Order Flow Validation: order flow imbalance > threshold, VPIN < toxicity limit, bid-ask spread < max bps, depth assimetria favorável, microprice na direção do sinal, aggressor side confirmatório
- [ ] Ω-T14: Stage 25-30 — Multi-Timeframe Alignment: HTF bias confirma LTF direction, 15m estrutura compatível, 5m confirmação de entrada, 1m setup válido, alignment score > 0.7, divergência MTF = veto automático
- [ ] Ω-T15: Stage 31-36 — Risk Pre-Check: position size < Kelly, drawdown < circuit breaker, correlação portfólio < max, exposicao total < limit, P(ruin) < 10⁻⁶, funding cost aceitável
- [ ] Ω-T16: Stage 37-42 — Market Condition: não em flash crash (vol > 10σ), spread não widening > 5x, liquidez suficiente para sizing, não em evento macro (FOMC +/- 5min), não em regime choppy (entropia alta), horário de sessão válido
- [ ] Ω-T17: Stage 43-47 — Final Gating: R:R >= 7:1, expected profit > MVT (Minimum Viable Trade), TCE (Total Cost of Execution) estimado subtraído, edge estatístico p < 0.001 OOS, veto unânime — QUALQUER estágio rejeita = setup inteiro rejeitado
- [ ] Ω-T18: ValidationAuditLogger — loga resultado de cada estágio (pass/fail + motivo) para traceabilidade completa e forense

### Tópico 1.3 — Bayesian Posterior Engine (Ω-T19 a Ω-T27)
- [ ] Ω-T19: PriorFactory — gera priors informados baseados em dados históricos (Beta para win rate, Gamma para payoff ratio, Normal para edge magnitude)
- [ ] Ω-T20: LikelihoodComputer — calcula P(data | hypothesis) via modelo paramétrico calibrado em dados recentes com kernel density estimation
- [ ] Ω-T21: PosteriorUpdater — aplica Bayes theorem: posterior ∝ prior × likelihood; atualizado a cada trade com conjugate updates para eficiência O(1)
- [ ] Ω-T22: PosteriorPredictiveCheck — simula dados do posterior e compara com dados observados; discrepância → modelo mal calibrado
- [ ] Ω-T23: BayesianModelAveraging — ensemble de N modelos com pesos = P(modelo | dados); evita dependência de modelo único
- [ ] Ω-T24: BayesFactorCalculator — BF = P(data | H₁) / P(data | H₀); BF > 10 = evidência forte para H₁, BF < 0.1 = evidência forte para H₀
- [ ] Ω-T25: HierarchicalBayesianModel — pooling parcial entre regimes similares; shrinkage automático para regimes com poucos dados
- [ ] Ω-T26: BayesianChangepointDetector — posterior sobre run length muda quando drift detectado; mais robusto que métodos frequentistas para séries curtas
- [ ] Ω-T27: CredibleIntervalCalculator — intervalos de 95% para TODA estimativa; largura do intervalo = medida de incerteza epistêmica

### Tópico 1.4 — Decision State Machine (Ω-T28 a Ω-T36)
- [ ] Ω-T28: DecisionStates — estados: IDLE → OBSERVING → SIGNAL_DETECTED → CONFLUENCE_CHECK → VALIDATION → RISK_CHECK → READY_TO_ENTER → ENTERED → MANAGING → EXITING → EXITED → POST_TRADE_ANALYSIS
- [ ] Ω-T29: GuardFunctions — cada transição tem guard function que deve retornar True; guards verificam invariantes antes de permitir transição
- [ ] Ω-T30: TimeoutHandler — cada estado tem timeout máximo; timeout sem progresso → rollback para estado estável (IDLE ou MANAGING)
- [ ] Ω-T31: StateObservability — cada estado emite métricas específicas (latência no estado, contagem de ciclos, taxa de transição)
- [ ] Ω-T32: EmergencyTransitions — transições de emergência que bypassam guards normais: circuit breaker → force exit → shutdown
- [ ] Ω-T33: StateHistoryTracker — histórico completo de transições com timestamp para reconstrução causal de qualquer decisão
- [ ] Ω-T34: ConcurrentDecisionLimiter — máximo N decisões ativas simultâneas; evita sobre-posição que causa correlação não calculada
- [ ] Ω-T35: DecisionIdempotency — cada decisão tem unique ID; re-executar mesma decisão = no-op (idempotente por design)
- [ ] Ω-T36: StateReconciliation — a cada 10s, reconciliar estado interno com estado externo (posições na exchange); discrepância → alert + correção

### Tópico 1.5 — Regime-Aware Routing (Ω-T37 a Ω-T45)
- [ ] Ω-T37: RegimeClassifier — classifica regime atual em ≥20 estados (trending strong/weak up/down, ranging tight/wide, choppy, flash crash, etc)
- [ ] Ω-T38: RegimeTransitionPredictor — prevê transição de regime 5-30s antes via critical slowing down (autocorrelação ↑ + variância ↑)
- [ ] Ω-T39: RegimeStrategyRouter — cada regime tem estratégia ótima associada; trending → trend-follow, ranging → mean-reversion, choppy → NO TRADE
- [ ] Ω-T40: RegimeParameterSets — parâmetros diferentes para cada regime (thresholds, sizing multipliers, hold times); swap instantâneo ao mudar regime
- [ ] Ω-T41: RegimeConfusionMatrix — acompanha acurácia de classificação por par de regimes; confusão frequente entre dois regimes → merge ou feature engineering
- [ ] Ω-T42: RegimeEdgeDecayMonitor — edge de cada estratégia decai a taxa diferente por regime; edge decay accelerate → alerta re-calibração
- [ ] Ω-T43: CrossAssetRegimeCascade — regime change em BTC propaga para ETH com delay; mapear cascata cross-asset para antecipar
- [ ] Ω-T44: RegimeUnknownHandler — quando modelo não tem confiança em nenhum regime conhecido → estado Regime Unknown → NO TRADE (operar em regime desconhecido = gambling)
- [ ] Ω-T45: RegimeAdaptationSpeed — mede tempo between regime change e adaptação completa do sistema; meta < 5s; tracking contínuo

### Tópico 1.6 — Decision Output Formatter (Ω-T46 a Ω-T54)
- [ ] Ω-T46: TradeSignal — output tipado com: direction, entry_price, stop_loss, take_profit, size, confidence, reasoning, regime, timestamp, trace_id
- [ ] Ω-T47: RationaleGenerator — gera explicação human-readable para cada decisão: "Long BTC @ $X porque: regime trending-up (85%), order flow bullish, confluência 8/10"
- [ ] Ω-T48: AlternativesLogger — loga alternativas consideradas e por que foram rejeitadas: "Short rejeitado: regime não compatível (22% confiança)"
- [ ] Ω-T49: RiskDisclosure — output contendo risco explícito do trade: max loss esperado, probabilidade de stop, drawdown potencial
- [ ] Ω-T50: ExitPlanGenerator — antes de entrar, gera plano de saída completo: triggers de saída, condições de trailing, time-based exit, invalidation
- [ ] Ω-T51: DecisionCheckpoint — serializa estado completo da decisão para replay/debug; input snapshot + scores + pipeline results + output
- [ ] Ω-T52: PriorityEncoder — classifica trade信号 por prioridade (A+ / A / B / C) que determina agressividade de execução e sizing
- [ ] Ω-T53: SignalPublishing — publica TradeSignal via pub-sub para execution layer; delivery guarantee at-least-once com dedup por signal_id
- [ ] Ω-T54: DecisionLatencyBudget — mede tempo total de data→signal; budget < 3ms p99; breach → degrade gracefully (simplificar pipeline)

---

## CONCEITO 2: RISK MANAGEMENT — KINETIC RISK ENGINE (Ω-T55 a Ω-T108)

### Tópico 2.1 — Kelly Criterion Bayesian Sizing (Ω-T55 a Ω-T63)
- [ ] Ω-T55: BayesianKellyEstimator — f* = E[b·p - q | dados] com posterior Beta(α,β) para p (win rate) e Gamma para b (payoff ratio)
- [ ] Ω-T56: FractionalKelly — quarter-Kelly (f*/4) como default; fração adaptada por regime (mais conservador em caudas pesadas)
- [ ] Ω-T57: KellyUncertaintyAdjuster — incerteza na estimativa de edge reduz sizing: sizing = Kelly × (1 - CV(edge)) onde CV = coeficiente de variação
- [ ] Ω-T58: MultiAssetKelly — Kelly estendido para portfólio correlacionado; sizing leva em conta correlações dinâmicas entre ativos
- [ ] Ω-T59: DrawdownAdjustedKelly — Kelly reduzido proporcionalmente ao drawdown atual; DD > 1% → sizing halved; DD > 2% → sizing quartered
- [ ] Ω-T60: KellyVsCvarOptimizer — sizing = min(Kelly, CVaR_budget) onde CVaR_99.5 limita tamanho máximo por risco de cauda
- [ ] Ω-T61: KellyDecayMonitor — tracking contínuo de Kelly ótimo vs Kelly usado; divergência persistente → recalibrar estimativas de edge
- [ ] Ω-T62: KellyRegimeWeights — Kelly diferente por regime; regime com win rate mais incerto → Kelly mais conservador automaticamente
- [ ] Ω-T63: AntiGambler — hard cap absolute de sizing (nunca > 25% Kelly full); previne over-betting em estimativas infladas

### Tópico 2.2 — Circuit Breaker System (Ω-T64 a Ω-T72)
- [ ] Ω-T64: SevenLevelCircuitBreaker — Verde (normal) → Amarelo (reduzir 30%) → Laranja (reduzir 60%) → Vermelho (pausa 5min) → Crítico (fechar tudo) → Emergência (shutdown) → Catastrófico (shutdown + hedge tail)
- [ ] Ω-T65: DrawdownCircuitBreaker — trigger principal = drawdown % do capital; thresholds calibrados para regras FTMO se aplicável
- [ ] Ω-T66: ConsecutiveLossBreaker — N perdas consecutivas → pausa automática; N adaptativo por regime (mais perdas em choppy = OK, em trending = problema)
- [ ] Ω-T67: VolatilityCircuitBreaker — vol instantânea > threshold extremo → NO TRADE; mercado em flash crash = execução quality unpredictable
- [ ] Ω-T68: LatencyCircuitBreaker — latência p99 > 2x média → reduzir exposição; alta latência = slippage imprevisível
- [ ] Ω-T69: DataQualityCircuitBreaker — dados corruptos, gaps, ou fonte offline → pausa até qualidade restaurada
- [ ] Ω-T70: AutoRecoveryProtocol — após trigger, sistema entra em cooldown; re-ativação gradual: paper trade → 25% sizing → 50% → 100%
- [ ] Ω-T71: CircuitBreakerMetrics — tracking de frequência e duração de triggers; triggers frequentes = sistema mal calibrado ou mercado hostil
- [ ] Ω-T72: FTMOComplianceLayer — constraints de prop firm (daily loss, total loss) como circuit breakers adicionais com margem de segurança 20%

### Tópico 2.3 — Position Risk Monitor (Ω-T73 a Ω-T81)
- [ ] Ω-T73: RealTimePnLTracker — P&L atualizado a cada tick com marcação a mercado; unrealized + realized separados
- [ ] Ω-T74: PositionConcentrationMonitor — max % do capital em um único trade; max % em trades correlacionados
- [ ] Ω-T75: DrawdownTracker — peak-to-trough drawdown em tempo real; tracking por trade, por dia, por semana, total
- [ ] Ω-T76: VaRCalculator — Value at Risk (99%) calculado via método histórico e paramétrico; máximo VaR como % do capital
- [ ] Ω-T77: CVaRTracker — Conditional VaR (expected loss dado VaR breach) via GPD (Generalized Pareto Distribution) para caudas pesadas
- [ ] Ω-T78: CorrelationMonitor — correlação entre posições abertas em tempo real via DCC-G近似; correlação crescente → risco de portfolio aumenta
- [ ] Ω-T79: LeverageTracker — alavancagem efetiva total; limite absoluto de alavancagem configurável
- [ ] Ω-T80: FundingCostTracker — custo acumulado de funding para posições open; funding adverso prolongado → sinal de saída
- [ ] Ω-T81: ExposureDashboard — visão consolidada de toda exposição: por direção, por ativo, por estratégia, por regime

### Tópico 2.4 — Dynamic Stop & Exit Engine (Ω-T82 a Ω-T90)
- [ ] Ω-T82: AdaptiveStopLoss — stop baseado em ATR × multiplicador por regime; trending: stop mais largo, ranging: stop mais apertado
- [ ] Ω-T83: TrailingStopAccelerator — trail distance tighten à medida que target se aproxima; gain lock-in progresivo
- [ ] Ω-T84: TimeBasedExit — se trade não atingiu target em T seconds (função de regime e ATR), sinal provavelmente fraco → exit
- [ ] Ω-T85: SignalInvalidationChecker — condição/original rationale do trade mudou? → exit imediato independente de P&L
- [ ] Ω-T86: RegimeChangeExit — regime mudou durante o trade? (trending → ranging) → reavaliar; se regime novo é adverso → exit
- [ ] Ω-T87: CounterSignalExit — sinal oposto apareceu com força significativa → exit e possivelmente inverter
- [ ] Ω-T88: EmergencyExit — condição de mercado adversa: flash crash, spread widening extremo, liquidity evaporation → exit market
- [ ] Ω-T89: PartialExitEngine — sair parcialmente em níveis predeterminados (50% no TP1, 25% no TP2, trail no restante)
- [ ] Ω-T90: ExitConfidenceScorer — cada trigger de saída tem confiança; múltiplos triggers concordando → exit mais urgente

### Tópico 2.5 — Tail Risk Protection (Ω-T91 a Ω-T99)
- [ ] Ω-T91: TailRiskDetector — detecta condições precursoras de tail events: skewness extremo, kurtosis exploding, correlation breakdown
- [ ] Ω-T92: EVTModel — Extreme Value Theory via GPD fitting nos retornos extremos; estima probabilidade de eventos além do observado
- [ ] Ω-T93: HedgeAllocator — 1-3% do capital em positions de tail hedge (puts, shorts distantes); custo do hedge = seguro permanente
- [ ] Ω-T94: StressTestEngine — simula portfólio under cenários de stress: flash crash, liquidation cascade, exchange downtime
- [ ] Ω-T95: LiquidationCascadePredictor — mapear clusters de liquidação; preço perto de cluster → risco de cascata → reduzir exposição
- [ ] Ω-T96: GapRiskAssessor — risco de gap (preço salta stop) estimado por: liquidez, volatilidade, horário, eventos
- [ ] Ω-T97: BlackSwanPreparer — sistema sempre preparado para evento de 10σ+: posição mínima, stops garantidos, circuit breakers armados
- [ ] Ω-T98: RecoveryPathPlanner — após grande perda, plano de recovery calibrado: sizing adaptativo, setups de ultra-alta confiança优先
- [ ] Ω-T99: InsuranceFund — reserva de capital separada (5% do total) nunca arriscada em trades; usada apenas para sobreviver seqüência de perdas

### Tópico 2.6 — Portfolio Risk Optimizer (Ω-T100 a Ω-T108)
- [ ] Ω-T100: PortfolioVarianceDecomposição — decompor variância do portfólio em contribuição de cada posição; identificar maiores contribuidores de risco
- [ ] Ω-T101: RiskParityAllocator — sizing para que cada posição contribua igualmente para risco total; evita concentração de risco oculto
- [ ] Ω-T102: CorrelationMatrixForecast — prever matriz de correlação futura via DCC-GARCH; correlações aumentam em crises → antecipar
- [ ] Ω-T103: ConcentrationRiskMonitor — Herfindahl-Hirschman Index do portfólio; HHI alto = concentração excessiva = risco
- [ ] Ω-T104: FactorExposureCalculator — exposição do portfólio a fatores conhecidos (momentum, value, carry, vol); se α ≈ 0 após controle, não há edge
- [ ] Ω-T105: RiskBudgetAllocator — budget de risco total dividido entre estratégias; cada estratégia tem risco máximo alocado
- [ ] Ω-T106: DrawdownContributionTracker — qual estratégia/trade contribuiu mais para drawdown atual; identificar culpados
- [ ] Ω-T107: OptimalHedgeRatio — para cada exposição direcional, calcular hedge ratio ótima via minimum variance hedge ou delta hedging
- [ ] Ω-T108: CapitalEfficiencyScore — retorno por unidade de capital alocado; estrategias com score baixo → reallocar capital

---

## CONCEITO 3: SHADOW ENGINE & POST-TRADE INTELLIGENCE (Ω-T109 a Ω-T162)

### Tópico 3.1 — Counterfual Simulation Engine (Ω-T109 a Ω-T117)
- [ ] Ω-T109: TimingContrafactual — simular entrada ±1, ±2, ±3, ±5, ±10, ±20 ticks mais cedo/tarde; superfície de performance temporal
- [ ] Ω-T110: ExitContrafactual — simular saída ±0.5s, ±1s, ±2s, ±5s, ±10s, ±30s mais cedo/tarde; superfície de performance de saída
- [ ] Ω-T111: SizingContrafactual — simular com 25%, 50%, 75%, 100%, 125%, 150%, 200% do sizing usado; identificar sizing ótimo ex-post
- [ ] Ω-T112: TriggerThresholdContrafactual — simular com thresholds ±0.5σ, ±1σ, ±1.5σ, ±2σ diferentes; calibrar thresholds ótimos
- [ ] Ω-T113: OrderTypeContrafactual — market → limit, limit → market, IOC → FOK; estimar slippage difference ex-post
- [ ] Ω-T114: PartialExecutionContrafactual — 1 bloco vs 2 parciais vs 3 parciais vs 5 parciais; qual split teria sido melhor
- [ ] Ω-T115: HedgeContrafactual — sem hedge, hedge parcial 25/50/75%, hedge completo; qual hedging strategy teria otimizado resultado
- [ ] Ω-T116: RegimeFilterContrafactual — com vs sem cada filtro de regime; quais filtros são realmente necessários vs overengineering
- [ ] Ω-T117: ContrafactualRepository —存储 todas análises contrafactuais com metadata; consulta por nearest-neighbor para trades futuros similares

### Tópico 3.2 — Post-Trade Forensic Analysis (Ω-T118 a Ω-T126)
- [ ] Ω-T118: Layer1_DataIntegrity — dados de entrada estavam corretos? Gap, delay, corrupção? Root cause se dados errados
- [ ] Ω-T119: Layer2_FeatureComputation — features computadas corretamente? Overflow, underflow, stale data, numerical precision?
- [ ] Ω-T120: Layer3_SignalGeneration — sinal gerado corretamente pelo modelo? Inputs corretos, lógica correta, thresholds aplicados?
- [ ] Ω-T121: Layer4_ConfluênciaEvaluation — confluência avaliada corretamente? Todos os filtros funcionaram? Algum deveria ter rejeitado?
- [ ] Ω-T122: Layer5_RegimeContext — regime identificado corretamente? Se mudou durante trade, foi detectado a tempo?
- [ ] Ω-T123: Layer6_RiskAssessment — risco avaliado corretamente? Sizing adequado? Stop adequado para vol do momento?
- [ ] Ω-T124: Layer7_ExecutionQuality — execução de qualidade? Slippage dentro do esperado? Latência aceitável? Fill rate?
- [ ] Ω-T125: Layer8_ExitLogic — saída executada corretamente? Triggers funcionaram? Algum deveria ter disparado antes?
- [ ] Ω-T126: Layer9_MarketCondition — condição era genuinamente adversa (flash crash, manipulação) ou era previsível com dados disponíveis?

### Tópico 3.3 — Root Cause & Patch System (Ω-T127 a Ω-T135)
- [ ] Ω-T127: RootCauseClassifier — classifica causa raiz em categorias: data, model, parameter, regime, execution, market_structure, unknown
- [ ] Ω-T128: PatchProposalEngine — para cada causa raiz identificada, propõe patch cirúrgico específico; não banda genérica mas correção exata
- [ ] Ω-T129: PatchImpactEstimator — estima impacto do patch proposto via simulação em dados históricos; patch que melhora ≥ X% → aprovar
- [ ] Ω-T130: PatchValidationPipeline — 47 variantes do patch testadas em 50 trades paper validation; requer Sharpe improvement e no regression
- [ ] Ω-T131: DeployWithMonitoring — patch deployado com monitoramento intensivo por 100 trades; regressão detectada → rollback automático
- [ ] Ω-T132: PostMortemArchiver — post-mortem permanente arquivado no Knowledge Graph; NUNCA o mesmo bug causa outra perda
- [ ] Ω-T133: PatternMatcher — novo trade perdedor → buscar no arquivo post-mortems similares; match encontrado → aplicar lição aprendida
- [ ] Ω-T134: RecurrencePrevention — check contra arquivo de post-mortems ANTES de cada trade; trade similar a precedente perdedor → veto ou sizing reduzido
- [ ] Ω-T135: LearningRateTracker — velocidade de aprendizado do sistema: tempo entre bug discovery e patch deployado; meta: decrescente

### Tópico 3.4 — Performance Attribution (Ω-T136 a Ω-T144)
- [ ] Ω-T136: SignalAttribution — quanto do P&L vem de cada sinal individualmente; sinais com contribuição negativa → investigar e possivelmente desativar
- [ ] Ω-T137: RegimeAttribution — quanto do P&L vem de cada regime; desempenho por regime revela onde edge existe e onde não existe
- [ ] Ω-T138: ExecutionAttribution — custo de execução vs alpha bruto; se TCE > 50% do gross alpha, otimização de execução > otimização de sinal
- [ ] Ω-T139: TimingAttribution — quanto do P&L é timing de entrada vs timing de saída vs direção correta; decomposição de valor
- [ ] Ω-T140: LuckVsSkillDecomposição — decompor retornos em componente sistemático (skill/edge) e estocástico (sorte); sorte alta → mean-revert esperado
- [ ] Ω-T141: InformationRatioTracker — IR = (return_atribuído_ao_sinal) / (tracking_error); IR alto = sinal consistente, IR baixo = inconsistente
- [ ] Ω-T142: DecayAttribution — edge decay decomposto em: modelo desatualizado, mercado adaptado, dados degradados, parâmetros stale
- [ ] Ω-T143: OpportunityCostTracker — P&L de trades rejeitados que teriam sido lucrativos (Rejected-Wrong) vs prejuízo evitado (Rejected-Right)
- [ ] Ω-T144: SharpeDecomposição — decompor Sharpe em: win rate contribution, payoff ratio contribution, frequency contribution; identificar bottleneck

### Tópico 3.5 — Adaptive Meta-Learning (Ω-T145 a Ω-T153)
- [ ] Ω-T145: OnlineLearningIncremental — modelos atualizados com cada novo trade; exponential decay (dados recentes pesam mais) sem re-treinamento completo
- [ ] Ω-T146: ConceptDriftDetector — Page-Hinkley, ADWIN, DDM, KSWIN, Fisher's Exact, Bayesian Online Changepoint; ensemble de detectores
- [ ] Ω-T147: MetaLearner — ajusta velocidade de adaptação por parâmetro: alta variância → adaptação rápida, baixa variância → adaptação lenta
- [ ] Ω-T148: MultiArmedBanditAllocator — Thompson Sampling com Beta priors para win rate de cada estratégia; aloca capital para estratégia com maior E[return]
- [ ] Ω-T149: StrategyPoolManager — pool de estratégias ativas; novas estratégias entram via exploration, antigas saem via underperformance
- [ ] Ω-T150: AutoCalibrationScheduler — recalibração automática de parâmetros quando drift detectado; schedule adaptativo por parâmetro
- [ ] Ω-T151: ParameterStabilityMonitor — tracking de estabilidade de cada parâmetro; parâmetros que mudam frequentemente → instáveis → investigar
- [ ] Ω-T152: ModelVersioningTracker — cada versão do modelo versionada com performance; rollback para versão anterior se nova versão underperform
- [ ] Ω-T153: AutonomousVsHumanApprovalRouter — ajustes paramétricos são autônomos; mudanças estruturais escaladas para aprovação do CEO

### Tópico 3.6 — Communication & Telemetry (Ω-T154 a Ω-T162)
- [ ] Ω-T154: DecisionTelemetry — cada decisão emite evento JSON estruturado com trace_id, span_id, inputs, scores, output, timestamp em microssegundo
- [ ] Ω-T155: ConfidenceBroadcast — confiança de cada decisão broadcast para dashboard e execution layer; confidence determina agressividade de execução
- [ ] Ω-T156: AlertHierarchy — INFO (log only) → WARNING (notification) → ERROR (alert) → CRITICAL (alert + action) → FATAL (all channels + shutdown)
- [ ] Ω-T157: RealTimeDashboardData — feed de dados para dashboard: P&L, open positions, signal status, confidence, regime, circuit breaker level
- [ ] Ω-T158: TradeSummaryGenerator — resumo de cada trade closed: direction, entry, exit, P&L, R:R, confidence pre/post, lessons learned
- [ ] Ω-T159: DailyReportEngine — daily report automático: trades do dia, P&L, win rate, drawdown, regime changes, system health, insights
- [ ] Ω-T160: AnomalyDetectionPreImpact — detecta anomalias em métricas do sistema ANTES de impacto financeiro: latência, error rate, throughput
- [ ] Ω-T161: DistributedTracingIntegration — integração com tracing distribuído; cada trade trace completo do data ingestion ao post-trade analysis
- [ ] Ω-T162: KnowledgeGraphUpdater — cada decisão, trade, insight atualiza o Knowledge Graph; monotonicamente crescente, nunca perde informação

---

## IMPLEMENTATION PLAN

### Diretórios:
```
core/decision/__init__.py
core/decision/omega_types.py       — Tipos de decisão (Signal, Trade Signal, Confluence Result)
core/decision/trinity_core.py      — Core decision engine (Tópico 1.1-1.6)
core/decision/kinetic_risk.py       — Risk management engine (Tópico 2.1-2.6)
core/decision/shadow_engine.py      — Counterfactual & post-trade analysis (Tópico 3.1-3.3)
core/decision/meta_learning.py      — Adaptive meta-learning (Tópico 3.5)
core/decision/telemetry.py          — Communication & telemetry (Tópico 3.6)
core/decision/performance.py        — Performance attribution (Tópico 3.4)
```

### Testes:
```
tests/test_trinity_core.py         — Vértices Ω-T01 a Ω-T54 (54 testes)
tests/test_kinetic_risk.py         — Vértices Ω-T55 a Ω-T108 (54 testes)
tests/test_shadow_engine.py        — Vértices Ω-T109 a Ω-T162 (54 testes)
```

### Dicionário SED:
```
dictionaries/decision_sed.md       — SED completo do módulo Decision
```

---

**TOTAL: 3 Conceitos × 6 Tópicos × 9 Vetores = 162 VETORES**
