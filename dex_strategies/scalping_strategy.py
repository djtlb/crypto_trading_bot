"""
DEX Scalping Strategy
====================

A strategy for executing quick trades based on small price movements.
"""

import time
import logging
from web3 import Web3
from dex_strategies.base_strategy import BaseStrategy
from typing import Dict, Any, Optional, List

logger = logging.getLogger("ScalpingStrategy")

class ScalpingStrategy(BaseStrategy):
    """Strategy for scalping small price movements on DEXes."""
    
    def __init__(
        self,
        wallet_manager,
        web3: Web3,
        chain_id: int,
        dex_id: str,
        token_address: str,
        base_token_address: Optional[str] = None,
        amount: float = 0.01,
        slippage: float = 1.0,
        gas_price: str = "auto",
        gas_limit: str = "auto",
        profit_target: float = 2.0,
        stop_loss: float = 1.0,
        trailing_stop: bool = True,
        price_check_interval: int = 5,
        max_trades_per_day: int = 10,
        max_gas_cost_percent: float = 5.0
    ):
        """Initialize the scalping strategy

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
            max_trades_per_day: Maximum number of trades per day
            max_gas_cost_percent: Maximum gas cost as percentage of trade amount
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
        
        # Scalping-specific parameters
        self.price_check_interval = price_check_interval
        self.max_trades_per_day = max_trades_per_day
        self.max_gas_cost_percent = max_gas_cost_percent
        
        # Price tracking
        self.price_history: List[Dict[str, Any]] = []
        self.last_price_check = 0
        self.last_trade_time = 0
        self.today_trades_count = 0
        self.today_date = time.strftime("%Y-%m-%d")
    
    def execute_strategy(self) -> Dict[str, Any]:
        """Execute the scalping strategy

        Returns:
            Dictionary with execution results
        """
        current_time = int(time.time())
        current_date = time.strftime("%Y-%m-%d")
        
        # Reset trade count if it's a new day
        if current_date != self.today_date:
            self.today_date = current_date
            self.today_trades_count = 0
        
        # Check if we've reached the maximum trades per day
        if self.today_trades_count >= self.max_trades_per_day:
            return {
                "success": True,
                "action": "skip",
                "message": f"Maximum trades per day reached ({self.max_trades_per_day})",
                "state": self.trade_state
            }
        
        # Update price if it's time
        if current_time - self.last_price_check >= self.price_check_interval:
            self.update_price()
            self.last_price_check = current_time
            
            # Add price to history
            self.price_history.append({
                "timestamp": current_time,
                "price": self.current_price
            })
            
            # Keep only the last 100 price points
            if len(self.price_history) > 100:
                self.price_history = self.price_history[-100:]
        
        # Main strategy logic
        if self.trade_state == "idle":
            # Check if it's a good time to buy
            should_buy = self._should_buy()
            
            if should_buy:
                # Check gas costs first
                gas_cost = self._estimate_gas_cost()
                if gas_cost["gas_cost_percent"] > self.max_gas_cost_percent:
                    logger.info(f"Gas cost too high: {gas_cost['gas_cost_percent']:.2f}% > {self.max_gas_cost_percent:.2f}%")
                    return {
                        "success": True,
                        "action": "skip",
                        "message": f"Gas cost too high: {gas_cost['gas_cost_percent']:.2f}%",
                        "gas_cost": gas_cost
                    }
                
                # Execute buy
                logger.info("Scalping strategy: Initiating buy")
                buy_result = self.buy()
                
                if buy_result["success"]:
                    self.last_trade_time = current_time
                    self.today_trades_count += 1
                    return {
                        "success": True,
                        "action": "buy",
                        "message": "Scalping buy executed",
                        "details": buy_result
                    }
                else:
                    return {
                        "success": False,
                        "action": "error",
                        "message": f"Scalping buy failed: {buy_result['message']}",
                        "details": buy_result
                    }
        
        elif self.trade_state == "bought":
            # Check if we should sell based on price movement
            sell_now = self._should_sell()
            
            if sell_now:
                logger.info("Scalping strategy: Initiating sell")
                sell_result = self.sell()
                
                if sell_result["success"]:
                    self.today_trades_count += 1
                    return {
                        "success": True,
                        "action": "sell",
                        "message": "Scalping sell executed",
                        "details": sell_result
                    }
                else:
                    return {
                        "success": False,
                        "action": "error",
                        "message": f"Scalping sell failed: {sell_result['message']}",
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
            "today_trades": self.today_trades_count
        }
    
    def _calculate_price_momentum(self, window_size: int = 10) -> float:
        """Calculate price momentum over a window

        Args:
            window_size: Number of price points to use

        Returns:
            Momentum value as percentage
        """
        if len(self.price_history) < window_size:
            return 0
        
        # Get the most recent prices
        recent_prices = [p["price"] for p in self.price_history[-window_size:]]
        
        if len(recent_prices) < 2:
            return 0
        
        # Calculate momentum (percentage change over the window)
        start_price = recent_prices[0]
        end_price = recent_prices[-1]
        
        if start_price <= 0:
            return 0
        
        momentum = ((end_price / start_price) - 1) * 100
        return momentum
    
    def _calculate_volatility(self, window_size: int = 20) -> float:
        """Calculate price volatility over a window

        Args:
            window_size: Number of price points to use

        Returns:
            Volatility value as percentage
        """
        if len(self.price_history) < window_size:
            return 0
        
        # Get the most recent prices
        recent_prices = [p["price"] for p in self.price_history[-window_size:]]
        
        if len(recent_prices) < 2:
            return 0
        
        # Calculate average price
        avg_price = sum(recent_prices) / len(recent_prices)
        
        if avg_price <= 0:
            return 0
        
        # Calculate standard deviation
        variance = sum((price - avg_price) ** 2 for price in recent_prices) / len(recent_prices)
        std_dev = variance ** 0.5
        
        # Volatility as percentage of average price
        volatility = (std_dev / avg_price) * 100
        return volatility
    
    def _should_buy(self) -> bool:
        """Determine if we should buy based on price analysis

        Returns:
            True if we should buy, False otherwise
        """
        # Ensure we have enough price history
        if len(self.price_history) < 20:
            logger.info("Not enough price history for buy decision")
            return False
        
        # Calculate short-term momentum (last 5 price points)
        short_momentum = self._calculate_price_momentum(5)
        
        # Calculate medium-term momentum (last 15 price points)
        medium_momentum = self._calculate_price_momentum(15)
        
        # Calculate volatility
        volatility = self._calculate_volatility(20)
        
        logger.info(f"Short momentum: {short_momentum:.2f}%, Medium momentum: {medium_momentum:.2f}%, Volatility: {volatility:.2f}%")
        
        # Buy conditions: 
        # 1. Short-term momentum is positive 
        # 2. Short-term momentum is stronger than medium-term (acceleration)
        # 3. Volatility is reasonable
        buy_decision = (
            short_momentum > 0.5 and  # Positive short-term momentum
            short_momentum > medium_momentum and  # Accelerating momentum
            volatility > 1.0 and volatility < 10.0  # Reasonable volatility
        )
        
        if buy_decision:
            logger.info(f"Buy conditions met: Momentum acceleration with reasonable volatility")
        
        return buy_decision
    
    def _should_sell(self) -> bool:
        """Determine if we should sell based on price analysis (beyond the standard stop/target)

        Returns:
            True if we should sell, False otherwise
        """
        # If normal exit conditions are met, we'll sell anyway
        if self.check_exit_conditions():
            return True
        
        # Ensure we have enough price history and a position
        if len(self.price_history) < 10 or not self.entry_price or not self.current_price:
            return False
        
        # Calculate short-term momentum (last 5 price points)
        short_momentum = self._calculate_price_momentum(5)
        
        # Calculate current profit
        current_profit = ((self.current_price / self.entry_price) - 1) * 100
        
        # Sell conditions:
        # 1. We have some profit but momentum is turning negative
        # 2. Momentum is strongly negative
        sell_decision = (
            (current_profit > 0.5 and short_momentum < -0.5) or  # Momentum turning negative with some profit
            short_momentum < -2.0  # Strongly negative momentum
        )
        
        if sell_decision:
            logger.info(f"Sell conditions met: Momentum turning negative with profit {current_profit:.2f}%")
        
        return sell_decision
    
    def _estimate_gas_cost(self) -> Dict[str, Any]:
        """Estimate gas cost for a transaction

        Returns:
            Dictionary with gas cost estimates
        """
        try:
            # Estimate gas for a swap
            token_info = self.dex_connector.get_token_info(self.base_token_address)
            amount_wei = int(self.amount * (10 ** token_info["decimals"]))
            
            # Prepare buy transaction (without sending)
            tx_data = self.dex_connector.prepare_buy_transaction(
                self.dex_id,
                self.token_address,
                amount_wei,
                self.wallet_manager.address,
                self.slippage,
                self.base_token_address
            )
            
            if "error" in tx_data:
                return {
                    "success": False,
                    "error": tx_data.get("error"),
                    "gas_cost_percent": 100.0  # Set to high value to prevent trade
                }
            
            # Get gas price
            if hasattr(self.web3.eth, 'max_priority_fee'):
                # EIP-1559
                base_fee = self.web3.eth.get_block('latest')['baseFeePerGas']
                priority_fee = self.web3.eth.max_priority_fee
                gas_price = base_fee + priority_fee
            else:
                # Legacy
                gas_price = self.web3.eth.gas_price
            
            # Estimate gas usage
            gas_limit = tx_data["transaction"].get("gas", 300000)
            
            # Calculate gas cost in native token (ETH, BNB, etc.)
            gas_cost_wei = gas_price * gas_limit
            gas_cost_eth = self.web3.from_wei(gas_cost_wei, 'ether')
            
            # Calculate as percentage of trade amount
            gas_cost_percent = (gas_cost_eth / self.amount) * 100
            
            return {
                "success": True,
                "gas_price": gas_price,
                "gas_limit": gas_limit,
                "gas_cost_wei": gas_cost_wei,
                "gas_cost_eth": gas_cost_eth,
                "gas_cost_percent": gas_cost_percent
            }
            
        except Exception as e:
            logger.error(f"Error estimating gas cost: {e}")
            return {
                "success": False,
                "error": str(e),
                "gas_cost_percent": 100.0  # Set to high value to prevent trade
            }
