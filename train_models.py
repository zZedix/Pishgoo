"""
Training script for AI models
Use this script to train all AI models before using auto trading
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import load_config
from core.exchange_manager import ExchangeManager
from core.data_fetcher import DataFetcher
from core.ai_model import AIModel
from core.prophet_model import ProphetForecaster
from utils.logger import setup_logger

logger = setup_logger(__name__)


def train_models_for_symbol(symbol: str, config: dict, data_fetcher: DataFetcher):
    """Train all models for a symbol"""
    logger.info(f" Starting model training for {symbol}...")
    
    # Fetch historical data
    logger.info(f" Fetching historical data for {symbol}...")
    df = data_fetcher.get_market_data(symbol, limit=500, include_indicators=True)
    
    if df is None or df.empty:
        logger.error(f" No data available for {symbol}")
        return False
    
    logger.info(f" Fetched {len(df)} data points")
    
    # Train ML models
    if config.get('ai', {}).get('enabled', True):
        logger.info(" Training ML models (RandomForest & XGBoost)...")
        ai_model = AIModel(config.get('ai', {}))
        
        if ai_model.train_ml_models(df, symbol):
            logger.info(" ML models trained successfully")
        else:
            logger.warning(" ML model training failed")
        
        # Train LSTM if enabled
        if 'lstm' in config.get('ai', {}).get('models', []):
            logger.info(" Training LSTM model...")
            if ai_model.train_lstm(df, symbol):
                logger.info(" LSTM model trained successfully")
            else:
                logger.warning(" LSTM model training failed")
    
    # Train Prophet
    if config.get('prophet', {}).get('enabled', True):
        logger.info(" Training Prophet model...")
        prophet = ProphetForecaster(config.get('prophet', {}))
        
        if prophet.train(df, symbol):
            logger.info(" Prophet model trained successfully")
        else:
            logger.warning(" Prophet model training failed")
    
    logger.info(f" Model training completed for {symbol}")
    return True


def main():
    """Main training function"""
    logger.info(" Starting model training...")
    
    # Load configuration
    config = load_config()
    if not config:
        logger.error(" Failed to load configuration")
        return
    
    # Initialize components
    try:
        exchange_manager = ExchangeManager(config)
        data_fetcher = DataFetcher(exchange_manager)
    except Exception as e:
        logger.error(f" Failed to initialize components: {e}")
        logger.error(" Make sure API keys are configured correctly")
        return
    
    # Get trading pairs
    pairs = config.get('pairs', ['BTCIRT', 'ETHIRT'])
    logger.info(f" Training models for pairs: {pairs}")
    
    # Train models for each pair
    for symbol in pairs:
        try:
            train_models_for_symbol(symbol, config, data_fetcher)
        except Exception as e:
            logger.error(f" Error training models for {symbol}: {e}")
    
    logger.info(" All models trained successfully!")
    logger.info(" You can now use auto trading or run backtests")


if __name__ == "__main__":
    main()







