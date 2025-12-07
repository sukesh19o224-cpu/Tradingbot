#!/bin/bash

# Strategy 2 Dashboard Launcher
# Opens the Strategy 2 monitoring dashboard on port 8502

echo "======================================================================"
echo "📊 STRATEGY 2 DASHBOARD"
echo "======================================================================"
echo "Monitoring: 50% Swing + 50% Positional (ULTRA STRICT)"
echo "Port: 8502 (separate from Strategy 1)"
echo "======================================================================"
echo ""

# Activate virtual environment
source venv/bin/activate

echo "🚀 Starting Strategy 2 Dashboard..."
echo "💡 Dashboard will open at: http://localhost:8502"
echo "💡 Press Ctrl+C to stop"
echo ""

# Run streamlit dashboard on port 8502
streamlit run dashboard_strategy2.py --server.port 8502 --server.headless true
