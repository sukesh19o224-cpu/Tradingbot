# 🎯 LIVE STRATEGY COMPARISON GUIDE

## 📊 **What Is This?**

Test **3 different trading strategies** simultaneously in real-time to find which one performs best!

Instead of guessing which signal quality threshold to use, **run them ALL in parallel** and let the data decide.

---

## 🧪 **The 3 Strategies**

Your system will test these 3 approaches simultaneously:

### **🟢 Strategy A: EXCELLENT**
- **Entry Criteria:** Score ≥ 8.5
- **Philosophy:** Only trade the absolute best signals
- **Expected:** Low frequency, high accuracy
- **Best For:** Conservative traders, lower risk

### **🟡 Strategy B: MODERATE**
- **Entry Criteria:** Score ≥ 8.0
- **Philosophy:** Trade good + excellent signals
- **Expected:** Balanced frequency & accuracy
- **Best For:** Balanced approach, moderate risk

### **🔵 Strategy C: ALL SIGNALS**
- **Entry Criteria:** Score ≥ 7.0
- **Philosophy:** Trade all Discord alerts
- **Expected:** High frequency, varied accuracy
- **Best For:** Aggressive traders, capturing all opportunities

---

## 🚀 **How To Use**

### **Step 1: Run Your System with Comparison Enabled**

For **continuous daily running** (recommended for 2 weeks):

```bash
python main.py --mode continuous --enable-comparison
```

This will:
- Scan 200 stocks every 5 minutes during market hours
- Generate signals as usual
- **Automatically route each signal to the appropriate portfolios**
- Track performance for all 3 strategies independently

### **Step 2: Open the Comparison Dashboard**

In a **separate terminal** (while the system is running):

```bash
python main.py --mode comparison
```

Or directly:

```bash
streamlit run comparison_dashboard.py
```

This opens a live dashboard at: **http://localhost:8502**

### **Step 3: Monitor Daily**

