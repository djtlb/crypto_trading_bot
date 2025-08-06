"""
Exchange Handler Module
======================

Handles interactions with cryptocurrency exchanges through the CCXT library.
"""

import ccxt
import logging
import time
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("ExchangeHandler")

class ExchangeHandler:
    """Handles all exchange-related operations"""
    
    def __init__(self, exchange_id: str, api_key: Optional[str] = None, api_secret: Optional[str] = None, 
                 sandbox: bool = False, passphrase: Optional[str] = None):
        """
        Initialize the exchange handler
        
        Args:
            exchange_id: The ID of the exchange (e.g., 'binance', 'coinbase', etc.)
            api_key: The API key for the exchange
            api_secret: The API secret for the exchange
            sandbox: Whether to use sandbox/testnet mode
            passphrase: API passphrase (required for Coinbase Pro)
        """
        self.exchange_id = exchange_id
        self.sandbox = sandbox
        
        # Handle different exchange names for Coinbase
        if exchange_id in ['coinbasepro', 'coinbase_pro']:
            # Try different variations of Coinbase exchange names
            possible_names = ['coinbase', 'coinbasepro', 'coinbaseadvanced']
            exchange_class = None
            
            for name in possible_names:
                try:
                    if hasattr(ccxt, name):
                        exchange_class = getattr(ccxt, name)
                        self.exchange_id = name
                        break
                except AttributeError:
                    continue
            
            if not exchange_class:
                # Fallback to a different exchange if Coinbase is not available
                logger.warning("Coinbase not available, falling back to Binance")
                exchange_class = getattr(ccxt, 'binance')
                self.exchange_id = 'binance'
        else:
            # Initialize the exchange
            try:
                exchange_class = getattr(ccxt, exchange_id)
            except AttributeError:
                logger.error(f"Exchange {exchange_id} not supported by CCXT")
                # Fallback to Binance
                exchange_class = getattr(ccxt, 'binance')
                self.exchange_id = 'binance'
        
        exchange_params = {
            'enableRateLimit': True,  # This is important to avoid getting banned
            'sandbox': sandbox,
        }
        
        if api_key and api_secret:
            exchange_params.update({
                'apiKey': api_key,
                'secret': api_secret
            })
            
            # Coinbase Pro requires a passphrase
            if self.exchange_id in ['coinbase', 'coinbasepro', 'coinbaseadvanced'] and passphrase:
                exchange_params['password'] = passphrase
        
        try:
            self.exchange = exchange_class(exchange_params)
            
            # Load markets with error handling
            try:
                self.exchange.load_markets()
                logger.info(f"Connected to {self.exchange_id} exchange (sandbox: {sandbox})")
            except Exception as e:
                logger.warning(f"Failed to load markets for {self.exchange_id}: {str(e)}")
                # Continue without markets loaded - some exchanges work without this
                logger.info(f"Connected to {self.exchange_id} exchange without market data (sandbox: {sandbox})")
                
        except Exception as e:
            logger.error(f"Failed to connect to {self.exchange_id}: {str(e)}")
            raise ConnectionError(f"Could not connect to {self.exchange_id}: {str(e)}")
    
    def get_balance(self, currency: Optional[str] = None) -> Dict:
        """
        Get account balance
        
        Args:
            currency: The currency to get balance for. If None, returns all balances.
            
        Returns:
            A dictionary containing balance information
        """
        try:
            balance = self.exchange.fetch_balance()
            
            if currency:
                if currency in balance:
                    return {currency: balance[currency]}
                else:
                    return {currency: {'free': 0, 'used': 0, 'total': 0}}
            
            return balance
        except Exception as e:
            logger.error(f"Error fetching balance: {str(e)}")
            return {}
    
    def get_ticker(self, symbol: str) -> Dict:
        """
        Get current ticker data for a symbol
        
        Args:
            symbol: The trading symbol (e.g., 'BTC/USDT')
            
        Returns:
            A dictionary containing ticker information
        """
        try:
            return self.exchange.fetch_ticker(symbol)
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {str(e)}")
            return {}
    
    def get_ohlcv(self, symbol: str, timeframe: str = '1m', limit: int = 100) -> List:
        """
        Get OHLCV (Open, High, Low, Close, Volume) data
        
        Args:
            symbol: The trading symbol
            timeframe: The timeframe ('1m', '5m', '1h', '1d', etc.)
            limit: The number of candles to fetch
            
        Returns:
            A list of OHLCV data
        """
        try:
            return self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {str(e)}")
            return []
    
    def create_market_buy_order(self, symbol: str, amount: float) -> Dict:
        """
        Create a market buy order
        
        Args:
            symbol: The trading symbol
            amount: The amount to buy
            
        Returns:
            Order details
        """
        try:
            return self.exchange.create_market_buy_order(symbol, amount)
        except Exception as e:
            logger.error(f"Error creating market buy order for {symbol}: {str(e)}")
            return {}
    
    def create_market_sell_order(self, symbol: str, amount: float) -> Dict:
        """
        Create a market sell order
        
        Args:
            symbol: The trading symbol
            amount: The amount to sell
            
        Returns:
            Order details
        """
        try:
            return self.exchange.create_market_sell_order(symbol, amount)
        except Exception as e:
            logger.error(f"Error creating market sell order for {symbol}: {str(e)}")
            return {}
    
    def create_limit_buy_order(self, symbol: str, amount: float, price: float) -> Dict:
        """
        Create a limit buy order
        
        Args:
            symbol: The trading symbol
            amount: The amount to buy
            price: The price to buy at
            
        Returns:
            Order details
        """
        try:
            return self.exchange.create_limit_buy_order(symbol, amount, price)
        except Exception as e:
            logger.error(f"Error creating limit buy order for {symbol}: {str(e)}")
            return {}
    
    def create_limit_sell_order(self, symbol: str, amount: float, price: float) -> Dict:
        """
        Create a limit sell order
        
        Args:
            symbol: The trading symbol
            amount: The amount to sell
            price: The price to sell at
            
        Returns:
            Order details
        """
        try:
            return self.exchange.create_limit_sell_order(symbol, amount, price)
        except Exception as e:
            logger.error(f"Error creating limit sell order for {symbol}: {str(e)}")
            return {}
    
    def get_order_status(self, order_id: str, symbol: str) -> Dict:
        """
        Get the status of an order
        
        Args:
            order_id: The ID of the order
            symbol: The trading symbol
            
        Returns:
            Order status details
        """
        try:
            return self.exchange.fetch_order(order_id, symbol)
        except Exception as e:
            logger.error(f"Error fetching order status for {order_id}: {str(e)}")
            return {}
    
    def cancel_order(self, order_id: str, symbol: str) -> Dict:
        """
        Cancel an order
        
        Args:
            order_id: The ID of the order
            symbol: The trading symbol
            
        Returns:
            Cancellation details
        """
        try:
            return self.exchange.cancel_order(order_id, symbol)
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {str(e)}")
            return {}
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List:
        """
        Get all open orders
        
        Args:
            symbol: The trading symbol. If None, returns open orders for all symbols.
            
        Returns:
            A list of open orders
        """
        try:
            return self.exchange.fetch_open_orders(symbol)
        except Exception as e:
            logger.error(f"Error fetching open orders: {str(e)}")
            return []
    
    def place_order(self, symbol: str, side: str, amount: float, order_type: str = 'market', price: Optional[float] = None) -> Dict:
        """
        Place an order (buy or sell)
        
        Args:
            symbol: The trading symbol
            side: 'buy' or 'sell'
            amount: The amount to trade
            order_type: 'market' or 'limit'
            price: The price for limit orders
            
        Returns:
            Order details
        """
        try:
            if order_type == 'market':
                if side == 'buy':
                    return self.exchange.create_market_buy_order(symbol, amount)
                else:
                    return self.exchange.create_market_sell_order(symbol, amount)
            elif order_type == 'limit':
                if price is None:
                    raise ValueError("Price is required for limit orders")
                if side == 'buy':
                    return self.exchange.create_limit_buy_order(symbol, amount, price)
                else:
                    return self.exchange.create_limit_sell_order(symbol, amount, price)
            else:
                raise ValueError(f"Unsupported order type: {order_type}")
        except Exception as e:
            logger.error(f"Error placing {side} order for {symbol}: {str(e)}")
            return {}
    
    def get_trade_history(self, symbol: Optional[str] = None, limit: int = 50) -> List:
        """
        Get trade history
        
        Args:
            symbol: The trading symbol. If None, returns trades for all symbols.
            limit: Maximum number of trades to return
            
        Returns:
            A list of trades
        """
        try:
            if symbol:
                return self.exchange.fetch_my_trades(symbol, limit=limit)
            else:
                # Get trades for all symbols
                all_trades = []
                markets = list(self.exchange.markets.keys())[:5]  # Limit to first 5 symbols to avoid rate limits
                for market in markets:
                    try:
                        trades = self.exchange.fetch_my_trades(market, limit=limit//len(markets))
                        all_trades.extend(trades)
                    except Exception as e:
                        logger.warning(f"Failed to fetch trades for {market}: {str(e)}")
                        continue
                return sorted(all_trades, key=lambda x: x.get('timestamp', 0), reverse=True)[:limit]
        except Exception as e:
            logger.error(f"Error fetching trade history: {str(e)}")
            return []
    
    def get_trading_fees(self, symbol: Optional[str] = None) -> Dict:
        """
        Get trading fees for a symbol
        
        Args:
            symbol: The trading symbol
            
        Returns:
            Trading fees information
        """
        try:
            return self.exchange.fetch_trading_fees(symbol)
        except Exception as e:
            logger.error(f"Error fetching trading fees: {str(e)}")
            return {}
    
    def get_deposit_address(self, currency: str) -> Dict:
        """
        Get deposit address for a currency
        
        Args:
            currency: The currency code (e.g., 'BTC', 'ETH')
            
        Returns:
            Deposit address information
        """
        try:
            return self.exchange.fetch_deposit_address(currency)
        except Exception as e:
            logger.error(f"Error fetching deposit address for {currency}: {str(e)}")
            return {}
    
    def is_sandbox(self) -> bool:
        """Check if exchange is in sandbox mode"""
        return self.sandbox
    
    def get_exchange_info(self) -> Dict:
        """Get exchange information and capabilities"""
        try:
            return {
                'id': self.exchange_id,
                'name': self.exchange.name,
                'sandbox': self.sandbox,
                'has': {
                    'fetchBalance': self.exchange.has.get('fetchBalance', False),
                    'fetchTicker': self.exchange.has.get('fetchTicker', False),
                    'fetchOHLCV': self.exchange.has.get('fetchOHLCV', False),
                    'createMarketOrder': self.exchange.has.get('createMarketOrder', False),
                    'createLimitOrder': self.exchange.has.get('createLimitOrder', False),
                    'fetchMyTrades': self.exchange.has.get('fetchMyTrades', False),
                    'fetchOpenOrders': self.exchange.has.get('fetchOpenOrders', False),
                },
                'markets_count': len(self.exchange.markets),
                'rate_limit': self.exchange.rateLimit
            }
        except Exception as e:
            logger.error(f"Error getting exchange info: {str(e)}")
            return {}
