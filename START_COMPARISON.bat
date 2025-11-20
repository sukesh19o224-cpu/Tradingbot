@echo off
REM 🎯 QUICK START: Live Strategy Comparison (Windows)
REM Run this script to start your 2-week comparison experiment

echo ╔═══════════════════════════════════════════════════════════╗
echo ║  🎯 LIVE STRATEGY COMPARISON - QUICK START               ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.
echo This will start comparing 3 trading strategies:
echo   🟢 EXCELLENT (≥8.5)
echo   🟡 MODERATE  (≥8.0)
echo   🔵 ALL       (≥7.0)
echo.

REM Create data directory if it doesn't exist
if not exist data mkdir data

echo ✅ Ready to start!
echo.
echo Choose an option:
echo   1) Run continuous (recommended for 2 weeks)
echo   2) Run single scan (quick test)
echo   3) Open dashboard only
echo   4) Reset comparison data and start fresh
echo.
set /p choice="Enter choice (1-4): "

if "%choice%"=="1" goto continuous
if "%choice%"=="2" goto once
if "%choice%"=="3" goto dashboard
if "%choice%"=="4" goto reset
echo ❌ Invalid choice
exit /b 1

:continuous
echo.
echo 🔄 Starting continuous mode with comparison...
echo.
echo The system will:
echo   • Scan 200 stocks every 5 minutes
echo   • Route signals to 3 portfolios
echo   • Run during market hours (9:15 AM - 3:30 PM IST)
echo.
echo 📊 To view dashboard, open another terminal and run:
echo    python main.py --mode comparison
echo.
echo Press Ctrl+C to stop
echo.
python main.py --mode continuous --enable-comparison
goto end

:once
echo.
echo 🎯 Running single scan with comparison...
python main.py --mode once --enable-comparison
echo.
echo ✅ Scan complete!
echo.
set /p open_dash="Open dashboard now? (y/n): "
if "%open_dash%"=="y" python main.py --mode comparison
goto end

:dashboard
echo.
echo 📊 Opening comparison dashboard...
echo 🌐 Browser will open at: http://localhost:8502
echo.
python main.py --mode comparison
goto end

:reset
echo.
set /p confirm="⚠️ Are you sure? This will delete all comparison data! (yes/no): "
if "%confirm%"=="yes" (
    del /f data\portfolio_comparison.json
    echo ✅ Comparison data reset!
    echo.
    echo Starting fresh...
    python main.py --mode continuous --enable-comparison
) else (
    echo ❌ Reset cancelled
)
goto end

:end
