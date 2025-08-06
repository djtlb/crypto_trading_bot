"""
DEX Swing Trading Strategy
=========================

A strategy for medium-term trades based on significant price movements.
"""

import time
import logging
from web3 import Web3
from dex_strategies.base_strategy import BaseStrategy
from typing import Dict, Any, Optional, List

logger = logging.getLogger("SwingStrategy")

class SwingStrategy(BaseStrategy):
    """Strategy for swing trading based on larger price movements on DEXes."""
    
    def __init__(
        self,
        wallet_manager,
        web3: Web3,
        chain_id: int,
        dex_id: str,
        token_address: str,
        base_token_address: Optional[str] = None,
        amount: float = 0.1,
        slippage: float = 1.0,
        gas_price: str = "auto",
        gas_limit: str = "auto",
        profit_target: float = 20.0,
        stop_loss: float = 10.0,
        trailing_stop: bool = True,
        price_check_interval: int = 300,  # 5 minutes
        trend_strength_threshold: float = 5.0,
        max_hold_time: int = 86400 * 7  # 7 days in seconds
    ):
        """Initialize the swing trading strategy

        Args:
            wallet_manager: Wallet manager instance
            web3: Web3 instance
            chain_id: Chain ID
            dex_id: DEX identifier (e.g., 'uniswap_v2')
            token_address: Token to trade
            base_token_address: Base token address (default is native token)
            amount: Amount to trade in base token units
            slippage: Slippage percentage
            gas_price: Gas price in wei or 'auto'
            gas_limit: Gas limit or 'auto'
            profit_target: Profit target percentage
            stop_loss: Stop loss percentage
            trailing_stop: Whether to use trailing stop
            price_check_interval: Seconds between price checks
            trend_strength_threshold: Minimum trend strength to enter a position
            max_hold_time: Maximum time to hold a position in seconds
        """
        super().__init__(
            wallet_manager=wallet_manager,
            web3=web3,
            chain_id=chain_id,
            dex_id=dex_id,
            token_address=token_address,
            base_token_address=base_token_address,
            amount=amount,
            slippage=slippage,
            gas_price=gas_price,
            gas_limit=gas_limit,
            profit_target=profit_target,
            stop_loss=stop_loss,
            trailing_stop=trailing_stop
        )
        
        # Swing trading specific parameters
        self.price_check_interval = price_check_interval
        self.trend_strength_threshold = trend_strength_threshold
        self.max_hold_time = max_hold_time
        
        # Price tracking
        self.price_history: List[Dict[str, Any]] = []
        self.last_price_check = 0
        self.position_start_time = None
        
        # Technical indicators
        self.ema_short = None  # Short EMA (Exponential Moving Average)
        self.ema_long = None   # Long EMA
        self.short_period = 12 # Short period for EMA calculation
        self.long_period = 26  # Long period for EMA calculation
    
    def execute_strategy(self) -> Dict[str, Any]:
        """Execute the swing trading strategy

        Returns:
            Dictionary with execution results
        """
        current_time = int(time.time())
        
        # Update price if it's time
        if current_time - self.last_price_check >= self.price_check_interval:
            self.update_price()
            self.last_price_check = current_time
            
            # Add price to history
            self.price_history.append({
                "timestamp": current_time,
                "price": self.current_price
            })
            
            # Keep up to 200 price points (covers a longer period for swing trading)
            if len(self.price_history) > 200:
                self.price_history = self.price_history[-200:]
            
            # Update technical indicators
            self._update_indicators()
        
        # Main strategy logic
        if self.trade_state == "idle":
            # Check if it's a good time to buy
            should_buy = self._should_buy()
            
            if should_buy:
                logger.info("Swing strategy: Initiating buy")
                buy_result = self.buy()
                
                if buy_result["success"]:
                    self.position_start_time = current_time
                    return {
                        "success": True,
                        "action": "buy",
                        "message": "Swing buy executed",
                        "details": buy_result
                    }
                else:
                    return {
                        "success": False,
                        "action": "error",
                        "message": f"Swing buy failed: {buy_result['message']}",
                        "details": buy_result
                    }
        
        elif self.trade_state == "bought":
            # Check for max hold time
            if self.position_start_time and current_time - self.position_start_time >= self.max_hold_time:
                logger.info(f"Max hold time reached ({self.max_hold_time / 86400:.1f} days), selling position")
                sell_result = self.sell()
                
                return {
                    "success": sell_result["success"],
                    "action": "max_hold_sell" if sell_result["success"] else "error",
                    "message": f"Max hold time reached: {sell_result['message']}",
                    "details": sell_result
                }
            
            # Check if trend has reversed
            trend_reversed = self._has_trend_reversed()
            
            if trend_reversed:
                logger.info("Trend has reversed, selling position")
                sell_result = self.sell()
                
                return {
                    "success": sell_result["success"],
                    "action": "trend_reversal_sell" if sell_result["success"] else "error",
                    "message": f"Trend reversal sell: {sell_result['message']}",
                    "details": sell_result
                }
        
        return {
            "success": True,
            "action": "monitor",
            "message": f"Monitoring position in state: {self.trade_state}",
            "state": self.trade_state,
            "current_price": self.current_price,
            "entry_price": self.entry_price,
            "profit_pct": ((self.current_price / self.entry_price) - 1) * 100 if self.current_price and self.entry_price else None,
            "ema_short": self.ema_short,
            "ema_long": self.ema_long,
            "hold_time": current_time - self.position_start_time if self.position_start_time else None
        }
    
    def _update_indicators(self):
        """Update technical indicators based on price history"""
        if len(self.price_history) < self.long_period:
            return
        
        prices = [p["price"] for p in self.price_history]
        
        # Calculate EMAs
        self.ema_short = self._calculate_ema(prices, self.short_period)
        self.ema_long = self._calculate_ema(prices, self.long_period)
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average

        Args:
            prices: List of prices
            period: EMA period

        Returns:
            EMA value
        """
        if len(prices) < period:
            return None
        
        # Calculate initial SMA
        sma = sum(prices[:period]) / period
        
        # Calculate multiplier
        multiplier = 2 / (period + 1)
        
        # Calculate EMA
        ema = sma
        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    def _calculate_trend_strength(self) -> float:
        """Calculate the current trend strength

        Returns:
            Trend strength as percentage
        """
        if not self.ema_short or not self.ema_long:
            return 0
        
        # Trend strength as percentage difference between short and long EMAs
        trend_strength = ((self.ema_short / self.ema_long) - 1) * 100
        return trend_strength
    
    def _should_buy(self) -> bool:
        """Determine if we should buy based on trend analysis

        Returns:
            True if we should buy, False otherwise
        """
        # Ensure we have enough price history and calculated indicators
        if not self.ema_short or not self.ema_long:
            logger.info("Not enough price history for buy decision")
            return False
        
        # Calculate trend strength
        trend_strength = self._calculate_trend_strength()
        
        # Trend strength must be above threshold and positive (uptrend)
        if trend_strength < self.trend_strength_threshold:
            return False
        
        # Check for EMA crossover (short EMA crosses above long EMA)
        previous_prices = [p["price"] for p in self.price_history[-30:]]
        
        if len(previous_prices) < self.long_period + 2:
            return False
        
        # Calculate EMAs for previous period
        prev_short_ema = self._calculate_ema(previous_prices[:-1], self.short_period)
        prev_long_ema = self._calculate_ema(previous_prices[:-1], self.long_period)
        
        # Crossover detection (short EMA crosses above long EMA)
        crossover = prev_short_ema <= prev_long_ema and self.ema_short > self.ema_long
        
        if crossover:
            logger.info(f"Buy signal: EMA crossover detected with trend strength {trend_strength:.2f}%")
            return True
        
        return False
    
    def _has_trend_reversed(self) -> bool:
        """Determine if the trend has reversed

        Returns:
            True if trend has reversed, False otherwise
        """
        if not self.ema_short or not self.ema_long:
            return False
        
        # Check for EMA crossover (short EMA crosses below long EMA)
        previous_prices = [p["price"] for p in self.price_history[-30:]]
        
        if len(previous_prices) < self.long_period + 2:
            return False
        
        # Calculate EMAs for previous period
        prev_short_ema = self._calculate_ema(previous_prices[:-1], self.short_period)
        prev_long_ema = self._calculate_ema(previous_prices[:-1], self.long_period)
        
        # Crossover detection (short EMA crosses below long EMA)
        crossover = prev_short_ema >= prev_long_ema and self.ema_short < self.ema_long
        
        if crossover:
            logger.info("Sell signal: EMA crossover detected (trend reversal)")
            return True
        
        return False
    
    def check_exit_conditions(self) -> bool:
        """Check if we should exit the position

        Returns:
            True if we should exit, False otherwise
        """
        # First check parent class exit conditions (profit target, stop loss, trailing stop)
        if super().check_exit_conditions():
            return True
        
        # Then check trend reversal if we're in a position
        if self.trade_state == "bought" and self.position:
            return self._has_trend_reversed()
        
        return False
