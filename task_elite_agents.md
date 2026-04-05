# ⚡ SOLÉNN v2 — TASK: Elite Agents Ω
## Protocolo 3-6-9: Grade Omega Completa (162 Vetores)

| Campo | Valor |
| :--- | :--- |
| **Módulo** | core/agents — Elite Synapse Agents Ω |
| **Conceitos** | 3 × 6 × 9 = 162 vetores |
| **Status** | EM IMPLEMENTAÇÃO |
| **Prioridade** | P1 — Sinais especializados para Decision |
| **Dependências** | Config Ω (pronto), Market Data Ω (pronto) |

---

## CONCEITO 1: MICROSTRUCTURE SIGNALS Ω (Ω-E01 a Ω-E54)

### Tópico 1.1 — Order Flow Intelligence (Ω-E01 a Ω-E09)
- [ ] Ω-E01: VPINCalculator — Volume-synchronized Probability of Informed Trading em janela deslizante
- [ ] Ω-E02: OrderFlowImbalance — (bid_volume - ask_volume) / (bid_volume + ask_volume) por nível
- [ ] Ω-E03: AggressorSideDetector — Lee-Ready tick test para classificar taker buy/sell
- [ ] Ω-E04: TradeSignClassifier — classificação de trades em informed vs uninformed vs noise
- [ ] Ω-E05: FlowToxicityMonitor — quando VPIN > threshold, sinal de flow tóxico → cautela
- [ ] Ω-E06: OrderFlowMomentum — autocorrelação de trade direction em janela curta
- [ ] Ω-E07: QueuePositionTracker — estima posição na fila do best bid/ask
- [ ] Ω-E08: MicropriceCalculator — price-weighted-by-depth estimate do fair price instantâneo
- [ ] Ω-E09: FlowDirectionEntropy — entropia de Lempel-Ziv da sequência trade directions

### Tópico 1.2 — Book Dynamics (Ω-E10 a Ω-E18)
- [ ] Ω-E10: DepthVelocityTracker — taxa de entrada/saída de liquidez por nível
- [ ] Ω-E11: PhantomLiquidityDetector — ordens que cancelam antes de serem hit (liquidity fantasma)
- [ ] Ω-E12: IcebergDetector — refresh patterns com tamanho constante no topo do book
- [ ] Ω-E13: BookPressureGradient — mudança de massa no book: pressure = Σ(level × depth_change)
- [ ] Ω-E14: SpreadDynamics — velocidade do spread, mean-reversion do spread, spread outliers
- [ ] Ω-E15: LiquidityResilienceScore — velocidade de recuperação do book após trade grande
- [ ] Ω-E16: CancelFillAnalyzer — ratio cancel-to-fill por lado como proxy de spoofing/indecisão
- [ ] Ω-E17: BookShapeAnalyzer — classificação da forma do book: flat, steep, wall, gap
- [ ] Ω-E18: HiddenVolumeIndicator — volume executado que não corresponde a ordens visíveis

### Tópico 1.3 — Market Impact & Slippage (Ω-E19 a Ω-E27)
- [ ] Ω-E19: ImpactModel — η(Q/D)^γ calibrado em tempo real via regressão
- [ ] Ω-E20: PassiveVsAggressiveOptimizer — quando ser maker vs taker baseado em cost-benefit
- [ ] Ω-E21: SlippagePredictor — modelo preditivo de slippage f(size, depth, vol, time_of_day)
- [ ] Ω-E22: InformationLeakageDetector — detecta padrões que revelam intenção ao mercado
- [ ] Ω-E23: QueueTheoryAnalyzer — modela fila de ordens como M/M/1 ou M/D/1 para prever fill time
- [ ] Ω-E24: AdverseSelectionProtector — protege contra fills que precedem movimento adverso
- [ ] Ω-E25: TimingOptimizer — melhor horário para execução em cada regime
- [ ] Ω-E26: RandomizationEngine — jitter de timing e sizing para evitar fingerprinting
- [ ] Ω-E27: ExecutionQualityScorer — score composto: slippage + impact + fill rate + latency

