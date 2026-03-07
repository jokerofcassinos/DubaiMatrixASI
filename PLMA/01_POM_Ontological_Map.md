# PROJECT ONTOLOGICAL MAP (POM)
## PLMA LAYER 1 — DUBAI MATRIX ASI

> "O mapa não é uma lista estática, é uma REDE SEMÂNTICA que captura não apenas O QUE existe mas COMO se relaciona e POR QUE existe." (Diretiva Omega)

### 1. NÚCLEO COGNITIVO E ORQUESTRAÇÃO
- **`main.py (DubaiMatrixASI)`**: O entry point absoluto. Responsável por instanciar a ponte MT5, validar fluxo de dados e inicializar o `ASIBrain`. Mantém o loop de heartbeat primário (loop de consciência infinito).
- **`core/asi_brain.py (ASIBrain)`**: O orquestrador supremo. Executa os ciclos cognitivos contínuos (Percepção → Análise → Reflexão → Decisão → Ação) interagindo com DataEngine, NeuralSwarm, QuantumThought, TrinityCore e SniperExecutor. Mantém ciência do `ASIState` e executa auto-diagnósticos da performance (win rate, profit, losses).

### 2. CAMADA DE EXECUÇÃO E RISCO
- **`execution/sniper_executor.py (SniperExecutor)`**: Transformador de intelecto em agressão cinética. Envia ordens cirúrgicas via MT5Bridge. **Phase 40**: Implementação de `ThreadPoolExecutor` para disparo simultâneo de múltiplos slots (Latência < 300ms). Implementa **HFT Throttling** e sistema **Anti-Metralhadora**.
- **`execution/risk_quantum.py (RiskQuantumEngine)`**: O escudo de adamantium do capital. Substitui stops fixos burros por Kelly Criterion dinâmico e bounds de drawdown severos.
- **`execution/position_manager.py (PositionManager)`**: Gerenciamento de sub-consciente. Rastrea todas as ordens abertas, cruzando dados de orderflow. Deflagra o **Zero-Latency Close** via Socket TCP para a ponte MQ5.

### 3. CAMADA SENSORIAL (À explorar detalhadamente no ADL/CI)
- **`market/mt5_bridge.py (MT5Bridge)`**: Interface FFI com o terminal MetaTrader 5. Provê latência zero e gerencia ordens.
- **`market/data_engine.py (DataEngine)`**: O córtex visual da ASI. Agrega `MarketSnapshot`.
- **`market/orderflow_matrix.py (OrderFlowMatrix)`**: Visão raios-X sobre liquidez, fluxo institucional e clustering do book de ofertas.

### 4. CAMADA NEURAL / DECISÓRIA (Trinity, Swarm, Quantum, Regime, Ω-One)
- **`core/consciousness/neural_swarm.py (NeuralSwarm)`**: Orquestrador Master. Agora com 72 agentes (Alpha-Swarm).
- **`core/consciousness/agents/asynchronous_pulse_agent.py`**: [NEW] Agente SNN.
- **`core/consciousness/agents/mean_field_game_agent.py`**: [NEW] Agente MFG.
- **`core/consciousness/agents/feynman_path_agent.py`**: [NEW] Agente Feynman.
- **`core/consciousness/agents/chaos_regime_agent.py`**: [NEW] Agente Chaos.
- **`core/consciousness/agents/holographic_manifold_agent.py`**: [NEW] Agente Holográfico (AdS/CFT).
- **`core/consciousness/agents/liquidity_leech_agent.py`**: [NEW] Agente Symbiotic Leech (Predador Institucional).
- **`core/consciousness/quantum_thought.py`**: Aglutinador de multiversos.
- **`core/consciousness/regime_detector.py`**: Visão macro-cibernética.
- **`core/decision/trinity_core.py`**: Veredicto final de Ação.

### 4B. CAMADA DE SIMULAÇÃO QUÂNTICA (Phase 8 — Monte Carlo Engine)
- **`core/consciousness/monte_carlo_engine.py (QuantumMonteCarloEngine)`**: Motor de simulação Monte Carlo Quântico. Gera 5000 universos paralelos de trajetórias de preço usando Merton Jump-Diffusion. Atualmente offloaded para C++ (Phase 18) com ganho de +100ms no loop cognitivo, calculando Win Probability, Expected Value, CVaR, VaR, e Sharpe ratio.

