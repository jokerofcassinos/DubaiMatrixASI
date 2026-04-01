# 📖 DICIONÁRIO EVOLUTIVO VIVO (SED) — Sensory Synchronization Ω

**Arquivo Relacionado:** `market/data_engine.py`, `market/hftp_bridge.py`, `main.py`  
**Conceito Arquitetural:** Omni-Data Engine (Ω-13) & Sovereign Bridge (Ω-6)

## 📌 CONTEXTO V1 vs V2

| Dimensão | v1 (DubaiMatrixASI) | v2 (SOLÉNN Ω) |
| :--- | :--- | :--- |
| **Sincronismo** | MT5 Python API (Síncrono/Lento) | TCP/MsgPack Assíncrono |
| **Integridade** | Confiança cega nos ticks | Z-Score/CRC32/Monotonicity |
| **Performance** | Memory leaks e OOM | PriorityQueue Lock-Free, Dual Channel |
| **Confiabilidade** | Quedas derrubavam a análise | Watchdog/Heartbeat 1s/Jitter Auth |

Na v1, a captura de dados dependia exclusivamente da API C do MT5 via polling. Isso gerava latências altíssimas (> 50ms), resultando em sinal degradado. O *Omni-Data Engine Ω-13* e *HFTP-P Bridge* abolem a necessidade da biblioteca pública. A ponte foi construída com `socket.TCP_NODELAY`, `MsgPack` nativo bi-direcional e Isolamento OOM (Bounding Priority Queues).

## 🧩 DNA DOS VETORES DE IMPLEMENTAÇÃO

### Omni-Data Engine (1.1 - 1.6)
*   **[V1.1.5] - Priority Queue Ingestion:** Em mercados de pânico, ticks institucionais de alto volume possuem tag de prioridade, furando a fila dos demais.
*   **[V1.2.9] - Schema Normalization & Zero-Copy:** `MarketData` normalizado e transformado numa interface imutável de slots.
*   **[V1.4.3] - Neural Validation Check-Gate:** Wash Trading proxies identificados e distorções (Negative Volume, Infinity, Drift Time) corrigidas silenciosamente ou dropadas.
*   **[V1.5.5] - Lorentz-Clock Drift Compensation:** Garantia estrita de ordenação temporal.

### HFTP-P Bridge (2.1 - 2.6)
*   **[V2.4.2] - Handshake Sentinel:** Nenhuma conexão é autorizada sem o Token Auth no `HELLO` e handshake `WELCOME`.
*   **[V2.5.1] - OMS Fast-Path:** Canal de ordem dual e prioritário. Tick traffic não afoga cancelamentos ou requisições de compra de emergência.
*   **[V2.3.2] - Watchdog Anti-Hibernation:** Monitoramento constante por 5s; não recarrega, hiberna com dignidade (Fallback).

### Synaptic Integration (3.1 - 3.6 - Orquestrador)
*   **[V3.1.9] - Thread Isolation:** O Sensory Loop atua em Core isolado; falhas no cognitivo (Córtex) não seguram os logs.

## 🧬 CONEXÕES X² (KNOWLEDGE GRAPH)
1. **[Ω-13] -> [Ω-35]:** O `OmniDataEngine` roteia dados diretamente ao Sistema Nervoso ASI na memória sem perdas para as interfaces de Risk (DataEngine → RiskManager → ExecutionEngine).
2. **[Ω-6] -> [Ω-21]:** A execução se propaga via TCP_NODELAY para o MT5 em latências não documentadas publicamente.

## ⚖️ JUSTIFICATIVA TÁTICA (ABOLIÇÃO DO IMPOSSÍVEL)
Nós nos recusamos a tratar a latência como custo do negócio. Reduzindo I/O overhead do terminal limitamos Information Leakage (Ω-42). Além disso, a filtragem das métricas com robust Z-Score nos impede de gerar sinais falsos. O mercado mente via `Phantom Liquidity`. Estes arquivos filtram as falácias do Order Book em tempo real. Oráculo purificado.
