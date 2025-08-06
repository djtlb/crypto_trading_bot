"""
Backtester Module
================

Runs backtests for trading strategies using historical data.
"""

import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("Backtester")

class Backtester:
    """Backtests trading strategies using historical data"""
    
    def __init__(self, strategy, symbol: str, days: int = 30, timeframe: str = '1h'):
        """
        Initialize the backtester
        
        Args:
            strategy: The strategy to test
            symbol: The trading symbol
            days: The number of days of historical data to use
            timeframe: The timeframe for the data
        """
        self.strategy = strategy
        self.symbol = symbol
        self.days = days
        self.timeframe = timeframe
        self.exchange_handler = strategy.exchange_handler
        
        # Load historical data
        self._load_historical_data()
    
    def _load_historical_data(self):
        """Load historical data from the exchange"""
        # Calculate how many candles we need based on days and timeframe
        timeframe_minutes = self._timeframe_to_minutes(self.timeframe)
        candles_needed = int((self.days * 24 * 60) / timeframe_minutes)
        
        logger.info(f"Loading {candles_needed} {self.timeframe} candles for {self.symbol}")
        
        # Some exchanges have limits on how many candles can be fetched at once
        # So we may need to make multiple requests
        max_candles_per_request = 1000
        all_candles = []
        
        for i in range(0, candles_needed, max_candles_per_request):
            limit = min(max_candles_per_request, candles_needed - i)
            candles = self.exchange_handler.get_ohlcv(self.symbol, self.timeframe, limit=limit)
            
            if not candles:
                break
            
            all_candles.extend(candles)
            
            # If we didn't get as many candles as we asked for, we've got all that's available
            if len(candles) < limit:
                break
        
        # Convert to DataFrame
        self.data = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        self.data['datetime'] = pd.to_datetime(self.data['timestamp'], unit='ms')
        self.data.set_index('datetime', inplace=True)
    
    def _timeframe_to_minutes(self, timeframe: str) -> int:
        """Convert a timeframe string to minutes"""
        unit = timeframe[-1]
        value = int(timeframe[:-1])
        
        if unit == 'm':
            return value
        elif unit == 'h':
            return value * 60
        elif unit == 'd':
            return value * 24 * 60
        else:
            return 1  # Default to 1 minute
    
    def run(self) -> Dict:
        """
        Run the backtest
        
        Returns:
            A dictionary of backtest results
        """
        if self.data.empty:
            logger.error("No historical data available for backtesting")
            return {'error': 'No historical data available'}
        
        logger.info(f"Running backtest with {len(self.data)} data points")
        
        # Initialize results
        initial_balance = self.strategy.trade_amount
        balance = initial_balance
        trades = []
        equity_curve = [initial_balance]
        
        # Simulate trading
        in_position = False
        entry_price = 0
        position_size = 0
        
        for i in range(len(self.data) - 1):
            # Get current candle data
            current_data = self.data.iloc[:i+1]
            next_price = self.data.iloc[i+1]['close']
            
            # If not in a position, check for entry signal
            if not in_position:
                signal = self._simulate_strategy_signal(current_data)
                
                if signal == 'buy':
                    # Calculate position size
                    entry_price = current_data.iloc[-1]['close']
                    position_size = balance / entry_price
                    
                    # Enter position
                    in_position = True
                    
                    # Record trade
                    trades.append({
                        'type': 'buy',
                        'datetime': current_data.index[-1],
                        'price': entry_price,
                        'amount': position_size,
                        'balance': balance
                    })
                    
                    logger.info(f"Backtest: BUY signal at {current_data.index[-1]}, price {entry_price}, position {position_size}")
            
            # If in a position, check for exit signals
            else:
                # Check for stop loss
                stop_loss_price = entry_price * (1 - self.strategy.risk_manager.stop_loss_percentage / 100.0)
                take_profit_price = entry_price * (1 + self.strategy.risk_manager.take_profit_percentage / 100.0)
                
                # Check if stop loss or take profit is hit on this candle
                if next_price <= stop_loss_price:
                    # Stop loss hit
                    exit_price = stop_loss_price
                    balance = position_size * exit_price
                    
                    # Exit position
                    in_position = False
                    
                    # Record trade
                    trades.append({
                        'type': 'sell_stop_loss',
                        'datetime': self.data.index[i+1],
                        'price': exit_price,
                        'amount': position_size,
                        'balance': balance
                    })
                    
                    logger.info(f"Backtest: STOP LOSS at {self.data.index[i+1]}, price {exit_price}, balance {balance}")
                
                elif next_price >= take_profit_price:
                    # Take profit hit
                    exit_price = take_profit_price
                    balance = position_size * exit_price
                    
                    # Exit position
                    in_position = False
                    
                    # Record trade
                    trades.append({
                        'type': 'sell_take_profit',
                        'datetime': self.data.index[i+1],
                        'price': exit_price,
                        'amount': position_size,
                        'balance': balance
                    })
                    
                    logger.info(f"Backtest: TAKE PROFIT at {self.data.index[i+1]}, price {exit_price}, balance {balance}")
                
                else:
                    # Check for strategy exit signal
                    signal = self._simulate_strategy_signal(current_data)
                    
                    if signal == 'sell':
                        # Calculate exit price
                        exit_price = current_data.iloc[-1]['close']
                        balance = position_size * exit_price
                        
                        # Exit position
                        in_position = False
                        
                        # Record trade
                        trades.append({
                            'type': 'sell_signal',
                            'datetime': current_data.index[-1],
                            'price': exit_price,
                            'amount': position_size,
                            'balance': balance
                        })
                        
                        logger.info(f"Backtest: SELL signal at {current_data.index[-1]}, price {exit_price}, balance {balance}")
            
            # Update equity curve
            if in_position:
                equity = position_size * next_price
            else:
                equity = balance
            
            equity_curve.append(equity)
        
        # Close any open position at the end
        if in_position:
            exit_price = self.data.iloc[-1]['close']
            balance = position_size * exit_price
            
            trades.append({
                'type': 'sell_end',
                'datetime': self.data.index[-1],
                'price': exit_price,
                'amount': position_size,
                'balance': balance
            })
            
            logger.info(f"Backtest: Final position closed at {self.data.index[-1]}, price {exit_price}, balance {balance}")
        
        # Calculate statistics
        total_trades = len([t for t in trades if t['type'] == 'buy'])
        winning_trades = len([t for t in trades if t['type'].startswith('sell_take_profit')])
        losing_trades = len([t for t in trades if t['type'].startswith('sell_stop_loss')])
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        profit_loss = balance - initial_balance
        profit_loss_percent = (profit_loss / initial_balance) * 100 if initial_balance > 0 else 0
        
        # Calculate drawdown
        equity_array = np.array(equity_curve)
        max_equity = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - max_equity) / max_equity * 100
        max_drawdown = abs(np.min(drawdown))
        
        # Prepare results
        results = {
            'initial_balance': initial_balance,
            'final_balance': balance,
            'profit_loss': profit_loss,
            'profit_loss_percent': profit_loss_percent,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'max_drawdown': max_drawdown,
            'trades': trades,
            'equity_curve': equity_curve
        }
        
        # Plot equity curve
        self._plot_equity_curve(equity_curve)
        
        return results
    
    def _simulate_strategy_signal(self, data):
        """Simulate a strategy signal on historical data"""
        # This is a simple implementation that just calls the strategy's signal method
        # In a real implementation, you would need to mock the exchange handler's methods
        # to work with historical data instead of live data
        return self.strategy.generate_signal(data)
    
    def _plot_equity_curve(self, equity_curve):
        """Plot the equity curve"""
        plt.figure(figsize=(12, 6))
        plt.plot(equity_curve)
        plt.title('Equity Curve')
        plt.xlabel('Candles')
        plt.ylabel('Equity')
        plt.grid(True)
        plt.savefig('backtest_equity_curve.png')
        plt.close()
