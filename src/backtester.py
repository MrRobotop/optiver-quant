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
        # We don't necessarily need to pre-load DeltaTable here if we use pl.read_delta

    def load_data(self, symbol: str = None) -> pl.DataFrame:
        """Loads historical data from Delta Lake."""
        logger.info(f"Loading historical data from {self.delta_path}...")
        
        try:
            df = pl.read_delta(self.delta_path)
            if symbol:
                df = df.filter(pl.col("symbol") == symbol)
            return df.sort("timestamp_ns")
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return pl.DataFrame()

    def run_strategy(self, strategy, df: pl.DataFrame):
        """Runs a strategy over a historical dataframe and calculates PNL."""
        if df.is_empty():
            return {"total_pnl": 0, "trade_count": 0, "win_rate": 0}
            
        logger.info(f"Running backtest for strategy: {strategy.name}")
        
        signals = []
        # In a real backtest, we iterate through the data
        # To make it fast for this demo, we'll process in chunks
        for i in range(0, len(df), 10):
            batch = df.slice(i, 10)
            new_signals = strategy.analyze(batch)
            if new_signals:
                # Store the signal and the data at that point for PNL calculation
                for sig in new_signals:
                    # Find approximate exit price (e.g., 5 seconds later)
                    # For simplicity in this demo, we'll just take a price 100 rows later
                    exit_idx = min(i + 100, len(df) - 1)
                    exit_price = (df[exit_idx, "bid_price"] + df[exit_idx, "ask_price"]) / 2
                    
                    # Store signal with exit price
                    signals.append({
                        "signal": sig,
                        "exit_price": exit_price
                    })

        return self.calculate_performance(signals)

    def calculate_performance(self, signals_with_exits) -> Dict:
        """Calculates PNL and other metrics from generated signals."""
        if not signals_with_exits:
            return {"total_pnl": 0, "trade_count": 0, "win_rate": 0, "total_signals": 0}

        total_pnl = 0
        wins = 0
        
        for item in signals_with_exits:
            sig = item["signal"]
            exit_p = item["exit_price"]
            
            pnl = 0
            if sig.action == "BUY":
                pnl = (exit_p - sig.price) * sig.size
            else:
                pnl = (sig.price - exit_p) * sig.size
                
            total_pnl += pnl
            if pnl > 0:
                wins += 1

        return {
            "total_pnl": round(total_pnl, 2),
            "trade_count": len(signals_with_exits),
            "win_rate": round(wins / len(signals_with_exits), 2) if signals_with_exits else 0,
            "total_signals": len(signals_with_exits)
        }

if __name__ == "__main__":
    backtester = BacktestingEngine()
    data = backtester.load_data(symbol="TICK0")
    
    for threshold in [0.5, 0.7, 0.9]:
        strat = ObiStrategy(threshold=threshold)
        perf = backtester.run_strategy(strat, data)
        print(f"Threshold: {threshold} | PNL: ${perf['total_pnl']} | Win Rate: {perf['win_rate']}")
