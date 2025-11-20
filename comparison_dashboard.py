"""
🎯 LIVE STRATEGY COMPARISON DASHBOARD
Compare 3 trading strategies in real-time over 2 weeks

Strategy A: EXCELLENT (score ≥ 8.5)
Strategy B: MODERATE (score ≥ 8.0)
Strategy C: ALL SIGNALS (score ≥ 7.0)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import os
import json

from src.comparison.portfolio_comparison import PortfolioComparison
from src.data.data_fetcher import DataFetcher


# Page config
st.set_page_config(
    page_title="Strategy Comparison Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .big-metric {
        font-size: 2.5rem;
        font-weight: bold;
    }
    .rank-1 { color: #00ff00; }
    .rank-2 { color: #ffaa00; }
    .rank-3 { color: #ff4444; }
    .excellent-badge { background-color: #00ff00; color: black; padding: 5px 10px; border-radius: 5px; }
    .moderate-badge { background-color: #ffaa00; color: black; padding: 5px 10px; border-radius: 5px; }
    .all-badge { background-color: #4488ff; color: white; padding: 5px 10px; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_portfolio_comparison():
    """Load portfolio comparison system"""
    return PortfolioComparison()


@st.cache_resource
def load_data_fetcher():
    """Load data fetcher"""
    return DataFetcher()


def get_current_prices(portfolio_comp):
    """Get current prices for all open positions"""
    data_fetcher = load_data_fetcher()
    all_symbols = set()

    for portfolio in portfolio_comp.portfolios.values():
        all_symbols.update(portfolio['positions'].keys())

    current_prices = {}
    for symbol in all_symbols:
        try:
            df = data_fetcher.get_stock_data(symbol)
            if not df.empty:
                current_prices[symbol] = df['Close'].iloc[-1]
        except:
            pass

    return current_prices


def render_portfolio_card(name, data, rank_colors):
    """Render a single portfolio card"""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        # Rank badge
        rank_class = f"rank-{data['rank']}"
        st.markdown(f"<h2 class='{rank_class}'>#{data['rank']}</h2>", unsafe_allow_html=True)

    with col2:
        # Portfolio name and description
        badge_class = name.lower() + "-badge"
        st.markdown(f"<span class='{badge_class}'>{data['name']}</span>", unsafe_allow_html=True)
        st.caption(data['description'])

    with col3:
        # Total return
        return_pct = data['total_return_pct']
        color = "green" if return_pct >= 0 else "red"
        st.markdown(f"<p style='color:{color}; font-size:1.5rem; font-weight:bold;'>{return_pct:+.2f}%</p>", unsafe_allow_html=True)

    # Metrics
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Value", f"₹{data['total_value']:,.0f}",
                  delta=f"₹{data['total_pnl']:+,.0f}")

    with col2:
        st.metric("Cash", f"₹{data['current_capital']:,.0f}")

    with col3:
        st.metric("Invested", f"₹{data['invested']:,.0f}")

    with col4:
        st.metric("Open Positions", data['open_positions'])

    with col5:
        st.metric("Total Trades", data['total_trades'])

    # Performance metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Win Rate", f"{data['win_rate']:.1f}%")

    with col2:
        color = "green" if data['winning_trades'] > data['losing_trades'] else "red"
        st.metric("W/L", f"{data['winning_trades']}/{data['losing_trades']}")

    with col3:
        st.metric("Best Trade", f"₹{data['best_trade']:+,.0f}")

    with col4:
        st.metric("Worst Trade", f"₹{data['worst_trade']:+,.0f}")

    # Avg win/loss
    if data['avg_win'] != 0 or data['avg_loss'] != 0:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Avg Win", f"₹{data['avg_win']:,.0f}")
        with col2:
            st.metric("Avg Loss", f"₹{data['avg_loss']:,.0f}")


def create_equity_curve_chart(portfolio_comp):
    """Create equity curve comparison chart"""
    fig = go.Figure()

    colors = {
        'EXCELLENT': '#00ff00',
        'MODERATE': '#ffaa00',
        'ALL': '#4488ff'
    }

    for name, portfolio in portfolio_comp.portfolios.items():
        if not portfolio['trade_history']:
            continue

        # Create equity curve from trade history
        equity = [portfolio_comp.initial_capital]
        dates = [datetime.fromisoformat(portfolio_comp.start_date)]

        for trade in portfolio['trade_history']:
            exit_date = datetime.fromisoformat(trade['exit_date'])
            new_equity = equity[-1] + trade['pnl']
            equity.append(new_equity)
            dates.append(exit_date)

        # Add current equity
        current_prices = get_current_prices(portfolio_comp)
        summary = portfolio_comp.get_comparison_summary(current_prices)
        equity.append(summary[name]['total_value'])
        dates.append(datetime.now())

        fig.add_trace(go.Scatter(
            x=dates,
            y=equity,
            mode='lines+markers',
            name=portfolio['name'],
            line=dict(color=colors[name], width=3),
            marker=dict(size=6)
        ))

    # Add baseline
    fig.add_hline(
        y=portfolio_comp.initial_capital,
        line_dash="dash",
        line_color="gray",
        annotation_text="Initial Capital"
    )

    fig.update_layout(
        title="📈 Equity Curve Comparison",
        xaxis_title="Date",
        yaxis_title="Portfolio Value (₹)",
        hovermode='x unified',
        height=500,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig


def create_performance_metrics_chart(summary):
    """Create performance metrics comparison chart"""
    portfolios = list(summary.keys())

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Total Return %", "Win Rate %", "Total Trades", "Total P&L (₹)"),
        specs=[[{"type": "bar"}, {"type": "bar"}],
               [{"type": "bar"}, {"type": "bar"}]]
    )

    colors = {
        'EXCELLENT': '#00ff00',
        'MODERATE': '#ffaa00',
        'ALL': '#4488ff'
    }

    # Total Return %
    fig.add_trace(
        go.Bar(
            x=portfolios,
            y=[summary[p]['total_return_pct'] for p in portfolios],
            marker_color=[colors[p] for p in portfolios],
            name="Return %"
        ),
        row=1, col=1
    )

    # Win Rate %
    fig.add_trace(
        go.Bar(
            x=portfolios,
            y=[summary[p]['win_rate'] for p in portfolios],
            marker_color=[colors[p] for p in portfolios],
            name="Win Rate"
        ),
        row=1, col=2
    )

    # Total Trades
    fig.add_trace(
        go.Bar(
            x=portfolios,
            y=[summary[p]['total_trades'] for p in portfolios],
            marker_color=[colors[p] for p in portfolios],
            name="Trades"
        ),
        row=2, col=1
    )

    # Total P&L
    fig.add_trace(
        go.Bar(
            x=portfolios,
            y=[summary[p]['total_pnl'] for p in portfolios],
            marker_color=[colors[p] for p in portfolios],
            name="P&L"
        ),
        row=2, col=2
    )

    fig.update_layout(
        height=600,
        showlegend=False
    )

    return fig


def render_trade_history(portfolio_comp, portfolio_name):
    """Render trade history for a portfolio"""
    portfolio = portfolio_comp.portfolios[portfolio_name]

    if not portfolio['trade_history']:
        st.info("No completed trades yet.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(portfolio['trade_history'])

    # Format dates
    df['entry_date'] = pd.to_datetime(df['entry_date']).dt.strftime('%Y-%m-%d %H:%M')
    df['exit_date'] = pd.to_datetime(df['exit_date']).dt.strftime('%Y-%m-%d %H:%M')

    # Format numbers
    df['entry_price'] = df['entry_price'].apply(lambda x: f"₹{x:.2f}")
    df['exit_price'] = df['exit_price'].apply(lambda x: f"₹{x:.2f}")
    df['pnl'] = df['pnl'].apply(lambda x: f"₹{x:+,.0f}")
    df['pnl_pct'] = df['pnl_pct'].apply(lambda x: f"{x:+.2f}%")

    # Select columns
    df = df[['symbol', 'entry_date', 'entry_price', 'exit_date', 'exit_price',
             'shares', 'pnl', 'pnl_pct', 'reason']]

    # Sort by exit date (newest first)
    df = df.sort_values('exit_date', ascending=False)

    st.dataframe(df, use_container_width=True, height=400)


def render_open_positions(portfolio_comp, portfolio_name, current_prices):
    """Render open positions for a portfolio"""
    portfolio = portfolio_comp.portfolios[portfolio_name]

    if not portfolio['positions']:
        st.info("No open positions.")
        return

    positions = []
    for symbol, pos in portfolio['positions'].items():
        current_price = current_prices.get(symbol, pos['entry_price'])
        unrealized_pnl = (current_price - pos['entry_price']) * pos['shares']
        unrealized_pnl_pct = (current_price - pos['entry_price']) / pos['entry_price'] * 100

        positions.append({
            'Symbol': symbol,
            'Entry Date': datetime.fromisoformat(pos['entry_date']).strftime('%Y-%m-%d'),
            'Entry Price': f"₹{pos['entry_price']:.2f}",
            'Current Price': f"₹{current_price:.2f}",
            'Shares': pos['shares'],
            'Invested': f"₹{pos['cost']:,.0f}",
            'Current Value': f"₹{current_price * pos['shares']:,.0f}",
            'Unrealized P&L': f"₹{unrealized_pnl:+,.0f}",
            'Unrealized %': f"{unrealized_pnl_pct:+.2f}%",
            'Target 1': f"₹{pos['target1']:.2f}",
            'Target 2': f"₹{pos['target2']:.2f}",
            'Target 3': f"₹{pos['target3']:.2f}",
            'Stop Loss': f"₹{pos['stop_loss']:.2f}",
            'Score': f"{pos['score']:.1f}/10",
            'Type': pos['trade_type']
        })

    df = pd.DataFrame(positions)
    st.dataframe(df, use_container_width=True, height=400)


def main():
    """Main dashboard"""

    # Header
    st.title("📊 Live Strategy Comparison Dashboard")
    st.markdown("**Compare 3 trading strategies in real-time to find the best performer**")

    # Load portfolio comparison
    portfolio_comp = load_portfolio_comparison()

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Dashboard Settings")

        # Auto-refresh
        auto_refresh = st.checkbox("Auto Refresh", value=True)
        if auto_refresh:
            refresh_interval = st.slider("Refresh Interval (seconds)", 10, 300, 60)
            st.info(f"Dashboard will refresh every {refresh_interval} seconds")

        st.divider()

        # Experiment info
        st.header("🧪 Experiment Info")
        start_date = datetime.fromisoformat(portfolio_comp.start_date)
        days_running = (datetime.now() - start_date).days
        st.metric("Days Running", days_running)
        st.metric("Started On", start_date.strftime('%Y-%m-%d'))
        st.metric("Initial Capital (Each)", f"₹{portfolio_comp.initial_capital:,.0f}")

        st.divider()

        # Strategy descriptions
        st.header("📝 Strategies")
        st.markdown("""
        **🟢 EXCELLENT**
        - Score ≥ 8.5
        - Only highest quality signals
        - Expected: Low frequency, high accuracy

        **🟡 MODERATE**
        - Score ≥ 8.0
        - Good + Excellent signals
        - Expected: Balanced frequency & accuracy

        **🔵 ALL SIGNALS**
        - Score ≥ 7.0
        - All Discord alerts
        - Expected: High frequency, varied accuracy
        """)

        st.divider()

        # Actions
        st.header("🔧 Actions")
        if st.button("🔄 Force Refresh", use_container_width=True):
            st.cache_resource.clear()
            st.rerun()

        if st.button("📁 Export Data", use_container_width=True):
            st.info("Export feature coming soon!")

        if st.button("🗑️ Reset All Portfolios", type="secondary", use_container_width=True):
            if st.checkbox("⚠️ Confirm Reset"):
                portfolio_comp.reset_all()
                st.success("All portfolios reset!")
                st.rerun()

    # Get current prices and summary
    current_prices = get_current_prices(portfolio_comp)
    summary = portfolio_comp.get_comparison_summary(current_prices)

    # Overview Section
    st.header("🎯 Performance Overview")

    # Rank colors
    rank_colors = {1: "green", 2: "orange", 3: "red"}

    # Create 3 columns for portfolios
    for portfolio_name in ['EXCELLENT', 'MODERATE', 'ALL']:
        with st.container():
            render_portfolio_card(portfolio_name, summary[portfolio_name], rank_colors)
            st.divider()

    # Charts Section
    st.header("📈 Performance Charts")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Equity curve
        equity_fig = create_equity_curve_chart(portfolio_comp)
        st.plotly_chart(equity_fig, use_container_width=True)

    with col2:
        # Performance metrics
        metrics_fig = create_performance_metrics_chart(summary)
        st.plotly_chart(metrics_fig, use_container_width=True)

    # Detailed View Section
    st.header("📊 Detailed View")

    # Tabs for each portfolio
    tab1, tab2, tab3 = st.tabs([
        f"🟢 EXCELLENT (#{summary['EXCELLENT']['rank']})",
        f"🟡 MODERATE (#{summary['MODERATE']['rank']})",
        f"🔵 ALL SIGNALS (#{summary['ALL']['rank']})"
    ])

    with tab1:
        st.subheader("Open Positions")
        render_open_positions(portfolio_comp, 'EXCELLENT', current_prices)
        st.subheader("Trade History")
        render_trade_history(portfolio_comp, 'EXCELLENT')

    with tab2:
        st.subheader("Open Positions")
        render_open_positions(portfolio_comp, 'MODERATE', current_prices)
        st.subheader("Trade History")
        render_trade_history(portfolio_comp, 'MODERATE')

    with tab3:
        st.subheader("Open Positions")
        render_open_positions(portfolio_comp, 'ALL', current_prices)
        st.subheader("Trade History")
        render_trade_history(portfolio_comp, 'ALL')

    # Footer
    st.divider()
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Auto-refresh
    if auto_refresh:
        import time
        time.sleep(refresh_interval)
        st.rerun()


if __name__ == "__main__":
    main()