Watch the dashboard daily to see:
- Which strategy is winning (ranked #1, #2, #3)
- Win rates for each strategy
- Total returns for each portfolio
- Trade history and open positions

---

## 📈 **Dashboard Features**

### **Performance Overview**
- Side-by-side comparison of all 3 portfolios
- Rank badges showing current leader
- Total returns, win rates, P&L

### **Equity Curves**
- Visual chart showing portfolio growth over time
- Compare all 3 strategies on one chart
- See which strategy is trending upward

### **Performance Metrics Charts**
- Total Return % comparison
- Win Rate % comparison
- Total Trades comparison
- Total P&L comparison

### **Detailed Views**
- Open positions for each strategy
- Complete trade history
- Entry/exit prices, P&L, reasons

### **Auto-Refresh**
- Dashboard updates automatically every 60 seconds
- Toggle auto-refresh on/off
- Adjust refresh interval (10-300 seconds)

---

## 💡 **Usage Scenarios**

### **Scenario 1: 2-Week Live Test (Recommended)**

```bash
# Terminal 1: Run system continuously for 2 weeks
python main.py --mode continuous --enable-comparison

# Terminal 2: Open dashboard to monitor
python main.py --mode comparison
```

**Goal:** Let the system run during market hours for 2 weeks. Check the dashboard daily. After 2 weeks, see which strategy performed best.

### **Scenario 2: Quick Test (1-3 Days)**

Same as above, but run for just a few days to get initial insights.

### **Scenario 3: Single Scan Test**

```bash
# Run one scan cycle
python main.py --mode once --enable-comparison

# Check results in dashboard
python main.py --mode comparison
```

**Note:** Single scans won't give enough data for meaningful comparison. You need at least 5-10 trading days.

---

## 📊 **How Signals Are Routed**

When your system generates a signal with **score 8.6**, it's automatically sent to:
- ✅ **EXCELLENT** portfolio (≥8.5)
- ✅ **MODERATE** portfolio (≥8.0)
- ✅ **ALL** portfolio (≥7.0)

When your system generates a signal with **score 8.3**, it's sent to:
- ❌ **EXCELLENT** portfolio (< 8.5)
- ✅ **MODERATE** portfolio (≥8.0)
- ✅ **ALL** portfolio (≥7.0)

When your system generates a signal with **score 7.2**, it's sent to:
- ❌ **EXCELLENT** portfolio (< 8.5)
- ❌ **MODERATE** portfolio (< 8.0)
- ✅ **ALL** portfolio (≥7.0)

**Each portfolio trades independently** with the same starting capital (₹100,000).

---

## 🎯 **What To Look For**

### **After 1 Week:**
- Which strategy has the highest return?
- Which has the best win rate?
- Which has the most trades?
- Are high-quality signals (EXCELLENT) actually performing better?

### **After 2 Weeks:**
- Is the ranking stable or changing?
- Which strategy has the best risk-adjusted return?
- Is the aggressive approach (ALL) worth the extra trades?
- Can you increase capital allocation to the winning strategy?

### **Key Metrics To Compare:**

1. **Total Return %** - Most important overall metric
2. **Win Rate %** - Consistency indicator
3. **Total P&L** - Absolute profit/loss
4. **Risk-Reward** - Avg Win / Avg Loss ratio
5. **Max Drawdown** - Worst loss from peak
6. **Total Trades** - Frequency indicator

---

## 📁 **Data Storage**

All comparison data is saved to:
```
data/portfolio_comparison.json
```

This file contains:
- All 3 portfolios (capital, positions, history)
- Trade records for each strategy
- Statistics and performance metrics
- Start date and days running

**Do not delete this file** while running your comparison experiment!

To reset and start fresh:
```bash
# Delete the comparison file
rm data/portfolio_comparison.json

# Or use the reset button in the dashboard
```

---

## 🔧 **Advanced Usage**

### **Custom Strategy Thresholds**

Edit `src/comparison/portfolio_comparison.py`:

```python
# Change the thresholds
if score >= 9.0:  # Ultra excellent only
    self._execute_trade('EXCELLENT', signal)

if score >= 7.5:  # Slightly higher moderate
    self._execute_trade('MODERATE', signal)

if score >= 6.5:  # More aggressive ALL
    self._execute_trade('ALL', signal)
```

### **More Than 3 Strategies**

You can add additional portfolios by editing:
```python
self.portfolios = {
    'EXCELLENT': {...},
    'MODERATE': {...},
    'ALL': {...},
    'ULTRA': {...},  # Add new strategy
}
```

Then update `process_signal()` method with new routing logic.

---

## 💬 **Discord Integration**

The comparison system runs **alongside** your Discord alerts. You'll still get Discord notifications for all signals (≥7.0), but now they're also being tested in 3 virtual portfolios.

Your Discord channel will show:
- **All signals** (as usual)
- **Paper trading results** (as usual)

The comparison portfolios run silently in the background and can be viewed in the dashboard.

---

## 🎓 **Expected Results**

### **Hypothesis #1: Quality > Quantity**
- EXCELLENT strategy should have **highest win rate**
- Fewer trades but better quality
- Lower drawdowns
- May have lower total return due to missed opportunities

### **Hypothesis #2: Balance Is Best**
- MODERATE strategy should have **best risk-adjusted returns**
- Good balance of frequency and quality
- Should capture most profitable moves
- May win the 2-week test

### **Hypothesis #3: Aggressive Pays Off**
- ALL strategy should have **most trades**
- Higher total return potential (if market is favorable)
- More false signals and drawdowns
- Higher risk, higher reward

**Let the data decide!** Run the experiment and see which hypothesis is correct for Indian markets.

---

## 📊 **Sample Workflow**

### **Monday Morning:**
```bash
# Start the system
python main.py --mode continuous --enable-comparison

# Open dashboard in browser
python main.py --mode comparison

# Go to: http://localhost:8502
```

### **Daily Check (10 minutes):**
- Open dashboard
- Check current rankings
- Review new trades
- Note any interesting patterns

### **End of Week 1:**
- Analyze 5 days of data
- Note which strategy is leading
- Check win rates and P&L

### **End of Week 2:**
- Full 10-day analysis
- Determine winning strategy
- Make decision: which threshold to use going forward?

### **After Experiment:**
- Keep using the winning threshold
- Continue monitoring
- Re-test every 2-3 months as market conditions change

---

## 🔥 **Pro Tips**

1. **Run During Market Hours Only** - Comparison only makes sense with live data during trading hours (9:15 AM - 3:30 PM IST)

2. **Don't Reset Mid-Experiment** - Let it run for full 2 weeks without resetting data

3. **Check Dashboard Daily** - Stay engaged with the experiment, note patterns

4. **Consider Market Conditions** - Trending markets favor aggressive strategy, choppy markets favor conservative

5. **Look Beyond Returns** - A strategy with 5% return and 70% win rate might be better than 8% return with 40% win rate

6. **Document Your Findings** - Take notes on what you observe each week

7. **Adjust Entry Criteria** - If all 3 strategies perform poorly, your entry criteria might need tuning

8. **Volume Matters** - Need at least 20-30 trades per strategy for statistical significance

---

## ❓ **FAQ**

### **Q: Can I run the comparison without Discord alerts?**
Yes! The comparison runs independently. You can disable Discord in `config/settings.py`:
```python
DISCORD_ENABLED = False
```

### **Q: Does this affect my paper trading?**
No! Paper trading continues separately. The comparison portfolios are virtual.

### **Q: What if I miss some days?**
The system saves all data. You can start/stop anytime. Missing days just extends your experiment timeline.

### **Q: Can I test with different capital amounts?**
Yes! Edit `config/settings.py`:
```python
PAPER_TRADING_CAPITAL = 200000  # Change to ₹2 lakh
```
Each portfolio will start with this amount.

### **Q: How many signals do I need for valid results?**
- **Minimum:** 10 trades per strategy
- **Good:** 20-30 trades per strategy
- **Excellent:** 50+ trades per strategy

With 200 stocks and daily scanning, you should hit 20-30 trades in 2 weeks.

### **Q: What if EXCELLENT portfolio has too few trades?**
Lower the threshold to 8.0 or 8.2. Or extend the experiment to 3-4 weeks.

---

## 🎯 **Success Metrics**

After your 2-week experiment, you should know:

✅ **Which signal quality threshold performs best**
✅ **What win rate you can realistically expect**
✅ **How many trades per week is optimal**
✅ **Whether quality or quantity wins in Indian markets**
✅ **Your system's real-world performance (not backtested!)**

---

## 🚀 **Next Steps**

1. **Start the experiment today!**
   ```bash
   python main.py --mode continuous --enable-comparison
   ```

2. **Open the dashboard**
   ```bash
   python main.py --mode comparison
   ```

3. **Let it run for 2 weeks** during market hours

4. **Analyze results** and choose your winning strategy

5. **Trade confidently** knowing you picked the best approach with real data!

---

**Good luck with your experiment! 🎯📈**

*"In trading, data beats opinions every time."*
