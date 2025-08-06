"""
Volatility Breakout Strategy Module
=================================

Implements a volatility breakout trading strategy.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("VolatilityBreakoutStrategy")

class VolatilityBreakoutStrategy:
    """
    Volatility Breakout Strategy
    
    This strategy identifies periods of low volatility (consolidation)
    and enters a position when price breaks out of the consolidation range.
    It uses the Average True Range (ATR) indicator to measure volatility.
    """
    
    def __init__(
        self,
        exchange_handler,
        risk_manager,
        symbol: str = "BTC/USDT",
        trade_amount: float = 100.0,
        use_percentage: float = 90.0,
        lookback_period: int = 14,
        volatility_threshold: float = 2.0,
        timeframe: str = '1h'
    ):
        """
        Initialize the volatility breakout strategy
        
        Args:
            exchange_handler: The exchange handler instance
            risk_manager: The risk manager instance
            symbol: The trading symbol
            trade_amount: The amount to trade
            use_percentage: The percentage of trade_amount to use
            lookback_period: The lookback period for calculating ATR
            volatility_threshold: The volatility threshold for triggering trades
            timeframe: The timeframe for data
        """
        self.exchange_handler = exchange_handler
        self.risk_manager = risk_manager
        self.symbol = symbol
        self.trade_amount = trade_amount
        self.use_percentage = use_percentage
        self.lookback_period = lookback_period
        self.volatility_threshold = volatility_threshold
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
        
        # Check for buy signal - breakout detected
        if 'volatility_breakout' in latest_candle and latest_candle['volatility_breakout']:
            return 'buy'
        
        # Check for sell signal - can be implemented based on your criteria
        if 'exit_signal' in latest_candle and latest_candle['exit_signal']:
            return 'sell'
        
        return 'hold'
    
    def _get_market_data(self) -> pd.DataFrame:
        """
        Get market data from the exchange
        
        Returns:
            A DataFrame of market data
        """
        # Get OHLCV data
        candles = self.exchange_handler.get_ohlcv(self.symbol, self.timeframe, limit=self.lookback_period * 2)
        
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
        # Calculate ATR (Average True Range)
        data['tr1'] = abs(data['high'] - data['low'])
        data['tr2'] = abs(data['high'] - data['close'].shift(1))
        data['tr3'] = abs(data['low'] - data['close'].shift(1))
        data['tr'] = data[['tr1', 'tr2', 'tr3']].max(axis=1)
        data['atr'] = data['tr'].rolling(window=self.lookback_period).mean()
        
        # Calculate volatility ratio
        data['volatility_ratio'] = data['tr'] / data['atr']
        
        # Identify consolidation periods (low volatility)
        data['consolidation'] = data['volatility_ratio'] < 0.8
        
        # Identify breakouts (high volatility following consolidation)
        data['volatility_breakout'] = (data['volatility_ratio'] > self.volatility_threshold) & \
                                     (data['consolidation'].shift(1))
        
        # Identify potential exit signals
        data['exit_signal'] = (data['volatility_ratio'] > self.volatility_threshold) & \
                             (data['close'] < data['close'].shift(1))
        
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
        if 'exit_signal' in latest_candle and latest_candle['exit_signal']:
            logger.info(f"Exit signal detected for {self.symbol}")
            
            # Close the position
            trade = self.risk_manager.close_trade(self.active_trade_id)
            
            if trade:
                logger.info(f"Closed position for {self.symbol} with trade ID {self.active_trade_id}")
                self.active_trade_id = None
