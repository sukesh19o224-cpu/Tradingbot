# 🚀 Super Math Trading System

**Automated swing & positional trading system for Indian stock market (NSE) with advanced mathematical indicators, ML predictions, and Discord alerts.**

---

## ✨ Key Features

- 📊 **200 Stock Coverage** - Scans all NIFTY 200 stocks
- ⚡ **Multi-threaded Scanning** - 10x faster with parallel processing
- 🎯 **0-10 Signal Scoring** - Weighted combination of technical, mathematical, and ML analysis
- 🤖 **Automated Paper Trading** - Virtual portfolio with Kelly Criterion position sizing
- 📱 **Discord Alerts** - Rich embedded notifications for all signals
- 📈 **Live Dashboard** - Streamlit web interface for monitoring
- 🎯 **Strategy Comparison** - Test 3 different strategies simultaneously

---

## 🚀 Quick Start (2 Minutes)

### **1. Setup (One Time)**

**Linux/Mac:**
```bash
./SETUP.sh
```

**Windows:**
```
SETUP.bat
```

This will:
- Install all dependencies
- Create data directories
- Setup .env file for Discord

### **2. Configure Discord**

Edit `.env` file and add your Discord webhook URL:
```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE
```

### **3. Run the System**

**Linux/Mac:**
```bash
./RUN.sh
```

**Windows:**
```
RUN.bat
```

Choose from the menu:
- **Option 1:** Single scan (quick test)
- **Option 2:** Live mode (runs during market hours)
- **Option 3:** Dashboard (view performance)
- **Option 4:** Comparison mode (test 3 strategies)

---

## 📖 How It Works

### **Signal Generation**

Every signal is scored 0-10 based on:

**Technical Analysis (40%):**
- RSI, MACD, EMA crossovers
- Bollinger Bands, ADX, Volume
- Support/Resistance levels

**Mathematical Models (30%):**
- Fibonacci retracements (23.6%, 38.2%, 50%, 61.8%, 78.6%)
- Elliott Wave pattern detection
- Gann angles and Square of 9

**Machine Learning (20%):**
- LSTM price prediction (10-day)
- Confidence scoring
- Statistical fallback

**Volume Analysis (10%):**
- Volume spikes
- OBV (On-Balance Volume)

### **Signal Thresholds**

- **Score ≥ 7.0** → Send Discord alert
- **Score ≥ 8.0** → Good quality signal
- **Score ≥ 8.5** → Excellent quality signal

### **Trade Management**

**Entry:**
- Kelly Criterion position sizing (1/4 Kelly for conservative approach)
- Risk per trade: 2% (swing) or 5% (positional)
- Entry price: Current market price

**Targets:**
- Target 1: 3% (swing) / 8% (positional)
- Target 2: 5% (swing) / 12% (positional)
- Target 3: 8% (swing) / 15% (positional)

**Exit:**
- Stop loss: 2% (swing) / 5% (positional)
- Target hits: Partial exits at each target
- Time-based: 15 days (swing) / 60 days (positional)

---

## 🎯 Strategy Comparison Mode

**Test 3 strategies simultaneously to find the best performer!**

### **The 3 Strategies:**

🟢 **EXCELLENT (≥8.5)**
- Only trades highest quality signals
- Low frequency, high accuracy
- Conservative approach

🟡 **MODERATE (≥8.0)**
- Trades good + excellent signals
- Balanced frequency & accuracy
- Moderate risk

🔵 **ALL SIGNALS (≥7.0)**
- Trades all Discord alerts
- High frequency, varied accuracy
- Aggressive approach

### **How To Use:**

**Option 1 - Automatic (Recommended):**
```bash
./RUN.sh    # Choose Option 4 → Option 1
```

This will:
- Start the system (runs scans continuously)
- Open the comparison dashboard
- Track all 3 strategies in real-time

**Option 2 - Manual (2 terminals):**

Terminal 1:
```bash
./RUN.sh live    # Or: python main.py --mode continuous --enable-comparison
```

Terminal 2:
```bash
./RUN.sh         # Choose Option 4 → Option 3
# Or: python main.py --mode comparison
```

### **What You'll See:**

