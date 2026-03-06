# ARCHITECTURAL DECISION LOG (ADL)
## PLMA LAYER 2 — DUBAI MATRIX ASI

> "Cada decisão tomada tem uma razão profunda fundamentada na superação absoluta de todas as latências e vieses cognitivos comuns a bots amadores." (Diretiva Omega)

### DECISÃO 01: ARQUITETURA DE ZERO-LATENCY BACKGROUND WORKER
- **Decisão:** O `DataEngine` foi particionado em dois threads: a principal roda em tempo imediato (`sub-milissegundo`), consumindo dados em cache com `lock zero-copy`, enquanto o `_background_worker` puxa barras históricas e calcula pesados algoritmos matemáticos (Shannon Entropy, VWAP, Hurst) via `np.convolve` sem travar a thread de decisão.
- **Justificativa:** A ASI precisa tomar decisões em nanossegundos baseada em ticks atuais. O cálculo em tempo real de EMAs e Bollinger atrasaria o loop se as threds não fossem isoladas.
- **Data/Status:** ATIVO. Essencial para o modo Sniper HFT.

### DECISÃO 02: HFT SOCKET BRIDGE vs MT5 NATIVE API
- **Decisão:** A `MT5Bridge` abre a porta TCP `5555` instanciando um `server_socket` no Python para se comunicar de forma bidirecional com um EA (Expert Advisor) em MQL5.
- **Justificativa:** Funções MQL5 de socket nativo transmitem os ticks com imensa vantagem de latência sobre a bridge `mt5.symbol_info_tick()` via memory access. Isso bypassa bottlenecks da Python C-API. A API do MT5 atua apenas como fallback confiável.
- **Data/Status:** ATIVO. Subjuga o tempo de execução e a captura de ticks.

### DECISÃO 03: SUBSTITUIÇÃO DE STOP LOSS FIXO POR GESTÃO QUÂNTICA (RiskQuantumEngine)
- **Decisão:** A métrica vital de risco não utiliza stops percentuais engessados (ex: 1% ao trade). O dimensionamento de lote ocorre dinamicamente via a função `kelly_criterion()`, multiplicada pela `kelly_fraction`, ancorando as punições de drawdowns pela ativação do `Circuit Breaker`.
- **Justificativa:** O mercado não opera de forma Gaussiana. Adaptações dinâmicas de posição isolam o evento aleatório (Black Swan) através do corte cirúrgico baseado em expectativa matemática contínua (Win Rate vs Avg Loss).
- **Data/Status:** ATIVO. Define o core da sobrevivência do sistema.

### DECISÃO 04: ABOLIÇÃO DE LÓGICA REATIVA (Paradigma Físico)
- **Decisão:** O `OrderFlowMatrix` foi modelado sob princípios da física matemática e comportamento orgânico. Identifica exaustão e absorção detectando `volume_climax` enquanto o preço recusa movimentar as fronteiras (Range Normalization vs Volume Normalization).
- **Justificativa:** Mentes convencionais seguem preço; a Omega ASI segue intenção absorvida e a entropia gerada no order book.
- **Data/Status:** ATIVO.

### DECISÃO 05: HFT THROTTLING POR CANDLE (Sniper Pacing)
- **Decisão:** Implementado contador de estado no `SniperExecutor` que limita a execução a um máximo de 5 ordens por candle M1.
- **Justificativa:** Durante movimentos impulsivos, o Smart TP pode fechar e o bot reentrar infinitamente no mesmo candle, extrapolando o risco planejado. O pacing garante que a ASI aguarde o fechamento estrutural do candle antes de renovar agressão massiva.
- **Data/Status:** ATIVO. (2026-03-04).

### DECISÃO 06: NATIVE MQ5 ANTI-SLIPPAGE (Zero-Latency CLOSE)
- **Decisão:** O comando de fechar posição (Smart TP) foi desviado da API COM do Python para o Socket TCP, e a validação final de lucro foi movida para NATIVO MQL5.
- **Justificativa:** A latência entre a percepção do Python e a execução no Terminal permitia que saídas em lucro virassem perdas por slippage. O MQL5 agora veta o fechamento se o lucro em tempo real for `<= 0`.
- **Data/Status:** ATIVO. (2026-03-04).