### Tópico 1.4 — Spoof Detection (Ω-E28 a Ω-E36)
- [ ] Ω-E28: SpoofPatternDetector — identifica spoofing nível 1: ordens grandes canceladas rapidamente
- [ ] Ω-E29: LayeringDetector — spoofing nível 2: múltiplas ordens em camadas para criar falsa profundidade
- [ ] Ω-E30: MomentumIgnitionDetector — spoofing nível 3: spoof para iniciar momentum seguido de trades reais
- [ ] Ω-E31: SpoofConfidenceScorer — score de confiança do spoofing detectado [0, 1]
- [ ] Ω-E32: SpoofHistoryTracker — histórico de spoofing patterns por exchange e símbolo
- [ ] Ω-E33: ManipulationImpactEstimator — quanto o spoofing afetou o preço
- [ ] Ω-E34: SpoofDirectionPredictor — spoof para cima → preço pode cair depois; spoof para baixo → subir
- [ ] Ω-E35: SpoofFingerprint — padrão identificável de spoof por algoritmo/ator
- [ ] Ω-E36: AntiManipulationSignal — sinal de trade oposto ao spoofing (exploit de manipulação)

### Tópico 1.5 — Volume Profile Analysis (Ω-E37 a Ω-E45)
- [ ] Ω-E37: VolumeProfileBuilder — volume acumulado por faixa de preço em período configurável
- [ ] Ω-E38: ValueAreaCalculator — faixa de preço com 70% do volume (VWAP ± std)
- [ ] Ω-E39: PointOfControlFinder — nível de preço com máximo volume (máxima aceitação)
- [ ] Ω-E40: VolumeNodesDetector — clusters de volume como suportes/resistências naturais
- [ ] Ω-E41: LowVolumeGaps — gaps no volume profile como zonas de transição rápida
- [ ] Ω-E42: VolumeProfileEvolution — como o volume profile muda ao longo do tempo
- [ ] Ω-E43: DeltaVolumeProfile — difference entre volume de compra e volume de venda por nível
- [ ] Ω-E44: CumulativeDelta — delta acumulado como indicador de acumulação/distribuição
- [ ] Ω-E45: VolumeWeightedMomentum — momentum ponderado por volume (high volume moves mais importantes)

### Tópico 1.6 — Liquidity & Spread Signals (Ω-E46 a Ω-E54)
- [ ] Ω-E46: EffectiveSpreadCalculator — 2 × |trade_price - mid_price| como medida real de spread
- [ ] Ω-E47: RealizedSpreadCalculator — spread após considerar impacto de preço
- [ ] Ω-E48: AmihudIlliquidity — |return| / volume como medida de iliquidez
- [ ] Ω-E49: KyleLambda — price impact per unit volume estimado via regressão
- [ ] Ω-E50: RollImplicitSpread — spread implícito via serial covariance de mudanças de preço
- [ ] Ω-E51: MarketQualityIndex — índice composto: spread + depth + resilience + toxicity
- [ ] Ω-E52: LiquidityAbsorptionRate — velocidade de absorção de liquidez no book
- [ ] Ω-E53: DarkPoolProxy — inferência de atividade em dark pools via volume discrepâncias
- [ ] Ω-E54: LiquidityMigrationDetector — quando liquidez migra de um exchange para outro

---

## CONCEITO 2: REGIME & STRUCTURAL SIGNALS Ω (Ω-E55 a Ω-E108)

### Tópico 2.1 — Fractal Analysis (Ω-E55 a Ω-E63)
- [ ] Ω-E55: HurstExponentCalculator — dinâmico via R/S method em janela deslizante
- [ ] Ω-E56: MultifractalSpectrum — espectro multifractal completo via MFDFA
- [ ] Ω-E57: FractalDimensionCalculator — dimensão fractal D = 2 - H
- [ ] Ω-E58: ScalingExponentEstimator — expoentes de escala para diferentes momentos q
- [ ] Ω-E59: MultifractalCoherence — coerência entre espectros de diferentes timeframes
- [ ] Ω-E60: FractalRegimeClassifier — classificar regime por espectro multifractal
- [ ] Ω-E61: ComplexityIndex — complexidade topológica do gráfico de preços
- [ ] Ω-E62: ScaleInvariantFeatures — features invariantes a mudança de escala de preço/volume
- [ ] Ω-E63: CrossScaleCoupling — acoplamento entre escalas temporais (1m ↔ 5m ↔ 15m)

