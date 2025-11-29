# 🚀 How to Run the Trading System

## Prerequisites

1. **Set up Discord Webhook** (for alerts):
   ```bash
   # Create a .env file in the project root
   echo "DISCORD_WEBHOOK_URL=your_webhook_url_here" > .env
   ```

2. **Install Dependencies**:
   ```bash
   bash SETUP.sh
   ```

---

## 🧪 MINI TEST (Recommended First!)

**What it does:**
- Scans **Top 100 NSE stocks** (market cap ranked)
- Sends **Discord BUY alerts** for all signals found (swing + positional)
- **NO buying** - Just testing the system
- **NO portfolio management** - Pure scan & alert
- **Sequential scanning** - Safe, one-by-one (no API ban risk)

**How to run:**
```bash
python mini_test.py
```

**What to expect:**
- Scan takes ~2-3 minutes (100 stocks, sequential)
- Discord alerts for both swing and positional signals
- Check Discord to see BUY signals with:
  - Entry price
  - Stop loss
  - 3 targets (T1, T2, T3)
  - Technical indicators
  - Strategy type (swing/positional)

**Use this to:**
- ✅ Verify Discord alerts are working
- ✅ Check signal quality
- ✅ Test system setup
- ✅ Quick feedback on market conditions

---

## 🎯 ONE-TIME SCAN (Full EOD System)

**What it does:**
- Scans **Top 500 NSE stocks** (from EOD ranking)
- Sends **Discord BUY alerts** for qualified signals
- **Auto-buys** in paper portfolio
- **NO continuous monitoring** - Just one scan

**How to run:**
```bash
python main_eod_system.py --mode once
```

**What to expect:**
- Scan takes ~10-15 minutes (500 stocks, sequential)
- Discord alerts for BUY signals
- Auto-executes trades in paper portfolio
- Shows portfolio summary

---

## 🤖 CONTINUOUS MODE (Full Automation!)

**What it does:**
1. **Scans** Top 500 stocks every 10 minutes during market hours (9:15 AM - 3:30 PM)
2. **Sends Discord BUY alerts** when signals found
3. **Auto-buys** in paper trading portfolio
4. **Manages positions** automatically
5. **Sends Discord SELL alerts** when exit conditions met
   - Target hit (profit!)
   - Stop loss hit (cut loss)
   - Time-based exit (no momentum)
6. **EOD ranking** at 3:45 PM (generates Top 500 for next day)
7. **Heartbeat mode** when market closed

**How to run:**
```bash
python main_eod_system.py --mode continuous
```

**What happens:**
- System runs 24/7
- **Market Hours (9:15 AM - 3:30 PM IST)**:
  - Scans Top 500 stocks every 10 minutes
  - Finds new signals → Discord BUY alert → Auto-buys in portfolio
  - Monitors open positions → Discord SELL alert when exit
- **3:45 PM**: EOD ranking (generates fresh Top 500 list)
- **After Hours**: Heartbeat mode (system active, waiting for next day)
- Dual portfolio system:
  - 60% capital for **swing trades** (2-5 days)
  - 40% capital for **positional trades** (10-45 days)

**Discord Alerts You'll Get:**

1. **BUY Signals**:
   - Symbol, Price, Score
   - Entry price, Stop loss, Targets
   - Technical analysis (RSI, MACD, ADX)
   - Risk management details

2. **SELL Signals**:
   - Symbol, Exit price
   - Profit/Loss amount and %
   - Exit reason (Target, Stop Loss, Time)
   - Shares sold

3. **Daily Summary**:
   - Total portfolio value
   - Today's return
   - Open positions
   - Win rate
   - Swing vs Positional performance

---

## 📱 Your Role (Manual Trading)

The system gives you **BUY and SELL signals via Discord**.

**You manually execute in real broker:**

1. **When BUY alert comes:**
   - Open your broker app
   - Buy the stock at the given price
   - Set stop loss at the given price
   - Set targets at T1, T2, T3

2. **When SELL alert comes:**
   - Open your broker app
   - Sell the stock
   - The alert tells you why (Target hit / Stop loss / Time)

**The paper trading portfolio is just for tracking!**
- It helps the system learn and improve
- You see performance metrics
- But YOU make real trades manually

---

## 🎯 Recommended Workflow

### First Time Setup:

1. **Day 1: Mini Test** (2-3 minutes)
   ```bash
   python mini_test.py
   ```
   - Check if signals make sense
   - Verify Discord alerts work
   - Review signal quality
   - Quick test of system

2. **Day 2: One-Time Scan** (10-15 minutes)
   ```bash
   python main_eod_system.py --mode once
   ```
   - Test with full 500 stocks
   - Check auto-buying in paper portfolio
   - Review portfolio summary

3. **Day 3: Continuous Mode**
   ```bash
   python main_eod_system.py --mode continuous
   ```
   - Let it run during market hours
   - Watch Discord for signals
   - Manually trade based on alerts

### Daily Routine:

1. **Before 9:00 AM** - Start continuous mode:
   ```bash
   python main_eod_system.py --mode continuous
   ```

2. **During Market Hours (9:15 AM - 3:30 PM)**:
   - Watch Discord for BUY/SELL alerts
   - Execute trades manually in broker
   - System auto-manages paper portfolio

3. **3:45 PM**:
   - System runs EOD ranking (generates Top 500 for next day)

4. **After Market Close**:
   - Review daily summary in Discord
   - System stays in heartbeat mode (can keep running overnight)

---

## 📊 Key Differences

| Feature | Mini Test | One-Time Scan | Continuous Mode |
|---------|-----------|---------------|----------------|
| **Stocks Scanned** | 100 | 500 | 500 |
| **Frequency** | One-time | One-time | Every 10 min |
| **Discord BUY Alerts** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Discord SELL Alerts** | ❌ No | ❌ No | ✅ Yes |
| **Auto-Buy Portfolio** | ❌ No | ✅ Yes | ✅ Yes |
| **Position Management** | ❌ No | ✅ Yes | ✅ Yes |
| **Daily Summary** | ❌ No | ✅ Yes | ✅ Yes |
| **EOD Ranking** | ❌ No | ❌ No | ✅ Yes (3:45 PM) |
| **Duration** | 2-3 min | 10-15 min | 24/7 |
| **Purpose** | Quick test | Full test | Production |

---

## 💡 Tips

1. **Always start with test mode** to verify everything works

2. **Check Discord webhook** before running:
   ```bash
   python src/alerts/discord_alerts.py
   ```

3. **Monitor the first few signals carefully** to understand quality

4. **Use stop losses religiously** - The system calculates them for a reason!

5. **Don't chase signals** - If you miss entry price, wait for next signal

6. **Trust the exits** - When system says SELL, it has analyzed the position

---

## 🔧 Troubleshooting

**No Discord alerts?**
- Check `.env` file has `DISCORD_WEBHOOK_URL`
- Test with: `python src/alerts/discord_alerts.py`

**No signals found?**
- Market conditions may not be favorable
- Try during high volatility times (10 AM - 2 PM)
- Check if market is trending (bull market = more signals)

**Too many signals?**
- System will prioritize by score
- Focus on score >= 7.0 for best quality
- Adjust thresholds in `config/settings.py` if needed

**System stuck?**
- Check internet connection
- Yahoo Finance may be slow
- Reduce threads in settings if needed

---

## 📞 Need Help?

Check the logs in terminal - they show exactly what's happening!

Good luck! 🚀
