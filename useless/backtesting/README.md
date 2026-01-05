# Positional Trading Backtester

EXACT replica of your positional trading system for historical backtesting.

## Features

✅ **Exact System Logic**
- 50/40/10 progressive exits (T1/T2/T3)
- Profit locking (+2% after T1, +3.5% after T2)
- Adaptive trailing stops (1.8x ATR, tightens to 1.0x after T2)
- ATR-based stop loss (1.5-2.5% range)
- Exact Zerodha trading charges
- 10-day max holding period

✅ **Data & Scanning**
- 1-hour candle data (accurate intraday timing)
- Top 1000 NSE stocks
- Multi-timeframe analysis
- Signal score filtering (≥7.7)

## Files

1. **`positional_backtest.py`** - Core backtester (EXACT system replica)
2. **`backtest_runner.py`** - Scanner + Backtester (scans Top 1000)

## Usage

### Option 1: Backtest a Single Known Signal

```python
from src.backtesting.positional_backtest import PositionalBacktester
from datetime import datetime

# Create backtester
backtester = PositionalBacktester(initial_capital=50000)

# Backtest a signal
result = backtester.backtest_symbol(
    symbol='RELIANCE.NS',
    entry_date=datetime(2024, 12, 1, 9, 15),
    entry_price=1250.0,
    atr=30.0,
    signal_score=8.5,
    days_forward=15
)

# Print results
print(f"Total P&L: ₹{result['total_pnl']:.2f}")
for trade in result['trades']:
    print(f"{trade['reason']}: ₹{trade['pnl']:.2f}")
```

### Option 2: Scan & Backtest Top 1000 Stocks

```python
from src.backtesting.backtest_runner import BacktestRunner
from datetime import datetime

# Create runner
runner = BacktestRunner(initial_capital=50000)

# Scan for signals on a specific date
signals = runner.scan_for_signals(
    stocks=NSE_TOP_1000[:100],  # Test with Top 100
    scan_date=datetime(2024, 11, 15)
)

# Backtest all signals found
if signals:
    results = runner.backtest_signals(signals, days_forward=15)
    summary = runner._aggregate_results(signals, results)
```

### Option 3: Historical Backtest (Multiple Dates)

```python
from src.backtesting.backtest_runner import BacktestRunner
from datetime import datetime

runner = BacktestRunner(initial_capital=50000)

# Backtest 1 month with weekly scans
results = runner.run_historical_backtest(
    start_date=datetime(2024, 11, 1),
    end_date=datetime(2024, 11, 30),
    stocks=NSE_TOP_1000[:100],  # Top 100 for testing
    scan_frequency_days=7  # Scan weekly
)

print(f"Total P&L: ₹{results['total_pnl']:,.2f}")
print(f"Win Rate: {results['win_rate']:.1f}%")
```

## Quick Start - Test Run

Run the built-in test:

```bash
cd /media/sukesh-k/Storage/Dcode\ folder\ /new\ Tr/TraDc
python3 src/backtesting/positional_backtest.py  # Test single trade
python3 src/backtesting/backtest_runner.py      # Test scan & backtest
```

## Settings

All settings from `config/settings.py` are automatically used:
- `POSITIONAL_TARGETS` = [2.5%, 4%, 6%]
- `MIN_SIGNAL_SCORE` = 7.7
- `ATR_MULTIPLIER_POSITIONAL` = 1.8
- `POSITIONAL_HOLD_DAYS_MAX` = 10

## Output

The backtester provides:
- Trade-by-trade P&L
- Exit reasons (TARGET_1/2/3, STOP_LOSS, MAX_HOLDING)
- Holding days
- Trading charges breakdown
- Win/loss statistics
- Best/worst trades
- Exit reason distribution

## Example Output

```
TARGET_1:
  Exit Price: ₹1281.25
  Exit Date: 2024-12-02 03:45:00
  Shares: 4/8
  P&L: ₹114.99 (2.50%)
  Holding: 0 days
  Partial Exit: 50%

Total P&L: ₹329.84
Win Rate: 100.0%
```

## Notes

- Uses 1-hour candles for accurate timing (2 years of history available)
- Handles timezone issues automatically
- Exact Zerodha charges calculation
- Conservative approach for ambiguous cases
- Same logic as your live paper trading system

## What's Next?

1. **Test with Known Signals**: Run backtests on stocks you know performed well
2. **Optimize Scan Date**: Try different dates to find signals
3. **Full Historical Test**: Run on Top 1000 for multiple months
4. **Analyze Results**: Compare with your paper trading performance

Happy Backtesting! 🚀
