import ccxt
import logging
from config import EXCHANGE_API_KEY, EXCHANGE_SECRET_KEY, TRADING_PAIR

logger = logging.getLogger(__name__)

class ExchangeInterface:
    def __init__(self):
        self.exchange = ccxt.binance({
            'apiKey': EXCHANGE_API_KEY,
            'secret': EXCHANGE_SECRET_KEY,
            'enableRateLimit': True,
        })
        logger.info(f"Exchange interface initialized for {TRADING_PAIR}")
        
    def get_balance(self):
        """Get current balance in the account"""
        try:
            balance = self.exchange.fetch_balance()
            logger.info(f"Current balance: {balance['total']['USDT']} USDT")
            return balance['total']['USDT']
        except Exception as e:
            logger.error(f"Error getting balance: {str(e)}")
            return 0
            
    def get_market_price(self):
        """Get current market price for the trading pair"""
        try:
            ticker = self.exchange.fetch_ticker(TRADING_PAIR)
            logger.info(f"Current {TRADING_PAIR} price: {ticker['last']}")
            return ticker['last']
        except Exception as e:
            logger.error(f"Error getting market price: {str(e)}")
            return None
            
    def buy(self, amount):
        """Execute a buy order"""
        try:
            order = self.exchange.create_market_buy_order(TRADING_PAIR, amount)
            logger.info(f"Buy order executed: {amount} at market price")
            return order
        except Exception as e:
            logger.error(f"Error executing buy order: {str(e)}")
            return None
            
    def sell(self, amount):
        """Execute a sell order"""
        try:
            order = self.exchange.create_market_sell_order(TRADING_PAIR, amount)
            logger.info(f"Sell order executed: {amount} at market price")
            return order
        except Exception as e:
            logger.error(f"Error executing sell order: {str(e)}")
            return None
            
    def get_historical_data(self, timeframe='1m', limit=100):
        """Get historical OHLCV data"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(TRADING_PAIR, timeframe, limit=limit)
            logger.info(f"Retrieved {len(ohlcv)} historical candles")
            return ohlcv
        except Exception as e:
            logger.error(f"Error retrieving historical data: {str(e)}")
            return []
