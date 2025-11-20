# 🚀 QUICK START GUIDE - Fully Automatic Trading System

## ✨ What's New?

Your trading system is now **FULLY AUTOMATIC**! Just run it once and it handles everything:

- ✅ **Automatic EOD Scanning** - Scans all NSE stocks at 4:00 PM daily
- ✅ **4-Tier Ranking System** - Top 50/100/250/500 stocks ranked by quality
- ✅ **Multi-Timeframe Analysis** - Uses both Daily + 15-minute candles
- ✅ **~800 Verified NSE Stocks** - All symbols tested and working
- ✅ **Smart Trading Strategies** - Swing trading for top stocks, positional for others

## 🎯 How It Works

### 1️⃣ AUTOMATIC MODE (Recommended)

```bash
./RUN.sh
# Choose Option 2: ✨ AUTOMATIC Mode
# Select your preferred tier (default: TIER 1 - Top 50 swing trades)
```

**What happens:**
- **9:15 AM**: Loads yesterday's top stocks (from EOD scan)
- **9:15 AM - 3:30 PM**: Scans every 5 minutes, generates signals, sends alerts
- **3:30 PM**: Generates daily summary
- **4:00 PM**: Automatically scans ALL NSE stocks, ranks top 500
- **4:30 PM+**: Sleeps until next market open

**You only need to:** Run it once, then leave it running!

### 2️⃣ Trading Tiers

Choose your trading style:

| Tier | Stocks | Strategy | Style | Risk |
|------|--------|----------|-------|------|
| **TIER 1** | Top 50 | Swing Trading | Aggressive short-term | Higher reward |
| **TIER 2** | Top 100 | Swing + Positional | Balanced mix | Medium |
| **TIER 3** | Top 250 | Positional | Medium-term trends | Conservative |
| **TIER 4** | Top 500 | All Viable | Long-term holds | Most conservative |

**Default:** TIER 1 (Best quality swing trades)

## 📋 First-Time Setup

### Step 1: Run Setup (One-time)
```bash
chmod +x SETUP.sh
./SETUP.sh
```

This installs all packages locally in `./venv/` (no system packages needed).

### Step 2: Configure Discord (Optional)
```bash
nano .env
# Add your Discord webhook URL
```

Test it:
```bash
./RUN.sh
# Choose Option 7: 🧪 Test Discord
```

### Step 3: Run First EOD Scan
```bash
./RUN.sh
# Choose Option 3: 🌙 EOD Scanner
# This creates the initial stock rankings
```

**Time needed:** 5-10 minutes (scans ~800 stocks)

### Step 4: Start Automatic Mode
```bash
./RUN.sh
# Choose Option 2: ✨ AUTOMATIC Mode
# Select tier (default: 1 = Top 50 swing trades)
# Leave it running!
```

## 🎛️ Manual Mode Options

### Single Scan (Testing)
```bash
./RUN.sh once
```
Runs one scan cycle, useful for testing.

### Manual EOD Scan
```bash
./RUN.sh eod
```
Re-scan all stocks manually (normally automatic at 4 PM).

### View Performance
```bash
./RUN.sh summary
```
Shows your paper trading performance.

### Dashboard
```bash
./RUN.sh dashboard
```
Opens web dashboard at http://localhost:8501

## 📊 EOD Scan Results

After EOD scan completes, check:
```bash
cat data/eod_scan_results.json
```

Results include:
- **4 Tiers** of ranked stocks
- **Signal quality scores** (0-10 scale)
- **Entry/target prices**
- **Trading strategies** per tier
- **Statistics** (excellent/good/moderate signals)

## 🔍 What Each Tier Contains

### TIER 1 - Top 50 (Swing Trading)
- **Best quality** signals (score ≥ 8.5)
- **Aggressive** short-term momentum plays
- **Quick profits** (1-3 days holding)
- **Higher risk/reward**
- **Most active monitoring** needed

### TIER 2 - Top 100 (Balanced)
- **Good quality** signals (score ≥ 8.0)
- **Mixed approach** - swing + positional
- **Medium holding** (3-7 days)
- **Balanced risk/reward**

### TIER 3 - Top 250 (Positional)
- **Medium quality** signals (score ≥ 7.0)
- **Positional trades** - follow trends
- **Longer holding** (1-3 weeks)
- **Lower risk** approach

### TIER 4 - Top 500 (Conservative)
- **All viable** signals (score ≥ 5.0)
- **Conservative** long-term plays
- **Extended holding** (1+ months)
- **Lowest risk** strategy

## 🎯 Signal Scoring (0-10 Scale)

Signals are scored based on:
- **Technical Indicators (40%)**: RSI, MACD, EMA, Bollinger Bands, ADX
- **Mathematical Models (30%)**: Fibonacci, Elliott Wave, Gann Theory
- **ML Prediction (20%)**: LSTM price forecasting
- **Volume Analysis (10%)**: Volume trends and confirmation

