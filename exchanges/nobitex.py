"""
Nobitex Exchange Integration
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


class NobitexExchange(BaseExchange):
    """Nobitex exchange implementation"""
    
    BASE_URL = "https://api.nobitex.ir"
    
    def __init__(self, api_key: str, api_secret: str):
        """
        Initialize Nobitex exchange
        
        Args:
            api_key: Nobitex API key
            api_secret: Nobitex API secret
        """
        super().__init__(api_key, api_secret)
        self.session = requests.Session()
        logger.info(" Nobitex exchange initialized")
    
    def _generate_signature(self, data: Dict[str, Any]) -> str:
        """Generate HMAC signature for API requests"""
        sorted_data = sorted(data.items())
        message = "&".join([f"{k}={v}" for k, v in sorted_data])
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _make_authenticated_request(self, endpoint: str, method: str = "POST", 
                                   params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make authenticated API request
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            params: Request parameters
            
        Returns:
            API response
        """
        params = params or {}
        params['apiKey'] = self.api_key
        params['timestamp'] = str(int(time.time() * 1000))
        
        signature = self._generate_signature(params)
        params['signature'] = signature
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            if method == "POST":
                response = self.session.post(url, json=params, timeout=10)
            else:
                response = self.session.get(url, params=params, timeout=10)
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f" Nobitex API error: {e}")
            raise
    
    @retry(max_attempts=3, delay=1.0)
    def get_balance(self) -> Dict[str, float]:
        """Get account balance"""
        try:
            endpoint = "/v2/wallets"
            response = self._make_authenticated_request(endpoint, method="GET")
            
            if response.get('status') == 'ok':
                wallets = response.get('wallets', {})
                balances = {}
                for currency, wallet_data in wallets.items():
                    if isinstance(wallet_data, dict):
                        balances[currency] = float(wallet_data.get('balance', 0))
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
        Get OHLCV data from Nobitex
        
        Args:
            symbol: Trading pair (e.g., 'BTCIRT')
            timeframe: Timeframe (1h, 4h, 1d)
            limit: Number of candles
        """
        try:
            # Convert timeframe to resolution
            resolution_map = {
                "1m": "1",
                "5m": "5",
                "15m": "15",
                "30m": "30",
                "1h": "60",
                "4h": "240",
                "1d": "D"
            }
            resolution = resolution_map.get(timeframe, "60")
            
            # Nobitex market endpoint
            endpoint = f"/market/udf/history"
            params = {
                "symbol": symbol.lower(),
                "resolution": resolution,
                "from": int(time.time()) - (limit * 3600),  # Approximate
                "to": int(time.time()),
                "countback": limit
            }
            
            url = f"{self.BASE_URL}{endpoint}"
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('s') == 'ok' and 't' in data:
                df = pd.DataFrame({
                    'timestamp': pd.to_datetime(data['t'], unit='s'),
                    'open': data['o'],
                    'high': data['h'],
                    'low': data['l'],
                    'close': data['c'],
                    'volume': data['v']
                })
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
        Place an order on Nobitex
        
        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            amount: Order amount
            price: Limit price (None for market order)
        """
        try:
            endpoint = "/v2/order"
            params = {
                "type": "limit" if price else "market",
                "execution": "limit" if price else "market",
                "srcCurrency": symbol.replace("IRT", "").replace("USDT", ""),
                "dstCurrency": "IRT" if "IRT" in symbol else "USDT",
                "amount": str(amount),
                "price": str(price) if price else None
            }
            
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            
            if side == "sell":
                # Swap currencies for sell
                params['srcCurrency'], params['dstCurrency'] = \
                    params['dstCurrency'], params['srcCurrency']
            
            response = self._make_authenticated_request(endpoint, method="POST", params=params)
            
            if response.get('status') == 'ok':
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
            endpoint = "/v2/order"
            params = {"id": order_id, "status": "cancelled"}
            
            response = self._make_authenticated_request(endpoint, method="POST", params=params)
            
            if response.get('status') == 'ok':
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
            endpoint = "/v2/orders"
            params = {"status": "open"}
            if symbol:
                params['market'] = symbol.lower()
            
            response = self._make_authenticated_request(endpoint, method="GET", params=params)
            
            if response.get('status') == 'ok':
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
            endpoint = f"/v2/orderbook/{symbol.lower()}"
            response = requests.get(f"{self.BASE_URL}{endpoint}", timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'ok':
                bids = data.get('bids', [])
                asks = data.get('asks', [])
                
                return {
                    'symbol': symbol,
                    'bid': float(bids[0][0]) if bids else 0,
                    'ask': float(asks[0][0]) if asks else 0,
                    'last': float(bids[0][0]) if bids else 0,
                    'volume': float(data.get('volume', 0))
                }
            else:
                return {}
        except Exception as e:
            logger.error(f" Error getting ticker: {e}")
            return {}







