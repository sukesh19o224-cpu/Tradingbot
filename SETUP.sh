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

# Offer to install system packages (makes scipy/numpy faster)
echo "💡 Optional: Install system packages for faster setup?"
echo "   This installs numpy, pandas, scipy from system repos (recommended)"
echo "   Skipping this will install from pip (slower, may need compilers)"
echo ""
read -p "   Install system packages? (y/n) [default: y]: " install_sys
install_sys=${install_sys:-y}

if [[ "$install_sys" =~ ^[Yy]$ ]]; then
    echo ""
    echo "📦 Installing system packages..."
    if command -v apt &> /dev/null; then
        # Debian/Ubuntu
        sudo apt update > /dev/null 2>&1
        sudo apt install -y python3-numpy python3-pandas python3-scipy python3-sklearn > /dev/null 2>&1
        echo "   ✅ System packages installed!"
    elif command -v dnf &> /dev/null; then
        # Fedora
        sudo dnf install -y python3-numpy python3-pandas python3-scipy python3-scikit-learn > /dev/null 2>&1
        echo "   ✅ System packages installed!"
    else
        echo "   ⚠️  Package manager not detected, skipping..."
    fi
    echo ""
fi

# Create virtual environment
echo "🔧 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "   ✅ Virtual environment already exists"
else
    # Use --system-site-packages to access system numpy/scipy
    python3 -m venv venv --system-site-packages
    if [ $? -eq 0 ]; then
        echo "   ✅ Virtual environment created (with system packages access)!"
    else
        echo "   ❌ Failed to create virtual environment"
        echo "   Try: sudo apt install python3-venv"
        exit 1
    fi
fi
echo ""

# Activate virtual environment
echo "📦 Installing remaining dependencies from pip..."
echo "   This may take 1-2 minutes..."
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip > /dev/null 2>&1

# Install dependencies (system packages will be skipped automatically)
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "   ✅ All dependencies installed!"
else
    echo "   ⚠️  Some packages failed to install"
    echo "   Core packages (numpy, pandas, scipy) should work from system install"
    echo "   You can continue and try running the system"
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
