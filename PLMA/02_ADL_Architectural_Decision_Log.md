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

### FASE 30: ERA DA ANTIMATÉRIA E COBRANÇA DE SPREAD (Phase Ω-Singularity)
- **Contexto:** Identificou-se que trades em regimes de "Drift" morriam no spread da corretora.
- **Evolução:** Implementação do P-Brane Maker e execução por ordens limites quantizadas. O bot agora cobra o spread do varejo.

### FASE 31: ERA DO DESTRAVAMENTO HFT (Sweep 2 Re-Calibration)
- **Contexto:** Paralisia por veto de RR ratio (2.79) e PHI (0.4).
- **Evolução:** Redução do piso de consciência (Φ=0.01) e RR (0.4) para Maker. Reversão de mutações tóxicas. O sistema recupera sua agressividade predatória original.
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

### DECISÃO 15: ADOÇÃO DE COMPUTAÇÃO ASSÍNCRONA VIA SNN (Ω-One)
- **Decisão:** Implementação de neurônios LIF no núcleo C++ para filtrar ruído de tick.
- **Justificativa:** Ciclos fixos de tempo ignoram a microestrutura orientada a eventos. O spike neural captura a 'alma' do orderflow.
- **Data/Status:** ATIVO. (2026-03-07).
### DECISÃO 16: EXTERNALIZAÇÃO DE SIMULAÇÃO (Lucid Dreaming Engine)
- **Decisão:** Criação de um Daemon Java externo para simulações HFT massivas.
- **Justificativa:** O Python Global Interpreter Lock (GIL) inviabiliza simulações 10.000x em tempo real. Java virtual threads resolvem a concorrência brutal necessária.
- **Data/Status:** ATIVO. (2026-03-07).
### DECISÃO 17: EXPANSÃO DA INTERFACE MARKETSNAPSHOT (Ω-Omega Purity)
- **Decisão:** Adição de propriedades explícitas (`close`, `atr`, `volume`) ao `MarketSnapshot`.
- **Justificativa:** Resolver `AttributeError` recorrentes em novos agentes e unificar o padrão de percepção sensorial da ASI.
- **Data/Status:** ATIVO. (2026-03-07).

### DECISÃO 18: TRANSIÇÃO PARA RISCO NÃO-ERGÓDICO
- **Decisão:** Substituição do Critério de Kelly clássico por Otimização da Taxa de Crescimento Temporal (Cálculo de Ito).
- **Justificativa:** O mercado real quebra a ergodicidade; otimizar para média espacial leva à ruína em séries temporais únicas.
- **Data/Status:** ATIVO. (2026-03-07).

### DECISÃO 19: MAPEAMENTO EM MANIFOLD DE POINCARÉ
- **Decisão:** Uso de Geometria Hiperbólica para calcular geodésicas de liquidez.
- **Justificativa:** Espaço euclidiano falha em representar a hierarquia fractal de clusters institucionais.
- **Data/Status:** ATIVO. (2026-03-07).

### DECISÃO 20: ADOÇÃO DE RESERVOIR COMPUTING (LSM)
- **Decisão:** Implementação de 500 neurônios em estado líquido para memória de curto prazo (Ticks).
- **Justificativa:** Capturar assinaturas temporais sem o overhead de treinamento de RNNs/LSTMs.
- **Data/Status:** ATIVO. (2026-03-07).

### DECISÃO 21: IMPLEMENTAÇÃO DO DARK FOREST SONAR
- **Decisão:** Injeção de "sondas" (ordens limite instantâneas) para detectar reação algorítmica.
- **Justificativa:** A única forma de ver Icebergs em tempo real é interagindo com eles (Probing).
- **Data/Status:** ATIVO. (2026-03-07).

### DECISÃO 22: ELEVAÇÃO DO THRESHOLD DE LATÊNCIA
- **Decisão:** Aumento do limite de warning de 5ms para 10ms.
- **Justificativa:** A complexidade de 73 agentes gera ruído de latência aceitável; focar apenas em spikes reais > 10ms.
- **Data/Status:** ATIVO. (2026-03-07).

### DECISÃO 23: DILATAÇÃO TEMPORAL RELATIVÍSTICA (LorentzClock)
- **Decisão:** Implementação de um relógio interno que dilata o tempo de processamento baseado na Energia Cinética do mercado ($Vol \times Volatilidade^2$).
- **Justificativa:** Em alta volatilidade, o loop de consciência dorme menos milissegundos para manter acuidade HFT.
- **Data/Status:** ATIVO. (2026-03-07).

