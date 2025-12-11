"""
Pishgoo Dashboard - Streamlit Web Interface
"""

import streamlit as st
import pandas as pd
import time
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import load_config
from core.exchange_manager import ExchangeManager
from core.data_fetcher import DataFetcher
from core.strategy import HybridAIStrategy
from core.risk_manager import RiskManager
from core.backtester import Backtester
from core.prophet_model import ProphetForecaster
from dashboard.components.charts import plot_price_chart, plot_prophet_forecast, plot_equity_curve, plot_indicators
from dashboard.components.trading_panel import display_signal, display_balance, display_open_positions, display_open_orders
from dashboard.components.settings_panel import render_settings
from utils.logger import setup_logger
from utils.translations import get_translation, set_language
from train_models import train_models_for_symbol

logger = setup_logger(__name__)

# Page config
st.set_page_config(
    page_title="Pishgoo Trading Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# Custom CSS with Vazirmatn font for Persian
st.markdown("""
<link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel="stylesheet" type="text/css" />
<style>
.main-header{font-size:3rem;font-weight:bold;text-align:center;color:#1f77b4;padding:1rem}
*{font-family:Vazirmatn,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif!important}
[data-testid="stSidebar"] *:not(script):not(style){font-family:Vazirmatn,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif!important}
/* Hide keyboard_double_arr text anywhere */
*:contains("keyboard_double_arr"), *:contains("keyb") {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    font-size: 0 !important;
    line-height: 0 !important;
    height: 0 !important;
    width: 0 !important;
    overflow: hidden !important;
}
/* Target Material Icons that might render as text */
.material-icons, [class*="material"], [class*="icon"] {
    font-family: 'Material Icons' !important;
}
</style>
<script>
(function() {
    function hideKeyboardText() {
        // Find and hide all elements containing keyboard_double_arr
        const allElements = document.querySelectorAll('*');
        allElements.forEach(el => {
            if (el.children.length === 0) {
                const text = el.textContent || el.innerText || '';
                if (text.includes('keyboard_double_arr') || text.includes('keyb') && text.length < 20) {
                    el.style.display = 'none';
                    el.style.visibility = 'hidden';
                    el.style.opacity = '0';
                    el.style.fontSize = '0';
                    el.style.height = '0';
                    el.style.width = '0';
                    el.style.overflow = 'hidden';
                    el.textContent = '';
                    el.innerHTML = '';
                }
            }
        });
        
        // Also check text nodes directly
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );
        let node;
        while (node = walker.nextNode()) {
            const text = node.textContent.trim();
            if (text === 'keyboard_double_arr' || (text.includes('keyb') && text.length < 20)) {
                node.textContent = '';
                if (node.parentElement) {
                    node.parentElement.style.display = 'none';
                }
            }
        }
    }
    
    // Run immediately
    hideKeyboardText();
    
    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', hideKeyboardText);
    }
    
    // Run periodically to catch dynamically added content
    setInterval(hideKeyboardText, 200);
    
    // Also use MutationObserver to catch new elements
    const observer = new MutationObserver(hideKeyboardText);
    observer.observe(document.body, {
        childList: true,
        subtree: true,
        characterData: true
    });
})();
</script>
""", unsafe_allow_html=True)

# Session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'trading_enabled' not in st.session_state:
    st.session_state.trading_enabled = False

# Initialize language
if 'language' not in st.session_state:
    config = load_config()
    st.session_state.language = config.get('dashboard', {}).get('language', 'en') if config else 'en'

# Helper function to get translations
def t(key: str) -> str:
    """Get translated text"""
    return get_translation(key, st.session_state.language)


def login_page():
    """Login page"""
    # Language selection on login page
    config = load_config()
    current_lang = config.get('dashboard', {}).get('language', 'en') if config else 'en'
    
    col1, col2 = st.columns([3, 1])
    with col2:
        lang_choice = st.selectbox(
            get_translation('select_language', current_lang),
            ['en', 'fa'],
            format_func=lambda x: get_translation('english', current_lang) if x == 'en' else get_translation('persian', current_lang),
            index=0 if current_lang == 'en' else 1
        )
        if lang_choice != current_lang:
            from config.settings import update_config
            update_config({'dashboard': {'language': lang_choice}})
            st.session_state.language = lang_choice
            st.rerun()
    
    st.title(get_translation('login_title', st.session_state.language))
    st.markdown("---")
    
    default_password = config.get('dashboard', {}).get('password', 'pishgoo123')
    
    password = st.text_input(t('password'), type="password")
    
    if st.button(t('login')):
        if password == default_password:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error(t('incorrect_password'))


def main_dashboard():
    """Main dashboard"""
    # Set direction based on language
    lang = st.session_state.get('language', 'en')
    if lang == 'fa':
        st.markdown("""
        <style>
        .stApp {
            direction: rtl;
        }
        .stMarkdown, .stText, .element-container {
            text-align: right;
        }
        </style>
        """, unsafe_allow_html=True)
    
    # Header
    st.markdown(f'<p class="main-header">{t("app_title")}</p>', unsafe_allow_html=True)
    
    # Load configuration
    config = load_config()
    if not config:
        st.error("Failed to load configuration")
        return
    
    # Sidebar
    with st.sidebar:
        # Language selector
        current_lang = st.session_state.language
        lang_choice = st.selectbox(
            t('select_language'),
            ['en', 'fa'],
            format_func=lambda x: t('english') if x == 'en' else t('persian'),
            index=0 if current_lang == 'en' else 1,
            key="lang_selector"
        )
        if lang_choice != current_lang:
            from config.settings import update_config
            update_config({'dashboard': {'language': lang_choice}})
            st.session_state.language = lang_choice
            st.rerun()
        
        st.markdown("---")
        
        page = st.selectbox(t('navigation'), [
            t('dashboard'),
            t('trading'),
            t('backtest'),
            t('train_models'),
            t('settings')
        ])
        
        # Map translated page names to actual page names
        page_map = {
            t('dashboard'): "Dashboard",
            t('trading'): "Trading",
            t('backtest'): "Backtest",
            t('train_models'): "Train Models",
            t('settings'): "Settings"
        }
        page = page_map.get(page, "Dashboard")
        
        if st.button(t('logout')):
            st.session_state.authenticated = False
            st.rerun()
        
        st.markdown("---")
        
        # Trading control
        trading_button_text = t('stop_trading') if st.session_state.trading_enabled else t('start_trading')
        if st.button(trading_button_text):
            st.session_state.trading_enabled = not st.session_state.trading_enabled
            st.rerun()
        
        if st.session_state.trading_enabled:
            st.success(t('trading_active'))
        else:
            st.info(t('trading_paused'))
    
    # Initialize components
    try:
        exchange_manager = ExchangeManager(config)
        data_fetcher = DataFetcher(exchange_manager)
        risk_manager = RiskManager(config.get('risk', {}))
        strategy = HybridAIStrategy(config, data_fetcher, risk_manager)
    except Exception as e:
        st.error(f" Error initializing components: {e}")
        st.stop()
    
    # Main content based on page
    if page == "Dashboard":
        render_dashboard(config, data_fetcher, strategy, exchange_manager)
    elif page == "Trading":
        render_trading(config, strategy, exchange_manager)
    elif page == "Backtest":
        render_backtest(config, strategy, data_fetcher)
    elif page == "Train Models":
        render_train_models(config, data_fetcher)
    elif page == "Settings":
        render_settings()
        st.stop()


def render_dashboard(config: dict, data_fetcher: DataFetcher, strategy: HybridAIStrategy, 
                    exchange_manager: ExchangeManager):
    """Render main dashboard"""
    pairs = config.get('pairs', ['BTCIRT'])
    selected_pair = st.selectbox(t('select_pair'), pairs)
    
    # Refresh button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button(t('refresh')):
            data_fetcher.clear_cache()
            st.rerun()
    
    # Get market data
    with st.spinner(t('loading_market_data')):
        try:
            df = data_fetcher.get_market_data(selected_pair, limit=200)
            
            if df is None or df.empty:
                st.error(t('no_market_data'))
                st.info(t('check_api_keys'))
                return
        except Exception as e:
            st.error(f"{t('no_market_data')}: {str(e)}")
            st.info(t('check_api_keys'))
            return
        
        # Current price
        current_price = df.iloc[-1]['close']
        price_change = ((current_price - df.iloc[-2]['close']) / df.iloc[-2]['close']) * 100 if len(df) > 1 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(t('current_price'), f"{current_price:,.0f} IRT", f"{price_change:+.2f}%")
        
        # Indicators
        if 'rsi' in df.columns:
            rsi = df.iloc[-1]['rsi']
            with col2:
                st.metric("RSI", f"{rsi:.2f}")
        
        if 'macd' in df.columns:
            macd = df.iloc[-1]['macd']
            with col3:
                st.metric("MACD", f"{macd:.2f}")
        
        # Generate signal
        with st.spinner("Generating trading signal..."):
            signal = strategy.generate_signal(selected_pair)
            with col4:
                st.metric(t('trading_signal'), signal['action'].upper(), f"{signal['confidence']:.2%}")
        
        # Price chart
        st.subheader(t('price_chart'))
        plot_price_chart(df, selected_pair)
        
        # Technical indicators
        plot_indicators(df)
        
        # Prophet forecast
        if config.get('prophet', {}).get('enabled', True):
            st.subheader("� Prophet Forecast")
            with st.spinner("Generating Prophet forecast..."):
                try:
                    prophet = ProphetForecaster(config.get('prophet', {}))
                    if prophet.model is None:
                        prophet.load_model(selected_pair)
                    
                    if prophet.model is not None:
                        forecast = prophet.forecast()
                        if not forecast['forecast_df'].empty:
                            plot_prophet_forecast(forecast['forecast_df'], df.tail(100))
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Direction", forecast['trend'].upper())
                            with col2:
                                st.metric("Confidence", f"{forecast['confidence']:.2%}")
                            with col3:
                                st.metric("Forecasted Price", f"{forecast.get('forecasted_price', 0):,.0f} IRT")
                except Exception as e:
                    st.warning(f"Prophet forecast not available: {e}")
        
        # Trading signal details
        st.subheader(t('trading_signal'))
        display_signal(signal)
        
        # Balance
        try:
            balance = exchange_manager.get_balance()
            if balance:
                display_balance(balance)
        except Exception as e:
            st.warning(f"Balance not available: {e}")


def render_trading(config: dict, strategy: HybridAIStrategy, exchange_manager: ExchangeManager):
    """Render trading page"""
    st.subheader(t('trading'))
    
    pairs = config.get('pairs', ['BTCIRT'])
    selected_pair = st.selectbox(t('select_pair'), pairs)
    
    # Generate signal
    if st.button(t('generate_signal')):
        with st.spinner("Generating signal..."):
            try:
                data_fetcher = DataFetcher(exchange_manager)
                strategy.data_fetcher = data_fetcher
                signal = strategy.generate_signal(selected_pair)
                display_signal(signal)
                
                # Manual trade execution
                if signal['action'] != 'hold':
                    st.subheader(t('execute_trade'))
                    col1, col2 = st.columns(2)
                    with col1:
                        amount = st.number_input(t('amount'), min_value=0.001, value=0.001, step=0.001)
                    with col2:
                        price = st.number_input(t('price'), min_value=0.0, value=0.0)
                    
                    if st.button(f"{signal['action'].upper()}"):
                        try:
                            result = exchange_manager.place_order(
                                selected_pair,
                                signal['action'],
                                amount,
                                price if price > 0 else None
                            )
                            st.success(f"{t('order_placed')}: {result.get('id', 'N/A')}")
                        except Exception as e:
                            st.error(f"{t('order_failed')}: {e}")
            except Exception as e:
                st.error(f"{t('error')}: {e}")
    
    # Open positions
    try:
        open_orders = exchange_manager.get_open_orders()
        if open_orders:
            display_open_orders(open_orders)
    except Exception as e:
        st.warning(f"Could not fetch open orders: {e}")


def render_backtest(config: dict, strategy: HybridAIStrategy, data_fetcher: DataFetcher):
    """Render backtest page"""
    st.subheader(t('backtesting'))
    
    pairs = config.get('pairs', ['BTCIRT'])
    selected_pair = st.selectbox(t('select_pair'), pairs)
    
    col1, col2 = st.columns(2)
    with col1:
        initial_balance = st.number_input(t('initial_balance'), min_value=1000000, value=100000000, step=10000000)
    
    if st.button(t('run_backtest')):
        with st.spinner("Running backtest..."):
            try:
                # Get historical data
                df = data_fetcher.get_market_data(selected_pair, limit=500)
                
                if df is None or df.empty:
                    st.error("No data available for backtest")
                    return
                
                # Run backtest
                risk_manager = RiskManager(config.get('risk', {}))
                backtester = Backtester(strategy, initial_balance)
                results = backtester.run_backtest(df, selected_pair)
                
                # Display results
                st.subheader(t('backtest_results'))
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric(t('total_return'), f"{results['total_return']:.2f}%")
                with col2:
                    st.metric(t('win_rate'), f"{results['win_rate']:.2f}%")
                with col3:
                    st.metric(t('total_trades'), results['total_trades'])
                with col4:
                    st.metric(t('max_drawdown'), f"{results['max_drawdown']:.2f}%")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric(t('sharpe_ratio'), f"{results['sharpe_ratio']:.2f}")
                with col2:
                    st.metric(t('profit_factor'), f"{results['profit_factor']:.2f}")
                with col3:
                    st.metric(t('final_balance'), f"{results['final_balance']:,.0f} IRT")
                with col4:
                    st.metric(t('total_pnl'), f"{results['total_pnl']:,.0f} IRT")
                
                # Equity curve
                plot_equity_curve(results['equity_curve'])
                
                # Trade list
                if results['trades']:
                    st.subheader("� Trade History")
                    trades_df = pd.DataFrame(results['trades'])
                    st.dataframe(trades_df, use_container_width=True)
                
            except Exception as e:
                st.error(f" Backtest error: {e}")


def render_train_models(config: dict, data_fetcher: DataFetcher):
    """Render model training page"""
    st.subheader(t('model_training'))
    
    st.info(t('training_in_progress'))
    
    pairs = config.get('pairs', ['BTCIRT', 'ETHIRT'])
    st.write(f"{t('select_pair')}: {', '.join(pairs)}")
    
    if st.button(t('train_all_models')):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            total_pairs = len(pairs)
            results = {}
            
            for idx, symbol in enumerate(pairs):
                status_text.text(f"{t('training_started')} {symbol}... ({idx+1}/{total_pairs})")
                progress_bar.progress((idx) / total_pairs)
                
                try:
                    # Fetch historical data
                    status_text.text(f"{t('training_status')}: {t('training_ml_models')} {symbol}")
                    df = data_fetcher.get_market_data(symbol, limit=500, include_indicators=True)
                    
                    if df is None or df.empty:
                        results[symbol] = {'status': 'failed', 'message': t('no_data_available')}
                        continue
                    
                    # Train ML models
                    if config.get('ai', {}).get('enabled', True):
                        from core.ai_model import AIModel
                        ai_model = AIModel(config.get('ai', {}))
                        
                        status_text.text(f"{t('training_status')}: {t('training_ml_models')} {symbol}")
                        ml_success = ai_model.train_ml_models(df, symbol)
                        
                        # Train LSTM if enabled
                        if 'lstm' in config.get('ai', {}).get('models', []):
                            status_text.text(f"{t('training_status')}: {t('training_lstm')} {symbol}")
                            ai_model.train_lstm(df, symbol)
                    
                    # Train Prophet
                    if config.get('prophet', {}).get('enabled', True):
                        status_text.text(f"{t('training_status')}: {t('training_prophet')} {symbol}")
                        from core.prophet_model import ProphetForecaster
                        prophet = ProphetForecaster(config.get('prophet', {}))
                        prophet.train(df, symbol)
                    
                    results[symbol] = {'status': 'success', 'message': t('models_trained')}
                    
                except Exception as e:
                    results[symbol] = {'status': 'failed', 'message': str(e)}
                
                progress_bar.progress((idx + 1) / total_pairs)
            
            # Display results
            status_text.text(t('training_completed'))
            st.success(t('training_completed'))
            
            st.subheader(t('training_status'))
            for symbol, result in results.items():
                if result['status'] == 'success':
                    st.success(f"✓ {symbol}: {result['message']}")
                else:
                    st.error(f"✗ {symbol}: {result['message']}")
            
        except Exception as e:
            st.error(f"{t('training_failed')}: {str(e)}")
            status_text.text(f"{t('training_failed')}: {str(e)}")


# Main app
def main():
    if not st.session_state.authenticated:
        login_page()
    else:
        main_dashboard()


if __name__ == "__main__":
    main()

