"""
📊 STREAMLIT DASHBOARD - Real-Time Portfolio Monitoring
Beautiful, interactive dashboard for tracking performance
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import os
import time

from config.settings import *
from src.paper_trading.paper_trader import PaperTrader
from src.data.data_fetcher import DataFetcher

# Page config
st.set_page_config(
    page_title="Super Math Trading System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #1f77b4;
    }
    .profit {
        color: #00cc00;
        font-weight: bold;
    }
    .loss {
        color: #ff0000;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_paper_trader():
    """Load paper trader (cached)"""
    return PaperTrader()


@st.cache_resource
def load_data_fetcher():
    """Load data fetcher (cached)"""
    return DataFetcher()


def display_header():
    """Display main header"""
    st.markdown('<h1 class="main-header">🚀 SUPER MATH TRADING SYSTEM 📊</h1>', unsafe_allow_html=True)
    st.markdown("---")


def display_portfolio_metrics(trader: PaperTrader, current_prices: dict):
    """Display key portfolio metrics"""
    summary = trader.get_summary(current_prices)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            label="💼 Portfolio Value",
            value=f"₹{summary['portfolio_value']:,.0f}",
            delta=f"{summary['total_return_percent']:+.2f}%"
        )

    with col2:
        st.metric(
            label="💰 Cash Available",
            value=f"₹{summary['capital']:,.0f}"
        )

    with col3:
        pnl_class = "profit" if summary['realized_pnl'] >= 0 else "loss"
        st.metric(
            label="📈 Realized P&L",
            value=f"₹{summary['realized_pnl']:+,.0f}"
        )

    with col4:
        st.metric(
            label="🎯 Win Rate",
            value=f"{summary['win_rate']:.1f}%",
            delta=f"{summary['winning_trades']}/{summary['total_trades']} trades"
        )

    with col5:
        st.metric(
            label="📊 Open Positions",
            value=summary['open_positions']
        )


def display_open_positions(trader: PaperTrader, current_prices: dict):
    """Display current open positions"""
    st.subheader("📊 Open Positions")

    if not trader.positions:
        st.info("No open positions")
        return

    positions_data = []

    for symbol, position in trader.positions.items():
        current_price = current_prices.get(symbol, position['entry_price'])

        pnl = (current_price - position['entry_price']) * position['shares']
        pnl_percent = (current_price - position['entry_price']) / position['entry_price'] * 100

        positions_data.append({
            'Symbol': symbol,
            'Type': position['trade_type'],
            'Shares': position['shares'],
            'Entry': f"₹{position['entry_price']:.2f}",
            'Current': f"₹{current_price:.2f}",
            'Target 2': f"₹{position['target2']:.2f}",
            'Stop Loss': f"₹{position['stop_loss']:.2f}",
            'P&L': f"₹{pnl:+,.0f}",
            'Return %': f"{pnl_percent:+.2f}%",
            'Score': position['score']
        })

    df = pd.DataFrame(positions_data)

    # Color code the dataframe
    st.dataframe(
        df,
        use_container_width=True,
        height=300
    )


def display_trade_history(trader: PaperTrader):
    """Display recent trade history"""
    st.subheader("📜 Recent Trades (Last 20)")

    if not trader.trade_history:
        st.info("No completed trades yet")
        return

    # Get last 20 trades
    recent_trades = sorted(
        trader.trade_history,
        key=lambda x: x['exit_date'],
        reverse=True
    )[:20]

    trades_data = []

    for trade in recent_trades:
        trades_data.append({
            'Symbol': trade['symbol'],
            'Type': trade['trade_type'],
            'Entry': f"₹{trade['entry_price']:.2f}",
            'Exit': f"₹{trade['exit_price']:.2f}",
            'Shares': trade['shares'],
            'P&L': f"₹{trade['pnl']:+,.0f}",
            'Return %': f"{trade['pnl_percent']:+.2f}%",
            'Reason': trade['reason'],
            'Exit Date': trade['exit_date'][:10]
        })

    df = pd.DataFrame(trades_data)
    st.dataframe(df, use_container_width=True, height=400)


def display_performance_chart(trader: PaperTrader):
    """Display performance chart"""
    st.subheader("📈 Performance Over Time")

    if not trader.trade_history:
        st.info("No trade history to display")
        return

    # Calculate cumulative P&L
    cumulative_pnl = []
    cumulative = 0
    dates = []

    for trade in sorted(trader.trade_history, key=lambda x: x['exit_date']):
        cumulative += trade['pnl']
        cumulative_pnl.append(cumulative)
        dates.append(trade['exit_date'][:10])

    # Create chart
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=dates,
        y=cumulative_pnl,
        mode='lines+markers',
        name='Cumulative P&L',
        line=dict(color='#1f77b4', width=3),
        fill='tozeroy'
    ))

    fig.update_layout(
        title='Cumulative Profit & Loss',
        xaxis_title='Date',
        yaxis_title='P&L (₹)',
        hovermode='x unified',
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)


def display_strategy_breakdown(trader: PaperTrader):
    """Display performance by strategy"""
    st.subheader("🎯 Strategy Performance")

    if not trader.trade_history:
        st.info("No data available")
        return

    # Group by strategy
    strategy_stats = {}

    for trade in trader.trade_history:
        strategy = trade['trade_type']

        if strategy not in strategy_stats:
            strategy_stats[strategy] = {
                'trades': 0,
                'wins': 0,
                'losses': 0,
                'total_pnl': 0
            }

        strategy_stats[strategy]['trades'] += 1
        strategy_stats[strategy]['total_pnl'] += trade['pnl']

        if trade['pnl'] > 0:
            strategy_stats[strategy]['wins'] += 1
        else:
            strategy_stats[strategy]['losses'] += 1

    # Display as metrics
    cols = st.columns(len(strategy_stats))

    for i, (strategy, stats) in enumerate(strategy_stats.items()):
        with cols[i]:
            win_rate = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0

            st.metric(
                label=f"{strategy}",
                value=f"₹{stats['total_pnl']:+,.0f}",
                delta=f"{win_rate:.1f}% WR"
            )
            st.text(f"Trades: {stats['trades']}")


def display_live_scanner():
    """Display live stock scanner status"""
    st.sidebar.header("🔍 Live Scanner")

    st.sidebar.info(f"""
    **Status:** Running

    **Scanning:**
    - {len(DEFAULT_WATCHLIST)} stocks
    - Every {SCAN_INTERVAL_MINUTES} minutes

    **Min Score:** {MIN_SIGNAL_SCORE}/10
    """)

    if st.sidebar.button("🔄 Force Refresh"):
        st.cache_resource.clear()
        st.rerun()


def main():
    """Main dashboard function"""
    display_header()

    # Sidebar
    display_live_scanner()

    # Auto-refresh control
    st.sidebar.header("⚙️ Settings")
    auto_refresh = st.sidebar.checkbox("Auto Refresh", value=True)
    refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 30, 300, 60)

    # Load data
    trader = load_paper_trader()
    fetcher = load_data_fetcher()

    # Get current prices for open positions
    current_prices = {}
    if trader.positions:
        for symbol in trader.positions.keys():
            price = fetcher.get_current_price(symbol)
            if price > 0:
                current_prices[symbol] = price

    # Main content
    display_portfolio_metrics(trader, current_prices)

    st.markdown("---")

    # Two columns for positions and trades
    col1, col2 = st.columns([1, 1])

    with col1:
        display_open_positions(trader, current_prices)

    with col2:
        display_strategy_breakdown(trader)

    st.markdown("---")

    display_performance_chart(trader)

    st.markdown("---")

    display_trade_history(trader)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666;">
    🚀 <b>Super Math Trading System</b> |
    Real-time monitoring with Paper Trading |
    Last updated: {time}
    </div>
    """.format(time=datetime.now().strftime('%H:%M:%S')), unsafe_allow_html=True)

    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()


if __name__ == "__main__":
    main()
