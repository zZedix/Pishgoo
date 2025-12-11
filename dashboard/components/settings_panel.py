"""
Settings panel components
"""

import streamlit as st
from config.settings import load_config, save_config
from utils.translations import get_translation

def t(key: str) -> str:
    """Get translated text"""
    lang = st.session_state.get('language', 'en')
    return get_translation(key, lang)


def render_settings():
    """Render settings panel"""
    config = load_config()
    
    if not config:
        st.error("Failed to load configuration")
        return
    
    st.subheader(t('settings'))
    
    # Password change section
    with st.expander(t('change_password')):
        current_password = st.text_input(t('current_password'), type="password")
        new_password = st.text_input(t('new_password'), type="password")
        confirm_password = st.text_input(t('confirm_password'), type="password")
        
        if st.button(t('save_password')):
            # Validate current password
            stored_password = config.get('dashboard', {}).get('password', 'pishgoo123')
            if current_password != stored_password:
                st.error(t('wrong_current_password'))
            elif new_password != confirm_password:
                st.error(t('password_mismatch'))
            elif len(new_password) < 3:
                st.error(t('password_too_short'))
            else:
                # Update password
                if 'dashboard' not in config:
                    config['dashboard'] = {}
                config['dashboard']['password'] = new_password
                save_config(config)
                st.success(t('password_saved'))
    
    # Exchange settings
    with st.expander(t('exchange_config')):
        exchange = st.selectbox(
            t('exchange'),
            ["nobitex", "wallex"],
            index=0 if config.get('exchange', 'nobitex') == 'nobitex' else 1
        )
        
        api_key = st.text_input(
            t('api_key'),
            value=config.get('api_key', ''),
            type="password"
        )
        
        api_secret = st.text_input(
            t('api_secret'),
            value=config.get('api_secret', ''),
            type="password"
        )
        
        if st.button(t('save_exchange')):
            config['exchange'] = exchange
            config['api_key'] = api_key
            config['api_secret'] = api_secret
            save_config(config)
            st.success(t('exchange_saved'))
    
    # Trading pairs
    with st.expander(t('trading_pairs')):
        default_pairs = config.get('pairs', ['BTCIRT', 'ETHIRT'])
        pairs_input = st.text_input(
            t('pairs_input'),
            value=", ".join(default_pairs)
        )
        
        if st.button(t('save_pairs')):
            pairs = [p.strip() for p in pairs_input.split(',')]
            config['pairs'] = pairs
            save_config(config)
            st.success(t('pairs_saved'))
    
    # Risk management
    with st.expander(t('risk_management')):
        # Convert decimal to percentage for display
        stop_loss_decimal = config.get('risk', {}).get('stop_loss', 0.03)
        stop_loss_percent = stop_loss_decimal * 100
        
        take_profit_decimal = config.get('risk', {}).get('take_profit', 0.05)
        take_profit_percent = take_profit_decimal * 100
        
        max_position_decimal = config.get('risk', {}).get('max_position_size', 0.20)
        max_position_percent = max_position_decimal * 100
        
        stop_loss = st.slider(
            t('stop_loss'),
            min_value=0,
            max_value=100,
            value=int(stop_loss_percent),
            step=1,
            format="%d%%"
        )
        
        take_profit = st.slider(
            t('take_profit'),
            min_value=0,
            max_value=100,
            value=int(take_profit_percent),
            step=1,
            format="%d%%"
        )
        
        max_position = st.slider(
            t('max_position_size'),
            min_value=0,
            max_value=100,
            value=int(max_position_percent),
            step=1,
            format="%d%%"
        )
        
        if st.button(t('save_risk')):
            if 'risk' not in config:
                config['risk'] = {}
            # Convert percentage back to decimal for storage
            config['risk']['stop_loss'] = stop_loss / 100.0
            config['risk']['take_profit'] = take_profit / 100.0
            config['risk']['max_position_size'] = max_position / 100.0
            save_config(config)
            st.success(t('risk_saved'))
    
    # Trading amount
    with st.expander(t('trading_amount')):
        amount = st.number_input(
            t('amount_per_trade'),
            min_value=100000,
            max_value=1000000000,
            value=config.get('amount_per_trade', 5000000),
            step=1000000
        )
        
        if st.button(t('save_amount')):
            config['amount_per_trade'] = amount
            save_config(config)
            st.success(t('amount_saved'))
    
    # AI settings
    with st.expander(t('ai_settings')):
        ai_enabled = st.checkbox(
            t('enable_ai'),
            value=config.get('ai', {}).get('enabled', True)
        )
        
        models = st.multiselect(
            t('select_models'),
            ["ml", "lstm", "prophet"],
            default=config.get('ai', {}).get('models', ['ml', 'lstm', 'prophet'])
        )
        
        confidence_threshold = st.slider(
            t('confidence_threshold'),
            min_value=0.0,
            max_value=1.0,
            value=config.get('ai', {}).get('confidence_threshold', 0.7),
            step=0.05
        )
        
        if st.button(t('save_ai')):
            if 'ai' not in config:
                config['ai'] = {}
            config['ai']['enabled'] = ai_enabled
            config['ai']['models'] = models
            config['ai']['confidence_threshold'] = confidence_threshold
            save_config(config)
            st.success(t('ai_saved'))

