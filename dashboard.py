"""
📊 LIVE PORTFOLIO DASHBOARD
Real-time view of your dual portfolio (Swing + Positional)

Auto-refreshes every 5 seconds
"""

import streamlit as st
import json
import os
from datetime import datetime
import time

# Page config
st.set_page_config(
    page_title="Trading Portfolio Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .big-metric { font-size: 2rem; font-weight: bold; }
    .positive { color: #00ff00; }
    .negative { color: #ff4444; }
    .header { background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); padding: 1rem; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

def load_portfolio_data():
    """Load portfolio data from JSON files"""
    try:
        # Load swing portfolio
        swing_data = {}
        if os.path.exists('data/swing_portfolio.json'):
            with open('data/swing_portfolio.json', 'r') as f:
                swing_data = json.load(f)

        # Load positional portfolio
        positional_data = {}
        if os.path.exists('data/positional_portfolio.json'):
            with open('data/positional_portfolio.json', 'r') as f:
                positional_data = json.load(f)

        # Load swing trades
        swing_trades = []
        if os.path.exists('data/swing_trades.json'):
            with open('data/swing_trades.json', 'r') as f:
                swing_trades = json.load(f)

        # Load positional trades
        positional_trades = []
        if os.path.exists('data/positional_trades.json'):
            with open('data/positional_trades.json', 'r') as f:
                positional_trades = json.load(f)

        return {
            'swing': swing_data,
            'positional': positional_data,
            'swing_trades': swing_trades,
            'positional_trades': positional_trades
        }
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def display_portfolio_summary(data):
    """Display combined portfolio summary"""
    if not data:
        st.warning("No portfolio data found. Start trading to see data here!")
        return

    swing = data.get('swing', {})
    positional = data.get('positional', {})

    # Calculate totals
    swing_capital = swing.get('capital', 60000)
    positional_capital = positional.get('capital', 40000)
    total_capital = swing_capital + positional_capital

    swing_positions = swing.get('positions', {})
    positional_positions = positional.get('positions', {})

    # Header
    st.markdown('<div class="header">', unsafe_allow_html=True)
    st.title("💼 DUAL PORTFOLIO DASHBOARD")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("💰 Total Capital", f"₹{total_capital:,.0f}")

    with col2:
        st.metric("🔥 Swing Cash", f"₹{swing_capital:,.0f}")

    with col3:
        st.metric("📈 Positional Cash", f"₹{positional_capital:,.0f}")

    with col4:
        total_positions = len(swing_positions) + len(positional_positions)
        st.metric("📊 Open Positions", total_positions)

def display_open_positions(data):
    """Display open positions"""
    if not data:
        return

    swing = data.get('swing', {})
    positional = data.get('positional', {})

    swing_positions = swing.get('positions', {})
    positional_positions = positional.get('positions', {})

    st.markdown("---")
    st.subheader("📊 OPEN POSITIONS")

    if not swing_positions and not positional_positions:
        st.info("No open positions. System is scanning for opportunities...")
        return

    # Swing positions
    if swing_positions:
        st.markdown("### 🔥 Swing Positions")
        for symbol, pos in swing_positions.items():
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                st.write(f"**{symbol.replace('.NS', '')}**")

            with col2:
                st.write(f"Entry: ₹{pos.get('entry_price', 0):.2f}")

            with col3:
                st.write(f"Shares: {pos.get('shares', 0)}")

            with col4:
                invested = pos.get('entry_price', 0) * pos.get('shares', 0)
                st.write(f"Invested: ₹{invested:,.0f}")

            with col5:
                entry_date = pos.get('entry_date', 'N/A')
                st.write(f"Since: {entry_date}")

    # Positional positions
    if positional_positions:
        st.markdown("### 📈 Positional Positions")
        for symbol, pos in positional_positions.items():
            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                st.write(f"**{symbol.replace('.NS', '')}**")

            with col2:
                st.write(f"Entry: ₹{pos.get('entry_price', 0):.2f}")

            with col3:
                st.write(f"Shares: {pos.get('shares', 0)}")

            with col4:
                invested = pos.get('entry_price', 0) * pos.get('shares', 0)
                st.write(f"Invested: ₹{invested:,.0f}")

            with col5:
                entry_date = pos.get('entry_date', 'N/A')
                st.write(f"Since: {entry_date}")

def display_trade_history(data):
    """Display recent trade history"""
    if not data:
        return

    swing_trades = data.get('swing_trades', [])
    positional_trades = data.get('positional_trades', [])

    st.markdown("---")
    st.subheader("📜 RECENT TRADES")

    if not swing_trades and not positional_trades:
        st.info("No trades yet. Waiting for signals...")
        return

    # Combine and sort by date
    all_trades = []
    for trade in swing_trades:
        trade['type'] = 'Swing'
        all_trades.append(trade)

    for trade in positional_trades:
        trade['type'] = 'Positional'
        all_trades.append(trade)

    # Sort by exit date (most recent first)
    all_trades.sort(key=lambda x: x.get('exit_date', ''), reverse=True)

    # Show last 10 trades
    for trade in all_trades[:10]:
        col1, col2, col3, col4, col5, col6 = st.columns(6)

        with col1:
            badge = "🔥" if trade['type'] == 'Swing' else "📈"
            st.write(f"{badge} **{trade.get('symbol', 'N/A').replace('.NS', '')}**")

        with col2:
            st.write(f"Entry: ₹{trade.get('entry_price', 0):.2f}")

        with col3:
            st.write(f"Exit: ₹{trade.get('exit_price', 0):.2f}")

        with col4:
            pnl = trade.get('pnl', 0)
            pnl_class = "positive" if pnl > 0 else "negative"
            st.markdown(f"<span class='{pnl_class}'>₹{pnl:+,.0f}</span>", unsafe_allow_html=True)

        with col5:
            pnl_pct = trade.get('pnl_percent', 0)
            pnl_class = "positive" if pnl_pct > 0 else "negative"
            st.markdown(f"<span class='{pnl_class}'>{pnl_pct:+.2f}%</span>", unsafe_allow_html=True)

        with col6:
            st.write(f"Exit: {trade.get('exit_date', 'N/A')}")

def main():
    """Main dashboard function"""
    # Auto-refresh every 5 seconds
    st.markdown("### 🔄 Auto-refresh: Every 5 seconds")

    # Load data
    data = load_portfolio_data()

    # Display sections
    display_portfolio_summary(data)
    display_open_positions(data)
    display_trade_history(data)

    # Footer
    st.markdown("---")
    current_time = datetime.now().strftime("%d %b %Y, %I:%M:%S %p")
    st.caption(f"Last updated: {current_time} | Data refreshes automatically")

    # Auto-refresh
    time.sleep(5)
    st.rerun()

if __name__ == "__main__":
    main()