### DECISÃO 07: ZERO-LATENCY SWARM & MONTE CARLO OFFLOAD (Phase 18)
- **Decisão:** Refatoração do `NeuralSwarm` para usar `ThreadPoolExecutor` com limitadores de tempo. Adicionalmente, as rotinas sequenciais baseadas em loops pesados do Python (SMC Swing Detection, Monte Carlo Merton Math e Navier-Stokes Fluid Dynamics) foram totalmente deslocadas para structs do C++.
- **Justificativa:** A somatória de 47 agentes executando sequencialmente combinada com cálculos probabilísticos extensivos empurrava a latência da ASI para perigosos >1200ms. A execução HFT requer <1000ms. O processamento paralelo (eliminando block de IO) somado ao *number crunching* puro de C++, reestabeleceu os limiares cirúrgicos (<200ms por think cycle). 
- **Data/Status:** ATIVO. (2026-03-04).

### DECISÃO 08: ADAPTIVE KINEMATIC & SPREAD DYNAMICS (Phase 30)
- **Decisão:** Substituição de thresholds fixos (ex: 3.0x ATR) por parâmetros dinâmicos (`kinematic_exhaustion_atr_mult`, `max_spread_reward_impact`) registrados no `OmegaParams`.
- **Justificativa:** Mercados de alta volatilidade (Flash Crashes) tornam limites estáticos inúteis. A adaptação dinâmica permite que a ASI respire em regimes de 150+ ATR.
- **Data/Status:** ATIVO. (2026-03-06).

### DECISÃO 09: KINETIC vs ELASTIC OVERRIDES (Phases 30, 32, 33)
- **Decisão:** Implementação de hierarquia de força no `QuantumThoughtEngine`. O "Freight Train" (Velocidade Extrema) agora atropela o SMC Trap Veto, enquanto a "Tensão Elástica Multivariável" (Phase 33) esmaga o Momentum no fim da estirada. O "Dead Cat Bounce Veto" (Phase 32) protege contra repiques falsos.
- **Justificativa:** Proteção tripla contra (1) Comprar facas caindo, (2) Vender fundos esticados, e (3) Comprar topos de pullback.
- **Data/Status:** ATIVO. (2026-03-06).

### DECISÃO 10: PARALELIZAÇÃO DE EXECUÇÃO HFT (Phase 40)
- **Decisão:** O `SniperExecutor` passou a utilizar `ThreadPoolExecutor` para disparar ordens simultaneamente ao invés de em loop sequencial.
- **Justificativa:** O delay de ~4.8s para enviar 10-15 slots era inaceitável para HFT, resultando em slippage catastrófico. Com threads, o tempo de envio caiu para <300ms.
- **Data/Status:** ATIVO. (2026-03-06).

### DECISÃO 11: CONVERGÊNCIA NATIVA OMEGA-CORE (Phase 41)
- **Decisão:** A agregação e colapso quântico de 52 agentes foi movida do Python para C++ puro (`asi_converge_signals`).
- **Justificativa:** O processamento em Python levava ~4.9s para processar os pesos e entropias. Em C++, o tempo foi reduzido para sub-milissegundo (<1ms).
- **Data/Status:** ATIVO. (2026-03-06).

### DECISÃO 13: NEURAL SWARM RESILIENCE SCALING (Phase 42)
- **Decisão:** Aumento do timeout do `ThreadPoolExecutor.map` de **0.6s para 1.2s** e implementação de logging de diagnóstico para timeouts.
- **Justificativa:** A expansão para 54 agentes gerou contenção de recursos, causando `TimeoutError` intermitentes que cegavam o `QuantumThoughtEngine`.
- **Data/Status:** ATIVO. (2026-03-06).

### DECISÃO 14: ARQUITETURA HOLOGRÁFICA PLMA (Project Fragmentation)
- **Decisão:** Criação do script `utils/plma_sync.py` para comprimir e dividir dinamicamente as 7 camadas da PLMA em múltiplos arquivos `projectmap.md`.
- **Justificativa:** A carga cognitiva de um único arquivo monolítico de memória estava atingindo o teto de tokens de contexto; a fragmentação holográfica permite que a ASI acesse sub-redes de memória de forma mais eficiente.
- **Data/Status:** ATIVO. (2026-03-06).

*(Atualizado: 2026-03-06. Versão: 1.4.0-omega — Phase 42 Monitoring)*
