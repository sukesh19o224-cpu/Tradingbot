#!/bin/bash

# 🎯 QUICK START: Live Strategy Comparison
# Run this script to start your 2-week comparison experiment

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  🎯 LIVE STRATEGY COMPARISON - QUICK START               ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "This will start comparing 3 trading strategies:"
echo "  🟢 EXCELLENT (≥8.5)"
echo "  🟡 MODERATE  (≥8.0)"
echo "  🔵 ALL       (≥7.0)"
echo ""

# Check if dependencies are installed
echo "📦 Checking dependencies..."
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit not found. Installing..."
    pip install streamlit plotly
fi

# Create data directory if it doesn't exist
mkdir -p data

echo ""
echo "✅ Ready to start!"
echo ""
echo "Choose an option:"
echo "  1) Run continuous (recommended for 2 weeks)"
echo "  2) Run single scan (quick test)"
echo "  3) Open dashboard only"
echo "  4) Reset comparison data and start fresh"
echo ""
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        echo ""
        echo "🔄 Starting continuous mode with comparison..."
        echo ""
        echo "The system will:"
        echo "  • Scan 200 stocks every 5 minutes"
        echo "  • Route signals to 3 portfolios"
        echo "  • Run during market hours (9:15 AM - 3:30 PM IST)"
        echo ""
        echo "📊 To view dashboard, open another terminal and run:"
        echo "   python main.py --mode comparison"
        echo ""
        echo "Press Ctrl+C to stop"
        echo ""
        python main.py --mode continuous --enable-comparison
        ;;
    2)
        echo ""
        echo "🎯 Running single scan with comparison..."
        python main.py --mode once --enable-comparison
        echo ""
        echo "✅ Scan complete!"
        echo ""
        read -p "Open dashboard now? (y/n): " open_dash
        if [ "$open_dash" = "y" ]; then
            python main.py --mode comparison
        fi
        ;;
    3)
        echo ""
        echo "📊 Opening comparison dashboard..."
        echo "🌐 Browser will open at: http://localhost:8502"
        echo ""
        python main.py --mode comparison
        ;;
    4)
        echo ""
        read -p "⚠️  Are you sure? This will delete all comparison data! (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            rm -f data/portfolio_comparison.json
            echo "✅ Comparison data reset!"
            echo ""
            echo "Starting fresh..."
            python main.py --mode continuous --enable-comparison
        else
            echo "❌ Reset cancelled"
        fi
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac
