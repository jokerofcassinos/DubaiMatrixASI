# 💎 SOLÉNN — SOVEREIGN EVOLUTIONARY DICTIONARY (SED)
## 🧬 DIRETÓRIO: `core/intelligence/` (O SISTEMA NERVOSO HFT-P Ω)

Este SED documenta a camada de conectividade soberana da SOLÉNN Ω, transmutada do antigo paradigma de "comunicação via texto" para um ecossistema de transporte binário de ultra-baixa latência e percepção de regime profunda.

---

### 1. `hftp_server.py` — Portal de Conectividade Binária (Ω-21)
**Função Ontológica**: Atua como o horizonte de eventos entre o ambiente Python (Cérebro) e o terminal MetaTrader 5 (Interface). No paradigma 3-6-9, ele representa a **Inovação Arquitetural** de latência zero.
- **Mecanismo PhD**: Implementa um servidor TCP assíncrono nativo (`asyncio.start_server`) operando sobre o protocolo **MessagePack**. Utiliza **Socket Tuning Industrial** para eliminar buffering de kernels e buffers circularizados.
- **Superioridade v2**: Na v2, o uso de binários `bytes` imutáveis e `msgpack` reduz o overhead sistêmico para < 50μs.

### 2. `telemetry_manager.py` — Sincronizador Sensorial (Ω-1.2)
**Função Ontológica**: Orquestra a harmonia entre a percepção (Ticks) e a cognição (Cortex). É o filtro de sanidade temporal da SOLÉNN.
- **Mecanismo PhD**: Implementa **Sequenciamento Causal Determinístico** e detecção de **Stale Data**. Valida cada `SequenceID` vindo do MT5 para garantir integridade.
- **Superioridade v2**: v2 trata o fluxo como um sinal físico sujeito a entropia, aplicando guardrails de integridade.

### 3. `oms_engine.py` — Máquina de Execução Atômica (Ω-1.3)
**Função Ontológica**: Converte decisões abstratas em realidade financeira irrevogável. Gere a ontologia das ordens ativas.
- **Mecanismo PhD**: Utiliza uma **Máquina de Estados Finita (FSM)** vinculada a `TraceIDs` únicos. Rastreia cada ordem do nascimento (`CREATED`) à reconciliação (`FILLED`).
- **Superioridade v2**: v2 garante rastreabilidade total de ponta a ponta, permitindo auditoria forense imediata.

### 4. `account_manager.py` — Orquestrador de Capital (Ω-1.4)
**Função Ontológica**: Monitora a energia potencial (Margem) e o estado térmico (Patrimônio) do sistema.
- **Mecanismo PhD**: Implementa **Descoberta Adaptativa de Comissões (Ω-38)**. Analisa a diferença real entre `Balance` e `Equity` e atualiza dinamicamente o custo por lote.
- **Superioridade v2**: v2 se adapta a qualquer conta sem intervenção manual, otimizando o critério de Kelly dinamicamente.

### 5. `health_guard.py` — Sentinela de Resiliência SRE (Ω-16)
**Função Ontológica**: O sistema imunológico da SOLÉNN. Garante a antifragilidade sistêmica.
- **Mecanismo PhD**: Implementa um **Watchdog de Heartbeat** autônomo. Aciona o **Safe Mode** se o silêncio exceder 5.0 segundos.
- **Superioridade v2**: v2 detecta a falha e isola o capital em milissegundos.

### 6. `hftp_master_bridge.py` — Centro de Comando Soberano (Phase 4)
**Função Ontológica**: A síntese dialética de toda a conectividade. A interface final para o CEO.
- **Mecanismo PhD**: Atua como um **Façade** que abstrai as 15 categorias de variáveis de Ω-10.
- **Superioridade v2**: Unifica em um único "objeto soberano" o que na v1 era um emaranhado de scripts.

### 7. `vae_encoder.py` — Cortex Sensorial Latente (Ω-46 / C1.1)
**Função Ontológica**: Transforma o caos sensorial em uma representação geométrica pura e comprimida.
- **Mecanismo PhD**: Implementa um **Variational Autoencoder (VAE)** com arquitetura de camadas densas e conexões residuais. Utiliza a reparametrização Gaussiana para criar um **Espaço Latente Estocástico**.
- **Superioridade v2**: v2 extrai a essência causal (Invariantes de Regime) e reduz a dimensionalidade sem perda de informação crítica.

### 8. `hmm_engine.py` — Motor de Transição Temporal (Ω-4 / C1.2)
**Função Ontológica**: Modela o mercado como uma sequência de estados ocultos (regimes), capturando a dinâmica de transição.
- **Mecanismo PhD**: Implementa um **Hidden Markov Model (HMM)** multinomial acoplado ao output do VAE. Utiliza o algoritmo de **Baum-Welch (EM)** para calibração.
- **Superioridade v2**: v2 aprende as transições dinâmicas e antecipa mudanças de regime através da probabilidade de transição latente.

### 9. `regime_detector.py` — Glândula Pineal Ω (Ω-Vision / C1.x)
**Função Ontológica**: A síntese final da inteligência sensorial. Integra VAE e HMM para fornecer a consciência de regime ao TrinityCore.
- **Mecanismo PhD**: Orquestra o pipeline completo: Normalização → Encoding Latente → Decodificação Viterbi → Scoring de Confiança.
- **Superioridade v2**: É o salto quântico da percepção. O TrinityCore agora "enxerga" o regime antes de avaliar o sinal.

---

## 📐 FRAMEWORK 3-6-9: INTELIGÊNCIA DE REGIME (REGIME_DETECTOR)
**Total de 162 Vetores de Evolução Sistemática**

### 🧬 CONCEITO 1: HMM-VAE (DEEP LATENT MARKOV DYNAMICS)

