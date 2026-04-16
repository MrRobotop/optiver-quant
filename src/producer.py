import os
import sys
import time
import argparse
import numpy as np
from confluent_kafka import Producer
import logging

from schema.market_data_pb2 import MarketData
from src.monitor import start_metrics_server, messages_produced
from src.utils import KafkaCircuitBreaker, latency_tracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "localhost:19092")
TOPIC_NAME = "market-events"

class MarketSimulator:
    def __init__(self, symbols, initial_prices, tick_rate=10000):
        self.symbols = symbols
        self.prices = np.array(initial_prices, dtype=float)
        self.batch_size = max(1, tick_rate // 10)  # Produce in batches of 1/10th sec
        self.tick_rate = tick_rate
        
        self.mu = np.random.uniform(-0.002, 0.002, len(self.symbols))
        self.sigma = 0.002
        self.dt = 1.0
        
        conf = {
            'bootstrap.servers': KAFKA_BROKER,
            'queue.buffering.max.messages': 5000000,
            'linger.ms': 5,
            'batch.num.messages': 10000,
            'compression.type': 'lz4'
        }
        self.producer = Producer(conf)

    @KafkaCircuitBreaker(failure_threshold=3, recovery_timeout=5)
    def produce_batch(self, batch):
        for msg in batch:
            self.producer.produce(TOPIC_NAME, value=msg)
            messages_produced.inc()
        self.producer.poll(0)

    @latency_tracker(name="simulate_tick")
    def simulate_tick(self):
        # Update prices with GBM and mutating macro-drift
        self.mu += np.random.normal(0, 0.00005, len(self.symbols))
        self.mu = np.clip(self.mu, -0.005, 0.005)
        
        Z = np.random.normal(0, 1, len(self.symbols))
        self.prices = self.prices * np.exp((self.mu - 0.5 * self.sigma**2) * self.dt + self.sigma * np.sqrt(self.dt) * Z)
        
        batch = []
        now_ns = time.time_ns()
        for i, sym in enumerate(self.symbols):
            price = self.prices[i]
            spread = price * 0.0005
            
            md = MarketData()
            md.timestamp_ns = now_ns
            md.symbol = sym
            md.bid_price = max(0.01, price - spread/2)
            md.ask_price = max(0.01, price + spread/2)
            md.bid_size = max(1.0, np.random.uniform(10, 1000))
            md.ask_size = max(1.0, np.random.uniform(10, 1000))
            
            batch.append(md.SerializeToString())
            
        return batch

    def run(self):
        logger.info(f"Starting MarketSimulator producing to {TOPIC_NAME}")
        symbols_per_batch = len(self.symbols)
        
        try:
            while True:
                start_t = time.time()
                
                # To reach tick_rate, we produce batches corresponding to the delta time.
                # If we want 10000 ticks/sec and we process 100 symbols per tick, we need 100 ticks per second.
                loop_ticks = self.batch_size // symbols_per_batch
                if loop_ticks == 0: loop_ticks = 1
                
                for _ in range(loop_ticks):
                    batch = self.simulate_tick()
                    self.produce_batch(batch)
                
                elapsed = time.time() - start_t
                target_elapsed = (loop_ticks * symbols_per_batch) / self.tick_rate
                
                if target_elapsed > elapsed:
                    time.sleep(target_elapsed - elapsed)
        except KeyboardInterrupt:
            logger.info("Stopping Market Simulator...")
        finally:
            self.producer.flush()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rate", type=int, default=10000, help="Target messages per second")
    args = parser.parse_args()
    
    start_metrics_server(8001)
    symbols = [f"TICK{i}" for i in range(100)]
    initial_prices = np.random.uniform(10, 500, len(symbols))
    
    sim = MarketSimulator(symbols, initial_prices, tick_rate=args.rate)
    sim.run()