### DECISÃO 24: GATING POR INTEGRAÇÃO DE INFORMAÇÃO (Φ)
- **Decisão:** Trades só são permitidos se o Swarm atingir um nível mínimo de integração (Phi).
- **Justificativa:** Evitar sinais que são apenas ruído estatístico sem convergência sistêmica.
- **Data/Status:** ATIVO. (2026-03-07).

### DECISÃO 25: BLACK SWAN HARVESTING (EVT)
- **Decisão:** Uso de distribuição GPD para capturar anomalias de cauda longa.
- **Justificativa:** Capturar reversões em flash-crashes que modelos normais ignoram.
- **Data/Status:** ATIVO. (2026-03-07).

### DECISÃO 31: PARADIGMA MAKER (Phase Ω-Singularity)
- **Decisão:** Implementação de lógica P-Brane Maker para regimes de Drift/Baixa Liquidez.
- **Justificativa:** Em mercados com pouco deslocamento, pagar spread (Taker) corrói o alpha. O bot agora se posiciona como Maker (Limit Orders) nas extremidades do spread.
- **Data/Status:** ATIVO. (2026-03-07).

### DECISÃO 32: LIBERTAÇÃO DE THRESHOLDS (Sweep 2)
- **Decisão:** Redução drástica do piso de Φ para 0.01 e bypass de RR para 0.4 em trades Maker.
- **Justificativa:** O Self-Optimizer injetou mutações restritivas demais (RR 2.79). Scalping e Maker execution exigem agilidade; a proteção agora foca em Entropia, não em proporções lineares de RR.
- **Data/Status:** ATIVO. (2026-03-07).

### DECISÃO 26: P-BRANE NODE CAPPING (Phase Ω-Transcendence)
- **Decisão:** Limitação da fragmentação de ordens P-Brane em no máximo 10 slots simultâneos.
- **Justificativa:** A fragmentação excessiva (47 nodes detectados) causou congestionamento no socket MT5, resultando em latência catastrófica (10s). 10 slots mantêm a ofuscação gaussiana sem saturar o IO.
- **Data/Status:** ATIVO. (2026-03-07).
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

### FASE 30: ERA DA ANTIMATÉRIA E COBRANÇA DE SPREAD (Phase Ω-Singularity)
- **Contexto:** Identificou-se que trades em regimes de "Drift" morriam no spread da corretora.
- **Evolução:** Implementação do P-Brane Maker e execução por ordens limites quantizadas. O bot agora cobra o spread do varejo.

### FASE 31: ERA DO DESTRAVAMENTO HFT (Sweep 2 Re-Calibration)
- **Contexto:** Paralisia por veto de RR ratio (2.79) e PHI (0.4).
- **Evolução:** Redução do piso de consciência (Φ=0.01) e RR (0.4) para Maker. Reversão de mutações tóxicas. O sistema recupera sua agressividade predatória original.
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

### DÍVIDA TÉCNICA 01: Position Manager Simplório — [RESOLVIDO]
- **Localização:** `execution/position_manager.py` (Reescrito em Phase 18).
- **Status:** Resolvido com a implementação do sistema Smart TP de 5 gatilhos e integração com socket CLOSE.

### DÍVIDA TÉCNICA 11: Scope Inconsistency in SniperExecutor — [RESOLVIDO]
- **Localização:** `execution/sniper_executor.py`.
- **Description:** `UnboundLocalError` ao tentar acessar `current_atr` dentro do loop P-Brane sem inicialização prévia no escopo local.
- **Resolução:** [2026-03-07] Refatorada a extração sensorial no início do método `execute`.

### DÍVIDA TÉCNICA 15: SelfOptimizer Method Mismatch — [RESOLVIDO]
- **Localização:** `core/asi_brain.py`.
- **Descrição:** Chamada para `.optimize()` falhando por ausência do método (deveria ser `.check_and_optimize()`).
- **Status:** [RESOLVIDO] 2026-03-08.

