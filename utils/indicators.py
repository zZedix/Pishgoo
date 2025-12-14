"""
Technical indicators for Pishgoo
"""

import pandas as pd
import numpy as np
import ta
from typing import Dict, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)


class TechnicalIndicators:
    """Calculate technical indicators for trading signals"""
    
    @staticmethod
    def calculate_all(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all technical indicators
        
        Args:
            df: DataFrame with OHLCV data (columns: open, high, low, close, volume)
            
        Returns:
            DataFrame with added indicator columns
        """
        if df.empty or len(df) < 20:
            logger.warning("Insufficient data for indicators")
            return df
        
        result_df = df.copy()
        
        try:
            # RSI (Relative Strength Index)
            result_df['rsi'] = ta.momentum.RSIIndicator(result_df['close']).rsi()
            
            # MACD (Moving Average Convergence Divergence)
            macd = ta.trend.MACD(result_df['close'])
            result_df['macd'] = macd.macd()
            result_df['macd_signal'] = macd.macd_signal()
            result_df['macd_diff'] = macd.macd_diff()
            
            # EMAs (Exponential Moving Averages)
            result_df['ema_9'] = ta.trend.EMAIndicator(result_df['close'], window=9).ema_indicator()
            result_df['ema_21'] = ta.trend.EMAIndicator(result_df['close'], window=21).ema_indicator()
            result_df['ema_50'] = ta.trend.EMAIndicator(result_df['close'], window=50).ema_indicator()
            result_df['ema_200'] = ta.trend.EMAIndicator(result_df['close'], window=200).ema_indicator()
            
            # SMA (Simple Moving Averages)
            result_df['sma_20'] = ta.trend.SMAIndicator(result_df['close'], window=20).sma_indicator()
            result_df['sma_50'] = ta.trend.SMAIndicator(result_df['close'], window=50).sma_indicator()
            
            # Bollinger Bands
            bb = ta.volatility.BollingerBands(result_df['close'], window=20, window_dev=2)
            result_df['bb_high'] = bb.bollinger_hband()
            result_df['bb_low'] = bb.bollinger_lband()
            result_df['bb_mid'] = bb.bollinger_mavg()
            
            # ATR (Average True Range)
            result_df['atr'] = ta.volatility.AverageTrueRange(
                result_df['high'], result_df['low'], result_df['close']
            ).average_true_range()
            
            # Momentum
            result_df['momentum'] = ta.momentum.ROCIndicator(result_df['close'], window=10).roc()
            
            # Volume indicators
            result_df['volume_sma'] = ta.volume.VolumeSMAIndicator(
                result_df['close'], result_df['volume']
            ).volume_sma()
            
            # ADX (Average Directional Index)
            result_df['adx'] = ta.trend.ADXIndicator(
                result_df['high'], result_df['low'], result_df['close']
            ).adx()
            
            # Stochastic Oscillator
            stoch = ta.momentum.StochasticOscillator(
                result_df['high'], result_df['low'], result_df['close']
            )
            result_df['stoch_k'] = stoch.stoch()
            result_df['stoch_d'] = stoch.stoch_signal()
            
            # Williams %R
            result_df['williams_r'] = ta.momentum.WilliamsRIndicator(
                result_df['high'], result_df['low'], result_df['close']
            ).williams_r()
            
            logger.debug("Technical indicators calculated successfully")
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
        
        return result_df
    
    @staticmethod
    def get_signal_strength(df: pd.DataFrame) -> Dict[str, float]:
        """
        Get overall signal strength from indicators
        
        Args:
            df: DataFrame with indicators
            
        Returns:
            Dictionary with signal strength scores
        """
        if df.empty or 'rsi' not in df.columns:
            return {"buy": 0.0, "sell": 0.0, "hold": 1.0}
        
        latest = df.iloc[-1]
        
        buy_signals = 0
        sell_signals = 0
        total_signals = 0
        
        # RSI signals
        if 'rsi' in df.columns and pd.notna(latest['rsi']):
            total_signals += 1
            if latest['rsi'] < 30:
                buy_signals += 1
            elif latest['rsi'] > 70:
                sell_signals += 1
        
        # MACD signals
        if all(col in df.columns for col in ['macd', 'macd_signal']) and \
           pd.notna(latest['macd']) and pd.notna(latest['macd_signal']):
            total_signals += 1
            if latest['macd'] > latest['macd_signal']:
                buy_signals += 1
            else:
                sell_signals += 1
        
        # EMA crossover
        if all(col in df.columns for col in ['ema_9', 'ema_21']) and \
           pd.notna(latest['ema_9']) and pd.notna(latest['ema_21']):
            total_signals += 1
            if latest['ema_9'] > latest['ema_21']:
                buy_signals += 1
            else:
                sell_signals += 1
        
        # Bollinger Bands
        if all(col in df.columns for col in ['close', 'bb_low', 'bb_high']) and \
           pd.notna(latest['close']):
            total_signals += 1
            if latest['close'] < latest['bb_low']:
                buy_signals += 1
            elif latest['close'] > latest['bb_high']:
                sell_signals += 1
        
        if total_signals == 0:
            return {"buy": 0.0, "sell": 0.0, "hold": 1.0}
        
        buy_score = buy_signals / total_signals
        sell_score = sell_signals / total_signals
        
        # Determine action
        if buy_score > 0.6:
            action = "buy"
        elif sell_score > 0.6:
            action = "sell"
        else:
            action = "hold"
        
        return {
            "action": action,
            "buy": buy_score,
            "sell": sell_score,
            "hold": 1.0 - max(buy_score, sell_score),
            "confidence": max(buy_score, sell_score)
        }

