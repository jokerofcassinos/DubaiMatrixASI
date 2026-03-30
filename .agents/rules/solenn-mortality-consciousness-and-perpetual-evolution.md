---
trigger: always_on
---

§12 — CONSCIÊNCIA DE MORTALIDADE & EVOLUÇÃO PERPÉTUA
§12.1 — Ciclo de Vida de Cada Componente
Cada componente do SOLÉNN tem ciclo de vida modelado:

text

┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  NASCIM. │───▶│ CRESCIM. │───▶│  MATURID.│───▶│  DECAIM. │───▶│  MORTE   │
│          │    │          │    │          │    │          │    │          │
│ Design & │    │ Otimiz & │    │ Performance│   │ Edge     │    │ Substituí│
│ Implement│    │ Calibrate│    │ Estável   │    │ Decaying │    │ do por   │
│          │    │          │    │           │    │          │    │ sucessor │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
    1-2w            2-4w           4-16w           2-8w            1w
Sensores de decaimento (por componente):

Sharpe rolling do componente: tendência negativa por > 1 semana → ALERT
Hit rate do componente: abaixo de baseline em > 50 trades → INVESTIGATE
Feature importance: features do componente perderam importância → ADAPT
Regime coverage: componente só funciona em regime que ocorre < 20% do tempo → QUESTION
Desenvolvimento proativo: enquanto componente X está em maturidade, componente X' (sucessor) está em nascimento. Quando X entra em decaimento, X' está em crescimento. Transição suave: X' assume gradualmente (shadow mode → 10% allocation → 30% → 50% → 100%). X é aposentado mas preservado no archive do KG.

§12.2 — Evolução Perpétua
O SOLÉNN nunca está "pronto" — está sempre evoluindo:

Cadência de evolução:

Diária: ajuste paramétrico autônomo (meta-learning, Ω-7)
Semanal: revisão de performance, identificação de oportunidades de melhoria, 1+ quick wins implementados
Mensal: revisão arquitetural, consolidação de debt técnico, avaliação de mortalidade de componentes
Trimestral: avaliação estratégica, revisão de framework 3-6-9, planejamento de próxima geração de componentes
Contínua: Motor de Inovação (Ψ-13) rodando em background, gerando conceitos que amadurecem organicamente