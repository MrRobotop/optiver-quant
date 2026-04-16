import logging
from src.backtester import BacktestingEngine
from src.strategy.obi_strategy import ObiStrategy
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StrategyRefiner:
    def __init__(self, delta_path: str = "storage/delta_lake"):
        self.backtester = BacktestingEngine(delta_path)

    def optimize_obi(self, symbol: str):
        """Finds the optimal OBI threshold for a given symbol."""
        data = self.backtester.load_data(symbol=symbol)
        
        best_threshold = 0
        max_signals = 0
        
        logger.info(f"Refining OBI Strategy for {symbol}...")
        
        # Grid search over thresholds
        for threshold in np.linspace(0.1, 0.9, 9):
            strat = ObiStrategy(threshold=threshold)
            perf = self.backtester.run_strategy(strat, data)
            
            logger.info(f"Tested Threshold {threshold:.2f} -> {perf['total_signals']} signals")
            
            if perf['total_signals'] > max_signals:
                max_signals = perf['total_signals']
                best_threshold = threshold
                
        logger.info(f"Optimization complete. Best OBI threshold: {best_threshold:.2f}")
        return best_threshold

if __name__ == "__main__":
    refiner = StrategyRefiner()
    # Refine for a specific symbol
    refiner.optimize_obi("TICK0")
