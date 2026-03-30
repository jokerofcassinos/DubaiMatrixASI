---
trigger: always_on
---

TARGETS QUANTITATIVOS (FLOORS, NÃO CEILINGS):

Métrica	Floor	Stretch	Medição
P&L Acumulado	≥ $70,000 USD	$150,000+	P&L líquido (após comissões, slippage, funding)
Número de Trades	≥ 200	500+	Trades executados e fechados
Win Rate	≥ 97%	~100%	Trades lucrativos / total
Sharpe Ratio	> 5.0	> 10.0	Annualized, net of costs
Sortino Ratio	> 8.0	> 15.0	Annualized, net of costs
Max Drawdown	< 2.0%	< 1.0%	Peak-to-trough, intraday
Profit Factor	> 15.0	> 50.0	Gross profit / Gross loss
Avg Win / Avg Loss	> 3.0	> 5.0	Mean of winning trades / Mean of losing trades
Expectancy	Positiva e crescente	> $200/trade	E[P&L per trade] = WR × AvgWin - (1-WR) × AvgLoss
Recovery Factor	> 15.0	> 30.0	Net profit / Max drawdown
Calmar Ratio	> 10.0	> 20.0	Annualized return / Max drawdown
Payoff Ratio	> 2.0	> 4.0	Average win / Average loss
Maximum Consecutive Losses	≤ 3	≤ 1	Longest losing streak
Time in Market	< 30%	< 15%	% of time with open position
Alpha Decay	Negativo e decrescente	Near zero	d(alpha)/dt
TRADE PERDEDOR = BUG P0: qualquer trade que feche em prejuízo dispara protocolo de investigação forense de 12 camadas:

Camada 1 — Data Integrity: dados de entrada estavam corretos? Houve gap, delay, corrupção?
Camada 2 — Feature Computation: features foram computadas corretamente? Overflow, underflow, division by zero, stale data?
Camada 3 — Signal Generation: sinal foi gerado corretamente pelo modelo? Inputs corretos, lógica correta, thresholds corretos?
Camada 4 — Confluence Evaluation: confluência foi avaliada corretamente? Todos os filtros funcionaram? Algum filtro deveria ter rejeitado?
Camada 5 — Regime Context: regime foi identificado corretamente? Se regime mudou durante o trade, foi detectado a tempo?
Camada 6 — Risk Assessment: risco foi avaliado corretamente? Position size era adequado? Stop era adequado?
Camada 7 — Execution Quality: execução foi de qualidade? Slippage dentro do esperado? Latência dentro do esperado?
Camada 8 — Exit Logic: saída foi executada corretamente? Triggers de saída funcionaram? Algum trigger deveria ter disparado antes?
Camada 9 — Market Condition: condição de mercado era genuinamente adversa (flash crash, manipulação, evento inesperado) ou era previsível?
Camada 10 — Model Adequacy: o modelo era adequado para este regime/condição? Estávamos operando fora do domínio de validade do modelo?
Camada 11 — Contrafactual: o que teria acontecido com timing/sizing/exit/order-type diferentes? Superfície contrafactual completa.
Camada 12 — Root Cause & Patch: causa raiz identificada → patch cirúrgico → code review aerospace-grade → 47 variantes testadas → 50 trades paper validation → deploy → monitoramento pós-patch por 100 trades → post-mortem permanente arquivado no Knowledge Graph → NUNCA o mesmo bug causa outra perda.