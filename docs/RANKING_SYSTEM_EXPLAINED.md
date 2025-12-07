# 🏆 Signal Ranking System - Complete Explanation

## 📊 How the System Ranks Stocks

When the scanner finds 10 stocks, it ranks them by **Signal Score** (0-10 scale) and takes the **top 5 for positional** and **top 2 for swing**.

---

## 🎯 Signal Score Calculation (0-10 Scale)

The signal score is calculated using a **weighted formula** that combines multiple factors:

### Formula:

```python
# WITH Intraday Data (15-minute):
Signal Score = (Technical Score × 50%) + 
               (Trend Score × 30%) + 
               (Intraday Timing × 10%) + 
               (Mathematical Score × 10%)

# WITHOUT Intraday Data (Daily only):
Signal Score = (Technical Score × 50%) + 
               (Trend Score × 40%) + 
               (Mathematical Score × 10%)
```

### Strategic Boost for Mean Reversion:
```python
if signal_type == 'MEAN_REVERSION':
    if quality_score >= 60:
        Signal Score += 0.5  # High quality boost
    elif quality_score >= 50:
        Signal Score += 0.3  # Good quality boost
```

---

## 📈 Component Breakdown

### 1. **Technical Score (50% weight)** - PRIMARY EDGE

This is calculated from **7 technical indicators**:

| Indicator | Max Points | What It Checks |
|-----------|-----------|----------------|
| **EMA Trend** | 1.0 | Price > EMA21 > EMA50 = Bullish |
| **RSI Signal** | 1.0 | RSI 50-70 = Bullish, <30 = Oversold |
| **MACD Signal** | 1.0 | MACD > Signal = Bullish |
| **Bollinger Bands** | 1.0 | Bounce from lower band = Buy |
| **ADX Trend Strength** | 1.0 | ADX >25 + +DI > -DI = Strong uptrend |
| **Volume Signal** | 1.0 | Volume >2x average = High interest |
| **Momentum** | 1.0 | 5-day >3%, 20-day >5% = Strong |

**Total:** 7 points → Converted to 0-10 scale

**Example:**
```
Stock A scores:
- EMA Trend: 1.0 (Bullish)
- RSI: 1.0 (62 - good momentum)
- MACD: 1.2 (Bullish crossover - bonus!)
- BB: 0.5 (Neutral)
- ADX: 1.0 (Strong uptrend)
- Volume: 1.0 (High volume)
- Momentum: 0.7 (Positive)

Raw Score: 6.4 / 7.0
Technical Score: (6.4 / 7.0) × 10 = 9.1/10 ✅
```

### 2. **Trend Score (30-40% weight)**

Based on **EMA alignment**:

| Condition | Trend | Score |
|-----------|-------|-------|
| Price > EMA50 > EMA200 | STRONG_UPTREND | 10/10 |
| Price > EMA50 | UPTREND | 8/10 |
| Price > EMA200 | WEAK_UPTREND | 6/10 |
| Price < EMA50 < EMA200 | STRONG_DOWNTREND | 2/10 |
| Other | SIDEWAYS | 5/10 |

**Example:**
```
Stock A:
Price: ₹2,500
EMA50: ₹2,400
EMA200: ₹2,300

Price > EMA50 > EMA200 → STRONG_UPTREND
Trend Score: 10/10 ✅
```

### 3. **Intraday Timing (10% weight)** - If Available

Based on **15-minute entry signals**:

| Entry Signals | Timing | Score |
|---------------|--------|-------|
| 3+ signals | EXCELLENT | 10/10 |
| 2 signals | GOOD | 7.5/10 |
| 1 signal | FAIR | 5/10 |
| 0 signals | POOR | 2/10 |

**Entry Signals Checked:**
- RSI oversold (<35 on 15m)
- MACD bullish crossover
- Price above VWAP
- Recent breakout detected

**Example:**
```
Stock A (15-minute):
✅ RSI oversold: Yes (32)
✅ MACD bullish: Yes
❌ Above VWAP: No
✅ Breakout: Yes

3 signals → EXCELLENT
Intraday Score: 10/10 ✅
```

### 4. **Mathematical Score (10% weight)** - Context Only

Based on **Fibonacci & Elliott Wave**:

| Factor | Points |
|--------|--------|
| Fibonacci support/resistance | 0-5 |
| Elliott Wave pattern | 0-5 |

**Example:**
```
Stock A:
- Fibonacci: Price at 38.2% retracement (support) → 4/5
- Elliott Wave: Wave 3 detected (bullish) → 4/5

Mathematical Score: 8/10 ✅
```

---

## 🧮 Complete Calculation Example

### Stock A: RELIANCE.NS

**Step 1: Calculate Components**
```
Technical Score: 9.1/10 (from 7 indicators)
Trend Score: 10/10 (Strong uptrend)
Intraday Score: 10/10 (3 entry signals)
Mathematical Score: 8/10 (Fibonacci + Elliott)
```

**Step 2: Apply Weights**
```
Signal Score = (9.1 × 0.50) + (10 × 0.30) + (10 × 0.10) + (8 × 0.10)
             = 4.55 + 3.0 + 1.0 + 0.8
             = 9.35/10
```