### DECISÃO 16: EXTERNALIZAÇÃO DE SIMULAÇÃO (Lucid Dreaming Engine)
- **Decisão:** Criação de um Daemon Java externo para simulações HFT massivas.
- **Justificativa:** O Python Global Interpreter Lock (GIL) inviabiliza simulações 10.000x em tempo real. Java virtual threads resolvem a concorrência brutal necessária.
- **Data/Status:** ATIVO. (2026-03-07).
### DECISÃO 17: EXPANSÃO DA INTERFACE MARKETSNAPSHOT (Ω-Omega Purity)
- **Decisão:** Adição de propriedades explícitas (`close`, `atr`, `volume`) ao `MarketSnapshot`.
- **Justificativa:** Resolver `AttributeError` recorrentes em novos agentes e unificar o padrão de percepção sensorial da ASI.
- **Data/Status:** ATIVO. (2026-03-07).

### DECISÃO 18: TRANSIÇÃO PARA RISCO NÃO-ERGÓDICO
- **Decisão:** Substituição do Critério de Kelly clássico por Otimização da Taxa de Crescimento Temporal (Cálculo de Ito).
- **Justificativa:** O mercado real quebra a ergodicidade; otimizar para média espacial leva à ruína em séries temporais únicas.
- **Data/Status:** ATIVO. (2026-03-07).

### DECISÃO 19: MAPEAMENTO EM MANIFOLD DE POINCARÉ
- **Decisão:** Uso de Geometria Hiperbólica para calcular geodésicas de liquidez.
- **Justificativa:** Espaço euclidiano falha em representar a hierarquia fractal de clusters institucionais.
- **Data/Status:** ATIVO. (2026-03-07).

### DECISÃO 20: ADOÇÃO DE RESERVOIR COMPUTING (LSM)
- **Decisão:** Implementação de 500 neurônios em estado líquido para memória de curto prazo (Ticks).
- **Justificativa:** Capturar assinaturas temporais sem o overhead de treinamento de RNNs/LSTMs.
- **Data/Status:** ATIVO. (2026-03-07).

### DECISÃO 21: IMPLEMENTAÇÃO DO DARK FOREST SONAR
- **Decisão:** Injeção de "sondas" (ordens limite instantâneas) para detectar reação algorítmica.
- **Justificativa:** A única forma de ver Icebergs em tempo real é interagindo com eles (Probing).
- **Data/Status:** ATIVO. (2026-03-07).

### DECISÃO 22: ELEVAÇÃO DO THRESHOLD DE LATÊNCIA
- **Decisão:** Aumento do limite de warning de 5ms para 10ms.
- **Justificativa:** A complexidade de 73 agentes gera ruído de latência aceitável; focar apenas em spikes reais > 10ms.
- **Data/Status:** ATIVO. (2026-03-07).

### DECISÃO 23: DILATAÇÃO TEMPORAL RELATIVÍSTICA (LorentzClock)
- **Decisão:** Implementação de um relógio interno que dilata o tempo de processamento baseado na Energia Cinética do mercado ($Vol \times Volatilidade^2$).
- **Justificativa:** Em alta volatilidade, o loop de consciência dorme menos milissegundos para manter acuidade HFT.
- **Data/Status:** ATIVO. (2026-03-07).

### DECISÃO 24: GATING POR INTEGRAÇÃO DE INFORMAÇÃO (Φ)
- **Decisão:** Trades só são permitidos se o Swarm atingir um nível mínimo de integração (Phi).
- **Justificativa:** Evitar sinais que são apenas ruído estatístico sem convergência sistêmica.
- **Data/Status:** ATIVO. (2026-03-07).

### DECISÃO 25: BLACK SWAN HARVESTING (EVT)
- **Decisão:** Uso de distribuição GPD para capturar anomalias de cauda longa.
- **Justificativa:** Capturar reversões em flash-crashes que modelos normais ignoram.
- **Data/Status:** ATIVO. (2026-03-07).

### DECISÃO 31: PARADIGMA MAKER (Phase Ω-Singularity)
- **Decisão:** Implementação de lógica P-Brane Maker para regimes de Drift/Baixa Liquidez.
- **Justificativa:** Em mercados com pouco deslocamento, pagar spread (Taker) corrói o alpha. O bot agora se posiciona como Maker (Limit Orders) nas extremidades do spread.
- **Data/Status:** ATIVO. (2026-03-07).

