"""
📊 STRATEGY 2 DASHBOARD - Simple & Working
"""

import streamlit as st
import json
import os
from datetime import datetime

st.set_page_config(
    page_title="Strategy 2 Dashboard",
    page_icon="🎯",
    layout="wide"
)

st.markdown("""
<style>
    .big-metric { font-size: 2rem; font-weight: bold; }
    .positive { color: #00ff00; }
    .negative { color: #ff4444; }
</style>
""", unsafe_allow_html=True)

def load_data():
    """Load Strategy 2 portfolio data"""
    swing = {'capital': 50000, 'initial_capital': 50000, 'positions': {}}
    pos = {'capital': 50000, 'initial_capital': 50000, 'positions': {}}
    
    try:
        if os.path.exists('data/strategy2_swing_portfolio.json'):
            with open('data/strategy2_swing_portfolio.json', 'r') as f:
                swing = json.load(f)
        
        if os.path.exists('data/strategy2_positional_portfolio.json'):
            with open('data/strategy2_positional_portfolio.json', 'r') as f:
                pos = json.load(f)
    except:
        pass
    
    return swing, pos

# Load data
swing, pos = load_data()

# Header
st.markdown("# 🎯 STRATEGY 2 - STRICTER PORTFOLIO")
st.markdown("### 50% Swing (≥8.3) + 50% Positional (≥7.5)")
st.markdown("---")

# Get values
swing_capital = swing.get('capital', 50000)
pos_capital = pos.get('capital', 50000)
swing_positions = swing.get('positions', {})
pos_positions = pos.get('positions', {})

# Calculate
swing_invested = 50000 - swing_capital
pos_invested = 50000 - pos_capital
total_capital = swing_capital + pos_capital
total_invested = swing_invested + pos_invested
total_value = total_capital + total_invested

# Top metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("💰 Total Value", f"₹{total_value:,.0f}")

with col2:
    st.metric("💵 Available Cash", f"₹{total_capital:,.0f}")

with col3:
    st.metric("📊 Invested", f"₹{total_invested:,.0f}")

with col4:
    st.metric("📌 Total Positions", f"{len(swing_positions) + len(pos_positions)}")

st.markdown("---")

# Portfolio breakdown
col1, col2 = st.columns(2)

with col1:
    st.subheader("🔥 SWING Portfolio")
    st.write(f"💰 Available: ₹{swing_capital:,.0f}")
    st.write(f"📊 Invested: ₹{swing_invested:,.0f}")
    st.write(f"📌 Positions: {len(swing_positions)} / 5")
    
    if swing_positions:
        st.write("**Open Positions:**")
        for symbol, pos_data in swing_positions.items():
            entry = pos_data.get('entry_price', 0)
            shares = pos_data.get('shares', 0)
            cost = pos_data.get('cost', 0)
            st.write(f"• {symbol.replace('.NS', '')}: {shares} @ ₹{entry:.2f} = ₹{cost:,.0f}")
    else:
        st.info("No swing positions yet")

with col2:
    st.subheader("📈 POSITIONAL Portfolio")
    st.write(f"💰 Available: ₹{pos_capital:,.0f}")
    st.write(f"📊 Invested: ₹{pos_invested:,.0f}")
    st.write(f"📌 Positions: {len(pos_positions)} / 5")
    
    if pos_positions:
        st.write("**Open Positions:**")
        for symbol, pos_data in pos_positions.items():
            entry = pos_data.get('entry_price', 0)
            shares = pos_data.get('shares', 0)
            cost = pos_data.get('cost', 0)
            st.write(f"• {symbol.replace('.NS', '')}: {shares} @ ₹{entry:.2f} = ₹{cost:,.0f}")
    else:
        st.info("No positional positions yet")

st.markdown("---")
st.markdown(f"*Last updated: {datetime.now().strftime('%d %b %Y, %I:%M:%S %p')} IST*")

# Auto refresh every 5 seconds
if st.sidebar.checkbox("Auto-refresh (5s)", value=True):
    import time
    time.sleep(5)
    st.rerun()
