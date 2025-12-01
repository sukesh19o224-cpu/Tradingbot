"""
📊 STRATEGY 2 - LIVE PORTFOLIO DASHBOARD
Real-time view of Strategy 2 dual portfolio (50% Swing + 50% Positional)

Auto-refreshes every 5 seconds
Port: 8502 (different from Strategy 1's 8501)
"""

import streamlit as st
import json
import os
from datetime import datetime
import time
from src.data.enhanced_data_fetcher import EnhancedDataFetcher
from src.utils.trading_calendar import calculate_trading_days

# Page config
st.set_page_config(
    page_title="Strategy 2 - Portfolio Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .big-metric { font-size: 2rem; font-weight: bold; }
    .positive { color: #00ff00; }
    .negative { color: #ff4444; }
    .header { background: linear-gradient(90deg, #764ba2 0%, #667eea 100%); padding: 1rem; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=10)
def get_current_prices(symbols):
    """Fetch current prices for all symbols"""
    try:
        fetcher = EnhancedDataFetcher(api_delay=0.1)
        prices = {}
        failed_symbols = []

        for symbol in symbols:
            try:
                price = fetcher.get_current_price(symbol)
                if price > 0:
                    prices[symbol] = price
                else:
                    failed_symbols.append(symbol)
                    prices[symbol] = 0
            except Exception as e:
                failed_symbols.append(symbol)
                prices[symbol] = 0

        if failed_symbols and len(failed_symbols) < len(symbols):
            st.warning(f"⚠️ Could not fetch prices for: {', '.join([s.replace('.NS', '') for s in failed_symbols])}")

        return prices
    except Exception as e:
        st.error(f"❌ Error fetching prices: {e}")
        return {}


def load_portfolio_data():
    """Load Strategy 2 portfolio data from JSON files"""
    try:
        # Load swing portfolio
        swing_data = {}
        if os.path.exists('data/strategy2_swing_portfolio.json'):
            with open('data/strategy2_swing_portfolio.json', 'r') as f:
                swing_data = json.load(f)

        # Load positional portfolio
        positional_data = {}
        if os.path.exists('data/strategy2_positional_portfolio.json'):
            with open('data/strategy2_positional_portfolio.json', 'r') as f:
                positional_data = json.load(f)

        # Load trades
        swing_trades = []
        if os.path.exists('data/strategy2_swing_trades.json'):
            with open('data/strategy2_swing_trades.json', 'r') as f:
                swing_trades = json.load(f)

        positional_trades = []
        if os.path.exists('data/strategy2_positional_trades.json'):
            with open('data/strategy2_positional_trades.json', 'r') as f:
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

def display_portfolio_summary(data, current_prices):
    """Display combined portfolio summary with live P&L"""
    if not data:
        st.error("❌ Failed to load portfolio data!")
        st.info("💡 Make sure the data files exist in the data/ folder")
        return

    swing = data.get('swing', {})
    positional = data.get('positional', {})
    
    # Check if portfolios are empty/new
    if not swing and not positional:
        st.warning("⚠️ No portfolio data found. Start Strategy 2 to see data here!")
        st.info("""
        **To start Strategy 2:**
        1. Run: `bash RUN2.sh`
        2. Choose option 4 or 5 (Run Both Strategies)
        3. Strategy 2 will start after Strategy 1 completes
        """)
        return

    # Get initial capital (50/50 split)
    swing_initial = swing.get('initial_capital', 50000)
    positional_initial = positional.get('initial_capital', 50000)
    total_initial = swing_initial + positional_initial

    # Get current cash
    swing_capital = swing.get('capital', 50000)
    positional_capital = positional.get('capital', 50000)
    total_cash = swing_capital + positional_capital

    swing_positions = swing.get('positions', {})
    positional_positions = positional.get('positions', {})
    
    # Check if portfolios are empty (no positions yet)
    if not swing_positions and not positional_positions:
        st.info("📊 **Strategy 2 Portfolio - Initial State**")
        col1, col2 = st.columns(2)
        with col1:
            st.success(f"✅ Swing Capital: ₹{swing.get('capital', 50000):,.2f}")
        with col2:
            st.success(f"✅ Positional Capital: ₹{positional.get('capital', 50000):,.2f}")
        st.warning("⚠️ No active positions yet. Start Strategy 2 to begin trading!")
        st.info("""
        **To start Strategy 2:**
        1. Run: `bash RUN2.sh`
        2. Choose option 4 or 5 (Run Both Strategies)
        3. Strategy 2 will start after Strategy 1 completes
        """)
        return

    # Calculate invested amount and current value
    swing_invested = sum(pos.get('cost', 0) for pos in swing_positions.values())
    positional_invested = sum(pos.get('cost', 0) for pos in positional_positions.values())
    total_invested = swing_invested + positional_invested

    # Calculate current value of positions
    swing_current_value = 0
    for symbol, pos in swing_positions.items():
        current_price = current_prices.get(symbol, pos.get('entry_price', 0))
        swing_current_value += pos.get('shares', 0) * current_price

    positional_current_value = 0
    for symbol, pos in positional_positions.items():
        current_price = current_prices.get(symbol, pos.get('entry_price', 0))
        positional_current_value += pos.get('shares', 0) * current_price

    total_current_value = swing_current_value + positional_current_value

    # Calculate total portfolio value
    total_portfolio_value = total_cash + total_current_value

    # Calculate realized P&L
    swing_trades = data.get('swing_trades', [])
    positional_trades = data.get('positional_trades', [])
    realized_pnl = sum(t.get('pnl', 0) for t in swing_trades) + sum(t.get('pnl', 0) for t in positional_trades)

    # Calculate total P&L
    total_pnl = total_portfolio_value - total_initial
    total_pnl_pct = (total_pnl / total_initial * 100) if total_initial > 0 else 0

    unrealized_pnl = total_pnl - realized_pnl
    unrealized_pnl_pct = (unrealized_pnl / total_initial * 100) if total_initial > 0 else 0

    # Header
    st.markdown('<div class="header">', unsafe_allow_html=True)
    st.markdown("# 🎯 STRATEGY 2 - ULTRA STRICT PORTFOLIO")
    st.markdown("### 50% Swing (≥9.0) + 50% Positional (≥8.5)")
    st.markdown('</div>', unsafe_allow_html=True)

    # Top metrics
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "💰 Total Value",
            f"₹{total_portfolio_value:,.0f}",
            f"{total_pnl_pct:+.2f}%"
        )

    with col2:
        pnl_color = "positive" if total_pnl >= 0 else "negative"
        st.markdown(f'<p style="margin:0; color: gray;">Total P&L</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="big-metric {pnl_color}">₹{total_pnl:,.0f}</p>', unsafe_allow_html=True)

    with col3:
        st.metric("📊 Invested", f"₹{total_invested:,.0f}", f"{len(swing_positions) + len(positional_positions)} positions")

    with col4:
        st.metric("💵 Available Cash", f"₹{total_cash:,.0f}")

    with col5:
        st.metric(
            "Unrealized P&L",
            f"₹{unrealized_pnl:,.0f}",
            f"{unrealized_pnl_pct:+.2f}%"
        )

    st.markdown("---")

    # Portfolio breakdown
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔥 SWING Portfolio (50%)")
        st.write(f"💰 Capital: ₹{swing_capital:,.0f} / ₹50,000")
        st.write(f"📊 Invested: ₹{swing_invested:,.0f}")
        st.write(f"📈 Current Value: ₹{swing_current_value:,.0f}")
        swing_pnl = swing_current_value - swing_invested
        swing_pnl_pct = (swing_pnl / swing_invested * 100) if swing_invested > 0 else 0
        st.write(f"💵 Unrealized P&L: ₹{swing_pnl:,.0f} ({swing_pnl_pct:+.2f}%)")
        st.write(f"📌 Positions: {len(swing_positions)} / 5")

    with col2:
        st.subheader("📈 POSITIONAL Portfolio (50%)")
        st.write(f"💰 Capital: ₹{positional_capital:,.0f} / ₹50,000")
        st.write(f"📊 Invested: ₹{positional_invested:,.0f}")
        st.write(f"📈 Current Value: ₹{positional_current_value:,.0f}")
        pos_pnl = positional_current_value - positional_invested
        pos_pnl_pct = (pos_pnl / positional_invested * 100) if positional_invested > 0 else 0
        st.write(f"💵 Unrealized P&L: ₹{pos_pnl:,.0f} ({pos_pnl_pct:+.2f}%)")
        st.write(f"📌 Positions: {len(positional_positions)} / 5")

    st.markdown("---")


def display_open_positions(data, current_prices, portfolio_type):
    """Display open positions for a specific portfolio"""
    portfolio_data = data.get(portfolio_type, {})
    positions = portfolio_data.get('positions', {})

    if not positions:
        st.info(f"No open {portfolio_type} positions")
        return

    st.subheader(f"{'🔥 SWING' if portfolio_type == 'swing' else '📈 POSITIONAL'} - Open Positions")

    for symbol, pos in positions.items():
        entry_date = datetime.fromisoformat(pos['entry_date'])
        entry_price = pos['entry_price']
        shares = pos['shares']
        cost = pos['cost']
        stop_loss = pos['stop_loss']
        targets = pos['targets']
        signal_score = pos.get('signal_score', 0)

        # Get current price
        current_price = current_prices.get(symbol, entry_price)

        # Calculate P&L
        current_value = shares * current_price
        pnl = current_value - cost
        pnl_pct = (pnl / cost * 100) if cost > 0 else 0

        # Calculate holding days
        hold_days = calculate_trading_days(entry_date, datetime.now())
        max_hold_days = pos.get('max_holding_days', 7 if portfolio_type == 'swing' else 15)

        # Display position card
        with st.expander(f"{'🔥' if pnl >= 0 else '❄️'} {symbol.replace('.NS', '')} | P&L: ₹{pnl:,.0f} ({pnl_pct:+.2f}%)", expanded=True):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.write("**Entry Details**")
                st.write(f"Entry: ₹{entry_price:.2f}")
                st.write(f"Shares: {shares}")
                st.write(f"Cost: ₹{cost:,.0f}")
                st.write(f"Score: {signal_score:.1f}/10")

            with col2:
                st.write("**Current Status**")
                st.write(f"Current: ₹{current_price:.2f}")
                st.write(f"Value: ₹{current_value:,.0f}")
                pnl_color = "🟢" if pnl >= 0 else "🔴"
                st.write(f"P&L: {pnl_color} ₹{pnl:,.0f} ({pnl_pct:+.2f}%)")
                st.write(f"Hold Days: {hold_days} / {max_hold_days}")

            with col3:
                st.write("**Exit Levels**")
                st.write(f"Stop Loss: ₹{stop_loss:.2f}")
                st.write(f"T1: ₹{targets[0]:.2f}")
                st.write(f"T2: ₹{targets[1]:.2f}")
                st.write(f"T3: ₹{targets[2]:.2f}")


def display_closed_trades(data, portfolio_type, limit=10):
    """Display recent closed trades"""
    trades = data.get(f'{portfolio_type}_trades', [])

    if not trades:
        st.info(f"No closed {portfolio_type} trades yet")
        return

    st.subheader(f"{'🔥 SWING' if portfolio_type == 'swing' else '📈 POSITIONAL'} - Recent Closed Trades")

    # Sort by exit date (most recent first)
    trades_sorted = sorted(trades, key=lambda x: x.get('exit_date', ''), reverse=True)[:limit]

    for trade in trades_sorted:
        symbol = trade['symbol']
        entry_price = trade['entry_price']
        exit_price = trade['exit_price']
        pnl = trade['pnl']
        pnl_pct = trade['pnl_pct']
        exit_reason = trade.get('exit_reason', 'Unknown')
        entry_date = trade.get('entry_date', 'N/A')
        exit_date = trade.get('exit_date', 'N/A')

        # Calculate hold days
        try:
            entry_dt = datetime.fromisoformat(entry_date)
            exit_dt = datetime.fromisoformat(exit_date)
            hold_days = calculate_trading_days(entry_dt, exit_dt)
        except:
            hold_days = 0

        pnl_emoji = "🟢" if pnl >= 0 else "🔴"

        with st.expander(f"{pnl_emoji} {symbol.replace('.NS', '')} | {exit_reason} | ₹{pnl:,.0f} ({pnl_pct:+.2f}%)"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.write(f"**Entry:** ₹{entry_price:.2f}")
                st.write(f"**Date:** {entry_date[:10] if entry_date != 'N/A' else 'N/A'}")

            with col2:
                st.write(f"**Exit:** ₹{exit_price:.2f}")
                st.write(f"**Date:** {exit_date[:10] if exit_date != 'N/A' else 'N/A'}")

            with col3:
                st.write(f"**P&L:** ₹{pnl:,.0f} ({pnl_pct:+.2f}%)")
                st.write(f"**Hold:** {hold_days} days")


def main():
    """Main dashboard function"""
    
    # Auto-refresh
    st.sidebar.markdown("### ⚙️ Settings")
    auto_refresh = st.sidebar.checkbox("Auto-refresh (5s)", value=True)
    
    if auto_refresh:
        time.sleep(5)
        st.rerun()

    # Load data
    data = load_portfolio_data()

    if not data:
        st.error("Failed to load portfolio data")
        return

    # Get all symbols for price fetching
    all_symbols = set()
    if data.get('swing', {}).get('positions'):
        all_symbols.update(data['swing']['positions'].keys())
    if data.get('positional', {}).get('positions'):
        all_symbols.update(data['positional']['positions'].keys())

    # Fetch current prices
    current_prices = get_current_prices(list(all_symbols)) if all_symbols else {}

    # Display sections
    display_portfolio_summary(data, current_prices)

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["🔥 Swing Positions", "📈 Positional Positions", "🔥 Swing History", "📈 Positional History"])

    with tab1:
        display_open_positions(data, current_prices, 'swing')

    with tab2:
        display_open_positions(data, current_prices, 'positional')

    with tab3:
        display_closed_trades(data, 'swing', limit=15)

    with tab4:
        display_closed_trades(data, 'positional', limit=15)

    # Footer
    st.markdown("---")
    st.markdown(f"*Last updated: {datetime.now().strftime('%d %b %Y, %I:%M:%S %p')} IST*")


if __name__ == '__main__':
    main()
