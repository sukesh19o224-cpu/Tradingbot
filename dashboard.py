"""
📊 LIVE PORTFOLIO DASHBOARD
Real-time view of your portfolios (Swing + Positional + ETF)

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
    initial_sidebar_state="expanded"
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

@st.cache_data(ttl=3)  # Cache for 3 seconds only (ultra-real-time price updates)
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


@st.cache_data(ttl=2)  # Cache for 2 seconds - ensures fresh data while reducing file reads
def load_portfolio_data():
    """Load portfolio data from JSON files"""
    try:
        # Load swing portfolio
        swing_data = {}
        swing_file = 'data/swing_portfolio.json'
        if os.path.exists(swing_file):
            with open(swing_file, 'r') as f:
                swing_data = json.load(f)

        # Load positional portfolio
        positional_data = {}
        positional_file = 'data/positional_portfolio.json'
        if os.path.exists(positional_file):
            with open(positional_file, 'r') as f:
                positional_data = json.load(f)

        # Load swing trades
        swing_trades = []
        swing_trades_file = 'data/swing_trades.json'
        if os.path.exists(swing_trades_file):
            with open(swing_trades_file, 'r') as f:
                swing_trades = json.load(f)

        # Load positional trades
        positional_trades = []
        positional_trades_file = 'data/positional_trades.json'
        if os.path.exists(positional_trades_file):
            with open(positional_trades_file, 'r') as f:
                positional_trades = json.load(f)

        # Load ETF portfolio
        etf_data = {}
        etf_file = 'data/etf_portfolio.json'
        if os.path.exists(etf_file):
            with open(etf_file, 'r') as f:
                etf_data = json.load(f)

        # Load ETF trades
        etf_trades = []
        etf_trades_file = 'data/etf_trades.json'
        if os.path.exists(etf_trades_file):
            with open(etf_trades_file, 'r') as f:
                etf_trades = json.load(f)

        return {
            'swing': swing_data,
            'positional': positional_data,
            'swing_trades': swing_trades,
            'positional_trades': positional_trades,
            'etf': etf_data,
            'etf_trades': etf_trades
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
    etf = data.get('etf', {})

    # Get initial capital from saved data
    swing_initial = swing.get('initial_capital', 0)
    positional_initial = positional.get('initial_capital', 130000)
    etf_initial = etf.get('initial_capital', 130000)
    total_initial = positional_initial  # Use positional as main capital

    # Get current cash
    swing_capital = swing.get('capital', 0)
    positional_capital = positional.get('capital', 0)
    etf_capital = etf.get('capital', 0)
    total_cash = swing_capital + positional_capital + etf_capital

    swing_positions = swing.get('positions', {})
    positional_positions = positional.get('positions', {})
    etf_positions = etf.get('positions', {})

    # Calculate invested amount and current value
    swing_invested = sum(pos.get('cost', 0) for pos in swing_positions.values())
    positional_invested = sum(pos.get('cost', 0) for pos in positional_positions.values())
    etf_invested = sum(pos.get('cost', 0) for pos in etf_positions.values())
    total_invested = swing_invested + positional_invested + etf_invested

    # Calculate current value of positions
    swing_current_value = 0
    for symbol, pos in swing_positions.items():
        current_price = current_prices.get(symbol, 0)
        # CRITICAL FIX: If price fetch failed (0 or negative), use entry price as fallback
        if current_price <= 0:
            current_price = pos.get('entry_price', 0)
        swing_current_value += pos.get('shares', 0) * current_price

    positional_current_value = 0
    for symbol, pos in positional_positions.items():
        current_price = current_prices.get(symbol, 0)
        # CRITICAL FIX: If price fetch failed (0 or negative), use entry price as fallback
        if current_price <= 0:
            current_price = pos.get('entry_price', 0)
        positional_current_value += pos.get('shares', 0) * current_price

    etf_current_value = 0
    for symbol, pos in etf_positions.items():
        current_price = current_prices.get(symbol, 0)
        # CRITICAL FIX: If price fetch failed (0 or negative), use entry price as fallback
        if current_price <= 0:
            current_price = pos.get('entry_price', 0)
        etf_current_value += pos.get('shares', 0) * current_price

    total_current_value = swing_current_value + positional_current_value + etf_current_value

    # Calculate total portfolio value (cash + positions)
    swing_portfolio_value = swing_capital + swing_current_value
    positional_portfolio_value = positional_capital + positional_current_value
    total_portfolio_value = total_cash + total_current_value

    # Calculate realized P&L from closed trades only (exited positions)
    swing_trades = data.get('swing_trades', [])
    positional_trades = data.get('positional_trades', [])
    
    # Get open positions to filter them out
    swing_open_symbols = set(swing.get('positions', {}).keys())
    positional_open_symbols = set(positional.get('positions', {}).keys())
    
    # Only count trades that have exited (have exit_date AND symbol not in open positions)
    # Store these for use throughout the function
    swing_realized_trades = [t for t in swing_trades if t.get('exit_date') and t.get('symbol') not in swing_open_symbols]
    positional_realized_trades = [t for t in positional_trades if t.get('exit_date') and t.get('symbol') not in positional_open_symbols]
    
    realized_pnl = sum(t.get('pnl', 0) for t in swing_realized_trades) + sum(t.get('pnl', 0) for t in positional_realized_trades)

    # Calculate total P&L (realized + unrealized)
    total_pnl = total_portfolio_value - total_initial
    total_pnl_pct = (total_pnl / total_initial * 100) if total_initial > 0 else 0

    # Header
    st.markdown('<div class="header">', unsafe_allow_html=True)
    st.title("💼 DUAL PORTFOLIO DASHBOARD")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ========================================
    # SWING PORTFOLIO SECTION
    # ========================================
    st.header("🔥 SWING PORTFOLIO (30% Capital)")
    
    swing_pnl = swing_portfolio_value - swing_initial
    swing_pnl_pct = (swing_pnl / swing_initial * 100) if swing_initial > 0 else 0
    
    # Get swing trade stats
    # CRITICAL FIX: Group trades by unique position (symbol + entry_date)
    # Partial exits should count as 1 trade, not multiple
    # Use swing_realized_trades already calculated in summary section above
    swing_position_trades = {}
    for trade in swing_realized_trades:
        key = (trade.get('symbol', ''), trade.get('entry_date', ''))
        if key not in swing_position_trades:
            swing_position_trades[key] = []
        swing_position_trades[key].append(trade)
    
    # Count unique positions (not individual trade records)
    swing_total_trades = len(swing_position_trades)
    # Use GROSS P&L for win/loss classification (preserves original win rate)
    swing_wins = sum(1 for trades_list in swing_position_trades.values() 
                     if sum(t.get('gross_pnl', t.get('pnl', 0)) for t in trades_list) > 0.01)  # > ₹0.01 = win (gross)
    swing_losses = sum(1 for trades_list in swing_position_trades.values() 
                       if sum(t.get('gross_pnl', t.get('pnl', 0)) for t in trades_list) < -0.01)  # < -₹0.01 = loss (gross)
    swing_breakeven = swing_total_trades - swing_wins - swing_losses  # ≈ ₹0 = breakeven
    
    # Win rate excluding breakeven: wins / (wins + losses) * 100
    swing_win_loss_total = swing_wins + swing_losses
    swing_win_rate = (swing_wins / swing_win_loss_total * 100) if swing_win_loss_total > 0 else 0
    
    swing_realized_pnl = sum(t.get('pnl', 0) for t in swing_realized_trades)
    swing_unrealized_pnl = swing_current_value - swing_invested
    
    # Calculate total trading charges for swing trades (detailed breakdown)
    swing_total_charges = sum(t.get('trading_charges', 0) for t in swing_realized_trades)
    swing_total_buy_charges = sum(t.get('buy_charges', 0) for t in swing_realized_trades)
    swing_total_sell_charges = sum(t.get('sell_charges', 0) for t in swing_realized_trades)
    swing_gross_pnl = swing_realized_pnl + swing_total_charges  # Gross P&L before charges
    swing_charges_trades_count = len([t for t in swing_realized_trades if t.get('trading_charges', 0) > 0])
    swing_avg_charges_per_trade = (swing_total_charges / swing_charges_trades_count) if swing_charges_trades_count > 0 else 0

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("💰 Initial", f"₹{swing_initial:,.0f}")
    
    with col2:
        st.metric("📊 Current Value", f"₹{swing_portfolio_value:,.0f}",
                 delta=f"₹{swing_pnl:+,.0f}")
    
    with col3:
        pnl_color = "positive" if swing_pnl >= 0 else "negative"
        st.markdown(f"**Total P&L**")
        st.markdown(f"<span class='{pnl_color} big-metric'>{swing_pnl_pct:+.2f}%</span>",
                   unsafe_allow_html=True)
    
    with col4:
        st.metric("💵 Cash", f"₹{swing_capital:,.0f}")
        st.metric("📈 Invested", f"₹{swing_invested:,.0f}")
    
    with col5:
        st.metric("📊 Positions", len(swing_positions))
        realized_color = "positive" if swing_realized_pnl >= 0 else "negative"
        st.markdown(f"**Realized P&L**")
        st.markdown(f"<span class='{realized_color}'>₹{swing_realized_pnl:+,.0f}</span>",
                   unsafe_allow_html=True)
        unrealized_color = "positive" if swing_unrealized_pnl >= 0 else "negative"
        st.markdown(f"**Unrealized P&L**")
        st.markdown(f"<span class='{unrealized_color}'>₹{swing_unrealized_pnl:+,.0f}</span>",
                   unsafe_allow_html=True)
    
    with col6:
        st.metric("📝 Total Trades", swing_total_trades)
        st.metric("✅ Win Rate", f"{swing_win_rate:.1f}%")
    
    # Trade Statistics Section
    st.markdown("### 📊 Trade Statistics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("✅ Wins", swing_wins)
    with col2:
        st.metric("❌ Losses", swing_losses)
    with col3:
        st.metric("⚖️ Win:Loss Ratio", f"{swing_wins}:{swing_losses}" if swing_losses > 0 else f"{swing_wins}:0")
    with col4:
        st.metric("➖ Breakeven", swing_breakeven)
    
    # Trading Charges Section (swing trades only) - ZERODHA STYLE
    st.markdown("### 💰 Zerodha Trading Charges (Swing Trading)")
    with st.container():
        # Main charges card
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("**💰 Total Charges Spent**")
            charges_color = "negative"
            st.markdown(f"<span class='{charges_color} big-metric'>₹{swing_total_charges:,.2f}</span>",
                       unsafe_allow_html=True)
            st.caption(f"Across {swing_charges_trades_count} trades")
        
        with col2:
            st.markdown("**📊 Charges Breakdown**")
            st.write(f"Buy Charges: ₹{swing_total_buy_charges:,.2f}")
            st.write(f"Sell Charges: ₹{swing_total_sell_charges:,.2f}")
            if swing_charges_trades_count > 0:
                st.caption(f"Avg per trade: ₹{swing_avg_charges_per_trade:,.2f}")
        
        with col3:
            st.markdown("**📈 Gross P&L**")
            gross_color = "positive" if swing_gross_pnl >= 0 else "negative"
            st.markdown(f"<span class='{gross_color}'>₹{swing_gross_pnl:+,.2f}</span>",
                       unsafe_allow_html=True)
            st.caption("Before charges")
        
        with col4:
            st.markdown("**✅ Net P&L**")
            net_color = "positive" if swing_realized_pnl >= 0 else "negative"
            st.markdown(f"<span class='{net_color}'>₹{swing_realized_pnl:+,.2f}</span>",
                       unsafe_allow_html=True)
            st.caption("After all charges")
        
        # Charges impact info
        st.info(f"💰 **Charges Include:** STT (0.0125% on sell), Exchange Transaction Charges, GST (18%), Stamp Duty, SEBI Turnover Fees, NSE IPFT | **Impact:** Charges reduce your net P&L by ₹{swing_total_charges:,.2f} ({((swing_total_charges / swing_gross_pnl) * 100) if swing_gross_pnl != 0 else 0:.2f}% of gross P&L)" if swing_gross_pnl != 0 else f"💰 **Charges Include:** STT (0.0125% on sell), Exchange Transaction Charges, GST (18%), Stamp Duty, SEBI Turnover Fees, NSE IPFT")

    st.markdown("---")

    # ========================================
    # POSITIONAL PORTFOLIO SECTION
    # ========================================
    st.header("📈 POSITIONAL PORTFOLIO (70% Capital)")
    
    positional_pnl = positional_portfolio_value - positional_initial
    positional_pnl_pct = (positional_pnl / positional_initial * 100) if positional_initial > 0 else 0
    
    # Get positional trade stats
    # CRITICAL FIX: Group trades by unique position (symbol + entry_date)
    # Partial exits should count as 1 trade, not multiple
    # Use positional_realized_trades already calculated in summary section above
    positional_position_trades = {}
    for trade in positional_realized_trades:
        key = (trade.get('symbol', ''), trade.get('entry_date', ''))
        if key not in positional_position_trades:
            positional_position_trades[key] = []
        positional_position_trades[key].append(trade)
    
    # Count unique positions (not individual trade records)
    positional_total_trades = len(positional_position_trades)
    positional_wins = sum(1 for trades_list in positional_position_trades.values() 
                          if sum(t.get('pnl', 0) for t in trades_list) > 0.01)  # > ₹0.01 = win
    positional_losses = sum(1 for trades_list in positional_position_trades.values() 
                            if sum(t.get('pnl', 0) for t in trades_list) < -0.01)  # < -₹0.01 = loss
    positional_breakeven = positional_total_trades - positional_wins - positional_losses  # ≈ ₹0 = breakeven
    
    # Win rate excluding breakeven: wins / (wins + losses) * 100
    positional_win_loss_total = positional_wins + positional_losses
    positional_win_rate = (positional_wins / positional_win_loss_total * 100) if positional_win_loss_total > 0 else 0
    
    positional_realized_pnl = sum(t.get('pnl', 0) for t in positional_realized_trades)
    positional_unrealized_pnl = positional_current_value - positional_invested

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("💰 Initial", f"₹{positional_initial:,.0f}")
    
    with col2:
        st.metric("📊 Current Value", f"₹{positional_portfolio_value:,.0f}",
                 delta=f"₹{positional_pnl:+,.0f}")
    
    with col3:
        pnl_color = "positive" if positional_pnl >= 0 else "negative"
        st.markdown(f"**Total P&L**")
        st.markdown(f"<span class='{pnl_color} big-metric'>{positional_pnl_pct:+.2f}%</span>",
                   unsafe_allow_html=True)
    
    with col4:
        st.metric("💵 Cash", f"₹{positional_capital:,.0f}")
        st.metric("📈 Invested", f"₹{positional_invested:,.0f}")
    
    with col5:
        st.metric("📊 Positions", len(positional_positions))
        realized_color = "positive" if positional_realized_pnl >= 0 else "negative"
        st.markdown(f"**Realized P&L**")
        st.markdown(f"<span class='{realized_color}'>₹{positional_realized_pnl:+,.0f}</span>",
                   unsafe_allow_html=True)
        unrealized_color = "positive" if positional_unrealized_pnl >= 0 else "negative"
        st.markdown(f"**Unrealized P&L**")
        st.markdown(f"<span class='{unrealized_color}'>₹{positional_unrealized_pnl:+,.0f}</span>",
                   unsafe_allow_html=True)
    
    with col6:
        st.metric("📝 Total Trades", positional_total_trades)
        st.metric("✅ Win Rate", f"{positional_win_rate:.1f}%")
    
    # Trade Statistics Section
    st.markdown("### 📊 Trade Statistics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("✅ Wins", positional_wins)
    with col2:
        st.metric("❌ Losses", positional_losses)
    with col3:
        st.metric("⚖️ Win:Loss Ratio", f"{positional_wins}:{positional_losses}" if positional_losses > 0 else f"{positional_wins}:0")
    with col4:
        st.metric("➖ Breakeven", positional_breakeven)

    st.markdown("---")

    # ========================================
    # ETF PORTFOLIO SECTION
    # ========================================
    st.header("💎 ETF PORTFOLIO")

    etf_portfolio_value = etf_capital + etf_current_value
    etf_pnl = etf_portfolio_value - etf_initial
    etf_pnl_pct = (etf_pnl / etf_initial * 100) if etf_initial > 0 else 0

    # Get ETF trade stats
    etf_trades_list = data.get('etf_trades', [])
    etf_total_trades = len(etf_trades_list)
    etf_wins = sum(1 for t in etf_trades_list if t.get('pnl', 0) > 0.01)
    etf_losses = sum(1 for t in etf_trades_list if t.get('pnl', 0) < -0.01)
    etf_win_loss_total = etf_wins + etf_losses
    etf_win_rate = (etf_wins / etf_win_loss_total * 100) if etf_win_loss_total > 0 else 0

    etf_realized_pnl = sum(t.get('pnl', 0) for t in etf_trades_list)
    etf_unrealized_pnl = etf_current_value - etf_invested

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric("💰 Initial", f"₹{etf_initial:,.0f}")

    with col2:
        st.metric("📊 Current Value", f"₹{etf_portfolio_value:,.0f}",
                 delta=f"₹{etf_pnl:+,.0f}")

    with col3:
        pnl_color = "positive" if etf_pnl >= 0 else "negative"
        st.markdown(f"**Total P&L**")
        st.markdown(f"<span class='{pnl_color} big-metric'>{etf_pnl_pct:+.2f}%</span>",
                   unsafe_allow_html=True)

    with col4:
        st.metric("💵 Cash", f"₹{etf_capital:,.0f}")
        st.metric("📈 Invested", f"₹{etf_invested:,.0f}")

    with col5:
        st.metric("📊 Holdings", len(etf_positions))
        realized_color = "positive" if etf_realized_pnl >= 0 else "negative"
        st.markdown(f"**Realized P&L**")
        st.markdown(f"<span class='{realized_color}'>₹{etf_realized_pnl:+,.0f}</span>",
                   unsafe_allow_html=True)
        unrealized_color = "positive" if etf_unrealized_pnl >= 0 else "negative"
        st.markdown(f"**Unrealized P&L**")
        st.markdown(f"<span class='{unrealized_color}'>₹{etf_unrealized_pnl:+,.0f}</span>",
                   unsafe_allow_html=True)

    with col6:
        st.metric("📝 Total Trades", etf_total_trades)
        st.metric("✅ Win Rate", f"{etf_win_rate:.1f}%")

    # Trade Statistics Section
    st.markdown("### 📊 Trade Statistics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("✅ Wins", etf_wins)
    with col2:
        st.metric("❌ Losses", etf_losses)
    with col3:
        st.metric("⚖️ Win:Loss Ratio", f"{etf_wins}:{etf_losses}" if etf_losses > 0 else f"{etf_wins}:0")

    st.markdown("---")

    # Combined Quick Summary
    st.subheader("📊 COMBINED SUMMARY")
    total_positions = len(swing_positions) + len(positional_positions) + len(etf_positions)
    total_pnl = total_portfolio_value - total_initial
    total_pnl_pct = (total_pnl / total_initial * 100) if total_initial > 0 else 0
    total_realized_pnl = realized_pnl + etf_realized_pnl
    total_unrealized_pnl = swing_unrealized_pnl + positional_unrealized_pnl + etf_unrealized_pnl
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("💰 Total Capital", f"₹{total_initial:,.0f}")
    with col2:
        st.metric("📊 Total Value", f"₹{total_portfolio_value:,.0f}")
    with col3:
        pnl_color = "positive" if total_pnl >= 0 else "negative"
        st.markdown(f"**Combined P&L**")
        st.markdown(f"<span class='{pnl_color}'>₹{total_pnl:+,.0f} ({total_pnl_pct:+.2f}%)</span>",
                   unsafe_allow_html=True)
    with col4:
        realized_color = "positive" if total_realized_pnl >= 0 else "negative"
        st.markdown(f"**Realized P&L**")
        st.markdown(f"<span class='{realized_color}'>₹{total_realized_pnl:+,.0f}</span>",
                   unsafe_allow_html=True)
        unrealized_color = "positive" if total_unrealized_pnl >= 0 else "negative"
        st.markdown(f"**Unrealized P&L**")
        st.markdown(f"<span class='{unrealized_color}'>₹{total_unrealized_pnl:+,.0f}</span>",
                   unsafe_allow_html=True)
    with col5:
        st.metric("📊 Total Positions", total_positions)

def display_open_positions(data, current_prices):
    """Display open positions with live P&L and detailed metrics"""
    if not data:
        return

    swing = data.get('swing', {})
    positional = data.get('positional', {})
    etf = data.get('etf', {})

    swing_positions = swing.get('positions', {})
    positional_positions = positional.get('positions', {})
    etf_positions = etf.get('positions', {})

    st.markdown("---")
    st.subheader("📊 OPEN POSITIONS")

    if not swing_positions and not positional_positions and not etf_positions:
        st.info("No open positions. System is scanning for opportunities...")
        return

    # Swing positions
    if swing_positions:
        st.markdown("### 🔥 Swing Positions")

        for symbol, pos in swing_positions.items():
            # Get current price with fallback if fetch failed
            current_price = current_prices.get(symbol, 0)
            entry_price = pos.get('entry_price', 0)
            # CRITICAL FIX: If price fetch failed (0 or negative), use entry price as fallback
            if current_price <= 0:
                current_price = entry_price
            shares = pos.get('shares', 0)
            initial_shares = pos.get('initial_shares', shares)

            # Calculate P&L - Use actual cost from portfolio (more accurate)
            invested = pos.get('cost', entry_price * shares)  # Use cost field if available
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

            # HYBRID TRAILING STOP (Breakeven + ATR-based) - Same logic as paper_trader.py
            initial_stop_loss = pos.get('initial_stop_loss', pos.get('stop_loss', 0))
            current_stop_loss = pos.get('stop_loss', initial_stop_loss)
            breakeven_active = pos.get('breakeven_active', False)
            trailing_active = pos.get('trailing_active', False)
            
            # Calculate what trailing stop should be (for display)
            # CRITICAL FIX: Use strategy-specific settings (same as paper_trader.py)
            from config.settings import TRAILING_STOP_ATR_MULTIPLIER, USE_ATR_STOP_LOSS
            
            # Strategy-specific thresholds (hardcoded like paper_trader.py)
            if strategy == 'swing':
                breakeven_threshold = 0.005  # +0.5% (swing)
                trailing_threshold = 0.007  # +0.7% (swing)
                swing_atr_multiplier = 0.5  # 0.5x ATR for swing
                swing_trailing_distance = 0.005  # 0.5% fallback for swing
            else:  # positional
                breakeven_threshold = 0.02  # +2% (positional)
                trailing_threshold = 0.03  # +3% (positional)
                positional_atr_multiplier = TRAILING_STOP_ATR_MULTIPLIER  # 0.8x ATR for positional
                positional_trailing_distance = 0.015  # 1.5% fallback for positional
            
            if pnl_pct >= breakeven_threshold * 100:
                breakeven_stop = entry_price
                if breakeven_stop > current_stop_loss:
                    current_stop_loss = breakeven_stop
                    breakeven_active = True
            
            if pnl_pct >= trailing_threshold * 100:
                atr = pos.get('atr', 0)
                if atr > 0 and USE_ATR_STOP_LOSS:
                    # ATR-based trailing: Strategy-specific multiplier
                    if strategy == 'swing':
                        trailing_distance = atr * swing_atr_multiplier
                    else:  # positional
                        trailing_distance = atr * positional_atr_multiplier
                    atr_trailing_stop = current_price - trailing_distance
                    trailing_stop = max(entry_price, atr_trailing_stop)
                else:
                    # Fallback: Strategy-specific fixed trailing
                    if strategy == 'swing':
                        trailing_stop = max(entry_price, current_price * (1 - swing_trailing_distance))
                    else:  # positional
                        trailing_stop = max(entry_price, current_price * (1 - positional_trailing_distance))
                
                if trailing_stop > current_stop_loss:
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
                    st.write(f"Invested: ₹{invested:,.0f}")
                    st.write(f"Current Value: ₹{current_value:,.0f}")
                    st.markdown(f"**P&L:** <span class='{pnl_color}'>₹{pnl:+,.0f} ({pnl_pct:+.2f}%)</span>",
                               unsafe_allow_html=True)

                with col4:
                    st.write("**Holding Period**")
                    st.write(f"Hold Days: {hold_days} / {max_hold_days}")
                    st.write(f"Target 1: ₹{pos.get('target1', 0):.2f}")
                    st.write(f"Target 2: ₹{pos.get('target2', 0):.2f}")
                    st.write(f"Target 3: ₹{pos.get('target3', 0):.2f}")

                    # Show stop loss status (breakeven, trailing, or normal)
                    if trailing_active:
                        atr = pos.get('atr', 0)
                        if atr > 0:
                            st.write(f"~~Initial Stop: ₹{initial_stop_loss:.2f}~~")
                            st.markdown(f"**🔒 ATR Trailing Stop: ₹{current_stop_loss:.2f}** (Active! 1.5x ATR)")
                        else:
                            st.write(f"~~Initial Stop: ₹{initial_stop_loss:.2f}~~")
                            st.markdown(f"**🔒 Trailing Stop: ₹{current_stop_loss:.2f}** (Active! 2% fixed)")
                    elif breakeven_active or abs(current_stop_loss - entry_price) < 0.01:
                        st.write(f"~~Initial Stop: ₹{initial_stop_loss:.2f}~~")
                        # Calculate stop loss percentage for display
                        stop_loss_pct = ((entry_price - current_stop_loss) / entry_price * 100) if entry_price > 0 else 0
                        if abs(stop_loss_pct) < 0.01:  # At breakeven
                            st.markdown(f"**✅ Breakeven Stop: ₹{current_stop_loss:.2f}** (Risk-Free! 0.00%)")
                        else:
                            st.markdown(f"**✅ Breakeven Stop: ₹{current_stop_loss:.2f}** (Risk-Free! {stop_loss_pct:.2f}%)")
                    else:
                        # Calculate stop loss percentage
                        stop_loss_pct = ((entry_price - current_stop_loss) / entry_price * 100) if entry_price > 0 else 0
                        st.write(f"Stop Loss: ₹{current_stop_loss:.2f} ({stop_loss_pct:.2f}%)")

    # Positional positions
    if positional_positions:
        st.markdown("### 📈 Positional Positions")

        for symbol, pos in positional_positions.items():
            # Get current price with fallback if fetch failed
            current_price = current_prices.get(symbol, 0)
            entry_price = pos.get('entry_price', 0)
            # CRITICAL FIX: If price fetch failed (0 or negative), use entry price as fallback
            if current_price <= 0:
                current_price = entry_price
            shares = pos.get('shares', 0)
            initial_shares = pos.get('initial_shares', shares)

            # Calculate P&L - Use actual cost from portfolio (more accurate)
            invested = pos.get('cost', entry_price * shares)  # Use cost field if available
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

            # OVERRIDE: Use correct max days based on strategy (positional = 15 days)
            # This fixes old positions that have incorrect max_holding_days
            strategy = pos.get('strategy', 'positional')
            if strategy == 'positional':
                max_hold_days = 15  # Positional trades should be 15 trading days (matches settings.py)
            else:
                max_hold_days = pos.get('max_holding_days', 45)

            # HYBRID TRAILING STOP (Breakeven + ATR-based) - Same logic as paper_trader.py
            initial_stop_loss = pos.get('initial_stop_loss', pos.get('stop_loss', 0))
            current_stop_loss = pos.get('stop_loss', initial_stop_loss)
            breakeven_active = pos.get('breakeven_active', False)
            trailing_active = pos.get('trailing_active', False)
            
            # Calculate what trailing stop should be (for display)
            # CRITICAL FIX: Use strategy-specific settings (same as paper_trader.py)
            from config.settings import TRAILING_STOP_ATR_MULTIPLIER, USE_ATR_STOP_LOSS
            
            # Strategy-specific thresholds (hardcoded like paper_trader.py)
            if strategy == 'swing':
                breakeven_threshold = 0.005  # +0.5% (swing)
                trailing_threshold = 0.007  # +0.7% (swing)
                swing_atr_multiplier = 0.5  # 0.5x ATR for swing
                swing_trailing_distance = 0.005  # 0.5% fallback for swing
            else:  # positional
                breakeven_threshold = 0.02  # +2% (positional)
                trailing_threshold = 0.03  # +3% (positional)
                positional_atr_multiplier = TRAILING_STOP_ATR_MULTIPLIER  # 0.8x ATR for positional
                positional_trailing_distance = 0.015  # 1.5% fallback for positional
            
            if pnl_pct >= breakeven_threshold * 100:
                breakeven_stop = entry_price
                if breakeven_stop > current_stop_loss:
                    current_stop_loss = breakeven_stop
                    breakeven_active = True
            
            if pnl_pct >= trailing_threshold * 100:
                atr = pos.get('atr', 0)
                if atr > 0 and USE_ATR_STOP_LOSS:
                    # ATR-based trailing: Strategy-specific multiplier
                    if strategy == 'swing':
                        trailing_distance = atr * swing_atr_multiplier
                    else:  # positional
                        trailing_distance = atr * positional_atr_multiplier
                    atr_trailing_stop = current_price - trailing_distance
                    trailing_stop = max(entry_price, atr_trailing_stop)
                else:
                    # Fallback: Strategy-specific fixed trailing
                    if strategy == 'swing':
                        trailing_stop = max(entry_price, current_price * (1 - swing_trailing_distance))
                    else:  # positional
                        trailing_stop = max(entry_price, current_price * (1 - positional_trailing_distance))
                
                if trailing_stop > current_stop_loss:
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
                    st.write(f"Invested: ₹{invested:,.0f}")
                    st.write(f"Current Value: ₹{current_value:,.0f}")
                    st.markdown(f"**P&L:** <span class='{pnl_color}'>₹{pnl:+,.0f} ({pnl_pct:+.2f}%)</span>",
                               unsafe_allow_html=True)

                with col4:
                    st.write("**Holding Period**")
                    st.write(f"Hold Days: {hold_days} / {max_hold_days}")
                    st.write(f"Target 1: ₹{pos.get('target1', 0):.2f}")
                    st.write(f"Target 2: ₹{pos.get('target2', 0):.2f}")
                    st.write(f"Target 3: ₹{pos.get('target3', 0):.2f}")

                    # Show stop loss status (breakeven, trailing, or normal)
                    if trailing_active:
                        atr = pos.get('atr', 0)
                        if atr > 0:
                            st.write(f"~~Initial Stop: ₹{initial_stop_loss:.2f}~~")
                            st.markdown(f"**🔒 ATR Trailing Stop: ₹{current_stop_loss:.2f}** (Active! 1.5x ATR)")
                        else:
                            st.write(f"~~Initial Stop: ₹{initial_stop_loss:.2f}~~")
                            st.markdown(f"**🔒 Trailing Stop: ₹{current_stop_loss:.2f}** (Active! 2% fixed)")
                    elif breakeven_active or abs(current_stop_loss - entry_price) < 0.01:
                        st.write(f"~~Initial Stop: ₹{initial_stop_loss:.2f}~~")
                        # Calculate stop loss percentage for display
                        stop_loss_pct = ((entry_price - current_stop_loss) / entry_price * 100) if entry_price > 0 else 0
                        if abs(stop_loss_pct) < 0.01:  # At breakeven
                            st.markdown(f"**✅ Breakeven Stop: ₹{current_stop_loss:.2f}** (Risk-Free! 0.00%)")
                        else:
                            st.markdown(f"**✅ Breakeven Stop: ₹{current_stop_loss:.2f}** (Risk-Free! {stop_loss_pct:.2f}%)")
                    else:
                        # Calculate stop loss percentage
                        stop_loss_pct = ((entry_price - current_stop_loss) / entry_price * 100) if entry_price > 0 else 0
                        st.write(f"Stop Loss: ₹{current_stop_loss:.2f} ({stop_loss_pct:.2f}%)")

    # ETF positions
    if etf_positions:
        st.markdown("### 💎 ETF Holdings")

        for symbol, pos in etf_positions.items():
            # Get current price with fallback if fetch failed
            current_price = current_prices.get(symbol, 0)
            entry_price = pos.get('entry_price', 0)
            if current_price <= 0:
                current_price = entry_price
            shares = pos.get('shares', 0)

            # Calculate P&L
            invested = pos.get('cost', entry_price * shares)
            current_value = current_price * shares
            pnl = current_value - invested
            pnl_pct = (pnl / invested * 100) if invested > 0 else 0
            pnl_color = "positive" if pnl >= 0 else "negative"

            # Calculate hold days
            entry_date = pos.get('entry_date', '')
            try:
                entry_dt = datetime.fromisoformat(entry_date)
                hold_days = (datetime.now() - entry_dt).days
            except:
                hold_days = 0

            # Display ETF position
            with st.expander(f"**{symbol}** | 💎 ETF | P&L: {pnl:+,.0f} ({pnl_pct:+.2f}%) | Current: ₹{current_price:.2f}"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write("**Entry Info**")
                    st.write(f"Type: 💎 ETF Investment")
                    st.write(f"Entry Price: ₹{entry_price:.2f}")
                    st.write(f"Entry Date: {entry_date[:10] if entry_date else 'N/A'}")
                    st.write(f"Hold Days: {hold_days} days")

                with col2:
                    st.write("**Units**")
                    st.write(f"Units: {shares}")
                    st.write(f"Invested: ₹{invested:,.0f}")
                    st.write(f"Current Value: ₹{current_value:,.0f}")

                with col3:
                    st.write("**Performance**")
                    st.markdown(f"<span class='{pnl_color}'>P&L: ₹{pnl:+,.0f}</span>", unsafe_allow_html=True)
                    st.markdown(f"<span class='{pnl_color}'>Return: {pnl_pct:+.2f}%</span>", unsafe_allow_html=True)
                    peak_price = pos.get('peak_price', entry_price)
                    lowest_price = pos.get('lowest_price', entry_price)
                    st.write(f"Peak: ₹{peak_price:.2f}")
                    st.write(f"Low: ₹{lowest_price:.2f}")

def display_holding_pnl(data, current_prices):
    """Display Holding P&L - Unrealized gains/losses for open positions"""
    if not data:
        return

    swing = data.get('swing', {})
    positional = data.get('positional', {})
    etf = data.get('etf', {})

    swing_positions = swing.get('positions', {})
    positional_positions = positional.get('positions', {})
    etf_positions = etf.get('positions', {})

    st.markdown("---")
    st.subheader("💰 HOLDING P&L (Unrealized)")

    if not swing_positions and not positional_positions and not etf_positions:
        st.info("No open positions to show P&L.")
        return

    # Prepare data for table
    holding_data = []

    # Add swing positions
    for symbol, pos in swing_positions.items():
        current_price = current_prices.get(symbol, 0)
        entry_price = pos.get('entry_price', 0)
        # CRITICAL FIX: If price fetch failed (0 or negative), use entry price as fallback
        if current_price <= 0:
            current_price = entry_price
        shares = pos.get('shares', 0)
        invested = pos.get('cost', entry_price * shares)
        current_value = current_price * shares
        pnl = current_value - invested
        pnl_pct = (pnl / invested * 100) if invested > 0 else 0

        holding_data.append({
            'Symbol': symbol.replace('.NS', ''),
            'Type': '🔥 Swing',
            'Shares': shares,
            'Entry': f"₹{entry_price:.2f}",
            'Current': f"₹{current_price:.2f}",
            'Invested': f"₹{invested:,.0f}",
            'Current Value': f"₹{current_value:,.0f}",
            'P&L': f"₹{pnl:+,.0f}",
            'P&L %': f"{pnl_pct:+.2f}%",
            '_pnl_raw': pnl,  # For sorting
            '_pnl_pct_raw': pnl_pct
        })

    # Add positional positions
    for symbol, pos in positional_positions.items():
        current_price = current_prices.get(symbol, 0)
        entry_price = pos.get('entry_price', 0)
        # CRITICAL FIX: If price fetch failed (0 or negative), use entry price as fallback
        if current_price <= 0:
            current_price = entry_price
        shares = pos.get('shares', 0)
        invested = pos.get('cost', entry_price * shares)
        current_value = current_price * shares
        pnl = current_value - invested
        pnl_pct = (pnl / invested * 100) if invested > 0 else 0

        holding_data.append({
            'Symbol': symbol.replace('.NS', ''),
            'Type': '📈 Positional',
            'Shares': shares,
            'Entry': f"₹{entry_price:.2f}",
            'Current': f"₹{current_price:.2f}",
            'Invested': f"₹{invested:,.0f}",
            'Current Value': f"₹{current_value:,.0f}",
            'P&L': f"₹{pnl:+,.0f}",
            'P&L %': f"{pnl_pct:+.2f}%",
            '_pnl_raw': pnl,
            '_pnl_pct_raw': pnl_pct
        })

    # Add ETF positions
    for symbol, pos in etf_positions.items():
        current_price = current_prices.get(symbol, 0)
        entry_price = pos.get('entry_price', 0)
        if current_price <= 0:
            current_price = entry_price
        shares = pos.get('shares', 0)
        invested = pos.get('cost', entry_price * shares)
        current_value = current_price * shares
        pnl = current_value - invested
        pnl_pct = (pnl / invested * 100) if invested > 0 else 0

        holding_data.append({
            'Symbol': symbol,
            'Type': '💎 ETF',
            'Shares': shares,
            'Entry': f"₹{entry_price:.2f}",
            'Current': f"₹{current_price:.2f}",
            'Invested': f"₹{invested:,.0f}",
            'Current Value': f"₹{current_value:,.0f}",
            'P&L': f"₹{pnl:+,.0f}",
            'P&L %': f"{pnl_pct:+.2f}%",
            '_pnl_raw': pnl,
            '_pnl_pct_raw': pnl_pct
        })

    # Sort by P&L percentage (best to worst)
    holding_data.sort(key=lambda x: x['_pnl_pct_raw'], reverse=True)

    # Calculate totals
    total_invested = sum(float(item['Invested'].replace('₹', '').replace(',', '')) for item in holding_data)
    total_current = sum(float(item['Current Value'].replace('₹', '').replace(',', '')) for item in holding_data)
    total_pnl = sum(item['_pnl_raw'] for item in holding_data)
    total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0

    # Display summary cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💼 Total Invested", f"₹{total_invested:,.0f}")
    with col2:
        st.metric("📊 Current Value", f"₹{total_current:,.0f}")
    with col3:
        pnl_color = "positive" if total_pnl >= 0 else "negative"
        st.markdown(f"**💰 Total P&L**")
        st.markdown(f"<span class='{pnl_color} big-metric'>₹{total_pnl:+,.0f}</span>", unsafe_allow_html=True)
    with col4:
        pnl_color = "positive" if total_pnl_pct >= 0 else "negative"
        st.markdown(f"**📈 Total P&L %**")
        st.markdown(f"<span class='{pnl_color} big-metric'>{total_pnl_pct:+.2f}%</span>", unsafe_allow_html=True)

    st.markdown("### 📋 Position-wise P&L")

    # Display table with color-coded P&L
    for item in holding_data:
        cols = st.columns([2, 2, 1, 2, 2, 2, 2, 2, 2])

        with cols[0]:
            st.write(f"**{item['Symbol']}**")
        with cols[1]:
            st.write(item['Type'])
        with cols[2]:
            st.write(item['Shares'])
        with cols[3]:
            st.write(item['Entry'])
        with cols[4]:
            st.write(item['Current'])
        with cols[5]:
            st.write(item['Invested'])
        with cols[6]:
            st.write(item['Current Value'])
        with cols[7]:
            pnl_color = "positive" if item['_pnl_raw'] >= 0 else "negative"
            st.markdown(f"<span class='{pnl_color}'>{item['P&L']}</span>", unsafe_allow_html=True)
        with cols[8]:
            pnl_color = "positive" if item['_pnl_pct_raw'] >= 0 else "negative"
            st.markdown(f"<span class='{pnl_color}'>{item['P&L %']}</span>", unsafe_allow_html=True)

def display_trade_history(data):
    """Display recent trade history"""
    if not data:
        return

    swing_trades = data.get('swing_trades', [])
    positional_trades = data.get('positional_trades', [])
    
    # Only show realized (exited) trades in history
    swing_open_symbols = set(data.get('swing', {}).get('positions', {}).keys())
    positional_open_symbols = set(data.get('positional', {}).get('positions', {}).keys())
    
    swing_realized = [t for t in swing_trades if t.get('exit_date') and t.get('symbol') not in swing_open_symbols]
    positional_realized = [t for t in positional_trades if t.get('exit_date') and t.get('symbol') not in positional_open_symbols]

    st.markdown("---")
    st.subheader("📜 RECENT TRADES (Closed Positions Only)")

    if not swing_realized and not positional_realized:
        st.info("No closed trades yet. Waiting for exits...")
        return

    # Show total charges info if swing trades have charges
    swing_charges_total = sum(t.get('trading_charges', 0) for t in swing_realized)
    if swing_charges_total > 0:
        st.info(f"💰 **Swing Trading Charges:** Total ₹{swing_charges_total:,.2f} deducted from {len([t for t in swing_realized if t.get('trading_charges', 0) > 0])} trades (Net P&L shown)")

    # Combine and sort by date (only exited trades)
    all_trades = []
    for trade in swing_realized:
        trade['type'] = 'Swing'
        all_trades.append(trade)

    for trade in positional_realized:
        trade['type'] = 'Positional'
        all_trades.append(trade)

    # Sort by exit date (most recent first)
    all_trades.sort(key=lambda x: x.get('exit_date', ''), reverse=True)

    # Show last 10 trades
    for trade in all_trades[:10]:
        # Use 7 columns if swing trade has charges, otherwise 6
        has_charges = trade.get('trading_charges', 0) > 0
        num_cols = 7 if has_charges else 6
        cols = st.columns(num_cols)

        with cols[0]:
            badge = "🔥" if trade['type'] == 'Swing' else "📈"
            st.write(f"{badge} **{trade.get('symbol', 'N/A').replace('.NS', '')}**")

        with cols[1]:
            st.write(f"Entry: ₹{trade.get('entry_price', 0):.2f}")

        with cols[2]:
            st.write(f"Exit: ₹{trade.get('exit_price', 0):.2f}")

        with cols[3]:
            pnl = trade.get('pnl', 0)
            pnl_class = "positive" if pnl > 0 else "negative"
            # Show "Net P&L" label for swing trades with charges
            label = "Net P&L" if has_charges else "P&L"
            st.markdown(f"**{label}:**")
            st.markdown(f"<span class='{pnl_class}'>₹{pnl:+,.2f}</span>", unsafe_allow_html=True)

        with cols[4]:
            pnl_pct = trade.get('pnl_percent', 0)
            pnl_class = "positive" if pnl_pct > 0 else "negative"
            st.markdown(f"**Gross %:**")
            st.markdown(f"<span class='{pnl_class}'>{pnl_pct:+.2f}%</span>", unsafe_allow_html=True)

        if has_charges:
            with cols[5]:
                charges = trade.get('trading_charges', 0)
                st.markdown(f"**Charges:**")
                st.markdown(f"<span class='negative'>₹{charges:.2f}</span>", unsafe_allow_html=True)
                st.caption(f"B: ₹{trade.get('buy_charges', 0):.2f}, S: ₹{trade.get('sell_charges', 0):.2f}")
            
            with cols[6]:
                exit_date = trade.get('exit_date', 'N/A')
                if isinstance(exit_date, str) and 'T' in exit_date:
                    exit_date = exit_date.split('T')[0]
                st.write(f"**Exit Date:**")
                st.write(exit_date)
        else:
            with cols[5]:
                exit_date = trade.get('exit_date', 'N/A')
                if isinstance(exit_date, str) and 'T' in exit_date:
                    exit_date = exit_date.split('T')[0]
                st.write(f"**Exit Date:**")
                st.write(exit_date)

def main():
    """Main dashboard function"""
    # Header with refresh controls
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### 🔄 Auto-refresh: Every 3 seconds (Ultra Real-Time)")
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
        display_holding_pnl(data, current_prices)
        display_trade_history(data)
    else:
        st.warning("No portfolio data available")

    # Footer
    st.markdown("---")
    current_time = datetime.now().strftime("%d %b %Y, %I:%M:%S %p")
    st.caption(f"Last updated: {current_time} | Data refreshes automatically")

    # Auto-refresh (faster for real-time prices)
    time.sleep(3)
    st.rerun()

if __name__ == "__main__":
    main()