**Step 3: Check for Mean Reversion Boost**
```
Signal Type: MEAN_REVERSION
Quality Score: 85/100 (>60)
Boost: +0.5

Final Score: 9.35 + 0.5 = 9.85/10 ✅
```

---

## 🏆 Ranking Process

### Step 1: Filter by Quality

**Positional:**
- Mean Reversion: Quality ≥50
- Momentum: Quality ≥60
- Breakout: Quality ≥60

**Swing:**
- All types: Quality ≥70 (A+ only)

### Step 2: Sort by Score

```python
# Sort signals by score (highest first)
positional_signals = sorted(signals, key=lambda x: x['score'], reverse=True)
swing_signals = sorted(signals, key=lambda x: x['score'], reverse=True)
```

### Step 3: Take Top N

```python
# Take top 5 positional, top 2 swing
positional_signals = positional_signals[:5]
swing_signals = swing_signals[:2]
```

---

## 📊 Example Scan Result

**10 Stocks Found:**

| Rank | Symbol | Type | Score | Quality | Action |
|------|--------|------|-------|---------|--------|
| 1 | RELIANCE.NS | MR | 9.85 | 85 | ✅ **POSITIONAL** |
| 2 | TCS.NS | MOM | 9.20 | 78 | ✅ **POSITIONAL** |
| 3 | INFY.NS | MOM | 8.90 | 72 | ✅ **POSITIONAL** |
| 4 | HDFCBANK.NS | MR | 8.50 | 68 | ✅ **POSITIONAL** |
| 5 | ICICIBANK.NS | MOM | 8.20 | 65 | ✅ **POSITIONAL** |
| 6 | SBIN.NS | MOM | 7.90 | 62 | ❌ Filtered (top 5 full) |
| 7 | TATAMOTORS.NS | MOM | 7.50 | 58 | ❌ Filtered (top 5 full) |
| 8 | WIPRO.NS | MR | 7.20 | 52 | ❌ Filtered (top 5 full) |
| 9 | LT.NS | MOM | 6.80 | 48 | ❌ Rejected (quality <60) |
| 10 | AXISBANK.NS | MR | 6.50 | 45 | ❌ Rejected (quality <50) |

**Final Selection:**
- **Positional:** 5 stocks (ranks 1-5)
- **Swing:** 0 stocks (none met quality ≥70 threshold)

---

## 🎯 Quality Scoring (0-100 Scale)

Each signal type has its own quality check:

### Mean Reversion Quality (100 points)

| Factor | Max Points | Requirement |
|--------|-----------|-------------|
| RSI in reversal zone (30-50) | 30 | RSI 30-40 = 30pts, 40-50 = 20pts |
| Above 50-day MA (uptrend) | 25 | Must be above |
| Volume spike (1.3x+) | 20 | 2x+ = 20pts, 1.5x = 15pts |
| MACD turning bullish | 15 | Histogram >0 |
| RS Rating vs Nifty | 15 | RS >110 = 15pts, >100 = 10pts |

**Pass Threshold:** 50+ points

### Momentum Quality (100 points)

| Factor | Max Points | Requirement |
|--------|-----------|-------------|
| RSI in momentum zone (50-68) | 25 | RSI 60-68 = 25pts |
| Above 50-day MA | 20 | Must be above |
| ADX strong trend (≥22) | 30 | ADX ≥40 = 30pts, ≥22 = 25pts |
| Within 12% of 20-MA | 15 | Not extended |
| Volume confirmation (1.3x+) | 20 | 2x+ = 20pts, 1.5x = 15pts |
| MACD bullish | 10 | Histogram >0 |
| RS Rating vs Nifty | 20 | RS >120 = 20pts, >110 = 15pts |

**Pass Threshold:** 60+ points

### Breakout Quality (100 points)

| Factor | Max Points | Requirement |
|--------|-----------|-------------|
| RSI in breakout zone (55-70) | 25 | RSI 60-68 = 25pts |
| Above 50-day MA | 25 | Must be above |
| ADX strong trend (≥25) | 30 | ADX ≥30 = 30pts, ≥25 = 25pts |
| Explosive volume (2x+) | 25 | 2.5x+ = 25pts, 2x = 20pts |
| MACD positive | 15 | Histogram >0 |
| RS Rating vs Nifty | 20 | RS >120 = 20pts |

**Pass Threshold:** 60+ points

---

## 🔑 Key Takeaways

1. **Signal Score (0-10)** determines ranking
2. **Quality Score (0-100)** determines if signal passes filters
3. **Technical indicators (50%)** are the primary edge
4. **Trend structure (30-40%)** confirms direction
5. **Mean Reversion gets boost** (+0.3 to +0.5) if quality is good
6. **Top 5 positional, Top 2 swing** are selected after ranking

---

## 📱 What You See in Discord

```
🔥 BUY SIGNAL - RELIANCE.NS

Signal Score: 9.85/10 🔥
Strategy: 🔄 MEAN_REVERSION
Quality Score: 85/100 ✅ (min 50)

This stock ranked #1 out of 10 qualified stocks!
```

---

**Last Updated:** December 7, 2025  
**System Version:** 2.0
