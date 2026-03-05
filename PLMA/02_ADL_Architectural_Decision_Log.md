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

*(Atualizado: 2026-03-04. Versão: 1.2.0-omega — Phase 18 Integration)*
