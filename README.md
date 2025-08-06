# Crypto Trading Bot

**IMPORTANT DISCLAIMER**: This trading bot is for educational purposes only. Cryptocurrency trading involves significant risk of loss. Never risk money you cannot afford to lose. Past performance is not indicative of future results.

## Overview

This is a cryptocurrency trading bot built in Python that supports both centralized exchanges via CCXT and decentralized exchanges via Web3. It implements several trading strategies and includes features for risk management, backtesting, and performance analysis.

## Features

### Centralized Exchange Features
- Connect to multiple cryptocurrency exchanges (Binance, Coinbase Pro, etc.)
- Implement various trading strategies (Moving Average Crossover, RSI, Volatility Breakout)
- Risk management with stop-loss and take-profit functionality
- Backtesting capabilities to test strategies on historical data

### Decentralized Exchange Features
- Connect to EVM-compatible wallets using Web3.py
- Trade on popular DEXes (Uniswap, PancakeSwap, SushiSwap)
- Multi-chain support (Ethereum, BSC, Polygon, Arbitrum)
- Token security validation to detect honeypot scams
- Advanced trading strategies (Sniper, Scalping, Swing, Arbitrage)
- Secure wallet management with encrypted private keys
- RESTful API for integration with other applications

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/crypto_trading_bot.git
cd crypto_trading_bot
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your API keys and trading parameters in the `.env` file:
```bash
cp .env.example .env
# Edit .env file with your exchange API keys and RPC endpoints
```

## Usage

### Centralized Exchange Trading

To start the bot in live trading mode with centralized exchanges:

```bash
python main.py
```

### Decentralized Exchange Trading

To start the DEX trading bot with Flask API and web interface:

```bash
python dex_bot_app.py
```

The DEX bot will start a Flask server that listens on port 5003 by default. You can access:
- Web interface at `http://localhost:5003`
- API endpoints at `http://localhost:5003/api/...`

### Backtesting

To test a strategy on historical data:

```bash
python main.py --backtest
```

## DEX Trading API Endpoints

The DEX bot exposes the following API endpoints:

- `GET /api/status` - Get the current status of the DEX bot
- `POST /api/connect_wallet` - Connect to a wallet using address or private key
- `POST /api/disconnect_wallet` - Disconnect the current wallet
- `GET /api/wallet_balances` - Get token balances for the connected wallet
- `GET /api/validate_token` - Validate a token by checking if it's a honeypot
- `POST /api/start_trade` - Start a trading strategy
- `POST /api/stop_trade` - Stop a running trading strategy
- `GET /api/strategy_status` - Get the status of trading strategies
- `GET /api/supported_chains` - Get list of supported chains
- `GET /api/supported_dexes` - Get list of supported DEXes
- `GET /api/get_gas_price` - Get current gas price for a specific chain

## Supported DEX Strategies

1. **Sniper Strategy**
   - For sniping new token listings with high-speed execution
   - Features gas price boosting to front-run other transactions
   - Configurable auto-sell based on time or profit targets

2. **Scalping Strategy**
   - For short-term trades based on small price movements
   - Uses momentum and volatility indicators for entry/exit
   - Smart gas cost estimation to ensure profitability

3. **Swing Strategy**
   - For medium-term trades based on significant price movements
   - Implements EMA crossover strategy with trend strength evaluation
   - Configurable trailing stops and maximum hold time

4. **Arbitrage Strategy**
   - Exploits price differences between different DEXes
   - Automatically estimates gas costs to ensure profitable trades
   - Supports cross-DEX trades on the same chain

## Configuration

Edit the `.env` file to configure your trading parameters:

```
# Centralized Exchange API credentials
EXCHANGE=binance
API_KEY=your_api_key_here
API_SECRET=your_api_secret_here

# DEX RPC endpoints
ETH_RPC_URL=https://ethereum.publicnode.com
BSC_RPC_URL=https://bsc-dataseed1.binance.org
POLYGON_RPC_URL=https://polygon-rpc.com
ARBITRUM_RPC_URL=https://arb1.arbitrum.io/rpc
```

## Project Structure

```
crypto_trading_bot/
├── main.py                    # Main entry point for CEX trading
├── dex_bot_app.py             # Flask API for DEX trading
├── requirements.txt           # Dependencies
├── .env                       # Configuration
├── templates/                 # Web interface templates
│   └── index.html             # Main dashboard HTML
├── static/                    # Static assets for web interface
│   ├── css/                   # CSS stylesheets
│   │   └── style.css          # Main stylesheet
│   └── js/                    # JavaScript files
│       └── app.js             # Main application logic
├── strategies/                # CEX trading strategies
│   ├── strategy_factory.py
│   ├── volatility_breakout.py
│   ├── moving_average_cross.py
│   └── rsi_strategy.py
├── dex_strategies/            # DEX trading strategies
│   ├── base_strategy.py       # Base strategy class
│   ├── strategy_factory.py    # Strategy factory
│   ├── sniper_strategy.py     # Sniper strategy
│   ├── scalping_strategy.py   # Scalping strategy
│   ├── swing_strategy.py      # Swing strategy
│   └── arbitrage_strategy.py  # Arbitrage strategy
├── dex_utils/                 # DEX utility modules
│   ├── wallet_manager.py      # Secure wallet management
│   ├── dex_connector.py       # DEX interaction
│   └── token_validator.py     # Token security validation
├── utils/                     # Utility modules
│   ├── exchange_handler.py
│   ├── risk_manager.py
│   └── backtester.py
├── logs/                      # Log files
└── data/                      # Data storage
```

## Risk Warning

This bot is provided for educational purposes only. Cryptocurrency trading involves significant risk of loss. Use this bot at your own risk. The creator of this bot does not assume any liability for any losses incurred as a result of using this software.

## Security Notice

When using the DEX trading functionality:
- Never share your private keys or .env file
- Use a dedicated wallet with limited funds for testing
- Enable read-only mode when possible
- Verify all transactions before signing
- Be aware of token security risks and use the token validation features

## License

This project is licensed under the MIT License - see the LICENSE file for details.
