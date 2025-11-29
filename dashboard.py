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
from src.data.enhanced_data_fetcher import EnhancedDataFetcher
from src.utils.trading_calendar import calculate_trading_days

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

@st.cache_data(ttl=10)  # Cache for 10 seconds only (more frequent updates)
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

        # Show warning if some prices failed to fetch
        if failed_symbols and len(failed_symbols) < len(symbols):
            st.warning(f"⚠️ Could not fetch prices for: {', '.join([s.replace('.NS', '') for s in failed_symbols])}")

        return prices
    except Exception as e:
        st.error(f"❌ Error fetching prices: {e}")
        return {}


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

def display_portfolio_summary(data, current_prices):
    """Display combined portfolio summary with live P&L"""
    if not data:
        st.warning("No portfolio data found. Start trading to see data here!")
        return

    swing = data.get('swing', {})
    positional = data.get('positional', {})

    # Get initial capital from saved data
    swing_initial = swing.get('initial_capital', 60000)
    positional_initial = positional.get('initial_capital', 40000)
    total_initial = swing_initial + positional_initial

    # Get current cash
    swing_capital = swing.get('capital', 60000)
    positional_capital = positional.get('capital', 40000)
    total_cash = swing_capital + positional_capital

    swing_positions = swing.get('positions', {})
    positional_positions = positional.get('positions', {})

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

    # Calculate total portfolio value (cash + positions)
    swing_portfolio_value = swing_capital + swing_current_value
    positional_portfolio_value = positional_capital + positional_current_value
    total_portfolio_value = total_cash + total_current_value

    # Calculate realized P&L from closed trades
    swing_trades = data.get('swing_trades', [])
    positional_trades = data.get('positional_trades', [])
    realized_pnl = sum(t.get('pnl', 0) for t in swing_trades) + sum(t.get('pnl', 0) for t in positional_trades)

    # Calculate total P&L (realized + unrealized)
    total_pnl = total_portfolio_value - total_initial
    total_pnl_pct = (total_pnl / total_initial * 100) if total_initial > 0 else 0

    # Header
    st.markdown('<div class="header">', unsafe_allow_html=True)
    st.title("💼 DUAL PORTFOLIO DASHBOARD")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Main Summary Metrics
    st.subheader("📊 PORTFOLIO OVERVIEW")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("💰 Initial Capital", f"₹{total_initial:,.0f}")

    with col2:
        # Normal delta coloring: green for profit, red for loss
        st.metric("📈 Current Value", f"₹{total_portfolio_value:,.0f}",
                 delta=f"₹{total_pnl:+,.0f}")
        # Note: st.metric automatically shows green↑ for positive, red↓ for negative

    with col3:
        pnl_color = "positive" if total_pnl >= 0 else "negative"
        st.markdown(f"**Total P&L**")
        st.markdown(f"<span class='{pnl_color} big-metric'>₹{total_pnl:+,.0f} ({total_pnl_pct:+.2f}%)</span>",
                   unsafe_allow_html=True)

    with col4:
        st.metric("💵 Available Cash", f"₹{total_cash:,.0f}")

    with col5:
        total_positions = len(swing_positions) + len(positional_positions)
        st.metric("📊 Open Positions", total_positions)

    st.markdown("---")

    # Detailed Breakdown
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔥 SWING PORTFOLIO")
        swing_pnl = swing_portfolio_value - swing_initial
        swing_pnl_pct = (swing_pnl / swing_initial * 100) if swing_initial > 0 else 0
        pnl_color = "positive" if swing_pnl >= 0 else "negative"

        st.write(f"**Initial:** ₹{swing_initial:,.0f}")
        st.write(f"**Current Value:** ₹{swing_portfolio_value:,.0f}")
        st.markdown(f"**P&L:** <span class='{pnl_color}'>₹{swing_pnl:+,.0f} ({swing_pnl_pct:+.2f}%)</span>",
                   unsafe_allow_html=True)
        st.write(f"**Cash:** ₹{swing_capital:,.0f}")
        st.write(f"**Invested:** ₹{swing_invested:,.0f}")
        st.write(f"**Positions:** {len(swing_positions)}")

    with col2:
        st.subheader("📈 POSITIONAL PORTFOLIO")
        positional_pnl = positional_portfolio_value - positional_initial
        positional_pnl_pct = (positional_pnl / positional_initial * 100) if positional_initial > 0 else 0
        pnl_color = "positive" if positional_pnl >= 0 else "negative"

        st.write(f"**Initial:** ₹{positional_initial:,.0f}")
        st.write(f"**Current Value:** ₹{positional_portfolio_value:,.0f}")
        st.markdown(f"**P&L:** <span class='{pnl_color}'>₹{positional_pnl:+,.0f} ({positional_pnl_pct:+.2f}%)</span>",
                   unsafe_allow_html=True)
        st.write(f"**Cash:** ₹{positional_capital:,.0f}")
        st.write(f"**Invested:** ₹{positional_invested:,.0f}")
        st.write(f"**Positions:** {len(positional_positions)}")

