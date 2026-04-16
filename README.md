# Optiver Quant Analytics Engine & Signal Platform

A high-throughput, low-latency market data analytics and algorithmic trading platform designed for real-time quantitative research and signal generation. This platform specializes in capturing alpha through **Order Book Imbalance (OBI)** and **Micro-price** statistical arbitrage.

![Dashboard Preview] 
*Note: Run the tool and replace this with your own screenshot!*

---

## 🎯 Problem Statement & Core Objective

In High-Frequency Trading (HFT), the standard "Mid-price" ($\frac{Bid + Ask}{2}$) is often a lagging indicator. It fails to account for the **depth** of the market and the **liquidity skew** between buyers and sellers. Processing these order book events at scale requires massive computational overhead and low-latency infrastructure.

**The Solution:** This platform provides an end-to-end, sub-millisecond pipeline that:
1.  **Ingests** massive streams of L2 market events.
2.  **Calculates** high-fidelity features (Micro-price/OBI) using vectorized memory engines.
3.  **Executes** statistical models to identify temporary market inefficiencies.
4.  **Persists** data into industrial-grade Delta Lakes for continuous strategy refinement.

---

## 🔬 Theoretical Framework & Math

The platform is engineered around the physics of market microstructure:

### 1. Order Book Imbalance (OBI)
OBI quantifies the relative buying vs. selling pressure at the best bid and offer (BBO). It is a predictor of short-term price direction.
- **Formula:** 
$$OBI = \frac{Size_{bid} - Size_{ask}}{Size_{bid} + Size_{ask}}$$
- **Range:** $[-1, 1]$.
    - $OBI \to 1$: Heavy buying pressure; high probability of an upward "tick".
    - $OBI \to -1$: Heavy selling pressure; high probability of a downward "tick".

### 2. Micro-price
The Micro-price is a "fair value" estimate that incorporates order sizes, making it less susceptible to "bid-ask bounce" and more reflective of true market intent.
- **Formula:** 
$$P_{micro} = \frac{Price_{bid} \times Size_{ask} + Price_{ask} \times Size_{bid}}{Size_{bid} + Size_{ask}}$$
- **Key Insight:** When the bid size is significantly larger than the ask size, the Micro-price moves closer to the ask price, signaling an imminent upward shift in the mid-price.

---

## 🏆 Key Accomplishments

-   **Zero-Copy Pipeline:** Utilizes **PyArrow** and **Protobuf** to move data from Kafka to the analysis engine with minimal CPU overhead.
-   **Vectorized Feature Engineering:** Leverages the **Polars** OLAP engine to conduct 100ms windowed aggregations on tens of thousands of messages per second.
-   **Industrial Storage:** Integrated **Delta Lake** (Hive-partitioned) for immutable, time-travel-capable historical data storage.
-   **Integrated Research Lab:** A custom-built UI and API that allows for real-time backtesting and **Auto-Refinement** of strategy parameters via grid search.
-   **High-Frequency Simulation:** Built a high-performance **Geometric Brownian Motion (GBM)** simulator capable of generating 50,000+ ticks/sec to stress-test the stack.

---

## 🏗️ System Architecture

1.  **Market Producer:** Streams L2 data into Kafka. Includes a GBM-based `MarketSimulator`.
2.  **Real-Time Engine:** Subscribes to Kafka, maps payloads to PyArrow, and conducts vectorized feature engineering.
3.  **Delta Lake Storage:** Immutable Hive-partitioned records for auditing and backtesting.
4.  **Strategy Research Lab (UI):** Direct browser-based control for strategy optimization and backtesting.
5.  **React Dashboard:** Real-time visualization of spreads, OBI, and generated trade signals.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- [Poetry](https://python-poetry.org/)
- Docker & Docker Compose

### Fast Launch
```bash
# Start Kafka, Redpanda, Engine, Producer, API, Frontend, and Prometheus
docker-compose up -d --build

# Real-Time Dashboard & Research Lab: http://localhost:5173
# Prometheus Metrics: http://localhost:9090
```

---

## 🧪 Backtesting & Strategy Refinement

The platform includes a **Strategy Research Lab** integrated into the UI, powered by a dedicated `BacktestingEngine`.

### Manual Backtesting
Adjust the **OBI Threshold** slider in the UI to see how your strategy would have performed on historical data. View **Total PNL**, **Win Rate**, and **Trade Count** instantly.

### Auto-Refining Strategies
The `AUTO-REFINE` feature allows AI agents or researchers to perform an automated grid search to find the optimal threshold that maximizes signal density and PNL.

---

## 🔌 Live Broker Integration

To use live data, replace `MarketSimulator` with a broker-specific client (e.g., Alpaca, IBKR, or Binance).
1. Create `src/broker_producer.py`.
2. Map the broker's WebSocket message to our `MarketData` protobuf schema.
3. Update `docker-compose.yml` to point to the new producer.

---

## 👨‍💻 Author
**Rishabh Patil**
Quantitative Developer & Systems Architect
