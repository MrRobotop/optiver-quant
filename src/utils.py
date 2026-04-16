import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

class CircuitBreakerOpenException(Exception):
    pass

class KafkaCircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 10, backoff_factor: float = 2.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.backoff_factor = backoff_factor
        
        self.failure_count = 0
        self.state = "CLOSED" # CLOSED, OPEN, HALF-OPEN
        self.last_failure_time = None

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if self.state == "OPEN":
                time_since_last_failure = time.time() - self.last_failure_time
                current_backoff = self.recovery_timeout * (self.backoff_factor ** (self.failure_count - self.failure_threshold))
                
                if time_since_last_failure > current_backoff:
                    self.state = "HALF-OPEN"
                    logger.info("Circuit breaker moved to HALF-OPEN state.")
                else:
                    raise CircuitBreakerOpenException(f"Circuit breaker OPEN. Backoff remaining: {current_backoff - time_since_last_failure:.2f}s")
            
            try:
                result = func(*args, **kwargs)
                if self.state == "HALF-OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                    logger.info("Circuit breaker closed successfully.")
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    logger.error(f"Circuit breaker opened. Last error: {e}")
                raise e
        return wrapper

def latency_tracker(name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            res = func(*args, **kwargs)
            end = time.time()
            elapsed = end - start
            try:
                from src.monitor import process_latency
                process_latency.labels(operation=name).observe(elapsed)
            except Exception as e:
                pass
            return res
        return wrapper
    return decorator
