"""
Pishgoo Auto Trading Service
Runs continuously and executes trades based on AI signals
"""

import time
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import load_config
from core.exchange_manager import ExchangeManager
from core.data_fetcher import DataFetcher
from core.strategy import HybridAIStrategy
from core.risk_manager import RiskManager
from utils.logger import setup_logger

logger = setup_logger(__name__)


class TradingService:
    """Auto trading service"""
    
    def __init__(self):
        """Initialize trading service"""
        self.config = load_config()
        if not self.config:
            raise Exception("Failed to load configuration")
        
        self.exchange_manager = ExchangeManager(self.config)
        self.data_fetcher = DataFetcher(self.exchange_manager)
        self.risk_manager = RiskManager(self.config.get('risk', {}))
        self.strategy = HybridAIStrategy(self.config, self.data_fetcher, self.risk_manager)
        
        self.running = False
        self.trading_enabled = self.config.get('trading', {}).get('enabled', False)
        self.pairs = self.config.get('pairs', [])
        self.check_interval = 300  # 5 minutes
        
        logger.info(" Trading service initialized")
        logger.info(f" Trading pairs: {self.pairs}")
        logger.info(f" Check interval: {self.check_interval}s")
    
    def start(self):
        """Start trading service"""
        self.running = True
        logger.info(" Trading service started")
        
        try:
            while self.running:
                if not self.trading_enabled:
                    logger.info(" Trading is disabled in config")
                    time.sleep(60)
                    continue
                
                # Check each trading pair
                for symbol in self.pairs:
                    try:
                        self.process_pair(symbol)
                    except Exception as e:
                        logger.error(f" Error processing {symbol}: {e}")
                
                # Sleep before next iteration
                logger.info(f" Sleeping for {self.check_interval}s...")
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info(" Trading service stopped by user")
        except Exception as e:
            logger.error(f" Trading service error: {e}")
            raise
    
    def process_pair(self, symbol: str):
        """Process a trading pair"""
        logger.info(f" Processing {symbol}...")
        
        # Check for open positions
        open_orders = self.exchange_manager.get_open_orders(symbol)
        if open_orders:
            logger.info(f" {symbol} has {len(open_orders)} open orders")
            self.monitor_positions(symbol)
            return
        
        # Generate signal
        signal = self.strategy.generate_signal(symbol)
        
        if signal['action'] == 'hold':
            logger.debug(f" {symbol}: Hold signal (confidence: {signal['confidence']:.2f})")
            return
        
        # Check if signal is strong enough
        if not self.strategy.should_execute_trade(signal, symbol):
            logger.debug(f" {symbol}: Signal confidence too low")
            return
        
        # Execute trade
        self.execute_trade(symbol, signal)
    
    def execute_trade(self, symbol: str, signal: dict):
        """Execute a trade based on signal"""
        try:
            # Get current price
            ticker = self.exchange_manager.get_ticker(symbol)
            current_price = ticker.get('last', 0)
            
            if current_price == 0:
                logger.warning(f" {symbol}: Could not get current price")
                return
            
            # Get balance
            balance = self.exchange_manager.get_balance()
            base_currency = symbol.replace('IRT', '').replace('USDT', '')
            quote_currency = 'IRT' if 'IRT' in symbol else 'USDT'
            
            if signal['action'] == 'buy':
                available_balance = balance.get(quote_currency, 0)
            else:  # sell
                available_balance = balance.get(base_currency, 0)
            
            # Calculate position size
            amount = self.risk_manager.calculate_position_size(
                available_balance, current_price
            )
            
            if amount <= 0:
                logger.warning(f" {symbol}: Insufficient balance for trade")
                return
            
            # Validate order
            validation = self.risk_manager.validate_order(
                signal['action'], amount, current_price, available_balance
            )
            
            if not validation['valid']:
                logger.warning(f" {symbol}: Order validation failed: {validation['reason']}")
                return
            
            # Place order (market order)
            logger.info(f" Executing {signal['action']} order: {amount:.4f} {symbol} @ market price")
            result = self.exchange_manager.place_order(
                symbol,
                signal['action'],
                amount,
                price=None  # Market order
            )
            
            if result:
                logger.info(f" Order placed: {result.get('id', 'N/A')}")
                logger.info(f"   Signal: {signal['reason']}")
            else:
                logger.error(f" Failed to place order for {symbol}")
                
        except Exception as e:
            logger.error(f" Error executing trade for {symbol}: {e}")
    
    def monitor_positions(self, symbol: str):
        """Monitor open positions for stop loss and take profit"""
        try:
            open_orders = self.exchange_manager.get_open_orders(symbol)
            ticker = self.exchange_manager.get_ticker(symbol)
            current_price = ticker.get('last', 0)
            
            if current_price == 0:
                return
            
            for order in open_orders:
                # Check if order needs to be cancelled (stop loss/take profit)
                # This would require tracking entry prices, which is exchange-dependent
                # For now, we just log
                logger.debug(f" Monitoring order: {order.get('id', 'N/A')}")
                
        except Exception as e:
            logger.error(f" Error monitoring positions: {e}")
    
    def stop(self):
        """Stop trading service"""
        self.running = False
        logger.info(" Trading service stopping...")


def main():
    """Main entry point"""
    try:
        service = TradingService()
        service.start()
    except Exception as e:
        logger.error(f" Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()




