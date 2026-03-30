---
trigger: always_on
---

§1.4 — MENTES FUNDACIONAIS DE QUANTITATIVE FINANCE
Shaw/Griffin/Asness — Infraestrutura & Factor Investing
Vantagem competitiva em 3 pilares: (i) infraestrutura tecnológica superior (latência, throughput, uptime, resiliência), (ii) engenharia reversa de market makers (inferir inventory, risk limits, quoting algorithm, hedge ratios), (iii) factor investing multi-escala. Factors em escalas de segundos: momentum (autocorrelação de retornos em 1s, 5s, 30s), value (distância de VWAP/fair value), carry (funding rate instantâneo), volatility (vol realizada vs implícita), quality (consistência de microestrutura = narrow spread, deep book, low cancel rate), liquidity (capacidade de absorção sem market impact). Cada factor tem Sharpe ajustado por regime que é rebalanceado continuamente. Decomposição de retorno: R_total = α + Σᵢ βᵢ·Fᵢ + ε onde α = alpha genuíno, βᵢ·Fᵢ = exposição a fatores, ε = ruído. Se α ≈ 0 após controlar por fatores, o "edge" é na verdade exposição a fator → frágil porque fatores são cíclicos. Alpha genuíno deve ser positivo após controle por TODOS os fatores conhecidos.