**Dashboard Features:**
- Side-by-side comparison with rankings (#1, #2, #3)
- Equity curves for all 3 portfolios
- Win rates, P&L, returns comparison
- Open positions and trade history
- Auto-refresh every 60 seconds

### **Expected Insights (After 2 Weeks):**

✅ Which signal quality threshold performs best
✅ Whether quality beats quantity
✅ Realistic win rates and returns
✅ Which strategy fits your risk tolerance

---

## 📊 Discord Alerts

### **How Alerts Work:**

**With Comparison DISABLED (default):**
- Sends alerts for all signals (score ≥ 7.0)
- Paper trading executes trades
- Simple and clean

**With Comparison ENABLED:**
- **Still sends alerts for all signals (≥7.0)** - No change!
- Paper trading continues as normal
- 3 comparison portfolios run silently in background
- View comparison results in dashboard only
- **No duplicate alerts** - Just one alert per signal

### **Alert Content:**

Each Discord alert includes:
- Stock symbol and score (0-10)
- Entry price and targets (3 levels)
- Stop loss and risk-reward ratio
- Technical analysis summary
- Mathematical model signals
- ML prediction (% move, confidence)
- Trade type (SWING or POSITIONAL)

---

## 📁 Project Structure

```
TraDc/
├── SETUP.sh / SETUP.bat           # One-time setup
├── RUN.sh / RUN.bat               # Main run script
├── main.py                         # Main system
├── dashboard.py                    # Main dashboard
├── comparison_dashboard.py         # Comparison dashboard
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
│
├── config/
│   ├── settings.py                 # Main configuration
│   └── nse_universe.py             # Stock lists (NIFTY 200)
│
├── src/
│   ├── data/
│   │   ├── data_fetcher.py         # Yahoo Finance data
│   │   └── fast_scanner.py         # Multi-threaded scanning
│   │
│   ├── indicators/
│   │   ├── technical_indicators.py # RSI, MACD, EMA, etc.
│   │   └── mathematical_indicators.py # Fibonacci, Elliott, Gann
│   │
│   ├── ml_models/
│   │   └── lstm_predictor.py       # LSTM price prediction
│   │
│   ├── strategies/
│   │   └── signal_generator.py     # Signal generation engine
│   │
│   ├── paper_trading/
│   │   └── paper_trader.py         # Virtual portfolio management
│   │
│   ├── alerts/
│   │   └── discord_alerts.py       # Discord notifications
│   │
│   ├── comparison/
│   │   └── portfolio_comparison.py # 3-strategy comparison
│   │
│   └── utils/
│       └── enhanced_filters.py     # Advanced entry filters
│
└── data/
    ├── paper_trades.json           # Paper trading data
    └── portfolio_comparison.json   # Comparison data
```

---

## ⚙️ Configuration

Edit `config/settings.py` to customize:

### **Stock Selection:**
```python
DEFAULT_WATCHLIST = WATCHLIST_AGGRESSIVE  # 200 stocks
# Options: WATCHLIST_CONSERVATIVE (50), WATCHLIST_MODERATE (100)
```

### **Signal Settings:**
```python
MIN_SIGNAL_SCORE = 7.0              # Minimum score for Discord alerts
MIN_TECHNICAL_SCORE = 6.0           # Minimum technical score
MIN_MATHEMATICAL_SCORE = 5.0        # Minimum math score
MIN_ML_CONFIDENCE = 0.6             # ML confidence threshold
```

### **Paper Trading:**
```python
PAPER_TRADING_AUTO_EXECUTE = True   # Auto-execute signals
PAPER_TRADING_CAPITAL = 100000      # Starting capital (₹1 lakh)
MAX_POSITIONS = 10                  # Max concurrent positions
MAX_POSITION_SIZE_PERCENT = 10      # Max 10% per position
```

### **Risk Management:**
```python
SWING_STOP_LOSS_PERCENT = 2.0       # 2% stop for swing trades
POSITIONAL_STOP_LOSS_PERCENT = 5.0  # 5% stop for positional
SWING_TARGET1_PERCENT = 3.0         # First target
SWING_TARGET2_PERCENT = 5.0         # Second target
SWING_TARGET3_PERCENT = 8.0         # Third target
```

### **Scanning:**
```python
SCAN_INTERVAL_MINUTES = 5           # Scan every 5 minutes
POSITION_MONITOR_INTERVAL = 3       # Check positions every 3 min
```

---

## 📈 Expected Performance

Based on professional trader statistics and research:

### **Realistic Targets:**

**Conservative (Score ≥ 8.5):**
- Win Rate: 60-70%
- Monthly Return: 1-2%
- Annual Return: 12-25%
- Trades/Month: 5-10

**Moderate (Score ≥ 8.0):**
- Win Rate: 55-65%
- Monthly Return: 2-3%
- Annual Return: 25-35%
- Trades/Month: 10-20

**Aggressive (Score ≥ 7.0):**
- Win Rate: 50-60%
- Monthly Return: 2-4%
- Annual Return: 25-40%
- Trades/Month: 20-40

**Note:** These are estimates. Your actual results will vary based on market conditions, capital, and execution.

---

## 🔧 Advanced Usage

### **Command Line Options:**

```bash
# Single scan
python main.py --mode once

# Continuous mode (market hours)
python main.py --mode continuous

# With comparison enabled
python main.py --mode continuous --enable-comparison

# Open main dashboard
python main.py --mode dashboard

# Open comparison dashboard
python main.py --mode comparison

# Show performance summary
python main.py --summary

# Test Discord connection
python main.py --test-discord
```

### **Run Multiple Dashboards:**

Terminal 1:
```bash
python main.py --mode continuous --enable-comparison
```

Terminal 2:
```bash
python main.py --mode dashboard    # Main dashboard on port 8501
```

Terminal 3:
```bash
python main.py --mode comparison   # Comparison dashboard on port 8502
```

### **Logs:**

All logs are saved to `logs/` directory:
- `comparison.log` - Comparison system logs
- System outputs to console by default

---

## 🐛 Troubleshooting

### **Discord alerts not working:**
1. Check `.env` file has correct webhook URL
2. Test connection: `./RUN.sh` → Option 6
3. Verify webhook is active in Discord settings

### **No signals generated:**
1. Lower `MIN_SIGNAL_SCORE` in `config/settings.py`
2. Check if market is open (9:15 AM - 3:30 PM IST)
3. Run a single scan to test: `./RUN.sh` → Option 1

### **Slow scanning:**
1. Reduce stock count in `config/settings.py`:
   ```python
   DEFAULT_WATCHLIST = WATCHLIST_MODERATE  # 100 stocks
   ```
2. Increase `SCAN_INTERVAL_MINUTES` to 10 or 15

### **Comparison dashboard shows no data:**
1. Make sure system is running with `--enable-comparison`
2. Wait for at least one signal to be generated
3. Check `data/portfolio_comparison.json` exists

### **Import errors:**
1. Run setup again: `./SETUP.sh`
2. Manually install: `pip install -r requirements.txt`
3. Check Python version: `python --version` (3.8+ required)

---

## 📞 Support

For issues or questions:
1. Check this README
2. Review configuration in `config/settings.py`
3. Test with single scan first: `./RUN.sh` → Option 1
4. Check logs in `logs/` directory

---

## 🎯 Best Practices

1. **Start Small:** Test with single scans before running live
2. **Test Discord:** Always test alerts before going live
3. **Monitor Daily:** Check dashboard daily during testing
4. **Run Comparison:** Use 2-week comparison to find best strategy
5. **Adjust Settings:** Tune based on your results
6. **Paper Trade First:** Never skip paper trading phase
7. **Market Hours:** System works best during market hours (9:15 AM - 3:30 PM IST)

---

## 📜 License

This is a personal trading system. Use at your own risk. Not financial advice.

---

## 🚀 Getting Started Checklist

- [ ] Run `./SETUP.sh` or `SETUP.bat`
- [ ] Configure Discord webhook in `.env`
- [ ] Test Discord: `./RUN.sh` → Option 6
- [ ] Run single scan: `./RUN.sh` → Option 1
- [ ] Check signals and alerts
- [ ] Open dashboard: `./RUN.sh` → Option 3
- [ ] Start live mode: `./RUN.sh` → Option 2
- [ ] (Optional) Run comparison: `./RUN.sh` → Option 4

**Ready to trade? 🎯📈**

---

**"The best traders don't guess. They test, measure, and optimize."**
