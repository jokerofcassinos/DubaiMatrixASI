# Phase 8: Market Data Layer Analysis Report
**Target**: `core/market/` Directory
**Status**: Completed

## 1. Architectural Overview

The Market Data Layer is the sensory nervous system of the ASI. It does not make trading decisions; it gathers, aggregates, formats, and historicizes multi-modal data streams for the Agent Swarm. 

**Sub-Components:**
1. **Data Engine (`data_engine.py`)**: Central hub and atomic snapshot creator.
2. **MT5 Bridge (`mt5_bridge.py`)**: The primary execution and perception link to the broker. Features a dual-path architecture (Socket vs MT5 Native).
3. **Orderflow Matrix (`orderflow_matrix.py`)**: Microstructure decoder looking for absorption and exhaustion.
4. **Memory Subsystem (`memory/`)**: Time-Series RAG (`episodic_memory.py`) and NLP for tape reading (`semantic_nlp.py`).
5. **Scraper Subsystem (`scraper/`)**: Off-chain and On-chain background workers capturing zero-cost API data (macro, sentiment, on-chain pressure).

## 2. Key Mechanisms & Innovations

### Dual-Path MT5 Bridge
The `mt5_bridge` utilizes a fascinating dual-path architecture to combat MT5 Python API latency:
- **HFT Socket Tunnel**: Starts a TCP server on port 5555. An underlying MQL5 Expert Advisor connects to this socket, streaming sub-millisecond tick data and directly receiving string-based execution commands (`LIMIT|BUY|...`).
- **Native Fallback**: If the socket crashes or stalls, the system seamlessly falls back to the native `MetaTrader5` Python package (slower, but highly reliable). 

### Data Engine: Zero-Latency Worker and Liquid State Reservoir
- The engine uses a background worker thread to pull multi-timeframe candles and calculate heavy indicators (EMAs, ATR, RSI, VWAP). This prevents the main loop from blocking.
- Incorporates a **Liquid State Reservoir** concept, perturbing a state space model with raw ticks and velocity measures to simulate cognitive sensory processing and "V-Pulse" detection (market ignition).

### Semantic NLP & Episodic Memory
- **Semantic NLP**: Translates order flow ticks into discrete categorical tokens (e.g., `WHALE_BUY_BOMB`, `RETAIL_NOISE`) and applies a primitive Multi-Head Attention layer in raw Numpy.
- **Episodic Memory**: Employs a vector database to search previous market snapshots and calculates a bias/confidence score for "Market Intuition", leaning on a fast C++ KNN search. 

### Web Scrapers
Background threads repeatedly ping free endpoints (CoinGecko, Alternative.me, Mempool.space, Blockchain.com). They use exponential backoff and gracefully handle timeouts to construct `SentimentSnapshot`, `MacroSnapshot`, and `OnChainSnapshot`.

## 3. Bugs, Weaknesses & Vulnerabilities

### ⚠️ HIGH RISK: Socket Desync in Orders (`mt5_bridge.py`)
When sending a LIMIT or MARKET order through the HFT socket, the Python code returns immediately with a dummy ticket (`"ticket": 0`). The real ticket arrives asynchronously via the `_handle_socket_data` loop and invokes `trade_registry.update_ticket(0, ticket)`.
- **The Issue**: If two socket orders are sent consecutively (e.g., Hydra mode sending 5 slots), **multiple pending requests** will have a ticket of `0`. The registry updater cannot reliably distinguish which real ticket belongs to which intent simply by mapping `0` to the incoming ticket. This leads to profound "Amnesia" where intents become unlinked.

### ⚠️ MEDIUM RISK: Round-Turn Logic Hardcoding (`detect_broker_commission`)
In `mt5_bridge.py`, if historical deals have zero commissions, it hardcodes `OMEGA.get("commission_per_lot", 15.0)` or returns `7.0`. Some FTMO/Prop firm indices (like NAS100 or US30) simply have 0 commission but feature baked-in spreads. Hardcoding high dynamic commissions can artificially restrict Smart TP logic and overstate break-even requirements on indices.

### ⚠️ MEDIUM RISK: Memory Leak Potential (`episodic_memory.py`)
`EpisodicMemory` keeps the vector database in `numpy.ndarray`. The `np.vstack` operation is extremely inefficient (O(N) copy) when performed thousands of times per session. While capped at `max_episodes`, accumulating 10,000 arrays dynamically using `vstack` will drastically slow down the event loop and fragment memory over time. Pre-allocation of the array combined with a moving index indicator would be standard.

## 4. Next Steps
The sensory array is complex and highly capable, but the async ticket syncing via the custom TCP tunnel has a terrifyingly high chance of creating race conditions during concurrent `SniperExecutor` strikes.

Phase 8 is complete. We should now move to **Phase 9: Config & Utils Layer** (`config/`, `utils/`, and UI/Websockets) or directly into the C++ Engine (Phase 10).
