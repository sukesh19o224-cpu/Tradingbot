#!/bin/bash

# 🎯 DUAL STRATEGY RUNNER
# Runs both Strategy 1 (70/30) and Strategy 2 (50/50) simultaneously
# NO TIME CONFLICTS - Both run independently at the same time

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Create directories if they don't exist
mkdir -p data data/cache data/cache_strategy2 logs

# Initialize Strategy 2 portfolio files if needed
if [ ! -f data/strategy2_swing_portfolio.json ]; then
    echo '{"capital": 50000, "initial_capital": 50000, "positions": {}}' > data/strategy2_swing_portfolio.json
fi

if [ ! -f data/strategy2_positional_portfolio.json ]; then
    echo '{"capital": 50000, "initial_capital": 50000, "positions": {}}' > data/strategy2_positional_portfolio.json
fi

if [ ! -f data/strategy2_swing_trades.json ]; then
    echo '[]' > data/strategy2_swing_trades.json
fi

if [ ! -f data/strategy2_positional_trades.json ]; then
    echo '[]' > data/strategy2_positional_trades.json
fi

show_menu() {
    clear
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║          🎯 DUAL STRATEGY TRADING SYSTEM                         ║"
    echo "║      Run Both Strategies Sequentially - NO CONFLICTS!            ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "┌───────────────────────────────────────────────────────────────────┐"
    echo "│ 📊 STRATEGY 1 (Main) - 70% Positional / 30% Swing                │"
    echo "│    • Positional: Score ≥7.0, ADX ≥25, Hold 5-15 days             │"
    echo "│    • Swing: Score ≥8.0, ADX ≥30, Hold 3-7 days (STRICT)          │"
    echo "│    • Max: 7 positions per portfolio                               │"
    echo "│    • Discord: ✅ Enabled                                          │"
    echo "│    • Dashboard: http://localhost:8501                             │"
    echo "│    • Files: data/swing_portfolio.json, positional_portfolio.json  │"
    echo "├───────────────────────────────────────────────────────────────────┤"
    echo "│ 🎯 STRATEGY 2 (Stricter) - 50% Swing / 50% Positional            │"
    echo "│    • Swing: Score ≥8.3, ADX ≥32 (vs 8.0/30 in Strategy 1)        │"
    echo "│    • Positional: Score ≥7.5, ADX ≥27 (vs 7.0/25 in Strategy 1)   │"
    echo "│    • Max: 5 positions per portfolio                               │"
    echo "│    • Discord: ❌ Disabled (Dashboard only)                        │"
    echo "│    • Dashboard: http://localhost:8502                             │"
    echo "│    • Files: data/strategy2_*.json (separate)                      │"
    echo "└───────────────────────────────────────────────────────────────────┘"
    echo ""
    echo "📋 MENU OPTIONS:"
    echo ""
    echo "  1) 🎯 Quick Test            - Test with 10 stocks (~15s)"
    echo "  2) 📊 Single Scan           - Both strategies scan once (~7 min)"
    echo "  3) 🌆 EOD Ranking           - Generate Top 500 list (~15 min)"
    echo "  4) 🔥 Run Both Strategies   - Systems only (continuous)"
    echo "  5) 🌟 Both + Dashboards     - RECOMMENDED (continuous)"
    echo "  6) 📊 Strategy 1 Only       - 70/30 continuous"
    echo "  7) 🎯 Strategy 2 Only       - 50/50 continuous"
    echo "  8) 📈 Strategy 1 Dashboard  - Open port 8501"
    echo "  9) 📊 Strategy 2 Dashboard  - Open port 8502"
    echo "  10) 📋 Show Summary         - View both portfolios"
    echo "  11) 🧪 Test Discord         - Test alerts"
    echo "  12) ❌ Exit"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "💡 HOW IT WORKS (SEQUENTIAL - NO API CONFLICTS):"
    echo "   1️⃣  Strategy 1 scans 500 stocks (~3 min)"
    echo "   2️⃣  Strategy 1 signals completion"
    echo "   3️⃣  Strategy 2 starts scanning (~3 min)"
    echo "   4️⃣  Both wait for next 10-min cycle"
    echo ""
    echo "   • SAME analysis (technical/math/ML) for both"
    echo "   • DIFFERENT filters (Strategy 2 stricter)"
    echo "   • ZERO API conflicts (sequential execution)"
    echo "   • Strategy 1: More trades (balanced)"
    echo "   • Strategy 2: Fewer trades (elite only)"
    echo ""
    echo "⏰ TIMING:"
    echo "   • Every 10 min: Strategy 1 → Strategy 2 (sequential)"
    echo "   • Every 5 min: Both monitor positions (independent)"
    echo "   • 3:45 PM: EOD ranking (Strategy 1 only)"
    echo "   • Closed: Heartbeat every 5 min"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

run_both_systems() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║          🔥 STARTING BOTH STRATEGIES (System Only)               ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "🚀 Launching Strategy 1 (70/30)..."
    python3 main_eod_system.py --mode continuous &
    STRATEGY1_PID=$!
    echo "   ✅ Strategy 1 started (PID: $STRATEGY1_PID)"
    sleep 2
    
    echo ""
    echo "🚀 Launching Strategy 2 (50/50 Ultra-Strict)..."
    python3 main_strategy2.py &
    STRATEGY2_PID=$!
    echo "   ✅ Strategy 2 started (PID: $STRATEGY2_PID)"
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✨ BOTH STRATEGIES RUNNING (SEQUENTIAL - NO CONFLICTS)!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📊 Strategy 1: PID $STRATEGY1_PID (70% Positional / 30% Swing)"
    echo "   • Scans first, signals when done"
    echo "   • Same analysis engine as Strategy 2"
    echo ""
    echo "🎯 Strategy 2: PID $STRATEGY2_PID (50% Swing / 50% Positional)"
    echo "   • Waits for Strategy 1 signal"
    echo "   • Same analysis, moderately stricter filters"
    echo ""
    echo "💡 TIP: Open dashboards to monitor:"
    echo "   • Strategy 1: http://localhost:8501"
    echo "   • Strategy 2: http://localhost:8502"
    echo ""
    echo "⏱️  Execution: Strategy 1 (3min) → Strategy 2 (3min) → Wait (4min) → Repeat"
    echo ""
    echo "Press Ctrl+C to stop both strategies..."
    echo ""
    
    # Wait for user interrupt
    trap "echo ''; echo '🛑 Stopping both strategies...'; kill $STRATEGY1_PID $STRATEGY2_PID 2>/dev/null; echo '✅ Both strategies stopped'; exit 0" INT
    wait
}

