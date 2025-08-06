"""
DEX Sniper Strategy
===================

A strategy for sniping new token listings on DEXes.
"""

import time
import logging
from web3 import Web3
from dex_strategies.base_strategy import BaseStrategy
from typing import Dict, Any, Optional

logger = logging.getLogger("SniperStrategy")

class SniperStrategy(BaseStrategy):
    """Strategy for sniping new token listings on DEXes."""
    
    def __init__(
        self,
        wallet_manager,
        web3: Web3,
        chain_id: int,
        dex_id: str,
        token_address: str,
        base_token_address: Optional[str] = None,
        amount: float = 0.01,
        slippage: float = 3.0,
        gas_price: str = "auto",
        gas_limit: str = "auto",
        profit_target: float = 50.0,
        stop_loss: float = 20.0,
        trailing_stop: bool = True,
        auto_sell_time: int = 0,
        gas_multiplier: float = 1.5
    ):
        """Initialize the sniper strategy

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
            auto_sell_time: Auto sell after this many seconds (0 = disabled)
            gas_multiplier: Multiplier for gas price to frontrun other transactions
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
        
        # Sniper-specific parameters
        self.auto_sell_time = auto_sell_time
        self.gas_multiplier = gas_multiplier
        self.buy_time = None
    
    def execute_strategy(self) -> Dict[str, Any]:
        """Execute the sniper strategy

        Returns:
            Dictionary with execution results
        """
        if self.trade_state == "idle":
            # Start by buying the token
            logger.info("Executing sniper strategy: Initiating buy")
            buy_result = self.buy()
            
            if buy_result["success"]:
                self.buy_time = int(time.time())
                return {
                    "success": True,
                    "action": "buy",
                    "message": "Sniper buy executed",
                    "details": buy_result
                }
            else:
                return {
                    "success": False,
                    "action": "error",
                    "message": f"Sniper buy failed: {buy_result['message']}",
                    "details": buy_result
                }
        
        elif self.trade_state == "bought" and self.auto_sell_time > 0 and self.buy_time is not None:
            # Check if we should auto-sell based on time
            current_time = int(time.time())
            elapsed_time = current_time - self.buy_time
            
            if elapsed_time >= self.auto_sell_time:
                logger.info(f"Auto-sell time reached ({self.auto_sell_time}s), selling position")
                sell_result = self.sell()
                
                return {
                    "success": sell_result["success"],
                    "action": "auto_sell" if sell_result["success"] else "error",
                    "message": f"Auto-sell after {elapsed_time}s: {sell_result['message']}",
                    "details": sell_result
                }
        
        return {
            "success": True,
            "action": "monitor",
            "message": f"Monitoring position in state: {self.trade_state}",
            "state": self.trade_state,
            "current_price": self.current_price,
            "entry_price": self.entry_price,
            "profit_pct": ((self.current_price / self.entry_price) - 1) * 100 if self.current_price and self.entry_price else None
        }
    
    def buy(self) -> Dict[str, Any]:
        """Execute a buy order with sniper-specific logic

        Returns:
            Dictionary with buy results
        """
        # If gas price is auto but we have a gas multiplier, we need to get the current gas price
        if self.gas_price == "auto" and self.gas_multiplier > 1.0:
            try:
                # For EIP-1559 chains
                if hasattr(self.web3.eth, 'max_priority_fee'):
                    base_fee = self.web3.eth.get_block('latest')['baseFeePerGas']
                    priority_fee = self.web3.eth.max_priority_fee
                    max_fee = int((base_fee + priority_fee) * self.gas_multiplier)
                    
                    # Use EIP-1559 transaction type
                    logger.info(f"Using EIP-1559 gas strategy with multiplier {self.gas_multiplier}")
                    logger.info(f"Base fee: {base_fee}, Priority fee: {priority_fee}, Max fee: {max_fee}")
                    
                    # Update transaction parameters for buy
                    self.wallet_manager.default_tx_params["maxFeePerGas"] = max_fee
                    self.wallet_manager.default_tx_params["maxPriorityFeePerGas"] = priority_fee
                    
                    # Remove legacy gas price if it exists
                    if "gasPrice" in self.wallet_manager.default_tx_params:
                        del self.wallet_manager.default_tx_params["gasPrice"]
                else:
                    # For legacy chains
                    gas_price = self.web3.eth.gas_price
                    gas_price_multiplied = int(gas_price * self.gas_multiplier)
                    logger.info(f"Using legacy gas price with multiplier {self.gas_multiplier}")
                    logger.info(f"Current gas price: {gas_price}, Multiplied: {gas_price_multiplied}")
                    
                    # Update transaction parameters for buy
                    self.wallet_manager.default_tx_params["gasPrice"] = gas_price_multiplied
            except Exception as e:
                logger.error(f"Error setting gas price with multiplier: {e}")
        
        # Call the parent buy method
        result = super().buy()
        
        # Reset transaction parameters to defaults after buy
        self.wallet_manager.reset_tx_params()
        
        return result
