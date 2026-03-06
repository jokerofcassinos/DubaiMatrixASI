# PROJECT ONTOLOGICAL MAP (POM)
## PLMA LAYER 1 — DUBAI MATRIX ASI

> "O mapa não é uma lista estática, é uma REDE SEMÂNTICA que captura não apenas O QUE existe mas COMO se relaciona e POR QUE existe." (Diretiva Omega)

### 1. NÚCLEO COGNITIVO E ORQUESTRAÇÃO
- **`main.py (DubaiMatrixASI)`**: O entry point absoluto. Responsável por instanciar a ponte MT5, validar fluxo de dados e inicializar o `ASIBrain`. Mantém o loop de heartbeat primário (loop de consciência infinito).
- **`core/asi_brain.py (ASIBrain)`**: O orquestrador supremo. Executa os ciclos cognitivos contínuos (Percepção → Análise → Reflexão → Decisão → Ação) interagindo com DataEngine, NeuralSwarm, QuantumThought, TrinityCore e SniperExecutor. Mantém ciência do `ASIState` e executa auto-diagnósticos da performance (win rate, profit, losses).

### 2. CAMADA DE EXECUÇÃO E RISCO
- **`execution/sniper_executor.py (SniperExecutor)`**: Transformador de intelecto em agressão cinética. Envia ordens cirúrgicas via MT5Bridge divididas em múltiplos slots. Implementa **HFT Throttling** (limitador de 5 ordens por candle M1) e sistema **Anti-Metralhadora** (Cooldown, Minimum Price Distance e Directional Conflict Check) para evitar loops de re-entrada suicidas.
- **`execution/risk_quantum.py (RiskQuantumEngine)`**: O escudo de adamantium do capital. Substitui stops fixos burros por Kelly Criterion dinâmico e bounds de drawdown severos. Configurado para **10% Global Risk Cap**.
- **`execution/position_manager.py (PositionManager)`**: Gerenciamento de sub-consciente. Rastrea todas as ordens abertas, cruzando dados de orderflow. Deflagra o **Zero-Latency Close** via Socket TCP para a ponte MQ5.

### 3. CAMADA SENSORIAL (À explorar detalhadamente no ADL/CI)
- **`market/mt5_bridge.py (MT5Bridge)`**: Interface FFI com o terminal MetaTrader 5. Provê latência zero e gerencia ordens.
- **`market/data_engine.py (DataEngine)`**: O córtex visual da ASI. Agrega `MarketSnapshot`.
- **`market/orderflow_matrix.py (OrderFlowMatrix)`**: Visão raios-X sobre liquidez, fluxo institucional e clustering do book de ofertas.

### 4. CAMADA NEURAL / DECISÓRIA (Trinity, Swarm, Quantum, Regime)
- **`core/consciousness/neural_swarm.py (NeuralSwarm)`**: Arquitetura Master. Instancia 52 neurônios interdimensionais (Classic, Omega, Predator, Chaos, Global Macro, Whale, Physics, Kinematics, Behavioral, Game Theory, SMC/ICT, Phase 17: ChartStructure & CandleAnatomy, **Phase 19: Market Dynamics**). Implementa execução concorrente via `ThreadPoolExecutor`, mitigando gargalos sequenciais I/O-bound e NumPy.
- **`core/consciousness/quantum_thought.py (QuantumThoughtEngine)`**: Aglutinador de multiversos. Colapsa a superposição dos agentes num vetor numérico.
- **`core/consciousness/regime_detector.py (RegimeDetector)`**: Visão macro-cibernética sobre onde o mercado se encontra (Choppy, Trend, Squeeze, etc).
- **`core/decision/trinity_core.py (TrinityCore)`**: Veredicto final de Ação (BUY, SELL, WAIT) ouvetando a agressividade dependendo do estado global do sistema. Integra Monte Carlo validation e **Adaptive Kinematic/Spread Vetoes** (Phase 30).

### 4B. CAMADA DE SIMULAÇÃO QUÂNTICA (Phase 8 — Monte Carlo Engine)
- **`core/consciousness/monte_carlo_engine.py (QuantumMonteCarloEngine)`**: Motor de simulação Monte Carlo Quântico. Gera 5000 universos paralelos de trajetórias de preço usando Merton Jump-Diffusion. Atualmente offloaded para C++ (Phase 18) com ganho de +100ms no loop cognitivo, calculando Win Probability, Expected Value, CVaR, VaR, e Sharpe ratio.

### 5. CAMADA DE ACELERAÇÃO NATIVA (Phase 7 — C++ FFI Core)
- **`cpp/src/asi_core.h/cpp`**: Núcleo C++ compilado em DLL carregado na memória via ctypes no Python. Fornece speedup de 100x+ para gargalos matemáticos.
- **`cpp/asi_bridge.py (CppASICore)`**: Instância singleton que auto-descobre a DLL e expõe métodos C++ transparentemente usando numpy arrays (zero-copy overhead reduction).

### 6. CAMADA DE INTELIGÊNCIA EXTERNA (Phase 5 — Web Scrapers Zero-Cost)
- **`market/scraper/sentiment_scraper.py (SentimentScraper)`**: Captura Fear & Greed Index (alternative.me) e dados CoinGecko em background (2min). Fornece `sentiment_score` [-1 a +1] consolidado para os agentes neurais.
- **`market/scraper/onchain_scraper.py (OnChainScraper)`**: Rastreia mempool.space e blockchain.com para métricas on-chain: mempool size, fees, hashrate. Fornece `network_pressure` [-1 a +1] que indica pressão vendedora/compradora.
- **`market/scraper/macro_scraper.py (MacroScraper)`**: Coleta dados macro multi-asset: ETH price, BTC/ETH ratio, Gold proxy (PAXG), volumes globais. Fornece `macro_bias` [-1 a +1] indicando ambiente macro favorável/desfavorável ao BTC.

### 7. CAMADA DE AUTO-EVOLUÇÃO (Phase 5 — Self-Evolution)
- **`core/evolution/performance_tracker.py (PerformanceTracker)`**: Registra cada trade com contexto completo (regime, sessão, coherence). Calcula win rate por regime/sessão/direção, Sharpe, Sortino, profit factor, equity curve. Persiste em JSON.
- **`core/evolution/mutation_engine.py (MutationEngine)`**: Motor darwiniano que aplica mutações (gaussian, uniform, targeted) nos OmegaParams baseado em fitness score. Mantém o melhor genome e reverte mutações que degradam performance.
- **`core/evolution/self_optimizer.py (SelfOptimizer)`**: Orquestrador da auto-evolução. Monitora alertas (low win rate, consecutive losses, max drawdown), orquestra mutações a cada 200 ciclos, e valida/reverte automaticamente.

### 8. PLMA Sync
- **`utils/plma_sync.py (PLMASync)`**: Atualiza o dicionário neural com as últimas alterações dos PLMAs enviando para consciencia neural IA.

### FRONTEIRAS E PREMISSAS
- Deslocamento de gargalos (Hot Paths): Funções de indicadores (EMA, RSI, Hurst, Entropy), Signal Convergence, e OrderFlow agora são computadas em C++ puro.
- O sistema subentende latência inferior a "ticks rate" (sub-milissegundo para os cálculos neurais), utilizando o `CONSCIOUSNESS_CYCLE_MS` para não asfixiar o CPU indevidamente se necessário.
- Paradigma multi-agentes: Cada arquivo sob `core` atua como subsistema dotado de capacidade de auto relato, fornecendo `metrics` unificadas ao Brain.

*(Atualizado: 2026-03-06. Versão: 3.2.0-omega+shield — Phase 34 Integration)*
