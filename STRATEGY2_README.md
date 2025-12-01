# 🎯 STRATEGY 2 - ULTRA STRICT TRADING SYSTEM

## Overview
Strategy 2 is a **50% Swing / 50% Positional** ultra-strict quality trading system that runs **SEQUENTIALLY** after Strategy 1 to avoid conflicts.

### Key Differences from Strategy 1

| Feature | Strategy 1 (70/30) | Strategy 2 (50/50) |
|---------|-------------------|-------------------|
| **Swing Allocation** | 30% (₹30k) | 50% (₹50k) |
| **Positional Allocation** | 70% (₹70k) | 50% (₹50k) |
| **Min Swing Score** | 8.0/10 | **8.3/10** ⚡ |
| **Min Positional Score** | 7.0/10 | **7.5/10** ⚡ |
| **Min ADX (Swing)** | 30 | **32** ⚡ |
| **Min ADX (Positional)** | 25 | **27** ⚡ |
| **Max Signals/Scan** | 2 swing, 5 pos | **2 swing, 3 pos** ⚡ |
| **Stop Loss** | 3.5% / 4% | **3.3% / 3.8%** (tighter) |
| **Max Positions** | 7 per portfolio | **5 per portfolio** |
| **Discord Alerts** | ✅ Enabled | ❌ Disabled (dashboard only) |
| **Dashboard Port** | 8501 | **8502** |
| **Cache Folder** | data/cache | **data/cache_strategy2** |

## 🚀 How It Works

### Sequential Execution (No Conflicts!)
```
9:00 AM - Strategy 1 starts scanning
9:03 AM - Strategy 1 finishes
9:03 AM - Strategy 2 starts scanning (automatically)
9:06 AM - Strategy 2 finishes
...wait until 9:10 AM...
9:10 AM - Strategy 1 starts again
9:13 AM - Strategy 1 finishes
9:13 AM - Strategy 2 starts again
...and so on
```

### Key Features
- ✅ **ZERO Conflicts** - Separate portfolios, cache, and timing
- ✅ **ELITE Quality Only** - Only top 1-2 signals per scan
- ✅ **Stricter Rules** - Higher scores, tighter stops, stronger trends
- ✅ **Balanced Allocation** - 50% swing, 50% positional
- ✅ **Dashboard Monitoring** - Real-time P&L tracking on port 8502
- ✅ **No Discord Spam** - Silent operation, monitor via dashboard

## 📂 File Structure

### Strategy 2 Files
```
config/
  settings_strategy2.py         # Strategy 2 settings (stricter rules)

src/paper_trading/
  dual_portfolio_strategy2.py   # Strategy 2 portfolio manager

data/
  strategy2_swing_portfolio.json       # Swing positions
  strategy2_positional_portfolio.json  # Positional positions
  strategy2_swing_trades.json          # Swing trade history
  strategy2_positional_trades.json     # Positional trade history
  cache_strategy2/                     # Separate cache folder

main_strategy2.py              # Strategy 2 main runner
dashboard_strategy2.py         # Strategy 2 dashboard (port 8502)
RUN_STRATEGY2.sh              # Run Strategy 2 system
RUN_DASHBOARD_STRATEGY2.sh    # Run Strategy 2 dashboard
```

## 🎮 How to Run

### Step 1: Run Strategy 1 (if not already running)
```bash
bash RUN.sh
```

### Step 2: Run Strategy 2 (in a new terminal)
```bash
bash RUN_STRATEGY2.sh
```

### Step 3: Open Strategy 2 Dashboard (in a new terminal)
```bash
bash RUN_DASHBOARD_STRATEGY2.sh
```

Or directly:
```bash
streamlit run dashboard_strategy2.py --server.port 8502
```

### Access Dashboards
- **Strategy 1 Dashboard**: http://localhost:8501
- **Strategy 2 Dashboard**: http://localhost:8502

## 📊 Strategy 2 Signal Criteria

### Swing Trading (50% capital, ₹50k)
- ✅ Signal Score ≥ **8.3/10** (vs 8.0 in Strategy 1)
- ✅ ADX ≥ **32** (vs 30 in Strategy 1)
- ✅ RSI > **47** (vs 45 in Strategy 1)
- ✅ Volume > **1.7x** average (vs 1.5x in Strategy 1)
- ✅ Max **2 signals** per scan (same as Strategy 1)
- ✅ Hold: **3-7 days**
- ✅ Stop Loss: **3.3%** (vs 3.5% in Strategy 1)
- ✅ Targets: **2.3%, 4.5%, 7%**

