---
trigger: always_on
---

§9 — KNOWLEDGE GRAPH: DICIONÁRIO VIVO DO SOLÉNN
§9.1 — Arquitetura do Knowledge Graph
text

┌─────────────────────────────────────────────────────────────────┐
│                 SOLÉNN KNOWLEDGE GRAPH                          │
│              (Dicionário Evolutivo Vivo)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  CAMADA 1 — ONTOLOGIA DE MÓDULOS                               │
│  ┌──────────┐   depends_on   ┌──────────┐                      │
│  │ Module A │───────────────▶│ Module B │                      │
│  │ (regime) │                │ (signal) │                      │
│  └────┬─────┘                └────┬─────┘                      │
│       │ outputs_to                │ inputs_from                 │
│       ▼                          ▼                              │
│  ┌──────────┐   correlates   ┌──────────┐                      │
│  │ Module C │◄──────────────▶│ Module D │                      │
│  │ (execut) │                │  (risk)  │                      │
│  └──────────┘                └──────────┘                      │
│                                                                 │
│  CAMADA 2 — ONTOLOGIA DE CONCEITOS                             │
│  Cada módulo ──▶ lista de conceitos implementados              │
│  Cada conceito ──▶ definição formal + intuição + equações      │
│  Cada conceito ──▶ relações com outros conceitos               │
│                                                                 │
│  CAMADA 3 — ONTOLOGIA DE DECISÕES                              │
│  Cada decisão de design ──▶ razão + alternativas + tradeoffs   │
│  Cada bug fix ──▶ sintoma + causa raiz + patch + validação     │
│  Cada post-mortem ──▶ trade + análise + lições + ações         │
│                                                                 │
│  CAMADA 4 — ONTOLOGIA DE PERFORMANCE                           │
│  Cada módulo ──▶ métricas de performance históricas            │
│  Cada configuração ──▶ resultados em cada regime               │
│  Cada versão ──▶ changelog + impacto medido                    │
│                                                                 │
│  CAMADA 5 — ONTOLOGIA DE OPORTUNIDADES                         │
│  Conexões POTENCIAIS (ainda não implementadas)                  │
│  Ideias geradas pelo 3-6-9 aguardando priorização              │
│  Insights do Motor de Inovação (Ψ-13) em maturação            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
§9.2 — Operações Fundamentais do Knowledge Graph
QUERY antes de CRIAR: antes de implementar QUALQUER funcionalidade, consultar o KG:

text

MATCH (n) WHERE n.functionality SIMILAR TO [nova_funcionalidade]
RETURN n, n.status, n.performance, n.connections
Se resultado não vazio → EXTEND ou CONSOLIDATE, nunca DUPLICATE.

UPDATE após cada ação: toda implementação, bugfix, insight, decisão atualiza o KG automaticamente. Nenhuma informação é perdida. O KG é monotonicamente crescente em informação.

EXPLORE para inovação: periodicamente, executar queries exploratórias:

text

// Encontrar módulos com poucas conexões (ilhas isoladas = oportunidade de integração)
MATCH (n) WHERE degree(n) < 3 RETURN n

// Encontrar caminhos indiretos longos (oportunidade de shortcut direto)
MATCH path = shortestPath((a)-[*]-(b)) WHERE length(path) > 4
RETURN a, b, length(path)

// Encontrar clusters desconectados (oportunidade de bridge)
CALL algo.communityDetection() YIELD communities
RETURN communities WHERE size(community) > 1 AND bridgeEdges = 0
§9.3 — Anti-Duplicação Formal
Regra de unicidade funcional: para cada função F no espaço funcional do SOLÉNN, existe EXATAMENTE UM módulo que é o owner autoritativo de F. Ownership é registrado no KG. Se dois módulos M₁ e M₂ ambos implementam funcionalidade similar F₁ ≈ F₂ (similaridade semântica > 0.7 medida por embedding de descrição), MERGE é obrigatório:

Avaliar qual implementação é superior (M₁ ou M₂) por métricas
Migrar funcionalidade para o superior
Redirecionar todos os dependentes do inferior para o superior
Deprecar o inferior (não deletar — mover para archive com referência)
Atualizar KG com merge record
§9.4 — Anti-Amnésia Formal
Regra de rastreabilidade total: para cada comportamento B do SOLÉNN, deve existir cadeia causal rastreável no KG:

text

B ←─ implementado_por ←─ decisão_D ←─ motivado_por ←─ insight_I ←─ observado_em ←─ evento_E
Se cadeia está incompleta (elo faltando), é flagada como debt de conhecimento com prioridade de correção. Debt de conhecimento é tratado como debt técnico — acumula juros (confusão futura) se não pago.

