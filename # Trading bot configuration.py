# Trading bot configuration

# API credentials (replace with your actual API keys)
EXCHANGE_API_KEY = "your_api_key_here"
EXCHANGE_SECRET_KEY = "your_secret_key_here"

# Trading parameters
TRADING_PAIR = "BTC/USDT"  # The cryptocurrency pair to trade
INITIAL_BALANCE = 20.0  # Starting capital in USD
TARGET_BALANCE = 200.0  # Target balance in USD
POSITION_SIZE = 0.95  # Percentage of balance to use per trade
STOP_LOSS_PERCENTAGE = 0.02  # 2% stop loss
TAKE_PROFIT_PERCENTAGE = 0.05  # 5% take profit

# Strategy parameters
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
EMA_FAST = 12
EMA_SLOW = 26
MACD_SIGNAL = 9

# Risk management
MAX_DAILY_TRADES = 10
MAX_LOSS_PERCENTAGE = 0.15  # Maximum 15% loss before stopping
