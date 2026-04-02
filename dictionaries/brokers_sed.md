# SED — BROKERS DE ALPHA REAL (MT5 e BINANCE HFT-P)
**Dicionário Evolutivo Vivo (Knowledge Graph)**

## 1. Módulos Transmutados (Execução Absoluta)
| Módulo Original | Novo Módulo SOLÉNN Ω | Path |
| :--- | :--- | :--- |
| `mt5_connector.py` genérico | `mt5_connector.py` Threads | `market/exchanges/mt5_connector.py` |
| Mock Poller Binace | Binance Raw WSS | `market/exchanges/binance_hftp.py` |

## 2. Visão Geopolítica da Evolução (Por Que a v2 é Superior)

### 2.1 Meta-Bridge (FTMO Limits Integrados na Raiz)
**Limitações da v1:** As chamadas MQL5 travavam o EventLoop nativo, criando "engasgos" visuais na interface e perigo de "slippage delay" nas outras rotinas preditivas.
**Superioridade v2 (Ω-45):**
* Adotou-se o Design Padrão de `ThreadPoolExecutor` com C-Python Wrapping. Isso envelopa chamadas de conexão síncrona `MetaTrader5` e joga-as em *side-threads*, resgatando sua resposta na *Main Loop Async* e permitindo fluxo O(1).
* Risco da Corretora In-Loco: Se o Equity cair -4% hoje, não esperamos o Risk Manager; a própria ponte REJEITA ordens bloqueando a execução e emitindo log de `CRITICAL_SHUTDOWN`.

### 2.2 Binance WSS Receptor (Cross Intelligence O(1))
**Limitações da v1:** Usávamos sleeps falsos. O pipeline não via liquidez.
**Superioridade v2 (Ω-22):**
* Foi acoplado à stream direta de tick real de mercado pela porta 9443 do backend da Binance Global (`btcusdt@ticker`).
* Uso de Back-pressure Handling: a *Queue* foi engessada em `maxlen=5000` via `collections.deque`. Overflow agora é impossível; Ticks velhos são varridos instantaneamente em O(1) e a Memória nunca engole o kernel do SO.

## 3. Knowledge Graph - Interconexões
* `executions_engine.py` --> [commands_to] --> `MetaBridge`
* `market/data_engine.py` <-- [feeds_from_callback] -- `BinanceHFTP`

## 4. Métricas Garantidas
* Latência Zero no *Event Loop* mesmo com atraso do servidor MT5.
* Auto-Reconnect Exponencial (máximo 30s) na quebra do link Websocket da Binance.