run_both_with_dashboards() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║      🌟 STARTING BOTH STRATEGIES + DASHBOARDS (RECOMMENDED)      ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "This will open:"
    echo "  📊 Strategy 1 Dashboard: http://localhost:8501"
    echo "  🎯 Strategy 2 Dashboard: http://localhost:8502"
    echo ""
    echo "⚠️  Keep ALL windows open for full functionality!"
    echo ""
    echo "Press Enter to start..."
    read -p ""
    
    echo ""
    echo "🚀 Starting Strategy 1 (70/30)..."
    python3 main_eod_system.py --mode continuous &
    STRATEGY1_PID=$!
    echo "   ✅ Strategy 1 started (PID: $STRATEGY1_PID)"
    sleep 2
    
    echo ""
    echo "🚀 Starting Strategy 2 (50/50 Ultra-Strict)..."
    python3 main_strategy2.py &
    STRATEGY2_PID=$!
    echo "   ✅ Strategy 2 started (PID: $STRATEGY2_PID)"
    sleep 2
    
    echo ""
    echo "📊 Starting Strategy 1 Dashboard (Port 8501)..."
    streamlit run dashboard.py --server.port=8501 --server.headless=true &
    DASH1_PID=$!
    echo "   ✅ Dashboard 1 started (PID: $DASH1_PID)"
    sleep 3
    
    echo ""
    echo "🎯 Starting Strategy 2 Dashboard (Port 8502)..."
    streamlit run dashboard_strategy2.py --server.port=8502 --server.headless=true &
    DASH2_PID=$!
    echo "   ✅ Dashboard 2 started (PID: $DASH2_PID)"
    sleep 3
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✨ ALL SYSTEMS RUNNING (SEQUENTIAL - NO API CONFLICTS)!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📊 Strategy 1: PID $STRATEGY1_PID | Dashboard: http://localhost:8501"
    echo "   → Scans first (3 min) → Signals completion"
    echo ""
    echo "🎯 Strategy 2: PID $STRATEGY2_PID | Dashboard: http://localhost:8502"
    echo "   → Waits for signal → Scans (3 min) → Done"
    echo ""
    echo "📈 Dashboard 1: PID $DASH1_PID (Port 8501)"
    echo "📊 Dashboard 2: PID $DASH2_PID (Port 8502)"
    echo ""
    echo "💡 Your browser should open automatically with both dashboards"
    echo ""
    echo "⏱️  Total cycle: ~6 min scan + 4 min wait = 10 min interval"
    echo ""
    echo "Press Ctrl+C to stop all systems..."
    echo ""
    
    # Open browsers
    sleep 2
    (xdg-open http://localhost:8501 2>/dev/null || open http://localhost:8501 2>/dev/null) &
    sleep 2
    (xdg-open http://localhost:8502 2>/dev/null || open http://localhost:8502 2>/dev/null) &
    
    # Wait for user interrupt
    trap "echo ''; echo '🛑 Stopping all systems...'; kill $STRATEGY1_PID $STRATEGY2_PID $DASH1_PID $DASH2_PID 2>/dev/null; echo '✅ All systems stopped'; exit 0" INT
    wait
}

run_strategy1_only() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║              📊 STRATEGY 1 ONLY (70/30 Main)                     ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Running Strategy 1 with continuous mode..."
    echo ""
    python3 main_eod_system.py --mode continuous
}