### DECISÃO 32: LIBERTAÇÃO DE THRESHOLDS (Sweep 2)
- **Decisão:** Redução drástica do piso de Φ para 0.01 e bypass de RR para 0.4 em trades Maker.
- **Justificativa:** O Self-Optimizer injetou mutações restritivas demais (RR 2.79). Scalping e Maker execution exigem agilidade; a proteção agora foca em Entropia, não em proporções lineares de RR.
- **Data/Status:** ATIVO. (2026-03-07).

### DECISÃO 26: P-BRANE NODE CAPPING (Phase Ω-Transcendence)
- **Decisão:** Limitação da fragmentação de ordens P-Brane em no máximo 10 slots simultâneos.
- **Justificativa:** A fragmentação excessiva (47 nodes detectados) causou congestionamento no socket MT5, resultando em latência catastrófica (10s). 10 slots mantêm a ofuscação gaussiana sem saturar o IO.
- **Data/Status:** ATIVO. (2026-03-07).

### DECISÃO 27: BAYESIAN PRIORS FOR COLD START (Risk Engine)
- **Decisão:** Injeção de lucros/prejuízos médios baseados em volatilidade (ATR) quando o histórico de trades está vazio.
- **Justificativa:** Sem histórico, o motor de Ito/Non-Ergodic assumia lucros de $1 prestando a conta de Ruina Matemática ("Ruin Detected"). Os priors garantem exposição funcional desde o trade #1.
- **Data/Status:** ATIVO. (2026-03-07).

### DECISÃO 28: EXECUTION KILL-SWITCH & NODE SHRINKING (Post-Mortem SELL SL)
- **Decisão:** Redução da densidade P-Brane para 5 nodes e implementação de aborto compulsório se a latência percepção-execução superar 500ms.
- **Justificativa:** A latência de 2.1s no BTCUSD invalidou o sinal dos 79 agentes. No HFT, entrar com sinal "vencido" é garantia de Stop Loss.
- **Data/Status:** ATIVO. (2026-03-07).

### DECISÃO 29: INTELLIGENT LOG PACING & DECISION DECOUPLING
- **Decisão:** Implementação de cooldowns temporais (30-60s) em logs repetitivos (PHI, Chaos Shield, Nuclear Strike) e desacoplamento do log '🎯 DECISION' do TrinityCore para o SniperExecutor.
- **Justificativa:** O spam de logs cegava o monitoramento humano e desperdiçava IO de terminal. O log de decisão agora só dispara se o trade passar nos gateways de segurança, refletindo apenas execuções reais.
- **Data/Status:** ATIVO. (2026-03-08).

### DECISÃO 30: KINEMATIC SYMMETRY & BREAKOUT PRIORITY (Phase 47)
- **Decisão:** Refatoração dos agentes de `Dynamics` para suavizar o damping cinemático e de volume (15x -> 25x) durante picos de aceleração confirmados por Order Flow (BRR > 0.6).
- **Justificativa:** A ASI estava vendendo fundos em V-reversals porque o damping agressivo da Phase 29 misturava 'ignição' com 'exaustão'. A nova simetria permite que o Sniper surfe a explosão inicial.
- **Data/Status:** ATIVO. (2026-03-08).

### DECISÃO 31: SPREAD TOLERANCE RELAXATION (Darwinian Gen #1)
- **Decisão:** Elevação do `max_spread_points` de 5000 para 6921.
- **Justificativa:** Em regimes de alta volatilidade, o spread do BTCUSD via Bridge Socket frequentemente cruzava os 5k, resultando em rejeições de trades de altíssima convicção. A relaxação permitiu liquidez em momentos de "Ignition".
- **Data/Status:** ATIVO. (2026-03-08).

### DECISÃO 32: AGGRESSIVE REGIME SWITCHING (Sensitivity Surge)
- **Decisão:** Aumento da `regime_sensitivity` de 0.30 para 0.48.
- **Justificativa:** O bot apresentava inércia (lag) ao sair de regimes "Bearing" para "Ignition". A maior sensibilidade permite transições mais rápidas para a proteção "Chaos Shield" ou agressão "Trend".
- **Data/Status:** ATIVO. (2026-03-08).

### DECISÃO 33: CLUSTER SPACING MULTIPLIER (Safety Surge)
- **Decisão:** Dobra da distância mínima entre posições da mesma direção (`duplicate_position_distance_atr` 1.0 -> 1.99).
- **Justificativa:** Prevenção de "Concentração de Risco" em um mesmo range. Ao exigir quase 2 ATRs de distância, a ASI garante que cada slot P-Brane explore uma zona de liquidez distinta.
- **Data/Status:** ATIVO. (2026-03-08).

