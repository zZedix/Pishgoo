"""
Helper utilities for Pishgoo
"""

import time
from typing import Callable, Any, Optional
from functools import wraps
from utils.logger import setup_logger

logger = setup_logger(__name__)


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Retry decorator for API calls
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Backoff multiplier
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempt = 0
            current_delay = delay
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.error(f" {func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    
                    logger.warning(f" {func.__name__} attempt {attempt} failed: {e}. Retrying in {current_delay}s...")
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            return None
        return wrapper
    return decorator


def format_currency(value: float, currency: str = "IRT") -> str:
    """Format currency value"""
    if currency == "IRT":
        return f"{value:,.0f} {currency}"
    return f"{value:.2f} {currency}"


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change"""
    if old_value == 0:
        return 0.0
    return ((new_value - old_value) / old_value) * 100







