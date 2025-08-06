"""
Moving Average Crossover Strategy Module
=======================================

Implements a moving average crossover trading strategy.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("MovingAverageCrossStrategy")

class MovingAverageCrossStrategy:
    """
    Moving Average Crossover Strategy
    
    This strategy uses two moving averages (fast and slow) and generates buy signals
    when the fast MA crosses above the slow MA, and sell signals when the fast MA
    crosses below the slow MA.
    """
    
    def __init__(
        self,
        exchange_handler,
        risk_manager,
        symbol: str = "BTC/USDT",
        trade_amount: float = 100.0,
        use_percentage: float = 90.0,
        fast_ma_period: int = 9,
        slow_ma_period: int = 21,
        ma_type: str = 'ema',
        timeframe: str = '1h'
    ):
        """
        Initialize the moving average crossover strategy
        
        Args:
            exchange_handler: The exchange handler instance
            risk_manager: The risk manager instance
            symbol: The trading symbol
            trade_amount: The amount to trade
            use_percentage: The percentage of trade_amount to use
            fast_ma_period: The period for the fast moving average
            slow_ma_period: The period for the slow moving average
            ma_type: The type of moving average ('sma' or 'ema')
            timeframe: The timeframe for data
        """
        self.exchange_handler = exchange_handler
        self.risk_manager = risk_manager
        self.symbol = symbol
        self.trade_amount = trade_amount
        self.use_percentage = use_percentage
        self.fast_ma_period = fast_ma_period
        self.slow_ma_period = slow_ma_period
        self.ma_type = ma_type
        self.timeframe = timeframe
        
        # State variables
        self.last_checked_candle = None
        self.active_trade_id = None
    
    def execute(self):
        """Execute the strategy"""
        # Get the latest market data
        data = self._get_market_data()
        
        if data.empty:
            logger.warning(f"No data available for {self.symbol}")
            return
        
        # Check if we already have a position
        if self.active_trade_id:
            # Check if the position needs to be managed
            self._manage_position()
        else:
            # Look for a new entry signal
            signal = self.generate_signal(data)
            
            if signal == 'buy':
                self._enter_position()
    
    def generate_signal(self, data) -> str:
        """
        Generate a trading signal based on the strategy
        
        Args:
            data: The market data
            
        Returns:
            A signal string ('buy', 'sell', or 'hold')
        """
        # Calculate indicators
        self._calculate_indicators(data)
        
        # Get the latest candle
        latest_candle = data.iloc[-1]
        
        # Skip if we've already processed this candle
        if self.last_checked_candle is not None and self.last_checked_candle == latest_candle.name:
            return 'hold'
        
        # Update last checked candle
        self.last_checked_candle = latest_candle.name
        
        # Check for buy signal - fast MA crosses above slow MA
        if 'ma_cross_up' in latest_candle and latest_candle['ma_cross_up']:
            return 'buy'
        
        # Check for sell signal - fast MA crosses below slow MA
        if 'ma_cross_down' in latest_candle and latest_candle['ma_cross_down']:
            return 'sell'
        
        return 'hold'
    
    def _get_market_data(self) -> pd.DataFrame:
        """
        Get market data from the exchange
        
        Returns:
            A DataFrame of market data
        """
        # Get OHLCV data
        limit = max(self.fast_ma_period, self.slow_ma_period) * 3  # Get enough data for indicators
        candles = self.exchange_handler.get_ohlcv(self.symbol, self.timeframe, limit=limit)
        
        if not candles:
            return pd.DataFrame()
        
        # Convert to DataFrame
        data = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        data['datetime'] = pd.to_datetime(data['timestamp'], unit='ms')
        data.set_index('datetime', inplace=True)
        
        return data
    
    def _calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate strategy indicators
        
        Args:
            data: The market data
            
        Returns:
            The market data with added indicators
        """
        # Calculate moving averages
        if self.ma_type.lower() == 'ema':
            data['fast_ma'] = data['close'].ewm(span=self.fast_ma_period, adjust=False).mean()
            data['slow_ma'] = data['close'].ewm(span=self.slow_ma_period, adjust=False).mean()
        else:  # default to SMA
            data['fast_ma'] = data['close'].rolling(window=self.fast_ma_period).mean()
            data['slow_ma'] = data['close'].rolling(window=self.slow_ma_period).mean()
        
        # Calculate crossovers
        data['ma_diff'] = data['fast_ma'] - data['slow_ma']
        data['ma_cross_up'] = (data['ma_diff'] > 0) & (data['ma_diff'].shift(1) <= 0)
        data['ma_cross_down'] = (data['ma_diff'] < 0) & (data['ma_diff'].shift(1) >= 0)
        
        return data
    
    def _enter_position(self):
        """Enter a new position based on the strategy signal"""
        # Check if we can open a trade based on risk management
        if not self.risk_manager.can_open_trade(self.symbol, self.trade_amount):
            logger.warning(f"Risk manager prevented opening a trade for {self.symbol}")
            return
        
        # Calculate position size
        position_size = self.risk_manager.calculate_position_size(
            self.symbol, 
            self.trade_amount, 
            self.use_percentage
        )
        
        if position_size <= 0:
            logger.warning(f"Calculated position size for {self.symbol} is <= 0")
            return
        
        logger.info(f"Entering position for {self.symbol} with size {position_size}")
        
        try:
            # Place a market buy order
            order = self.exchange_handler.create_market_buy_order(self.symbol, position_size)
            
            if not order or 'id' not in order:
                logger.error("Failed to place buy order")
                return
            
            # Get the entry price
            ticker = self.exchange_handler.get_ticker(self.symbol)
            entry_price = ticker['last'] if ticker and 'last' in ticker else 0
            
            # Set stop loss and take profit
            stop_loss = self.risk_manager.set_stop_loss(self.symbol, entry_price, position_size)
            take_profit = self.risk_manager.set_take_profit(self.symbol, entry_price, position_size)
            
            # Register the trade with the risk manager
            self.active_trade_id = self.risk_manager.register_trade(
                self.symbol, 
                order, 
                stop_loss, 
                take_profit
            )
            
            logger.info(f"Entered position for {self.symbol} at {entry_price} with trade ID {self.active_trade_id}")
        
        except Exception as e:
            logger.error(f"Error entering position: {str(e)}")
    
    def _manage_position(self):
        """Manage an existing position"""
        # Check if the trade is still active
        if self.active_trade_id not in self.risk_manager.active_trades:
            logger.info(f"Trade {self.active_trade_id} is no longer active")
            self.active_trade_id = None
            return
        
        # Get the latest market data
        data = self._get_market_data()
        
        if data.empty:
            return
        
        # Calculate indicators
        self._calculate_indicators(data)
        
        # Get the latest candle
        latest_candle = data.iloc[-1]
        
        # Check for exit signal
        if 'ma_cross_down' in latest_candle and latest_candle['ma_cross_down']:
            logger.info(f"Exit signal detected for {self.symbol}")
            
            # Close the position
            trade = self.risk_manager.close_trade(self.active_trade_id)
            
            if trade:
                logger.info(f"Closed position for {self.symbol} with trade ID {self.active_trade_id}")
                self.active_trade_id = None