**Score meanings:**
- **9.0-10.0**: Exceptional - rare, highest confidence
- **8.5-9.0**: Excellent - top quality (Tier 1)
- **8.0-8.5**: Good - solid signals (Tier 2)
- **7.0-8.0**: Moderate - decent trades (Tier 3)
- **5.0-7.0**: Fair - viable but lower confidence (Tier 4)
- **< 5.0**: Weak - filtered out

## ⚙️ Advanced Configuration

### Change Tier Mid-Run
Stop the system (Ctrl+C) and restart with a different tier:
```bash
./RUN.sh
# Choose Option 2
# Select different tier
```

### Custom Scan Interval
Edit `config/settings.py`:
```python
SCAN_INTERVAL_MINUTES = 5  # Default
# Change to 3, 10, 15, etc.
```

### Discord Alert Customization
Edit `config/settings.py`:
```python
MIN_SIGNAL_SCORE = 7.0  # Minimum score to send alert
PAPER_TRADING_AUTO_EXECUTE = True  # Auto-trade on signals
SEND_DAILY_SUMMARY = True  # End-of-day summary
```

## 🐛 Troubleshooting

### No EOD Scan Results
```bash
# Run manual EOD scan first:
./RUN.sh eod
```

### "No verified stocks found"
Make sure `config/nse_verified_stocks.py` exists. Re-run setup if needed.

### Discord Alerts Not Working
```bash
# Test Discord connection:
./RUN.sh
# Option 7: 🧪 Test Discord

# Check .env file has webhook URL:
cat .env | grep DISCORD_WEBHOOK_URL
```

### System Crashes
Check logs:
```bash
tail -f logs/*.log
```

### Market Hours Not Working
System uses IST (Indian Standard Time). Ensure your system time is correct:
```bash
date
# If wrong, it will scan at wrong times
```

## 📈 Performance Expectations

Based on backtesting and market conditions:

| Timeframe | Expected Signals | Approx. Trades |
|-----------|------------------|----------------|
| Daily | 1-3 signals | 5-10 trades/month |
| Weekly | 5-15 signals | 20-30 trades/month |
| Monthly | 20-60 signals | 60-100 trades/month |

**Returns:**
- Conservative target: 8-15% annual (TIER 3-4)
- Moderate target: 12-25% annual (TIER 2)
- Aggressive target: 20-40% annual (TIER 1)

**Note:** Past performance doesn't guarantee future results. Always use proper risk management.

## 🔐 Safety Features

✅ **Paper Trading** - No real money at risk
✅ **Stop Losses** - Automatic exit on losses
✅ **Position Sizing** - Kelly Criterion (1/4 Kelly conservative)
✅ **Risk Management** - Max 2-3% per trade
✅ **Diversification** - Multiple stocks, never all-in

## 🆘 Getting Help

**View System Status:**
```bash
./RUN.sh summary
```

**Check Recent Trades:**
```bash
cat data/paper_trades.json | tail -20
```

**Check EOD Results:**
```bash
cat data/eod_scan_results.json
```

**View Logs:**
```bash
tail -f logs/trading.log
```

## 🚀 Quick Command Reference

```bash
# Setup (one-time)
./SETUP.sh

# Automatic mode (recommended)
./RUN.sh          # Interactive menu
./RUN.sh live     # Direct command

# Other modes
./RUN.sh once     # Single scan
./RUN.sh eod      # Manual EOD scan
./RUN.sh summary  # View performance
./RUN.sh dashboard # Open web dashboard

# Testing
./RUN.sh test-discord  # Test Discord alerts
```

## 📚 File Structure

```
TraDc/
├── SETUP.sh              # One-time setup
├── RUN.sh                # Main run script
├── main.py               # Core system
├── config/
│   ├── settings.py       # Configuration
│   └── nse_verified_stocks.py  # ~800 verified stocks
├── src/
│   ├── data/
│   │   ├── eod_scanner.py      # End-of-day scanner
│   │   ├── nse_stock_fetcher.py # Stock list management
│   │   └── data_fetcher.py     # Yahoo Finance data
│   └── strategies/
│       ├── signal_generator.py     # Signal scoring
│       └── multitimeframe_analyzer.py  # Daily + 15-min analysis
└── data/
    ├── eod_scan_results.json   # Latest EOD scan
    ├── paper_trades.json       # Trade history
    └── portfolio.json          # Current positions
```

## 🎉 You're All Set!

```bash
# Start your fully automatic trading system:
./RUN.sh
# Choose Option 2
# Select TIER 1 (or your preferred tier)
# Let it run!
```

The system will handle everything automatically. Check Discord for alerts!

---

**Questions?** Check README.md for detailed documentation.
