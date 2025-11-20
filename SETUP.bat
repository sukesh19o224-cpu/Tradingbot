@echo off
REM 🚀 ONE-TIME SETUP SCRIPT (Windows)
REM Run this once to set up your trading system

echo ╔══════════════════════════════════════════════════════════╗
echo ║     🚀 SUPER MATH TRADING SYSTEM - SETUP                ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

REM Check Python
echo 📋 Checking Python version...
python --version
echo.

REM Install dependencies
echo 📦 Installing dependencies...
echo    This may take 2-3 minutes...
pip install -q -r requirements.txt
echo    ✅ Dependencies installed!
echo.

REM Create directories
echo 📁 Creating data directories...
if not exist data mkdir data
if not exist logs mkdir logs
echo    ✅ Directories created!
echo.

REM Setup .env file
if not exist .env (
    echo 🔧 Setting up .env file...
    copy .env.example .env
    echo    ⚠️  IMPORTANT: Edit .env file and add your Discord webhook URL!
    echo    File location: .env
    echo.
) else (
    echo ✅ .env file already exists
    echo.
)

REM Test imports
echo 🧪 Testing Python imports...
python -c "from config.settings import *; from src.data.data_fetcher import DataFetcher; print('   ✅ All imports working!')"
echo.

REM Summary
echo ╔══════════════════════════════════════════════════════════╗
echo ║                  ✅ SETUP COMPLETE!                      ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo 📝 Next Steps:
echo.
echo 1. Configure Discord (if not done):
echo    notepad .env    # Add your webhook URL
echo.
echo 2. Test Discord connection:
echo    RUN.bat test-discord
echo.
echo 3. Run the system:
echo    RUN.bat          # Interactive menu
echo    RUN.bat once     # Single scan
echo    RUN.bat live     # Continuous mode
echo.
echo 📖 For full documentation, see: README.md
echo.
pause