### Tópico 2.2 — Volatility Regime Detection (Ω-E64 a Ω-E72)
- [ ] Ω-E64: VolatilityCone — current vol vs historical percentiles por horizonte
- [ ] Ω-E65: VolCompressionDetector — detectar Bollinger squeeze e volatility contraction
- [ ] Ω-E66: VolExpansionSignal — detectar início de expansão de volatilidade → breakout iminente
- [ ] Ω-E67: VolOfVolCalculator — volatilidade da volatilidade (VVIX equivalente)
- [ ] Ω-E68: VolTermStructureAnalyzer — estrutura temporal de vol implícita (contango/backwardation)
- [ ] Ω-E69: VolSkewDetector — assimetria de vol (put-call asymmetry)
- [ ] Ω-E70: VolRegimeTransitionPredictor — prever transição de regime de volatilidade via CSD
- [ ] Ω-E71: VolMeanReversionSpeed — velocidade de mean-reversion da volatilidade (processo OU)
- [ ] Ω-E72: RoughVolEstimator — rough volatility com H ≈ 0.1

### Tópico 2.3 — Trend & Momentum Signals (Ω-E73 a Ω-E81)
- [ ] Ω-E73: TrendStrengthIndex — R² de regressão linear como medida de força de tendência
- [ ] Ω-E74: MomentumDecayCurve — como o momentum decai ao longo do tempo
- [ ] Ω-E75: TrendSustainabilityScore — tendência é sustentável (volume) ou esgotando?
- [ ] Ω-E76: DivergenceDetector — divergências entre preço e indicadores (RSI, MACD, volume)
- [ ] Ω-E77: TrendReversalPredictor — previsão de reversão de tendência via Lyapunov exponent
- [ ] Ω-E78: AutocorrelationProfile — autocorrelação de retornos em múltiplos lags
- [ ] Ω-E79: HarmonicConvergence — quando múltiplos indicadores técnicos convergem no mesmo sinal
- [ ] Ω-E80: ElliottWaveCounter — contagem automatizada de ondas de Elliott
- [ ] Ω-E81: MarketRegimePersistence — quão persistente é o regime atual (half-life)

### Tópico 2.4 — Statistical Arbitrage Signals (Ω-E82 a Ω-E90)
- [ ] Ω-E82: CorrelationBreakdownDetector — quando correlações históricas quebram
- [ ] Ω-E83: CointegrationTracker — cointegração entre pares de ativos em janela deslizante
- [ ] Ω-E84: PairsTradingSignal — sinal de mean-reversion para pares cointegrados
- [ ] Ω-E85: CrossAssetLeadLag — lead-lag entre ativos cross-market (BTC→ETH, DXY→BTC)
- [ ] Ω-E86: BasisAnomalyDetector — anomalias no basis spot-perpetual
- [ ] Ω-E87: FundingRateArbitrage — oportunidades de carry trade via funding rate
- [ ] Ω-E88: TriangularArbDetector — triangular arbitrage entre 3 pares
- [ ] Ω-E89: CalendarSpreadAnalyzer — spreads entre futuros de diferentes maturidades
- [ ] Ω-E90: StatisticalFairValue — fair value estimado via modelo estatístico vs preço atual

### Tópico 2.5 — Event-Driven Signals (Ω-E91 a Ω-E99)
- [ ] Ω-E91: MacroEventImpactEstimator — impacto estimado de eventos macro (FOMC, CPI, NFP)
- [ ] Ω-E92: LiquidationCascadePredictor — prever cascata de liquidações
- [ ] Ω-E93: FlashCrashEarlyWarning — early warning para flash crash via anomalias de microestrutura
- [ ] Ω-E94: ExchangeDowntimeImpact — impacto de downtime de exchange no preço
- [ ] Ω-E95: WhaleMovementTracker — rastreamento de movimentos de grandes wallets
- [ ] Ω-E96: StablecoinFlowDetector — fluxos de stablecoins in/out de exchanges
- [ ] Ω-E97: OptionsExpiryEffect — efeito de expiração de opções no spot
- [ ] Ω-E98: SessionTransitionSignal — sinais de transição entre sessões (Tokyo→London→NY)
- [ ] Ω-E99: PostEventVolatilityDecay — decaimento de volatilidade pós-evento

