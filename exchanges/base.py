"""
Base exchange interface
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import pandas as pd


class BaseExchange(ABC):
    """Base class for all exchanges"""
    
    def __init__(self, api_key: str, api_secret: str):
        """
        Initialize exchange
        
        Args:
            api_key: API key
            api_secret: API secret
        """
        self.api_key = api_key
        self.api_secret = api_secret
    
    @abstractmethod
    def get_balance(self) -> Dict[str, float]:
        """
        Get account balance
        
        Returns:
            Dictionary with currency balances
        """
        pass
    
    @abstractmethod
    def get_ohlcv(self, symbol: str, timeframe: str = "1h", limit: int = 100) -> pd.DataFrame:
        """
        Get OHLCV data
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCIRT')
            timeframe: Timeframe (e.g., '1h', '4h', '1d')
            limit: Number of candles to fetch
            
        Returns:
            DataFrame with OHLCV data
        """
        pass
    
    @abstractmethod
    def place_order(self, symbol: str, side: str, amount: float, price: Optional[float] = None) -> Dict[str, Any]:
        """
        Place an order
        
        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            amount: Order amount
            price: Limit price (None for market orders)
            
        Returns:
            Order information dictionary
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get open orders
        
        Args:
            symbol: Optional symbol filter
            
        Returns:
            List of open orders
        """
        pass
    
    @abstractmethod
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get ticker information
        
        Args:
            symbol: Trading pair
            
        Returns:
            Ticker data
        """
        pass




