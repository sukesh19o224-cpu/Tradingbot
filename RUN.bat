@echo off
REM 🚀 MAIN RUN SCRIPT - Super Math Trading System (Windows)

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

if "%1"=="once" goto run_single_scan
if "%1"=="scan" goto run_single_scan
if "%1"=="live" goto run_live_mode
if "%1"=="continuous" goto run_live_mode
if "%1"=="dashboard" goto run_dashboard
if "%1"=="dash" goto run_dashboard
if "%1"=="comparison" goto run_comparison_menu
if "%1"=="compare" goto run_comparison_menu
if "%1"=="test" goto run_comparison_menu
if "%1"=="summary" goto show_summary
if "%1"=="stats" goto show_summary
if "%1"=="test-discord" goto test_discord
if "%1"=="discord" goto test_discord

:menu
cls
echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║     🚀 SUPER MATH TRADING SYSTEM                        ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo Choose what to run:
echo.
echo   1) 🎯 Single Scan           - Run one scan cycle
echo   2) 🔄 Live Mode             - Run continuously (recommended)
echo   3) 📊 Dashboard             - Open main dashboard
echo   4) 🎯 Comparison Mode       - Test 3 strategies
echo   5) 📈 Show Summary          - View current performance
echo   6) 🧪 Test Discord          - Test Discord alerts
echo   7) ❌ Exit
echo.
set /p choice="Enter choice (1-7): "

if "%choice%"=="1" goto run_single_scan
if "%choice%"=="2" goto run_live_mode
if "%choice%"=="3" goto run_dashboard
if "%choice%"=="4" goto run_comparison_menu
if "%choice%"=="5" goto show_summary
if "%choice%"=="6" goto test_discord
if "%choice%"=="7" goto exit_script
echo.
echo ❌ Invalid choice. Please enter 1-7.
timeout /t 2 >nul
goto menu

:run_single_scan
cls
echo.
echo 🎯 Running single scan...
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
python main.py --mode once
if not "%1"=="" exit /b
echo.
pause
goto menu

:run_live_mode
cls
echo.
echo 🔄 Starting live continuous mode...
echo.
echo 📌 System will:
echo    • Scan 200 stocks every 5 minutes
echo    • Generate signals and send Discord alerts
echo    • Execute paper trades automatically
echo    • Monitor positions for exits
echo    • Run during market hours (9:15 AM - 3:30 PM IST)
echo.
echo Press Ctrl+C to stop
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
python main.py --mode continuous
if not "%1"=="" exit /b
goto menu

:run_dashboard
cls
echo.
echo 📊 Opening main dashboard...
echo 🌐 Browser: http://localhost:8501
echo.
echo Press Ctrl+C to stop
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
python main.py --mode dashboard
if not "%1"=="" exit /b
goto menu

:run_comparison_menu
cls
echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║     🎯 STRATEGY COMPARISON MODE                         ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo This mode tests 3 strategies simultaneously:
echo   🟢 EXCELLENT  - Only signals ≥ 8.5 (best quality)
echo   🟡 MODERATE   - Signals ≥ 8.0 (good quality)
echo   🔵 ALL        - All signals ≥ 7.0 (all alerts)
echo.
echo Run for 2 weeks to see which performs best!
echo.
echo Choose option:
echo   1) Start comparison + open dashboard (recommended)
echo   2) Run comparison only (system)
echo   3) Open dashboard only (view results)
echo.
set /p comp_choice="Enter choice (1-3): "

if "%comp_choice%"=="1" goto comparison_both
if "%comp_choice%"=="2" goto comparison_system
if "%comp_choice%"=="3" goto comparison_dashboard
echo ❌ Invalid choice
timeout /t 2 >nul
goto run_comparison_menu

:comparison_both
echo.
echo 🚀 Starting comparison system...
echo    This will open 2 windows:
echo    1. System window (running scans)
echo    2. Dashboard window (viewing results)
echo.
echo ⚠️  Keep BOTH windows open!
echo.
pause
start "Trading System" cmd /k python main.py --mode continuous --enable-comparison
timeout /t 3 >nul
python main.py --mode comparison
goto menu

:comparison_system
cls
echo.
echo 🔄 Running comparison system...
echo    Discord alerts: YES (all signals ≥7.0)
echo    Paper trading: YES
echo    Comparison portfolios: YES (3 strategies)
echo.
echo Open dashboard in another window:
echo    RUN.bat → Option 4 → Option 3
echo.
echo Press Ctrl+C to stop
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
python main.py --mode continuous --enable-comparison
goto menu

:comparison_dashboard
cls
echo.
echo 📊 Opening comparison dashboard...
echo 🌐 Browser: http://localhost:8502
echo.
echo ⚠️  Make sure system is running in another window!
echo    (Run option 4→2 in another window if not running)
echo.
echo Press Ctrl+C to stop
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
python main.py --mode comparison
goto menu

:show_summary
cls
echo.
echo 📈 Current Performance Summary
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
python main.py --summary
if not "%1"=="" exit /b
echo.
pause
goto menu

:test_discord
cls
echo.
echo 🧪 Testing Discord connection...
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
python main.py --test-discord
echo.
echo Check your Discord channel for test message!
if not "%1"=="" exit /b
pause
goto menu

:exit_script
cls
echo.
echo 👋 Goodbye!
echo.
exit /b 0