### Tópico 2.6 — Network Science Signals (Ω-E100 a Ω-E108)
- [ ] Ω-E100: CorrelationNetworkBuilder — rede dinâmica de correlações entre ativos
- [ ] Ω-E101: CentralityAnalyzer — centralidade (betweenness, eigenvector) de cada ativo na rede
- [ ] Ω-E102: CommunityDetector — comunidades de ativos que movem juntos (Louvain)
- [ ] Ω-E103: SystemicRiskIndicator — distância ao limiar de percolação na rede
- [ ] Ω-E104: ContagionPredictor — prever contágio de um ativo para outro na rede
- [ ] Ω-E105: NetworkRobustnessScore — resiliência da rede a choques
- [ ] Ω-E106: InformationFlowTracker — direção de fluxo de informação entre ativos (transfer entropy)
- [ ] Ω-E107: CascadeDepthPredictor — profundidade estimada de cascata na rede
- [ ] Ω-E108: CrossMarketSpillover — spillover de um mercado para outro (crypto→forex, etc)

---

## CONCEITO 3: ADVANCED QUANT SIGNALS Ω (Ω-E109 a Ω-E162)

### Tópico 3.1 — Information Theory Signals (Ω-E109 a Ω-E117)
- [ ] Ω-E109: ShannonEntropyCalculator — entropia de Shannon da distribuição de retornos
- [ ] Ω-E110: MutualInformationEstimator — I(X;Y) entre features e retorno futuro
- [ ] Ω-E111: TransferEntropyCalculator — Transfer Entropy T(X→Y) para informação direcional
- [ ] Ω-E112: CrossEntropyMonitor — D_KL(P||Q) entre distribuição atual e modelo
- [ ] Ω-E113: ChannelCapacityEstimator — C = B log₂(1+SNR) para limite informacional
- [ ] Ω-E114: RedundancyAnalyzer — redundância entre sinais para feature selection
- [ ] Ω-E115: NoveltyScore — quão "novo" é o estado atual baseado em info theory
- [ ] Ω-E116: InformationDecay — decaimento da informação mútua ao longo do tempo
- [ ] Ω-E117: PredictabilityBound — limite teórico de previsibilidade via data processing inequality

### Tópico 3.2 — Topological Signals (Ω-E118 a Ω-E126)
- [ ] Ω-E118: PersistentHomologyCalculator — diagramas de persistência do order flow
- [ ] Ω-E119: BettiNumbersTracker — β₀ (clusters), β₁ (loops), β₂ (voids) do mercado
- [ ] Ω-E120: TopologySimplificationSignal — simplificação topológica = precursor de movimento forte
- [ ] Ω-E121: EulerCharacteristic — característica de Euler como medida de complexidade
- [ ] Ω-E122: BottleneckDistance — similaridade entre regimes via distância de bottleneck
- [ ] Ω-E123: MapperAlgorithm —_mapper para visualização de estrutura de mercado
- [ ] Ω-E124: TopologicalRegimeClassifier — classificação de regime por invariante topológico
- [ ] Ω-E125: ShapeDescriptor — descritor de forma do order book via TDA
- [ ] Ω-E126: TopologicalAnomalyDetector — anomalias detectadas via persistent outliers

### Tópico 3.3 — Wavelet & Spectral Signals (Ω-E127 a Ω-E135)
- [ ] Ω-E127: WaveletDecomposer — decomposição wavelet db4/db8 com 8-10 níveis
- [ ] Ω-E128: SpectralEnergyTracker — energia espectral por escala temporal
- [ ] Ω-E129: CrossSpectralCoherence — coerência espectral entre timeframes
- [ ] Ω-E130: DominantFrequencyDetector — frequência dominante no order flow
- [ ] Ω-E131: WaveletScalogram — representação tempo-frequência completa
- [ ] Ω-E132: NoiseSeparation — separar sinal de ruído via thresholding wavelet
- [ ] Ω-E133: SpectralChangePointDetector — mudança na composição espectral = regime change
- [ ] Ω-E134: MultiResolutionFeatures — features extraídas em múltiplas resoluções
- [ ] Ω-E135: HarmonicOscillatorModel — modelo de osciladores harmônicos para periodicidades

