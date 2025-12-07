#!/bin/bash

# Strategy 2 Runner Script
# Runs Strategy 2 trading system (AFTER Strategy 1 completes)

echo "======================================================================"
echo "🎯 STRATEGY 2 - ULTRA STRICT TRADING SYSTEM"
echo "======================================================================"
echo "50% Swing (≥9.0 score) + 50% Positional (≥8.5 score)"
echo "Runs SEQUENTIALLY after Strategy 1 completes each scan"
echo "Dashboard: http://localhost:8502"
echo "======================================================================"
echo ""

# Activate virtual environment
source venv/bin/activate

# Create data directory if not exists
mkdir -p data
mkdir -p logs
mkdir -p data/cache_strategy2

# Initialize empty portfolio files if they don't exist
if [ ! -f data/strategy2_swing_portfolio.json ]; then
    echo '{"capital": 50000, "initial_capital": 50000, "positions": {}}' > data/strategy2_swing_portfolio.json
    echo "✅ Created strategy2_swing_portfolio.json"
fi

if [ ! -f data/strategy2_positional_portfolio.json ]; then
    echo '{"capital": 50000, "initial_capital": 50000, "positions": {}}' > data/strategy2_positional_portfolio.json
    echo "✅ Created strategy2_positional_portfolio.json"
fi

if [ ! -f data/strategy2_swing_trades.json ]; then
    echo '[]' > data/strategy2_swing_trades.json
    echo "✅ Created strategy2_swing_trades.json"
fi

if [ ! -f data/strategy2_positional_trades.json ]; then
    echo '[]' > data/strategy2_positional_trades.json
    echo "✅ Created strategy2_positional_trades.json"
fi

echo ""
echo "🚀 Starting Strategy 2 Trading System..."
echo "💡 TIP: Open dashboard in browser: http://localhost:8502"
echo "💡 Press Ctrl+C to stop"
echo ""

# Run the main trading system
python main_strategy2.py
