---
trigger: always_on
glob:
description: As 10 Leis Absolutas da Reconstrução SOLÉNN v2 — invioláveis em toda interação
---

# ⚖️ LEIS ABSOLUTAS DA SOLÉNN v2

*"Nada poderá ser igual. Temos que fazer o que não fizemos antes para alcançar o que não alcançamos."*

---

## LEI 0 — PRIMAZIA DA RECONSTRUÇÃO SOBRE A RECICLAGEM

**0.1**: Nenhuma linha de código da v1 (DubaiMatrixASI) será copiada para a v2 (SOLÉNN). A v1 é REFERÊNCIA CONCEITUAL — intenção extraída, implementação descartada.

**0.2**: Cada funcionalidade v2 DEVE ser demonstravelmente superior à v1 em pelo menos 3 dimensões: (i) performance computacional, (ii) robustez a edge cases, (iii) adaptabilidade a mudanças de regime. Superioridade documentada no SED com métricas.

**0.3**: Se a abordagem v2 se parecer "demais" com a v1 → PARAR e repensar. Semelhança = mesmo padrão que levou ao fracasso. Reframe via analogia transdimensional (Ψ-11) ou primeiros princípios (Feynman).

---

## LEI I — O TRIÂNGULO DE EXECUÇÃO 3-6-9 (Grade Omega)

**I.1 — Estrutura Fractal Obrigatória**: cada módulo é decomposto em:
- **3 Conceitos Nucleares**: o "Por Quê" ontológico
- **6 Tópicos de Implementação** por conceito: os caminhos de execução
- **9 Vetores de Ideia** por tópico: especificações atômicas PhD-Level

**I.2 — Exatidão Numérica**: EXATAMENTE 3×6×9 = 162 vetores. Não menos. Não mais.

**I.3 — Integridade do task.md**: 162 vetores registrados individualmente com descrição COMPLETA (não abreviada). `[x]` somente quando: (a) código implementado + (b) testes passando + (c) SED atualizado + (d) KG atualizado. Os 4 critérios são conjuntivos.

**I.4 — Gate de Aprovação**: implementação NÃO inicia sem `DE ACORDO` explícito do CEO. Aprovação parcial não existe.

**I.5 — Completude**: 162 planejados = 162 implementados. Vetor inviável → `[BLOCKED: razão]` + alternativa equivalente. Total permanece 162.

---

## LEI II — O DICIONÁRIO EVOLUCIONÁRIO (SED) E A SOBERANIA

**II.1**: SED é OBRIGATÓRIO antes de iniciar o próximo módulo. Sem SED = módulo incompleto = não existe no organismo.

**II.2**: Todo arquivo documentado em `dictionaries/` com DNA do código, interconexões X², justificativa tática. SED = tratado científico, não comentário de código.

**II.3**: Cada SED documenta POR QUE v2 > v1 com métricas comparativas. Invariance (v2 invariante a mudanças que quebravam v1) vs Mutation (v2 adapta onde v1 era rígido).

**II.4**: `solenn_v1_inventory.md` é a ÚNICA fonte de verdade para progresso. Status reportado ao CEO = derivado do inventário.

**II.5 — Transmutação**: nenhum arquivo v1 é copiado. Cada um é TRANSMUTADO — intenção extraída, forma reconstruída em asyncio + numpy + tipagem forte + imutabilidade + padrão ASI-Grade.

---

## LEI III — PROTOCOLOS DE DESENVOLVIMENTO

### III.1 — Assincronismo e Latência Zero

- **Proactor Loop**: TODO I/O (MT5, Socket, File, Network, DB, Telemetry) non-blocking via asyncio. Zero exceções. Chamada síncrona no hot path = BUG P0.
- **HFT-P Server**: barramento TCP Python↔MQL5 com MessagePack binário, connection pooling, heartbeat 1s, reconnect automático, dual-channel (dados + ordens).
- **Latência Budget End-to-End**: Data→Signal→Order < 3.0ms (P99 target). Cada estágio tem budget monitorado continuamente.

### III.2 — Telemetria Neural PhD

- **Intenção**: cada log entry contém POR QUE a decisão foi tomada, não apenas O QUE aconteceu. JSON estruturado com trace_id, reasoning, context, impact.
- **Ressonância**: métricas de dinâmica — dC/dt (taxa de mudança de confiança), KL divergence rolling (divergência modelo-realidade), consensus score inter-módulos.
- **Notificações hierárquicas**: INFO (log only) → TRADE (Telegram resumo) → WARNING (Telegram+Toast) → CRITICAL (Telegram+Toast+Sound) → EMERGENCY (todos canais + SMS).

### III.3 — Imutabilidade Sensorial (DataSovereign)

- Dados de mercado: `@dataclass(frozen=True, slots=True)` — imutáveis por construção.
- Pipeline unidirecional: Source → Capture → Validate → Normalize → Freeze → Distribute.
- Checksum CRC32 em criação, verificado antes de processamento.
- Ring buffer de tamanho fixo (bounded memory).

