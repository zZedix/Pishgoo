"""
Chart components for Streamlit dashboard
"""

import streamlit as st
import pandas as pd
from typing import Dict, Optional

# Optional import for plotly
try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    go = None


def plot_price_chart(df: pd.DataFrame, symbol: str, title: str = "Price Chart"):
    """Plot OHLCV price chart"""
    if not PLOTLY_AVAILABLE:
        st.warning("Plotly is not available. Please install with: pip install plotly")
        st.line_chart(df[['close']])
        return
    
    if df.empty:
        st.warning("No data available for chart")
        return
    
    fig = go.Figure()
    
    # Candlestick chart
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='Price'
    ))
    
    # Add EMAs if available
    if 'ema_9' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['ema_9'],
            name='EMA 9',
            line=dict(color='blue', width=1)
        ))
    
    if 'ema_21' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['ema_21'],
            name='EMA 21',
            line=dict(color='orange', width=1)
        ))
    
    if 'ema_50' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['ema_50'],
            name='EMA 50',
            line=dict(color='purple', width=1)
        ))
    
    # Bollinger Bands
    if all(col in df.columns for col in ['bb_high', 'bb_low', 'bb_mid']):
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['bb_high'],
            name='BB High',
            line=dict(color='gray', width=1, dash='dash'),
            showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['bb_low'],
            name='BB Low',
            line=dict(color='gray', width=1, dash='dash'),
            fill='tonexty',
            fillcolor='rgba(128,128,128,0.2)',
            showlegend=False
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Time",
        yaxis_title="Price (IRT)",
        template="plotly_dark",
        height=500,
        xaxis_rangeslider_visible=False
    )
    
    st.plotly_chart(fig, use_container_width=True)


def plot_prophet_forecast(forecast_df: pd.DataFrame, historical_df: Optional[pd.DataFrame] = None):
    """Plot Prophet forecast"""
    if not PLOTLY_AVAILABLE:
        st.warning("Plotly is not available. Please install with: pip install plotly")
        return
    
    if forecast_df.empty:
        st.warning("No forecast data available")
        return
    
    fig = go.Figure()
    
    # Historical data
    if historical_df is not None and not historical_df.empty:
        fig.add_trace(go.Scatter(
            x=historical_df.index,
            y=historical_df['close'],
            name='Historical Price',
            line=dict(color='blue', width=2)
        ))
    
    # Forecast
    fig.add_trace(go.Scatter(
        x=forecast_df['ds'],
        y=forecast_df['yhat'],
        name='Forecast',
        line=dict(color='green', width=2)
    ))
    
    # Confidence interval
    fig.add_trace(go.Scatter(
        x=forecast_df['ds'],
        y=forecast_df['yhat_upper'],
        name='Upper Bound',
        line=dict(color='gray', width=1, dash='dash'),
        showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=forecast_df['ds'],
        y=forecast_df['yhat_lower'],
        name='Lower Bound',
        line=dict(color='gray', width=1, dash='dash'),
        fill='tonexty',
        fillcolor='rgba(0,255,0,0.1)',
        showlegend=False
    ))
    
    fig.update_layout(
        title="Prophet Forecast",
        xaxis_title="Time",
        yaxis_title="Price (IRT)",
        template="plotly_dark",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def plot_equity_curve(equity_curve: list):
    """Plot equity curve from backtest"""
    if not PLOTLY_AVAILABLE:
        st.warning("Plotly is not available. Please install with: pip install plotly")
        st.line_chart(pd.DataFrame({'equity': equity_curve}))
        return
    
    if not equity_curve or len(equity_curve) < 2:
        st.warning("No equity curve data available")
        return
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        y=equity_curve,
        mode='lines',
        name='Equity',
        line=dict(color='green', width=2)
    ))
    
    fig.update_layout(
        title="Equity Curve",
        xaxis_title="Trade Number",
        yaxis_title="Balance (IRT)",
        template="plotly_dark",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


def plot_indicators(df: pd.DataFrame):
    """Plot technical indicators"""
    if not PLOTLY_AVAILABLE:
        st.warning("Plotly is not available. Please install with: pip install plotly")
        return
    
    if df.empty:
        return
    
    # RSI
    if 'rsi' in df.columns:
        st.subheader("RSI")
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(
            x=df.index,
            y=df['rsi'],
            name='RSI',
            line=dict(color='purple', width=2)
        ))
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
        fig_rsi.update_layout(template="plotly_dark", height=250)
        st.plotly_chart(fig_rsi, use_container_width=True)
    
    # MACD
    if all(col in df.columns for col in ['macd', 'macd_signal']):
        st.subheader("MACD")
        fig_macd = go.Figure()
        fig_macd.add_trace(go.Scatter(
            x=df.index,
            y=df['macd'],
            name='MACD',
            line=dict(color='blue', width=2)
        ))
        fig_macd.add_trace(go.Scatter(
            x=df.index,
            y=df['macd_signal'],
            name='Signal',
            line=dict(color='orange', width=2)
        ))
        if 'macd_diff' in df.columns:
            fig_macd.add_trace(go.Bar(
                x=df.index,
                y=df['macd_diff'],
                name='Histogram',
                marker_color='gray'
            ))
        fig_macd.update_layout(template="plotly_dark", height=250)
        st.plotly_chart(fig_macd, use_container_width=True)

