---
trigger: always_on
---

§10 — PRINCÍPIOS ARQUITETURAIS INVIOLÁVEIS DO SOLÉNN v2
§10.1 — Os 12 Mandamentos Arquiteturais
Mandamento 1 — Modularidade Orgânica: cada módulo é um órgão com homeostase própria — se auto-monitora, se auto-calibra, se auto-diagnostica. Módulos se comunicam via interfaces tipadas explícitas (contratos), nunca via estado global compartilhado. Substituição de qualquer módulo não colapsa o sistema.

Mandamento 2 — Composicionalidade Categórica: se módulo A produz output de tipo T₁ e módulo B consome input de tipo T₁ e produz T₂, a composição B∘A é garantida por tipagem. Pipeline inteiro é composicional — cada módulo pode ser testado isoladamente E em composição. Functors e natural transformations (Ω-44) como framework formal.

Mandamento 3 — Observabilidade Total: cada módulo emite 3 tipos de telemetria — métricas (quantitativas, time-series), logs (eventos discretos, JSON estruturado), traces (causalidade entre eventos). Nenhuma decisão é opaca. Qualquer comportamento pode ser explicado por inspeção de telemetria.

Mandamento 4 — Graceful Degradation: falha de qualquer módulo resulta em funcionalidade REDUZIDA, nunca em crash. Hierarquia de degradação: full_capability → reduced_capability → safe_mode → minimal_mode → shutdown_orderly. Cada nível tem funcionalidade e riscos documentados.

Mandamento 5 — Invariantes por Construção: propriedades críticas de segurança (position_size ≤ max, drawdown ≤ limit, etc.) são garantidas por TIPO (type system), não por CHECK (runtime validation). Checks existem como segunda linha de defesa, não como primeira. Primeira linha = impossibilidade de violar por design.

Mandamento 6 — Idempotência Universal: toda operação que pode ser retried é idempotente. Execute(op, nonce) chamada N vezes produz mesmo resultado que chamada 1 vez. Implementado via nonce de operação + verificação de estado pré-condição.

Mandamento 7 — Separação de Concerns Quádrupla: (i) Percepção (dados do mercado) é separada de (ii) Cognição (análise e decisão) que é separada de (iii) Ação (execução de ordens) que é separada de (iv) Reflexão (post-trade analysis e aprendizado). Cada concern tem ciclo de vida, taxas de atualização e requisitos de latência diferentes.

Mandamento 8 — Configuration as Code: ZERO parâmetros hardcoded. Toda configuração é externalizada, versionada, documentada com razão de cada valor, e auditável. Mudança de configuração = commit com mensagem explicativa + aprovação + rollback plan.

Mandamento 9 — Determinismo Reproduzível: dado o mesmo estado de mercado + mesma configuração + mesmo timestamp, o SOLÉNN produz EXATAMENTE a mesma decisão. Não-determinismo (randomização de timing, jitter anti-fingerprint) é adicionado em camada SEPARADA e desativável para debugging/replay.

Mandamento 10 — Testing como Primeira Classe: testes não são afterthought — são co-criados com código. Para cada módulo: unit tests (cada função), integration tests (interação entre módulos), property-based tests (propriedades que devem valer para QUALQUER input: Hypothesis/QuickCheck), regression tests (cada bug fixado tem teste que previne recorrência), performance tests (latência e throughput sob carga).

Mandamento 11 — Documentação Viva: documentação é gerada a partir de código + KG, não escrita separadamente. Sempre atualizada por construção. Documentação separada do código é debt que acumula juros de desatualização.

Mandamento 12 — Anti-Entropia Ativa: complexidade é medida continuamente (cyclomatic complexity, coupling, cohesion, lines of code, number of dependencies). Se complexidade cresce sem justificativa proporcional em funcionalidade, refactoring é OBRIGATÓRIO antes de novas adições. Entropy budget: cada sprint tem budget de complexidade; se excedido, sprint seguinte é dedicado a simplificação.

§10.2 — Transição Programa → Organismo
O SOLÉNN v2 não é um programa — é um organismo digital:

Conceito de Programa	Conceito de Organismo (SOLÉNN v2)
Módulo executa função	Órgão mantém homeostase
Variável armazena dado	Célula contém estado vivo
If-else decide	Sistema nervoso integra e responde
Loop repete	Metabolismo processa continuamente
Error handler recupera	Sistema imunológico detecta e neutraliza
Configuração parametriza	DNA codifica comportamento
Deploy atualiza	Evolução adapta
Teste valida	Sistema sensorial monitora
Log registra	Memória armazena experiência
Shutdown desliga	Hibernação preserva estado
Cada módulo possui 6 capacidades orgânicas:

Auto-monitoramento: mede própria saúde (latência, acurácia, throughput)
Auto-calibração: ajusta parâmetros quando performance degrada
Auto-diagnóstico: identifica causa de degradação
Auto-healing: corrige problemas simples autonomamente
Auto-reporting: comunica estado para o sistema nervoso central (orquestrador)
Auto-evolução: sugere melhorias para próxima versão (via Ψ-13)