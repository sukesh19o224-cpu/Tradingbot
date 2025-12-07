#!/bin/bash

# 🚀 MAIN RUN SCRIPT - EOD + Intraday Trading System
# Complete automated trading system with heartbeat monitoring

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

show_menu() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║     🚀 PROFESSIONAL TRADING SYSTEM v2.0                 ║"
    echo "║     Dual Portfolio • Industry-Standard Quality         ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
    echo "💰 Capital Allocation:"
    echo "   📈 Positional: ₹50,000 (Real money, balanced strategies)"
    echo "   🔥 Swing: ₹25,000 (Paper test, A+ only - Score ≥8.5, Quality ≥70)"
    echo ""
    echo "🎯 System Features:"
    echo "   ✅ ATR-based dynamic stops (2-6% based on volatility)"
    echo "   ✅ Quality scoring: MR 50+, Momentum 60+, Breakout 60+"
    echo "   ✅ Locked profit after T1: +3% trail stop (not breakeven)"
    echo "   ✅ Multi-timeframe confirmation (Daily + Intraday)"
    echo "   ✅ Auto-replacement: High-quality signals replace weak positions"
    echo ""
    echo "Choose what to run:"
    echo ""
    echo "  1) 🎯 Quick Test            - Test with 10 stocks (~15s)"
    echo "  2) 📊 Single Scan (500)     - Scan Top 500 stocks (~7 min)"
    echo "  3) 🌆 EOD Ranking           - Generate Top 500 list (~15 min)"
    echo "  4) 🔥 CONTINUOUS MODE       - 24/7 Automated (RECOMMENDED)"
    echo "  5) 📈 Show Summary          - View portfolio performance"
    echo "  6) 🧪 Test Discord          - Test Discord alerts"
    echo "  7) 🔧 OLD System            - Run old main.py (backward compat)"
    echo "  8) ❌ Exit"
    echo ""
    echo "💡 CONTINUOUS Mode (Option 4):"
    echo "   • Heartbeat every 5 mins when market closed"
    echo "   • Scans 500 stocks every 10 mins (9:15 AM - 3:30 PM)"
    echo "   • EOD ranking at 3:45 PM (generates Top 500)"
    echo "   • Monitors positions every 5 mins"
    echo "   • 98%+ data success rate"
    echo ""
    echo "💡 Quick Test (Option 1): Perfect for first-time testing!"
    echo ""
}

run_quick_test() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║     🧪 QUICK TEST - 10 Stocks                           ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
    echo "Testing with 10 large-cap stocks..."
    echo "Expected time: ~15 seconds"
    echo ""
    echo "Press Enter to start, or Ctrl+C to cancel"
    read -p ""
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    python3 test_system.py
}

run_single_scan() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║     📊 SINGLE SCAN - Top 500 NSE Stocks                 ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
    echo "Scanning Top 500 NSE stocks..."
    echo "Expected time: ~7 minutes"
    echo "Expected success: 97-98% (485-490 stocks)"
    echo ""
    echo "Press Enter to start, or Ctrl+C to cancel"
    read -p ""
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    python3 main_eod_system.py --mode once
}

run_eod_ranking() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║     🌆 EOD RANKING - Generate Top 500 List              ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
    echo "📌 What this does:"
    echo "   • Fetches all ~2,200 NSE stocks"
    echo "   • Ranks by market capitalization"
    echo "   • Saves Top 500 to config/nse_top_500_live.py"
    echo "   • Used for tomorrow's intraday scans"
    echo ""
    echo "⏳ Expected time: ~15 minutes"
    echo "💾 Output: config/nse_top_500_live.py"
    echo ""
    echo "Press Enter to start, or Ctrl+C to cancel"
    read -p ""
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    python3 main_eod_system.py --mode eod
}

