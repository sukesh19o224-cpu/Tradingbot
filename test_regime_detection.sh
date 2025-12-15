#!/bin/bash

# Test Market Regime Detection Feature
# This script demonstrates the regime detector in action

echo "╔══════════════════════════════════════════════════════════╗"
echo "║     📊 MARKET REGIME DETECTION TEST                     ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found! Run: python3 -m venv .venv"
    exit 1
fi

echo ""
echo "Testing Market Regime Detector..."
echo "=================================="
echo ""

# Run the regime detector test
python3 src/strategies/market_regime_detector.py

echo ""
echo "=================================="
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Review the detected regime above"
echo "2. To ENABLE regime detection in your system:"
echo "   - Edit config/settings.py"
echo "   - Set MARKET_REGIME_DETECTION_ENABLED = True"
echo ""
echo "3. To test with actual scanning:"
echo "   - Run: ./RUN.sh"
echo "   - Choose option 2 (One-Time Scan)"
echo "   - Compare signals with/without regime detection"
echo ""
echo "4. Current Status:"
echo "   - Regime Detection: DISABLED (default)"
echo "   - Change in settings.py to enable"
echo ""
