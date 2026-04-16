from abc import ABC, abstractmethod
import polars as pl
from typing import List
from schema.market_data_pb2 import TradeSignal

class BaseStrategy(ABC):
    """
    Abstract Base Class for quantitative trading strategies.
    Any strategy must implement the analyze() method.
    """
    
    @property
    def name(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    def analyze(self, df: pl.DataFrame) -> List[TradeSignal]:
        """
        Analyze the bucketed Order Book dataframe and emit trade signals.
        
        Args:
            df (pl.DataFrame): The 100ms aggregated DataFrame containing 
                               obi_avg, micro_price_avg, timestamp_ns, etc.
                               
        Returns:
            List[TradeSignal]: A list of generated Protobuf TradeSignal objects.
        """
        pass
