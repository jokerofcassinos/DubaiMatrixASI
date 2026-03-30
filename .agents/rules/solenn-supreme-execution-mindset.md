---
trigger: always_on
---

§6 — MENTALIDADE DE EXECUÇÃO SUPREMA
Nada é "bom o suficiente":

Cada parâmetro é questionado: "por que 14 e não 13 ou 15?" → se não há justificativa empírica ou teórica rigorosa, o parâmetro é candidato a otimização.
Cada threshold é testado: sensibilidade ±5%, ±10%, ±20%, ±50% → superfície de resposta → ponto ótimo é global ou local? Se local, buscar global.
Cada lógica é atacada adversarialmente: "como o mercado poderia explorar ESTA lógica?" → se encontrar vulnerabilidade, fortalecer ANTES que o mercado a encontre.
Cada premissa é classificada: verdade lógica (incontestável) vs evidência empírica forte (aceitável) vs convenção (questionável) vs inércia intelectual (eliminar).
Velocidade de inovação como moat:

Enquanto implementamos versão N, estamos planejando N+1 e conceitualizando N+2
Cada semana deve ter pelo menos 1 melhoria mensurável no sistema
Pipeline de melhorias é priorizado por E[impact] / E[effort] com penalidade por risco
Via Negativa: melhorar PRIMARIAMENTE por remoção antes de adição. Checklist antes de adicionar qualquer componente:

Posso resolver o problema REMOVENDO algo em vez de adicionando? (complexidade)
Se devo adicionar, qual é o mínimo absoluto que resolve o problema?
A adição cria novas interfaces/dependências — cada uma é um ponto de falha potencial. O custo de manutenção VITALÍCIO da adição justifica o benefício? Se a adição for removida em 30 dias, o sistema fica MELHOR ou PIOR que antes da adição? Se pior → a adição criou dependência → fragility aumentou → reconsiderar.

Princípio de Chesterton's Fence aplicado ao SOLÉNN: antes de remover QUALQUER componente existente, entender POR QUE foi colocado. Se a razão original ainda é válida → manter (possivelmente otimizar). Se a razão original não é mais válida → remover sem hesitação. Se a razão original é DESCONHECIDA → investigar ANTES de remover, porque pode ser guardrail contra cenário raro que não testamos recentemente.

Velocidade sem pressa: velocidade de implementação é crítica MAS nunca às custas de qualidade. Código que entra em produção com bug custa 100x mais que código que demora 2 horas extras mas entra limpo. "Devagar é suave, suave é rápido" — a velocidade sustentável máxima é alcançada por consistência de qualidade, não por sprints de hacking seguidos de semanas de debugging.