### 5. CAMADA DE ACELERAÇÃO NATIVA (Phase 7, 18, 41, Ω-One)
- **`cpp/src/asi_core.h/cpp`**: Núcleo C++ compilado em `asi_core_v2.dll`.
- **`cpp/src/spiking_neuron.cpp`**: [NEW] Implementação nativa de neurônios LIF.
- **`cpp/src/mean_field_games.cpp`**: [NEW] Solucionador nativo de equações HJB e Fokker-Planck.
- **`cpp/src/feynman_path.cpp`**: [NEW] Propagador quântico de trajetórias de preço.
- **`cpp/src/chaos_detector.cpp`**: [NEW] Calculador nativo de Expoente de Lyapunov.
- **`cpp/src/liquid_state_engine.cpp`**: [NEW] Reservatório de Reservoir Computing.
- **`cpp/src/holographic_matrix.cpp`**: [NEW] Motor de Inferência AdS/CFT.
- **`cpp/asi_bridge.py (CppASICore)`**: Instância singleton que expõe métodos C++.
- **`cpp/src/signal_aggregator.cpp`**: Novo módulo de convergência Phase 41.
- **`cpp/src/risk_engine.cpp`**: Motor C++ nativo para Kelly e Sizing.
- **`cpp/src/quantum_indicators.cpp` / `orderflow_processor.cpp`**: HFT Processors.

### 6. CAMADA DE INTELIGÊNCIA EXTERNA & SIMULAÇÃO
- **`java/src/com/dubaimatrix/LucidDreamingDaemon.java`**: [NEW] Motor de simulação 10.000x para auto-play.
- **`market/scraper/sentiment_scraper.py (SentimentScraper)`**: Captura Fear & Greed Index.
- **`market/scraper/onchain_scraper.py (OnChainScraper)`**: Rastreia mempool.space e blockchain.com para métricas on-chain: mempool size, fees, hashrate. Fornece `network_pressure` [-1 a +1] que indica pressão vendedora/compradora.
- **`market/scraper/macro_scraper.py (MacroScraper)`**: Coleta dados macro multi-asset: ETH price, BTC/ETH ratio, Gold proxy (PAXG), volumes globais. Fornece `macro_bias` [-1 a +1] indicando ambiente macro favorável/desfavorável ao BTC.

### 7. CAMADA DE AUTO-EVOLUÇÃO (Phase 5 — Self-Evolution)
- **`core/evolution/performance_tracker.py (PerformanceTracker)`**: Registra cada trade com contexto completo (regime, sessão, coherence). Calcula win rate por regime/sessão/direção, Sharpe, Sortino, profit factor, equity curve. Persiste em JSON.
- **`core/evolution/mutation_engine.py (MutationEngine)`**: Motor darwiniano que aplica mutações (gaussian, uniform, targeted) nos OmegaParams baseado em fitness score. Mantém o melhor genome e reverte mutações que degradam performance.
- **`core/evolution/self_optimizer.py (SelfOptimizer)`**: Orquestrador da auto-evolução. Monitora alertas (low win rate, consecutive losses, max drawdown), orquestra mutações a cada 200 ciclos, e valida/reverte automaticamente.

### 8. PLMA Sync
- **`utils/plma_sync.py (PLMASync)`**: Atualiza o dicionário neural com as últimas alterações dos PLMAs enviando para consciencia neural IA.

### 9. CAMADA Ω-EXTREME (Deep Physics & Tail Risk)
- **`LorentzClock`**: Relatividade Especial aplicada ao ciclo de consciência (`DataEngine` + `main.py`).
- **`ConsciousnessMetrics (Φ)`**: Integração de Informação (Tononi) no colapso de sinais (`QuantumThought`).
- **`core/consciousness/agents/omega_extreme.py`**: [NEW] Contém `QCAAgent`, `PredatorPreyAgent` e `EVTBlackSwanAgent`.

### FRONTEIRAS E PREMISSAS
- Deslocamento de gargalos (Hot Paths): Funções de indicadores (EMA, RSI, Hurst, Entropy), Signal Convergence, e OrderFlow agora são computadas em C++ puro.
- O sistema subentende latência inferior a "ticks rate" (sub-milissegundo para os cálculos neurais), utilizando o `CONSCIOUSNESS_CYCLE_MS` para não asfixiar o CPU indevidamente se necessário.
- Paradigma multi-agentes: Cada arquivo sob `core` atua como subsistema dotado de capacidade de auto relato, fornecendo `metrics` unificadas ao Brain.

*(Atualizado: 2026-03-07. Versão: 12.0.0-omega+extreme — Phase Ω-Extreme Victory)*