### Positional Trading (50% capital, ₹50k)
- ✅ Signal Score ≥ **7.5/10** (vs 7.0 in Strategy 1)
- ✅ ADX ≥ **27** (vs 25 in Strategy 1)
- ✅ RSI > **47** (vs 45 in Strategy 1)
- ✅ Volume > **1.7x** average (vs 1.5x in Strategy 1)
- ✅ Max **3 signals** per scan (vs 5 in Strategy 1)
- ✅ Hold: **5-15 days**
- ✅ Stop Loss: **3.8%** (vs 4% in Strategy 1)
- ✅ Targets: **4.5%, 9%, 14%**

## 🔒 Risk Management (Stricter)

### Position Sizing
- Max Risk Per Trade: **2%** (vs 2.5% in Strategy 1)
- Max Portfolio Risk: **12%** (vs 15% in Strategy 1)
- Max Positions: **5** per portfolio (vs 7 in Strategy 1)
- Max Sector Exposure: **30%** (vs 40% in Strategy 1)

### Circuit Breakers
- Market Crash Threshold: **-3%** (vs -3.5% in Strategy 1)
- Trailing Stop Activation: **+2.5%** (vs +3% in Strategy 1)
- Trailing Stop Distance: **1.5%** (vs 2% in Strategy 1)

## 📈 Expected Performance

### Strategy 2 Characteristics
- **Higher Win Rate** (60%+ expected vs 55% in Strategy 1)
- **Lower Drawdown** (12% max vs 15% in Strategy 1)
- **Fewer Trades** (only elite setups)
- **Higher Quality** (stricter filters = better stocks)
- **More Conservative** (tighter stops, smaller targets)

### Ideal For
- ✅ Risk-averse traders
- ✅ Quality over quantity approach
- ✅ Testing stricter criteria
- ✅ Running parallel to main strategy
- ✅ Comparing different approaches

## 🔧 Configuration

Edit `config/settings_strategy2.py` to adjust:
- Signal score thresholds
- ADX requirements
- Stop loss levels
- Target percentages
- Max positions
- Risk parameters

## 📱 Monitoring

### Dashboard Features (Port 8502)
- 💰 Real-time P&L tracking
- 📊 Portfolio breakdown (50/50 split)
- 📈 Open positions with live prices
- 📜 Trade history
- 🎯 Performance metrics
- ⏱️ Auto-refresh every 5 seconds

### No Discord Alerts
Strategy 2 runs silently without Discord notifications to avoid spam. Monitor via dashboard only.

## ⚠️ Important Notes

### Timing
- Strategy 2 **waits 3 minutes** for Strategy 1 to complete
- Both strategies scan every 10 minutes
- No overlap = no conflicts

### Data Separation
- ✅ Separate portfolio files (`strategy2_*.json`)
- ✅ Separate cache folder (`cache_strategy2/`)
- ✅ Separate dashboard port (8502)
- ✅ No Discord alerts (dashboard only)

### Stock Overlap Prevention
- If a stock is in Strategy 1's swing portfolio, Strategy 2 won't trade it
- If a stock is in Strategy 2's positional portfolio, it won't add it to swing
- Cross-portfolio duplicate prevention built-in

## 🧪 Testing Both Strategies

### Compare Performance
Run both strategies simultaneously and compare:
1. **Win rates** (Strategy 2 should be higher)
2. **Drawdowns** (Strategy 2 should be lower)
3. **Trade frequency** (Strategy 2 will have fewer trades)
4. **Quality** (Strategy 2 targets only elite setups)

### Recommended Approach
- Start with **Strategy 1** (main system, proven)
- Add **Strategy 2** after 1-2 weeks to compare
- Monitor both dashboards side-by-side
- Adjust allocation based on results

## 📞 Support

If you encounter issues:
1. Check both strategies are using different ports (8501 vs 8502)
2. Verify separate cache folders exist
3. Ensure Strategy 2 waits for Strategy 1 to finish
4. Check logs for conflicts

## 🎯 Quick Start Summary

```bash
# Terminal 1: Run Strategy 1 (main)
bash RUN.sh

# Terminal 2: Run Strategy 2 (ultra-strict)
bash RUN_STRATEGY2.sh

# Terminal 3: Strategy 1 Dashboard
streamlit run dashboard.py --server.port 8501

# Terminal 4: Strategy 2 Dashboard
bash RUN_DASHBOARD_STRATEGY2.sh
```

**Dashboard URLs:**
- Strategy 1: http://localhost:8501
- Strategy 2: http://localhost:8502

---

**Strategy 2 is designed for traders who want:**
- 🎯 ELITE quality signals only
- 💎 Higher win rates with lower drawdown
- 🔒 More conservative risk management
- 📊 A/B testing different approaches
- 🚀 Parallel strategy execution without conflicts
