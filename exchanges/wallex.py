"""
Wallex Exchange Integration
"""

import requests
import time
import hashlib
import hmac
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any
from exchanges.base import BaseExchange
from utils.logger import setup_logger
from utils.helpers import retry

logger = setup_logger(__name__)


class WallexExchange(BaseExchange):
    """Wallex exchange implementation"""
    
    BASE_URL = "https://api.wallex.ir"
    
    def __init__(self, api_key: str, api_secret: str):
        """
        Initialize Wallex exchange
        
        Args:
            api_key: Wallex API key
            api_secret: Wallex API secret
        """
        super().__init__(api_key, api_secret)
        self.session = requests.Session()
        logger.info(" Wallex exchange initialized")
    
    def _generate_signature(self, method: str, path: str, params: Dict[str, Any] = None) -> str:
        """Generate HMAC signature for API requests"""
        params = params or {}
        query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
        
        message = f"{method}\n{path}\n{query_string}\n{int(time.time())}"
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _make_authenticated_request(self, endpoint: str, method: str = "GET",
                                   params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make authenticated API request
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            params: Request parameters
        """
        params = params or {}
        timestamp = int(time.time())
        
        signature = self._generate_signature(method, endpoint, params)
        
        headers = {
            "X-API-Key": self.api_key,
            "X-Signature": signature,
            "X-Timestamp": str(timestamp),
            "Content-Type": "application/json"
        }
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            if method == "POST":
                response = self.session.post(url, json=params, headers=headers, timeout=10)
            else:
                response = self.session.get(url, params=params, headers=headers, timeout=10)
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f" Wallex API error: {e}")
            raise
    
    @retry(max_attempts=3, delay=1.0)
    def get_balance(self) -> Dict[str, float]:
        """Get account balance"""
        try:
            endpoint = "/v1/account/balances"
            response = self._make_authenticated_request(endpoint, method="GET")
            
            if response.get('result') and 'balances' in response:
                balances = {}
                for currency, balance_data in response['balances'].items():
                    if isinstance(balance_data, dict):
                        balances[currency] = float(balance_data.get('available', 0))
                logger.info(f" Balance fetched: {len(balances)} currencies")
                return balances
            else:
                logger.error(f" Failed to fetch balance: {response}")
                return {}
        except Exception as e:
            logger.error(f" Error getting balance: {e}")
            return {}
    
    @retry(max_attempts=3, delay=1.0)
    def get_ohlcv(self, symbol: str, timeframe: str = "1h", limit: int = 100) -> pd.DataFrame:
        """
        Get OHLCV data from Wallex
        
        Args:
            symbol: Trading pair (e.g., 'BTCIRT')
            timeframe: Timeframe (1h, 4h, 1d)
            limit: Number of candles
        """
        try:
            # Convert timeframe to interval
            interval_map = {
                "1m": "1",
                "5m": "5",
                "15m": "15",
                "30m": "30",
                "1h": "60",
                "4h": "240",
                "1d": "1D"
            }
            interval = interval_map.get(timeframe, "60")
            
            endpoint = "/v1/markets/candles"
            params = {
                "symbol": symbol.upper(),
                "resolution": interval,
                "from": int(time.time()) - (limit * 3600),
                "to": int(time.time())
            }
            
            response = requests.get(f"{self.BASE_URL}{endpoint}", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('result') and 'candles' in data:
                candles = data['candles']
                df = pd.DataFrame(candles)
                df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                df.set_index('timestamp', inplace=True)
                df = df.sort_index()
                logger.info(f" Fetched {len(df)} candles for {symbol}")
                return df
            else:
                logger.warning(f" No data returned for {symbol}")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f" Error fetching OHLCV for {symbol}: {e}")
            return pd.DataFrame()
    
    @retry(max_attempts=3, delay=1.0)
    def place_order(self, symbol: str, side: str, amount: float,
                   price: Optional[float] = None) -> Dict[str, Any]:
        """
        Place an order on Wallex
        
        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            amount: Order amount
            price: Limit price (None for market order)
        """
        try:
            endpoint = "/v1/orders"
            params = {
                "symbol": symbol.upper(),
                "side": side.upper(),
                "type": "LIMIT" if price else "MARKET",
                "quantity": str(amount),
                "price": str(price) if price else None
            }
            
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            
            response = self._make_authenticated_request(endpoint, method="POST", params=params)
            
            if response.get('result'):
                order = response.get('order', {})
                logger.info(f" Order placed: {side} {amount} {symbol} at {price or 'market'}")
                return {
                    'id': order.get('id'),
                    'symbol': symbol,
                    'side': side,
                    'amount': amount,
                    'price': price,
                    'status': 'open',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                error_msg = response.get('message', 'Unknown error')
                logger.error(f" Order failed: {error_msg}")
                raise Exception(f"Order failed: {error_msg}")
        except Exception as e:
            logger.error(f" Error placing order: {e}")
            raise
    
    @retry(max_attempts=3, delay=1.0)
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        try:
            endpoint = f"/v1/orders/{order_id}"
            
            response = self._make_authenticated_request(endpoint, method="DELETE")
            
            if response.get('result'):
                logger.info(f" Order {order_id} cancelled")
                return True
            else:
                logger.error(f" Failed to cancel order: {response}")
                return False
        except Exception as e:
            logger.error(f" Error cancelling order: {e}")
            return False
    
    @retry(max_attempts=3, delay=1.0)
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get open orders"""
        try:
            endpoint = "/v1/orders"
            params = {"status": "NEW"}
            if symbol:
                params['symbol'] = symbol.upper()
            
            response = self._make_authenticated_request(endpoint, method="GET", params=params)
            
            if response.get('result'):
                orders = response.get('orders', [])
                logger.info(f" Found {len(orders)} open orders")
                return orders
            else:
                return []
        except Exception as e:
            logger.error(f" Error getting open orders: {e}")
            return []
    
    @retry(max_attempts=3, delay=1.0)
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker information"""
        try:
            endpoint = f"/v1/markets/quotes/{symbol.upper()}"
            response = requests.get(f"{self.BASE_URL}{endpoint}", timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('result'):
                quote = data['result']
                return {
                    'symbol': symbol,
                    'bid': float(quote.get('bid', 0)),
                    'ask': float(quote.get('ask', 0)),
                    'last': float(quote.get('lastPrice', 0)),
                    'volume': float(quote.get('volume24h', 0))
                }
            else:
                return {}
        except Exception as e:
            logger.error(f" Error getting ticker: {e}")
            return {}







