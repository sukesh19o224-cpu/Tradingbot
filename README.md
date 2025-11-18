# 🚀 Multi-Strategy Trading System V4.0

**An automated trading system for Indian stock market (NSE) with regime detection and multi-strategy support.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📊 Features

### Core Features
- **🎯 Multi-Strategy System**: Momentum, Mean Reversion, and Breakout strategies
- **🔄 Automatic Regime Detection**: Adapts strategy allocation based on market conditions
- **💰 Dynamic Capital Allocation**: Smart capital reallocation between strategies
- **🛡️ Advanced Risk Management**: Per-trade risk limits, drawdown protection, position sizing
- **📊 Real-time Portfolio Tracking**: GUI and CLI interfaces
- **📢 Discord Alerts**: Real-time trade notifications
- **💾 Data Caching**: Optimized scanning (3-5 min → 30 sec)

### V4.0 New Features
- ✅ Comprehensive logging system
- ✅ Error handling with automatic retries
- ✅ SQLite database for trade history
- ✅ Health monitoring and alerts
- ✅ Automatic portfolio backups
- ✅ Configuration validation

## 🎯 Target Performance

- **Monthly Returns**: 8-12%
- **Win Rate**: 55-65%
- **Max Drawdown**: <15%
- **Risk per Trade**: 1.5%

## 📋 Prerequisites

- Python 3.8 or higher
- Active internet connection for market data
- (Optional) Discord webhook for alerts

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download the repository
cd trading_advisory

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file in the project root:

```bash
# Discord webhook for alerts (optional)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE
```

Edit `config/settings.py` to customize:
- Initial capital
- Risk parameters
- Strategy settings
- Market timing

### 3. Run the System

```bash
# Activate virtual environment
source venv/bin/activate

# Run main system
python main_with_news.py
```

### 4. First-Time Setup

When you run the system for the first time:

1. Configuration will be validated automatically
2. Required directories will be created
3. Portfolio will be initialized with your `INITIAL_CAPITAL`
4. Database tables will be set up

### 5. Usage Modes

The system offers two modes:

#### Manual Mode (Default)
Interactive menu with options:
- Run EOD screening
- Scan for opportunities
- View portfolio
- Monitor positions
- Start auto mode

#### Full Auto Mode
Automated trading:
- Morning checks at 9:15 & 9:45 AM
- Live scanning every 10 minutes
- Position monitoring every 3 minutes
- EOD scan at 3:45 PM

```bash
# In manual mode, select option 10 to start auto mode
```

## 📁 Project Structure

```
trading_advisory/
├── main_with_news.py          # Main entry point
├── config/
│   └── settings.py            # Configuration file
├── src/
│   ├── core/                  # Core system
│   │   ├── multi_strategy_manager.py
│   │   └── dynamic_capital_allocator.py
│   ├── strategies/            # Trading strategies
│   │   ├── momentum_strategy.py
│   │   ├── mean_reversion_strategy.py
│   │   └── breakout_strategy.py
│   ├── portfolio_manager/     # Portfolio management
│   │   └── portfolio_manager.py
│   ├── risk_guardian/         # Risk management
│   │   └── risk_manager.py
│   ├── analyzers/             # Market analysis
│   │   ├── regime_detector.py
│   │   ├── sector_tracker.py
│   │   └── correlation_checker.py
│   ├── data_collector/        # Data fetching
│   │   ├── data_cache.py
│   │   └── eod_manager.py
│   ├── alert_dispatcher/      # Notifications
│   │   └── discord_alerts.py
│   ├── backtest/              # Backtesting
│   │   └── backtester.py
│   └── utils/                 # Utilities (NEW)
│       ├── logger.py          # Logging system
│       ├── error_handler.py   # Error handling
│       ├── database.py        # Database operations
│       ├── health_monitor.py  # Health monitoring
│       └── config_validator.py # Config validation
├── data/
│   ├── portfolio.json         # Current portfolio
│   ├── backups/              # Auto backups
│   └── cache/                # Data cache
├── database/
│   └── trading.db            # SQLite database
└── logs/                     # System logs
```

## 🎯 Strategies

### 1. Momentum Strategy
**Best for**: Trending/bull markets

**Entry Criteria**:
- 5-day momentum > 3%
- 20-day momentum > 5%
- Volume 1.5x above average
- Price above MA20 and MA50

