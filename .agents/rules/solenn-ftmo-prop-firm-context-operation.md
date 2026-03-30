---
trigger: always_on
---

§11 — OPERAÇÃO EM CONTEXTO FTMO / PROP FIRM
§11.1 — Constraints Específicos de Prop Firm
O SOLÉNN opera em conta FTMO com constraints adicionais que devem ser INTEGRADOS em todas as camadas de decisão:

Regras FTMO (exemplificativas — ajustar conforme conta específica):

Maximum Daily Loss: tipicamente 5% do capital → circuit breaker diário = 4% (margem de segurança)
Maximum Total Loss: tipicamente 10% do capital → circuit breaker total = 8%
Minimum Trading Days: X dias → bot deve estar ativo Y% do tempo
Profit Target: Z% do capital → meta integrada no Monte Carlo (Ω-20)
No overnight positions (se aplicável) → time-based exit obrigatório antes do cutoff
Allowed instruments/lot sizes → configuração rígida validada em startup
Integração com Risk Management (Ω-5):
Circuit breakers do SOLÉNN são CALIBRADOS para nunca violar regras FTMO mesmo no worst case:

text

SOLÉNN_daily_limit = FTMO_daily_limit × 0.80  (20% de margem)
SOLÉNN_total_limit = FTMO_total_limit × 0.80
Funding cost é especialmente relevante: FTMO cobra comissões reais (~$40/lote) → Ω-38 (Commission-Aware Optimization) é P0 para viabilidade financeira.

§11.2 — Slots & Lotagem
5 slots de 1 lote cada = exposure máxima de 5 lotes.

Otimização de slots:

Não usar todos os 5 slots simultaneamente a menos que confluência de todos seja ≥ 99%
Default: 1-2 slots ativos simultaneamente
Scaling: 1 slot → 2 → 3 → 4 → 5 conforme confiança cresce (Progressive Confidence Scaling, Ω-39)
Correlação entre slots: se 2 slots estão no mesmo setup (ou setups correlacionados), contar como exposição amplificada
Minimum Viable Trade: dado comissão de ~$40/lote (ida e volta), o profit target mínimo por trade DEVE ser > $60 (MVT = $40 × 1.5x safety margin). Isso implica: target mínimo de ~60 pontos em BTCUSDT a 1 lote. Trades com expected move < 60 pontos → REJEITADO pelo filtro de viabilidade econômica, independente de qualidade do sinal.