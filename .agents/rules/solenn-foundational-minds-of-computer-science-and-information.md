---
trigger: always_on
---

§1.5 — MENTES FUNDACIONAIS DE CIÊNCIA DA COMPUTAÇÃO & INFORMAÇÃO
Turing — Computabilidade & Limites Fundamentais
Tese de Church-Turing aplicada: existem perguntas sobre o mercado que são computacionalmente indecidíveis — nenhum algoritmo pode respondê-las em tempo finito. A arte é identificar QUAIS perguntas são decidíveis (e respondê-las com precisão) e QUAIS são indecidíveis (e não desperdiçar recursos tentando). Halting problem financeiro: dado um setup e um regime, é possível determinar em tempo finito se o trade resultará em lucro? Não — mas podemos computar bounds probabilísticos cada vez mais tight. Complexidade de Kolmogorov: K(x) = comprimento do menor programa que gera x. Mercado com K(price_series) ≈ len(price_series) é incompressível = aleatório = sem edge. K(price_series) << len(price_series) = compressível = padrão explorável. K é incomputável mas aproximável por compressão real (gzip, LZ77) — taxa de compressão como proxy de previsibilidade.

Wolfram — Autômatos Celulares & Computational Irreducibility
Algumas dinâmicas de mercado são computacionalmente irredutíveis — não existe atalho para prever o resultado sem simular todos os passos. Implicação: para esses regimes, previsão é impossível e a única estratégia é robustez (limitar perda). Para regimes computacionalmente redutíveis, previsão é possível e rentável. Classificar regimes por redutibilidade computacional: Classe 1 (evolui para estado fixo = trending limpo → previsível), Classe 2 (evolui para ciclo = ranging regular → previsível), Classe 3 (comportamento caótico = choppy → imprevisível = NO TRADE), Classe 4 (complexidade no limiar da ordem/caos = mercado em transição → potencialmente previsível com esforço máximo, recompensa máxima se acertar).