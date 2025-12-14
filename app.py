"""
Pishgoo - AI-Powered Trading System
Main entry point for the application
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.exchange_manager import ExchangeManager
from core.data_fetcher import DataFetcher
from core.strategy import HybridAIStrategy
from core.risk_manager import RiskManager
from utils.logger import setup_logger
from config.settings import load_config

logger = setup_logger(__name__)


def main():
    """Main function to run Pishgoo trading system"""
    logger.info("Starting Pishgoo Trading System...")
    
    # Load configuration
    config = load_config()
    if not config:
        logger.error("Failed to load configuration")
        return
    
    # Initialize components
    exchange_manager = ExchangeManager(config)
    data_fetcher = DataFetcher(exchange_manager)
    risk_manager = RiskManager(config.get('risk', {}))
    strategy = HybridAIStrategy(config, data_fetcher, risk_manager)
    
    logger.info("Pishgoo initialized successfully")
    logger.info(f"Trading pairs: {config.get('pairs', [])}")
    logger.info(f"Amount per trade: {config.get('amount_per_trade', 0)}")
    
    # Start trading loop (this would typically run in trader_service.py)
    logger.info("Use 'streamlit run dashboard/app.py' to access the dashboard")
    logger.info("Use 'python services/trader_service.py' to start auto trading")


if __name__ == "__main__":
    main()

