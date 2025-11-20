#!/bin/bash

# 🚀 ONE-TIME SETUP SCRIPT
# Run this once to set up your trading system

echo "╔══════════════════════════════════════════════════════════╗"
echo "║     🚀 SUPER MATH TRADING SYSTEM - SETUP                ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "📋 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "   ❌ Python3 not found! Please install Python 3.8 or higher."
    exit 1
fi
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   ✅ Found: Python $python_version"
echo ""

# Create virtual environment
echo "🔧 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "   ✅ Virtual environment already exists"
else
    python3 -m venv venv
    if [ $? -eq 0 ]; then
        echo "   ✅ Virtual environment created!"
    else
        echo "   ❌ Failed to create virtual environment"
        echo "   Try: sudo apt install python3-venv"
        exit 1
    fi
fi
echo ""

# Activate virtual environment
echo "📦 Installing dependencies..."
echo "   This may take 2-3 minutes..."
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip > /dev/null 2>&1

# Install dependencies
if pip install -r requirements.txt; then
    echo "   ✅ All dependencies installed!"
else
    echo "   ❌ Failed to install some dependencies"
    echo "   Check requirements.txt and try again"
    exit 1
fi
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
if python3 -c "
import sys
try:
    from config.settings import *
    from src.data.data_fetcher import DataFetcher
    from src.strategies.signal_generator import SignalGenerator
    print('   ✅ All imports working!')
except Exception as e:
    print(f'   ❌ Import error: {e}')
    sys.exit(1)
" 2>&1; then
    echo ""
else
    echo "   ⚠️  Some imports failed, but you can continue"
    echo ""
fi

# Deactivate venv
deactivate

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
echo "💡 Note: Virtual environment created in 'venv' folder"
echo "   RUN.sh automatically activates it when needed"
echo ""
echo "📖 For full documentation, see: README.md"
echo ""
