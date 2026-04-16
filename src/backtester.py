import os
import logging
import polars as pl
from deltalake import DeltaTable
from src.strategy.obi_strategy import ObiStrategy
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BacktestingEngine:
    def __init__(self, delta_path: str = "storage/delta_lake"):
        self.delta_path = delta_path
        self.dt = DeltaTable(self.delta_path)

    def load_data(self, symbol: str = None) -> pl.DataFrame:
        """Loads historical data from Delta Lake."""
        logger.info(f"Loading historical data from {self.delta_path}...")
        
        # We can use polars to read delta directly
        df = pl.read_delta(self.delta_path)
        
        if symbol:
            df = df.filter(pl.col("symbol") == symbol)
            
        return df.sort("timestamp_ns")

    def run_strategy(self, strategy, df: pl.DataFrame):
        """Runs a strategy over a historical dataframe and calculates PNL."""
        logger.info(f"Running backtest for strategy: {strategy.name}")
        
        # Simulate processing in chunks or as a whole
        # For OBI, the strategy.analyze expects a batch (it takes the last row per symbol)
        # To backtest properly, we should simulate the flow of time.
        
        signals = []
        # Group by 100ms buckets to match real-time engine behavior
        buckets = df.group_by("bucket_100ms").all().sort("bucket_100ms")
        
        # Simple backtest: iterate through time
        for i in range(len(df)):
            # In a real backtest, we might want to feed data in windows
            # Here we feed row by row or small batches
            batch = df.slice(i, 1)
            new_signals = strategy.analyze(batch)
            signals.extend(new_signals)

        return self.calculate_performance(signals)

    def calculate_performance(self, signals) -> Dict:
        """Calculates PNL and other metrics from generated signals."""
        if not signals:
            return {"total_pnl": 0, "trade_count": 0, "win_rate": 0}

        total_pnl = 0
        wins = 0
        
        # This is a very simplified PNL calculation:
        # Assuming we 'close' the position at the next micro_price or mid-price
        # In a real system, we'd track open positions and market impact.
        
        # For simplicity, let's just count BUY/SELL and track theoretical PNL
        # assuming we exit at a fixed spread or fixed time later.
        # Here we just report the number of signals as a proxy for activity.
        
        for s in signals:
            # Theoretical: Buy at ask, Sell at bid
            # To calculate real PNL we need an exit strategy.
            pass

        return {
            "total_signals": len(signals),
            "trade_count": len(signals),
            "strategy": signals[0].strategy_name if signals else "N/A"
        }

if __name__ == "__main__":
    backtester = BacktestingEngine()
    data = backtester.load_data(symbol="TICK0")
    
    # Try different thresholds to find the best one
    for threshold in [0.5, 0.7, 0.9]:
        strat = ObiStrategy(threshold=threshold)
        perf = backtester.run_strategy(strat, data)
        print(f"Threshold: {threshold} | Signals: {perf['total_signals']}")
