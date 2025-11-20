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
    echo "║     🚀 SUPER MATH TRADING SYSTEM                        ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
    echo "Choose what to run:"
    echo ""
    echo "  1) 🎯 Single Scan           - Run one scan cycle"
    echo "  2) 🔄 Live Mode             - Run continuously (recommended)"
    echo "  3) 📊 Dashboard             - Open main dashboard"
    echo "  4) 🎯 Comparison Mode       - Test 3 strategies"
    echo "  5) 📈 Show Summary          - View current performance"
    echo "  6) 🧪 Test Discord          - Test Discord alerts"
    echo "  7) ❌ Exit"
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
    echo "🔄 Starting live continuous mode..."
    echo ""
    echo "📌 System will:"
    echo "   • Scan 200 stocks every 5 minutes"
    echo "   • Generate signals and send Discord alerts"
    echo "   • Execute paper trades automatically"
    echo "   • Monitor positions for exits"
    echo "   • Run during market hours (9:15 AM - 3:30 PM IST)"
    echo ""
    echo "Press Ctrl+C to stop"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    python3 main.py --mode continuous
}

run_dashboard() {
    echo ""
    echo "📊 Opening main dashboard..."
    echo "🌐 Browser: http://localhost:8501"
    echo ""
    echo "Press Ctrl+C to stop"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    python3 main.py --mode dashboard
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
    dashboard|dash)
        run_dashboard
        ;;
    comparison|compare|test)
        run_comparison_mode
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
            read -p "Enter choice (1-7): " choice

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
                    run_dashboard
                    ;;
                4)
                    run_comparison_mode
                    ;;
                5)
                    show_summary
                    echo ""
                    read -p "Press Enter to continue..."
                    ;;
                6)
                    test_discord
                    read -p "Press Enter to continue..."
                    ;;
                7)
                    echo ""
                    echo "👋 Goodbye!"
                    echo ""
                    exit 0
                    ;;
                *)
                    echo ""
                    echo "❌ Invalid choice. Please enter 1-7."
                    sleep 2
                    ;;
            esac
        done
        ;;
esac
