# Multiple Trading Setup - Quick Start Guide

## 🚀 Your $50 Multi-Strategy Trading Bot

Your bot is now configured to make **multiple trades** using a **total budget of $50**. Here's what I've set up for you:

### 📊 Configuration Summary
- **Total Budget**: $50
- **Trade Size**: $3-$8 per trade
- **Max Concurrent Trades**: 10
- **Multiple Strategies**: Volatility Breakout, RSI, Moving Average Cross
- **Multiple Symbols**: BTC/USDT, ETH/USDT, BNB/USDT, ADA/USDT, SOL/USDT
- **Smaller Risk**: 3% stop-loss, 8% take-profit

### 🎯 How It Works
1. **Portfolio Manager** controls your $50 budget
2. **Multiple strategies** run simultaneously on different coins
3. **Smart position sizing** - trades between $3-$8 each
4. **Risk management** - never risk more than your budget allows
5. **Real-time dashboard** to monitor all trades

## 🏃‍♂️ Quick Start

### 1. Check Configuration
```bash
python run_bot.py --check-config
```

### 2. Start Trading (Multiple Strategies)
```bash
python run_bot.py
```

### 3. Alternative: Single Strategy Mode
```bash
python main.py --single
```

### 4. Backtest Mode
```bash
python main.py --backtest
```

## 📈 Dashboard Access

When running, you'll get:
- **Console Dashboard**: Updates every 30 seconds in terminal
- **HTML Dashboard**: `logs/dashboard.html` (open in browser)
- **JSON Data**: `logs/dashboard_data.json` (for analysis)

## 🔧 Key Features Added

### 1. Portfolio Manager (`utils/portfolio_manager.py`)
- Tracks your $50 budget in real-time
- Prevents over-trading
- Manages position sizing
- Daily loss limits

### 2. Multi-Strategy Trader (`utils/multi_strategy_trader.py`)
- Runs 3 strategies simultaneously
- Each strategy monitors different coins
- Automatic trade execution
- Performance tracking

### 3. Enhanced Risk Manager
- Works with portfolio manager
- Dynamic position sizing
- Better trade tracking

### 4. Trading Dashboard (`utils/dashboard.py`)
- Real-time portfolio status
- Strategy performance metrics
- HTML and JSON output

## 📋 Current Settings (.env file)

```env
# Trading parameters
TRADING_SYMBOL=BTC/USDT
TRADE_AMOUNT=5          # Base amount per trade
USE_PERCENTAGE=95       # Use 95% of allocated amount
MAX_TRADES=10           # Max concurrent trades
TOTAL_BUDGET=50         # Your total budget
STOP_LOSS_PERCENTAGE=3  # 3% stop loss
TAKE_PROFIT_PERCENTAGE=8 # 8% take profit

# Strategy parameters
STRATEGY=volatility_breakout
LOOKBACK_PERIOD=14
VOLATILITY_THRESHOLD=2
```

## 🎮 Trading Strategy Mix

1. **Volatility Breakout**: BTC/USDT, ETH/USDT, BNB/USDT
2. **RSI Strategy**: BTC/USDT, ETH/USDT, ADA/USDT  
3. **Moving Average Cross**: BTC/USDT, SOL/USDT

Each strategy runs on different timeframes and intervals to maximize opportunities.

## 🛡️ Safety Features

- **Budget Protection**: Never exceeds your $50 limit
- **Daily Loss Limit**: Stops trading if you lose $10 in a day
- **Position Limits**: Max 10 concurrent trades
- **Smart Sizing**: Smaller trades when budget is low
- **Emergency Stop**: Can close all trades if needed

## 📊 Monitoring Your Trades

### Console Output
```
==================================================
CRYPTO TRADING BOT DASHBOARD
==================================================
Portfolio Status:
  Total Budget: $52.30
  Available Budget: $35.20
  Active Trades: 3/10
  Daily PnL: $2.30

Strategy Performance:
  volatility_breakout: 5 trades, 80% success
  rsi_strategy: 3 trades, 67% success
==================================================
```

### HTML Dashboard
Open `logs/dashboard.html` in your browser for a visual dashboard that auto-refreshes.

## 🚨 Important Notes

1. **Paper Trading**: Set up with testnet/sandbox mode first
2. **Start Small**: The $50 budget is already conservative
3. **Monitor Closely**: Check the dashboard regularly
4. **API Keys**: Make sure your exchange API keys are properly configured
5. **Internet**: Keep stable internet connection for trading

## 🛠️ Troubleshooting

### Check Dependencies
```bash
pip install -r requirements.txt
```

### Verify Configuration
```bash
python run_bot.py --check-config
```

### View Logs
```bash
tail -f logs/trading_bot.log
```

## 📝 What's Different from Before

**BEFORE**: Single strategy, $50 per trade, manual management
**NOW**: Multiple strategies, $3-8 per trade, automated portfolio management

This setup maximizes your chances of finding profitable trades while keeping risk controlled with your $50 budget!
