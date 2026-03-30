---
trigger: always_on
---

ANÁLISE & INTELIGÊNCIA (Ω-11 a Ω-20) - part 2
Ω-16 — RESILIÊNCIA & DISASTER RECOVERY

Princípio de design: o sistema deve sobreviver a QUALQUER falha individual e à maioria das combinações de falhas duplas.

Catálogo de falhas e respostas:

Falha	Detecção	Resposta Automática	Recovery
Exchange crash	Heartbeat timeout + HTTP health check	Fechar posições via backup API/exchange	Reconciliar estado pós-recovery
Websocket disconnect	Missing heartbeat > 3s	Reconnect com exponential backoff; switch to REST polling	Resume websocket, replay missed data
Data corruption	Checksum mismatch, range violation	Rejeitar dados corrompidos, usar cache válido, alert	Investigar fonte, corrigir pipeline
Clock skew > 50ms	NTP monitoring	Recalibrar timestamps, alert se > 100ms	Root cause (VM migration? Network?)
Race condition	Detectável por invariant violation	Rollback to last consistent state	Fix mutex/sequencing, replay
Memory leak	RSS monitoring > threshold	Graceful restart (fechar posições → shutdown → restart → reconciliar)	Memory profiling, fix allocation
Disk full	Filesystem monitoring > 90%	Rotate logs, compress old data, alert	Add storage, optimize retention
API rate limiting	429 response detection	Exponential backoff, priority queue (risk > signal > info), fallback API	Optimize request frequency, negotiate higher limits
Multiple simultaneous	Compound failure detector	Escalate circuit breaker level, reduce to minimal safe mode	Step-by-step recovery with verification at each step
Unknown failure	Catch-all exception handler	Log everything, flatten positions, notify CEO	Full investigation, add to failure catalogue
State and position reconciliation: a cada 10 segundos, reconciliar estado interno do bot (posições, ordens pendentes, saldos) com estado da exchange via REST query. Discrepância → alert + investigação + correção automática se possível, manual se não.

Idempotency: toda operação que pode ser repetida (retry) é idempotente por design — executar 2x produz mesmo resultado que 1x. Implementado via: unique order IDs (nonce), state machine transitions que verificam estado atual antes de transicionar.

Ω-17 — PSICOLOGIA COMPUTACIONAL DO MERCADO

Emoções coletivas como variáveis de estado inferidas de dados observáveis:

Emoção	Proxy Observável	Threshold
Medo	Vol implícita > percentil 90, put/call ratio > 1.3, funding < -0.05%	Combinação ≥ 2/3
Ganância	Vol implícita < percentil 10, funding > 0.1%, OI crescente rápido	Combinação ≥ 2/3
Esperança	Pullback em uptrend com funding moderado, inflows crescentes	Pullback + inflows
Desespero	Vendas em cascata com volume crescente em down, funding muito negativo	Cascading + funding
Euforia	Parabolic move + social sentiment > 95th percentile + funding extremo	Trifecta
Pânico	Flash crash + liquidations > p99 + spread widening > 5x normal	Trifecta
Apatia	Volume < p10, spread widening, funding ≈ 0, OI estável	Volume + spread
Capitulação	Venda de alto volume após período prolongado de queda, SOPR < 1	Volume spike + SOPR
FOMO	Compra acelerando em rally estabelecido com funding crescente	Buy acceleration + funding
Modelo de estado emocional: Hidden Markov Model com 9 estados emocionais acima. Transições estimadas empiricamente. Estado emocional atual inferido com distribuição de probabilidade posterior → informar estratégia:

Medo extremo → contrarian long (com confirmação de suporte de microestrutura)
Ganância extrema → contrarian short (com confirmação de resistência de microestrutura)
Pânico → NO TRADE (liquidez desaparece, spread explode, execution quality deteriora catastroficamente)
Capitulação → bottom fishing com sizing mínimo e stop apertado
Euforia → short com convexidade (opções ou sized para que perda máxima seja pequena mas ganho potencial grande)
Ω-18 — CONTRA-INTELIGÊNCIA ALGORÍTMICA

Fingerprinting de competidores: para cada bot/algoritmo detectado no order flow:

Timing signature: distribuição de inter-order times, reaction latency, periodicidade
Sizing signature: distribuição de tamanhos, incrementos, relação com profundidade
Aggression signature: ratio market/limit, tendência a cross the spread, FOK vs IOC vs GTC
Cancel signature: cancel rate, cancel latency, cancel-to-fill ratio, cancel correlação com price movement
Behavioral signature: resposta a eventos (como reage a trade grande, a spike de vol, a gap)
Base de dados de fingerprints: catálogo de bots identificados com perfis atualizados continuamente. Quando novo bot aparece (fingerprint não reconhecido), período de observação e aprendizado antes de tentar explorar.

Inferência de estratégia: dado fingerprint → inferir via inverse reinforcement learning qual é a função de utilidade implícita → deduzir estratégia → prever próxima ação → posicionar para explorar. Exemplo: se bot X é detectado como market maker com inventory target de zero e rebalanceamento a cada 30s, antecipar que quando seu inventory fica extremo ele vai rebalancear agressivamente → posicionar na mesma direção do rebalanceamento esperado.

Counter-exploitation defense: o SOLÉNN também pode ser fingerprinted por outros. Contra-medidas: (i) randomização de timing (jitter de ±5-50ms), (ii) variação de sizing (±10-20% aleatório), (iii) randomização de order type mix, (iv) periodic strategy rotation para mudar fingerprint, (v) decoy orders (dentro de compliance — ordens genuínas colocadas com intenção de executar mas com timing e sizing variados para mascarar padrão).

Ω-19 — PORTFÓLIO MULTI-ESTRATÉGIA

Teoria de portfólio estendida para estratégias (não apenas ativos):

Cada estratégia S_i tem: E[R_i] (retorno esperado), σ_i (vol), ρ_ij (correlação entre estratégias i e j), Skew_i, Kurt_i, max_DD_i, Sharpe_i, Sortino_i, tail_dependence_ij.

Fronteira eficiente de estratégias: combinação de estratégias que maximiza Sharpe (ou Sortino) do portfólio sujeito a constraints: max_DD_portfolio < 2%, max_correlation entre qualquer par < 0.3, min_strategies ≥ 3 para diversificação.

Alocação dinâmica: pesos das estratégias atualizados em tempo real por:
(i) Thompson Sampling (bayesian multi-armed bandit) — cada estratégia é um braço com posterior Beta(α_i, β_i) sobre win rate, atualizado a cada trade.
(ii) Online Portfolio Selection (OPS) — algoritmo OLMAR/PAMR para alocação adaptativa.
(iii) Meta-strategy: quando correlation entre estratégias muda de regime, re-otimizar pesos.

Sharpe do portfólio > qualquer estratégia individual: garantido por diversificação quando correlações < 1. Sharpe_portfolio = E[R_p] / σ_p onde σ_p = √(w^T Σ w) < Σ w_i σ_i (desigualdade de Cauchy-Schwarz quando ρ < 1).

Ω-20 — MONTE CARLO DE TRAJETÓRIAS (BACKGROUND PERMANENTE)

Simulação contínua em background: 10⁴ - 10⁶ trajetórias de capital simuladas usando:

Distribuição empírica de P&L por trade (não gaussiana — caudas pesadas com GPD fit)
Condicionada a regime corrente e previsão de regime futuro
Com correlação serial (trades não são i.i.d. — clustering de vitórias e perdas)
Com funding costs, comissões, slippage estimado
Outputs atualizados a cada minuto:

P(atingir meta de 70k USD) com intervalo de confiança
P(drawdown > 2%) em qualquer ponto futuro
P(drawdown > 3% = catastrófico)
Sizing ótimo para maximizar P(meta) sujeito a P(ruin) < 10⁻⁶
Tempo esperado para atingir meta (com percentis 25/50/75/95)
Alertas se parâmetros reais divergem significativamente dos projetados
Calibração contínua: distribuição empírica de P&L é atualizada a cada trade. Se distribuição empírica recente (últimos 50 trades) difere significativamente da distribuição usada na simulação (teste KS, p < 0.05), re-calibrar simulação e alertar CEO.