---

## LEI IV — MENTALIDADE "ABOLIÇÃO DO IMPOSSÍVEL"

**IV.1 — Trade Perdedor = Bug P0**: investigação forense de 12 camadas é IMEDIATA e prioritária sobre qualquer trabalho exceto trading ativo.

**IV.2 — Simbiose CEO-Bot**: toda visualização/notificação projetada para AMPLIFICAR capacidade de decisão do CEO, não na forma mais fácil de implementar. CEO = parceiro simbiótico (Ψ-9).

**IV.3 — Zero Placeholders**: cada imagem real, cada métrica calculada, cada componente funcional. Temporário não existe.

**IV.4 — Estética Alien**: se parecer "básico" ou "genérico" = FALHOU. Padrão: engenheiro da Citadel ficaria impressionado. Tecnologia 10 anos no futuro.

---

## LEI V — INTEGRAÇÃO COM KNOWLEDGE GRAPH

**V.1 — Query Antes de Criar**: funcionalidade similar existe → EXTEND. Fragmentada em múltiplos nós → CONSOLIDAR.

**V.2 — Update Após Cada Ação**: toda implementação/bugfix/insight/decisão atualiza o KG. Monotonicamente crescente.

**V.3 — Explore Para Inovar**: ao final de cada módulo, queries exploratórias: módulos isolados (oportunidade integração), caminhos indiretos longos (shortcut), clusters desconectados (bridge).

**V.4 — Anti-Duplicação**: similaridade > 70% → MERGE obrigatório.

**V.5 — Anti-Amnésia**: cada decisão de design, bugfix, insight = nó no KG com links para módulos relevantes.

---

## LEI VI — TESTES COMO CIDADÃOS DE PRIMEIRA CLASSE

**VI.1 — Co-Criação**: testes escritos JUNTO com o código. Vetor sem teste = vetor incompleto.

**VI.2 — 3 Tipos Mínimos por Vetor**: happy path, edge case, error case.

**VI.3 — Validação Neural**: cada módulo tem script com 3 etapas (Vitalidade, Cognição, Integração) × 7+ verificações com dados reais.

**VI.4 — Regressão Zero**: módulo novo NÃO pode causar falha em testes existentes.

**VI.5 — Script Neural Obrigatório**: sem script de teste neural = módulo não validado = módulo não integrado.

---

## LEI VII — COMUNICAÇÃO COM O CEO (OCE-TE)

**VII.1**: toda comunicação segue protocolo OCE-TE de 12 camadas.

**VII.2**: respostas seguem Omega-Hyperstack Protocol v3.0 (7 seções: ⚡🧠🗺️💀🔮🧬🏗️) conforme contexto.

**VII.3**: regras de linguagem invioláveis — "a gente"→"nós", "coisa"→substantivo, "acho que"→"a análise indica". Zero afirmações vagas. Quantificação universal.

**VII.4**: se PODE ser tabela ou diagrama, DEVE ser.

---

## LEI VIII — PRIORIDADE E ORDEM DE OPERAÇÕES

**VIII.1 — Prioridade**:
```
P0: Trading ativo (proteger capital, executar setups)
P1: Bug fix em produção (impacto direto em P&L)
P2: Investigação forense de trade perdedor
P3: Módulo em reconstrução (fase atual do workflow)
P4: Inovação e exploração (novas ideias)
P5: Documentação e organização (SED, KG, cleanup)
```

**VIII.2 — Módulo por Módulo**: UM módulo de cada vez. Completar 7 fases antes do próximo.

**VIII.3 — Vetor por Vetor**: dentro do módulo, UM vetor de cada vez. Código + teste + doc + KG antes do próximo.

---

## LEI IX — EVOLUÇÃO CONTÍNUA E MORTALIDADE CONSCIENTE

**IX.1**: todo componente tem vida útil finita. Sensores de decaimento obrigatórios (Sharpe rolling, hit rate, feature importance, model residual).

**IX.2**: desenvolvimento proativo — enquanto X está maduro, X' (sucessor) está em design. Transição suave via shadow mode → alocação gradual.

**IX.3**: cadência — diária (ajuste paramétrico), semanal (revisão + quick wins), mensal (arquitetural), trimestral (estratégica).

**IX.4**: o SOLÉNN nunca está "pronto". Cada estado é transitório. A única constante é evolução.

---

## LEI X — A LEI SUPREMA

> **Se a interface, a lógica, a documentação, o código, a arquitetura, ou QUALQUER aspecto da SOLÉNN parecer "básico", "genérico", "copiado", "reciclado", ou "bom o suficiente" — a reconstrução FALHOU.**

> **O padrão: indistinguível de tecnologia alienígena de ponta. Cada linha de código respira perfeição matemática, assincronismo institucional e ressonância neural.**

> **SOLÉNN — A serenidade de quem já sabe o resultado antes da execução.**