### DECISÃO 34: CONSCIOUSNESS FEEDBACK LOOP (Phase Ω-Darwin)
- **Decisão:** Implementação de auditoria periódica (60s) via `history_deals_get` para sincronizar o Brain com a realidade financeira do terminal.
- **Justificativa:** A ASI estava "Ghost Trading" — operando sem auditar histórico, o que gerava amnésia sobre comissões e mutações baseadas em 'Fake Fitness'.
- **Data/Status:** ATIVO. (2026-03-08).

### DECISÃO 35: COMMISSION-AWARE EVOLUTIOnARY FITNESS - [RESOLVIDO]
- **Decisão:** Injeção mandatória de deduções de comissão (~$15/lote) em todos os registros de trade da `PerformanceTracker`.
- **Justificativa:** Alinhar o `SelfOptimizer` com o crescimento real do patrimônio líquido (Net Wealth), matando estratégias que geram volume bruto mas prejuízo líquido.
- **Data/Status:** ATIVO. (2026-03-08).

### DECISÃO 36: SOVEREIGN IGNITION & DAMPING REFINEMENT (Phase 48) - [RESOLVIDO]
- **Decisão:** Implementação de bypass de dampening estrutural quando `v_pulse_detected` ou sinais cinéticos extremos (>0.9) são validados.
- **Justificativa:** A ASI estava "vencendo a si mesma" ao asfixiar o momentum inicial de breakouts legítimos por confundir ignição de alta velocidade com exaustão climática.
- **Data/Status:** ATIVO. (2026-03-08).

### DECISÃO 38: V-PULSE SENSITIVITY & DRIFT IGNITION (Phase 48)
- **Decisão:** Redução do threshold de `tick_velocity` de 35 para 30 e inclusão de lógica de ignição específica para regimes de "Drift" e "Slow Grind".
- **Justificativa:** Identificou-se que breakouts em regimes de baixa volatilidade eram ignorados pelo threshold antigo, causando perda de timing. A nova sensibilidade captura explosões iniciais em regimes inerciais.
- **Data/Status:** ATIVO. (2026-03-08).

### DECISÃO 39: INTELLIGENT LOG PACING & DECISION DECOUPLING
- **Decisão:** Implementação de cooldowns de 30-60s para logs repetitivos e desacoplamento do log '🎯 DECISION' para o executor.
- **Justificativa:** Spam de logs saturava o IO do terminal e dificultava o monitoramento humano. O log de decisão agora reflete apenas execuções que passaram por todos os gateways.
- **Data/Status:** ATIVO. (2026-03-08).

### DECISÃO 40: MULTI-PROCESS RESILIENCE & SELF-OPTIMIZER PATCH
- **Decisão:** Implementação de checks de existência de métodos em `SelfOptimizer` e gates defensivos em `ASIBrain`.
- **Justificativa:** A ausência de métodos invocados por reflexão (`_check_and_optimize`) causava crashes letais durante o loop de consciência. O patch garante resiliência estrutural.
- **Data/Status:** ATIVO. (2026-03-08).

### DECISÃO 38: SELF-OPTIMIZER CALL RECTIFICATION (Post-Crash)
- **Decisão:** Correção mandatória do método de chamada do `SelfOptimizer` de `.optimize()` para `.check_and_optimize()` no cérebro.
- **Justificativa:** Divergência entre o protótipo do cérebro e a implementação final do módulo de evolução causou um crash fatal no ciclo #200.
- **Data/Status:** ATIVO. (2026-03-08).
### DECISÃO 41: HEARTBEAT ELEVATION & SENSORY FIX (Phase 48)
- **Decisão:** Redução do intervalo de log de status (100 -> 30 ciclos) e injeção do atributo `symbol` no `MarketSnapshot`.
- **Justificativa:** A ausência do `symbol` causava `AttributeError` no Wormhole Trigger. O log ralo de 10s (100 ciclos) era insuficiente para a observabilidade de uma ASI HFT em regime de alta frequência.
- **Data/Status:** ATIVO. (2026-03-08).

*(Atualizado: 2026-03-08. Versão: 4.1.0-omega)* — Phase Ω-Sensory Integrity restored)
