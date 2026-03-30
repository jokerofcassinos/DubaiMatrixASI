---
trigger: always_on
---

META-INTELIGÊNCIA & EVOLUÇÃO (Ω-31 a Ω-40) - part 2
HTF Context Objects: cada HTF timeframe produz "context object" que é passado para LTF como input:

text

HTF_Context = {
    bias: "bullish" | "bearish" | "neutral",
    bias_strength: float [0,1],
    key_levels: [price_levels with type (S/R/OB/FVG/liquidity)],
    current_structure: "HH-HL" | "LH-LL" | "range" | "complex",
    volatility_context: "expanding" | "contracting" | "stable",
    nearest_poi: {price, type, distance},
    invalidation_level: price,
    next_targets: [price_levels]
}
Ω-37 — OPPORTUNITY COST ENGINE (OCE)

Problema original: "muitas oportunidades de entrada a ASI deixa passar."

Solução — Análise sistemática de trades NÃO tomados:

Para CADA setup que passou por ≥50% do pipeline de validação mas foi REJEITADO:

Registrar: timestamp, razão da rejeição (qual filtro bloqueou), estado do mercado
Rastrear: o que o preço fez DEPOIS da rejeição (o trade teria sido lucrativo?)
Classificar: Rejected-Right (rejeitou e teria perdido → filtro correto), Rejected-Wrong (rejeitou e teria lucrado → filtro excessivamente conservador)
Quantificar: Opportunity Cost = Σ (profit_of_rejected_winning_trades) × sizing_that_would_have_been_used
Otimizar: para cada filtro, calcular True Positive Rate (setups ruins rejeitados) vs False Positive Rate (setups bons rejeitados). Ajustar threshold de cada filtro para maximizar TPR - FPR (Youden's J statistic)
Meta: reduzir Rejected-Wrong sem aumentar Rejected-Right-that-becomes-Wrong. Tradeoff fundamental: ser conservador demais perde dinheiro por inação, ser agressivo demais perde por ação errada. O ótimo é mensurável e encontrável.

Rolling dashboard de oportunidades perdidas: CEO pode ver em tempo real: "hoje rejeitamos 47 setups. 42 teriam perdido (correto). 5 teriam lucrado (oportunidade perdida = $X). Filtros mais restritivos: regime_filter (bloqueou 3 dos 5), confidence_threshold (bloqueou 2 dos 5)."

Ω-38 — ADAPTIVE COMMISSION-AWARE OPTIMIZATION

Problema original: "cada lote tem comissão de uns $40, então se fizermos $80 só pegamos $40 para lucro."

Solução — Otimização commission-aware de ponta a ponta:

Minimum Viable Profit (MVP): para cada trade, calcular MVP = commission_entry + commission_exit + slippage_expected + funding_cost_expected. Trade com E[gross_profit] < MVP × safety_margin (1.5x) → REJEITADO. Não adianta ter edge de $30 se custos são $40.

Commission-adjusted Sharpe: Sharpe_net = E[R - C] / σ(R - C) onde C = custo total por trade. Otimizar Sharpe_net, não Sharpe_gross.

Trade frequency optimization: dado commission structure, existe frequência ótima de trading. Muito frequente → commissions destroem alpha. Pouco frequente → alpha não capturado. f* = argmax_f [f × E[profit_per_trade|f] - f × E[cost_per_trade|f]] considerando que E[profit_per_trade] pode depender de f (trades mais seletivos = mais rentáveis por trade).

Tier optimization: exchanges oferecem fee tiers por volume. Mapear exatamente quanto volume é necessário para próximo tier → calcular se o desconto justifica volume adicional → se sim, ajustar sizing/frequência para atingir tier.

Maker vs Taker optimization: ordens maker (limit) têm fee menor (ou rebate) vs taker (market). Para cada setup, avaliar: "posso esperar e usar limit order sem perder o trade?" Se sim, economizar $X em comissão. Se não (urgência alta), usar market e aceitar o custo. Ratio maker/taker é otimizado continuamente.

Ω-39 — PROGRESSIVE CONFIDENCE SCALING

Sizing adaptativo por confiança crescente:

Não entrar com position completa de uma vez — entrar progressivamente à medida que confirmações chegam:

text

Fase 1 (Sinal Inicial): 20% do sizing total
  Trigger: confluência primária atingida (3+ sinais alinhados)
  
Fase 2 (Confirmação): +30% (total 50%)
  Trigger: price action confirma direção, order flow sustentado
  
Fase 3 (Validação): +30% (total 80%)
  Trigger: HTF confirma, regime confirma, funding não adverso
  
Fase 4 (Full Conviction): +20% (total 100%)
  Trigger: momentum acelerado, todas métricas confirmando

Scaling reverso (de-escalation):
  Se qualquer trigger de fase anterior invalidar, REDUZIR para sizing da fase anterior
  Se sinal original invalidar, FECHAR tudo
Vantagem: se o trade está errado, perde apenas 20% do sizing no pior caso (fase 1 falhou imediatamente). Se está certo, captura 80-100% do movimento com sizing crescente. Payoff assimétrico por construção.

Ω-40 — FATIGUE & DEGRADATION MONITORING

Monitoramento de degradação do próprio sistema:

Métrica	Significado	Threshold	Ação
Sharpe Rolling 50 trades	Performance recente	< 2.0	Investigar, reduzir sizing
Hit Rate Rolling 50 trades	Precisão recente	< 55%	Investigar, re-calibrar modelos
Avg Win / Avg Loss Rolling	Qualidade de trades	< 1.5	Investigar exits
Consecutive Losses	Streak negativa	> 5	Pausa automática, diagnóstico
Time Since Last Win	Seca de vitórias	> 2 horas de trading ativo	Reduzir sizing 50%
Edge Decay Rate	dSharpe/dt	Negativo por 24h+	Alerta CEO, possível regime shift permanente
Model Residual Growth	Erro do modelo crescendo	> 2σ do baseline	Re-calibrar ou desativar modelo
Feature Importance Shift	Features mudaram de importância	Top 3 features mudaram	Possível mudança de estrutura de mercado