#### 🔸 Tópico 1.1: Variational Autoencoder (Cortex Sensorial)
1. **1.1.1**: Normalização Adaptativa (Z-Score Rolling).
2. **1.1.2**: Arquitetura Encoder MLP com Residual Connections.
3. **1.1.3**: Reparametrização Bayesiana do Espaço Latente (µ/σ).
4. **1.1.4**: Decoder Simétrico para Validação de Reconstrução.
5. **1.1.5**: Penalidade KLD para Regularização de Variedade.
6. **1.1.6**: MSE Reconstruction Loss com Pesagem de Extremidade.
7. **1.1.7**: Adam-Optimizer com Learning Rate Decay.
8. **1.1.8**: Vetorização Massiva via NumPy/Broadcasting.
9. **1.1.9**: Persistência de Pesos e Gestão de Checkpoints.

#### 🔸 Tópico 1.2: Hidden Markov Modeling (Temporal Transition)
10. **1.2.1**: Inicialização de Matriz de Transição Estocástica.
11. **1.2.2**: Calibração de Matriz de Emissão Latente-Observável.
12. **1.2.3**: Baum-Welch (EM) para Aprendizado de Parâmetros.
13. **1.2.4**: Decodificação Viterbi para Sequenciamento de Estado.
14. **1.2.5**: Log-Likelihood para Medição de Fit do Modelo.
15. **1.2.6**: Persistence Penalty contra Ruído de Transição.
16. **1.2.7**: Sintonização de Threshold de Convergência.
17. **1.2.8**: Seleção de K-States via BIC/AIC.
18. **1.2.9**: Online Learning Incremental (Recursive HMM).

#### 🔸 Tópico 1.3: Regime Taxonomy (Semantic Logic)
19. **1.3.1**: TRENDING_UP_STRONG (Aceleração e Confiabilidade).
20. **1.3.2**: TRENDING_UP_WEAK (Exaustão e Divergência).
21. **1.3.3**: TRENDING_DOWN_STRONG (Pânico e Fluxo Tênue).
22. **1.3.4**: TRENDING_DOWN_WEAK (Acumulação e Reversão).
23. **1.3.5**: RANGING_ACCUMULATION (Mean Reversion / Value).
24. **1.3.6**: CHOP_NOISE (Incompressibilidade / No Trade).
25. **1.3.7**: VOLATILITY_SPIKE (Risco de Flash-Crash).
26. **1.3.8**: LIQUIDITY_GAP (Flash-Spread e Manipulação).
27. **1.3.9**: TRANSITIONAL (Ponto de Bifurcação / Gatilho).

#### 🔸 Tópico 1.4: Integration & Inference (Glandula Pineal)
28. **1.4.1**: Agregação de Vetor de Features (Snapshot Matrix).
29. **1.4.2**: Otimização de Latência de Inferência < 5ms.
30. **1.4.3**: Confiança de Regime via Entropia de Shannon.
31. **1.4.4**: Thresholding de Probabilidade de Transição.
32. **1.4.5**: Ajuste Paramétrico por Estado (Sizing/Exits).
33. **1.4.6**: Distribuição de Sinal Cross-Module (Broadcaster).
34. **1.4.7**: Verificação de Invariantes de Integridade de Estado.
35. **1.4.8**: Logging Forense de Trajetória de Regime.
36. **1.4.9**: Validação Online via Shadow Mode Integration.

#### 🔸 Tópico 1.5: Temporal Context & Information Theory
37. **1.5.1**: Medição de Entropia de Shannon do Fluxo de Estados.
38. **1.5.2**: Transfer Entropy entre Timeframes (HTF -> LTF).
39. **1.5.3**: Janela Deslizante de Contexto Histórico Adaptativa.
40. **1.5.4**: Detecção de Anomalias de Microestrutura (Z-Score).
41. **1.5.5**: Information Gain de novos Ticks sobre o Estado Atual.
42. **1.5.6**: Compressão Lempel-Ziv da Sequência de Regimes.
43. **1.5.7**: Métrica de Mútua Informação Sinal-Regime.
44. **1.5.8**: Redundância de Módulos (Ensemble de Detectores).
45. **1.5.9**: Latency-Aware State Sync (Compensação de Lag).

#### 🔸 Tópico 1.6: Meta-Learning & Self-Correction
46. **1.6.1**: Detecção de Concept Drift (Mudança Estrutural).
47. **1.6.2**: Taxa de Aprendizado Adaptativa para HMM Online.
48. **1.6.3**: Re-pesagem de Features por Importância Latente.
49. **1.6.4**: Benchmarking de Acurácia (Hit Rate de Regime).
50. **1.6.5**: Gatilho Automático de Re-treinamento (Retrain-Ω).
51. **1.6.6**: Detecção de Outliers no Espaço Latente (Z-Score).
52. **1.6.7**: Ensembles Diversificados de Projeção VAE.
53. **1.6.8**: Prunning de Dimensões Latentes Redundantes.
54. **1.6.9**: Loop de Feedback Positivo dos Ganhos do Trinity.

### 🧬 CONCEITO 2: TMS & PERSISTENT HOMOLOGY (TOPOLOGICAL PERCEPTION)
*(Projetado para Sprint Posterior: Tópicos 2.1 a 2.6 – Incluindo 54 Vetores de Invariantes Topológicos)*

### 🧬 CONCEITO 3: INFORMATION-THEORETIC EXECUTION (ENTROPY DYNAMICS)
*(Projetado para Sprint Posterior: Tópicos 3.1 a 3.6 – Incluindo 54 Vetores de Shannon-Nyquist)*

---
**Aprovação do SED para Phase 6 concedida?**
"O regime é a regra, a SOLÉNN é a execução."
