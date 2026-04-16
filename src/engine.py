import os
import time
import argparse
import logging
from confluent_kafka import Consumer, Producer
import polars as pl
import pyarrow as pa
from schema.market_data_pb2 import MarketData
from src.storage import DeltaLakeStorage
from src.monitor import start_metrics_server, messages_consumed, obi_gauge, micro_price_gauge, signals_generated
from src.utils import latency_tracker
from src.strategy import ObiStrategy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "localhost:19092")
TOPIC_NAME = "market-events"
TRADE_TOPIC_NAME = "trade-signals"

class RealTimeEngine:
    def __init__(self, flush_interval=1.0):
        conf = {
            'bootstrap.servers': KAFKA_BROKER,
            'group.id': 'analytics-engine',
            'auto.offset.reset': 'latest',
            'fetch.wait.max.ms': 100
        }
        self.consumer = Consumer(conf)
        self.consumer.subscribe([TOPIC_NAME])
        self.storage = DeltaLakeStorage("storage/delta_lake")
        self.flush_interval = flush_interval

        self.signal_producer = Producer({
            'bootstrap.servers': KAFKA_BROKER,
            'compression.type': 'lz4'
        })
        self.strategies = [ObiStrategy(threshold=0.8)]

    @latency_tracker(name="process_messages")
    def process_messages(self, messages):
        if not messages:
            return
            
        symbols, timestamps, b_prices, a_prices, b_sizes, a_sizes = [], [], [], [], [], []
        
        parse_start = time.time()
        for msg in messages:
            if msg.error():
                continue
            
            md = MarketData()
            md.ParseFromString(msg.value())
            
            symbols.append(md.symbol)
            timestamps.append(md.timestamp_ns)
            b_prices.append(md.bid_price)
            a_prices.append(md.ask_price)
            b_sizes.append(md.bid_size)
            a_sizes.append(md.ask_size)
            
            messages_consumed.inc()

        arrow_table = pa.Table.from_arrays(
            [pa.array(symbols), pa.array(timestamps), pa.array(b_prices), pa.array(a_prices), pa.array(b_sizes), pa.array(a_sizes)],
            names=["symbol", "timestamp_ns", "bid_price", "ask_price", "bid_size", "ask_size"]
        )
        
        lf = pl.LazyFrame(arrow_table)
        
        # OBI and Micro-price computations
        lf = lf.with_columns([
            ((pl.col("bid_size") - pl.col("ask_size")) / (pl.col("bid_size") + pl.col("ask_size"))).alias("obi"),
            ((pl.col("bid_price") * pl.col("ask_size") + pl.col("ask_price") * pl.col("bid_size")) / (pl.col("bid_size") + pl.col("ask_size"))).alias("micro_price")
        ])
        
        # 100ms bucket based on timestamp_ns (1e8 ns = 100ms)
        lf = lf.with_columns(
            (pl.col("timestamp_ns") // int(1e8) * int(1e8)).alias("bucket_100ms")
        )
        
        # Vectorized aggregation
        lf = lf.group_by(["bucket_100ms", "symbol"]).agg([
            pl.col("obi").mean().alias("obi_avg"),
            pl.col("micro_price").mean().alias("micro_price_avg"),
            pl.col("timestamp_ns").last().alias("timestamp_ns"),
            pl.col("bid_price").last(),
            pl.col("ask_price").last(),
            pl.col("bid_size").last(),
            pl.col("ask_size").last()
        ])
        
        df = lf.collect()
        
        if not df.is_empty():
            latest = df.group_by("symbol").last()
            for row in latest.iter_rows(named=True):
                obi_gauge.labels(symbol=row['symbol']).set(row['obi_avg'])
                micro_price_gauge.labels(symbol=row['symbol']).set(row['micro_price_avg'])
                
        # Evaluate strategies
        for strategy in self.strategies:
            signals = strategy.analyze(df)
            for signal in signals:
                signals_generated.labels(strategy=strategy.name, action=signal.action, symbol=signal.symbol).inc()
                self.signal_producer.produce(TRADE_TOPIC_NAME, value=signal.SerializeToString())
        self.signal_producer.poll(0)
                
        self.storage.write_batch(df)

    def run(self):
        logger.info(f"Starting RealTimeEngine consuming from {TOPIC_NAME}")
        last_optimize = time.time()
        
        try:
            while True:
                msgs = self.consumer.consume(num_messages=5000, timeout=0.1)
                if msgs:
                    self.process_messages(msgs)
                    
                if time.time() - last_optimize > 60:
                    logger.info("Running Delta Lake file compaction (optimize)")
                    self.storage.optimize()
                    last_optimize = time.time()
                    
        except KeyboardInterrupt:
            logger.info("Stopping Engine...")
        finally:
            self.consumer.close()

if __name__ == "__main__":
    start_metrics_server(8002)
    engine = RealTimeEngine()
    engine.run()
