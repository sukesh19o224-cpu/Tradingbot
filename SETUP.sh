#!/bin/bash

# 🚀 ONE-TIME SETUP SCRIPT
# Run this once to set up your trading system

echo "╔══════════════════════════════════════════════════════════╗"
echo "║     🚀 SUPER MATH TRADING SYSTEM - SETUP                ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Found: Python $python_version"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
echo "   This may take 2-3 minutes..."
pip install -q -r requirements.txt
echo "   ✅ Dependencies installed!"
echo ""

# Create directories
echo "📁 Creating data directories..."
mkdir -p data
mkdir -p logs
echo "   ✅ Directories created!"
echo ""

# Setup .env file
if [ ! -f .env ]; then
    echo "🔧 Setting up .env file..."
    cp .env.example .env
    echo "   ⚠️  IMPORTANT: Edit .env file and add your Discord webhook URL!"
    echo "   File location: .env"
    echo ""
else
    echo "✅ .env file already exists"
    echo ""
fi

# Test imports
echo "🧪 Testing Python imports..."
python3 -c "
import sys
try:
    from config.settings import *
    from src.data.data_fetcher import DataFetcher
    from src.strategies.signal_generator import SignalGenerator
    print('   ✅ All imports working!')
except Exception as e:
    print(f'   ❌ Import error: {e}')
    sys.exit(1)
"
echo ""

# Check Discord webhook
echo "🔍 Checking Discord configuration..."
if grep -q "YOUR_WEBHOOK_URL_HERE" .env 2>/dev/null; then
    echo "   ⚠️  WARNING: Discord webhook not configured!"
    echo "   Edit .env file and add your webhook URL"
    echo ""
else
    echo "   ✅ Discord webhook configured"
    echo ""
fi

# Summary
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                  ✅ SETUP COMPLETE!                      ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Configure Discord (if not done):"
echo "   nano .env    # Add your webhook URL"
echo ""
echo "2. Test Discord connection:"
echo "   ./RUN.sh test-discord"
echo ""
echo "3. Run the system:"
echo "   ./RUN.sh          # Interactive menu"
echo "   ./RUN.sh once     # Single scan"
echo "   ./RUN.sh live     # Continuous mode"
echo ""
echo "📖 For full documentation, see: README.md"
echo ""