run_strategy2_only() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║          🎯 STRATEGY 2 ONLY (50/50 Ultra-Strict)                 ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Running Strategy 2 with continuous mode..."
    echo ""
    python3 main_strategy2.py
}

open_dashboard1() {
    echo ""
    echo "📊 Opening Strategy 1 Dashboard..."
    echo "🌐 URL: http://localhost:8501"
    echo ""
    streamlit run dashboard.py --server.port=8501 --server.headless=true
}

open_dashboard2() {
    echo ""
    echo "🎯 Opening Strategy 2 Dashboard..."
    echo "🌐 URL: http://localhost:8502"
    echo ""
    streamlit run dashboard_strategy2.py --server.port=8502 --server.headless=true
}

run_quick_test() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║                    🧪 QUICK TEST - 10 Stocks                     ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Testing with 10 large-cap stocks (Strategy 1 only)..."
    echo "Expected time: ~15 seconds"
    echo ""
    echo "Press Enter to start, or Ctrl+C to cancel"
    read -p ""
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    python3 test_system.py
}

run_single_scan() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║            📊 SINGLE SCAN - Both Strategies                      ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "This will:"
    echo "  1️⃣  Strategy 1 scans Top 500 NSE stocks (~3 min)"
    echo "  2️⃣  Strategy 2 scans (waits for Strategy 1) (~3 min)"
    echo ""
    echo "Total time: ~7 minutes"
    echo "Expected success: 97-98% (485-490 stocks)"
    echo ""
    echo "Press Enter to start, or Ctrl+C to cancel"
    read -p ""
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🚀 Starting Strategy 1..."
    python3 main_eod_system.py --mode once &
    SCAN1_PID=$!
    wait $SCAN1_PID
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🎯 Strategy 1 complete! Starting Strategy 2..."
    echo ""
    
    # Simulate one scan for Strategy 2
    python3 -c "
import sys
sys.path.insert(0, '.')
from main_strategy2 import Strategy2TradingSystem
system = Strategy2TradingSystem()
system.scan_and_generate_signals()
"
    echo ""
    echo "✅ Both strategies completed!"
}