def display_open_positions(data, current_prices):
    """Display open positions with live P&L and detailed metrics"""
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
            # Get current price
            current_price = current_prices.get(symbol, pos.get('entry_price', 0))
            entry_price = pos.get('entry_price', 0)
            shares = pos.get('shares', 0)
            initial_shares = pos.get('initial_shares', shares)

            # Calculate P&L
            invested = entry_price * shares
            current_value = current_price * shares
            pnl = current_value - invested
            pnl_pct = (pnl / invested * 100) if invested > 0 else 0
            pnl_color = "positive" if pnl >= 0 else "negative"

            # Calculate hold days (trading days)
            entry_date = pos.get('entry_date', '')
            try:
                entry_dt = datetime.fromisoformat(entry_date)
                hold_days = calculate_trading_days(entry_dt, datetime.now())
            except:
                hold_days = 0

            # OVERRIDE: Use correct max days based on strategy (swing = 7 days)
            # This fixes old positions that have incorrect max_holding_days
            strategy = pos.get('strategy', 'swing')
            if strategy == 'swing':
                max_hold_days = 7  # Swing trades should be 7 trading days
            else:
                max_hold_days = pos.get('max_holding_days', 15)

            # Calculate trailing stop (same logic as paper_trader.py)
            initial_stop_loss = pos.get('stop_loss', 0)
            current_stop_loss = initial_stop_loss
            trailing_active = False

            # Trailing stop activates at +5% profit
            if pnl_pct >= 5.0:
                # Trail stop at 3% below current price or breakeven, whichever is higher
                trailing_stop = max(entry_price, current_price * 0.97)
                if trailing_stop > initial_stop_loss:
                    current_stop_loss = trailing_stop
                    trailing_active = True

            # Display position in expandable section
            with st.expander(f"**{symbol.replace('.NS', '')}** | 🔥 SWING | P&L: {pnl:+,.0f} ({pnl_pct:+.2f}%) | Current: ₹{current_price:.2f}"):
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.write("**Entry Info**")
                    st.write(f"Strategy: 🔥 Swing")
                    signal_type = pos.get('signal_type', 'UNKNOWN')
                    signal_emoji = {"MOMENTUM": "🚀", "MEAN_REVERSION": "🔄", "BREAKOUT": "💥", "UNKNOWN": "❓"}
                    st.write(f"Type: {signal_emoji.get(signal_type, '❓')} {signal_type}")
                    st.write(f"Entry Price: ₹{entry_price:.2f}")
                    st.write(f"Entry Date: {entry_date[:10] if entry_date else 'N/A'}")
                    st.write(f"Score: {pos.get('score', 0):.1f}/10")

                with col2:
                    st.write("**Shares**")
                    st.write(f"Initial: {initial_shares}")
                    st.write(f"Current: {shares}")
                    if initial_shares != shares:
                        exited = initial_shares - shares
                        st.write(f"Exited: {exited} ({exited/initial_shares*100:.0f}%)")

                with col3:
                    st.write("**Current Status**")
                    st.write(f"Current Price: ₹{current_price:.2f}")
                    st.write(f"Current Value: ₹{current_value:,.0f}")
                    st.markdown(f"**P&L:** <span class='{pnl_color}'>₹{pnl:+,.0f} ({pnl_pct:+.2f}%)</span>",
                               unsafe_allow_html=True)

                with col4:
                    st.write("**Holding Period**")
                    st.write(f"Hold Days: {hold_days} / {max_hold_days}")
                    st.write(f"Target 1: ₹{pos.get('target1', 0):.2f}")
                    st.write(f"Target 2: ₹{pos.get('target2', 0):.2f}")

                    # Show stop loss status (breakeven, trailing, or normal)
                    if trailing_active:
                        st.write(f"~~Initial Stop: ₹{initial_stop_loss:.2f}~~")
                        st.markdown(f"**🔒 Trailing Stop: ₹{current_stop_loss:.2f}** (Active!)")
                    elif abs(current_stop_loss - entry_price) < 0.01:  # Stop at breakeven
                        st.write(f"~~Initial Stop: ₹{initial_stop_loss:.2f}~~")
                        st.markdown(f"**✅ Breakeven Stop: ₹{current_stop_loss:.2f}** (T1 Hit!)")
                    else:
                        st.write(f"Stop Loss: ₹{current_stop_loss:.2f}")

    # Positional positions
    if positional_positions:
        st.markdown("### 📈 Positional Positions")

        for symbol, pos in positional_positions.items():
            # Get current price
            current_price = current_prices.get(symbol, pos.get('entry_price', 0))
            entry_price = pos.get('entry_price', 0)
            shares = pos.get('shares', 0)
            initial_shares = pos.get('initial_shares', shares)

            # Calculate P&L
            invested = entry_price * shares
            current_value = current_price * shares
            pnl = current_value - invested
            pnl_pct = (pnl / invested * 100) if invested > 0 else 0
            pnl_color = "positive" if pnl >= 0 else "negative"

            # Calculate hold days (trading days)
            entry_date = pos.get('entry_date', '')
            try:
                entry_dt = datetime.fromisoformat(entry_date)
                hold_days = calculate_trading_days(entry_dt, datetime.now())
            except:
                hold_days = 0

            # OVERRIDE: Use correct max days based on strategy (positional = 30 days)
            # This fixes old positions that have incorrect max_holding_days
            strategy = pos.get('strategy', 'positional')
            if strategy == 'positional':
                max_hold_days = 30  # Positional trades should be 30 trading days
            else:
                max_hold_days = pos.get('max_holding_days', 45)

            # Calculate trailing stop (same logic as paper_trader.py)
            initial_stop_loss = pos.get('stop_loss', 0)
            current_stop_loss = initial_stop_loss
            trailing_active = False

            # Trailing stop activates at +5% profit
            if pnl_pct >= 5.0:
                # Trail stop at 3% below current price or breakeven, whichever is higher
                trailing_stop = max(entry_price, current_price * 0.97)
                if trailing_stop > initial_stop_loss:
                    current_stop_loss = trailing_stop
                    trailing_active = True

            # Display position in expandable section
            with st.expander(f"**{symbol.replace('.NS', '')}** | 📈 POSITIONAL | P&L: {pnl:+,.0f} ({pnl_pct:+.2f}%) | Current: ₹{current_price:.2f}"):
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.write("**Entry Info**")
                    st.write(f"Strategy: 📈 Positional")
                    signal_type = pos.get('signal_type', 'UNKNOWN')
                    signal_emoji = {"MOMENTUM": "🚀", "MEAN_REVERSION": "🔄", "BREAKOUT": "💥", "UNKNOWN": "❓"}
                    st.write(f"Type: {signal_emoji.get(signal_type, '❓')} {signal_type}")
                    st.write(f"Entry Price: ₹{entry_price:.2f}")
                    st.write(f"Entry Date: {entry_date[:10] if entry_date else 'N/A'}")
                    st.write(f"Score: {pos.get('score', 0):.1f}/10")

                with col2:
                    st.write("**Shares**")
                    st.write(f"Initial: {initial_shares}")
                    st.write(f"Current: {shares}")
                    if initial_shares != shares:
                        exited = initial_shares - shares
                        st.write(f"Exited: {exited} ({exited/initial_shares*100:.0f}%)")

                with col3:
                    st.write("**Current Status**")
                    st.write(f"Current Price: ₹{current_price:.2f}")
                    st.write(f"Current Value: ₹{current_value:,.0f}")
                    st.markdown(f"**P&L:** <span class='{pnl_color}'>₹{pnl:+,.0f} ({pnl_pct:+.2f}%)</span>",
                               unsafe_allow_html=True)

                with col4:
                    st.write("**Holding Period**")
                    st.write(f"Hold Days: {hold_days} / {max_hold_days}")
                    st.write(f"Target 1: ₹{pos.get('target1', 0):.2f}")
                    st.write(f"Target 2: ₹{pos.get('target2', 0):.2f}")

                    # Show stop loss status (breakeven, trailing, or normal)
                    if trailing_active:
                        st.write(f"~~Initial Stop: ₹{initial_stop_loss:.2f}~~")
                        st.markdown(f"**🔒 Trailing Stop: ₹{current_stop_loss:.2f}** (Active!)")
                    elif abs(current_stop_loss - entry_price) < 0.01:  # Stop at breakeven
                        st.write(f"~~Initial Stop: ₹{initial_stop_loss:.2f}~~")
                        st.markdown(f"**✅ Breakeven Stop: ₹{current_stop_loss:.2f}** (T1 Hit!)")
                    else:
                        st.write(f"Stop Loss: ₹{current_stop_loss:.2f}")

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
    # Header with refresh controls
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### 🔄 Auto-refresh: Every 5 seconds")
    with col2:
        # Manual refresh button
        if st.button("🔄 Force Refresh", key="refresh_btn"):
            st.cache_data.clear()  # Clear cache to force fresh data
            st.rerun()

    # Load data
    data = load_portfolio_data()

    if data:
        # Get all symbols from both portfolios
        swing_positions = data.get('swing', {}).get('positions', {})
        positional_positions = data.get('positional', {}).get('positions', {})
        all_symbols = list(swing_positions.keys()) + list(positional_positions.keys())

        # Fetch current prices
        if all_symbols:
            with st.spinner("🔄 Fetching live prices..."):
                current_prices = get_current_prices(all_symbols)
                if current_prices:
                    # Count how many prices were successfully fetched
                    successful = sum(1 for p in current_prices.values() if p > 0)
                    st.info(f"📊 Fetched {successful}/{len(all_symbols)} prices successfully")
        else:
            current_prices = {}

        # Display sections
        display_portfolio_summary(data, current_prices)
        display_open_positions(data, current_prices)
        display_trade_history(data)
    else:
        st.warning("No portfolio data available")

    # Footer
    st.markdown("---")
    current_time = datetime.now().strftime("%d %b %Y, %I:%M:%S %p")
    st.caption(f"Last updated: {current_time} | Data refreshes automatically")

    # Auto-refresh
    time.sleep(5)
    st.rerun()

if __name__ == "__main__":
    main()
