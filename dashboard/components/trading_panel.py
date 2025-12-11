"""
Trading panel components
"""

import streamlit as st
from typing import Dict, Optional


def display_signal(signal: Dict):
    """Display trading signal"""
    if not signal:
        st.info("No signal available")
        return
    
    action = signal.get('action', 'hold')
    confidence = signal.get('confidence', 0.0)
    reason = signal.get('reason', 'No reason provided')
    
    # Color based on action
    if action == 'buy':
        color = 'green'
        emoji = ''
    elif action == 'sell':
        color = 'red'
        emoji = ''
    else:
        color = 'gray'
        emoji = ''
    
    st.markdown(f"### Trading Signal: **{action.upper()}**")
    st.markdown(f"**Confidence:** {confidence:.2%}")
    st.markdown(f"**Reason:** {reason}")
    
    # Signal breakdown
    if 'signals' in signal:
        signals = signal['signals']
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Buy Signals", signals.get('buy', 0))
        with col2:
            st.metric("Sell Signals", signals.get('sell', 0))
        with col3:
            st.metric("Hold Signals", signals.get('hold', 0))


def display_balance(balance: Dict[str, float]):
    """Display account balance"""
    if not balance:
        st.warning("Balance not available")
        return
    
    st.subheader("Account Balance")
    
    cols = st.columns(min(4, len(balance)))
    for idx, (currency, amount) in enumerate(balance.items()):
        with cols[idx % 4]:
            st.metric(currency, f"{amount:,.2f}")


def display_open_positions(positions: list):
    """Display open positions"""
    st.subheader("Open Positions")
    
    if not positions:
        st.info("No open positions")
        return
    
    for pos in positions:
        with st.expander(f"{pos.get('symbol', 'N/A')} - {pos.get('side', 'N/A').upper()}"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Entry Price", f"{pos.get('entry_price', 0):,.0f}")
            with col2:
                st.metric("Amount", f"{pos.get('amount', 0):,.4f}")
            with col3:
                st.metric("Stop Loss", f"{pos.get('stop_loss', 0):,.0f}")


def display_open_orders(orders: list):
    """Display open orders"""
    st.subheader("� Open Orders")
    
    if not orders:
        st.info("No open orders")
        return
    
    for order in orders:
        st.write(f"- {order.get('symbol', 'N/A')} | {order.get('side', 'N/A')} | "
                f"Amount: {order.get('amount', 0):,.4f} | "
                f"Price: {order.get('price', 0):,.0f}")