run_continuous_mode() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║     🔥 CONTINUOUS MODE - 24/7 Automated Trading         ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
    echo "✨ COMPLETE AUTOMATION:"
    echo ""
    echo "📌 Before Market (Before 9:15 AM):"
    echo "   💓 Heartbeat every 5 minutes"
    echo "   📊 Shows: Loaded stocks, system status"
    echo ""
    echo "📌 Market Hours (9:15 AM - 3:30 PM):"
    echo "   🔍 Scan 500 stocks every 10 minutes"
    echo "   👁️ Monitor positions every 5 minutes"
    echo "   📱 Send Discord alerts for qualified stocks"
    echo "   ⚡ Expected: 3-10 signals per scan"
    echo ""
    echo "📌 EOD (3:45 PM):"
    echo "   🌆 Auto-generate Top 500 list"
    echo "   💾 Updates for tomorrow's scans"
    echo "   ⏳ Takes ~15 minutes"
    echo ""
    echo "📌 After Market (After 4:00 PM):"
    echo "   💓 Heartbeat every 5 minutes"
    echo "   💤 System sleeps until next market open"
    echo ""
    echo "💼 Portfolio: Positional 70% (5-14 days) + Swing STRICT 30% (score ≥8.0)"
    echo "📊 Max Positions: 7 per portfolio • Success Rate: 97.8% (489/500)"
    echo ""
    echo "Choose mode:"
    echo "  1) System only (no dashboard)"
    echo "  2) System + Dashboard (RECOMMENDED)"
    echo ""
    read -p "Enter choice (1-2): " cont_choice

    case $cont_choice in
        1)
            echo ""
            echo "🚀 Starting CONTINUOUS MODE (System Only)..."
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            python3 main_eod_system.py --mode continuous
            ;;
        2)
            echo ""
            echo "🚀 Starting CONTINUOUS MODE with Dashboard..."
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            echo "📊 Dashboard will open in your browser..."
            echo "🌐 URL: http://localhost:8501"
            echo ""
            echo "⚠️  Keep BOTH windows open!"
            echo "   • Terminal: Trading system"
            echo "   • Browser: Live dashboard"
            echo ""
            echo "Press Enter to start..."
            read -p ""

            # Start trading system in background
            python3 main_eod_system.py --mode continuous &
            SYSTEM_PID=$!
            echo "   System started (PID: $SYSTEM_PID)"
            sleep 3

            # Start dashboard (foreground)
            echo "   Starting dashboard..."
            streamlit run dashboard.py --server.port=8501 --server.headless=true

            # When dashboard closes, kill system
            echo ""
            echo "Stopping trading system..."
            kill $SYSTEM_PID 2>/dev/null
            ;;
        *)
            echo "❌ Invalid choice"
            ;;
    esac
}

show_summary() {
    echo ""
    echo "📈 Portfolio Performance Summary"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    python3 main_eod_system.py --summary
}

test_discord() {
    echo ""
    echo "🧪 Testing Discord connection..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    python3 main.py --test-discord
    echo ""
    echo "Check your Discord channel for test message!"
}

run_old_system() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║     🔧 OLD SYSTEM (main.py)                             ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
    echo "⚠️  This runs the OLD main.py (backward compatibility)"
    echo "💡 For NEW system features, use other options!"
    echo ""
    echo "Choose mode:"
    echo "  1) Single scan"
    echo "  2) Continuous mode"
    echo "  3) Back to main menu"
    echo ""
    read -p "Enter choice (1-3): " old_choice

    case $old_choice in
        1)
            echo ""
            echo "🎯 Running old single scan..."
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            python3 main.py --mode once
            ;;
        2)
            echo ""
            echo "🔄 Running old continuous mode..."
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            python3 main.py --mode continuous
            ;;
        3)
            return
            ;;
        *)
            echo "❌ Invalid choice"
            ;;
    esac
}

# Main script logic
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
    live|continuous)
        run_continuous_mode
        ;;
    summary|stats)
        show_summary
        ;;
    test-discord|discord)
        test_discord
        ;;
    old)
        run_old_system
        ;;
    *)
        # Interactive menu
        while true; do
            show_menu
            read -p "Enter choice (1-8): " choice

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
                    run_continuous_mode
                    ;;
                5)
                    show_summary
                    echo ""
                    read -p "Press Enter to continue..."
                    ;;
                6)
                    test_discord
                    echo ""
                    read -p "Press Enter to continue..."
                    ;;
                7)
                    run_old_system
                    echo ""
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
