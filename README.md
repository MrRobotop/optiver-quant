# Optiver Quant Analytics Engine & Signal Platform

A high-throughput, low-latency market data analytics and algorithmic trading platform designed for real-time quantitative research and signal generation. This platform specializes in **Order Book Imbalance (OBI)** and **Micro-price** statistical arbitrage.

![Dashboard Preview](https://via.placeholder.com/1000x500.png?text=Dashboard+UI+Preview+Placeholder) 
*Note: Run the tool and replace this with your own screenshot!*

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
4.  **Strategy Research Lab (UI):** A dedicated interface to trigger backtests and auto-refine strategy parameters natively in the browser.
5.  **React Dashboard:** A Vite/TypeScript frontend for real-time visualization of spreads, OBI, and generated trade signals.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- [Poetry](https://python-poetry.org/) (for dependency management)
- Docker & Docker Compose

### Fast Launch (Simulated Mode)
```bash
# Bring up the entire stack (Kafka, Redpanda, Engine, Producer, API, Frontend, Prometheus)
docker-compose up -d --build

# Access the Real-Time Dashboard & Research Lab
# http://localhost:5173

# Monitor System Stats via Prometheus
# http://localhost:9090
```

---

## 🧪 Backtesting & Strategy Refinement

The platform includes a **Strategy Research Lab** integrated directly into the UI, powered by a dedicated `BacktestingEngine` and `StrategyRefiner`.

### Manual Backtesting
Select a ticker in the dashboard and use the **Strategy Research Lab** panel to:
1. Adjust the **OBI Threshold** slider.
2. Click **BACKTEST** to run your strategy against all historical data in Delta Lake.
3. Instantly view **Total PNL**, **Win Rate**, and **Trade Count**.

### Auto-Refining Strategies (For AI Agents)
The `AUTO-REFINE` feature performs an automated grid search across parameter spaces (e.g., OBI thresholds from 0.1 to 0.9) to find the configuration that maximizes performance metrics.

```bash
# CLI usage is also supported:
python -m src.backtester
python -m src.refiner
```

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

## 🔌 Live Broker Integration

To use this tool with real live data, replace the `MarketSimulator` with a broker-specific client.

### How to connect your own API Key:
1.  **Create a new Producer:** Create `src/broker_producer.py`.
2.  **Map to Schema:** Convert the broker's WebSocket message (e.g., from Alpaca, IBKR, or Binance) into our `MarketData` protobuf schema.
3.  **Update `docker-compose.yml`:** Point the `producer` service to your new script and inject your API keys as environment variables.

---

## 📊 Monitoring & Performance
The system utilizes robust exponential backoff routines to tolerate connection jitter.
- **Pipeline Latency:** Tracked per-message from producer to signal.
- **Throughput:** Capable of processing >50,000 events/sec on a single node.
- **Metrics:** Native Prometheus export on port `:8002/metrics`.
