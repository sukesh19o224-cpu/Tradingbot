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
    echo "  2) ✨ AUTOMATIC Mode        - Fully automatic! (RECOMMENDED)"
    echo "  3) 🌙 EOD Scanner           - Manual EOD scan (for testing)"
    echo "  4) 📊 Dashboard             - Open main dashboard"
    echo "  5) 🎯 Comparison Mode       - Test 3 strategies"
    echo "  6) 📈 Show Summary          - View current performance"
    echo "  7) 🧪 Test Discord          - Test Discord alerts"
    echo "  8) ❌ Exit"
    echo ""
    echo "💡 NEW: Option 2 = Fully automatic! EOD scan at 4 PM daily"
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
    echo "║     🔄 FULLY AUTOMATIC CONTINUOUS MODE                  ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
    echo "✨ FULLY AUTOMATIC SYSTEM - Just run once!"
    echo ""
    echo "📌 System will AUTOMATICALLY:"
    echo "   • Morning (9:15 AM): Load top stocks from yesterday's EOD scan"
    echo "   • Market hours: Scan every 5 minutes (Daily + 15-min candles)"
    echo "   • Generate signals and send Discord alerts"
    echo "   • Execute paper trades and monitor positions"
    echo "   • 3:30 PM: Generate daily summary"
    echo "   • 4:00 PM: Run automatic EOD scan of ALL NSE stocks"
    echo "   • Rank top 500 stocks in 4 tiers for next day"
    echo "   • Sleep until next market open"
    echo ""
    echo "🎯 Which tier of stocks to trade?"
    echo "   TIER 1: Top 50  (Best swing trades - aggressive)"
    echo "   TIER 2: Top 100 (Swing + positional - balanced)"
    echo "   TIER 3: Top 250 (Positional - medium-term)"
    echo "   TIER 4: Top 500 (All viable - conservative)"
    echo ""
    read -p "Enter tier (1-4) [default: 1]: " tier_choice
    tier_choice=${tier_choice:-1}

    case $tier_choice in
        1)
            tier="tier1"
            tier_name="TIER 1 - TOP 50 (Swing Trading)"
            ;;
        2)
            tier="tier2"
            tier_name="TIER 2 - TOP 100 (Swing + Positional)"
            ;;
        3)
            tier="tier3"
            tier_name="TIER 3 - TOP 250 (Positional)"
            ;;
        4)
            tier="tier4"
            tier_name="TIER 4 - TOP 500 (All Viable)"
            ;;
        *)
            tier="tier1"
            tier_name="TIER 1 - TOP 50 (Swing Trading)"
            ;;
    esac

    echo ""
    echo "🚀 Starting fully automatic mode with $tier_name"
    echo ""
    echo "✨ Just leave it running - it handles everything!"
    echo "Press Ctrl+C to stop"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    python3 main.py --mode continuous --eod-tier $tier
}

run_eod_scan() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║     🌙 END-OF-DAY SCANNER                               ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
    echo "⏰ Best time: After 3:30 PM IST (market close)"
    echo "📊 Scans: ALL NSE verified stocks (~600-800 stocks)"
    echo "⏱️  Time needed: 5-10 minutes"
    echo ""
    echo "📈 This scan ranks all NSE stocks by signal quality"
    echo "   Results saved in 4 TIERS for different trading styles:"
    echo "   • TIER 1: Top 50  (Swing trading - aggressive)"
    echo "   • TIER 2: Top 100 (Swing + positional - balanced)"
    echo "   • TIER 3: Top 250 (Positional - medium-term)"
    echo "   • TIER 4: Top 500 (All viable - conservative)"
    echo ""
    echo "💡 Note: In automatic mode, EOD scan runs automatically at 4 PM"
    echo "   This manual option is for testing or re-running scans"
    echo ""
    echo "How many top stocks to rank?"
    echo "  1) Top 250 (faster - good for testing)"
    echo "  2) Top 500 (recommended - full ranking)"
    echo "  3) Top 750 (comprehensive)"
    echo ""
    read -p "Enter choice (1-3) [default: 2]: " eod_choice
    eod_choice=${eod_choice:-2}

    case $eod_choice in
        1)
            top_n=250
            ;;
        2)
            top_n=500
            ;;
        3)
            top_n=750
            ;;
        *)
            top_n=500
            ;;
    esac

    echo ""
    echo "🚀 Starting EOD scan (top $top_n stocks in 4 tiers)..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    python3 main.py --mode eod --eod-top-n $top_n
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
    eod)
        run_eod_scan
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
            read -p "Enter choice (1-8): " choice

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
                    run_eod_scan
                    echo ""
                    read -p "Press Enter to continue..."
                    ;;
                4)
                    run_dashboard
                    ;;
                5)
                    run_comparison_mode
                    ;;
                6)
                    show_summary
                    echo ""
                    read -p "Press Enter to continue..."
                    ;;
                7)
                    test_discord
                    read -p "Press Enter to continue..."
                    ;;
                8)
                    echo ""
                    echo "👋 Goodbye!"
                    echo ""
                    exit 0
                    ;;
                *)
                    echo ""
                    echo "❌ Invalid choice. Please enter 1-8."
                    sleep 2
                    ;;
            esac
        done
        ;;
esac
