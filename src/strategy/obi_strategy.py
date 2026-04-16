import polars as pl
from typing import List
from .base import BaseStrategy
from schema.market_data_pb2 import TradeSignal

class ObiStrategy(BaseStrategy):
    """
    Triggers execution signals when absolute Order Book Imbalance (OBI) 
    crosses a threshold.
    """
    def __init__(self, threshold: float = 0.8, trade_size: float = 100.0):
        self.threshold = threshold
        self.trade_size = trade_size

    def analyze(self, df: pl.DataFrame) -> List[TradeSignal]:
        signals = []
        
        if df.is_empty():
            return signals

        latest = df.group_by("symbol").last()
        
        for row in latest.iter_rows(named=True):
            sym = row["symbol"]
            obi = row["obi_avg"]
            ts = int(row["timestamp_ns"])
            
            action = None
            if obi > self.threshold:
                action = "BUY"
            elif obi < -self.threshold:
                action = "SELL"
                
            if action:
                signal = TradeSignal()
                signal.timestamp_ns = ts
                signal.symbol = sym
                signal.action = action
                signal.size = self.trade_size
                signal.price = float(row["ask_price"]) if action == "BUY" else float(row["bid_price"])
                signal.strategy_name = self.name
                
                signals.append(signal)

        return signals
