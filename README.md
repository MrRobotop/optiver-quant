# Optiver Quant Analytics Engine & Signal Platform

A high-throughput, low-latency market data analytics and algorithmic trading platform designed for real-time quantitative research and signal generation. This platform specializes in **Order Book Imbalance (OBI)** and **Micro-price** statistical arbitrage.

---

## 🔬 Theoretical Framework

This platform is built upon two core pillars of High-Frequency Trading (HFT) market microstructure:

### 1. Order Book Imbalance (OBI)
OBI measures the relative buying vs. selling pressure at the top of the order book.
- **Formula:** $OBI = \frac{Size_{bid} - Size_{ask}}{Size_{bid} + Size_{ask}}$
- **Purpose:** A high positive OBI suggests a high probability of a short-term price increase as buyers are aggressive, while a negative OBI suggests downward pressure.

### 2. Micro-price
Unlike the standard "Mid-price", the Micro-price accounts for the volume (size) of orders at the best bid and ask.
- **Formula:** $P_{micro} = \frac{Price_{bid} \times Size_{ask} + Price_{ask} \times Size_{bid}}{Size_{bid} + Size_{ask}}$
- **Purpose:** The Micro-price provides a more accurate "fair" value of the asset. It is more responsive to order book shifts and is often a leading indicator of where the mid-price will settle next.

---

## 🏗️ System Architecture

The platform operates as a distributed microservices ecosystem:

1.  **Market Producer:** An extensible service that streams L2 data into Kafka. It ships with a `MarketSimulator` that uses Geometric Brownian Motion (GBM) to simulate realistic price action.
2.  **Real-Time Engine:** Subscribes to Kafka, maps Protobuf payloads to PyArrow blobs, and conducts vectorized feature engineering (OBI/Micro-price) using the `Polars` memory engine with 100ms bucketing.
3.  **Delta Lake Storage:** Provides an immutable, Hive-partitioned historical record of all processed quant features for backtesting and auditing.
4.  **React Dashboard:** A Vite/TypeScript frontend for real-time visualization of spreads, OBI, and generated trade signals.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- [Poetry](https://python-poetry.org/) (for dependency management)
- Docker & Docker Compose

### Fast Launch (Simulated Mode)
```bash
# Bring up the entire stack (Kafka, Redpanda, Engine, Producer, Frontend, Prometheus)
docker-compose up -d --build

# Access the Real-Time Dashboard
# http://localhost:5173

# Monitor System Stats via Prometheus
# http://localhost:8002/metrics
```

---

## 🔌 Live Broker Integration

To use this tool with real live data, you must replace the `MarketSimulator` with a broker-specific client.

### How to connect your own API Key:

1.  **Choose your Broker:** Most quants use **Alpaca**, **Interactive Brokers (IBKR)**, or **Binance**.
2.  **Create a new Producer:** Create `src/broker_producer.py`.
3.  **Map to Schema:** Convert the broker's WebSocket message format into our `MarketData` protobuf schema.

**Example (Conceptual Alpaca implementation):**
```python
import os
from alpaca.data.live import StockDataStream
from schema.market_data_pb2 import MarketData

# Load your API Keys
api_key = os.environ.get("ALPACA_KEY")
secret_key = os.environ.get("ALPACA_SECRET")

stream = StockDataStream(api_key, secret_key)

async def quote_handler(data):
    md = MarketData()
    md.timestamp_ns = data.timestamp.value
    md.symbol = data.symbol
    md.bid_price = data.bid_price
    md.ask_price = data.ask_price
    md.bid_size = data.bid_size
    md.ask_size = data.ask_size
    
    # Push to Kafka (topic: market-events)
    kafka_producer.produce("market-events", md.SerializeToString())

stream.subscribe_quotes(quote_handler, "AAPL", "MSFT", "TSLA")
stream.run()
```

4.  **Update `docker-compose.yml`:** Point the `producer` service to your new script and inject your API keys as environment variables.

---

## 🛠️ Strategy SDK (For Quants)

We have engineered an extensible SDK so quants can focus on math, not infrastructure.

### Writing a Custom Strategy
1.  Navigate to `src/strategy/`.
2.  Extend `BaseStrategy` and implement the `analyze(self, df)` method.
3.  `df` is a 100ms-bucketed `polars.DataFrame` containing pre-calculated `obi_avg` and `micro_price_avg`.

```python
import polars as pl
from .base import BaseStrategy

class MyAlphaStrategy(BaseStrategy):
    def analyze(self, df: pl.DataFrame):
        # Your statistical arbitrage logic here
        # Return a list of TradeSignal() objects
        pass
```

4.  Register your strategy in `src/engine.py`.

---

## 🧪 Backtesting & Strategy Refinement

The platform includes a dedicated `BacktestingEngine` and `StrategyRefiner` to allow users (and AI agents) to validate strategies against historical data before going live.

### Running a Backtest
Historical data is automatically loaded from the Delta Lake storage. The engine simulates the flow of time by feeding data to your strategy in chronological order.

```bash
# Run the built-in backtester
python -m src.backtester

# Output Example:
# INFO:__main__:Loading historical data from storage/delta_lake...
# INFO:__main__:Running backtest for strategy: ObiStrategy
# Threshold: 0.5 | Signals: 808
# Threshold: 0.7 | Signals: 224
# Threshold: 0.9 | Signals: 43
```

### Auto-Refining Strategies (For AI Agents)
The `StrategyRefiner` allows for automated parameter optimization. For example, it can perform a grid search to find the OBI threshold that maximizes signal generation or theoretical PNL.

```bash
# Run the strategy refiner
python -m src.refiner

# Output Example:
# INFO:__main__:Refining OBI Strategy for TICK0...
# INFO:__main__:Tested Threshold 0.10 -> 15961 signals
# INFO:__main__:Tested Threshold 0.50 -> 808 signals
# INFO:__main__:Tested Threshold 0.90 -> 43 signals
# INFO:__main__:Optimization complete. Best OBI threshold: 0.10
```

**Refinement Workflow:**
1.  **Collect Data:** Run the system in simulation mode for a few hours to populate Delta Lake.
2.  **Analyze:** Use `src/backtester.py` to see current performance.
3.  **Optimize:** Run `src/refiner.py` to find optimal parameters.
4.  **Deploy:** Update your strategy with the new parameters in `src/engine.py`.

---

## 📊 Monitoring & Performance
The system utilizes robust exponential backoff routines to tolerate connection jitter.
- **Pipeline Latency:** Tracked per-message from producer to signal.
- **Throughput:** Capable of processing >50,000 events/sec on a single node.
- **Metrics:** Native Prometheus export on port `:8002/metrics`.
