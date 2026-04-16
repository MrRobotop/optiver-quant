import os
import time
import logging
import polars as pl
from deltalake import write_deltalake, DeltaTable

logger = logging.getLogger(__name__)

class DeltaLakeStorage:
    def __init__(self, uri="storage/delta_lake"):
        self.uri = uri
        os.makedirs(self.uri, exist_ok=True)

    def write_batch(self, df: pl.DataFrame):
        if df.is_empty():
            return
            
        # Convert timestamp_ns to a datetime for hourly partitioning
        df = df.with_columns(
            pl.from_epoch(pl.col("timestamp_ns") / 1e9, time_unit="s").dt.strftime("%Y-%m-%d-%H").alias("hour")
        )
        
        # Write to delta table partitioning by symbol and hour
        write_deltalake(
            self.uri,
            df.to_arrow(),
            mode="append",
            partition_by=["symbol", "hour"]
        )

    def optimize(self):
        try:
            dt = DeltaTable(self.uri)
            dt.optimize.compact()
            dt.vacuum(retention_hours=168, enforce_retention_duration=False)
        except Exception as e:
            logger.warning(f"Optimization skipped (table might be empty or locked): {e}")