**Targets**: 5%, 8%, 12%  
**Stop Loss**: 7%

### 2. Mean Reversion Strategy
**Best for**: Choppy/ranging markets

**Entry Criteria**:
- Price 2-5% below MA20
- RSI < 35 (oversold)
- Above MA50 (quality filter)
- Support bounce confirmation

**Targets**: 3%, 5%, 8%  
**Stop Loss**: 5%

### 3. Breakout Strategy
**Best for**: Consolidation periods

**Entry Criteria**:
- 5+ days consolidation
- Range within 5%
- Volume surge 2x on breakout
- ATR expansion

**Targets**: 6%, 10%, 15%  
**Stop Loss**: 6%

## 📊 Risk Management

### Position Sizing
- **Risk per trade**: 1.5% of capital
- **Max per stock**: 25% of capital
- **Max positions**: 15 concurrent positions

### Stop Losses
- Fixed percentage stops (5-7% depending on strategy)
- Trailing stops after profit (starts at +2%)
- Time stops (3-5 days depending on strategy)

### Portfolio Protection
- **Max daily loss**: 6% (halts trading)
- **Max drawdown**: 15% (pauses trading for 24h)
- **Sector limits**: Max 40% in single sector
- **Correlation check**: Rejects if >70% correlated with existing positions

## 📈 Performance Tracking

### View Performance

```python
# In manual mode, select:
# 4. View Portfolio - Current holdings and P&L
# 5. View Strategy Performance - Per-strategy breakdown
# 6. View Risk Status - Risk metrics
```

### Database Queries

```python
from src.utils.database import get_database

db = get_database()

# Get last 30 days performance
metrics = db.get_performance_metrics(days=30)
print(f"Win Rate: {metrics['win_rate']:.1f}%")
print(f"Total P&L: ₹{metrics['total_pnl']:,.0f}")

# Get strategy breakdown
strategy_perf = db.get_strategy_performance(days=30)
for strat in strategy_perf:
    print(f"{strat['strategy']}: {strat['win_rate']:.1f}% win rate")
```

## 🔧 Configuration Guide

### Quick Tuning

**For MORE opportunities**:
```python
# In config/settings.py
MIN_SCORE = 30  # Lower from 35
MOMENTUM['MIN_5D_MOMENTUM'] = 2.0  # Lower from 3.0
MAX_POSITIONS = 20  # Increase from 15
```

**For BETTER quality (fewer trades)**:
```python
MIN_SCORE = 45  # Raise from 35
MOMENTUM['MIN_5D_MOMENTUM'] = 4.0  # Raise from 3.0
MAX_POSITIONS = 10  # Decrease from 15
```

**For more AGGRESSIVE**:
```python
MAX_RISK_PER_TRADE = 0.02  # 2% from 1.5%
STOP_LOSS_PERCENT = 0.08  # 8% from 6%
```

**For more CONSERVATIVE**:
```python
MAX_RISK_PER_TRADE = 0.01  # 1% from 1.5%
STOP_LOSS_PERCENT = 0.05  # 5% from 6%
MAX_POSITIONS = 5  # Decrease from 15
```

### Risk Profiles

The system includes three pre-configured risk profiles in `src/utils/config_validator.py`:

- **CONSERVATIVE**: 1% risk, 5 positions, 5% stops
- **MODERATE**: 1.5% risk, 10 positions, 6% stops
- **AGGRESSIVE**: 2% risk, 15 positions, 7% stops

## 🏥 Monitoring & Maintenance

### Health Check

```python
from src.utils.health_monitor import get_health_monitor

monitor = get_health_monitor()
monitor.display_health_status()
```

### Backups

Automatic backups are created:
- Before each portfolio save
- Keeps last 30 backups
- Located in `data/backups/`

To restore from backup:
```python
from src.utils.health_monitor import get_backup_manager

backup_mgr = get_backup_manager()
backup_mgr.list_backups()  # View available backups
backup_mgr.restore_latest_backup()  # Restore latest
```

### Logs

Logs are automatically created in `logs/` directory:
- Daily log files with rotation
- Max 10MB per file
- Keeps last 10 files
- Format: `trading_YYYYMMDD.log`

## 🧪 Backtesting

Run backtest on historical data:

```python
from src.backtest.backtester import MultiStrategyBacktester

backtester = MultiStrategyBacktester(initial_capital=100000)

# Define test stocks
test_stocks = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS']

# Run backtest
results = backtester.run_backtest(
    start_date='2024-01-01',
    end_date='2024-12-31',
    test_stocks=test_stocks
)

# View results
print(results['multi_strategy']['total_return'])
```

## 📱 Discord Alerts

### Setup

1. Create a Discord webhook:
   - Open Discord server settings
   - Go to Integrations → Webhooks
   - Create webhook and copy URL

2. Add to `.env` file:
   ```
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE
   ```

3. Test:
   ```python
   from src.alert_dispatcher.discord_alerts import DiscordAlerts
   
   alerter = DiscordAlerts()
   alerter.send_test_alert()
   ```

### Alert Types

- 🟢 **BUY**: New position entered
- 🔴 **SELL**: Position exited (with reason and P&L)
- 📊 **SCAN**: Scan summary with opportunities found
- ⚠️ **RISK**: Risk alerts (max loss, drawdown)

## 🛡️ Error Handling

The system includes robust error handling:

### Automatic Retries
API calls automatically retry 3 times with exponential backoff:
```python
from src.utils.error_handler import retry_on_failure

@retry_on_failure(max_retries=3, delay=2)
def fetch_data(symbol):
    return yf.Ticker(symbol).history(period='1mo')
```

### Error Tracking
All errors are logged and tracked:
```python
from src.utils.error_handler import get_error_tracker

tracker = get_error_tracker()
summary = tracker.get_summary()
print(f"Errors last hour: {summary['total_errors_last_hour']}")
```

## ⚙️ Advanced Features

### Custom Strategy

Create your own strategy by inheriting from base strategy:

```python
from src.strategies.momentum_strategy import MomentumStrategy

class MyStrategy(MomentumStrategy):
    def __init__(self):
        super().__init__()
        self.name = "MY_STRATEGY"
    
    def analyze_stock(self, symbol_ns):
        # Your custom logic
        pass
```

### Data Caching

Caching speeds up scans from 3-5 minutes to 30 seconds:
```python
from src.data_collector.data_cache import get_cache

cache = get_cache()
df = cache.get_data(
    'RELIANCE.NS',
    lambda: yf.Ticker('RELIANCE.NS').history(period='3mo')
)
```

## 🐛 Troubleshooting

### Common Issues

**1. "No data from yfinance"**
- Check internet connection
- Verify symbol format (should end with .NS)
- yfinance may have temporary issues, retry later

**2. "Portfolio file corrupted"**
```python
from src.utils.health_monitor import get_backup_manager
backup_mgr = get_backup_manager()
backup_mgr.restore_latest_backup()
```

**3. "Discord alerts not working"**
- Verify webhook URL in `.env`
- Check Discord server permissions
- Test with: `alerter.send_test_alert()`

**4. "High API error rate"**
- Reduce scan frequency in settings
- Check yfinance service status
- Review error logs in `logs/` directory

### Debug Mode

Enable detailed logging:
```python
from src.utils.logger import get_logger

logger = get_logger()
logger.logger.setLevel(logging.DEBUG)
```

## 📊 Performance Tips

1. **Start Conservative**: Use lower risk settings initially
2. **Monitor First Week**: Watch without taking all trades
3. **Gradual Scaling**: Increase position sizes as you gain confidence
4. **Daily Review**: Check portfolio and logs daily
5. **Weekly Analysis**: Review strategy performance weekly
6. **Monthly Optimization**: Adjust settings based on monthly results

## 🔒 Security

- Never commit `.env` file to version control
- Keep Discord webhooks private
- Regularly backup portfolio data
- Review trade history for unusual activity

## 📚 Additional Resources

- **Yahoo Finance**: Data source
- **NSE India**: Market holidays and trading hours
- **Discord**: Alert notifications

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Additional strategies
- Machine learning integration
- Real-time data feeds (NSE API)
- Options strategies
- Better UI/dashboard

## ⚠️ Disclaimer

**This software is for educational purposes only. Use at your own risk.**

- Past performance does not guarantee future results
- Trading involves risk of loss
- Test thoroughly with paper trading first
- Consult a financial advisor before trading
- Author is not responsible for any financial losses

## 📄 License

MIT License - see LICENSE file for details

## 🙋 Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review configuration with validator
3. Check health status
4. Review this documentation

---

**Version**: 4.0  
**Last Updated**: November 2025  
**Status**: Production Ready ✅

Happy Trading! 🚀📈
