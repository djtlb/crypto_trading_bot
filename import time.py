import time
import logging
import threading
from datetime import datetime
from exchange import ExchangeInterface
from strategy import TradingStrategy
from config import (
    TRADING_PAIR, INITIAL_BALANCE, TARGET_BALANCE, 
    POSITION_SIZE, STOP_LOSS_PERCENTAGE, 
    TAKE_PROFIT_PERCENTAGE, MAX_DAILY_TRADES,
    MAX_LOSS_PERCENTAGE
)

logger = logging.getLogger(__name__)

class TradingBot:
    def __init__(self):
        self.exchange = ExchangeInterface()
        self.strategy = TradingStrategy()
        self.running = False
        self.current_position = None
        self.entry_price = 0
        self.position_size = 0
        self.trades_today = 0
        self.starting_balance = self.exchange.get_balance() or INITIAL_BALANCE
        self.current_balance = self.starting_balance
        logger.info(f"Trading bot initialized with ${self.starting_balance} balance")
        
    def start(self):
        """Start the trading bot"""
        self.running = True
        trading_thread = threading.Thread(target=self.trading_loop)
        trading_thread.start()
        logger.info(f"Trading bot started - target: ${TARGET_BALANCE}")
        return "Trading bot started successfully"
        
    def stop(self):
        """Stop the trading bot"""
        self.running = False
        if self.current_position:
            self.exit_position("Bot stopped")
        logger.info("Trading bot stopped")
        return "Trading bot stopped successfully"
        
    def get_status(self):
        """Get current bot status"""
        return {
            "running": self.running,
            "starting_balance": self.starting_balance,
            "current_balance": self.current_balance,
            "profit_percentage": ((self.current_balance - self.starting_balance) / self.starting_balance) * 100,
            "target_balance": TARGET_BALANCE,
            "current_position": self.current_position,
            "trades_today": self.trades_today
        }
        
    def enter_position(self, position_type):
        """Enter a trading position"""
        if self.trades_today >= MAX_DAILY_TRADES:
            logger.warning("Maximum daily trades reached")
            return False
            
        current_price = self.exchange.get_market_price()
        if not current_price:
            return False
            
        # Calculate position size based on current balance
        self.position_size = self.current_balance * POSITION_SIZE
        
        if position_type == "BUY":
            # Calculate amount of crypto to buy
            amount = self.position_size / current_price
            order = self.exchange.buy(amount)
            if order:
                self.current_position = "LONG"
                self.entry_price = current_price
                self.trades_today += 1
                logger.info(f"Entered LONG position at ${current_price}")
                return True
        elif position_type == "SELL":
            # For short position (simplified - in reality, shorting is more complex)
            # This is just a demonstration
            amount = self.position_size / current_price
            order = self.exchange.sell(amount)
            if order:
                self.current_position = "SHORT"
                self.entry_price = current_price
                self.trades_today += 1
                logger.info(f"Entered SHORT position at ${current_price}")
                return True
                
        return False
        
    def exit_position(self, reason):
        """Exit the current position"""
        if not self.current_position:
            return False
            
        current_price = self.exchange.get_market_price()
        if not current_price:
            return False
            
        if self.current_position == "LONG":
            # Calculate profit/loss
            pnl = ((current_price - self.entry_price) / self.entry_price) * self.position_size
            # Execute sell order
            amount = self.position_size / self.entry_price
            order = self.exchange.sell(amount)
            if order:
                self.current_balance += pnl
                logger.info(f"Exited LONG position at ${current_price}, PnL: ${pnl:.2f}, Reason: {reason}")
        elif self.current_position == "SHORT":
            # Calculate profit/loss (inverse for short)
            pnl = ((self.entry_price - current_price) / self.entry_price) * self.position_size
            # Close short position
            amount = self.position_size / self.entry_price
            order = self.exchange.buy(amount)
            if order:
                self.current_balance += pnl
                logger.info(f"Exited SHORT position at ${current_price}, PnL: ${pnl:.2f}, Reason: {reason}")
                
        self.current_position = None
        self.entry_price = 0
        self.position_size = 0
        return True
        
    def check_exit_conditions(self):
        """Check if we should exit the current position"""
        if not self.current_position:
            return False
            
        current_price = self.exchange.get_market_price()
        if not current_price:
            return False
            
        # Calculate current profit/loss
        if self.current_position == "LONG":
            pnl_percentage = (current_price - self.entry_price) / self.entry_price
        else:  # SHORT
            pnl_percentage = (self.entry_price - current_price) / self.entry_price
            
        # Check stop loss
        if pnl_percentage <= -STOP_LOSS_PERCENTAGE:
            self.exit_position("Stop loss triggered")
            return True
            
        # Check take profit
        if pnl_percentage >= TAKE_PROFIT_PERCENTAGE:
            self.exit_position("Take profit triggered")
            return True
            
        # Check if target balance reached
        if self.current_balance >= TARGET_BALANCE:
            self.exit_position("Target balance reached")
            self.running = False
            logger.info(f"🎉 Target balance of ${TARGET_BALANCE} reached! Trading stopped.")
            return True
            
        # Check maximum loss
        if (self.current_balance / self.starting_balance) <= (1 - MAX_LOSS_PERCENTAGE):
            self.exit_position("Maximum loss threshold reached")
            self.running = False
            logger.warning(f"⚠️ Maximum loss threshold of {MAX_LOSS_PERCENTAGE*100}% reached. Trading stopped.")
            return True
            
        return False
        
    def trading_loop(self):
        """Main trading loop"""
        while self.running:
            try:
                # Update current balance
                balance = self.exchange.get_balance()
                if balance:
                    self.current_balance = balance
                
                # Check if we should exit current position
                if self.current_position:
                    self.check_exit_conditions()
                else:
                    # Get market data
                    historical_data = self.exchange.get_historical_data()
                    
                    # Analyze market and get signal
                    signal = self.strategy.analyze_market(historical_data)
                    
                    # Execute trade based on signal
                    if signal in ["BUY", "SELL"]:
                        self.enter_position(signal)
                
                # Sleep to avoid API rate limits
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in trading loop: {str(e)}")
                time.sleep(30)  # Sleep longer on error
