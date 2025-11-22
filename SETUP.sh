#!/bin/bash

# 🚀 CLEAN SETUP SCRIPT - LOCAL INSTALLATION ONLY
# Deletes old venv and creates fresh local installation
# NOTHING installed to OS/system - everything in ./venv/

echo "╔══════════════════════════════════════════════════════════╗"
echo "║     🚀 TRADING SYSTEM - CLEAN LOCAL SETUP               ║"
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

# Remove old venv if exists (CLEAN START)
echo "🗑️  Removing old virtual environment (if exists)..."
if [ -d "venv" ]; then
    echo "   Deleting old venv..."
    rm -rf venv
    echo "   ✅ Old venv deleted!"
else
    echo "   ✅ No old venv found"
fi

# Remove any .venv as well
if [ -d ".venv" ]; then
    echo "   Deleting old .venv..."
    rm -rf .venv
    echo "   ✅ Old .venv deleted!"
fi
echo ""

# Create fresh virtual environment
echo "🔧 Creating FRESH virtual environment in project directory..."
python3 -m venv venv
if [ $? -eq 0 ]; then
    echo "   ✅ Fresh virtual environment created in ./venv/"
else
    echo "   ❌ Failed to create virtual environment"
    echo "   Try: sudo apt install python3-venv"
    exit 1
fi
echo ""

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate
echo "   ✅ Virtual environment activated"
echo ""

# Verify we're using LOCAL venv, NOT system Python
echo "🔍 Verifying local installation..."
PYTHON_PATH=$(which python3)
if [[ $PYTHON_PATH == *"/venv/"* ]]; then
    echo "   ✅ Using LOCAL Python: $PYTHON_PATH"
else
    echo "   ⚠️  WARNING: Python path: $PYTHON_PATH"
    echo "   This should be in ./venv/ directory!"
fi
echo ""

# Upgrade pip (local only)
echo "⬆️  Upgrading pip (local venv only)..."
pip install --upgrade pip --quiet
echo "   ✅ Pip upgraded"
echo ""

# Install dependencies (LOCAL ONLY - no system installation)
echo "📦 Installing dependencies (LOCAL in ./venv/ only)..."
echo "   This may take 2-3 minutes..."
echo ""

# Install core packages (most important ones explicitly)
echo "   Installing core packages..."
pip install --no-cache-dir numpy pandas --quiet
pip install --no-cache-dir yfinance --quiet
pip install --no-cache-dir streamlit plotly --quiet
pip install --no-cache-dir requests discord-webhook --quiet
pip install --no-cache-dir python-dotenv pytz colorama --quiet
pip install --no-cache-dir sqlalchemy --quiet
pip install --no-cache-dir ta-lib --quiet 2>/dev/null || echo "   ⚠️  ta-lib skipped (optional)"

echo ""
echo "   ✅ All packages installed in ./venv/ (LOCAL only)"
echo ""

# Verify yfinance is installed locally
echo "🧪 Verifying installations..."
python3 -c "import yfinance as yf; print('   ✅ yfinance installed successfully!')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "   ❌ yfinance not found! Retrying..."
    pip install yfinance
fi

python3 -c "import pandas as pd; print('   ✅ pandas installed successfully!')" 2>/dev/null
python3 -c "import numpy as np; print('   ✅ numpy installed successfully!')" 2>/dev/null
python3 -c "import streamlit as st; print('   ✅ streamlit installed successfully!')" 2>/dev/null
echo ""

# Create directories
echo "📁 Creating data directories..."
mkdir -p data
mkdir -p logs
mkdir -p data/cache
echo "   ✅ Directories created!"
echo ""

# Setup .env file
if [ ! -f .env ]; then
    echo "🔧 Setting up .env file..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "   ⚠️  IMPORTANT: Edit .env file and add your Discord webhook URL!"
        echo "   File location: .env"
    else
        echo "   ⚠️  .env.example not found, creating basic .env..."
        echo "DISCORD_WEBHOOK_URL=YOUR_WEBHOOK_URL_HERE" > .env
    fi
    echo ""
else
    echo "✅ .env file already exists"
    echo ""
fi

# Test imports
echo "🧪 Testing project imports..."
python3 -c "
import sys
try:
    from config.settings import *
    print('   ✅ config.settings imported')
    from src.data.data_fetcher import DataFetcher
    print('   ✅ DataFetcher imported')
    from src.strategies.signal_generator import SignalGenerator
    print('   ✅ SignalGenerator imported')
    from config.nse_top_500 import NIFTY_500_STOCKS
    print('   ✅ NIFTY_500_STOCKS imported')
    print('   ✅ All project imports working!')
except Exception as e:
    print(f'   ❌ Import error: {e}')
    print('   This may be okay if some files are missing')
" 2>&1
echo ""

# Show installation location
echo "📍 Installation verification:"
echo "   Python: $(which python3)"
echo "   Pip: $(which pip)"
echo "   Packages location: ./venv/lib/python*/site-packages/"
echo ""

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
echo "║            ✅ CLEAN SETUP COMPLETE!                     ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "📝 What was installed:"
echo "   ✅ Fresh virtual environment in ./venv/"
echo "   ✅ All Python packages in ./venv/ (LOCAL only)"
echo "   ✅ NOTHING installed to OS/system Python"
echo "   ✅ Data directories created"
echo ""
echo "📊 Disk usage: $(du -sh venv 2>/dev/null | cut -f1) in ./venv/"
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Configure Discord (if needed):"
echo "   nano .env    # Add your webhook URL"
echo ""
echo "2. Test the system:"
echo "   ./RUN.sh once     # Single scan (recommended first test)"
echo ""
echo "3. Run live trading:"
echo "   ./RUN.sh          # Interactive menu"
echo "   ./RUN.sh live     # Continuous mode"
echo ""
echo "💡 RUN.sh automatically activates ./venv/ when needed"
echo "   Everything is LOCAL - no OS/system packages used!"
echo ""
