"""
DEX Strategy Factory
=================

Factory for creating and managing trading strategies.
"""

import logging
from typing import Dict, Any, Optional, List
from web3 import Web3
from cryptography.fernet import Fernet

from dex_strategies.sniper_strategy import SniperStrategy
from dex_strategies.scalping_strategy import ScalpingStrategy
from dex_strategies.swing_strategy import SwingStrategy
from dex_strategies.arbitrage_strategy import ArbitrageStrategy
from dex_utils.wallet_manager import WalletManager
from dex_utils.token_validator import TokenValidator

logger = logging.getLogger("StrategyFactory")

class StrategyFactory:
    """Factory for creating and managing trading strategies"""
    
    STRATEGY_TYPES = {
        "sniper": SniperStrategy,
        "scalping": ScalpingStrategy,
        "swing": SwingStrategy,
        "arbitrage": ArbitrageStrategy
    }
    
    def __init__(self, web3: Web3, chain_id: int, wallet_manager: WalletManager):
        """Initialize the strategy factory

        Args:
            web3: Web3 instance
            chain_id: Chain ID
            wallet_manager: Wallet manager instance
        """
        self.web3 = web3
        self.chain_id = chain_id
        self.wallet_manager = wallet_manager
        self.active_strategies = {}
        self.fernet = None
        self.token_validator = TokenValidator(web3, chain_id)
    
    def set_encryption(self, fernet: Fernet):
        """Set encryption for secure wallet operations

        Args:
            fernet: Fernet encryption instance
        """
        self.fernet = fernet
    
    def create_strategy(
        self,
        strategy_id: str,
        strategy_type: str,
        token_address: str,
        dex_id: str,
        base_token_address: Optional[str] = None,
        amount: float = 0.01,
        slippage: float = 1.0,
        gas_price: str = "auto",
        gas_limit: str = "auto",
        profit_target: float = 5.0,
        stop_loss: float = 2.0,
        trailing_stop: bool = False,
        custom_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new strategy

        Args:
            strategy_id: Unique identifier for the strategy
            strategy_type: Type of strategy (sniper, scalping, swing, arbitrage)
            token_address: Token to trade
            dex_id: DEX identifier (e.g., 'uniswap_v2')
            base_token_address: Base token address (default is native token)
            amount: Amount to trade in base token units
            slippage: Slippage percentage
            gas_price: Gas price in wei or 'auto'
            gas_limit: Gas limit or 'auto'
            profit_target: Profit target percentage
            stop_loss: Stop loss percentage
            trailing_stop: Whether to use trailing stop
            custom_params: Additional parameters specific to the strategy type

        Returns:
            Dictionary with creation result
        """
        # Check if strategy ID already exists
        if strategy_id in self.active_strategies:
            return {
                "success": False,
                "message": f"Strategy with ID {strategy_id} already exists",
                "strategy_id": strategy_id
            }
        
        # Check if strategy type is valid
        if strategy_type not in self.STRATEGY_TYPES:
            return {
                "success": False,
                "message": f"Invalid strategy type: {strategy_type}. Valid types: {', '.join(self.STRATEGY_TYPES.keys())}",
                "strategy_id": strategy_id
            }
        
        try:
            # Validate token
            token_address = Web3.to_checksum_address(token_address)
            
            if base_token_address:
                base_token_address = Web3.to_checksum_address(base_token_address)
            
            # Validate token for safety (optional)
            if strategy_type != "arbitrage":  # Skip validation for arbitrage
                logger.info(f"Validating token {token_address} for safety")
                validation = self.token_validator.validate_token(token_address, dex_id, base_token_address)
                
                if not validation["is_valid"]:
                    return {
                        "success": False,
                        "message": f"Token validation failed: {validation['message']}",
                        "validation": validation,
                        "strategy_id": strategy_id
                    }
            
            # Prepare parameters
            params = {
                "wallet_manager": self.wallet_manager,
                "web3": self.web3,
                "chain_id": self.chain_id,
                "token_address": token_address,
                "base_token_address": base_token_address,
                "amount": amount,
                "slippage": slippage,
                "gas_price": gas_price,
                "gas_limit": gas_limit,
                "profit_target": profit_target,
                "stop_loss": stop_loss,
                "trailing_stop": trailing_stop
            }
            
            # Add custom parameters for specific strategy types
            if strategy_type == "arbitrage":
                # For arbitrage, dex_id should be source DEX
                if custom_params and "target_dex_id" in custom_params:
                    params["source_dex_id"] = dex_id
                    params["target_dex_id"] = custom_params["target_dex_id"]
                else:
                    return {
                        "success": False,
                        "message": "Arbitrage strategy requires target_dex_id in custom_params",
                        "strategy_id": strategy_id
                    }
            else:
                params["dex_id"] = dex_id
            
            # Add other custom parameters
            if custom_params:
                for key, value in custom_params.items():
                    if key != "target_dex_id" or strategy_type != "arbitrage":
                        params[key] = value
            
            # Create strategy instance
            strategy_class = self.STRATEGY_TYPES[strategy_type]
            strategy = strategy_class(**params)
            
            # Set encryption if available
            if self.fernet:
                strategy.set_encryption(self.fernet)
            
            # Store strategy
            self.active_strategies[strategy_id] = {
                "id": strategy_id,
                "type": strategy_type,
                "instance": strategy,
                "token_address": token_address,
                "dex_id": dex_id,
                "base_token_address": base_token_address,
                "params": params
            }
            
            logger.info(f"Created {strategy_type} strategy with ID {strategy_id} for token {token_address}")
            
            return {
                "success": True,
                "message": f"Strategy created successfully",
                "strategy_id": strategy_id,
                "type": strategy_type,
                "token_address": token_address,
                "dex_id": dex_id
            }
            
        except Exception as e:
            logger.error(f"Error creating strategy: {e}")
            return {
                "success": False,
                "message": f"Error creating strategy: {str(e)}",
                "strategy_id": strategy_id
            }
    
    def get_strategy(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """Get a strategy by ID

        Args:
            strategy_id: Strategy ID

        Returns:
            Strategy details or None if not found
        """
        if strategy_id not in self.active_strategies:
            return None
        
        strategy_data = self.active_strategies[strategy_id].copy()
        strategy_data.pop("instance", None)  # Remove instance from response
        
        # Add current state
        strategy = self.active_strategies[strategy_id]["instance"]
        strategy_data["running"] = strategy.running
        strategy_data["trade_state"] = strategy.trade_state
        strategy_data["current_price"] = strategy.current_price
        
        if strategy.trade_state == "bought" and strategy.entry_price and strategy.current_price:
            strategy_data["current_profit"] = ((strategy.current_price / strategy.entry_price) - 1) * 100
        
        # Add performance metrics
        strategy_data["performance"] = strategy.get_performance_metrics()
        
        return strategy_data
    
    def list_strategies(self) -> List[Dict[str, Any]]:
        """List all active strategies

        Returns:
            List of strategy details
        """
        return [self.get_strategy(strategy_id) for strategy_id in self.active_strategies]
    
    def start_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """Start a strategy

        Args:
            strategy_id: Strategy ID

        Returns:
            Dictionary with result
        """
        if strategy_id not in self.active_strategies:
            return {
                "success": False,
                "message": f"Strategy with ID {strategy_id} not found",
                "strategy_id": strategy_id
            }
        
        try:
            strategy = self.active_strategies[strategy_id]["instance"]
            
            if strategy.running:
                return {
                    "success": True,
                    "message": f"Strategy {strategy_id} already running",
                    "strategy_id": strategy_id
                }
            
            strategy.start()
            
            return {
                "success": True,
                "message": f"Strategy {strategy_id} started",
                "strategy_id": strategy_id
            }
            
        except Exception as e:
            logger.error(f"Error starting strategy {strategy_id}: {e}")
            return {
                "success": False,
                "message": f"Error starting strategy: {str(e)}",
                "strategy_id": strategy_id
            }
    
    def stop_strategy(self, strategy_id: str, force_sell: bool = False) -> Dict[str, Any]:
        """Stop a strategy

        Args:
            strategy_id: Strategy ID
            force_sell: Whether to force sell any open position

        Returns:
            Dictionary with result
        """
        if strategy_id not in self.active_strategies:
            return {
                "success": False,
                "message": f"Strategy with ID {strategy_id} not found",
                "strategy_id": strategy_id
            }
        
        try:
            strategy = self.active_strategies[strategy_id]["instance"]
            
            if not strategy.running:
                return {
                    "success": True,
                    "message": f"Strategy {strategy_id} already stopped",
                    "strategy_id": strategy_id
                }
            
            # Check if we need to force sell
            sell_result = None
            if force_sell and strategy.trade_state == "bought":
                logger.info(f"Force selling position for strategy {strategy_id}")
                sell_result = strategy.sell()
            
            strategy.stop()
            
            result = {
                "success": True,
                "message": f"Strategy {strategy_id} stopped",
                "strategy_id": strategy_id
            }
            
            if sell_result:
                result["sell_result"] = sell_result
            
            return result
            
        except Exception as e:
            logger.error(f"Error stopping strategy {strategy_id}: {e}")
            return {
                "success": False,
                "message": f"Error stopping strategy: {str(e)}",
                "strategy_id": strategy_id
            }
    
    def execute_strategy_action(self, strategy_id: str, action: str) -> Dict[str, Any]:
        """Execute a specific action on a strategy

        Args:
            strategy_id: Strategy ID
            action: Action to execute (buy, sell, execute)

        Returns:
            Dictionary with result
        """
        if strategy_id not in self.active_strategies:
            return {
                "success": False,
                "message": f"Strategy with ID {strategy_id} not found",
                "strategy_id": strategy_id
            }
        
        try:
            strategy = self.active_strategies[strategy_id]["instance"]
            
            if action == "buy":
                return strategy.buy()
            elif action == "sell":
                return strategy.sell()
            elif action == "execute":
                return strategy.execute_strategy()
            else:
                return {
                    "success": False,
                    "message": f"Invalid action: {action}. Valid actions: buy, sell, execute",
                    "strategy_id": strategy_id
                }
            
        except Exception as e:
            logger.error(f"Error executing action {action} on strategy {strategy_id}: {e}")
            return {
                "success": False,
                "message": f"Error executing action: {str(e)}",
                "strategy_id": strategy_id,
                "action": action
            }
    
    def delete_strategy(self, strategy_id: str, force_sell: bool = False) -> Dict[str, Any]:
        """Delete a strategy

        Args:
            strategy_id: Strategy ID
            force_sell: Whether to force sell any open position

        Returns:
            Dictionary with result
        """
        if strategy_id not in self.active_strategies:
            return {
                "success": False,
                "message": f"Strategy with ID {strategy_id} not found",
                "strategy_id": strategy_id
            }
        
        try:
            # Stop strategy first
            stop_result = self.stop_strategy(strategy_id, force_sell)
            
            if not stop_result["success"] and not force_sell:
                return stop_result
            
            # Remove strategy
            strategy_data = self.active_strategies.pop(strategy_id)
            
            return {
                "success": True,
                "message": f"Strategy {strategy_id} deleted",
                "strategy_id": strategy_id,
                "stop_result": stop_result
            }
            
        except Exception as e:
            logger.error(f"Error deleting strategy {strategy_id}: {e}")
            return {
                "success": False,
                "message": f"Error deleting strategy: {str(e)}",
                "strategy_id": strategy_id
            }
    
    def get_strategy_performance(self, strategy_id: str) -> Dict[str, Any]:
        """Get performance metrics for a strategy

        Args:
            strategy_id: Strategy ID

        Returns:
            Dictionary with performance metrics
        """
        if strategy_id not in self.active_strategies:
            return {
                "success": False,
                "message": f"Strategy with ID {strategy_id} not found",
                "strategy_id": strategy_id
            }
        
        try:
            strategy = self.active_strategies[strategy_id]["instance"]
            metrics = strategy.get_performance_metrics()
            
            return {
                "success": True,
                "strategy_id": strategy_id,
                "metrics": metrics
            }
            
        except Exception as e:
            logger.error(f"Error getting performance for strategy {strategy_id}: {e}")
            return {
                "success": False,
                "message": f"Error getting performance: {str(e)}",
                "strategy_id": strategy_id
            }