run_eod_ranking() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║              🌆 EOD RANKING - Generate Top 500 List              ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📌 What this does:"
    echo "   • Fetches all ~2,200 NSE stocks"
    echo "   • Ranks by market capitalization"
    echo "   • Saves Top 500 to config/nse_top_500_live.py"
    echo "   • Used by BOTH strategies for tomorrow's scans"
    echo ""
    echo "⏳ Expected time: ~15 minutes"
    echo "💾 Output: config/nse_top_500_live.py"
    echo ""
    echo "Press Enter to start, or Ctrl+C to cancel"
    read -p ""
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    python3 main_eod_system.py --mode eod
}

show_summary() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║                  📋 PORTFOLIO SUMMARY                            ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📊 STRATEGY 1 (70% Positional / 30% Swing)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    python3 main_eod_system.py --summary
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🎯 STRATEGY 2 (50% Swing / 50% Positional)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Check if Strategy 2 portfolios exist
    if [ -f "data/strategy2_swing_portfolio.json" ] && [ -f "data/strategy2_positional_portfolio.json" ]; then
        python3 -c "
import json
import os

try:
    with open('data/strategy2_swing_portfolio.json', 'r') as f:
        swing = json.load(f)
    with open('data/strategy2_positional_portfolio.json', 'r') as f:
        pos = json.load(f)
    
    swing_positions = len(swing.get('positions', {}))
    pos_positions = len(pos.get('positions', {}))
    swing_capital = swing.get('capital', 50000)
    pos_capital = pos.get('capital', 50000)
    
    print(f'💰 Swing Capital: ₹{swing_capital:,.0f} | Positions: {swing_positions}/5')
    print(f'💰 Positional Capital: ₹{pos_capital:,.0f} | Positions: {pos_positions}/5')
    print(f'💰 Total Capital: ₹{swing_capital + pos_capital:,.0f}')
except Exception as e:
    print(f'⚠️  No data yet or error: {e}')
"
    else
        echo "⚠️  Strategy 2 not started yet. Run Strategy 2 to see data here."
    fi
    
    echo ""
}

test_discord() {
    echo ""
    echo "🧪 Testing Discord connection (Strategy 1 only)..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    python3 main.py --test-discord
    echo ""
    echo "Check your Discord channel for test message!"
}

# Main script
case "$1" in
    test|quick)
        run_quick_test
        ;;
    once|scan)
        run_single_scan
        ;;
    eod|ranking)
        run_eod_ranking
        ;;
    both|dual)
        run_both_systems
        ;;
    both-dash|dual-dash)
        run_both_with_dashboards
        ;;
    s1|strategy1)
        run_strategy1_only
        ;;
    s2|strategy2)
        run_strategy2_only
        ;;
    dash1|d1)
        open_dashboard1
        ;;
    dash2|d2)
        open_dashboard2
        ;;
    summary|stats)
        show_summary
        ;;
    test-discord|discord)
        test_discord
        ;;
    *)
        # Interactive menu
        while true; do
            show_menu
            read -p "Enter choice (1-12): " choice
            
            case $choice in
                1)
                    run_quick_test
                    echo ""
                    read -p "Press Enter to continue..."
                    ;;
                2)
                    run_single_scan
                    echo ""
                    read -p "Press Enter to continue..."
                    ;;
                3)
                    run_eod_ranking
                    echo ""
                    read -p "Press Enter to continue..."
                    ;;
                4)
                    run_both_systems
                    ;;
                5)
                    run_both_with_dashboards
                    ;;
                6)
                    run_strategy1_only
                    echo ""
                    read -p "Press Enter to continue..."
                    ;;
                7)
                    run_strategy2_only
                    echo ""
                    read -p "Press Enter to continue..."
                    ;;
                8)
                    open_dashboard1
                    echo ""
                    read -p "Press Enter to continue..."
                    ;;
                9)
                    open_dashboard2
                    echo ""
                    read -p "Press Enter to continue..."
                    ;;
                10)
                    show_summary
                    echo ""
                    read -p "Press Enter to continue..."
                    ;;
                11)
                    test_discord
                    echo ""
                    read -p "Press Enter to continue..."
                    ;;
                12)
                    echo ""
                    echo "👋 Goodbye!"
                    echo ""
                    exit 0
                    ;;
                *)
                    echo ""
                    echo "❌ Invalid choice. Please enter 1-12."
                    sleep 2
                    ;;
            esac
        done
        ;;
esac
