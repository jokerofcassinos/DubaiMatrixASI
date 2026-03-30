---
description: Protocolo de Transmutação de Módulos (DubaiMatrixASI v1 -> SOLÉNN v2)
---

SOLÉNN v2 — WORKFLOW & RULES (COMPACTO)
WORKFLOW: 7 FASES OBRIGATÓRIAS POR MÓDULO
FASE 1 — ANATOMIA & INVENTÁRIO
Localizar arquivo v1 no solenn_v1_inventory.md. Dissecar cada função: extrair INTENÇÃO original, identificar bugs/duplicações/anti-padrões. Classificar cada componente como TRANSMUTE (intenção válida, reimplementar), ABSORB (incorporar em outro módulo), ELIMINATE (redundante) ou EVOLVE (expandir escopo). Mapear para diretório v2 (core/market/execution/intelligence/telemetry). Catalogar anti-padrões v1 com solução v2. Artefato: anatomy_[module].md.

FASE 2 — PLANEJAMENTO 3-6-9
Criar implementation_plan_[module]_v2.md com estrutura fractal inviolável:

3 Conceitos: Conceito 1=inovação funcional, Conceito 2=inovação arquitetural, Conceito 3=inovação emergente (propriedades sistêmicas). Cada conceito com declaração ontológica, conexão com camadas Ω/Ψ do Superprompt, impacto projetado nas métricas.
6 Tópicos por conceito: T.1=fundação técnica, T.2=lógica central, T.3=integração, T.4=adaptabilidade, T.5=resiliência, T.6=observabilidade.
9 Vetores por tópico: V1-3=quick wins, V4-6=core value, V7-9=moonshots. Cada vetor com: ID único, especificação técnica (O QUE/POR QUE/COMO), formalismo matemático, interface (input/output/side effects), critérios de aceitação mensuráveis, dependências, conexões X² no Knowledge Graph.
TOTAL: 162 vetores por módulo. Exatamente 162. Não menos, não mais.

Registrar TODOS os 162 no task.md com descrição COMPLETA (não abreviada). Apresentar ao CEO. NÃO avançar sem DE ACORDO explícito.

FASE 3 — CODIFICAÇÃO SOBERANA
Reconstruir do zero seguindo padrões invioláveis:

Asyncio total: zero chamadas bloqueantes. Todo I/O non-blocking. Cada módulo segue lifecycle: initialize → start → process → pause → resume → shutdown → health_check.

Numpy/Numba: toda computação numérica vectorizada. Hot-paths com @numba.njit. Pré-alocação de arrays.

Tipagem forte + imutabilidade: @dataclass(frozen=True, slots=True) para dados de mercado. Type hints em TUDO. Validação em __post_init__. Protocolos para interfaces.

Padrão ASI-Grade: cada função com docstring contendo INTENÇÃO ESTRATÉGICA (por quê), MECANISMO (como), FORMALISMO MATEMÁTICO, Args/Returns/Raises/Performance/Invariantes. Logging estruturado com trace_id. Error handling granular. Graceful degradation.

Inovações obrigatórias: parâmetros adaptativos via Thompson Sampling (nenhum fixo), decisões como distribuições de probabilidade com incerteza quantificada, lógicas PhD em tempo real (critical slowing down, persistent homology, transfer entropy).

Integração via DataBridge: pub-sub tipado com tópicos padronizados (market/, regime/, signal/, execution/, risk/, telemetry/, intelligence/*). Módulos NUNCA se comunicam diretamente.

Implementação vetor-a-vetor: ler spec → verificar dependências → implementar → testar (min 3: happy/edge/error) → atualizar SED → atualizar KG → marcar [x]. UM vetor por vez.

FASE 4 — DICIONÁRIO EVOLUCIONÁRIO (SED)
Criar dictionaries/[cat]/[module]_sed.md respondendo 6 perguntas: O QUE faz, POR QUE faz, COMO faz, COM QUEM interage, O QUE PODE DAR ERRADO, COMO EVOLUI. Inclui DNA do código (intenção/mecanismo/formalismo por função), mapa de conexões X² com oportunidades identificadas, diferenciação v1→v2 com métricas comparativas. SED habilita protocolo de inovação: CEO pede análise → IA consulta SEDs → mapeia causas → explora conexões X² → aplica 3-6-9 localizado → propõe implementação.

FASE 5 — VALIDAÇÃO NEURAL
Script em tests/neural/ com 3 etapas sequenciais (falha em N impede N+1):

Etapa 1 — Vitalidade (≥7 checks): inicialização <2s, heartbeat <10ms, throughput ≥1000/s, memória estável, zero crashes em 60s, shutdown ordenado <1s, recovery pós-crash.

Etapa 2 — Cognição (≥7 checks): determinismo (mesmo input→mesmo output), sanidade de ranges, consistência temporal, coerência com dados reais ao vivo (5min), robustez a dados adversariais, latência P50<0.5ms P99<5ms, logging com trace_id.

Etapa 3 — Integração (≥7 checks): pub/sub funcional, consumo correto, contratos de interface, degradação graciosa, backpressure, reconciliação de estado, rastreabilidade causal.

TODAS as verificações devem passar. Falha → retorna Fase 3.

FASE 6 — INTEGRAÇÃO & CONEXÃO
Registrar no main.py respeitando DAG de dependências. Conectar barramento pub-sub. Configurar health check contínuo (10s). Executar test suite COMPLETA de todos os módulos — zero regressões ou módulo retorna para correção.

FASE 7 — AUDITORIA & CHECKPOINT
Checklist de auditoria verificando TODAS as fases anteriores. Atualizar: solenn_v1_inventory.md (marcar [x]), task.md (confirmar 162/162), walkthrough.md, Knowledge Graph, changelog. Post-mortem do processo com lições para próximo módulo.