#!/bin/bash

# 🚀 MAIN RUN SCRIPT - Super Math Trading System
# Simple interface to run your trading system

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

show_menu() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║     🎯 HYBRID TRADING SYSTEM                            ║"
    echo "║     Swing + Positional • Dual Portfolio                 ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
    echo "Choose what to run:"
    echo ""
    echo "  1) 🎯 Single Scan           - Run one hybrid scan"
    echo "  2) 🔥 HYBRID Mode           - Swing + Positional! (RECOMMENDED)"
    echo "  3) 📊 GUI Dashboard         - Live Portfolio Dashboard"
    echo "  4) 📈 Show Summary          - View dual portfolio performance"
    echo "  5) 🧪 Test Discord          - Test Discord alerts"
    echo "  6) ❌ Exit"
    echo ""
    echo "💡 HYBRID Mode: Swing + Positional simultaneously"
    echo "   • Scans ALL stocks every 10 minutes during market hours"
    echo "   • Monitors positions every 5 minutes"
    echo "   • Never misses opportunities!"
    echo "💡 GUI Dashboard: Beautiful live portfolio viewer!"
    echo ""
}

run_single_scan() {
    echo ""
    echo "🎯 Running single scan..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    python3 main.py --mode once
}

run_live_mode() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║     🎯 HYBRID AUTOMATIC MODE                            ║"
    echo "║     Swing + Positional Trading Simultaneously           ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
    echo "✨ HYBRID SYSTEM - Never miss opportunities!"
    echo ""
    echo "📌 How it works:"
    echo "   • Scans ALL 800 verified NSE stocks"
    echo "   • Every stock checked for BOTH opportunities:"
    echo "     🔥 Swing: Fast momentum, breakouts (5-10%, 1-5 days)"
    echo "     📈 Positional: Trends, pullbacks (15-30%, 2-4 weeks)"
    echo "   • Dual portfolios (60% swing, 40% positional)"
    echo "   • Separate Discord alerts for each type"
    echo "   • Market hours: Scan every 10 minutes"
    echo "   • 3:30 PM: Daily summary"
    echo ""
    echo "💼 Portfolio Split:"
    echo "   🔥 Swing Portfolio: 60% capital (aggressive short-term)"
    echo "   📈 Positional Portfolio: 40% capital (conservative long-term)"
    echo ""
    echo "Press Enter to start, or Ctrl+C to cancel"
    read -p ""
    echo ""
    echo "🚀 Starting HYBRID automatic mode..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    python3 main.py --mode continuous
}


run_gui_dashboard() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║     📊 LIVE PORTFOLIO DASHBOARD (GUI)                   ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
    echo "✨ Features:"
    echo "   • Live portfolio summary (capital, P&L, win rate)"
    echo "   • Open positions table (both swing & positional)"
    echo "   • Complete trade history logs"
    echo "   • Auto-refresh every 5 seconds"
    echo ""
    echo "Press Ctrl+C to close"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    python3 GUI.py
}

run_comparison_mode() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║     🎯 STRATEGY COMPARISON MODE                         ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
    echo "This mode tests 3 strategies simultaneously:"
    echo "  🟢 EXCELLENT  - Only signals ≥ 8.5 (best quality)"
    echo "  🟡 MODERATE   - Signals ≥ 8.0 (good quality)"
    echo "  🔵 ALL        - All signals ≥ 7.0 (all alerts)"
    echo ""
    echo "Run for 2 weeks to see which performs best!"
    echo ""
    echo "Choose option:"
    echo "  1) Start comparison + open dashboard (recommended)"
    echo "  2) Run comparison only (system)"
    echo "  3) Open dashboard only (view results)"
    echo ""
    read -p "Enter choice (1-3): " comp_choice

    case $comp_choice in
        1)
            echo ""
            echo "🚀 Starting comparison system..."
            echo "   Terminal 1: Running system"
            echo "   Terminal 2: Opening dashboard"
            echo ""
            echo "⚠️  Keep BOTH windows open!"
            echo ""

            # Start system in background
            python3 main.py --mode continuous --enable-comparison > logs/comparison.log 2>&1 &
            SYSTEM_PID=$!
            echo "   System PID: $SYSTEM_PID"
            sleep 3

            # Start dashboard
            echo "   Opening dashboard..."
            python3 main.py --mode comparison

            # Kill system when dashboard closes
            kill $SYSTEM_PID 2>/dev/null
            ;;
        2)
            echo ""
            echo "🔄 Running comparison system..."
            echo "   Discord alerts: YES (all signals ≥7.0)"
            echo "   Paper trading: YES"
            echo "   Comparison portfolios: YES (3 strategies)"
            echo ""
            echo "Open dashboard in another terminal:"
            echo "   ./RUN.sh → Option 4 → Option 3"
            echo ""
            echo "Press Ctrl+C to stop"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            python3 main.py --mode continuous --enable-comparison
            ;;
        3)
            echo ""
            echo "📊 Opening comparison dashboard..."
            echo "🌐 Browser: http://localhost:8502"
            echo ""
            echo "⚠️  Make sure system is running in another terminal!"
            echo "   (Run option 4→2 in another terminal if not running)"
            echo ""
            echo "Press Ctrl+C to stop"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            python3 main.py --mode comparison
            ;;
        *)
            echo "❌ Invalid choice"
            ;;
    esac
}

show_summary() {
    echo ""
    echo "📈 Current Performance Summary"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    python3 main.py --summary
}

test_discord() {
    echo ""
    echo "🧪 Testing Discord connection..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    python3 main.py --test-discord
    echo ""
    echo "Check your Discord channel for test message!"
}

# Main script logic
case "$1" in
    once|scan)
        run_single_scan
        ;;
    live|continuous)
        run_live_mode
        ;;
    gui)
        run_gui_dashboard
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
            read -p "Enter choice (1-6): " choice

            case $choice in
                1)
                    run_single_scan
                    echo ""
                    read -p "Press Enter to continue..."
                    ;;
                2)
                    run_live_mode
                    ;;
                3)
                    run_gui_dashboard
                    echo ""
                    read -p "Press Enter to continue..."
                    ;;
                4)
                    show_summary
                    echo ""
                    read -p "Press Enter to continue..."
                    ;;
                5)
                    test_discord
                    echo ""
                    read -p "Press Enter to continue..."
                    ;;
                6)
                    echo ""
                    echo "👋 Goodbye!"
                    echo ""
                    exit 0
                    ;;
                *)
                    echo ""
                    echo "❌ Invalid choice. Please enter 1-6."
                    sleep 2
                    ;;
            esac
        done
        ;;
esac