### Tópico 3.4 — Entropy & Thermodynamics (Ω-E136 a Ω-E144)
- [ ] Ω-E136: MarketTemperatureEstimator — "temperatura" do mercado = intensidade de negociação
- [ ] Ω-E137: FreeEnergyCalculator — energia livre F = U - TS do mercado
- [ ] Ω-E138: EntropyGradient — gradiente de entropia como driving force do mercado
- [ ] Ω-E139: EquilibriumDetector — mercado em equilíbrio termodinâmico (eficiente localmente)
- [ ] Ω-E140: PhaseTransitionPredictor — prever transições de fase via critical slowing down
- [ ] Ω-E141: DissipationRate — taxa de dissipação de energia = fricção do mercado
- [ ] Ω-E142: MaximumEntropyEstimator — máxima entropia = máxima imprevisibilidade
- [ ] Ω-E143: ThermodynamicRegimeClassifier — classificar regime por temperatura/entropia
- [ ] Ω-E144: EnergyReleasePredictor — quando energia acumulada será liberada (explosão)

### Tópico 3.5 — Causal Discovery Signals (Ω-E145 a Ω-E153)
- [ ] Ω-E145: GrangerCausalityTracker — causalidade de Granger entre timeframes e ativos
- [ ] Ω-E146: PCAlgorithm — causal discovery via Conditional Independence tests
- [ ] Ω-E147: CausalDirectionPredictor — quem causa quem: A→B ou B→A?
- [ ] Ω-E148: ConfounderDetector — detectar variáveis confundidoras ocultas
- [ ] Ω-E149: CausalStrengthEstimator — força do efeito causal (intervention effect)
- [ ] Ω-E150: TimeVaryingCausalGraph — grafo causal dinâmico com edge birth/death
- [ ] Ω-E151: CounterfactualCausalEffect — efeito causal contrafactual (do-calculus simplificado)
- [ ] Ω-E152: CausalInnovationDetector — novos edges no grafo causal = inovação estrutural
- [ ] Ω-E153: CausalSignalSelector — selecionar sinais baseado em causalidade, não correlação

### Tópico 3.6 — Meta-Signal Aggregation (Ω-E154 a Ω-E162)
- [ ] Ω-E154: SignalQualityTracker — qualidade de cada sinal: Sharpe, hit rate, decay por regime
- [ ] Ω-E155: EnsembleAggregator — agregar sinais via weighted vote com pesos Bayesianos
- [ ] Ω-E156: SignalDiversityScore — diversidade de sinais → robustez do ensemble
- [ ] Ω-E157: RedundancyEliminator — eliminar sinais redundantemente informativos
- [ ] Ω-E158: SignalHealthMonitor — health check de cada sinal (staleness, divergence, error)
- [ ] Ω-E159: AdaptiveWeighting — pesos dos sinais adaptados via Thompson Sampling
- [ ] Ω-E160: MetaSignalSynthesizer — sintetizar meta-signal a partir de N sub-signais
- [ ] Ω-E161: SignalDecayCurve — curva de decaimento de cada sinal ao longo do tempo
- [ ] Ω-E162: KnowledgeGraphSignalUpdater — cada sinal atualiza o KG com seu performance e conexão

---

## IMPLEMENTATION PLAN

### Diretórios:
```
core/agents/__init__.py
core/agents/orderflow.py         — Microstructure signals (Tópico 1.1-1.6)
core/agents/regime.py            — Regime & structural signals (Tópico 2.1-2.6)
core/agents/quant_signals.py     — Advanced quant signals (Tópico 3.1-3.6)
core/agents/base_synapse.py      — Base synapse interface
core/agents/elite_synapse.py     — Elite synapse adapter
core/agents/signal_aggregator.py — Meta-signal aggregation (Tópico 3.6)
```

### Testes:
```
tests/test_elite_agents.py       — Vértices Ω-E01 a Ω-E162 (todos testados)
```

### Dicionário SED:
```
dictionaries/elite_agents_sed.md  — SED completo do módulo Elite Agents
```

---

**TOTAL: 3 Conceitos × 6 Tópicos × 9 Vetores = 162 VETORES**
